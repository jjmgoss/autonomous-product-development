# Research Skill: Research Audit

## Skill name/id
`research_audit`

## Use when

- APD needs a final gap analysis before import, review, or promotion
- claims or candidates might be overreaching their evidence
- repair feedback or validation errors need to become explicit follow-up items

## Inputs

- claims, themes, candidates, and validation gates
- evidence links and source coverage
- validation errors or repair history if available

## Procedure

1. Look for unsupported claims, weak evidence coverage, and overconfident synthesis.
2. Identify which candidates depend on thin or one-sided evidence.
3. Separate import blockers from non-blocking follow-up questions.
4. Note disconfirming evidence that should stay visible to reviewers.
5. Turn missing evidence into explicit follow-up questions or validation gates.
6. Do not invent new event types to represent the audit if the schema does not support them.

## Output contract

- produce a concise structured audit summary for trace metadata, reviewer notes, or a future audit object
- include unsupported item IDs, missing-evidence areas, disconfirming evidence notes, and follow-up questions when possible
- keep audit output separate from grounded claims and candidate events

## Quality checks

- unsupported synthesis is called out explicitly
- the audit distinguishes blockers from lower-priority gaps
- disconfirming evidence remains visible
- the audit creates actionable follow-up rather than vague doubt

## Failure modes

- silent acceptance of unsupported claims
- treating an audit as generic criticism with no actionable output
- hiding disconfirming evidence to preserve a preferred candidate
- emitting fake component events for audit concepts that APD does not support yet

## Mini example

Good audit finding: "Candidate `candidate-2` relies on one practitioner blog and no direct complaint evidence; gather at least two direct workflow complaints before promotion."

Bad audit finding: "Need more confidence."

## Eval hooks

- measure unsupported-item detection rate
- measure blocker precision
- measure follow-up actionability