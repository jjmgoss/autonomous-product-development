# Product Skill: Design Doc

## Goal

Create the simplest technical design that can support the validated wedge credibly.

## When to use

After requirements are defined and before meaningful implementation.

## Procedure

1. Define the core user flow end to end.
2. Choose the smallest architecture that supports that flow.
3. Identify the minimum data model and integrations.
4. Note where a quick technical spike is needed before commitment.
5. Define privacy, security, and cost assumptions appropriate to the MVP.
6. Define the test strategy for the highest-risk paths.

## Design rules

- Start from the wedge, not the imagined platform.
- Prefer reversible choices when uncertainty is high.
- Add infrastructure only when the MVP truly needs it.
- Call out any architecture choice that increases operator burden.

## Expected outputs

- `docs/design.md`

## Common failure modes

- overcomplicating the design to feel serious
- hiding risky assumptions behind diagrams
- choosing architecture that only makes sense for a much larger product
