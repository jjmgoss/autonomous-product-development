from __future__ import annotations

import argparse

from apd.app.db import SessionLocal
from apd.fixtures.seed import FIXTURE_ID
from apd.fixtures.seed import reset_fixture_data
from apd.fixtures.seed import seed_fixture_data


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed deterministic APD fixture data into the local database.")
    parser.add_argument(
        "--reset-fixture",
        action="store_true",
        help="Delete existing fixture-owned records first, then reseed fixture data.",
    )
    parser.add_argument(
        "--reset-only",
        action="store_true",
        help="Delete fixture-owned records and exit without reseeding.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    with SessionLocal() as session:
        if args.reset_only:
            reset_result = reset_fixture_data(session)
            session.commit()
            print(f"fixture_id={FIXTURE_ID} removed_runs={reset_result.removed_runs}")
            return 0

        seed_result = seed_fixture_data(session, reset_fixture=args.reset_fixture)
        session.commit()

    print(
        " ".join(
            [
                f"fixture_id={FIXTURE_ID}",
                f"created={seed_result.created}",
                f"run_id={seed_result.run_id}",
                f"runs={seed_result.run_count}",
                f"sources={seed_result.source_count}",
                f"excerpts={seed_result.excerpt_count}",
                f"claims={seed_result.claim_count}",
                f"themes={seed_result.theme_count}",
                f"candidates={seed_result.candidate_count}",
                f"evidence_links={seed_result.evidence_link_count}",
                f"validation_gates={seed_result.validation_gate_count}",
                f"review_notes={seed_result.review_note_count}",
                f"decisions={seed_result.decision_count}",
                f"artifacts={seed_result.artifact_count}",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
