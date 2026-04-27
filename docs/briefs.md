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

Behavior:

- APD calls local Ollama `POST /api/generate` with `stream=false`.
- APD extracts JSON from the model output using a narrow parser:
  1) full output as JSON,
  2) fenced ```json block,
  3) substring from first `{` to last `}`,
  4) otherwise parse failure.
- APD validates strictly, applies safe normalization for common near-miss fields, and attempts at most one repair call.
- APD imports only when strict validation passes.
- Brief metadata stores concise execution diagnostics under `metadata_json.last_execution`.

Limitations:

- Ollama only. No other provider integrations are included in this path.
- No streaming, background jobs, source fetching, or external publishing.
- Tests mock Ollama calls; live Ollama verification is manual.
