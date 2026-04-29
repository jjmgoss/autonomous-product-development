# Research Briefs

APD supports creating a small research brief and starting research directly from the brief detail page.

Purpose

- Reduce friction between a research question and APD's autonomous local research workflow.

Workflow

1. Create a research brief in the APD UI under `/briefs`.
2. Open the brief detail page and click `Start Research`.
3. APD uses the configured local model to run the current autonomous research path internally.
4. APD shows concise execution status on the brief detail page, including web discovery and component execution phases when applicable.
5. If execution succeeds, APD redirects to the imported run. If execution fails, APD keeps the raw execution payload available behind a collapsed details disclosure.

Notes

- APD will import the package as draft/unreviewed research for human inspection and review.
- The new brief form includes a local sample/randomizer for dogfooding. It does not call a model or save anything until you submit the brief form.
- APD also supports optional model-generated brief ideation using configured local Ollama settings. These generated ideas are draft form prefills only, are not researched findings, do not perform web/source research, do not use hosted provider API keys, and are not saved until you submit the brief form.
- The older prompt-copy / validate / normalize / import workflow is legacy/debug fallback only. It is no longer the normal brief-detail experience.

Note: The run review UI is candidate-first — the run detail page surfaces product
candidates before sources and reasoning so reviewers can prioritize candidate
inspection and then trace claims/themes/gates back to supporting evidence.
- A deterministic stub runner still exists for tests and debugging, but it is no longer the normal user-facing brief workflow.

## Local Ollama execution (Issue #46)

APD now supports a local Ollama execution path from brief detail pages.

Required environment variables:

- `APD_MODEL_PROVIDER=ollama`
- `APD_OLLAMA_BASE_URL=http://localhost:11434`
- `APD_OLLAMA_MODEL=<installed-model-name>`

Optional:

- `APD_OLLAMA_TIMEOUT_SECONDS` (default: `120`)
- `APD_OLLAMA_REPAIR_ATTEMPTS` (default: `1`, capped at one repair call)
- `APD_OLLAMA_KEEP_ALIVE` (default: `0`, unload model after each APD run to free GPU/VRAM)

Behavior:

