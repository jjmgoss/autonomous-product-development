# Runbook

This file tells the agent how to operate in practice.

## Step 0: Bootstrap from the canonical entrypoint

If startup instructions are not otherwise explicit, begin with:

- `START_HERE.md`
- `ACTIVE_RUN.md`

Do not invent launcher scripts or startup paths that the repo does not name.

## Step 1: Identify direct intent and defaults

Start every run by identifying the direct kickoff intent from the user prompt or kickoff command.
If direct intent is missing, ask for it instead of inferring it from repository history or `theme.md`.
Read `theme.md` after that as background defaults and constraints.

## Step 2: Read the operating instructions

Read the following before doing substantive work:

- `agent/system-prompt.md`
- `agent/human-gates.md`
- `agent/repo-conventions.md`
- `agent/research-corpus-conventions.md`
- `agent/artifact-output-conventions.md`
- `DISCOVERY_RUN_MODE.md` when the run is discovery-first
- `BUILD_RUN.md` and `docs/prototype-standard.md` when the run is build-forward

Read `agent/definition-of-done.md`, `agent/lifecycle-map.md`, and `agent/orchestration-v3.md` only when the current stage needs them.

## Step 3: Create or refresh the lifecycle artifacts

Make sure the docs in `docs/` are present and consistent.
Treat these docs as reusable framework guidance during a discovery run.
If the run is new, read them and use their structure.
If the run is ongoing after a go decision, update them rather than duplicating them.

If the run is discovery-first, also initialize a matching run folder in:

- `research-corpus/runs/<run-id>/`
- `artifacts/runs/<run-id>/`
- `artifacts/runs/<run-id>/review-package/`

Prefer `python scripts/autopd.py MODE "DIRECT_INTENT"` over manual run-folder setup.
The kickoff command creates the run shell only.
After launch, immediately populate the corpus, manifests, review package, and run index before using the completion check.
Do not pause early just because the run reached a named checkpoint. Follow the `completion point`, `post-discovery default`, and `hard boundaries` from `ACTIVE_RUN.md`.

## Step 4: Decide the run mode

Before deeper work, decide both the lifecycle stage and the execution depth:

- Discovery-first stage: used for first runs, idea generation, market mapping, and opportunity ranking
- Build-forward stage: used only after one opportunity clearly earns a go decision and is specific enough to prototype honestly
- Prototype stage: prove one narrow local slice
- Hardening stage: improve trust and reliability without widening scope
- Polish stage: improve clarity and usability without pretending the product is already broader
- Productionization stage: prepare for deployment, exposure, and support burden
- `test` mode: compact validation pass with bounded evidence and lightweight prototype-planning continuation
- `real` mode: deeper pass with more evidence, more disconfirmation, and fuller prototype-planning continuation

Default to discovery-first stage unless the existing docs already contain a strong validated opportunity.
When `ACTIVE_RUN.md` selects discovery, follow `DISCOVERY_RUN_MODE.md` as the boundary file for both `test` and `real` modes.

## Step 5: Research before building

Use the product skills first.
Do not start coding until the validation stage produces a clear go decision.

In discovery-first mode, produce at minimum:

- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`
- `artifacts/runs/<run-id>/manifest.json`
- `artifacts/runs/<run-id>/run-index.md`
- `artifacts/runs/<run-id>/review-package/research.md`
- `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- `artifacts/runs/<run-id>/review-package/candidate-review.md`
- `artifacts/runs/<run-id>/review-package/validation.md`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`

While doing the discovery work:

- add real entries to `research-corpus/runs/<run-id>/manifest.json` as sources are saved
- keep `research-corpus/runs/<run-id>/candidate-links.md` current while the shortlist changes
- add completed entries to `artifacts/runs/<run-id>/manifest.json` as reviewer-facing outputs are written
- treat `artifacts/runs/<run-id>/run-index.md` as the reviewer control document for the whole package

If no opportunity earns a clear go decision, stop there with an explicit recommendation.
If any artifact is still template-shaped, the run is not ready to stop.
Make the key source URLs visible in the run index and discovery summary so a reviewer does not need to dig through the manifest first.
If one candidate clearly earns a go-now recommendation and no hard boundary applies, continue into `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md` rather than waiting for review by default.
Do not treat that handoff as complete unless those docs name the first buyer, first workflow, first wedge, prototype success event, and first monetization path.

## Step 6: Plan before implementation

Before writing meaningful code:

- define the MVP clearly
- identify the critical path
- break the work into milestones and issues
- prefer the smallest vertical slice that can falsify or support the product thesis
- use the shared scaffold and `docs/prototype-standard.md` unless there is a good reason to do something else

## Step 7: Implement iteratively

During implementation:

- work from acceptance criteria
- keep changes small and legible
- prefer boring reliability over cleverness
- keep demo behavior deterministic
- document what is stubbed instead of implying it is real
- verify behavior continuously
- update `docs/work-log.md` and `docs/decision-log.md`

## Step 8: Verify honestly

Before declaring success:

- compare the product to `docs/requirements.md`
- run tests and smoke checks
- run or document a health check or equivalent sanity check
- document known gaps
- classify the result honestly as a UI shell, working demo, or real local prototype
- confirm whether the app is truly runnable

## Step 9: Close the loop

Finish with:

- `docs/release.md`
- `docs/retrospective.md`
- `docs/lifecycle-review.md`
- an explicit recommendation: iterate, pivot, stop, or archive

## Required product-discovery checks

Before a go decision, confirm that you have answered all of these:

- Who exactly has the problem?
- How do they solve it today?
- Why are current tools or workarounds insufficient?
- Why would anyone plausibly pay for improvement?
- Can the product start as a narrow wedge?
- Can a solo operator with agents plausibly build and maintain it?
- Is it compatible with mostly virtual operations?
- Does it avoid immediate dependence on heavy compliance, services, or enterprise sales?

Also confirm that the strongest claims point back to saved evidence rather than unattributed summaries.
Also confirm that the winning candidate has a specific first buyer, first workflow, first wedge, and first monetization path.

Before stopping a discovery pass, run `python scripts/check_repo_readiness.py --run-id <run-id>`.
Do not use that command as the next action right after launch.
Use it only after the package is populated and the run index reflects the final reviewer-facing state.
If it fails, either fix the package or document the boundary exception in the run index.
Treat the named checkpoint as a status marker, not as the default reason to pause.

## Fallback behavior when stuck

If progress stalls:

- reduce scope
- revisit assumptions
- run a smaller experiment
- ask what evidence is missing
- use the stuck-recovery and scope-cutting skills
