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
      run-index.md
      review-package/
      reports/
      evaluations/
      exports/
  projects/
    <project-slug>/
  shared/
```

## What belongs where

- `artifacts/runs/<run-id>/run-index.md` is the reviewer-facing entry point for one run.
- `artifacts/runs/<run-id>/review-package/` stores the canonical Gate 1 review deliverables for that run.
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

The run manifest should include entries for the run index, each review-package file, and the discovery summary.

## First-run review package

The review package should usually contain:

- `review-package/research.md`
- `review-package/opportunity-scorecard.md`
- `review-package/candidate-review.md`
- `review-package/validation.md`
- `review-package/product-brief.md` only if the recommendation is `Go now`

These are the canonical first-run review artifacts.
Do not treat `docs/` as the final run package location.

## Documentation rule

Whenever an agent creates a non-trivial artifact, it should:

1. place it in the correct artifact directory
2. add it to the run manifest
3. mention it in `docs/work-log.md` if it materially changed the run

This keeps later reviewers from having to guess which outputs mattered.

The run index should also tell the reviewer what to read first, whether boundaries were met, and what evidence could overturn the current recommendation.