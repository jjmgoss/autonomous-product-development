from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "FIRST_RUN_PROMPT.md",
    "FIRST_RUN_MODE.md",
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
    "docs/first-run-readiness-note.md",
    "skills/product/research-skill.md",
    "skills/product/first-run-discovery-skill.md",
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
    "FIRST_RUN_SETUP_SUMMARY.md",
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
    "## reviewer route",
    "## recommendation snapshot",
    "## evidence that could overturn the ranking",
    "## next step requested at gate 1",
}

MIN_NONEMPTY_LINES = {
    "run-index.md": 12,
    "review-package/research.md": 25,
    "review-package/opportunity-scorecard.md": 18,
    "review-package/candidate-review.md": 18,
    "review-package/validation.md": 18,
    "reports/discovery-summary.md": 16,
    "candidate-links.md": 10,
}


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

    min_lines = MIN_NONEMPTY_LINES.get(relative_path.split("artifacts/runs/")[-1], MIN_NONEMPTY_LINES.get(Path(relative_path).name, 0))
    if min_lines and nonempty_line_count(text) < min_lines:
        errors.append(f"{relative_path} looks too thin ({nonempty_line_count(text)} non-empty lines).")

    matches = find_forbidden_matches(text)
    if matches:
        errors.append(f"{relative_path} contains unresolved placeholder/template text: {', '.join(matches)}")

    if required_headings:
        present = heading_set(text)
        missing = sorted(required_headings - present)
        if missing:
            errors.append(f"{relative_path} is missing required sections: {', '.join(missing)}")

    return errors


def validate_research_manifest(relative_path: str) -> list[str]:
    errors: list[str] = []
    data, load_error = load_json(relative_path)
    if load_error:
        return [load_error]
    assert data is not None

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        return [f"{relative_path} must contain a non-empty 'sources' list."]

    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            errors.append(f"{relative_path} source #{index} is not an object.")
            continue
        missing = sorted(field for field in RESEARCH_MANIFEST_FIELDS if not source.get(field))
        if missing:
            errors.append(f"{relative_path} source #{index} is missing fields: {', '.join(missing)}")
    return errors


def validate_artifact_manifest(relative_path: str, run_id: str) -> list[str]:
    errors: list[str] = []
    data, load_error = load_json(relative_path)
    if load_error:
        return [load_error]
    assert data is not None

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return [f"{relative_path} must contain a non-empty 'artifacts' list."]

    paths: set[str] = set()
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict):
            errors.append(f"{relative_path} artifact #{index} is not an object.")
            continue
        missing = sorted(field for field in ARTIFACT_MANIFEST_FIELDS if artifact.get(field) in (None, "", []))
        if missing:
            errors.append(f"{relative_path} artifact #{index} is missing fields: {', '.join(missing)}")
            continue
        paths.add(str(artifact["path"]))

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
    print(f"Checking first-run package completeness for {run_id}.\n")

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
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/run-index.md", REQUIRED_RUN_INDEX_HEADINGS))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/review-package/research.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/review-package/opportunity-scorecard.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/review-package/candidate-review.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/review-package/validation.md"))
    errors.extend(validate_markdown(f"artifacts/runs/{run_id}/reports/discovery-summary.md"))
    errors.extend(validate_markdown(f"research-corpus/runs/{run_id}/candidate-links.md"))

    research_manifest, _ = load_json(f"research-corpus/runs/{run_id}/manifest.json")
    run_index_text, _ = load_text(f"artifacts/runs/{run_id}/run-index.md")
    candidate_links_text, _ = load_text(f"research-corpus/runs/{run_id}/candidate-links.md")
    assert research_manifest is not None and run_index_text is not None and candidate_links_text is not None

    documented_exception = exception_is_documented(run_index_text)
    sources = research_manifest.get("sources", [])
    source_count = len(sources)
    source_types = {source.get("source_type") for source in sources if isinstance(source, dict) and source.get("source_type")}
    candidate_count = sum(1 for line in candidate_links_text.splitlines() if line.strip().startswith("## Candidate:"))

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
        print(f"READY  Run package {run_id} is complete enough for Gate 1 review.")
        return 0

    print()
    print(f"NOT READY  Found {len(errors)} completeness issue(s) in run package {run_id}.")
    for error in errors:
        print(f"- {error}")
    return 1


def validate_repo() -> int:
    print("Checking first-run readiness for discovery-first execution.\n")
    missing_files = check_paths(REQUIRED_FILES, expect_dir=False)
    print()
    missing_dirs = check_paths(REQUIRED_DIRS, expect_dir=True)

    total_missing = len(missing_files) + len(missing_dirs)
    print()
    if total_missing == 0:
        print("READY  Repo contains the required first-run discovery files and directories.")
        return 0

    print(f"NOT READY  Missing {total_missing} required path(s).")
    if missing_files:
        print("Missing files:")
        for path in missing_files:
            print(f"- {path}")
    if missing_dirs:
        print("Missing directories:")
        for path in missing_dirs:
            print(f"- {path}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate first-run framework readiness or a completed run package.")
    parser.add_argument("--run-id", help="Validate the completed Gate 1 package for the given run ID.")
    args = parser.parse_args()

    if args.run_id:
        return validate_run(args.run_id)
    return validate_repo()


if __name__ == "__main__":
    sys.exit(main())