# Product Skill: First-Run Discovery

## Goal

Run a discovery-first pass that produces a ranked set of candidate opportunities without rushing into implementation.

The discovery run should produce a bounded, fully completed review package, not a sprawling research archive or a premature codebase.

## When to use

- a fresh discovery pass for the current theme
- any run where the goal is to discover what to build next
- any run where the current opportunity set is weak or stale

## Procedure

1. Read `theme.md` carefully and extract the preferred product profile.
2. Read `START_HERE.md`, `ACTIVE_RUN.md`, and `DISCOVERY_RUN_MODE.md`.
3. Run `python scripts/start_discovery_run.py` to create the run directory structure, including `artifacts/runs/<run-id>/review-package/`.
4. Use the research skill to identify repeated pain and workflow friction.
5. Keep the saved corpus bounded and auditable.
6. Generate candidate wedges from the strongest pain patterns.
7. Limit the serious candidate set to at most 5 ideas and the detailed scorecard to the top 3.
8. Score the candidates in `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`.
9. Use monetization, substitute, and agent-operability skills on the top few candidates.
10. Create `artifacts/runs/<run-id>/review-package/candidate-review.md` for human review.
11. Create `artifacts/runs/<run-id>/reports/discovery-summary.md` and `artifacts/runs/<run-id>/run-index.md`.
12. Decide whether one candidate earns a go decision, more validation, or no-go.
13. Run `python scripts/check_repo_readiness.py --run-id <run-id>` before stopping.

## Required outputs

- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`
- `artifacts/runs/<run-id>/manifest.json`
- `artifacts/runs/<run-id>/run-index.md`
- `artifacts/runs/<run-id>/review-package/research.md`
- `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- `artifacts/runs/<run-id>/review-package/candidate-review.md`
- `artifacts/runs/<run-id>/review-package/validation.md`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`

## Default rule

A first run should usually stop after ranking and recommendation unless one idea clearly earns a narrow, evidence-backed go decision.

If a human has not explicitly approved moving forward, the review package is the endpoint.

## Completion rule

The package is not complete if:

- placeholders remain
- unresolved prompts remain
- only one candidate is meaningfully developed
- the ranking is not traceable to saved evidence IDs
- the run checker fails

## Common failure modes

- treating the first plausible idea as the winner
- starting implementation because building feels more concrete than discovery
- producing a long candidate list with no hard ranking or recommendation
- collecting weak source volume instead of strong evidence density
- making claims that are not traceable to saved source IDs
- editing reusable docs in place instead of writing the run-scoped review package
