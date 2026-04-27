from __future__ import annotations

import argparse
import json
from pathlib import Path

from apd.services.agent_draft_validation import normalize_agent_draft_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Best-effort normalize a near-miss APD agent draft package to an explicit output path. "
            "Normalization never imports data and strict validation remains the final gate."
        )
    )
    parser.add_argument("--path", required=True, help="Path to an input agent draft package JSON file")
    parser.add_argument("--out", required=True, help="Explicit output path for the normalized JSON file")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    input_path = Path(args.path)
    output_path = Path(args.out)

    result = normalize_agent_draft_file(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.normalized_data, indent=2), encoding="utf-8")

    report = result.validation_report
    print(
        " ".join(
            [
                f"path={input_path.as_posix()}",
                f"out={output_path.as_posix()}",
                f"applied_fixes={len(result.applied_fixes)}",
                f"valid={'true' if report.is_valid else 'false'}",
                f"errors={report.error_count}",
            ]
        )
    )
    for fix in result.applied_fixes[:20]:
        print(f"FIX: {fix}")
    if not report.is_valid:
        for summary in report.grouped_errors[:12]:
            print(f"ISSUE: {summary}")
        for hint in report.repair_hints[:16]:
            print(f"HINT: {hint}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
