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

Use `YYYYMMDD-theme-slug-rN`.

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
- research and validation docs

## What to save

For each meaningful source:

1. Save the raw capture in `raw/` when possible.
2. Save cleaned text or a normalized markdown summary in `normalized/` when helpful.
3. Create a short source note in `notes/<source-id>.md`.
4. Add an entry to `manifest.json`.

If raw capture is not possible, still create a note and manifest entry explaining what was captured and why full raw storage was not practical.

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

## Candidate linkage

Maintain `candidate-links.md` with a short section for each candidate:

- candidate name
- evidence IDs that support the pain claim
- evidence IDs that weaken or challenge the opportunity
- notes on substitute pressure

## Citation rule

Major claims in these docs should point back to saved evidence IDs:

- `docs/research.md`
- `docs/opportunity-scorecard.md`
- `docs/candidate-review.md`
- `docs/validation.md`

Do not rely on unattributed summaries when a claim materially affects ranking or recommendation.