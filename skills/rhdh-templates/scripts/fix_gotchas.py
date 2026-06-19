#!/usr/bin/env python3
"""Check and fix common RHDH Software Template gotchas.

Loads rules from references/gotchas-rules.json adjacent to the skill root.

Stdlib only per project ADR-0002.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color

TOKEN_PATTERNS = [
    re.compile(r"(?i)(ghp_[a-zA-Z0-9]{20,})"),
    re.compile(r"(?i)(github_pat_[a-zA-Z0-9_]{20,})"),
    re.compile(r"(?i)(glpat-[a-zA-Z0-9\-]{20,})"),
    re.compile(r"(?i)token:\s*['\"]?[a-zA-Z0-9_\-]{24,}"),
]

ACTION_PATTERN = re.compile(r"^\s*action:\s*([a-zA-Z]+:[a-zA-Z][a-zA-Z0-9]*)", re.MULTILINE)
V1BETA2_EXPR = re.compile(r"(?<!\$)\{\{\s*parameters\.")
API_VERSION_PATTERN = re.compile(r"^apiVersion:\s*(.+)$", re.MULTILINE)


def load_rules(skill_dir: Path) -> list[dict]:
    rules_path = skill_dir / "references" / "gotchas-rules.json"
    data = json.loads(rules_path.read_text(encoding="utf-8"))
    return data.get("rules", [])


def resolve_template_path(path: Path) -> Path:
    path = path.resolve()
    if path.is_file():
        return path
    if path.is_dir():
        candidate = path / "template.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No template.yaml at {path}")


def check_api_version(content: str) -> list[dict]:
    findings = []
    match = API_VERSION_PATTERN.search(content)
    if not match:
        findings.append({"line": 0, "message": "Missing apiVersion field"})
    elif "scaffolder.backstage.io/v1beta3" not in match.group(1):
        findings.append({"line": 0, "message": f"Unexpected apiVersion: {match.group(1).strip()}"})
    return findings


def fix_api_version(content: str) -> str:
    if API_VERSION_PATTERN.search(content):
        return API_VERSION_PATTERN.sub(
            "apiVersion: scaffolder.backstage.io/v1beta3", content, count=1
        )
    return "apiVersion: scaffolder.backstage.io/v1beta3\n" + content


def check_action_casing(content: str) -> list[dict]:
    findings = []
    for match in ACTION_PATTERN.finditer(content):
        action = match.group(1)
        if ":" not in action:
            continue
        ns, name = action.split(":", 1)
        if name != name.lower() and any(c.isupper() for c in name):
            line = content[: match.start()].count("\n") + 1
            findings.append(
                {
                    "line": line,
                    "message": f"Action '{action}' may use wrong casing — expected camelCase segment",
                    "action": action,
                }
            )
    return findings


def fix_action_casing(content: str) -> str:
    def repl(m: re.Match) -> str:
        action = m.group(1)
        if ":" not in action:
            return m.group(0)
        ns, name = action.split(":", 1)
        if not name:
            return m.group(0)
        if name != name.lower():
            # Backstage/RHDH built-in actions use lowercase segments (publish:github).
            fixed = f"{ns}:{name.lower()}"
        else:
            fixed = action
        return f"action: {fixed}"

    return ACTION_PATTERN.sub(repl, content)


def check_v1beta2_expressions(content: str) -> list[dict]:
    findings = []
    for match in V1BETA2_EXPR.finditer(content):
        line = content[: match.start()].count("\n") + 1
        findings.append(
            {
                "line": line,
                "message": "v1beta2 expression '{{ parameters.' in v1beta3 template",
            }
        )
        break
    return findings


def convert_expressions(content: str) -> str:
    return re.sub(
        r"\{\{\s*parameters\.([^}]+)\}\}",
        r"${{ parameters.\1 }}",
        content,
    )


def check_hardcoded_secrets(content: str) -> list[dict]:
    findings = []
    for i, line in enumerate(content.splitlines(), start=1):
        for pattern in TOKEN_PATTERNS:
            if pattern.search(line) and "secrets." not in line:
                findings.append({"line": i, "message": "Possible hardcoded token in step input"})
                break
    return findings


def check_missing_section(content: str, section: str) -> list[dict]:
    if re.search(rf"^  {section}:", content, re.MULTILINE):
        return []
    return [{"line": 0, "message": f"Missing spec.{section} section"}]


def check_fetch_template_values(content: str) -> list[dict]:
    findings = []
    blocks = re.split(r"\n\s*-\s+id:", content)
    for block in blocks:
        if "action: fetch:template" not in block:
            continue
        if "values:" not in block:
            findings.append({"line": 0, "message": "fetch:template step missing values map"})
    return findings


def check_skeleton_parameters(template_path: Path) -> list[dict]:
    findings = []
    skeleton = template_path.parent / "skeleton"
    if not skeleton.is_dir():
        return findings
    for file in skeleton.rglob("*"):
        if not file.is_file():
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "parameters." in text and "values." not in text:
            findings.append(
                {
                    "line": 0,
                    "message": f"Skeleton file {file.relative_to(template_path.parent)} may use parameters.* instead of values.*",
                }
            )
    return findings


def check_workflow_raw_blocks(template_path: Path) -> list[dict]:
    findings = []
    skeleton = template_path.parent / "skeleton"
    if not skeleton.is_dir():
        return findings
    for wf in skeleton.rglob(".github/workflows/*"):
        if not wf.is_file():
            continue
        try:
            text = wf.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "{{" in text and "{% raw %}" not in text:
            findings.append(
                {
                    "line": 0,
                    "message": f"Workflow {wf.relative_to(template_path.parent)} contains '{{' without raw block",
                }
            )
    return findings


SENSITIVE_PARAM_NAMES = re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key|auth[_-]?token|access[_-]?token|token)"
)


def check_metadata_tags(content: str) -> list[dict]:
    if re.search(r"^\s*tags:\s*\n\s*-\s+", content, re.MULTILINE):
        return []
    if re.search(r"^\s*tags:\s*\[.+\]", content, re.MULTILINE):
        return []
    return [{"line": 0, "message": "metadata.tags is missing — add tags for Create UI filtering"}]


def check_sensitive_param_secret_field(content: str) -> list[dict]:
    """Flag password/token-like parameter keys without ui:field: Secret."""
    findings = []
    # Focus on spec.parameters section only
    spec_match = re.search(r"^spec:\s*\n(.*)", content, re.MULTILINE | re.DOTALL)
    if not spec_match:
        return findings
    params_section = spec_match.group(1)
    if "parameters:" not in params_section:
        return findings

    skip_keys = {"properties", "title", "required", "dependencies", "oneOf", "allOf", "enum"}
    lines = params_section.splitlines()
    i = 0
    while i < len(lines):
        key_match = re.match(r"^\s{8,}([a-zA-Z][a-zA-Z0-9]*):\s*$", lines[i])
        if key_match:
            key = key_match.group(1)
            if key not in skip_keys and SENSITIVE_PARAM_NAMES.search(key):
                block_end = min(i + 12, len(lines))
                block = "\n".join(lines[i:block_end])
                if "ui:field: Secret" not in block:
                    findings.append(
                        {
                            "line": 0,
                            "message": f"Parameter '{key}' looks sensitive — use ui:field: Secret",
                        }
                    )
        i += 1
    return findings


def check_template_docs(content: str, template_path: Path) -> list[dict]:
    if "backstage.io/techdocs-ref" in content:
        return []
    readme = template_path.parent / "README.md"
    if readme.is_file():
        return []
    return [
        {
            "line": 0,
            "message": "No README.md or backstage.io/techdocs-ref annotation — add template documentation",
        }
    ]


CHECKERS = {
    "api_version": lambda c, p: check_api_version(c),
    "action_pascal_case": lambda c, p: check_action_casing(c),
    "v1beta2_expression_syntax": lambda c, p: check_v1beta2_expressions(c),
    "hardcoded_secret": lambda c, p: check_hardcoded_secrets(c),
    "missing_parameters": lambda c, p: check_missing_section(c, "parameters"),
    "missing_steps": lambda c, p: check_missing_section(c, "steps"),
    "fetch_template_values": lambda c, p: check_fetch_template_values(c),
    "workflow_raw_blocks": lambda c, p: check_workflow_raw_blocks(p),
    "skeleton_parameters_ref": lambda c, p: check_skeleton_parameters(p),
    "metadata_tags": lambda c, p: check_metadata_tags(c),
    "sensitive_param_secret_field": lambda c, p: check_sensitive_param_secret_field(c),
    "template_docs": lambda c, p: check_template_docs(c, p),
}

FIXERS = {
    "set_api_version_v1beta3": fix_api_version,
    "lowercase_action_segment": fix_action_casing,
    "convert_to_v1beta3_expressions": convert_expressions,
}


def run_checks(content: str, template_path: Path, rules: list[dict]) -> list[dict]:
    results = []
    for rule in rules:
        checker = CHECKERS.get(rule.get("check", ""))
        if not checker:
            continue
        for finding in checker(content, template_path):
            results.append(
                {
                    "rule_id": rule["id"],
                    "severity": rule["severity"],
                    "description": rule["description"],
                    **finding,
                }
            )
    return results


def apply_fixes(content: str, rules: list[dict]) -> str:
    updated = content
    for rule in rules:
        fix_name = rule.get("fix")
        if not fix_name:
            continue
        fixer = FIXERS.get(fix_name)
        if fixer:
            updated = fixer(updated)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Check and fix RHDH template gotchas.")
    parser.add_argument(
        "--path", required=True, type=Path, help="template.yaml or template directory"
    )
    parser.add_argument("--apply", action="store_true", help="Apply automatic fixes")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    try:
        template_path = resolve_template_path(args.path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    rules = load_rules(skill_dir)
    original = template_path.read_text(encoding="utf-8")
    findings = run_checks(original, template_path, rules)

    updated = original
    if args.apply:
        updated = apply_fixes(original, rules)
        if updated != original:
            template_path.write_text(updated, encoding="utf-8")
        findings = run_checks(updated, template_path, rules)

    critical = [f for f in findings if f["severity"] == "critical"]
    result = {
        "ok": len(critical) == 0,
        "template": str(template_path),
        "finding_count": len(findings),
        "critical_count": len(critical),
        "findings": findings,
        "applied": args.apply and updated != original,
    }

    if args.json:
        print(json.dumps(result, indent=2 if _is_tty else None))
    else:
        print(f"Template: {template_path}")
        print(f"Findings: {len(findings)} ({len(critical)} critical)")
        for f in findings:
            sev = f["severity"].upper()
            line = f.get("line", 0)
            loc = f"line {line}: " if line else ""
            print(f"  [{sev}] {loc}{f['message']}")
        if args.apply and updated != original:
            print("Applied automatic fixes.")

    return EXIT_SUCCESS if len(critical) == 0 else EXIT_FINDINGS


if __name__ == "__main__":
    sys.exit(main())
