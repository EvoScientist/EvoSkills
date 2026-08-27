---
name: paper-review
description: "Guides self-review of YOUR OWN academic paper before submission with adversarial stress-testing. Core method: three-pass protocol (adversarial deep read, then 5-aspect checklist — contribution sufficiency, writing clarity, results quality, testing completeness, method design — then mechanical consistency scans), experimental protocol audit (data flow, assumptions, leakage), counterintuitive protocol (reject-first simulation, delete unsupported claims, score trust, promote limitations, attack novelty), reverse-outlining, and figure/table quality checks. Use when: user wants to self-review or self-check their own paper draft before submission, stress-test their claims, prepare for reviewer criticism, or mentions 'self-review', 'check my draft', 'is my paper ready'. Do NOT use for writing a peer review of someone else's paper, and do NOT use after receiving actual reviews (use paper-rebuttal instead)."
allowed-tools: "read_file edit_file write_file think_tool"
metadata:
  author: EvoScientist
  version: '1.1.0'
  tags: [core, writing, academic-writing, peer-review]
---

# Paper Review

A systematic approach to self-reviewing academic papers before submission, run as **three passes**: an adversarial deep read, a checklist sweep (5 aspects, reverse-outlining, figure/table quality), and mechanical consistency scans plus an experimental protocol audit. Ends with rebuttal preparation.

## When to Use This Skill

- User wants to review or check a paper draft before submission
- User asks for feedback on paper quality or completeness
- User wants to prepare for potential reviewer criticism
- User mentions "review paper", "check my draft", "self-review"

> If the user has already received reviewer comments and needs to write a rebuttal, use the `paper-rebuttal` skill instead.

## Prerequisites

Before starting review, confirm the `paper-writing` handoff checklist is satisfied: all sections drafted, claims anchored to evidence, limitation section present, figures finalized, and no unresolved `\todo{}` markers. If any item is incomplete, finish writing before reviewing.

---

## How to Run the Review: Three Passes

Run the review as three separate passes, in this order, and merge findings only at the end. Do **not** start from the checklists: a checklist primes you to see only what it names, and the flaws that kill papers in review are often the ones no checklist question points at.

### Pass 1 — Adversarial deep read (checklists closed)

Read the paper end-to-end as a skeptical expert reviewer, *before* consulting any checklist in this skill. Chase cross-section threads as you read:

- Does the evidence actually support each claim at the place it is made?
- Does an assumption stated in the setup ever get revisited — or quietly violated — later?
- Do the numbers quoted in prose match the tables? Does the conclusion deliver what the abstract promised?
- Would this method survive outside the paper's exact setting?

Write down **every** suspicion with its location, including ones you cannot yet prove (see the confidence policy below). This pass is where hidden, cross-section flaws surface; no checklist replaces it.

### Pass 2 — Checklist sweep

Now work through the structured materials: the 5-aspect checklist, the counterintuitive protocol, reverse-outlining, and the figure/table and conclusion checks. This pass buys breadth and catches the known, frequent failure patterns.

### Pass 3 — Mechanical scans and protocol audit

Execute the **Experimental Protocol Audit** and the **Mechanical Consistency Scans** (both below) explicitly, using search/cross-referencing over the source files. These checks need no judgment and have a high hit rate — and "reading carefully" never triggers them on its own.

### Merge

Union the findings of all three passes and deduplicate. **Never drop a Pass-1 suspicion because no checklist item names it** — those are often the most valuable findings.

## Reporting Findings: Calibrated Suspicion

A review finding contains two kinds of statements, with different rules:

- **Factual assertions about the paper** — what a table contains, what a section says, whether something is present or absent. These must be verifiable: check the text before asserting, and anchor the finding to an exact location or short quote. Never state that the paper says something it does not — one fabricated criticism costs more credibility than ten valid ones buy.
- **Suspicions and judgments** — "these gains may be within seed noise", "this assumption looks unrealistic in deployment". These are allowed and *encouraged*, including at low confidence. Phrase them as what they are: state the suspicion, mark the confidence, and name what evidence would settle it ("no variance is reported; 3 seeds would settle this").

Do not suppress a suspicion because you cannot prove it. In self-review, a hidden flaw that survives to the real reviewers costs far more than a raised-and-then-cleared suspicion. Precision discipline applies to *facts*, not to *doubts*.

---

## The Perfectionist Approach

> Strive for perfection: review your own paper, consider every question a reviewer might ask, and address them one by one.

The best defense against negative reviews is a thorough self-review:
1. **Adversarial review**: Read your own paper as a critical reviewer would
2. **Seek advisor feedback**: Ask your advisor to review — the more feedback, the better
3. **Address everything**: For every potential weakness you find, either fix it or prepare a defense

## Counterintuitive Review Protocol

Run this protocol before final polishing:

