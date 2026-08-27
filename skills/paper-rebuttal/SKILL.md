---
name: paper-rebuttal
description: "Guides writing effective rebuttals after receiving peer review feedback. Covers review diagnosis (score-driven color-coding), response strategy (champion identification, common-theme consolidation), tactical writing (18 rules), and counterintuitive rebuttal principles. Use when: user received reviewer scores/comments, needs to write a rebuttal or author response, wants to respond to specific criticism (e.g. 'limited novelty', 'missing baselines'), mentions 'rebuttal', 'reviewer comments', 'author response', or 'respond to reviewers'. Do NOT use for pre-submission self-review (use paper-review instead)."
allowed-tools: "write_file edit_file read_file think_tool"
metadata:
  author: EvoScientist
  version: '1.4.0'
  tags: [core, writing, academic-writing, peer-review]
---

# Paper Rebuttal

A systematic approach to writing rebuttals after receiving peer review feedback. The goal is not to defend every point — it's to move scores by addressing the concerns that actually drive them.

## When to Use This Skill

- User received reviewer comments and needs to write a rebuttal
- User asks how to respond to specific reviewer criticism
- User wants to analyze reviews strategically before responding
- User mentions "rebuttal", "reviewer comments", "review feedback", "respond to reviewers"

> For pre-submission self-review and catching weaknesses before they become reviewer complaints, use the `paper-review` skill.

## Step 1: Diagnose Reviews

Before writing a single word, answer: **"Why did this reviewer give this exact score?"** Not what they wrote — what drove the score. Most researchers skip this and address every comment equally. That is a mistake.

### Score Diagnosis

For each reviewer, ask: "What would move this reviewer from their current score to acceptance?"

| Score Range | Typical Situation | Your Strategy |
|-------------|------------------|---------------|
| 7+ | Already your champion | Arm them with ammunition for the discussion phase |
| 5-6 | On the fence, 1-2 concerns holding them back | Identify and resolve those specific concerns |
| 3-4 | Fundamental objection | Determine if the objection is addressable; if not, focus elsewhere |
| **1-2** | **Strong rejection — fundamental flaw** | **Identify the 1-3 specific objections that drive the score — not every point they raise** |

### Score-Weighted Prioritization

Reviewer score tells you **where to look**, not **how much to flag**. A low score means that reviewer's *core objection* is decision-relevant — but a reviewer who lists eight points is driven by one or two of them, not all eight. Your job is to find those one or two, not to paint every low-score comment Red.

**Anchor on the meta-review / AC comment first.** If an area-chair or meta-review names specific unresolved issues, *those are the Red set* — they are the closest thing to ground truth for what drives the decision. The meta-review is the strongest signal for **fence-sitter and high-score** concerns; it does **not** override a low-score reviewer's own core objection (see the recall floor below).

| Reviewer Score | How to prioritize their concerns |
|----------------|----------------------------------|
| **1-2** | Find the **1-3 core objections** they cite as the reason for rejection — those are Red. Their *secondary* points (nice-to-haves, minor asks) are Orange/Gray like anyone else's. |
| **3-4** | Identify the **specific blocker(s)** they name — usually 1-2. Red. Not their entire comment list. |
| **5-6** | The 1-2 concerns they say are holding them back are Red; the rest Orange. |
| **7+** | Only what they explicitly flag as a concern; most Gray. |

**Recall floor — never drop a rejecter's core objection.** For every reviewer scoring **at or below the rejection threshold (≤3)**, their **1-3 primary objections are Red by default** — the reason they reject *is* what drives the decision, whether or not they spell out "this is why I can't accept," and whether or not the meta-review echoes it. Demote such an objection out of Red **only** if the paper/rebuttal already resolves it. This is the one place reviewer score outranks the meta-review anchor: an AC can omit an issue that a reviewer still rejects over. The floor is a *minimum* (1-3 per low-score reviewer), not a license to Red their entire list — their secondary asks stay Orange/Gray.

**Red is scarce by design.** Across all reviewers, Red should be the *minority* of comments — typically the handful of issues that actually span the accept/reject boundary. If more than ~40% of comments end up Red, you are over-flagging: re-ask which ones the *decision* actually turns on.

### Color-Code Every Comment

Read through each review and mark every comment:

