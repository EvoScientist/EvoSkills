---
name: evo-memory
description: "Manages persistent research memory across ideation and experimentation cycles. Maintains two stores: Ideation Memory M_I (feasible/unsuccessful directions) and Experimentation Memory M_E (reusable strategies for data processing, model training, architecture, debugging). Three evolution mechanisms: IDE (after idea-tournament), IVE (after experiment failure — classifies failures as implementation vs fundamental), ESE (after experiment success — extracts reusable strategies). Use when: updating memory after completing idea tournaments or experiment pipelines, classifying why a method failed (implementation vs fundamental failure), starting a new research cycle needing prior knowledge, user mentions 'update memory', 'classify failure', 'what worked before', 'research history', 'evolution'. Do NOT use for running experiments (use experiment-pipeline), debugging experiment code (use experiment-craft), or generating ideas (use idea-tournament)."
allowed-tools: "write_file edit_file read_file think_tool"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, meta-learning]
---

# Evo-Memory

A persistent learning layer that accumulates research knowledge across ideation and experimentation cycles. Maintains two memory stores and implements three evolution mechanisms that feed learned patterns back into future research.

## When to Use This Skill

- User has completed an `idea-tournament` and needs to update Ideation Memory
- User has completed (or failed) an `experiment-pipeline` and needs to update memory
- User is starting a new research cycle and wants to load prior knowledge
- User asks about research memory, learned patterns, or cross-cycle knowledge
- User mentions "evo-memory", "update memory", "what worked before", "research history", "evolution"

## The Learning Layer

Research is iterative. Each cycle — from ideation through experimentation — generates knowledge that should inform the next cycle. Without persistent memory, every new project starts from scratch, repeating mistakes and rediscovering patterns.

Evo-memory solves this by maintaining two structured memory stores and three evolution mechanisms that extract, classify, and inject knowledge across cycles.

## Two Memory Stores

### Ideation Memory (M_I)

**Location**: `/memory/ideation-memory.md`

Records what you've learned about research DIRECTIONS — which areas are promising and which are dead ends.

**Two sections**:

| Section | What It Contains | Example Entry |
|---------|-----------------|---------------|
| Feasible Directions | Directions that showed promise in prior cycles | "Contrastive learning for few-shot classification — confirmed feasible, top-3 in tournament cycle 2" |
| Unsuccessful Directions | Directions that were tried and failed, with failure classification | "Autoregressive generation for real-time video — fundamental failure: latency constraint incompatible with autoregressive decoding" |

**Each entry records**: Direction name, one-sentence summary, evidence (which cycle, what results), classification (feasible / implementation failure / fundamental failure), date.

**How it's used**: `idea-tournament` reads M_I at the start of Phase 1. The paper uses embedding-based retrieval with cosine similarity, selecting the top-k_I most similar items (k_I=2 in experiments). Feasible directions from prior cycles can seed new tree branches. Unsuccessful directions are used during pruning — fundamental failures are pruned; implementation failures may be retried.

See [assets/ideation-memory-template.md](assets/ideation-memory-template.md) for the template.

### Experimentation Memory (M_E)

**Location**: `/memory/experiment-memory.md`

Records what you've learned about research STRATEGIES — which technical approaches and configurations work in practice.

The paper defines M_E as storing "reusable data processing and model training strategies." ESE jointly summarizes (i) a **data processing strategy** and (ii) a **model training strategy**. We extend this with two additional practical sections (architecture and debugging) for comprehensive coverage.

**Two core sections (from paper) + two practical extensions**:

| Section | Source | What It Contains | Example Entry |
|---------|--------|-----------------|---------------|
| Data Processing Strategies | Paper (core) | Preprocessing, augmentation, and data handling patterns | "For noisy sensor data: median filter before normalization reduces training instability by ~40%" |
| Model Training Strategies | Paper (core) | Hyperparameters, training tricks, and training schedules | "Learning rate warmup for 10% of steps prevents early divergence in transformer fine-tuning" |
| Architecture Strategies | Extension | Design choices, module configurations, and structural patterns | "Residual connections are critical for modules inserted deeper than 10 layers in transformers" |
| Debugging Strategies | Extension | Diagnostic patterns that resolved experiment failures | "When loss plateaus after 50% of training: check gradient norm — clipping threshold may be too aggressive" |

