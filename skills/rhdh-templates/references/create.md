# create — From-Scratch Template

<required_reading>

- `conventions.md`
- `template-structure.md`
- `parameter-widgets.md`
- `assets/examples/minimal-template/template.yaml`
- `assets/examples/nodejs-backend/template.yaml` — full publish/register pipeline
- `assets/examples/java-springboot/template.yaml` — Spring Boot + Maven

</required_reading>

<process>

Use when **no reference codebase** exists. For converting existing code, use `templatize` instead.

## Step 1: Gather intent

Ask (one round, not necessarily one question each):

1. **Template purpose** — what golden path does this enable?
2. **Target type** — `service`, `website`, `library`, `plugin`, etc.
3. **Parameters** — minimum form fields (name, owner, repo URL, …)
4. **Steps** — fetch skeleton only, or publish + register too?
5. **SCM** — GitHub, GitLab, Bitbucket?

## Step 1b: Match reference examples (recommended)

Before writing files, query the curated catalog and suggest 1–3 study references:

```bash
python <skill-dir>/scripts/list_examples.py \
  --match "<template purpose and stack from Step 1>" \
  --limit 3 --json
```

Present upstream URLs from the matches. When a match includes `local_bundled`, also point at `assets/examples/<name>/` for offline patterns. Ask whether to mirror a reference's step sequence or start from `assets/examples/minimal-template/`.

Load `example-catalog.md` when the user asks what customers typically build.

## Step 2: Ensure layout

If no template repo exists, run `init` first.

## Step 3: Create template directory

```
templates/<kebab-name>/
├── template.yaml
├── skeleton/
│   ├── README.md
│   └── catalog-info.yaml   # when registering a Component
└── README.md               # optional
```

Use `assets/examples/minimal-template/` as the starting skeleton for simple templates.

## Step 4: Build template.yaml

1. `metadata` — descriptive `name`, `title`, `description`, meaningful `tags` (see `best-practices.md` tip 8)
2. `spec.type` — set to a discoverable category, not generic default when possible
3. `spec.parameters` — at least one section with required fields; use EntityPicker/Secret widgets per `best-practices.md` tips 4 and 7
4. `spec.steps` — minimal path:

```yaml
steps:
  - id: fetch-base
    name: Fetch skeleton
    action: fetch:template
    input:
      url: ./skeleton
      values:
        componentId: ${{ parameters.componentId }}
        owner: ${{ parameters.owner }}
        description: ${{ parameters.description }}
```

Add publish/register steps when user wants full end-to-end flow.

## Step 5: Write skeleton files

Keep skeleton minimal but valid:

- `README.md` with `{{ values.componentId }}` placeholder
- `catalog-info.yaml` when using `catalog:register`

## Step 6: Register templates

```bash
python <skill-dir>/scripts/create_location.py --path <repo-root> [--json]
```

## Step 7: fix-gotchas

```bash
python <skill-dir>/scripts/fix_gotchas.py --path templates/<name>/template.yaml [--apply] [--json]
```

### Critique and fix loop

Before finishing, verify:

1. Parameters use appropriate widgets from `parameter-widgets.md`
2. Steps match the user's SCM choice (publish + register when requested)
3. `fix_gotchas.py` reports zero critical findings after `--apply`
4. `create_location.py` lists the new template

5. Add `README.md` (or TechDocs per `best-practices.md` tip 9) for non-trivial templates

Exit bar: minimal but complete template for the described use case, passes `validate`, ready for Template Editor (`best-practices.md` tip 2).

</process>

<success_criteria>

- Valid v1beta3 `template.yaml` with parameters, steps, and output appropriate to use case
- `skeleton/` contains at least one templated file
- `location.yaml` registers the new template
- fix-gotchas passes with no critical findings

</success_criteria>
