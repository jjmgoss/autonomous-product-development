from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any
from urllib import parse

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.services.agent_draft_import import import_agent_draft_package
from apd.services.agent_draft_validation import validate_agent_draft_data
from apd.services.research_components import ComponentDraftAssembler, parse_component_batch_from_data
from apd.services.web_research import extract_title_and_text


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_DIR = REPO_ROOT / "evals" / "research" / "cases"
DEFAULT_FIXTURES_DIR = REPO_ROOT / "evals" / "research" / "fixtures"
DEFAULT_RESULTS_DIR = REPO_ROOT / "evals" / "research" / "results"
PHASE_ORDER = ("candidate_batch", "claim_theme_batch", "validation_gate_batch")


@dataclass(frozen=True)
class CaseRunResult:
    case_id: str
    result: dict[str, Any]


def load_research_eval_cases(cases_dir: Path = DEFAULT_CASES_DIR) -> list[dict[str, Any]]:
    case_paths = sorted(cases_dir.glob("*.yaml"))
    cases: list[dict[str, Any]] = []
    for case_path in case_paths:
        raw_data = yaml.safe_load(case_path.read_text(encoding="utf-8"))
        if not isinstance(raw_data, dict):
            raise ValueError(f"Eval case must be a mapping: {case_path}")
        cases.append(_normalize_case(case_path, raw_data))
    return cases


def run_fixture_research_evals(
    *,
    cases_dir: Path = DEFAULT_CASES_DIR,
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    fixture_only: bool = True,
    model_label: str = "fixture-mocked",
    harness_label: str = "apd-research-eval-fixture-v1",
    write_results: bool = True,
) -> dict[str, Any]:
    if not fixture_only:
        raise ValueError("Only fixture-only execution is supported in the first eval harness version.")

    started_at = _iso_now()
    case_results = [
        run_fixture_research_eval_case(
            case,
            fixtures_dir=fixtures_dir,
            model_label=model_label,
            harness_label=harness_label,
        )
        for case in load_research_eval_cases(cases_dir)
    ]
    aggregate = _build_aggregate_summary(case_results)
    output = {
        "schema_version": "1.0",
        "generated_at": _iso_now(),
        "harness": {
            "mode": "fixture_only",
            "runner": harness_label,
            "model": model_label,
            "cases_dir": str(cases_dir.resolve()),
            "fixtures_dir": str(fixtures_dir.resolve()),
            "started_at": started_at,
        },
        "aggregate": aggregate,
        "cases": [item.result for item in case_results],
    }
    if write_results:
        results_dir.mkdir(parents=True, exist_ok=True)
        output_path = results_dir / f"research-evals-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        output["results_path"] = str(output_path.resolve())
    return output


