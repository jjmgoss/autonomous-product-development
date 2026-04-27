from __future__ import annotations

import argparse

from apd.app.db import SessionLocal
from apd.services.legacy_import import import_legacy_run


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import or link a legacy APD run by run ID. "
            "Reads existing research-corpus and artifacts files without modifying them."
        )
    )
    parser.add_argument("--run-id", required=True, help="Legacy run ID to import or link")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    with SessionLocal() as session:
        result = import_legacy_run(session, args.run_id)

    if result is None:
        print(f"legacy_run_id={args.run_id} imported=false reason=not_found")
        return 1

    print(
        " ".join(
            [
                f"legacy_run_id={result.legacy_run_id}",
                "imported=true",
                f"run_db_id={result.run_db_id}",
                f"created_run={str(result.created_run).lower()}",
                f"linked_artifacts={result.linked_artifact_count}",
                f"imported_sources={result.imported_source_count}",
                f"warnings={len(result.warnings)}",
            ]
        )
    )
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
