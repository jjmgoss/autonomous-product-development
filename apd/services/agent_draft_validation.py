from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from apd.domain.models import EvidenceRelationship, EvidenceTargetType, RunPhase
from apd.services.agent_draft_import import AgentDraftPackage


FIELD_ALIASES: dict[str, dict[str, str]] = {
    "sources": {
        "type": "source_type",
        "accessed_at": "captured_at",
    },
    "evidence_excerpts": {
        "text": "excerpt_text",
        "locator": "location_reference",
    },
    "claims": {
        "claim": "statement",
    },
    "themes": {
        "theme": "name",
    },
    "candidates": {
        "name": "title",
        "description": "summary",
    },
}

LEGACY_GATE_PHASE_MAP = {
    "problem_validation": RunPhase.SUPPORTED_OPPORTUNITY.value,
    "solution_validation": RunPhase.VETTED_OPPORTUNITY.value,
    "commercial_validation": RunPhase.VETTED_OPPORTUNITY.value,
}

LEGACY_EVIDENCE_TARGET_FIELDS = {
    "claim_id": EvidenceTargetType.CLAIM.value,
    "theme_id": EvidenceTargetType.THEME.value,
    "candidate_id": EvidenceTargetType.CANDIDATE.value,
    "gate_id": EvidenceTargetType.VALIDATION_GATE.value,
}

ALLOWED_GATE_PHASES = [phase.value for phase in RunPhase]
ALLOWED_EVIDENCE_RELATIONSHIPS = [relationship.value for relationship in EvidenceRelationship]

OBJECT_ALLOWED_FIELDS: dict[str, set[str]] = {
    "run": {"title", "intent", "summary", "mode", "phase", "recommendation"},
    "sources": {
        "id",
        "title",
        "source_type",
        "url",
        "origin",
        "author_or_org",
        "captured_at",
        "published_at",
        "raw_path",
        "normalized_path",
        "reliability_notes",
        "summary",
        "metadata_json",
    },
    "evidence_excerpts": {
        "id",
        "source_id",
        "excerpt_text",
        "location_reference",
        "excerpt_type",
        "metadata_json",
    },
    "claims": {
        "id",
        "statement",
        "claim_type",
        "confidence",
        "created_by",
        "metadata_json",
    },
    "themes": {
        "id",
        "name",
        "summary",
        "theme_type",
        "severity",
        "frequency",
        "user_segment",
        "workflow",
        "metadata_json",
    },
    "candidates": {
        "id",
        "title",
        "summary",
        "target_user",
        "first_workflow",
        "first_wedge",
        "prototype_success_event",
        "monetization_path",
        "substitutes",
        "risks",
        "why_now",
        "why_it_might_fail",
        "score",
        "rank",
        "metadata_json",
    },
    "validation_gates": {
        "id",
        "candidate_id",
        "phase",
        "name",
        "description",
        "status",
        "blocking",
        "evidence_summary",
        "missing_evidence",
        "metadata_json",
    },
    "evidence_links": {
        "id",
        "source_id",
        "excerpt_id",
        "target_type",
        "target_id",
        "relationship",
        "strength",
        "notes",
        "metadata_json",
    },
}


@dataclass
class AgentDraftValidationReport:
    path: Path
    is_valid: bool
    package: AgentDraftPackage | None = None
    errors: list[str] = field(default_factory=list)
    grouped_errors: list[str] = field(default_factory=list)
    repair_hints: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def build_repair_prompt(self) -> str:
        summary_lines = self.grouped_errors or self.errors or ["No validation errors recorded."]
        hint_lines = self.repair_hints or [
            "Preserve the research meaning. Only repair APD draft schema shape, enums, and field names.",
        ]
        prompt_lines = [
            "Repair this APD agent draft package so it passes strict APD draft validation.",
            "Return only JSON.",
            "Preserve the underlying research content and IDs unless a schema fix requires a field rename.",
            "Use exact APD field names and enums.",
            "Move unexpected extra object fields into metadata_json when they still matter.",
            "",
            "Validation summary:",
        ]
        prompt_lines.extend(f"- {line}" for line in summary_lines)
        prompt_lines.append("")
        prompt_lines.append("Likely fixes:")
        prompt_lines.extend(f"- {line}" for line in hint_lines)
        return "\n".join(prompt_lines)


