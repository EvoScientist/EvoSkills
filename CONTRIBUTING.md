# Contributing to EvoSkills

Welcome! EvoSkills is the community-driven skill repository for [EvoScientist](https://github.com/EvoScientist/EvoScientist). There are two main ways to contribute:

| What | Guide |
|------|-------|
| Add or improve a **skill** | [`skills/README.md`](./skills/README.md) |
| Add an **MCP server** | [`mcp/README.md`](./mcp/README.md) |

## Prerequisites

- **EvoScientist** installed (`pip install evoscientist` or `pip install -e ".[dev]"` from source) and configured (`EvoSci onboard`)
- **EvoSkills** cloned:
  ```bash
  git clone https://github.com/EvoScientist/EvoSkills.git
  cd EvoSkills
  ```
- An LLM API key configured

## Repository Layout

```
EvoSkills/
  skills/                    # 10 skills (one directory each)
    paper-planning/
    paper-writing/
    research-ideation/
    ...
  mcp/                       # MCP server marketplace (one YAML each)
    arxiv.yaml
    exa.yaml
    ...
```

See [`skills/README.md`](./skills/README.md) and [`mcp/README.md`](./mcp/README.md) for the anatomy of each type.

## Commit & PR Standards

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) with the skill or server name as scope:

```
feat(paper-planning): add fallback narrative section
fix(evo-memory): correct IVE trigger condition in memory-schema.md
docs(experiment-pipeline): add 20% regression threshold note
feat(mcp): add my-new-server
```

### Pull Requests

- Title: brief summary under 70 characters
- Body: describe what changed and why
- **Include eval scores** if a skill description was optimized with `skill-creator`
