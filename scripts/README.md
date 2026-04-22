# Scripts

This directory is intentionally light in the starter scaffold.

As the framework evolves, this is where helper scripts can live for:

- generating labels or milestones from `.github/` docs
- checking repository completeness
- turning docs into issue batches
- validating that required lifecycle artifacts exist

## Included helper

- `check_first_run_readiness.py` verifies that the key files and directories for a discovery-first first run are present.

Run it from the repo root with:

```text
python scripts/check_first_run_readiness.py
```

Do not add automation here unless it clearly improves agent execution quality or human review quality.
