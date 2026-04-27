# Research Briefs

APD supports creating a small research brief that generates a copyable agent prompt.

Purpose

- Reduce friction between a research question and the manual agent handoff.

Workflow

1. Create a research brief in the APD UI under `/briefs`.
2. Copy the generated agent prompt shown on the brief detail page and paste it into an external research agent (e.g. GPT-4, Claude).
3. Save the agent's JSON output to a local file.
4. Validate the JSON using APD's validation tooling:

```bash
uv run python scripts/validate_agent_draft.py --path <draft.json> --repair-hints
uv run python scripts/normalize_agent_draft.py --path <draft.json> --out <normalized.json>
```

5. After validation passes, import the draft:

```bash
uv run python scripts/import_agent_draft.py --path <normalized.json>
```

Notes

- APD will import the package as draft/unreviewed research for human inspection and review.
- The current workflow is manual: APD does not run models itself yet. Automation is tracked in issue #44.
 - A website-first prototype (Issue #44) is available that demonstrates an in-process, deterministic "stub" runner. The stub does not call external models or services; it builds a synthetic agent draft package, validates it with APD's validators, and imports it locally so you can exercise the end-to-end import and run creation flow without external network calls.
- The generated prompt includes reminders about APD's expected field names and schema. Use them to avoid common near-miss errors (e.g. `sources.source_type`, `evidence_excerpts.excerpt_text`, `claims.statement`).

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

Limitations:

- Ollama only. No other provider integrations are included in this path.
- No streaming, background jobs, source fetching, or external publishing.
- Local/Ollama runs should not invent sources, URLs, citations, or claims of fetched web evidence.
- Tests mock Ollama calls; live Ollama verification is manual.

## Component-based execution prototype (Issue #51)

APD now includes an experimental component-based execution path that uses a provider-agnostic event contract.

Why this exists:

- Monolithic draft JSON generation is brittle across models.
- Component batches let APD validate smaller typed events before final import.
- APD still assembles a standard APD draft package and uses strict draft validation/import as the final gate.

What this is:

- A synchronous website-first prototype path (`Start Research with Components (experimental)`).
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
- Uses the same keep-alive behavior (`keep_alive: 0` default) to free local model resources after execution.
