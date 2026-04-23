# Run Artifacts

Create one folder per run using the same run ID used in `research-corpus/runs/`.

For discovery runs, prefer `python scripts/autopd.py MODE "DIRECT_INTENT"` so the artifact tree and corpus tree are initialized together.

Each run folder should contain:

- `manifest.json`
- `run-index.md`
- `review-package/`
- `reports/`
- `evaluations/`
- `exports/`