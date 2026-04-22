# Active Run

This file is the canonical run selector.

## Current Run

- run type: discovery
- status: ready to execute discovery run
- objective: execute a bounded discovery run from `theme.md` and produce a complete discovery handoff package for Checkpoint 1
- theme file: `theme.md`
- theme slug override: none
- boundary file: `DISCOVERY_RUN_MODE.md`
- detailed prompt: `DISCOVERY_RUN_PROMPT.md`
- readiness check: `python scripts/check_repo_readiness.py`
- launcher command: `python scripts/start_discovery_run.py`
- completion check: `python scripts/check_repo_readiness.py --run-id RUN_ID`
- reviewer entry point: `artifacts/runs/RUN_ID/run-index.md`
- checkpoint label: Checkpoint 1
- checkpoint behavior: continue unless blocked
- completion point: completion-checked discovery handoff package ready for Checkpoint 1 review

## Startup Order

1. Read `START_HERE.md`.
2. Read this file and follow the run type named above.
3. Read `theme.md`.
4. Read `agent/runbook.md`, then the files it requires.
5. Run the readiness check.
6. If the readiness check returns `READY`, run the launcher command to create a fresh run path.
7. Use the launched run path to do the actual discovery work: save sources, update manifests, fill the reviewer artifacts, and complete the run index.
8. Run the completion check only after the package is complete.
9. Record checkpoint status in the run index and stop only when the completion point named above has been reached.

## Execution Contract

- The required discovery sequence is: readiness check -> launcher -> research work -> manifest population -> reviewer package completion -> completion check -> checkpoint status update -> completion point reached.
- Launch alone does not count as discovery progress complete.
- The completion check is the last step before stopping, not the next step after launch.
- `artifacts/runs/RUN_ID/run-index.md` must be a reviewer-facing control document, not a stub.
- `research-corpus/runs/RUN_ID/manifest.json` and `artifacts/runs/RUN_ID/manifest.json` are required outputs, not optional bookkeeping.
- Checkpoint labels mark review surfaces. They do not by themselves authorize a pause or implementation.

## Checkpoint Policy

- `continue`: keep moving through the active run unless a risky action or blocker requires human input.
- `continue unless blocked`: the default for discovery. Keep going until the named completion point is satisfied or a real blocker appears.
- `pause for human review`: stop after the completion check and handoff package, then wait for explicit human direction.

## Run ID Policy

- Use `python scripts/start_discovery_run.py` to create a fresh run ID unless a human explicitly provides one.
- Never reuse an existing run directory by default.
- If a generated run ID collides, increment `rN` until both `research-corpus/runs/RUN_ID/` and `artifacts/runs/RUN_ID/` are unused.
- Use the same run ID in both trees and in the reviewer-facing summary.
- Derive the run slug from the current `theme.md` by default.
- Use `theme slug override` only when the human intentionally wants a different slug.

## Response Policy

- Do not assume an unnamed launcher exists.
- Do not stop at a planning response, a launch response, or a completion-check failure.
- Write the details into artifacts and keep the final chat response short.
- During discovery, do not pause just because Checkpoint 1 exists. Follow `checkpoint behavior` and `completion point` explicitly.