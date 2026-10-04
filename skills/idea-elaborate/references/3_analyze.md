<!--
Sources lifted / adapted from EvoSkills (re-check on upstream version bumps):

- paper-review/references/counterintuitive-review.md → Phases 1, 3, 4, 5 below.
- paper-planning/references/counterintuitive-planning.md → Rule 1 supplies Phase 2 (mock-rejection table); Rule 4 supplies the honest-weakness requirement folded into Phase 5.
- paper-review/SKILL.md "Perfectionist Approach" prose → tone preamble.

Adaptation: paper-stage → idea-stage. The original protocols audit a *completed paper draft*; we apply them to an *elaborated research direction* (stage 2's output) before any experiments exist. Concrete differences:

- claim-evidence audits map against the shortlist's `evidence_quote` (from paper-navigator's quote-or-zero discipline) rather than tables / figures in a draft.
- trust scorecard items adapt: no "fairness of baseline comparison" (no experiments yet) — replaced with grounding-equivalents from the shortlist.
- kill-switch conditions become "abandon-direction conditions" rather than "do-not-submit conditions."

If upstream rules / phases shift, re-lift. These are agent-discipline templates, not code, and they can drift.
-->

You are running an **adversarial analysis** on a single research direction that has just been elaborated (stage 2). The direction is fixed. Your job is to attack it as a top-tier reviewer would — *before* any experiments are run — and produce a structured audit that stage 4 (conclusions) can synthesize and stage 5 (paper draft, if it runs) can preempt.

## Tone

> Strive for perfection: read the elaborated direction as a critical reviewer would, consider every question they might ask, and address them one by one. The best defense against a wasted research cycle is a thorough self-audit *now*, not after spending months on experiments that a reviewer would have killed in five minutes.

Do not soften. Do not write positives until you have written the reject summary. Specific attacks survive next-stage synthesis; vague concerns do not. Cite shortlist papers by `[paper rank N]` when grounding an attack — ungrounded attacks have the same problem as ungrounded claims.

---

## Stage 2 output (the elaborated direction being audited)

{elaborated_idea}

## Literature shortlist (paper-navigator output from stage 1)

{papers}

## Focusing phrase (optional)

{focusing_phrase}

If non-empty, treat as a hard scope constraint on every phase below.

---

## Phase 1 — Reject-First Summary

*Source: paper-review/references/counterintuitive-review.md Phase 1.*

Write this FIRST, in reviewer tone, before any positive comment. Do not skip to other phases; the reject summary surfaces high-risk weaknesses fastest.

```
This direction should not be pursued because:
1) ...
2) ...
3) ...
```

Exactly 3 reasons, each one sentence, each pointing at a specific weakness in the elaborated direction — not generic critique. Each reason must be **grounded**: cite either a shortlist paper showing the weakness is real, or the elaborated direction's own load-bearing assumption that you suspect breaks.

## Phase 2 — Mock-Rejection Risk Table

*Source: paper-planning/references/counterintuitive-planning.md Rule 1.*

Predict the rejection comments this direction would get if it became a paper submission, then score and triage them. Use this table format exactly:

| Predicted Rejection Comment | Probability (1-5) | Impact (1-5) | Preemption (concrete edit to direction, or new experiment to add) |
|---|---:|---:|---|

Populate at least 4 rows. Include:

- *"Novelty is limited"* — preempt with explicit difference table vs the closest shortlist paper(s).
- *"Missing baseline X"* — name X. If the shortlist contains an obvious baseline missing from stage 2's *Concrete proposal*, this is real.
- *"Claim Y unsupported"* — name a specific claim from the elaborated direction.
- *"Not robust"* / *"Won't generalize"* — pick the more applicable.

Add more rows for direction-specific risks. Sort the final table by `Probability × Impact` descending. **Triage order for preemption work:**
1. Desk-reject prevention (missing baselines, unsupported core claims).
2. Highest risk-score items from the table.
3. Polish-level items only after 1 and 2 are addressed.

## Phase 3 — Novelty Stress Test

*Source: paper-review/references/counterintuitive-review.md Phase 2.*

Apply this exact question to the elaborated direction:

> "Could a capable PhD in this subfield derive this direction in one afternoon after reading the shortlist papers?"

Answer with one of three verdicts:

