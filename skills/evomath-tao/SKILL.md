---
name: evomath-tao
description: "Use this skill whenever the user submits a non-trivial mathematical claim that needs a rigorous proof or audit. Trigger on IMO/Putnam/USAMO/Olympiad-style problems, ML/AI theoretical statements, research conjectures, suspected-false claims, multi-step proofs the user already failed on, proof drafts with possible hidden assumptions, or any request containing 'prove rigorously', 'verify this', 'is this true', 'find the gap', 'audit my proof', 'find a counterexample', or 'use EvoMath' that targets a mathematical claim. Activate also when the problem requires more than three reasoning steps. Do NOT use for single-step calculations, definition lookups, textbook exercises with a known recipe, code analysis tasks, literature survey questions, pure symbolic manipulation, or non-mathematical applications of those trigger phrases (e.g., 'is it true that GPT-4 can solve math?', 'verify this LaTeX syntax'); hand those back instead."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, math, proof, olympiad, research]
---

# EvoMath (Tao-style)

EvoMath is a lightweight proof workflow for contest-style mathematical
reasoning. Its job is to produce a rigorous proof, a verified counterexample, a
useful partial result, or a clear handoff. Keep the process small; do not run a
heavy audit pipeline by default.

## Methodology Anchor — Terence Tao's Research-Math Practice

This skill operationalizes the way Terence Tao approaches research mathematics:

1. **Compute small cases first** (Kepler before Newton) — build intuition from data before reaching for theory.
2. **Try the standard toolbox broadly before going deep** — most hard problems crack to a standard technique; the few that don't only reveal which after several have failed.
3. **Hold rigor and intuition together** (post-rigorous mathematics) — trust intuition, but verify every step. "It feels right" is a hypothesis, not a proof.
4. **Atomize when stuck** — decompose into independently checkable sub-claims. A clean map of proved / conjectured / open beats a polished but shaky narrative.
5. **Stay honest about what isn't proved** — distinguish PROVED / VERIFIED_NUMERICALLY / CONJECTURED / HANDED_OFF. When blocked, name the precise gap.
6. **Distill each result into reusable insight** — after every problem, extract what worked into a strategy and what failed into a named pattern. Mathematical maturity is accumulated meta-insight.

Every phase below is a concrete operationalization of one or more of these principles.

## Operating Rules

- Use Markdown notes for handoff between steps. Do not require JSON/YAML unless
  a script explicitly asks for it.
- Keep only compact state: plan, verified claims, failed attempts, final audit.
  Do not pass long failed derivations into later prompts.
- Prefer a few independent proof attempts over one long derivation.
- **Numerical verification is NOT a proof step** (math-olympiad rule). Checking
  a claim on n=1..100 and finding no counterexample does NOT make it PROVED;
  the strongest label such evidence can earn is VERIFIED_NUMERICALLY.
- Exact arithmetic can refute; approximate numerics only suggest.
- A proof is final only after an adversarial check of the clean proof.
- **Calibrated abstention over bluffing**: when verification fails repeatedly,
  admit it. Return partial results and mark unfixed gaps explicitly (math-
  olympiad rule). Final status HANDED_OFF with a structured wall report is
  always preferable to PROVED with hand-waved gaps.
- Every final answer must include a visible `final-status: ...` line.
- Use TodoWrite to drive the workflow. Each step is one todo; you cannot mark a
  todo completed unless the corresponding `.md` file passes its validator.

