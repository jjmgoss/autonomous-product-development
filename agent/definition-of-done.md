# Definition of Done

A task, issue, milestone, or product stage is not complete just because code was written.

## A task is done when

- the acceptance criteria are satisfied
- the relevant code path is exercised
- tests or checks appropriate to the risk level were run
- affected docs were updated
- remaining caveats are documented

## A milestone is done when

- the promised end-to-end capability exists
- critical user paths were exercised
- dependencies are resolved or explicitly deferred
- known issues are captured

## The MVP is done when

- the core user problem is solved in one real flow
- the product is runnable by a human reviewer
- the behavior is compared against `docs/requirements.md`
- release notes and known gaps are documented

## A no-go decision is done when

- the opportunity was researched and documented
- validation clearly showed it was not worth building or not yet worth building
- the reasons are explicit enough for a future reviewer to understand the call

## Things that do not count as done

- code compiles but no behavior was exercised
- docs exist but contradict implementation
- tests were written but not run
- UI exists but core workflow fails
- claims of success are based on assumptions rather than evidence
