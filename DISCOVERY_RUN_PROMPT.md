# Recommended Discovery Run Prompt

Use this prompt when the framework should execute the actual discovery-to-planning run through the named completion point with a complete discovery handoff package.

## Prompt

You are operating inside an autonomous product-development framework repository.

This is an execution pass, not a planning-only pass.
Do the work now.
Do not stop after describing intent.
Do not leave partially completed templates behind.

Before doing anything else:
1. Read `START_HERE.md`.
2. Read `ACTIVE_RUN.md` and the boundary file it names.
3. Identify the explicit kickoff mode and direct intent from the user prompt or kickoff command.
4. If direct intent is missing, stop and ask for it instead of inferring it from `theme.md`.
5. Run the readiness check named in `ACTIVE_RUN.md`.
6. If the repo is not `READY`, stop and report the missing framework gaps.
7. If the repo is `READY`, run the kickoff command named in `ACTIVE_RUN.md`.
8. After launch, immediately do the actual discovery work inside the new run paths.
9. Run the completion check named in `ACTIVE_RUN.md` only after the package is fully populated.
10. Read and obey the `completion point`, `post-discovery default`, and `hard boundaries` from `ACTIVE_RUN.md`.

Use `theme.md` only as background defaults and constraints.
The primary research target is the direct kickoff intent, not the defaults file.

Look for monetizable, fully virtual, agent-compatible product opportunities that could be primarily built, operated, maintained, and iterated on through software and agent workflows, with human approval reserved for risky transitions.

Bias toward products that:
- can be sold digitally
- do not require physical inventory, physical delivery, or in-person operations
- can start as a narrow useful wedge
- have one clear first buyer and one clear first workflow
- can be validated and prototyped by a solo operator with agent assistance
- do not depend on large enterprise sales motions before they become useful
- do not require deep proprietary data or compliance-heavy infrastructure at MVP stage

Be skeptical of ideas that are interesting but weakly monetizable, operationally awkward, too broad, or already solved well enough by substitutes.
Treat broad platform visions as a failure mode unless you can name the smaller sellable wedge that should exist first.

Do not implement product code.
Do not deploy anything.
Do not create noisy external side effects.
Do not pause early just because Checkpoint 1 exists.
Do not continue into deployment, publishing, destructive actions, or other hard-boundary work unless `ACTIVE_RUN.md` or a human explicitly approves it.

Important output rule:
- files under `docs/` are reusable framework guides during discovery
- the canonical final outputs for the discovery package belong under `artifacts/runs/<run-id>/review-package/`
- the run root should provide a reviewer-friendly entry point through `artifacts/runs/<run-id>/run-index.md`
- the kickoff command only creates the run shell; it does not complete the manifests or reviewer package for you
- if the recommendation is go-now, continue into the prototype-planning docs named in `ACTIVE_RUN.md`

Required workflow:
1. Follow `START_HERE.md` and `ACTIVE_RUN.md` rather than inventing your own startup path.
2. Use the kickoff helper to create a fresh run ID and initialize matching folders.
3. In `test` mode, save between 6 and 12 meaningful sources and use at least 3 source types when practical.
4. In `real` mode, save between 10 and 24 meaningful sources and use at least 4 source types when practical.
5. Update `research-corpus/runs/<run-id>/manifest.json` as you save sources. It must contain real source entries before the run can stop.
6. Give every serious source a real URL and a source note that repeats that URL near the top.
7. Surface the most important source URLs directly in the run index and discovery summary so a reviewer can inspect them quickly.
8. Research repeated pain and unmet needs in the direct-intent area.
9. Let concrete complaint, workaround, review, issue, and practitioner evidence drive the ranking. Use broad topic hubs only as supporting context.
10. In `test` mode, generate at most 5 serious candidates and score at most the top 3 in detail.
11. In `real` mode, generate at most 7 serious candidates and score at most the top 4 in detail.
12. Keep `research-corpus/runs/<run-id>/candidate-links.md` meaningfully populated with supporting and weakening evidence IDs plus visible supporting links for each serious candidate.
13. Force each serious candidate into a narrow wedge frame: first buyer, first workflow, first pain, first monetization path.
14. Explain why the leading candidate is not a broad platform fantasy.
15. Produce a reviewer-friendly comparison of the strongest candidates.
16. Complete `artifacts/runs/<run-id>/manifest.json` and `artifacts/runs/<run-id>/run-index.md` as part of the required package.
17. Make an explicit recommendation:
   - prototype candidate A first
   - continue validating candidates A and B
   - no current candidate is strong enough
18. Run the completion check named in `ACTIVE_RUN.md` before moving on.
19. Record checkpoint status, recommended next stage, and hard-boundary status in the run index.
20. If the recommendation is `prototype candidate A first` and no hard boundary applies, continue into `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md` before stopping.

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

Completion rules:
- the run is not complete while placeholder bullets remain
- the run is not complete while template prompts such as `Choose one:` or `Explain why.` remain in final artifacts
- the run is not complete while required sections are blank or obviously unresolved
- the run is not complete if only one candidate is developed while the others are just names or thin bullets
- the run is not complete if the manifests are still empty, still marked as launch scaffolds, or missing required entries
- the run is not complete if the run index still reads like a launch scaffold or leaves core reviewer fields unresolved
- the run is not complete if source notes or linked files named in the manifest are missing
- the run is not complete if the run index and summary bury all real URLs in the manifest instead of surfacing key source links directly
- the run is not complete if the completion check fails and the run index does not explain an allowed boundary exception
- a go-now result is not complete while the prototype-planning docs named in `ACTIVE_RUN.md` are still missing or clearly unresolved

For each top candidate, explain:
- target user
- painful workflow
- narrow wedge or MVP angle
- first monetization path
- why existing substitutes are insufficient or good enough
- monetization angle
- why agent-led build and operation are or are not plausible
- why this is not a platform fantasy
- top risks
- why it may fail
- what evidence would overturn the current ranking

Bound the comparison to the strongest few candidates. Favor evidence density and honest tradeoffs over breadth.

Keep chat updates minimal unless blocked.
Write the details into artifacts, not into chat.
Continue by default while discovery and prototype-planning work are still in scope.
Pause only if a hard boundary or blocker requires approval, or if `ACTIVE_RUN.md` explicitly ends the current run at the completed planning package.