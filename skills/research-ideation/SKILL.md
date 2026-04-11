---
name: research-ideation
description: "End-to-end research ideation pipeline: literature grounding → multi-track idea generation (3 personas: innovator/pragmatist/critic) → iterative refinement → ELO tournament ranking → present top-3 to user → expand user's choice into a manuscript-quality proposal. Use when: user wants to find a research direction, brainstorm ideas, evaluate idea novelty, design a novel solution, rank/compare research ideas, or generate a research proposal. Do NOT use for finding/searching/reading papers (use paper-navigator), literature survey reports (use research-survey), or planning a paper (use paper-planning)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '2.1.0'
  tags: [core, research, ideation, tournament, proposal]
---

# Research Ideation

From research goal to ranked ideas and a detailed proposal.

```
Step 0: Load evo-memory (M_I)
    ↓
Step 1: Define Goal
    ↓
Step 2: Literature Grounding (MUST use paper-navigator scripts)
    ↓
Step 3: Generate Ideas (3 directions × 3 personas)
    ↓
Step 4: Refine Ideas (3 tracks × N iterations)
    ↓
Step 5: ELO Tournament → Present Top-3 to User
    ↓                          ↓
Step 6: User Selects →    Update evo-memory (IDE)
    ↓
Step 7: Expand into Proposal
    ↓
Step 8: Validate and Iterate
```

## When to Use

- User wants to find a research direction or brainstorm research ideas
- User wants to evaluate whether an idea is novel or worth pursuing
- User wants to rank or compare multiple research ideas
- User wants to generate a research proposal from an idea

## When NOT to Use

- **Finding/reading papers** → use `paper-navigator`
- **Literature survey report** → use `research-survey`
- **Planning a paper (story design, experiment plan)** → use `paper-planning`

---

## Step 0: Load Prior Knowledge from evo-memory

**Before any ideation begins**, load Ideation Memory (M_I) from prior research cycles:

1. Read M_I at `/memory/ideation-memory.md` (refer to `evo-memory` skill)
2. Select the **top-2 entries** (k_I=2) most relevant to the user's current goal by comparing each entry's Summary and Retrieval Tags against the goal
3. **Feasible directions** from prior cycles → use as seeds in Step 3 (incorporate as candidate research directions alongside new ones)
4. **Unsuccessful directions** marked as fundamental failures → use during idea pruning in Step 4 (prune any idea that matches a fundamental failure pattern)
5. If M_I doesn't exist yet (first cycle), skip this step

This step prevents repeating known dead ends and builds on prior successes across research cycles.

## Step 1: Define a Long-Term Research Goal

Start with a goal that has both scientific and practical value. Ambitious enough for multiple papers, concrete enough to guide daily decisions.

Ask: "What is the ultimate form of this research direction? What would the world look like if this problem were fully solved?"

## Step 2: Literature Grounding (via paper-navigator)

**Invoke `paper-navigator`** (Workflow 9: Ideation Support) to collect 30-50 relevant papers. Do NOT skip this step or substitute with general knowledge — ideas must be grounded in real papers.

**CRITICAL: All paper discovery in this step MUST use the `paper-navigator` skill and its scripts (scholar_search, citation_traverse, arxiv_monitor, recommend, etc.). Using WebSearch, WebFetch, or any generic web search tool for finding papers is PROHIBITED.** Generic web search returns blog posts, news articles, and low-quality results — only paper-navigator provides access to Semantic Scholar, arXiv, citation graph traversal, and academic recommendations needed for rigorous literature grounding.

### Build Challenge-Insight Tree

From the collected papers, construct a **challenge-insight tree** — a many-to-many mapping between technical challenges and the insights/techniques that address them:

- **Extract challenges**: From each paper, what technical problem does it solve?
- **Extract insights**: What technique or key idea does it use?
- **Map connections**: Which insights address which challenges?

**How this drives ideation**:
- Challenges with few insights → **unsolved problem** (candidate for Step 3)
- Insights not yet applied to a challenge → **cross-domain transfer opportunity** (candidate for Step 4)
- Challenges with many insights → well-studied, avoid unless you have a fundamentally new angle

Also generate a condensed **literature review synthesis** as context for idea generation (for full surveys use `research-survey`).

See `references/literature-tree.md` for construction methodology.

**Execution rule**: Do NOT generate ideas without real paper grounding. The tree must reference actual papers with titles, authors, and findings. Paper search MUST go through `paper-navigator` — never use WebSearch/WebFetch as a shortcut.

## Step 3: Generate Ideas

Generate 3 initial research ideas from 3 distinct research directions, grounded in the literature.

