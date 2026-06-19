# RHDH Templates Examples

Bundled worked examples for **local learning and validation**. Each passes `validate.py` with zero critical findings.

For the full curated catalog of upstream reference templates (official library, AI quickstarts), run:

```bash
python skills/rhdh-templates/scripts/list_examples.py --recommended --json
```

See [../references/example-catalog.md](../references/example-catalog.md) for category guide and customer-demand context.

| Example | Stack | Highlights |
|---------|-------|------------|
| [minimal-template](./minimal-template/) | Generic | Starter scaffold from `init` — single parameter form |
| [nodejs-backend](./nodejs-backend/) | Node.js | `EntityPicker`, `RepoUrlPicker`, publish + register, GitHub Actions `{% raw %}` |
| [java-springboot](./java-springboot/) | Java / Spring Boot | Maven `pom.xml`, `Application.java`, multi-section forms |

These bundled examples correspond to upstream references in [red-hat-developer-hub-software-templates](https://github.com/redhat-developer/red-hat-developer-hub-software-templates): `nodejs-backend` → `templates/github/nodejs-backend`, `java-springboot` → `templates/github/spring-boot-backend`.

Validate any example locally:

```bash
python skills/rhdh-templates/scripts/validate.py \
  --path skills/rhdh-templates/assets/examples/nodejs-backend \
  --repo --lint-skeleton --json
```

Replace `nodejs-backend` with `java-springboot` or `minimal-template` as needed.
