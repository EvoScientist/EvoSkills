# IVE Protocol — Idea Validation Evolution

Step-by-step process for classifying experiment failures and updating Ideation Memory (M_I) accordingly. IVE is the most critical evolution mechanism because it prevents future cycles from repeating dead-end directions.

## When to Trigger

The paper defines two IVE trigger conditions:

1. **Rule-based trigger**: The engineer cannot find any executable code within the pre-defined budget at any stage. The code simply doesn't run despite all attempts. This is an automatic (rule-based) failure detection.

2. **LLM-based trigger**: Experiments complete and produce an execution report W, but the EMA's LLM-based analysis determines the proposal failed — typically because the proposed method performs worse than the baseline.

**Practical guidance**: The most common IVE trigger is when Stage 3 (Proposed Method) exhausts its budget without outperforming the baseline. However, IVE can also trigger when earlier stages fail entirely (no executable code), indicating the direction may be fundamentally too difficult to implement.

## Step 1: Run the Paper's IVE Prompt (Primary Classification)

The paper's IVE prompt (see [paper-prompts.md](paper-prompts.md)) is the primary failure classification mechanism. Run it first:

1. Read the IVE prompt from `paper-prompts.md`
2. Fill in the variables:
   - `{research_proposal}` ← the content of `/research-proposal.md`
   - `{execution_report}` ← Stage 3 trajectory logs and metrics (or the stage where failure occurred)
3. Reason through the filled prompt step by step
4. The prompt performs a two-step classification:
   - **FAILURE CASE CHECK (Rule-based)**: If the execution report indicates the engineer could not find any executable code within the pre-defined budget → **FAILED (NoExecutableWithinBudget)**
   - **PERFORMANCE VALIDATION (Result-based)**: If experiments completed but the proposed method performs worse than baselines → **FAILED (WorseThanBaseline)**. Otherwise → **NOT_FAILED (ValidatedOrInconclusive)**
5. The prompt also outputs: failure signals, countermeasures, do-not-repeat notes, and retrieval tags

### Decision Tree After Paper Classification

- **FAILED (NoExecutableWithinBudget)** → Implementation failure (retryable). The code didn't run — this is almost always an implementation issue, not a direction issue. Record as "retry with fixes" in M_I.
- **FAILED (WorseThanBaseline)** → Run Step 2 (Extended Diagnostic) below to distinguish implementation vs fundamental failure. The paper's binary classification doesn't differentiate here.
- **NOT_FAILED (ValidatedOrInconclusive)** → No IVE memory update needed. The direction is validated or inconclusive.

## Step 2: Extended Diagnostic (When Paper Classification is Ambiguous)

Use this 5-question framework when the paper's IVE prompt classifies the result as **FAILED (WorseThanBaseline)**. The binary classification tells you IT failed, but not WHY — was it a bad implementation of a good idea, or a good implementation of a bad idea?

## The Core Decision: Implementation vs Fundamental Failure

This is the most consequential classification in the evolution system. Getting it wrong has asymmetric costs:

| Misclassification | Cost |
|-------------------|------|
| Calling a good direction "fundamental failure" | **High**: Permanently discards a viable research direction. All future cycles will avoid it, potentially missing high-impact work. |
| Calling a bad direction "implementation failure" | **Low**: Wastes one future retry cycle. But the retry will fail again, and IVE will trigger again with more evidence. |

**When in doubt, classify as implementation failure.** The cost of one wasted retry is much lower than permanently discarding a promising direction.

## Five Diagnostic Questions (Step 2 Detail)

Answer these questions using the code trajectory logs from Stage 3:

### Q1: Did any variant show partial success?

Look at all 12 attempts. Did ANY attempt show improvement on ANY metric, even if not enough to meet the gate?

- **Yes → Implementation failure signal**: The direction has potential. Partial success means the core hypothesis may be correct but the implementation needs refinement.
- **No → Fundamental failure signal**: Zero improvement across 12 varied attempts suggests the hypothesis itself may be wrong.

### Q2: Does the hypothesis hold for simpler problems?

If you simplified the problem (smaller data, easier setting), did the method work?

- **Yes → Implementation failure signal**: The method works in principle. Scaling issues are usually fixable.
- **No → Strong fundamental failure signal**: If the method can't work even on a simple version of the problem, the core approach is likely flawed.

### Q3: Have related approaches succeeded in published work?

Check the literature: have similar methods (same core principle, different implementation) succeeded on similar problems?

- **Yes → Implementation failure signal**: Others made it work. Your implementation is missing something.
- **No → Fundamental failure signal**: If nobody has made this class of approach work, the challenge may be fundamental.

### Q4: Were failure patterns consistent across implementations?

Did different implementations (different architectures, different training strategies) all fail in the SAME way?

- **Yes → Fundamental failure signal**: Consistent failure across varied implementations points to a problem with the approach, not the implementation.
- **No → Implementation failure signal**: Different failure modes suggest the approach is sensitive to implementation details — with the right details, it might work.

### Q5: Can you identify specific bugs or configuration issues?

Reading the trajectory logs, do you see specific technical problems that could explain the failure?

