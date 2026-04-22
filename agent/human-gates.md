# Human Gates

Use this file to determine when the agent should pause for a human decision.

## Default recommendation

The framework works best when human gates exist at a few high-leverage moments rather than after every tiny action.

## Suggested gate points

### Gate 1: Before coding begins

Require human review after:

- research is completed
- top opportunities are scored
- a candidate comparison artifact exists
- one opportunity is selected or explicitly not selected
- validation results are written
- the discovery summary and run index are complete

Human should check:

- is the problem painful enough to matter, not just interesting to discuss?
- is there clear evidence of recurring pain rather than isolated complaints?
- does the top-ranked idea have a believable narrow wedge?
- is the monetization angle plausible for a digital product?
- is the idea compatible with mostly virtual operations?
- could a solo operator with agents plausibly build and maintain it?
- do substitutes already solve the problem well enough?
- is there a better candidate in the comparison set?

Gate 1 should usually be reviewable from these artifacts:

- `artifacts/runs/<run-id>/run-index.md`
- `artifacts/runs/<run-id>/reports/discovery-summary.md`
- `artifacts/runs/<run-id>/review-package/research.md`
- `artifacts/runs/<run-id>/review-package/opportunity-scorecard.md`
- `artifacts/runs/<run-id>/review-package/candidate-review.md`
- `artifacts/runs/<run-id>/review-package/validation.md`
- `artifacts/runs/<run-id>/review-package/product-brief.md` if an opportunity was selected
- `research-corpus/runs/<run-id>/manifest.json`
- `research-corpus/runs/<run-id>/candidate-links.md`

Gate 1 should not be considered review-ready if the run checker fails, the run index is missing, or any review-package file still looks like an unresolved template.

Gate 1 rejection triggers:

- the target user is still vague
- the product only looks good if many future features land
- willingness to pay is asserted but not argued
- major claims are not traceable to saved evidence
- the review package leaves placeholders, unresolved prompts, or blank sections in final artifacts
- only one candidate is meaningfully developed despite a multi-candidate comparison claim
- the idea requires heavy human services, field work, or compliance before it becomes useful
- the product looks like a demo, not a viable narrow business seed

When `ACTIVE_RUN.md` selects discovery, Gate 1 is also the default stopping point.
Do not continue into implementation unless a human explicitly approves the next stage.

### Gate 2: Before deployment or public exposure

Require human review when:

- the prototype is functionally complete enough to run
- deployment configuration is present
- the agent is about to expose the app or data externally

Human should check:

- security and privacy risk
- whether the app is worth exposing yet
- whether there are obvious quality or cost problems
- whether the support burden is realistic for a solo operator
- whether observability and rollback are good enough for the intended exposure level

### Gate 3: Before merge to the mainline release path

Require human review when:

- the agent believes the prototype is complete
- the release notes are drafted
- verification is done

Human should check:

- does this meet the stated goal?
- is the implementation coherent?
- should the next step be iteration, pivot, or stop?
- are the release claims matched by actual evidence?
- are the remaining risks acceptable for the next step?

## Fully autonomous mode

If the run is configured to be fully autonomous, the agent should still generate the review artifacts that a human would have inspected.
It should not skip the gate outputs just because no one interrupted it.

## Review speed guideline

These gates are meant to help, not to create bureaucracy.

- Gate 1 should be reviewable in 10-20 minutes.
- Gate 2 should be reviewable in 10 minutes if the release and operations artifacts are honest.
- Gate 3 should be reviewable in 10-15 minutes.

If review takes much longer, the agent should tighten the artifacts rather than produce more prose.

The fastest Gate 1 review path should be:

1. run index
2. discovery summary
3. candidate review
4. validation
5. scorecard
6. corpus manifest and candidate-evidence map
