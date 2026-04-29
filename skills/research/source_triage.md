# Research Skill: Source Triage

## Skill name/id
`source_triage`

## Use when

- APD has fetched more source material than should enter the active prompt context
- some sources look weak, duplicative, or off-topic
- the run needs a tighter source packet before claim generation

## Inputs

- captured sources and basic metadata
- brief objective and target workflow
- current context budget
- any known evidence gaps

## Procedure

1. Rank sources by direct relevance to the workflow and pain under investigation.
2. Prefer sources with concrete complaints, workarounds, substitute behavior, or practitioner detail.
3. Keep diversity across source types when possible.
4. Deprioritize generic summaries, duplicate perspectives, and low-signal pages.
5. Reject sources that are off-topic, too shallow, or only supportive background.
6. Record what evidence is still missing after triage.

## Output contract

- produce retained-source and dropped-source decisions with concise reasons
- surface which sources should enter the active grounding packet first
- record missing evidence areas that later phases should respect

## Quality checks

- retained sources are relevant to the brief
- the packet does not collapse to one redundant source type
- low-signal pages do not crowd out concrete evidence
- triage decisions are explainable to a reviewer

## Failure modes

- keeping everything and blowing the prompt budget
- dropping disconfirming evidence because it is inconvenient
- overweighting generic context pages
- making triage decisions with no visible rationale

## Mini example

Keep: a user complaint thread, a practitioner writeup, and a substitute comparison.

Drop or deprioritize: a generic market overview that repeats no workflow details.

## Eval hooks

- measure high-signal-source retention rate
- measure source diversity after triage
- measure disconfirming-evidence retention rate