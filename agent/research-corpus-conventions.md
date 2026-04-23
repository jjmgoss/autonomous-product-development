# Research Corpus Conventions

Use these conventions whenever a discovery or validation run gathers external evidence.

## Goals

- keep source material inspectable
- make research claims auditable
- preserve evidence across runs
- separate raw captures from cleaned text and interpretation

## Directory layout

Use this structure:

```text
research-corpus/
  runs/
    <run-id>/
      manifest.json
      candidate-links.md
      raw/
      normalized/
      notes/
  shared/
```

## Run ID convention

Use `YYYYMMDD-intent-slug-rN`.

Prefer `python scripts/autopd.py MODE "DIRECT_INTENT"` to create discovery-run IDs and matching folders.
If you are not using the helper, you must still choose a fresh unused ID and check both run roots before writing files.

Examples:

- `20260421-devtools-r1`
- `20260421-research-automation-r2`

## Source ID convention

Assign stable IDs in capture order:

- `SRC-001`
- `SRC-002`
- `SRC-003`

Use the source ID in:

- `manifest.json`
- normalized filenames when practical
- note filenames
- reviewer-facing run artifacts

## What to save

For each meaningful source:

1. Save the raw capture in `raw/` when possible.
2. Save cleaned text or a normalized markdown summary in `normalized/` when helpful.
3. Create a short source note in `notes/<source-id>.md`.
4. Add an entry to `manifest.json`.

If raw capture is not possible, still create a note and manifest entry explaining what was captured and why full raw storage was not practical.
The manifest alone is not enough. Reviewers should be able to open the saved files named there.
Broad topic hubs, tag pages, and landing pages can be saved as context, but they should not dominate the core evidence set.

## Manifest fields

Each manifest entry should record:

- `id`
- `title`
- `url`
- `captured_at`
- `source_type`
- `run_id`
- `raw_path`
- `normalized_path`
- `note_path`
- `speaker_or_org`
- `workflow`
- `summary`
- `why_it_matters`
- `reliability_notes`

Each serious source should use a real `http` or `https` URL unless the note explicitly explains why that was impossible.
Do not let a placeholder domain or a vague source description count as strong evidence.
Aim for at least several concrete complaint, workaround, review, issue, or practitioner sources in each complete run.

## Candidate linkage

Maintain `candidate-links.md` with a short section for each candidate:

- candidate name
- short thesis
- evidence IDs that support the pain claim
- evidence IDs that weaken or challenge the opportunity
- notes on substitute pressure
- open questions that could overturn ranking

For any serious candidate, do not leave either the supporting or weakening side empty unless you explicitly state why evidence is missing.
Also record the first buyer and first wedge for any serious candidate that remains in contention.

## Citation rule

Major claims in these docs should point back to saved evidence IDs:

- `artifacts/runs/<run-id>/review-package/research.md`
- `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- `artifacts/runs/<run-id>/review-package/candidate-review.md`
- `artifacts/runs/<run-id>/review-package/validation.md`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`

Do not rely on unattributed summaries when a claim materially affects ranking or recommendation.

If a claim refers to a repeated pattern rather than a single-source incident, cite more than one evidence ID when practical.

## Reviewer link visibility

Source notes should repeat the exact URL near the top.
The run index and discovery summary should surface the highest-signal URLs directly so a human can inspect the strongest evidence without manifest archaeology.