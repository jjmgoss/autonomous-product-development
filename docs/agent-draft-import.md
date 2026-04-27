# Agent Draft Import Format

Issue: #27

This document defines the APD draft import package contract for research-agent output.

## Purpose

An agent draft package is the handoff format between a research agent and APD.

APD imports this package as draft/unreviewed research so humans can review and decide what to accept.

Imported draft data is not accepted truth by default.

## Command

```text
uv run python scripts/import_agent_draft.py --path apd/fixtures/examples/agent_draft_sample.json
```

Optional duplicate override:

```text
uv run python scripts/import_agent_draft.py --path apd/fixtures/examples/agent_draft_sample.json --allow-duplicate-external-id
```

Validate before import:

```text
uv run python scripts/validate_agent_draft.py --path apd/fixtures/examples/agent_draft_sample.json
uv run python scripts/validate_agent_draft.py --path .local/drafts/dogfood-product-research.json --repair-hints
uv run python scripts/validate_agent_draft.py --path .local/drafts/dogfood-product-research.json --repair-prompt
```

Optional best-effort normalization to an explicit output path:

```text
uv run python scripts/normalize_agent_draft.py --path .local/drafts/input.json --out .local/drafts/input.normalized.json
```

## Re-import behavior

- Default behavior: reject duplicate `external_draft_id` imports.
- If a package has an `external_draft_id` already imported, the command fails safely.
- Use `--allow-duplicate-external-id` to intentionally import the same external draft ID again as a new run.
- If `external_draft_id` is omitted, each import creates a new run.

## Minimum required content

A package must include:

- `run` object
- at least one of:
  - `sources`
  - `claims`
  - `candidates`
- plus `run.title` or `run.intent`

## Draft package JSON shape

```json
{
  "schema_version": "1.0",
  "external_draft_id": "draft-optional-id",
  "agent_name": "optional-agent-name",
  "generated_at": "2026-04-26T18:20:00Z",
  "run": {
    "title": "optional-title",
    "intent": "optional-intent",
    "summary": "optional-summary",
    "mode": "optional-mode",
    "phase": "optional-run-phase",
    "recommendation": "optional-draft-recommendation"
  },
  "warnings": ["optional warning strings"],
  "limitations": ["optional limitation strings"],
  "sources": [
    {
      "id": "src-1",
      "title": "optional",
      "source_type": "required",
      "url": "optional",
      "origin": "optional",
      "author_or_org": "optional",
      "captured_at": "optional datetime",
      "published_at": "optional datetime",
      "raw_path": "optional",
      "normalized_path": "optional",
      "reliability_notes": "optional",
      "summary": "optional",
      "metadata_json": {}
    }
  ],
  "evidence_excerpts": [
    {
      "id": "ex-1",
      "source_id": "src-1",
      "excerpt_text": "required",
      "location_reference": "optional",
      "excerpt_type": "optional",
      "metadata_json": {}
    }
  ],
  "claims": [
    {
      "id": "claim-1",
      "statement": "required",
      "claim_type": "optional",
      "confidence": 0.7,
      "created_by": "optional",
      "metadata_json": {}
    }
  ],
  "themes": [
    {
      "id": "theme-1",
      "name": "required",
      "summary": "optional",
      "theme_type": "optional",
      "severity": "optional",
      "frequency": "optional",
      "user_segment": "optional",
      "workflow": "optional",
      "metadata_json": {}
    }
  ],
  "candidates": [
    {
      "id": "cand-1",
      "title": "required",
      "summary": "optional",
      "target_user": "optional",
      "first_workflow": "optional",
      "first_wedge": "optional",
      "prototype_success_event": "optional",
      "monetization_path": "optional",
      "substitutes": "optional",
      "risks": "optional",
      "why_now": "optional",
      "why_it_might_fail": "optional",
      "score": 0.6,
      "rank": 1,
      "metadata_json": {}
    }
  ],
  "validation_gates": [
    {
      "id": "gate-1",
      "candidate_id": "optional candidate id",
      "phase": "optional run phase",
      "name": "required",
      "description": "optional",
      "status": "optional validation gate status",
      "blocking": true,
      "evidence_summary": "optional",
      "missing_evidence": "optional",
      "metadata_json": {}
    }
  ],
  "evidence_links": [
    {
      "id": "link-1",
      "source_id": "optional source id",
      "excerpt_id": "optional excerpt id",
      "target_type": "claim|theme|candidate|validation_gate",
      "target_id": "required external object id",
      "relationship": "supports|weakens|contradicts|context_for|example_of",
      "strength": "weak|medium|strong",
      "notes": "optional",
      "metadata_json": {}
    }
  ]
}
```

