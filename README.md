# Autonomous Product Development

This repository is an opinionated framework for autonomous product development, not a generic coding template.

Its job is to help an agent move from a direct user intent to one of two honest outcomes:

1. a validated, narrowly scoped product prototype path with traceable reasoning, or
2. a clearly documented no-go decision.

The repository is now kickoff-command driven.
The human gives the research target directly in the kickoff prompt or command, for example `python scripts/autopd.py test "Investigate ..."`.
`theme.md` remains as a background defaults file, not the main run-target surface.

The canonical bootstrap path is:

1. `START_HERE.md`
2. `ACTIVE_RUN.md`
3. the boundary file and helper commands named there

## What this repo is especially good for

This version is tuned for discovery-stage product runs where the agent should look for opportunities that are:

- fully virtual or mostly virtual to operate
- plausible to monetize digitally
- buildable and maintainable by a solo operator with agent assistance
- narrow enough to prototype quickly
- useful before any large enterprise sales motion or physical-world logistics

The framework biases toward developer tools, workflow tools, automation products, niche SaaS, research/reporting products, monitoring and quality tooling, knowledge tools, and other software-first products with a clear narrow workflow.

## What the agent should do

Use this repository when you want an agent to:

1. research real user pain inside a broad focus area
2. generate candidate product directions from repeated pain patterns
3. compare those candidates using evidence, monetization, and agent-operability filters
4. validate whether one opportunity is worth building now
5. define a narrow MVP and vertical slices
6. implement a repeatable local prototype using a thin scaffold and explicit prototype standard
7. harden, polish, and optionally productionize the product in later stages when the earlier stage is honestly complete
7. compare the result against requirements and decide whether to iterate or stop

## Repo layout

- `START_HERE.md` - canonical repo bootstrap entrypoint for agents
- `ACTIVE_RUN.md` - canonical active-run selector and launch contract
- `theme.md` - background defaults and constraints for kickoff-driven runs
- `DISCOVERY_RUN_MODE.md` - boundary file for discovery-to-planning runs
- `DISCOVERY_RUN_PROMPT.md` - detailed discovery-to-planning prompt when a tiny prompt is not enough
- `agent/` - repo-wide operating instructions, gates, lifecycle map, and conventions
- `skills/product/` - discovery, scoring, validation, monetization, operability, requirements, design, and planning skills
- `skills/engineering/` - prototype, implementation loop, debugging, testing, review, release, and deployment guidance
- `skills/meta/` - anti-slop, evidence, critic, scope-cutting, and stuck-recovery guidance
- `skills/operations/` - observability, incident readiness, and feedback-loop guidance for MVP operation
- `docs/` - reusable framework guides for discovery outputs and later-stage living project docs after a human-approved go decision
- `research-corpus/` - saved raw sources, normalized text, source notes, and candidate-to-evidence links
- `artifacts/` - run-scoped review packages, reports, evaluations, exports, generated projects, and a shared prototype scaffold
- `.github/` - issue templates, labels, milestone notes, and PR template
- `templates/` - reusable status and reporting blocks

## Core operating bias

This framework is intentionally not neutral.

It biases toward:

- real user pain over cleverness
- repeated pain over isolated complaints
- narrow wedges over platform fantasies
- evidence over confidence
- monetizable product seeds over impressive demos
- virtual operations over physical delivery or heavy service layers
- agent-compatible execution over ideas that require large human teams
- honest no-go calls over forced implementation

## Operating model

The default operating mode is continue-by-default.

The agent should:

1. research real workflow pain
2. compare narrow candidate wedges
3. validate the strongest option honestly
4. continue into the next non-risky stage when the active run says to continue
5. stop only at the active completion point or a true hard boundary

The staged build-forward model is now explicit:

- prototype = prove one narrow local slice
- hardening = improve reliability and trust without widening scope
- polish = improve usability and presentation without pretending the product is bigger
- productionization = prepare for deployment, exposure, and support burden

Discovery packages live under `artifacts/runs/<run-id>/`, with `run-index.md` as the reviewer entry point and `review-package/` as the canonical milestone bundle.

Reviewable artifacts are asynchronous inspection surfaces.
They are not automatic pause points.

Hard boundaries remain for destructive actions, deployment or public exposure, external publishing, externally consequential tickets or PRs, purchases or credentials, and other noisy or hard-to-reverse side effects.

## How to use it

