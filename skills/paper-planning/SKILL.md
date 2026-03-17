---
name: paper-planning
description: "Guides pre-writing planning for academic papers with 4 structured steps: story design (task-challenge-insight-contribution-advantage), experiment planning (comparisons + ablations), figure design (pipeline + teaser), and 4-week timeline management. Includes counterintuitive planning tactics (write a mock rejection letter to identify weaknesses before writing, narrow before broad claims, design ablations first). Use when: user wants to plan a paper before writing, design story/contributions, plan experiments, create figure sketches, set a writing timeline, or write a pre-emptive rejection letter for planning purposes. Do NOT use for actual writing (use paper-writing), running experiments (use experiment-pipeline), self-reviewing a finished draft (use paper-review), or finding research problems (use research-ideation)."
allowed-tools: "write_file edit_file read_file think_tool"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, research, writing, academic-writing, experiment-design]
---

# Paper Planning

A structured approach to planning academic papers before writing begins. Covers four key activities: Story design, Experiment planning, Figure design, and Timeline management.

## When to Use This Skill

> If you don't yet have an idea, use the `research-ideation` skill first to find a problem and design a solution.

- User wants to plan a paper before writing
- User asks about structuring a paper's story or contributions
- User needs to plan experiments (comparisons, ablations)
- User wants to design pipeline figures or teaser figures
- User asks about writing timelines or submission schedules

## Planning Overview

Paper planning follows four steps, ideally completed **before** writing begins:

```
Step 1: Story Design     → What is the narrative? What are the contributions?
Step 2: Experiment Plan   → What experiments prove our claims?
Step 3: Figure Design     → How do we visually communicate the method?
Step 4: Timeline          → When does each section get written?
```

## Counterintuitive Planning First

Prioritize these counterintuitive rules before regular planning:

1. **Write your rejection letter first**: Draft the top-5 likely rejection comments ("limited novelty", "missing baseline", "not robust", etc.), then plan experiments that directly preempt each one.
2. **Narrow claim before broad claim**: Define the smallest defensible core claim first. Expand only after evidence is strong. Over-broad claims fail review more often than narrow strong claims.
3. **Design ablations before polishing method text**: If a module cannot be ablated cleanly, its contribution claim is weak.
4. **Allocate compute to stress tests, not only benchmarks**: A single convincing stress-test figure often contributes more than multiple small benchmark gains.
5. **Plan a fallback narrative now**: If SOTA gain is marginal, predefine a secondary value proposition (efficiency, robustness, fewer assumptions, wider applicability).

See [references/counterintuitive-planning.md](references/counterintuitive-planning.md)

---

## Step 1: Story Design

The "story" is the logical narrative that connects the problem, insight, method, and results.

### Reverse Engineering the Story

Work backwards to build the story:

1. **What is the technical problem?** — The specific challenge that existing methods cannot solve well
2. **What are our contributions?** — The concrete technical novelties
3. **What are the benefits and new insights?** — What advantages does our approach provide?
4. **How do we lead into the challenge?** — How to frame the task and previous methods to naturally arrive at the challenge

Then write forward: Task → Previous methods → Challenge → Our contributions → Advantages

### Core Elements to Define

Before writing any section, clearly articulate:

| Element | Question | Example |
|---------|----------|---------|
| Task | What problem does this paper address? | "Real-time 3D scene reconstruction" |
| Challenge | Why can't existing methods solve it well? | "Cannot handle dynamic objects efficiently" |
| Insight | What key observation drives our approach? | "Motion patterns are temporally sparse" |
| Contribution | What do we propose? | "Sparse temporal attention for dynamic regions" |
| Advantage | Why is our approach better? | "Reduces computation while preserving quality" |

### Starting Point: Pipeline Figure Sketch

> Start by drawing a pipeline figure sketch. This forces you to clarify the overall method before writing.

The pipeline figure sketch serves as the paper's visual backbone:
- Draw it before writing anything
- It reveals whether the method is clear enough to explain
- It identifies the novel modules vs. standard components
- It determines subsection structure for the Method section

See [references/story-design.md](references/story-design.md)

---

## Step 2: Experiment Planning

Plan experiments **before** writing to avoid discovering gaps late.

### Two Categories of Experiments