### Three Personas

| Persona | Focus |
|---------|-------|
| **Innovator** | Novelty & creativity — groundbreaking, high-risk/high-reward |
| **Pragmatist** | Feasibility — realistic, clearly executable |
| **Critic** | Scientific value — advances understanding, rigorous |

### Process

1. Analyze literature + challenge-insight tree → identify 3 fundamentally different research directions
2. Generate one idea per direction using **Innovator** persona
3. Each idea must follow one of two methodological paths:
   - **Path 1 (Focused Contribution)**: Single new component; clean hypothesis
   - **Path 2 (System Contribution)**: Tight causal interaction between components; emergent capability

### Idea Format

```
# Research Idea: [Concise Title]

## Core Idea
[One paragraph: the proposal + which research direction it addresses]

## Validation Plan
[Concrete experiment outline: datasets, baselines, metrics]
```

## Step 4: Refine Ideas

Run 3 parallel refinement tracks — one per initial idea. Each track uses all 3 personas.

```
For each track:
  For N=3 iterations:
    1. Evaluate current best idea (novelty, feasibility, impact, alignment)
    2. All 3 personas generate refined versions based on evaluation
    3. Pick the best refinement as seed for next iteration
  Track champion = best idea across iterations
```

### 5 Evolution Strategies

1. **Enhancement through Grounding**: Strengthen with literature citations
2. **Improving Coherence**: Fix logical flaws in the mechanism
3. **Inspiration and Combination**: Combine with a different concept from literature
4. **Simplification**: Strip down to a clean, testable hypothesis
5. **Literature-Driven Pivot**: Abandon the mechanism; propose a new approach from literature

**Critical rule**: If evaluation says the approach is a dead-end, the persona MUST pivot — refinement is not restricted to patching.

### Logical Cohesion Principles

- **Too many variables** → Focus via Subtraction: isolate the most promising variable
- **Disconnected components** → Justify via Strong Correlation: build explicit causal links

## Step 5: ELO Tournament → Present Top-3

Rank all track champions through pairwise comparison, then **present the top-3 to the user for selection**.

### Four Dimensions

| Dimension | What It Measures |
|-----------|-----------------|
| **Novelty** | How different from existing published work? |
| **Feasibility** | Can this be implemented within reasonable resources? |
| **Relevance** | Does this address an important problem aligned with the goal? |
| **Clarity** | Is the idea well-defined enough to start immediately? |

### Tournament

- **Starting Elo**: 1500 | **K-factor**: 32
- Compare ideas pairwise → update Elo → sort by final score
- See `references/elo-ranking-guide.md` for rubric and formula

### Present Top-3 to User

After the tournament, present the top-3 ideas with **both** a comparison table and the **full refined idea** for each. This ensures the user sees the concrete, actionable version of each idea — not just a summary.

#### Part 1: Comparison Table

```
## Top-3 Research Ideas (ranked by ELO)

| Rank | Title | Core Mechanism | Novelty | Feasibility | Relevance | Clarity | ELO |
|------|-------|---------------|---------|-------------|-----------|---------|-----|
| 1 | ... | ... | 9 | 7 | 8 | 8 | 1280 |
| 2 | ... | ... | 7 | 9 | 8 | 7 | 1240 |
| 3 | ... | ... | 8 | 6 | 9 | 7 | 1210 |
```

#### Part 2: Full Refined Ideas

For **each** of the top-3, present the refined idea using the same structured format as Step 3, plus a refinement summary:

```
# Refined Idea [Rank]: [Concise Title]

## Core Idea
[One paragraph: the refined proposal — this should reflect ALL changes from Step 4 refinement,
not the original Step 3 version]

## Validation Plan
[Concrete experiment outline updated with refinement insights: datasets, baselines, metrics,
key ablations identified during refinement]

## Refinement Summary
[Brief paragraph summarizing what changed from the initial idea and why:
- What was simplified or removed (and why)
- What was added or concretized (and why)
- Which persona drove the most impactful change
- Key risk mitigations added during refinement]
```

**This section is mandatory** — do NOT skip the full refined ideas or collapse them into the comparison table. The user needs to see the complete, refined version to make an informed selection.

#### Part 3: Selection Prompt

```
Which idea would you like to develop into a full proposal? (1/2/3, or combine elements)
```

**Wait for user selection before proceeding to Step 6.** The user may:
- Pick one of the top-3
- Ask to combine elements from multiple ideas
- Request modifications before expanding
- Ask to regenerate with different constraints

## Step 6: Update evo-memory

After the tournament and before the user selects, trigger `evo-memory` IDE (Idea Direction Evolution):

