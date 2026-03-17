---
name: paper-writing
description: "Guides writing academic papers section by section using an 11-step workflow with LaTeX templates and counterintuitive writing tactics. Covers Abstract, Introduction, Method, Experiments, Related Work, Conclusion, and Supplementary. Use when: user asks to write or draft a paper section, needs LaTeX templates, wants to improve academic writing quality, optimize novelty framing, or mentions 'write introduction', 'draft method', 'paper writing'. Do NOT use for pre-submission review (use paper-review), experiment execution (use experiment-pipeline), or paper planning/story design (use paper-planning)."
allowed-tools: "write_file edit_file read_file think_tool"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, research, writing, academic-writing, latex]
---

# Paper Writing

A systematic 11-step workflow for writing academic papers, with section-specific templates and battle-tested writing principles.

## When to Use This Skill

- User asks to write or draft a paper or paper section
- User needs LaTeX templates for Abstract, Introduction, Method, Experiments, etc.
- User wants to improve academic writing quality
- User mentions "paper writing", "write introduction", "draft method section", etc.

## Artifact Sources

If you used upstream EvoSkills, pull these artifacts before writing:

| Source Skill | Artifact | Used In |
|-------------|----------|---------|
| `paper-planning` | Story summary (task → challenge → insight → contribution → advantage) | Steps 1-2 (Introduction writing plan) |
| `paper-planning` | Module Motivation Mapping table | Step 3 (Method subsections) |
| `paper-planning` | Experiment plan (comparisons + ablations + demos) | Step 5 (Experiments section) |
| `paper-planning` | Pipeline figure sketch | Steps 1, 6 (Method overview figure) |
| `paper-planning` | Claim-to-experiment mapping | Steps 2, 5 (Abstract, Introduction, Experiments) |
| `paper-planning` | Fallback narrative (if planned) | Steps 7-8 (Introduction / Conclusion pivot) |
| `experiment-pipeline` | Stage 1-4 results, ablation tables, trajectory logs | Step 5 (write experiments) |
| `experiment-craft` | Failure analysis, implementation tricks | Step 3 (Method section), Step 9 (limitations) |

## The 11-Step Writing Process

Follow these steps in order. Each step builds on the previous one.

1. **Draw a pipeline figure sketch** — Sketch the method's pipeline figure to clarify the overall approach. The figure highlights novelty, not just explanation.
2. **Design the story and plan experiments** — Outline the paper's story (core contribution, module motivations). List comparison experiments and ablation studies. Draft an Introduction writing plan.
3. **Write Method** — Organize the Method writing plan, then draft Method. Run experiments in parallel.
4. **Revise Introduction and Method** — Iterate on both sections while experiments continue.
5. **Write Experiments** — Once experiments are mostly done, organize the Experiments writing plan, then draft.
6. **Polish figures** — Finalize the pipeline figure. Create the teaser figure.
7. **Write Related Work** — List related papers, group into topics, write paragraphs.
8. **Review the paper** — Self-review Introduction, Method, and Experiments. Use the `paper-review` skill.
9. **Write Abstract** — Organize the Abstract writing plan, then draft.
10. **Choose the title** — List important keywords, then compose an informative title.
11. **Iterate** — Repeatedly review and revise the entire paper.

## Counterintuitive Writing Rules

Apply these rules when aiming for higher acceptance probability:

1. **Underclaim in prose, overdeliver in evidence**: Reduce adjective intensity in Abstract/Introduction; let tables and figures carry the strength.
2. **State one meaningful limitation early**: A controlled limitation statement increases credibility and lowers reviewer suspicion.
3. **Lead with mechanism, not only metric**: Explain why the method works before listing numbers; reviewers trust causal logic more than isolated gains.
4. **Prefer one decisive figure over many average figures**: Build one "cannot-ignore" figure that validates the central claim under hard conditions.
5. **Remove weak but flashy claims**: Any claim without direct evidence should be deleted, even if it sounds impressive.
6. **Declare scope boundaries explicitly**: One sentence in Introduction and Conclusion stating what your method targets reduces reviewer fear of hidden assumptions.
7. **Show one failure case**: Include one representative failure with diagnosis — it signals competence, not weakness.

See [references/counterintuitive-writing.md](references/counterintuitive-writing.md) for all 7 tactics with before/after examples.

## Section Quick Reference

### Abstract

Answer these questions before drafting:
1. What technical problem do we solve, and why is there no well-established solution?
2. What is our technical contribution?
3. Why does our method fundamentally work?
4. What is our technical advantage / new insight?

Three template versions: challenge-first, insight-bridge, multi-contribution.
See [references/abstract-templates.md](references/abstract-templates.md)

### Introduction

