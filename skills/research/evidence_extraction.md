# Research Skill: Evidence Extraction

## Skill name/id
`evidence_extraction`

## Use when

- APD needs bounded excerpts rather than full source text
- later phases require reusable evidence snippets with source linkage
- the source packet needs to stay within prompt limits

## Inputs

- retained sources or readable source text
- excerpt budget and excerpt-size limits
- target workflow, pain, substitute, and risk questions

## Procedure

1. Pull excerpts that preserve who is speaking, what workflow they are in, and what goes wrong.
2. Prefer concrete evidence over generic opinion.
3. Keep excerpts short enough for prompt reuse without losing meaning.
4. Capture location references when possible.
5. Avoid duplicating the same evidence in slightly different wording.
6. Note why the excerpt matters if the meaning is not obvious from the quote alone.

## Output contract

- produce excerpt candidates with source linkage and excerpt metadata
- preserve fields compatible with APD evidence excerpts, such as source_id, excerpt_text, location_reference, and excerpt_type
- keep any added interpretation separate from the excerpt itself

## Quality checks

- excerpts are linked back to the correct source
- each excerpt contains concrete workflow or pain evidence
- excerpt text is bounded and readable
- interpretation is not mixed into the quote itself

## Failure modes

- excerpts that are too long for prompt reuse
- paraphrases presented as direct evidence without source linkage
- generic excerpts that do not support product judgment
- duplicate excerpts that waste budget

## Mini example

Strong excerpt: a short complaint describing manual invoice matching and the workaround used after the tool fails.

Weak excerpt: a broad statement that automation matters for finance teams.

## Eval hooks

- measure excerpt usefulness for downstream claims
- measure excerpt duplication rate
- measure source-link integrity rate