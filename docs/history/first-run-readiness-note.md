# First-Run Readiness Note

Archived historical note from the initial bootstrap phase.
The current diagnosis and bootstrap model now live in `docs/launch-diagnosis.md` and `START_HERE.md`.

## Purpose

Capture the specific setup gaps that still needed to be closed before the first live discovery run.

## Remaining gaps observed

- Research guidance existed, but saved evidence did not yet have a stable on-disk corpus structure.
- The repo had living docs, but it did not yet have a predictable home for run-scoped artifacts such as source manifests, evaluation outputs, or generated reports.
- First-run discovery guidance was directionally correct, but it did not yet impose explicit source-count limits, candidate-count limits, or a hard stop after the review package.
- Human review artifacts existed, but claims were not yet anchored to a concrete evidence-ID convention.
- The scripts directory mentioned completeness checks, but no actual readiness checker existed.

## Readiness work required

1. Add a persistent research corpus convention with run-scoped folders, manifests, normalized text, and source notes.
2. Add artifact-output conventions so run outputs and later generated projects land in predictable locations.
3. Add an explicit first-run mode with hard boundaries and stop conditions.
4. Tighten discovery docs so major claims point back to saved evidence.
5. Add a lightweight readiness checker that verifies the framework is prepared for a discovery-first run.