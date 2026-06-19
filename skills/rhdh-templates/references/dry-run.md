# dry-run — Remote Template Execution Test

<required_reading>

- `conventions.md`

</required_reading>

<process>

Execute a template against the Scaffolder v2 dry-run API without creating real resources. Mutation steps (publish, register) are simulated — warn the user that full E2E testing still requires running the template in RHDH.

**Prerequisite:** run local `validate` first (route to the `validate` command) until `critical_count` is 0.

## Capability gate

Requires:

- Reachable RHDH with Scaffolder v2 API
- PyYAML available (`uv sync --extra dev` in this repo; or system PyYAML)
- Valid `template.yaml` and optional `skeleton/` directory

If RHDH is unreachable, skip and suggest local `validate` only.

## Step 1: Prepare values

Create a JSON file with parameter values matching `spec.parameters`:

```json
{
  "componentId": "demo-service",
  "owner": "group:default/team-a",
  "description": "Demo from dry-run"
}
```

Use fake data — never real tokens or production identifiers unless the user explicitly provides them.

## Step 2: Run dry-run script

```bash
python <skill-dir>/scripts/dry_run.py \
  --rhdh-url https://rhdh.example.com \
  --path templates/my-template/ \
  --values /tmp/values.json \
  [--secrets /tmp/secrets.json] \
  [--token TOKEN] \
  [--json]
```

The script:

1. Parses `template.yaml`
2. Serializes `skeleton/` as base64 directory contents
3. POSTs to `/api/scaffolder/v2/dry-run`
4. Returns log lines, output metadata, and generated file count

## Step 3: Interpret failures

| Symptom | Likely cause |
|---------|--------------|
| 401/403 | Missing or expired token |
| 400 with `errors` | Invalid parameter values or malformed template |
| Action not found | Wrong action ID — run `list-actions` |
| Empty skeleton output | Missing `fetch:template` step or wrong `values` wiring |

Re-run local `validate` and `fix-gotchas` before retrying dry-run.

</process>

<success_criteria>

- Dry-run completes with exit code 0
- Log shows expected steps executed (especially `fetch:template`)
- User understands dry-run skips real mutations and may need manual E2E verification

</success_criteria>
