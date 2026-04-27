# MVP Contract

## Purpose

The first APD MVP is a local research cockpit for product-discovery runs.

The MVP should make APD usable as a working system, not just a Markdown framework. A human should be able to open the app, inspect recent research runs, drill into the evidence and reasoning behind a run, review agent-generated claims, and assign a decision.

The MVP is successful when a human can understand what a run concluded, what evidence supports or weakens it, what remains unvalidated, and what should happen next without manually opening raw Markdown files.

## Primary User

The primary user is the repo owner using APD to run repeated product-discovery experiments.

The user wants to:

- explore product ideas without immediately chasing all of them
- understand whether an opportunity is supported by evidence
- inspect and challenge agent-generated research
- preserve useful findings for future research
- turn selected outputs into reports, post outlines, prototype briefs, or follow-up research tasks

## Core MVP Workflow

1. Create or import a research run.
2. View the run in a recent-runs list.
3. Open a run detail page.
4. Inspect sources and evidence.
5. Inspect claims, themes, and candidate product wedges.
6. Review claims or candidates as accepted, weak, disputed, or needing follow-up.
7. See validation phase and missing gates.
8. Assign a run-level decision.
9. Export or inspect a Markdown report.

## Required Screens Or Surfaces

### Recent Runs

Shows a list of runs with:

- run title or intent
- phase
- decision
- top candidate or recommendation
- source count
- claim/theme/candidate counts
- last updated timestamp

### Run Detail

Shows:

- run intent
- summary
- validation phase
- decision state
- recommendation
- key claims
- pain themes
- candidate wedges
- validation gaps
- links to sources and artifacts

### Source / Evidence View

Shows:

- source title
- source type
- URL or file reference
- reliability notes
- relevant excerpts
- linked claims, themes, or candidates

### Candidate View

Shows:

- candidate title
- target user
- first workflow
- first wedge
- evidence supporting the candidate
- evidence weakening the candidate
- substitutes or workarounds
- monetization notes
- risks
- prototype success event, if known
- current review status

### Review Controls

Allow the human to mark claims, themes, candidates, or gates as:

- accepted
- weak
- disputed
- needs follow-up

### Decision Control

Allow the human to assign a run-level decision:

- archive
- watch
- publish
- prototype later
- build-approved

## Core Domain Objects

The MVP should support these concepts:

- Run
- Source
- Claim
- Theme
- Candidate
- EvidenceLink
- ValidationGate
- ReviewNote
- Decision
- Artifact

These do not all need rich UI in the first pass, but the data model should be able to represent them.

## Validation Phases

The MVP should represent these phases:

- vague_notion
- evidence_collected
- supported_opportunity
- vetted_opportunity
- prototype_ready
- build_approved

The MVP does not need perfect automatic phase evaluation. It may start with manually assigned or simply computed phases, as long as the phase is visible and reviewable.

## MVP Non-Goals

The MVP should not include:

- SaaS hosting
- multi-user authentication
- public deployment
- live scraping
- vector database infrastructure
- automatic Substack publishing
- automatic GitHub issue creation from generated ideas
- automatic project/repository creation from generated ideas
- GitHub PR-style research review integration
- background job orchestration
- full autonomous multi-agent research

These can be revisited after the local research cockpit works.

## Data And Storage Expectations

The MVP should use a simple local-first storage model.

Structured run data should live in an application database.

Raw source text, normalized source text, generated reports, and exports may live on the local filesystem with database records pointing to their paths.

Agent-generated outputs should be importable as draft structured data, not automatically accepted as truth.

## Success Criteria

The MVP is complete when:

- the app runs locally from documented commands
- a fixture/demo run can be loaded
- recent runs are visible in the UI
- a run detail view exposes sources, claims, themes, candidates, validation state, and decision state
- a human can mark review status on at least claims or candidates
- a human can assign a run-level decision
- a Markdown report can be exported or viewed
- basic tests cover the app startup, core data model, and at least one run-detail path
- setup and test commands are documented

## First Fixture Run

The first fixture run should be small, deterministic, and committed to the repo.

It should include enough data to exercise the cockpit:

- one run
- several sources
- several claims
- at least two themes
- at least two candidates
- evidence links between sources and claims/candidates
- at least one disputed or weak claim
- at least one validation gap
- a run-level decision

The fixture should be useful for local development, tests, and screenshots.

## Product Discipline

The MVP should make good ideas inspectable, not irresistible.

The system should help the human avoid chasing every plausible opportunity. A run can be interesting and still end as archive, watch, publish, or prototype later.

Only explicit human approval should move a candidate into build-approved status.