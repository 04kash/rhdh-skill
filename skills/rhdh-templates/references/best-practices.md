# Backstage Software Template Best Practices

<required_reading>

Load when authoring, reviewing, or improving templates — especially during `create`, `templatize`, `add-parameter`, `add-skeleton`, and pre-merge `validate`.

Source: [10 tips for better Backstage Software Templates](https://developers.redhat.com/articles/2025/03/17/10-tips-better-backstage-software-templates) (Red Hat Developer, 2025).

</required_reading>

<process>

## 1. Structure your template repository

Use a **central template repository** with one folder per template and a root `location.yaml` that registers all templates via glob — new templates appear in the catalog after commit without per-template import.

**Why:** Reduces operational toil — platform engineers commit a folder; catalog sync picks it up. Split into multiple repos only when authorship or access boundaries require it.

**RHDH convention:** See `conventions.md` for the `./templates/**/template.yaml` layout, `location.yaml` pattern, and catalog registration via the location URL (not individual template files).

Reference implementations: [backstage/software-templates](https://github.com/backstage/software-templates/), [rhdh-demo-gh/templates](https://github.com/rhdh-demo-gh/templates/).

## 2. Experiment with the Template Editor

Avoid the slow loop of push → wait for catalog sync → test run. Use Backstage's **Template Editor** at `/create/edit` (or **Template Editor** link on the Software Templates page) to:

- Edit templates from a local directory or paste YAML
- Preview form rendering live on the right
- Experiment with custom field extensions before committing

**When to use:** After local `validate` passes, paste into Template Editor for form UX review. Copy final YAML back to the repo.

**Skill workflow:** `validate` locally first → Template Editor for UX → `dry-run` against live RHDH for execution.

## 3. Explore installed actions

Action IDs and schemas vary by RHDH instance (installed plugins). Never guess action names from docs alone.

| Method | Path / command |
|--------|----------------|
| RHDH UI | Software Catalog → **Installed Actions**, or `/create/actions` |
| Skill CLI | `list-actions --rhdh-url …` |
| Single action schema | `explain-action --action-id …` |

Use the exact `id` string from the live instance in `steps[].action`. Plugin actions follow `namespace:actionName` (e.g., `quay:create-repository`).

## 4. Improve DevEx with custom field extensions

Forms use [react-jsonschema-form](https://github.com/rjsf-team/react-jsonschema-form). Built-in **Custom Field Extensions** reduce errors vs free-text entry:

| Field | Use when |
|-------|----------|
| `EntityPicker` | Owner, system, component, domain — catalog-backed selection |
| `RepoUrlPicker` | SCM URL with host/org validation |
| `OwnerPicker` | Shortcut for owner groups |
| `Secret` | Passwords, tokens, API keys (see tip 7) |

Set `allowArbitraryValues: false` when the value must resolve to a catalog entity. See `parameter-widgets.md` for wiring patterns and examples.

## 5. Process structured data with template filters

[Template filters](https://backstage.io/docs/features/software-templates/template-extensions) transform values in step expressions. Entity pickers return string refs like `component:default/my-service`.

```yaml
title: "Deploy ${{ parameters.component | parseEntityRef | pick('name') }}"
targetPath: ./${{ parameters.component | parseEntityRef | pick('name') }}
```

Common filters: `parseEntityRef`, `pick`, `json`, `replace`. Use filters in step `input` and `output` — not in skeleton Nunjucks (skeleton uses `values.*` from `fetch:template`; see `conventions.md`).

## 6. Use the Nunjucks API in skeletons

`fetch:template` processes skeleton files with [Nunjucks](https://mozilla.github.io/nunjucks/templating.html). Pass data via the step `values` map; reference as `{{ values.name }}` in skeleton files.

**Tags beyond substitution:**

| Tag | Use when |
|-----|----------|
| `{% if %}…{% endif %}` | Conditional files or sections based on parameters |
| `{% for %}…{% endfor %}` | Iterate arrays passed in `values` |
| `{% raw %}…{% endraw %}` | Preserve literal `{{` / `{%` (GitHub Actions, Helm) |

GitHub Actions and Helm files need `{% raw %}` or `copyWithoutTemplating` — see `conventions.md`, `template-structure.md`, and `add-skeleton.md`. `fix-gotchas` and `validate --lint-skeleton` detect common mistakes.

## 7. Protect secrets

Never collect credentials with a plain `type: string` text field. Use Backstage's **Secret** field — see `parameter-widgets.md` for the form definition.

Secrets are masked in the form, review screen, and logs. In steps, reference integration secrets (e.g. `${{ secrets.user.github.token }}`) — never hardcode tokens. Exact secret paths depend on configured integrations; confirm against your RHDH instance. `fix-gotchas` flags obvious hardcoded tokens in step inputs.

## 8. Specify template type and tags

`spec.type` is required but often left as generic `service`. Set a meaningful type (`website`, `microservice`, `library`, `infrastructure`) so the Create UI groups templates. Add `metadata.tags` for subcategory filtering.

See `template-structure.md` for `metadata` and `spec.type` fields. Use the `recommended` tag to highlight golden paths.

**Why:** The Software Templates page becomes unusable at scale without type/tag filters.

## 9. Document your templates

Self-service templates need docs beyond `description`. Two levels:

**Human README** — `templates/<name>/README.md` with purpose, parameters, post-scaffold steps.

**TechDocs** (when RHDH has TechDocs configured): add `backstage.io/techdocs-ref: dir:.` annotation and `mkdocs.yml` beside `template.yaml`. See `template-structure.md` for the annotation pattern.

Documented templates show a **View TechDocs** link in the Create UI. Example: [rhdh-demo-gh/templates/deploy-component](https://github.com/rhdh-demo-gh/templates/tree/main/deploy-component).

## 10. Plan for maintenance

Templates codify best practices — outdated templates undermine trust. Treat template repos like application code:

| Practice | How the skill supports it |
|----------|---------------------------|
| Keep skeleton dependencies current | Re-run `templatize` when source repos change |
| Automated regression | `dry-run` via Scaffolder HTTP API after changes |
| Pre-merge checks | `validate` + `fix-gotchas` with zero critical findings |
| Periodic review | Schedule dependency bumps in skeleton `package.json`, Dockerfiles, CI versions |

**Failure modes to avoid:** Scaffolded apps that fail on first build, frameworks with known CVEs, broken publish/register wiring after SCM API changes.

## Bonus: Accelerate the development loop

Shrink feedback time with local RHDH:

| Approach | When |
|----------|------|
| **rhdh-local** skill | Fast local RHDH for plugin/template testing |
| Template Editor | Form UX without catalog sync |
| `validate --lint-skeleton` | Nunjucks/skeleton checks without RHDH |
| `dry-run` | End-to-end step execution against live instance |

Recommended loop: `init` → author → `validate` → Template Editor → `dry-run` → commit.

</process>

<authoring_checklist>

Before merge, confirm:

- [ ] Repo follows central `location.yaml` + `templates/<name>/` layout
- [ ] `spec.type` and `metadata.tags` set for discoverability
- [ ] EntityPicker / RepoUrlPicker / Secret used instead of free-text where appropriate
- [ ] Skeleton uses `values.*`; workflows use `{% raw %}` or `copyWithoutTemplating`
- [ ] Sensitive inputs use `ui:field: Secret`; step tokens use `${{ secrets.* }}`
- [ ] README or TechDocs present for non-trivial templates
- [ ] `validate.py` reports zero critical findings
- [ ] Template tested in Template Editor or via `dry-run`

</authoring_checklist>
