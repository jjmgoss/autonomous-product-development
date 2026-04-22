# Discovery Run Hardening Note

## Still-Relevant Failure Causes

- Launch used to create only empty shells, which made it too easy to stop after run initialization.
- The completion check could be invoked too early because the repo treated it more like a generic probe than a final validator.
- The manifests and run index were present conceptually, but not reinforced strongly enough as required reviewer-facing outputs.

## Files That Must Carry The Middle Of The Run

- `START_HERE.md` and `ACTIVE_RUN.md` must define the sequence clearly.
- `DISCOVERY_RUN_MODE.md`, `DISCOVERY_RUN_PROMPT.md`, and `agent/runbook.md` must make the middle work explicit: save sources, update manifests, compare candidates, fill the package, then validate.
- `scripts/start_discovery_run.py` and `scripts/check_repo_readiness.py` must shape behavior mechanically through scaffolds and final-validation messaging.
- `templates/` must show what complete manifests, candidate maps, summaries, and run indexes look like.

## Language To Retire From The Live Surface

- Transitional `first-run` wording in active operating files when the behavior now supports repeatable discovery runs.
- Launch framing that sounds like initialization alone is meaningful progress.
- Any wording that treats manifests as optional bookkeeping or the run index as a thin pointer file.