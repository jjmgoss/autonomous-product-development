# Recommended Discovery Run Prompt

Use this prompt when the framework should execute the actual discovery run and stop at Gate 1 with a complete reviewer package.

## Prompt

You are operating inside an autonomous product-development framework repository.

This is an execution pass, not a planning pass.
Do the work now.
Do not stop after describing intent.
Do not leave partially completed templates behind.

Before doing anything else:
1. Read `START_HERE.md`.
2. Read `ACTIVE_RUN.md` and the boundary file it names.
3. Run the readiness check named in `ACTIVE_RUN.md`.
4. If the repo is not `READY`, stop and report the missing framework gaps.
5. If the repo is `READY`, run the launcher command named in `ACTIVE_RUN.md` and execute the discovery run immediately.

Start from `theme.md` and look for monetizable, fully virtual, agent-compatible product opportunities that could be primarily built, operated, maintained, and iterated on through software and agent workflows, with human approval at key checkpoints.

Bias toward products that:
- can be sold digitally
- do not require physical inventory, physical delivery, or in-person operations
- can start as a narrow useful wedge
- can be validated and prototyped by a solo operator with agent assistance
- do not depend on large enterprise sales motions before they become useful
- do not require deep proprietary data or compliance-heavy infrastructure at MVP stage

Be skeptical of ideas that are interesting but weakly monetizable, operationally awkward, too broad, or already solved well enough by substitutes.

Do not implement product code.
Do not deploy anything.
Do not create noisy external side effects.
Do not continue past Gate 1 unless a human explicitly approves it.

Important output rule:
- files under `docs/` are reusable framework guides and templates
- the canonical final outputs for this run belong under `artifacts/runs/<run-id>/review-package/`
- the run root should provide a reviewer-friendly entry point through `artifacts/runs/<run-id>/run-index.md`

Required workflow:
1. Follow `START_HERE.md` and `ACTIVE_RUN.md` rather than inventing your own startup path.
2. Use the launcher helper to create a fresh run ID and initialize matching folders.
3. Save between 6 and 12 meaningful sources with manifest entries, normalized text when useful, and short source notes.
4. Use at least 3 source types when practical. If you cannot, explicitly explain why in the run index.
5. Research repeated pain and unmet needs in the theme area.
6. Generate at most 5 candidate opportunities from those pain patterns.
7. Score at most the top 3 candidates in detail.
8. Produce a reviewer-friendly comparison of the strongest candidates.
9. Make an explicit recommendation:
   - prototype candidate A first
   - continue validating candidates A and B
   - no current candidate is strong enough
10. Run the completion check named in `ACTIVE_RUN.md` before stopping.

Major claims in the ranking and recommendation must cite saved evidence IDs.
If a claim describes a repeated pattern, back it with more than one evidence ID when possible.

Required outputs:
- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`
- `artifacts/runs/<run-id>/manifest.json`
- `artifacts/runs/<run-id>/run-index.md`
- `artifacts/runs/<run-id>/review-package/research.md`
- `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- `artifacts/runs/<run-id>/review-package/candidate-review.md`
- `artifacts/runs/<run-id>/review-package/validation.md`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`
- `artifacts/runs/<run-id>/review-package/product-brief.md` only if one candidate clearly earns a go-now decision

Completion rules:
- the run is not complete while placeholder bullets remain
- the run is not complete while template prompts such as `Choose one:` or `Explain why.` remain in final artifacts
- the run is not complete while required sections are blank or obviously unresolved
- the run is not complete if only one candidate is developed while the others are just names or thin bullets
- the run is not complete if the completion check fails and the run index does not explain an allowed boundary exception

For each top candidate, explain:
- target user
- painful workflow
- narrow wedge or MVP angle
- why existing substitutes are insufficient or good enough
- monetization angle
- why agent-led build and operation are or are not plausible
- top risks
- why it may fail
- what evidence would overturn the current ranking

Bound the comparison to the strongest few candidates. Favor evidence density and honest tradeoffs over breadth.

Keep chat updates minimal unless blocked.
Write the details into artifacts, not into chat.
Stop only after the full Gate 1 package exists and the run has reached the default discovery endpoint.