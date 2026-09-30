---
name: paper-rebuttal
description: "Guides writing effective rebuttals after receiving peer review feedback. Covers review diagnosis (score-driven color-coding), response strategy (champion identification, common-theme consolidation), tactical writing (18 rules), and counterintuitive rebuttal principles. Use when: user received reviewer scores/comments, needs to write a rebuttal or author response, wants to respond to specific criticism (e.g. 'limited novelty', 'missing baselines'), mentions 'rebuttal', 'reviewer comments', 'author response', or 'respond to reviewers'. Do NOT use for pre-submission self-review (use paper-review instead)."
allowed-tools: "write_file edit_file read_file think_tool"
metadata:
  author: EvoScientist
  version: '1.1.0'
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
| 1-2 | Strong rejection | Identify the one or two objections that drive the score, not every point they raise |

### Color-Code Every Comment

Read through each review and mark every comment:

| Color | Meaning | Action | Budget |
|-------|---------|--------|--------|
| **Red** | Score-driving concern — this is why the score is low | Address first, maximum effort and evidence | 60% |
| **Orange** | Addressable concern — can be resolved | Respond with concrete data or revision | 30% |
| **Gray** | Minor or cosmetic | Acknowledge briefly, confirm fix | 10% |
| **Green** | Positive comment or praise | Note as ammunition for your champion | — |

### Which Concerns Are Red

Reviewer score tells you where to look, not how much to flag. A reviewer who lists eight points is usually driven by one or two of them, so marking every comment from a low-score reviewer Red spends the 60% budget on points that move nothing.

**The decision test.** Mark a concern Red only if both hold:

1. You can name the decision it drives: "without this, R3 stays at 3" or "the AC's cited concern stays open". If you cannot name one, it is not Red.
2. It is still unresolved. A concern the paper already answers is not score-driving, however fundamental it sounds: answer it by pointing to the evidence (Counterintuitive Rebuttal Principle 3 below) and mark it Orange.

Any one of the following is enough to name the decision for point 1:

- The meta-review or AC comment names the concern as unresolved: the decision is the AC's. Use this only when such a comment is actually in the input.
- It is the core objection of a reviewer who recommends rejection (1-4), whether they call it their main issue or it is simply the substance of their review: the decision is that reviewer's score. This holds even when it is politely phrased and even when the meta-review does not repeat it. Expect one or two per reviewer, not their whole list.
- A reviewer on the fence (5-6) ties it to their reservation: the decision is that reviewer's score.
- Two or more reviewers raise the same fundamental issue independently: the decision is the AC's reading of the consensus.
- If true, it would change the paper's main conclusion: the decision is whether the central claim stands.

Common over-flagging, Orange or Gray instead: a rejecting reviewer's secondary asks; improvement suggestions ("it would be stronger if…") that are neither a rejecting reviewer's core objection nor tied by a fence-sitter to their reservation; points that merely touch the method; minor clarifications.

Red means the concern decides the outcome, not that you can win it. When a Red objection cannot be answered, concede it plainly and narrow the claim instead of spending the budget arguing.

There is no quota. Short, harsh reviews can make most comments Red, and that is then the honest picture: do not demote a rejecting reviewer's core objection to keep the Red list short. When long reviews leave most comments Red, rerun the test on each one; you are probably flagging by score rather than by decision.

### Identify the Invisible Question

Behind every reviewer comment is an unspoken question. A comment like "The baselines are outdated" really asks: "Is this method actually competitive with current approaches?" Address the invisible question, not just the surface request.

## Step 2: Plan Response Strategy

### Categorize Every Concern

| Category | Response Strategy |
|----------|-----------------|
| **Misunderstanding** | Clarify with specific references to the paper; restate the key point |
| **Missing experiment** | First check whether existing results (including the appendix) already answer it: cite the exact location and restate them. Otherwise run it and show the result inline. If it cannot be run, explain the constraint honestly and narrow the claim; a scoped, concrete promise is the last resort |
| **Missing baseline** | Point to the comparison if the paper already reports it; otherwise add it, or explain precisely why the baseline is not applicable |
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

3. **Existing evidence first, new experiments second, promises last.** Before proposing a new experiment, search the submitted paper, main text and appendix, for evidence that already answers the concern, and quote it with its exact table, figure or section: the AC can verify it in the PDF they already have, and discounts promised future work. If the paper does not answer it, a small new experiment with the result shown inline still beats any amount of reasoning; reviewers are trained to be skeptical of arguments, not of data. If the experiment cannot be run, say so and narrow the claim. A promise without results is the weakest move: keep it rare and concrete (what will be run, on which data, by when). A rebuttal stacked with "we will add…" reads as an admission that the paper is incomplete.

4. **The best rebuttal is written before submission.** Draft responses to likely attacks while writing the paper ("prebuttal"). Two benefits: you often realize the attack is valid and fix the paper, and if the attack comes, you have a polished response ready.

5. **Don't defend every point equally.** Equal effort signals you don't know which points matter. Allocate your word budget according to the color-coding: 60% red, 30% orange, 10% gray. Reviewers notice when you nail the big issues.

## Common Reviewer Concerns

Prepare responses for these frequent concerns. Having a prepared response doesn't mean copying it verbatim — adapt to your specific paper and the reviewer's specific framing. In every row, principle 3 applies first: if the submitted paper already answers the concern, point to that evidence before adding anything.

| Common Concern | Response Strategy |
|---------------|-------------------|
| "Limited novelty" | Articulate the specific insight; show what prior work cannot do; narrow and sharpen the claim |
| "Marginal improvement" | Emphasize other advantages (speed, generalizability, simplicity); add challenging test cases |
| "Missing ablations" | Point to the ablation if the paper or appendix already has it; otherwise provide the ablation table inline in the rebuttal |
| "Missing baselines" | Point to the comparison if it is already reported; otherwise add it, or explain precisely why it's not applicable |
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
| Prebuttal drafts (Phase 6 of the counterintuitive protocol) | Ready-made response templates for common criticisms |
| Trust scorecard | Identifies weaknesses you can proactively concede |

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| 18 tactical rules | [rebuttal-tactics.md](references/rebuttal-tactics.md) | Detailed writing guidance for structure, content, tone |
| Rebuttal template | [rebuttal-template.md](assets/rebuttal-template.md) | Starting a new rebuttal document |
