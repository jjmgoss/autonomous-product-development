from __future__ import annotations

import argparse
from pathlib import Path

from apd.app.db import SessionLocal
from apd.services.agent_draft_import import (
    AgentDraftValidationError,
    DuplicateExternalDraftIdError,
    import_agent_draft_file,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import an APD agent draft package JSON file as draft/unreviewed research. "
            "This command does not fetch URLs or call external model APIs."
        )
    )
    parser.add_argument("--path", required=True, help="Path to an agent draft package JSON file")
    parser.add_argument(
        "--allow-duplicate-external-id",
        action="store_true",
        help="Allow importing when external_draft_id has already been imported. By default duplicates are rejected.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    draft_path = Path(args.path)

    with SessionLocal() as session:
        try:
            result = import_agent_draft_file(
                session,
                draft_path,
                allow_duplicate_external_id=args.allow_duplicate_external_id,
            )
        except AgentDraftValidationError as exc:
            print(f"path={draft_path.as_posix()} imported=false reason=validation_error errors={len(exc.errors)}")
            for error in exc.errors:
                print(f"ERROR: {error}")
            return 2
        except DuplicateExternalDraftIdError as exc:
            print(
                " ".join(
                    [
                        f"path={draft_path.as_posix()}",
                        "imported=false",
                        "reason=duplicate_external_draft_id",
                        f"external_draft_id={exc.external_draft_id}",
                        f"existing_run_id={exc.run_id}",
                    ]
                )
            )
            return 3

    print(
        " ".join(
            [
                f"path={draft_path.as_posix()}",
                "imported=true",
                f"run_db_id={result.run_db_id}",
                f"external_draft_id={result.external_draft_id or 'none'}",
                f"imported_sources={result.imported_source_count}",
                f"imported_excerpts={result.imported_excerpt_count}",
                f"imported_claims={result.imported_claim_count}",
                f"imported_themes={result.imported_theme_count}",
                f"imported_candidates={result.imported_candidate_count}",
                f"imported_validation_gates={result.imported_validation_gate_count}",
                f"imported_evidence_links={result.imported_evidence_link_count}",
                f"warnings={len(result.warnings)}",
            ]
        )
    )
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
