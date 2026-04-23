# Run Defaults

This file keeps background defaults for kickoff-driven runs.

The direct kickoff intent should come from the user prompt or `python scripts/autopd.py MODE "DIRECT_INTENT"`.
Use this file for reusable defaults, constraints, and preferences that should shape the run after the direct intent is already clear.

## Focus area

Describe the default domain bias to use when the direct kickoff intent is adjacent or under-specified.

**Current default focus area:**

> Discover product opportunities in autonomous product development and developer workflow automation.

## Desired product profile

Use this section to bias the agent toward product shapes that fit the framework.

**Current desired profile:**

- software-first or information-first products
- digitally monetizable products
- mostly virtual operations after launch
- narrow workflows with clear users
- useful to a solo operator with agent assistance
- capable of starting small and becoming useful quickly

## Constraints

State the hard constraints the agent should respect.

**Current constraints:**

- Keep the first useful MVP small, testable, and understandable by one reviewer.
- Favor products that can be prototyped in days, not quarters.
- Avoid ideas that require enterprise sales before they become useful.
- Avoid paid APIs unless clearly necessary for the wedge.
- Prefer reversible architecture and distribution choices.
- Prefer products that can be built, operated, and iterated on mostly through software and agent workflows.

## Commercial lens

State what kind of business seed the agent should look for.

**Current commercial lens:**

- Look for pain linked to budgets, measurable time savings, risk reduction, throughput improvement, or recurring operational friction.
- Favor products with plausible subscription, usage-based, seat-based, or recurring report/monitoring pricing models.
- Be skeptical of ideas that are interesting but have weak willingness-to-pay signals.

## Technology preferences

Set implementation defaults for ideas that earn a go decision.

**Current preferences:**

- Backend: Python
- Frontend: Next.js or another lightweight web UI when a UI is needed
- Data layer: SQLite or Postgres depending on state and concurrency needs
- Containerization: Docker
- Testing: lightweight but real automated checks

## Exclusions

Use this section to keep the agent away from dead ends.

**Current exclusions:**

- generic chatbot wrappers
- undifferentiated note apps
- broad "AI for everything" platforms
- products that require proprietary data access you do not have
- products that need physical inventory, physical delivery, or in-person operations
- products that need compliance-heavy infrastructure at MVP stage unless unusually well justified
- products that mainly work through large sales, support, or service organizations

## Human review posture

Choose one:

- Hard boundaries only
- Hard boundaries plus manual discovery stop
- Hard boundaries plus manual release stop

**Current posture:**

> Hard boundaries only.

## Discovery-run preference

Describe how conservative the agent should be on the next discovery pass.

**Current discovery-run preference:**

> Prioritize discovery, ranking, and validation. Do not code unless one opportunity clearly earns a go decision and the wedge is narrow.
