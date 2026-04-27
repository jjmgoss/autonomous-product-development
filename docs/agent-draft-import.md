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

## Sample package

A committed example package is available at:

- `apd/fixtures/examples/agent_draft_sample.json`
