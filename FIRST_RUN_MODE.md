# First-Run Mode

Use this file as the default operating boundary for the first live run of the framework.

## Objective

The first live run is discovery-only.

Its job is to:

- collect a bounded research corpus
- generate a bounded set of candidate ideas
- compare the strongest candidates
- recommend one next move for human review

It is not allowed to drift into implementation just because coding feels more concrete than research.

## Default scope

- Create a run ID using `YYYYMMDD-theme-slug-rN`.
- Initialize `research-corpus/runs/<run-id>/`.
- Initialize `artifacts/runs/<run-id>/`.
- Save between 6 and 12 meaningful sources unless a human explicitly approves a wider pass.
- Use at least 3 source types when possible.
- Generate at most 5 candidate ideas.
- Score at most the top 3 candidates in detail.
- Recommend only one of these outcomes:
  - prototype candidate X first
  - continue validating the top 2 candidates
  - no current candidate is strong enough

## Required outputs

- `docs/research.md`
- `docs/opportunity-scorecard.md`
- `docs/candidate-review.md`
- `docs/validation.md`
- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`
- `artifacts/runs/<run-id>/manifest.json`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`

## Evidence quality expectations

- Prefer repeated pain over topical chatter.
- Prefer direct complaints, workarounds, reviews, issue threads, and practitioner writeups over generic trend content.
- Prefer a small number of strong sources over a large pile of weak ones.
- Major claims in review artifacts should cite saved evidence IDs.

## Stop conditions

Stop the run after the review package is complete unless a human explicitly approves moving forward.

The first-run handoff package is complete when:

- the corpus manifest exists
- the candidate-to-evidence linkage exists
- the ranked shortlist exists
- a recommendation exists
- the reasons against the leading candidate are written down

## Explicit prohibitions

- Do not implement product code.
- Do not deploy anything.
- Do not create noisy external side effects unless a human explicitly allows them.
- Do not create GitHub issues, PRs, or project boards for product implementation.
- Do not gather excessive numbers of weak sources to simulate rigor.
- Do not create more files than needed to support evidence, comparison, and review.