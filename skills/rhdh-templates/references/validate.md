# validate — Local Template Validation

<required_reading>

- `conventions.md`

</required_reading>

<process>

Validate without a running RHDH instance. Combines YAML structure checks, JSON Schema validation (structural subset always; full bundled schema when `jsonschema` is installed), packaged gotcha rules, optional repo `location.yaml` verification, and optional djLint for skeleton files.

## Step 1: Run validate script

```bash
python <skill-dir>/scripts/validate.py --path <template-dir-or-template.yaml> [--repo] [--lint-skeleton] [--json]
```

| Flag | Purpose |
|------|---------|
| `--repo` | Also check root `location.yaml` for the template repository |
| `--lint-skeleton` | Run djLint on `skeleton/` when installed |
| `--no-json-schema` | Skip optional full JSON Schema validation (structural checks still run) |
| `--json` | Structured output for agent consumption |

Consume full JSON output when `--json` is passed. Do not pipe through `head`, `tail`, or `grep`.

## Step 2: Interpret results

| Exit code | Meaning |
|-----------|---------|
| 0 | No critical findings |
| 1 | Critical findings remain |
| 2 | Usage error |

Severity levels:

- **critical** — likely Template Editor failure (wrong apiVersion, action casing, invalid schema, v1beta2 expressions)
- **warning** — should fix before merge (missing parameters, unknown parameter refs, workflow raw blocks)
- **info** — optional tooling skipped (PyYAML/djlint/jsonschema not installed)

## Step 3: Fix and re-run

1. Run `fix-gotchas` with `--apply` for auto-fixable critical issues.
2. Manually address remaining findings.
3. Re-run `validate.py` until `critical_count` is 0.

For remote execution validation against a live RHDH instance, use `dry-run` after local validation passes.

Review warning/info findings against the `<authoring_checklist>` in `best-practices.md` (tags, docs, Secret fields, maintenance).

## Nunjucks skeleton lint (`--lint-skeleton`)

Use when the user asks to lint Nunjucks, run djLint, or check skeleton syntax only. There is no separate script — pass `--lint-skeleton` to `validate.py`.

Install djLint when missing:

```bash
pip install djlint
# or: uv tool install djlint
```

If djLint is absent, `validate` reports an **info** finding and continues — YAML and gotcha checks still run.

Common Nunjucks fixes:

- Wrap GitHub Actions `${{ }}` in `{% raw %}…{% endraw %}` (see `conventions.md`)
- Use `{{ values.field }}` not `{{ parameters.field }}` in skeleton files
- Add missing `{% endif %}` / `{% endfor %}` closers

For pre-merge checks, run full `validate` with and without `--lint-skeleton`, or combine both in one invocation.

</process>

<success_criteria>

- `validate.py --json` reports `ok: true` and `critical_count: 0`
- User understands any warnings and whether to fix them before merge
- When `--lint-skeleton` is used, Nunjucks issues are surfaced or djlint skip is documented

</success_criteria>
