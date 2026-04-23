# Framework Refactor Summary

## What Changed

- kickoff model: direct command-style kickoff is now primary through `python scripts/autopd.py <test|real> "INTENT"`
- mode model: `test` and `real` now have explicit source and candidate bounds enforced by the checker
- intent entry: user intent now enters directly as the launch argument instead of relying on `theme.md` as the primary kickoff surface
- continuation: when discovery reaches go-now and no hard boundary applies, the default continuation path now moves into `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md`
- static skills and guidance: active docs, prompts, runbook, system prompt, scripts README, and related conventions were aligned around the new launcher and continuation model
- rough edges cleaned up: `scripts/start_discovery_run.py` remains only as a deprecation shim, stale legacy references were reduced to intentional archival or compatibility surfaces, and the readiness checker now validates mode-aware run shapes plus the new kickoff metadata

## Real Validation Run

- validation seed: `internal recruiting workflow operations`
- validation command: `python scripts/autopd.py test "Investigate internal recruiting workflow operations and select one narrow, monetizable, agent-compatible software wedge for small teams"`
- validation run ID: `20260422-investigate-internal-recruiting-operations-r1`
- validation result: READY at the current discovery milestone after populating a seven-source run package and exercising the continuation path into the planning docs
- selected wedge: `Hiring Loop Coordinator`, a post-interview feedback and decision-lag workflow layer for small internal recruiting teams

## Next 4.1 Test Run

- suggested prompt: `Investigate customer onboarding handoff operations and select one narrow, monetizable, agent-compatible software wedge for small B2B SaaS teams`
- suggested command: `python scripts/autopd.py test "Investigate customer onboarding handoff operations and select one narrow, monetizable, agent-compatible software wedge for small B2B SaaS teams"`

## Suggested Commit Message

`Refactor kickoff model to direct intent, add test/real modes, and validate with recruiting-ops self-run`