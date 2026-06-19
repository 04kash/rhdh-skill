# fix-gotchas — Apply Common Template Corrections

<required_reading>

- `conventions.md`

</required_reading>

<process>

Apply packaged rules to catch mistakes that pass YAML parsing but fail in Template Editor or at execution time.

## Step 1: Target path

Accept:

- Path to `template.yaml`
- Path to `templates/<name>/` directory (script finds `template.yaml`)

## Step 2: Run checker

```bash
python <skill-dir>/scripts/fix_gotchas.py \
  --path <template.yaml-or-dir> \
  [--apply] \
  [--json]
```

Without `--apply`: report findings only.
With `--apply`: write safe automatic fixes in place.

## Step 3: Review findings

| Severity | Action |
|----------|--------|
| critical | Must fix before merge — apply or manual edit |
| warning | Recommend fix — explain to user |
| info | Convention suggestion |

Rule definitions (id, severity, check, auto-fix availability) live in `references/gotchas-rules.json`. The same rules run inside `validate.py`.

## Step 4: Manual fixes

Some rules are **detect-only** (require human judgment):

- Correct `owner` entity refs
- Choosing `copyWithoutTemplating` vs `{% raw %}`
- Secret path selection for the user's integrations

Document manual items in the response.

## Step 5: Re-run until clean

Loop until no critical findings remain, then run `validate` for full pre-merge checks.

</process>

<success_criteria>

- `fix_gotchas.py` executed with JSON output reviewed
- All critical findings resolved (auto or manual)
- User informed of detect-only items
- Template ready for Template Editor validation

</success_criteria>
