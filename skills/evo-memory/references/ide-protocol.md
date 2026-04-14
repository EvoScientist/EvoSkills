# IDE Protocol — Idea Direction Evolution

Step-by-step process for extracting and storing promising research directions after completing an `research-ideation`. IDE is the primary mechanism for building Ideation Memory (M_I) over time.

## When to Trigger

IDE runs after `research-ideation` Step 5 (ELO Tournament) is complete and Step 6 has prepared `/direction-summary.md`. The input is the direction summary containing the top-3 ranked ideas.

## Step-by-Step Process

### Step 1: Read Current M_I

Read `/memory/ideation-memory.md` to understand what's already stored:
- Which directions are currently listed as feasible?
- Which are listed as unsuccessful?
- Are any of the top-3 ideas related to existing entries?

### Step 2: Run the Paper's IDE Prompt

The paper's IDE prompt (in [paper-prompts.md](paper-prompts.md)) is the primary extraction mechanism. Before manually abstracting directions, reason through it step by step:

1. Read the IDE prompt from `paper-prompts.md`
2. Fill in the variables:
   - `{user_goal}` ← the original research direction from the user (the seed direction used before Step 3 ideation and Step 4 refinement). Note: do NOT use `/research-proposal.md` here — that file is created in Step 7, which runs AFTER IDE is triggered in Step 6.
   - `{top_ranked_ideas}` ← the content of `/direction-summary.md` (top-3 ideas with ratings and feedback from the tournament)
3. Reason through the filled prompt step by step
4. The output (DIRECTION SUMMARY with Title, Core idea, Why promising, Requirements, Validation plan) becomes the input to Step 3 below

This ensures the paper's extraction logic is applied before our additional abstraction and overlap-checking steps.

### Step 3: Abstract the Directions

For each of the top-3 tournament results, extract the research direction at a reusable level of abstraction.

**The abstraction ladder**:

| Level | Example | Reusability |
|-------|---------|-------------|
| Specific idea | "4-bit quantization of attention weights in Llama-2 using GPTQ with group size 128" | Very low — tied to one model and method |
| Technique-domain pair | "Post-training quantization for decoder-only LLMs" | Low — tied to one technique |
| **Direction** (target level) | "Precision reduction techniques for large language model inference" | **Good — spawns many future ideas** |
| Field | "Efficient AI" | Too broad — not actionable |

**The right level of abstraction** preserves the core insight while allowing variation in implementation. A future cycle should be able to read the direction and generate NEW ideas from it.

### Step 4: Check for Overlaps

Compare each abstracted direction against existing M_I entries:

- **Exact match**: The direction is already stored. Update the evidence and date, but don't duplicate.
- **Partial overlap**: The new direction is a sub-direction or super-direction of an existing entry. Consider merging (if closely related) or adding as a separate entry (if the angle is meaningfully different).
- **No overlap**: New direction. Append to the feasible directions list.

### Step 5: Update Exhaustion Status

Check if any previously "feasible" direction should be updated:
- Has this direction been explored in 3+ tournament cycles without producing a successful experiment? → Consider marking as "approaching exhaustion" (not yet unsuccessful, but diminishing returns).
- Has new published work claimed the remaining opportunities in this direction? → Mark as "claimed territory" with reference.

### Step 6: Write M_I Entry

For each new or updated direction, write an M_I entry. The paper's IDE prompt (see [paper-prompts.md](paper-prompts.md)) outputs: Title, Core idea, Why promising, Requirements/assumptions, Minimal validation plan. We extend this into a persistent entry format:

```markdown
### [Direction Name]

- **Summary**: [One-sentence description of the direction — the "core idea" from IDE output]
- **Why Promising**: [Why this is promising for the user goal — novelty/feasibility/relevance/clarity]
- **Requirements**: [Key requirements and assumptions — data, compute, tools, environment]
- **Validation Plan**: [2-4 step minimal plan to validate the direction]
- **Evidence**: [Which tournament cycle(s), ranking, key findings]
- **Status**: feasible | approaching exhaustion | claimed territory
- **Related Entries**: [Links to related directions in M_I]
- **Retrieval Tags**: [Keywords for embedding-based retrieval in future cycles]
- **Date Added**: [YYYY-MM-DD]
- **Last Updated**: [YYYY-MM-DD]
```

### Step 7: Write Evolution Report

Generate a report at `/memory/evolution-reports/cycle_N_ide.md`:
- What directions were added or updated
- Why each change was made (evidence from tournament)
- Expected impact on future `research-ideation` cycles

## Abstraction Examples

### Example 1: From Tournament Winner to Direction

**Tournament winner**: "Cross-modal attention pruning for vision-language models that preserves text-guided image understanding"

**Abstraction process**:
1. Core insight: Different modalities have different pruning sensitivities
2. Generalizable principle: Cross-modal dependencies create structured importance patterns
3. **Direction**: "Modality-aware model compression for multi-modal architectures"

This direction can spawn future ideas: modality-aware distillation, modality-specific quantization, adaptive inference that routes by modality, etc.

### Example 2: Updating an Existing Entry

**Existing M_I entry**: "Contrastive learning for structured data representations" (feasible, from cycle 2)

**New tournament result**: "Graph contrastive learning with domain-specific augmentations" (ranked #2)

**Update decision**: This is a sub-direction of the existing entry. Update the evidence to include cycle 5 results, but don't create a separate entry. Note that domain-specific augmentation is a promising variant.

### Example 3: Approaching Exhaustion

**Existing M_I entry**: "Prompt engineering for few-shot learning" (feasible, cycles 1-4)

**Evidence**: Multiple tournament cycles have generated ideas in this direction, but recent top-performing ideas have shifted toward parameter-efficient fine-tuning. Published work (2025-2026) has covered most promising prompt engineering variations.

**Update**: Change status to "approaching exhaustion." Note: "Most accessible prompt engineering approaches have been published. Remaining opportunities may require combination with fine-tuning (see separate direction)."

## Common Mistakes

### Over-Abstracting

**Mistake**: "Machine learning research" — too broad to be useful.
**Fix**: Keep enough specificity that a future researcher can generate concrete ideas from the direction. The direction should answer "what kind of ideas should I think about?" not just "what field am I in?"

### Under-Abstracting

**Mistake**: Storing the exact tournament idea as a direction.
**Fix**: Strip implementation details. The direction should be about the APPROACH, not the specific method.

### Ignoring Context

**Mistake**: Storing "Reinforcement learning for X" without noting that the tournament evidence was in a specific setting.
**Fix**: Include the context where this direction showed promise. Future cycles can judge whether the context applies to their problem.
