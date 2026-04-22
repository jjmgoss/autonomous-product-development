# Scripts

This directory is intentionally light in the starter scaffold.

As the framework evolves, this is where helper scripts can live for:

- generating labels or milestones from `.github/` docs
- checking repository completeness
- turning docs into issue batches
- validating that required lifecycle artifacts exist

## Included helper

- `check_repo_readiness.py` validates the canonical bootstrap surfaces and can also validate a completed discovery run package.
- `start_discovery_run.py` creates a fresh discovery run ID, initializes the run directories, and writes manifest stubs.
- `check_first_run_readiness.py` remains as a compatibility wrapper for older prompts.

Only run scripts that are explicitly named in `ACTIVE_RUN.md` or in this file.

Run the readiness check from the repo root with:

```text
python scripts/check_repo_readiness.py
```

Do not add automation here unless it clearly improves agent execution quality or human review quality.
