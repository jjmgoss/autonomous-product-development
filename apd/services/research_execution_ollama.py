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
from apd.services.research_skills import resolve_research_skills_for_phase
from apd.services.research_trace import (
    append_research_trace_event,
    attach_run_to_trace_events,
    create_trace_correlation_id,
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


def _trace_execution_event(
    db: Session,
    brief,
    *,
    correlation_id: str | None,
    event_type: str,
    phase: str | None = None,
    message: str | None = None,
    payload: dict[str, Any] | None = None,
    run_id: int | None = None,
) -> None:
    if not correlation_id:
        return

    append_research_trace_event(
        db,
        brief_id=getattr(brief, "id", None),
        run_id=run_id,
        correlation_id=correlation_id,
        phase=phase,
        event_type=event_type,
        message=message,
        payload=payload,
    )


def get_ollama_execution_config(db: Session | None = None) -> tuple[OllamaExecutionConfig | None, list[str]]:
    # Prefer DB-backed settings when available. Import lazily to avoid circular imports.
    try:
        from apd.services.model_execution_settings import resolve_ollama_execution_config

        resolved, missing = resolve_ollama_execution_config(db)
    except Exception:
        resolved = None
        missing = []

    if resolved is None:
        # fallback to env-based resolution
        provider = (os.getenv("APD_MODEL_PROVIDER") or "").strip().lower()
        base_url = (os.getenv("APD_OLLAMA_BASE_URL") or "").strip()
        model = (os.getenv("APD_OLLAMA_MODEL") or "").strip()

        missing = []
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

    # Build typed config from resolved dict
    timeout_seconds = int(resolved.get("ollama_timeout_seconds") or 120)
    repair_attempts = int(resolved.get("component_repair_attempts") or 1)
    repair_attempts = min(repair_attempts, 1)
    keep_alive = resolved.get("ollama_keep_alive")

    return (
        OllamaExecutionConfig(
            provider=resolved.get("provider"),
            base_url=resolved.get("ollama_base_url"),
            model=resolved.get("ollama_model"),
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


def execute_research_brief_ollama(
    db: Session,
    brief,
    *,
    trace_correlation_id: str | None = None,
) -> dict[str, Any]:
    config, missing_env = get_ollama_execution_config(db)
    now = _iso_now()
    trace_correlation_id = trace_correlation_id or create_trace_correlation_id(brief_id=brief.id)
    trace_phase = "draft_execution"

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
            "trace_correlation_id": trace_correlation_id,
        }

    prompt = generate_ollama_execution_prompt(brief)
    status = "failed"
    errors_list: list[str] = []
    warnings_list: list[str] = []
    run_id: int | None = None
    started_at = now
    finished_at = now
    try:
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="phase_started",
            phase=trace_phase,
            message="Draft execution started.",
            payload={"provider": config.provider, "model": config.model},
        )
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="model_call_started",
            phase=trace_phase,
            message="Started draft model call.",
            payload={"provider": config.provider, "model": config.model, "attempt": 1, "prompt_chars": len(prompt)},
        )
        draft_data, parse_error = _call_ollama_for_draft(config, prompt)
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="model_call_completed",
            phase=trace_phase,
            message="Completed draft model call.",
            payload={
                "provider": config.provider,
                "model": config.model,
                "attempt": 1,
                "success": parse_error is None,
                "error": parse_error,
                "response_keys": sorted(draft_data.keys())[:8] if draft_data else [],
            },
        )
        if parse_error:
            status = "parse_failed" if parse_error.startswith("parse_failed") else "provider_error"
            errors_list.append(parse_error)
            finished_at = _iso_now()
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="phase_completed",
                phase=trace_phase,
                message="Draft execution failed.",
                payload={"status": status, "error_count": len(errors_list)},
            )
            return _build_result(
                config,
                status,
                started_at,
                finished_at,
                run_id,
                errors_list,
                warnings_list,
                trace_correlation_id=trace_correlation_id,
            )

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
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="repair_attempted",
                phase=trace_phase,
                message="Attempting draft repair after validation failure.",
                payload={"attempt": 1, "validation_error_count": len(report.grouped_errors or report.errors)},
            )
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="model_call_started",
                phase=trace_phase,
                message="Started repair model call.",
                payload={"provider": config.provider, "model": config.model, "attempt": 2, "repair": True},
            )
            repaired_data, repair_error = _call_ollama_for_repair(config, draft_data, report.grouped_errors or report.errors)
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="model_call_completed",
                phase=trace_phase,
                message="Completed repair model call.",
                payload={
                    "provider": config.provider,
                    "model": config.model,
                    "attempt": 2,
                    "repair": True,
                    "success": repair_error is None,
                    "error": repair_error,
                    "response_keys": sorted(repaired_data.keys())[:8] if repaired_data else [],
                },
            )
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
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="validation_failed",
                phase=trace_phase,
                message="Draft execution failed validation.",
                payload={"status": status, "errors": _first_errors(report.errors, limit=3)},
            )
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="phase_completed",
                phase=trace_phase,
                message="Draft execution failed.",
                payload={"status": status, "error_count": len(errors_list)},
            )
            return _build_result(
                config,
                status,
                started_at,
                finished_at,
                run_id,
                errors_list,
                warnings_list,
                trace_correlation_id=trace_correlation_id,
            )

        quality_result = _evaluate_product_quality_gate(package)
        warnings_list.extend(quality_result.warnings)
        if quality_result.error:
            finished_at = _iso_now()
            errors_list.append(quality_result.error)
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="validation_failed",
                phase="quality_gate",
                message="Draft execution failed the quality gate.",
                payload={"status": quality_result.status, "error": quality_result.error},
            )
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="phase_completed",
                phase=trace_phase,
                message="Draft execution failed.",
                payload={"status": quality_result.status, "error_count": len(errors_list)},
            )
            return _build_result(
                config,
                quality_result.status,
                started_at,
                finished_at,
                run_id,
                errors_list,
                warnings_list,
                trace_correlation_id=trace_correlation_id,
            )

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
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="phase_completed",
                phase=trace_phase,
                message="Draft execution failed during import.",
                payload={"status": status, "error_count": len(errors_list)},
            )
            return _build_result(
                config,
                status,
                started_at,
                finished_at,
                run_id,
                errors_list,
                warnings_list,
                trace_correlation_id=trace_correlation_id,
            )

        run_id = import_result.run_db_id
        attach_run_to_trace_events(db, correlation_id=trace_correlation_id, run_id=run_id)
        warnings_list.extend(_first_errors(import_result.warnings, limit=5))
        status = "imported"
        finished_at = _iso_now()
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="import_completed",
            phase="import",
            message="Imported draft execution result.",
            payload={"run_id": run_id, "warning_count": len(import_result.warnings)},
            run_id=run_id,
        )
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="phase_completed",
            phase=trace_phase,
            message="Draft execution completed.",
            payload={"status": status, "warning_count": len(warnings_list)},
            run_id=run_id,
        )
        return _build_result(
            config,
            status,
            started_at,
            finished_at,
            run_id,
            errors_list,
            warnings_list,
            trace_correlation_id=trace_correlation_id,
        )
    finally:
        _unload_ollama_model(config)


