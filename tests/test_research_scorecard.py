from __future__ import annotations

import json
from pathlib import Path

import pytest

from apd.evals.research_scorecard import build_research_scorecard_report, expand_result_paths, load_eval_result_file, render_scorecard_markdown, write_scorecard_artifacts
from scripts.run_research_scorecard import main as run_scorecard_main


def _make_case(
    case_id: str,
    *,
    status: str = "imported",
    import_success: bool = True,
    schema_success: bool = True,
    valid_links: int = 1,
    unknown_refs: int = 0,
    claim_cov: float = 1.0,
    theme_cov: float = 1.0,
    candidate_cov: float = 1.0,
    forbidden_hits: int = 0,
    retry_count: int = 0,
    attempts_by_phase: dict[str, int] | None = None,
    runtime_seconds: float = 0.02,
    overall_score: float = 1.0,
) -> dict:
    return {
        "id": case_id,
        "status": status,
        "execution": {
            "mode": "fixture_only",
            "provider": "fixture-mocked",
            "model": "synthetic-model",
            "harness": "synthetic-runner",
            "attempts_by_phase": attempts_by_phase or {"candidate_batch": 1, "claim_theme_batch": 1},
            "retry_count": retry_count,
        },
        "metrics": {
            "import_success": import_success,
            "schema_validation_success": schema_success,
            "valid_source_links": valid_links,
            "unknown_source_reference_count": unknown_refs,
            "expected_claim_trait_coverage": claim_cov,
            "expected_theme_trait_coverage": theme_cov,
            "expected_candidate_trait_coverage": candidate_cov,
            "forbidden_claim_hit_count": forbidden_hits,
            "retry_count": retry_count,
            "attempts_by_phase": attempts_by_phase or {"candidate_batch": 1, "claim_theme_batch": 1},
            "runtime_seconds": runtime_seconds,
        },
        "score_summary": {"overall_score": overall_score},
    }


def _write_result(path: Path, *, model: str, runner: str, cases: list[dict]) -> Path:
    payload = {
        "schema_version": "1.0",
        "generated_at": "2026-04-29T00:00:00+00:00",
        "harness": {
            "mode": "fixture_only",
            "runner": runner,
            "model": model,
            "started_at": "2026-04-29T00:00:00+00:00",
        },
        "cases": cases,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_load_eval_result_file_requires_expected_fields(tmp_path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required fields"):
        load_eval_result_file(bad_path)


def test_build_research_scorecard_report_aggregates_one_file(tmp_path):
    result_path = _write_result(
        tmp_path / "one.json",
        model="qwen3:14b",
        runner="apd-research-eval-fixture-v1",
        cases=[
            _make_case("case-a", runtime_seconds=0.01, overall_score=0.8),
            _make_case("case-b", unknown_refs=1, claim_cov=0.5, forbidden_hits=1, runtime_seconds=0.03, overall_score=0.6),
        ],
    )

    report = build_research_scorecard_report([result_path])
    scorecard = report["scorecards"][0]

    assert scorecard["model"] == "qwen3:14b"
    assert scorecard["runner_label"] == "apd-research-eval-fixture-v1"
    assert scorecard["eval_case_count"] == 2
    assert scorecard["import_success_rate"] == 1.0
    assert scorecard["unknown_reference_rate"] == 0.333
    assert scorecard["forbidden_claim_hits"] == 1
    assert scorecard["median_runtime_seconds"] == 0.02


def test_build_research_scorecard_report_compares_two_files(tmp_path):
    baseline = _write_result(
        tmp_path / "baseline.json",
        model="model-a",
        runner="runner-a",
        cases=[_make_case("case-a", overall_score=0.5, unknown_refs=1, runtime_seconds=0.02, retry_count=1)],
    )
    candidate = _write_result(
        tmp_path / "candidate.json",
        model="model-b",
        runner="runner-b",
        cases=[_make_case("case-a", overall_score=0.9, unknown_refs=0, runtime_seconds=0.01, retry_count=0)],
    )

    report = build_research_scorecard_report([baseline, candidate])
    comparison = report["comparison"]

    assert comparison["baseline"]["model"] == "model-a"
    assert comparison["deltas_vs_first"][0]["label"] == "model-b / runner-b"
    assert comparison["deltas_vs_first"][0]["delta_average_overall_score"] == 0.4
    assert comparison["deltas_vs_first"][0]["delta_unknown_reference_rate"] == -0.5


def test_render_scorecard_markdown_and_write_artifacts(tmp_path):
    result_path = _write_result(
        tmp_path / "one.json",
        model="model-a",
        runner="runner-a",
        cases=[_make_case("case-a", status="validation_failed", import_success=False, schema_success=False, overall_score=0.2)],
    )
    report = build_research_scorecard_report([result_path])

    markdown = render_scorecard_markdown(report)
    assert "| model | runner |" in markdown
    assert "case status counts" in markdown
    assert "failure breakdown uses case status counts" in markdown

    written = write_scorecard_artifacts(
        report,
        out_json=tmp_path / "scorecard.json",
        out_md=tmp_path / "scorecard.md",
    )
    assert Path(written["json"]).exists()
    assert Path(written["markdown"]).exists()


def test_expand_result_paths_and_cli_stdout(tmp_path, capsys):
    first = _write_result(tmp_path / "a.json", model="model-a", runner="runner-a", cases=[_make_case("case-a")])
    second = _write_result(tmp_path / "b.json", model="model-b", runner="runner-b", cases=[_make_case("case-b")])

    paths = expand_result_paths([str(tmp_path / "*.json")])
    assert paths == sorted([first.resolve(), second.resolve()])

    exit_code = run_scorecard_main(["--results", str(tmp_path / "*.json")])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "| model | runner |" in captured.out
    assert "## Comparison" in captured.out


def test_build_research_scorecard_report_errors_when_no_results_supplied():
    with pytest.raises(ValueError, match="at least one eval result file"):
        build_research_scorecard_report([])