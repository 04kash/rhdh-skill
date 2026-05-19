# XML Structure Guide for Skills

XML tags help agents parse complex prompts unambiguously — especially when a skill mixes instructions, context, examples, and variable inputs. Wrapping each type of content in its own tag reduces misinterpretation.

## When to use XML vs markdown

| Pattern | Structure | Rationale |
|---|---|---|
| **Simple skill** (single workflow) | Markdown headings | Not enough structure to benefit from XML overhead |
| **Router skill** (multiple commands) | XML tags for sections, markdown within | Sections are semantically distinct — XML makes boundaries unambiguous |
| **Domain expertise skill** (full lifecycle) | XML tags for sections, markdown within | Many interleaved concerns need clear separation |

**Rule of thumb:** If a skill has an intake question, a routing table, and essential principles, use XML tags. They give agents clear section boundaries that markdown headings can't reliably provide — headings blend together in long prompts, while XML tags create unambiguous containers.

## Suggested tag patterns

These are patterns that have worked well in practice. Invent new tags as needed — the goal is descriptive, consistent names (lowercase, underscored) that make section boundaries unambiguous.

### Common structural tags

| Tag | Purpose | Example use |
|---|---|---|
| `<essential_principles>` | Rules that apply across all commands | Cross-cutting constraints |
| `<intake>` | User-facing menu or intake question | "What do you want to do?" |
| `<routing>` | Table mapping responses to workflows/references | After `<intake>` |
| `<reference_index>` | Reference files with "load when..." guidance | Skills with multiple references |
| `<success_criteria>` | Observable, verifiable outcomes checklist | Measurable completion |
| `<cli_setup>` | CLI initialization — path discovery, variable setup | Skills that depend on a CLI tool |
| `<context_scan>` | Environment detection run on invocation | Adapting to environment state |
| `<skills_index>` | Related skills with paths | Cross-skill routing |

### Other patterns seen in the wild

| Tag | Purpose |
|---|---|
| `<principle name="...">` | Named principle inside `<essential_principles>` for cross-referencing |
| `<cli_commands>` | CLI command reference |
| `<workflows_index>` | Workflow files listing |
| `<templates_index>` | Template files listing |
| `<tracking_system>` | Activity logging and context persistence |
| `<inline_*>` | Inline mini-workflows (e.g., `<inline_status_check>`) |

## Patterns

### Named principles

Use `<principle name="...">` when principles need to be referenced by name from other sections or workflow files:

```xml
<essential_principles>

<principle name="token_safety">
Never read `.jira-token` into context. Always use shell substitution: `"$(cat "$TOKEN_FILE")"`.
Tokens in context risk leaking into outputs and persist across compacted sessions.
</principle>

<principle name="data_sources">
Plugin package definitions come from rhdh-plugin-export-overlays on GitHub.
Always fetch the OCI reference from `spec.dynamicArtifact` — do NOT construct OCI URLs manually.
Manually constructed URLs miss the PR number and commit SHA that CI embeds.
</principle>

</essential_principles>
```

When principles are short and don't need cross-referencing, plain `<essential_principles>` with bullet points or markdown content inside works fine.

### Intake → routing flow

The `<intake>` and `<routing>` tags form a natural pair. Keep them adjacent:

```xml
<intake>
## What would you like to do?

1. **Create an issue** — New feature, epic, story, task, or bug
2. **Refine an issue** — Size, complete fields, challenge scope
3. **Plan the sprint** — Capacity, assignments, sprint goals

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| 1, "create", "new issue" | `references/to-issue.md` |
| 2, "refine", "groom" | `references/refine.md` |
| 3, "plan", "sprint" | `references/plan.md` |
</routing>
```

### Reference index with conditional loading

The `<reference_index>` tag replaces a flat markdown list with structured guidance about when each reference should be loaded:

```xml
<reference_index>

| Reference | Purpose | Path |
|-----------|---------|------|
| sources | Lifecycle URLs per platform | `references/sources.md` |
| auth | Token setup and curl patterns | `../rhdh-jira/references/auth.md` |

</reference_index>
```

### Nesting markdown inside XML

XML tags are containers — use markdown freely inside them for formatting, tables, code blocks, and lists. This mixes the structural clarity of XML with the readability of markdown:

```xml
<essential_principles>

- **Copy-sync first** — all edits go in `rhdh-customizations/`, never in `rhdh-local/` directly.
  After every edit, run `rhdh local apply` to sync.
- **Use scripts** — run `rhdh local up` / `rhdh local down`, never `podman compose` directly.

</essential_principles>
```

## Anti-patterns

**Don't wrap everything in XML.** Simple skills with a linear workflow don't benefit — XML just adds noise. Only use XML when the skill has semantically distinct sections that need unambiguous boundaries.

**Don't nest XML deeply.** One level of nesting (`<essential_principles>` → `<principle>`) is the maximum. Deeper nesting creates parsing ambiguity and is harder to read.

**Prefer existing tag names when they fit.** If your skill has an intake question, `<intake>` is clearer than `<user_prompt>` or `<menu>`. But don't force a tag name that doesn't describe your content — invent a better one.

**Don't put XML tags inside code blocks as examples and expect them to be parsed.** If showing XML as an example, use fenced code blocks. Only bare XML tags in the skill body are treated as structural.