def execute_research_brief_ollama_components(db: Session, brief) -> dict[str, Any]:
    """Experimental component-based execution path using provider-agnostic event schema."""
    config, missing_env = get_ollama_execution_config(db)
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
    try:
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
    finally:
        _unload_ollama_model(config)


def execute_research_brief_ollama_components_grounded(
    db: Session,
    brief,
    *,
    trace_correlation_id: str | None = None,
) -> dict[str, Any]:
    from apd.services.web_research import get_grounding_source_packet_for_brief, render_grounding_source_packet

    config, missing_env = get_ollama_execution_config(db)
    component_repair_attempts = _parse_component_repair_attempts_env("APD_COMPONENT_REPAIR_ATTEMPTS", default=2)
    now = _iso_now()
    trace_correlation_id = trace_correlation_id or create_trace_correlation_id(brief_id=brief.id)
    execution_phase = "grounded_component_execution"
    if config is None:
        return {
            "success": False,
            "provider": "ollama-components-grounded",
            "status": "config_missing",
            "started_at": now,
            "finished_at": now,
            "errors": [f"Missing required env: {value}" for value in missing_env],
            "warnings": [],
            "run_id": None,
            "grounding_status": "config_missing",
            "grounding_errors": [f"Missing required env: {value}" for value in missing_env],
            "trace_correlation_id": trace_correlation_id,
        }

    _trace_execution_event(
        db,
        brief,
        correlation_id=trace_correlation_id,
        event_type="phase_started",
        phase=execution_phase,
        message="Grounded component execution started.",
        payload={"provider": config.provider, "model": config.model},
    )

    grounding_packet = get_grounding_source_packet_for_brief(db, brief)
    if not grounding_packet.sources or not grounding_packet.evidence_excerpts:
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="validation_failed",
            phase=execution_phase,
            message="Grounded component execution requires captured sources.",
            payload={"status": "grounding_missing_sources"},
        )
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="phase_completed",
            phase=execution_phase,
            message="Grounded component execution failed.",
            payload={"status": "grounding_missing_sources"},
        )
        return {
            "success": False,
            "provider": "ollama-components-grounded",
            "model": config.model,
            "status": "grounding_missing_sources",
            "started_at": now,
            "finished_at": now,
            "errors": ["No captured web sources are available for grounded component execution. Run web discovery first."],
            "warnings": [],
            "run_id": None,
            "mode": "grounded_component_execution",
            "grounding_status": "missing_sources",
            "grounding_errors": ["Run web discovery first to capture sources before grounded component execution."],
            "grounding_source_count": 0,
            "grounding_excerpt_count": 0,
            "trace_correlation_id": trace_correlation_id,
        }

    started_at = now
    grounded_source_packet = render_grounding_source_packet(grounding_packet)
    try:
        run_title = brief.title or (brief.research_question[:120] if brief.research_question else "Grounded Component Research")
        assembler = ComponentDraftAssembler(
            run_title=run_title,
            run_intent=brief.research_question,
            agent_name="ollama-grounded-component-prototype",
            external_draft_id=f"brief-{brief.id}-grounded-components-{started_at}",
        )
        assembler.seed_grounding_sources(
            sources=grounding_packet.sources,
            evidence_excerpts=grounding_packet.evidence_excerpts,
        )

        attempts_by_phase: dict[str, int] = {}
        warnings_list: list[str] = []
        candidate_ids: list[str] = []
        phases = ["candidate_batch", "claim_theme_batch", "validation_gate_batch"]
        known_source_ids = grounding_packet.source_ids
        known_excerpt_ids = grounding_packet.excerpt_ids
        excerpt_to_source_id = {
            str(item["id"]): str(item["source_id"]) for item in grounding_packet.evidence_excerpts
        }

        for phase_name in phases:
            errors_for_phase: list[str] = []
            prior_raw_batch: dict[str, Any] | None = None
            max_attempts = component_repair_attempts + 1
            attempts_by_phase[phase_name] = 0
            selected_skill_ids = resolve_research_skills_for_phase(phase_name, max_skills=None)

            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="phase_started",
                phase=phase_name,
                message=f"Component phase {phase_name} started.",
                payload={"attempt_limit": max_attempts, "candidate_count": len(candidate_ids)},
            )
            if selected_skill_ids:
                _trace_execution_event(
                    db,
                    brief,
                    correlation_id=trace_correlation_id,
                    event_type="skill_context_selected",
                    phase=phase_name,
                    message=f"Selected research skills for {phase_name}.",
                    payload={"skill_ids": selected_skill_ids, "skill_count": len(selected_skill_ids)},
                )

            for attempt_index in range(max_attempts):
                attempts_by_phase[phase_name] = attempt_index + 1
                if attempt_index == 0:
                    prompt = generate_ollama_component_phase_prompt(
                        brief,
                        phase_name,
                        candidate_ids=candidate_ids,
                        grounded_source_packet=grounded_source_packet,
                    )
                else:
                    prompt = generate_ollama_component_repair_prompt(
                        brief,
                        phase_name=phase_name,
                        validation_errors=errors_for_phase,
                        invalid_batch_data=prior_raw_batch,
                        grounded_source_packet=grounded_source_packet,
                    )

                if attempt_index > 0:
                    _trace_execution_event(
                        db,
                        brief,
                        correlation_id=trace_correlation_id,
                        event_type="repair_attempted",
                        phase=phase_name,
                        message=f"Attempting repair for {phase_name}.",
                        payload={"attempt": attempt_index + 1, "validation_error_count": len(errors_for_phase)},
                    )

                _trace_execution_event(
                    db,
                    brief,
                    correlation_id=trace_correlation_id,
                    event_type="model_call_started",
                    phase=phase_name,
                    message=f"Started model call for {phase_name}.",
                    payload={
                        "provider": config.provider,
                        "model": config.model,
                        "attempt": attempt_index + 1,
                        "repair": attempt_index > 0,
                    },
                )
                raw_batch_data, parse_error = _call_ollama_for_component_batch(config, prompt)
                _trace_execution_event(
                    db,
                    brief,
                    correlation_id=trace_correlation_id,
                    event_type="model_call_completed",
                    phase=phase_name,
                    message=f"Completed model call for {phase_name}.",
                    payload={
                        "provider": config.provider,
                        "model": config.model,
                        "attempt": attempt_index + 1,
                        "repair": attempt_index > 0,
                        "success": parse_error is None,
                        "error": parse_error,
                        "event_count": len(raw_batch_data.get("events") or []) if raw_batch_data else 0,
                    },
                )
                if parse_error:
                    errors_for_phase = [f"{phase_name}: {parse_error}"]
                    prior_raw_batch = None
                    _trace_execution_event(
                        db,
                        brief,
                        correlation_id=trace_correlation_id,
                        event_type="validation_failed",
                        phase=phase_name,
                        message=f"Model output for {phase_name} failed parsing.",
                        payload={"attempt": attempt_index + 1, "kind": "parse", "errors": errors_for_phase[:3]},
                    )
                    continue

                prior_raw_batch = raw_batch_data
                batch, batch_errors = parse_component_batch_from_data(raw_batch_data)
                if batch is None:
                    errors_for_phase = [f"{phase_name}: {line}" for line in _first_errors(batch_errors, limit=5)]
                    _trace_execution_event(
                        db,
                        brief,
                        correlation_id=trace_correlation_id,
                        event_type="validation_failed",
                        phase=phase_name,
                        message=f"Model output for {phase_name} failed batch validation.",
                        payload={"attempt": attempt_index + 1, "kind": "batch", "errors": errors_for_phase[:3]},
                    )
                    continue

                phase_errors = _validate_component_phase_batch(phase_name, batch)
                if phase_errors:
                    errors_for_phase = phase_errors
                    _trace_execution_event(
                        db,
                        brief,
                        correlation_id=trace_correlation_id,
                        event_type="validation_failed",
                        phase=phase_name,
                        message=f"Component batch for {phase_name} failed phase validation.",
                        payload={"attempt": attempt_index + 1, "kind": "phase", "errors": errors_for_phase[:3]},
                    )
                    continue

                grounding_errors = _validate_component_grounding(
                    phase_name,
                    batch,
                    known_source_ids=known_source_ids,
                    known_excerpt_ids=known_excerpt_ids,
                    excerpt_to_source_id=excerpt_to_source_id,
                )
                if grounding_errors:
                    errors_for_phase = grounding_errors
                    _trace_execution_event(
                        db,
                        brief,
                        correlation_id=trace_correlation_id,
                        event_type="validation_failed",
                        phase=phase_name,
                        message=f"Component batch for {phase_name} failed grounding validation.",
                        payload={"attempt": attempt_index + 1, "kind": "grounding", "errors": errors_for_phase[:3]},
                    )
                    continue

                assembly_result = assembler.apply_batch(batch)
                if not assembly_result.success:
                    errors_for_phase = [f"{phase_name}: {line}" for line in _first_errors(assembly_result.errors, limit=5)]
                    _trace_execution_event(
                        db,
                        brief,
                        correlation_id=trace_correlation_id,
                        event_type="validation_failed",
                        phase=phase_name,
                        message=f"Component batch for {phase_name} failed assembly.",
                        payload={"attempt": attempt_index + 1, "kind": "assembly", "errors": errors_for_phase[:3]},
                    )
                    continue

                if phase_name == "candidate_batch":
                    candidate_ids = [
                        event.external_id
                        for event in batch.events
                        if event.event_type == ResearchComponentEventType.CANDIDATE_PROPOSED
                    ]
                warnings_list.extend(_first_errors(assembly_result.warnings, limit=5))
                _trace_execution_event(
                    db,
                    brief,
                    correlation_id=trace_correlation_id,
                    event_type="phase_completed",
                    phase=phase_name,
                    message=f"Component phase {phase_name} completed.",
                    payload={
                        "status": "completed",
                        "attempts": attempts_by_phase[phase_name],
                        "event_count": len(batch.events),
                    },
                )
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
                _trace_execution_event(
                    db,
                    brief,
                    correlation_id=trace_correlation_id,
                    event_type="phase_completed",
                    phase=phase_name,
                    message=f"Component phase {phase_name} failed.",
                    payload={"status": failure_status, "attempts": attempts_by_phase[phase_name], "errors": errors_for_phase[:3]},
                )
                _trace_execution_event(
                    db,
                    brief,
                    correlation_id=trace_correlation_id,
                    event_type="phase_completed",
                    phase=execution_phase,
                    message="Grounded component execution failed.",
                    payload={"status": failure_status, "last_phase": phase_name},
                )
                return {
                    **_build_result(
                        config,
                        failure_status,
                        started_at,
                        finished_at,
                        None,
                        _first_errors(errors_for_phase or [f"{phase_name}: failed"], limit=5),
                        _first_errors(warnings_list, limit=5),
                        provider_override="ollama-components-grounded",
                        mode="grounded_component_execution",
                        last_phase=phase_name,
                        attempts_by_phase=attempts_by_phase,
                        trace_correlation_id=trace_correlation_id,
                    ),
                    "grounding_status": "failed",
                    "grounding_errors": _first_errors(errors_for_phase or [f"{phase_name}: failed"], limit=5),
                    "grounding_source_count": len(grounding_packet.sources),
                    "grounding_excerpt_count": len(grounding_packet.evidence_excerpts),
                }

        assembled_package = assembler.package_dict()
        report = validate_agent_draft_data(Path("<ollama-grounded-components-output>"), assembled_package)
        if not report.is_valid or report.package is None:
            finished_at = _iso_now()
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="validation_failed",
                phase="final_validation",
                message="Grounded component execution failed final validation.",
                payload={"errors": _first_errors(report.errors, limit=3)},
            )
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="phase_completed",
                phase=execution_phase,
                message="Grounded component execution failed.",
                payload={"status": "validation_failed", "last_phase": "final_validation"},
            )
            return {
                **_build_result(
                    config,
                    "validation_failed",
                    started_at,
                    finished_at,
                    None,
                    _first_errors(report.errors, limit=5),
                    _first_errors(warnings_list, limit=5),
                    provider_override="ollama-components-grounded",
                    mode="grounded_component_execution",
                    last_phase="final_validation",
                    attempts_by_phase=attempts_by_phase,
                    trace_correlation_id=trace_correlation_id,
                ),
                "grounding_status": "passed",
                "grounding_errors": [],
                "grounding_source_count": len(grounding_packet.sources),
                "grounding_excerpt_count": len(grounding_packet.evidence_excerpts),
            }

        quality_result = _evaluate_product_quality_gate(report.package)
        warnings_list.extend(quality_result.warnings)
        if quality_result.error:
            finished_at = _iso_now()
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="validation_failed",
                phase="quality_gate",
                message="Grounded component execution failed the quality gate.",
                payload={"status": quality_result.status, "error": quality_result.error},
            )
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="phase_completed",
                phase=execution_phase,
                message="Grounded component execution failed.",
                payload={"status": quality_result.status, "last_phase": "quality_gate"},
            )
            return {
                **_build_result(
                    config,
                    quality_result.status,
                    started_at,
                    finished_at,
                    None,
                    [quality_result.error],
                    _first_errors(warnings_list, limit=5),
                    provider_override="ollama-components-grounded",
                    mode="grounded_component_execution",
                    last_phase="quality_gate",
                    attempts_by_phase=attempts_by_phase,
                    trace_correlation_id=trace_correlation_id,
                ),
                "grounding_status": "passed",
                "grounding_errors": [],
                "grounding_source_count": len(grounding_packet.sources),
                "grounding_excerpt_count": len(grounding_packet.evidence_excerpts),
            }

        try:
            import_result = import_agent_draft_package(
                db,
                report.package,
                package_path=None,
                allow_duplicate_external_id=False,
            )
        except Exception as exc:
            finished_at = _iso_now()
            _trace_execution_event(
                db,
                brief,
                correlation_id=trace_correlation_id,
                event_type="phase_completed",
                phase=execution_phase,
                message="Grounded component execution failed during import.",
                payload={"status": "import_failed", "last_phase": "import"},
            )
            return {
                **_build_result(
                    config,
                    "import_failed",
                    started_at,
                    finished_at,
                    None,
                    [f"import_failed: {exc}"],
                    _first_errors(warnings_list, limit=5),
                    provider_override="ollama-components-grounded",
                    mode="grounded_component_execution",
                    last_phase="import",
                    attempts_by_phase=attempts_by_phase,
                    trace_correlation_id=trace_correlation_id,
                ),
                "grounding_status": "passed",
                "grounding_errors": [],
                "grounding_source_count": len(grounding_packet.sources),
                "grounding_excerpt_count": len(grounding_packet.evidence_excerpts),
            }

        finished_at = _iso_now()
        warnings_list.extend(import_result.warnings)
        attach_run_to_trace_events(db, correlation_id=trace_correlation_id, run_id=import_result.run_db_id)
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="import_completed",
            phase="import",
            message="Imported grounded component execution result.",
            payload={"run_id": import_result.run_db_id, "warning_count": len(import_result.warnings)},
            run_id=import_result.run_db_id,
        )
        _trace_execution_event(
            db,
            brief,
            correlation_id=trace_correlation_id,
            event_type="phase_completed",
            phase=execution_phase,
            message="Grounded component execution completed.",
            payload={"status": "imported", "last_phase": "import"},
            run_id=import_result.run_db_id,
        )
        return {
            **_build_result(
                config,
                "imported",
                started_at,
                finished_at,
                import_result.run_db_id,
                [],
                _first_errors(warnings_list, limit=5),
                provider_override="ollama-components-grounded",
                mode="grounded_component_execution",
                last_phase="import",
                attempts_by_phase=attempts_by_phase,
                trace_correlation_id=trace_correlation_id,
            ),
            "grounding_status": "passed",
            "grounding_errors": [],
            "grounding_source_count": len(grounding_packet.sources),
            "grounding_excerpt_count": len(grounding_packet.evidence_excerpts),
        }
    finally:
        _unload_ollama_model(config)


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
    trace_correlation_id: str | None = None,
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
    if trace_correlation_id is not None:
        result["trace_correlation_id"] = trace_correlation_id
    return result


