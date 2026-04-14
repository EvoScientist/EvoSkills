# Memory Schema

Complete data structure definitions for Ideation Memory (M_I), Experimentation Memory (M_E), and Evolution Reports. Use this reference when creating, reading, or maintaining memory files.

## File Locations

| Memory Store | File Path | Created By |
|-------------|-----------|------------|
| Ideation Memory (M_I) | `/memory/ideation-memory.md` | First IDE or IVE trigger |
| Experimentation Memory (M_E) | `/memory/experiment-memory.md` | First ESE trigger |
| Evolution Reports | `/memory/evolution-reports/cycle_N_type.md` | Each evolution trigger |

All paths are relative to the workspace root. Memory files persist across sessions because `/memory/` maps to the shared memory directory.

## Ideation Memory (M_I) Schema

### File Structure

```markdown
# Ideation Memory

Last Updated: [YYYY-MM-DD]
Total Cycles: [N]

## Feasible Directions

### [Direction 1 Name]
- **Summary**: ...
- **Why Promising**: ...
- **Requirements**: ...
- **Validation Plan**: ...
- **Evidence**: ...
- **Status**: feasible | approaching exhaustion | claimed territory
- **Related Entries**: ...
- **Retrieval Tags**: ...
- **Date Added**: ...
- **Last Updated**: ...

### [Direction 2 Name]
...

## Unsuccessful Directions

### [Direction A Name]
- **Summary**: ...
- **Failure Classification**: Fundamental
- **Evidence**: ...
- **Root Cause**: ...
- **Boundary Conditions**: ...
- **Countermeasures**: ...
- **Do-Not-Repeat Notes**: ...
- **Retrieval Tags**: ...
- **Date Added**: ...

### [Direction B Name]
...
```

### Field Definitions

#### Feasible Directions