1. **Reject-first simulation**: Force yourself to write a one-paragraph reject summary before writing any positive comments.
2. **Delete one unsupported strong claim**: If a strong claim lacks direct evidence, remove it instead of defending it.
3. **Score trust, not only score gains**: Papers with slightly lower gains but higher fairness and reproducibility often receive better review outcomes.
4. **Promote one explicit limitation**: Move one meaningful limitation from hidden notes into the paper; transparency can increase confidence.
5. **Attack your novelty claim**: Ask "Could a strong PhD derive this in one afternoon?" If yes, narrow and sharpen the novelty statement.

See [references/counterintuitive-review.md](references/counterintuitive-review.md)

---

## 5-Aspect Self-Review Checklist

### Aspect 1: Contribution Sufficiency

> The paper does not provide readers with new knowledge.

Ask these questions to evaluate whether the contribution is sufficient:

- [ ] **Are the failure cases common?** If the failure cases are frequent and obvious, reviewers may question whether the method is ready for publication.
- [ ] **Is the proposed technique well-explored?** If the technique is already widely studied, what new insight or improvement do we bring?
- [ ] **Is the improvement foreseeable / well-known?** If the improvement was predictable from combining known ideas, the novelty may be questioned.
- [ ] **Is the technique too straightforward?** A straightforward application of existing techniques may lack sufficient contribution.

**Red flag**: If "yes" to any of these, strengthen the contribution narrative or add more technical depth.

### Aspect 2: Writing Clarity

> Missing technical details, not reproducible; a method module lacks motivation.

- [ ] **Missing technical details?** Would a reader be able to reproduce the method from the paper alone?
- [ ] **Missing module motivation?** Does every module in the Method section explain *why* it exists, not just *what* it does?
- [ ] **Paragraph structure**: Does each paragraph have a clear topic? Does the first sentence state the point?
- [ ] **Flow**: Is the logical flow between paragraphs and sections smooth?
- [ ] **Terminology**: Are terms used consistently throughout?

**Red flag**: If reproducibility is in doubt, add implementation details or supplementary material.

### Aspect 3: Experimental Results Quality

> Only slightly better than previous methods; or better than previous methods but still not good enough.

- [ ] **Marginal improvement?** If the improvement over SOTA is very small, is it statistically significant?
- [ ] **Absolute quality insufficient?** Even if better than baselines, is the output quality good enough for the application?
- [ ] **Visual quality**: Do qualitative results look convincing? Are improvements visible?

**Red flag**: If improvements are marginal, emphasize other advantages (speed, generalizability, simplicity) or add more challenging test cases.

### Aspect 4: Experimental Testing Completeness

> Missing ablation studies; missing important baselines; missing important evaluation metrics; data too simple.

- [ ] **Missing ablation studies?** Is every core contribution ablated?
- [ ] **Missing important baselines?** Are recent SOTA methods included?
- [ ] **Missing evaluation metrics?** Are all standard metrics for this task reported?
- [ ] **Datasets too simple?** Do the benchmarks truly test the method's capabilities?
- [ ] **No failure case analysis?** Honest failure analysis increases credibility.

**Red flag**: Missing ablations or baselines is one of the most common reasons for rejection.

### Aspect 5: Method Design Issues

> Experimental setting is impractical; method has technical flaws; method is not robust; new method's costs outweigh its benefits.

- [ ] **Impractical experimental setting?** Are assumptions realistic for the intended use case?
- [ ] **Technical flaws?** Does the method have theoretical or conceptual weaknesses?
- [ ] **Not robust?** Does the method require per-scene hyperparameter tuning?
- [ ] **Benefit < Limitation?** Does the new module introduce limitations that outweigh its benefits?

**Red flag**: If the method requires significant tuning per scenario, add robustness experiments or acknowledge and address the limitation.

---

## Experimental Protocol Audit

The most damaging experimental flaws hide in single sentences of the setup — stated once, never revisited. Audit the experimental section line by line as a hostile auditor, not a reader:

1. **Reconstruct the data flow.** From the text alone, write out: what was trained on what, tuned on what, evaluated on what. Any overlap between test data and training/tuning data — including a phrase like "hyperparameters tuned on the test split" buried in the setup — is a major finding. If split hygiene cannot be reconstructed from the text at all, that is itself a finding.
2. **List every assumption.** Search the method and setup for "we assume", "assuming", "provided that", "given access to". For each: is it realistic at deployment time, and is its impact discussed anywhere downstream? A strong assumption stated once and never mentioned again is a major finding.
3. **Check information availability.** Does the method consume anything at inference time that would not exist in practice — labels, oracle signals, future information, test-distribution statistics?
4. **Check the comparison protocol.** Same data, same compute budget, same tuning effort for all baselines? Are baseline numbers reproduced under this paper's setup, or copied from papers with different setups?

---

## Critical Reminder: Claims Must Have Support

> Every claim in the paper (especially in the Abstract and Introduction) must be correct and supported by experiments. Some reviewers will reject a paper directly for unsupported claims.

