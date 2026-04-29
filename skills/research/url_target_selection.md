# Research Skill: URL Target Selection

## Skill name/id
`url_target_selection`

## Use when

- APD needs explicit public URLs to validate and fetch
- search results or candidate pages need pruning down to a bounded list
- the run needs safer, higher-value fetch targets

## Inputs

- candidate URLs or source candidates
- research brief and likely workflows
- APD safety rules for public URL fetching
- fetch-count budget

## Procedure

1. Prefer pages that are likely to contain direct user pain, workaround details, or substitute comparisons.
2. Reject URLs that look generic, duplicative, or low-signal.
3. Favor URLs that are public, stable, and specific enough to justify a fetch.
4. Avoid homepages, tag hubs, and trend summaries unless they are supporting context only.
5. Keep the final list small and ranked by expected evidence value.
6. Leave safety enforcement to APD, but do not propose obviously unsafe or private targets.

## Output contract

- produce URL entries compatible with APD's current shape: `url` and `rationale`
- each rationale should explain the expected evidence value of fetching the page
- the list must fit inside APD's explicit URL budget

## Quality checks

- URLs are public `http` or `https` targets
- the list is not dominated by generic landing pages
- rationales are specific to the product investigation
- the final set is small enough to fetch deliberately

## Failure modes

- proposing unsafe, private, or credentialed URLs
- selecting many near-duplicate pages from one domain
- choosing only generic context pages
- using URLs as fabricated citations rather than fetch targets

## Mini example

Good target: a public forum thread where operators describe manual reconciliation steps.

Weak target: a top-level category page with no concrete workflow evidence.

## Eval hooks

- measure fetched-page usefulness rate
- measure unsafe-URL rejection rate
- measure duplicate-domain overuse rate