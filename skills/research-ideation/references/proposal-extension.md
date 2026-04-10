# Proposal Extension

Guidance for extending the tournament winner into a full research proposal in Phase 4. The paper defines proposal P as containing 5 sections: **background, related work, method, experimental plan, and expected results**. We add a 6th practical section (risks and mitigations). The proposal should have enough detail to begin implementation — it's a blueprint, not a sketch.

## Section 1: Background

### What to Include

- **Exact problem definition**: Inputs, outputs, constraints, and evaluation criteria. Be specific enough that someone could implement an evaluation function from this description alone.
- **Why existing solutions are insufficient**: Not just "existing methods don't work well" but specifically WHERE and WHY they fail. Reference concrete limitations from your literature tree.
- **Scope boundaries**: What is IN scope and what is NOT. Explicit non-goals prevent scope creep later.

### How to Write It

Start from the tournament winner's description and expand. The idea candidate form has a one-sentence summary — the problem statement expands this into a precise, complete definition.

**Test**: After writing the problem statement, ask "Could a peer implement an evaluation pipeline from this description?" If the answer is no, add more specifics.

### Common Pitfalls

| Pitfall | Example | Fix |
|---------|---------|-----|
| Too broad | "Improve LLM efficiency" | "Reduce 7B LLM inference latency by ≥40% on single A100 while maintaining ≥95% of original MMLU accuracy" |
| No baseline reference | "Current methods are slow" | "State-of-the-art (SpecDec, 2024) achieves 2.3x speedup but requires a draft model, limiting deployment flexibility" |
| Missing constraints | "Faster inference" | "Under the constraint of no auxiliary models and ≤16GB VRAM" |

## Section 2: Related Work

### What to Include

- **Positioning**: Where does your idea fit in the landscape of existing work?
- **Key prior work**: The 3-5 most relevant papers and how they relate to your approach
- **Gaps**: What specific limitations in prior work does your idea address?
- **Differentiation**: How is your approach fundamentally different from the closest related work?

### How to Write It

Draw on the literature L that was retrieved during Phase 1 tree generation. The related work section should set up the problem statement and make the case for why your approach is needed.

**Test**: After writing, ask "Does the related work section make the reader expect and want the method I'm about to propose?"

## Section 3: Proposed Method

### What to Include

- **High-level approach**: The core technical idea in 2-3 sentences. What is the key insight?
- **Method overview**: A step-by-step description of how the method works. Enough detail for a researcher to understand the approach and begin implementation planning.
- **Key differentiator**: What makes this approach different from prior work. This should map directly to the novelty argument from the tournament.
- **Assumptions**: What does this method assume about the data, model, or setting? Explicit assumptions prevent later surprises.

### Level of Detail

More detailed than an abstract, less detailed than a paper's method section. The reader should understand:
1. What the method does (input → output transformation)
2. How it achieves this (the mechanism)
3. Why this should work (the insight or principle)

