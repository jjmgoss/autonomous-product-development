# Autonomous Product Development

This repository is a starter kit for running an autonomous product-development loop with an LLM agent.

The repository is designed so the human changes exactly one file at the start of a run: `theme.md`.
Everything else acts as operating instructions, templates, stage gates, and reusable skill packs.

## What this repo is for

Use this repository when you want an agent to:

1. Research a broad area for real product pain.
2. Select and validate a narrow opportunity.
3. Define a minimal but coherent product.
4. Break the work into milestones and issues.
5. Implement a real prototype.
6. Test, verify, and optionally deploy it.
7. Compare the result against requirements and decide what to do next.

## Repo layout

- `theme.md` — the one file the human edits before a run.
- `agent/` — the agent operating system: system prompt, runbook, gates, lifecycle map, and repo conventions.
- `skills/product/` — product research, scoring, validation, requirements, design docs, and roadmap guidance.
- `skills/engineering/` — implementation loop, debugging, testing, code review, refactoring, release verification, and deployment readiness.
- `skills/meta/` — critic, evidence checking, scope cutting, anti-slop, and recovery when stuck.
- `skills/operations/` — observability, incident readiness, and feedback loops.
- `docs/` — living artifacts the agent must maintain during a run.
- `.github/` — labels, issue templates, milestone conventions, and PR template.
- `templates/` — reusable status/update blocks.

## Core idea

This is intentionally opinionated.

The agent should not be allowed to free-associate from a vague theme directly into code.
It should earn the right to build by producing evidence, narrowing scope, and passing explicit stage gates.

The framework biases toward:

- narrow MVPs over broad product fantasies
- real user pain over cleverness
- vertical slices over sprawling scaffolding
- verification over confident storytelling
- documented decisions over hidden improvisation

## How to use it

1. Edit `theme.md` with the focus area and constraints for the run.
2. Point your coding agent at this repository.
3. Use a simple instruction such as:
   - “Inspect this repository, follow the instructions, and work the lifecycle until you reach a verified prototype or a documented no-go decision.”
4. Optionally enforce the human gates in `agent/human-gates.md`.
5. Review the outputs in `docs/`, issues, PRs, and running app artifacts.

## Expected outcome

A successful run should leave behind:

- evidence-backed product research
- a clear product brief and requirements set
- design decisions and implementation plan
- a prioritized backlog and milestone breakdown
- a working prototype or an honest no-go decision
- release verification notes and retrospective learnings

## What v3 adds

Compared with earlier versions, v3 strengthens:

- engineering execution skills
- critic and evidence-checking routines
- definition-of-done enforcement
- GitHub issue template structure
- operations and feedback-loop coverage
- lifecycle gap analysis so the agent can see what is still weak

## Practical warning

The weak link in autonomous product development is usually not code generation.
It is product selection and scope discipline.

This repository is built to force more skepticism before building and more honesty after building.
