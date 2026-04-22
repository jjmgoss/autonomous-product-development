# Product Skill: Discovery Run

## Goal

Run a bounded discovery pass that reaches the active completion point with a fully populated Checkpoint 1 handoff package.

The discovery run is complete only after the middle of the run has happened:

- real sources are saved
- both manifests are populated with real entries
- source-note and linked-file paths actually exist
- candidates are compared with supporting and weakening evidence
- key source URLs are visible in reviewer-facing artifacts
- the run index and review package are fully written
- the completion check passes at the end

## When to use

- a fresh discovery pass for the current theme
- any run where the goal is to decide what to build next
- any run where the current opportunity set is weak or stale

## Sequence

1. Read `START_HERE.md`, `ACTIVE_RUN.md`, and `DISCOVERY_RUN_MODE.md`.
2. Run the readiness check named in `ACTIVE_RUN.md`.
3. Run `python scripts/start_discovery_run.py` to create the run shell.
4. Use the research skill to identify repeated pain and workflow friction.
5. Save each meaningful source, create a source note, and update `research-corpus/runs/<run-id>/manifest.json` as you go.
6. Keep `research-corpus/runs/<run-id>/candidate-links.md` current while the shortlist changes.
7. Limit the serious candidate set to at most 5 ideas and the detailed scorecard to the top 3.
8. Use monetization, substitute, and agent-operability skills on the top few candidates.
9. Complete the reviewer artifacts and record them in `artifacts/runs/<run-id>/manifest.json`.
10. Complete `artifacts/runs/<run-id>/run-index.md` as the reviewer control document, including key source links.
11. Run `python scripts/check_repo_readiness.py --run-id <run-id>` only after the package is complete.
12. Record checkpoint status in the run index and obey `checkpoint behavior` from `ACTIVE_RUN.md`.

## Required outputs

- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`
- `artifacts/runs/<run-id>/manifest.json`
- `artifacts/runs/<run-id>/run-index.md`
- `artifacts/runs/<run-id>/review-package/research.md`
- `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- `artifacts/runs/<run-id>/review-package/candidate-review.md`
- `artifacts/runs/<run-id>/review-package/validation.md`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`

## Completion rule

The package is not complete if:

- placeholders remain
- unresolved prompts remain
- the manifests still read like scaffolds or have empty required lists
- linked source files or notes named in the manifest are missing
- the candidate map is thin or missing weakening evidence or key links
- the run index still looks like a launch note instead of a reviewer-facing control document
- the ranking is not traceable to saved evidence IDs and visible source URLs
- the completion check fails

## Common failure modes

- stopping after launch because the run shell exists
- running the completion check too early and treating the failure as the endpoint
- collecting sources without updating the manifest or creating source notes
- creating the files but leaving the contents structurally incomplete
- producing one attractive candidate and barely developing the alternatives
- editing reusable docs in place instead of writing the run-scoped package