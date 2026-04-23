from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "START_HERE.md",
    "ACTIVE_RUN.md",
    "DISCOVERY_RUN_PROMPT.md",
    "DISCOVERY_RUN_MODE.md",
    "theme.md",
    "agent/runbook.md",
    "agent/system-prompt.md",
    "agent/human-gates.md",
    "agent/repo-conventions.md",
    "agent/research-corpus-conventions.md",
    "agent/artifact-output-conventions.md",
    "docs/research.md",
    "docs/opportunity-scorecard.md",
    "docs/candidate-review.md",
    "docs/validation.md",
    "skills/product/research-skill.md",
    "skills/product/discovery-run-skill.md",
    "skills/product/monetization-sanity-skill.md",
    "skills/product/agent-operability-skill.md",
    "skills/product/competitor-substitute-analysis-skill.md",
    "templates/research-source-note.md",
    "templates/candidate-evidence-map.md",
    "templates/discovery-summary.md",
    "templates/run-index.md",
    "templates/research-manifest.template.json",
    "templates/artifact-manifest.template.json",
    "research-corpus/README.md",
    "research-corpus/runs/README.md",
    "research-corpus/shared/README.md",
    "artifacts/README.md",
    "artifacts/runs/README.md",
    "artifacts/projects/README.md",
    "artifacts/shared/README.md",
    "scripts/start_discovery_run.py",
    "scripts/clean_empty_run_dirs.py",
    "LAUNCH_MODEL_SUMMARY.md",
]

REQUIRED_DIRS = [
    "research-corpus/runs",
    "research-corpus/shared",
    "artifacts/runs",
    "artifacts/shared",
    "artifacts/projects",
]

RESEARCH_MANIFEST_FIELDS = {
    "id",
    "title",
    "url",
    "captured_at",
    "source_type",
    "run_id",
    "raw_path",
    "normalized_path",
    "note_path",
    "speaker_or_org",
    "workflow",
    "summary",
    "why_it_matters",
    "reliability_notes",
}

ARTIFACT_MANIFEST_FIELDS = {
    "id",
    "artifact_type",
    "path",
    "created_at",
    "created_by",
    "inputs",
    "purpose",
    "notes",
}

LAUNCH_SCAFFOLD_MARKER = "launch scaffold"
OPTIONAL_EMPTY_VALUES = {"", "none", "n/a", "na", "null"}

FORBIDDEN_PATTERNS = [
    re.compile(r"<run-id>", re.IGNORECASE),
    re.compile(r"<name>", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"Choose one:", re.IGNORECASE),
    re.compile(r"Explain why\.", re.IGNORECASE),
    re.compile(r"Use this file as reusable guidance", re.IGNORECASE),
    re.compile(r"Use this file shape", re.IGNORECASE),
    re.compile(r"Do not treat this file", re.IGNORECASE),
    re.compile(r"current status:\s*advance, keep alive, or drop", re.IGNORECASE),
]

REQUIRED_RUN_INDEX_HEADINGS = {
    "## run context",
    "## boundary status",
    "## execution checklist",
    "## key source links",
    "## reviewer route",
    "## recommendation snapshot",
    "## evidence that could overturn the ranking",
    "## continuation status",
}

REQUIRED_START_HEADINGS = {
    "## startup order",
    "## execution rules",
    "## stop rule",
    "## response policy",
}

REQUIRED_ACTIVE_RUN_HEADINGS = {
    "## current run",
    "## startup order",
    "## run id policy",
    "## response policy",
}

REQUIRED_ACTIVE_RUN_FIELDS = [
    "- run type:",
    "- boundary file:",
    "- detailed prompt:",
    "- readiness check:",
    "- launcher command:",
    "- completion check:",
    "- reviewer entry point:",
    "- checkpoint label:",
    "- checkpoint behavior:",
    "- post-discovery default:",
    "- hard boundaries:",
    "- completion point:",
]

MIN_NONEMPTY_LINES = {
    "START_HERE.md": 12,
    "ACTIVE_RUN.md": 16,
    "run-index.md": 18,
    "review-package/research.md": 25,
    "review-package/opportunity-scorecard.md": 18,
    "review-package/candidate-review.md": 18,
    "review-package/validation.md": 18,
    "reports/discovery-summary.md": 16,
    "candidate-links.md": 12,
}

