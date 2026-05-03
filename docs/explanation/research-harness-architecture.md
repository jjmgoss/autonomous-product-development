# APD Research Harness Architecture

APD is becoming a guided product-research harness.

That means APD is not just a UI around model output, and it is not a generic agent framework that asks the user to wire together prompts, tools, permissions, and review flow. APD owns the working research loop for product investigation: it frames the job, constrains the tools, assembles the context, validates the outputs, persists the evidence, and presents the results for human review.

The model is a worker inside that harness. It is not the whole product.

## What APD is becoming

APD should help a user move from a product investigation question to a structured, evidence-linked product opportunity map.

In practical repo terms, the intended loop is:

1. A user creates a research brief.
2. APD starts a bounded research execution from that brief.
3. APD runs controlled search discovery, source triage, and source capture.
4. APD uses captured sources to drive grounded component generation.
5. APD validates, repairs, and imports structured research objects.
6. The user reviews candidates, claims, themes, gates, and evidence links.
7. APD preserves review outcomes and turns them into next actions later.

APD is not becoming:

- a generic browser automation tool
- a generic RAG workspace
- a generic notes app
- a free-form agent graph builder
- a generic coding agent shell

APD may eventually use skills, evals, traces, and provider abstractions that resemble broader agent systems, but those capabilities should stay in service of product research rather than turn APD into a general-purpose orchestration framework.

## Harness vs framework

A framework gives a developer parts to assemble.

A harness gives a user or implementer an already-working execution environment with a fixed loop, fixed boundaries, and clear observability.

For APD, that distinction matters.

A framework-style product would expect the user to choose or assemble:

- the research phases
- the prompts
- the tools
- the safety rules
- the source permissions
- the validation logic
- the repair loop
- the review model

A harness-style product should already provide those things.

APD should therefore own:

- the outer research loop
- phase progression and state handoff
- tool boundaries and budgets
- context assembly for each phase
- skill discovery and injection
- model/provider calls
- validation and repair
- source and evidence persistence
- execution traces and replay context
- evals and model scorecards
- the human review surface

The practical test is simple: a user should not have to invent an agent architecture in order to do product research inside APD. The harness should already know how product research runs.

## Current product loop

Today, the concrete product loop in the repo is:

1. Create a research brief.
2. Click `Start Research`.
3. APD generates a bounded query plan.
4. APD calls a configured live search provider.
5. APD triages candidate results into keep, discard, bait, or uncertain.
6. APD validates and fetches only kept safe public URLs.
7. APD stores `Source` and `EvidenceExcerpt` records plus discovery metadata.
8. APD runs grounded component execution against a bounded source packet.
9. APD validates, repairs, and imports draft research objects.
10. The user reviews the imported run through the candidate-first run detail UI.

That loop is still early, but it is already harness behavior. The runtime is no longer just "copy a prompt into another tool and import a JSON file later."

Manual draft import still exists as a legacy or debug path. It should not define the main architectural story anymore.

## Intended research phases

The current implementation groups some work into broader runtime steps such as web discovery and three component batches. The longer-term harness should still think in more explicit research phases, even when multiple phases are currently collapsed into one prompt or one service call.

These phases are conceptual harness phases, not a promise that every phase maps 1:1 to a separate function or model call today.

### `brief_framing`

Purpose:
- turn a raw product curiosity into a bounded research brief with a clear question, constraints, expected outputs, and non-goals

Model role:
- optionally help refine wording, sharpen ambiguity, or propose a better framing

APD harness role:
- persist the brief, keep the user-visible framing surface simple, and decide whether the brief is strong enough to start research

Expected output objects:
- `ResearchBrief`
- optional brief clarification metadata later

Validation and safety checks:
- title and research question present
- product-investigation orientation remains clear
- no external actions or source access yet

### `research_planning`

Purpose:
- decide what kinds of evidence the run should seek before synthesis begins

Model role:
- propose research directions, target source types, and likely evidence needs

