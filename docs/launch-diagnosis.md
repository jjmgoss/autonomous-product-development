# Operating Surface Audit

## Authoritative active files

- `START_HERE.md`
- `ACTIVE_RUN.md`
- `DISCOVERY_RUN_MODE.md`
- `DISCOVERY_RUN_PROMPT.md`
- `agent/`
- `scripts/`
- `templates/`

## Supporting reference

- `README.md`
- reusable guides under `docs/`
- product skills under `skills/product/`

## Historical or archive-only

- `docs/history/`
- one-time setup and hardening notes that describe migration events rather than the current operating loop

## Redundant, stale, or confusing patterns to avoid

- root-level compatibility aliases that look like active operating files
- wording that treats a checkpoint label as an automatic pause point
- stale slug hints that silently outrank the current theme
- reviewer artifacts that mention evidence IDs but hide the real URLs

## Wording patterns that encouraged premature stopping

- "stop at Checkpoint 1" when the real intent is only to mark a review milestone
- "default endpoint" without a separate completion-point concept
- launch-success language that sounds like the run is complete once folders exist

## Cleanup direction

- keep the active operating path centered on `START_HERE.md` and `ACTIVE_RUN.md`
- keep checkpoints as review surfaces and make pause behavior explicit in `ACTIVE_RUN.md`
- prefer theme-derived slugs and visible key-source links
- move migration residue out of the active path or remove it entirely when it no longer earns its place

## What a tiny launch prompt was missing

- a single start file
- a canonical active-run selector
- a real supported launcher helper
- explicit run ID collision handling
- explicit response policy for short final chat output

## First-run residue that should no longer act as live operating structure

- one-time setup and hardening summaries at the repo root
- first-run readiness notes that describe a migration event rather than the current operating system
- launch guidance that still implies the repo is waiting for its first-ever use instead of supporting repeatable runs

## Refactor direction

The repo now needs one canonical bootstrap layer, one active-run selector, one supported discovery initializer, generalized readiness checks, and archived historical notes.