1. Decide the direct intent you want the run to investigate.
2. Read `START_HERE.md`.
3. Confirm or update `ACTIVE_RUN.md`.
4. Run `python scripts/check_repo_readiness.py`.
5. Launch the run with `python scripts/autopd.py test "DIRECT_INTENT"` or `python scripts/autopd.py real "DIRECT_INTENT"`.
6. Do the actual discovery work inside the launched run paths.
7. Run `python scripts/check_repo_readiness.py --run-id <run-id>` only after the package is complete.
8. If the result is go-now, continue into `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md` before stopping.
9. If build-forward mode begins, read `BUILD_RUN.md`, `docs/prototype-standard.md`, and initialize `artifacts/projects/<project-slug>/` from `artifacts/shared/prototype-scaffold/` or `python scripts/init_prototype_scaffold.py`.
10. If you need a detailed launch prompt, use `DISCOVERY_RUN_PROMPT.md`.
11. Use `agent/human-gates.md` only for true hard-boundary decisions.
12. Review the run through `artifacts/runs/<run-id>/run-index.md`, then inspect the saved evidence in `research-corpus/` and any later-stage planning docs in `docs/`.

For discovery runs, prefer direct-intent slugs and visible source links in the run index and summary over stale config hints or manifest-only evidence.

## Modes

`test` mode is the compact validation path.
Use it when you want one strong bounded pass with full completion discipline and a lightweight continuation into prototype planning if a winner emerges.

`real` mode is the deeper execution path.
Use it when you want more evidence, more disconfirming work, and a stronger continuation push into prototype-planning docs.

## Expected output from a strong run

A strong run should leave behind:

- research grounded in repeated pain and substitutes
- a saved research corpus with evidence IDs and notes
- a ranked set of candidate opportunities
- explicit monetization and agent-operability judgments
- an explicit first buyer, first workflow, and first wedge for any leading candidate
- an explicit prototype success event and first monetization path before coding begins
- a clean run-scoped review package with a clear reviewer entry point
- a selected product brief or a justified no-go
- clear requirements, design, and roadmap artifacts if the idea earns a go decision
- a prototype that says whether it is a UI shell, working demo, or real local prototype
- deterministic demo data, a clear local run path, and honest notes on what is stubbed
- honest verification and lifecycle review

## Practical warning

Autonomous product development usually fails before implementation.

The failure mode is not that the agent cannot write code. It is that the agent picks weak ideas, overstates validation, ignores substitutes, or chooses products that are not viable for a solo operator with software and agent workflows.

This repository is built to make those mistakes harder.

## Local app skeleton (issue #4)

The repository now includes a minimal local app foundation for the APD cockpit backend.

### Install dependencies

```text
uv sync --extra dev
```

### Run tests

```text
./scripts/test.ps1
python scripts/check_repo_readiness.py
```

### Database migrations (SQLite via Alembic)

```text
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"
```

### Start the local app

```text
uv run uvicorn apd.app.main:app --reload
```

Then open `http://127.0.0.1:8000/health` and expect:

```json
{"status":"ok"}
```

### Seed deterministic fixture data (issue #6)

Seed one synthetic fixture run for local demos/tests:

```text
uv run python scripts/seed_fixture.py
```

The command is idempotent by default and will not duplicate fixture records.

To explicitly reset fixture-owned records and reseed:

```text
uv run python scripts/seed_fixture.py --reset-fixture
```

To remove fixture-owned records only, without reseeding:

```text
uv run python scripts/seed_fixture.py --reset-only
```

### View the local web UI (issue #7)

After seeding fixture data, start the app and open the browser UI:

```text
uv run uvicorn apd.app.main:app --reload
```

Then open `http://127.0.0.1:8000/runs` in a browser.

- `/runs` — recent-runs list. Shows each run's title, phase, decision, recommendation, source/claim/theme/candidate counts, and a link to its detail page. Fixture runs are labeled.
- `/runs/{run_id}` — run detail page. Shows run intent, summary, recommendation, phase, decision, sources, claims (with review status), themes, candidates, validation gates, artifacts, and evidence traceability.
- `/` — redirects to `/runs`.

To seed and view the fixture run against a throwaway database:

```text
$env:APD_DATABASE_URL = "sqlite+pysqlite:///./.local/apd_demo.db"
uv run alembic upgrade head
uv run python scripts/seed_fixture.py
uv run uvicorn apd.app.main:app --reload
```

Open `http://127.0.0.1:8000/runs` — the fixture run should appear. Click its title to open the run detail page.