**Each entry records**: Strategy name, context (when to use this), evidence (which cycle, what results), generality (domain-specific or broadly applicable), date.

**How it's used**: `experiment-pipeline` reads M_E at the start of each cycle. The paper uses embedding-based retrieval with cosine similarity, selecting the top-k_E most similar items (k_E=1 in experiments). Relevant strategies from prior cycles inform hyperparameter choices, data processing decisions, and debugging approaches, reducing the number of attempts needed.

See [assets/experiment-memory-template.md](assets/experiment-memory-template.md) for the template.

## Three Evolution Mechanisms

### IDE — Idea Direction Evolution

**Trigger**: After `idea-tournament` completes (Phase 3 direction summary is available).

**Purpose**: Extract promising research directions from the tournament results and store them in M_I for future cycles.

**Paper Prompt**: Use the IDE prompt from [references/paper-prompts.md](references/paper-prompts.md) as the primary extraction mechanism. Fill in `{user_goal}` from the original research direction and `{top_ranked_ideas}` from `/direction-summary.md`, then reason through the prompt step by step. The output (DIRECTION SUMMARY with Title, Core idea, Why promising, Requirements, Validation plan) feeds directly into the steps below.

**Process**:
1. Read current M_I from `/memory/ideation-memory.md`
2. Run the paper's IDE prompt (see above), reasoning through it step by step
3. For each direction in the prompt output, abstract it to a reusable level. "Attention-based feature selection for 3D point clouds" becomes "Cross-domain attention mechanisms for sparse data" — specific enough to be useful, abstract enough to transfer.
4. Check M_I for existing entries on similar directions. Update if exists, append if new.
5. If any previously "feasible" direction was found to be exhausted during this cycle, update its status.
6. Write an evolution report documenting what changed and why.

**Key principle**: Store directions, not ideas. A direction like "contrastive learning for structured data" can spawn many specific ideas across future cycles. A specific idea like "SimCLR with graph augmentations on molecular datasets" is too narrow to be reusable.

See [references/ide-protocol.md](references/ide-protocol.md) for the full process.

### IVE — Idea Validation Evolution

**Trigger** (two conditions, following the paper):
1. **Rule-based**: The engineer cannot find any executable code within the pre-defined budget at any stage — the code simply doesn't run.
2. **LLM-based**: Experiments complete but the proposed method performs worse than the baseline, as determined by analyzing the execution report W.

**Purpose**: Classify WHY the method failed and update M_I accordingly. This is the most critical evolution mechanism because it prevents future cycles from repeating dead-end directions.

**Paper Prompt**: Use the IVE prompt from [references/paper-prompts.md](references/paper-prompts.md) as the primary classification mechanism. Fill in `{research_proposal}` from `/research-proposal.md` and `{execution_report}` from the stage trajectory logs, then reason through the prompt step by step. The prompt classifies the failure as FAILED(NoExecutableWithinBudget), FAILED(WorseThanBaseline), or NOT_FAILED.

**After running the paper prompt**:
- **FAILED(NoExecutableWithinBudget)** → Implementation failure (retryable). Record as "retry with fixes" in M_I.
- **FAILED(WorseThanBaseline)** → Use the 5-question diagnostic below to distinguish implementation vs fundamental failure.
- **NOT_FAILED** → No IVE update needed.

**Five diagnostic questions** (for WorseThanBaseline cases):
1. Did any variant show partial success? (Yes → implementation failure)
2. Does the hypothesis hold for simpler problems? (No → fundamental failure)
3. Have related approaches succeeded in published work? (Yes → implementation failure)
4. Were failure patterns consistent across implementations? (Yes → fundamental failure)
5. Can you identify specific bugs in trajectory logs? (Yes → implementation failure)

If 3+ answers point to one type, classify as that type. If split, classify as implementation failure (more conservative — allows retry).