- **likely yes** — the direction recombines existing shortlist ideas without a non-obvious mechanism. The novelty case is weak. Recommend one of: narrow the claim scope; emphasize a non-obvious mechanism or theoretical justification the shortlist lacks; reframe the contribution around robustness / efficiency / setting realism rather than novelty rhetoric.
- **likely no** — the direction relies on a non-obvious mechanism that the shortlist does not directly suggest. Name the mechanism precisely. The novelty case is defensible.
- **uncertain** — the shortlist does not contain enough adjacent work to settle the question. Name what additional literature would resolve it (and what your provisional best guess is meanwhile).

Worked-example contrast (do not echo, just match the rigor level):

> Before: *"We propose a novel attention mechanism that achieves superior performance."*
> After: *"We show that axis-aligned decomposition of 3D attention reduces memory from O(N³) to O(N) while preserving reconstruction quality within 0.3 dB — derivable from [paper rank 7] only via a non-obvious factorization of the temporal axis."*

## Phase 4 — Claim-Evidence Audit

*Source: paper-review/references/counterintuitive-review.md Phase 3, adapted: evidence comes from the shortlist's `evidence_quote` (paper-navigator's quote-or-zero) rather than tables / figures in a draft.*

For each claim in stage 2's *Concrete proposal* and each item in stage 2's *Falsifiability* and *Load-bearing assumptions* sections, produce an audit row:

| Claim ID | Claim (verbatim from stage 2) | Evidence (`[paper rank N]` + ≤80-char quote, or "none in shortlist") | Verdict |
|---|---|---|---|

Verdicts:

- **supported** — at least one shortlist paper directly supports the claim. Quote the supporting evidence.
- **weak** — adjacent support exists but doesn't directly prove the claim. Weaken the wording: replace strong verbs with qualified ones (*may, suggests, in regimes where*).
- **unsupported** — no shortlist paper supports the claim. **Delete or rewrite** before stage 4 / stage 5. Do not let an unsupported claim survive the audit.

The audit is the *anchor* for stage 4's synthesis — every "unsupported" verdict here is a load-bearing item the conclusions must surface.

## Phase 5 — Trust Scorecard with Mandatory Honest Weakness

*Source: paper-review/references/counterintuitive-review.md Phase 4 + paper-planning/references/counterintuitive-planning.md Rule 4. Adapted: idea-stage scorecard items replace paper-stage ones (no experiments yet).*

Score each item 0–2 (0 = absent / problematic, 1 = partial, 2 = clear / strong):

- **Grounding in shortlist** — does the elaborated direction cite specific shortlist papers for each technical choice, or does it handwave?
- **Reproducibility hooks** — does the direction name datasets, splits, metrics, and at least one concrete protocol such that a reader could begin implementation?
- **Honest scope boundary** — does the elaborated direction acknowledge what it will *not* address? Is there at least one explicit non-goal?
- **Failure-mode transparency** — does *Load-bearing assumptions* honestly enumerate what might break, with at least one named failure mode?
- **Specificity of contribution claim** — is the *Refined direction* sentence concrete (numbered deltas, named regime) rather than promotional?

If total `< 7/10`, the direction is **not yet ready** for stage 5 (paper draft). Stage 4 (conclusions) should surface this as "needs another elaboration pass" rather than "ready to write."

**Mandatory honest weakness (paper-planning Rule 4):** independent of the score, name **exactly one** controlled failure mode for this direction:

- Pick one representative failure case (a regime, dataset, or assumption boundary where the direction is *expected* to underperform).
- Explain in one sentence why the failure happens given the proposed technique.
- Promote it: this is the limitation the user will surface up-front in stage 4's conclusions and (if it runs) stage 5's paper. Hiding it loses ground; promoting it buys trust.

Counterintuitive effect: one honest limitation often increases confidence in all other claims.

---

## What to emit

A single markdown document with these five top-level sections, in this order, using these exact headers:

```
# Phase 1 — Reject-First Summary
# Phase 2 — Mock-Rejection Risk Table
# Phase 3 — Novelty Stress Test
# Phase 4 — Claim-Evidence Audit
# Phase 5 — Trust Scorecard with Mandatory Honest Weakness
```

No preamble, no postamble, no fenced code block wrapping the whole thing — start at `# Phase 1`. Stage 4 will read all five sections and synthesize; do not collapse phases or skip ahead.
