# Implementation Loop Skill

## Goal

Disciplined, incremental implementation of the MVP without losing the product thesis.

## When to Use
During all coding phases.

## Procedure
1. Restate the issue and acceptance criteria.
2. Inspect the codebase before changing it.
3. Reconfirm that the issue still supports the validated wedge rather than future scope.
4. If a fresh local app is needed, start from the shared prototype scaffold unless there is a clear better fit.
5. Identify the smallest viable change.
6. Implement narrowly.
7. Keep demo behavior deterministic and keep stubs explicit.
8. Run targeted checks first, then broaden testing when needed.
9. Update docs if behavior, scope, or assumptions changed.

## Expected Outputs
- Code changes
- `docs/work-log.md`
- `docs/decision-log.md`

## Common Failure Modes
- Overbuilding
- Skipping verification
- quietly drifting from the selected wedge into a larger product
- polishing or abstracting before the prototype success event is proven
- hiding fake integrations behind confident wording
