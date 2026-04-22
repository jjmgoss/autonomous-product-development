# Autonomous Product Development

This repository is an opinionated framework for autonomous product development, not a generic coding template.

Its job is to help an agent move from a broad theme to one of two honest outcomes:

1. a validated, narrowly scoped product prototype with traceable reasoning, or
2. a clearly documented no-go decision.

The repository is designed so the human mainly edits one file at the start of a run: `theme.md`.
Everything else exists to steer the agent, sharpen decisions, and leave behind inspectable artifacts.

## What this repo is especially good for

This version is tuned for first-run product discovery where the agent should look for opportunities that are:

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

- `theme.md` - the main human-edited run configuration
- `agent/` - repo-wide operating instructions, gates, lifecycle map, and conventions
- `skills/product/` - discovery, scoring, validation, monetization, operability, requirements, design, and planning skills
- `skills/engineering/` - implementation loop, debugging, testing, review, release, and deployment guidance
- `skills/meta/` - anti-slop, evidence, critic, scope-cutting, and stuck-recovery guidance
- `skills/operations/` - observability, incident readiness, and feedback-loop guidance for MVP operation
- `docs/` - living artifacts the agent updates during each run
- `research-corpus/` - saved raw sources, normalized text, source notes, and candidate-to-evidence links
- `artifacts/` - run-scoped reports, evaluations, exports, and later generated projects
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

## First-run mode

The best first use of this repository is discovery-first, not implementation-first.

On a first live run, the agent should usually stop after producing:

- a strong research summary
- a scored candidate list
- a human review artifact comparing the best candidates
- an explicit recommendation about which idea to prototype first, if any

Use `FIRST_RUN_MODE.md` as the hard boundary file for that run.
Use `research-corpus/` to store saved evidence and `artifacts/` to store generated run outputs.

If no idea earns a clear go decision, the correct result is a documented no-go or more targeted follow-up research.

## How to use it

1. Edit `theme.md`.
2. Run `python scripts/check_first_run_readiness.py`.
3. Read or provide `FIRST_RUN_PROMPT.md` to the agent for discovery-first work.
4. Let the agent follow the instructions in `agent/`, `FIRST_RUN_MODE.md`, and the skill packs in `skills/`.
5. Use the gate checklists in `agent/human-gates.md` to review research, validation, and release readiness.
6. Review the living artifacts in `docs/`, the saved evidence in `research-corpus/`, and any run outputs in `artifacts/`.

## Expected output from a strong run

A strong run should leave behind:

- research grounded in repeated pain and substitutes
- a saved research corpus with evidence IDs and notes
- a ranked set of candidate opportunities
- explicit monetization and agent-operability judgments
- run-scoped artifacts that summarize what was produced
- a selected product brief or a justified no-go
- clear requirements, design, and roadmap artifacts if the idea earns a go decision
- honest verification and lifecycle review

## Practical warning

Autonomous product development usually fails before implementation.

The failure mode is not that the agent cannot write code. It is that the agent picks weak ideas, overstates validation, ignores substitutes, or chooses products that are not viable for a solo operator with software and agent workflows.

This repository is built to make those mistakes harder.
