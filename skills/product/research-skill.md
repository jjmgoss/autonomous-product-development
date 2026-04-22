# Product Skill: Research

Use this skill when exploring a theme for real product opportunities.

## Goal

Find repeated, valuable pain inside a specific workflow and turn that pain into candidate product wedges that can later be scored and validated.

## When to use

- at the start of a new run
- when the current opportunity set is weak
- when validation failed and the search needs to widen again

## Procedure

1. Initialize the research corpus.
	- Create or confirm the current `run-id`.
	- Create the matching folder under `research-corpus/runs/<run-id>/`.
	- Prepare `manifest.json`, `candidate-links.md`, and the `raw/`, `normalized/`, and `notes/` subdirectories.
	- Prepare `artifacts/runs/<run-id>/review-package/research.md` as the canonical research output for the run.

2. Define the user and workflow boundary.
	- Name likely user segments.
	- Name the workflow you are investigating.
	- Avoid vague groups such as "business users" or "creators" unless later narrowed.

3. Gather evidence from multiple source types.
	- Look for issue trackers, forum threads, review sites, Reddit, community discussions, changelog complaints, workflow writeups, and expert commentary.
	- Prefer a mix of direct complaints, workaround descriptions, and evidence of current tool usage.
	- Stay within the source-count limits for the current run mode unless a human explicitly approves a wider pass.

4. Save each meaningful source in the corpus.
	- Assign a stable source ID.
	- Save raw material when practical.
	- Save normalized text or a markdown extraction when helpful.
	- Create a short source note.
	- Add a manifest entry with why the source matters.

5. Log evidence with context, not just quotes.
	- Capture who is speaking, what workflow they are in, what goes wrong, and what they do instead.
	- Separate the source from your interpretation.

6. Synthesize pain patterns.
	- Group complaints that point to the same broken workflow.
	- Separate repeated pain from one-off friction.
	- Treat a pattern as stronger when it appears across multiple sources, users, or contexts.

7. Judge the pain, not just the noise.
	- Distinguish annoying friction from expensive, frequent, risky, or time-consuming pain.
	- Ask whether the pain touches budgets, throughput, quality, compliance risk, or recurring operational work.

8. Name substitutes and workarounds.
	- Record the direct tools, manual processes, spreadsheets, scripts, or service work people use today.
	- Good substitutes can kill an otherwise interesting idea.

9. Generate candidate opportunity wedges.
	- Frame narrow product responses, not full platforms.
	- Each candidate should describe one user, one workflow, one pain point, and one wedge.

10. Apply early fit filters.
	- Can this be sold or monetized digitally?
	- Can it operate mostly virtually?
	- Could a solo operator with agent assistance plausibly build and maintain it?
	- Does it avoid immediate dependence on heavy services, compliance, or enterprise sales?

11. Link candidates back to evidence.
	- Update `candidate-links.md` so each serious candidate has supporting and weakening evidence IDs.
	- Do not let candidate ranking float free from saved sources.
	- If a candidate remains in serious contention, it should have both positive and negative evidence recorded.

12. Capture open questions that matter.
	- Missing evidence is acceptable.
	- Hidden uncertainty is not.

## Research quality rules

- Prefer repeated pain over trend chatter.
- Prefer evidence that reveals current behavior over opinions about future demand.
- Treat generic enthusiasm as weak evidence.
- Treat explicit workarounds, complaints, switching behavior, and budget-linked frustration as stronger evidence.
- Do not confuse a broad market category with a narrow product opportunity.

## Output expectations

`artifacts/runs/<run-id>/review-package/research.md` should make it possible for a reviewer to answer:

- who exactly has the pain
- what recurring workflow is broken
- how they handle it today
- why current tools are insufficient or good enough
- which candidate wedges are emerging
- which candidates already look weak

When multiple candidates survive the research pass, the research artifact should show enough evidence for a reviewer to understand why more than one candidate remained viable.

The strongest claims should cite evidence IDs that exist in the run corpus.

## Common failure modes

- inventing user pain from intuition alone
- treating one vivid complaint as a market pattern
- jumping to solution design before the workflow is concrete
- ignoring substitutes because the new idea feels cleaner
- selecting pain that is real but too small, too rare, or too weakly monetizable
