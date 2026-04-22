# Artifact Output Conventions

Use these conventions to keep run outputs predictable and reviewable.

## Goals

- keep generated outputs out of random repo locations
- make it easy to inspect one run at a time
- distinguish durable projects from disposable run outputs

## Directory layout

Use this structure:

```text
artifacts/
  runs/
    <run-id>/
      manifest.json
      reports/
      evaluations/
      exports/
  projects/
    <project-slug>/
  shared/
```

## What belongs where

- `artifacts/runs/<run-id>/reports/` stores run summaries and reviewer-facing generated reports.
- `artifacts/runs/<run-id>/evaluations/` stores score exports, ranking tables, or other generated evaluation outputs.
- `artifacts/runs/<run-id>/exports/` stores transformed datasets, text bundles, or other run-scoped exports.
- `artifacts/projects/<project-slug>/` stores generated software projects only after a human-approved go decision.
- `artifacts/shared/` stores reusable helper outputs that are not tied to a single run.

## Naming guidance

- Use the same run ID in both `research-corpus/` and `artifacts/` for the same run.
- Use lowercase kebab-case for project slugs.
- Prefer descriptive filenames such as `discovery-summary.md` or `candidate-ranking.csv` over vague names.

## Artifact manifest

Each `artifacts/runs/<run-id>/manifest.json` entry should record:

- `id`
- `artifact_type`
- `path`
- `created_at`
- `created_by`
- `inputs`
- `purpose`
- `notes`

## Documentation rule

Whenever an agent creates a non-trivial artifact, it should:

1. place it in the correct artifact directory
2. add it to the run manifest
3. mention it in `docs/work-log.md` if it materially changed the run

This keeps later reviewers from having to guess which outputs mattered.