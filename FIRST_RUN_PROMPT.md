# Recommended First-Run Prompt

Use this prompt when the framework's job is to research and propose monetizable, fully virtual, agent-compatible product ideas before any implementation begins.

## Prompt

You are operating inside an autonomous product-development framework repository. Inspect the repository and follow its instructions.

Your goal for this run is discovery-first product research, not coding.

Treat `FIRST_RUN_MODE.md` as a hard boundary file for this run.

Start from `theme.md` and look for product opportunities that could plausibly be monetized entirely or primarily virtually and could be primarily built, operated, maintained, and iterated on through software and agent workflows, with human approval at key checkpoints.

Bias toward products that:
- can be sold digitally
- do not require physical inventory, physical delivery, or in-person operations
- can start as a narrow useful wedge
- can be validated and prototyped by a solo operator with agent assistance
- do not depend on large enterprise sales motions before they become useful
- do not require deep proprietary data or compliance-heavy infrastructure at MVP stage

Be skeptical of ideas that are interesting but weakly monetizable, operationally awkward, or too broad.

Do not rush into implementation. Only recommend coding if one opportunity clearly earns a go decision.

Required workflow:
1. Read the repo instructions and operate in discovery-first mode.
2. Create a run ID using the repo convention and initialize matching folders in `research-corpus/runs/` and `artifacts/runs/`.
3. Save between 6 and 12 meaningful sources with manifest entries, normalized text when useful, and short source notes.
4. Research repeated pain and unmet needs in the theme area.
5. Generate at most 5 candidate opportunities from those pain patterns.
6. Compare the top candidates using the repo's scorecard, monetization, substitute, and agent-operability guidance.
7. Produce a reviewer-friendly comparison of the strongest candidates.
8. Make an explicit recommendation:
   - prototype candidate A first
   - continue validating candidates A and B
   - no current candidate is strong enough

Major claims in the ranking and recommendation should cite saved evidence IDs.
Stop after the review package unless a human explicitly approves a next step.

Required outputs:
- `docs/research.md`
- `docs/opportunity-scorecard.md`
- `docs/candidate-review.md`
- `docs/validation.md`
- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`
- `artifacts/runs/<run-id>/manifest.json`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`
- `docs/product-brief.md` only if one candidate clearly earns a go decision

For each top candidate, explain:
- target user
- painful workflow
- narrow wedge or MVP angle
- why existing substitutes are insufficient
- monetization angle
- why agent-led build and operation are or are not plausible
- top risks
- why it may fail

Bound the comparison to the strongest few candidates. Favor evidence density and honest tradeoffs over breadth.

Finish with a ranked recommendation and an honest statement of what evidence would change your mind.
