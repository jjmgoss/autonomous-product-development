# Recommended First-Run Prompt

Use this prompt when the framework's job is to research and propose monetizable, fully virtual, agent-compatible product ideas before any implementation begins.

## Prompt

You are operating inside an autonomous product-development framework repository. Inspect the repository and follow its instructions.

Your goal for this run is discovery-first product research, not coding.

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
2. Research repeated pain and unmet needs in the theme area.
3. Generate candidate opportunities from those pain patterns.
4. Compare the best candidates using the repo's scorecard, monetization, substitute, and agent-operability guidance.
5. Produce a reviewer-friendly comparison of the top candidates.
6. Make an explicit recommendation:
   - prototype candidate A first
   - continue validating candidates A and B
   - no current candidate is strong enough

Required outputs:
- `docs/research.md`
- `docs/opportunity-scorecard.md`
- `docs/candidate-review.md`
- `docs/validation.md`
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

Finish with a ranked recommendation and an honest statement of what evidence would change your mind.
