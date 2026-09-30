# Expanded Review Checklist

This is an expanded version of the 5-aspect checklist from SKILL.md with additional detail and reviewer-perspective questions.

## How this file is used

This checklist is **Pass 2** of the SKILL.md protocol, not an entry point.
Pass 1 — an adversarial end-to-end read with no checklist in hand — comes
first, because a checklist run first anchors you to its own categories and
the suspicions it does not name never surface. Do not start here.

**Within Pass 2**, items marked **(Q)** are the highest-risk ones: they catch
the most common rejection reasons, and are the ones to cover first when the
whole list will not fit. Working through every item in all five aspects is
the norm before final submission.

There is no time budget attached to either. The old "~15 min / ~60+ min"
estimates described the checklist as the whole review; under the three-pass
protocol they would have described only this middle pass, and would have
understated it.

---

## Aspect 1: Contribution Sufficiency

> Core question: Does this paper give readers new knowledge?
> Core question: Does this paper provide readers with new knowledge?

### Novelty Assessment

- [ ] **(Q)** Is the core idea genuinely new, or a straightforward combination of existing ideas?
- [ ] If building on prior work, is the extension significant enough?
- [ ] Could a domain expert have easily arrived at this solution?
- [ ] Does the paper provide a new insight or understanding, not just a new method?

### Failure Case Analysis

- [ ] Are the paper's failure cases common in practice?
- [ ] Would the target audience frequently encounter scenarios where this method fails?
- [ ] Are failure cases honestly discussed?

### Technique Maturity

- [ ] Has the core technique been extensively studied before?
- [ ] If the technique is known, does the paper provide a new perspective or significant improvement?
- [ ] Is the improvement surprising or was it predictable?

### Contribution Scope

- [ ] Are the claimed contributions consistent with what the paper actually delivers?
- [ ] Is each contribution verifiable from the paper content?
- [ ] Does each contribution provide concrete technical value (not just "we propose...")?

---

## Aspect 2: Writing Clarity

> Core question: Can a reader understand and reproduce the method?

### Reproducibility

- [ ] **(Q)** Are all model architectures specified (layers, dimensions, activation functions)?
- [ ] Are training details provided (optimizer, learning rate, batch size, epochs)?
- [ ] Are data preprocessing steps described?
- [ ] Are evaluation protocols clearly defined?
- [ ] Would code release be necessary for reproducibility? If so, is it planned?

### Method Clarity

- [ ] **(Q)** Does every method module have a clear motivation paragraph?
- [ ] Is the forward process (input → steps → output) described for each module?
- [ ] Are technical advantages of each design choice explained?
- [ ] Is the method overview clear (setting → core contribution → section roadmap)?

### Structural Clarity

- [ ] Does each paragraph convey exactly one message?
- [ ] Does each paragraph's first sentence state its topic?
- [ ] Is the flow between paragraphs logical?
- [ ] Is the flow between sections smooth?
- [ ] Are transitions between ideas explicit?

### Language Quality

- [ ] Is terminology consistent throughout the paper?
- [ ] Are all symbols/notations defined before use?
- [ ] Is the writing concise (no unnecessary verbosity)?
- [ ] Are sentences grammatically correct?

---

## Aspect 3: Experimental Results Quality

> Core question: Are the results convincing?

### Quantitative Results

- [ ] **(Q)** Is the improvement over baselines significant (not within noise)?
- [ ] Are standard deviations or confidence intervals provided?
- [ ] Is the absolute performance level acceptable for the application?
- [ ] Do results hold across all datasets, or only on specific ones?

### Qualitative Results

- [ ] Are visual comparisons provided alongside tables?
- [ ] Are improvements visible in qualitative results?
- [ ] Are failure cases shown (builds trust)?
- [ ] Is the visual quality of result figures professional?

### Efficiency

- [ ] Is computational cost compared (runtime, FLOPs, memory)?
- [ ] Is the trade-off between quality and efficiency discussed?
- [ ] Are practical requirements (GPU memory, training time) reported?

---

## Aspect 4: Experimental Testing Completeness

> Core question: Are all claims tested?

### Ablation Completeness

- [ ] **(Q)** Is every claimed contribution ablated in an experiment?
- [ ] Is there a comprehensive ablation table (full model vs. removing each component)?
- [ ] Are there focused tables for design choices and hyperparameters?
- [ ] Do ablation results match the paper's claims about each component?

### Baseline Completeness

- [ ] **(Q)** Are current SOTA methods included as baselines?
- [ ] Are recent methods from the last 2-3 years included?
- [ ] Are classic/foundational methods included?
- [ ] Is the comparison fair (same data, metrics, protocol)?

### Metric Completeness

- [ ] Are all standard metrics for this task reported?
- [ ] Are metrics appropriate for what the paper claims to improve?
- [ ] Are user studies included (if applicable)?

### Dataset Coverage

- [ ] Are standard benchmarks used for comparability?
- [ ] Are challenging/diverse datasets included?
- [ ] Do datasets truly test the method's strengths and reveal its weaknesses?

---

## Aspect 5: Method Design

> Core question: Is the method sound?

### Setting Validity

- [ ] **(Q)** Are the assumptions realistic?
- [ ] Is the input data available in practice?
- [ ] Is the computational requirement practical?
- [ ] Would users actually use this method as described?

### Technical Soundness

- [ ] Is the method theoretically motivated (not just empirically)?
- [ ] Are there known failure modes? Are they addressed?
- [ ] Does the method handle edge cases gracefully?

### Robustness

- [ ] Does the method work with default hyperparameters across scenes/cases?
- [ ] Is per-scene tuning required? (Major weakness if so)
- [ ] How sensitive is the method to input quality?
- [ ] Is the method stable during training?

### Benefit vs. Cost

- [ ] **(Q)** Do the benefits of new modules outweigh the limitations they introduce?
- [ ] Is the added complexity justified by the improvement?
- [ ] Are there simpler alternatives that achieve similar results?

---

## Reviewer Perspective Questions

As a reviewer, consider these overarching questions:

1. **Significance**: Would this paper change how people in the field think or work?
2. **Novelty**: Is the core idea new and non-obvious?
3. **Soundness**: Is the method technically sound and well-evaluated?
4. **Clarity**: Is the paper well-written and easy to follow?
5. **Completeness**: Are the experiments comprehensive?
6. **Limitations**: Are limitations honestly discussed?
7. **Reproducibility**: Could I reproduce the results from the paper alone?
