# template.yaml Structure

<required_reading>

Load when writing, reviewing, or explaining `template.yaml` sections.

</required_reading>

<process>

## Minimal anatomy

```yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: example-template
  title: Example Template
  description: Short description shown in the Create UI
  tags:
    - recommended
spec:
  owner: group:default/platform-team
  type: service
  parameters: []   # form sections
  steps: []        # scaffolder actions in order
  output: {}       # links shown after completion
```

## metadata

| Field | Purpose |
|-------|---------|
| `name` | Machine ID (lowercase, hyphens) — unique in catalog |
| `title` | Human label in Create UI |
| `description` | Shown in template picker |
| `tags` | Filtering in UI (`recommended` highlights template) |
| `annotations.backstage.io/techdocs-ref` | Optional — `dir:.` when template ships TechDocs |

## spec.parameters

Array of **form sections**. Each section has `title`, optional `required`, `properties`, and optional `dependencies` for conditional fields.

```yaml
parameters:
  - title: Component details
    required:
      - repoName
      - owner
    properties:
      repoName:
        title: Repository Name
        type: string
      owner:
        title: Owner
        type: string
        ui:field: EntityPicker
        ui:options:
          catalogFilter:
            kind: [Group, User]
```

Use `dependencies` + `oneOf` / `allOf` for conditional fields (see RHDH software-templates examples).

## spec.steps

Ordered list of actions. Each step needs unique `id`, human `name`, `action`, and `input`.

```yaml
steps:
  - id: fetch-base
    name: Fetch skeleton
    action: fetch:template
    input:
      url: ./skeleton
      values:
        repoName: ${{ parameters.repoName }}
        owner: ${{ parameters.owner }}

  - id: publish
    name: Publish to GitHub
    action: publish:github
    input:
      repoUrl: ${{ parameters.repoUrl }}
      description: ${{ parameters.description }}
      defaultBranch: main

  - id: register
    name: Register in catalog
    action: catalog:register
    input:
      repoContentsUrl: ${{ steps.publish.output.repoContentsUrl }}
      catalogInfoPath: /catalog-info.yaml
```

Reference prior step outputs as `${{ steps.<id>.output.<field> }}`.

## spec.output

Optional links/icons after success:

```yaml
output:
  links:
    - title: Open repository
      url: ${{ steps.publish.output.remoteUrl }}
    - title: View in catalog
      icon: catalog
      entityRef: ${{ steps.register.output.entityRef }}
```

## copyWithoutTemplating

On `fetch:template`, exclude paths that must not be Nunjucks-processed:

```yaml
input:
  url: ./skeleton
  copyWithoutTemplating:
    - .github/workflows/
```

Use when workflow files are parameterized separately or wrapped in `{% raw %}`.

</process>
