# Active Run

This file is the canonical run selector.

## Current Run

- run type: discovery
- status: discovery-first and continue-by-default
- objective: execute a bounded discovery run from `theme.md`, choose a narrow wedge, and record the continuation state for the next non-risky stage
- theme file: `theme.md`
- theme slug override: none
- boundary file: `DISCOVERY_RUN_MODE.md`
- detailed prompt: `DISCOVERY_RUN_PROMPT.md`
- readiness check: `python scripts/check_repo_readiness.py`
- launcher command: `python scripts/start_discovery_run.py`
- completion check: `python scripts/check_repo_readiness.py --run-id RUN_ID`
- reviewer entry point: `artifacts/runs/RUN_ID/run-index.md`
- checkpoint label: Checkpoint 1
- checkpoint behavior: status marker only; continue by default
- post-discovery default: if one candidate earns a go-now recommendation and no hard boundary applies, continue into product brief, requirements, design, roadmap, and backlog without waiting
- hard boundaries: destructive actions, deployment or public exposure, external publishing, externally consequential tickets or PRs, purchases or credentials, and other noisy or hard-to-reverse side effects
- completion point: completion-checked discovery package with continuation status recorded and no unresolved scaffold content

## Startup Order

1. Read `START_HERE.md`.
2. Read this file and follow the run type named above.
3. Read `theme.md`.
4. Read `agent/runbook.md`, then the files it requires.
5. Run the readiness check.
6. If the readiness check returns `READY`, run the launcher command to create a fresh run path.
7. Use the launched run path to do the actual discovery work: save sources, update manifests, fill the reviewer artifacts, and complete the run index.
8. Run the completion check only after the package is complete.
9. Record checkpoint status as a milestone, then keep going unless the completion point or a hard boundary says to stop.

## Execution Contract

- The required discovery sequence is: readiness check -> launcher -> research work -> manifest population -> reviewer package completion -> completion check -> checkpoint status update -> continuation decision recorded.
- Launch alone does not count as discovery progress complete.
- The completion check is the last step before stopping, not the next step after launch.
- `artifacts/runs/RUN_ID/run-index.md` must be a reviewer-facing control document, not a stub.
- `research-corpus/runs/RUN_ID/manifest.json` and `artifacts/runs/RUN_ID/manifest.json` are required outputs, not optional bookkeeping.
- Checkpoint labels mark status milestones. They do not by themselves authorize a pause or end the loop.
- Reviewable artifacts are asynchronous inspection surfaces, not default stopping points.
- Broad sources may support context, but concrete complaint, workaround, review, issue, and practitioner evidence should dominate the package.
- If the strongest candidate still looks like a platform fantasy, narrow the wedge before you call the package complete.

## Hard Boundary Policy

- Continue through discovery, validation, planning, local implementation, and local verification by default.
- Ask for approval only at the hard boundaries named above or when a real blocker prevents safe continuation.
- A checkpoint label or reviewable package alone does not require approval.
- If the current run is meant to end at discovery, the completion point says so explicitly. Otherwise keep moving.

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
- During discovery, do not pause just because Checkpoint 1 exists. Follow `completion point`, `post-discovery default`, and `hard boundaries` explicitly.