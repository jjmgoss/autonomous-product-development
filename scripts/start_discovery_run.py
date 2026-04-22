from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent


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

LAUNCH_SCAFFOLD_MARKER = "launch scaffold"
SOURCE_TARGET_MIN = 6
SOURCE_TARGET_MAX = 12
SOURCE_TYPE_TARGET_MIN = 3

RESEARCH_MANIFEST_FIELDS = [
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
]

ARTIFACT_MANIFEST_FIELDS = [
    "id",
    "artifact_type",
    "path",
    "created_at",
    "created_by",
    "inputs",
    "purpose",
    "notes",
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
    return {
        "run_id": run_id,
        "population_status": LAUNCH_SCAFFOLD_MARKER,
        "completion_note": "Replace this scaffold metadata with saved source entries before running the completion check.",
        "source_requirements": {
            "minimum_sources": SOURCE_TARGET_MIN,
            "maximum_sources": SOURCE_TARGET_MAX,
            "minimum_source_types": SOURCE_TYPE_TARGET_MIN,
            "required_fields": RESEARCH_MANIFEST_FIELDS,
        },
        "sources": [],
    }


def artifact_manifest_stub(run_id: str) -> dict:
    return {
        "run_id": run_id,
        "population_status": LAUNCH_SCAFFOLD_MARKER,
        "completion_note": "Replace this scaffold metadata with completed artifact entries before running the completion check.",
        "required_artifact_paths": [output.format(run_id=run_id) for output in DISCOVERY_OUTPUTS[3:]],
        "required_fields": ARTIFACT_MANIFEST_FIELDS,
        "artifacts": [],
    }


def candidate_links_stub(run_id: str) -> str:
    return dedent(
        f"""\
        # Candidate Evidence Map

        Launch scaffold: replace this note with completed candidate-to-evidence links before the completion check.

        Run ID: {run_id}

        ## How To Finish This File

        - Add one `## Candidate:` section per serious candidate that survived research.
        - Record both supporting and weakening evidence IDs for each serious candidate.
        - Keep only the bounded candidate set that was actually compared.
        - Remove this launch-scaffold note once the candidate map is complete.

        ### Candidate Section Template

        - short thesis:
        - status in ranking:
        - supporting evidence IDs:
        - weakening evidence IDs:
        - substitute pressure notes:
        - open questions that could change ranking:
        """
    )


def run_index_stub(run_id: str) -> str:
    return dedent(
        f"""\
        # Run Index

        Launch scaffold: this run has been initialized, but the research and reviewer package are not complete yet.

        ## Run Context

        - run ID: {run_id}
        - theme: replace with the current theme in one sentence
        - corpus path: research-corpus/runs/{run_id}/
        - artifact path: artifacts/runs/{run_id}/

        ## Boundary Status

        - source target: {SOURCE_TARGET_MIN}-{SOURCE_TARGET_MAX} meaningful sources
        - actual source count: 0
        - actual source-type count: 0
        - candidate target: at most 5 serious candidates, score at most top 3 in detail
        - actual candidate count: 0
        - boundary result: in progress
        - exception note: none

        ## Execution Checklist

        - [ ] save meaningful sources under the run corpus and record them in `manifest.json`
        - [ ] update `candidate-links.md` with serious candidates plus supporting and weakening evidence IDs
        - [ ] write the review-package artifacts with evidence-backed rankings and recommendation
        - [ ] update `artifacts/runs/{run_id}/manifest.json` with completed artifact entries
        - [ ] replace this launch scaffold note with reviewer-facing completion status
        - [ ] run `python scripts/check_repo_readiness.py --run-id {run_id}` only after the package is complete

        ## Reviewer Route

        1. Read `reports/discovery-summary.md`.
        2. Read `review-package/candidate-review.md`.
        3. Read `review-package/validation.md`.
        4. Read `review-package/opportunity-scorecard.md`.
        5. Inspect `research-corpus/runs/{run_id}/manifest.json` and `candidate-links.md`.

        ## Recommendation Snapshot

        - recommended outcome: in progress
        - leading candidate: in progress
        - runner-up: in progress
        - why the leader won: replace with evidence-backed summary
        - why it may still fail: replace with disconfirming evidence and open risks

        ## Evidence That Could Overturn The Ranking

        - replace with the evidence IDs or missing evidence that could change the current call

        ## Next Step Requested At Gate 1

        - requested human decision: do not fill until the package is complete
        - stop status: launch complete, research and package completion still in progress
        """
    )


def research_review_stub(run_id: str) -> str:
    return dedent(
        f"""\
        # Research

        Launch scaffold: replace this note with completed research findings before the completion check.

        Run ID: {run_id}

        ## Boundary

        - user and workflow focus:
        - sources captured so far: 0
        - source types captured so far: 0

        ## Repeated Pain Patterns

        Explain the strongest recurring workflow pain with evidence IDs.

        ## Current Workarounds And Substitutes

        Explain what users do today and why that is insufficient or good enough.

        ## Candidate Directions Emerging From Research

        List only serious candidate wedges and cite the evidence IDs that support or weaken them.

        ## Research Gaps That Still Matter

        Explain what evidence is still missing and why it could change the ranking.
        """
    )


def opportunity_scorecard_stub(run_id: str) -> str:
    return dedent(
        f"""\
        # Opportunity Scorecard

        Launch scaffold: replace this note with completed candidate scoring before the completion check.

        Run ID: {run_id}

        ## Scoring Rules

        Score at most the top 3 candidates in detail. Cite saved evidence IDs in each judgment.

        ## Candidate 1

        - user and workflow:
        - pain severity:
        - substitute pressure:
        - monetization angle:
        - agent-operability judgment:
        - strongest supporting evidence IDs:
        - strongest weakening evidence IDs:
        - current rank:

        ## Candidate 2

        Fill this section only if a second candidate remains serious.

        ## Candidate 3

        Fill this section only if a third candidate remains serious.
        """
    )


def candidate_review_stub(run_id: str) -> str:
    return dedent(
        f"""\
        # Candidate Review

        Launch scaffold: replace this note with the completed comparison before the completion check.

        Run ID: {run_id}

        ## Shortlist

        Name the serious candidates that survived the research pass.

        ## Why The Leading Candidate Leads

        Explain the ranking with evidence IDs, monetization logic, and substitute pressure.

        ## Why The Runner-Up Lost

        Explain why the next-best option did not win.

        ## Why The Leader May Still Fail

        Document the strongest reasons not to build it yet.

        ## Recommendation

        Choose one outcome and justify it with evidence:

        - prototype the leading candidate now
        - continue validating the top 2 candidates
        - no current candidate is strong enough
        """
    )


def validation_stub(run_id: str) -> str:
    return dedent(
        f"""\
        # Validation

        Launch scaffold: replace this note with completed validation reasoning before the completion check.

        Run ID: {run_id}

        ## What Would Need To Be True

        Explain the core assumptions that must hold for the current recommendation to be good.

        ## What Evidence Supports The Recommendation

        Cite the strongest evidence IDs and why they matter.

        ## What Evidence Pushes Back

        Cite the strongest weakening evidence IDs, substitute pressure, and operational concerns.

        ## What Would Change The Decision

        Explain the disconfirming evidence that would overturn the current ranking.

        ## Gate 1 Request

        State what human decision is being requested once the package is complete.
        """
    )


def discovery_summary_stub(run_id: str) -> str:
    return dedent(
        f"""\
        # Discovery Summary

        Launch scaffold: replace this note with a completed reviewer summary before the completion check.

        Run ID: {run_id}

        ## Run Context

        - theme:
        - source count:
        - source types used:
        - candidate count:
        - boundary exceptions, if any:

        ## Top Recommendation

        - recommended outcome:
        - leading candidate:
        - why it leads:
        - what may still kill it:

        ## Ranked Shortlist

        Summarize the strongest candidates and the evidence that separates them.

        ## What Would Change The Call

        Explain which missing evidence could materially change the recommendation.

        ## Stop Point

        State that the run stopped at Gate 1 after the package was completed.
        """
    )


def write_scaffold(path: Path, contents: str) -> None:
    path.write_text(contents.rstrip() + "\n", encoding="utf-8")


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
    write_scaffold(research_root / "candidate-links.md", candidate_links_stub(run_id))
    (artifact_root / "manifest.json").write_text(
        json.dumps(artifact_manifest_stub(run_id), indent=2) + "\n",
        encoding="utf-8",
    )
    write_scaffold(artifact_root / "run-index.md", run_index_stub(run_id))
    write_scaffold(artifact_root / "review-package" / "research.md", research_review_stub(run_id))
    write_scaffold(artifact_root / "review-package" / "opportunity-scorecard.md", opportunity_scorecard_stub(run_id))
    write_scaffold(artifact_root / "review-package" / "candidate-review.md", candidate_review_stub(run_id))
    write_scaffold(artifact_root / "review-package" / "validation.md", validation_stub(run_id))
    write_scaffold(artifact_root / "reports" / "discovery-summary.md", discovery_summary_stub(run_id))

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
    print("NEXT_STEP  Launch complete. Do the research work now, fully populate the manifests and reviewer artifacts, then run the completion check last.")
    print("DO_NOT_STOP  A launched run with scaffold files is not a completed Gate 1 package.")
    print("REQUIRED_OUTPUTS")
    for output in DISCOVERY_OUTPUTS:
        print(f"- {output.format(run_id=run_id)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())