# Framework Hardening Summary

## What this pass fixed

- Softened checkpoint behavior for discovery runs: checkpoints are now review surfaces, while pause behavior is set explicitly in `ACTIVE_RUN.md`.
- Reduced stale theme and slug leakage by deriving launch slugs from `theme.md` by default and warning on legacy mismatches.
- Surfaced real web links more clearly by reserving reviewer-facing key-source-link sections in the run index, discovery summary, candidate map, and source notes.
- Hardened evidence traceability by expecting saved source-note and linked-file coverage instead of manifest-only completeness.
- Cleaned up active wording around hard stops, launch-only success, and migration-era first-run language.
- Kept the empty-run cleanup utility as the lightweight maintenance path for stray scaffolds.

## How checkpoints work now

Use the checkpoint label as a milestone and review surface.
Keep going until the named completion point is satisfied.
Pause only if `ACTIVE_RUN.md` explicitly says `checkpoint behavior: pause for human review` or if a blocker or risky action requires approval.

## Next lower-cost-model prompt

Use this prompt:

`Go. Read START_HERE.md, execute the active run through the named completion point, record checkpoint status in the artifacts, run the completion check last, and continue unless ACTIVE_RUN.md says to pause.`

## Suggested commit message

`Harden discovery checkpoints, evidence traceability, and legacy surface cleanup`