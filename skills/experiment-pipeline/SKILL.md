---
name: experiment-pipeline
description: "Guides structured 4-stage experiment execution with attempt budgets and gate conditions: Stage 1 initial implementation (reproduce baseline), Stage 2 hyperparameter tuning, Stage 3 proposed method validation, Stage 4 ablation study. Integrates with evo-memory (load prior strategies, trigger IVE/ESE) and experiment-craft (5-step diagnostic on failure). Use when: user has a planned experiment, needs to reproduce baselines, organize experiment workflow, or systematically validate a method. Do NOT use for debugging a specific experiment failure (use experiment-craft) or designing which experiments to run (use paper-planning)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, experimentation, experiment-design]
---

# Experiment Pipeline

A structured 4-stage framework for executing research experiments from initial implementation through ablation study, with attempt budgets and gate conditions that prevent wasted effort. This follows the Experiment Tree Search design from the EvoScientist paper, where the engineer agent iteratively generates executable code, runs experiments, and records structured execution results at each stage.

## When to Use This Skill

- User has a planned experiment and needs to organize the execution workflow
- User wants to systematically validate a novel method against baselines
- User asks about experiment stages, attempt budgets, or when to move on
- User needs to reproduce baseline results before testing their method
- User mentions "experiment pipeline", "baseline first", "ablation study", "stage budget", "experiment execution"

## The Pipeline Mindset

**Experiments fail for two reasons: wrong order and no stopping criteria.** Most researchers jump straight to testing their novel method without verifying their baseline setup, then wonder why results don't make sense. Others spend weeks tuning hyperparameters without a budget, hoping the next run will work.

The 4-stage pipeline solves both problems. It enforces a strict order (each stage validates assumptions the next stage depends on) and assigns attempt budgets (forcing systematic thinking over brute-force iteration).

## Before Starting: Load Prior Knowledge

If coming from `idea-tournament`, your research proposal (Phase 4) provides the experiment plan — datasets, baselines, metrics, and ablation design — that maps directly to Stages 1-4 below.

Before entering the pipeline, load Experimentation Memory (M_E) from prior cycles:

1. Refer to the **evo-memory** skill → Read M_E at `/memory/experiment-memory.md`
2. Select the top-1 entry (k_E=1) most relevant to the current experiment domain by comparing each entry's Context and Category against the current problem
3. The selected strategy informs hyperparameter ranges (Stage 2), debugging approaches (Stages 1-3), and training configurations across all stages
4. If M_E doesn't exist yet (first cycle), skip this step and proceed — your results will seed M_E via ESE after pipeline completion

## 4-Stage Pipeline Overview

Each stage follows a **generate → execute → record → diagnose → revise** loop:

| Stage | Goal | Budget (N_E^s) | Gate Condition |
|-------|------|--------|----------------|
| 1. Initial Implementation | Get baseline code running and reproduce known results | ≤20 attempts | Metrics within 2% of reported values (or within reported variance) |
| 2. Hyperparameter Tuning | Optimize config for your setup | ≤12 attempts | Stable config, variance < 5% across 3 runs |
| 3. Proposed Method | Implement & validate novel method | ≤12 attempts | Outperforms tuned baseline on primary metric, consistent across 3 runs |
| 4. Ablation Study | Prove each component's contribution | ≤18 attempts | All claims evidenced with controlled experiments |

Each stage saves artifacts to `/experiments/stageN_name/`.

### The Stage Loop

Within every stage, repeat this cycle for each attempt:

1. **Generate**: Form a hypothesis or plan for this attempt. What specifically will you try? What do you expect to happen?
2. **Execute**: Run the experiment. Record exact configuration, code changes, and runtime.
3. **Record**: Log results immediately using the stage log template. Include both metrics and observations.
4. **Diagnose**: Compare results to expectations. If they match, assess the gate condition. If they don't, load `experiment-craft` for the 5-step diagnostic flow.
5. **Revise**: Based on diagnosis, either advance to the next stage (gate met) or plan the next attempt (gate not met).

## Stage 1: Initial Implementation

**Goal**: Find or generate executable baseline code and verify it reproduces published results. This stage corresponds to the paper's "initial implementation" — the engineer agent searches for working code, runs it, and records structured execution results.

**Why this matters**: If you can't get the baseline running and reproducing known results, every subsequent comparison is meaningless. Initial implementation validates your data pipeline, evaluation code, training infrastructure, and understanding of prior work.

**Budget**: ≤20 attempts (N_E^1=20). Baselines can be tricky — missing details in papers, version mismatches, unreported preprocessing steps. 20 attempts gives enough room to debug without allowing infinite tinkering.

**Gate**: Primary metrics within 2% of reported values (or within the reported variance if provided).

**Process**:
1. Find the original baseline code (official repo, re-implementations, or write from paper description)
2. Get the code running in your environment — resolve dependencies, fix compatibility issues
3. Match the exact training configuration from the paper (dataset splits, preprocessing, hyperparameters)
4. Run and compare metrics. If off by >2%, diagnose the gap
5. Common pitfalls: different random seeds, different data splits, unreported data augmentation, framework version differences

