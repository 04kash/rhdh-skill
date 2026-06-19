# list-actions — Discover Scaffolder Actions

<required_reading>

- `conventions.md` — action ID casing rules

</required_reading>

<process>

Query a running RHDH instance for installed Scaffolder actions. Requires network access to the RHDH backend.

Equivalent UI: **Installed Actions** in Software Catalog or `/create/actions` (`best-practices.md` tip 3).

## Capability gate

Run only when:

- User provides `--rhdh-url` or confirms their RHDH base URL
- RHDH instance is reachable from the agent environment

If unreachable, state in one line that the step is skipped and offer local `validate` instead. Do not ask the user to install tooling.

## Step 1: Run list-actions script

```bash
python <skill-dir>/scripts/list_actions.py --rhdh-url https://rhdh.example.com [--filter publish] [--token TOKEN] [--json]
```

Token resolution order:

1. `--token` flag
2. `RHDH_TOKEN` environment variable
3. `BACKSTAGE_TOKEN` environment variable

When RHDH uses backend permissions, the user may need a browser session token from the frontend.

## Step 2: Use results

Each action includes:

- `id` — use this exact string in `template.yaml` `action:` fields
- `description` — human-readable summary
- `schema.input` / `schema.output` — JSON Schema for step wiring

Filter with `--filter` when the user asks about a specific action family (e.g., `publish`, `fetch`, `catalog`).

For detailed schema of one action, route to `explain-action`.

</process>

<success_criteria>

- Script exits 0 with action list JSON
- User can pick correct action IDs for `add-step` or template authoring
- Action IDs match live instance (not guessed from docs)

</success_criteria>
