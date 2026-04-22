# First-Run Setup Summary

This setup pass finished the repo work needed to make the first live discovery run bounded, evidence-backed, and easy to review.

## What was added

- `FIRST_RUN_MODE.md` now defines the default first-run boundary: discovery only, bounded source count, bounded candidate count, and a hard stop at the review package.
- `agent/research-corpus-conventions.md` and `research-corpus/` now define how saved sources, normalized text, source notes, and candidate-to-evidence links should be organized.
- `agent/artifact-output-conventions.md` and `artifacts/` now define where run summaries, evaluations, exports, and later generated projects belong.
- `scripts/check_first_run_readiness.py` now provides a lightweight readiness check before the first live run.
- discovery docs and skills now require stronger evidence linkage through saved source IDs.

## How research corpus handling works now

For each run, create `research-corpus/runs/<run-id>/`.

That run folder should contain:

- `manifest.json` for source metadata
- `raw/` for saved source captures when practical
- `normalized/` for cleaned text or markdown extractions
- `notes/` for short source notes
- `candidate-links.md` for candidate-to-evidence mapping

High-stakes claims in discovery and validation docs should cite the saved evidence IDs from that corpus.

## How artifact production is organized now

Run-scoped outputs belong under `artifacts/runs/<run-id>/`.

Use:

- `reports/` for reviewer-facing summaries
- `evaluations/` for generated scoring or comparison outputs
- `exports/` for transformed data bundles or text exports

Generated software projects belong under `artifacts/projects/` only after a go decision and human approval.

## How first-run safety is enforced

The repo now defaults the first live run to discovery-only behavior.

The boundary layer requires:

- 6 to 12 meaningful saved sources unless a human approves more
- at most 5 candidates, with detailed scoring focused on the top 3
- a reviewer package with research, scorecard, candidate review, validation, corpus manifest, candidate-evidence map, and discovery summary
- a stop after the review package unless a human explicitly approves the next stage

The first live run explicitly does not implement product code, deploy anything, or create noisy external side effects by default.

## How to verify readiness

Run:

```text
python scripts/check_first_run_readiness.py
```

If it prints `READY`, the repo has the required first-run files and directories.

## What to do next

1. Create a fresh branch for the first live discovery pass.
2. Update `theme.md` if the theme needs refinement.
3. Run `python scripts/check_first_run_readiness.py`.
4. Start the agent with `FIRST_RUN_PROMPT.md` and keep `FIRST_RUN_MODE.md` in scope.
5. Review the resulting package at Gate 1 before approving any implementation.