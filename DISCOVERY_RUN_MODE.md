# Discovery Run Mode

Use this file when `ACTIVE_RUN.md` selects a discovery-to-planning run.

## Objective

The default run is discovery-first, but not discovery-only.

Its job is to:

- collect a mode-bounded research corpus
- generate a bounded set of candidate ideas
- compare the strongest candidates honestly
- recommend one narrow next move with a concrete continuation path
- continue into prototype-planning docs when one candidate clearly earns a go-now recommendation

It should only hand off into build-forward mode when the chosen candidate is specific enough to prototype honestly.

It is not allowed to drift into implementation just because coding feels more concrete than research.

## Run Modes

The kickoff command must name one explicit mode.

`test` mode:
- save between 6 and 12 meaningful sources
- use at least 3 source types when possible
- generate at most 5 serious candidates
- score at most the top 3 candidates in detail
- optimize for a compact but completion-checked package
- if one candidate wins, continue into lean prototype-planning docs before stopping

`real` mode:
- save between 10 and 24 meaningful sources
- use at least 4 source types when possible
- generate at most 7 serious candidates
- score at most the top 4 candidates in detail
- spend more effort on disconfirming evidence and substitute pressure
- if one candidate wins, continue further into fuller prototype-planning docs before stopping

If the run falls short of the mode target, it is not complete unless the run index documents an explicit exception.

## Required Sequence

Follow this sequence in order:

1. Run the readiness check.
2. Run the kickoff command to create a fresh run ID and scaffold the run files with explicit mode and direct intent.
3. Do the middle of the run: save sources, update the research manifest as you go, compare candidates, and fill the review package.
4. Complete the run index and artifact manifest as reviewer-facing outputs.
5. Run the completion check only after the package is fully populated.
6. Record checkpoint status, recommended next stage, and hard-boundary status in the run index.
7. If the recommendation is go-now and no hard boundary applies, continue into prototype-planning docs.
8. Stop only when the active completion point is satisfied.

The kickoff command and the completion check are bookends.
They do not replace the actual discovery work that happens between them.
Checkpoint 1 is a milestone surface, not a reason to stop early while the package is still incomplete or to stop automatically once it becomes reviewable.

## Middle-Of-Run Work

During the run itself:

- save each meaningful source under `research-corpus/runs/<run-id>/`
- add a real entry to `research-corpus/runs/<run-id>/manifest.json` for each saved source
- keep `candidate-links.md` current as candidates survive or drop
- write the review-package files as reviewer-facing deliverables, not as thin placeholders
- record completed artifact entries in `artifacts/runs/<run-id>/manifest.json`
- keep `artifacts/runs/<run-id>/run-index.md` accurate enough that a human could review the package from that file alone
- keep broad sources as supporting context only; do not let them dominate the shortlist logic or key-link sections
- if the leading recommendation becomes go-now, move into `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md`

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

The files under `docs/` are reusable framework guidance during discovery.
Once a candidate earns a go-now recommendation, they become the prototype-planning surface that the agent should update directly.

The manifests and run index are part of the required package.
They are not optional metadata to fill in later if time remains.

## Evidence Quality Expectations

- Prefer repeated pain over topical chatter.
- Prefer direct complaints, workarounds, reviews, issue threads, and practitioner writeups over generic trend content.
- Prefer a small number of strong sources over a large pile of weak ones.
- Prefer sources with real, inspectable URLs over unattributed summaries.
- Treat generic topic hubs, broad tag pages, landing pages, and top-level community homepages as weak supporting context unless paired with concrete complaint evidence.
- Let concrete complaint or workaround evidence dominate the key-source-link list and the final ranking.
- Each serious candidate should be traceable to concrete evidence about one workflow, one user, and one specific pain pattern.
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
- what should happen next

## Continuation Model

Treat Checkpoint 1 as a status milestone.
By default, keep going until the active run's completion point is satisfied and continue into the next non-risky stage if `ACTIVE_RUN.md` says to continue.
Pause only at a hard boundary or if `ACTIVE_RUN.md` explicitly makes the completed discovery package the end of the current run.

When the result is `prototype candidate X first`, the package is only half-finished until the next-stage docs are updated.
At minimum, continuation should name the first buyer, first workflow, first wedge, prototype success event, first monetization path, scope boundary, first prototype slice, and immediate backlog shape.

## Prototype-Readiness Gate

Do not treat a candidate as good enough to prototype unless the package can answer all of these concretely:

- Who is the first buyer or user?
- What exact workflow is being improved first?
- What is the smallest sellable wedge?
- What observable event would count as prototype success?
- What is the first credible monetization path?
- Why is this not just the first page of a platform fantasy?
- What is the smallest local slice that could prove or disprove the thesis?

Checkpoint 1 is the default discovery status surface.
Do not continue into deployment, publishing, or other hard-boundary actions unless the active run or a human explicitly authorizes that step.

## Explicit Prohibitions

- Do not implement product code during this run mode unless `ACTIVE_RUN.md` explicitly changes the completion point.
- Do not enter build-forward mode with a vague buyer, vague workflow, or vague prototype success event.
- Do not deploy anything.
- Do not create noisy external side effects unless a human explicitly allows them.
- Do not create GitHub issues, PRs, or project boards for product implementation.
- Do not gather excessive numbers of weak sources to simulate rigor.
- Do not create more files than needed to support evidence, comparison, review, and prototype planning.
- Do not treat partially completed templates as finished artifacts.