**When to load `experiment-craft`**: If attempts 1-5 all fail significantly (>10% gap), switch to the 5-step diagnostic flow to isolate the cause before burning more attempts.

**Output**: `/experiments/stage1_baseline/` containing results, config, and verified baseline code.

See [references/stage-protocols.md](references/stage-protocols.md) for detailed initial implementation checklists.

## Stage 2: Hyperparameter Tuning

**Goal**: Find the optimal hyperparameter configuration for YOUR specific setup.

**Why this matters**: Published hyperparameters are tuned for the authors' setup. Your hardware, data version, framework version, or subtle implementation differences mean their config may not be optimal for you. Tuning now prevents confounding your novel method's results with suboptimal baselines.

**Budget**: ≤12 attempts. Hyperparameter tuning has diminishing returns. If 12 structured attempts don't find a stable config, the problem is likely deeper than hyperparameters.

**Gate**: Stable configuration found — variance < 5% across 3 independent runs with different random seeds.

**Process**:
1. Identify the most sensitive hyperparameters (usually: learning rate, batch size, loss weights)
2. Start with coarse search on the most sensitive parameter
3. Narrow the range based on results, then move to the next parameter
4. Validate final config with 3 independent runs

**Priority order for tuning**: Learning rate → batch size → loss weights → regularization → architecture-specific params. This order reflects typical sensitivity.

**When to load `experiment-craft`**: If results are highly unstable (variance > 20%) across runs, there's likely a training instability issue. Use diagnostic flow.

**Output**: `/experiments/stage2_tuning/` containing tuning logs, final config, and stability verification.

See [references/attempt-budget-guide.md](references/attempt-budget-guide.md) for budget rationale and adjustment rules.

## Stage 3: Proposed Method

**Goal**: Implement and validate your novel method, demonstrating improvement over the tuned baseline.

**Why this matters**: This is the core contribution. But because you've verified the baseline (Stage 1) and optimized the config (Stage 2), any improvement you see is genuinely attributable to your method — not to a better-tuned setup or a broken baseline.

**Budget**: ≤12 attempts. Your method should work within a reasonable number of iterations if the underlying idea is sound. Excessive attempts suggest a fundamental problem, not a tuning issue.

**Gate**: Outperforms the tuned baseline on the primary metric. The improvement should be consistent across at least 3 runs.

**Process**:
1. Implement the core method incrementally — don't add everything at once
2. Test each component's integration with the baseline pipeline
3. Run full training and compare against Stage 2 results
4. If underperforming, isolate which component causes the gap

**Integration strategy**: Add your method's components one at a time to the working baseline. Each added component should stay within 20% of the baseline's performance — if a single component causes a >20% regression, isolate and debug it before proceeding. Never integrate the full method in one shot.

**When to load `experiment-craft`**: When your method underperforms the baseline despite correct implementation. The 5-step diagnostic flow will help distinguish between implementation bugs and fundamental issues.

**Critical decision — failure classification**: If the method underperforms the baseline after exhausting the attempt budget, hand off to `evo-memory` for IVE (Idea Validation Evolution) — this is evo-memory's job, not this skill's. IVE triggers under two conditions:
1. **No executable code**: Cannot find working code within the budget at any stage.
2. **Worse than baseline**: Experiments complete but the method underperforms.

The `evo-memory` skill will classify the failure as:
- **Implementation failure**: Bugs or missing tricks → retryable in a future cycle.
- **Fundamental direction failure**: Core idea doesn't work → update ideation memory to prevent retrying.

**Output**: `/experiments/stage3_method/` containing method code, results, comparison with baseline.

## Stage 4: Ablation Study

**Goal**: Prove that each component of your method contributes meaningfully to the final result.

**Why this matters**: Reviewers will ask "is component X really necessary?" for every part of your method. Without ablation, you can't answer. More importantly, ablation helps YOU understand why your method works — sometimes components you thought were important aren't, and vice versa.

**Budget**: ≤18 attempts. Ablation requires multiple controlled experiments — one per component being ablated, plus interaction effects. 18 attempts covers a method with 4-5 components.

**Gate**: Every claimed contribution is supported by a controlled experiment showing its effect.

**Process**:
1. List all components of your method that you claim contribute to performance
2. Design ablation experiments: remove ONE component at a time, measure the impact
3. For components that interact, test interaction effects
4. Verify that no single component's removal improves results (would invalidate the claim)

**Three ablation designs**:
- **Leave-one-out**: Remove each component individually. Shows each component's marginal contribution.
- **Additive**: Start from baseline, add components one at a time. Shows incremental gains.
- **Substitution**: Replace your component with an alternative approach. Shows your component is better than alternatives, not just better than nothing.

**When to load `experiment-craft`**: If ablation results contradict your hypothesis (removing a component improves results), use diagnostic flow to understand why.

**Output**: `/experiments/stage4_ablation/` containing ablation results table, per-component analysis.

See [references/stage-protocols.md](references/stage-protocols.md) for detailed ablation design patterns.

## Integrating experiment-craft for Diagnosis

When a stage attempt fails, refer to the **experiment-craft** skill for structured diagnosis:

