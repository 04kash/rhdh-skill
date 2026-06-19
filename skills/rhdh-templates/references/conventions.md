# RHDH Software Template Conventions

<required_reading>

Load this file before editing `template.yaml`, skeleton files, or `location.yaml`.

</required_reading>

<process>

## API versions

| Artifact | apiVersion | kind |
|----------|------------|------|
| `template.yaml` | `scaffolder.backstage.io/v1beta3` | `Template` |
| `location.yaml` | `backstage.io/v1alpha1` | `Location` |
| `catalog-info.yaml` (in skeleton) | `backstage.io/v1alpha1` | `Component` (typical) |

Use v1beta3 for new templates — it uses `${{ }}` step expressions. Do not mix v1beta2 `{{ }}` syntax in the same template.

## Action IDs

Scaffolder actions use **camelCase** IDs:

| Correct | Wrong |
|---------|-------|
| `fetch:template` | `fetch:template` with wrong casing in docs only — verify against live instance |
| `publish:github` | `publish:GitHub` |
| `catalog:register` | `catalog:Register` |

When unsure, list actions from a running RHDH instance with the `list-actions` command.

## Parameter form conventions

- Group related fields under `parameters[].title` sections (e.g., "Provide information about the new component").
- Use `ui:field: EntityPicker` with `catalogFilter.kind` for owner/system pickers.
- Use `ui:field: RepoUrlPicker` with `allowedHosts` for repo URL parameters.
- Use `pattern` + `ui:help` for constrained IDs (see `assets/examples/minimal-template/template.yaml`).

## Skeleton templating

Skeleton files use Nunjucks with **values from `fetch:template` steps**, not `parameters` directly:

```yaml
# template.yaml step
action: fetch:template
input:
  url: ./skeleton
  values:
    repoName: ${{ parameters.repoName }}
```

```text
# skeleton/README.md
# Project: {{ values.repoName }}
```

### When to use `{% raw %}` … `{% endraw %}`

Wrap content that must pass through unchanged and contains `{{` or `{%` — common in:

- GitHub Actions workflows (`.github/workflows/*.yaml`)
- Helm charts with Go templates
- Any file where braces are literal syntax, not Nunjucks

## Secrets in templates

Use Backstage/RHDH secrets syntax in step inputs — never hardcode tokens in skeleton files:

```yaml
token: ${{ secrets.user.github.token }}
```

Exact secret paths depend on configured integrations; confirm against your RHDH instance.

## Repository layout

```
template-repo/
├── location.yaml              # kind: Location — registers all templates
└── templates/
    └── my-template/
        ├── template.yaml
        ├── skeleton/          # optional README, catalog-info.yaml, app source
        └── README.md          # optional human docs
```

## location.yaml pattern

```yaml
apiVersion: backstage.io/v1alpha1
kind: Location
metadata:
  name: my-org-templates
  description: Software Templates for My Org
spec:
  targets:
    - ./templates/**/template.yaml
```

Register the **location.yaml URL** in RHDH (Catalog Import or `catalog.locations` in app-config), not individual template files.

For repository layout rationale and multi-repo splitting guidance, see `best-practices.md` tip 1.

## Common publish + register sequence

Most service templates end with:

1. `fetch:template` — materialize skeleton
2. `publish:github` (or `publish:gitlab`, etc.) — push to remote
3. `catalog:register` — register `catalog-info.yaml` from the new repo

Wire `repoContentsUrl` from publish output into register input.

</process>