@dataclass
class AgentDraftNormalizationResult:
    normalized_data: dict[str, Any]
    applied_fixes: list[str]
    validation_report: AgentDraftValidationReport


def validate_agent_draft_file(path: Path) -> AgentDraftValidationReport:
    try:
        raw_data = _read_raw_json(path)
    except ValueError as exc:
        error_text = str(exc)
        return AgentDraftValidationReport(
            path=path,
            is_valid=False,
            errors=[error_text],
            grouped_errors=[error_text],
        )
    if not isinstance(raw_data, dict):
        return AgentDraftValidationReport(
            path=path,
            is_valid=False,
            errors=["top-level JSON value must be an object"],
            grouped_errors=["Top-level JSON value must be an object."],
            repair_hints=["Wrap the package in one JSON object with run, sources, claims, candidates, and related arrays."],
        )

    try:
        package = AgentDraftPackage.model_validate(raw_data)
    except ValidationError as exc:
        errors = _format_validation_errors(exc)
        grouped_errors = _collect_grouped_errors(raw_data)
        repair_hints = _collect_repair_hints(raw_data)
        if not grouped_errors:
            grouped_errors = errors[:8]
        return AgentDraftValidationReport(
            path=path,
            is_valid=False,
            errors=errors,
            grouped_errors=grouped_errors,
            repair_hints=repair_hints,
        )

    return AgentDraftValidationReport(path=path, is_valid=True, package=package)


def normalize_agent_draft_file(path: Path) -> AgentDraftNormalizationResult:
    try:
        raw_data = _read_raw_json(path)
    except ValueError as exc:
        report = AgentDraftValidationReport(
            path=path,
            is_valid=False,
            errors=[str(exc)],
            grouped_errors=[str(exc)],
        )
        return AgentDraftNormalizationResult(normalized_data={}, applied_fixes=[], validation_report=report)
    if not isinstance(raw_data, dict):
        report = AgentDraftValidationReport(
            path=path,
            is_valid=False,
            errors=["top-level JSON value must be an object"],
            grouped_errors=["Top-level JSON value must be an object."],
        )
        return AgentDraftNormalizationResult(normalized_data={}, applied_fixes=[], validation_report=report)

    normalized = json.loads(json.dumps(raw_data))
    applied_fixes: list[str] = []

    _normalize_section_aliases(normalized, applied_fixes)
    _normalize_claim_confidence(normalized, applied_fixes)
    _normalize_gate_phases(normalized, applied_fixes)
    _normalize_evidence_link_targets(normalized, applied_fixes)
    _move_extra_fields_to_metadata(normalized, applied_fixes)

    report = validate_agent_draft_data(path, normalized)
    return AgentDraftNormalizationResult(
        normalized_data=normalized,
        applied_fixes=applied_fixes,
        validation_report=report,
    )


def validate_agent_draft_data(path: Path, raw_data: dict[str, Any]) -> AgentDraftValidationReport:
    try:
        package = AgentDraftPackage.model_validate(raw_data)
    except ValidationError as exc:
        errors = _format_validation_errors(exc)
        grouped_errors = _collect_grouped_errors(raw_data)
        repair_hints = _collect_repair_hints(raw_data)
        if not grouped_errors:
            grouped_errors = errors[:8]
        return AgentDraftValidationReport(
            path=path,
            is_valid=False,
            errors=errors,
            grouped_errors=grouped_errors,
            repair_hints=repair_hints,
        )

    return AgentDraftValidationReport(path=path, is_valid=True, package=package)


def _read_raw_json(path: Path) -> Any:
    try:
        raw_text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"could not read draft package: {exc}") from exc

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def _format_validation_errors(exc: ValidationError) -> list[str]:
    errors: list[str] = []
    for err in exc.errors():
        location = ".".join(str(part) for part in err.get("loc", []))
        message = err.get("msg", "validation error")
        errors.append(f"{location}: {message}" if location else message)
    return errors


