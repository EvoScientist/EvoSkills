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
| [`research-ideation`](research-ideation/) | Literature grounding, idea generation, tournament ranking & proposal generation |
| [`paper-planning`](paper-planning/) | Research paper planning & outline generation |
| [`experiment-pipeline`](experiment-pipeline/) | Structured 4-stage experiment execution |
| [`experiment-craft`](experiment-craft/) | Experiment debugging, logging & iteration |
| [`paper-writing`](paper-writing/) | End-to-end paper writing assistance |
| [`paper-review`](paper-review/) | Automated paper review & feedback |
| [`paper-rebuttal`](paper-rebuttal/) | Rebuttal writing after peer review |
| [`paper-figures`](paper-figures/) | Publication-ready matplotlib figures from tabular data |
| [`academic-slides`](academic-slides/) | Academic presentation & research talk creation |
| [`experiment-iterative-coder`](experiment-iterative-coder/) | Iterative code refinement (plan → code → evaluate → refine cycles) |
| [`evo-memory`](evo-memory/) | Persistent research memory & self-evolution |
| [`paper-navigator`](paper-navigator/) | Academic paper discovery, evaluation & reading |
| [`research-survey`](research-survey/) | Structured literature survey synthesis |
| [`paper-graph`](paper-graph/) | Lineage map of a research field as Mermaid diagrams (challenges → solutions → per-solution evolution) |
| [`nano-banana`](nano-banana/) | AI-generated presentation slides & illustrations via Gemini image generation |
| [`evomath-tao`](evomath-tao/) | Tao-style olympiad-grade proof workflow with calibrated abstention |

## Contributing a Skill

### Skill Anatomy

Each skill is a directory under `skills/`:

```
my-skill/
  SKILL.md          # required — frontmatter + body
  references/       # optional — docs loaded into agent context
  assets/           # optional — files used in agent output (templates, images)
  scripts/          # optional — helper scripts the agent runs
  requirements.txt  # optional — Python packages the skill needs
  EXPERT.md         # optional — makes the skill dispatchable as an expert
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

All four top-level fields and the three `metadata` fields are required; CI rejects a `SKILL.md` that misses any of them. `name` matches the directory name. Keep the frontmatter to these fields — it is the part of a skill every agent sees before deciding to load it, so anything that is not used for routing or indexing does not belong there. The one addition is `metadata.type` for [expert skills](#expert-skills).

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

### Scripts and Dependencies

Skills are installed into many environments (EvoScientist, and other coding agents via skills.sh), so a `SKILL.md` must not assume where the skill lives or which Python runs it.

- **Write script paths relative to the skill's own directory**, and say so once in the `SKILL.md` ("Script paths in this document are relative to this skill's directory"). The agent knows that directory — it is where it read `SKILL.md` from — and resolves the path against it, wherever the skill happens to be installed:

  ```text
  python scripts/fetch_paper.py --url <URL>                        # correct
  python /skills/my-skill/scripts/fetch_paper.py                   # one harness's mount path
  python skills/my-skill/scripts/fetch_paper.py                    # this repo's layout
  python <skill-dir>/scripts/fetch_paper.py                        # placeholder the agent has to guess
  ```

- **Declare dependencies.** If the skill needs packages outside the standard library — in its scripts or in the code it asks the agent to write — list them in a `requirements.txt` at the skill root and add one install line to `SKILL.md`, e.g. `pip install pillow google-genai` (also listed in `requirements.txt` at the skill root).
- **Do not name an interpreter.** Write plain `python`, never `uv run python` or an absolute interpreter path. Researchers often drive several Python environments at once; the agent should install into and run in whichever one the user is working in.

All Python in the repository, including every skill's `scripts/`, is linted in CI with ruff.

### Expert Skills

A skill can also be dispatched by EvoScientist as a background **expert** — an agent with its own persona that works on a task and reports back. To make a skill an expert, add an `EXPERT.md` next to `SKILL.md`:

- No frontmatter. The directory name is the expert's name, and the file's presence is the declaration.
- Open with the scope line `> This file defines a dispatchable expert; outside the EvoScientist expert container, ignore it.`
- `## Persona` — who the expert is, what its task must name (inputs, output path), and when to halt with an error instead of improvising.
- `## Envelope` — the final message: exactly one JSON object with `status`, `output_path`, `summary`, and `metadata`.

Also add `type: [skill, expert]` under `metadata` so catalog listings can show it. Do not add actor fields such as `role`, `byline`, `capability_tags`, `avatar_hint`, or `default_dispatch` to the frontmatter. `SKILL.md` stays plain knowledge that any agent can load and follow in-turn; `EXPERT.md` is an additive layer other harnesses ignore.

### Orchestration Scripts

