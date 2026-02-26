# Debugging Methodology

A detailed guide for systematically diagnosing why experiments fail. This expands on the 5-step diagnostic flow from the main skill, with branching logic and a cause taxonomy.

## Overview: Two Diagnostic Paths

After collecting failure cases (Step 1) and finding a working version (Step 2), there are two paths to isolate the cause:

- **Path A: Working → Non-working comparison** — Start from something that works, incrementally add complexity until it breaks
- **Path B: Good cases → Failure cases comparison** — Compare what differs between successful and unsuccessful examples

Both paths aim to isolate the ONE factor that drives the performance gap.

## Step 1: Collect Failure Cases

Look at actual outputs, not just metrics:
- Save specific examples of bad results (images, text, numbers)
- Note surface phenomena: What does the failure look like?
- Is the failure systematic (same type of error) or random (different errors each time)?
- Systematic failures are easier to diagnose — they point to a specific cause

## Step 2: Find a Working Version

### Option A: Simplify the Task

Reduce difficulty until the method works:
- Use simpler/smaller data (fewer objects, lower resolution, shorter sequences)
- Relax the task constraints (more supervision, easier evaluation criteria)
- Use synthetic data where you control the ground truth

### Option B: Remove Your Changes

Roll back to the unmodified baseline:
- Start from the published baseline (their code, their settings)
- Remove YOUR algorithmic improvements one by one
- Find the version before your changes that worked

**Critical**: You need a concrete working version, not a hypothetical one. If you can't find one, simplify further.

## Step 3: Isolate the Cause

### Path A: Working → Non-working

Starting from the working version, incrementally add factors:

1. List all differences between the working version and the failing version
2. Add ONE difference at a time to the working version
3. After each addition, evaluate: does it still work?
4. Find the single factor that causes the transition from working to failing
5. The more atomic this factor, the better. If "adding module X" breaks things, try adding only part of module X

**Example progression:**
```
Working baseline                    → works
+ more complex data                → works
+ more complex data + your module  → fails ← module is the cause
```

But go deeper:
```
Working baseline + complex data          → works
+ complex data + module component A      → works
+ complex data + module component B      → fails ← component B is the cause
```

### Path B: Good Cases → Failure Cases

Compare successful and unsuccessful examples directly:

1. From the failure cases, identify cases where the method works well (good cases)
2. Compare data characteristics:
   - What differs between good and failure cases?
   - Is it data complexity? Specific data properties? Edge cases?
3. Identify the data characteristic that drives the performance gap
4. Analyze why this characteristic causes failure (technical reason)

**Example:**
```
Good cases:  objects are centered, single object, clean background
Failure cases: objects at edges, multiple overlapping, cluttered background
→ Cause: the method assumes centered single objects
```

## Step 4: Cause Taxonomy

Once you've isolated the factor, classify the cause:

### Code Bugs

| Sub-type | Diagnostic Action |
|----------|-------------------|
| Implementation error | Step through code line by line. Print intermediate outputs. Check tensor shapes. Visualize intermediate results. Compare with a reference implementation if available. |
| Misunderstanding of algorithm | Re-read the paper carefully. Understand the theory. Then re-check whether your code matches the described algorithm. Common: misunderstanding loss function terms, gradient flow, data preprocessing. |

### Algorithm Issues

| Sub-type | Diagnostic Action |
|----------|-------------------|
| Wrong hyperparameters | Check related papers for their hyperparameter settings. Try grid search on the most sensitive parameters first (usually learning rate, loss weights). |
| Missing tricks | Check related papers' supplementary material and code for tricks that made similar approaches work. Common: specific initialization, learning rate warmup, data augmentation, normalization. |
| Data mismatch | The problem might be data difficulty, not the algorithm. Try simpler data first. If the algorithm works on simple data, the issue is handling complexity — not the algorithm itself. |
| Fundamental limitation | The algorithm genuinely cannot handle this case. Verify by testing on multiple variants of the failure case. If confirmed, you need a different approach — no amount of tuning will fix a fundamental mismatch. |

### Distinguishing Code Bugs from Algorithm Issues

A useful test:
- If the method works perfectly on very simple data but fails on complex data → likely algorithm issue
- If the method fails even on simple data where it should obviously work → likely code bug
- If results are unstable across runs → likely hyperparameter sensitivity or training instability

## Step 5: Propose Solutions

### Build Your Weapon Library

Use the literature tree (see the `research-ideation` skill) to maintain a library of known techniques:
- When you encounter a confirmed cause, search your challenge-insight tree for relevant techniques
- Search broadly across domains — solutions often come from unexpected fields

### Verify Direction Regularly

Don't go too deep into one approach without checking:
- After 3-5 failed attempts at the same approach, step back and reconsider
- Discuss with colleagues — they may see alternatives you've missed
- Are you solving the right sub-problem, or have you drifted into a local minimum?

### When to Pivot

Consider switching approaches when:
- The confirmed cause is a fundamental limitation of your approach (not fixable with tricks)
- Multiple independent sub-problems each require major solutions (compound difficulty)
- You've exhausted known techniques for the confirmed cause
- A simpler formulation of the problem would still be a valid contribution

## Debugging Checklist

When stuck, verify you haven't skipped a step:

- [ ] Do you have concrete failure cases (not just bad metrics)?
- [ ] Do you have a working version to compare against?
- [ ] Have you isolated the cause to a SINGLE factor?
- [ ] Have you verified the cause experimentally (not just hypothesized)?
- [ ] Have you checked related papers for tricks and implementation details?
- [ ] Have you discussed with at least one colleague?
