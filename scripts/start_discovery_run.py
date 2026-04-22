from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ACTIVE_RUN_PATH = ROOT / "ACTIVE_RUN.md"
THEME_PATH = ROOT / "theme.md"

DISCOVERY_OUTPUTS = [
    "research-corpus/runs/{run_id}/manifest.json",
    "research-corpus/runs/{run_id}/candidate-links.md",
    "artifacts/runs/{run_id}/manifest.json",
    "artifacts/runs/{run_id}/run-index.md",
    "artifacts/runs/{run_id}/review-package/research.md",
    "artifacts/runs/{run_id}/review-package/opportunity-scorecard.md",
    "artifacts/runs/{run_id}/review-package/candidate-review.md",
    "artifacts/runs/{run_id}/review-package/validation.md",
    "artifacts/runs/{run_id}/reports/discovery-summary.md",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_active_run_field(field_name: str) -> str | None:
    text = read_text(ACTIVE_RUN_PATH)
    pattern = re.compile(rf"^-\s*{re.escape(field_name)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value.strip("`")


def slugify(value: str) -> str:
    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "run"


def infer_slug_from_theme() -> str:
    if not THEME_PATH.exists():
        return "theme"

    text = read_text(THEME_PATH)
    quote_match = re.search(r"^>\s*(.+)$", text, re.MULTILINE)
    if quote_match:
        tokens = re.findall(r"[a-z0-9]+", quote_match.group(1).lower())
    else:
        tokens = re.findall(r"[a-z0-9]+", text.lower())

    stopwords = {
        "a",
        "an",
        "and",
        "automation",
        "build",
        "developer",
        "development",
        "discover",
        "for",
        "in",
        "of",
        "opportunities",
        "product",
        "the",
        "to",
        "workflow",
    }
    meaningful = [token for token in tokens if token not in stopwords]
    selected = meaningful[:3] or tokens[:3] or ["theme"]
    return slugify("-".join(selected))


def choose_slug(explicit_slug: str | None) -> str:
    if explicit_slug:
        return slugify(explicit_slug)

    slug_hint = parse_active_run_field("run slug hint")
    if slug_hint:
        return slugify(slug_hint)

    return infer_slug_from_theme()


def run_exists(run_id: str) -> bool:
    research_path = ROOT / "research-corpus" / "runs" / run_id
    artifact_path = ROOT / "artifacts" / "runs" / run_id
    return research_path.exists() or artifact_path.exists()


def next_run_id(date_prefix: str, slug: str) -> str:
    counter = 1
    while True:
        run_id = f"{date_prefix}-{slug}-r{counter}"
        if not run_exists(run_id):
            return run_id
        counter += 1


def research_manifest_stub(run_id: str) -> dict:
    return {"run_id": run_id, "sources": []}


def artifact_manifest_stub(run_id: str) -> dict:
    return {"run_id": run_id, "artifacts": []}


def candidate_links_stub(run_id: str) -> str:
    return "\n".join(
        [
            "# Candidate Evidence Map",
            "",
            f"Run ID: {run_id}",
            "",
            "Add one `## Candidate:` section per serious candidate during the run.",
            "Link supporting and weakening evidence IDs before stopping.",
            "",
        ]
    )


def initialize_run(run_id: str) -> tuple[Path, Path]:
    research_root = ROOT / "research-corpus" / "runs" / run_id
    artifact_root = ROOT / "artifacts" / "runs" / run_id

    for path in [
        research_root / "raw",
        research_root / "normalized",
        research_root / "notes",
        artifact_root / "review-package",
        artifact_root / "reports",
        artifact_root / "evaluations",
        artifact_root / "exports",
    ]:
        path.mkdir(parents=True, exist_ok=False)

    (research_root / "manifest.json").write_text(
        json.dumps(research_manifest_stub(run_id), indent=2) + "\n",
        encoding="utf-8",
    )
    (research_root / "candidate-links.md").write_text(candidate_links_stub(run_id), encoding="utf-8")
    (artifact_root / "manifest.json").write_text(
        json.dumps(artifact_manifest_stub(run_id), indent=2) + "\n",
        encoding="utf-8",
    )

    return research_root, artifact_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a fresh discovery run with a collision-safe run ID.")
    parser.add_argument("--run-id", help="Explicit run ID to use. Fails if the run already exists.")
    parser.add_argument("--slug", help="Override the default theme slug hint.")
    parser.add_argument("--date", help="Override the YYYYMMDD date prefix.")
    args = parser.parse_args()

    date_prefix = args.date or datetime.now().strftime("%Y%m%d")
    if not re.fullmatch(r"\d{8}", date_prefix):
        print("ERROR  --date must use YYYYMMDD.")
        return 1

    if args.run_id:
        run_id = args.run_id.strip()
        if run_exists(run_id):
            print(f"ERROR  Run ID already exists: {run_id}")
            return 1
    else:
        slug = choose_slug(args.slug)
        run_id = next_run_id(date_prefix, slug)

    research_root, artifact_root = initialize_run(run_id)

    print(f"RUN_ID  {run_id}")
    print(f"CORPUS_ROOT  {research_root.relative_to(ROOT).as_posix()}")
    print(f"ARTIFACT_ROOT  {artifact_root.relative_to(ROOT).as_posix()}")
    print("READINESS_CHECK  python scripts/check_repo_readiness.py")
    print(f"COMPLETION_CHECK  python scripts/check_repo_readiness.py --run-id {run_id}")
    print("REQUIRED_OUTPUTS")
    for output in DISCOVERY_OUTPUTS:
        print(f"- {output.format(run_id=run_id)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())