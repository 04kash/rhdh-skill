#!/usr/bin/env python3
"""Initialize an RHDH Software Template authoring workspace.

Checks required tooling, scaffolds recommended directory layout, and
optionally probes RHDH Scaffolder API connectivity.

Stdlib only per project ADR-0002.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_PARTIAL = 1
EXIT_USAGE = 2

REQUIRED_TOOLS = ("python3", "git")
RECOMMENDED_TOOLS = ("djlint",)

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color


def _c(code: str, text: str) -> str:
    return f"{code}{text}\033[0m" if _is_tty else text


def green(t: str) -> str:
    return _c("\033[0;32m", t)


def yellow(t: str) -> str:
    return _c("\033[1;33m", t)


def red(t: str) -> str:
    return _c("\033[0;31m", t)


def tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def check_tools() -> dict:
    results = {"required": {}, "recommended": {}}
    for tool in REQUIRED_TOOLS:
        results["required"][tool] = tool_available(tool)
    for tool in RECOMMENDED_TOOLS:
        results["recommended"][tool] = tool_available(tool)
    return results


def probe_rhdh(url: str, timeout: int = 10) -> dict:
    base = url.rstrip("/")
    endpoint = f"{base}/api/scaffolder/v2/actions"
    try:
        req = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body) if body else []
            count = len(data) if isinstance(data, list) else 0
            return {"reachable": True, "endpoint": endpoint, "action_count": count}
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as exc:
        return {"reachable": False, "endpoint": endpoint, "error": str(exc)}


def scaffold_layout(root: Path, skill_dir: Path) -> dict:
    created: list[str] = []
    existing: list[str] = []

    templates_dir = root / "templates"
    example_dir = templates_dir / "example-template"
    skeleton_dir = example_dir / "skeleton"

    for path in (templates_dir, example_dir, skeleton_dir):
        if path.exists():
            existing.append(str(path.relative_to(root)))
        else:
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path.relative_to(root)))

    example_template = skill_dir / "assets" / "examples" / "minimal-template" / "template.yaml"
    target_template = example_dir / "template.yaml"
    if not target_template.exists() and example_template.exists():
        shutil.copy2(example_template, target_template)
        created.append(str(target_template.relative_to(root)))

    example_skeleton = skill_dir / "assets" / "examples" / "minimal-template" / "skeleton"
    if example_skeleton.is_dir():
        for item in example_skeleton.iterdir():
            dest = skeleton_dir / item.name
            if not dest.exists():
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
                created.append(str(dest.relative_to(root)))

    example_readme = example_dir / "README.md"
    if not example_readme.exists():
        example_readme.write_text(
            "# example-template\n\nRename this directory and customize `template.yaml`.\n",
            encoding="utf-8",
        )
        created.append(str(example_readme.relative_to(root)))

    location_path = root / "location.yaml"
    if not location_path.exists():
        content = (
            "apiVersion: backstage.io/v1alpha1\n"
            "kind: Location\n"
            "metadata:\n"
            f"  name: {root.name}-templates\n"
            "  description: Software Templates\n"
            "spec:\n"
            "  targets:\n"
            "    - ./templates/**/template.yaml\n"
        )
        location_path.write_text(content, encoding="utf-8")
        created.append("location.yaml")

    return {"created": created, "existing": existing}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize RHDH Software Template authoring workspace.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Template repository root (default: current directory)",
    )
    parser.add_argument(
        "--rhdh-url",
        help="Optional RHDH base URL to probe Scaffolder API",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    root = args.path.resolve()
    skill_dir = Path(__file__).resolve().parent.parent

    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
    elif not root.is_dir():
        print(red(f"Not a directory: {root}"), file=sys.stderr)
        return EXIT_USAGE

    tools = check_tools()
    missing_required = [k for k, v in tools["required"].items() if not v]
    missing_recommended = [k for k, v in tools["recommended"].items() if not v]

    layout = scaffold_layout(root, skill_dir)
    rhdh = probe_rhdh(args.rhdh_url) if args.rhdh_url else None

    ok = not missing_required
    partial = bool(missing_recommended) or (rhdh and not rhdh.get("reachable"))

    result = {
        "ok": ok,
        "path": str(root),
        "tools": tools,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "layout": layout,
        "rhdh": rhdh,
    }

    if args.json:
        print(json.dumps(result, indent=2 if _is_tty else None))
    else:
        print(green("RHDH Templates init"))
        print(f"  Path: {root}")
        for tool, present in tools["required"].items():
            status = green("ok") if present else red("missing")
            print(f"  {tool}: {status}")
        for tool, present in tools["recommended"].items():
            status = green("ok") if present else yellow("missing (optional)")
            print(f"  {tool}: {status}")
        if layout["created"]:
            print(green("Created:"))
            for p in layout["created"]:
                print(f"    {p}")
        if rhdh:
            if rhdh.get("reachable"):
                print(green(f"RHDH reachable — {rhdh.get('action_count', 0)} actions"))
            else:
                print(yellow(f"RHDH unreachable: {rhdh.get('error')}"))
        if missing_required:
            print(red("Install missing required tools before authoring."))

    if not ok:
        return EXIT_PARTIAL
    return EXIT_PARTIAL if partial else EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
