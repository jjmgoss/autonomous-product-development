# Product Skill: Requirements

## Goal

Translate a validated opportunity into explicit, testable requirements for a narrow MVP.

## When to use

After a clear go decision.

## Procedure

1. Restate the target user, workflow, and pain in plain language.
2. Define the MVP wedge and what it does not attempt.
3. Write user stories around the core workflow only.
4. Write functional requirements tied to those stories.
5. Write non-functional requirements only where they materially affect trust, speed, privacy, or operability.
6. Add acceptance criteria that a reviewer could actually verify.
7. Record non-goals, commercial assumptions, and operator constraints that must remain true for the MVP to make sense.

## Requirement quality rules

- Every requirement should support the wedge directly.
- Avoid platform requirements unless the MVP cannot function without them.
- If a requirement exists mainly to support a future vision, cut or defer it.

## Expected outputs

- `docs/requirements.md`

## Common failure modes

- vague requirements that cannot be tested
- requirements copied from a larger imagined product
- forgetting the commercial and operator assumptions that justified the idea in the first place
