# Product research review model

APD separates different kinds of research objects because they mean different things and should be reviewed differently.

A claim is not a theme. A theme is not a candidate. A candidate is not a decision to build. Review states should reflect those differences.

## Claims

Claims are propositions about the world.

Examples:

- Small teams struggle to tune alerts after their first production deployment.
- Managed observability substitutes win because they reduce maintenance burden.
- Restore confidence matters more than backup creation alone.

Claim review answers: do we believe this proposition enough to use it?

Suggested claim dispositions:

- `unreviewed`: Imported or generated, not yet evaluated by a human.
- `accepted`: True enough, with current evidence, to use in reasoning.
- `weak`: Plausible but under-supported.
- `disputed`: Possibly wrong, contradicted, or misleading.
- `dismissed`: Not useful for this run, out of scope, or too low quality.
- `needs_followup`: Important enough to investigate further.

Current implementation may not support all of these states yet. The concept should guide future changes.

## Themes

Themes are synthesized patterns across claims, workflows, user pains, or substitutes.

Examples:

- Observability burden is cumulative, not one-time.
- Managed substitutes win when support is part of the offer.
- Deploy simplicity beats infrastructure flexibility in the first wedge.

Theme review answers: is this a useful and sufficiently supported pattern?

Suggested theme dispositions:

- `unreviewed`: Imported or generated, not yet evaluated.
- `supported`: A useful synthesis supported by enough claims/evidence.
- `weak`: Interesting but not yet supported strongly.
- `duplicate_or_merge`: Overlaps another theme and should be merged or reframed.
- `dismissed`: Not useful or too vague.
- `needs_more_evidence`: Useful but needs more support before driving candidate decisions.

Themes should eventually show which claims support them and which candidates they help motivate.

## Candidates

Candidates are product opportunities or product wedges.

Examples:

- Compose Ops Wrapper for single-app production.
- Observability Autopilot for self-hosted stacks.
- Restore Drill Assistant for self-hosted stateful apps.

Candidate review does not mean accepting the candidate as true. A candidate is not a proposition; it is a possible direction.

Candidate review answers: what should we do with this opportunity?

Suggested candidate dispositions:

- `unreviewed`: Imported or generated, not yet evaluated.
- `reject`: Do not pursue this direction.
- `watch`: Keep it in the corpus, but do not act yet.
- `validate_next`: Worth focused validation work.
- `prototype_later`: Promising, but not the immediate next build.
- `build_approved`: Human-approved for prototype brief or build-forward work.

This differs from claim review. A claim can be accepted as true; a candidate should be advanced, parked, rejected, or promoted.

## Validation gates

Validation gates are the checklist that moves a candidate forward.

A gate names a required learning milestone, such as:

- Confirm buyer urgency.
- Prove default alert packs reduce maintenance.
- Test willingness to pay against managed incumbents.

Gate review answers: what must be learned before this candidate can advance?

Suggested gate states:

- `not_started`: No validation work has been done.
- `in_progress`: Validation is underway.
- `weak`: Some evidence exists, but not enough.
- `passed`: The gate is sufficiently satisfied for the current stage.
- `failed`: The gate failed and should block or redirect the candidate.
- `not_applicable`: The gate no longer applies.

## Run decisions

A run decision is the disposition of the overall research run.

It should answer: what should happen after reviewing this run?

Suggested run decisions:

- `archive`: Keep the record, but do not pursue.
- `watch`: Keep the area under observation.
- `publish`: Turn the reviewed run into a public or private report.
- `prototype_later`: Preserve as a promising future prototype direction.
- `build_approved`: Move into prototype brief or build-forward workflow.

## Review as human understanding

Review is valuable even before any agent follow-up exists.

The user is using APD to build their own map of a product space. Review actions should make that map clearer by distinguishing accepted claims, weak claims, disputed reasoning, useful themes, and candidate priorities.

## Review as agent feedback

Review should also become input to future agent loops.

Examples:

- A disputed claim can generate a follow-up research task.
- A weak theme can request more supporting claims or better sources.
- A promising candidate can request validation gates and interview questions.
- A rejected candidate can teach the agent what not to propose again.
- An accepted claim can enter the durable corpus as reusable knowledge.

This feedback loop is a core future product direction.

## Design principle

Do not collapse all review into one generic status.

Different object types need different review semantics. The UI may use shared controls where practical, but the product meaning should remain explicit.
