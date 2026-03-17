---
name: research-ideation
description: "Guides research ideation through a 5-step goal-driven workflow: define long-term goal, build literature tree (novelty + challenge-insight), select a problem (well-established solution check), design a solution (cross-domain transfer + decomposition), validate and iterate. Also covers structured paper reading (3 depth levels). Use when: user wants to find a research direction, brainstorm ideas, build field vision, do a literature review, evaluate idea novelty, or read papers systematically. Do NOT use for comparing/ranking existing ideas (use idea-tournament) or planning a paper (use paper-planning)."
allowed-tools: "write_file edit_file read_file think_tool"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, research, ideation, literature]
---

# Research Ideation

A goal-driven workflow for finding important research problems, designing novel solutions, and building deep field understanding through structured paper reading.

## When to Use This Skill

- User wants to find a research direction or brainstorm research ideas
- User needs to do a literature review or map a research field
- User asks about evaluating whether an idea is novel or worth pursuing
- User wants to read papers more effectively or build a systematic reading habit
- User mentions "research ideation", "find a problem", "literature tree", "novelty check", "paper reading"

## Goal-Driven Research Workflow

Follow these five steps in order. Each step builds on the previous one.

### Step 1: Define a Long-Term Research Goal

Start with a goal that has both scientific and practical value. The goal should be ambitious enough to sustain multiple papers, but concrete enough to guide daily decisions.

Ask: "What is the ultimate form of this research direction? What would the world look like if this problem were fully solved?"

### Step 2: Build a Literature Tree

Map the field by constructing two complementary trees:

- **Novelty tree**: Classify existing work by milestone tasks, representative pipelines, and novel modules. This reveals WHERE the field has gaps.
- **Challenge-insight tree**: Collect technical challenges and the insights/techniques that address them. This reveals WHICH problems lack good solutions.

See [references/literature-tree.md](references/literature-tree.md) for the full construction method and four types of novelty.

### Step 3: Select a Problem

Find tasks with genuine research space. The key question: "Is this problem worth solving, or has a well-established solution already claimed this territory?"

Use the well-established solution check (4 levels) to decide whether to proceed or switch problems. Actively seek new failure cases rather than improving on known benchmarks.

See [references/problem-selection.md](references/problem-selection.md) for the full selection framework.

### Step 4: Design a Solution

Novel techniques are creative combinations of existing methods, not simple concatenations. Use two design patterns:

- **Cross-domain transfer**: Find papers in completely different domains that solve a technically similar problem, then adapt their solution.
- **Problem decomposition**: Break the problem into sub-problems, solve each via cross-domain transfer, then combine.

See [references/solution-design.md](references/solution-design.md) for the full design methodology and knowledge distillation pipeline.

### Step 5: Validate and Iterate

Run experiments on representative data. Use results to refine your understanding. If the approach fails, return to Step 3 or Step 4 with updated knowledge from the failure.

**Output artifacts**: Research direction summary (problem statement, proposed approach, novelty claim, key risks) — this becomes the input to `idea-tournament` or `paper-planning`.

See the `experiment-craft` skill for systematic debugging when experiments don't work as expected.

## Counterintuitive Ideation Rules

Prioritize these rules before regular ideation:

1. **Problem selection matters more than solution design**: Choosing WHAT to solve has more impact than HOW you solve it. A great solution to an unimportant problem is still unimportant.
2. **Pursue new failure cases, not incremental improvements**: Don't improve a technique on its original setting. Find new settings where it breaks — new failure cases on new data are contributions even if the technique itself isn't novel.
3. **If a well-established solution exists, switch problems**: Solving an already-solved problem wastes time regardless of your angle. Improvement space is too small.
4. **Technology is creative combination, not concatenation**: Novel techniques combine existing methods in non-obvious ways. Simple A-to-B pipelines are not contributions — if direct concatenation worked, the problem would have no technical challenge.
5. **When a breakthrough tool appears, apply it to YOUR roadmap**: Don't improve the tool itself on its original benchmarks. Use it to solve YOUR milestone tasks — this produces high-impact work because you combine the tool's power with your domain expertise.
6. **A paper without real contribution wastes your time**: Even if accepted, it doesn't advance the field or earn respect. Do work that genuinely moves the needle.

## Structured Paper Reading

Turn reading into structured Q&A using a paper parsing tree. Three levels of depth:

| Level | Goal | What You Can Do After |
|-------|------|----------------------|
| 1. Technical | Understand all details and terminology | Reproduce the method; explain each component |
| 2. Analytical | Know what problem it solves and why this approach | Explain the paper's motivation and design choices |
| 3. Contextual | Know its position in the literature tree | Update your field map; generate new research questions |

Write a structured summary for every paper you read. Use the template at [assets/paper-summary-template.md](assets/paper-summary-template.md).

See [references/paper-reading.md](references/paper-reading.md) for the full reading methodology and habit-building guidance.

## Handoff to Idea Tournament or Planning

When you have a research direction but want to explore multiple concrete approaches, pass to `idea-tournament` for tree-structured generation and Elo ranking before planning.

When ideation is complete — you have a problem, a proposed solution approach, and supporting literature — pass these artifacts to `paper-planning`:

| Artifact | Source Step | Used By |
|----------|-----------|---------|
| Research goal and scope | Step 1 | Story design (task definition) |
| Literature tree (novelty + challenge-insight) | Step 2 | Related work mapping, novelty claims |
| Problem statement and motivation | Step 3 | Introduction motivation paragraphs |
| Solution sketch and design rationale | Step 4 | Method section planning |
| Key failure cases to address | Step 3 | Experiment planning (stress tests) |
| Relevant prior work and their limitations | Step 2 | Baseline selection, comparison design |

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| Literature tree construction | [literature-tree.md](references/literature-tree.md) | Mapping a research field |
| Problem selection | [problem-selection.md](references/problem-selection.md) | Evaluating whether a problem is worth solving |
| Solution design | [solution-design.md](references/solution-design.md) | Designing a novel approach |
| Paper reading methodology | [paper-reading.md](references/paper-reading.md) | Reading papers effectively |
| Paper summary template | [paper-summary-template.md](assets/paper-summary-template.md) | Writing structured paper notes |
