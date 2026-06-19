# Parameter Form Widgets

<required_reading>

Load when adding parameters via `add-parameter`, building `spec.parameters` in `templatize` or `create`, or choosing the right UI field for a form input.

</required_reading>

<process>

## Common property patterns

| Use case | Type | Widget / options |
|----------|------|------------------|
| Component or repo ID | `string` | `pattern` + `ui:help` for kebab-case IDs |
| Free text description | `string` | default text field |
| Catalog owner | `string` | `ui:field: EntityPicker`, filter `Group`/`User` |
| Catalog system | `string` | `ui:field: EntityPicker`, filter `System` |
| Repository URL | `string` | `ui:field: RepoUrlPicker` + `allowedHosts` |
| Environment choice | `string` | `enum` or `ui:widget: radio` |
| Boolean toggle | `boolean` | default checkbox |
| Numeric replicas / port | `number` | `minimum` / `maximum` when bounded |
| Multi-select owners | `array` | `ui:widget: checkboxes` or EntityPicker multi |
| Password / API token | `string` | `ui:field: Secret` (masks input in form, review, logs) |

## EntityPicker (owner, system, domain)

```yaml
owner:
  title: Owner
  type: string
  ui:field: EntityPicker
  ui:options:
    catalogFilter:
      kind:
        - Group
        - User
```

Use `allowArbitraryValues: false` when the picker must resolve to catalog entities only.

## RepoUrlPicker (GitHub / GitLab / Bitbucket)

```yaml
repoUrl:
  title: Repository Location
  type: string
  ui:field: RepoUrlPicker
  ui:options:
    allowedHosts:
      - github.com
      - gitlab.com
```

Pair with `allowedOwners` when restricting orgs. The publish step reads `${{ parameters.repoUrl }}`.

## Constrained IDs

```yaml
componentId:
  title: Component ID
  type: string
  pattern: '^[a-z0-9-]*[a-z0-9]$'
  ui:help: Lowercase letters, digits, and dashes only
  ui:autofocus: true
```

## Conditional fields (dependencies)

Show fields only when another field matches:

```yaml
parameters:
  - title: Repository details
    properties:
      repoChoice:
        title: Repository host
        type: string
        enum:
          - github
          - gitlab
        default: github
      githubOrg:
        title: GitHub organization
        type: string
    dependencies:
      repoChoice:
        oneOf:
          - properties:
              repoChoice:
                enum: [github]
              githubOrg:
                title: GitHub organization
                type: string
            required: [githubOrg]
```

## Parameter → skeleton wiring

Form keys use `parameters.<name>`. Skeleton files use `values.<name>` populated in `fetch:template`:

```yaml
values:
  componentId: ${{ parameters.componentId }}
  owner: ${{ parameters.owner }}
```

Every parameter referenced in skeleton or downstream steps must appear in a `values` map or step `input`.

## Secret field (sensitive inputs)

Use for passwords, tokens, and API keys — never a plain text field:

```yaml
apiToken:
  title: API Token
  type: string
  ui:field: Secret
  ui:options:
    visibilityToggle: true
```

See `best-practices.md` tip 7 for step-level `${{ secrets.* }}` wiring.

## Template filters in step expressions

EntityPicker values are string refs (`component:default/my-service`). Use filters in step `input`, not skeleton files:

```yaml
repoName: ${{ parameters.component | parseEntityRef | pick('name') }}
```

See `best-practices.md` tip 5 for common filters.

</process>
