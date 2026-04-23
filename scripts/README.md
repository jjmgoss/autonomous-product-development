# Scripts

This directory contains the supported helper scripts for startup, cleanup, and final validation.

As the framework evolves, this is where helper scripts can live for:

- generating labels or milestones from `.github/` docs
- checking repository completeness
- turning docs into issue batches
- validating that required lifecycle artifacts exist
- cleaning empty run directories left behind by failed or partial launches

## Included helper

- `check_repo_readiness.py` validates the canonical bootstrap surfaces and also serves as the final discovery-package validator.
- `start_discovery_run.py` creates a fresh discovery run ID, initializes the run directories, and writes scaffold files for the manifests, run index, review package, and summary.
- `clean_empty_run_dirs.py` removes only truly empty run subdirectories and reports suspicious partial non-empty run folders.

The startup sequence for a discovery run is:

1. `python scripts/check_repo_readiness.py`
2. `python scripts/start_discovery_run.py`
3. do the actual discovery work inside the launched run paths
4. `python scripts/check_repo_readiness.py --run-id <run-id>`

Do not run the completion check as the next action right after launch.
It is intended for the end of the run, after the manifests and reviewer package are fully populated.
Do not pause at a named checkpoint by default. Treat checkpoints as status markers and inspectable artifacts unless `ACTIVE_RUN.md` explicitly ends the run there.

Only run scripts that are explicitly named in `ACTIVE_RUN.md` or in this file.

Run the readiness check from the repo root with:

```text
python scripts/check_repo_readiness.py
```

To inspect and optionally clean empty leftover run folders:

```text
python scripts/clean_empty_run_dirs.py --dry-run
```

The cleanup utility is intentionally conservative:

- it removes only truly empty nested run directories
- it leaves non-empty directories untouched
- it reports suspicious mismatches such as one-sided run trees or missing manifests

Do not add automation here unless it clearly improves execution quality, evidence quality, or safe continuation through the loop.
