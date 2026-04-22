# Testing Skill

## Goal

Verify that code meets requirements with a level of rigor appropriate to the risk.

## When to Use
After each implementation step and before release.

## Procedure
1. Identify the highest-risk behavior changed.
2. Write targeted tests for new code and changed behavior where feasible.
3. Run the narrowest useful checks first.
4. Broaden testing if the change affects shared paths, data handling, auth, billing-like logic, or release confidence.
5. Document what was tested, what was not tested, and why in `docs/release.md`.

## Risk-based guidance

- Low risk: smoke check or focused automated test may be enough.
- Moderate risk: add targeted automated coverage plus a manual end-to-end check.
- Higher risk: exercise failure paths, data boundaries, and any security- or trust-sensitive flow.

## Expected Outputs
- Test results
- Release evidence

## Common Failure Modes
- Incomplete test coverage
- Not documenting test results
- running broad checks while missing the actual changed behavior
