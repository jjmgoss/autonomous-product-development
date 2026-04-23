from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD_ROOT = ROOT / "artifacts" / "shared" / "prototype-scaffold"
DEFAULT_TARGET_ROOT = ROOT / "artifacts" / "projects"

TOKENS = {
    "__PROJECT_TITLE__": "",
    "__PROJECT_SLUG__": "",
}


def copy_with_replacements(source: Path, destination: Path, replacements: dict[str, str]) -> None:
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            copy_with_replacements(child, destination / child.name, replacements)
        return

    text_extensions = {".md", ".txt", ".py", ".json"}
    if source.suffix in text_extensions:
        text = source.read_text(encoding="utf-8")
        for token, value in replacements.items():
            text = text.replace(token, value)
        destination.write_text(text, encoding="utf-8")
    else:
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy the shared prototype scaffold into artifacts/projects/<project-slug>/.")
    parser.add_argument("project_slug", help="Target project slug under artifacts/projects/.")
    parser.add_argument("--title", help="Optional human-readable project title.")
    parser.add_argument("--target-root", help="Override the default target root.")
    args = parser.parse_args()

    if not SCAFFOLD_ROOT.is_dir():
        print(f"ERROR  Missing scaffold directory: {SCAFFOLD_ROOT}")
        return 1

    target_root = Path(args.target_root) if args.target_root else DEFAULT_TARGET_ROOT
    project_root = target_root / args.project_slug
    if project_root.exists():
        print(f"ERROR  Target already exists: {project_root}")
        return 1

    replacements = dict(TOKENS)
    replacements["__PROJECT_SLUG__"] = args.project_slug
    replacements["__PROJECT_TITLE__"] = args.title or args.project_slug.replace("-", " ").title()

    copy_with_replacements(SCAFFOLD_ROOT, project_root, replacements)
    print(f"READY  Prototype scaffold copied to {project_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())