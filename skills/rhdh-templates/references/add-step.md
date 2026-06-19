# add-step — Incremental Step Authoring

<required_reading>

- `conventions.md`
- `template-structure.md`

</required_reading>

<process>

Add a scaffolder step to an existing template without rebuilding from scratch.

## Step 1: Identify action

Ask user what the step should do. Map to a scaffolder action:

| Intent | Typical action |
|--------|----------------|
| Copy/template files | `fetch:template` |
| Fetch plain files | `fetch:plain` |
| Publish to GitHub | `publish:github` |
| Register catalog entity | `catalog:register` |
| Run custom action | `custom:<action-name>` |

Action IDs are camelCase. When unsure of installed actions, use the `list-actions` command to query the live instance.

## Step 2: Choose position

Steps run **in series**. Ask where to insert:

- Before publish (materialize content)
- After publish (register, notify, trigger CI)

Assign unique `id` (kebab-case) and human-readable `name`.

## Step 3: Build input

Reference parameters and prior step outputs:

```yaml
- id: notify-team
  name: Notify platform team
  action: notification:send
  input:
    recipients: entity:group:default/platform-team
    title: New component ${{ parameters.componentId }}
    info: ${{ steps.publish.output.remoteUrl }}
```

## Step 4: Update output (if needed)

If the step produces user-facing results, add `spec.output.links` referencing `${{ steps.<id>.output.* }}`.

## Step 5: Verify wiring

Checklist:

- [ ] `id` unique among all steps
- [ ] `action` uses correct camelCase ID
- [ ] All `${{ parameters.* }}` exist in form
- [ ] All `${{ steps.*.output.* }}` reference prior step IDs
- [ ] `fetch:template` steps include complete `values` map

## Step 6: fix-gotchas

```bash
python <skill-dir>/scripts/fix_gotchas.py --path <template.yaml> [--apply] [--json]
```

</process>

<success_criteria>

- New step inserted at correct position with unique `id`
- Action ID and inputs match conventions.md
- Downstream steps and `output` updated if they depend on new step
- fix-gotchas reports no critical action-casing or expression errors

</success_criteria>
