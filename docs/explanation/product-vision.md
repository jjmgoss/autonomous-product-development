# APD product vision

APD is a product investigation and guided product-development workspace.

Its job is not to be a generic research archive or a generic coding agent wrapper. Its job is to help a user move from a product research question to a structured understanding of a product space, then to a decision about what to validate, park, reject, or prototype.

The central product loop is:

1. A user enters a product investigation direction.
2. An agent produces a draft research map: sources, excerpts, claims, themes, candidates, validation gates, and evidence links.
3. APD imports that draft as unreviewed structured research.
4. The user reviews the reasoning chain from product candidates back to evidence.
5. The user accepts, disputes, dismisses, or requests follow-up on parts of the map.
6. APD converts that review into next actions: follow-up research, candidate validation, prototype brief, no-go decision, or build approval.

## Positioning

APD should be understood as an overlay over the product-development process.

The differentiation is not simply that an LLM can research or write code. The differentiation is that APD organizes the messy middle between a vague product idea and a buildable direction:

- It turns research into structured, reviewable product reasoning.
- It makes evidence traceable.
- It separates claims about the world from synthesized themes and proposed product candidates.
- It gives the user an explicit review surface.
- It preserves decisions and follow-up needs.
- It can eventually turn a validated candidate into a prototype brief or scaffolded project.

## Primary user job

The user starts from a question like:

> I know little about this space. Help me understand what is happening, what product opportunities might exist, why those opportunities were recommended, and what I should validate next.

The user is not merely reading a report. They are building an internal map of a space.

APD should help them:

- identify product candidates
- understand which pains, workflows, or themes each candidate addresses
- inspect the claims behind those themes
- trace claims back to sources and evidence excerpts
- separate supported claims from weak or disputed ones
- decide which candidate deserves more validation or prototyping

## Product scope

APD may use general research techniques, but the product should stay oriented around product investigation.

Canonical use cases include:

- market pain discovery
- product opportunity research
- competitor and substitute analysis
- customer complaint mining
- prototype prioritization
- validation planning
- guided transition from research to prototype brief

Non-primary use cases include broad academic research, generic document search, generic note-taking, or generic enterprise knowledge management. Those may be adjacent later, but they should not drive the early product shape.

## Expected outputs

A successful APD run should produce more than a prose report.

It should produce:

- candidate product opportunities
- themes or pain patterns
- claims about users, workflows, substitutes, risks, and willingness to pay
- source-backed evidence links
- validation gates that describe what must be learned before advancing
- review state and notes from the human
- an explicit disposition: reject, watch, validate next, prototype later, or build approved

## The build-forward extension

The long-term path may extend beyond research into product creation.

When a candidate is sufficiently reviewed and promoted, APD can eventually generate a prototype brief, a backlog, and possibly a scaffolded GitHub repository. The expected deliverable does not need to be a production-ready business. It can be a runnable prototype or design artifact that the user can inspect, continue developing, or use as inspiration.

The key is that build-forward work should be grounded in reviewed product reasoning rather than raw brainstorming.

## Current constraint

APD is currently local-first and single-user. It should continue to support dogfooding locally while avoiding design choices that block future hosted or multi-user versions.
