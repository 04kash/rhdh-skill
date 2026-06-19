---
name: rhdh-templates
description: >-
  Author and validate RHDH Software Templates (Scaffolder) with AI-guided workflows. Use when
  asked to "create software template", "templatize a codebase", "convert repo to
  template", "write template.yaml", "location.yaml for templates", "scaffolder
  template", "golden path template", "parameterize skeleton files", "fix template
  gotchas", "validate template", "dry-run template", "list scaffolder actions",
  "explain scaffolder action", "Nunjucks in template", "template best practices",
  "reference templates", "example templates", "what templates do customers use",
  "Template Editor", or mentions RHDH template
  authoring, Software Catalog templates, or /rhdh-templates commands. Covers setup,
  templatize (highest value), from-scratch create, reference example discovery,
  incremental parameter/step/skeleton authoring, location.yaml generation, common
  convention fixes, local validation, and live Scaffolder API dry-run/action discovery.
---

<essential_principles>

## Domain

Software Templates are `kind: Template` entities processed by the Scaffolder. Each template has:

- `template.yaml` — metadata, `spec.parameters` (form), `spec.steps` (actions), `spec.output`
- `skeleton/` — files copied/templated into the target repo (Nunjucks `{% raw %}` blocks where needed)
- `location.yaml` (repo root) — `kind: Location` registering all `template.yaml` files for catalog import

Read `references/conventions.md` before editing any template artifact — it encodes RHDH-specific rules that differ from generic Backstage docs.

Read `references/best-practices.md` when authoring or reviewing templates — it encodes Red Hat's 10 tips for repository layout, Template Editor workflow, custom fields, Nunjucks, secrets, type/tags, TechDocs, and maintenance.

## Authoring stance

- **Interactive, not fully automatic.** Templatize proposes parameterization; the user confirms each literal-to-parameter mapping.
- **Conservative parameterization.** Under-parameterize rather than expose every string — users can add parameters incrementally.
- **First-try correctness.** Generated artifacts should pass local `validate` with zero critical findings before merge.

## Script paths

All `scripts/` and `references/` paths are relative to this SKILL.md directory. Resolve them before invoking.

</essential_principles>

<setup>

## Setup gates (non-optional before file edits)

| Gate | Required check | If fail |
|------|----------------|---------|
| Command | Sub-command reference loaded | Load the matching `references/<command>.md` (or `example-catalog.md` for `examples`) |
| Layout | Template project initialized or path confirmed | Run `init` or ask user for template repo root |
| Conventions | `references/conventions.md` read for authoring commands | Read it first |

</setup>

<intake>

## What would you like to do?

| # | Command |
|---|---------|
| 1 | `init` |
| 2 | `templatize` |
| 3 | `create` |
| 4 | `add-parameter` |
| 5 | `add-step` |
| 6 | `add-skeleton` |
| 7 | `create-location` |
| 8 | `fix-gotchas` |
| 9 | `validate` |
| 10 | `list-actions` |
| 11 | `dry-run` |
| 12 | `explain-action` |
| 13 | `examples` |

Command descriptions and argument hints: `scripts/command-metadata.json`

**Wait for response before proceeding.**

</intake>

<routing>

| Response | Reference |
|----------|-----------|
| 1, "init", "setup", "scaffold", "prerequisites" | [references/init.md](references/init.md) |
| 2, "templatize", "convert", "parameterize repo", "existing codebase" | [references/templatize.md](references/templatize.md) |
| 3, "create", "from scratch", "new template" | [references/create.md](references/create.md) |
| 4, "add-parameter", "add parameter", "form field" | [references/add-parameter.md](references/add-parameter.md) |
| 5, "add-step", "add step", "scaffolder action", "pipeline step" | [references/add-step.md](references/add-step.md) |
| 6, "add-skeleton", "skeleton file", "nunjucks" | [references/add-skeleton.md](references/add-skeleton.md) |
| 7, "create-location", "location.yaml", "register templates" | [references/create-location.md](references/create-location.md) |
| 8, "fix-gotchas", "fix template", "gotchas", "raw endraw" | [references/fix-gotchas.md](references/fix-gotchas.md) |
| 9, "validate", "lint template", "check template", "lint-nunjucks", "lint nunjucks", "djlint", "nunjucks lint" | [references/validate.md](references/validate.md) |
| 10, "list-actions", "list actions", "scaffolder actions" | [references/list-actions.md](references/list-actions.md) |
| 11, "dry-run", "dry run", "test template remotely" | [references/dry-run.md](references/dry-run.md) |
| 12, "explain-action", "action schema", "parameter schema" | [references/explain-action.md](references/explain-action.md) |
| 13, "examples", "reference templates", "show me templates", "what templates exist" | [references/example-catalog.md](references/example-catalog.md) |
| First word doesn't match | Infer from context. "Turn my Spring Boot app into a template" → `templatize`. "Add owner picker to my template" → `add-parameter`. "Does my template validate?" → `validate`. "What templates do customers use?" → `examples`. |

</routing>

<cli_commands>

## Bundled scripts

```bash
# Resolve skill directory (adjust if SKILL.md path differs)
SKILL_DIR="<path-to>/skills/rhdh-templates"

python "$SKILL_DIR/scripts/init.py" --help
python "$SKILL_DIR/scripts/analyze.py" --help
python "$SKILL_DIR/scripts/create_location.py" --help
python "$SKILL_DIR/scripts/fix_gotchas.py" --help
python "$SKILL_DIR/scripts/validate.py" --help
python "$SKILL_DIR/scripts/list_actions.py" --help
python "$SKILL_DIR/scripts/dry_run.py" --help
python "$SKILL_DIR/scripts/explain_action.py" --help
python "$SKILL_DIR/scripts/list_examples.py" --help
```

Run `init.py` for deterministic tooling checks and project scaffolding. Use `analyze.py` during `templatize` Phase 1. Use `list_examples.py` during `create`, `templatize`, or `examples` to rank upstream reference templates. Use `create_location.py` and `fix_gotchas.py` where the reference files direct you — they produce structured JSON when piped.

Validation scripts: `validate.py` for local checks (include `--lint-skeleton` for Nunjucks/djLint); `list_actions.py`, `dry_run.py`, and `explain_action.py` require a reachable RHDH `--rhdh-url` and optional bearer token (`RHDH_TOKEN` env or `--token`).

</cli_commands>

<reference_index>

| File | Load when... |
|------|-------------|
| `references/conventions.md` | Any authoring command — RHDH template rules |
| `references/best-practices.md` | Authoring/review — Red Hat 10 tips and pre-merge checklist |
| `references/template-structure.md` | Writing or reviewing `template.yaml` anatomy |
| `references/parameter-widgets.md` | Choosing form fields and UI widgets for parameters |
| `references/example-catalog.md` | Command `examples` or picking upstream study references (`assets/example-catalog.json` is the data source; bundled templates under `assets/examples/`) |
| `references/schemas/template-v1beta3.schema.json` | Bundled JSON Schema for deep `validate` checks |

</reference_index>
