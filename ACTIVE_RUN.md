# Active Run

This file is the canonical run selector.

## Current Run

- run type: discovery
- status: ready to launch
- objective: execute a bounded discovery run from `theme.md` and stop at Gate 1 with a review package
- theme file: `theme.md`
- run slug hint: autodev
- boundary file: `DISCOVERY_RUN_MODE.md`
- detailed prompt: `DISCOVERY_RUN_PROMPT.md`
- readiness check: `python scripts/check_repo_readiness.py`
- launcher command: `python scripts/start_discovery_run.py`
- completion check: `python scripts/check_repo_readiness.py --run-id RUN_ID`
- reviewer entry point: `artifacts/runs/RUN_ID/run-index.md`
- stop gate: Gate 1

## Startup Order

1. Read `START_HERE.md`.
2. Read this file and follow the run type named above.
3. Read `theme.md`.
4. Read `agent/runbook.md`, then the files it requires.
5. Run the readiness check.
6. If the readiness check returns `READY`, run the launcher command to create a fresh run path.
7. Populate the required run artifacts and stop at the gate named above.

## Run ID Policy

- Use `python scripts/start_discovery_run.py` to create a fresh run ID unless a human explicitly provides one.
- Never reuse an existing run directory by default.
- If a generated run ID collides, increment `rN` until both `research-corpus/runs/RUN_ID/` and `artifacts/runs/RUN_ID/` are unused.
- Use the same run ID in both trees and in the reviewer-facing summary.

## Response Policy

- Do not assume an unnamed launcher exists.
- Do not stop at a planning response.
- Write the details into artifacts and keep the final chat response short.
- During discovery, stop at Gate 1 unless a human explicitly approves a later stage.