- APD calls local Ollama `POST /api/generate` with `stream=false`.
- APD extracts JSON from the model output using a narrow parser:
  1) full output as JSON,
  2) fenced ```json block,
  3) substring from first `{` to last `}`,
  4) otherwise parse failure.
- APD validates strictly, applies safe normalization for common near-miss fields, and attempts at most one repair call.
- APD imports only when strict validation and a minimal product-quality gate pass.
- Schema-valid output is not automatically product-useful. APD rejects zero-candidate local runs with `quality_failed_no_candidates`.
- If local output includes source URLs without provided source context, APD records a quality warning (`quality_warning_unprovided_source_urls`).
- Brief metadata stores concise execution diagnostics under `metadata_json.last_execution`.
- APD sends Ollama requests with `keep_alive: 0` by default so local model resources are released after execution.
 - APD keeps the model warm during a single execution (generation/repair/component phases), then unloads at the end by default.
 - If `APD_OLLAMA_KEEP_ALIVE` is explicitly set to a non-zero value, APD respects that and does not force an unload.

Limitations:

- Ollama only. No other provider integrations are included in this path.
- No streaming, background jobs, source fetching, or external publishing.
- Local/Ollama runs should not invent sources, URLs, citations, or claims of fetched web evidence.
- Tests mock Ollama calls; live Ollama verification is manual.

## APD-orchestrated web discovery phase (Issue #62)

APD now includes a controlled web discovery phase inside the website execution prototype.

Intended workflow:

1. Create a research brief.
2. Start one research execution.
3. APD runs an internal web discovery phase.
4. The local model proposes a small JSON list of search queries and direct public URLs.
5. APD validates and fetches only explicit public URLs that pass safety checks.
6. APD stores captured pages as APD-owned `Source` and `EvidenceExcerpt` records where feasible.
7. Execution continues into component generation.

Current prototype behavior:

- The brief detail page exposes one primary `Start Research` action for normal users.
- `Start Research` routes to APD's current best local execution path: web discovery followed by grounded component execution.
- Execution metadata records web discovery and component execution as separate phases under `metadata_json.last_execution`.
- Captured sources are shown as part of execution status, not as a separate user prerequisite step.
- Grounded component execution builds a bounded source packet from APD-captured `Source` and `EvidenceExcerpt` rows.
- APD validates that model-generated `evidence_link.added` events only reference known captured `source_id` and `excerpt_id` values.
- APD rejects grounded batches that invent source URLs, invent source/excerpt IDs, or produce claims without at least one supporting grounded evidence link.
- This is grounding-by-reference only. APD does not verify that captured excerpts make generated claims true.
- Brief execution status now prioritizes readable phase summaries and error summaries, with raw execution JSON collapsed behind a disclosure.

Safety and budget controls:

- This is not free browsing.
- No crawling beyond explicit proposed URLs.
- No authenticated or private sources.
- No localhost, loopback, or private-network targets.
- Only validated public `http` or `https` URLs are fetched.
- Max model-proposed queries: `5`
- Max fetched URLs per run: `5`
- Small fixed timeout and response/text caps are enforced in code.

Notes:

- Proposed queries are stored in execution status for future search-provider integration, but this issue only fetches direct validated URLs.
- Captured web sources remain draft research material for later human review.
- Because sources are still run-scoped in the current schema, APD creates a small capture run for the brief and records the originating `brief_id` in metadata.
- Tests mock both model output and HTTP fetches; no live network access is required.

## UI-managed local model settings (Issue #55)

APD now includes a Settings page at `/settings/model-execution` for local model execution configuration.

What changed:

- PowerShell `$env:` values are process-scoped and temporary unless persisted in a profile.
- You can save local/Ollama execution settings from the APD UI.
- Saved settings are stored in the APD database (`app_settings`) and persist across app restarts.
- Environment variables remain fallback values when DB settings are not present.
- This feature stores non-secret local settings only.
- Hosted provider API keys are not implemented by this feature.

Testing notes:

- Tests for this feature use local DB state and mocked execution paths.
- No live Ollama calls are required in tests.

## Component-based execution prototype (Issue #51)

APD now includes an experimental component-based execution path that uses a provider-agnostic event contract.

Why this exists:

- Monolithic draft JSON generation is brittle across models.
- Component batches let APD validate smaller typed events before final import.
- APD still assembles a standard APD draft package and uses strict draft validation/import as the final gate.

What this is:

- A synchronous brief workflow exposed as `Start Research`.
- A web-assisted grounded execution path that reuses APD-captured web sources internally.
- Provider-agnostic schema names (`ResearchComponentEvent`, `ResearchComponentBatch`, `ComponentDraftAssembler`).
- Ollama is the first adapter implementation.

What this is not:

- Not browser streaming.
- Not WebSockets or SSE.
- Not background jobs.
- Not a provider registry.

Current component minimum:

- Supports candidate, claim, and theme events (plus optional source/excerpt/gate/link events).
- Rejects zero-candidate assembled output before import.
- In grounded mode, seeds captured sources/excerpts into the assembled package so evidence links resolve through normal draft import.
- In grounded mode, allows only APD-provided source/excerpt identifiers and blocks invented URL-like citations.
- Uses the same keep-alive behavior (`keep_alive: 0` default) to free local model resources after execution.

## Component repair and retry loop (Issue #53)

Component execution now runs as small APD-orchestrated phases instead of trusting a single batch:

- `candidate_batch` (required, must include at least one `candidate.proposed`)
- `claim_theme_batch` (must include `claim.proposed` and/or `theme.proposed`)
- `validation_gate_batch` (must include `validation_gate.proposed`)

For each phase APD:

- sends a phase-specific component prompt,
- parses and validates the `ResearchComponentBatch`,
- checks phase-specific required content,
- retries with a repair prompt when invalid, including concise validation errors,
- applies only valid batches to the assembler.

Retry cap:

- `APD_COMPONENT_REPAIR_ATTEMPTS` (default `2`, capped at `3`)
- total attempts per phase are `1 + repair_attempts`

Execution diagnostics in `ResearchBrief.metadata_json.last_execution` include:

- `mode: component_execution`
- `status`
- `last_phase`
- `attempts_by_phase`
- concise `errors` and `warnings`

This remains a synchronous prototype path:

- no browser streaming
- no WebSockets/SSE
- no background jobs