If filesystem access is available, create a Markdown workspace with (script paths are relative to this skill's directory):

```bash
python scripts/evomath_workspace.py init --dir .evomath/current
```

If filesystem access is not available, keep the same Markdown sections inline in
the conversation. In that case run the validators by mentally checking the same
required fields the script checks — the discipline is the same.

## Fast Exit

Do not use EvoMath for single calculations, definition lookups, symbolic
manipulation, or answer-only requests with no proof obligation. Give the direct
answer instead. No TodoWrite list is needed for a Fast Exit.

If the statement has a blocking ambiguity that changes truth value, ask one
specific clarification question before solving.

## Execution Protocol (TodoWrite + Validation)

For any problem that passes the Fast Exit Gate, follow this protocol.

### 1. Create the 5-step todo list

Before doing any solving work, call TodoWrite with these five items in this
order. Each item names its primary reference file:

1. **Plan Briefly** — read `references/intake-checklist.md` for type
   classification, ambiguity handling, goal types.
2. **Try Candidates** — read `references/angles-by-type.md` for technique ideas
   if you are out of angles for this problem type.
3. **Assemble** — read `references/output-formats.md` if you need formatting
   conventions or LaTeX templates.
4. **Audit** — read `references/grading-taxonomy.md` for issue classes and
   severity rules. Read `references/phase-4-audit.md` only if the user requests
   strict multi-reviewer audit.
5. **Reflect** — read `references/claim-memory.md` only when deep reflection is
   triggered (see "Deep Reflection Triggers" below).

### 2. Per-step discipline

For each step in order:

1. Mark the todo `in_progress` before reading the reference or writing output.
2. Read the referenced file(s) if and only if you need them for this step.
3. Produce the corresponding `.md` output (plan.md, candidates.md, audit.md,
   final.md sections, etc.).
4. Run the validator before marking the todo completed:

   ```bash
   python scripts/evomath_workspace.py validate-phase <N> --dir .evomath/current
   ```

5. If validation FAILS, the todo stays `in_progress`. Revise the `.md` file
   based on the printed failure messages and re-run the validator. Do not mark
   completed until the validator exits 0.

### 3. PROVED gate

If your final-status is `PROVED`, you MUST additionally run:

```bash
python scripts/evomath_workspace.py validate-proved --dir .evomath/current
```

This verifies that the 10-item PROVED Self-Check Checklist (see
`references/output-formats.md`) is present in final.md with all boxes ticked.
If this fails, downgrade final-status to CONJECTURED or HANDED_OFF and revise
the answer.

### 4. Deep Reflection Triggers

Step 5 (Reflect) has two modes:

- **Light reflection** (default): three lines — successful pattern, failed
  pattern to avoid, whether memory was written.
- **Deep reflection** (triggered when any of the following hold):
  - Step 2 required 3+ revision rounds for any candidate
  - Step 4 identified a fatal flaw before the final repair
  - A new winning technique appeared that is not yet in any L2 strategy entry
  - The user explicitly asks for self-evolution or cross-problem learning
  - final-status is HANDED_OFF with a recurring failure-mode

  In deep reflection mode, run the full ESE/IVE protocols described in
  `references/claim-memory.md` and update L2/L3 memory in
  `.evomath/session-memory.md`.

### 5. Fallback when filesystem is unavailable

If you cannot run scripts, keep the same TodoWrite discipline:
- Still create the 5-item list and march through it.
- Still keep the same `.md` sections inline in the conversation.
- Substitute mental validation for the script call — check the same required
  fields the validator would check.

## Workflow

### 1. Plan Briefly

Write a short Markdown plan:

- Problem type: algebra, geometry, number theory, combinatorics, analysis, or
  other.
- Goal: prove, refute, find example, or audit proof.
- Strategy: one sentence.
- Subgoals: at most five bullets.

For "determine all" problems, include both:

- existence/construction
- impossibility/exclusion

For a simple problem, one root subgoal is enough.

### 2. Try Candidates

**Mode dispatch** (decide before generating):

- If Phase 0 `goal = find-numeric-answer` (AIME-style: answer is a single
  number, no proof required) → **AIME mode**: generate 5–7 short candidate
  answers using varied approaches (small-case enumeration, modular invariants,
  algebraic manipulation, generating functions, brute-force code). Take
  majority vote across candidates. Verify the top two by substitution into the
  original problem. Skip the rest of the proof workflow; output the numeric
  answer with `final-status: PROVED` only when both top candidates agree AND
  substitution checks pass.
- Otherwise → **Proof mode**: continue below.

**Proof mode — per-candidate 5-round internal loop**:

For each active subgoal, try up to four genuinely different candidate routes.
Each candidate is itself the product of a 5-round internal mini-process — not
a one-shot generation:

1. **Solve** — produce a proof attempt using reasoning only. **No tool use
   during this round** (no calculator, sympy, Lean, web). Pure pencil-and-paper.
2. **Self-improve** — refine the attempt for clarity, fix obvious gaps.
3. **Self-verify** — walk through line by line, looking for: shielding words
   ("obviously"/"clearly"), unjustified swaps, missing hypotheses, off-by-one
   cases, hidden assumptions.
4. **Correct** — fix issues found in step 3.
5. Repeat 1–4 up to **5 times** per candidate, or until the candidate self-
   reports as `is_sound`.

Each candidate's internal-rounds count is recorded so Phase 4 can see how much
self-revision was needed. A candidate that needs 5 rounds is more likely to be
borderline than one that's sound in 1.

Record candidates in this Markdown table:

| Candidate | Idea | Internal rounds | Verdict | Issue or reason |
|---|---|---|---|---|
| C1 |  | 1–5 | sound / repair / fail |  |

Judging a candidate:

- `sound`: enough to use as a verified claim.
- `repair`: promising but missing a local step; revise at most twice **outside**
  the 5-round internal loop (so total max revisions = 5 internal + 2 external).
- `fail`: wrong, circular, too weak, or repeats a known dead end.

**Computation discipline (math-olympiad VERBATIM rule)**: during the Solve
round, no tool calls. Computation is allowed in Phase 1 (Empirical) and in
Phase 5 Deep Mode, NEVER during Phase 2 Solve. This protects against
ritualized "I called sympy so it must be right" reasoning.

When a candidate is sound, add it to **Proof Artifact / Verified Claims** with
a one-paragraph proof summary. When a route fails, add one line to **Negative
Attempts** so it is not repeated.

Use `references/angles-by-type.md` only when you are out of ideas for a problem
type. Do not load it by default.

### 3. Assemble

Turn the accepted claims into a clean proof or refutation.

Rules:

- State the original claim.
- Present the final argument only; omit failed attempts.
- Justify every non-trivial step by a verified claim, theorem, construction, or exact
  computation.
- If a required subgoal remains unsolved, stop pretending the proof is complete:
  output a partial result or handoff.

### 4. Audit

Audit only the clean proof, not the exploration notes.

Check:

- The proof proves the original statement, not a weaker restatement.
- All cases, boundary values, degeneracies, and quantifiers are handled.
- No claim is cited without proof or explicit acceptance in the Proof Artifact.
- Refutations use an exactly verified counterexample.

**Audit follows math-olympiad's 3-safeguard pattern** (see `references/phase-4-audit.md`):
1. Verifier context isolation (strip thinking traces before review).
2. Asymmetric voting (4 HOLDS to confirm; 2 HOLE FOUND to refute).
3. Pigeonhole exit (stop launching reviewers after threshold).

Apply the named-pattern screen (P4 / P5 / P6 / P18 / P40 / P41 in `grading-taxonomy.md`) plus the counterexample-first rule before any PROVED award.

For ordinary use, one careful local audit is enough. Use the heavier
`references/phase-4-audit.md` protocol only when the user asks for strict
multi-reviewer audit or when the result is high-risk.

### 5. Reflect

After the final answer, add a short reflection note. It should be compact:

- successful pattern, if any
- failed pattern to avoid
- whether memory was written

Per-problem memory resets at the next problem. Cross-problem memory is optional:
write only compact strategy/failure summaries to `.evomath/session-memory.json`
when file access is available. If not written, say `memory-persisted: false`.

## Status Labels

Use exactly one:

| Status | Meaning |
|---|---|
| `PROVED` | Complete proof of the original statement passed Safeguards 1–3 audit. The strongest label EvoMath awards. |
| `REFUTED` | Exact counterexample or contradiction proof found |
| `VERIFIED_NUMERICALLY` | Finite exact checks only; no general proof. Numerical evidence is NOT a proof — this label exists to record empirical support honestly. |
| `CONJECTURED` | Strong partial evidence or partial proof, but incomplete |
| `HANDED_OFF` | Stopped with a precise remaining gap or user question |

Exactly one of these five labels must appear in every final answer. See `references/confidence-rules.md` for award conditions and promotion rules.

## Final Answer Shape

Use Markdown, not a rigid schema:

```markdown
final-status: PROVED

## Result
<answer>

## Proof / Report
<clean proof, refutation, audit report, partial result, or handoff>

## Audit
- audits-run:
- critical-issues:
- remaining-gaps:

## Proof Artifact
- verified claims:
- negative attempts:

## Reflection
- memory-persisted:
- storage-location:
- proposed-memory-updates:
```

For proof-audit requests, lead with findings ordered by severity, then give the
verdict and suggested repair.

## Optional Helpers

- `scripts/evomath_workspace.py`:
  - `init`         creates the five Markdown state files.
  - `check`        verifies `final.md` has a valid `final-status:` line.
  - `validate-phase N`  validates the .md output for step N (1..5). Use this
    before marking the corresponding todo completed. Add `--strict` to also
    re-validate all prior steps.
  - `validate-proved`  when final-status is PROVED, verifies the 10-item
    Self-Check Checklist is fully ticked.
- `references/angles-by-type.md`: technique ideas by problem type.
- `references/grading-taxonomy.md`: detailed flaw taxonomy for audits.
- `references/phase-4-audit.md`: heavier independent-review protocol.
- `references/output-formats.md`: optional Markdown/LaTeX formatting details +
  the PROVED Self-Check Checklist template.
- `references/claim-memory.md`: three-layer memory architecture and ESE/IVE
  reflection protocols. Read only in deep-reflection mode.
- `references/model-tier.md`: per-tier parameter table (Haiku / Sonnet /
  Opus). Read once at the start of Phase 0 to set K, internal-rounds, audit
  passes, and abstain thresholds for the active model.
