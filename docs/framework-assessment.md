# Framework Assessment

## Purpose

Capture the repo-improvement assessment before the vNext polishing pass so later changes stay grounded in specific weaknesses rather than expanding the framework blindly.

## Current architecture in brief

The repository already has the right core shape for autonomous product development:

- one human-edited starting file in `theme.md`
- repo-wide agent operating instructions in `agent/`
- modular skill packs in `skills/`
- living lifecycle artifacts in `docs/`
- lightweight GitHub scaffolding in `.github/`

The intended workflow is coherent: research first, select an opportunity, validate it, define an MVP, decompose the work, implement, verify honestly, and either iterate or stop.

## Strong areas

- The repo already has a strong narrow-MVP bias.
- The anti-slop posture is directionally correct.
- The lifecycle is explicit and reviewable.
- The engineering side is present and modular rather than mixed into product discovery.
- The repo is still small enough for one reviewer to inspect.

## Thin or underpowered areas

- Research guidance is too shallow to help an agent separate repeated pain from isolated complaints.
- Opportunity scoring is too generic to distinguish a buildable tool from a plausible business seed.
- Validation is the thinnest high-stakes stage in the repo.
- Monetization guidance exists as a phrase, not an operational filter.
- Agent-operability is implied but not explicitly assessed.
- Human gate guidance is too light for fast, high-quality review.
- First-run discovery mode is not strong enough yet.

## Overlap or consistency issues

- Evidence checking, critic behavior, and anti-slop guidance overlap without clear role boundaries.
- Opportunity selection terminology is split across skills and docs.
- Research artifacts do not yet cleanly separate raw evidence, candidate ideas, and final comparison.
- Several doc templates are structurally consistent but too generic to improve decision quality.

## Improvement priorities

1. Strengthen research, opportunity selection, and validation so the framework is materially better at finding monetizable virtual products.
2. Add explicit filters for monetization, substitute pressure, and agent-operability.
3. Improve first-run discovery mode so the agent does not rush into implementation.
4. Give human reviewers sharper comparison and gate artifacts.
5. Preserve the existing engineering and verification discipline while tightening naming and reducing duplication.

## Target outcome for this pass

After this upgrade, the repository should be ready for a first real run focused on discovering digital product ideas that:

- are painful enough to matter
- can start narrow
- can plausibly be monetized virtually
- can mostly be built and run by software and agent workflows
- do not depend on heavy compliance, large sales motions, or physical operations at MVP stage