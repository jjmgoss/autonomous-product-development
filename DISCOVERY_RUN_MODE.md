# Discovery Run Mode

Use this file when `ACTIVE_RUN.md` selects a discovery run.

## Objective

The default discovery run is discovery-only.

Its job is to:

- collect a bounded research corpus
- generate a bounded set of candidate ideas
- compare the strongest candidates
- recommend one next move for checkpoint review

It is not allowed to drift into implementation just because coding feels more concrete than research.

## Required Sequence

Follow this sequence in order:

1. Run the readiness check.
2. Run the launcher to create a fresh run ID and scaffold the run files.
3. Do the middle of the run: save sources, update the research manifest as you go, compare candidates, and fill the review package.
4. Complete the run index and artifact manifest as reviewer-facing outputs.
5. Run the completion check only after the package is fully populated.
6. Record checkpoint status and the requested decision in the run index.
7. Follow the checkpoint behavior in `ACTIVE_RUN.md`.

The launcher and the completion check are bookends.
They do not replace the actual discovery work that happens between them.
Checkpoint 1 is a milestone surface, not a reason to stop early while the package is still incomplete.

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

## Middle-Of-Run Work

During the run itself:

- save each meaningful source under `research-corpus/runs/<run-id>/`
- add a real entry to `research-corpus/runs/<run-id>/manifest.json` for each saved source
- keep `candidate-links.md` current as candidates survive or drop
- write the review-package files as reviewer-facing deliverables, not as thin placeholders
- record completed artifact entries in `artifacts/runs/<run-id>/manifest.json`
- keep `artifacts/runs/<run-id>/run-index.md` accurate enough that a human could review the package from that file alone

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

The manifests and run index are part of the required package.
They are not optional metadata to fill in later if time remains.

## Evidence Quality Expectations

- Prefer repeated pain over topical chatter.
- Prefer direct complaints, workarounds, reviews, issue threads, and practitioner writeups over generic trend content.
- Prefer a small number of strong sources over a large pile of weak ones.
- Prefer sources with real, inspectable URLs over unattributed summaries.
- Major claims in review artifacts should cite saved evidence IDs.
- Major ranking, rejection, and recommendation claims should point to more than one evidence ID when the claim spans a pattern rather than a single incident.
- Source notes should repeat the exact URL near the top and preserve enough local context that a reviewer can inspect the saved file without manifest archaeology.

## Review-Package Completion Contract

The discovery review package must be fully completed before the run may stop.

The review package is incomplete if any of these are true:

- placeholder bullets remain
- template prompts such as `Choose one:` or `Explain why.` remain in the final package
- required sections are blank, one-line stubs, or obviously unresolved
- the summary only develops one idea while other shortlisted candidates are barely described
- major claims about pain, ranking, substitutes, or recommendation are not traceable to saved evidence IDs
- the research manifest still has zero saved sources or missing required source fields
- the artifact manifest still has zero completed artifact entries or missing required artifact fields
- the run index still reads like a launch scaffold instead of a reviewer control document
- the candidate-evidence map names candidates without meaningful supporting and weakening evidence IDs

At minimum, the review package must make it easy for a human to understand:

- what the run investigated
- which sources were saved and why they matter
- which real source links are most worth opening first
- which candidates were considered
- why the leading candidate won
- why it may still fail
- which evidence could overturn the ranking
- what should happen next at Checkpoint 1

## Checkpoint Behavior

Treat Checkpoint 1 as a review milestone.
By default, keep going until the active run's completion point is satisfied.
Pause only if `ACTIVE_RUN.md` explicitly says `checkpoint behavior: pause for human review`.

The discovery handoff package is complete when:

- the corpus manifest exists
- the candidate-to-evidence linkage exists
- the run index exists
- the ranked shortlist exists with at least 2 meaningfully developed candidates when multiple candidates were considered
- a recommendation exists
- the reasons against the leading candidate are written down
- the review-package files are fully written rather than template-shaped stubs
- the discovery summary explains both why the top candidate leads and what would overturn that call
- both manifests are fully populated with real entries rather than scaffold status
- the run index explains the reviewer route, current counts, recommendation, requested Checkpoint 1 decision, and key source links

Checkpoint 1 is the default discovery review surface.
Do not continue into implementation, deployment, or external execution unless the active run or a human explicitly authorizes the next stage after the completed discovery handoff.

## Explicit Prohibitions

- Do not implement product code.
- Do not deploy anything.
- Do not create noisy external side effects unless a human explicitly allows them.
- Do not create GitHub issues, PRs, or project boards for product implementation.
- Do not gather excessive numbers of weak sources to simulate rigor.
- Do not create more files than needed to support evidence, comparison, and review.
- Do not treat partially completed templates as finished artifacts.