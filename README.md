# Autonomous Product Development

This repository is an opinionated framework for autonomous product development, not a generic coding template.

Its job is to help an agent move from a broad theme to one of two honest outcomes:

1. a validated, narrowly scoped product prototype with traceable reasoning, or
2. a clearly documented no-go decision.

The repository is designed so the human mainly edits one file at the start of a run: `theme.md`.
Everything else exists to steer the agent, sharpen decisions, and leave behind inspectable artifacts while the loop continues by default.

The canonical bootstrap path is:

1. `START_HERE.md`
2. `ACTIVE_RUN.md`
3. the boundary file and helper commands named there

## What this repo is especially good for

This version is tuned for discovery-stage product runs where the agent should look for opportunities that are:

- fully virtual or mostly virtual to operate
- plausible to monetize digitally
- buildable and maintainable by a solo operator with agent assistance
- narrow enough to prototype quickly
- useful before any large enterprise sales motion or physical-world logistics

The framework biases toward developer tools, workflow tools, automation products, niche SaaS, research/reporting products, monitoring and quality tooling, knowledge tools, and other software-first products with a clear narrow workflow.

## What the agent should do

Use this repository when you want an agent to:

1. research real user pain inside a broad focus area
2. generate candidate product directions from repeated pain patterns
3. compare those candidates using evidence, monetization, and agent-operability filters
4. validate whether one opportunity is worth building now
5. define a narrow MVP and vertical slices
6. implement, verify, and optionally deploy the product
7. compare the result against requirements and decide whether to iterate or stop

## Repo layout

- `START_HERE.md` - canonical repo bootstrap entrypoint for agents
- `ACTIVE_RUN.md` - canonical active-run selector and launch contract
- `theme.md` - the main human-edited run configuration
- `DISCOVERY_RUN_MODE.md` - boundary file for discovery runs
- `DISCOVERY_RUN_PROMPT.md` - detailed discovery-run prompt when a tiny prompt is not enough
- `agent/` - repo-wide operating instructions, gates, lifecycle map, and conventions
- `skills/product/` - discovery, scoring, validation, monetization, operability, requirements, design, and planning skills
- `skills/engineering/` - implementation loop, debugging, testing, review, release, and deployment guidance
- `skills/meta/` - anti-slop, evidence, critic, scope-cutting, and stuck-recovery guidance
- `skills/operations/` - observability, incident readiness, and feedback-loop guidance for MVP operation
- `docs/` - reusable framework guides for discovery outputs and later-stage living project docs after a human-approved go decision
- `research-corpus/` - saved raw sources, normalized text, source notes, and candidate-to-evidence links
- `artifacts/` - run-scoped review packages, reports, evaluations, exports, and later generated projects
- `.github/` - issue templates, labels, milestone notes, and PR template
- `templates/` - reusable status and reporting blocks

## Core operating bias

This framework is intentionally not neutral.

It biases toward:

- real user pain over cleverness
- repeated pain over isolated complaints
- narrow wedges over platform fantasies
- evidence over confidence
- monetizable product seeds over impressive demos
- virtual operations over physical delivery or heavy service layers
- agent-compatible execution over ideas that require large human teams
- honest no-go calls over forced implementation

## Operating model

The default operating mode is continue-by-default.

The agent should:

1. research real workflow pain
2. compare narrow candidate wedges
3. validate the strongest option honestly
4. continue into the next non-risky stage when the active run says to continue
5. stop only at the active completion point or a true hard boundary

Discovery packages live under `artifacts/runs/<run-id>/`, with `run-index.md` as the reviewer entry point and `review-package/` as the canonical milestone bundle.

Reviewable artifacts are asynchronous inspection surfaces.
They are not automatic pause points.

Hard boundaries remain for destructive actions, deployment or public exposure, external publishing, externally consequential tickets or PRs, purchases or credentials, and other noisy or hard-to-reverse side effects.

## How to use it

1. Edit `theme.md`.
2. Read `START_HERE.md`.
3. Confirm or update `ACTIVE_RUN.md`.
4. Run `python scripts/check_repo_readiness.py`.
5. For discovery runs, run `python scripts/start_discovery_run.py`.
6. Do the actual discovery work inside the launched run paths.
7. Run `python scripts/check_repo_readiness.py --run-id <run-id>` only after the package is complete.
8. If you need a detailed launch prompt, use `DISCOVERY_RUN_PROMPT.md`.
9. Use `agent/human-gates.md` only for true hard-boundary decisions.
10. Review the run through `artifacts/runs/<run-id>/run-index.md`, then inspect the saved evidence in `research-corpus/` and any later-stage project docs in `docs/`.

For discovery runs, prefer theme-derived slugs and visible source links in the run index and summary over stale config hints or manifest-only evidence.

## Expected output from a strong run

A strong run should leave behind:

- research grounded in repeated pain and substitutes
- a saved research corpus with evidence IDs and notes
- a ranked set of candidate opportunities
- explicit monetization and agent-operability judgments
- an explicit first buyer, first workflow, and first wedge for any leading candidate
- a clean run-scoped review package with a clear reviewer entry point
- a selected product brief or a justified no-go
- clear requirements, design, and roadmap artifacts if the idea earns a go decision
- honest verification and lifecycle review

## Practical warning

Autonomous product development usually fails before implementation.

The failure mode is not that the agent cannot write code. It is that the agent picks weak ideas, overstates validation, ignores substitutes, or chooses products that are not viable for a solo operator with software and agent workflows.

This repository is built to make those mistakes harder.
