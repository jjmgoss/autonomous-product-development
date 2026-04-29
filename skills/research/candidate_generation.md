# Research Skill: Candidate Generation

## Skill name/id
`candidate_generation`

## Use when

- APD needs candidate product wedges from grounded research
- themes and claims are strong enough to support product judgment
- the run must avoid broad platform fantasies

## Inputs

- grounded themes and claims
- substitute behavior and risk notes
- product constraints from the brief
- candidate event schema

## Procedure

1. Start from one user, one workflow, and one repeated pain pattern.
2. Frame a narrow wedge rather than a full platform.
3. Name the first buyer or user, first workflow, first wedge, and first prototype success event.
4. Include substitutes, risks, and a plausible first monetization path when possible.
5. Prefer candidates that are specific enough to validate quickly.
6. Reject candidates that depend on vague future expansion to make sense.

## Output contract

- produce `candidate.proposed` events
- include structured candidate fields such as title, summary, target_user, first_workflow, first_wedge, prototype_success_event, monetization_path, substitutes, and risks when the evidence supports them
- keep any missing details visible as open questions rather than hiding them

## Quality checks

- the candidate is narrow and product-investigation oriented
- the candidate has a credible workflow and user boundary
- the wedge can be explained without platform language
- the candidate can be traced back to evidence and themes

## Failure modes

- broad platform ideas with no smallest sellable wedge
- candidate summaries that restate themes without a product response
- no substitutes or risks considered
- missing first workflow or success event for a leading candidate

## Mini example

Stronger candidate: "Reconciliation exception QA for finance-ops teams using spreadsheets and lightweight ERP exports."

Weaker candidate: "AI finance workspace for every back-office process."

## Eval hooks

- measure wedge specificity
- measure evidence traceability for candidates
- measure first-workflow clarity