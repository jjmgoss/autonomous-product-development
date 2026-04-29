# Research Skill: Question Framing

## Skill name/id
`question_framing`

## Use when

- the starting brief is vague, broad, or solution-biased
- APD needs a brief that can support bounded product research
- clarification is needed before web discovery or synthesis begins

## Inputs

- raw user curiosity or product direction
- optional notes, prior context, and explicit constraints
- desired depth or expected outputs if provided

## Procedure

1. Name the likely user and workflow instead of a broad market category.
2. Rewrite the ask as a research question about pain, substitutes, opportunity conditions, or validation needs.
3. Capture hard boundaries, non-goals, and what should not be investigated.
4. Identify which unknowns are blocking the run from starting.
5. Ask clarification questions only when a missing boundary would materially change the run.
6. Avoid turning the brief into a build plan or feature list.

## Output contract

- produce brief-ready fields such as title, research question, constraints, desired depth, expected outputs, and notes
- include clarification questions only when needed to unblock the brief
- record explicit non-goals when the prompt risks drifting into a broad platform search

## Quality checks

- the brief is narrow enough to guide a bounded research run
- the question is product-investigation oriented rather than generic market analysis
- constraints and non-goals are visible
- the wording does not assume a solution is already correct

## Failure modes

- broad market scans with no workflow boundary
- hidden assumptions about the product solution
- feature brainstorming instead of research framing
- missing non-goals that allow scope sprawl

## Mini example

Weak framing: "Find AI tools for finance teams."

Better framing: "Investigate repeated reconciliation pain for finance-ops teams using spreadsheets and lightweight ERP exports, with focus on narrow QA wedges rather than full ERP replacement."

## Eval hooks

- measure brief specificity before and after framing
- measure clarification-question necessity rate
- measure scope-creep rate in downstream phases