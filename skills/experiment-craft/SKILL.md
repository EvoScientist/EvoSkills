---
name: experiment-craft
description: "Use this skill when the user wants to debug, diagnose, or systematically iterate on an experiment that already exists, or when they need a structured experiment log for tracking runs, hypotheses, failures, results, and next steps during active research. Apply it to underperforming methods, training that will not converge, regressions after a change, inconsistent results across datasets, aimless experimentation without progress, and questions like 'why doesn't this work?', 'no progress after many attempts', or 'how should I investigate this failure?'. Also use it for setting up practical experiment logging/record-keeping that supports debugging and iteration. Do not use it for designing a brand-new experiment pipeline or full experiment program (use experiment-pipeline), generating research ideas, fixing isolated coding/syntax errors, or writing retrospective summaries into research memory/notes/knowledge bases."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, experimentation, experiment-design]
---

# Experiment Craft

A systematic approach to running, debugging, and iterating on research experiments. The critical skill is not running more experiments — it's understanding WHY experiments fail.

## When to Use This Skill

- User's experiment is not working or producing unexpected results
- User needs help diagnosing why a method fails on certain data
- User wants to organize their experiment process with structured logging
- User asks about debugging research code or iterating on approaches
- User mentions "experiment debugging", "why doesn't this work", "experiment log", "results are wrong"

> This skill is typically loaded from within `experiment-pipeline` when a stage attempt fails. After debugging, return to the pipeline's stage-gate structure to continue. Can also be used standalone for any experiment debugging.

## The Debugging Mindset

**Finding WHY experiments fail is the most critical research skill.** Not analyzing results leads to two failure modes:
1. **Slow progress**: Running random experiments without understanding failure causes
2. **Wasted time**: Abandoning good approaches because activation tricks were missed

The goal is not to run more experiments. The goal is to run the RIGHT experiments — ones that isolate causes and test specific hypotheses.

## 5-Step Diagnostic Flow

When an experiment fails or produces unexpected results, follow these five steps:

### Step 1: Collect Failure Cases

Gather concrete examples of bad results. Look at the actual outputs, not just aggregate metrics. What specifically went wrong? Are the failures systematic or random?

### Step 2: Find a Working Version

You need a baseline that works. Two ways to find one:

- **Simplify the task**: Reduce data complexity, relax the task setting, add more supervision, use easier inputs
- **Remove your changes**: Start from the baseline method and remove your algorithmic improvements one by one

If you can't find any working version, simplify further until something works. There is always a simple enough version that works.

### Step 3: Bridge the Gap

Starting from the working version, incrementally add complexity until it breaks:

- Add ONE factor at a time (more complex data, one algorithmic change, one constraint)
- Find the single factor that causes failure
- The more atomic the identified cause, the more useful the diagnosis

This step isolates the cause. Without it, you're guessing.

### Step 4: Hypothesize and Verify

Based on the isolated cause from Step 3:

1. List possible explanations for why this factor causes failure
2. Rank by likelihood (based on your understanding and literature)
3. Design targeted experiments to verify or eliminate each hypothesis
4. Confirm the actual cause experimentally — don't rely on intuition alone

### Step 5: Propose and Implement a Fix

Based on the confirmed cause:

- Search for techniques that address this specific cause (use your literature tree from the `research-ideation` skill)
- Design a fix that targets the confirmed cause, not the surface symptom
- Verify the fix works on the original failure cases
- Check that the fix doesn't break previously working cases

See [references/debugging-methodology.md](references/debugging-methodology.md) for detailed branching logic and a cause taxonomy.

## Counterintuitive Experiment Rules

Prioritize these rules during experimental work:

1. **Change only one variable at a time**: If you change two things and it works, you don't know which one fixed it. If you change two things and it doesn't work, you don't know which one is wrong. Single-variable changes are slower per experiment but faster overall.
2. **Fast iteration requires effective experiments, not more experiments**: Blind experimentation makes things worse. One well-designed diagnostic experiment is worth ten random trials.
3. **Some great techniques don't work alone**: They need specific activation tricks — learning rate schedules, initialization schemes, data preprocessing steps. Don't discard a technique after one failed attempt. Check related papers for their undisclosed tricks.
4. **Check related papers for their tricks**: Papers solving similar technical challenges often have critical implementation details buried in supplementary material or code. These tricks can make the difference between a technique working or failing.
5. **"Once you've ruled out the impossible, whatever remains must be true"**: Systematic elimination beats intuition. When debugging, explicitly list ALL possible causes, then eliminate them one by one with targeted experiments.

## Experiment Logging

Every experiment should be logged with five sections. Use the template at [assets/experiment-log-template.md](assets/experiment-log-template.md).

| Section | What to Record |
|---------|---------------|
| Purpose | Why you're running this experiment; what you expect to learn |
| Setting | Data, algorithm changes, hyperparameters — everything needed to reproduce |
| Results | Quantitative metrics + qualitative observations + specific good/failure cases |
| Analysis | Do results match expectations? If not, hypothesized causes ranked by likelihood |
| Next Steps | What to do based on the analysis — YOU are the project leader |

**The "Next Steps" section is the most important.** Don't wait for someone to tell you what to do next. Analyze your results and propose the next experiment yourself. This is what distinguishes a researcher from a technician.

> **Cross-cycle learning**: If using `experiment-pipeline`, your experiment logs feed into `evo-memory`'s ESE (Experiment Strategy Evolution) mechanism. Tag reusable strategies with `[Reusable]` so ESE can extract them for future cycles.

## Return to experiment-pipeline

After completing the 5-step diagnostic flow, return to `experiment-pipeline` with:
- Confirmed cause of failure (from Step 4)
- Proposed fix and its verification status (from Step 5)
- Updated experiment log entry

## Handoff to Paper Writing

When experiments succeed and you have a complete set of results, pass these artifacts to `paper-writing`:

| Artifact | Source | Used By |
|----------|--------|---------|
| Final experiment results (tables and figures) | Experiment logs | Experiments section |
| Ablation study results | Diagnostic experiments | Ablation tables |
| Failure case analysis | Step 1 + Step 3 | Limitations discussion |
| Key implementation details and tricks | Steps 3-5 | Method section / Supplementary |
| Baseline comparison results | Step 2 | Comparison tables |

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| Debugging methodology | [debugging-methodology.md](references/debugging-methodology.md) | Diagnosing why experiments fail |
| Experiment log template | [experiment-log-template.md](assets/experiment-log-template.md) | Recording experiment details |
