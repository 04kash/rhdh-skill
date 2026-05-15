#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["ruamel.yaml"]
# ///
"""Check AKS Kubernetes version lifecycle using the official AKS release status API.

Primary source: https://releases.aks.azure.com/parsed_data.json
Cross-verify:   https://endoflife.date/api/azure-kubernetes-service.json
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from configured_versions import print_configured_versions, resolve_repo_root

AKS_API_URL = "https://releases.aks.azure.com/parsed_data.json"
EOL_API_URL = "https://endoflife.date/api/azure-kubernetes-service.json"
CONFIG_DIR = "ci-operator/config/redhat-developer/rhdh"


def fetch_json(url):
    """Fetch JSON from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "rhdh-skill"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError) as exc:
        print(f"ERROR: Failed to fetch {url}: {exc}", file=sys.stderr)
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check AKS K8s version lifecycle.")
    parser.add_argument("--mapt-ref", help="Path to MAPT ref YAML (repo-relative)")
    parser.add_argument("--test-pattern", help="Regex to match test names")
    parser.add_argument("--config-dir", default=CONFIG_DIR, help="CI config directory")
    parser.add_argument("--repo-dir", help="Path to openshift/release checkout")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    args = parser.parse_args(argv)

    root, is_remote = resolve_repo_root(args.repo_dir)

    # Print configured versions if test pattern provided
    if args.test_pattern:
        print_configured_versions(
            args.config_dir, args.test_pattern, root, is_remote, args.mapt_ref
        )

    # Fetch AKS release data (primary source)
    data = fetch_json(AKS_API_URL)
    if not data:
        sys.exit(1)

    # Extract supported versions from the first region
    try:
        regional = data["Sections"]["KubernetesSupportedVersions"]["Components"][
            "KubernetesVersions"
        ]["RegionalStatuses"]
        first_region = list(regional.values())[0][0]["Current"]["KubernetesVersionList"]
    except (KeyError, IndexError, TypeError):
        print("ERROR: Unexpected AKS API response structure", file=sys.stderr)
        sys.exit(1)

    # Group by minor version
    minor_versions = {}
    for entry in first_region:
        parts = entry["VersionName"].split(".")
        minor = f"{parts[0]}.{parts[1]}"
        if minor not in minor_versions:
            minor_versions[minor] = {"is_lts": False, "is_preview": False}
        if entry.get("IsLTS"):
            minor_versions[minor]["is_lts"] = True
        if entry.get("IsPreview"):
            minor_versions[minor]["is_preview"] = True

    sorted_versions = sorted(
        minor_versions.items(),
        key=lambda x: [int(n) for n in x[0].split(".")],
        reverse=True,
    )

    # Deprecated version
    try:
        deprecated = regional[list(regional.keys())[0]][0]["Current"].get(
            "DeprecatedVersion", "N/A"
        )
    except (KeyError, IndexError):
        deprecated = "N/A"

    # Cross-verify with endoflife.date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    eol_data = fetch_json(EOL_API_URL)
    eol_supported = []
    if eol_data:
        for entry in eol_data:
            eol = entry.get("eol", "N/A")
            ext = entry.get("extendedSupport", "N/A")
            has_support = False
            if eol == "N/A":
                has_support = True
            elif isinstance(eol, bool):
                has_support = not eol
            elif isinstance(eol, str) and eol > today:
                has_support = True
            if not has_support and isinstance(ext, str) and ext > today:
                has_support = True
            if has_support:
                eol_supported.append(entry)
        eol_supported.sort(key=lambda e: [int(x) for x in e["cycle"].split(".")], reverse=True)

    # JSON output
    if args.json_output:
        result = {
            "versions": [
                {
                    "version": ver,
                    "status": "LTS"
                    if info["is_lts"]
                    else ("Preview" if info["is_preview"] else "GA"),
                }
                for ver, info in sorted_versions
            ],
            "deprecated": deprecated,
            "endoflife_date": [
                {"version": e["cycle"], "eol": str(e.get("eol", "N/A"))} for e in eol_supported
            ],
        }
        json.dump(result, sys.stdout, indent=2)
        print()
        return

    # Human-readable output
    print("=== AKS Release Status (releases.aks.azure.com) ===")
    print("Supported minor versions (newest first):")
    for ver, info in sorted_versions:
        if info["is_lts"]:
            status = "LTS"
        elif info["is_preview"]:
            status = "Preview"
        else:
            status = "GA"
        print(f"  {ver:<8s} {status}")
    print(f"Recently deprecated: {deprecated}")

    print()
    print("=== Cross-verify (endoflife.date) ===")
    if not eol_data:
        print("WARNING: Failed to fetch endoflife.date", file=sys.stderr)
        return
    for entry in eol_supported:
        print(f"  {entry['cycle']}\tEOL: {entry.get('eol', 'N/A')}")


if __name__ == "__main__":
    main()
