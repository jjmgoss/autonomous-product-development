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

## A prototype is done when

- one narrow vertical slice works locally
- deterministic demo or seed data exists
- a README explains setup, run, and test steps
- a health check or equivalent sanity hook exists
- at least one smoke check and one behavior-oriented check were run where practical
- the result says whether it is a UI shell, working demo, or real local prototype
- stubs and known rough edges are documented

## A hardening milestone is done when

- the same wedge is more trustworthy without becoming broader
- fragile assumptions are reduced or documented
- verification is stronger for the highest-risk behavior

## A polish milestone is done when

- usability or reviewer clarity improves without overstating product maturity
- the work does not hide missing core functionality behind presentation

## Productionization is done when

- the product is ready for the intended exposure level
- deployment or recovery expectations are explicit
- operational and support burdens are understood well enough for the current stage

## A no-go decision is done when

- the opportunity was researched and documented
- validation clearly showed it was not worth building or not yet worth building
- the reasons are explicit enough for a future reviewer to understand the call

## A discovery package is done when

- the run-scoped review package exists under `artifacts/runs/<run-id>/review-package/`
- the run index exists and points the reviewer to the right files
- the corpus manifest and candidate-evidence map exist
- source-count and candidate-count boundaries are met or explicitly justified
- major ranking and recommendation claims cite saved evidence IDs
- no final artifact still contains unresolved template prompts, placeholders, or blank required sections
- the discovery summary explains both the case for the winner and the reasons it may still fail
- the package was checked at the end of the run rather than immediately after launch

## Things that do not count as done

- code compiles but no behavior was exercised
- docs exist but contradict implementation
- tests were written but not run
- UI exists but core workflow fails
- claims of success are based on assumptions rather than evidence
- framework templates were edited in place and mistaken for completed run outputs
- a summary exists but the candidate comparison is too thin to support the ranking
