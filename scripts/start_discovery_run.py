from __future__ import annotations

import sys


def main() -> int:
    print("DEPRECATED  scripts/start_discovery_run.py belongs to the older theme-driven kickoff flow.")
    print("NEXT  Use `python scripts/autopd.py test \"DIRECT_INTENT\"` or `python scripts/autopd.py real \"DIRECT_INTENT\"` instead.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