def run_fixture_research_eval_case(
    case: dict[str, Any],
    *,
    fixtures_dir: Path,
    model_label: str,
    harness_label: str,
) -> CaseRunResult:
    started = time.perf_counter()
    sources, excerpts = _build_fixture_packet(case, fixtures_dir)
    known_source_ids = {item["id"] for item in sources}
    known_excerpt_ids = {item["id"] for item in excerpts}

    assembler = ComponentDraftAssembler(
        run_title=case["brief"]["title"],
        run_intent=case["brief"]["research_question"],
        agent_name=harness_label,
        external_draft_id=f"eval-{case['id']}",
    )
    assembler.seed_grounding_sources(sources=sources, evidence_excerpts=excerpts)

    attempts_by_phase = {
        phase: int(value)
        for phase, value in dict(case["simulated_execution"].get("attempts_by_phase") or {}).items()
    }
    assembly_errors: list[str] = []
    for phase_name in PHASE_ORDER:
        raw_batch = case["simulated_execution"]["phase_batches"].get(phase_name)
        if raw_batch is None:
            continue
        attempts_by_phase.setdefault(phase_name, 1)
        batch, batch_errors = parse_component_batch_from_data(raw_batch)
        if batch is None:
            assembly_errors.extend(f"{phase_name}: {line}" for line in batch_errors[:5])
            continue
        assembly_result = assembler.apply_batch(batch)
        if not assembly_result.success:
            assembly_errors.extend(f"{phase_name}: {line}" for line in assembly_result.errors[:5])

    package_data = assembler.package_dict()
    validation_report = validate_agent_draft_data(Path(f"<research-eval:{case['id']}>"), package_data)
    import_summary: dict[str, Any] | None = None
    status = "validation_failed"
    errors = list(assembly_errors)
    warnings: list[str] = []
    if validation_report.is_valid and validation_report.package is not None and not assembly_errors:
        try:
            import_summary = _import_package_for_eval(validation_report.package)
            warnings.extend(import_summary["warnings"])
            status = "imported"
        except Exception as exc:
            errors.append(f"import_failed: {exc}")
            status = "import_failed"
    else:
        errors.extend(validation_report.errors[:5])

    metrics = _score_case(
        case,
        package_data=package_data,
        known_source_ids=known_source_ids,
        known_excerpt_ids=known_excerpt_ids,
        attempts_by_phase=attempts_by_phase,
        validation_success=validation_report.is_valid and not assembly_errors,
        import_summary=import_summary,
        runtime_seconds=time.perf_counter() - started,
        warnings=warnings,
    )
    score_summary = _build_score_summary(metrics)
    result = {
        "id": case["id"],
        "title": case["title"],
        "brief": case["brief"],
        "status": status,
        "execution": {
            "mode": "fixture_only",
            "provider": "fixture-mocked",
            "model": model_label,
            "harness": harness_label,
            "attempts_by_phase": attempts_by_phase,
            "retry_count": metrics["retry_count"],
        },
        "relevant_source_ids": case["relevant_source_ids"],
        "irrelevant_source_ids": case["irrelevant_source_ids"],
        "rubric_metadata": case["rubric_metadata"],
        "metrics": metrics,
        "score_summary": score_summary,
        "warnings": warnings[:10],
        "errors": errors[:10],
        "import_summary": import_summary,
    }
    return CaseRunResult(case_id=case["id"], result=result)


def render_eval_summary_table(output: dict[str, Any]) -> str:
    lines = [
        "Case                           Status           Score   Import  UnknownRefs  Retries",
        "-----------------------------  ---------------  ------  ------  -----------  -------",
    ]
    for case in output.get("cases", []):
        lines.append(
            "{case_id:<29}  {status:<15}  {score:>6.3f}  {imported:>6}  {unknown:>11}  {retries:>7}".format(
                case_id=str(case.get("id") or "")[:29],
                status=str(case.get("status") or "")[:15],
                score=float(case.get("score_summary", {}).get("overall_score") or 0.0),
                imported="yes" if case.get("metrics", {}).get("import_success") else "no",
                unknown=int(case.get("metrics", {}).get("unknown_source_reference_count") or 0),
                retries=int(case.get("metrics", {}).get("retry_count") or 0),
            )
        )
    aggregate = output.get("aggregate", {})
    lines.extend(
        [
            "",
            "Aggregate",
            f"- cases: {aggregate.get('case_count', 0)}",
            f"- imported: {aggregate.get('import_success_count', 0)}",
            f"- avg overall score: {float(aggregate.get('average_overall_score') or 0.0):.3f}",
            f"- total unknown source refs: {aggregate.get('total_unknown_source_reference_count', 0)}",
        ]
    )
    if output.get("results_path"):
        lines.append(f"- results json: {output['results_path']}")
    return "\n".join(lines)


