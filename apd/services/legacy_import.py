from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from apd.domain.models import Artifact, Run, RunPhase, Source


@dataclass
class LegacyImportResult:
    legacy_run_id: str
    run_db_id: int
    created_run: bool
    linked_artifact_count: int
    imported_source_count: int
    warnings: list[str]


def import_legacy_run(
    db: Session,
    legacy_run_id: str,
    repo_root: Optional[Path] = None,
) -> Optional[LegacyImportResult]:
    root = repo_root or Path(__file__).resolve().parents[2]
    research_dir = root / "research-corpus" / "runs" / legacy_run_id
    artifact_dir = root / "artifacts" / "runs" / legacy_run_id

    if not research_dir.exists() and not artifact_dir.exists():
        return None

    warnings: list[str] = []

    research_manifest = _load_json_if_exists(
        research_dir / "manifest.json",
        warnings,
        missing_warning=f"missing research manifest: research-corpus/runs/{legacy_run_id}/manifest.json",
    )
    artifact_manifest = _load_json_if_exists(
        artifact_dir / "manifest.json",
        warnings,
        missing_warning=f"missing artifact manifest: artifacts/runs/{legacy_run_id}/manifest.json",
    )
    run_index_text = _read_text_if_exists(
        artifact_dir / "run-index.md",
        warnings,
        missing_warning=f"missing run index: artifacts/runs/{legacy_run_id}/run-index.md",
    )
    candidate_links_text = _read_text_if_exists(
        research_dir / "candidate-links.md",
        warnings,
        missing_warning=f"missing candidate links: research-corpus/runs/{legacy_run_id}/candidate-links.md",
    )
    discovery_summary_text = _read_first_existing_text(
        [artifact_dir / "reports" / "discovery-summary.md"],
        warnings,
        missing_warning=f"missing discovery summary: artifacts/runs/{legacy_run_id}/reports/discovery-summary.md",
    )

    intent = _first_non_empty(
        _as_str((research_manifest or {}).get("intent")),
        _as_str((artifact_manifest or {}).get("intent")),
        _extract_markdown_bullet(run_index_text, "intent"),
    )
    title = _derive_title(legacy_run_id, intent)
    summary = _derive_summary(discovery_summary_text, run_index_text, intent, legacy_run_id)
    recommendation = _clean_placeholder_value(_extract_markdown_bullet(run_index_text, "recommended outcome"))
    mode = _first_non_empty(
        _as_str((research_manifest or {}).get("mode")),
        _as_str((artifact_manifest or {}).get("mode")),
        _extract_markdown_bullet(run_index_text, "mode"),
        "legacy_import",
    )

    existing_run = _find_existing_legacy_run(db, legacy_run_id)
    created_run = existing_run is None
    run = existing_run or Run(
        title=title,
        intent=intent,
        summary=summary,
        mode=mode,
        phase=RunPhase.VAGUE_NOTION,
        recommendation=recommendation,
        metadata_json={
            "legacy_run_id": legacy_run_id,
            "legacy_imported": True,
        },
    )

    run.title = title
    run.intent = intent
    run.summary = summary
    run.mode = mode
    run.recommendation = recommendation
    run.metadata_json = {
        **(run.metadata_json or {}),
        "legacy_run_id": legacy_run_id,
        "legacy_imported": True,
        "legacy_paths": {
            "research_dir": _repo_relative_path(research_dir, root) if research_dir.exists() else None,
            "artifact_dir": _repo_relative_path(artifact_dir, root) if artifact_dir.exists() else None,
        },
        "legacy_warnings": warnings,
    }

    if created_run:
        db.add(run)
        db.flush()

    imported_source_count = _import_sources(
        db=db,
        run=run,
        legacy_run_id=legacy_run_id,
        research_manifest=research_manifest,
        root=root,
        warnings=warnings,
    )

    linked_artifact_count = _link_markdown_artifacts(
        db=db,
        run=run,
        legacy_run_id=legacy_run_id,
        root=root,
        research_dir=research_dir,
        artifact_dir=artifact_dir,
        artifact_manifest=artifact_manifest,
        warnings=warnings,
    )

    db.flush()

    source_count = len(db.execute(select(Source).where(Source.run_id == run.id)).scalars().all())
    run.source_count = source_count
    run.claim_count = run.claim_count or 0
    run.theme_count = run.theme_count or 0
    run.candidate_count = run.candidate_count or 0
    run.phase = RunPhase.EVIDENCE_COLLECTED if source_count else RunPhase.VAGUE_NOTION
    run.updated_at = datetime.now(timezone.utc)
    run.metadata_json = {
        **(run.metadata_json or {}),
        "legacy_warnings": warnings,
    }

    db.commit()
    db.refresh(run)

    return LegacyImportResult(
        legacy_run_id=legacy_run_id,
        run_db_id=run.id,
        created_run=created_run,
        linked_artifact_count=linked_artifact_count,
        imported_source_count=imported_source_count,
        warnings=warnings,
    )


