#!/usr/bin/env python3
"""JSON Schema and structural validation for Software Template entities.

Provides stdlib structural checks (always available) and optional full JSON
Schema validation when jsonschema is installed.

Stdlib only per project ADR-0002 (optional jsonschema when installed).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PARAM_EXPR = re.compile(r"\$\{\{\s*parameters\.([a-zA-Z0-9_.]+)\s*\}\}")
STEP_OUTPUT_EXPR = re.compile(
    r"\$\{\{\s*steps(?:\[['\"]([^'\"]+)['\"]\]|\.([a-zA-Z0-9_-]+))\.output"
)
STEP_REF_BRACKET = re.compile(r"steps\[['\"]([^'\"]+)['\"]\]")
STEP_REF_DOT = re.compile(r"steps\.([a-zA-Z0-9_-]+)\.output")

VALID_PARAM_TYPES = frozenset(
    {"string", "number", "integer", "boolean", "array", "object", "null"}
)
RESERVED_PARAM_KEYS = frozenset(
    {
        "properties",
        "required",
        "dependencies",
        "oneOf",
        "allOf",
        "anyOf",
        "not",
        "if",
        "then",
        "else",
        "title",
        "description",
        "type",
        "enum",
        "const",
        "default",
        "items",
        "additionalProperties",
        "pattern",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "format",
        "ui:field",
        "ui:widget",
        "ui:options",
        "ui:help",
        "ui:autofocus",
        "ui:placeholder",
        "ui:disabled",
        "ui:readonly",
        "backstage:permissions",
    }
)


def _finding(
    check: str,
    severity: str,
    message: str,
    *,
    path: str = "",
    line: int = 0,
) -> dict:
    return {
        "check": check,
        "severity": severity,
        "message": message,
        "path": path,
        "line": line,
    }


def schema_path(skill_dir: Path) -> Path:
    return skill_dir / "references" / "schemas" / "template-v1beta3.schema.json"


def normalize_parameter_forms(parameters: Any) -> list[dict]:
    if parameters is None:
        return []
    if isinstance(parameters, dict):
        return [parameters]
    if isinstance(parameters, list):
        return [item for item in parameters if isinstance(item, dict)]
    return []


def collect_parameter_keys(parameters: Any) -> set[str]:
    keys: set[str] = set()
    for form in normalize_parameter_forms(parameters):
        props = form.get("properties")
        if isinstance(props, dict):
            keys.update(props.keys())
        required = form.get("required")
        if isinstance(required, list):
            keys.update(str(item) for item in required if isinstance(item, str))
    return keys


def validate_parameter_property(name: str, prop: Any, path: str) -> list[dict]:
    findings: list[dict] = []
    if not isinstance(prop, dict):
        findings.append(
            _finding(
                "json_schema",
                "critical",
                f"Parameter '{name}' must be an object",
                path=path,
            )
        )
        return findings

    prop_type = prop.get("type")
    if prop_type is not None:
        if isinstance(prop_type, str):
            if prop_type not in VALID_PARAM_TYPES:
                findings.append(
                    _finding(
                        "json_schema",
                        "warning",
                        f"Parameter '{name}' has unknown type '{prop_type}'",
                        path=f"{path}.type",
                    )
                )
        elif isinstance(prop_type, list):
            unknown = [t for t in prop_type if t not in VALID_PARAM_TYPES]
            if unknown:
                findings.append(
                    _finding(
                        "json_schema",
                        "warning",
                        f"Parameter '{name}' has unknown types: {', '.join(unknown)}",
                        path=f"{path}.type",
                    )
                )
        else:
            findings.append(
                _finding(
                    "json_schema",
                    "warning",
                    f"Parameter '{name}' type must be a string or list",
                    path=f"{path}.type",
                )
            )
    elif "enum" not in prop and "const" not in prop and "oneOf" not in prop:
        findings.append(
            _finding(
                "json_schema",
                "warning",
                f"Parameter '{name}' missing type (add type or enum)",
                path=path,
            )
        )

    if prop_type == "object" or (isinstance(prop_type, list) and "object" in prop_type):
        nested = prop.get("properties")
        if isinstance(nested, dict):
            for nested_name, nested_prop in nested.items():
                findings.extend(
                    validate_parameter_property(
                        f"{name}.{nested_name}",
                        nested_prop,
                        f"{path}.properties.{nested_name}",
                    )
                )

    if prop_type == "array" or (isinstance(prop_type, list) and "array" in prop_type):
        items = prop.get("items")
        if items is not None and not isinstance(items, dict):
            findings.append(
                _finding(
                    "json_schema",
                    "warning",
                    f"Parameter '{name}' array items must be an object schema",
                    path=f"{path}.items",
                )
            )

    return findings


def validate_parameter_forms(parameters: Any) -> list[dict]:
    findings: list[dict] = []
    forms = normalize_parameter_forms(parameters)
    if parameters is not None and not forms:
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "spec.parameters must be an object or array of form sections",
                path="spec.parameters",
            )
        )
        return findings

    for index, form in enumerate(forms):
        base = f"spec.parameters[{index}]"
        if not form.get("title"):
            findings.append(
                _finding(
                    "json_schema",
                    "warning",
                    "Parameter form section missing title",
                    path=f"{base}.title",
                )
            )
        props = form.get("properties")
        if props is None:
            findings.append(
                _finding(
                    "json_schema",
                    "warning",
                    "Parameter form section missing properties",
                    path=f"{base}.properties",
                )
            )
            continue
        if not isinstance(props, dict):
            findings.append(
                _finding(
                    "json_schema",
                    "critical",
                    "Parameter form properties must be an object",
                    path=f"{base}.properties",
                )
            )
            continue

        required = form.get("required", [])
        if required is not None and not isinstance(required, list):
            findings.append(
                _finding(
                    "json_schema",
                    "critical",
                    "Parameter form required must be an array",
                    path=f"{base}.required",
                )
            )
        elif isinstance(required, list):
            for req_key in required:
                if not isinstance(req_key, str):
                    continue
                if req_key not in props:
                    findings.append(
                        _finding(
                            "json_schema",
                            "critical",
                            f"Required parameter '{req_key}' is not defined in properties",
                            path=f"{base}.required",
                        )
                    )

        for name, prop in props.items():
            if name in RESERVED_PARAM_KEYS:
                continue
            findings.extend(
                validate_parameter_property(name, prop, f"{base}.properties.{name}")
            )

    return findings


def validate_steps(steps: Any) -> list[dict]:
    findings: list[dict] = []
    if not isinstance(steps, list):
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "spec.steps must be an array",
                path="spec.steps",
            )
        )
        return findings
    if not steps:
        findings.append(
            _finding(
                "json_schema",
                "warning",
                "spec.steps is empty",
                path="spec.steps",
            )
        )

    seen_ids: set[str] = set()
    for index, step in enumerate(steps):
        path = f"spec.steps[{index}]"
        if not isinstance(step, dict):
            findings.append(
                _finding(
                    "json_schema",
                    "critical",
                    "Each step must be an object",
                    path=path,
                )
            )
            continue

        step_id = step.get("id")
        if step_id is not None:
            if not isinstance(step_id, str) or not step_id.strip():
                findings.append(
                    _finding(
                        "json_schema",
                        "critical",
                        "Step id must be a non-empty string",
                        path=f"{path}.id",
                    )
                )
            elif step_id in seen_ids:
                findings.append(
                    _finding(
                        "json_schema",
                        "critical",
                        f"Duplicate step id '{step_id}'",
                        path=f"{path}.id",
                    )
                )
            else:
                seen_ids.add(step_id)

        action = step.get("action")
        if not action:
            findings.append(
                _finding(
                    "json_schema",
                    "critical",
                    "Step missing required action",
                    path=f"{path}.action",
                )
            )
        elif not isinstance(action, str) or ":" not in action:
            findings.append(
                _finding(
                    "json_schema",
                    "critical",
                    f"Step action '{action}' must use namespace:actionName format",
                    path=f"{path}.action",
                )
            )

        step_input = step.get("input")
        if step_input is not None and not isinstance(step_input, dict):
            findings.append(
                _finding(
                    "json_schema",
                    "critical",
                    "Step input must be an object",
                    path=f"{path}.input",
                )
            )

    return findings


def validate_output(output: Any) -> list[dict]:
    findings: list[dict] = []
    if output is None:
        return findings
    if not isinstance(output, dict):
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "spec.output must be an object",
                path="spec.output",
            )
        )
        return findings

    links = output.get("links")
    if links is not None:
        if not isinstance(links, list):
            findings.append(
                _finding(
                    "json_schema",
                    "critical",
                    "spec.output.links must be an array",
                    path="spec.output.links",
                )
            )
        else:
            for index, link in enumerate(links):
                path = f"spec.output.links[{index}]"
                if not isinstance(link, dict):
                    findings.append(
                        _finding(
                            "json_schema",
                            "critical",
                            "Output link must be an object",
                            path=path,
                        )
                    )
                    continue
                if not any(link.get(key) for key in ("title", "url", "entityRef")):
                    findings.append(
                        _finding(
                            "json_schema",
                            "warning",
                            "Output link should include title, url, or entityRef",
                            path=path,
                        )
                    )

    return findings


def _extract_param_refs_from_value(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, str):
        for match in PARAM_EXPR.finditer(value):
            refs.add(match.group(1).split(".")[0])
    elif isinstance(value, dict):
        for nested in value.values():
            refs.update(_extract_param_refs_from_value(nested))
    elif isinstance(value, list):
        for nested in value:
            refs.update(_extract_param_refs_from_value(nested))
    return refs


def _extract_step_refs_from_value(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, str):
        for match in STEP_OUTPUT_EXPR.finditer(value):
            step_id = match.group(1) or match.group(2)
            if step_id:
                refs.add(step_id)
        for match in STEP_REF_BRACKET.finditer(value):
            refs.add(match.group(1))
        for match in STEP_REF_DOT.finditer(value):
            refs.add(match.group(1))
    elif isinstance(value, dict):
        for nested in value.values():
            refs.update(_extract_step_refs_from_value(nested))
    elif isinstance(value, list):
        for nested in value:
            refs.update(_extract_step_refs_from_value(nested))
    return refs


def validate_cross_references(data: dict) -> list[dict]:
    findings: list[dict] = []
    spec = data.get("spec")
    if not isinstance(spec, dict):
        return findings

    param_keys = collect_parameter_keys(spec.get("parameters"))
    steps = spec.get("steps")
    if not isinstance(steps, list):
        return findings

    step_ids = {
        step.get("id")
        for step in steps
        if isinstance(step, dict) and isinstance(step.get("id"), str)
    }

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        path = f"spec.steps[{index}]"
        for ref in _extract_param_refs_from_value(step.get("input")):
            if param_keys and ref not in param_keys:
                findings.append(
                    _finding(
                        "json_schema",
                        "warning",
                        f"Step references unknown parameter '{ref}'",
                        path=path,
                    )
                )

    for ref in _extract_step_refs_from_value(spec.get("output")):
        if step_ids and ref not in step_ids:
            findings.append(
                _finding(
                    "json_schema",
                    "warning",
                    f"Output references unknown step id '{ref}'",
                    path="spec.output",
                )
            )

    return findings


def validate_metadata(data: dict) -> list[dict]:
    findings: list[dict] = []
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "metadata must be an object",
                path="metadata",
            )
        )
        return findings

    name = metadata.get("name")
    if not name:
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "metadata.name is required",
                path="metadata.name",
            )
        )
    elif not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        findings.append(
            _finding(
                "json_schema",
                "warning",
                "metadata.name should be lowercase alphanumeric with hyphens",
                path="metadata.name",
            )
        )

    tags = metadata.get("tags")
    if tags is not None and not isinstance(tags, list):
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "metadata.tags must be an array",
                path="metadata.tags",
            )
        )

    return findings


def validate_spec_root(data: dict) -> list[dict]:
    findings: list[dict] = []
    spec = data.get("spec")
    if not isinstance(spec, dict):
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "spec must be an object",
                path="spec",
            )
        )
        return findings

    template_type = spec.get("type")
    if not template_type:
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "spec.type is required",
                path="spec.type",
            )
        )
    elif not isinstance(template_type, str) or not template_type.strip():
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "spec.type must be a non-empty string",
                path="spec.type",
            )
        )

    findings.extend(validate_parameter_forms(spec.get("parameters")))
    findings.extend(validate_steps(spec.get("steps")))
    findings.extend(validate_output(spec.get("output")))
    findings.extend(validate_cross_references(data))
    return findings


def validate_structural(data: dict) -> list[dict]:
    """Always-available structural and JSON Schema subset validation."""
    findings: list[dict] = []
    if data.get("apiVersion") != "scaffolder.backstage.io/v1beta3":
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "apiVersion must be scaffolder.backstage.io/v1beta3",
                path="apiVersion",
            )
        )
    if data.get("kind") != "Template":
        findings.append(
            _finding(
                "json_schema",
                "critical",
                "kind must be Template",
                path="kind",
            )
        )
    findings.extend(validate_metadata(data))
    findings.extend(validate_spec_root(data))
    return findings


def validate_with_jsonschema(data: dict, skill_dir: Path) -> tuple[list[dict], str | None]:
    """Optional full JSON Schema validation when jsonschema is installed."""
    try:
        import jsonschema  # type: ignore[import-untyped]
    except ImportError:
        return [], "jsonschema not installed — structural checks only"

    schema_file = schema_path(skill_dir)
    if not schema_file.is_file():
        return [
            _finding(
                "json_schema",
                "info",
                f"Bundled schema not found at {schema_file}",
            )
        ], None

    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    findings: list[dict] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(part) for part in error.path) or "(root)"
        findings.append(
            _finding(
                "json_schema",
                "critical",
                error.message,
                path=path,
            )
        )
    return findings, None


def run_schema_validation(data: dict, skill_dir: Path, *, use_jsonschema: bool = True) -> dict:
    """Run structural validation and optional jsonschema validation."""
    structural = validate_structural(data)
    jsonschema_findings: list[dict] = []
    note: str | None = None

    if use_jsonschema:
        jsonschema_findings, note = validate_with_jsonschema(data, skill_dir)

    # Structural checks are more specific for cross-refs; prefer them over duplicate
    # jsonschema messages for the same paths when both fire.
    combined = structural + jsonschema_findings
    return {
        "findings": combined,
        "structural_count": len(structural),
        "jsonschema_count": len(jsonschema_findings),
        "note": note,
    }
