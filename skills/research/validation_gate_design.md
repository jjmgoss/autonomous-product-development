# Research Skill: Validation Gate Design

## Skill name/id
`validation_gate_design`

## Use when

- APD needs explicit blockers before a candidate can advance
- candidates have promise but still carry evidence gaps or risk
- the run is preparing reviewer-facing validation work

## Inputs

- candidate IDs and candidate summaries
- current research phase model
- open risks, substitute pressure, and missing evidence
- validation gate event schema

## Procedure

1. Identify what must be true before a candidate can credibly move forward.
2. Write gates as concrete checks, not generic reminders.
3. Link gates to the right candidate whenever possible.
4. Match the gate to APD's phase vocabulary.
5. Distinguish between blocking gaps and useful but non-blocking follow-up questions.
6. Prefer a few high-value gates over a noisy checklist.

## Output contract

- produce `validation_gate.proposed` events
- include candidate_id, phase, name, description, blocking, evidence_summary, and missing_evidence when supported
- keep gate wording specific enough that a reviewer knows what evidence would satisfy it

## Quality checks

- each gate is tied to a real uncertainty or risk
- gate language is specific and testable
- phase values stay inside APD's maturity model
- candidate linkage is present when relevant

## Failure modes

- vague gates such as "do more validation"
- gates that duplicate the candidate summary instead of testing it
- missing candidate linkage for candidate-specific blockers
- too many low-value gates that hide the important ones

## Mini example

Strong gate: "Confirm at least three finance-ops teams will pay for exception review QA before replacing spreadsheet checks."

Weak gate: "Validate product-market fit."

## Eval hooks

- measure gate specificity
- measure gate-to-candidate linkage rate
- measure blocker usefulness in later review