def _find_existing_legacy_run(db: Session, legacy_run_id: str) -> Optional[Run]:
    runs = db.execute(select(Run)).scalars().all()
    for run in runs:
        metadata = run.metadata_json or {}
        if metadata.get("legacy_run_id") == legacy_run_id:
            return run
    return None


def _import_sources(
    *,
    db: Session,
    run: Run,
    legacy_run_id: str,
    research_manifest: Optional[dict[str, Any]],
    root: Path,
    warnings: list[str],
) -> int:
    if not research_manifest:
        return 0

    entries = research_manifest.get("sources")
    if entries is None:
        warnings.append("research manifest has no 'sources' field")
        return 0
    if not isinstance(entries, list):
        warnings.append("research manifest 'sources' field is not a list")
        return 0

    existing_sources = db.execute(select(Source).where(Source.run_id == run.id)).scalars().all()
    existing_ids = {
        (source.metadata_json or {}).get("legacy_source_id")
        for source in existing_sources
        if (source.metadata_json or {}).get("legacy_source_id")
    }

    imported = 0
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            warnings.append(f"skipped malformed source entry at index {index}: expected object")
            continue

        legacy_source_id = _as_str(entry.get("id")) or f"source-{index}"
        if legacy_source_id in existing_ids:
            continue

        title = _as_str(entry.get("title")) or _as_str(entry.get("url")) or f"Legacy source {index}"
        source_type = _as_str(entry.get("source_type")) or "legacy_source"
        raw_path = _normalize_manifest_path(entry.get("raw_path"), root)
        normalized_path = _normalize_manifest_path(entry.get("normalized_path"), root)
        note_path = _normalize_manifest_path(entry.get("note_path"), root)

        source = Source(
            run_id=run.id,
            title=title,
            source_type=source_type,
            url=_as_str(entry.get("url")),
            origin="legacy_import",
            author_or_org=_as_str(entry.get("speaker_or_org")),
            captured_at=_parse_datetime(_as_str(entry.get("captured_at")), warnings, f"source {legacy_source_id} captured_at"),
            raw_path=raw_path,
            normalized_path=normalized_path,
            reliability_notes=_as_str(entry.get("reliability_notes")),
            summary=_as_str(entry.get("summary")),
            metadata_json={
                "legacy_run_id": legacy_run_id,
                "legacy_source_id": legacy_source_id,
                "legacy_note_path": note_path,
                "legacy_workflow": _as_str(entry.get("workflow")),
                "legacy_why_it_matters": _as_str(entry.get("why_it_matters")),
            },
        )
        db.add(source)
        existing_ids.add(legacy_source_id)
        imported += 1

    return imported


def _link_markdown_artifacts(
    *,
    db: Session,
    run: Run,
    legacy_run_id: str,
    root: Path,
    research_dir: Path,
    artifact_dir: Path,
    artifact_manifest: Optional[dict[str, Any]],
    warnings: list[str],
) -> int:
    artifact_paths: set[Path] = set()

    candidate_links = research_dir / "candidate-links.md"
    if candidate_links.exists():
        artifact_paths.add(candidate_links)

    run_index = artifact_dir / "run-index.md"
    if run_index.exists():
        artifact_paths.add(run_index)

    review_dir = artifact_dir / "review-package"
    if review_dir.exists():
        artifact_paths.update(path for path in review_dir.glob("*.md") if path.is_file())
    else:
        warnings.append(f"missing review-package directory: artifacts/runs/{legacy_run_id}/review-package")

    reports_dir = artifact_dir / "reports"
    if reports_dir.exists():
        artifact_paths.update(path for path in reports_dir.glob("*.md") if path.is_file())
    else:
        warnings.append(f"missing reports directory: artifacts/runs/{legacy_run_id}/reports")

    if artifact_manifest and isinstance(artifact_manifest.get("artifacts"), list):
        for entry in artifact_manifest["artifacts"]:
            if not isinstance(entry, dict):
                warnings.append("skipped malformed artifact manifest entry: expected object")
                continue
            path_value = _as_str(entry.get("path"))
            if not path_value:
                continue
            full_path = root / path_value
            if full_path.suffix.lower() == ".md" and full_path.exists():
                artifact_paths.add(full_path)

    if not artifact_paths:
        warnings.append(f"no legacy markdown artifacts found for run {legacy_run_id}")
        return 0

    existing_artifact_paths = {
        artifact.path
        for artifact in db.execute(select(Artifact).where(Artifact.run_id == run.id)).scalars().all()
        if artifact.path
    }

    linked = 0
    for full_path in sorted(artifact_paths):
        relative_path = _repo_relative_path(full_path, root)
        if relative_path in existing_artifact_paths:
            continue

        text = _safe_read_text(full_path)
        artifact = Artifact(
            run_id=run.id,
            artifact_type=_classify_artifact_type(relative_path),
            title=_artifact_title(relative_path),
            path=relative_path,
            created_by="legacy_import",
            summary=_artifact_summary(text, relative_path),
            metadata_json={
                "legacy_run_id": legacy_run_id,
                "legacy_linked": True,
            },
        )
        db.add(artifact)
        existing_artifact_paths.add(relative_path)
        linked += 1

    return linked


