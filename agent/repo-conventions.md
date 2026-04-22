# Repo Conventions

These conventions keep autonomous work legible and reviewable.

## General

- Keep the repository understandable by a single human reviewer.
- Prefer plain language in docs.
- Keep filenames predictable.
- Update existing docs rather than creating near-duplicates.
- Route startup through `START_HERE.md` and `ACTIVE_RUN.md` instead of scattering launch behavior.

## Operating-surface map

- Active operating surface: `START_HERE.md`, `ACTIVE_RUN.md`, the boundary and prompt files named there, `agent/`, `scripts/`, and `templates/`.
- Supporting reference: reusable guides in `docs/` and skill files under `skills/`.
- Historical reference: `docs/history/`.
- Avoid leaving compatibility aliases or migration notes at the repo root when they are no longer part of the active path.

## Artifact roles

Use the docs for clearly different purposes:

- `docs/research.md` defines the reusable structure for a discovery-run research artifact and later becomes a living project doc after a go decision.
- `docs/opportunity-scorecard.md` defines the reusable scoring frame and later-stage comparison rules.
- `docs/candidate-review.md` defines the reusable reviewer-facing comparison structure.
- `docs/validation.md` defines the reusable validation argument structure.
- `docs/product-brief.md` defines the reusable selected-product structure for post-Gate-1 work.

During a discovery run, the canonical final outputs live here instead:

- `artifacts/runs/<run-id>/run-index.md`
- `artifacts/runs/<run-id>/review-package/research.md`
- `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- `artifacts/runs/<run-id>/review-package/candidate-review.md`
- `artifacts/runs/<run-id>/review-package/validation.md`
- `artifacts/runs/<run-id>/review-package/product-brief.md` only if one candidate earns a go-now recommendation

Use the non-doc output directories for clearly different purposes:

- `research-corpus/` stores saved evidence, normalized text, and source notes.
- `artifacts/runs/` stores run-scoped generated reports, the review package, evaluations, exports, and a reviewer-facing run index.
- `artifacts/projects/` stores generated product code only after a go decision and human approval.

## Run naming

Use `YYYYMMDD-theme-slug-rN` for run IDs.

Use `python scripts/start_discovery_run.py` when discovery mode is active unless a human explicitly provides a run ID.

Use the same run ID in:

- `research-corpus/runs/<run-id>/`
- `artifacts/runs/<run-id>/`
- any reviewer-facing run summary

Never reuse an existing run ID by default.
If a collision exists, increment `rN` until both run roots are unused.
Prefer theme-derived slugs over manual hints. Only use an override when the human intentionally wants a different slug.

## Decision logging

Every significant decision should include:

- context
- options considered
- chosen option
- why it won
- what remains uncertain
- whether the decision is reversible

Record these in `docs/decision-log.md`.

## Work logging

Record meaningful progress in `docs/work-log.md`.
Focus on changes in understanding, code, risk, and verification.
Do not spam it with trivial edits.

## Backlog hygiene

`docs/backlog.md` should distinguish between:

- active work
- deferred work
- rejected work
- technical debt
- future experiments

Research and validation tasks may stay in the backlog if they are the critical path to a go/no-go decision.

## Implementation style

- Prefer narrow vertical slices.
- Avoid speculative abstractions.
- Keep architecture simple until pain is proven.
- Do not create broad infra before the MVP needs it.

## Verification style

- Tests are evidence, not decoration.
- Smoke checks count, but only if actually run.
- Known gaps must be written down.
- Never say "done" when "partially working" is more accurate.

## Discovery style

- Do not let candidate ideas blur together.
- Always separate raw evidence from your interpretation of it.
- Give saved evidence stable IDs and cite them in high-stakes claims.
- Use the run index to connect the human reviewer to the right files without requiring repo archaeology.
- Surface the strongest source URLs directly in reviewer-facing artifacts.
- Name substitutes explicitly, including spreadsheets, manual workarounds, and incumbent tools.
- If a product looks buildable but weakly monetizable, say so.
- If a product is commercially interesting but operationally unrealistic for an agent-led build, say so.

## Discovery review-package rule

For a discovery run, do not write the final reviewer package into `docs/`.
Those files are framework guidance.
The completed Checkpoint 1 package must live inside the run-specific artifact directory.
