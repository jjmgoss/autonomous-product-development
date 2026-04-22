# Observability Skill

## Goal

Ensure the MVP is observable enough that failures, usage, and operator burden are visible early.

## When to Use
During implementation and before deployment.

## Procedure
1. Add basic logging for the core flow and the most likely failure points.
2. Define a very small set of meaningful metrics.
3. Include at least one product-value signal and one operator-burden signal when possible.
4. Document the observability setup and remaining gaps in `docs/operations-gap-analysis.md`.

## Good minimum examples

- request or job success and failure counts
- latency for the core workflow
- queue or retry visibility if background work exists
- manual intervention count if the operator has to step in
- simple usage or activation counts for the main wedge

## Expected Outputs
- Observability plan
- Metrics list

## Common Failure Modes
- No monitoring or logging
- Missing key metrics
- tracking vanity metrics while missing failure visibility
