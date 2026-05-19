"""Shared gcloud access token helper for rhdh-test-plan-review scripts.

Library module — imported by check_gsheets.py and fetch_schedule.py.
Not a CLI script; do not invoke directly.
"""

import shutil
import subprocess


def get_gcloud_token():
    """Return (access_token_or_None, error_message_or_None) from gcloud CLI."""
    gcloud = shutil.which("gcloud")
    if not gcloud:
        return None, "gcloud not on PATH — install Google Cloud CLI and add gcloud to PATH"

    result = subprocess.run(
        [gcloud, "auth", "print-access-token"],
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()
    if token:
        return token, None
    return None, "No active gcloud account — run: gcloud auth login --enable-gdrive-access"
