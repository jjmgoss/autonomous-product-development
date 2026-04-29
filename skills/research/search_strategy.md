# Research Skill: Search Strategy

## Skill name/id
`search_strategy`

## Use when

- APD is planning evidence collection before fetching sources
- the web discovery phase needs better query coverage
- the run risks overfitting to one source type or one vocabulary choice

## Inputs

- research brief
- likely user segments and workflows
- source-count budget and source-type diversity goals
- any existing claims that need confirmation or disconfirmation

## Procedure

1. Translate the brief into a small set of evidence-seeking questions.
2. Generate query variants that target complaints, workarounds, substitutes, and practitioner language.
3. Mix direct pain queries with substitute-comparison queries.
4. Prefer search terms likely to uncover first-person workflow evidence, not generic industry pages.
5. Keep the list short enough that APD can enforce URL and fetch budgets.
6. Avoid query spam, synonyms without purpose, or terms that only produce trend commentary.

## Output contract

- produce a compact query list with short rationales
- each query should imply why that search is likely to surface concrete product evidence
- queries should stay compatible with APD's bounded web-discovery JSON format

## Quality checks

- the query set covers more than one source type
- at least some queries target explicit pain or workaround language
- queries are not just keyword permutations of the title
- the list stays within the configured budget

## Failure modes

- generic topic queries that only surface directories or thought leadership
- too many near-duplicate queries
- no attention to substitute or workaround evidence
- search plans that exceed APD's fetch budget

## Mini example

Better query pair:

- `spreadsheet reconciliation pain month end close`
- `manual invoice matching workaround finance ops`

These are stronger than a generic query such as `finance automation trends`.

## Eval hooks

- measure diversity of returned source types
- measure complaint or workaround source hit rate
- measure wasted-query rate