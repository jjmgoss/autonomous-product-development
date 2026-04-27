"""Research brief service: CRUD operations and agent prompt generation."""

from __future__ import annotations

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
