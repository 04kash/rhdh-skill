#!/usr/bin/env python3
"""Generate or update location.yaml for an RHDH template repository.

Discovers templates/**/template.yaml and writes a Location entity at repo root.

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

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color


def discover_templates(root: Path) -> list[str]:
    templates_dir = root / "templates"
    if not templates_dir.is_dir():
        return []
    found: list[str] = []
    for path in sorted(templates_dir.rglob("template.yaml")):
        rel = path.relative_to(root).as_posix()
        found.append(rel)
    return found


def build_location_yaml(name: str, description: str, targets: list[str]) -> str:
    lines = [
        "apiVersion: backstage.io/v1alpha1",
        "kind: Location",
        "metadata:",
        f"  name: {name}",
        f"  description: {description}",
        "spec:",
        "  targets:",
    ]
    if targets:
        for target in targets:
            lines.append(f"    - ./{target}")
    else:
        lines.append("    - ./templates/**/template.yaml")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate location.yaml for template repo.")
    parser.add_argument("--path", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--name", help="metadata.name for Location (default: <dir>-templates)")
    parser.add_argument("--description", help="metadata.description")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Print YAML without writing")
    args = parser.parse_args()

    root = args.path.resolve()
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
    elif not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return EXIT_USAGE

    templates = discover_templates(root)
    name = args.name or f"{root.name}-templates"
    description = args.description or f"Software Templates in {root.name}"
    content = build_location_yaml(name, description, templates)

    location_path = root / "location.yaml"
    written = False
    if not args.dry_run:
        location_path.write_text(content, encoding="utf-8")
        written = True

    result = {
        "ok": True,
        "path": str(root),
        "location_file": str(location_path),
        "written": written,
        "template_count": len(templates),
        "templates": templates,
        "metadata_name": name,
    }

    if args.json:
        print(json.dumps(result, indent=2 if _is_tty else None))
    else:
        print(f"Location: {location_path}")
        print(f"Templates discovered: {len(templates)}")
        for t in templates:
            print(f"  - {t}")
        if written:
            print("Wrote location.yaml")
        elif args.dry_run:
            print("--- dry-run ---")
            print(content)

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
