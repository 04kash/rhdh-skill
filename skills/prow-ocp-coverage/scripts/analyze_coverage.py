#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["ruamel.yaml"]
# ///
"""Analyze RHDH OCP version coverage.

Cross-references cluster pools, CI test configs, RHDH lifecycle, and OCP
lifecycle data to identify coverage gaps and stale configurations.

Two dimensions are checked:
  1. OCP lifecycle -- is the OCP version itself still supported?
  2. RHDH compatibility -- does RHDH officially list this OCP version?
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from fetch_yaml import extract_branch, fetch_yaml, list_yaml_files
from ocp_lifecycle import classify_ocp_versions
from resolve_repo import resolve_repo_root
from rhdh_lifecycle import fetch_lifecycle_api, rhdh_supported_ocp_versions

POOL_DIR = "clusters/hosted-mgmt/hive/pools/rhdh"
CI_CONFIG_DIR = "ci-operator/config/redhat-developer/rhdh"


def ver_key(v):
    """Sort key for version strings like '4.16'."""
    return [int(x) for x in v.split(".")]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Analyze RHDH OCP version coverage.")
    parser.add_argument("--pool-dir", default=POOL_DIR, help="Pool directory")
    parser.add_argument("--config-dir", default=CI_CONFIG_DIR, help="CI config directory")
    parser.add_argument("--repo-dir", help="Path to openshift/release checkout")
    args = parser.parse_args(argv)

    root, is_remote = resolve_repo_root(args.repo_dir)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    mode_desc = "remote (GitHub API)" if is_remote else "local"

    print("=" * 56)
    print("  RHDH OCP Coverage Analysis")
    print("=" * 56)
    print()
    print(f"Pool directory:   {args.pool_dir}")
    print(f"Config directory: {args.config_dir}")
    print(f"Access mode:      {mode_desc}")
    print(f"Analysis time:    {now.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print()

    # ------- 1. Cluster pool versions -------
    print("--- Cluster Pools ---")
    pool_versions = []
    pool_files = list_yaml_files(args.pool_dir, "*_clusterpool.yaml", root, is_remote)
    for filepath in pool_files:
        data = fetch_yaml(filepath, root, is_remote)
        if not data:
            continue
        ver = data.get("metadata", {}).get("labels", {}).get("version")
        if not ver:
            continue
        pool_name = data.get("metadata", {}).get("name", "unknown")
        size = data.get("spec", {}).get("size", 0)
        max_size = data.get("spec", {}).get("maxSize", 0)
        pool_versions.append(ver)
        print(f"  {ver:<8s}  {pool_name:<25s}  size={size} max={max_size}")
    print()

    # ------- 2. Test config versions per branch -------
    print("--- Test Configs ---")
    prefix = "redhat-developer-rhdh-"
    branch_versions: dict[str, list[str]] = {}
    all_test_versions: list[str] = []

    config_files = list_yaml_files(args.config_dir, f"{prefix}*.yaml", root, is_remote)
    for filepath in config_files:
        branch = extract_branch(prefix, filepath)
        data = fetch_yaml(filepath, root, is_remote)
        if not data or "tests" not in data:
            continue
        versions = sorted(
            {
                t["cluster_claim"]["version"]
                for t in data["tests"]
                if t.get("cluster_claim", {}).get("version")
            },
            key=ver_key,
        )
        if versions:
            branch_versions[branch] = versions
            all_test_versions.extend(versions)
            print(f"  {branch}: {' '.join(versions)}")
    print()

    unique_test_versions = sorted(set(all_test_versions), key=ver_key)

    # ------- 3. RHDH lifecycle -------
    print("--- RHDH Lifecycle ---")
    print("  Fetching from Red Hat Product Life Cycles API...")
    rhdh_response = fetch_lifecycle_api("Red Hat Developer Hub")
    from rhdh_lifecycle import parse_rhdh_versions

    rhdh_data = parse_rhdh_versions(rhdh_response)

    for v in rhdh_data:
        if v["supported"]:
            print(f"  RHDH {v['version']} ({v['type']}): OCP {', '.join(v['ocp_versions'])}")

    rhdh_supported_ocp = rhdh_supported_ocp_versions(rhdh_data)
    print()
    print(f"  OCP versions supported by active RHDH releases: {' '.join(rhdh_supported_ocp)}")
    print()

    # Build per-RHDH-release -> OCP version mapping
    rhdh_branch_ocp: dict[str, list[str]] = {}
    latest_rhdh_ocp: list[str] = []
    for v in rhdh_data:
        if v["supported"]:
            branch = f"release-{v['version']}"
            rhdh_branch_ocp[branch] = v["ocp_versions"]
            latest_rhdh_ocp = v["ocp_versions"]

    # ------- 4. OCP lifecycle -------
    print("--- OCP Lifecycle ---")
    print("  Fetching from Red Hat Product Life Cycles API...")
    ocp_response = fetch_lifecycle_api("Red Hat OpenShift Container Platform")
    ocp_lifecycle = classify_ocp_versions(ocp_response, today)

    ocp_supported = [v["version"] for v in ocp_lifecycle if v["ocp_supported"]]
    ocp_eol = [v["version"] for v in ocp_lifecycle if not v["ocp_supported"]]
    print(f"  OCP supported:     {' '.join(ocp_supported)}")
    print(f"  OCP end-of-life:   {' '.join(ocp_eol)}")
    print()

    # Compute "main" branch OCP support
    if latest_rhdh_ocp:
        max_rhdh = max(latest_rhdh_ocp, key=ver_key)
        max_parts = ver_key(max_rhdh)
        main_ocp = list(latest_rhdh_ocp)
        for ocp_ver in ocp_supported:
            ocp_parts = ver_key(ocp_ver)
            if ocp_parts > max_parts and ocp_ver not in main_ocp:
                main_ocp.append(ocp_ver)
        rhdh_branch_ocp["main"] = sorted(main_ocp, key=ver_key)

    # ------- 5. OCP version matrix -------
    print("--- OCP Version Matrix ---")
    print()
    print(
        f"  {'OCP':<8s}  {'OCP_SUPP':<10s}  {'RHDH_SUPP':<10s}  {'OCP_PHASE':<30s}  RHDH_RELEASES"
    )
    print(
        f"  {'---':<8s}  {'--------':<10s}  {'---------':<10s}  {'---------':<30s}  -------------"
    )

    all_relevant = sorted(
        set(pool_versions + unique_test_versions + rhdh_supported_ocp + ocp_supported),
        key=ver_key,
    )

    ocp_phase_map = {v["version"]: v for v in ocp_lifecycle}
    for ver in all_relevant:
        ocp_info = ocp_phase_map.get(ver, {})
        ocp_sup = "yes" if ocp_info.get("ocp_supported") else "no"
        ocp_phase = ocp_info.get("phase", "N/A")
        rhdh_sup = "yes" if ver in rhdh_supported_ocp else "no"
        rhdh_releases = ", ".join(
            v["version"] for v in rhdh_data if v["supported"] and ver in v["ocp_versions"]
        )
        print(f"  {ver:<8s}  {ocp_sup:<10s}  {rhdh_sup:<10s}  {ocp_phase:<30s}  {rhdh_releases}")
    print()

    # ------- 6. Cross-reference analysis -------
    print("=" * 56)
    print("  Analysis Results")
    print("=" * 56)
    print()

    has_actions = False
    eol_pool_count = 0
    notrhdh_pool_count = 0
    mismatch_test_count = 0
    missing_pool_count = 0
    missing_test_count = 0

    # 6a. Pools for OCP-EOL versions
    print("--- Pools for OCP-EOL Versions (REMOVE) ---")
    for ver in pool_versions:
        if ver in ocp_eol:
            print(f"  REMOVE pool: {ver} (OCP end-of-life)")
            eol_pool_count += 1
            has_actions = True
    if eol_pool_count == 0:
        print("  (none)")
    print()

    # 6b. Pools for non-RHDH-supported versions
    print("--- Pools for Non-RHDH-Supported OCP Versions (REVIEW) ---")
    for ver in pool_versions:
        if ver in ocp_eol:
            continue
        if ver not in rhdh_supported_ocp:
            print(f"  REVIEW pool: {ver} (OCP supported, but not in any active RHDH release)")
            notrhdh_pool_count += 1
            has_actions = True
    if notrhdh_pool_count == 0:
        print("  (none)")
    print()

    # 6c. Test entries mismatched with RHDH compatibility
    print("--- Test Entries Mismatched With RHDH Compatibility (REVIEW) ---")
    for branch, versions in branch_versions.items():
        branch_ocp = rhdh_branch_ocp.get(branch, [])
        for ver in versions:
            if ver in ocp_eol:
                print(f"  REMOVE test: {ver} from {branch} (OCP end-of-life)")
                mismatch_test_count += 1
                has_actions = True
            elif branch_ocp and ver not in branch_ocp:
                print(f"  REVIEW test: {ver} in {branch} (not in RHDH openshift_compatibility)")
                mismatch_test_count += 1
                has_actions = True
    if mismatch_test_count == 0:
        print("  (none)")
    print()

    # 6d. Missing pools
    print("--- RHDH-Supported OCP Versions Missing Pools (ADD) ---")
    all_rhdh_ocp = sorted(
        {ver for ocp_list in rhdh_branch_ocp.values() for ver in ocp_list},
        key=ver_key,
    )
    for ver in all_rhdh_ocp:
        if ver in ocp_eol:
            continue
        if ver not in pool_versions:
            needed = ", ".join(
                v["version"] for v in rhdh_data if v["supported"] and ver in v["ocp_versions"]
            )
            print(f"  ADD pool: {ver} (needed by RHDH {needed})")
            missing_pool_count += 1
            has_actions = True
    if missing_pool_count == 0:
        print("  (none)")
    print()

    # 6e. Missing tests
    print("--- RHDH-Supported OCP Versions Missing Tests (ADD) ---")
    for branch, ocp_list in rhdh_branch_ocp.items():
        existing = branch_versions.get(branch, [])
        for ver in ocp_list:
            if ver in ocp_eol:
                continue
            if ver not in existing:
                print(f"  ADD test: {ver} to {branch}")
                missing_test_count += 1
                has_actions = True
    if missing_test_count == 0:
        print("  (none)")
    print()

    # ------- 7. Summary -------
    print("=" * 56)
    print("  Summary")
    print("=" * 56)
    print()
    print(f"  Pool versions:           {' '.join(pool_versions)}")
    print(f"  Test versions:           {' '.join(unique_test_versions)}")
    print(f"  OCP supported:           {' '.join(ocp_supported)}")
    print(f"  RHDH-supported OCP:      {' '.join(rhdh_supported_ocp)}")
    print()

    print("  RHDH branch -> OCP support (excluding OCP-EOL):")
    for branch in sorted(rhdh_branch_ocp.keys()):
        active = [v for v in rhdh_branch_ocp[branch] if v not in ocp_eol]
        eol_listed = [v for v in rhdh_branch_ocp[branch] if v in ocp_eol]
        line = f"    {branch}: {' '.join(active)}"
        if eol_listed:
            line += f"  (RHDH lists but OCP-EOL: {' '.join(eol_listed)})"
        print(line)
    print()

    print(f"  EOL pools to remove:         {eol_pool_count}")
    print(f"  Non-RHDH pools to review:    {notrhdh_pool_count}")
    print(f"  Mismatched tests to review:  {mismatch_test_count}")
    print(f"  Missing pools to add:        {missing_pool_count}")
    print(f"  Missing tests to add:        {missing_test_count}")
    print()

    if has_actions:
        print("  Data sources:")
        print("    RHDH lifecycle: https://access.redhat.com/support/policy/updates/developerhub")
        print(
            "    OCP lifecycle:  https://access.redhat.com/product-life-cycles/"
            "?product=OpenShift+Container+Platform+4"
        )
        print()
        print("  NOTE: The 'main' branch targets the next unreleased RHDH version.")
        print("  Its OCP support is estimated as: latest RHDH release's OCP list")
        print("  plus any newer OCP versions that have reached GA.")
        print("  REVIEW items require judgment; REMOVE/ADD items are actionable.")
    else:
        print("  All clear -- no coverage gaps or stale configurations found.")


if __name__ == "__main__":
    main()
