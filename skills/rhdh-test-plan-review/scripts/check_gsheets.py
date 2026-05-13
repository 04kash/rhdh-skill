#!/usr/bin/env python3
"""Check if gcloud auth is configured for rhdh-test-plan-review."""

import argparse
import json
import os
import sys

from gcloud_token import get_gcloud_token

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color


def colored(text, code):
    if _is_tty:
        return f"\033[{code}m{text}\033[0m"
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Check if gcloud auth is configured for the Google Sheets API."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON (default: human-readable)",
    )
    args = parser.parse_args()

    token, error = get_gcloud_token()
    result = {
        "credentials_found": token is not None,
        "method": "gcloud",
        "error": error,
    }

    if args.json_output:
        json.dump(result, sys.stdout, indent=2)
        print()
    else:
        if result["credentials_found"]:
            print(colored("✓", "32") + " gcloud auth token available")
        else:
            print(colored("✗", "31") + f" {error}")
            print()
            if not (error and "PATH" in error):
                print("Run: gcloud auth login --enable-gdrive-access")

    sys.exit(0 if result["credentials_found"] else 1)


if __name__ == "__main__":
    main()
