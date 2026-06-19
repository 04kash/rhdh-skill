#!/usr/bin/env python3
"""Explain a Scaffolder action or template parameter schema.

For actions: fetches GET /api/scaffolder/v2/actions and returns the matching
action's input/output JSON Schema.

For templates: fetches GET /api/scaffolder/v2/templates/:ns/:kind/:name/parameter-schema.

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

from scaffolder_api import get_action_schema, get_template_parameter_schema  # noqa: E402

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain Scaffolder action or template schema.")
    parser.add_argument("--rhdh-url", required=True, help="RHDH base URL")
    parser.add_argument("--action", help="Action id (e.g. publish:github)")
    parser.add_argument(
        "--template-ref",
        help="Catalog template ref (e.g. template:default/my-template)",
    )
    parser.add_argument("--token", help="Bearer token (default: RHDH_TOKEN or BACKSTAGE_TOKEN env)")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    if bool(args.action) == bool(args.template_ref):
        print("Provide exactly one of --action or --template-ref", file=sys.stderr)
        return EXIT_USAGE

    try:
        if args.action:
            action = get_action_schema(args.rhdh_url, args.action, token=args.token)
            if action is None:
                print(f"Action not found: {args.action}", file=sys.stderr)
                return EXIT_FAILURE
            result = {
                "ok": True,
                "type": "action",
                "id": action.get("id"),
                "description": action.get("description"),
                "schema": action.get("schema"),
                "examples": action.get("examples"),
            }
        else:
            schema = get_template_parameter_schema(
                args.rhdh_url,
                args.template_ref,
                token=args.token,
            )
            result = {
                "ok": True,
                "type": "template-parameter-schema",
                "template_ref": args.template_ref,
                "schema": schema,
            }
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_FAILURE

    if args.json:
        print(json.dumps(result, indent=2 if _is_tty else None))
    else:
        if result["type"] == "action":
            print(f"Action: {result['id']}")
            if result.get("description"):
                print(result["description"])
            schema = result.get("schema") or {}
            if schema.get("input"):
                print("\nInput schema:")
                print(json.dumps(schema["input"], indent=2))
            if schema.get("output"):
                print("\nOutput schema:")
                print(json.dumps(schema["output"], indent=2))
        else:
            print(f"Template: {result['template_ref']}")
            print(json.dumps(result["schema"], indent=2))

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
