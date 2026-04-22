# Discovery Run Mode

Use this file when `ACTIVE_RUN.md` selects a discovery run.

## Objective

The default discovery run is discovery-only.

Its job is to:

- collect a bounded research corpus
- generate a bounded set of candidate ideas
- compare the strongest candidates
- recommend one next move for human review

It is not allowed to drift into implementation just because coding feels more concrete than research.

## Default Scope

- Create a fresh run ID using `YYYYMMDD-theme-slug-rN`.
- Initialize `research-corpus/runs/<run-id>/`.
- Initialize `artifacts/runs/<run-id>/`.
- Initialize `artifacts/runs/<run-id>/review-package/`.
- Save between 6 and 12 meaningful sources unless a human explicitly approves a wider pass.
- Use at least 3 source types when possible.
- Generate at most 5 candidate ideas.
- Score at most the top 3 candidates in detail.
- Recommend only one of these outcomes:
  - prototype candidate X first
  - continue validating the top 2 candidates
  - no current candidate is strong enough

If the run falls short of the source-count target, source-type target, or required review-package files, it is not complete.
The agent must either fix the gap before stopping or explicitly document why it could not.

## Required Outputs

- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`
- `artifacts/runs/<run-id>/manifest.json`
- `artifacts/runs/<run-id>/run-index.md`
- `artifacts/runs/<run-id>/review-package/research.md`
- `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- `artifacts/runs/<run-id>/review-package/candidate-review.md`
- `artifacts/runs/<run-id>/review-package/validation.md`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`

The files under `docs/` are reusable framework guidance and templates.
They are not the canonical final outputs for a discovery run.

## Evidence Quality Expectations

- Prefer repeated pain over topical chatter.
- Prefer direct complaints, workarounds, reviews, issue threads, and practitioner writeups over generic trend content.
- Prefer a small number of strong sources over a large pile of weak ones.
- Major claims in review artifacts should cite saved evidence IDs.
- Major ranking, rejection, and recommendation claims should point to more than one evidence ID when the claim spans a pattern rather than a single incident.

## Review-Package Completion Contract

The discovery review package must be fully completed before the run may stop.

The review package is incomplete if any of these are true:

- placeholder bullets remain
- template prompts such as `Choose one:` or `Explain why.` remain in the final package
- required sections are blank, one-line stubs, or obviously unresolved
- the summary only develops one idea while other shortlisted candidates are barely described
- major claims about pain, ranking, substitutes, or recommendation are not traceable to saved evidence IDs

At minimum, the review package must make it easy for a human to understand:

- what the run investigated
- which sources were saved and why they matter
- which candidates were considered
- why the leading candidate won
- why it may still fail
- which evidence could overturn the ranking
- what should happen next at Gate 1

## Stop Conditions

Stop the run after the review package is complete unless a human explicitly approves moving forward.

The discovery handoff package is complete when:

- the corpus manifest exists
- the candidate-to-evidence linkage exists
- the run index exists
- the ranked shortlist exists with at least 2 meaningfully developed candidates when multiple candidates were considered
- a recommendation exists
- the reasons against the leading candidate are written down
- the review-package files are fully written rather than template-shaped stubs
- the discovery summary explains both why the top candidate leads and what would overturn that call

Gate 1 is the default endpoint.
Do not continue into implementation, deployment, or external execution unless a human explicitly approves the next stage after reviewing the completed package.

## Explicit Prohibitions

- Do not implement product code.
- Do not deploy anything.
- Do not create noisy external side effects unless a human explicitly allows them.
- Do not create GitHub issues, PRs, or project boards for product implementation.
- Do not gather excessive numbers of weak sources to simulate rigor.
- Do not create more files than needed to support evidence, comparison, and review.
- Do not treat partially completed templates as finished artifacts.