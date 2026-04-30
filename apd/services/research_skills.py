"""Research skill manifest loading and prompt-context rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESEARCH_SKILL_MANIFEST = REPO_ROOT / "skills" / "research" / "manifest.yaml"

# Runtime phases use a few pragmatic batch names that are intentionally narrower
# than the durable research-harness phase names in the skill manifest.
PHASE_ALIASES: dict[str, tuple[str, ...]] = {
    "candidate_batch": ("candidate_generation",),
    "claim_theme_batch": ("grounded_claim_generation", "theme_synthesis"),
    "validation_gate_batch": ("validation_gate_generation",),
    "web_research_targets": ("web_discovery",),
}


@dataclass(frozen=True)
class ResearchSkillSpec:
    """Manifest entry for one research skill."""

    id: str
    path: str
    phases: tuple[str, ...]
    trigger_terms: tuple[str, ...]
    expected_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    max_prompt_budget_chars: int
    repo_root: Path

    @property
    def file_path(self) -> Path:
        return self.repo_root / self.path


def _parse_inline_manifest_value(raw_value: str) -> object:
    value = raw_value.strip()
    if value.startswith("[") and value.endswith("]"):
        items: list[str] = []
        for part in value[1:-1].split(","):
            item = part.strip().strip("\"'")
            if item:
                items.append(item)
        return items
    if re.fullmatch(r"\d+", value):
        return int(value)
    return value.strip("\"'")


def _coerce_string_tuple(value: object, *, field_name: str, skill_id: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Research skill `{skill_id}` field `{field_name}` must be a list.")
    items = tuple(str(item).strip() for item in value if str(item).strip())
    if not items:
        raise ValueError(f"Research skill `{skill_id}` field `{field_name}` must not be empty.")
    return items


def _repo_root_for_manifest(manifest_path: Path) -> Path:
    # The stable manifest path is <repo>/skills/research/manifest.yaml.
    try:
        return manifest_path.resolve().parents[2]
    except IndexError:
        return REPO_ROOT


def load_research_skill_manifest(
    manifest_path: str | Path | None = None,
) -> list[ResearchSkillSpec]:
    """Load the research skill manifest without adding a runtime YAML dependency.

    The repository manifest deliberately uses a small YAML subset: a top-level
    ``skills:`` list with scalar fields and inline lists. This parser validates
    that shape and fails with actionable errors when the skill tree drifts.
    """

    resolved_manifest_path = Path(manifest_path or DEFAULT_RESEARCH_SKILL_MANIFEST)
    repo_root = _repo_root_for_manifest(resolved_manifest_path)

    try:
        text = resolved_manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Missing research skill manifest: {resolved_manifest_path}") from exc

    raw_skills: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    found_skills_list = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not found_skills_list:
            if stripped == "skills:":
                found_skills_list = True
            continue

        if stripped.startswith("- "):
            if current is not None:
                raw_skills.append(current)
            field_text = stripped[2:]
            if ":" not in field_text:
                raise ValueError(f"{resolved_manifest_path} has an invalid skill entry: {stripped}")
            key, value = field_text.split(":", 1)
            current = {key.strip(): _parse_inline_manifest_value(value)}
            continue

        if current is None:
            raise ValueError(f"{resolved_manifest_path} has fields before the first skill entry.")
        if not line.startswith("    "):
            raise ValueError(
                f"{resolved_manifest_path} has unsupported indentation for skill fields: {stripped}"
            )
        if ":" not in stripped:
            raise ValueError(f"{resolved_manifest_path} has an invalid skill field: {stripped}")

        key, value = stripped.split(":", 1)
        current[key.strip()] = _parse_inline_manifest_value(value)

    if current is not None:
        raw_skills.append(current)

    if not found_skills_list:
        raise ValueError(f"{resolved_manifest_path} must contain a top-level `skills:` list.")
    if not raw_skills:
        raise ValueError(f"{resolved_manifest_path} must contain at least one research skill.")

    specs: list[ResearchSkillSpec] = []
    for index, raw_skill in enumerate(raw_skills, start=1):
        skill_id = str(raw_skill.get("id") or "").strip()
        if not skill_id:
            raise ValueError(f"{resolved_manifest_path} skill #{index} is missing `id`.")
        path = str(raw_skill.get("path") or "").strip()
        if not path:
            raise ValueError(f"{resolved_manifest_path} skill `{skill_id}` is missing `path`.")

        max_budget = raw_skill.get("max_prompt_budget_chars")
        if not isinstance(max_budget, int) or max_budget <= 0:
            raise ValueError(
                f"{resolved_manifest_path} skill `{skill_id}` must declare a positive "
                "`max_prompt_budget_chars` integer."
            )

        spec = ResearchSkillSpec(
            id=skill_id,
            path=path,
            phases=_coerce_string_tuple(raw_skill.get("phases"), field_name="phases", skill_id=skill_id),
            trigger_terms=_coerce_string_tuple(
                raw_skill.get("trigger_terms"), field_name="trigger_terms", skill_id=skill_id
            ),
            expected_inputs=_coerce_string_tuple(
                raw_skill.get("expected_inputs"), field_name="expected_inputs", skill_id=skill_id
            ),
            expected_outputs=_coerce_string_tuple(
                raw_skill.get("expected_outputs"), field_name="expected_outputs", skill_id=skill_id
            ),
            max_prompt_budget_chars=max_budget,
            repo_root=repo_root,
        )
        if not spec.file_path.is_file():
            raise FileNotFoundError(f"Research skill `{spec.id}` references missing file: {spec.file_path}")
        specs.append(spec)

    return specs


def _expanded_phase_names(phase_name: str) -> tuple[str, ...]:
    normalized = str(phase_name or "").strip().lower()
    if not normalized:
        return tuple()
    return PHASE_ALIASES.get(normalized, (normalized,))


def resolve_research_skills_for_phase(
    phase_name: str,
    *,
    max_skills: int | None = 4,
    manifest_path: str | Path | None = None,
) -> list[str]:
    """Resolve a deterministic, bounded skill list for a runtime phase."""

    phase_names = set(_expanded_phase_names(phase_name))
    if not phase_names:
        return []

    specs = load_research_skill_manifest(manifest_path)
    selected: list[str] = []

    # Research protocol is a cross-phase discipline skill. Keep it first when
    # applicable so every injected context reminds the model about grounding.
    for spec in specs:
        if spec.id == "research_protocol" and phase_names.intersection(spec.phases):
            selected.append(spec.id)
            break

    for spec in specs:
        if spec.id == "research_protocol":
            continue
        if phase_names.intersection(spec.phases):
            selected.append(spec.id)

    if max_skills is not None:
        return selected[: max(0, max_skills)]
    return selected


def _trim_to_chars(text: str, max_chars: int) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return cleaned
    marker = "\n...[research skill context truncated]"
    if max_chars <= len(marker):
        return cleaned[:max(0, max_chars)].rstrip()
    return cleaned[: max_chars - len(marker)].rstrip() + marker


def render_research_skill_context(
    skill_ids: list[str] | tuple[str, ...],
    *,
    max_chars: int = 3500,
    manifest_path: str | Path | None = None,
) -> str:
    """Render bounded research skill instructions for prompt injection."""

    if max_chars <= 0 or not skill_ids:
        return ""

    specs = load_research_skill_manifest(manifest_path)
    specs_by_id = {spec.id: spec for spec in specs}

    chunks: list[str] = [
        "## Selected APD research skills",
        "",
        "Use these phase-scoped skills as operational instructions. Keep output within the current phase contract.",
    ]

    remaining = max_chars - len("\n".join(chunks))
    for skill_id in skill_ids:
        spec = specs_by_id.get(skill_id)
        if spec is None:
            raise ValueError(f"Unknown research skill id requested for prompt context: {skill_id}")
        if remaining <= 0:
            break

        text = spec.file_path.read_text(encoding="utf-8")
        per_skill_budget = max(300, min(spec.max_prompt_budget_chars, remaining))
        trimmed = _trim_to_chars(text, per_skill_budget)
        chunk = "\n".join(
            [
                "",
                f"### Research skill: {spec.id}",
                f"Manifest path: `{spec.path}`",
                f"Applies to phases: {', '.join(spec.phases)}",
                "",
                trimmed,
            ]
        )
        chunks.append(chunk)
        remaining = max_chars - len("\n".join(chunks))

    return _trim_to_chars("\n".join(chunks), max_chars)


def render_research_skill_context_for_phase(
    phase_name: str,
    *,
    max_skills: int | None = 4,
    max_chars: int = 3500,
    manifest_path: str | Path | None = None,
) -> str:
    """Resolve and render research skill context for one runtime phase."""

    skill_ids = resolve_research_skills_for_phase(
        phase_name,
        max_skills=max_skills,
        manifest_path=manifest_path,
    )
    return render_research_skill_context(
        skill_ids,
        max_chars=max_chars,
        manifest_path=manifest_path,
    )