| Field | Type | Description |
|-------|------|-------------|
| Direction Name | H3 heading | A short, descriptive name for the direction |
| Summary | String | One-sentence description of the research direction |
| Why Promising | String | Why this direction is promising — novelty/feasibility/relevance/clarity (from paper's IDE prompt) |
| Requirements | String | Key requirements and assumptions — data, compute, tools, environment |
| Validation Plan | String | 2-4 step minimal plan to validate the direction |
| Evidence | String | Which cycle(s) provided evidence, tournament rankings, key findings |
| Status | Enum | `feasible` (active), `approaching exhaustion` (diminishing returns), `claimed territory` (published work has covered it), `retry with fixes` (IVE implementation failure) |
| Related Entries | String | Cross-references to other M_I entries (both feasible and unsuccessful) |
| Retrieval Tags | String | Keywords for embedding-based retrieval in future cycles |
| Retry Count | Integer | Number of IVE implementation failure classifications. When ≥3, escalate to re-evaluation. **IVE-only**: present only for `retry with fixes` entries |
| Retry Guidance | String | What to try differently. **IVE-only**: present only for `retry with fixes` entries. If retry count reaches 3, escalate to re-evaluation |
| Countermeasures | String | Actionable items from IVE. **IVE-only**: present only for `retry with fixes` entries |
| Date Added | Date | When this entry was first created |
| Last Updated | Date | When this entry was last modified |

#### Unsuccessful Directions

| Field | Type | Description |
|-------|------|-------------|
| Direction Name | H3 heading | A short, descriptive name for the direction |
| Summary | String | One-sentence description of the research direction |
| Failure Classification | Enum | Always `Fundamental` (implementation failures stay in Feasible) |
| Evidence | String | Specific results from experiments that support this classification |
| Diagnostic Answers | String | Summary of Q1-Q5 IVE diagnostic responses |
| Root Cause | String | Best understanding of WHY the direction doesn't work |
| Boundary Conditions | String | Conditions under which this might become feasible (optional) |
| Countermeasures | String | 3-6 actionable items to prevent same failure pattern (from paper's IVE prompt) |
| Do-Not-Repeat Notes | String | Explicit guidance on what future cycles should avoid |
| Retrieval Tags | String | Keywords for embedding-based retrieval in future cycles |
| Date Added | Date | When this entry was first created |

### Example M_I Entry (Feasible)

```markdown
### Modality-Aware Model Compression

- **Summary**: Leveraging different compression tolerances across modalities
  (vision, language, audio) to achieve better compression-quality trade-offs
  in multi-modal architectures.
- **Why Promising**: High novelty (no prior work on per-modality compression
  ratios); feasible (builds on existing pruning tools); relevant (multi-modal
  models are growing fastest); clear (well-defined evaluation protocol).
- **Requirements**: Pre-trained VL model (e.g., BLIP-2), pruning library
  (torch-pruning), 1× A100 GPU, MS-COCO + VQA datasets.
- **Validation Plan**: 1) Apply uniform pruning as control. 2) Apply
  modality-specific ratios (2:1 vision:language). 3) Compare accuracy-latency
  trade-offs. 4) Verify on a second VL architecture.
- **Evidence**: Cycle 3 tournament — ranked #2 (Elo 1548); Cycle 5 — produced
  successful experiment pipeline. Top-performing variant: asymmetric pruning
  ratios for VL models.
- **Status**: feasible
- **Related Entries**: See "Efficient Multi-Modal Inference" (feasible),
  "Uniform Compression for Multi-Modal Models" (unsuccessful)
- **Retrieval Tags**: compression, pruning, multi-modal, modality-aware, VL models
- **Date Added**: 2026-01-15
- **Last Updated**: 2026-02-28
```

### Example M_I Entry (Retry with Fixes — IVE Implementation Failure)

```markdown
### Contrastive Pruning for LLM Compression

- **Summary**: Using contrastive objectives to guide structured pruning
  decisions in large language models.
- **Why Promising**: Novel combination of contrastive learning and pruning;
  related paper showed contrastive objectives help in vision pruning.
- **Requirements**: Pre-trained LLM (Llama-7B), pruning library, 2× A100 GPU.
- **Validation Plan**: 1) Fix gradient scaling issue found in Cycle 4.
  2) Adopt training schedule from related contrastive pruning paper.
  3) Test on GPT-2 first (confirmed working), then scale to Llama-7B.
- **Evidence**: Cycle 4, Stage 3 — 12 attempts, best was 3% below baseline.
  Attempt 7 showed 1% improvement on MMLU but regressed on GSM8K.
  Gradient scaling bug found in attempt 10.
- **Status**: retry with fixes
- **Related Entries**: See "Modality-Aware Model Compression" (feasible)
- **Retry Guidance**: Fix gradient scaling, try schedule from related paper,
  consider architecture-specific adaptations for decoder-only models.
- **Countermeasures**: 1) Verify gradient norms before full training.
  2) Test on small model first. 3) Use per-layer contrastive loss instead
  of global. 4) Monitor per-benchmark metrics, not just average.
- **Retry Count**: 1
- **Retrieval Tags**: contrastive, pruning, LLM, compression, structured pruning
- **Date Added**: 2026-02-15
- **Last Updated**: 2026-02-28
```

### Example M_I Entry (Unsuccessful)

```markdown
### Autoregressive Real-Time Video Generation

- **Summary**: Using autoregressive token-by-token generation for video
  prediction under real-time latency constraints.
- **Failure Classification**: Fundamental
- **Evidence**: Cycle 4, Stage 3 — 12 attempts, all exceeded latency target
  by >5x. Tested on multiple architectures and resolutions.
- **Diagnostic Answers**: Q1: No partial success. Q2: Fails even at 64x64.
  Q3: No published real-time autoregressive video work. Q4: All bottleneck
  on sequential decoding. Q5: No bugs found.
- **Root Cause**: Sequential autoregressive decoding has O(n) latency in
  sequence length, incompatible with real-time constraints for video outputs.
- **Boundary Conditions**: May become feasible if hardware achieves >10x
  current throughput or if resolution/framerate requirements are relaxed.
- **Countermeasures**: 1) Use non-autoregressive or parallel decoding for
  real-time video. 2) Pre-generate and cache token blocks offline. 3) Limit
  autoregressive scope to keyframes only. 4) Profile latency per-token before
  scaling to full resolution.
- **Do-Not-Repeat Notes**: Do not attempt autoregressive generation under
  real-time constraints without first verifying per-token latency at target
  resolution. The O(n) bottleneck is inherent, not implementation-specific.
- **Retrieval Tags**: autoregressive, video generation, real-time, latency,
  sequential decoding
- **Date Added**: 2026-02-10
```

## Experimentation Memory (M_E) Schema

The paper defines M_E as storing "reusable data processing and model training strategies" — two core categories. We extend with Architecture and Debugging sections for comprehensive coverage.

### File Structure

```markdown
# Experimentation Memory

Last Updated: [YYYY-MM-DD]
Total Cycles: [N]

## Data Processing Strategies          ← Paper core category

### [Strategy 1 Name]
- **Category**: Data Processing
- **Context**: ...
- **Strategy**: ...
- **Evidence**: ...
- **Generality**: ...
- **Related Entries**: ...
- **Date Added**: ...
- **Last Updated**: ...

## Model Training Strategies           ← Paper core category

### [Strategy 2 Name]
...

## Architecture Strategies             ← Practical extension

### [Strategy 3 Name]
...

## Debugging Strategies                ← Practical extension

### [Strategy 4 Name]
...

## Archive

*Pruned entries are moved here to preserve historical record.*
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| Strategy Name | H3 heading | Short, descriptive name for the strategy |
| Category | Enum | `Data Processing`, `Model Training`, `Debugging`, or `Architecture` |
| Context | String | When to apply this strategy — domain, scale, conditions |
| Strategy | String | What to do — specific, actionable guidance |
| Evidence | String | Cycle, stage, attempt — what happened that supports this |
| Generality | Enum | `Broadly applicable`, `Domain-specific`, `Highly specific` |
| Confidence | String | `Single observation`, `Confirmed (N cycles)`, `Contradicted` |
| Related Entries | String | Cross-references to other M_E entries |
| Date Added | Date | When first created |
| Last Updated | Date | When last modified |

### Example M_E Entry

```markdown
### Cosine Annealing with Warm Restarts for Small-Dataset Fine-Tuning

- **Category**: Model Training
- **Context**: Transformer fine-tuning on datasets with <50K training samples.
  Particularly effective when the pre-trained model is large relative to the
  dataset.
- **Strategy**: Use cosine annealing with warm restarts (T_0=10, T_mult=2).
  Start with LR in [1e-4, 5e-4]. This consistently outperforms linear decay
  and step decay schedules.
- **Evidence**: Cycle 3, Stage 2, Attempts 5-7 — improved final accuracy by
  2.1% vs linear decay; Cycle 5, Stage 2 — confirmed on different architecture.
- **Generality**: Broadly applicable
- **Confidence**: Confirmed (2 cycles)
- **Related Entries**: See "Learning Rate Warmup" (complements this strategy)
- **Date Added**: 2026-01-20
- **Last Updated**: 2026-02-28
```

## Evolution Report Schema

### File Structure

Reports are saved to `/memory/evolution-reports/cycle_N_type.md` where `type` is `ide`, `ive`, or `ese`.

```markdown
# Evolution Report: Cycle [N] — [IDE|IVE|ESE]

**Date**: [YYYY-MM-DD]
**Trigger**: [What triggered this evolution — skill completion or failure]
**Source Artifacts**: [Which files were read as input]

## Changes Made

### Added
- [Entry 1]: [Brief description of what was added and to which memory store]

### Updated
- [Entry 2]: [What changed and why]

### Removed/Archived
- [Entry 3]: [Why it was removed — if any]

## Reasoning

[2-3 paragraphs explaining the decisions made. Why were these directions/strategies
extracted? Why at this level of abstraction? Any judgment calls made.]

## Impact on Future Cycles

- **For research-ideation**: [How will M_I changes affect future ideation?]
- **For experiment-pipeline**: [How will M_E changes affect future experiments?]
- **Confidence level**: [How confident are you in these updates?]
```

## Memory Lifecycle

### Create

Memory files are created on first use:
- M_I: Created when the first IDE or IVE trigger occurs
- M_E: Created when the first ESE trigger occurs
- If the file doesn't exist, initialize from the templates in `assets/`

### Grow

Memory grows through evolution triggers:
- IDE adds feasible directions to M_I
- IVE adds unsuccessful directions or retry guidance to M_I
- ESE adds strategies to M_E

### Prune

Periodic maintenance (recommended every 5-10 cycles):
- Remove entries older than 10 cycles without being referenced
- Archive superseded strategies (move to an archive section, don't delete)
- Update confidence levels based on accumulated evidence
- Resolve contradictions (if entry A says "do X" and entry B says "don't do X", investigate and resolve)

### Archive

Entries that are pruned are not deleted — they're moved to an `## Archive` section at the bottom of the memory file. This preserves the historical record while keeping the active sections clean.

## Version Tracking

Each memory file header includes `Last Updated` and `Total Cycles`. When modifying entries:
- Update `Last Updated` on the entry AND the file header
- Increment `Total Cycles` only when a new evolution trigger occurs (not for maintenance)
- The evolution report for each cycle serves as the detailed changelog