| Color | Meaning | Action | Budget |
|-------|---------|--------|--------|
| **Red** | Score-driving concern — this is why the score is low | Address first, maximum effort and evidence | 60% |
| **Orange** | Addressable concern — can be resolved | Respond with concrete data or revision | 30% |
| **Gray** | Minor or cosmetic | Acknowledge briefly, confirm fix | 10% |
| **Green** | Positive comment or praise | Note as ammunition for your champion | — |

### What Makes a Concern "Score-Driving"?

A concern is **Red** only if it clears BOTH bars:

**(a) It is decision-relevant** — at least one of:
1. **Named in the meta-review / AC comment** as an unresolved issue (strongest signal — overrides the rest)
2. A **primary/core objection of a reviewer scoring ≤3** — presumed to be their reason for rejecting even without explicit "this is why I can't accept" phrasing (cap 1-3 per reviewer; see the recall floor above). Explicit "main concern / can't accept" language makes it certain but is not required.
3. **Same fundamental issue raised independently by ≥2 reviewers** AND still unresolved
4. **Challenges the validity of the core claim** in a way that, if true, changes the paper's conclusion

**(b) It is still unresolved** — not already addressed in the paper or rebuttal. An issue the paper already handles is not score-driving, no matter how fundamental it sounds.

**Do NOT mark Red** — these are the common over-flagging traps that cost precision:
- A point that merely *touches* the method or "could affect validity" but is not cited as a score reason and has no meta-review/consensus backing → Orange at most
- Additional-experiment or additional-baseline *suggestions* framed as improvements ("it would be stronger if…") unless a reviewer ties them to their score
- **Secondary points from a low-score reviewer beyond their 1-3 stated core objections** — a 2-score reviewer's fifth minor ask is not Red just because their score is low
- Anything the paper already addresses
- Minor clarifications, stylistic notes, or "nice to have" asks

**Fence-sitters (3-6):** a politely-phrased ask ("consider adding…") *is* Red **only if** the reviewer links it to their reservation, or it has meta-review/consensus backing. Politeness alone doesn't demote a real blocker — but a polite suggestion with no score linkage is not automatically a blocker either.

**Rule of thumb:** For each Red, name the concrete decision it drives — "without this, R3 stays at 2" or "the AC's cited concern stays open." If you cannot name that decision, it is not Red.

### Identify the Invisible Question

Behind every reviewer comment is an unspoken question. A comment like "The baselines are outdated" really asks: "Is this method actually competitive with current approaches?" Address the invisible question, not just the surface request.

## Step 2: Plan Response Strategy

### Categorize Every Concern

| Category | Response Strategy |
|----------|-----------------|
| **Misunderstanding** | Clarify with specific references to the paper; restate the key point |
| **Missing experiment** | First check whether existing results (incl. appendix) already answer it — cite the exact location and restate them; else provide the experiment inline; a scoped, concrete promise is the last resort |
| **Missing baseline** | Add comparison or explain precisely why the baseline is not applicable |
| **Writing clarity** | Acknowledge and provide revised text in the rebuttal |
| **Fundamental concern** | Address directly with technical arguments AND additional evidence |
| **Minor issue** | Thank the reviewer and confirm the fix |

### Identify Common Themes

If multiple reviewers raise the same concern, it's almost certainly a real weakness. Consolidate these into a "Common Response" section — this saves word count and demonstrates that you understand the pattern.

### Distinguish Actionable vs. Subjective

- **Actionable**: "Missing comparison with Method X" — you can do this
- **Subjective**: "The novelty is limited" — harder to address, but can be reframed with evidence

### The Champion Strategy

**Your rebuttal's real audience is not the negative reviewer — it's the positive one.**

Your champion argues on your behalf in the AC discussion, often using your exact words. Write your rebuttal to arm them:

1. Make key arguments **copy-pasteable** — your champion will quote you directly
2. Highlight where reviewers **agree with each other** — consensus strengthens the champion's position
3. Flag **contradictions between reviewers** — if R1 says "limited novelty" but R2 says "interesting approach," your champion can use this
4. Lead with **strengths before weaknesses** — remind the AC what your paper does well

See [references/rebuttal-tactics.md](references/rebuttal-tactics.md) for the full 18 tactical rules.

## Step 3: Write the Rebuttal

### Structure

1. **Opening**: One line thanking reviewers (keep it short)
2. **Common concerns**: Address issues raised by multiple reviewers first — these are highest priority
3. **Per-reviewer responses**: Address remaining concerns in priority order (red → orange → gray), NOT in the order the reviewer wrote them