RUN_INDEX_REQUIRED_FIELDS = {
    "actual source count",
    "actual source-type count",
    "actual candidate count",
    "recommended outcome",
    "leading candidate",
    "first buyer/user",
    "first wedge",
    "why this is not a platform fantasy",
    "why the leader won",
    "why it may still fail",
    "recommended next stage",
    "status marker",
    "hard-boundary status",
    "completion point status",
}

RUN_INDEX_PLACEHOLDER_SNIPPETS = (
    "in progress",
    "replace with",
    "do not fill until",
    "not reached yet",
    "discovery work still in progress",
    "requested human decision",
)

CANDIDATE_LINK_REQUIRED_BULLETS = {
    "short thesis",
    "status in ranking",
    "first buyer/user",
    "first wedge",
    "supporting evidence ids",
    "weakening evidence ids",
    "key supporting links",
    "substitute pressure notes",
    "why this is not a platform fantasy",
    "open questions that could change ranking",
}

WEAK_SUPPORTING_SOURCE_PATTERNS = [
    re.compile(r"https?://(?:www\.)?producthunt\.com/topics/[^/]+/?$", re.IGNORECASE),
    re.compile(r"https?://(?:www\.)?dev\.to/t/[^/]+/?$", re.IGNORECASE),
    re.compile(r"https?://(?:www\.)?reddit\.com/r/[^/]+/?$", re.IGNORECASE),
    re.compile(r"https?://(?:www\.)?[^/]+/(?:topics|topic|tags|tag)/[^/]+/?$", re.IGNORECASE),
]

MIN_KEY_SOURCE_URLS = 2
MIN_CONCRETE_SOURCES = 3


def check_paths(paths: list[str], expect_dir: bool) -> list[str]:
    missing: list[str] = []
    for relative_path in paths:
        full_path = ROOT / relative_path
        exists = full_path.is_dir() if expect_dir else full_path.is_file()
        if exists:
            print(f"PASS  {relative_path}")
        else:
            print(f"FAIL  {relative_path}")
            missing.append(relative_path)
    return missing


