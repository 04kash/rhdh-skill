#!/usr/bin/env python3
"""List Scaffolder actions from a running RHDH instance.

Uses GET /api/scaffolder/v2/actions.

Stdlib only per project ADR-0002.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from scaffolder_api import list_actions  # noqa: E402

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color


def main() -> int:
    parser = argparse.ArgumentParser(description="List Scaffolder actions from RHDH.")
    parser.add_argument(
        "--rhdh-url", required=True, help="RHDH base URL (e.g. https://rhdh.example.com)"
    )
    parser.add_argument("--token", help="Bearer token (default: RHDH_TOKEN or BACKSTAGE_TOKEN env)")
    parser.add_argument("--filter", help="Case-insensitive substring filter on action id")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    try:
        actions = list_actions(args.rhdh_url, token=args.token)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_FAILURE

    if args.filter:
        needle = args.filter.lower()
        actions = [a for a in actions if needle in a.get("id", "").lower()]

    result = {
        "ok": True,
        "rhdh_url": args.rhdh_url.rstrip("/"),
        "action_count": len(actions),
        "actions": actions,
    }

    if args.json:
        print(json.dumps(result, indent=2 if _is_tty else None))
    else:
        print(f"RHDH: {args.rhdh_url.rstrip('/')}")
        print(f"Actions: {len(actions)}")
        for action in actions:
            desc = action.get("description") or ""
            if desc:
                desc = desc.split("\n", 1)[0][:80]
                print(f"  {action['id']} — {desc}")
            else:
                print(f"  {action['id']}")

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
