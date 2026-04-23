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

THEME_SLUG_STOPWORDS = {
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
OPTIONAL_EMPTY_VALUES = {"", "none", "n/a", "na", "null"}

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


def optional_active_run_field(field_name: str) -> str | None:
    value = parse_active_run_field(field_name)
    if value is None:
        return None
    if value.strip().lower() in OPTIONAL_EMPTY_VALUES:
        return None
    return value


def slugify(value: str) -> str:
    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "run"


def extract_theme_summary() -> str:
    if not THEME_PATH.exists():
        return "theme"

    text = read_text(THEME_PATH)
    quote_match = re.search(r"^>\s*(.+)$", text, re.MULTILINE)
    if quote_match:
        return quote_match.group(1).strip()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return "theme"


def checkpoint_label() -> str:
    return optional_active_run_field("checkpoint label") or "Checkpoint 1"


def checkpoint_behavior() -> str:
    return optional_active_run_field("checkpoint behavior") or "continue unless blocked"


def infer_slug_from_theme() -> str:
    tokens = re.findall(r"[a-z0-9]+", extract_theme_summary().lower())
    meaningful = [token for token in tokens if token not in THEME_SLUG_STOPWORDS]
    selected = meaningful[:3] or tokens[:3] or ["theme"]
    return slugify("-".join(selected))


def choose_slug(explicit_slug: str | None) -> tuple[str, str | None]:
    if explicit_slug:
        return slugify(explicit_slug), None

    slug_override = optional_active_run_field("theme slug override") or optional_active_run_field("run slug override")
    if slug_override:
        return slugify(slug_override), None

    inferred_slug = infer_slug_from_theme()

    legacy_slug_hint = optional_active_run_field("run slug hint")
    if legacy_slug_hint:
        legacy_slug = slugify(legacy_slug_hint)
        if legacy_slug != inferred_slug:
            return inferred_slug, (
                f"Legacy run slug hint '{legacy_slug_hint}' does not match the current theme-derived slug '{inferred_slug}'. "
                "Using the theme-derived slug. Set 'theme slug override' in ACTIVE_RUN.md only when you intentionally need a different slug."
            )

    return inferred_slug, None


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
        - first buyer/user:
        - first wedge:
        - supporting evidence IDs:
        - weakening evidence IDs:
        - key supporting links:
        - substitute pressure notes:
        - why this is not a platform fantasy:
        - open questions that could change ranking:
        """
    )


def run_index_stub(run_id: str) -> str:
    theme_summary = extract_theme_summary()
    current_checkpoint = checkpoint_label()
    current_behavior = checkpoint_behavior()
    return dedent(
        f"""\
        # Run Index

        Launch scaffold: this run has been initialized, but the discovery package is not complete yet.

        ## Run Context

        - run ID: {run_id}
        - theme: {theme_summary}
        - corpus path: research-corpus/runs/{run_id}/
        - artifact path: artifacts/runs/{run_id}/
        - checkpoint label: {current_checkpoint}
        - checkpoint behavior: {current_behavior}

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
        - [ ] add key source links with evidence IDs and real URLs in this file
        - [ ] run `python scripts/check_repo_readiness.py --run-id {run_id}` only after the package is complete

        ## Key Source Links

        - add 3-5 high-signal evidence IDs with real URLs once sources are saved

        ## Reviewer Route

        1. Read `reports/discovery-summary.md`.
        2. Read `review-package/candidate-review.md`.
        3. Read `review-package/validation.md`.
        4. Read `review-package/opportunity-scorecard.md`.
        5. Inspect `research-corpus/runs/{run_id}/manifest.json` and `candidate-links.md`.

        ## Recommendation Snapshot

        - recommended outcome: in progress
        - leading candidate: in progress
        - first buyer/user: replace with the first user who gets clear value
        - first wedge: replace with the smallest sellable workflow slice
        - why this is not a platform fantasy: replace with the narrowness test that keeps the idea bounded
        - runner-up: in progress
        - why the leader won: replace with evidence-backed summary
        - why it may still fail: replace with disconfirming evidence and open risks

        ## Evidence That Could Overturn The Ranking

        - replace with the evidence IDs or missing evidence that could change the current call

        ## Continuation Status

        - recommended next stage: do not fill until the package is complete
        - status marker: {current_checkpoint} not reached yet
        - hard-boundary status: none triggered yet
        - completion point status: discovery work still in progress
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

        ## Key Sources

        List the highest-signal evidence IDs with direct URLs so a reviewer can inspect the strongest sources quickly.

        ## Current Workarounds And Substitutes

        Explain what users do today and why that is insufficient or good enough.

        ## Candidate Directions Emerging From Research

        List only serious candidate wedges and cite the evidence IDs that support or weaken them.
        Name one buyer, one workflow, and one wedge per candidate.

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
        - first buyer/user:
        - first wedge:
        - substitute pressure:
        - monetization angle:
        - agent-operability judgment:
        - why this is not a platform fantasy:
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

        ## First Wedge

        Name the first buyer, first workflow, first wedge, and first monetization path for the leader.

        ## Why The Runner-Up Lost

        Explain why the next-best option did not win.

        ## Why This Is Not A Platform Fantasy

        Explain what keeps the recommendation narrow, concrete, and sellable.

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

        ## Continuation Recommendation

        State the recommended next stage, whether any hard boundary blocks it, and what evidence would justify changing course.
        """
    )


def discovery_summary_stub(run_id: str) -> str:
    theme_summary = extract_theme_summary()
    current_checkpoint = checkpoint_label()
    return dedent(
        f"""\
        # Discovery Summary

        Launch scaffold: replace this note with a completed reviewer summary before the completion check.

        Run ID: {run_id}

        ## Run Context

        - theme: {theme_summary}
        - source count:
        - source types used:
        - candidate count:
        - boundary exceptions, if any:

        ## Key Source Links

        List the most important evidence IDs with direct URLs.

        ## Top Recommendation

        - recommended outcome:
        - leading candidate:
        - first buyer/user:
        - first wedge:
        - why it leads:
        - why this is not a platform fantasy:
        - what may still kill it:

        ## Ranked Shortlist

        Summarize the strongest candidates and the evidence that separates them.

        ## What Would Change The Call

        Explain which missing evidence could materially change the recommendation.

        ## Continuation Status

        State whether the discovery package reached {current_checkpoint}, what the recommended next stage is, whether any hard boundary applies, and whether the loop should continue.
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
        slug, slug_warning = choose_slug(args.slug)
        run_id = next_run_id(date_prefix, slug)

    if not args.run_id and slug_warning:
        print(f"WARN  {slug_warning}")

    research_root, artifact_root = initialize_run(run_id)

    print(f"RUN_ID  {run_id}")
    print(f"CORPUS_ROOT  {research_root.relative_to(ROOT).as_posix()}")
    print(f"ARTIFACT_ROOT  {artifact_root.relative_to(ROOT).as_posix()}")
    print("READINESS_CHECK  python scripts/check_repo_readiness.py")
    print(f"COMPLETION_CHECK  python scripts/check_repo_readiness.py --run-id {run_id}")
    print(f"THEME  {extract_theme_summary()}")
    print(f"CHECKPOINT  {checkpoint_label()}")
    print(f"CHECKPOINT_BEHAVIOR  {checkpoint_behavior()}")
    print("NEXT_STEP  Launch complete. Do the research work now, fully populate the corpus, manifests, links, and reviewer artifacts, then run the completion check last.")
    print("DO_NOT_PAUSE  A launched run with scaffold files does not satisfy the active completion point.")
    print("REQUIRED_OUTPUTS")
    for output in DISCOVERY_OUTPUTS:
        print(f"- {output.format(run_id=run_id)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())