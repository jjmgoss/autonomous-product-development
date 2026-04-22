# Deployment Readiness Skill

## Goal

Prepare the MVP for deployment with minimal avoidable risk.

## When to Use
After release verification, before deployment.

## Procedure
1. Review deployment assumptions and requirements.
2. Check for missing docs, tests, configs, secrets handling, or environment assumptions.
3. Confirm rollback and monitoring plans.
4. Review privacy, security, support burden, and cost assumptions for the intended exposure level.
5. Confirm whether the MVP is truly ready to be exposed or should remain a private prototype.

## Expected Outputs
- Deployment checklist
- Updated docs

## Common Failure Modes
- Deploying without rollback plan
- Missing monitoring or configs
- exposing an MVP whose support or trust burden exceeds what one operator can handle
