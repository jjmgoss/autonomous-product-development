# Prototype Skill

## Goal

Create the smallest plausible local prototype that proves the selected wedge honestly.

## When To Use

- after discovery and validation already selected one opportunity
- when build-forward mode begins
- when a fresh generated project needs a repeatable local app shape

## Procedure

1. Read the selected run artifacts and the current `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md`.
2. Restate the first buyer, first workflow, first wedge, and prototype success event.
3. Classify the intended result as a UI shell, working demo, or real local prototype.
4. Start from `artifacts/shared/prototype-scaffold/` or `python scripts/init_prototype_scaffold.py` unless there is a clear better fit.
5. Keep the slice narrow enough that one reviewer can run it locally and understand it quickly.
6. Prefer deterministic demo data, simple local persistence when helpful, and boring reliability over cleverness.
7. Add one smoke check and one behavior-oriented check where practical.
8. Write down what is stubbed, what is rough, and what the next milestone should be.

## Expected Outputs

- generated project under `artifacts/projects/<project-slug>/`
- README with setup, run, test, stub, rough-edge, and next-milestone sections
- health check or equivalent sanity hook
- deterministic seed or demo data
- focused verification results

## Common Failure Modes

- reinventing project structure from scratch every run
- building a broad platform instead of one vertical slice
- hiding fake integrations behind polished wording
- writing code without a reproducible local run path
- leaving the prototype class ambiguous