def _normalize_case(case_path: Path, raw_data: dict[str, Any]) -> dict[str, Any]:
    brief = dict(raw_data.get("brief") or {})
    fixture_sources = list(raw_data.get("fixture_sources") or [])
    simulated_execution = dict(raw_data.get("simulated_execution") or {})
    phase_batches = dict(simulated_execution.get("phase_batches") or {})
    if not raw_data.get("id"):
        raise ValueError(f"Eval case missing id: {case_path}")
    if not brief.get("title") or not brief.get("research_question"):
        raise ValueError(f"Eval case brief requires title and research_question: {case_path}")
    if not fixture_sources:
        raise ValueError(f"Eval case requires fixture_sources: {case_path}")
    if not phase_batches:
        raise ValueError(f"Eval case requires simulated_execution.phase_batches: {case_path}")

    normalized_sources: list[dict[str, Any]] = []
    for item in fixture_sources:
        if not isinstance(item, dict) or not item.get("id") or not item.get("path") or not item.get("url"):
            raise ValueError(f"Eval case fixture_sources entries require id, path, and url: {case_path}")
        normalized_sources.append(
            {
                "id": str(item["id"]),
                "path": str(item["path"]),
                "url": str(item["url"]),
                "title": item.get("title"),
                "source_type": str(item.get("source_type") or "public_web"),
                "excerpt_type": str(item.get("excerpt_type") or "web_capture"),
                "relevant": bool(item.get("relevant", True)),
            }
        )
    relevant_source_ids = list(raw_data.get("relevant_source_ids") or [item["id"] for item in normalized_sources if item["relevant"]])
    irrelevant_source_ids = list(raw_data.get("irrelevant_source_ids") or [item["id"] for item in normalized_sources if not item["relevant"]])
    return {
        "id": str(raw_data["id"]),
        "title": str(raw_data.get("title") or raw_data["id"]),
        "brief": {
            "title": str(brief["title"]),
            "research_question": str(brief["research_question"]),
            "constraints": brief.get("constraints"),
            "desired_depth": brief.get("desired_depth"),
            "expected_outputs": brief.get("expected_outputs"),
            "notes": brief.get("notes"),
        },
        "fixture_sources": normalized_sources,
        "relevant_source_ids": [str(item) for item in relevant_source_ids],
        "irrelevant_source_ids": [str(item) for item in irrelevant_source_ids],
        "expected_claim_traits": [str(item) for item in list(raw_data.get("expected_claim_traits") or [])],
        "expected_theme_traits": [str(item) for item in list(raw_data.get("expected_theme_traits") or [])],
        "expected_candidate_traits": [str(item) for item in list(raw_data.get("expected_candidate_traits") or [])],
        "forbidden_claim_patterns": [str(item) for item in list(raw_data.get("forbidden_claim_patterns") or [])],
        "rubric_metadata": dict(raw_data.get("rubric_metadata") or {}),
        "simulated_execution": {
            "attempts_by_phase": dict(simulated_execution.get("attempts_by_phase") or {}),
            "phase_batches": phase_batches,
        },
    }


