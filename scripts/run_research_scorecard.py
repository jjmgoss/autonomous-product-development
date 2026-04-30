from __future__ import annotations

import argparse
from pathlib import Path

from apd.evals.research_scorecard import build_research_scorecard_report, render_scorecard_markdown, write_scorecard_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build APD research scorecards from one or more eval result JSON files.")
    parser.add_argument("--results", nargs="+", required=True, help="Eval result JSON paths or glob patterns.")
    parser.add_argument("--out-json", help="Optional path to write the aggregated scorecard JSON artifact.")
    parser.add_argument("--out-md", help="Optional path to write the markdown summary artifact.")
    args = parser.parse_args(argv)

    report = build_research_scorecard_report(args.results)
    markdown = render_scorecard_markdown(report)
    print(markdown)

    write_scorecard_artifacts(
        report,
        out_json=Path(args.out_json) if args.out_json else None,
        out_md=Path(args.out_md) if args.out_md else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())