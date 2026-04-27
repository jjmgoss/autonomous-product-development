# AGENTS.md

## Scope

These instructions apply to this repository: Autonomous Product Development, or APD.

Use the higher-level coding-projects `AGENTS.md` for general workflow, PR, safety, and code-quality rules. This file only adds APD-specific product, domain, and implementation guidance.

## Product Definition

APD is a research cockpit and execution engine for agent-assisted product discovery.

Its purpose is to help a human turn vague product curiosity into reviewable, evidence-backed product judgments.

APD should make it possible to:

- create or import product-discovery runs
- collect and inspect sources
- extract claims, themes, and candidate product wedges
- trace conclusions back to evidence
- review agent-generated research like draft work, not accepted truth
- identify validation gaps
- decide whether an opportunity should be archived, watched, published, parked for later prototyping, or explicitly approved for development
- preserve useful research so future runs can build on prior accepted knowledge

APD is not primarily a startup-idea generator. It is a system for deciding what ideas deserve belief, attention, publication, validation, or development.

## Core Workflow

The intended product workflow is:

1. A human starts with a product curiosity, market question, uploaded corpus, or research prompt.
2. APD creates or imports a research run.
3. Sources and evidence are attached to the run.
4. Agent or human analysis produces claims, pain themes, candidate wedges, validation gates, and recommendations.
5. The human reviews the evidence, claims, themes, and candidates.
6. The run receives a decision.
7. Accepted outputs can become durable research memory, reports, post outlines, prototype briefs, or follow-up research tasks.

Generated product ideas should not automatically become build projects. Product ideas become build projects only after explicit human approval.

## Validation Phases

Use these phases consistently when modeling or discussing research maturity:

- `vague_notion`: an idea, question, or prompt exists, but there is little or no evidence.
- `evidence_collected`: sources and concrete examples have been collected.
- `supported_opportunity`: repeated pain, a user/workflow, substitutes, and candidate wedges are supported by evidence.
- `vetted_opportunity`: substitutes, feasibility, monetization, distribution, and disconfirming evidence have been examined.
- `prototype_ready`: the first buyer/user, first workflow, first wedge, prototype success event, non-goals, requirements, and backlog are defined.
- `build_approved`: a human explicitly approved moving from research into a build project.

Do not advance phases based only on confident prose. Phase advancement should be backed by structured evidence, review, or explicit human decision.

## Decision States

Use these decision states consistently:

- `archive`: not worth further attention now.
- `watch`: interesting, but not ready for action.
- `publish`: worth turning into public or private writing.
- `prototype_later`: promising, but intentionally parked behind other work.
- `build_approved`: explicitly allowed to become a separate build project.

The default outcome of a promising idea is not `build_approved`.

## Core Domain Objects

Use these concepts consistently in code, docs, tests, and UI:

- `Run`: a product-discovery investigation.
- `Source`: a URL, file, note, transcript, issue, thread, review, or other evidence input.
- `Claim`: a specific assertion made by an agent or human.
- `Theme`: a cluster of related pain, need, workaround, behavior, or opportunity evidence.
- `Candidate`: a possible product wedge.
- `EvidenceLink`: a connection between a source or excerpt and a claim, theme, candidate, or validation gate.
- `ValidationGate`: a required check before a run can credibly advance phases.
- `ReviewNote`: human feedback on a run, source, claim, theme, candidate, or gate.
- `Decision`: the current disposition of a run or candidate.
- `Artifact`: a generated or curated output, such as a report, post outline, prototype brief, export, or review package.

Agent-generated objects should be treated as drafts until reviewed or accepted.

## Research Quality Bar

APD should prefer grounded, traceable, falsifiable research over impressive-sounding synthesis.

Strong outputs should identify:

- who has the problem
- the workflow where the problem appears
- repeated pain patterns
- concrete source evidence
- existing substitutes and workarounds
- why current substitutes may be insufficient
- why the opportunity might fail
- what evidence would change the recommendation
- the smallest plausible wedge
- the next validation step

Weak outputs include:

- broad platform ideas without a narrow wedge
- claims without evidence links
- summaries that hide source quality
- one-off anecdotes treated as repeated pain
- recommendations without disconfirming evidence
- build plans that skip validation

## Human Review Model

APD should support human review as a first-class part of the research loop.

A human should be able to mark claims, themes, candidates, and gates as accepted, weak, disputed, or needing follow-up.

Human review should be preserved as part of the run history and should be usable as input to future research or revision.

## Development Posture

Build APD as a durable product engine, not as a one-off script collection.

Prefer:

- explicit domain models
- clear service boundaries
- testable logic
- traceable artifacts
- deterministic fixtures
- small vertical slices
- boring implementation choices
- local-first workflows until a specific issue says otherwise

Avoid:

- hidden state
- unreviewable agent output
- broad automation that cannot be inspected
- premature external integrations
- premature deployment assumptions
- chasing APD-generated product ideas inside APD implementation work

## Tech Stack Direction

Use Python as the core implementation language unless an issue explicitly chooses otherwise.

Prefer conventional, portable application boundaries:

- web/API layer
- domain/service layer
- persistence layer
- artifact/export layer
- tests and fixtures

Database, frontend, deployment, search, and background-job choices should be documented in decision records when they become concrete implementation commitments.

## Safety Constraints Specific To APD

Do not delete research runs, source corpora, artifacts, generated reports, or review packages unless explicitly authorized.

Do not publish research externally unless explicitly authorized.

Do not create downstream repositories, issues, pull requests, posts, emails, or public artifacts from generated product ideas unless explicitly authorized.

Do not treat agent-generated research as accepted knowledge without review.

Do not treat an idea as approved for development unless it has the `build_approved` decision or equivalent explicit human approval.

## Documentation Placement

Keep durable product/domain guidance in this file.

Put temporary plans, current milestones, near-term implementation sequence, and tactical non-goals in roadmap or planning docs.

Put concrete architecture choices and tradeoffs in decision records.

Put setup, commands, and operational instructions in README or dedicated development docs.

Put shared GitHub workflow rules in `docs/github-workflow.md`.
