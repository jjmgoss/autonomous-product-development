# Research Briefs

Research briefs are the normal starting point for APD's local product-research workflow.

The brief is where a user defines the product investigation direction. From there, the expected path is simple: configure local model settings if needed, click `Start Research`, let APD run the current bounded research flow, and then review the imported run.

## Overview

Use a research brief when you want APD to investigate a product space, pain pattern, workflow, substitute, or opportunity question.

The brief should give APD:

- a clear research question
- optional constraints
- optional desired depth
- optional expected outputs
- optional notes or prior context

APD treats the resulting research as draft and unreviewed until a person inspects it.

## Normal workflow

1. Create a brief under `/briefs`.
2. Configure local model settings at `/settings/model-execution` if they are not already saved.
3. Open the brief detail page and click `Start Research`.
4. Watch the brief detail page for concise execution status.
5. If the run imports successfully, APD redirects to the new run.
6. Review the run through the candidate-first review UI.

This is the normal product path.

Manual prompt copy/paste and manual import still exist as legacy or debug support paths. They are not the main workflow.

## Model settings

APD currently supports a local Ollama-backed execution path.

You can configure it at `/settings/model-execution`.

Saved settings are stored in the APD database and are used by the brief-detail `Start Research` action. Environment variables still act as fallback values when database-backed settings are not present.

Required settings for the current local path:

- `APD_MODEL_PROVIDER=ollama`
- `APD_OLLAMA_BASE_URL=http://localhost:11434`
- `APD_OLLAMA_MODEL=<installed-model-name>`

Optional settings include timeout, keep-alive, and component repair attempts.

If required settings are missing, the brief detail page shows a concise prompt linking to the settings page instead of trying to run a research execution.

## What `Start Research` does

`Start Research` routes to APD's current best local autonomous path.

Today that means:

1. APD sends the brief to the local model for web discovery planning.
2. The model proposes a small JSON list of search queries and direct URLs.
3. APD validates the proposed URLs and fetches only safe public targets.
4. APD stores captured material as APD-owned `Source` and `EvidenceExcerpt` records.
5. APD builds a bounded grounding packet from captured sources.
6. APD runs grounded component execution against that packet.
7. APD validates, repairs, and imports the result only if it passes schema, quality, and grounding checks.

This path is synchronous and local-first. It does not do unrestricted browsing, background jobs, or hosted provider calls.

## Execution results and failure states

The brief detail page stores and displays a concise `last_execution` summary.

The page prioritizes:

- overall status
- web discovery phase status
- captured source count
- component execution phase status
- grounding status when relevant
- readable error summaries

Raw execution JSON is secondary debug material. It remains available behind a collapsed details disclosure.

Common execution outcomes include:

- configuration missing
- provider error
- parse failure
- validation failure
- grounded validation failure
- import success

When web discovery succeeds but component execution fails later, the brief detail page should still make that phase split clear rather than forcing the user to read raw JSON.

## Candidate-first review

If APD imports the run successfully, the main next step is run review.

APD's run detail UI is candidate-first. The intent is that the reviewer starts with candidate product wedges, then drills down into claims, themes, gates, and evidence links.

This matters because APD is trying to support product judgment, not just source collection. Research is only useful if the user can decide what to believe, what to validate next, and what to reject or park.

## Legacy or debug manual import

APD still supports a manual draft-import workflow for debugging and external-agent experiments.

That path is useful when you want to:

- import a hand-authored or externally generated APD draft package
- inspect validation behavior directly
- exercise import tooling without running the local model path

The rough flow is:

1. create or obtain an APD draft JSON package
2. validate it with APD tooling
3. optionally normalize near-miss fields
4. import it into APD

Validation commands:

```bash
uv run python scripts/validate_agent_draft.py --path <draft.json> --repair-hints
uv run python scripts/normalize_agent_draft.py --path <draft.json> --out <normalized.json>
uv run python scripts/import_agent_draft.py --path <normalized.json>
```

This is a legacy or debug-support path. It should not be treated as the main brief-detail experience.

## Safety notes

The current brief-driven execution path follows these rules:

- APD fetches only validated public `http` and `https` URLs
- APD does not allow localhost, loopback, private IPs, or credentialed URLs
- APD does not crawl beyond explicit proposed URLs
- APD does not bypass authentication, paywalls, or access controls
- grounded source references are validation signals, not truth verification
- imported research remains draft until a human reviews it

## Testing notes

Automated tests for the brief workflow mock:

- local model output
- web-fetch behavior
- execution success and failure paths

Tests do not require live Ollama or live web access.

Manual verification remains useful for UI sanity checks, but raw execution details should only be needed when debugging a failure rather than understanding the normal user workflow.