def _build_fixture_packet(case: dict[str, Any], fixtures_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sources: list[dict[str, Any]] = []
    excerpts: list[dict[str, Any]] = []
    pages_dir = fixtures_dir / "pages"
    for item in case["fixture_sources"]:
        fixture_path = pages_dir / item["path"]
        raw_body = fixture_path.read_bytes()
        content_type = "text/html" if fixture_path.suffix.lower() == ".html" else "text/plain"
        extracted_title, extracted_text, extraction_error = extract_title_and_text(raw_body, content_type)
        title = str(item.get("title") or extracted_title or item["id"])
        excerpt_text = (extracted_text or title).strip()
        source_id = item["id"]
        excerpt_id = f"{source_id}::excerpt"
        parsed_url = parse.urlsplit(item["url"])
        sources.append(
            {
                "id": source_id,
                "title": title,
                "source_type": item["source_type"],
                "url": item["url"],
                "origin": parsed_url.hostname,
                "summary": excerpt_text[:400],
                "metadata_json": {
                    "fixture_case_id": case["id"],
                    "fixture_path": item["path"],
                    "relevant": item["relevant"],
                    "extraction_error": extraction_error,
                },
            }
        )
        excerpts.append(
            {
                "id": excerpt_id,
                "source_id": source_id,
                "excerpt_text": excerpt_text,
                "location_reference": item["path"],
                "excerpt_type": item["excerpt_type"],
                "metadata_json": {
                    "fixture_case_id": case["id"],
                    "fixture_source_id": source_id,
                },
            }
        )
    return sources, excerpts


def _import_package_for_eval(package) -> dict[str, Any]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_cls = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    try:
        with session_cls() as db:
            import_result = import_agent_draft_package(
                db,
                package,
                package_path=None,
                allow_duplicate_external_id=True,
            )
            return {
                "run_id": import_result.run_db_id,
                "warnings": list(import_result.warnings),
                "imported_source_count": import_result.imported_source_count,
                "imported_excerpt_count": import_result.imported_excerpt_count,
                "imported_claim_count": import_result.imported_claim_count,
                "imported_theme_count": import_result.imported_theme_count,
                "imported_candidate_count": import_result.imported_candidate_count,
                "imported_validation_gate_count": import_result.imported_validation_gate_count,
                "imported_evidence_link_count": import_result.imported_evidence_link_count,
            }
    finally:
        engine.dispose()


def _score_case(
    case: dict[str, Any],
    *,
    package_data: dict[str, Any],
    known_source_ids: set[str],
    known_excerpt_ids: set[str],
    attempts_by_phase: dict[str, int],
    validation_success: bool,
    import_summary: dict[str, Any] | None,
    runtime_seconds: float,
    warnings: list[str],
) -> dict[str, Any]:
    valid_link_count = 0
    unknown_reference_count = 0
    claim_support: dict[str, int] = {str(item.get("id")): 0 for item in package_data.get("claims", [])}
    for link in package_data.get("evidence_links", []):
        if not isinstance(link, dict):
            continue
        source_id = link.get("source_id")
        excerpt_id = link.get("excerpt_id")
        source_ok = source_id is None or str(source_id) in known_source_ids
        excerpt_ok = excerpt_id is None or str(excerpt_id) in known_excerpt_ids
        if not source_ok:
            unknown_reference_count += 1
        if not excerpt_ok:
            unknown_reference_count += 1
        if source_ok and excerpt_ok:
            valid_link_count += 1
            if str(link.get("target_type") or "") == "claim" and str(link.get("relationship") or "") == "supports":
                target_id = str(link.get("target_id") or "")
                if target_id in claim_support:
                    claim_support[target_id] += 1

    claims = [str(item.get("statement") or "") for item in package_data.get("claims", []) if isinstance(item, dict)]
    themes = [" ".join(filter(None, [str(item.get("name") or ""), str(item.get("summary") or "")])).strip() for item in package_data.get("themes", []) if isinstance(item, dict)]
    candidates = [
        " ".join(
            filter(
                None,
                [
                    str(item.get("title") or ""),
                    str(item.get("summary") or ""),
                    str(item.get("target_user") or ""),
                    str(item.get("first_workflow") or ""),
                    str(item.get("first_wedge") or ""),
                ],
            )
        ).strip()
        for item in package_data.get("candidates", [])
        if isinstance(item, dict)
    ]
    claim_coverage = _trait_coverage(case["expected_claim_traits"], claims)
    theme_coverage = _trait_coverage(case["expected_theme_traits"], themes)
    candidate_coverage = _trait_coverage(case["expected_candidate_traits"], candidates)
    forbidden_hits = _forbidden_claim_hits(case["forbidden_claim_patterns"], claims)
    unsupported_claim_count = sum(1 for count in claim_support.values() if count == 0)
    retry_count = sum(max(int(value) - 1, 0) for value in attempts_by_phase.values())

    return {
        "import_success": bool(import_summary),
        "schema_validation_success": validation_success,
        "valid_source_links": valid_link_count,
        "unknown_source_reference_count": unknown_reference_count,
        "unsupported_claim_count": unsupported_claim_count,
        "expected_claim_trait_coverage": claim_coverage["coverage"],
        "matched_claim_traits": claim_coverage["matched_traits"],
        "expected_theme_trait_coverage": theme_coverage["coverage"],
        "matched_theme_traits": theme_coverage["matched_traits"],
        "expected_candidate_trait_coverage": candidate_coverage["coverage"],
        "matched_candidate_traits": candidate_coverage["matched_traits"],
        "forbidden_claim_hit_count": forbidden_hits,
        "schema_error_count": 0 if validation_success else 1,
        "retry_count": retry_count,
        "attempts_by_phase": attempts_by_phase,
        "runtime_seconds": round(runtime_seconds, 4),
        "import_warning_count": len(warnings),
    }


def _trait_coverage(expected_traits: list[str], texts: list[str]) -> dict[str, Any]:
    if not expected_traits:
        return {"coverage": 1.0, "matched_traits": []}
    haystack = "\n".join(texts).lower()
    matched = [trait for trait in expected_traits if trait.lower() in haystack]
    coverage = len(matched) / len(expected_traits)
    return {"coverage": round(coverage, 3), "matched_traits": matched}


def _forbidden_claim_hits(patterns: list[str], claims: list[str]) -> int:
    lowered_claims = [claim.lower() for claim in claims]
    hits = 0
    for pattern in patterns:
        lowered = pattern.lower()
        if any(lowered in claim for claim in lowered_claims):
            hits += 1
    return hits


def _build_score_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "import_success": 1.0 if metrics["import_success"] else 0.0,
        "schema_validation_success": 1.0 if metrics["schema_validation_success"] else 0.0,
        "source_link_integrity": 1.0 if metrics["unknown_source_reference_count"] == 0 else 0.0,
        "claim_support": 1.0 if metrics["unsupported_claim_count"] == 0 else 0.0,
        "expected_claim_trait_coverage": float(metrics["expected_claim_trait_coverage"]),
        "expected_theme_trait_coverage": float(metrics["expected_theme_trait_coverage"]),
        "expected_candidate_trait_coverage": float(metrics["expected_candidate_trait_coverage"]),
        "forbidden_claim_safety": 1.0 if metrics["forbidden_claim_hit_count"] == 0 else 0.0,
    }
    overall_score = round(sum(normalized.values()) / len(normalized), 3)
    passed_checks = sorted(name for name, value in normalized.items() if value >= 1.0)
    failed_checks = sorted(name for name, value in normalized.items() if value < 1.0)
    return {
        "overall_score": overall_score,
        "normalized_metrics": normalized,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
    }


