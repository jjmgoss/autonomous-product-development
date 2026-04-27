from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ResearchComponentEventType(StrEnum):
    CANDIDATE_PROPOSED = "candidate.proposed"
    CLAIM_PROPOSED = "claim.proposed"
    THEME_PROPOSED = "theme.proposed"
    SOURCE_ADDED = "source.added"
    EVIDENCE_EXCERPT_ADDED = "evidence_excerpt.added"
    VALIDATION_GATE_PROPOSED = "validation_gate.proposed"
    EVIDENCE_LINK_ADDED = "evidence_link.added"


class ResearchComponentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0", min_length=1)
    event_type: ResearchComponentEventType
    external_id: str = Field(min_length=1)
    payload: dict[str, Any]


class ResearchComponentBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0", min_length=1)
    batch_id: str | None = None
    events: list[ResearchComponentEvent] = Field(default_factory=list)


@dataclass(frozen=True)
class ComponentExecutionResult:
    success: bool
    package: dict[str, Any] | None
    errors: list[str]
    warnings: list[str]


class ComponentDraftAssembler:
    def __init__(self, *, run_title: str, run_intent: str | None, agent_name: str, external_draft_id: str):
        self._run_title = run_title
        self._run_intent = run_intent
        self._agent_name = agent_name
        self._external_draft_id = external_draft_id
        self._warnings: list[str] = []
        self._event_ids: set[str] = set()
        self._data: dict[str, Any] = {
            "schema_version": "1.0",
            "external_draft_id": external_draft_id,
            "agent_name": agent_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "run": {
                "title": run_title,
                "intent": run_intent,
                "mode": "ollama_component_execution",
                "recommendation": "needs_human_review",
            },
            "warnings": [],
            "limitations": ["Component-based prototype output assembled from typed model events."],
            "sources": [],
            "evidence_excerpts": [],
            "claims": [],
            "themes": [],
            "candidates": [],
            "validation_gates": [],
            "evidence_links": [],
        }

    def apply_batch(self, batch: ResearchComponentBatch) -> ComponentExecutionResult:
        errors: list[str] = []
        for index, event in enumerate(batch.events):
            if event.external_id in self._event_ids:
                errors.append(f"duplicate event external_id in batch: {event.external_id}")
                continue
            self._event_ids.add(event.external_id)
            try:
                self._apply_event(event)
            except ValueError as exc:
                errors.append(f"event[{index}] {event.event_type.value}: {exc}")
        return ComponentExecutionResult(success=len(errors) == 0, package=self.package_dict(), errors=errors, warnings=list(self._warnings))

    def package_dict(self) -> dict[str, Any]:
        package = dict(self._data)
        package["warnings"] = list(self._warnings)
        return package

    def _apply_event(self, event: ResearchComponentEvent) -> None:
        payload = dict(event.payload or {})
        metadata = payload.get("metadata_json")
        if metadata is None or not isinstance(metadata, dict):
            metadata = {}
        payload["metadata_json"] = metadata

        if event.event_type == ResearchComponentEventType.CANDIDATE_PROPOSED:
            title = str(payload.get("title") or "").strip()
            if not title:
                raise ValueError("candidate payload requires title")
            self._data["candidates"].append(
                {
                    "id": event.external_id,
                    "title": title,
                    "summary": payload.get("summary"),
                    "target_user": payload.get("target_user"),
                    "first_workflow": payload.get("first_workflow"),
                    "first_wedge": payload.get("first_wedge"),
                    "prototype_success_event": payload.get("prototype_success_event"),
                    "monetization_path": payload.get("monetization_path"),
                    "substitutes": payload.get("substitutes"),
                    "risks": payload.get("risks"),
                    "why_now": payload.get("why_now"),
                    "why_it_might_fail": payload.get("why_it_might_fail"),
                    "metadata_json": metadata,
                }
            )
            return

        if event.event_type == ResearchComponentEventType.CLAIM_PROPOSED:
            statement = str(payload.get("statement") or "").strip()
            if not statement:
                raise ValueError("claim payload requires statement")
            claim: dict[str, Any] = {
                "id": event.external_id,
                "statement": statement,
                "claim_type": payload.get("claim_type"),
                "created_by": payload.get("created_by"),
                "metadata_json": metadata,
            }
            if payload.get("confidence") is not None:
                try:
                    claim["confidence"] = float(payload["confidence"])
                except (TypeError, ValueError):
                    raise ValueError("claim confidence must be numeric")
            self._data["claims"].append(claim)
            return

        if event.event_type == ResearchComponentEventType.THEME_PROPOSED:
            name = str(payload.get("name") or "").strip()
            if not name:
                raise ValueError("theme payload requires name")
            self._data["themes"].append(
                {
                    "id": event.external_id,
                    "name": name,
                    "summary": payload.get("summary"),
                    "theme_type": payload.get("theme_type"),
                    "severity": payload.get("severity"),
                    "frequency": payload.get("frequency"),
                    "user_segment": payload.get("user_segment"),
                    "workflow": payload.get("workflow"),
                    "metadata_json": metadata,
                }
            )
            return

        if event.event_type == ResearchComponentEventType.SOURCE_ADDED:
            source_type = str(payload.get("source_type") or "").strip()
            if not source_type:
                raise ValueError("source payload requires source_type")
            self._data["sources"].append(
                {
                    "id": event.external_id,
                    "title": payload.get("title"),
                    "source_type": source_type,
                    "url": payload.get("url"),
                    "origin": payload.get("origin"),
                    "summary": payload.get("summary"),
                    "metadata_json": metadata,
                }
            )
            return

        if event.event_type == ResearchComponentEventType.EVIDENCE_EXCERPT_ADDED:
            source_id = str(payload.get("source_id") or "").strip()
            excerpt_text = str(payload.get("excerpt_text") or "").strip()
            if not source_id or not excerpt_text:
                raise ValueError("evidence excerpt payload requires source_id and excerpt_text")
            self._data["evidence_excerpts"].append(
                {
                    "id": event.external_id,
                    "source_id": source_id,
                    "excerpt_text": excerpt_text,
                    "location_reference": payload.get("location_reference"),
                    "excerpt_type": payload.get("excerpt_type"),
                    "metadata_json": metadata,
                }
            )
            return

        if event.event_type == ResearchComponentEventType.VALIDATION_GATE_PROPOSED:
            name = str(payload.get("name") or "").strip()
            if not name:
                raise ValueError("validation gate payload requires name")
            self._data["validation_gates"].append(
                {
                    "id": event.external_id,
                    "candidate_id": payload.get("candidate_id"),
                    "phase": payload.get("phase"),
                    "name": name,
                    "description": payload.get("description"),
                    "status": payload.get("status"),
                    "blocking": payload.get("blocking", True),
                    "evidence_summary": payload.get("evidence_summary"),
                    "missing_evidence": payload.get("missing_evidence"),
                    "metadata_json": metadata,
                }
            )
            return

        if event.event_type == ResearchComponentEventType.EVIDENCE_LINK_ADDED:
            target_type = str(payload.get("target_type") or "").strip()
            target_id = str(payload.get("target_id") or "").strip()
            relationship = str(payload.get("relationship") or "").strip()
            if not target_type or not target_id or not relationship:
                raise ValueError("evidence link payload requires target_type, target_id, and relationship")
            self._data["evidence_links"].append(
                {
                    "id": event.external_id,
                    "source_id": payload.get("source_id"),
                    "excerpt_id": payload.get("excerpt_id"),
                    "target_type": target_type,
                    "target_id": target_id,
                    "relationship": relationship,
                    "strength": payload.get("strength"),
                    "notes": payload.get("notes"),
                    "metadata_json": metadata,
                }
            )
            return

        raise ValueError(f"unsupported event type: {event.event_type}")


def parse_component_batch_from_data(raw_data: dict[str, Any]) -> tuple[ResearchComponentBatch | None, list[str]]:
    try:
        batch = ResearchComponentBatch.model_validate(raw_data)
    except ValidationError as exc:
        errors: list[str] = []
        for err in exc.errors():
            location = ".".join(str(part) for part in err.get("loc", []))
            message = err.get("msg", "validation error")
            errors.append(f"{location}: {message}" if location else message)
        return None, errors
    return batch, []
