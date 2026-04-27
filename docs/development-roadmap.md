# Development Roadmap

This roadmap describes the near-term path from APD's current framework state to a working local MVP.

For durable product/domain guidance, use `AGENTS.md`.
For scope and success criteria, use `docs/mvp-contract.md`.
For durable architecture/product choices, use `docs/decision-log.md`.

## Target MVP

The first working MVP is a local research cockpit for product-discovery runs.

It should let a human:

- view recent runs
- open a run detail page
- inspect sources and evidence
- inspect claims, themes, and candidate product wedges
- review agent-generated claims and candidates
- see validation phase and gaps
- assign a run-level decision
- export or view a Markdown report

The MVP should make APD usable for dogfooding before adding advanced automation.

## Milestone 0 - Repo Rails And Product Direction

Goal: make the repo safe for agent-assisted development and clarify the first product target.

Tasks:

- apply repo-rails workflow scaffolding
- add APD-specific `AGENTS.md`
- add `docs/mvp-contract.md`
- add `docs/development-roadmap.md`
- add `docs/decision-log.md`
- create first implementation issues

Acceptance criteria:

- issue templates exist
- PR template exists
- CI and PR policy checks exist
- APD product direction is documented
- MVP scope is documented
- agents have clear repo-specific instructions

## Milestone 1 - App Skeleton

Goal: create the smallest local app foundation.

Tasks:

- add Python package structure
- add FastAPI app
- add local settings/config module
- add SQLite database configuration
- add SQLAlchemy
- add Alembic
- add health route
- add pytest setup
- add `scripts/test.ps1`
- document local setup and test commands

Acceptance criteria:

- app starts locally
- health route responds
- tests run locally
- CI runs the test script
- no product UI is required yet

## Milestone 2 - Core Data Model

Goal: represent the APD research domain in structured data.

Tasks:

- add models for Run, Source, Claim, Theme, Candidate, EvidenceLink, ValidationGate, ReviewNote, Decision, and Artifact
- add migrations
- add basic CRUD/service functions where useful
- add deterministic fixture data
- add tests for model creation and relationships

Acceptance criteria:

- database can be initialized from migrations
- fixture run can be seeded
- tests verify core relationships
- structured data can represent a minimal research run

## Milestone 3 - Recent Runs UI

Goal: make runs visible in a browser.

Tasks:

- add a basic local UI
- add recent-runs page
- display run intent/title
- display phase
- display decision
- display source/claim/theme/candidate counts
- display last updated timestamp
- link to run detail page

Acceptance criteria:

- user can open the app locally
- recent runs are visible
- fixture run appears in the UI
- basic UI route test exists

## Milestone 4 - Run Detail UI

Goal: make one research run inspectable.

Tasks:

- add run detail page
- show summary and recommendation fields
- show sources
- show claims
- show themes
- show candidates
- show validation gates
- show artifacts or export links where available

Acceptance criteria:

- user can inspect a fixture run without opening Markdown files
- sources and evidence relationships are visible
- candidates are understandable
- validation gaps are visible
- basic route/rendering tests exist

## Milestone 5 - Human Review Controls

Goal: make agent-generated research reviewable.

Tasks:

- add review status to claims, themes, candidates, and validation gates
- support statuses: accepted, weak, disputed, needs follow-up
- add review notes
- expose review controls in the UI
- persist review changes
- show review status in run detail

Acceptance criteria:

- user can mark a claim or candidate as accepted, weak, disputed, or needs follow-up
- user can add a review note
- review state persists after reload
- tests cover review update behavior

## Milestone 6 - Run Decisions

Goal: make opportunity disposition explicit.

Tasks:

- add run-level decision control
- support decisions: archive, watch, publish, prototype_later, build_approved
- show decision on recent-runs page
- show decision on run detail page
- require explicit human action for build_approved

Acceptance criteria:

- user can assign a run decision
- decision persists
- recent-runs page reflects the decision
- build_approved is represented as explicit human approval, not an automatic state

## Milestone 7 - Import Existing Run Artifacts

Goal: bridge the old Markdown framework into the new app.

Tasks:

- import existing run metadata where possible
- read existing research manifest JSON
- read source records where possible
- link existing Markdown artifacts as artifacts
- tolerate incomplete or legacy runs
- report import warnings clearly

Acceptance criteria:

- at least one existing APD run can be imported or linked
- import does not destroy or rewrite source artifacts
- imported runs appear in the UI
- warnings are visible for missing or unparsed fields

## Milestone 8 - Agent Draft Import

Goal: let agents generate structured draft research.

Tasks:

- define draft JSON schema
- import claims, themes, candidates, evidence links, and validation gates from draft JSON
- mark imported draft objects as unreviewed or draft
- validate draft shape before import
- report malformed input clearly

Acceptance criteria:

- an agent-produced draft file can populate a run
- draft objects are not treated as accepted knowledge
- malformed draft files fail safely
- tests cover successful and failed import

## Milestone 9 - Markdown Report Export

Goal: produce useful human-readable outputs.

Tasks:

- render run report from structured data
- include sources, claims, themes, candidates, validation gaps, review state, and decision
- distinguish accepted, weak, disputed, and follow-up-needed claims
- export to local Markdown file
- link exported artifact from the run

Acceptance criteria:

- user can export a run report
- exported report is readable and traceable
- report includes evidence links or source references
- export is recorded as an artifact

## Milestone 10 - Research Memory And Search

Goal: make accumulated research reusable.

Tasks:

- add search across runs, claims, themes, candidates, and sources
- show related prior runs
- surface recurring themes
- distinguish accepted knowledge from draft/unreviewed claims

Acceptance criteria:

- user can search prior research
- run detail can show related runs or recurring themes
- accepted knowledge is visually distinct from unreviewed material

## Later Directions

These are intentionally out of the first MVP:

- live web/source scraping
- vector search or embeddings
- Substack publishing automation
- GitHub issue creation from candidates
- GitHub PR-style research review
- multi-agent orchestration
- hosted deployment
- multi-user support
- bring-your-own-corpus SaaS workflow

Add these only after the local cockpit is useful.