APD harness role:
- constrain planning to product research, select relevant skills, and keep the plan bounded by time, source, and context budgets

Expected output objects:
- planning summary metadata
- future trace events and skill selections

Validation and safety checks:
- no tool execution yet
- plan stays within allowed source and budget boundaries

### `web_discovery`

Purpose:
- identify explicit public web targets relevant to the brief

Model role:
- later: help refine search planning when APD adds model-assisted query planning again

APD harness role:
- generate bounded search queries, call the selected search adapter, collect candidate metadata, triage results, reject unsafe URLs, enforce caps, and decide what actually gets fetched

Expected output objects:
- query list
- candidate search result list
- triage decisions with keep/discard reasons
- web discovery execution metadata

Validation and safety checks:
- public `http` or `https` only
- no localhost, loopback, private IPs, credentials, or authenticated sources
- no uncontrolled crawling
- small fixed budgets for query count, candidate-result count, kept fetch count, timeouts, and response size

The first provider integration should stay simple, but the normal product workflow should still use a real search backend. APD now exposes a clean provider interface so Brave Search can serve as the initial live path, while deterministic static/mock providers remain available for tests, evals, and local development.

If no live provider is configured, APD should stop at setup-required discovery status rather than continuing into synthesis with empty results.

### `source_triage`

Purpose:
- decide which fetched material is relevant enough to keep in the run context

Model role:
- later: help identify high-value or low-value sources

APD harness role:
- persist discovery decisions and all captured material that passed safety checks, track fetch failures and rejected targets, and later choose which sources enter the active source packet

Expected output objects:
- `Source`
- source-level summaries or triage annotations later

Validation and safety checks:
- source metadata remains APD-owned
- rejected or failed fetches remain observable
- triage does not silently discard safety-relevant history

Rejected candidates should stay traceable with a reason such as discard, bait, uncertain, invalid URL, duplicate, or fetch failure.

### `evidence_extraction`

Purpose:
- turn fetched source text into bounded, reusable evidence snippets

Model role:
- later: propose better excerpt selection or evidence clustering

APD harness role:
- extract readable text deterministically at first, create excerpts, and keep excerpt size within prompt budgets

Expected output objects:
- `EvidenceExcerpt`
- bounded source packet material for later phases

Validation and safety checks:
- excerpt size caps
- excerpt-to-source linkage preserved
- extraction is traceable back to the captured source

### `grounded_claim_generation`

Purpose:
- produce specific claims about pains, workflows, substitutes, and opportunity conditions using captured evidence

Model role:
- generate claims and evidence-link events grounded in the source packet

APD harness role:
- inject only the relevant source packet and skills, require structured component output, reject invented citations, and require grounded support for claims in grounded mode

Expected output objects:
- `Claim`
- `EvidenceLink`

Validation and safety checks:
- known `source_id` and `excerpt_id` only
- no invented URLs
- at least some grounded supporting evidence in grounded mode

### `theme_synthesis`

Purpose:
- cluster repeated pains, needs, and behavior patterns into reviewable themes

Model role:
- synthesize recurring patterns from grounded claims and excerpts

APD harness role:
- keep theme prompts bounded, preserve traceability to claims and evidence, and avoid letting themes become detached from support

Expected output objects:
- `Theme`
- supporting `EvidenceLink` and relationship objects later

Validation and safety checks:
- themes remain connected to grounded claims or evidence
- synthesis does not replace traceability

### `candidate_generation`

Purpose:
- propose concrete product wedges the user can review, reject, park, validate, or promote later

Model role:
- generate candidate wedges from grounded patterns, workflows, and user pains

APD harness role:
- enforce a candidate-first output shape, require at least one candidate for product-oriented runs, and keep candidate metadata structured enough for later review and build-forward handoff

Expected output objects:
- `Candidate`

Validation and safety checks:
- zero-candidate runs fail the product-quality gate
- candidates must stay product-investigation oriented rather than generic summaries