**Comparison Experiments** — Prove our method is better:
- Which baseline methods to compare against?
- Which datasets and metrics?
- What is the evaluation protocol?

**Ablation Studies** — Prove each module is effective:
- Part 1: One big table showing impact of core contributions
- Part 2: Several small tables for design choices and hyperparameters

### Planning Checklist

- [ ] List all comparison baselines (recent, relevant, SOTA)
- [ ] Define evaluation metrics (standard for the task)
- [ ] Identify datasets (standard benchmarks + challenging demos)
- [ ] List ablation configurations (remove each core component)
- [ ] Plan design-choice tables (hyperparameters, input quality, alternatives)
- [ ] Plan demo scenarios (challenging data to showcase upper limit)

See [references/experiment-planning.md](references/experiment-planning.md)

### Experiment Plan Template

Use the template at [assets/experiment-plan-template.md](assets/experiment-plan-template.md) to organize your experiment plan.

---

## Step 3: Figure Design

> The pipeline figure is for highlighting novelty, not for making readers understand. The Method text is what makes readers understand.

### Pipeline Figure Principles

- **Highlight novelty**: The pipeline figure showcases what is new, not just the workflow
- **Differentiate from prior work**: The figure must look different from previous methods
- **Novel modules stand out**: If the overall pipeline is standard, zoom in on novel modules
- Focus on clarity of the novel parts; standard components can be simplified

### Teaser Figure

The teaser (usually Figure 1) shows the key result at a glance:
- Place it at the top of the first page
- Should be immediately compelling
- Reference it from the Introduction

### Visual Quality Matters

Visual polish directly influences review outcomes. See [references/figure-design.md](references/figure-design.md) for the full visual quality guide (pipeline figures, tables, typography)

---

## Step 4: Timeline

### 4-Week Countdown

Start writing **at least 1 month** before the deadline.

| Week | Tasks |
|------|-------|
| **4 weeks before** | 1. Organize story (core contribution, module motivations). 2. List comparison experiments and ablation studies. 3. Write Introduction first draft. |
| **3 weeks before** | 1. Finalize the pipeline figure sketch. 2. Write Method first draft (use `\todo{}` for unsettled details). **Deadline: give Introduction + Method draft to advisor.** |
| **2 weeks before** | Write first drafts of Experiments, Abstract, Related Work. |
| **Last week** | Revise paper, polish pipeline figure and teaser, run demos. |

> Critical: By the end of Week 3, you must send the Introduction and Method drafts to your advisor — otherwise the advisor likely will not have enough time to finish reviewing the paper.

See [references/timeline-4week.md](references/timeline-4week.md) for the detailed schedule and progress tracking template.

---

## Handoff to Writing

When planning is complete, pass these artifacts to `paper-writing`:

| Artifact | Source Step | Used By |
|----------|-----------|---------|
| Story summary (task → challenge → insight → contribution → advantage) | Step 1 | Introduction |
| Module Motivation Mapping table | Step 1 | Method subsections |
| Experiment plan (comparisons + ablations + demos) | Step 2 | Experiments section |
| Pipeline figure sketch | Step 1 / Step 3 | Method overview + Figure 2 |
| Claim-to-experiment mapping | Step 2 | Abstract, Introduction, Experiments |
| Fallback narrative (if planned) | Counterintuitive Rule 5 | Introduction / Conclusion pivot |
| Rejection-risk table | Counterintuitive Rule 1 | Self-review prioritization |

---

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| Story design | [story-design.md](references/story-design.md) | Starting a new paper |
| Experiment planning | [experiment-planning.md](references/experiment-planning.md) | Before running experiments |
| Timeline | [timeline-4week.md](references/timeline-4week.md) | Setting up a writing schedule |
| Figure design | [figure-design.md](references/figure-design.md) | Designing pipeline/teaser figures |
| Experiment plan template | [experiment-plan-template.md](assets/experiment-plan-template.md) | Creating a structured experiment plan |
| Counterintuitive strategy | [counterintuitive-planning.md](references/counterintuitive-planning.md) | Increasing acceptance odds with non-obvious planning choices |

## Handoff to Presentation

If preparing a conference talk or slide deck, the `academic-slides` skill guides slide creation from your planning artifacts — including translating your story design and pipeline figure into presentation structure.
