# Product Skill: First-Run Discovery

## Goal

Run a discovery-first pass that produces a ranked set of candidate opportunities without rushing into implementation.

The first live run should produce a bounded review package, not a sprawling research archive or a premature codebase.

## When to use

- the first live run of the framework
- any run where the goal is to discover what to build next
- any run where the current opportunity set is weak or stale

## Procedure

1. Read `theme.md` carefully and extract the preferred product profile.
2. Read `FIRST_RUN_MODE.md` and adopt its source-count, candidate-count, and stop-boundary rules.
3. Use the research skill to identify repeated pain and workflow friction.
4. Keep the saved corpus bounded and auditable.
5. Generate candidate wedges from the strongest pain patterns.
6. Limit the serious candidate set to at most 5 ideas and the detailed scorecard to the top 3.
7. Score the candidates in `docs/opportunity-scorecard.md`.
8. Use monetization, substitute, and agent-operability skills on the top few candidates.
9. Create `docs/candidate-review.md` for human review.
10. Produce a concise run summary in `artifacts/runs/<run-id>/reports/discovery-summary.md`.
11. Decide whether one candidate earns a go decision, more validation, or no-go.

## Required outputs

- `docs/research.md`
- `docs/opportunity-scorecard.md`
- `docs/candidate-review.md`
- `docs/validation.md`
- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`
- `artifacts/runs/<run-id>/manifest.json`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`

## Default rule

A first run should usually stop after ranking and recommendation unless one idea clearly earns a narrow, evidence-backed go decision.

If a human has not explicitly approved moving forward, the review package is the endpoint.

## Common failure modes

- treating the first plausible idea as the winner
- starting implementation because building feels more concrete than discovery
- producing a long candidate list with no hard ranking or recommendation
- collecting weak source volume instead of strong evidence density
- making claims that are not traceable to saved source IDs
