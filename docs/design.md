# Design

Document the technical design for the prototype or later milestone.

## Architecture Overview

Prefer the simplest architecture that can credibly support the current slice.

Include:

- application entrypoint
- local persistence choice when needed
- deterministic seed or demo data pattern
- health check or sanity hook
- test strategy for the changed behavior
- explicit statement of what is real versus stubbed

## Stack Choices And Rationale

- choose tools that reduce one-off improvisation
- prefer boring local reliability over cleverness
- explain why the chosen stack is good enough for the current stage

## Data Model

- name only the entities the current slice actually needs
- do not design a platform-wide schema before the wedge proves itself

## Major Flows

- describe the happy path the prototype proves
- describe one failure path when practical
- keep later-stage flows separate from the prototype slice

## Interfaces

- list only the interfaces needed now
- mark which interfaces are real, mocked, fixture-backed, or deferred

## Local Run Contract

- explain how a reviewer runs the prototype locally
- explain how seed data is loaded
- explain how tests and smoke checks are run

## Known Rough Edges

- name the rough parts that are acceptable at prototype stage
- say what should move to hardening rather than be hidden in the current design

## Security And Privacy Considerations

- document only the concerns that materially affect the current slice

## Test Strategy

- name the highest-risk behavior
- name the narrowest useful checks to run first
- say what is intentionally not covered yet

## Rule

Prefer the simplest architecture that can credibly support the MVP.
