# Launch Model Summary

## What changed

- Added `START_HERE.md` as the canonical bootstrap entrypoint.
- Added `ACTIVE_RUN.md` as the canonical active-run selector.
- Generalized the discovery boundary and detailed prompt into `DISCOVERY_RUN_MODE.md` and `DISCOVERY_RUN_PROMPT.md`.
- Hardened the discovery launcher so it now scaffolds the manifests, run index, summary, and review-package files.
- Hardened the completion checker so it behaves like a final validator instead of a generic next-step action.
- Tightened the templates so the manifests, candidate map, summary, and run index are harder to leave structurally incomplete.
- Reduced live `first-run` wording in the active operating files and moved the canonical discovery skill to `skills/product/discovery-run-skill.md`.
- Added a cleanup utility for empty run directories under `scripts/`.
- Archived one-time first-run setup and hardening notes under `docs/history/`.

## How future launch should work

Use a tiny prompt such as: `Go. Read START_HERE.md, execute the active run end to end, run the completion check last, and stop at the named gate.`

The model should then:

1. read `START_HERE.md`
2. read `ACTIVE_RUN.md`
3. run the readiness check named there
4. run the launcher named there
5. do the actual discovery work inside the launched run paths
6. populate the manifests, candidate map, run index, and reviewer package
7. run the completion check at the end
8. stop at the named gate

## Human next step before another lower-cost-model test

Review `ACTIVE_RUN.md`, confirm the run type and slug hint still fit the current theme, optionally run `python scripts/clean_empty_run_dirs.py --dry-run`, and then test the repo with the tiny launch prompt above.