def _load_json_if_exists(path: Path, warnings: list[str], missing_warning: str) -> Optional[dict[str, Any]]:
    if not path.exists():
        warnings.append(missing_warning)
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warnings.append(f"could not parse JSON at {path.as_posix()}: {exc.msg}")
        return None
    if not isinstance(raw, dict):
        warnings.append(f"expected JSON object at {path.as_posix()}")
        return None
    return raw


def _read_text_if_exists(path: Path, warnings: list[str], missing_warning: str) -> Optional[str]:
    if not path.exists():
        warnings.append(missing_warning)
        return None
    return _safe_read_text(path)


def _read_first_existing_text(paths: list[Path], warnings: list[str], missing_warning: str) -> Optional[str]:
    for path in paths:
        if path.exists():
            return _safe_read_text(path)
    warnings.append(missing_warning)
    return None


def _safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_markdown_bullet(text: Optional[str], field_name: str) -> Optional[str]:
    if not text:
        return None
    pattern = re.compile(rf"^-\s*{re.escape(field_name)}:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip().strip("`")


def _derive_title(legacy_run_id: str, intent: Optional[str]) -> str:
    slug = re.sub(r"^\d{8}-", "", legacy_run_id)
    slug = re.sub(r"-r\d+$", "", slug)
    words = [part for part in slug.split("-") if part]
    base_title = " ".join(word.capitalize() for word in words) if words else legacy_run_id
    if base_title.lower() == "run":
        base_title = legacy_run_id
    if intent and intent.strip() and intent.strip().lower() != base_title.lower():
        return base_title
    return base_title


def _derive_summary(
    discovery_summary_text: Optional[str],
    run_index_text: Optional[str],
    intent: Optional[str],
    legacy_run_id: str,
) -> str:
    for text in (discovery_summary_text, run_index_text):
        summary = _first_meaningful_paragraph(text)
        if summary:
            return summary
    if intent:
        return f"Legacy APD run imported from existing artifacts. Intent: {intent}"
    return f"Legacy APD run imported from existing artifacts for run ID {legacy_run_id}."


def _first_meaningful_paragraph(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    for paragraph in paragraphs:
        if paragraph.startswith("#"):
            continue
        if paragraph.lower().startswith("launch scaffold"):
            continue
        if paragraph.startswith("-"):
            continue
        return " ".join(line.strip() for line in paragraph.splitlines()).strip()
    return None


def _clean_placeholder_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lowered = value.lower()
    if any(token in lowered for token in ("in progress", "replace with", "do not fill", "not run yet")):
        return None
    return value


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _parse_datetime(value: Optional[str], warnings: list[str], label: str) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        warnings.append(f"could not parse datetime for {label}: {value}")
        return None


def _normalize_manifest_path(value: Any, root: Path) -> Optional[str]:
    text = _as_str(value)
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path.as_posix()
    return (root / path).relative_to(root).as_posix()


def _repo_relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _classify_artifact_type(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.endswith("candidate-links.md"):
        return "legacy_candidate_links"
    if normalized.endswith("run-index.md"):
        return "legacy_run_index"
    if "/review-package/" in normalized:
        return "legacy_review_package"
    if "/reports/" in normalized:
        return "legacy_report"
    return "legacy_markdown"


def _artifact_title(relative_path: str) -> str:
    name = Path(relative_path).stem.replace("-", " ").replace("_", " ")
    return name.title()


def _artifact_summary(text: str, relative_path: str) -> str:
    summary = _first_meaningful_paragraph(text)
    if summary:
        return summary[:300]
    return f"Legacy linked artifact from {relative_path}."


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
