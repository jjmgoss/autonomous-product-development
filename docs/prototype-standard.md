# Prototype Standard

Use this file to judge whether a thin local product slice is good enough to count as a real prototype.

## Purpose

The goal is not to require polished software.
The goal is to keep future prototypes runnable, understandable, honest, and repeatable.

## Prototype Classes

Every prototype should say which class it belongs to:

- `UI shell`: mostly interface and flow framing; little or no working domain behavior
- `working demo`: the core flow works locally, but major integrations or persistence may still be stubbed
- `real local prototype`: the selected wedge works locally in one end-to-end slice with deterministic demo behavior and honest verification

Do not call something a real local prototype if it is only a UI shell.

## Minimum Standard

A good thin prototype should generally include:

- one narrow vertical slice tied to the selected wedge
- one explicit prototype success event
- one clear local run path
- a README with setup, run, and test instructions
- deterministic demo or seed data
- a health check or equivalent sanity hook
- at least one smoke check and one behavior-oriented test where practical
- a clear statement of what is stubbed, fake, or omitted
- a clear statement of known rough edges
- a short next milestone section
- enough product-doc updates to support continuation without rediscovery

## Recommended Shape

When practical, a local prototype should make these things easy to inspect:

- app entrypoint
- dependency file
- tests
- seed or demo data path
- one happy path
- one failure path
- health check or sanity route
- notes on what is real versus fake

## Honest Stubbing Rules

- Prefer simple real behavior over fake sophistication.
- Prefer deterministic fake integrations over vague simulated magic.
- Say exactly which components are stubbed.
- Keep the fake parts legible enough that a reviewer can tell what would need to become real later.

## Quality Bar

A prototype is good enough when a human reviewer can:

- run it locally
- understand what workflow it proves
- see what is real and what is stubbed
- inspect at least one meaningful verification step
- understand the next milestone without guessing

## Things That Do Not Count

- a repository with only scaffolding and no working wedge behavior
- a UI demo with no meaningful state or workflow logic that is still described as working software
- undocumented seed data or hidden setup steps
- implicit fake behavior that a reviewer cannot detect
- code that runs but has no known-gap statement or next milestone