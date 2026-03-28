# Skills

This directory contains the **skill library** for EvoSkills. Each subdirectory is a self-contained skill that extends EvoScientist with domain-specific expertise.

## How It Works

EvoScientist discovers skills by scanning `skills/*/SKILL.md`. Each skill is loaded into the agent's context when a user query matches its description. Install commands:

- **`/install-skill EvoScientist/EvoSkills@skills`** — install all skills at once
- **`/install-skill EvoScientist/EvoSkills@skills/<name>`** — install a single skill

> **Not using EvoScientist?** These skills are compatible with any coding agent via [**skills.sh**](https://skills.sh/):
> ```bash
> npx skills add EvoScientist/EvoSkills
> ```

## Available Skills

| Skill | Description |
| ----- | ----------- |
| [`research-ideation`](research-ideation/) | Research ideation, literature tree & problem finding |
| [`idea-tournament`](idea-tournament/) | Competitive idea ranking & proposal generation |
| [`paper-planning`](paper-planning/) | Research paper planning & outline generation |
| [`experiment-pipeline`](experiment-pipeline/) | Structured 4-stage experiment execution |
| [`experiment-craft`](experiment-craft/) | Experiment debugging, logging & iteration |
| [`paper-writing`](paper-writing/) | End-to-end paper writing assistance |
| [`paper-review`](paper-review/) | Automated paper review & feedback |
| [`paper-rebuttal`](paper-rebuttal/) | Rebuttal writing after peer review |
| [`academic-slides`](academic-slides/) | Academic presentation & research talk creation |
| [`experiment-iterative-coder`](experiment-iterative-coder/) | Iterative code refinement (plan → code → evaluate → refine cycles) |
| [`evo-memory`](evo-memory/) | Persistent research memory & self-evolution |
| [`paper-navigator`](paper-navigator/) | End-to-end academic paper discovery, reading & organization |

## Contributing a Skill

### Skill Anatomy

Each skill is a directory under `skills/`:

```
my-skill/
  SKILL.md          # required — frontmatter + body
  references/       # optional — docs loaded into agent context
  assets/           # optional — files used in agent output (templates, images)
```

### SKILL.md Frontmatter

```yaml
---
name: my-skill
description: "One-line summary. Key method/framework keywords. Use when: specific triggers."
allowed-tools: "write_file edit_file read_file think_tool"
metadata:
  author: YourName
  version: '1.0.0'
  tags: [relevant, keywords]
---
```

### Description Tips

The existing skills use a common description pattern that works well for routing accuracy:

```
"[1-sentence summary]. [Core method/framework keywords].
 Use when: [specific triggers].
 Do NOT use for [scenarios that belong to other skills]."
```

The `Do NOT use for` clause helps the agent distinguish skills with overlapping domains — for example, `paper-planning` says `Do NOT use for actual writing (use paper-writing)`. This isn't required, but it's helpful when your skill shares keywords with others.

### Body

After the frontmatter, the body contains the skill's full instructions: workflow steps, rules, examples, and cross-references to `references/` files. Structure varies by skill type — see existing skills for patterns.

## Improving an Existing Skill

| Change | Example |
|--------|---------|
| Content fix | Correct a rule, add a missing example |
| Reference update | Update a guide in `references/` |
| Cross-skill consistency | Ensure related skills agree on shared terms or outputs |

Workflow:

1. Edit the skill files in `skills/<name>/`
2. Validate structure: the directory must contain `SKILL.md` with valid frontmatter
3. Manual test: install the skill and try it in EvoSci (`/install-skill path/to/EvoSkills/skills/<name>`)
4. If you changed the **description**, we recommend running eval with `skill-creator` (see [Testing & Evaluation](#testing--evaluation))

## Adding a New Skill

### 1. Bootstrap

You can ask EvoSci to create a skill for you using the built-in `skill-creator`:

```text
"Create a new skill called my-new-skill in path/to/EvoSkills/skills"
```

Or manually create `skills/my-new-skill/SKILL.md` following the frontmatter format above.

### 2. Write the Skill

- Write a clear `description` in the frontmatter — see [Description Tips](#description-tips) for the recommended pattern
- Write the body with workflow steps, rules, and examples
- Look at existing skills for inspiration

### 3. Test

Install and try the skill in a real EvoSci session:

```text
/install-skill path/to/EvoSkills/skills/my-new-skill
```

### 4. Update README

Add your skill to the table in this file and to the descriptions in the top-level `README.md`.

## Testing & Evaluation

### Manual Testing

The simplest approach — install the skill and use it in real tasks:

1. Start an EvoSci session
2. Install your skill: `/install-skill path/to/EvoSkills/skills/<name>`
3. Try queries that should trigger the skill, and queries that should not
4. Verify the skill produces correct output when loaded

This is sufficient for most content changes.

### Automated Eval with `skill-creator` (Recommended for Description Changes)

EvoScientist ships with a built-in `skill-creator` skill that can systematically evaluate and optimize skill descriptions. To use it:

1. Start an EvoSci session (`skill-creator` is built-in, no extra install needed)
2. Ask it to evaluate or optimize your skill's description:
   ```text
   "Optimize the description for path/to/EvoSkills/skills/paper-planning"
   ```
3. `skill-creator` will:
   - Generate 20 trigger eval queries (10 should-trigger, 10 should-not-trigger)
   - Let you review and edit the queries
   - Run an automated eval + improvement loop (train/test split, iterative refinement)
   - Report the best description with scores

This is the same methodology used to optimize the existing 10 EvoSkills descriptions.

See the [`skill-creator` SKILL.md](https://github.com/EvoScientist/EvoScientist/tree/main/EvoScientist/skills/skill-creator) for full details on the eval workflow.

## Checklist

Use the appropriate tier based on your change:

### Content Changes (no description edit)
- [ ] SKILL.md frontmatter is valid (name, description, allowed-tools)
- [ ] Cross-references to `references/` files are correct
- [ ] Manual test: install skill, run a sample query in EvoSci

### Description Changes
- [ ] All of the above, plus:
- [ ] Tested with `skill-creator` eval (recommended) or thorough manual testing

### New Skill
- [ ] All of the above, plus:
- [ ] README.md updated with skill entry

## Quick Reference

| Task | Command |
|------|---------|
| Install skill for testing | `/install-skill path/to/EvoSkills/skills/my-skill` (in EvoSci session) |
| Install all skills | `/install-skill path/to/EvoSkills/skills` (in EvoSci session) |
| Eval with skill-creator | Ask EvoSci: `"Optimize the description for path/to/skills/my-skill"` |
| Create a new skill | Ask EvoSci: `"Create a new skill called my-skill in path/to/EvoSkills/skills"` |
