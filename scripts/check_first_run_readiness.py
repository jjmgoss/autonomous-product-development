from __future__ import annotations

from pathlib import Path
import sys


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


def main() -> int:
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


if __name__ == "__main__":
    sys.exit(main())