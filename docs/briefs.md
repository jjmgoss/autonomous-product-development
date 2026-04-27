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
