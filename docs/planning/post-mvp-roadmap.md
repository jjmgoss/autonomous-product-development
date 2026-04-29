# Post-MVP roadmap

This roadmap starts from APD's current local-first baseline: a product-research harness that can start from a brief, run a bounded research loop, import structured output, and present the results for candidate-first review.

The roadmap should no longer treat manual prompt copy/paste as the main product path. That workflow still exists as a legacy or debug fallback, but the architectural direction is now harness maturity: APD owns the research loop, the tool boundaries, the validation gates, and the review surface.

## North star

APD should help a user move from a product research question to a reviewed product opportunity and then, when appropriate, to follow-up research, a validation brief, or a build-forward handoff.

The target loop is:

1. Create a research brief.
2. Click `Start Research`.
3. Let APD run a bounded research harness with explicit phases, tools, and safety checks.
4. Review the resulting candidate-centered reasoning chain.
5. Accept, dispute, dismiss, or request follow-up on the generated research.
6. Preserve reviewed knowledge in the corpus.
7. Generate follow-up tasks or build-forward artifacts only after review.

## Current baseline

APD already has the minimum viable harness loop for local dogfooding:

- single `Start Research` brief workflow (#65)
- local model settings (#55)
- controlled web discovery and source capture (#62)
- grounded component execution from captured sources (#63)
- candidate-first run review (#35)

That means the next phase is not "make APD run models at all." The next phase is to make the existing harness architecture explicit, observable, and extensible.

## Near-term harness maturity order

The recommended near-term order is:

1. #65 Single `Start Research` workflow and brief UI cleanup.
2. #62 and #63 Web-assisted and source-grounded execution.
3. #68 Research harness architecture docs and roadmap alignment.
4. #69 Research skill tree and manifest.
5. #70 Skill discovery and injection into phase prompts.
6. #71 Research trace and event log.
7. #72 Controlled research eval harness.
8. #73 Model and harness scorecards.
9. #74 Deterministic browser smoke coverage for the primary brief workflow.
10. #22 Corpus browser and accepted-knowledge surfaces.
11. #38, #39, #40, and #41 Review semantics, reasoning relationships, follow-up tasks, and candidate promotion refinements.
12. Build-forward handoff: validation briefs, prototype briefs, requirements, issue drafts, and scaffolded project outputs.

This ordering reflects a practical dependency chain:

- document the harness
- define the skill layer
- inject skills into the loop
- add traceability
- add evals
- add scorecards
- then expand corpus and post-review workflows on top of a measurable runtime

## Legacy baseline work

Completed or baseline work that should remain supported, but no longer define the main product story:

- #31 Research brief creation UI
- #32 Browser-based draft import flow
- #34 Agent draft validation and repair workflow

Those paths still matter for testing, debugging, or importing externally created drafts. They should be documented as supporting workflows, not as the architectural center of APD.

## Harness maturity workstream

### Phase A: Make the harness explicit

Goal:
- document the runtime as a harness with fixed phases, tools, context assembly, safety rules, traces, and review boundaries

Relevant issues:
- #68 Research harness architecture docs
- #69 Research skill tree and manifest
- #70 Skill discovery and prompt integration

Expected result:
- future implementers understand that APD owns the outer research loop and the model operates inside that loop

### Phase B: Make the harness observable and measurable

Goal:
- make research executions inspectable, replayable, and comparable across harness or model changes

Relevant issues:
- #71 Research trace/event log
- #72 Research eval harness
- #73 Model scorecards
- #74 Browser smoke coverage

Expected result:
- APD can explain what happened during a run, compare harness changes across versions, and measure research quality beyond vibes

### Phase C: Make reviewed knowledge reusable

Goal:
- turn one-off runs into reusable research memory and actionable next steps

Relevant issues:
- #22 Corpus browser
- #38 Explicit reasoning relationships
- #39 Theme review semantics
- #40 Candidate promotion workflow
- #41 Follow-up research tasks

Expected result:
- APD becomes a workspace for accumulated product reasoning rather than only a one-run viewer

### Phase D: Build-forward handoff

Goal:
- turn reviewed candidates into grounded downstream artifacts

Future work should cover:

- validation brief generation
- prototype brief export
- requirements and non-goals generation
- GitHub issue draft export
- scaffolded repository generation
- handoff from APD research runs to build projects

Expected result:
- a reviewed opportunity can become a build package without skipping the research and review loop

## Provider and deployment posture

APD remains local-first for now.

Future provider and deployment work should support the harness architecture rather than bypass it. Provider integrations should fit inside APD's phase boundaries, safety rules, traceability, and eval framework. Hosted or multi-user capabilities remain future design work, not the current product center.
