"""Research brief service: CRUD operations and agent prompt generation."""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from apd.domain.models import ResearchBrief, ResearchBriefStatus

# ── APD schema field reminders embedded in every generated prompt ─────────────
_SCHEMA_REMINDERS = """\
## APD draft JSON schema requirements

Return a single JSON object matching the APD agent draft package format.

### Top-level shape

```json
{
  "schema_version": "1.0",
  "external_draft_id": "<unique-id>",
  "agent_name": "<your-agent-name>",
  "generated_at": "<ISO-8601 datetime>",
  "run": { ... },
  "sources": [ ... ],
  "evidence_excerpts": [ ... ],
  "claims": [ ... ],
  "themes": [ ... ],
  "candidates": [ ... ],
  "validation_gates": [ ... ],
  "evidence_links": [ ... ]
}
```

### Required and common field names — use these exactly

| Object            | Required field      | Common wrong name |
|-------------------|---------------------|-------------------|
| sources           | source_type         | type              |
| evidence_excerpts | excerpt_text        | text              |
| claims            | statement           | claim             |
| themes            | name                | theme             |
| candidates        | title               | name              |
| candidates        | summary             | description       |
| evidence_links    | target_type         | claim_id / theme_id / candidate_id / gate_id |
| evidence_links    | target_id           | (same as above)   |
| evidence_links    | relationship        | (must be present) |

### Allowed values

- `sources.source_type`: any descriptive string (e.g. "reddit_thread", "blog_post", "hn_comment")
- `evidence_links.target_type`: claim | theme | candidate | validation_gate
- `evidence_links.relationship`: supports | weakens | contradicts | context_for | example_of
- `evidence_links.strength`: weak | medium | strong
- `validation_gates.phase`: vague_notion | evidence_collected | supported_opportunity | vetted_opportunity | prototype_ready | build_approved
- `validation_gates.status`: not_started | in_progress | satisfied | weak | failed | waived

### Minimum required content

The package must include:
- A `run` object with `title` or `intent`.
- At least one of: `sources`, `claims`, or `candidates`.

Produce as many of the following as the research supports:
- sources and evidence_excerpts (with source → excerpt links)
- claims (specific assertions about users, pain, workflow, substitutes, willingness-to-pay, or risk)
- themes (clusters of related pain, need, workaround, or opportunity)
- candidates (possible product wedges with title and summary)
- validation_gates (required checks before a run can credibly advance)
- evidence_links (connecting excerpts or sources to claims, themes, candidates, or gates)

### APD validation and repair tooling

APD includes a validation and repair tool you can run before import:

```bash
uv run python scripts/validate_agent_draft.py --path <draft.json> --repair-hints
uv run python scripts/normalize_agent_draft.py --path <draft.json> --out <normalized.json>
```

Producing valid JSON on the first attempt avoids requiring a repair loop.
"""

_OLLAMA_EXECUTION_CONSTRAINTS = """\
## Local Ollama execution constraints (mandatory)

- APD is a product investigation system, not a general Q&A system.
- If this brief is not product/problem/opportunity oriented, return a structured needs-clarification draft instead of inventing a product run.
- Do not invent sources, URLs, citations, Reddit threads, forum posts, or evidence.
- No source text/source pack is provided in this local run. If evidence is ungrounded, label it as synthetic/model-prior in source metadata and avoid fake URLs.
- For a normal product investigation run, include at least one candidate.
- Claims must be specific enough to influence product judgment.
- Candidates should include target user, first workflow, first wedge, substitutes, risks, and validation gates when possible.
- All output remains draft/unreviewed.
"""

_COMPONENT_EXECUTION_CONSTRAINTS = """\
## APD ResearchComponentBatch contract (mandatory)

Return only one JSON object matching this shape:

{
  "schema_version": "1.0",
  "batch_id": "<optional-id>",
  "events": [
    {
      "schema_version": "1.0",
      "event_type": "candidate.proposed|claim.proposed|theme.proposed|source.added|evidence_excerpt.added|validation_gate.proposed|evidence_link.added",
      "external_id": "<required-event-id>",
      "payload": { ... }
    }
  ]
}

Rules:
- Return a ResearchComponentBatch only. Do not return a full APD draft package.
- Use event_type values exactly as listed.
- Every event needs schema_version, event_type, external_id, and payload.
- For product investigations, include at least one candidate.proposed event.
- Do not invent source URLs or citations.
- If ungrounded, mark metadata as synthetic/model-prior.
"""

