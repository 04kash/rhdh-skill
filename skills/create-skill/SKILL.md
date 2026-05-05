---
name: create-skill
description: Create new agent skills following the Agent Skills open standard (agentskills.io). Interviews the user relentlessly about intent, scope, and edge cases before drafting. Covers SKILL.md structure, frontmatter, progressive disclosure, description optimization, script bundling, and review. Use when the user wants to create a skill, write a skill, build a new skill, make a skill, draft a SKILL.md, or mentions "create-skill". Also use when asked to package expertise, workflows, or domain knowledge into a reusable skill.
---

# Create Skill

Create agent skills following the [Agent Skills open standard](https://agentskills.io/specification).

## Phase 1: Interview

Interview the user relentlessly about every aspect of this skill until reaching shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask questions one at a time. If a question can be answered by exploring the codebase, explore the codebase instead.

Cover these areas before writing anything:

- **What task does this skill cover?** What specific problem does it solve? What does the user do today without it?
- **Scope boundaries.** What should this skill NOT do? What adjacent tasks should be left to other skills or the agent's general capabilities?
- **Input/output.** What does the user provide? What does the skill produce? Are there specific formats?
- **Edge cases.** What goes wrong? What are the common mistakes? What gotchas would a new user hit?
- **Success criteria.** How do you know the skill worked correctly?
- **What can be scripted?** Actively look for operations that can be deterministic code rather than LLM instructions. Scripts are cheaper, faster, and more reliable. The more of a skill that runs as scripts, the less compute it burns. Only leave judgment calls and creative reasoning to instructions.
- **References needed?** Is there domain knowledge too large for the main SKILL.md that should live in separate files?
- **Existing patterns.** Are there similar skills or workflows to draw from? Check the codebase for conventions.
- **Platform constraints.** Will this skill run on macOS, Windows, and Linux? Scripts must handle path separators, temp directories, and shell differences across platforms.

Do not proceed to Phase 2 until the user confirms the scope is complete.

## Phase 2: Draft the SKILL.md

Write the skill following the spec. Read `references/spec-guide.md` for the full format reference before drafting.

### Frontmatter

```yaml
---
name: skill-name        # lowercase, hyphens, max 64 chars
description: |           # max 1024 chars — this is the ONLY triggering mechanism
  What the skill does. Use when [specific triggers].
  Also use when [additional triggers].
---
```

The description must be slightly "pushy" — agents tend to undertrigger. Include both what the skill does AND specific phrases/contexts that should activate it.

### Body structure

Follow progressive disclosure — three loading levels:

1. **Metadata** (~100 tokens): `name` and `description` loaded at startup for all skills
2. **Instructions** (< 500 lines): Full SKILL.md body loaded when skill activates
3. **Resources** (as needed): `references/`, `scripts/`, `assets/` loaded only when required

Keep the SKILL.md body under 500 lines. If approaching this limit, split domain-specific content into `references/` files with clear pointers about when to read them.

### Writing patterns

- Use imperative form: "Run the command" not "You should run the command"
- Define output formats with templates when the output structure matters
- Include concrete examples showing input → output
- Add gotchas sections for common mistakes
- Use checklists for multi-step workflows
- Tell the agent *when* to load each reference file: "Read `references/api-errors.md` if the API returns a non-200 status code" is better than "see references/ for details"

## Phase 3: Description Optimization

The description is the only thing agents see at startup. Read `references/description-guide.md` for the full optimization process.

Quick validation:

1. Write 5 should-trigger queries (different phrasings, including ones that don't name the skill directly)
2. Write 5 should-not-trigger queries (near-misses that share keywords but need different skills)
3. Check: would the description correctly distinguish these?
4. Revise if needed — broaden for missed triggers, narrow for false triggers
5. Verify under 1024 characters

## Phase 4: Scripts

Read `references/scripts-guide.md` for the full guide.

**Bias toward scripts.** Every deterministic operation should be a script, not an instruction. Scripts are cheaper (no LLM tokens), faster (no reasoning), and more reliable (no hallucination). Instructions should only cover judgment calls, creative reasoning, and decision-making that genuinely requires LLM capability.

For each piece of the skill's workflow, ask: "Could a script do this?" If yes, write the script.

Examples of what should be scripts:
- Validation (input format, required fields, schema compliance)
- File generation from templates
- Data extraction and transformation
- API calls with structured responses
- Setup and environment checks
- Output formatting

Examples of what should stay as instructions:
- Deciding between architectural approaches
- Reviewing code for quality or style
- Explaining tradeoffs to the user
- Creative writing or design decisions

Key patterns:
- **Python without dependencies**: stdlib only, `argparse` for CLI parsing
- **Python with dependencies**: PEP 723 inline metadata with `uv run`
- **All scripts**: Structured output (JSON when piped), clear exit codes, descriptive `--help`

## Phase 5: Review

Before presenting the final skill, verify against this checklist:

- [ ] `name` is lowercase, hyphens only, max 64 chars
- [ ] `description` is under 1024 chars and includes trigger phrases
- [ ] `description` is slightly pushy — covers edge phrasings that should activate the skill
- [ ] SKILL.md body is under 500 lines
- [ ] Instructions use imperative form
- [ ] References are split out with clear "when to read" pointers
- [ ] Scripts (if any) have shebangs, structured output, and `--help`
- [ ] No time-sensitive information (URLs to specific versions, dates that will go stale)
- [ ] Consistent terminology throughout
- [ ] Concrete examples included for non-obvious workflows
