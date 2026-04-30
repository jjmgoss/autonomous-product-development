from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import glob
import json
from pathlib import Path
from statistics import median
from typing import Any


_GLOB_CHARS = set("*?[]")
REQUIRED_TOP_LEVEL_FIELDS = {"generated_at", "harness", "cases"}
REQUIRED_HARNESS_FIELDS = {"model", "runner"}
REQUIRED_CASE_FIELDS = {"id", "status", "execution", "metrics"}


@dataclass(frozen=True)
class LoadedEvalResult:
    path: Path
    data: dict[str, Any]


def expand_result_paths(patterns: list[str]) -> list[Path]:
    resolved: list[Path] = []
    for pattern in patterns:
        raw_pattern = str(pattern or "").strip()
        if not raw_pattern:
            continue
        if any(char in raw_pattern for char in _GLOB_CHARS):
            matches = sorted(Path(match).resolve() for match in glob.glob(raw_pattern))
            resolved.extend(matches)
            continue
        path = Path(raw_pattern)
        if path.is_file():
            resolved.append(path.resolve())
            continue
        raise ValueError(f"Result file does not exist: {raw_pattern}")

    unique_paths = sorted(dict.fromkeys(resolved))
    if not unique_paths:
        raise ValueError("No eval result files matched the provided --results patterns.")
    return unique_paths


def load_eval_result_file(path: Path) -> LoadedEvalResult:
    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Result file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in result file {path}: line {exc.lineno} column {exc.colno}") from exc

    if not isinstance(raw_data, dict):
        raise ValueError(f"Eval result file must be a JSON object: {path}")

    missing_top_level = sorted(field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in raw_data)
    if missing_top_level:
        raise ValueError(f"Eval result file {path} is missing required fields: {', '.join(missing_top_level)}")

    harness = raw_data.get("harness")
    if not isinstance(harness, dict):
        raise ValueError(f"Eval result file {path} has invalid harness metadata.")
    missing_harness = sorted(field for field in REQUIRED_HARNESS_FIELDS if field not in harness or not harness.get(field))
    if missing_harness:
        raise ValueError(f"Eval result file {path} is missing harness fields: {', '.join(missing_harness)}")

    cases = raw_data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"Eval result file {path} must contain a non-empty cases list.")
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Eval result file {path} case #{index} must be an object.")
        missing_case = sorted(field for field in REQUIRED_CASE_FIELDS if field not in case)
        if missing_case:
            raise ValueError(
                f"Eval result file {path} case #{index} is missing required fields: {', '.join(missing_case)}"
            )

    return LoadedEvalResult(path=path.resolve(), data=raw_data)


def build_research_scorecard_report(result_paths: list[str] | list[Path]) -> dict[str, Any]:
    loaded_results = [load_eval_result_file(path if isinstance(path, Path) else Path(path)) for path in _coerce_paths(result_paths)]
    summaries = [summarize_eval_result(loaded) for loaded in loaded_results]
    report = {
        "schema_version": "1.0",
        "generated_at": _iso_now(),
        "scorecards": summaries,
        "comparison": _build_comparison_section(summaries),
    }
    return report


def summarize_eval_result(loaded: LoadedEvalResult) -> dict[str, Any]:
    data = loaded.data
    harness = dict(data.get("harness") or {})
    cases = list(data.get("cases") or [])
    case_count = len(cases)

    total_valid_source_links = sum(_metric_number(case, "valid_source_links") for case in cases)
    total_unknown_references = sum(_metric_number(case, "unknown_source_reference_count") for case in cases)
    total_reference_events = total_valid_source_links + total_unknown_references
    valid_source_link_rate = 1.0 if total_reference_events == 0 else round(total_valid_source_links / total_reference_events, 3)
    unknown_reference_rate = 0.0 if total_reference_events == 0 else round(total_unknown_references / total_reference_events, 3)

    average_attempts_by_phase = _average_attempts_by_phase(cases)
    summary = {
        "model": str(harness.get("model") or _first_execution_value(cases, "model") or "unknown"),
        "runner_label": str(harness.get("runner") or _first_execution_value(cases, "harness") or "unknown"),
        "mode": str(harness.get("mode") or _first_execution_value(cases, "mode") or "unknown"),
        "result_file_path": str(loaded.path),
        "generated_at": str(data.get("generated_at") or ""),
        "eval_case_count": case_count,
        "import_success_rate": _rate(cases, lambda case: bool(_metric_bool(case, "import_success"))),
        "schema_validation_success_rate": _rate(cases, lambda case: bool(_metric_bool(case, "schema_validation_success"))),
        "valid_source_link_rate": valid_source_link_rate,
        "unknown_reference_rate": unknown_reference_rate,
        "expected_claim_trait_coverage": _average_metric(cases, "expected_claim_trait_coverage"),
        "expected_theme_trait_coverage": _average_metric(cases, "expected_theme_trait_coverage"),
        "expected_candidate_trait_coverage": _average_metric(cases, "expected_candidate_trait_coverage"),
        "forbidden_claim_hits": int(sum(_metric_number(case, "forbidden_claim_hit_count") for case in cases)),
        "average_retry_count": _average_metric(cases, "retry_count"),
        "average_attempts_by_phase": average_attempts_by_phase,
        "median_runtime_seconds": _median_metric(cases, "runtime_seconds"),
        "status_counts": _status_counts(cases),
        "average_overall_score": _average_overall_score(cases, data.get("aggregate")),
        "approximations": {
            "grounded_evidence_link_validity": "Computed from total valid_source_links divided by valid_source_links plus unknown_source_reference_count across cases.",
            "failure_breakdown": "Uses case status counts because the #72 result schema does not persist a separate phase-failure histogram.",
        },
    }
    return summary


