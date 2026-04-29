# Research Skill: Theme Synthesis

## Skill name/id
`theme_synthesis`

## Use when

- APD needs repeated pain or behavior patterns grouped into themes
- grounded claims and excerpts are numerous enough to cluster
- the run needs reviewer-friendly synthesis without losing traceability

## Inputs

- grounded claims
- supporting excerpts or evidence links
- target user and workflow context
- theme schema or event contract

## Procedure

1. Group repeated claims that point to the same workflow problem or opportunity condition.
2. Keep themes narrow enough that a reviewer can explain the pattern in one sentence.
3. Preserve the distinction between a repeated pattern and a one-off anecdote.
4. Record supporting evidence or claim references for each theme.
5. Separate pain themes from substitute, risk, or monetization themes when useful.
6. Avoid letting a theme become a generic market story.

## Output contract

- produce `theme.proposed` events for reviewer-facing patterns
- keep supporting evidence references available through evidence links or metadata
- use theme summaries that remain grounded in the underlying claims

## Quality checks

- each theme reflects repeated evidence, not one vivid example
- themes are distinct enough to avoid duplication
- summaries remain connected to grounded claims or excerpts
- themes are useful for later candidate generation

## Failure modes

- themes that are just renamed claims
- evidence-detached synthesis
- collapsing unrelated problems into one broad theme
- trend commentary mistaken for a repeated workflow pattern

## Mini example

Theme: "Exception review remains manual even after rule-based matching" is stronger than "finance automation is broken" because it names the recurring workflow and pain precisely.

## Eval hooks

- measure theme support density
- measure duplicate-theme rate
- measure reviewer usefulness of themes for candidate selection