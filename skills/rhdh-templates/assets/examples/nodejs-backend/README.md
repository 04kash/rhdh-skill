# Node.js Backend Service

Scaffolds a minimal Express-style Node.js service with:

- `package.json` parameterized by component ID and Node version
- `catalog-info.yaml` for Software Catalog registration
- GitHub Actions CI workflow (with `{% raw %}` for Actions syntax)

## Parameters

| Parameter | Purpose |
|-----------|---------|
| `componentId` | Catalog entity name and npm package name |
| `description` | Shown in catalog and repository |
| `owner` | Catalog owner entity ref |
| `nodeVersion` | Node.js LTS version (`20` or `22`) |
| `repoUrl` | Target GitHub repository |

## Post-scaffold steps

1. Run `npm install` in the new repository
2. Push triggers CI via GitHub Actions
3. Confirm the component appears in the Software Catalog
