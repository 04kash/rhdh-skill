#!/usr/bin/env python3
"""List curated RHDH Software Template reference examples.

Reads the bundled example catalog and filters or ranks entries for authoring
workflows. Stdlib only per project ADR-0002.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_USAGE = 2

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = SKILL_DIR / "assets" / "example-catalog.json"
BUNDLED_EXAMPLES_DIR = "assets/examples"


def load_catalog(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Catalog not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def source_map(catalog: dict) -> dict[str, dict]:
    return {item["id"]: item for item in catalog.get("sources", [])}


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def example_blob(example: dict) -> str:
    parts = [
        example.get("id", ""),
        example.get("title", ""),
        example.get("category", ""),
        " ".join(example.get("tags", [])),
        " ".join(example.get("stack", [])),
        " ".join(example.get("use_cases", [])),
    ]
    return " ".join(parts).lower()


def score_example(example: dict, query_tokens: list[str]) -> int:
    if not query_tokens:
        return 0
    blob = example_blob(example)
    score = 0
    for token in query_tokens:
        if token in blob:
            score += 2
        for part in blob.split():
            if token in part or part in token:
                score += 1
    if example.get("recommended"):
        score += 1
    return score


def filter_examples(
    catalog: dict,
    *,
    category: str | None = None,
    tag: str | None = None,
    stack: str | None = None,
    recommended: bool = False,
    local_only: bool = False,
    official_only: bool = False,
    query: str | None = None,
    match: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    examples = list(catalog.get("examples", []))
    sources = source_map(catalog)

    if category:
        examples = [e for e in examples if e.get("category") == category]
    if tag:
        examples = [e for e in examples if tag in e.get("tags", [])]
    if stack:
        examples = [
            e for e in examples if stack in e.get("stack", []) or stack in e.get("tags", [])
        ]
    if recommended:
        examples = [e for e in examples if e.get("recommended")]
    if local_only:
        examples = [e for e in examples if e.get("local_bundled")]
    if official_only:
        official_ids = {sid for sid, src in sources.items() if src.get("official")}
        examples = [e for e in examples if e.get("source") in official_ids]

    search_text = match or query
    if search_text:
        tokens = tokenize(search_text)
        scored = [(score_example(e, tokens), e) for e in examples]
        scored = [(score, e) for score, e in scored if score > 0]
        scored.sort(key=lambda item: (-item[0], item[1].get("title", "")))
        examples = [e for _, e in scored]
        if match:
            for score, example in scored:
                example["_match_score"] = score
    elif match is not None:
        examples = []

    if limit is not None and limit >= 0:
        examples = examples[:limit]

    return examples


def enrich_example(example: dict, catalog: dict) -> dict:
    sources = source_map(catalog)
    source = sources.get(example.get("source", ""), {})
    enriched = dict(example)
    enriched["source_repo"] = source.get("repo")
    enriched["source_url"] = source.get("url")
    if example.get("local_bundled"):
        enriched["local_path"] = f"{BUNDLED_EXAMPLES_DIR}/{example['local_bundled']}"
    return enriched


def format_text(examples: list[dict], catalog: dict) -> str:
    if not examples:
        return "No matching reference templates found."

    lines = []
    disclaimer = catalog.get("disclaimer")
    if disclaimer:
        lines.append(disclaimer)
        lines.append("")

    for example in examples:
        score = example.get("_match_score")
        prefix = f"[{score}] " if score is not None else ""
        lines.append(f"{prefix}{example['title']} ({example['id']})")
        lines.append(f"  category: {example.get('category')}")
        lines.append(f"  url: {example.get('url')}")
        if example.get("local_bundled"):
            lines.append(f"  local example: {BUNDLED_EXAMPLES_DIR}/{example['local_bundled']}")
        if example.get("recommended"):
            lines.append("  recommended: yes")
        lines.append("")

    return "\n".join(lines).rstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List curated RHDH Software Template reference examples.",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help=f"Path to example catalog JSON (default: {DEFAULT_CATALOG})",
    )
    parser.add_argument("--category", help="Filter by category (backend, ai, catalog, ...)")
    parser.add_argument("--tag", help="Filter by tag (recommended, go, rag, ...)")
    parser.add_argument("--stack", help="Filter by stack marker (go, java, python, ai, ...)")
    parser.add_argument(
        "--recommended",
        action="store_true",
        help="Only templates tagged recommended upstream",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only examples with a bundled local counterpart in assets/examples/",
    )
    parser.add_argument(
        "--official-only",
        action="store_true",
        help="Only examples from official Red Hat Developer sources",
    )
    parser.add_argument("--query", help="Substring token search across title, tags, and use cases")
    parser.add_argument(
        "--match",
        help="Rank examples by relevance to a natural-language intent (e.g. 'spring boot backend with ci')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of results (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON (compact when piped)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        catalog = load_catalog(args.catalog)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    examples = filter_examples(
        catalog,
        category=args.category,
        tag=args.tag,
        stack=args.stack,
        recommended=args.recommended,
        local_only=args.local_only,
        official_only=args.official_only,
        query=args.query,
        match=args.match,
        limit=args.limit,
    )

    enriched = [enrich_example(example, catalog) for example in examples]
    for item in enriched:
        item.pop("_match_score", None)

    if args.json:
        payload = {
            "ok": True,
            "count": len(enriched),
            "disclaimer": catalog.get("disclaimer"),
            "examples": enriched,
        }
        indent = 2 if sys.stdout.isatty() else None
        print(json.dumps(payload, indent=indent))
        return EXIT_SUCCESS

    print(format_text(examples, catalog))
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
