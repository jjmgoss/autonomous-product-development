# Start Here

This repository is an operating system for autonomous product-development runs.

If the prompt is tiny, start here instead of guessing how to launch the repo.

## Startup Order

1. Read `ACTIVE_RUN.md`.
2. Read the boundary file and detailed prompt named there.
3. Read `theme.md`.
4. Read the repo operating files named in `agent/runbook.md`.
5. Run the readiness check declared in `ACTIVE_RUN.md`.
6. If the active run is discovery and no fresh run has been initialized yet, run the launcher command declared in `ACTIVE_RUN.md`.
7. Execute the run and write details into the run artifacts, not into chat.

## Execution Rules

- Treat `ACTIVE_RUN.md` as the canonical run selector.
- Only run scripts that are explicitly named in `ACTIVE_RUN.md` or `scripts/README.md`.
- Do not invent a missing launcher such as `scripts/first_run_discovery.py`.
- Use the launcher helper when one is provided instead of manually guessing run IDs or folder structure.
- Treat `docs/` as reusable guidance unless the active mode explicitly says otherwise.

## Stop Rule

Stop at the gate or completion point named in `ACTIVE_RUN.md`.
Do not continue into a later stage just because coding feels more concrete.

## Response Policy

- Execute instead of narrating a plan.
- Keep progress chatter minimal unless blocked.
- Keep the final chat response short and point the human to the run index or other named reviewer entry point.
- If a required script or file is missing, say that plainly and continue with the supported path instead of inventing one.