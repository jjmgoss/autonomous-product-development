# Start Here

This repository is an operating system for autonomous product-development runs.

If the prompt is tiny, start here instead of guessing how to launch the repo.

## Startup Order

1. Read `ACTIVE_RUN.md`.
2. Read the boundary file and detailed prompt named there.
3. Read `theme.md` and `agent/runbook.md`.
4. Run the readiness check declared in `ACTIVE_RUN.md`.
5. If the repo is `READY` and the active run names a launcher, run that launcher.
6. Do the actual run work inside the launched paths: save evidence, update manifests, fill artifacts, and record status as you go.
7. Run the completion check declared in `ACTIVE_RUN.md` only after the required package is fully populated.
8. Continue into the next non-risky stage by default unless `ACTIVE_RUN.md` says the current completion point ends the run.

## Execution Rules

- Treat `ACTIVE_RUN.md` as the canonical run selector.
- Only run scripts that are explicitly named in `ACTIVE_RUN.md` or `scripts/README.md`.
- Use the launcher helper when one is provided instead of manually guessing run IDs or folder structure.
- Treat the launcher as scaffold creation, not as the substantive work itself.
- Treat the completion check as a final validator, not as an early probe to run right after launch.
- Do not stop after launch, run-folder creation, scaffold-file creation, or milestone labeling.
- Treat checkpoints as status markers and async review surfaces, not as default pause points.
- Treat `docs/` as reusable guidance unless the active mode explicitly says otherwise.
- Keep the strongest URLs visible in reviewer-facing outputs instead of burying them only in manifests.
- Favor narrow wedges, concrete workflows, and first buyers over broad platforms.

## Stop Rule

Stop only at the completion point named in `ACTIVE_RUN.md` or at a hard boundary that requires approval.
Do not pause early just because a checkpoint label appears in the artifacts.
Do not stop early just because the run launched successfully or a package became reviewable.
Hard boundaries include destructive actions, deployment or public exposure, publishing externally, creating externally consequential tickets or PRs, and other noisy or hard-to-reverse side effects.

## Response Policy

- Execute instead of narrating a plan.
- Keep progress chatter minimal unless blocked.
- Keep the final chat response short and point the human to the current entry point or completion artifact.
- If a required script or file is missing, say that plainly and continue with the supported path instead of inventing one.