### `validation_gate_generation`

Purpose:
- identify what must still be learned before a candidate can credibly advance

Model role:
- propose concrete validation gates tied to candidates and research maturity

APD harness role:
- keep gates phase-aware, candidate-linked where possible, and reviewable later

Expected output objects:
- `ValidationGate`

Validation and safety checks:
- phase values stay within APD's maturity model
- gate output remains structured and specific

### `audit_gap_analysis`

Purpose:
- identify missing evidence, overreach, unsupported synthesis, or next research gaps before import or promotion

Model role:
- later: summarize uncertainty and evidence gaps explicitly

APD harness role:
- compare outputs against grounding, validation errors, trace data, and future eval expectations

Expected output objects:
- gap analysis metadata
- follow-up recommendations later

Validation and safety checks:
- unsupported claims are not silently treated as reliable research
- audit findings stay attached to the run and can feed follow-up work

### `import`

Purpose:
- convert validated structured output into APD's durable domain objects

Model role:
- none; import is a harness boundary

APD harness role:
- validate schema, run quality gates, map source and excerpt IDs, import objects transactionally, and fail clearly when the package is invalid

Expected output objects:
- `Run`
- imported `Source`, `EvidenceExcerpt`, `Claim`, `Theme`, `Candidate`, `ValidationGate`, and `EvidenceLink` rows

Validation and safety checks:
- strict schema validation
- import only after quality and grounding checks pass
- duplicate handling and import warnings remain visible

### `human_review`

Purpose:
- turn model-generated research into reviewed product judgment

Model role:
- none by default; human review is first-class, not an optional cleanup step

APD harness role:
- present candidate-first reasoning, preserve review notes and decisions, and distinguish unreviewed draft output from accepted knowledge

Expected output objects:
- review notes
- review statuses
- run and candidate decisions

Validation and safety checks:
- no generated output is treated as accepted truth by default
- review state becomes durable product memory later

### `follow_up_generation`

Purpose:
- turn review outcomes into concrete next actions

Model role:
- later: propose follow-up research, validation plans, or prototype-brief seeds

APD harness role:
- ensure follow-up work is grounded in reviewed outcomes rather than raw synthesis

Expected output objects:
- follow-up tasks
- validation briefs later
- prototype briefs later

Validation and safety checks:
- build-forward outputs depend on human decisions, not just model enthusiasm

## Research tools

APD-controlled research tools are constrained capabilities, not model freedoms.

Current or near-term tools include:

- propose search queries
- propose direct URLs
- validate public URLs
- fetch public URLs
- extract title and readable text
- create `Source`
- create `EvidenceExcerpt`
- build bounded grounding packets
- generate component batches
- validate grounding references
- validate and import a run
- export reports later

The key rule is consistent across all of them:

- the model proposes
- APD validates and executes
- APD persists the result
- APD decides what becomes usable context for later phases

The model should not browse freely, fetch arbitrary URLs, or decide its own permissions. APD should enforce budgets, safety, and persistence around every tool boundary.

## Skills

In APD, skills should be operational instructions, not passive documentation.

That means a skill should describe how to perform a specific research task inside a specific phase, with concrete inputs, output contracts, quality checks, and failure modes.

Future skill work should follow these rules:

- skills are small and phase-specific
- skills are discoverable through a manifest
- skills declare their expected inputs and outputs
- skills are injected only when relevant to the current phase
- APD does not dump the entire skill tree into every prompt

The initial research skill tree now lives under `skills/research/manifest.yaml`. Issue #70 should make skill selection and prompt injection part of the harness runtime.

## Context assembly

The harness is responsible for assembling prompt context for each phase.

That context should be compact and targeted. At a minimum, APD should be able to assemble some combination of:

- brief data
- the current phase objective
- selected skills
- bounded source packet or excerpts
- prior phase summary
- validation errors and repair feedback
- output schema or component contract
- safety constraints and tool limits

Context assembly should be phase-aware and budget-aware.