def _call_ollama_for_draft(
    config: OllamaExecutionConfig,
    prompt: str,
) -> tuple[dict[str, Any] | None, str | None]:
    payload = _build_generate_payload(config, prompt, during_execution=True)
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
    payload = _build_generate_payload(config, prompt, during_execution=True)
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
    payload = _build_generate_payload(config, prompt, during_execution=True)
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


def _build_generate_payload(
    config: OllamaExecutionConfig,
    prompt: str,
    *,
    during_execution: bool = False,
) -> dict[str, Any]:
    keep_alive_value = _execution_keep_alive(config) if during_execution else config.keep_alive
    return {
        "model": config.model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": keep_alive_value,
    }


def _execution_keep_alive(config: OllamaExecutionConfig) -> int | str:
    if _should_unload_after_execution(config):
        return "5m"
    return config.keep_alive


def _should_unload_after_execution(config: OllamaExecutionConfig) -> bool:
    keep_alive = config.keep_alive
    if isinstance(keep_alive, int):
        return keep_alive == 0
    return str(keep_alive).strip() == "0"


def _unload_ollama_model(config: OllamaExecutionConfig) -> None:
    if not _should_unload_after_execution(config):
        return
    payload = {
        "model": config.model,
        "prompt": "",
        "stream": False,
        "keep_alive": 0,
    }
    _ollama_generate(config, payload)


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

    has_source_urls = any(
        bool(source.url and str(source.url).strip()) and not bool((source.metadata_json or {}).get("grounding_source"))
        for source in package.sources
    )
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