## Import semantics

- Claims are imported with `review_status=unreviewed` and `is_agent_generated=true`.
- Candidates are imported with `review_status=unreviewed` and `is_agent_generated=true`.
- Themes are imported with `review_status=unreviewed` and metadata marker `agent_generated=true`.
- Validation gates are imported without forcing accepted/satisfied status.
- Evidence links map by external IDs in the package and preserve traceability.

## Failure and warning behavior

- Malformed JSON or schema violations fail with clear validation errors.
- Unknown references in excerpts, gates, or evidence links are skipped with warning lines.
- Import warnings are recorded in run metadata under `metadata_json.agent_draft.import_warnings`.

## Validation and repair loop

Use this loop during dogfooding or external-agent handoff:

1. Generate an APD draft package JSON file.
2. Run `scripts/validate_agent_draft.py` before import.
3. If validation fails, use `--repair-hints` or `--repair-prompt` to repair the JSON.
4. Optionally run `scripts/normalize_agent_draft.py` to rewrite common near-miss fields to a new explicit output path.
5. Re-run validation on the repaired or normalized file.
6. Import only after strict validation passes.

Validation is read-only and does not create a `Run` or any other database rows.

Normalization is optional. It only writes to the output path you provide and does not import anything.

Import remains the strict final gate. Validation and normalization should help repair packages, not weaken import rules.

## Common near-miss fields

The validator and normalizer recognize these common schema drifts:

- `sources.type` -> `source_type`
- `sources.accessed_at` -> `captured_at`
- `evidence_excerpts.text` -> `excerpt_text`
- `evidence_excerpts.locator` -> `location_reference`
- `claims.claim` -> `statement`
- `claims.confidence` string values should be numeric
- `themes.theme` -> `name`
- `candidates.name` -> `title`
- `candidates.description` -> `summary`
- `validation_gates.phase=problem_validation` -> `supported_opportunity`
- `validation_gates.phase=solution_validation` -> `vetted_opportunity`
- `validation_gates.phase=commercial_validation` -> `vetted_opportunity`
- `evidence_links.claim_id|theme_id|candidate_id|gate_id` -> `target_type` + `target_id`
- missing `evidence_links.relationship`
- unexpected extra object fields that belong in `metadata_json`

## Repair prompt template

If you want a copyable prompt without running `--repair-prompt`, use this template:

```text
Repair this APD agent draft package so it passes strict APD draft validation.
Return only JSON.
Preserve the research meaning and IDs unless a schema repair requires a field rename.
Use exact APD field names and enums.
Move unexpected extra object fields into metadata_json when they still matter.

Fix these common APD schema near-misses when present:
- sources.type -> source_type
- sources.accessed_at -> captured_at
- evidence_excerpts.text -> excerpt_text
- evidence_excerpts.locator -> location_reference
- claims.claim -> statement
- claims.confidence must be numeric, not a string
- themes.theme -> name
- candidates.name -> title
- candidates.description -> summary
- validation_gates.phase must be one of vague_notion, evidence_collected, supported_opportunity, vetted_opportunity, prototype_ready, build_approved
- validation_gates.problem_validation -> supported_opportunity
- validation_gates.solution_validation -> vetted_opportunity
- validation_gates.commercial_validation -> vetted_opportunity
- evidence_links.claim_id -> target_type claim + target_id
- evidence_links.theme_id -> target_type theme + target_id
- evidence_links.candidate_id -> target_type candidate + target_id
- evidence_links.gate_id -> target_type validation_gate + target_id
- evidence_links must include relationship: supports, weakens, contradicts, context_for, or example_of

Return corrected JSON only.
```

## Sample package

A committed example package is available at:

- `apd/fixtures/examples/agent_draft_sample.json`
