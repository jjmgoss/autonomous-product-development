# Launch Diagnosis

## Why weaker models invent a launcher

- The repo previously told the model to read several guidance files and run a readiness checker, but it did not name a canonical startup file or a sanctioned launcher.
- The presence of `scripts/` plus a checker encouraged an inference that a matching execution script should exist.
- The old detailed prompt described what a discovery run must produce, but it did not give the repo itself a single executable starting surface.

## What was ambiguous about startup

- The active run mode was implicit instead of being declared in one canonical file.
- The boundary file, detailed prompt, readiness check, launcher, and stop gate were spread across multiple documents.
- The repo did not clearly say that unsupported scripts must not be invented.
- Run ID creation and collision handling were described as conventions rather than as one supported path.

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