def load_json(relative_path: str) -> tuple[dict | None, str | None]:
    full_path = ROOT / relative_path
    try:
        return json.loads(full_path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"Missing file: {relative_path}"
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON in {relative_path}: {exc}"


def load_text(relative_path: str) -> tuple[str | None, str | None]:
    full_path = ROOT / relative_path
    try:
        return full_path.read_text(encoding="utf-8"), None
    except FileNotFoundError:
        return None, f"Missing file: {relative_path}"


def nonempty_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def optional_active_run_field(field_name: str) -> str | None:
    text, load_error = load_text("ACTIVE_RUN.md")
    if load_error:
        return None
    assert text is not None

    pattern = re.compile(rf"^-\s*{re.escape(field_name)}:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip().strip("`")
    if value.lower() in OPTIONAL_EMPTY_VALUES:
        return None
    return value


def checkpoint_label() -> str:
    return optional_active_run_field("checkpoint label") or "Checkpoint 1"


def http_link_count(text: str) -> int:
    return len(re.findall(r"https?://", text, re.IGNORECASE))


def resolve_repo_relative_path(base_relative_path: str, referenced_path: str) -> str | None:
    raw_value = str(referenced_path).strip()
    if not raw_value:
        return None

    referenced = Path(raw_value)
    if referenced.is_absolute():
        try:
            return referenced.relative_to(ROOT).as_posix()
        except ValueError:
            return referenced.as_posix()

    root_candidate = ROOT / referenced
    if root_candidate.exists():
        return root_candidate.relative_to(ROOT).as_posix()

    base_candidate = (ROOT / base_relative_path).parent / referenced
    return base_candidate.relative_to(ROOT).as_posix()


def referenced_file_exists(base_relative_path: str, referenced_path: str) -> bool:
    normalized = resolve_repo_relative_path(base_relative_path, referenced_path)
    if not normalized:
        return False
    return (ROOT / normalized).is_file()


def is_weak_supporting_source(url: str) -> bool:
    stripped = url.strip()
    return any(pattern.fullmatch(stripped) for pattern in WEAK_SUPPORTING_SOURCE_PATTERNS)


def find_forbidden_matches(text: str) -> list[str]:
    matches: list[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            matches.append(pattern.pattern)
    return matches


def heading_set(text: str) -> set[str]:
    return {line.strip().lower() for line in text.splitlines() if line.strip().startswith("##")}


def parse_boundary_fields(text: str) -> tuple[str, str]:
    boundary_result = ""
    exception_note = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if lower.startswith("- boundary result:"):
            boundary_result = line.split(":", 1)[1].strip()
        if lower.startswith("- exception note:"):
            exception_note = line.split(":", 1)[1].strip()
    return boundary_result, exception_note


def parse_markdown_bullets(text: str) -> dict[str, str]:
    bullets: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        bullets[key.strip().lower()] = value.strip()
    return bullets


def count_candidate_sections(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip().startswith("## Candidate:"))


def validate_run_index(relative_path: str) -> list[str]:
    errors = validate_markdown(relative_path, REQUIRED_RUN_INDEX_HEADINGS)
    text, load_error = load_text(relative_path)
    if load_error:
        return [load_error]
    assert text is not None

    if http_link_count(text) < MIN_KEY_SOURCE_URLS:
        errors.append(
            f"{relative_path} must surface at least {MIN_KEY_SOURCE_URLS} real source URLs for fast inspection."
        )

    bullets = parse_markdown_bullets(text)
    missing_fields = sorted(field for field in RUN_INDEX_REQUIRED_FIELDS if not bullets.get(field))
    if missing_fields:
        errors.append(f"{relative_path} is missing populated run-index fields: {', '.join(missing_fields)}")

    placeholder_fields: list[str] = []
    for field in RUN_INDEX_REQUIRED_FIELDS:
        value = bullets.get(field, "")
        lowered = value.lower()
        if any(snippet in lowered for snippet in RUN_INDEX_PLACEHOLDER_SNIPPETS):
            placeholder_fields.append(field)
    if placeholder_fields:
        errors.append(
            f"{relative_path} still contains placeholder run-index values for: {', '.join(sorted(placeholder_fields))}"
        )
    return errors


def validate_candidate_links(relative_path: str) -> list[str]:
    errors = validate_markdown(relative_path)
    text, load_error = load_text(relative_path)
    if load_error:
        return [load_error]
    assert text is not None

    sections = re.split(r"(?m)^## Candidate:\s*", text)
    candidate_sections = sections[1:]
    if not candidate_sections:
        errors.append(f"{relative_path} must contain at least one `## Candidate:` section.")
        return errors

    for index, section in enumerate(candidate_sections, start=1):
        bullets = parse_markdown_bullets(section)
        missing = sorted(field for field in CANDIDATE_LINK_REQUIRED_BULLETS if not bullets.get(field))
        if missing:
            errors.append(f"{relative_path} candidate #{index} is missing fields: {', '.join(missing)}")
    return errors


def validate_source_note(relative_path: str, expected_url: str) -> list[str]:
    errors = validate_markdown(relative_path)
    text, load_error = load_text(relative_path)
    if load_error:
        return [load_error]
    assert text is not None

    lowered = text.lower()
    if "## url" not in lowered:
        errors.append(f"{relative_path} must include a visible URL section near the top.")
    if expected_url and expected_url not in text:
        errors.append(f"{relative_path} must repeat the manifest URL exactly so reviewers can inspect the source directly.")
    if http_link_count(text) == 0:
        errors.append(f"{relative_path} must contain at least one real URL.")
    if "## direct evidence excerpt" not in lowered and "## key insights" not in lowered:
        errors.append(f"{relative_path} must capture a direct evidence excerpt or a key-insights section.")
    return errors


def exception_is_documented(run_index_text: str) -> bool:
    boundary_result, exception_note = parse_boundary_fields(run_index_text)
    if boundary_result.lower() != "exception":
        return False
    normalized = exception_note.strip().lower()
    return normalized not in {"", "none", "n/a", "na"}


def validate_markdown(relative_path: str, required_headings: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    text, load_error = load_text(relative_path)
    if load_error:
        return [load_error]
    assert text is not None

    relative_key = relative_path.split("artifacts/runs/")[-1]
    min_lines = MIN_NONEMPTY_LINES.get(relative_key, MIN_NONEMPTY_LINES.get(Path(relative_path).name, 0))
    if min_lines and nonempty_line_count(text) < min_lines:
        errors.append(f"{relative_path} looks too thin ({nonempty_line_count(text)} non-empty lines).")

    if LAUNCH_SCAFFOLD_MARKER in text.lower():
        errors.append(
            f"{relative_path} is still a launch scaffold. Replace the scaffold text with completed run content before the completion check."
        )

    matches = find_forbidden_matches(text)
    if matches:
        errors.append(f"{relative_path} contains unresolved placeholder/template text: {', '.join(matches)}")

    if required_headings:
        present = heading_set(text)
        missing = sorted(required_headings - present)
        if missing:
            errors.append(f"{relative_path} is missing required sections: {', '.join(missing)}")

    return errors


def validate_active_run() -> list[str]:
    errors: list[str] = []
    text, load_error = load_text("ACTIVE_RUN.md")
    if load_error:
        return [load_error]
    assert text is not None

    missing_fields = [field for field in REQUIRED_ACTIVE_RUN_FIELDS if field not in text.lower()]
    if missing_fields:
        errors.append(f"ACTIVE_RUN.md is missing required fields: {', '.join(missing_fields)}")
    return errors


def validate_research_manifest(relative_path: str) -> list[str]:
    errors: list[str] = []
    data, load_error = load_json(relative_path)
    if load_error:
        return [load_error]
    assert data is not None

    if str(data.get("population_status", "")).strip().lower() == LAUNCH_SCAFFOLD_MARKER:
        errors.append(
            f"{relative_path} is still marked as a launch scaffold. Save real source entries and remove the scaffold status before the completion check."
        )

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"{relative_path} must contain a non-empty 'sources' list.")
        return errors

    weak_supporting_sources = 0
    concrete_sources = 0

    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            errors.append(f"{relative_path} source #{index} is not an object.")
            continue
        missing = sorted(field for field in RESEARCH_MANIFEST_FIELDS if not source.get(field))
        if missing:
            errors.append(f"{relative_path} source #{index} is missing fields: {', '.join(missing)}")
            continue

        url = str(source.get("url", "")).strip()
        if not re.fullmatch(r"https?://.+", url, re.IGNORECASE):
            errors.append(f"{relative_path} source #{index} must use a real http(s) URL.")
        elif is_weak_supporting_source(url):
            weak_supporting_sources += 1
        else:
            concrete_sources += 1

        for field_name in ["raw_path", "normalized_path", "note_path"]:
            referenced_path = str(source.get(field_name, "")).strip()
            if not referenced_file_exists(relative_path, referenced_path):
                errors.append(f"{relative_path} source #{index} references a missing file in {field_name}: {source.get(field_name)}")

        note_path = resolve_repo_relative_path(relative_path, str(source.get("note_path", "")).strip())
        if note_path:
            errors.extend(validate_source_note(note_path, url))

    if len(sources) >= 6 and concrete_sources < MIN_CONCRETE_SOURCES:
        errors.append(
            f"{relative_path} has only {concrete_sources} concrete sources. At least {MIN_CONCRETE_SOURCES} should be complaint, workaround, review, issue, or practitioner evidence rather than broad supporting pages."
        )
    if weak_supporting_sources > max(2, len(sources) // 2):
        errors.append(
            f"{relative_path} relies too heavily on broad supporting pages ({weak_supporting_sources} of {len(sources)} sources). Use them as context, not as the majority of core evidence."
        )
    return errors


def validate_artifact_manifest(relative_path: str, run_id: str) -> list[str]:
    errors: list[str] = []
    data, load_error = load_json(relative_path)
    if load_error:
        return [load_error]
    assert data is not None

    if str(data.get("population_status", "")).strip().lower() == LAUNCH_SCAFFOLD_MARKER:
        errors.append(
            f"{relative_path} is still marked as a launch scaffold. Add completed artifact entries and remove the scaffold status before the completion check."
        )

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append(f"{relative_path} must contain a non-empty 'artifacts' list.")
        return errors

    paths: set[str] = set()
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict):
            errors.append(f"{relative_path} artifact #{index} is not an object.")
            continue
        missing = sorted(field for field in ARTIFACT_MANIFEST_FIELDS if artifact.get(field) in (None, "", []))
        if missing:
            errors.append(f"{relative_path} artifact #{index} is missing fields: {', '.join(missing)}")
            continue
        normalized_path = resolve_repo_relative_path(relative_path, str(artifact["path"]))
        if not normalized_path:
            errors.append(f"{relative_path} artifact #{index} has an invalid path field: {artifact.get('path')}")
            continue
        paths.add(normalized_path)
        if not (ROOT / normalized_path).is_file():
            errors.append(f"{relative_path} artifact #{index} points to a missing file: {artifact.get('path')}")

    expected_paths = {
        f"artifacts/runs/{run_id}/run-index.md",
        f"artifacts/runs/{run_id}/review-package/research.md",
        f"artifacts/runs/{run_id}/review-package/opportunity-scorecard.md",
        f"artifacts/runs/{run_id}/review-package/candidate-review.md",
        f"artifacts/runs/{run_id}/review-package/validation.md",
        f"artifacts/runs/{run_id}/reports/discovery-summary.md",
    }

    missing_paths = sorted(expected_paths - paths)
    if missing_paths:
        errors.append(f"{relative_path} is missing manifest entries for: {', '.join(missing_paths)}")
    return errors


def validate_run(run_id: str) -> int:
    print(f"Checking discovery run package completeness for {run_id}.\n")
    print("This validator is for the end of the discovery run, after the manifests and reviewer package are fully populated.\n")

    required_run_files = [
        f"research-corpus/runs/{run_id}/manifest.json",
        f"research-corpus/runs/{run_id}/candidate-links.md",
        f"artifacts/runs/{run_id}/manifest.json",
        f"artifacts/runs/{run_id}/run-index.md",
        f"artifacts/runs/{run_id}/review-package/research.md",
        f"artifacts/runs/{run_id}/review-package/opportunity-scorecard.md",
        f"artifacts/runs/{run_id}/review-package/candidate-review.md",
        f"artifacts/runs/{run_id}/review-package/validation.md",
        f"artifacts/runs/{run_id}/reports/discovery-summary.md",
    ]
    missing_files = check_paths(required_run_files, expect_dir=False)
    print()

    if missing_files:
        print(f"NOT READY  Missing {len(missing_files)} required run artifact(s).")
        return 1

    errors: list[str] = []
    errors.extend(validate_research_manifest(f"research-corpus/runs/{run_id}/manifest.json"))
    errors.extend(validate_artifact_manifest(f"artifacts/runs/{run_id}/manifest.json", run_id))
    errors.extend(validate_run_index(f"artifacts/runs/{run_id}/run-index.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/review-package/research.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/review-package/opportunity-scorecard.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/review-package/candidate-review.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/review-package/validation.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/reports/discovery-summary.md"))
    errors.extend(validate_candidate_links(f"research-corpus/runs/{run_id}/candidate-links.md"))

    research_manifest, _ = load_json(f"research-corpus/runs/{run_id}/manifest.json")
    artifact_manifest, _ = load_json(f"artifacts/runs/{run_id}/manifest.json")
    run_index_text, _ = load_text(f"artifacts/runs/{run_id}/run-index.md")
    candidate_links_text, _ = load_text(f"research-corpus/runs/{run_id}/candidate-links.md")
    if research_manifest is None or artifact_manifest is None or run_index_text is None or candidate_links_text is None:
        print()
        print(f"NOT READY  Found {len(errors)} completeness issue(s) in run package {run_id}.")
        print("NEXT  Fix the incomplete artifacts listed below, update the manifests and run index, then rerun the completion check.")
        for error in errors:
            print(f"- {error}")
        return 1

    summary_text, _ = load_text(f"artifacts/runs/{run_id}/reports/discovery-summary.md")
    if summary_text is None:
        errors.append(f"artifacts/runs/{run_id}/reports/discovery-summary.md could not be loaded.")
    elif http_link_count(summary_text) < MIN_KEY_SOURCE_URLS:
        errors.append(
            f"artifacts/runs/{run_id}/reports/discovery-summary.md must surface at least {MIN_KEY_SOURCE_URLS} real source URLs for fast reviewer inspection."
        )

    documented_exception = exception_is_documented(run_index_text)
    sources = research_manifest.get("sources", [])
    source_count = len(sources)
    source_types = {source.get("source_type") for source in sources if isinstance(source, dict) and source.get("source_type")}
    candidate_count = count_candidate_sections(candidate_links_text)
    launch_only = any(
        marker == LAUNCH_SCAFFOLD_MARKER
        for marker in [
            str(research_manifest.get("population_status", "")).strip().lower(),
            str(artifact_manifest.get("population_status", "")).strip().lower(),
        ]
    ) or LAUNCH_SCAFFOLD_MARKER in run_index_text.lower() or LAUNCH_SCAFFOLD_MARKER in candidate_links_text.lower()

    boundary_errors: list[str] = []
    if source_count < 6 or source_count > 12:
        boundary_errors.append(f"Source count {source_count} is outside the 6-12 target.")
    if len(source_types) < 3:
        boundary_errors.append(f"Source type count {len(source_types)} is below the 3-type target.")
    if candidate_count == 0:
        boundary_errors.append("Candidate map does not contain any candidates.")
    elif candidate_count > 5:
        boundary_errors.append(f"Candidate count {candidate_count} exceeds the limit of 5.")

    if boundary_errors:
        if documented_exception:
            for error in boundary_errors:
                print(f"WARN  {error} Boundary exception documented in run index.")
        else:
            errors.extend(boundary_errors)

    print(f"INFO  source_count={source_count}")
    print(f"INFO  source_type_count={len(source_types)}")
    print(f"INFO  candidate_count={candidate_count}")

    if not errors:
        print()
        print(f"READY  Run package {run_id} is complete at the current discovery milestone and ready for continuation or async inspection.")
        return 0

    print()
    if launch_only and source_count == 0 and candidate_count == 0:
        print(f"NOT READY  Run package {run_id} has only been launched so far; the research and review package have not been populated yet.")
        print("NEXT  Save real sources, fill both manifests, complete the reviewer artifacts, then rerun this completion check last.")
    else:
        print(f"NOT READY  Found {len(errors)} completeness issue(s) in run package {run_id}.")
        print("NEXT  Fix the incomplete artifacts listed below, update the manifests and run index, then rerun the completion check.")
    for error in errors:
        print(f"- {error}")
    return 1


def validate_repo() -> int:
    print("Checking repo bootstrap readiness for autonomous runs.\n")
    missing_files = check_paths(REQUIRED_FILES, expect_dir=False)
    print()
    missing_dirs = check_paths(REQUIRED_DIRS, expect_dir=True)

    errors: list[str] = []
    errors.extend(validate_markdown("START_HERE.md", REQUIRED_START_HEADINGS))
    errors.extend(validate_markdown("ACTIVE_RUN.md", REQUIRED_ACTIVE_RUN_HEADINGS))
    errors.extend(validate_active_run())

    total_missing = len(missing_files) + len(missing_dirs)
    print()
    if total_missing == 0 and not errors:
        print("READY  Repo contains the required bootstrap files and directories.")
        return 0

    problem_count = total_missing + len(errors)
    print(f"NOT READY  Found {problem_count} bootstrap issue(s).")
    if missing_files:
        print("Missing files:")
        for path in missing_files:
            print(f"- {path}")
    if missing_dirs:
        print("Missing directories:")
        for path in missing_dirs:
            print(f"- {path}")
    for error in errors:
        print(f"- {error}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repo startup readiness or the final completeness of a discovery run package.")
    parser.add_argument("--run-id", help="Validate the completed discovery handoff package for the given run ID.")
    args = parser.parse_args()

    if args.run_id:
        return validate_run(args.run_id)
    return validate_repo()


if __name__ == "__main__":
    sys.exit(main())