**Retry escalation rule**: If a direction has been classified as "implementation failure" 3 times across different cycles, escalate to a careful re-evaluation — three separate implementation failures may indicate the direction is harder than it appears. Consider reclassifying as fundamental.

See [references/ive-protocol.md](references/ive-protocol.md) for the full process and worked examples.

### ESE — Experiment Strategy Evolution

**Trigger**: After `experiment-pipeline` succeeds — all 4 stages complete and gates met.

**Purpose**: Distill reusable strategies from the successful experiment run and store them in M_E for future cycles.

**Paper Prompt**: Use the ESE prompt from [references/paper-prompts.md](references/paper-prompts.md) as the primary extraction mechanism. Fill in `{research_proposal}` from `/research-proposal.md` and `{trajectories}` from all 4 stage trajectory logs, then reason through the prompt step by step. The prompt outputs DATA SUMMARY and MODEL SUMMARY, which map to our Data Processing Strategies and Model Training Strategies sections.

**Process**:
1. Run the paper's ESE prompt (see above), reasoning through it step by step
2. Use the DATA SUMMARY output to populate the Data Processing Strategies section of M_E
3. Use the MODEL SUMMARY output to populate the Model Training Strategies section of M_E
4. After the prompt run, manually extract from trajectory logs:
   - **Architecture decisions** (extension): Which design choices were key to performance?
   - **Debugging patterns** (extension): Which diagnostic approaches resolved failures fastest?
5. For each identified pattern, assess generality:
   - Is this domain-specific (only works for this type of data/model)?
   - Or broadly applicable (likely to work in other contexts)?
6. Check M_E for existing similar entries. Update if exists, append if new.
7. Write an evolution report documenting the extracted strategies.

**Generalization guidelines**: A strategy is broadly applicable if it addresses a general challenge (training instability, overfitting, slow convergence) rather than a domain-specific characteristic. When in doubt, record the context alongside the strategy and let future users judge applicability.

See [references/ese-protocol.md](references/ese-protocol.md) for the full process.

## Reading Memory at Cycle Start

When starting a new research cycle (loading `idea-tournament` or `experiment-pipeline`):

1. Read `/memory/ideation-memory.md` and `/memory/experiment-memory.md`
2. Summarize relevant entries to inject into the current context
3. For `idea-tournament`: Use M_I feasible directions to seed tree branches. Use M_I unsuccessful directions (fundamental failures only) during pruning.
4. For `experiment-pipeline`: Use M_E strategies to inform hyperparameter ranges, training schedules, and debugging approaches.

**Don't blindly apply old strategies.** Context matters. A strategy that worked for image classification may not work for text generation. Always check the recorded context against the current problem.

**Retrieval method**: The paper uses embedding-based cosine similarity for retrieval. In practice, perform this semantic comparison by reading each entry's Summary/Context and Retrieval Tags, then judging relevance to the current goal. If automated embedding tools are available in your environment, use those instead for larger memory stores.

### For idea-tournament (inject M_I)

1. Read `/memory/ideation-memory.md`
2. Select the top-k_I=2 entries most relevant to the user's current goal. Compare the user's goal statement against each entry's Summary and Retrieval Tags for semantic similarity.
3. For each selected feasible direction: incorporate it as a seed branch at Level 1 of the idea tree. Example injection: *"Prior cycle found 'Modality-aware model compression' promising (Elo 1548, cycle 3). Use as a Level 1 branch alongside new technique variants."*
4. For each unsuccessful direction with `Failure Classification: Fundamental`: flag for pruning. Example injection: *"Prior cycle confirmed 'Autoregressive real-time video generation' is a fundamental failure (O(n) latency). Prune any tree branch matching this pattern."*

### For experiment-pipeline (inject M_E)

1. Read `/memory/experiment-memory.md`
2. Select the top-k_E=1 entry most relevant to the current experiment domain. Compare the experiment's problem description against each entry's Context and Category.
3. Inject the selected strategy as context for all stages. Example injection: *"Prior cycle found 'Cosine annealing with warm restarts (T_0=10, T_mult=2)' effective for transformer fine-tuning on small datasets (confirmed, 2 cycles). Apply in Stage 2 tuning as the default schedule."*
4. Also scan the Debugging Strategies section for any entries matching the current domain — these can save significant time when diagnosing failures.

