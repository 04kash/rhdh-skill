#!/usr/bin/env python3
"""Shared HTTP helpers for RHDH Scaffolder v2 API calls.

Stdlib only per project ADR-0002.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT = 30


def auth_headers(token: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    resolved = token or os.environ.get("RHDH_TOKEN") or os.environ.get("BACKSTAGE_TOKEN")
    if resolved:
        headers["Authorization"] = f"Bearer {resolved}"
    return headers


def api_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[int, Any]:
    data = None
    headers = auth_headers(token)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return resp.status, None
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {"error": exc.reason}
        except json.JSONDecodeError:
            payload = {"error": raw or exc.reason}
        return exc.code, payload


def list_actions(base_url: str, *, token: str | None = None) -> list[dict[str, Any]]:
    status, payload = request_json(
        "GET",
        api_url(base_url, "/api/scaffolder/v2/actions"),
        token=token,
    )
    if status != 200:
        raise RuntimeError(f"list-actions failed ({status}): {payload}")
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected list-actions response: {payload!r}")
    return payload


def get_action_schema(
    base_url: str,
    action_id: str,
    *,
    token: str | None = None,
) -> dict[str, Any] | None:
    actions = list_actions(base_url, token=token)
    for action in actions:
        if action.get("id") == action_id:
            return action
    return None


def get_template_parameter_schema(
    base_url: str,
    template_ref: str,
    *,
    token: str | None = None,
) -> dict[str, Any]:
    """Fetch parameter schema for a catalog Template entity."""
    kind, namespace, name = parse_template_ref(template_ref)
    path = f"/api/scaffolder/v2/templates/{namespace}/{kind}/{name}/parameter-schema"
    status, payload = request_json("GET", api_url(base_url, path), token=token)
    if status != 200:
        raise RuntimeError(f"parameter-schema failed ({status}): {payload}")
    return payload


def parse_template_ref(template_ref: str) -> tuple[str, str, str]:
    """Parse template:namespace/name into (kind, namespace, name)."""
    ref = template_ref.strip()
    if ":" not in ref or "/" not in ref:
        raise ValueError(
            f"Invalid template ref {template_ref!r} — expected template:namespace/name"
        )
    kind_part, rest = ref.split(":", 1)
    namespace, name = rest.split("/", 1)
    return kind_part.lower(), namespace, name


def load_directory_contents(root: Path) -> list[dict[str, str]]:
    """Serialize a directory tree for Scaffolder dry-run API."""
    contents: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        contents.append(
            {
                "path": rel,
                "base64Content": base64.b64encode(raw).decode("ascii"),
            }
        )
    return contents


def dry_run(
    base_url: str,
    *,
    template: dict[str, Any],
    values: dict[str, Any],
    directory_contents: list[dict[str, str]],
    secrets: dict[str, str] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "template": template,
        "values": values,
        "directoryContents": directory_contents,
    }
    if secrets:
        body["secrets"] = secrets
    status, payload = request_json(
        "POST",
        api_url(base_url, "/api/scaffolder/v2/dry-run"),
        token=token,
        body=body,
    )
    if status != 200:
        raise RuntimeError(f"dry-run failed ({status}): {payload}")
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected dry-run response: {payload!r}")
    return payload
