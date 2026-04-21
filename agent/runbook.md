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
- `agent/definition-of-done.md`
- `agent/lifecycle-map.md`
- `agent/orchestration-v3.md`

## Step 3: Create or refresh the lifecycle artifacts

Make sure the docs in `docs/` are present and consistent.
If the run is new, initialize them.
If the run is ongoing, update them rather than duplicating them.

## Step 4: Research before building

Use the product skills first.
Do not start coding until the validation stage produces a clear go decision.

## Step 5: Plan before implementation

Before writing meaningful code:

- define the MVP clearly
- identify the critical path
- break the work into milestones and issues
- prefer the smallest vertical slice that can falsify or support the product thesis

## Step 6: Implement iteratively

During implementation:

- work from acceptance criteria
- keep changes small and legible
- verify behavior continuously
- update `docs/work-log.md` and `docs/decision-log.md`

## Step 7: Verify honestly

Before declaring success:

- compare the product to `docs/requirements.md`
- run tests and smoke checks
- document known gaps
- confirm whether the app is truly runnable

## Step 8: Close the loop

Finish with:

- `docs/release.md`
- `docs/retrospective.md`
- `docs/lifecycle-review.md`
- an explicit recommendation: iterate, pivot, pause, or archive

## Fallback behavior when stuck

If progress stalls:

- reduce scope
- revisit assumptions
- run a smaller experiment
- ask what evidence is missing
- use the stuck-recovery and scope-cutting skills
