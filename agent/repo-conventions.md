# Repo Conventions

These conventions keep autonomous work legible and reviewable.

## General

- Keep the repository understandable by a single human reviewer.
- Prefer plain language in docs.
- Keep filenames predictable.
- Update existing docs rather than creating near-duplicates.

## Artifact roles

Use the docs for clearly different purposes:

- `docs/research.md` holds evidence, patterns, substitutes, and candidate opportunity seeds.
- `docs/opportunity-scorecard.md` compares candidate ideas using a consistent scoring frame.
- `docs/candidate-review.md` is the reviewer-friendly comparison artifact for the top few candidates.
- `docs/validation.md` determines whether one selected opportunity deserves a go decision.
- `docs/product-brief.md` describes the single selected product direction after the choice is made.

Use the non-doc output directories for clearly different purposes:

- `research-corpus/` stores saved evidence, normalized text, and source notes.
- `artifacts/runs/` stores run-scoped generated reports, evaluations, and exports.
- `artifacts/projects/` stores generated product code only after a go decision and human approval.

## Run naming

Use `YYYYMMDD-theme-slug-rN` for run IDs.

Use the same run ID in:

- `research-corpus/runs/<run-id>/`
- `artifacts/runs/<run-id>/`
- any reviewer-facing run summary

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
- Never say “done” when “partially working” is more accurate.

## Discovery style

- Do not let candidate ideas blur together.
- Always separate raw evidence from your interpretation of it.
- Give saved evidence stable IDs and cite them in high-stakes claims.
- Name substitutes explicitly, including spreadsheets, manual workarounds, and incumbent tools.
- If a product looks buildable but weakly monetizable, say so.
- If a product is commercially interesting but operationally unrealistic for an agent-led build, say so.
