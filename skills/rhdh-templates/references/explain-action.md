# explain-action — Action or Template Schema Reference

<required_reading>

- `conventions.md`

</required_reading>

<process>

Show input/output JSON Schema for a Scaffolder action, or the parameter form schema for a catalog Template entity.

## Mode selection

| User asks about | Flag |
|-----------------|------|
| Scaffolder action input fields (`publish:github`, `fetch:template`, …) | `--action <id>` |
| Template form parameters for a registered template | `--template-ref template:namespace/name` |

Provide exactly one mode per invocation.

## Step 1: Run explain script

**Action schema** (from list-actions response):

```bash
python <skill-dir>/scripts/explain_action.py \
  --rhdh-url https://rhdh.example.com \
  --action publish:github \
  [--token TOKEN] \
  [--json]
```

**Template parameter schema** (from parameter-schema endpoint):

```bash
python <skill-dir>/scripts/explain_action.py \
  --rhdh-url https://rhdh.example.com \
  --template-ref template:default/my-template \
  [--token TOKEN] \
  [--json]
```

## Step 2: Apply schema to authoring

For `add-step`:

- Wire `input:` fields to match `schema.input` required properties
- Reference prior step outputs using `${{ steps.<stepId>.output.<field> }}`

For `add-parameter`:

- Compare proposed fields against an existing template's parameter schema when templating from a registered example

If action is not found, run `list-actions --filter <substring>` to discover the correct id.

</process>

<success_criteria>

- Schema JSON returned for the requested action or template
- User can author a step or parameter block without guessing field names
- Action id matches live instance casing

</success_criteria>
