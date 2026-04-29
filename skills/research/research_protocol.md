# Research Skill: Research Protocol

## Skill name/id
`research_protocol`

## Use when

- any APD research phase needs a shared evidence and safety discipline
- the model might drift into unsupported synthesis or invented sources
- a repair prompt needs a compact reminder of phase scope and traceability rules

## Inputs

- research brief or phase objective
- current phase name
- source packet or source availability status
- APD output contract and safety constraints

## Procedure

1. Restate the narrow product investigation question in one sentence before producing output.
2. Separate grounded facts from model-prior hypotheses.
3. Use only APD-provided sources, source IDs, excerpt IDs, and URLs for factual claims.
4. Keep output inside the current phase and schema boundary.
5. Prefer repeated workflow pain over broad market chatter or trend summaries.
6. Mark uncertainty explicitly when evidence is weak, conflicting, or missing.
7. Refuse invented citations, fake complaints, and generic platform expansion.

## Output contract

- return only the object type requested by the active phase prompt
- preserve APD field names, IDs, and event types exactly
- label unsupported ideas as model-prior or open questions instead of facts

## Quality checks

- every factual claim is tied to provided evidence or clearly marked as model-prior
- the output stays within the requested phase scope
- the output shape matches the APD schema or event contract
- candidate ideas remain narrow and product-oriented

## Failure modes

- invented sources, citations, or excerpt references
- unsupported claims presented as facts
- phase drift into generic summaries or brainstorming
- output that ignores the requested APD schema

## Mini example

Input: candidate generation for complaints about brittle spreadsheet reconciliation.

Good output: one narrow finance-ops reconciliation QA candidate tied to the provided complaint excerpts.

Bad output: a general AI finance platform with no evidence links.

## Eval hooks

- measure invented-source rate
- measure grounded-claim rate
- measure schema-valid output rate
- measure phase-drift rate