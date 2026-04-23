# Framework Hardening Summary

## What changed in the kickoff model

- The framework now takes direct user intent from the kickoff prompt or command.
- The primary launcher is now `python scripts/autopd.py MODE "DIRECT_INTENT"`.
- `theme.md` remains as background defaults and constraints, not as the main run-target surface.

## New mode model

- `test` mode is the compact validation path with 6-12 sources, at least 3 source types, at most 5 serious candidates, and at most 3 deeply scored candidates.
- `real` mode is the deeper path with 10-24 sources, at least 4 source types, at most 7 serious candidates, and at most 4 deeply scored candidates.
- The launcher, scaffolds, and checker now carry mode metadata so validation can follow the active mode instead of one hardcoded discovery shape.

## New completion model

- `ACTIVE_RUN.md` now defines the kickoff model, direct intent source, mode model, completion point, post-discovery default, and hard boundaries explicitly.
- A completed discovery package is still a milestone, not an endpoint by itself.
- If a candidate earns a go-now recommendation and no hard boundary applies, the framework now points the agent into `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md` before stopping.

## Hard boundaries that still remain

- destructive or hard-to-reverse actions
- deployment or public exposure
- external publishing or outbound communication
- externally consequential tickets, PRs, or issue creation
- financial, credential-sensitive, legal, privacy, or compliance-relevant actions

## Stronger evidence expectations

- The checker distinguishes broad supporting pages from more concrete evidence and flags runs that lean too heavily on generic sources.
- The run index and discovery summary require stronger URL visibility.
- Source notes are expected to carry a direct evidence excerpt or key-insights section, not just a title and URL.
- Prompts, docs, and skills push complaint threads, reviews, issues, workarounds, and practitioner evidence ahead of broad category pages.

## Narrower wedge discipline

- The leading candidate must now name a first buyer, first wedge, and why it is not a platform fantasy.
- Prompts, docs, skills, and checker fields all reinforce the smaller sellable wedge instead of broad-platform drift.

## Prompt for the next 4.1 test run

Use this pattern:

`Go. Read START_HERE.md and ACTIVE_RUN.md, run python scripts/check_repo_readiness.py, launch python scripts/autopd.py test "DIRECT_INTENT", fully populate the run package, continue into prototype-planning docs if the winner is go-now, stop only at a true hard boundary or the named completion point, and end with a suggested commit message.`

## Suggested commit message

`Shift kickoff to direct intent with explicit test and real modes`