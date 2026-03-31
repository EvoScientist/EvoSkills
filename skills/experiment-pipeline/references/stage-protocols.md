# Stage Protocols

Detailed checklists and common patterns for each of the 4 experiment pipeline stages. Use this as a reference during execution — it expands on the stage summaries in the main SKILL.md.

## Stage 1: Initial Implementation

### Before You Start

- [ ] Identify the baseline paper and its reported metrics
- [ ] Find the official implementation (check paper, GitHub, HuggingFace Papers)
- [ ] If no official code, find the most-starred re-implementation
- [ ] Get the code running in your environment — resolve dependencies, fix compatibility issues
- [ ] Read the paper's experimental setup section thoroughly — note dataset, splits, preprocessing, hyperparameters
- [ ] Check the paper's supplementary material for unreported details

### Common Implementation Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Different data splits | Metrics close but consistently off | Use the exact split from the paper (often a specific random seed or provided split files) |
| Framework version mismatch | Subtle numerical differences | Match the framework version from the paper's requirements or code |
| Unreported preprocessing | Large metric gap despite correct code | Check the codebase's data loading pipeline for transforms not mentioned in the paper |
| Different evaluation protocol | Metrics computed differently | Read the evaluation code carefully — is it per-sample or per-batch? Macro or micro average? |
| Hardware differences | Training diverges or converges differently | Adjust batch size and learning rate proportionally (linear scaling rule) |
| Missing random seed | Results vary significantly across runs | Use the seed from the code if available; otherwise run 3 seeds and report mean |

### Verification Checklist

- [ ] Primary metric within 2% of reported value
- [ ] Secondary metrics in the right ballpark (within 5%)
- [ ] Training curve shape matches expectations (convergence time, stability)
- [ ] Qualitative results look reasonable (visualize outputs if applicable)
- [ ] Run with 3 different seeds to verify stability

### When to Escalate

If after 5 attempts metrics are still >10% off, stop and use `experiment-craft`:
1. Collect specific failure cases (Step 1)
2. Start from the simplest possible version (Step 2)
3. Incrementally add complexity to find where results diverge (Step 3)

## Stage 2: Hyperparameter Tuning

### Tuning Priority Order

Tune parameters in this order — each subsequent parameter has less impact but more interactions:

1. **Learning rate** — Most sensitive. Try 3-5 values spanning an order of magnitude around the paper's value.
2. **Batch size** — Affects effective learning rate and regularization. Usually 2-3 options are sufficient.
3. **Loss weights** — If multiple loss terms exist. Grid search the ratios.
4. **Regularization** — Weight decay, dropout, label smoothing. Usually less sensitive.
5. **Architecture-specific** — Hidden dimensions, number of layers, attention heads. Only if default architecture is questionable.

### Search Strategies

**Coarse-to-fine** (recommended for ≤12 attempts):
1. Attempts 1-4: Coarse grid on learning rate (e.g., 1e-2, 1e-3, 1e-4, 1e-5)
2. Attempts 5-7: Narrow range around best LR, try 2-3 batch sizes
3. Attempts 8-10: Fine-tune loss weights or regularization
4. Attempts 11-12: Stability verification (3 seeds with best config)

**Bayesian optimization** (if infrastructure supports it):
- Use for >5 hyperparameters
- Start with 5 random trials, then optimize
- Still respect the 12-attempt budget

### Stability Verification

A config is "stable" when:
- [ ] Variance < 5% across 3 runs with different random seeds
- [ ] Training curves converge consistently (no run diverges)
- [ ] No outlier runs (all within 1 standard deviation of mean)

## Stage 3: Proposed Method

### Integration Strategy

**Incremental integration** (recommended):
1. Start from the fully working, tuned baseline from Stage 2 (verify Stage 2 gate was met before proceeding)
2. Add your method's simplest component first
3. Verify the pipeline still runs and produces results within 20% of the baseline
4. Add the next component
5. Continue until the full method is integrated

**Why not integrate everything at once?** If the full method fails, you won't know which component caused the failure. Incremental integration gives you immediate feedback on each component.

### Regression Testing

After each component integration:
- [ ] Method runs without errors
- [ ] Training converges (loss decreases)
- [ ] Metrics are within 20% of baseline (not yet expected to beat baseline during incremental integration)
- [ ] No previously passing test cases now fail

### Comparison Protocol

When comparing your method to the baseline:
- [ ] Use the EXACT same data, splits, and evaluation protocol
- [ ] Use the tuned config from Stage 2 as starting point
- [ ] Run both methods with the same 3 seeds
- [ ] Report mean and standard deviation
- [ ] Improvement should exceed the standard deviation to be meaningful

### Budget Exhaustion Protocol

If 12 attempts are exhausted without outperforming the baseline:

1. **Review trajectory logs** — Is there a trend? Are metrics improving but slowly?
2. **Classify the failure** (for `evo-memory` IVE):
   - Found specific bugs but ran out of time → implementation failure (retryable)
   - Core approach consistently underperforms → likely fundamental failure
   - Partial success on some metrics but not primary → needs investigation
3. **Document thoroughly** — Future cycles depend on accurate failure classification

## Stage 4: Ablation Study

### Three Ablation Designs

**Leave-one-out** (most common):
- Remove each component individually, keeping everything else
- Shows the marginal contribution of each component
- Requires N experiments for N components

**Additive** (useful for building the story):
- Start from baseline, add components one at a time
- Shows cumulative improvement
- Good for papers — tells a progressive story

**Substitution** (strongest evidence):
- Replace your component with a simpler alternative
- Shows your approach is better than alternatives, not just better than nothing
- Most convincing for reviewers but requires identifying alternatives

### What to Ablate

List every component you claim contributes to performance:
- Novel loss terms
- New architectural components (modules, layers, connections)
- Data processing innovations
- Training strategy modifications
- Post-processing steps

For each: can you remove/replace it independently? If not, test the smallest removable unit.

### Common Ablation Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|---------------|-----|
| Ablating components that interact without testing interactions | May miss that A only works with B | Test A without B, B without A, and neither |
| Not retuning after removal | Removing a component may require different hyperparameters | At minimum retune learning rate for each ablation |
| Reporting only the primary metric | Component may hurt primary but help secondary | Report all metrics for all ablations |
| Ablating too many components at once | Can't isolate individual contributions | One component per experiment |

### Ablation Results Table Format

```
| Configuration | Metric 1 | Metric 2 | Metric 3 |
|---------------|----------|----------|----------|
| Full method   |   XX.X   |   XX.X   |   XX.X   |
| w/o Component A | XX.X   |   XX.X   |   XX.X   |
| w/o Component B | XX.X   |   XX.X   |   XX.X   |
| w/o Component C | XX.X   |   XX.X   |   XX.X   |
| Baseline only |   XX.X   |   XX.X   |   XX.X   |
```

### Gate Verification

- [ ] Every claimed component shows measurable contribution when removed
- [ ] No component's removal IMPROVES results (would invalidate the claim)
- [ ] Additive ablation tells a consistent, progressive story
- [ ] Results are consistent across multiple runs (3 seeds)
