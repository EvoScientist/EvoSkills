---
name: idea-tournament
description: "Guides competitive idea generation and ranking using tree-structured search (up to N_I=21 candidates across technique/domain/formulation axes) and Elo tournaments (4 dimensions: novelty, feasibility, relevance, clarity). Produces a ranked direction summary and full research proposal. Use when: user has a research direction and needs concrete ranked ideas, wants to compare multiple approaches, or mentions 'rank ideas', 'compare approaches', 'which idea is best', 'research proposal'. Do NOT use for finding a research direction from scratch (use research-ideation) or planning the paper itself (use paper-planning)."
allowed-tools: "write_file edit_file read_file think_tool"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, research, ideation]
---

# Idea Tournament

A structured framework for generating diverse research ideas through tree-based expansion, then selecting the strongest candidate via Elo-rated pairwise tournaments across four quality dimensions.

## When to Use This Skill

- User has a research direction from `research-ideation` and needs concrete, ranked ideas
- User wants to systematically compare multiple research ideas before committing
- User asks about idea ranking, competitive selection, or proposal generation
- User wants to explore variations of a research concept and select the best one
- User mentions "idea tournament", "rank ideas", "compare approaches", "research proposal", "which idea is best"

## From Direction to Proposal

The gap between "I have a research direction" and "I have a concrete proposal" is where most researchers stall. They either commit to their first idea (missing better alternatives) or endlessly brainstorm without converging (analysis paralysis).