1. Follow the **experiment-craft** diagnostic protocol
2. Run the 5-step diagnostic flow (observe, hypothesize, test, conclude, prescribe)
3. The diagnosis does NOT consume your stage budget — it's a free analysis step
4. The diagnosis output (a prescription) becomes the plan for your next attempt
5. Return to the pipeline and record the diagnosis in your trajectory log

**Trigger points**: After any failed attempt in any stage. Especially important:
- **Stage 1**: After 5+ failed attempts (>10% gap from reported metrics)
- **Stage 2**: When variance > 20% across runs
- **Stage 3**: When method consistently underperforms baseline
- **Stage 4**: When ablation results contradict your hypothesis

## Code Trajectory Logging

Every attempt across all stages should be logged in a structured format that captures not just WHAT you did but WHY and WHAT YOU LEARNED. These logs feed into `evo-memory`'s Experiment Strategy Evolution (ESE) mechanism.

For each attempt, record:
- **Attempt number** and stage
- **Hypothesis**: What you expected and why
- **Code changes**: Summary of what was modified (not a full diff, but the key changes)
- **Result**: Metrics and observations
- **Analysis**: Whether the hypothesis was confirmed or refuted, and what you learned

See [references/code-trajectory-logging.md](references/code-trajectory-logging.md) for the full logging format and how logs feed into `evo-memory`.

## Counterintuitive Pipeline Rules

Prioritize these rules during experiment execution:

1. **Initial implementation is not wasted time**: It validates your entire infrastructure — data pipeline, evaluation code, training setup. Skipping it means every subsequent result is built on unverified ground. Most "method doesn't work" bugs are actually baseline setup bugs.

2. **Budget limits prevent rabbit holes**: Fixed attempt budgets force you to think systematically. When you know you have 12 attempts, you design each one to maximize information. Without limits, attempt #47 is rarely more informative than attempt #12 — it's just more desperate.

3. **Stage order is non-negotiable**: Each stage validates assumptions the next depends on. Skipping Stage 1 means Stage 3 results could be wrong due to a broken baseline. Skipping Stage 2 means Stage 3 improvements might just be better hyperparameters, not a better method. There are no shortcuts.

4. **Ablation is not optional cleanup**: It's the primary evidence that your method works for the right reasons. A method that outperforms the baseline but has no ablation is a method you don't understand. Reviewers know this.

5. **Failed attempts are data, not waste**: Each failed attempt narrows the search space and reveals something about the problem. Log failures carefully — they feed into `evo-memory` and prevent future researchers from repeating the same mistakes.

6. **Early termination is a feature**: Stopping before budget exhaustion is smart, not lazy. If the gate is clearly unachievable after systematic attempts, escalate to `evo-memory` IVE rather than burning remaining budget on increasingly random variations.

## Handoff to Paper Writing

When all four stages are complete, pass these artifacts to `paper-writing`:

| Artifact | Source Stage | Used By |
|----------|-------------|---------|
| Initial implementation results | Stage 1 | Comparison tables, setup verification |
| Optimal hyperparameter config | Stage 2 | Reproducibility section |
| Method vs baseline comparison | Stage 3 | Main results table |
| Ablation study results | Stage 4 | Ablation table, contribution claims |
| Code trajectory logs (all stages) | All stages | Method section details, supplementary |
| Implementation details and tricks | Stages 1-3 | Method section, reproducibility (captured in trajectory log Analysis fields and `[Reusable]` tags) |

Also pass results to `evo-memory` for evolution updates:
- If any stage exhausts budget without executable code, OR Stage 3 method underperforms the tuned baseline → trigger IVE (Idea Validation Evolution)
- If all stages succeeded → trigger ESE (Experiment Strategy Evolution)

## Skill Integration

### Before Starting (load memory)
Refer to the **evo-memory** skill to read Experimentation Memory:
→ Read M_E at `/memory/experiment-memory.md`

### On Failure (within any stage)
Refer to the **experiment-craft** skill for 5-step diagnostic:
→ Run diagnosis → Return to pipeline

### On IVE Trigger (budget exhausted or method underperforms)
Refer to the **evo-memory** skill for failure classification:
→ Run IVE protocol

### On Pipeline Success (all 4 stages complete)
Refer to the **evo-memory** skill for strategy extraction:
→ Run ESE protocol with trajectory logs

### Handoff to Paper Writing
Refer to the **paper-writing** skill:
→ Pass all stage artifacts

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| Per-stage checklists and patterns | [stage-protocols.md](references/stage-protocols.md) | Detailed guidance for each stage |
| Budget rationale and adjustment | [attempt-budget-guide.md](references/attempt-budget-guide.md) | When budgets feel too tight or too loose |
| Code trajectory logging format | [code-trajectory-logging.md](references/code-trajectory-logging.md) | Recording attempts for evo-memory |
| Stage log template | [stage-log-template.md](assets/stage-log-template.md) | Logging a single stage's progress |
| Pipeline tracker template | [pipeline-tracker-template.md](assets/pipeline-tracker-template.md) | Tracking the full 4-stage pipeline |
