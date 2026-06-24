#!/usr/bin/env python3
"""Dry-run a Software Template against a running RHDH Scaffolder.

Uses POST /api/scaffolder/v2/dry-run with template.yaml, skeleton files, and
parameter values.

Requires PyYAML to parse template.yaml (available in project dev dependencies).

Stdlib + optional PyYAML per project ADR-0002.
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

from scaffolder_api import dry_run, load_directory_contents  # noqa: E402

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color


def load_yaml_file(path: Path) -> dict:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required for dry-run. Install dev deps: uv sync --extra dev"
        ) from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def resolve_template_dir(path: Path) -> tuple[Path, Path]:
    path = path.resolve()
    if path.is_file():
        template_yaml = path
        template_dir = path.parent
    elif path.is_dir():
        template_dir = path
        template_yaml = path / "template.yaml"
    else:
        raise FileNotFoundError(f"Path not found: {path}")
    if not template_yaml.is_file():
        raise FileNotFoundError(f"No template.yaml at {template_yaml}")
    return template_yaml, template_dir


def summarize_log(log: list) -> list[str]:
    lines: list[str] = []
    for entry in log or []:
        body = entry.get("body") if isinstance(entry, dict) else None
        if isinstance(body, dict) and body.get("message"):
            lines.append(str(body["message"]))
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run an RHDH Software Template.")
    parser.add_argument("--rhdh-url", required=True, help="RHDH base URL")
    parser.add_argument(
        "--path",
        required=True,
        type=Path,
        help="Template directory or template.yaml path",
    )
    parser.add_argument(
        "--values",
        type=Path,
        help="JSON file with parameter values (default: {})",
    )
    parser.add_argument(
        "--secrets",
        type=Path,
        help="JSON file with secrets map (optional)",
    )
    parser.add_argument(
        "--skeleton-dir",
        type=Path,
        help="Skeleton directory (default: <template-dir>/skeleton)",
    )
    parser.add_argument("--token", help="Bearer token (default: RHDH_TOKEN or BACKSTAGE_TOKEN env)")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    try:
        template_yaml, template_dir = resolve_template_dir(args.path)
        template = load_yaml_file(template_yaml)
        values: dict = {}
        if args.values:
            values = json.loads(args.values.read_text(encoding="utf-8"))
            if not isinstance(values, dict):
                raise ValueError("--values file must contain a JSON object")
        secrets: dict[str, str] | None = None
        if args.secrets:
            raw = json.loads(args.secrets.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("--secrets file must contain a JSON object")
            secrets = {str(k): str(v) for k, v in raw.items()}

        directory_contents: list[dict[str, str]] = []
        content_root = args.skeleton_dir or template_dir
        if content_root.is_dir():
            if args.skeleton_dir:
                prefix = content_root.relative_to(template_dir).as_posix()
                for item in load_directory_contents(content_root):
                    directory_contents.append(
                        {
                            "path": f"{prefix}/{item['path']}",
                            "base64Content": item["base64Content"],
                        }
                    )
            else:
                directory_contents = load_directory_contents(content_root)

        response = dry_run(
            args.rhdh_url,
            template=template,
            values=values,
            directory_contents=directory_contents,
            secrets=secrets,
            token=args.token,
        )
    except (RuntimeError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_FAILURE if isinstance(exc, RuntimeError) else EXIT_USAGE

    log_lines = summarize_log(response.get("log", []))
    output_files = response.get("directoryContents") or []
    result = {
        "ok": True,
        "template": str(template_yaml),
        "log_line_count": len(log_lines),
        "log": log_lines,
        "output_file_count": len(output_files),
        "output": response.get("output"),
        "steps": response.get("steps"),
    }

    if args.json:
        print(json.dumps(result, indent=2 if _is_tty else None))
    else:
        print(f"Dry-run succeeded for {template_yaml}")
        print(f"Log lines: {len(log_lines)}")
        for line in log_lines[-10:]:
            print(f"  {line}")
        print(f"Output files: {len(output_files)}")
        if response.get("output"):
            print("Output:")
            print(json.dumps(response["output"], indent=2))

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