APD should not:

- dump the full corpus into every prompt
- dump the whole skill tree into every prompt
- include every prior artifact by default
- let repair prompts grow without bounds

Compact prompts are not just a cost concern. They are part of harness correctness. They reduce confusion, make failures easier to interpret, and create cleaner traces for later evals.

## Permission and safety layer

The harness should own a strict permission and safety posture.

Current rules already visible in the repo include:

- only APD-validated public `http` and `https` URLs may be fetched
- no localhost, loopback, private-network targets, or credentialed URLs
- no authenticated or paywalled bypass behavior
- no crawling beyond explicit URLs by default
- no hosted APIs unless they are intentionally added later
- no source-grounding claim should be treated as truth verification

Safety in APD should be practical and enforceable.

The harness should never rely on prompt text alone to stop unsafe behavior. Prompts can ask the model to behave, but APD must still validate tool requests, reject unsafe inputs, and persist the rejection reasons where useful.

## Trace and session persistence

Every meaningful research execution should become observable.

Traces matter because they make it possible to:

- debug failures
- inspect why the model or harness made a choice
- reproduce or replay parts of a run later
- compare harness changes across versions
- support evals and model scorecards
- make research generation auditable rather than mystical

Issue #71 should add a durable research trace or event log for phase starts, tool calls, model calls, validation failures, repair attempts, source capture, and import outcomes.

The architecture point is larger than one storage choice: APD should treat traces as first-class harness data, not as incidental debug printouts.

## Evals and scorecards

APD should eventually measure research quality across separate dimensions instead of treating "looked good in dogfooding" as enough.

Important dimensions include:

- source discovery and retrieval quality
- source safety and rejection behavior
- source triage quality
- evidence extraction quality
- grounding and citation faithfulness
- schema reliability
- synthesis quality
- product usefulness
- review and actionability quality
- runtime cost, latency, and retry rate

Issue #72 should add a controlled eval harness with fixture sources or a mini-web. Issue #73 should add model and harness scorecards that summarize those results across runs or configurations.

The harness should therefore be designed so that phases, tool boundaries, validation outcomes, and trace data can feed evals later without re-architecting the whole runtime.

## Human review inside the harness

Human review is not outside the harness. It is part of the harness.

Generated research in APD remains draft and unreviewed until a person evaluates it.

Human review should therefore:

- accept, dispute, weaken, or dismiss claims
- evaluate themes and candidates in context
- set run and candidate dispositions
- drive follow-up research rather than just annotate reports
- eventually become a signal for evals and accepted knowledge

This matters because APD is not trying to produce a final answer and hide its uncertainty. It is trying to produce structured research that a person can inspect and decide what to do with.

## Near-term architecture map

### Current baseline

APD already has:

- local model settings
- a single `Start Research` UI entry point
- controlled web discovery
- safe public URL validation and fetch
- source and excerpt capture
- grounded component execution using captured sources
- validation, repair, and import gates
- candidate-first run review

### Next harness-maturity steps

The next architectural work should focus on making that loop more explicit, observable, and reusable:

- research harness architecture docs (#68)
- research skill tree and manifest (#69)
- skill discovery and phase prompt injection (#70)
- research trace and event log (#71)
- controlled research eval harness (#72)
- model and harness scorecards (#73)
- deterministic browser smoke coverage for the primary brief workflow (#74)
- broader corpus, review, follow-up, and build-forward workflows after the harness core is stable

## Design posture

When extending APD from here, prefer changes that make the harness more explicit rather than more magical.

Good questions to ask before implementation work:

- Which phase is this change part of?
- What tool boundary does APD own here?
- What context should the model see, and what should it not see?
- What validation or repair gate protects this step?
- What data should be persisted for traceability or evals?
- How will a human inspect the result later?

If a proposed feature makes the runtime harder to audit, harder to bound, or more reliant on model vibes, it is probably pushing APD away from the harness architecture rather than toward it.