def _collect_grouped_errors(raw_data: dict[str, Any]) -> list[str]:
    grouped: list[str] = []

    for section, aliases in FIELD_ALIASES.items():
        items = _section_items(raw_data, section)
        for alias, canonical in aliases.items():
            count = sum(1 for item in items if alias in item and canonical not in item)
            if count:
                grouped.append(
                    f"{section}: rename {alias} -> {canonical} in {count} item(s)."
                )

    confidence_count = sum(
        1
        for item in _section_items(raw_data, "claims")
        if isinstance(item.get("confidence"), str)
    )
    if confidence_count:
        grouped.append(
            f"claims: confidence must be numeric, not string, in {confidence_count} item(s)."
        )

    gate_phase_counts: dict[str, int] = {}
    for item in _section_items(raw_data, "validation_gates"):
        phase = item.get("phase")
        if isinstance(phase, str) and phase in LEGACY_GATE_PHASE_MAP:
            gate_phase_counts[phase] = gate_phase_counts.get(phase, 0) + 1
    for phase, count in gate_phase_counts.items():
        grouped.append(
            f"validation_gates: phase {phase} is not allowed; use {LEGACY_GATE_PHASE_MAP[phase]} in {count} item(s)."
        )

    legacy_target_count = 0
    for item in _section_items(raw_data, "evidence_links"):
        if any(field in item for field in LEGACY_EVIDENCE_TARGET_FIELDS):
            legacy_target_count += 1
    if legacy_target_count:
        grouped.append(
            "evidence_links: replace legacy target fields like claim_id/theme_id/candidate_id/gate_id with target_type + target_id "
            f"in {legacy_target_count} item(s)."
        )

    relationship_count = sum(
        1
        for item in _section_items(raw_data, "evidence_links")
        if "relationship" not in item
    )
    if relationship_count:
        grouped.append(
            f"evidence_links: relationship is required in {relationship_count} item(s)."
        )

    extras = _collect_extra_field_summaries(raw_data)
    grouped.extend(extras)
    return grouped


def _collect_repair_hints(raw_data: dict[str, Any]) -> list[str]:
    hints: list[str] = []
    for section, aliases in FIELD_ALIASES.items():
        items = _section_items(raw_data, section)
        for alias, canonical in aliases.items():
            if any(alias in item and canonical not in item for item in items):
                hints.append(f"In {section}, rename {alias} to {canonical}.")

    if any(isinstance(item.get("confidence"), str) for item in _section_items(raw_data, "claims")):
        hints.append("Convert claims.confidence values from quoted strings like \"0.72\" to numbers like 0.72.")

    gate_aliases = [
        phase
        for phase in LEGACY_GATE_PHASE_MAP
        if any(item.get("phase") == phase for item in _section_items(raw_data, "validation_gates"))
    ]
    if gate_aliases:
        hints.append(
            "Use validation_gates.phase values from the APD run phases only: "
            + ", ".join(ALLOWED_GATE_PHASES)
            + "."
        )
        for phase in gate_aliases:
            hints.append(f"Map validation_gates.phase {phase} to {LEGACY_GATE_PHASE_MAP[phase]}.")

    if any(any(field in item for field in LEGACY_EVIDENCE_TARGET_FIELDS) for item in _section_items(raw_data, "evidence_links")):
        hints.append(
            "Replace evidence_links legacy target fields with target_type and target_id: claim_id -> target_type claim, theme_id -> theme, candidate_id -> candidate, gate_id -> validation_gate."
        )

    if any("relationship" not in item for item in _section_items(raw_data, "evidence_links")):
        hints.append(
            "Each evidence link needs relationship set to one of: "
            + ", ".join(ALLOWED_EVIDENCE_RELATIONSHIPS)
            + "."
        )

    if _collect_extra_field_summaries(raw_data):
        hints.append("Move unexpected extra object fields into metadata_json when they are still useful to keep.")

    return hints


