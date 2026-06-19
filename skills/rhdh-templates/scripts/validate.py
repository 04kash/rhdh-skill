#!/usr/bin/env python3
"""Local validation for RHDH Software Templates.

Combines YAML structure checks, gotcha rules from fix_gotchas.py, JSON Schema
validation (structural subset always; bundled schema when jsonschema is installed), optional
location.yaml verification, and optional djLint for skeleton Nunjucks files.

Stdlib only per project ADR-0002 (optional PyYAML and djlint when installed).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from fix_gotchas import load_rules, resolve_template_path, run_checks  # noqa: E402
from schema_validate import run_schema_validation  # noqa: E402


def _c(code: str, text: str) -> str:
    return f"{code}{text}\033[0m" if _is_tty else text


def green(t: str) -> str:
    return _c("\033[0;32m", t)


def red(t: str) -> str:
    return _c("\033[0;31m", t)


def yellow(t: str) -> str:
    return _c("\033[1;33m", t)


def load_yaml(text: str) -> tuple[dict | None, str | None]:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None, "PyYAML not installed — skipping YAML syntax parse (gotcha checks still run)"
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, f"YAML syntax error: {exc}"
    if not isinstance(data, dict):
        return None, "template.yaml root must be a mapping"
    return data, None


def check_yaml_structure(data: dict) -> list[dict]:
    findings: list[dict] = []
    if data.get("kind") != "Template":
        findings.append(
            {
                "check": "yaml_structure",
                "severity": "critical",
                "message": f"Expected kind: Template, got {data.get('kind')!r}",
            }
        )
    api = data.get("apiVersion", "")
    if api != "scaffolder.backstage.io/v1beta3":
        findings.append(
            {
                "check": "yaml_structure",
                "severity": "critical",
                "message": f"Expected apiVersion scaffolder.backstage.io/v1beta3, got {api!r}",
            }
        )
    spec = data.get("spec")
    if not isinstance(spec, dict):
        findings.append(
            {
                "check": "yaml_structure",
                "severity": "critical",
                "message": "Missing or invalid spec section",
            }
        )
        return findings
    if "parameters" not in spec:
        findings.append(
            {
                "check": "yaml_structure",
                "severity": "warning",
                "message": "spec.parameters is missing",
            }
        )
    if "steps" not in spec:
        findings.append(
            {
                "check": "yaml_structure",
                "severity": "warning",
                "message": "spec.steps is missing",
            }
        )
    elif isinstance(spec.get("steps"), list) and len(spec["steps"]) == 0:
        findings.append(
            {
                "check": "yaml_structure",
                "severity": "warning",
                "message": "spec.steps is empty",
            }
        )
    metadata = data.get("metadata")
    if not isinstance(metadata, dict) or not metadata.get("name"):
        findings.append(
            {
                "check": "yaml_structure",
                "severity": "critical",
                "message": "metadata.name is required",
            }
        )
    return findings


def check_location_yaml(repo_root: Path) -> list[dict]:
    findings: list[dict] = []
    location = repo_root / "location.yaml"
    if not location.is_file():
        findings.append(
            {
                "check": "location",
                "severity": "warning",
                "message": "Root location.yaml not found",
            }
        )
        return findings
    text = location.read_text(encoding="utf-8")
    if "kind: Location" not in text:
        findings.append(
            {
                "check": "location",
                "severity": "critical",
                "message": "location.yaml missing kind: Location",
            }
        )
    if "templates/**/template.yaml" not in text and "targets:" not in text:
        findings.append(
            {
                "check": "location",
                "severity": "warning",
                "message": "location.yaml may not register template.yaml files",
            }
        )
    return findings


def run_djlint(skeleton_dir: Path) -> list[dict]:
    import shutil

    if not shutil.which("djlint"):
        return [
            {
                "check": "nunjucks_lint",
                "severity": "info",
                "message": "djlint not installed — skipping Nunjucks lint",
            }
        ]
    cmd = [
        "djlint",
        str(skeleton_dir),
        "--profile=jinja",
        "--lint",
        "--quiet",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as exc:
        return [
            {
                "check": "nunjucks_lint",
                "severity": "info",
                "message": f"djlint skipped: {exc}",
            }
        ]
    if proc.returncode == 0:
        return []
    findings: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        findings.append(
            {
                "check": "nunjucks_lint",
                "severity": "warning",
                "message": line,
            }
        )
    if not findings:
        findings.append(
            {
                "check": "nunjucks_lint",
                "severity": "warning",
                "message": proc.stderr.strip() or "djlint reported issues",
            }
        )
    return findings


def validate_template(path: Path, *, check_repo: bool, lint_skeleton: bool, use_jsonschema: bool = True) -> dict:
    template_path = resolve_template_path(path)
    content = template_path.read_text(encoding="utf-8")
    template_dir = template_path.parent
    repo_root = template_dir.parent.parent if template_dir.parent.name == "templates" else template_dir

    findings: list[dict] = []

    parsed, yaml_note = load_yaml(content)
    if yaml_note and parsed is None and yaml_note.startswith("YAML syntax"):
        findings.append({"check": "yaml_syntax", "severity": "critical", "message": yaml_note})
    elif parsed is not None:
        findings.extend(check_yaml_structure(parsed))
        schema_result = run_schema_validation(parsed, SKILL_DIR, use_jsonschema=use_jsonschema)
        for item in schema_result["findings"]:
            findings.append(
                {
                    "check": item["check"],
                    "severity": item["severity"],
                    "message": item["message"],
                    "path": item.get("path", ""),
                }
            )
        if schema_result.get("note"):
            findings.append(
                {
                    "check": "json_schema",
                    "severity": "info",
                    "message": schema_result["note"],
                }
            )
    elif yaml_note:
        findings.append({"check": "yaml_syntax", "severity": "info", "message": yaml_note})

    rules = load_rules(SKILL_DIR)
    for item in run_checks(content, template_path, rules):
        findings.append(
            {
                "check": item.get("rule_id", "gotcha"),
                "severity": item["severity"],
                "message": item.get("message") or item.get("description", ""),
                "line": item.get("line", 0),
            }
        )

    if check_repo:
        findings.extend(check_location_yaml(repo_root))

    skeleton = template_dir / "skeleton"
    if lint_skeleton and skeleton.is_dir():
        findings.extend(run_djlint(skeleton))

    critical = [f for f in findings if f["severity"] == "critical"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    return {
        "ok": len(critical) == 0,
        "template": str(template_path),
        "finding_count": len(findings),
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate RHDH Software Template locally.")
    parser.add_argument("--path", required=True, type=Path, help="template.yaml or template directory")
    parser.add_argument(
        "--repo",
        action="store_true",
        help="Also validate root location.yaml for the template repo",
    )
    parser.add_argument(
        "--lint-skeleton",
        action="store_true",
        help="Run djlint on skeleton/ when djlint is installed",
    )
    parser.add_argument(
        "--no-json-schema",
        action="store_true",
        help="Skip optional full JSON Schema validation (structural checks still run)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    try:
        result = validate_template(
            args.path,
            check_repo=args.repo,
            lint_skeleton=args.lint_skeleton,
            use_jsonschema=not args.no_json_schema,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        print(json.dumps(result, indent=2 if _is_tty else None))
    else:
        status = green("PASS") if result["ok"] else red("FAIL")
        print(f"Validation: {status}")
        print(f"Template: {result['template']}")
        print(
            f"Findings: {result['finding_count']} "
            f"({result['critical_count']} critical, {result['warning_count']} warnings)"
        )
        for finding in result["findings"]:
            sev = finding["severity"].upper()
            line = finding.get("line", 0)
            loc = f"line {line}: " if line else ""
            color = red if finding["severity"] == "critical" else yellow
            print(f"  {color(f'[{sev}]')} {loc}{finding['message']}")

    return EXIT_SUCCESS if result["ok"] else EXIT_FINDINGS


if __name__ == "__main__":
    sys.exit(main())
