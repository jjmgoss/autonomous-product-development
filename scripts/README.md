# Scripts

This directory contains the supported helper scripts for startup, cleanup, and final validation.

As the framework evolves, this is where helper scripts can live for:

- generating labels or milestones from `.github/` docs
- checking repository completeness
- turning docs into issue batches
- validating that required lifecycle artifacts exist
- cleaning empty run directories left behind by failed or partial launches
- initializing a reusable local prototype scaffold for build-forward mode

## Included helpers

- `check_repo_readiness.py` validates the canonical bootstrap surfaces and also serves as the final discovery-package validator.
- `autopd.py` is the primary kickoff helper. It accepts `test` or `real` plus a direct intent, creates a fresh run ID, initializes the run directories, and writes scaffold files for the manifests, run index, review package, and summary.
- `init_prototype_scaffold.py` copies the shared prototype scaffold into `artifacts/projects/<project-slug>/` so build-forward runs start from one coherent local app shape.
- `start_discovery_run.py` is the older theme-driven launcher and should not be used for the active kickoff model.
- `clean_empty_run_dirs.py` removes only truly empty run subdirectories and reports suspicious partial non-empty run folders.

The startup sequence for a discovery-to-planning run is:

1. `python scripts/check_repo_readiness.py`
2. `python scripts/autopd.py test "DIRECT_INTENT"` or `python scripts/autopd.py real "DIRECT_INTENT"`
3. do the actual discovery work inside the launched run paths
4. `python scripts/check_repo_readiness.py --run-id <run-id>`
5. if the recommendation is go-now, continue into the planning docs named in `ACTIVE_RUN.md`

The first steps for build-forward mode are:

1. confirm that discovery and validation already selected one prototype-ready wedge
2. read `BUILD_RUN.md` and `docs/prototype-standard.md`
3. initialize `artifacts/projects/<project-slug>/` from the shared scaffold
4. implement only the smallest credible local slice
5. run focused local verification and update the product docs honestly

Do not run the completion check as the next action right after launch.
It is intended for the end of the discovery package, after the manifests and reviewer package are fully populated.
Do not pause at a named checkpoint by default. Treat checkpoints as status markers and inspectable artifacts unless `ACTIVE_RUN.md` explicitly ends the run there.

Only run scripts that are explicitly named in `ACTIVE_RUN.md` or in this file.

Run the readiness check from the repo root with:

```text
python scripts/check_repo_readiness.py
```

Kick off a compact validation run with:

```text
python scripts/autopd.py test "DIRECT_INTENT"
```

Kick off a deeper execution run with:

```text
python scripts/autopd.py real "DIRECT_INTENT"
```

Initialize a reusable local prototype project with:

```text
python scripts/init_prototype_scaffold.py my-project-slug --title "My Project"
```

To inspect and optionally clean empty leftover run folders:

```text
python scripts/clean_empty_run_dirs.py --dry-run
```

To seed deterministic APD fixture/demo data into the configured local database:

```text
python scripts/seed_fixture.py
```

To explicitly reset fixture-owned data and reseed:

```text
python scripts/seed_fixture.py --reset-fixture
```

To import or link an existing legacy APD run by run ID without mutating legacy files:

```text
python scripts/import_legacy_run.py --run-id 20260422-kickoff-smoke-r1
```

The legacy import script is read-only against `research-corpus/runs/<run-id>/` and `artifacts/runs/<run-id>/`. It creates database records and warnings only; it does not rewrite manifests or Markdown files.

The cleanup utility is intentionally conservative:

- it removes only truly empty nested run directories
- it leaves non-empty directories untouched
- it reports suspicious mismatches such as one-sided run trees or missing manifests

Do not add automation here unless it clearly improves execution quality, evidence quality, or safe continuation through the loop.
