# Release Verification Skill

## Goal

Ensure the release matches requirements and that the claims made about it are honest.

## When to Use
Before claiming a release is complete.

## Procedure
1. Compare implementation to requirements.
2. Confirm that the core user flow actually works.
3. Run smoke tests and any higher-risk checks that still matter.
4. List what works, what is partial, what was not tested, and what remains risky.
5. Check whether the product still matches the chosen wedge instead of a broader imagined product.

## Expected Outputs
- `docs/release.md`
- Honest verification summary

## Common Failure Modes
- Overstating readiness
- Hiding gaps or risks
- claiming product value based on code completion rather than exercised behavior
