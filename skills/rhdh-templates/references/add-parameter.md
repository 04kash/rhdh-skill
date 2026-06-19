# add-parameter — Incremental Parameter Authoring

<required_reading>

- `conventions.md`
- `template-structure.md`
- `parameter-widgets.md`

</required_reading>

<process>

Extend an existing `template.yaml` without re-running full `templatize` or `create`.

## Step 1: Locate template

Confirm path to `templates/<name>/template.yaml`.

## Step 2: Define parameter

Gather from user:

| Field | Notes |
|-------|-------|
| Name | camelCase key (e.g., `repoName`) |
| Title | Form label |
| Type | `string`, `number`, `boolean`, `array` |
| Widget | default, `EntityPicker`, `RepoUrlPicker`, `radio`, etc. |
| Section | existing `parameters[].title` or new section |
| Required | yes/no |

## Step 3: Edit template.yaml

Add to appropriate `parameters` section:

```yaml
repoName:
  title: Repository Name
  type: string
  description: GitHub repository name for the new component
  ui:autofocus: true
```

For conditional fields, add `dependencies` block per `template-structure.md`.

## Step 4: Wire into steps

Every new parameter used in skeleton or actions must appear in a `fetch:template` `values` map:

```yaml
values:
  repoName: ${{ parameters.repoName }}
```

Search all `steps[].input` for missing wiring after the edit.

## Step 5: Update skeleton (if needed)

If the parameter replaces a literal in skeleton files, update Nunjucks to `{{ values.<name> }}`.

## Step 6: Verify

Run `fix_gotchas.py` on the template path. Confirm parameter appears in form and values map.

</process>

<success_criteria>

- Parameter added to correct form section with type and UI field
- All `fetch:template` steps pass the parameter in `values`
- Skeleton references updated when parameter replaces literals
- No duplicate parameter keys

</success_criteria>
