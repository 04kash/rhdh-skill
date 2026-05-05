# Agent Skills open standard

All skills in this project follow the [Agent Skills specification](https://agentskills.io/specification) — an open format for giving AI agents new capabilities. Skills use `SKILL.md` files with frontmatter metadata, progressive disclosure (description → instructions → references), and bundled `scripts/` and `references/` directories per the spec. This makes the skills portable across any agent that supports the format (VS Code, Claude Code, OpenAI Codex, Gemini CLI, pi, and others listed at [agentskills.io/clients](https://agentskills.io/clients)). The `.claude-plugin/` directory is an additional distribution layer for Claude Code's marketplace — it doesn't change the skills themselves, which remain agent-agnostic.

## Consequences

- Skill structure is constrained by the spec (frontmatter format, directory conventions, description length limits).
- New skills should be validated against the [best practices](https://agentskills.io/skill-creation/best-practices) and [description optimization](https://agentskills.io/skill-creation/optimizing-descriptions) guidance.
- The project works with any compatible agent without modification. Client-specific distribution (like `.claude-plugin/`) is layered on top, not baked in.
