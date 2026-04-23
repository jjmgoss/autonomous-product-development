# Active Run

This file is the canonical run selector.

## Current Run

- run type: discovery-to-planning
- status: direct-intent kickoff, mode-aware, and continue-by-default
- objective: accept direct kickoff intent, run discovery in explicit `test` or `real` mode, choose a narrow wedge, and continue into prototype-planning docs when one opportunity clearly earns a go-now recommendation
- intent source: direct kickoff command or explicit user prompt
- defaults file: `theme.md` for background defaults only
- mode model: `test` = compact validation run, `real` = deeper execution run
- boundary file: `DISCOVERY_RUN_MODE.md`
- detailed prompt: `DISCOVERY_RUN_PROMPT.md`
- readiness check: `python scripts/check_repo_readiness.py`
- kickoff command: `python scripts/autopd.py MODE "DIRECT_INTENT"`
- completion check: `python scripts/check_repo_readiness.py --run-id RUN_ID`
- reviewer entry point: `artifacts/runs/RUN_ID/run-index.md`
- checkpoint label: Checkpoint 1
- checkpoint behavior: status marker only; continue by default
- post-discovery default: if one candidate earns a go-now recommendation and no hard boundary applies, continue into `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md` before stopping
- hard boundaries: destructive actions, deployment or public exposure, external publishing, externally consequential tickets or PRs, purchases or credentials, and other noisy or hard-to-reverse side effects
- completion point: completion-checked discovery package with continuation status recorded; if the recommendation is go-now, continue into prototype-planning docs before stopping unless a hard boundary blocks that move

## Startup Order

1. Read `START_HERE.md`.
2. Read this file and follow the run type named above.
3. Identify the direct kickoff intent and explicit mode from the user prompt or kickoff command. If either is missing, ask instead of guessing.
4. Read `theme.md` for defaults and `agent/runbook.md` for operating instructions.
5. Run the readiness check.
6. If the readiness check returns `READY`, run the kickoff command to create a fresh run path.
7. Use the launched run path to do the actual discovery work: save sources, update manifests, fill the reviewer artifacts, and complete the run index.
8. Run the completion check only after the package is complete.
9. Record checkpoint status as a milestone, then follow `post-discovery default` unless the completion point or a hard boundary says to stop.

## Execution Contract

- The required sequence is: readiness check -> kickoff command -> research work -> manifest population -> reviewer package completion -> completion check -> continuation decision recorded.
- Launch alone does not count as discovery progress complete.
- The completion check is the last step before stopping, not the next step after launch.
- `artifacts/runs/RUN_ID/run-index.md` must be a reviewer-facing control document, not a stub.
- `research-corpus/runs/RUN_ID/manifest.json` and `artifacts/runs/RUN_ID/manifest.json` are required outputs, not optional bookkeeping.
- Checkpoint labels mark status milestones. They do not by themselves authorize a pause or end the loop.
- Reviewable artifacts are asynchronous inspection surfaces, not default stopping points.
- Broad sources may support context, but concrete complaint, workaround, review, issue, and practitioner evidence should dominate the package.
- If the strongest candidate still looks like a platform fantasy, narrow the wedge before you call the package complete.
- `test` mode is a bounded validation pass.
- `real` mode is a deeper pass with more evidence, more disconfirming work, and stronger continuation pressure into prototype planning.

## Hard Boundary Policy

- Continue through discovery, validation, planning, local implementation, and local verification by default.
- Ask for approval only at the hard boundaries named above or when a real blocker prevents safe continuation.
- A checkpoint label or reviewable package alone does not require approval.
- If the current run is meant to end at discovery or planning, the completion point says so explicitly. Otherwise keep moving.

## Run ID Policy

- Use `python scripts/autopd.py MODE "DIRECT_INTENT"` to create a fresh run ID unless a human explicitly provides one.
- Never reuse an existing run directory by default.
- If a generated run ID collides, increment `rN` until both `research-corpus/runs/RUN_ID/` and `artifacts/runs/RUN_ID/` are unused.
- Use the same run ID in both trees and in the reviewer-facing summary.
- Derive the run slug from the direct kickoff intent by default.
- Use `--slug` only when the human intentionally wants a different slug.

## Response Policy

- Do not assume an unnamed launcher exists.
- Do not infer the direct research target from `theme.md` when the kickoff command or user prompt is available.
- Do not stop at a planning response, a launch response, or a completion-check failure.
- Write the details into artifacts and keep the final chat response short.
- During discovery, do not pause just because Checkpoint 1 exists. Follow `completion point`, `post-discovery default`, and `hard boundaries` explicitly.