They should NOT need to understand:
- Exact hyperparameter values (that's for experiments)
- Implementation details of standard components (that's for code)
- Mathematical proofs (that's for the paper)

### Connecting to the Key Insight

Every strong method has a core insight — a non-obvious observation or principle that makes the approach work. State this explicitly. "Our key insight is that [X], which enables [Y] because [Z]."

The insight should not be a restatement of the approach. "Our key insight is that pruning makes models smaller" is a definition, not an insight. "Our key insight is that attention heads in different layers respond to different input lengths, enabling layer-specific pruning ratios" is an insight.

### Key Contributions (3 Claims)

The paper's method section includes testable contributions. Include them as part of Section 3 rather than a standalone section.

### The Rule of Three

List exactly 3 contributions. This is a convention, not an arbitrary limit:
- 1 contribution suggests limited novelty
- 2 contributions feels incomplete
- 3 contributions feels substantive but focused
- 4+ contributions suggests the work isn't focused enough

### Making Claims Testable

A contribution is testable if you can design an experiment whose outcome determines whether the claim holds.

| Type | Non-Testable | Testable |
|------|-------------|----------|
| Method | "We propose a novel approach" | "We propose X, which achieves Y% improvement on Z benchmark" |
| Analysis | "We provide insights" | "We demonstrate that component A is necessary and sufficient for the observed improvement through ablation" |
| Resource | "We release a dataset" | "We release a benchmark of N examples across K categories, establishing baseline performance at Y%" |

### Contribution Hierarchy

Order contributions by strength:
1. **Primary**: The main technical contribution (usually the method itself)
2. **Secondary**: A supporting contribution (usually analysis or insight)
3. **Tertiary**: An enabling contribution (usually a resource, benchmark, or tool)

## Section 4: Experimental Plan

### What to Include

Structure this section to align with what `experiment-pipeline` will need:

**Datasets**:
- Which datasets will you use? Why these specifically?
- What splits? How many examples per split?
- Any preprocessing or filtering?

**Baselines**:
- Which methods will you compare against? (At least 3, including the current state-of-the-art)
- Will you use official implementations or re-implementations?
- Any baselines that need adaptation for your setting?

**Metrics**:
- Primary metric (the ONE number that determines success)
- Secondary metrics (additional perspectives on quality)
- Any qualitative evaluation? (Visualizations, human judgment)

**Ablation design**:
- What components will you ablate?
- Which ablation design? (Leave-one-out, additive, substitution)
- This should map directly to Contribution 2 (analysis claim)

### Connecting to experiment-pipeline

The experiment plan here becomes the input for `experiment-pipeline`:
- Datasets and baselines → Stage 1 (Initial Implementation)
- Metrics → Gate conditions for all stages
- Ablation design → Stage 4

## Section 5: Expected Results

### Quantitative Targets

Set specific, measurable targets for your primary and secondary metrics:
- "We expect 15-20% latency reduction compared to the unmodified model"
- "We target ≥95% of original accuracy on MMLU, ≥90% on GSM8K"

**Why specificity matters**: Vague expectations ("significant improvement") can't be evaluated. Specific targets force you to reason about whether the idea is realistic. If you can't set a target, you don't yet understand the problem well enough.

### Qualitative Expectations

What should the results LOOK like beyond the numbers?
- "The method should show larger gains on longer sequences (>4K tokens)"
- "Pruning ratios should vary across layers, with attention layers pruned more aggressively"

These qualitative predictions, if confirmed, strengthen the narrative that you understand WHY the method works.

### Calibration

Set targets that are ambitious but realistic:
- Too conservative: "We expect marginal improvement" — then why bother?
- Too ambitious: "We will achieve 10x speedup with no quality loss" — likely unrealistic, sets up for disappointment
- Right calibration: "15-20% improvement" — specific range, meaningful impact, achievable

## Section 6: Risks and Mitigations (Practical Extension)

This section is not in the paper's proposal structure but is valuable for practical research planning.

### Risk Categories

**Technical risks**: The method might not work for specific technical reasons.
- Example: "Attention head pruning may break cross-layer dependencies"
- Mitigation: "We'll monitor per-layer activation patterns and use gradient-based importance scores"

**Resource risks**: Time, compute, or data constraints might prevent completion.
- Example: "Full training on 7B model requires 8x A100 for 72 hours per run"
- Mitigation: "Validate approach on 1.3B model first; scale up only after confirming the method works"

**Evaluation risks**: The evaluation might not capture the method's true performance.
- Example: "MMLU may not capture reasoning degradation from pruning"
- Mitigation: "Include chain-of-thought evaluation on GSM8K and HumanEval in addition to MMLU"

### Fallback Plans

For each major technical risk, describe what you'd do if it materializes:
1. Can you modify the method to address the issue?
2. Can you scope the contribution differently (narrower claims but solid evidence)?
3. Is there a plan B approach that avoids the risk entirely?

A proposal with honest risks and concrete fallback plans is more credible than one with no acknowledged risks.
