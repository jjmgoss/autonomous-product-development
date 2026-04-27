from __future__ import annotations

import argparse

from apd.app.db import SessionLocal
from apd.services.report_export import export_run_markdown_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a run as a local Markdown report and record it as an Artifact. "
            "Exports are timestamped to avoid silent overwrite."
        )
    )
    parser.add_argument("--run-id", type=int, required=True, help="Run ID to export")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    with SessionLocal() as session:
        result = export_run_markdown_report(session, args.run_id)

    if result is None:
        print(f"run_id={args.run_id} exported=false reason=not_found")
        return 1

    print(
        " ".join(
            [
                f"run_id={result.run_id}",
                "exported=true",
                f"artifact_id={result.artifact_id}",
                f"path={result.artifact_path.as_posix()}",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