def _section_items(raw_data: dict[str, Any], section: str) -> list[dict[str, Any]]:
    value = raw_data.get(section)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _collect_extra_field_summaries(raw_data: dict[str, Any]) -> list[str]:
    summaries: list[str] = []
    run_value = raw_data.get("run")
    if isinstance(run_value, dict):
        extras = sorted(set(run_value) - OBJECT_ALLOWED_FIELDS["run"])
        if extras:
            summaries.append(f"run: unexpected fields {', '.join(extras)}.")

    for section, allowed_fields in OBJECT_ALLOWED_FIELDS.items():
        if section == "run":
            continue
        extras_count = 0
        for item in _section_items(raw_data, section):
            extras = set(item) - allowed_fields - set(FIELD_ALIASES.get(section, {})) - set(LEGACY_EVIDENCE_TARGET_FIELDS)
            if extras:
                extras_count += 1
        if extras_count:
            summaries.append(
                f"{section}: move unexpected extra fields into metadata_json in {extras_count} item(s)."
            )
    return summaries


def _normalize_section_aliases(raw_data: dict[str, Any], applied_fixes: list[str]) -> None:
    for section, aliases in FIELD_ALIASES.items():
        for index, item in enumerate(_section_items(raw_data, section)):
            for alias, canonical in aliases.items():
                if alias in item and canonical not in item:
                    item[canonical] = item.pop(alias)
                    applied_fixes.append(f"{section}[{index}]: renamed {alias} -> {canonical}")


def _normalize_claim_confidence(raw_data: dict[str, Any], applied_fixes: list[str]) -> None:
    for index, item in enumerate(_section_items(raw_data, "claims")):
        confidence = item.get("confidence")
        if isinstance(confidence, str):
            try:
                item["confidence"] = float(confidence)
            except ValueError:
                continue
            applied_fixes.append(f"claims[{index}]: converted confidence string to number")


def _normalize_gate_phases(raw_data: dict[str, Any], applied_fixes: list[str]) -> None:
    for index, item in enumerate(_section_items(raw_data, "validation_gates")):
        phase = item.get("phase")
        if phase in LEGACY_GATE_PHASE_MAP:
            item["phase"] = LEGACY_GATE_PHASE_MAP[phase]
            applied_fixes.append(
                f"validation_gates[{index}]: mapped phase {phase} -> {item['phase']}"
            )


def _normalize_evidence_link_targets(raw_data: dict[str, Any], applied_fixes: list[str]) -> None:
    for index, item in enumerate(_section_items(raw_data, "evidence_links")):
        if item.get("target_type") and item.get("target_id"):
            continue

        matches = [
            (field_name, target_type, item.get(field_name))
            for field_name, target_type in LEGACY_EVIDENCE_TARGET_FIELDS.items()
            if item.get(field_name)
        ]
        if len(matches) != 1:
            continue

        field_name, target_type, target_id = matches[0]
        item["target_type"] = target_type
        item["target_id"] = target_id
        item.pop(field_name, None)
        applied_fixes.append(
            f"evidence_links[{index}]: mapped {field_name} -> target_type={target_type}, target_id={target_id}"
        )


def _move_extra_fields_to_metadata(raw_data: dict[str, Any], applied_fixes: list[str]) -> None:
    for section, allowed_fields in OBJECT_ALLOWED_FIELDS.items():
        if section == "run":
            continue
        for index, item in enumerate(_section_items(raw_data, section)):
            extras = sorted(
                set(item)
                - allowed_fields
                - set(FIELD_ALIASES.get(section, {}))
                - set(LEGACY_EVIDENCE_TARGET_FIELDS)
            )
            if not extras:
                continue
            metadata_json = item.get("metadata_json")
            if not isinstance(metadata_json, dict):
                metadata_json = {}
                item["metadata_json"] = metadata_json
            for field_name in extras:
                metadata_json[field_name] = item.pop(field_name)
            applied_fixes.append(
                f"{section}[{index}]: moved unexpected fields to metadata_json ({', '.join(extras)})"
            )
