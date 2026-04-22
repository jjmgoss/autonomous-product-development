# Launch Model Summary

## What changed

- Added `START_HERE.md` as the canonical bootstrap entrypoint.
- Added `ACTIVE_RUN.md` as the canonical active-run selector.
- Generalized the discovery boundary and detailed prompt into `DISCOVERY_RUN_MODE.md` and `DISCOVERY_RUN_PROMPT.md`.
- Added a real discovery initializer and a generalized readiness checker under `scripts/`.
- Archived one-time first-run setup and hardening notes under `docs/history/`.

## How future launch should work

Use a tiny prompt such as: `Go. Read START_HERE.md and execute the active run.`

The model should then:

1. read `START_HERE.md`
2. read `ACTIVE_RUN.md`
3. run the readiness check named there
4. run the launcher named there
5. execute the active run and stop at the named gate

## Human next step before another lower-cost-model test

Review `ACTIVE_RUN.md`, confirm the run type and slug hint still fit the current theme, and then test the repo with the tiny launch prompt above.