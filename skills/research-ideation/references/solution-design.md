# Solution Design

Novel techniques are creative combinations of existing methods, not simple concatenations. This guide provides a systematic methodology for designing solutions once you have selected a problem worth solving.

## Core Principle

**Making a tool work is hard; just applying it is easy.**

The value in solution design lies in understanding WHY a technique works (or fails) in a given context, then creatively combining insights to address your specific problem. The hard part is the understanding, not the implementation.

## Knowledge Distillation Pipeline

Before designing a solution, gather knowledge from four sources in order of accessibility:

### Source 1: From Papers

Search for papers solving similar problems. Look broadly — the most useful papers are often in completely different sub-fields.

Key reading strategy:
- Focus on Introduction paragraphs 2-3, where authors analyze the technical cause of the problem
- Read the Method section for the specific insight, not just the overall pipeline
- Search with different terminology — the same technical challenge appears under many names across domains

### Source 2: From Synthesis

Don't just collect paper insights — synthesize them into your own framework:
- Summarize what you've learned in your own words
- Form your own analysis of why the problem is hard
- Identify which existing insights apply to your specific setting and which don't
- Build a mental model of the solution space

This synthesis step is where original thinking happens. Skip it and you're just copying.

### Source 3: From People

Discuss with experienced researchers:
- Share YOUR thinking (not just the problem) — articulating your analysis deepens it
- Ask for perspectives on your approach — others may see angles you've missed
- Build a habit of discussing inspiring papers with colleagues
- Regularly update collaborators on your progress and roadblocks

Discussion is not just information gathering — the act of explaining your thinking to others clarifies and strengthens it.

### Source 4: From Experiments

Run targeted experiments to verify your hypotheses:
- Test hypothesized causes of failure experimentally
- Collect observations that confirm or contradict your analysis
- Use experiment results to refine your understanding before designing the full solution

Don't design the complete solution first and test it all at once. Iteratively verify your assumptions.

## Two Solution Design Patterns

### Pattern A: Cross-Domain Transfer

Use when: A similar technical core problem is solved in a different domain (Well-Established Solution Check Level 3).

**Process:**
1. Identify the technical core of your problem (strip away domain-specific details)
2. Search broadly for papers in different fields that address a technically similar problem
3. Study their solution — understand not just WHAT they do, but WHY it works
4. Adapt the solution to your domain:
   - What changes are needed for your data format/modality?
   - Which components transfer directly and which need redesign?
   - What domain-specific constraints must the adapted solution satisfy?
5. Validate the adaptation on representative examples before full experiments

**Key insight**: The further the source domain from yours, the more novel the transfer appears. But also the more adaptation work is needed.

### Pattern B: Problem Decomposition

Use when: No domain has a good solution for your problem (Well-Established Solution Check Level 4).

**Process:**
1. Break the technical problem into sub-problems:
   - What are the independent challenges that must each be solved?
   - What is the dependency structure between sub-problems?
2. For each sub-problem, apply Pattern A (cross-domain transfer):
   - Search for solutions to technically similar sub-problems in any domain
   - Adapt and combine
3. If a sub-problem has no known solution in any domain:
   - Decompose it further into smaller sub-problems
   - Or simplify the sub-problem (relax constraints, reduce scope)
4. Combine sub-solutions into a complete pipeline:
   - Ensure interfaces between components are compatible
   - Test the combined system incrementally (add one component at a time)

## Creative Combination Principles

The essence of a novel technique is combining existing methods in non-obvious ways. Keep these principles in mind:

### Simple Concatenation Is Not Enough

If you can solve the problem by simply chaining Method A then Method B in a straightforward pipeline, the problem has no genuine technical challenge. A contribution requires understanding WHY naive approaches fail and designing a combination that addresses the specific technical bottleneck.

### Enumerate Before Selecting

When combining techniques:
1. List ALL possible combinations and pipeline orderings
2. For each combination, analyze trade-offs (accuracy, efficiency, assumptions, failure modes)
3. Select the most promising based on analysis, not intuition
4. Test the selected design against at least one alternative to validate the choice

### Verify the Novelty

Before investing in implementation, check:
- Has this specific combination been tried before? (Search carefully)
- If tried, why didn't it work? (Your insight must address their failure)
- If not tried, why not? (There may be a good reason, or there may be an opportunity)

## When Decomposition Fails

If you cannot decompose the problem or find solutions for sub-problems, consider three possibilities:

### 1. Skill Gap

You lack the ability to decompose the problem effectively. This is the most common case.

**Fix**: Read more papers (especially from distant fields), discuss with experienced researchers, take time to deepen your understanding before forcing a solution.

### 2. Search Gap

Relevant solutions exist in papers you haven't found yet. The technique may be described using different terminology or in an unexpected field.

**Fix**: Search more broadly. Try different keywords. Look at reference lists of the closest papers. Ask colleagues in other sub-fields.

### 3. Genuinely World-Class Hard Problem

The problem is fundamentally unsolved across all domains. This is rare.

**Verify**: Discuss with senior researchers. If they confirm the hardness, decide whether to:
- Simplify the problem (relax constraints, reduce scope) and solve the simplified version
- Invest long-term effort with acceptance of high risk
- Switch to a different problem with more tractable structure

## Solution Design Checklist

Before proceeding to full experiments:

- [ ] You can explain WHY your solution should work (not just WHAT it does)
- [ ] The solution addresses a specific technical bottleneck (not a vague improvement)
- [ ] You have checked that this combination hasn't been done before
- [ ] You have tested key assumptions with small-scale experiments
- [ ] You can articulate the advantage over the most obvious alternative approach
- [ ] The solution is implementable with your available resources
