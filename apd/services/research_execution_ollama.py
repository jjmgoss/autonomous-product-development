from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from sqlalchemy.orm import Session

from apd.services.agent_draft_import import AgentDraftPackage, import_agent_draft_package
from apd.services.agent_draft_validation import validate_agent_draft_data
from apd.services.research_brief_service import (
    generate_ollama_component_phase_prompt,
    generate_ollama_component_repair_prompt,
    generate_ollama_execution_prompt,
)
from apd.services.research_components import (
    ComponentDraftAssembler,
    ResearchComponentBatch,
    ResearchComponentEventType,
    parse_component_batch_from_data,
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OllamaExecutionConfig:
    provider: str
    base_url: str
    model: str
    timeout_seconds: int
    repair_attempts: int
    keep_alive: int | str


@dataclass(frozen=True)
class ProductQualityGateResult:
    status: str
    error: str | None
    warnings: list[str]


def get_ollama_execution_config() -> tuple[OllamaExecutionConfig | None, list[str]]:
    provider = (os.getenv("APD_MODEL_PROVIDER") or "").strip().lower()
    base_url = (os.getenv("APD_OLLAMA_BASE_URL") or "").strip()
    model = (os.getenv("APD_OLLAMA_MODEL") or "").strip()

    missing: list[str] = []
    if provider != "ollama":
        missing.append("APD_MODEL_PROVIDER=ollama")
    if not base_url:
        missing.append("APD_OLLAMA_BASE_URL")
    if not model:
        missing.append("APD_OLLAMA_MODEL")

    if missing:
        return None, missing

    timeout_seconds = _parse_positive_int_env("APD_OLLAMA_TIMEOUT_SECONDS", default=120)
    repair_attempts = _parse_nonnegative_int_env("APD_OLLAMA_REPAIR_ATTEMPTS", default=1)
    # Scope guardrail: permit at most one repair call.
    repair_attempts = min(repair_attempts, 1)
    keep_alive = _parse_keep_alive_env("APD_OLLAMA_KEEP_ALIVE", default=0)

    return (
        OllamaExecutionConfig(
            provider=provider,
            base_url=base_url.rstrip("/"),
            model=model,
            timeout_seconds=timeout_seconds,
            repair_attempts=repair_attempts,
            keep_alive=keep_alive,
        ),
        [],
    )


def extract_json_object_from_model_output(text: str) -> tuple[dict[str, Any] | None, str | None]:
    candidate = text.strip()
    if not candidate:
        return None, "parse_failed: empty_model_output"

    full = _parse_json_object(candidate)
    if full is not None:
        return full, None

    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", candidate, flags=re.IGNORECASE | re.DOTALL)
    if fenced_match:
        fenced = _parse_json_object(fenced_match.group(1))
        if fenced is not None:
            return fenced, None

    first = candidate.find("{")
    last = candidate.rfind("}")
    if first != -1 and last != -1 and first < last:
        sliced = _parse_json_object(candidate[first : last + 1])
        if sliced is not None:
            return sliced, None

    return None, "parse_failed: unable_to_extract_json_object"


def execute_research_brief_ollama(db: Session, brief) -> dict[str, Any]:
    config, missing_env = get_ollama_execution_config()
    now = _iso_now()

    if config is None:
        return {
            "success": False,
            "provider": "ollama",
            "status": "config_missing",
            "started_at": now,
            "finished_at": now,
            "errors": [f"Missing required env: {value}" for value in missing_env],
            "warnings": [],
            "run_id": None,
        }

    prompt = generate_ollama_execution_prompt(brief)
    status = "failed"
    errors_list: list[str] = []
    warnings_list: list[str] = []
    run_id: int | None = None
    started_at = now
    finished_at = now

    draft_data, parse_error = _call_ollama_for_draft(config, prompt)
    if parse_error:
        status = "parse_failed" if parse_error.startswith("parse_failed") else "provider_error"
        errors_list.append(parse_error)
        finished_at = _iso_now()
        return _build_result(config, status, started_at, finished_at, run_id, errors_list, warnings_list)

    report = validate_agent_draft_data(Path("<ollama-output>"), draft_data)
    package = report.package
    if not report.is_valid or package is None:
        normalized_data, normalize_fixes = _safe_normalize_near_miss(draft_data)
        if normalize_fixes:
            warnings_list.append(f"applied_normalization_fixes={len(normalize_fixes)}")
            normalized_report = validate_agent_draft_data(Path("<ollama-output-normalized>"), normalized_data)
            if normalized_report.is_valid and normalized_report.package is not None:
                report = normalized_report
                package = normalized_report.package

    if (package is None or not report.is_valid) and config.repair_attempts > 0:
        warnings_list.append("repair_attempted=1")
        repaired_data, repair_error = _call_ollama_for_repair(config, draft_data, report.grouped_errors or report.errors)
        if repair_error:
            errors_list.append(repair_error)
        elif repaired_data is not None:
            repaired_report = validate_agent_draft_data(Path("<ollama-output-repair>"), repaired_data)
            if repaired_report.is_valid and repaired_report.package is not None:
                package = repaired_report.package
                report = repaired_report
                warnings_list.append("repair_succeeded=true")
            else:
                errors_list.extend(_first_errors(repaired_report.errors, limit=5))

    if package is None or not report.is_valid:
        status = "validation_failed"
        if not errors_list:
            errors_list.extend(_first_errors(report.errors, limit=5))
        finished_at = _iso_now()
        return _build_result(config, status, started_at, finished_at, run_id, errors_list, warnings_list)

    quality_result = _evaluate_product_quality_gate(package)
    warnings_list.extend(quality_result.warnings)
    if quality_result.error:
        finished_at = _iso_now()
        errors_list.append(quality_result.error)
        return _build_result(config, quality_result.status, started_at, finished_at, run_id, errors_list, warnings_list)

    try:
        import_result = import_agent_draft_package(
            db,
            package,
            package_path=None,
            allow_duplicate_external_id=False,
        )
    except Exception as exc:
        status = "import_failed"
        errors_list.append(f"import_failed: {exc}")
        finished_at = _iso_now()
        return _build_result(config, status, started_at, finished_at, run_id, errors_list, warnings_list)

    run_id = import_result.run_db_id
    warnings_list.extend(_first_errors(import_result.warnings, limit=5))
    status = "imported"
    finished_at = _iso_now()
    return _build_result(config, status, started_at, finished_at, run_id, errors_list, warnings_list)


def execute_research_brief_ollama_components(db: Session, brief) -> dict[str, Any]:
    """Experimental component-based execution path using provider-agnostic event schema."""
    config, missing_env = get_ollama_execution_config()
    component_repair_attempts = _parse_component_repair_attempts_env("APD_COMPONENT_REPAIR_ATTEMPTS", default=2)
    now = _iso_now()
    if config is None:
        return {
            "success": False,
            "provider": "ollama-components",
            "status": "config_missing",
            "started_at": now,
            "finished_at": now,
            "errors": [f"Missing required env: {value}" for value in missing_env],
            "warnings": [],
            "run_id": None,
        }

    started_at = now
    run_title = brief.title or (brief.research_question[:120] if brief.research_question else "Component Research")
    assembler = ComponentDraftAssembler(
        run_title=run_title,
        run_intent=brief.research_question,
        agent_name="ollama-component-prototype",
        external_draft_id=f"brief-{brief.id}-components-{started_at}",
    )
    attempts_by_phase: dict[str, int] = {}
    warnings_list: list[str] = []
    candidate_ids: list[str] = []
    phases = ["candidate_batch", "claim_theme_batch", "validation_gate_batch"]

    for phase_name in phases:
        errors_for_phase: list[str] = []
        prior_raw_batch: dict[str, Any] | None = None
        max_attempts = component_repair_attempts + 1
        attempts_by_phase[phase_name] = 0

        for attempt_index in range(max_attempts):
            attempts_by_phase[phase_name] = attempt_index + 1
            if attempt_index == 0:
                prompt = generate_ollama_component_phase_prompt(brief, phase_name, candidate_ids=candidate_ids)
            else:
                prompt = generate_ollama_component_repair_prompt(
                    brief,
                    phase_name=phase_name,
                    validation_errors=errors_for_phase,
                    invalid_batch_data=prior_raw_batch,
                )

            raw_batch_data, parse_error = _call_ollama_for_component_batch(config, prompt)
            if parse_error:
                errors_for_phase = [f"{phase_name}: {parse_error}"]
                prior_raw_batch = None
                continue

            prior_raw_batch = raw_batch_data
            batch, batch_errors = parse_component_batch_from_data(raw_batch_data)
            if batch is None:
                errors_for_phase = [f"{phase_name}: {line}" for line in _first_errors(batch_errors, limit=5)]
                continue

            phase_errors = _validate_component_phase_batch(phase_name, batch)
            if phase_errors:
                errors_for_phase = phase_errors
                continue

            assembly_result = assembler.apply_batch(batch)
            if not assembly_result.success:
                errors_for_phase = [f"{phase_name}: {line}" for line in _first_errors(assembly_result.errors, limit=5)]
                continue

            if phase_name == "candidate_batch":
                candidate_ids = [
                    event.external_id
                    for event in batch.events
                    if event.event_type == ResearchComponentEventType.CANDIDATE_PROPOSED
                ]
            warnings_list.extend(_first_errors(assembly_result.warnings, limit=5))
            break
        else:
            finished_at = _iso_now()
            failure_status = "quality_failed_no_candidates" if phase_name == "candidate_batch" else "component_validation_failed"
            if phase_name == "candidate_batch":
                errors_for_phase = [
                    (
                        "The model returned no product candidates. Refine the brief toward a product/problem/opportunity, "
                        "or try a stronger model."
                    )
                ]
            return _build_result(
                config,
                failure_status,
                started_at,
                finished_at,
                None,
                _first_errors(errors_for_phase or [f"{phase_name}: failed"], limit=5),
                _first_errors(warnings_list, limit=5),
                provider_override="ollama-components",
                mode="component_execution",
                last_phase=phase_name,
                attempts_by_phase=attempts_by_phase,
            )

    assembled_package = assembler.package_dict()
    report = validate_agent_draft_data(Path("<ollama-components-output>"), assembled_package)
    if not report.is_valid or report.package is None:
        finished_at = _iso_now()
        return _build_result(
            config,
            "validation_failed",
            started_at,
            finished_at,
            None,
            _first_errors(report.errors, limit=5),
            _first_errors(warnings_list, limit=5),
            provider_override="ollama-components",
            mode="component_execution",
            last_phase="final_validation",
            attempts_by_phase=attempts_by_phase,
        )

    quality_result = _evaluate_product_quality_gate(report.package)
    warnings_list.extend(quality_result.warnings)
    if quality_result.error:
        finished_at = _iso_now()
        return _build_result(
            config,
            quality_result.status,
            started_at,
            finished_at,
            None,
            [quality_result.error],
            _first_errors(warnings_list, limit=5),
            provider_override="ollama-components",
            mode="component_execution",
            last_phase="quality_gate",
            attempts_by_phase=attempts_by_phase,
        )

    try:
        import_result = import_agent_draft_package(
            db,
            report.package,
            package_path=None,
            allow_duplicate_external_id=False,
        )
    except Exception as exc:
        finished_at = _iso_now()
        return _build_result(
            config,
            "import_failed",
            started_at,
            finished_at,
            None,
            [f"import_failed: {exc}"],
            _first_errors(warnings_list, limit=5),
            provider_override="ollama-components",
            mode="component_execution",
            last_phase="import",
            attempts_by_phase=attempts_by_phase,
        )

    finished_at = _iso_now()
    warnings_list.extend(import_result.warnings)
    return _build_result(
        config,
        "imported",
        started_at,
        finished_at,
        import_result.run_db_id,
        [],
        _first_errors(warnings_list, limit=5),
        provider_override="ollama-components",
        mode="component_execution",
        last_phase="import",
        attempts_by_phase=attempts_by_phase,
    )


def _build_result(
    config: OllamaExecutionConfig,
    status: str,
    started_at: str,
    finished_at: str,
    run_id: int | None,
    errors_list: list[str],
    warnings_list: list[str],
    provider_override: str | None = None,
    mode: str | None = None,
    last_phase: str | None = None,
    attempts_by_phase: dict[str, int] | None = None,
) -> dict[str, Any]:
    result = {
        "success": status == "imported" and run_id is not None,
        "provider": provider_override or config.provider,
        "model": config.model,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "errors": errors_list[:5],
        "warnings": warnings_list[:5],
        "run_id": run_id,
    }
    if mode is not None:
        result["mode"] = mode
    if last_phase is not None:
        result["last_phase"] = last_phase
    if attempts_by_phase is not None:
        result["attempts_by_phase"] = dict(attempts_by_phase)
    return result


def _call_ollama_for_draft(
    config: OllamaExecutionConfig,
    prompt: str,
) -> tuple[dict[str, Any] | None, str | None]:
    payload = _build_generate_payload(config, prompt)
    response_data, call_error = _ollama_generate(config, payload)
    if call_error:
        return None, call_error

    output_text = str(response_data.get("response") or "")
    if not output_text.strip():
        return None, "provider_error: empty_ollama_response"

    return extract_json_object_from_model_output(output_text)


def _call_ollama_for_component_batch(
    config: OllamaExecutionConfig,
    prompt: str,
) -> tuple[dict[str, Any] | None, str | None]:
    payload = _build_generate_payload(config, prompt)
    response_data, call_error = _ollama_generate(config, payload)
    if call_error:
        return None, call_error
    output_text = str(response_data.get("response") or "")
    if not output_text.strip():
        return None, "provider_error: empty_ollama_response"
    parsed, parse_error = extract_json_object_from_model_output(output_text)
    if parse_error:
        return None, parse_error
    return parsed, None


def _call_ollama_for_repair(
    config: OllamaExecutionConfig,
    prior_data: dict[str, Any],
    validation_errors: list[str],
) -> tuple[dict[str, Any] | None, str | None]:
    errors_block = "\n".join(f"- {line}" for line in _first_errors(validation_errors, limit=8))
    prior_json = json.dumps(prior_data, ensure_ascii=False)
    prompt = (
        "Repair this APD agent draft package so it passes strict APD draft validation.\n"
        "Return only JSON.\n"
        "Preserve meaning and IDs unless schema repair requires a rename.\n\n"
        "Validation errors:\n"
        f"{errors_block}\n\n"
        "Draft JSON:\n"
        f"{prior_json}"
    )
    payload = _build_generate_payload(config, prompt)
    response_data, call_error = _ollama_generate(config, payload)
    if call_error:
        return None, call_error

    output_text = str(response_data.get("response") or "")
    if not output_text.strip():
        return None, "provider_error: empty_ollama_repair_response"

    return extract_json_object_from_model_output(output_text)


def _ollama_generate(
    config: OllamaExecutionConfig,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    url = f"{config.base_url}/api/generate"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as resp:
            status_code = getattr(resp, "status", 200)
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        return {}, f"provider_error: ollama_http_{exc.code}"
    except error.URLError as exc:
        return {}, f"provider_error: ollama_unreachable ({exc.reason})"
    except TimeoutError:
        return {}, "provider_error: ollama_timeout"
    except Exception as exc:
        return {}, f"provider_error: {exc}"

    if status_code >= 400:
        return {}, f"provider_error: ollama_http_{status_code}"

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}, "provider_error: ollama_invalid_json_response"

    if not isinstance(parsed, dict):
        return {}, "provider_error: ollama_response_not_object"

    return parsed, None


def _build_generate_payload(config: OllamaExecutionConfig, prompt: str) -> dict[str, Any]:
    return {
        "model": config.model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": config.keep_alive,
    }


def _evaluate_product_quality_gate(package: AgentDraftPackage) -> ProductQualityGateResult:
    if len(package.candidates) == 0:
        return ProductQualityGateResult(
            status="quality_failed_no_candidates",
            error=(
                "The model returned no product candidates. Refine the brief toward a product/problem/opportunity, "
                "or try a stronger model."
            ),
            warnings=[],
        )

    recommendation = (package.run.recommendation or "").strip().lower()
    if recommendation in {"needs_clarification", "needs-clarification"}:
        return ProductQualityGateResult(
            status="needs_clarification",
            error="The model requested clarification. Refine the brief with a concrete product/problem/opportunity focus.",
            warnings=[],
        )

    has_source_urls = any(bool(source.url and str(source.url).strip()) for source in package.sources)
    warnings: list[str] = []
    if has_source_urls:
        warnings.append("quality_warning_unprovided_source_urls")

    return ProductQualityGateResult(status="ok", error=None, warnings=warnings)


def _parse_json_object(candidate: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _first_errors(values: list[str], *, limit: int) -> list[str]:
    return [str(v) for v in values[:limit]]


def _parse_positive_int_env(name: str, *, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _parse_nonnegative_int_env(name: str, *, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def _parse_keep_alive_env(name: str, *, default: int) -> int | str:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return raw


def _parse_component_repair_attempts_env(name: str, *, default: int) -> int:
    value = _parse_nonnegative_int_env(name, default=default)
    return min(value, 3)


def _validate_component_phase_batch(phase_name: str, batch: ResearchComponentBatch) -> list[str]:
    event_types = {event.event_type for event in batch.events}
    if phase_name == "candidate_batch":
        if ResearchComponentEventType.CANDIDATE_PROPOSED not in event_types:
            return [
                (
                    "The model returned no product candidates. Refine the brief toward a product/problem/opportunity, "
                    "or try a stronger model."
                )
            ]
        return []
    if phase_name == "claim_theme_batch":
        if (
            ResearchComponentEventType.CLAIM_PROPOSED not in event_types
            and ResearchComponentEventType.THEME_PROPOSED not in event_types
        ):
            return [f"{phase_name}: batch must include claim.proposed and/or theme.proposed"]
        return []
    if phase_name == "validation_gate_batch":
        if ResearchComponentEventType.VALIDATION_GATE_PROPOSED not in event_types:
            return [f"{phase_name}: batch must include validation_gate.proposed"]
        return []
    return []


def _safe_normalize_near_miss(raw_data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    normalized = json.loads(json.dumps(raw_data))
    applied: list[str] = []

    aliases: dict[str, dict[str, str]] = {
        "sources": {"type": "source_type", "accessed_at": "captured_at"},
        "evidence_excerpts": {"text": "excerpt_text", "locator": "location_reference"},
        "claims": {"claim": "statement"},
        "themes": {"theme": "name"},
        "candidates": {"name": "title", "description": "summary"},
    }

    for section, mapping in aliases.items():
        items = normalized.get(section)
        if not isinstance(items, list):
            continue
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for old_name, new_name in mapping.items():
                if old_name in item and new_name not in item:
                    item[new_name] = item.pop(old_name)
                    applied.append(f"{section}[{idx}]: {old_name}->{new_name}")

    gate_phase_map = {
        "problem_validation": "supported_opportunity",
        "solution_validation": "vetted_opportunity",
        "commercial_validation": "vetted_opportunity",
    }
    gates = normalized.get("validation_gates")
    if isinstance(gates, list):
        for idx, gate in enumerate(gates):
            if not isinstance(gate, dict):
                continue
            phase = gate.get("phase")
            mapped = gate_phase_map.get(phase)
            if mapped:
                gate["phase"] = mapped
                applied.append(f"validation_gates[{idx}]: phase->{mapped}")

    links = normalized.get("evidence_links")
    legacy_target_map = {
        "claim_id": "claim",
        "theme_id": "theme",
        "candidate_id": "candidate",
        "gate_id": "validation_gate",
    }
    if isinstance(links, list):
        for idx, link in enumerate(links):
            if not isinstance(link, dict):
                continue
            if link.get("target_type") and link.get("target_id"):
                continue
            matches = [(field_name, target_type) for field_name, target_type in legacy_target_map.items() if link.get(field_name)]
            if len(matches) != 1:
                continue
            field_name, target_type = matches[0]
            link["target_type"] = target_type
            link["target_id"] = link.pop(field_name)
            applied.append(f"evidence_links[{idx}]: {field_name}->target_type,target_id")

    return normalized, applied
