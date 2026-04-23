# Operating Surface Audit

Date: 2026-04-22

## Canonical Active Operating Surface

- `START_HERE.md`: canonical bootstrap entrypoint for tiny prompts
- `ACTIVE_RUN.md`: canonical run selector, run goal, completion point, and hard-boundary summary
- `theme.md`: canonical human-edited direction and product-shape constraints
- `DISCOVERY_RUN_MODE.md`: canonical discovery boundary and package contract
- `DISCOVERY_RUN_PROMPT.md`: detailed run-facing prompt when the launch prompt is too small
- `agent/runbook.md`: canonical practical operating behavior across stages
- `agent/system-prompt.md`: canonical repo-local behavioral contract for the agent
- `agent/repo-conventions.md`, `agent/research-corpus-conventions.md`, `agent/artifact-output-conventions.md`: canonical storage and output rules
- `scripts/check_repo_readiness.py` and `scripts/start_discovery_run.py`: canonical launcher/checker contract
- `templates/`: canonical scaffold shapes for run outputs

## Supporting Reference

- `README.md`: human-readable repo overview, should stay shorter than the canonical operating files
- `skills/product/*.md`: reusable discovery and evaluation heuristics
- `skills/meta/*.md`, `skills/engineering/*.md`, `skills/operations/*.md`: later-stage support guidance
- `scripts/README.md`: helper-script reference, not the main operating contract
- `agent/human-gates.md`: should become a hard-boundary reference instead of a pause policy
- `agent/lifecycle-map.md`, `agent/definition-of-done.md`, `agent/orchestration-v3.md`: useful background, not startup-critical
- `docs/*.md`: framework references and later-stage living docs after a candidate earns continued execution

## Archive Or History

- `docs/history/*`: already archival
- `docs/discovery-run-hardening-note.md`: transition-era hardening note, not part of the active path
- `docs/framework-assessment.md`: assessment snapshot, not operational guidance
- `docs/launch-diagnosis.md`: diagnosis history, not canonical startup behavior

## Redundant Or Nearly Redundant

- `START_HERE.md`, `ACTIVE_RUN.md`, `DISCOVERY_RUN_MODE.md`, `DISCOVERY_RUN_PROMPT.md`, `README.md`, and `agent/runbook.md` all restate launch order, checkpoint behavior, and discovery stopping rules
- `agent/human-gates.md` overlaps with `ACTIVE_RUN.md` and `DISCOVERY_RUN_MODE.md` on when discovery should pause
- `LAUNCH_MODEL_SUMMARY.md` overlaps with hardening notes and is better used as the one current top-level summary rather than another quasi-operational file
- templates repeat checkpoint and review wording that no longer matches the intended continue-by-default loop

## Main Sources Of Remaining Friction

- discovery is still described as a handoff endpoint in too many places rather than as one stage in a longer loop
- checkpoint language is everywhere, so weaker models still over-index on it even when the text says not to pause
- human-review wording remains stronger and more numerous than hard-boundary wording
- broad, generic sources are still allowed to satisfy the package too easily because the evidence-quality contract is mostly advisory
- candidate framing still permits broad platforms because the wedge discipline is not explicit enough in prompts, templates, and scoring artifacts
- launcher scaffolds still bias the package toward “requested human decision” language instead of “continuation status” and “next concrete stage”
- checker logic still has brittle paths where invalid manifests can reach assertions instead of returning actionable failures

## Simplification Direction

- keep `START_HERE.md`, `ACTIVE_RUN.md`, `DISCOVERY_RUN_MODE.md`, `DISCOVERY_RUN_PROMPT.md`, `agent/runbook.md`, and `agent/system-prompt.md` as the only active behavior-defining surfaces
- convert `agent/human-gates.md` into a small hard-boundaries reference focused on risky actions only
- shorten `README.md` so it points to the canonical files instead of re-specifying the run contract
- strengthen templates, source-note guidance, skills, and checker rules so concrete URL-backed complaint evidence is mandatory for core claims
- bias artifacts toward narrow wedge framing, first buyer, first workflow, first monetization path, and “why this is not a platform fantasy”
- archive transition-era hardening notes and diagnosis docs that no longer belong in the active operating path