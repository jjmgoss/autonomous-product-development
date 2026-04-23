# Operating Surface Audit

Date: 2026-04-22

## Canonical Active Operating Surface

- `START_HERE.md`: canonical bootstrap entrypoint for tiny prompts
- `ACTIVE_RUN.md`: canonical run selector, run goal, completion point, and hard-boundary summary
- `theme.md`: background defaults and product-shape constraints for kickoff-driven runs
- `DISCOVERY_RUN_MODE.md`: canonical discovery-to-planning boundary and package contract
- `DISCOVERY_RUN_PROMPT.md`: detailed run-facing prompt when the kickoff prompt is too small
- `agent/runbook.md`: canonical practical operating behavior across stages
- `agent/system-prompt.md`: canonical repo-local behavioral contract for the agent
- `agent/repo-conventions.md`, `agent/research-corpus-conventions.md`, `agent/artifact-output-conventions.md`: canonical storage and output rules
- `scripts/check_repo_readiness.py` and `scripts/autopd.py`: canonical kickoff/checker contract
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

- discovery can still be mistaken for an endpoint if the operator ignores `post-discovery default`
- checkpoint language is still present enough that weaker models may over-index on it even when the text says not to pause
- human-review wording can still overshadow hard-boundary wording if the active run is not followed carefully
- broad, generic sources are still partly governed by advice rather than hard thresholds beyond the checker
- legacy references to the theme-driven launcher remain in archival or compatibility surfaces

## Simplification Direction

- keep `START_HERE.md`, `ACTIVE_RUN.md`, `DISCOVERY_RUN_MODE.md`, `DISCOVERY_RUN_PROMPT.md`, `agent/runbook.md`, and `agent/system-prompt.md` as the only active behavior-defining surfaces
- keep kickoff command, mode model, and continuation policy aligned across scripts, prompts, and skills
- strengthen templates, source-note guidance, skills, and checker rules so concrete URL-backed complaint evidence is mandatory for core claims
- bias artifacts toward narrow wedge framing, first buyer, first workflow, first monetization path, and `why this is not a platform fantasy`
- archive transition-era hardening notes and diagnosis docs that no longer belong in the active operating path