**Thinking process** (reverse then forward):
- Reverse: (1) What is the technical problem? (2) What are our contributions? (3) Benefits and new insights? (4) How to lead into the challenge?
- Forward: (1) Task → (2) Previous methods → challenge → (3) Our contributions → (4) Technical advantages and insights

Four ways to introduce the task, three ways to present challenges, four ways to describe the pipeline.
See [references/introduction-templates.md](references/introduction-templates.md)

**Anti-pattern**: Never write "here is a naive solution, then our improvement" — this makes the work appear incremental.

### Method

Every pipeline module needs three elements:
1. **Module design** — Data structure, network design, forward process (given X input, step 1..., step 2..., output Y)
2. **Motivation** — Why this module exists (problem-driven: "A remaining challenge is...")
3. **Technical advantages** — Why this module works well

Start with an Overview paragraph (setting + core contribution + section roadmap), then one subsection per module.
See [references/method-templates.md](references/method-templates.md)

### Experiments

Three key questions to answer:
1. How to prove our method is better → comparison experiments
2. How to prove our modules are effective → ablation studies
3. How to showcase the method's upper limit → demos on challenging data

Ablation studies need: one big table (core contributions) + several small tables (design choices, hyperparameters).
See [references/experiments-guide.md](references/experiments-guide.md)

### Related Work

Three-step process:
1. List papers closely related to our method (most important — missing key references can cause rejection)
2. Determine topics based on research direction and algorithm techniques
3. Organize writing plan based on listed papers

See [references/related-work-guide.md](references/related-work-guide.md)

### Conclusion

- Must include **Limitation** section (reviewers frequently cite "no limitation" as a weakness)
- Limitation = task goal / setting limitations (like future work), NOT technical defects
- Rule: "If our method does not fall below current SOTA metrics, it is not a technical defect"

### Supplementary Material

For page-limited venues, decide what goes in main paper vs. supplementary:
- Core evidence for claims must stay in the main paper
- Implementation details, extra ablations, full visual galleries go in supplementary
- Reference supplementary at the point of need, not as a blanket statement

See [references/supplementary-guide.md](references/supplementary-guide.md)

## Core Writing Principles

1. **One message per paragraph** — Each paragraph conveys exactly one point
2. **Topic sentence first** — The first sentence tells readers what this paragraph is about
3. **Plan before writing** — Outline the writing plan, refine each part, then write English sentences
4. **Flow between sentences** — Ensure logical continuity between consecutive sentences
5. **Terminology consistency** — Use the same term throughout; do not alternate names
6. **Reverse-outlining** — After writing, extract the outline from paragraphs; check if the flow is smooth
7. **Iterate relentlessly** — Polish repeatedly, asking whether readers can follow

See [references/writing-principles.md](references/writing-principles.md)

## Key Insight

Visual polish directly influences review outcomes. See the `paper-planning` skill's [figure-design.md](../paper-planning/references/figure-design.md) for the full visual quality guide.

## Paper Title Guidelines

- The title attracts specific reviewers — choose keywords carefully
- Before writing the title, list important keywords, then compose
- Title must be **informative**: include the technique, task, or problem solved
- Avoid generic titles; specific phrases are more memorable

## LaTeX Assets

- [assets/paper-skeleton.tex](assets/paper-skeleton.tex) — Annotated LaTeX skeleton with section structure
- [assets/table-style.tex](assets/table-style.tex) — Booktabs table macros with color highlighting

## Handoff to Review

Before invoking `paper-review`, verify this checklist:

- [ ] All sections (Abstract, Introduction, Method, Experiments, Related Work, Conclusion) drafted
- [ ] Every claim in Abstract/Introduction anchored to a table or figure
- [ ] Limitation section present in Conclusion
- [ ] Pipeline figure and teaser figure finalized
- [ ] All `\todo{}` markers resolved or removed

---

## Section Navigation

| Section | Reference File | When to Load |
|---------|---------------|--------------|
| Abstract | [abstract-templates.md](references/abstract-templates.md) | Step 9: Writing abstract |
| Introduction | [introduction-templates.md](references/introduction-templates.md) | Step 2: Story design |
| Method | [method-templates.md](references/method-templates.md) | Step 3: Writing method |
| Experiments | [experiments-guide.md](references/experiments-guide.md) | Step 5: Writing experiments |
| Related Work | [related-work-guide.md](references/related-work-guide.md) | Step 7: Writing related work |
| Writing Principles | [writing-principles.md](references/writing-principles.md) | Any time during writing |
| Supplementary | [supplementary-guide.md](references/supplementary-guide.md) | Deciding main vs. supplementary content |
| Counterintuitive strategy | [counterintuitive-writing.md](references/counterintuitive-writing.md) | Improving reviewer trust and novelty perception |
| Writing Practice | [writing-practice.md](references/writing-practice.md) | Building writing ability through deliberate practice |
