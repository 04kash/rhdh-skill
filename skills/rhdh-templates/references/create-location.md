# create-location — Generate location.yaml

<required_reading>

- `conventions.md`

</required_reading>

<process>

Standalone utility for generating or refreshing root `location.yaml`. Templatize and create flows may also produce this file — use this command when templates were added manually or the glob target is stale.

## Step 1: Confirm repo root

The template repository root contains `templates/` with one or more `template.yaml` files.

## Step 2: Run script

```bash
python <skill-dir>/scripts/create_location.py \
  --path <repo-root> \
  --name <location-metadata-name> \
  [--description "Human description"] \
  [--json]
```

| Flag | Default |
|------|---------|
| `--path` | current directory |
| `--name` | derived from directory name + `-templates` suffix |
| `--description` | auto-generated |

The script:

1. Discovers `templates/**/template.yaml`
2. Writes or updates `location.yaml` at repo root with glob target `./templates/**/template.yaml`
3. Lists discovered templates in JSON output

## Step 3: Review output

Show user the generated `location.yaml` and template count.

If zero templates found, stop — run `init` or `create` first.

## Step 4: Registration reminder

Tell user to register **the location.yaml URL** in RHDH:

- Catalog Import UI: `/catalog-import`
- Or `catalog.locations` in app-config:

```yaml
catalog:
  locations:
    - type: url
      target: https://github.com/acme-corp/templates/blob/main/location.yaml
      rules:
        - allow: [Location, Template]
```

</process>

<success_criteria>

- `location.yaml` exists at repo root with `kind: Location`
- `spec.targets` includes `./templates/**/template.yaml`
- Script JSON reports all discovered template paths
- User knows how to register the Location in RHDH

</success_criteria>
