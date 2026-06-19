# init — Setup Template Authoring Environment

<required_reading>

- `conventions.md` — target repository layout

</required_reading>

<process>

## Step 1: Run the init script

From the user's target directory (or current directory):

```bash
python <skill-dir>/scripts/init.py --path . [--rhdh-url https://rhdh.example.com] [--json]
```

The script:

1. Checks required tools (`python3`, `git`)
2. Reports recommended tools (`djlint` for Nunjucks — used by `validate --lint-skeleton`)
3. Scaffolds `templates/example-template/` with starter `template.yaml` and `skeleton/`
4. Creates root `location.yaml` if missing
5. Optionally probes `GET /api/scaffolder/v2/actions` when `--rhdh-url` is set

Consume full JSON output when `--json` is passed. Do not pipe through `head`, `tail`, or `grep`.

## Step 2: Interpret results

| Exit code | Meaning |
|-----------|---------|
| 0 | Ready — required tools present, layout scaffolded or already valid |
| 1 | Partial — layout created but optional tools or RHDH unreachable |
| 2 | Usage error |

If RHDH is unreachable, tell the user local authoring and `validate` still work; use `list-actions` / `dry-run` when connectivity is available.

## Step 3: Confirm with user

Show:

- Which tools are missing (if any) and install hints
- Scaffolded paths
- RHDH connectivity status (if checked)

Ask whether to rename `example-template` or start `templatize` / `create` on the new layout.

Mention the recommended dev loop from `best-practices.md`: local `validate` → Template Editor (`/create/edit`) → `dry-run` when RHDH is reachable. Route to `rhdh-local` skill if the user wants a local RHDH instance.

</process>

<success_criteria>

- `init.py` exit code 0 or 1 with clear user messaging
- `templates/` directory exists with at least one template folder
- Root `location.yaml` exists with glob target `./templates/**/template.yaml`
- User knows next command (`templatize`, `create`, or incremental add-*)

</success_criteria>
