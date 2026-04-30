from __future__ import annotations

import argparse

from apd.evals.research_runner import render_eval_summary_table, run_fixture_research_evals


def main() -> int:
    parser = argparse.ArgumentParser(description="Run APD research eval harness against fixture cases.")
    parser.add_argument("--fixture-only", action="store_true", help="Run the deterministic fixture-only harness.")
    parser.add_argument("--model-label", default="fixture-mocked", help="Label to record in eval output for the mocked model.")
    parser.add_argument(
        "--harness-label",
        default="apd-research-eval-fixture-v1",
        help="Label to record in eval output for the harness configuration.",
    )
    args = parser.parse_args()

    output = run_fixture_research_evals(
        fixture_only=args.fixture_only,
        model_label=args.model_label,
        harness_label=args.harness_label,
        write_results=True,
    )
    print(render_eval_summary_table(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())