# ── CRUD ─────────────────────────────────────────────────────────────────────


def create_brief(
    db: Session,
    *,
    title: str,
    research_question: str,
    constraints: Optional[str] = None,
    desired_depth: Optional[str] = None,
    expected_outputs: Optional[str] = None,
    notes: Optional[str] = None,
) -> ResearchBrief:
    brief = ResearchBrief(
        title=title.strip(),
        research_question=research_question.strip(),
        constraints=constraints.strip() if constraints else None,
        desired_depth=desired_depth.strip() if desired_depth else None,
        expected_outputs=expected_outputs.strip() if expected_outputs else None,
        notes=notes.strip() if notes else None,
        status=ResearchBriefStatus.DRAFT,
    )
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return brief


def list_briefs(db: Session) -> list[ResearchBrief]:
    return (
        db.query(ResearchBrief)
        .order_by(ResearchBrief.created_at.desc())
        .all()
    )


def get_brief(db: Session, brief_id: int) -> Optional[ResearchBrief]:
    return db.query(ResearchBrief).filter(ResearchBrief.id == brief_id).first()


def update_brief_status(
    db: Session,
    brief: ResearchBrief,
    status: ResearchBriefStatus,
) -> ResearchBrief:
    brief.status = status
    db.commit()
    db.refresh(brief)
    return brief


# ── Prompt generation ─────────────────────────────────────────────────────────


