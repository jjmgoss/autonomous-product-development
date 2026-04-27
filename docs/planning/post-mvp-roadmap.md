# Post-MVP roadmap

This roadmap starts from the current local APD cockpit: a single-user app that can import structured agent drafts, display runs, support human review, record decisions, export reports, and link legacy artifacts.

The next phase is to turn that cockpit into a product investigation workflow.

## North star

APD should help a user move from a product research question to a reviewed product opportunity and then, when appropriate, to a prototype brief or scaffolded project.

The product loop is:

1. Create a research direction.
2. Generate or import an agent draft.
3. Review the candidate-centered reasoning chain.
4. Accept, dispute, dismiss, or request follow-up on claims and themes.
5. Promote, park, or reject candidates.
6. Generate follow-up research tasks or a prototype brief.
7. Preserve reviewed knowledge in the corpus.

## Phase 1: Make the dogfood loop ergonomic

Goal: reduce friction between research question, agent output, and APD review.

Relevant issues:

- #31 Add research brief creation UI and generated agent prompt
- #32 Add browser-based agent draft import flow
- #34 Add agent draft validation and repair workflow

Expected result:

A user can create a research brief in APD, copy a generated prompt to an external agent, paste the returned draft JSON back into APD, repair/validate it when needed, and immediately review the imported run.

This is still not a fully automated agent runner. It is the minimum product-like workflow before APD starts calling models itself.

## Phase 2: Make run review candidate-centered

Goal: make APD feel like a product investigation cockpit rather than a structured report viewer.

Relevant issues:

- #35 Improve run detail UI for product-research review workflow
- #38 Add explicit reasoning relationship model
- #39 Add theme review surface and semantics
- #40 Refine candidate review and promotion workflow

Expected result:

The user starts with product candidates, then drills down into validation gates, themes, claims, and evidence. The review actions fit the object being reviewed: claims are accepted/disputed/dismissed; themes are supported/weak/merged; candidates are rejected, watched, validated, prototyped later, or approved for build-forward work.

## Phase 3: Turn review into next actions

Goal: make human review feed the next research or product-development loop.

Relevant issues:

- #41 Generate follow-up research tasks from review feedback
- future issue: generate validation brief from candidate gates
- future issue: generate prototype brief from promoted candidate

Expected result:

A disputed claim can become a follow-up research task. A weak theme can request more evidence. A candidate marked validate_next can produce validation questions, source requests, or interview prompts. A candidate marked prototype_later or build_approved can produce a prototype brief.

## Phase 4: Make the corpus first-class

Goal: make accumulated research inspectable and reusable across runs.

Relevant issues:

- #22 Add corpus browser as first-class product surface
- future issue: define accepted knowledge layer
- future issue: search across runs and reviewed knowledge
- future issue: show related runs, recurring themes, and repeated candidates

Expected result:

APD is no longer only a run viewer. It becomes a workspace where sources, claims, themes, candidates, review states, decisions, and artifacts can be inspected across runs.

Accepted or supported knowledge should be visually distinct from unreviewed draft output.

## Phase 5: Add research contexts and source ingestion

Goal: let users prime research runs with selected data sources.

Relevant issues:

- #23 Add source pack model for reusable research contexts
- #24 Add public URL source ingestion
- #28 Add research brief and run config model
- future issue: uploaded-file source ingestion
- future issue: GitHub repository or issue source ingestion

Expected result:

A user can define a source pack, create a research brief, and tell an external or future internal agent what sources are allowed for a run. Source access should be explicit and scoped, not global.

## Phase 6: Prepare for model/provider integrations

Goal: avoid hardcoding APD to one AI provider or runtime.

Relevant issues:

- #25 Add model provider abstraction design and local stubs
- #33 Add future local agent runner design and stub
- #26 Design workspace and user boundary for future multi-user APD

Expected result:

APD has clear boundaries for model providers, source access, and user/workspace ownership. It remains local-first now, but does not paint itself into a corner if a hosted or multi-user version becomes useful.

## Phase 7: Build-forward workflow

Goal: turn a promoted product candidate into useful product-building artifacts.

Future issues should cover:

- prototype brief export
- requirements and non-goals generation
- GitHub issue draft export
- scaffolded repository generation
- repo-rails integration for generated projects
- handoff from APD research run to a build project

Expected result:

When a candidate is sufficiently reviewed and promoted, APD can create a build package. The package may include a prototype brief, requirements, backlog, issue drafts, and possibly a runnable scaffolded repository.

The goal is not to guarantee a production app. The goal is to produce a grounded, inspectable, runnable starting point.

## Recommended near-term order

1. #34 Agent draft validation and repair workflow
2. #31 Research brief creation UI
3. #32 Browser-based draft import flow
4. #35 Candidate-centered run detail UI
5. #38 Explicit reasoning relationships
6. #39 Theme review
7. #40 Candidate promotion
8. #41 Follow-up research tasks
9. #22 Corpus browser

This order keeps the dogfood loop usable while moving the product toward the reviewed product-investigation workflow.
