# Decision Log

This file records durable APD product, architecture, and workflow decisions.

Use this file when a choice affects future implementation direction, repo structure, data modeling, runtime behavior, or agent workflow. Keep entries short and explicit.

## Entry Format

```markdown
## YYYY-MM-DD - Decision title

Status: proposed | accepted | superseded

Decision:
-

Context:
-

Alternatives considered:
-

Consequences:
-

Follow-ups:
-
```

## 2026-04-26 - Build APD as a research cockpit and product-discovery engine

Status: accepted

Decision:
- APD should become a local research cockpit and execution engine for agent-assisted product discovery.
- The product should help humans review evidence-backed product research, inspect claims and candidates, identify validation gaps, and decide what deserves attention.
- APD should not be framed as a generic startup-idea generator.

Context:
- The repo began as a Markdown-heavy autonomous product-development framework.
- The useful core is the repeatable engine: research evidence, identify themes, generate candidate wedges, validate them, and preserve the reasoning.
- The first user is the repo owner dogfooding the system for repeated product-discovery experiments.

Alternatives considered:
- Keep APD as a prompt/doc framework only.
- Build a Substack post generator first.
- Build a bring-your-own-corpus insight SaaS first.
- Build a UI that only shows generated product ideas.

Consequences:
- The first app surface should focus on recent runs, run details, evidence, claims, themes, candidates, validation gates, review status, and decisions.
- Publishing, BYO corpus, and generated-idea galleries remain possible later outputs, not the first product center.

Follow-ups:
- Maintain `docs/mvp-contract.md`.
- Create implementation issues for the local research cockpit.

## 2026-04-26 - Use explicit validation phases and decision states

Status: accepted

Decision:
- APD should model research maturity with explicit validation phases.
- APD should model run disposition with explicit decision states.
- Generated ideas should not automatically become build projects.

Context:
- The engine will generate distracting product ideas.
- APD needs to help decide what deserves belief or action, not simply produce more ideas.

Alternatives considered:
- Let each research run end in freeform recommendations.
- Treat every good idea as a prototype candidate.
- Use only a confidence score.

Consequences:
- Runs and candidates should expose phase, decision, and validation gaps.
- UI and exports should make “interesting but not build-approved” easy to represent.
- Build-approved requires explicit human approval.

Follow-ups:
- Encode phases and decisions in the data model.
- Add review controls and validation gates to the MVP.

## 2026-04-26 - SQLite-first for the MVP

Status: accepted

Decision:
- Use SQLite first for the local MVP.
- Keep the app portable by using SQLAlchemy and migrations.
- Move to Postgres only when a concrete need appears.

Context:
- The first priority is getting a working local cockpit and dogfooding loop.
- SQLite reduces infrastructure friction.
- APD may eventually need Postgres for concurrency, deployment, background workers, or richer search, but not immediately.

Alternatives considered:
- Postgres from day one.
- DuckDB as the primary database.
- MongoDB/document database.
- Vector database as the primary store.

Consequences:
- Avoid SQLite-specific assumptions where practical.
- Keep structured domain objects in the database.
- Store large raw/normalized source text and generated reports as files with database references.
- Document any future migration trigger before switching databases.

Follow-ups:
- Add SQLAlchemy and Alembic when the app skeleton is implemented.
- Add a clean settings layer for `DATABASE_URL`.

## 2026-04-26 - Do not use a vector database for the first MVP

Status: accepted

Decision:
- Do not add vector database infrastructure in the MVP.
- Start with structured traceability and conventional search.
- Consider embeddings later for semantic retrieval across the accumulated research corpus.

Context:
- APD's first value depends on evidence traceability, human review, and structured reasoning.
- A vector DB too early could hide weak source/claim relationships behind fuzzy retrieval.

Alternatives considered:
- Add vector DB infrastructure immediately.
- Use embeddings as the primary source of truth.
- Skip structured source/claim/candidate links.

Consequences:
- The first data model should make relationships explicit.
- Evidence links should be inspectable.
- Semantic search can be added later as an enhancement, not a foundation.

Follow-ups:
- Model `EvidenceLink` explicitly.
- Add simple search before semantic search.

## 2026-04-26 - Keep generated research draft-first

Status: accepted

Decision:
- Agent-generated research should be imported or stored as draft material until reviewed.
- Accepted knowledge should be distinguishable from unreviewed agent output.

Context:
- APD is meant to help humans avoid fooling themselves.
- Agent-written claims can sound strong while being weakly supported.
- The UI should support research review as a first-class loop.

Alternatives considered:
- Treat generated reports as final outputs.
- Accept all agent-generated claims by default.
- Keep review only as freeform notes.

Consequences:
- Claims, themes, candidates, and gates should have review status.
- Review notes should be preserved.
- Exports should be able to distinguish accepted, weak, disputed, and follow-up-needed claims.

Follow-ups:
- Add review status fields to the data model.
- Add review controls to the UI.

## 2026-04-26 - Keep repo-rails workflow scaffolding separate from APD product direction

Status: accepted

Decision:
- Use repo-rails for generic issue-driven, PR-based, agent-friendly workflow scaffolding.
- Keep APD-specific product and architecture direction in APD-owned docs.
- Do not use repo-rails to decide APD's app architecture.

Context:
- repo-rails provides useful generic repository rails.
- APD needs its own product-specific instructions and roadmap.

Alternatives considered:
- Fold APD-specific direction into repo-rails templates.
- Let repo-rails profiles impose a full app stack.
- Avoid repo-rails entirely.

Consequences:
- `AGENTS.md` and APD planning docs should carry product-specific context.
- repo-rails managed files may remain generic.
- Future repo-rails checks may report intentional local overrides if APD customizes managed workflow files.

Follow-ups:
- Keep `AGENTS.md` APD-specific and durable.
- Use planning docs for near-term roadmap and MVP scope.