def _validate_component_grounding(
    phase_name: str,
    batch: ResearchComponentBatch,
    *,
    known_source_ids: set[str],
    known_excerpt_ids: set[str],
    excerpt_to_source_id: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    claim_ids = {
        event.external_id
        for event in batch.events
        if event.event_type == ResearchComponentEventType.CLAIM_PROPOSED
    }
    grounded_claim_links: set[str] = set()

    for event in batch.events:
        if event.event_type in {ResearchComponentEventType.SOURCE_ADDED, ResearchComponentEventType.EVIDENCE_EXCERPT_ADDED}:
            errors.append(f"{phase_name}: do not add new source or excerpt events in grounded mode")
            continue

        payload = dict(event.payload or {})
        for key in ("url", "source_url", "citation_url"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip().lower().startswith(("http://", "https://")):
                errors.append(f"{phase_name}: do not invent source URLs in {event.event_type.value}")

        if event.event_type != ResearchComponentEventType.EVIDENCE_LINK_ADDED:
            continue

        source_id = str(payload.get("source_id") or "").strip()
        excerpt_id = str(payload.get("excerpt_id") or "").strip()
        target_type = str(payload.get("target_type") or "").strip()
        target_id = str(payload.get("target_id") or "").strip()
        relationship = str(payload.get("relationship") or "").strip()

        if not source_id and not excerpt_id:
            errors.append(f"{phase_name}: grounded evidence links must reference source_id and/or excerpt_id")
        if source_id and source_id not in known_source_ids:
            errors.append(f"{phase_name}: unknown grounded source_id '{source_id}'")
        if excerpt_id and excerpt_id not in known_excerpt_ids:
            errors.append(f"{phase_name}: unknown grounded excerpt_id '{excerpt_id}'")
        if source_id and excerpt_id and excerpt_to_source_id.get(excerpt_id) != source_id:
            errors.append(f"{phase_name}: excerpt_id '{excerpt_id}' does not belong to source_id '{source_id}'")
        if target_type == "claim" and target_id:
            if target_id not in claim_ids:
                errors.append(f"{phase_name}: evidence link references unknown claim target_id '{target_id}'")
            if relationship == "supports" and (source_id or excerpt_id):
                grounded_claim_links.add(target_id)

    if phase_name == "claim_theme_batch" and claim_ids and not grounded_claim_links:
        errors.append(f"{phase_name}: at least one claim needs a supporting grounded evidence link")
    return errors


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
