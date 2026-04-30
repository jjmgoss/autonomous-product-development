from __future__ import annotations

import json
from pathlib import Path

from apd.evals.research_runner import load_research_eval_cases, render_eval_summary_table, run_fixture_research_evals


def test_run_fixture_research_evals_scores_cases_and_writes_json(tmp_path):
    output = run_fixture_research_evals(results_dir=tmp_path, fixture_only=True, write_results=True)

    assert output["aggregate"]["case_count"] >= 3
    assert output["aggregate"]["import_success_count"] == output["aggregate"]["case_count"]
    assert output["aggregate"]["total_unknown_source_reference_count"] == 1
    assert output["aggregate"]["total_forbidden_claim_hit_count"] == 1

    cases = {item["id"]: item for item in output["cases"]}
    assert cases["maintenance_handoff"]["metrics"]["retry_count"] == 0
    assert cases["solo_operator_maintenance"]["metrics"]["retry_count"] == 1
    assert cases["hiring_feedback_loop"]["metrics"]["unknown_source_reference_count"] == 1
    assert cases["hiring_feedback_loop"]["metrics"]["forbidden_claim_hit_count"] == 1

    results_path = Path(output["results_path"])
    assert results_path.exists()
    persisted = json.loads(results_path.read_text(encoding="utf-8"))
    assert persisted["aggregate"]["case_count"] == output["aggregate"]["case_count"]

    summary = render_eval_summary_table(output)
    assert "Aggregate" in summary
    assert "maintenance_handoff" in summary


def test_load_research_eval_cases_returns_expected_case_shape():
    cases = load_research_eval_cases()
    assert len(cases) >= 3
    assert all(case["brief"]["title"] for case in cases)
    assert all(case["simulated_execution"]["phase_batches"] for case in cases)