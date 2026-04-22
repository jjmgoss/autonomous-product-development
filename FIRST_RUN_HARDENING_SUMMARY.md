# First-Run Hardening Summary

## What framework weaknesses were fixed

- First-run outputs no longer target reusable docs in place.
- Gate 1 now requires a cohesive run-scoped review package with a reviewer entry point.
- Completion rules now explicitly reject placeholders, unresolved prompts, blank sections, thin summaries, and shallow evidence linkage.
- The checker now validates both framework readiness and completed run-package structure.

## How run outputs are now organized

- Saved evidence remains under `research-corpus/runs/<run-id>/`.
- Reviewer-facing run outputs now live under `artifacts/runs/<run-id>/`.
- `artifacts/runs/<run-id>/run-index.md` is the human entry point.
- `artifacts/runs/<run-id>/review-package/` contains the canonical Gate 1 deliverables.
- `artifacts/runs/<run-id>/reports/discovery-summary.md` remains the concise summary layer.

## How completion is now enforced

- `FIRST_RUN_MODE.md` defines the review-package completion contract.
- Discovery skills and reusable doc guides now direct outputs into the run package.
- The checker rejects missing run outputs, unresolved placeholders, thin artifacts, missing manifest entries, and out-of-bounds source or candidate counts unless an exception is explicitly documented in the run index.

## What the next 4.1 first-run test should do

- Read the operating files.
- Run `python scripts/check_first_run_readiness.py` before starting.
- Produce the full run-scoped Gate 1 package under one run directory.
- Run `python scripts/check_first_run_readiness.py --run-id <run-id>` before stopping.
- Stop at Gate 1 unless a human explicitly approves the next stage.

## How a human should review the resulting run package

1. Open `artifacts/runs/<run-id>/run-index.md`.
2. Read the discovery summary and candidate review first.
3. Use validation and the scorecard to inspect why the winner beat the alternatives.
4. Use the corpus manifest and candidate-evidence map to spot-check traceability.
5. Approve, reject, or request more validation at Gate 1.