- **Yes → Strong implementation failure signal**: Identified bugs mean the approach wasn't given a fair chance.
- **No → Fundamental failure signal**: If 12 systematic attempts with no identifiable bugs still fail, the issue is likely conceptual.

## Classification Rule

Count the signals from Q1-Q5:

| Implementation Failure Signals | Fundamental Failure Signals | Classification |
|-------------------------------|----------------------------|----------------|
| 3-5 | 0-2 | **Implementation failure** (retryable) |
| 0-2 | 3-5 | **Fundamental failure** (not retryable) |

If the count is ambiguous (e.g., a question is unanswerable from available evidence), exclude it and adjust the threshold proportionally. **When in doubt, default to implementation failure** — the cost of one wasted retry is much lower than permanently discarding a viable direction.

## Writing the M_I Entry

### For Implementation Failures

Add or update an entry in the M_I feasible directions section:

```markdown
### [Direction Name]

- **Summary**: [Direction description]
- **Why Promising**: [Retain from original entry, or from tournament evidence]
- **Requirements**: [Retain from original entry, or note what was needed]
- **Validation Plan**: [Updated plan based on what was learned from the failure]
- **Evidence**: [Original tournament context + failed attempt: Cycle [N], Stage 3, specific results and metrics]
- **Status**: retry with fixes
- **Related Entries**: [Links to related directions in M_I]
- **Retry Guidance**: [What to try differently next time — from IVE diagnostic]
- **Countermeasures**: [3-6 actionable items to prevent same failure — from paper's IVE prompt]
- **Retry Count**: [Number of failed implementation attempts across cycles. When ≥3, escalate to re-evaluation]
- **Retrieval Tags**: [Keywords for embedding-based retrieval in future cycles]
- **Date Added**: [Original creation date, or today if new entry]
- **Last Updated**: [YYYY-MM-DD]
```

**Retry limit**: If a direction has been classified as "implementation failure" 3 times across different cycles, escalate to a careful re-evaluation. Three separate implementation failures may indicate the direction is harder than it appears — consider reclassifying.

### For Fundamental Failures

Add an entry to the M_I unsuccessful directions section:

```markdown
### [Direction Name]

- **Summary**: [Direction description]
- **Failure Classification**: Fundamental
- **Evidence**: [Specific results from the 12 attempts that support this classification]
- **Diagnostic Answers**: [Summary of Q1-Q5 responses]
- **Root Cause**: [Best understanding of WHY the direction doesn't work]
- **Boundary Conditions**: [Under what conditions might this direction actually work? (Optional but valuable)]
- **Do-Not-Repeat Notes**: [What future cycles should avoid — from paper's IVE prompt]
- **Countermeasures**: [3-6 actionable items to prevent same failure pattern]
- **Retrieval Tags**: [Keywords for embedding-based retrieval in future cycles]
- **Date Added**: [YYYY-MM-DD]
```

**Boundary conditions**: Even fundamental failures have limits. "Autoregressive generation is too slow for real-time video" is a fundamental failure — but with faster hardware or shorter sequences, it might become feasible. Recording boundary conditions makes the entry more useful for future cycles that may operate under different constraints.

## Worked Examples

### Example 1: Implementation Failure

**Situation**: Tried "contrastive pruning" for LLM compression. 12 attempts, best result was 3% below baseline.

**Diagnostic answers**:
- Q1: Yes — attempt 7 showed 1% improvement on MMLU but regressed on GSM8K
- Q2: Yes — works on GPT-2 small, fails on Llama-7B
- Q3: Yes — recent paper showed contrastive objectives help in pruning (different architecture)
- Q4: No — different training schedules produced different failure modes
- Q5: Yes — found gradient scaling issue in attempt 10

**Classification**: Implementation failure (4 implementation signals, 1 fundamental signal)

**Entry**: Mark direction as "retry with fixes." Note: fix gradient scaling, try the training schedule from the related paper, consider architecture-specific adaptations.

### Example 2: Fundamental Failure

**Situation**: Tried "autoregressive generation for real-time video prediction." 12 attempts, all significantly too slow.

**Diagnostic answers**:
- Q1: No — all attempts exceeded latency target by >5x
- Q2: No — even on 64x64 resolution with 4 frames, too slow for real-time
- Q3: No — no published work achieves real-time autoregressive video generation
- Q4: Yes — all attempts bottleneck on sequential token generation
- Q5: No — implementation is correct; the bottleneck is inherent to autoregressive decoding

**Classification**: Fundamental failure (5 fundamental signals, 0 implementation signals)

**Entry**: Add to unsuccessful directions. Root cause: "Sequential autoregressive decoding has O(n) latency in sequence length, which is fundamentally incompatible with real-time constraints for video-resolution outputs." Boundary condition: "May become feasible if hardware achieves >10x current throughput or if the video resolution/framerate requirements are relaxed significantly."

## Post-IVE Actions

After updating M_I:
1. Write an evolution report at `/memory/evolution-reports/cycle_N_ive.md`
2. If classified as implementation failure: The direction stays in the feasible list. The next `research-ideation` cycle may regenerate ideas in this direction, informed by the retry guidance.
3. If classified as fundamental failure: The direction is added to the unsuccessful list. Future `research-ideation` cycles will prune tree branches that match this direction.
