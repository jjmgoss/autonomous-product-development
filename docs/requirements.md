# Requirements

Translate the selected product into explicit prototype and later-stage requirements.

## User Stories

- capture the first buyer or user stories only
- keep them tied to the selected wedge
- include one happy path and one failure path where practical

## Functional Requirements

- list only the functional requirements needed for the first vertical slice
- state what working behavior is required for the prototype success event
- separate real behavior from intentionally stubbed behavior

## Non-Functional Requirements

- local run path should be understandable without hidden steps
- product code should stay small, legible, and boringly reliable
- demo behavior should be deterministic
- verification should be runnable locally by a human reviewer

## Constraints

- restate the scope boundary from the product brief
- name any integration, trust, compliance, or data constraints that materially limit the first slice

## Acceptance Criteria

- include one prototype success event that a reviewer can actually observe
- include one smoke check expectation
- include one behavior-oriented verification expectation where practical
- say what would still count as incomplete even if the app launches

## Prototype Documentation Expectations

- README with setup, run, and test instructions
- clear statement of prototype class
- health check or equivalent sanity check behavior
- explicit stub list
- explicit known rough edges
- explicit next milestone

## Non-Goals

- name the tempting adjacent scope that should stay out of the prototype
- say what later-stage work belongs in hardening, polish, or productionization instead

## Edge Cases That Matter For The MVP

- list only the edge cases that materially affect trust in the prototype

## Rule

Requirements should be tight enough to guide implementation and verification, but not bloated with speculative future needs.
