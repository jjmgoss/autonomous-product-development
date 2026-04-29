# Open product questions

This document records choices APD should not resolve accidentally.

The current direction is product investigation and guided product development. These questions should be revisited as the app is dogfooded.

## Product scope

### Should APD remain product-investigation-specific?

Current leaning: yes.

APD may use general research techniques, but the early product should stay focused on product opportunities, validation, and prototype readiness.

Open question:

- At what point, if any, should APD broaden into a general research deep-dive platform?

Risk:

- Broadening too early could make the workflow generic and less useful.

## Corpus and accepted knowledge

### What enters the accepted corpus?

Possible options:

- only accepted claims
- accepted claims plus supported themes
- accepted claims, supported themes, and promoted candidates
- every imported object with review status attached

Current leaning:

- Store everything, but visually and operationally distinguish draft, weak, disputed, dismissed, and accepted knowledge.

Open questions:

- Should dismissed claims remain searchable?
- Should disputed claims be hidden by default or surfaced as warnings?
- How should accepted claims be revised if later evidence weakens them?

## Candidate promotion

### What does it mean to promote a candidate?

A candidate is not a statement of fact. Promoting a candidate means choosing what action to take with that opportunity.

Candidate states may include reject, watch, validate_next, prototype_later, and build_approved.

Open questions:

- Should candidate promotion automatically change the run decision?
- Can multiple candidates in one run be promoted?
- Should build_approved require all blocking validation gates to pass, or only require explicit human override?
- Should APD support side-by-side candidate comparison before promotion?

## Review feedback and follow-up research

### What should happen when a user disputes a claim?

Possible next actions:

- record only the user's understanding
- generate a follow-up research task
- ask an agent to find confirming and disconfirming evidence
- prevent the claim from supporting themes or candidates until resolved

Current leaning:

- Record the review first, then use it to generate optional follow-up tasks.

Open questions:

- Which review states should automatically suggest follow-up tasks?
- Should follow-up tasks be run-scoped or corpus-scoped?
- How should APD represent a revised claim after follow-up research?

## Themes

### Are themes durable knowledge objects?

Themes summarize patterns. They may be run-local, or they may become durable corpus concepts.

Open questions:

- Should similar themes across runs be merged?
- Who decides whether two themes are the same?
- Should a theme be allowed to support multiple candidates across runs?

## Reasoning relationships

### How explicit should the reasoning graph be?

The current evidence model links evidence to claims, themes, candidates, and validation gates. The product workflow also needs relationships such as candidate-addresses-theme and theme-supported-by-claim.

Open questions:

- Should these be first-class relationship records?
- Should the draft import schema require them?
- Should APD infer relationships from shared evidence links, or only display explicit links?

Current leaning:

- Add explicit relationships, but keep evidence links as the bottom-layer traceability model.

## Agent execution boundary

### Should APD run the model, or only coordinate external agents?

Current state:

- APD already runs a local-first harness path from a brief.
- The normal flow is brief -> `Start Research` -> controlled web discovery -> source capture -> grounded component execution -> import.
- Manual prompt/import remains a legacy or debug-support workflow, not the primary product loop.

Future options:

- APD calls a configured model provider directly.
- APD coordinates a local agent runner.
- APD remains a review/import workspace and never owns model execution.

Open questions:

- How much of the runtime should stay in a fixed APD-owned harness versus becoming provider-pluggable?
- What is the first additional provider worth integrating, if any?
- Should users bring their own API keys, or should APD stay local-first longer?
- How should APD enforce source permissions and tool boundaries before it has real multi-user auth?
- Which execution details must become durable traces in order to support replay and evals later?

## Source access and integrations

### How much data should an agent be able to access?

Current principle:

- Agents should only access explicitly selected sources for a run.

Open questions:

- Are source packs enough, or does each run need a detailed source permission plan?
- How should APD handle private data in later hosted versions?
- Should derived claims from private sources be marked as private?
- What should happen when a source is deleted or disconnected?

## Build-forward output

### What should APD produce after build approval?

Possible outputs:

- prototype brief
- requirements and non-goals
- validation plan
- GitHub issue drafts
- generated repository scaffold
- runnable local prototype

Current leaning:

- Start with prototype brief and issue drafts before full repository generation.

Open questions:

- How complete should a generated prototype be?
- Should APD create repositories directly, or only produce a build package?
- How should repo-rails be used for generated project setup?
- What counts as success for a prototype generated from APD?

## Hosted or multi-user future

### What must change for APD to become a hosted product?

Likely requirements:

- users
- workspaces
- workspace memberships
- provider connections
- data-source connections
- credential handling
- data isolation
- deletion and purge policy
- private/public export controls

Open questions:

- Is hosted APD a real product direction or only a future option?
- Should local-first usage remain the primary path?
- How should users audit what an agent saw and produced?

## Product success signal

### What would prove APD is useful?

Possible signals:

- User can understand a new product space faster than with a normal LLM report.
- User can trace every candidate recommendation back to claims and evidence.
- User can turn review feedback into better follow-up research.
- User can promote a candidate into a prototype brief with less ambiguity.
- User returns to the corpus to reuse prior accepted claims or themes.

Open question:

- Which of these should be the main dogfood metric for the next milestone?
