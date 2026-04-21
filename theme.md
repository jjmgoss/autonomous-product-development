# Theme

This is the one file the human is expected to modify before starting a run.

## Focus area

Choose a broad but meaningful area to investigate.
Examples:

- personal productivity for knowledge workers
- home infrastructure and self-hosting
- lightweight data tooling for analysts
- workflow automation for small teams
- consumer note-taking and knowledge retrieval

Replace the text below with the theme for the current run.

**Current theme:**

> Build something in the area of autonomous product development and developer workflow automation.

## Constraints

Specify constraints the agent should respect.

Examples:

- prefer open-source tools where possible
- keep the MVP implementable in 1–3 days of focused work
- avoid paid APIs unless clearly necessary
- prefer local-first or low-cost deployment
- keep the product understandable by one maintainer

**Current constraints:**

- Use a small, testable MVP.
- Favor a web app or developer-facing tool over a mobile app.
- Avoid ideas that require enterprise sales before they are useful.
- Prefer reversible architecture choices.
- Prefer products that can be meaningfully evaluated by one human reviewer.

## Technology preferences

Set default implementation preferences if relevant.

**Current preferences:**

- Backend: Python
- Frontend: Next.js or other lightweight web UI
- Data layer: SQLite or Postgres depending on need
- Containerization: Docker
- Testing: lightweight but real automated checks

## Exclusions

Use this section to keep the agent away from dead ends.

**Current exclusions:**

- generic chatbot wrappers
- undifferentiated note apps
- broad “AI for everything” platforms
- ideas that depend on proprietary data access you do not have

## Human review posture

Choose one:

- Fully autonomous until completion
- Human gates enabled
- Human gates enabled only before coding, before deployment, and before merge

**Current posture:**

> Human gates enabled only before coding, before deployment, and before merge.
