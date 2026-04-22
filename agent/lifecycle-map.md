# Lifecycle Map

This file maps the full lifecycle the agent is expected to cover.

## 1. Discover

Research the focus area and identify concrete user pain, unmet needs, or broken workflows.

Outputs:

- Discovery mode: `artifacts/runs/<run-id>/review-package/research.md` and `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- Later project mode: `docs/research.md` and `docs/opportunity-scorecard.md`

## 2. Select

Choose one narrow opportunity and explain why it is the best prototype target.

Outputs:

- Discovery mode: `artifacts/runs/<run-id>/review-package/candidate-review.md` and optional `artifacts/runs/<run-id>/review-package/product-brief.md`
- Later project mode: `docs/product-brief.md` and scorecard updates

## 3. Validate

Stress-test whether the idea deserves to be built.

Outputs:

- Discovery mode: `artifacts/runs/<run-id>/review-package/validation.md`, `artifacts/runs/<run-id>/reports/discovery-summary.md`, and `artifacts/runs/<run-id>/run-index.md`
- Later project mode: `docs/validation.md` and explicit go/no-go decision

## 4. Define

Translate the product into requirements, architecture, and scope boundaries.

Outputs:

- `docs/requirements.md`
- `docs/design.md`

## 5. Plan

Break the work into milestones, issues, and implementation slices.

Outputs:

- `docs/roadmap.md`
- `docs/backlog.md`

## 6. Build

Implement the product in small verifiable increments.

Outputs:

- code changes
- `docs/work-log.md`
- `docs/decision-log.md`

## 7. Verify

Run tests, smoke checks, and requirement comparison.

Outputs:

- `docs/release.md`
- evidence of checks performed

## 8. Reflect

Decide what to do next.

Outputs:

- `docs/retrospective.md`
- `docs/lifecycle-review.md`
- next-step recommendation

## Cross-cutting lifecycle concerns

These must be considered even if the MVP is small:

- observability
- incident handling
- feedback collection
- deployment readiness
- lifecycle gaps that block real-world use