The tournament solves both problems. Phase 1 forces breadth — you generate up to N_I=21 candidates (the paper's maximum) by systematically varying technique, domain, and formulation. Phase 2 forces convergence — pairwise Elo comparisons identify the strongest idea without requiring you to hold all candidates in your head simultaneously.

Before starting:
1. Load prior knowledge from Ideation Memory (M_I):
   - Refer to the **evo-memory** skill → Read M_I at `/memory/ideation-memory.md`
   - Select the top-2 entries (k_I=2) most relevant to the user's current goal by comparing each entry's Summary and Retrieval Tags against the goal
   - Feasible directions become tree seeds — incorporate them as Level 1 branches in Phase 1
   - Unsuccessful directions (fundamental failures only) are used during pruning — prune any tree branch that matches a fundamental failure pattern
   - If M_I doesn't exist yet (first cycle), skip this step
2. Retrieve relevant literature L for the user goal G. The paper defines idea tree search as IdeaTreeSearch(G, L, K_I) — literature is a formal input alongside the user goal and retrieved memory. Use web search or provided papers to ground idea generation in existing work.

## Phase 1: Tree-Structured Idea Generation

Expand a seed idea into a tree of candidates by varying one axis per level. The tree structure ensures diversity — each branch explores a fundamentally different variation rather than minor tweaks of the same concept.

### The Three Axes

| Level | Axis | What Varies | Example |
|-------|------|-------------|---------|
| 0 | Seed | Starting research direction | "Efficient LLM inference" |
| 1 | Technique | The core technical approach | Pruning, quantization, distillation |
| 2 | Domain | The application context | Edge devices, multi-modal, long-context |
| 3 | Formulation | The problem framing | Latency-constrained, memory-constrained, accuracy-preserving |

### Expansion Process

**Level 0 — Seed (1 node)**: Start with the research direction from `research-ideation`. This is your root node.

**Level 1 — Technique variants (3 nodes)**: Generate 3 fundamentally different technical approaches to the seed direction. These should be distinct paradigms, not variations of the same technique. Reflect carefully to verify each is genuinely different.

**Level 2 — Domain adaptations (6-9 nodes)**: For each Level 1 node, generate 2-3 domain-specific adaptations. How does this technique apply differently in different contexts? What domain-specific constraints create new challenges?

**Level 3 — Formulation variants (up to N_I=21 total leaves)**: For each Level 2 node, refine into 1-3 specific problem formulations. A formulation pins down the exact problem statement — the inputs, outputs, constraints, and evaluation criteria. The paper sets N_I=21 as the maximum number of candidate ideas. If the tree produces fewer than 15 leaves, expand Level 2 or Level 3 further. If more than 21, prune to stay within the N_I limit.

### Per-Node Cycle: Propose → Review → Refine

For each new node:
1. **Propose**: Write a 2-3 sentence description of the idea
2. **Review**: Evaluate critically — Is this genuinely different from sibling nodes? Is it at least plausible?
3. **Refine**: Sharpen the description based on the review. Remove vague language. Make the novelty claim specific.

### Pruning

After expanding each level, prune clearly infeasible branches. A branch is "clearly infeasible" if:
- It requires resources fundamentally unavailable (e.g., proprietary datasets you can't access)
- It contradicts well-established theoretical results
- It duplicates an existing, well-established solution with no meaningful variation
- It appears in `evo-memory`'s unsuccessful directions as a fundamental failure (not implementation failure)

**Important**: Pruning removes only the obviously unworkable. Do NOT prune ideas that are risky, unconventional, or outside your current expertise — these are exactly the ideas tournaments are designed to evaluate fairly.

Save the complete tree to `/idea-tree.md`.

See [references/tree-search-protocol.md](references/tree-search-protocol.md) for detailed expansion rules and diversity metrics.

## Phase 2: Elo Tournament Ranking

Rank all leaf candidates through pairwise comparisons on four quality dimensions. Swiss-system pairing keeps the number of comparisons manageable while still producing reliable rankings.

### The Four Dimensions

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Novelty | 25% | How different is this from existing published work? |
| Feasibility | 25% | Can this be implemented and validated within reasonable time and resources? |
| Relevance | 25% | Does this address an important, open problem in the field? |
| Clarity | 25% | Is the idea well-defined enough to start working on immediately? |

All dimensions are weighted equally. Researchers tend to overweight novelty and underweight feasibility — equal weights correct this bias.

### Tournament Mechanics

**Starting Elo**: 1500 for all candidates.

**K-factor**: 32 (standard for new players; large enough that a few matches significantly move ratings).

**Swiss-system pairing** (4-5 rounds):
1. Round 1: Random pairing
2. Subsequent rounds: Pair candidates with similar current Elo ratings, avoiding rematches
3. 4-5 rounds is sufficient for 15-21 candidates to produce stable rankings

**Per-match process**:
1. Present both candidates side by side with their full descriptions
2. Score each on all 4 dimensions (1-10 scale)
3. Compute composite scores (average of 4 dimensions)
4. Determine the match winner (higher composite score)
5. Update Elo ratings using the standard formula (see [elo-ranking-guide.md](references/elo-ranking-guide.md) for the formula, worked example, and convergence criteria)

Save rankings to `/idea-rankings.md`.

See [references/elo-ranking-guide.md](references/elo-ranking-guide.md) for the detailed rubric and convergence criteria.

## Phase 3: Direction Summarization

Synthesize the top-3 ranked ideas into a "promising directions" summary. This serves two purposes: it preserves optionality (the best idea may combine elements from multiple candidates), and it feeds into `evo-memory` for future cycles.

### Summarization Process

For each of the top-3 ideas:
1. Extract the core research direction (abstract away from specific implementation details)
2. Identify the key insight that makes this direction promising
3. Note the primary risk or uncertainty
4. Check against `evo-memory` — has this direction been explored before? What was learned?

Then synthesize across the top-3:
- What common threads run through the top-3? These may suggest an even stronger combined direction.
- What dimensions do the top ideas excel in? Are there patterns (e.g., all top ideas score high on feasibility but moderate on novelty)?
- What's missing? Are there important aspects of the original seed that none of the top ideas address?

Save to `/direction-summary.md`.

After completion, trigger `evo-memory` IDE (Idea Direction Evolution) to update Ideation Memory with the promising directions identified.

## Phase 4: Proposal Extension

Extend the tournament winner (rank #1) into a full research proposal with enough detail to begin implementation.

### Proposal Structure

The paper defines proposal P as containing 5 sections: **background, related work, method, experiment plan, and expected results**. We extend this with a 6th practical section (risks and mitigations).

**1. Background**: Define the exact problem — inputs, outputs, constraints, and why existing solutions are insufficient. Be specific: "LLM inference on edge devices with <2GB memory while maintaining >90% of full-model accuracy" is a background statement; "make LLMs faster" is not. Include context and motivation.

**2. Related Work**: Position the idea within the existing literature. What has been tried? What are the gaps? This should draw on the literature L retrieved during Phase 1 tree generation.

**3. Proposed Method**: Describe the technical approach at a level of detail sufficient for implementation. Include the key insight that differentiates this from prior work. State assumptions explicitly. List 3 testable contributions.

**4. Experiment Plan**: Datasets, baselines, metrics, and ablation design. This should align with what `experiment-pipeline` Stage 4 will need. Include both quantitative metrics and qualitative evaluation where appropriate.

**5. Expected Results**: Quantitative targets (e.g., "15-20% latency reduction with <2% accuracy loss") and qualitative expectations. Being specific about expected results forces you to think about whether the idea is realistic.

**6. Risks and Mitigations** (practical extension): Technical risks that could prevent success, and fallback plans for each. A proposal without risks is either dishonest or insufficiently analyzed. This section is not in the paper but is valuable for practical research planning.

Save to `/research-proposal.md`.

See [references/proposal-extension.md](references/proposal-extension.md) for detailed guidance on each section.

## Counterintuitive Tournament Rules

Prioritize these rules during idea generation and ranking:

1. **Quantity before quality**: Generate many candidates before evaluating any. Premature filtering kills diversity. You can't know which idea is strongest until you've seen the alternatives — and the best ideas often emerge from unexpected branches of the tree.

2. **Vary one axis per level**: Changing multiple axes simultaneously produces ideas that are different but not meaningfully diverse. Each level of the tree should explore ONE dimension of variation, so you understand exactly what makes each branch unique.

3. **Feasibility is not optional**: Brilliant but infeasible ideas waste entire research cycles. A novel idea that can't be validated within your constraints is not a contribution — it's a thought experiment. Weight feasibility equally with novelty.

4. **The tournament finds surprises**: Structured pairwise comparison often reveals that your initial favorite isn't actually the strongest idea. Trust the rankings over your gut feeling. If the results surprise you, that means the tournament is working — it's surfacing information you wouldn't have found through intuition alone.

5. **Pruning is not selecting**: Prune only clearly infeasible branches. The tournament handles quality ranking. If you aggressively prune before the tournament, you're substituting your initial intuition for systematic comparison — exactly the bias the tournament is designed to correct.

6. **Top-3, not top-1**: Summarizing the top 3 directions (not just the winner) preserves optionality. The best final approach may combine elements from multiple top candidates. Committing to exactly one idea too early discards valuable signal.

## Handoff to Planning

When the tournament is complete and the proposal is written, pass these artifacts to `paper-planning`:

| Artifact | Source Phase | Used By |
|----------|-------------|---------|
| Research proposal (5+1 sections) | Phase 4 | Story design, experiment planning |
| Idea tree (full structure) | Phase 1 | Related work positioning |
| Elo rankings with scores | Phase 2 | Justification for chosen direction |
| Direction summary (top-3) | Phase 3 | Fallback directions if primary fails |
| Tournament scorecards | Phase 2 | Understanding idea strengths/weaknesses |

Also pass results to `evo-memory` for evolution updates:
- Trigger IDE (Idea Direction Evolution) with the top-3 directions from Phase 3

## Skill Integration

### Before Starting (load memory)
Refer to the **evo-memory** skill to read Ideation Memory:
→ Read M_I at `/memory/ideation-memory.md`

### After Phase 3 (update memory)
Refer to the **evo-memory** skill and trigger IDE:
→ Run IDE protocol with `/direction-summary.md`

### After Phase 4 (handoff to planning)
Refer to the **paper-planning** skill:
→ Pass `/research-proposal.md`

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| Tree expansion rules and diversity | [tree-search-protocol.md](references/tree-search-protocol.md) | Generating diverse idea candidates |
| Elo formula, rubric, and pairing | [elo-ranking-guide.md](references/elo-ranking-guide.md) | Running the tournament |
| Proposal section guidance | [proposal-extension.md](references/proposal-extension.md) | Writing the research proposal |
| Idea candidate template | [idea-candidate-template.md](assets/idea-candidate-template.md) | Describing individual ideas |
| Ranking scorecard template | [ranking-scorecard-template.md](assets/ranking-scorecard-template.md) | Recording pairwise comparisons |
| Direction summary template | [direction-summary-template.md](assets/direction-summary-template.md) | Synthesizing top-3 directions |
