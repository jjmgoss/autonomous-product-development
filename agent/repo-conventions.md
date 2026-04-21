# Repo Conventions

These conventions keep autonomous work legible and reviewable.

## General

- Keep the repository understandable by a single human reviewer.
- Prefer plain language in docs.
- Keep filenames predictable.
- Update existing docs rather than creating near-duplicates.

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