def _build_aggregate_summary(case_results: list[CaseRunResult]) -> dict[str, Any]:
    case_dicts = [item.result for item in case_results]
    case_count = len(case_dicts)
    average_overall_score = round(
        sum(float(item["score_summary"]["overall_score"]) for item in case_dicts) / case_count,
        3,
    )
    return {
        "case_count": case_count,
        "import_success_count": sum(1 for item in case_dicts if item["metrics"]["import_success"]),
        "schema_validation_success_count": sum(1 for item in case_dicts if item["metrics"]["schema_validation_success"]),
        "average_overall_score": average_overall_score,
        "average_expected_claim_trait_coverage": _average_metric(case_dicts, "expected_claim_trait_coverage"),
        "average_expected_theme_trait_coverage": _average_metric(case_dicts, "expected_theme_trait_coverage"),
        "average_expected_candidate_trait_coverage": _average_metric(case_dicts, "expected_candidate_trait_coverage"),
        "total_unknown_source_reference_count": sum(int(item["metrics"]["unknown_source_reference_count"]) for item in case_dicts),
        "total_forbidden_claim_hit_count": sum(int(item["metrics"]["forbidden_claim_hit_count"]) for item in case_dicts),
        "total_retry_count": sum(int(item["metrics"]["retry_count"]) for item in case_dicts),
        "status_counts": _status_counts(case_dicts),
    }


def _average_metric(case_dicts: list[dict[str, Any]], metric_name: str) -> float:
    if not case_dicts:
        return 0.0
    return round(sum(float(item["metrics"][metric_name]) for item in case_dicts) / len(case_dicts), 3)


def _status_counts(case_dicts: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in case_dicts:
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()