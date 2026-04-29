# Research Skill: Claim Grounding

## Skill name/id
`claim_grounding`

## Use when

- APD is generating claims from a grounded source packet
- the current phase needs claim and evidence-link events
- factual statements must stay tied to known source and excerpt IDs

## Inputs

- grounding packet with source IDs and excerpt IDs
- claim schema or event contract
- brief objective and target workflows

## Procedure

1. Write claims that are specific enough to change product judgment.
2. Tie each factual claim to at least one provided source or excerpt.
3. Prefer claims about repeated pain, substitute behavior, risks, workflow friction, or buyer conditions.
4. Use model-prior language only for hypotheses that are not grounded in the packet.
5. Emit evidence links alongside claims so traceability is explicit.
6. Never invent source IDs, excerpt IDs, URLs, or citations.

## Output contract

- produce `claim.proposed` events for grounded assertions
- produce matching `evidence_link.added` events that reference provided source_id and or excerpt_id values
- keep unsupported ideas out of grounded factual claims

## Quality checks

- every grounded claim has visible evidence support
- claim wording is concrete and falsifiable
- only known source and excerpt identifiers are used
- no invented citations appear in metadata or notes

## Failure modes

- orphan claims with no evidence links
- vague claims that do not influence product judgment
- invented identifiers or URLs
- unsupported synthesis passed off as grounded fact

## Mini example

Good claim: "Finance-ops teams still run manual exception review after automated match rules fail on vendor naming inconsistencies." Supported by one complaint excerpt and one workaround excerpt.

Bad claim: "Most finance teams want AI-native automation" with no packet support.

## Eval hooks

- measure supported-claim rate
- measure invented-identifier rate
- measure claim specificity score