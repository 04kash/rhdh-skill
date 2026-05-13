#!/usr/bin/env python3
"""RHDH release lifecycle data from the Red Hat Product Life Cycles API.

Shared module used by:
  - lifecycle-rhdh/scripts/check_rhdh_lifecycle.py
  - lifecycle-ocp/scripts/check_ocp_lifecycle.py
  - prow-ocp-coverage/scripts/analyze_coverage.py

Usage:
    from rhdh_lifecycle import fetch_rhdh_lifecycle
    versions = fetch_rhdh_lifecycle()
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

LIFECYCLE_API_URL = "https://access.redhat.com/product-life-cycles/api/v1/products"


def fetch_lifecycle_api(product_name):
    """Fetch lifecycle data from the Red Hat Product Life Cycles API."""
    url = f"{LIFECYCLE_API_URL}?name={product_name.replace(' ', '+')}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "rhdh-skill"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError) as exc:
        print(f"ERROR: Failed to fetch lifecycle data for {product_name}: {exc}", file=sys.stderr)
        sys.exit(1)


def parse_rhdh_versions(api_data, filter_version=None):
    """Parse RHDH lifecycle data into structured version info.

    Returns a list of dicts with keys: version, type, supported, ga_date,
    full_support_end, maintenance_end, ocp_versions.
    """
    versions_raw = api_data.get("data", [{}])[0].get("versions", [])
    results = []
    for ver in versions_raw:
        name = ver.get("name", "")
        if filter_version and name != filter_version:
            continue
        vtype = ver.get("type", "")
        phases = ver.get("phases", [])

        def phase_date(pname):
            for p in phases:
                if p.get("name") == pname:
                    d = p.get("end_date", "N/A")
                    if d and isinstance(d, str) and d[:4].isdigit():
                        return d[:10]
                    return str(d) if d else "N/A"
            return "N/A"

        ocp_compat = ver.get("openshift_compatibility", "")
        ocp_versions = [v.strip() for v in ocp_compat.split(",") if v.strip()] if ocp_compat else []

        results.append(
            {
                "version": name,
                "type": vtype,
                "supported": vtype != "End of life",
                "ga_date": phase_date("General availability"),
                "full_support_end": phase_date("Full support"),
                "maintenance_end": phase_date("Maintenance support"),
                "ocp_versions": ocp_versions,
            }
        )
    results.sort(
        key=lambda v: [int(x) for x in v["version"].split(".")] if "." in v["version"] else [0]
    )
    return results


def fetch_rhdh_lifecycle(filter_version=None):
    """Fetch and parse RHDH lifecycle data. Convenience wrapper."""
    api_data = fetch_lifecycle_api("Red Hat Developer Hub")
    return parse_rhdh_versions(api_data, filter_version)


def rhdh_supported_ocp_versions(rhdh_data):
    """Return sorted list of OCP versions supported by any active RHDH release."""
    return sorted(
        {ocp for v in rhdh_data if v["supported"] for ocp in v["ocp_versions"]},
        key=lambda x: [int(n) for n in x.split(".")],
    )
