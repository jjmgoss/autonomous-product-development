# Roadmap

Break the work into stages and milestones that reflect the real maturity of the product.

## Stage Model

- Prototype: prove the wedge locally with one narrow vertical slice
- Hardening: improve reliability, failure handling, and trust without expanding scope
- Polish: improve clarity and usability without pretending the product is already bigger
- Productionization: prepare for deployment, exposure, and support burden

## Milestone Overview

- milestone 1 should deliver one runnable or meaningfully testable slice
- later milestones should either deepen trust in the same wedge or deliberately widen scope with justification

## First Vertical Slice

Name the smallest slice that proves the prototype success event.

The first vertical slice should usually specify:

- who the buyer or user is
- which workflow is being exercised
- what state or data is seeded
- what end-to-end success looks like locally
- what remains intentionally fake or omitted

## Milestone Goals And Acceptance Checks

Each milestone should include:

- goal
- acceptance check
- what changed relative to the earlier stage
- what remains deferred

## Dependencies And Unresolved Risks

- keep this list short and material
- separate risks that block the current slice from later improvement ideas

## Cut-Line Options

- define how to keep the prototype honest if one dependency or design choice becomes too heavy

## Later Improvements Only If Still Credible

- list only improvements that still support the chosen wedge

## Framework Dogfood Roadmap Seed

- AI progress monitor / agent progress observability: a future internal or dogfooded product for monitoring autonomous runs, stages, artifacts, blockers, and outcomes once the framework's prototype scaffold and staged build model are stable enough to support it honestly.
