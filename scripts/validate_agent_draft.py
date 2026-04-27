from __future__ import annotations

import argparse
from pathlib import Path

from apd.services.agent_draft_validation import validate_agent_draft_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an APD agent draft package JSON file without writing anything to the database. "
            "Use this before import to catch schema drift and common near-miss fields."
        )
    )
    parser.add_argument("--path", required=True, help="Path to an agent draft package JSON file")
    parser.add_argument(
        "--repair-hints",
        action="store_true",
        help="Print concise repair hints for common near-miss schema problems.",
    )
    parser.add_argument(
        "--repair-prompt",
        action="store_true",
        help="Print a copyable repair prompt for an LLM or manual repair pass.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    draft_path = Path(args.path)
    report = validate_agent_draft_file(draft_path)

    if report.is_valid:
        print(
            " ".join(
                [
                    f"path={draft_path.as_posix()}",
                    "valid=true",
                    "errors=0",
                    "hints=0",
                ]
            )
        )
        return 0

    print(
        " ".join(
            [
                f"path={draft_path.as_posix()}",
                "valid=false",
                f"errors={report.error_count}",
                f"summaries={len(report.grouped_errors)}",
                f"hints={len(report.repair_hints)}",
            ]
        )
    )
    for summary in report.grouped_errors[:12]:
        print(f"ISSUE: {summary}")
    if args.repair_hints:
        for hint in report.repair_hints[:16]:
            print(f"HINT: {hint}")
    if args.repair_prompt:
        print("REPAIR_PROMPT_BEGIN")
        print(report.build_repair_prompt())
        print("REPAIR_PROMPT_END")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
