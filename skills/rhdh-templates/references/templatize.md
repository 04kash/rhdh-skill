# templatize — Convert Existing Codebase to Template

<required_reading>

- `conventions.md`
- `template-structure.md`
- `example-catalog.md` — upstream references by stack and workflow

</required_reading>

<process>

Templatize is the **highest-value workflow**: most platform engineers start from working code, not a blank template.

## Overview

```
analyze → review → scaffold → template.yaml → location.yaml → fix-gotchas handoff
```

Interactive at every decision point. Do not auto-parameterize without user confirmation.

---

### Phase 1: Analyze

1. Confirm source path — local directory or cloned repo.
2. Run the analyzer script (deterministic scan):

```bash
python <skill-dir>/scripts/analyze.py --path <source-dir> [--json]
```

Consume full JSON output. It reports:

- `project_types` — detected stack markers (nodejs, java-maven, python, …)
- `candidate_literals` — heuristic list with category, sources, and `usually_parameterize` hint
- `workflow_files` — `.github/workflows/*` files that may need `{% raw %}`

3. Supplement script output with manual review for business-specific literals the heuristics miss.
4. Match reference templates for the detected stack:

```bash
python <skill-dir>/scripts/list_examples.py \
  --match "<detected project_types and user goal>" \
  --limit 3 --json
```

Suggest upstream examples to study (parameter forms, publish/register steps, CI patterns). Prefer `local_bundled` paths when offline validation is needed.
5. List **candidate literals** for parameterization:

| Category | Examples | Usually parameterize? |
|----------|----------|----------------------|
| Names | repo name, app name, namespace | Yes |
| Org/owner | GitHub org, catalog owner | Yes |
| URLs/hosts | registry, cluster API | Often |
| Ports, replicas | `8080`, `3` | Sometimes |
| Boilerplate | framework defaults, LICENSE | Rarely |

6. Flag files needing `{% raw %}` (`.github/workflows/`, Helm templates).

Output a **candidate table** for user review before editing files.

---

### Phase 2: Review (user gate)

Present the candidate table. For each row ask: parameterize / keep literal / skip.

Principles:

- **Conservative** — when uncertain, keep literal; user can `add-parameter` later.
- **Group parameters** — repo + owner + system belong in one form section.
- **Match RHDH examples** — compare against [red-hat-developer-hub-software-templates](https://github.com/redhat-developer/red-hat-developer-hub-software-templates) patterns for similar stacks.

Do not proceed until user confirms the parameter list.

---

### Phase 3: Scaffold

1. Create `templates/<template-name>/skeleton/` in the **template repo** (not inside source repo unless user directs).
2. Copy source files into `skeleton/`, preserving structure.
3. Replace confirmed literals with Nunjucks `{{ values.<param> }}` placeholders.
4. Add `{% raw %}` blocks to CI/workflow files as needed.
5. Include `catalog-info.yaml` in skeleton when the template should register a Component.

---

### Phase 4: template.yaml

1. Read `template-structure.md` and `assets/examples/minimal-template/template.yaml`.
2. Set `metadata.name`, `title`, `description`, `tags` from user input.
3. Build `spec.parameters` from confirmed parameter list with appropriate `ui:field` widgets.
4. Build `spec.steps`:

   | Typical order | Action |
   |---------------|--------|
   | 1 | `fetch:template` → `./skeleton` with full `values` map |
   | 2 | `publish:github` or user's SCM action |
   | 3 | `catalog:register` |

5. Add `spec.output` links to repo and catalog entity.

---

### Phase 5: location.yaml

If root `location.yaml` missing or stale:

```bash
python <skill-dir>/scripts/create_location.py --path <template-repo-root> [--json]
```

Templatize may emit `location.yaml` inline; `create-location` remains the standalone utility for updates.

---

### Phase 6: fix-gotchas handoff

```bash
python <skill-dir>/scripts/fix_gotchas.py --path templates/<template-name>/template.yaml [--apply] [--json]
```

Review script output. Apply fixes with `--apply`. Re-run until no critical findings remain.

Run local validation:

```bash
python <skill-dir>/scripts/validate.py --path templates/<template-name>/ --repo [--lint-skeleton] [--json]
```

When RHDH is reachable, optionally run `dry-run` with sample parameter values.

### Critique and fix loop

Before finishing, self-check and patch until no material issues remain:

1. Did the user confirm every parameterized literal?
2. Does `validate.py --json` report zero critical findings?
3. Are all skeleton placeholders wired through `fetch:template` `values`?
4. Are workflow files either wrapped in `{% raw %}` or listed in `copyWithoutTemplating`?

Exit bar: template passes `validate.py` with no critical issues and matches `conventions.md`.

</process>

<success_criteria>

- User confirmed parameter map before skeleton edits
- `templates/<name>/template.yaml`, `skeleton/`, and root `location.yaml` exist
- Skeleton uses `values.*` not `parameters.*`
- `validate.py` reports zero critical issues
- Template structure matches conventions.md

</success_criteria>
