# Testing Skill

## Goal

Verify that code meets requirements with a level of rigor appropriate to the risk.

## When to Use
After each implementation step and before release.

## Procedure
1. Identify the highest-risk behavior changed.
2. Write at least one smoke check and one behavior-oriented test where feasible.
3. Run the narrowest useful checks first.
4. Include a health check or equivalent sanity hook when practical.
5. Broaden testing if the change affects shared paths, data handling, auth, billing-like logic, or release confidence.
6. Document what was tested, what was not tested, and why in `docs/release.md`.

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
- claiming a runnable prototype without a real local run or sanity check