def render_scorecard_markdown(report: dict[str, Any]) -> str:
    scorecards = list(report.get("scorecards") or [])
    lines = [
        "| model | runner | cases | import | schema | valid links | unknown refs | claim cov | theme cov | candidate cov | forbidden | avg retries | median runtime | avg score |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for scorecard in scorecards:
        lines.append(
            "| {model} | {runner} | {cases} | {import_rate} | {schema_rate} | {valid_rate} | {unknown_rate} | {claim_cov} | {theme_cov} | {candidate_cov} | {forbidden} | {avg_retries} | {median_runtime} | {avg_score} |".format(
                model=scorecard["model"],
                runner=scorecard["runner_label"],
                cases=scorecard["eval_case_count"],
                import_rate=_pct(scorecard["import_success_rate"]),
                schema_rate=_pct(scorecard["schema_validation_success_rate"]),
                valid_rate=_pct(scorecard["valid_source_link_rate"]),
                unknown_rate=_pct(scorecard["unknown_reference_rate"]),
                claim_cov=_pct(scorecard["expected_claim_trait_coverage"]),
                theme_cov=_pct(scorecard["expected_theme_trait_coverage"]),
                candidate_cov=_pct(scorecard["expected_candidate_trait_coverage"]),
                forbidden=scorecard["forbidden_claim_hits"],
                avg_retries=_fmt_number(scorecard["average_retry_count"]),
                median_runtime=_fmt_number(scorecard["median_runtime_seconds"], digits=4),
                avg_score=_fmt_number(scorecard["average_overall_score"]),
            )
        )

    for scorecard in scorecards:
        lines.extend(
            [
                "",
                f"### {scorecard['model']} / {scorecard['runner_label']}",
                f"- result file: {scorecard['result_file_path']}",
                f"- generated_at: {scorecard['generated_at']}",
                f"- mode: {scorecard['mode']}",
                f"- case status counts: {_render_mapping(scorecard['status_counts'])}",
                f"- average attempts by phase: {_render_mapping(scorecard['average_attempts_by_phase'])}",
            ]
        )

    comparison = dict(report.get("comparison") or {})
    deltas = list(comparison.get("deltas_vs_first") or [])
    if deltas:
        lines.extend(
            [
                "",
                "## Comparison",
                "| candidate | delta avg score | delta import | delta unknown refs | delta avg retries |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for delta in deltas:
            lines.append(
                "| {label} | {avg_score} | {import_rate} | {unknown_rate} | {avg_retries} |".format(
                    label=delta["label"],
                    avg_score=_signed(delta["delta_average_overall_score"]),
                    import_rate=_signed_pct(delta["delta_import_success_rate"]),
                    unknown_rate=_signed_pct(delta["delta_unknown_reference_rate"]),
                    avg_retries=_signed(delta["delta_average_retry_count"]),
                )
            )

    lines.extend(
        [
            "",
            "## Notes",
            "- grounded evidence link validity is approximated from valid source links versus unknown source or excerpt reference counts emitted by the #72 eval runner",
            "- failure breakdown uses case status counts because #72 does not yet persist a dedicated per-phase failure histogram in the result JSON",
        ]
    )
    return "\n".join(lines)


def write_scorecard_artifacts(report: dict[str, Any], *, out_json: Path | None = None, out_md: Path | None = None) -> dict[str, str]:
    written: dict[str, str] = {}
    if out_json is not None:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        written["json"] = str(out_json.resolve())
    if out_md is not None:
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(render_scorecard_markdown(report), encoding="utf-8")
        written["markdown"] = str(out_md.resolve())
    return written


def _coerce_paths(result_paths: list[str] | list[Path]) -> list[Path]:
    if not result_paths:
        raise ValueError("Provide at least one eval result file with --results.")
    raw_patterns = [str(path) for path in result_paths]
    return expand_result_paths(raw_patterns)


def _build_comparison_section(scorecards: list[dict[str, Any]]) -> dict[str, Any]:
    if len(scorecards) < 2:
        return {"baseline": None, "deltas_vs_first": []}
    baseline = scorecards[0]
    deltas: list[dict[str, Any]] = []
    for scorecard in scorecards[1:]:
        deltas.append(
            {
                "label": f"{scorecard['model']} / {scorecard['runner_label']}",
                "delta_average_overall_score": round(scorecard["average_overall_score"] - baseline["average_overall_score"], 3),
                "delta_import_success_rate": round(scorecard["import_success_rate"] - baseline["import_success_rate"], 3),
                "delta_unknown_reference_rate": round(scorecard["unknown_reference_rate"] - baseline["unknown_reference_rate"], 3),
                "delta_average_retry_count": round(scorecard["average_retry_count"] - baseline["average_retry_count"], 3),
            }
        )
    return {
        "baseline": {
            "model": baseline["model"],
            "runner_label": baseline["runner_label"],
            "result_file_path": baseline["result_file_path"],
        },
        "deltas_vs_first": deltas,
    }


def _average_attempts_by_phase(cases: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for case in cases:
        attempts = dict(_metric_mapping(case, "attempts_by_phase"))
        for phase, value in attempts.items():
            totals[str(phase)] = totals.get(str(phase), 0.0) + float(value)
            counts[str(phase)] = counts.get(str(phase), 0) + 1
    averages: dict[str, float] = {}
    for phase in sorted(totals):
        averages[phase] = round(totals[phase] / counts[phase], 3)
    return averages


def _average_metric(cases: list[dict[str, Any]], metric_name: str) -> float:
    if not cases:
        return 0.0
    return round(sum(_metric_number(case, metric_name) for case in cases) / len(cases), 3)


def _average_overall_score(cases: list[dict[str, Any]], aggregate: Any) -> float:
    if isinstance(aggregate, dict) and aggregate.get("average_overall_score") is not None:
        return round(float(aggregate["average_overall_score"]), 3)
    scores = [float((case.get("score_summary") or {}).get("overall_score") or 0.0) for case in cases]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 3)


def _first_execution_value(cases: list[dict[str, Any]], field_name: str) -> str | None:
    for case in cases:
        execution = case.get("execution")
        if isinstance(execution, dict) and execution.get(field_name):
            return str(execution[field_name])
    return None


def _median_metric(cases: list[dict[str, Any]], metric_name: str) -> float:
    values = [_metric_number(case, metric_name) for case in cases]
    if not values:
        return 0.0
    return round(float(median(values)), 4)


def _metric_bool(case: dict[str, Any], metric_name: str) -> bool:
    metrics = case.get("metrics")
    if not isinstance(metrics, dict):
        return False
    return bool(metrics.get(metric_name))


def _metric_mapping(case: dict[str, Any], metric_name: str) -> dict[str, Any]:
    metrics = case.get("metrics")
    if not isinstance(metrics, dict):
        return {}
    value = metrics.get(metric_name)
    if isinstance(value, dict):
        return value
    return {}


def _metric_number(case: dict[str, Any], metric_name: str) -> float:
    metrics = case.get("metrics")
    if not isinstance(metrics, dict):
        return 0.0
    value = metrics.get(metric_name)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _pct(value: float) -> str:
    return f"{round(float(value) * 100, 1):.1f}%"


def _rate(cases: list[dict[str, Any]], predicate) -> float:
    if not cases:
        return 0.0
    return round(sum(1 for case in cases if predicate(case)) / len(cases), 3)


def _render_mapping(values: dict[str, Any]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}={values[key]}" for key in sorted(values))


def _signed(value: float) -> str:
    return f"{float(value):+.3f}"


def _signed_pct(value: float) -> str:
    return f"{round(float(value) * 100, 1):+.1f}%"


def _status_counts(cases: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in cases:
        status = str(case.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _fmt_number(value: float, *, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()