## Memory Maintenance

### Pruning Stale Entries

Periodically review both memory stores and remove or archive entries that are no longer relevant:

- Entries older than 10 cycles without being referenced
- Strategies superseded by strictly better alternatives
- Directions in fields that have fundamentally shifted (new paradigms, new state-of-the-art)

### Version Tracking

Each memory file maintains a `Last Updated` field and a cycle counter. When entries are modified (not just appended), note what changed in the evolution report. This creates an audit trail of how your research knowledge evolves.

### Evolution Reports

After each evolution mechanism triggers, generate a report saved to `/memory/evolution-reports/cycle_N_type.md`:
- What changed (added, updated, or removed entries)
- Why (evidence from the triggering cycle)
- Expected impact on future cycles

See [assets/evolution-report-template.md](assets/evolution-report-template.md) for the template.

## Counterintuitive Memory Rules

Prioritize these rules when updating and using memory:

1. **Abstract before storing**: Store directions and strategies, not specific experiment details. "Contrastive learning improves few-shot classification" is reusable across many projects; "set lr=0.001 for ResNet-50 on CIFAR-10" is not. The goal is transferable knowledge, not a lab notebook.

2. **Failed directions are more valuable than successful ones**: Knowing what NOT to try saves more time than knowing what worked. Success stories are published in papers — everyone can access them. Failure stories are rarely shared, making your failure memory a unique competitive advantage.

3. **Implementation failures are not direction failures**: The most common evolution mistake is marking a good direction as failed because the implementation was buggy. IVE exists specifically to make this distinction. When in doubt, classify as implementation failure — it's cheaper to retry a good idea than to permanently discard it.

4. **Memory decays without pruning**: A strategy that worked 10 cycles ago on different data may no longer be relevant. Accumulating stale entries adds noise that makes it harder to find useful strategies. Prune actively — a smaller, curated memory is more valuable than a large, noisy one.

5. **Cross-pollination beats deep specialization**: Strategies from M_E in one domain often transfer to another. Learning rate warmup helps in NLP AND vision AND speech. Review the full M_E before starting a new experiment pipeline, not just domain-specific entries.

6. **The evolution report is for humans**: Write reports that a researcher — not just an AI agent — can understand and act on. Include enough context that someone reading the report 6 months later understands WHY the change was made, not just WHAT changed.

## Memory Integration Points

How evo-memory connects to other skills in the pipeline:

| Trigger | Source Skill | Mechanism | Memory Updated |
|---------|-------------|-----------|----------------|
| Tournament completed | `idea-tournament` | IDE | M_I (feasible directions) |
| No executable code within budget, or method underperforms baseline | `experiment-pipeline` | IVE | M_I (unsuccessful directions) |
| Pipeline succeeded | `experiment-pipeline` | ESE | M_E (data processing + model training; optionally architecture + debugging) |
| New cycle starts | `idea-tournament` | Read (top-k_I=2) | M_I read for seeding/pruning |
| New cycle starts | `experiment-pipeline` | Read (top-k_E=1) | M_E read for strategy guidance |

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| IDE process details | [ide-protocol.md](references/ide-protocol.md) | After completing idea-tournament |
| IVE process details | [ive-protocol.md](references/ive-protocol.md) | After experiment-pipeline failure (no executable code or method underperforms) |
| ESE process details | [ese-protocol.md](references/ese-protocol.md) | After experiment-pipeline succeeds |
| Paper's actual prompts | [paper-prompts.md](references/paper-prompts.md) | Reference for exact IDE/IVE/ESE prompt design |
| Memory data structures | [memory-schema.md](references/memory-schema.md) | Understanding M_I and M_E formats |
| Ideation memory template | [ideation-memory-template.md](assets/ideation-memory-template.md) | Initializing M_I |
| Experiment memory template | [experiment-memory-template.md](assets/experiment-memory-template.md) | Initializing M_E |
| Evolution report template | [evolution-report-template.md](assets/evolution-report-template.md) | Documenting memory updates |
