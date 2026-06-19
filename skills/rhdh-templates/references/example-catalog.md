# example-catalog — Reference Template Catalog

<required_reading>

- `assets/example-catalog.json` (data source — do not edit by hand during normal authoring)

</required_reading>

<process>

Surface curated reference templates customers reach for most often. Use when the user asks "what templates exist?", "show me an example", "what do customers usually build?", or before `create` / `templatize` to pick a study reference.

## Step 1: Parse intent

Extract from the user's message:

- **Stack** — go, nodejs, java, spring-boot, quarkus, python, ai, rag, ansible, …
- **Workflow** — new service, import existing, add CI/GitOps, AI agent, plugin scaffold
- **Constraints** — offline/local only, official sources only, recommended starters

## Step 2: Query the catalog

```bash
python <skill-dir>/scripts/list_examples.py --match "<user intent>" --limit 5 --json
```

Use filters when intent is narrow:

```bash
python <skill-dir>/scripts/list_examples.py --category backend --recommended --json
python <skill-dir>/scripts/list_examples.py --stack python --json
python <skill-dir>/scripts/list_examples.py --local-only --json
```

Consume full JSON output. Never pipe through `head`, `tail`, or `grep`.

## Step 3: Present results

For each match, show:

1. **Title** and **category**
2. **URL** to upstream `template.yaml` (or bundled `assets/examples/` path)
3. **Why it matches** — stack, use case, or recommended tag
4. **Next step** — "Study this before authoring" or "Open bundled `assets/examples/<name>` for offline validation"

Repeat the catalog **disclaimer** once (see below).

## Step 4: Offer handoff

Ask whether to:

- **`create`** — build a similar template from scratch
- **`templatize`** — convert their existing codebase using the reference as a pattern guide
- **`validate`** — check their current template against conventions

If the user only wanted a list, stop after Step 3.

---

## Disclaimer

Upstream templates in GitHub are **learning aids**, not production-ready golden paths. Always validate, test in a safe RHDH environment, and customize for your organization's standards. See the upstream repo caution in [red-hat-developer-hub-software-templates](https://github.com/redhat-developer/red-hat-developer-hub-software-templates).

## Primary sources

| Source | Repo | When to study it |
|--------|------|------------------|
| Official library | [red-hat-developer-hub-software-templates](https://github.com/redhat-developer/red-hat-developer-hub-software-templates) | Backend + CI, catalog import, Tekton/ArgoCD, Ansible, plugin scaffolding |
| AI quickstarts | [aiquickstarttemplates](https://github.com/redhat-developer/aiquickstarttemplates) | RAG chatbots, IT agents, LLM serving on OpenShift AI |
| AI Lab samples | [ai-lab-template](https://github.com/redhat-ai-dev/ai-lab-template) | Smaller AI samples (RAG, chatbot, codegen) |
| Bundled skill examples | `assets/examples/` in this skill | Local validation, minimal patterns without cloning repos |

## Categories (customer demand order)

1. **backend** — Go, Node.js, Spring Boot, Quarkus, Python services with CI (most common golden path)
2. **catalog** — Register existing repos into the Software Catalog
3. **cicd / gitops** — Tekton pipelines, ArgoCD bootstrap
4. **automation** — Ansible Automation Platform job templates
5. **ai** — RAG, agents, LLM serving (fastest-growing ask)
6. **plugin** — Dynamic frontend/backend plugin scaffolding
7. **docs** — TechDocs starter
8. **starter** — Bundled minimal examples for local learning

Templates marked **recommended** upstream (`tags: recommended` in their `template.yaml`) are the default "start here" references.

## How to use references during authoring

| Situation | Action |
|-----------|--------|
| User describes a new template | Run `--match` on their description; suggest top 1–3 upstream URLs to study |
| Match has `local_bundled` | Also open `assets/examples/<name>/` for offline validation patterns |
| Templatizing existing code | Compare detected stack from `analyze.py` to `--stack` filter |
| AI / RAG / agent request | Prefer `ai-quickstart-templates` over generic backend examples |
| Import-only workflow | Point at `register-component` |

Do not copy upstream skeletons wholesale into customer repos without review — study their **parameter forms**, **step sequences**, and **conventions**, then adapt.

## Catalog maintenance

Data lives in `assets/example-catalog.json`. Refresh when:

- `templates.yaml` changes in the official library
- New AI quickstart templates ship
- Field teams report a recurring customer pattern not yet listed

Run `list_examples.py --json` after edits to verify parsing.

</process>

<success_criteria>

- `list_examples.py --json` returns at least one relevant match for the stated intent, or clearly reports zero matches with suggested broader filters
- User receives clickable upstream URLs plus local bundled paths when available
- Disclaimer stated once per session when showing upstream templates

</success_criteria>
