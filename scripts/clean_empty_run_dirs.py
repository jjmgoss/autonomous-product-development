from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESEARCH_RUNS_ROOT = ROOT / "research-corpus" / "runs"
ARTIFACT_RUNS_ROOT = ROOT / "artifacts" / "runs"
PROTECTED_ROOTS = {RESEARCH_RUNS_ROOT.resolve(), ARTIFACT_RUNS_ROOT.resolve()}


def directory_is_empty(path: Path) -> bool:
    return not any(path.iterdir())


def remove_empty_subdirectories(root: Path, dry_run: bool) -> list[Path]:
    removed: list[Path] = []
    directories = sorted((path for path in root.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True)

    for path in directories:
        if path.resolve() in PROTECTED_ROOTS:
            continue
        if not directory_is_empty(path):
            continue
        removed.append(path)
        if dry_run:
            print(f"WOULD_REMOVE  {path.relative_to(ROOT).as_posix()}")
        else:
            path.rmdir()
            print(f"REMOVED  {path.relative_to(ROOT).as_posix()}")

    return removed


def top_level_run_dirs(root: Path) -> dict[str, Path]:
    if not root.exists():
        return {}
    return {path.name: path for path in root.iterdir() if path.is_dir()}


def suspicious_run_notes() -> list[str]:
    notes: list[str] = []
    research_runs = top_level_run_dirs(RESEARCH_RUNS_ROOT)
    artifact_runs = top_level_run_dirs(ARTIFACT_RUNS_ROOT)
    run_ids = sorted(set(research_runs) | set(artifact_runs))

    for run_id in run_ids:
        research_path = research_runs.get(run_id)
        artifact_path = artifact_runs.get(run_id)

        if research_path and any(research_path.iterdir()) and not artifact_path:
            notes.append(
                f"SUSPICIOUS  research-corpus/runs/{run_id} is non-empty but has no matching artifacts/runs/{run_id} directory."
            )
        if artifact_path and any(artifact_path.iterdir()) and not research_path:
            notes.append(
                f"SUSPICIOUS  artifacts/runs/{run_id} is non-empty but has no matching research-corpus/runs/{run_id} directory."
            )
        if research_path and any(research_path.iterdir()) and not (research_path / "manifest.json").exists():
            notes.append(f"SUSPICIOUS  research-corpus/runs/{run_id} is non-empty but missing manifest.json.")
        if artifact_path and any(artifact_path.iterdir()) and not (artifact_path / "manifest.json").exists():
            notes.append(f"SUSPICIOUS  artifacts/runs/{run_id} is non-empty but missing manifest.json.")
        if artifact_path and any(artifact_path.iterdir()) and not (artifact_path / "run-index.md").exists():
            notes.append(f"SUSPICIOUS  artifacts/runs/{run_id} is non-empty but missing run-index.md.")

    return notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove only truly empty run subdirectories and report suspicious non-empty partial run folders."
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what would be removed without deleting it.")
    args = parser.parse_args()

    print("Scanning run directories for empty leftovers.\n")

    removed = []
    for root in [RESEARCH_RUNS_ROOT, ARTIFACT_RUNS_ROOT]:
        removed.extend(remove_empty_subdirectories(root, dry_run=args.dry_run))

    if not removed:
        print("INFO  No empty run subdirectories found.")

    notes = suspicious_run_notes()
    if notes:
        print()
        for note in notes:
            print(note)
    else:
        print()
        print("INFO  No suspicious partial non-empty run directories found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())