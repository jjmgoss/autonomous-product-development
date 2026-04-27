from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from apd.domain.models import Artifact, ReviewStatus, Run
from apd.web.queries import get_run_detail


@dataclass
class ReportExportResult:
    run_id: int
    artifact_id: int
    artifact_path: Path


def export_run_markdown_report(db: Session, run_id: int, export_root: Optional[Path] = None) -> Optional[ReportExportResult]:
    detail = get_run_detail(db, run_id)
    if detail is None:
        return None

    run = detail["run"]
    markdown = render_run_report_markdown(detail)

    root = export_root or _default_export_root()
    safe_dir = root / f"run-{run_id}"
    safe_dir.mkdir(parents=True, exist_ok=True)

    output_path = _next_report_path(safe_dir, run_id)
    output_path.write_text(markdown, encoding="utf-8")

    artifact = Artifact(
        run_id=run_id,
        artifact_type="markdown_report",
        title=f"Run {run_id} Markdown Report",
        path=str(_to_repo_relative(output_path)),
        created_by="local_export",
        summary="Markdown report export generated from structured run data.",
        metadata_json={
            "format": "markdown",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phase": str(run.phase),
            "decision": str(run.current_decision) if run.current_decision else None,
        },
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return ReportExportResult(run_id=run_id, artifact_id=artifact.id, artifact_path=output_path)


def render_run_report_markdown(detail: dict) -> str:
    run = detail["run"]
    sources = detail["sources"]
    claims = detail["claims"]
    themes = detail["themes"]
    candidates = detail["candidates"]
    validation_gates = detail["validation_gates"]
    review_notes = detail["review_notes"]
    decision_history = detail.get("decision_history", [])
    evidence_index = detail.get("evidence_index", {})

    lines: list[str] = []

    lines.append(f"# {run.title}")
    lines.append("")
    if run.intent:
        lines.append("## Intent")
        lines.append("")
        lines.append(run.intent)
        lines.append("")

    lines.append("## Run State")
    lines.append("")
    lines.append(f"- Phase: {str(run.phase).replace('_', ' ')}")
    lines.append(f"- Current decision: {_display_or_none(run.current_decision)}")
    lines.append("")

    if run.summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(run.summary)
        lines.append("")

    if run.recommendation:
        lines.append("## Recommendation")
        lines.append("")
        lines.append(run.recommendation)
        lines.append("")

    if decision_history:
        lines.append("## Decision History")
        lines.append("")
        for d in decision_history:
            decided_at = d.decided_at.strftime("%Y-%m-%d %H:%M UTC") if d.decided_at else "unknown"
            rationale = f" - rationale: {d.rationale}" if d.rationale else ""
            lines.append(f"- {str(d.decision).replace('_', ' ')} at {decided_at}{rationale}")
        lines.append("")

    lines.append("## Sources")
    lines.append("")
    if not sources:
        lines.append("- None")
    else:
        for s in sources:
            reference = s.url or s.raw_path or "no reference"
            summary = f" - {s.summary}" if s.summary else ""
            lines.append(f"- [source#{s.id}] {s.title or 'Untitled'} ({s.source_type}) - {reference}{summary}")
    lines.append("")

    lines.append("## Claims")
    lines.append("")
    _append_items_with_status(lines, claims, "claim", evidence_index)

    lines.append("## Themes")
    lines.append("")
    _append_items_with_status(lines, themes, "theme", evidence_index)

    lines.append("## Candidates")
    lines.append("")
    if not candidates:
        lines.append("- None")
        lines.append("")
    else:
        for c in candidates:
            status = str(c.review_status).replace("_", " ")
            decision_part = f", decision={str(c.decision).replace('_', ' ')}" if c.decision else ""
            lines.append(f"- [candidate#{c.id}] ({status}{decision_part}) {c.title}")
            if c.summary:
                lines.append(f"  - summary: {c.summary}")
            if c.target_user:
                lines.append(f"  - target_user: {c.target_user}")
            if c.first_workflow:
                lines.append(f"  - first_workflow: {c.first_workflow}")
            if c.first_wedge:
                lines.append(f"  - first_wedge: {c.first_wedge}")
            if c.why_it_might_fail:
                lines.append(f"  - why_it_might_fail: {c.why_it_might_fail}")
            _append_evidence_refs(lines, evidence_index, "candidate", c.id)
        lines.append("")

    lines.append("## Validation Gates And Gaps")
    lines.append("")
    if not validation_gates:
        lines.append("- None")
    else:
        for g in validation_gates:
            phase = str(g.phase).replace("_", " ") if g.phase else "none"
            status = str(g.status).replace("_", " ")
            blocking = "blocking" if g.blocking else "non-blocking"
            lines.append(f"- [gate#{g.id}] {g.name} ({status}, {blocking}, phase={phase})")
            if g.description:
                lines.append(f"  - description: {g.description}")
            if g.missing_evidence:
                lines.append(f"  - missing_evidence: {g.missing_evidence}")
    lines.append("")

    lines.append("## Review Notes")
    lines.append("")
    if not review_notes:
        lines.append("- None")
    else:
        for n in review_notes:
            author = n.author or "unknown"
            target = f"{str(n.target_type)}#{n.target_id}"
            lines.append(f"- [{str(n.status)}] {target} by {author}: {n.note}")
    lines.append("")

    lines.append("## Known Weak, Disputed, Or Needs-Followup Material")
    lines.append("")
    _append_flagged_material(lines, claims, themes, candidates)

    next_action = _next_suggested_action(run, validation_gates)
    if next_action:
        lines.append("")
        lines.append("## Next Suggested Action")
        lines.append("")
        lines.append(next_action)

    lines.append("")
    return "\n".join(lines)


def _append_items_with_status(lines: list[str], items: list, item_type: str, evidence_index: dict) -> None:
    if not items:
        lines.append("- None")
        lines.append("")
        return

    grouped = {
        ReviewStatus.ACCEPTED.value: [],
        ReviewStatus.WEAK.value: [],
        ReviewStatus.DISPUTED.value: [],
        ReviewStatus.NEEDS_FOLLOWUP.value: [],
        ReviewStatus.UNREVIEWED.value: [],
    }

    for item in items:
        grouped.setdefault(str(item.review_status), []).append(item)

    for status_key in [
        ReviewStatus.ACCEPTED.value,
        ReviewStatus.WEAK.value,
        ReviewStatus.DISPUTED.value,
        ReviewStatus.NEEDS_FOLLOWUP.value,
        ReviewStatus.UNREVIEWED.value,
    ]:
        entries = grouped.get(status_key, [])
        lines.append(f"### {status_key.replace('_', ' ').title()}")
        if not entries:
            lines.append("")
            lines.append("- None")
            lines.append("")
            continue

        lines.append("")
        for item in entries:
            name = getattr(item, "statement", None) or getattr(item, "name", None) or "unnamed"
            lines.append(f"- [{item_type}#{item.id}] {name}")
            summary = getattr(item, "summary", None)
            if summary:
                lines.append(f"  - summary: {summary}")
            _append_evidence_refs(lines, evidence_index, item_type, item.id)
        lines.append("")


def _append_evidence_refs(lines: list[str], evidence_index: dict, target_type: str, target_id: int) -> None:
    refs = evidence_index.get(target_type, {}).get(target_id, [])
    if not refs:
        lines.append("  - evidence: none linked")
        return

    for ref in refs:
        source_ref = f"source#{ref.get('source_id')}" if ref.get("source_id") else "source?"
        source_title = ref.get("source_title") or source_ref
        rel = ref.get("relationship_type") or "related"
        strength = f", strength={ref.get('strength')}" if ref.get("strength") else ""
        lines.append(f"  - evidence: {source_title} ({source_ref}, {rel}{strength})")


def _append_flagged_material(lines: list[str], claims: list, themes: list, candidates: list) -> None:
    flagged = []
    for label, items, text_attr in [
        ("claim", claims, "statement"),
        ("theme", themes, "name"),
        ("candidate", candidates, "title"),
    ]:
        for item in items:
            status = str(item.review_status)
            if status in {
                ReviewStatus.WEAK.value,
                ReviewStatus.DISPUTED.value,
                ReviewStatus.NEEDS_FOLLOWUP.value,
            }:
                text = getattr(item, text_attr)
                flagged.append(f"- [{label}#{item.id}] ({status.replace('_', ' ')}) {text}")

    if not flagged:
        lines.append("- None")
        return

    lines.extend(flagged)


def _next_suggested_action(run: Run, validation_gates: list) -> Optional[str]:
    if run.recommendation:
        return run.recommendation

    blocking_open = [
        g for g in validation_gates
        if g.blocking and str(g.status) in {"not_started", "in_progress", "weak", "failed"}
    ]
    if blocking_open:
        return "Address blocking validation-gate gaps before advancing the run phase."

    if run.current_decision:
        decision = str(run.current_decision)
        if decision == "watch":
            return "Collect additional evidence and re-evaluate the strongest weak or disputed claims."
        if decision == "publish":
            return "Draft a publishable report based on accepted claims and clearly-labeled uncertainties."
        if decision == "prototype_later":
            return "Capture explicit trigger conditions for when to revisit this prototype."
        if decision == "build_approved":
            return "Define the first prototype slice and success event before implementation."
        if decision == "archive":
            return "Archive for now and document what new evidence would justify reopening."

    return None


def _display_or_none(value: object) -> str:
    if value is None:
        return "none"
    return str(value).replace("_", " ")


def _default_export_root() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / ".local" / "exports" / "reports"


def _to_repo_relative(path: Path) -> str:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _next_report_path(run_dir: Path, run_id: int) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    base = run_dir / f"run-{run_id}-report-{stamp}.md"
    if not base.exists():
        return base

    suffix = 2
    while True:
        candidate = run_dir / f"run-{run_id}-report-{stamp}-v{suffix}.md"
        if not candidate.exists():
            return candidate
        suffix += 1
