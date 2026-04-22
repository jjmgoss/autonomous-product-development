# Runbook

This file tells the agent how to operate in practice.

## Step 1: Read the theme and constraints

Start every run by reading `theme.md`.
Do not infer the theme from old docs or repository history if `theme.md` is present.

## Step 2: Read the operating instructions

Read the following before doing substantive work:

- `agent/system-prompt.md`
- `agent/human-gates.md`
- `agent/repo-conventions.md`
- `agent/research-corpus-conventions.md`
- `agent/artifact-output-conventions.md`
- `agent/definition-of-done.md`
- `agent/lifecycle-map.md`
- `agent/orchestration-v3.md`
- `FIRST_RUN_MODE.md` when the run is discovery-first

## Step 3: Create or refresh the lifecycle artifacts

Make sure the docs in `docs/` are present and consistent.
Treat these docs as reusable framework guidance during the first discovery run.
If the run is new, read them and use their structure.
If the run is ongoing after a human-approved go decision, update them rather than duplicating them.

If the run is discovery-first, also initialize a matching run folder in:

- `research-corpus/runs/<run-id>/`
- `artifacts/runs/<run-id>/`
- `artifacts/runs/<run-id>/review-package/`

## Step 4: Decide the run mode

Before deeper work, decide which of these two modes fits the current run:

- Discovery-first mode: used for first runs, idea generation, market mapping, and opportunity ranking
- Build-forward mode: used only after one opportunity clearly earns a go decision

Default to discovery-first mode unless the existing docs already contain a strong validated opportunity.

On the first live run, follow `FIRST_RUN_MODE.md` as a hard boundary file.

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

If no opportunity earns a clear go decision, stop there with an explicit recommendation.
If any artifact is still template-shaped, the run is not ready to stop.

## Step 6: Plan before implementation

Before writing meaningful code:

- define the MVP clearly
- identify the critical path
- break the work into milestones and issues
- prefer the smallest vertical slice that can falsify or support the product thesis

## Step 7: Implement iteratively

During implementation:

- work from acceptance criteria
- keep changes small and legible
- verify behavior continuously
- update `docs/work-log.md` and `docs/decision-log.md`

## Step 8: Verify honestly

Before declaring success:

- compare the product to `docs/requirements.md`
- run tests and smoke checks
- document known gaps
- confirm whether the app is truly runnable

## Step 9: Close the loop

Finish with:

- `docs/release.md`
- `docs/retrospective.md`
- `docs/lifecycle-review.md`
- an explicit recommendation: iterate, pivot, pause, or archive

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

Before stopping a first-run discovery pass, run `python scripts/check_first_run_readiness.py --run-id <run-id>`.
If it fails, either fix the package or document the boundary exception in the run index.

## Fallback behavior when stuck

If progress stalls:

- reduce scope
- revisit assumptions
- run a smaller experiment
- ask what evidence is missing
- use the stuck-recovery and scope-cutting skills
