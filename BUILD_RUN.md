# Build Run

Use this file when a completed discovery package has already selected one opportunity and the loop should move into build-forward mode.

## Objective

Build-forward mode exists to turn a validated wedge into the smallest plausible local product slice without pretending the result is already hardened or polished.

Its job is to:

- continue from the selected discovery artifacts instead of reopening the ranking
- build one narrow vertical slice that exercises the first buyer, first workflow, and first wedge
- keep the result runnable, testable, and honest about what is still stubbed
- distinguish prototype work from later hardening, polish, and productionization
- continue by default through local verification unless a hard boundary applies

## Entry Criteria

Do not enter build-forward mode unless the discovery package already names all of these clearly:

- specific first buyer or user
- specific first workflow
- specific first wedge
- specific prototype success event
- credible first monetization path
- explicit reason this is not a broad platform fantasy
- enough evidence to justify the smallest plausible local slice

If any of those are still vague, stay in discovery or validation and tighten the package first.

## Required Sequence

1. Read the selected run index, candidate review, validation, product brief, requirements, design, roadmap, and backlog.
2. Restate the first buyer, first workflow, first wedge, and prototype success event before writing code.
3. Choose the narrowest slice that proves the wedge in a local runnable form.
4. Initialize a generated project under `artifacts/projects/<project-slug>/`, preferably from the shared prototype scaffold.
5. Implement only the prototype slice needed for the success event.
6. Run focused local verification.
7. Update `docs/work-log.md`, `docs/decision-log.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md` when the implementation changes the plan or exposes a better cut line.
8. Stop only at the active completion point or a hard boundary.

## Stage Model

### Prototype

Prototype is a legitimate stage, not a failed polish attempt.

At prototype stage, the product should usually include:

- one narrow vertical slice
- one clear local run path
- deterministic demo or seed data
- one visible happy path
- one failure path where practical
- at least one smoke check and one behavior-oriented test where practical
- a health check or equivalent sanity hook
- a README with setup, run, and test instructions
- an explicit stub list and known rough edges
- a short next milestone statement

Prototype does not require deployment, polished UX, real integrations everywhere, or production-grade operations.

### Hardening

Hardening improves trust and repeatability without expanding the wedge.

Typical hardening work includes:

- better failure handling
- less brittle local persistence
- stronger tests for changed behavior
- clearer release notes and known-gap tracking
- removal of fragile one-off assumptions

### Polish

Polish improves usability, presentation, and reviewer clarity without changing the product thesis.

Typical polish work includes:

- UX cleanup
- copy cleanup
- clearer onboarding or empty states
- less awkward demo behavior
- tighter docs and screenshots when useful

### Productionization

Productionization prepares the product for external use or exposure.

Typical productionization work includes:

- deployment
- operational monitoring
- rollback or recovery planning
- security and privacy controls
- real support burden analysis

This stage is usually a hard-boundary stage because it is closer to noisy or hard-to-reverse actions.

## Completion Rules

Build-forward work is not complete when:

- the code exists but the main workflow was not exercised
- the app has no run instructions
- the result is only a UI shell but is described as a working prototype
- demo data is non-deterministic or missing
- stubs and fake behavior are hidden instead of documented
- tests were written but not run
- the implementation quietly expanded into a broader platform story

## Explicit Prohibitions

- Do not restart discovery from scratch unless the selected run is clearly unusable.
- Do not inflate the prototype into a platform.
- Do not deploy or expose the product publicly without approval.
- Do not create noisy external side effects by default.
- Do not confuse polish with validation.
- Do not hide fake integrations behind polished wording.

## Default Continuation Behavior

Continue by default from prototype into hardening only when the current wedge still looks valid and the next step improves trust or repeatability.

Do not skip directly from prototype to productionization just because the code runs locally.