# Research Scorecards

APD research scorecards summarize one or more eval result JSON files produced by the fixture-only research eval harness from issue #72.

## Overview

The scorecard tool does not rerun evals.

It reads existing result files, computes aggregate comparisons, prints a markdown-friendly table to stdout, and can optionally write JSON or Markdown artifacts.

Use it when you want to compare:

- two local models against the same eval suite
- one model across two harness revisions
- one harness configuration before and after a prompt or validation change

## Running Scorecards

Compare one or more result files with:

```bash
uv run python scripts/run_research_scorecard.py --results evals/research/results/*.json
```

You can also pass explicit files:

```bash
uv run python scripts/run_research_scorecard.py --results path/to/a.json path/to/b.json
```

Optional artifact output:

```bash
uv run python scripts/run_research_scorecard.py \
  --results evals/research/results/*.json \
  --out-json evals/research/scorecards/latest.json \
  --out-md evals/research/scorecards/latest.md
```

Runtime scorecard artifacts under `evals/research/scorecards/` are ignored by git.

## Loaded Fields

The scorecard loader uses the #72 eval result schema directly.

From each result file it reads:

- top-level `generated_at`
- top-level `harness.model`
- top-level `harness.runner`
- top-level `harness.mode`
- each case `status`
- each case `metrics`
- each case `score_summary.overall_score`

If a result file is missing required fields, the command fails clearly instead of inventing defaults.

## Scorecard Metrics

Each scorecard row includes:

- model
- runner label
- result file path
- generated time
- eval case count
- import success rate
- schema validation success rate
- valid source link rate
- unknown reference rate
- expected claim trait coverage
- expected theme trait coverage
- expected candidate trait coverage
- forbidden claim hits
- average retry count
- average attempts by phase
- median runtime
- case status counts
- average overall score

## Approximations

The #72 result schema is already useful, but it does not separate every future scorecard dimension yet.

Current approximations:

- grounded evidence link validity is computed from `valid_source_links / (valid_source_links + unknown_source_reference_count)` across cases
- unknown reference rate is computed from `unknown_source_reference_count / (valid_source_links + unknown_source_reference_count)` across cases
- failure breakdown is represented as case status counts because the #72 result JSON does not yet persist a dedicated per-phase failure histogram

These approximations are deliberate. The scorecard tool only reports metrics that the eval result JSON can currently support.

## Comparing Runs

When you pass more than one result file, the first file is treated as the baseline.

The comparison section reports deltas for:

- average overall score
- import success rate
- unknown reference rate
- average retry count

Typical workflow:

1. Run evals with one model or harness label.
2. Run evals again with a second model or harness label.
3. Pass both result files to the scorecard script.
4. Compare average score, unknown references, retry count, and status counts.

## Reading the Output

Interpretation guidance:

- higher import and schema success rates are better
- higher valid link rate and lower unknown reference rate are better
- higher trait coverage means the generated output stayed closer to the expected wedge
- fewer forbidden claim hits are better
- lower retry counts usually mean the harness needed fewer repairs to complete the suite
- median runtime helps compare stability and speed without overreacting to outliers

No live web, live model, hosted API, or external service is required for scorecards. They operate entirely on previously generated eval result JSON files.