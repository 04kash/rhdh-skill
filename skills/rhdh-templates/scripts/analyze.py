#!/usr/bin/env python3
"""Analyze a source codebase for Software Template templatize workflow.

Detects project type, candidate literals for parameterization, and files
that likely need {% raw %} blocks or copyWithoutTemplating.

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
EXIT_USAGE = 2

_no_color = os.environ.get("NO_COLOR") is not None
_is_tty = sys.stderr.isatty() and not _no_color

TEXT_EXTENSIONS = {
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".xml",
    ".properties",
    ".env",
    ".txt",
    ".gradle",
    ".kts",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".bash",
    ".Dockerfile",
}
TEXT_FILENAMES = {
    "Dockerfile",
    "Makefile",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "go.mod",
    "catalog-info.yaml",
    "package.json",
    "pyproject.toml",
    "Chart.yaml",
}

PROJECT_MARKERS = [
    ("nodejs", ["package.json"]),
    ("java-maven", ["pom.xml"]),
    ("java-gradle", ["build.gradle", "build.gradle.kts"]),
    ("python", ["pyproject.toml", "setup.py", "requirements.txt"]),
    ("go", ["go.mod"]),
    ("dotnet", ["*.csproj"]),
    ("helm", ["Chart.yaml"]),
    ("quarkus", ["pom.xml", ".quarkus"]),
    ("spring-boot", ["pom.xml", "src/main/resources/application.properties"]),
    ("kubernetes", ["k8s", "kubernetes", "deploy", "manifests"]),
]

GITHUB_URL = re.compile(r"github\.com[/:]([\w.-]+)/([\w.-]+)")
GITLAB_URL = re.compile(r"gitlab\.(?:com|[^/]+)[/:]([\w.-]+)/([\w.-]+)")
K8S_NAME = re.compile(r"^\s*name:\s*['\"]?([\w.-]+)['\"]?\s*$", re.MULTILINE)
K8S_NAMESPACE = re.compile(r"^\s*namespace:\s*['\"]?([\w.-]+)['\"]?\s*$", re.MULTILINE)
PORT = re.compile(r"\b(?:port|PORT)\s*[=:]\s*(\d{2,5})\b")


def _read_text(path: Path, max_bytes: int = 256_000) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > max_bytes:
        data = data[:max_bytes]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _is_text_candidate(path: Path) -> bool:
    if path.name in TEXT_FILENAMES:
        return True
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return False


def detect_project_types(root: Path) -> list[str]:
    found: list[str] = []
    names = {p.name for p in root.rglob("*") if p.is_file()}
    rel_dirs = {p.relative_to(root).parts[0] for p in root.rglob("*") if p.is_dir() and p != root}

    for project_type, markers in PROJECT_MARKERS:
        for marker in markers:
            if marker.startswith("*"):
                if any(n.endswith(marker[1:]) for n in names):
                    found.append(project_type)
                    break
            elif marker in names:
                found.append(project_type)
                break
            elif marker in rel_dirs:
                found.append(project_type)
                break
    return sorted(set(found))


def find_workflow_files(root: Path) -> list[dict]:
    results = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if ".github/workflows" not in rel:
            continue
        text = _read_text(path)
        if text is None:
            continue
        needs_raw = "{{" in text and "{% raw %}" not in text
        results.append(
            {
                "path": rel,
                "needs_raw_block": needs_raw,
                "reason": "Contains '{{' without {% raw %} wrapper" if needs_raw else None,
            }
        )
    return results


def _add_candidate(
    candidates: dict[str, dict],
    value: str,
    *,
    category: str,
    source: str,
    usually_parameterize: str = "maybe",
) -> None:
    value = value.strip().strip("'\"")
    if not value or len(value) < 2:
        return
    if value in {".", "..", "main", "master", "true", "false", "null"}:
        return
    key = value.lower()
    if key not in candidates:
        candidates[key] = {
            "value": value,
            "category": category,
            "sources": [source],
            "usually_parameterize": usually_parameterize,
        }
    elif source not in candidates[key]["sources"]:
        candidates[key]["sources"].append(source)


def extract_from_package_json(path: Path, rel: str, candidates: dict[str, dict]) -> None:
    text = _read_text(path)
    if not text:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return
    if isinstance(data.get("name"), str):
        _add_candidate(
            candidates, data["name"], category="name", source=rel, usually_parameterize="yes"
        )
    if isinstance(data.get("description"), str) and len(data["description"]) < 120:
        _add_candidate(
            candidates,
            data["description"],
            category="description",
            source=rel,
            usually_parameterize="sometimes",
        )


def extract_from_catalog_info(path: Path, rel: str, candidates: dict[str, dict]) -> None:
    text = _read_text(path)
    if not text:
        return
    for match in re.finditer(r"^\s*name:\s*['\"]?([\w.-]+)['\"]?\s*$", text, re.MULTILINE):
        _add_candidate(
            candidates, match.group(1), category="name", source=rel, usually_parameterize="yes"
        )
    for match in re.finditer(r"^\s*owner:\s*['\"]?([\w:./-]+)['\"]?\s*$", text, re.MULTILINE):
        _add_candidate(
            candidates, match.group(1), category="owner", source=rel, usually_parameterize="yes"
        )


def extract_from_pom(path: Path, rel: str, candidates: dict[str, dict]) -> None:
    text = _read_text(path)
    if not text:
        return
    for tag in ("artifactId", "groupId", "name"):
        for match in re.finditer(rf"<{tag}>([^<]+)</{tag}>", text):
            cat = "name" if tag != "groupId" else "org"
            usually = "yes" if tag in {"artifactId", "name"} else "often"
            _add_candidate(
                candidates, match.group(1), category=cat, source=rel, usually_parameterize=usually
            )


def extract_urls(text: str, rel: str, candidates: dict[str, dict]) -> None:
    for match in GITHUB_URL.finditer(text):
        org, repo = match.group(1), match.group(2).removesuffix(".git")
        _add_candidate(candidates, org, category="org", source=rel, usually_parameterize="yes")
        _add_candidate(candidates, repo, category="name", source=rel, usually_parameterize="yes")
    for match in GITLAB_URL.finditer(text):
        org, repo = match.group(1), match.group(2).removesuffix(".git")
        _add_candidate(candidates, org, category="org", source=rel, usually_parameterize="yes")
        _add_candidate(candidates, repo, category="name", source=rel, usually_parameterize="yes")


def scan_candidates(root: Path) -> list[dict]:
    candidates: dict[str, dict] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.name == "package.json":
            extract_from_package_json(path, rel, candidates)
        elif path.name == "catalog-info.yaml":
            extract_from_catalog_info(path, rel, candidates)
        elif path.name == "pom.xml":
            extract_from_pom(path, rel, candidates)
        if not _is_text_candidate(path):
            continue
        text = _read_text(path)
        if not text:
            continue
        extract_urls(text, rel, candidates)
        for match in K8S_NAME.finditer(text):
            _add_candidate(
                candidates,
                match.group(1),
                category="name",
                source=rel,
                usually_parameterize="often",
            )
        for match in K8S_NAMESPACE.finditer(text):
            _add_candidate(
                candidates,
                match.group(1),
                category="namespace",
                source=rel,
                usually_parameterize="often",
            )
        for match in PORT.finditer(text):
            _add_candidate(
                candidates,
                match.group(1),
                category="port",
                source=rel,
                usually_parameterize="sometimes",
            )
    rows = list(candidates.values())
    rows.sort(key=lambda r: (r["usually_parameterize"] != "yes", r["category"], r["value"]))
    return rows


def analyze(root: Path) -> dict:
    project_types = detect_project_types(root)
    workflows = find_workflow_files(root)
    candidates = scan_candidates(root)
    return {
        "ok": True,
        "path": str(root),
        "project_types": project_types or ["unknown"],
        "file_count": sum(1 for p in root.rglob("*") if p.is_file()),
        "workflow_files": workflows,
        "candidate_literals": candidates,
        "candidate_count": len(candidates),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a codebase for RHDH Software Template templatize workflow.",
    )
    parser.add_argument("source", type=Path, nargs="?", help="Source directory to analyze")
    parser.add_argument("--path", type=Path, help="Alias for source directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    source = args.path or args.source
    if source is None:
        parser.print_help()
        return EXIT_USAGE

    root = source.resolve()
    if not root.exists() or not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return EXIT_USAGE

    result = analyze(root)

    if args.json:
        print(json.dumps(result, indent=2 if _is_tty else None))
    else:
        print(f"Source: {root}")
        print(f"Project types: {', '.join(result['project_types'])}")
        print(f"Files: {result['file_count']}")
        print(f"Candidate literals: {result['candidate_count']}")
        for row in result["candidate_literals"][:20]:
            print(
                f"  [{row['category']}] {row['value']} "
                f"({row['usually_parameterize']}) — {', '.join(row['sources'][:2])}"
            )
        if result["workflow_files"]:
            print("Workflow files:")
            for wf in result["workflow_files"]:
                flag = "needs raw" if wf["needs_raw_block"] else "ok"
                print(f"  {wf['path']}: {flag}")

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
