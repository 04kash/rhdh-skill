#!/usr/bin/env python3
"""Validate components in fields.md against live Jira project data.

Compares the Component Catalog table in references/fields.md against the
components actually configured in RHIDP and RHDHPLAN Jira projects. Reports
components that exist in Jira but are missing from fields.md, and components
listed in fields.md that no longer exist in Jira.

Usage:
  python scripts/validate_components.py
  python scripts/validate_components.py --json

Requires:
  - .jira-token file next to acli (email:token format)
  - Network access to redhat.atlassian.net

Exit codes:
  0  All components match
  1  Drift detected (missing or extra components)
  2  Argument error
  3  Token file not found
  4  API request failed
"""

import argparse
import base64
import json
import shutil
import sys
import urllib.request
from pathlib import Path


def find_token_file() -> Path | None:
    """Find .jira-token next to acli executable."""
    acli = shutil.which("acli")
    if not acli:
        return None
    token_path = Path(acli).resolve().parent / ".jira-token"
    return token_path if token_path.exists() else None


def fetch_components(token: str, project: str) -> list[str]:
    """Fetch component names from a Jira project via REST API."""
    url = f"https://redhat.atlassian.net/rest/api/3/project/{project}/components"
    auth = base64.b64encode(token.encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"Error fetching {project} components: {e}", file=sys.stderr)
        sys.exit(4)
    return sorted(c["name"] for c in data)


def parse_fields_md(fields_path: Path) -> set[str]:
    """Extract component names from the Component Catalog tables in fields.md."""
    text = fields_path.read_text(encoding="utf-8")
    components = set()
    # Match table rows: | ComponentName | Description | ... |
    # Skip header rows (contain "Component" or "---")
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        # cells[0] is empty (before first |), cells[1] is the component name
        if len(cells) < 3:
            continue
        name = cells[1]
        if not name or name == "Component" or name.startswith("---"):
            continue
        # Skip non-component table rows (from other tables in fields.md)
        # Component tables come after "### Component Catalog"
        components.add(name)
    return components


def parse_component_section(fields_path: Path) -> set[str]:
    """Extract only components from the Component Catalog section."""
    text = fields_path.read_text(encoding="utf-8")
    components = set()
    in_catalog = False
    in_table = False

    for line in text.splitlines():
        if "### Component Catalog" in line:
            in_catalog = True
            continue
        if in_catalog and line.startswith("### "):
            # Hit next section
            in_catalog = False
            continue
        if not in_catalog:
            continue

        if line.startswith("|") and "---" in line:
            in_table = True
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")]
            if len(cells) >= 3 and cells[1] and cells[1] != "Component":
                components.add(cells[1])
        elif in_table and not line.startswith("|"):
            if line.strip() == "" or line.startswith("**"):
                in_table = False  # gap between tables, reset
            else:
                in_table = False

    return components


def main():
    parser = argparse.ArgumentParser(
        description="Validate fields.md components against live Jira data."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    # Find fields.md relative to this script
    script_dir = Path(__file__).resolve().parent
    fields_path = script_dir.parent / "references" / "fields.md"
    if not fields_path.exists():
        print(f"fields.md not found at {fields_path}", file=sys.stderr)
        sys.exit(2)

    # Find token
    token_path = find_token_file()
    if not token_path:
        print("Token file not found. Run scripts/setup.py first.", file=sys.stderr)
        sys.exit(3)
    token = token_path.read_text().strip()

    # Parse fields.md
    documented = parse_component_section(fields_path)

    # Fetch live components from both projects
    rhidp_components = set(fetch_components(token, "RHIDP"))
    rhdhplan_components = set(fetch_components(token, "RHDHPLAN"))
    live = rhidp_components | rhdhplan_components

    # Compare
    in_jira_not_doc = sorted(live - documented)
    in_doc_not_jira = sorted(documented - live)

    if args.json_output:
        result = {
            "documented_count": len(documented),
            "live_count": len(live),
            "missing_from_docs": in_jira_not_doc,
            "missing_from_jira": in_doc_not_jira,
            "in_sync": len(in_jira_not_doc) == 0 and len(in_doc_not_jira) == 0,
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"Documented components: {len(documented)}")
        print(f"Live Jira components:  {len(live)}")
        print(f"  RHIDP:    {len(rhidp_components)}")
        print(f"  RHDHPLAN: {len(rhdhplan_components)}")
        print()

        if in_jira_not_doc:
            print(f"⚠️  In Jira but NOT in fields.md ({len(in_jira_not_doc)}):")
            for c in in_jira_not_doc:
                projects = []
                if c in rhidp_components:
                    projects.append("RHIDP")
                if c in rhdhplan_components:
                    projects.append("RHDHPLAN")
                print(f"  + {c}  ({', '.join(projects)})")
            print()

        if in_doc_not_jira:
            print(f"⚠️  In fields.md but NOT in Jira ({len(in_doc_not_jira)}):")
            for c in in_doc_not_jira:
                print(f"  - {c}")
            print()

        if not in_jira_not_doc and not in_doc_not_jira:
            print("✅ All components in sync.")
        else:
            print(
                f"❌ Drift detected: {len(in_jira_not_doc)} missing from docs, "
                f"{len(in_doc_not_jira)} missing from Jira."
            )

    sys.exit(0 if not in_jira_not_doc and not in_doc_not_jira else 1)


if __name__ == "__main__":
    main()