Go through every claim in the Abstract and Introduction. For each claim:
- [ ] Is it factually correct?
- [ ] Is there an experiment or analysis that supports it?
- [ ] Is the supporting experiment clearly referenced?

An unsupported claim — especially in the Abstract or Introduction — can be grounds for rejection.

---

## Reverse-Outlining Technique

> Extract the writing plan from finished paragraphs and check whether the flow is smooth.

After writing a section (or the entire paper):

1. **Read each paragraph** one at a time
2. **Write down the main message** of each paragraph in one sentence
3. **Read the sequence of messages** — does it flow logically?
4. **Identify breaks**: Where does the flow feel abrupt or illogical?
5. **Fix**: Reorganize paragraphs, add transitions, or split/merge paragraphs

Apply this to:
- Introduction (check narrative flow)
- Method (check if modules are presented in logical order)
- Experiments (check if results are presented in a meaningful sequence)

---

## Figure and Table Quality Checklist

### Figures
- [ ] Pipeline figure highlights novelty (not just explanation)
- [ ] Pipeline figure looks distinct from prior work
- [ ] Teaser figure is compelling and self-contained
- [ ] All figures have clear captions
- [ ] Resolution is high enough for print
- [ ] Color-blind friendly (avoid red-green only distinctions)
- [ ] Figures are referenced in the text

### Tables
- [ ] Captions are above the table
- [ ] No vertical lines
- [ ] Using booktabs (`\toprule`, `\midrule`, `\bottomrule`)
- [ ] Best results highlighted (bold/color)
- [ ] Metric direction indicated (↑/↓)
- [ ] Captions describe setup/notation, not results
- [ ] All tables are referenced in the text

---

## Conclusion and Limitation Check

- [ ] Conclusion summarizes contributions and key results
- [ ] **Limitation section is present** (reviewers frequently flag its absence)
- [ ] Limitations are about task/setting scope (like future work), not technical defects
  > Rule: "If our method does not fall below SOTA metrics, it is not a technical defect"
- [ ] Limitations are honest but not self-defeating

---

## Mechanical Consistency Scans

These checks need search and cross-referencing, not judgment — and they are among the most frequently missed, precisely because "reading carefully" never triggers them. Execute each one explicitly against the source files:

1. **Citation integrity.** Collect every citation key used in the text and verify each resolves to a bibliography entry (an unresolved key renders as "[?]"). Also flag bibliography entries missing venue/year/authors.
2. **Promise–delivery alignment.** List the contributions promised in the abstract and introduction (especially numbered contribution lists). For each, find the section/experiment that delivers it *and* its echo in the conclusion. A contribution promised up front that silently disappears by the conclusion is a finding.
3. **Module motivation.** For each named component of the method, locate the sentence explaining *why* it exists. A module described only by *what* it does, with the motivation nowhere, is a finding — and usually predicts a missing ablation.
4. **Claimed-but-missing comparisons.** Any method the paper itself calls "directly comparable", "closest prior work", or state-of-the-art must appear in the results tables — or the paper must say why not. Admitted in related work but absent from experiments is a finding.
5. **Numeric consistency.** Every number quoted in the abstract, introduction, or conclusion must match its source table. Recompute claimed improvements ("X% better", "reduces Y by Z"). Prose interpretation must match the table — "substantially better" backed by a 0.1-point gap is a finding.
6. **Leftover markers.** Search for `\todo`, `TODO`, `FIXME`, `XXX`, placeholder text, and commented-out warnings everywhere, including the appendix.
7. **Table/figure mechanics.** Beyond the style checklist above: verify the bolded "best" value actually **is** the best in each column, arrows match metric direction, and every table/figure is referenced in the text.

---

## Pre-Submission Final Checks

- [ ] All references are complete (no "?" or missing entries)
- [ ] Author information matches venue requirements
- [ ] Page count is within limits
- [ ] Supplementary material is properly referenced
- [ ] No TODO markers remain in the paper
- [ ] Acknowledgments section is appropriate
- [ ] No accidental double-blind violations (for anonymous review)
- [ ] All cited works have complete bibliographic entries (authors, title, venue, year)
- [ ] No self-citations that break anonymity (for double-blind venues)
- [ ] Key related works cited — missing a prominent baseline paper can trigger rejection

---

## Handoff to Rebuttal

When reviews come back, use the `paper-rebuttal` skill for:
- Score diagnosis and review color-coding
- Champion strategy (arming your positive reviewer for discussion)
- 18 tactical rules for structure, content, and tone
- Counterintuitive rebuttal principles

Your self-review artifacts (reject-first simulation, claim-evidence audit, prebuttal drafts from the counterintuitive protocol) feed directly into the rebuttal process.

---

See [references/review-checklist.md](references/review-checklist.md) for an expanded version of the 5-aspect checklist with more detailed sub-questions.

For adversarial stress testing and reject-risk thresholds, see [references/counterintuitive-review.md](references/counterintuitive-review.md).