When a skill's value is a reliable multi-step loop — fan out over N items, retry the failed subset, stop on a convergence gate — the control flow can ship as a JavaScript file under `scripts/` that EvoScientist's code interpreter runs, dispatching sub-agents with `task()`. Keep judgement in prose and control flow in the script, and keep the prose workflow in `SKILL.md` as the fallback for environments without the interpreter.

[`paper-review`](paper-review/) is the reference for both: see its `EXPERT.md` and `scripts/five_aspect_review.js`.

## Improving an Existing Skill

| Change | Example |
|--------|---------|
| Content fix | Correct a rule, add a missing example |
| Reference update | Update a guide in `references/` |
| Cross-skill consistency | Ensure related skills agree on shared terms or outputs |

Workflow:

1. Edit the skill files in `skills/<name>/`
2. Bump `metadata.version` in the skill's `SKILL.md`, even for a small fix. EvoScientist's WebUI offers an update for an installed skill only when the version here is higher than the installed one, so a change without a bump never reaches those users. Use dotted numbers such as `1.2.3`.
3. Validate: run the [CI checks](#ci-checks) locally
4. Manual test: install the skill and try it in EvoSci (`/install-skill path/to/EvoSkills/skills/<name>`)
5. If you changed the **description**, we recommend running eval with `skill-creator` (see [Testing & Evaluation](#testing--evaluation))

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
- If the skill ships scripts or needs packages, follow [Scripts and Dependencies](#scripts-and-dependencies)
- Look at existing skills for inspiration

### 3. Test

Install and try the skill in a real EvoSci session:

```text
/install-skill path/to/EvoSkills/skills/my-new-skill
```

### 4. Update README

Add your skill to the table in this file, and to the catalog table, detail section, and pipeline diagram in the top-level `README.md` and `README.zh-CN.md`.

## Testing & Evaluation

### CI Checks

CI runs ruff, skill validation, MCP validation and the test suite on every pull request; all four must pass before a merge. Run them from the repository root before pushing:

```bash
pip install pytest pyyaml httpx python-dotenv "ruff==0.15.8"
python .github/scripts/validate_skills.py --base origin/main   # frontmatter + version bumps
ruff check . && ruff format --check .                          # all Python in the repository
pytest tests -q                                                # consistency checks + script tests
```

Skill validation checks the frontmatter of every skill (required fields, `name` equal to the directory name, a quoted dotted-number `metadata.version`, `EXPERT.md` matching `metadata.type`). With `--base`, it also fails when a skill has changed files but its version is not higher than on the base branch — which is what CI runs on pull requests. Without `--base` it only checks the frontmatter.

The test suite under `tests/` checks what the validator does not: a description is at most 1024 characters (a skill named as a known exception in the test file is reported without failing), a skill's step overview matches its step sections, relative links and `references/` / `assets/` / `scripts/` paths in a skill's Markdown resolve, and every skill has a row in the tables of `README.md`, `README.zh-CN.md` and this file. It also tests the validation scripts themselves.

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

This is the same methodology used to optimize the existing EvoSkills descriptions.

See the [`skill-creator` SKILL.md](https://github.com/EvoScientist/EvoScientist/tree/main/EvoScientist/skills/skill-creator) for full details on the eval workflow.

## Checklist

Use the appropriate tier based on your change:

### Content Changes (no description edit)
- [ ] [CI checks](#ci-checks) pass locally (frontmatter has name, description, allowed-tools, metadata)
- [ ] `metadata.version` is bumped (when changing an existing skill)
- [ ] Cross-references to `references/` files are correct
- [ ] Script paths are relative to the skill directory; dependencies are in `requirements.txt` with a matching `pip install` line in `SKILL.md`
- [ ] Manual test: install skill, run a sample query in EvoSci

### Description Changes
- [ ] All of the above, plus:
- [ ] Tested with `skill-creator` eval (recommended) or thorough manual testing

### New Skill
- [ ] All of the above, plus:
- [ ] This file, `README.md`, and `README.zh-CN.md` updated with the skill entry

## Quick Reference

| Task | Command |
|------|---------|
| Install skill for testing | `/install-skill path/to/EvoSkills/skills/my-skill` (in EvoSci session) |
| Install all skills | `/install-skill path/to/EvoSkills/skills` (in EvoSci session) |
| Eval with skill-creator | Ask EvoSci: `"Optimize the description for path/to/skills/my-skill"` |
| Create a new skill | Ask EvoSci: `"Create a new skill called my-skill in path/to/EvoSkills/skills"` |
| Validate skills | `python .github/scripts/validate_skills.py --base origin/main` |
| Lint scripts | `ruff check . && ruff format --check .` |
| Run the tests | `pytest tests -q` |