1. Save the top-3 directions to `/direction-summary.md`
2. Trigger IDE protocol via `evo-memory` skill with the direction summary
3. Each top direction is added to M_I as a feasible direction with its ELO score
4. Any ideas that were clearly unworkable during refinement (Step 4) are recorded as unsuccessful directions with failure classification (fundamental vs implementation)

This ensures future ideation cycles benefit from what was learned in this cycle.

## Step 7: Expand into Proposal

After the user selects an idea, expand it into a manuscript-quality research proposal. **This is a two-phase process** because different fields require different proposal structures.

### Phase 1: Generate a Domain-Specific Template

Before writing, first generate a proposal template tailored to the user's field:

1. Identify the field from the research goal and literature
2. Start with universal sections (Abstract, Problem, Related Work, Method, Evaluation, Conclusion)
3. Add field-specific sections (e.g., Ethics/IRB for medical research, Safety analysis for chemistry, Statistical power analysis for clinical trials, Ablation design for ML)
4. Adapt terminology to the field's conventions (e.g., "Study Design" in medicine, "Methodology" in social sciences, "Proposed Method" in engineering)

See `assets/proposal-template.md` for the complete field-specific section guide and writing instructions.

### Phase 2: Write the Proposal

Fill the generated template following these universal principles:
- Write for a top-tier reviewer in the field — every claim supported, every design justified
- Avoid variable confusion: clearly isolate the core contribution
- Match the field's rigor standards (math for quantitative fields, protocols for experimental fields, coding schemes for qualitative fields)
- Anticipate skeptical reviewer questions proactively

See `references/proposal-extension.md` for detailed section guidance.

## Step 8: Validate and Iterate

Run experiments on representative data. If the approach fails, return to Step 3 or Step 4 with updated knowledge. See `experiment-craft` for systematic debugging.

---

## Counterintuitive Rules

1. **Problem selection > solution design**: Choosing WHAT to solve matters more than HOW
2. **Pursue new failure cases, not incremental improvements**: Find settings where existing methods break
3. **If a well-established solution exists, switch problems**: Improvement space is too small
4. **Technology is creative combination, not concatenation**: Simple A→B pipelines are not contributions
5. **Quantity before quality in generation**: Generate many candidates before evaluating any
6. **Feasibility is not optional**: Brilliant but infeasible ideas waste research cycles
7. **The tournament finds surprises**: Trust rankings over gut feeling

---

## Dependency: paper-navigator

All paper discovery goes through `paper-navigator`. This skill does not search for papers itself. **Using WebSearch, WebFetch, or any generic search tool to find papers is PROHIBITED** — these tools cannot access Semantic Scholar, citation graphs, or academic recommendation systems. Always use `paper-navigator` and its scripts (scholar_search, citation_traverse, arxiv_monitor, recommend, trending, etc.) for all paper discovery needs in Steps 2, 3, and 4.

| Step | Requires paper-navigator for |
|------|------------------------------|
| Step 2 | Collect 30-50 relevant papers for literature tree construction |
| Step 3 | Verify no well-established solution exists for selected problems |
| Step 4 | Cross-domain search for transferable techniques during refinement |

## evo-memory Integration

| When | Action | Details |
|------|--------|---------|
| **Step 0** (before ideation) | **Read M_I** | Load `/memory/ideation-memory.md`, select top-2 relevant entries, use feasible directions as seeds, avoid fundamental failures |
| **Step 6** (after tournament) | **Write M_I via IDE** | Save top-3 directions with ELO scores as feasible; save dead-end ideas as unsuccessful with failure classification |

## Handoff

| To | When |
|----|------|
| `paper-planning` | Proposal complete (Step 7) → plan paper structure |
| `experiment-pipeline` | Proposal complete (Step 7) → start experiments |
| `evo-memory` | After tournament (Step 6) → update Ideation Memory via IDE protocol |

---

## References & Assets

| Topic | File |
|-------|------|
| Literature tree construction | `references/literature-tree.md` |
| Problem selection framework | `references/problem-selection.md` |
| Solution design methodology | `references/solution-design.md` |
| Tree expansion rules | `references/tree-search-protocol.md` |
| ELO formula & rubric | `references/elo-ranking-guide.md` |
| Proposal section guidance | `references/proposal-extension.md` |
| Idea candidate template | `assets/idea-candidate-template.md` |
| Ranking scorecard | `assets/ranking-scorecard-template.md` |
| Direction summary | `assets/direction-summary-template.md` |
| Proposal example (E-FNO) | `assets/proposal-template.md` |