### Per-Concern Format

For each concern, follow this three-part structure:

1. **Acknowledge**: Show you understand the concern (one sentence)
2. **Respond**: Provide your answer — evidence, clarification, new experiment results
3. **Action**: State what you changed in the revision (specific section/table/figure)

Use a fillable template at [assets/rebuttal-template.md](assets/rebuttal-template.md).

### The Neutral Third-Party Test

Before submitting, have someone who hasn't read your paper read only the reviews and your rebuttal. Ask: "Can you tell whether the concerns were addressed?" If not, rewrite.

## Counterintuitive Rebuttal Principles

1. **Submit a rebuttal even with extreme scores.** A paper with scores of 3/8/8 has better odds than you think. The negative reviewer may realize they are an outlier during discussion. But only if you submit a rebuttal — without one, the AC has nothing to work with.

2. **Concede something small, win something big.** Acknowledging a minor weakness ("We agree that Table 2 could include dataset X for completeness") makes your defense of major points more credible. Pure defense with zero concession reads as unobjective.

3. **Existing evidence first, new experiments second, bare promises last.** Before proposing any new experiment, mine the submitted paper — main text *and* appendix — for evidence that already answers the concern, and quote it with its exact table/figure/section. ACs reward answers grounded in the paper they already have and discount promised future work. If the paper genuinely lacks the answer, a small new experiment with results shown inline still beats any amount of reasoning — reviewers are trained to be skeptical of arguments, not of data. A promise without results is the weakest move: make it rare, singular, and concrete (what will be run, on which data, by when). A rebuttal stacked with "we will add…" reads as an admission that the paper is incomplete.

4. **The best rebuttal is written before submission.** Draft responses to likely attacks while writing the paper ("prebuttal"). Two benefits: you often realize the attack is valid and fix the paper, and if the attack comes, you have a polished response ready.

5. **Don't defend every point equally.** Equal effort signals you don't know which points matter. Allocate your word budget according to the color-coding: 60% red, 30% orange, 10% gray. Reviewers notice when you nail the big issues.

## Common Reviewer Concerns

Prepare responses for these frequent concerns. Having a prepared response doesn't mean copying it verbatim — adapt to your specific paper and the reviewer's specific framing.

| Common Concern | Response Strategy |
|---------------|-------------------|
| "Limited novelty" | Articulate the specific insight; show what prior work cannot do; narrow and sharpen the claim |
| "Marginal improvement" | Emphasize other advantages (speed, generalizability, simplicity); add challenging test cases |
| "Missing ablations" | Provide the ablation table inline in the rebuttal |
| "Missing baselines" | Add the comparison or explain precisely why it's not applicable |
| "Not reproducible" | Add implementation details; commit to code release with a specific timeline |
| "Limited evaluation" | Add diverse datasets or metrics; if infeasible, explain resource constraints honestly |
| "No limitation discussed" | Add a limitation section in the revision; acknowledge this was an oversight |
| "Overclaimed results" | Weaken specific claims to match evidence; show the revised wording |
| "Unfair comparison" | Use standard evaluation protocols; add commonly reported baselines |
| "Method is engineering, not research" | Identify the scientific insight behind the design; explain why the choice is non-obvious |
| "Metrics don't match claims" | Align each claim with a specific metric; add the missing metric if feasible |
| "Related work incomplete" | Add the missing references; explain the relationship to your work |

> **Need to run new experiments for the rebuttal?** Use the `experiment-craft` skill for targeted debugging, or `experiment-pipeline` for a full new experiment stage.

## Handoff from Paper Review

This skill picks up where `paper-review` leaves off. If you used `paper-review` before submission, these artifacts are especially useful for rebuttal:

| Artifact from paper-review | How It Helps Rebuttal |
|---------------------------|----------------------|
| Reject-first simulation | You've already anticipated likely attacks |
| Claim-evidence audit table | Quickly verify whether a reviewer's concern about unsupported claims is valid |
| Prebuttal drafts (Phase 6) | Ready-made response templates for common criticisms |
| Trust scorecard | Identifies weaknesses you can proactively concede |

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| 18 tactical rules | [rebuttal-tactics.md](references/rebuttal-tactics.md) | Detailed writing guidance for structure, content, tone |
| Rebuttal template | [rebuttal-template.md](assets/rebuttal-template.md) | Starting a new rebuttal document |