def generate_agent_prompt(brief: ResearchBrief) -> str:
    """Return a copyable agent prompt for the given research brief."""
    lines: list[str] = []

    lines.append("# APD Research Agent Prompt")
    lines.append("")
    lines.append(
        "You are a product research agent. Your task is to investigate the research "
        "direction below and return structured findings as a valid APD agent draft JSON package."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Research direction")
    lines.append("")
    lines.append(brief.research_question)
    lines.append("")

    if brief.constraints:
        lines.append("## Constraints")
        lines.append("")
        lines.append(brief.constraints)
        lines.append("")

    if brief.desired_depth:
        lines.append("## Desired depth")
        lines.append("")
        lines.append(brief.desired_depth)
        lines.append("")

    if brief.expected_outputs:
        lines.append("## Expected outputs")
        lines.append("")
        lines.append(brief.expected_outputs)
        lines.append("")

    if brief.notes:
        lines.append("## Additional notes")
        lines.append("")
        lines.append(brief.notes)
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(_SCHEMA_REMINDERS)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Safety constraints (mandatory)")
    lines.append("")
    lines.append(
        "- Return only valid APD draft JSON. Do not wrap it in prose or markdown fences "
        "unless the entire response is a single fenced ```json block."
    )
    lines.append("- All output is draft and unreviewed. Do not assert conclusions as facts.")
    lines.append(
        "- Do not publish externally, create GitHub issues or repositories, send emails, "
        "post to social media, or take any external actions."
    )
    lines.append("- Do not call external APIs, fetch live URLs, or access private data.")
    lines.append("- Do not run code or execute commands.")
    lines.append("")
    lines.append(
        "Return only the JSON package. APD will import and review it."
    )

    return "\n".join(lines)


def generate_ollama_execution_prompt(brief: ResearchBrief) -> str:
    """Return a stricter prompt for local Ollama execution."""
    base = generate_agent_prompt(brief)
    return "\n".join([base, "", "---", "", _OLLAMA_EXECUTION_CONSTRAINTS, "", "Return only the JSON package."])


def generate_ollama_component_prompt(brief: ResearchBrief) -> str:
    """Return a provider-agnostic component contract prompt for Ollama prototype execution."""
    base = generate_ollama_execution_prompt(brief)
    return "\n".join([base, "", "---", "", _COMPONENT_EXECUTION_CONSTRAINTS, "", "Return only the ResearchComponentBatch JSON object."])


def generate_ollama_component_phase_prompt(
    brief: ResearchBrief,
    phase_name: str,
    *,
    candidate_ids: list[str] | None = None,
    grounded_source_packet: str | None = None,
) -> str:
    """Return a phase-specific component batch prompt."""
    base = generate_ollama_execution_prompt(brief)
    candidates_block = ", ".join(candidate_ids or [])
    if not candidates_block:
        candidates_block = "(none yet)"

    phase_instructions: dict[str, str] = {
        "candidate_batch": (
            "Phase: candidate_batch\n"
            "- Return only ResearchComponentBatch JSON.\n"
            "- Include at least one candidate.proposed event.\n"
            "- No full APD draft package.\n"
            "- No fake source URLs or citations."
        ),
        "claim_theme_batch": (
            "Phase: claim_theme_batch\n"
            "- Return only ResearchComponentBatch JSON.\n"
            "- Use claim.proposed and/or theme.proposed events.\n"
            "- Claims must be specific enough to influence product judgment.\n"
            "- No fake source URLs or citations."
        ),
        "validation_gate_batch": (
            "Phase: validation_gate_batch\n"
            "- Return only ResearchComponentBatch JSON.\n"
            "- Use validation_gate.proposed events.\n"
            "- Prefer candidate_id values from existing candidates.\n"
            f"- Existing candidate IDs: {candidates_block}"
        ),
    }
    selected = phase_instructions.get(
        phase_name,
        "Phase: generic_component_batch\n- Return only ResearchComponentBatch JSON.",
    )
    grounded_constraints = ""
    if grounded_source_packet:
        grounded_constraints = "\n".join(
            [
                "## Source-grounded execution constraints (mandatory)",
                "- Use only the provided APD-captured source packet for factual claims.",
                "- Do not invent sources, URLs, citations, source IDs, or excerpt IDs.",
                "- Do not emit source.added or evidence_excerpt.added for provided packet sources.",
                "- Every factual claim should have at least one evidence_link.added referencing a provided source_id and/or excerpt_id.",
                "- Unsupported hypotheses may appear only when clearly marked as model-prior assumptions in metadata_json.",
                "",
                grounded_source_packet,
            ]
        )
    parts = [base, "", "---", "", _COMPONENT_EXECUTION_CONSTRAINTS]
    if grounded_constraints:
        parts.extend(["", grounded_constraints])
    parts.extend(["", selected, "", "Return only the ResearchComponentBatch JSON object."])
    return "\n".join(parts)


def generate_ollama_component_repair_prompt(
    brief: ResearchBrief,
    *,
    phase_name: str,
    validation_errors: list[str],
    invalid_batch_data: dict[str, object] | None,
    grounded_source_packet: str | None = None,
) -> str:
    """Return a phase-specific repair prompt for an invalid component batch."""
    base = generate_ollama_execution_prompt(brief)
    errors_block = "\n".join(f"- {line}" for line in validation_errors[:8]) or "- unknown validation error"
    invalid_json = "{}" if invalid_batch_data is None else json.dumps(invalid_batch_data, ensure_ascii=False)
    parts = [
        base,
        "",
        "---",
        "",
        _COMPONENT_EXECUTION_CONSTRAINTS,
    ]
    if grounded_source_packet:
        parts.extend(
            [
                "",
                "## Source-grounded execution constraints (mandatory)",
                "- Use only the provided APD-captured source packet for factual claims.",
                "- Do not invent sources, URLs, citations, source IDs, or excerpt IDs.",
                "- Preserve valid source_id and excerpt_id references from the provided packet.",
                "",
                grounded_source_packet,
            ]
        )
    parts.extend(
        [
            "",
            "Phase repair request:",
            f"- Phase name: {phase_name}",
            "- Return only corrected ResearchComponentBatch JSON.",
            "- Preserve valid event external_id values where possible.",
            "- Fix only schema/shape/required-content problems.",
            "- Do not add prose.",
            "",
            "Validation errors:",
            errors_block,
            "",
            "Invalid batch JSON:",
            invalid_json,
            "",
            "Return only the corrected ResearchComponentBatch JSON object.",
        ]
    )
    return "\n".join(parts)
