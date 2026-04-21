# Human Gates

Use this file to determine when the agent should pause for a human decision.

## Default recommendation

The framework works best when human gates exist at a few high-leverage moments rather than after every tiny action.

## Suggested gate points

### Gate 1: Before coding begins

Require human review after:

- research is completed
- top opportunities are scored
- one opportunity is selected
- validation results are written
- MVP scope is defined

Human should check:

- is the problem actually interesting?
- is the product too broad?
- is there a more obvious or better direction?

### Gate 2: Before deployment or public exposure

Require human review when:

- the prototype is functionally complete enough to run
- deployment configuration is present
- the agent is about to expose the app or data externally

Human should check:

- security and privacy risk
- whether the app is worth exposing yet
- whether there are obvious quality or cost problems

### Gate 3: Before merge to the mainline release path

Require human review when:

- the agent believes the prototype is complete
- the release notes are drafted
- verification is done

Human should check:

- does this meet the stated goal?
- is the implementation coherent?
- should the next step be iteration, pivot, or stop?

## Fully autonomous mode

If the run is configured to be fully autonomous, the agent should still generate the review artifacts that a human would have inspected.
It should not skip the gate outputs just because no one interrupted it.
