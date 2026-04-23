# Framework Hardening Summary

## What stop or review friction was removed

- Checkpoints are now status markers and async inspection surfaces, not default pause points.
- The canonical files now say `continue by default` and reserve approval only for explicit hard boundaries.
- `agent/human-gates.md` was rewritten into a hard-boundary reference instead of a general pause policy.
- Run-index and summary scaffolds now record continuation status instead of a default requested human decision.

## New completion model

- `ACTIVE_RUN.md` now defines the completion point, post-discovery default, and hard boundaries explicitly.
- A completed discovery package is a milestone inside the loop, not an endpoint by itself.
- If a candidate earns a go-now recommendation and no hard boundary applies, the framework now points the agent toward continuing into product brief, requirements, design, roadmap, and backlog work.

## Hard boundaries that still remain

- destructive or hard-to-reverse actions
- deployment or public exposure
- external publishing or outbound communication
- externally consequential tickets, PRs, or issue creation
- financial, credential-sensitive, legal, privacy, or compliance-relevant actions

## Stronger evidence expectations

- The checker now distinguishes broad supporting pages from more concrete evidence and flags runs that lean too heavily on generic sources.
- The run index and discovery summary now require stronger URL visibility.
- Source notes are expected to carry a direct evidence excerpt or key-insights section, not just a title and URL.
- Skills and conventions now push complaint threads, reviews, issues, workarounds, and practitioner evidence ahead of broad category pages.

## Narrower wedge discipline

- The leading candidate must now name a first buyer, first wedge, and why it is not a platform fantasy.
- Templates, prompts, skills, and checker fields all reinforce the smaller sellable wedge instead of broad-platform drift.

## Repo simplification and cleanup

- The canonical operating surface is now clearer: `START_HERE.md`, `ACTIVE_RUN.md`, the named boundary and prompt files, the core agent docs, scripts, and templates.
- An audit note was added in `docs/operating-surface-audit.md` to classify active, supporting, and archival surfaces.
- Transition-era diagnosis and hardening notes are ready to leave the active path and be archived.
- The launcher, checker, and templates now share the same continuation-status contract.

## Prompt for the next lower-cost-model run

Use this prompt:

`Go. Read START_HERE.md and ACTIVE_RUN.md, follow the named boundary file, keep moving through the product-development loop by default, treat milestones as status markers, keep the strongest URLs visible, reject broad platform drift, stop only at a true hard boundary or the named completion point, and end with a suggested commit message.`

## Suggested commit message

`Shift the framework to continue-by-default with stronger evidence and wedge discipline`