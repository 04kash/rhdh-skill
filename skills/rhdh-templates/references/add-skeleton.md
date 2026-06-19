# add-skeleton — Incremental Skeleton Authoring

<required_reading>

- `conventions.md`

</required_reading>

<process>

Add or extend files under `templates/<name>/skeleton/` for an existing template.

## Step 1: Confirm template context

Locate `templates/<name>/template.yaml` and existing `skeleton/` tree.

## Step 2: Determine file role

| File type | Templating approach |
|-----------|---------------------|
| App source, README, YAML config | Nunjucks `{{ values.* }}` |
| GitHub Actions, Helm with `{{` | `{% raw %}` … `{% endraw %}` OR `copyWithoutTemplating` |
| Binary / images | Do not template — document manual copy |

## Step 3: Add file

Create file under `skeleton/` mirroring target repo layout.

Example `skeleton/catalog-info.yaml`:

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: {{ values.componentId }}
  description: {{ values.description }}
spec:
  type: service
  lifecycle: experimental
  owner: {{ values.owner }}
```

## Step 4: Sync template.yaml

1. Ensure parameters exist for every `values.*` key used.
2. Update `fetch:template` step `values` map.
3. If adding CI workflows, set `copyWithoutTemplating` or raw blocks:

```yaml
input:
  url: ./skeleton
  copyWithoutTemplating:
    - .github/workflows/
```

## Step 5: Optional additional fetch step

When skeleton has CI overlay from shared path (RHDH software-templates pattern):

```yaml
- id: ci-template
  name: Add CI skeleton
  action: fetch:template
  input:
    url: ${{ parameters.ci }}
    copyWithoutTemplating:
      - .github/workflows/
    values:
      repoName: ${{ parameters.repoName }}
```

## Step 6: Verify

- Grep skeleton for `parameters.` — should be **zero** matches (use `values.` only).
- Grep for unwrapped `{{` in workflow files — should be inside `{% raw %}` or excluded via `copyWithoutTemplating`.
- Run `validate --lint-skeleton` for Nunjucks syntax checks (see `validate.md`).

</process>

<success_criteria>

- New skeleton files use `values.*` references only
- Workflow/chart files protected from accidental Nunjucks processing
- `fetch:template` `values` map includes all new placeholders
- File paths match expected output repo structure

</success_criteria>
