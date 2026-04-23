# Run Corpora

Create one folder per run using the run ID from `ACTIVE_RUN.md` and the boundary file it names.

For discovery runs, prefer `python scripts/autopd.py MODE "DIRECT_INTENT"` so the run ID and matching artifact tree stay aligned.

Example:

- `research-corpus/runs/20260421-devtools-r1/`

Each run folder should contain:

- `manifest.json`
- `candidate-links.md`
- `raw/`
- `normalized/`
- `notes/`

The matching reviewer-facing outputs for the same run should live in `artifacts/runs/<run-id>/`.