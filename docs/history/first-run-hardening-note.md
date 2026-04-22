# First-Run Hardening Note

Archived historical note from the first template/output cleanup pass.
The current operating answer to this problem is the run-scoped review package plus the canonical bootstrap layer.

## Likely causes of the first-run template/output failure

- The framework told the model to use `docs/` both as reusable guidance and as the canonical first-run deliverable location.
- The artifact tree only required a thin summary, so the run could appear complete even when the real review package was scattered or underdeveloped.
- Completion language emphasized file presence more than artifact completeness, making it too easy to stop with template scaffolding still present.

## Where output placement was ambiguous

- `FIRST_RUN_MODE.md`, `FIRST_RUN_PROMPT.md`, the runbook, and discovery skills all named `docs/research.md`, `docs/opportunity-scorecard.md`, `docs/candidate-review.md`, and `docs/validation.md` as final run outputs.
- `artifacts/runs/<run-id>/` existed, but only as a place for summaries and loose outputs rather than the canonical reviewer package.
- Human-gate guidance pointed reviewers at scattered files instead of one run-root entry point.

## Stricter completion contract needed for the next run

- Treat `docs/` as reusable guides, not final Gate 1 deliverables.
- Require a run-scoped review package plus a run index under `artifacts/runs/<run-id>/`.
- Reject completion when placeholders, unresolved prompts, blank sections, missing manifests, weak candidate comparison, or shallow evidence linkage remain.
- Require the checker to validate both pre-run framework readiness and post-run package completeness.