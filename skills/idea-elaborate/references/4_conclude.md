You are synthesizing the conclusions for a single research direction. Stages 2 and 3 have done the work — your job is to **close the loop**: read both, decide whether the direction is worth pursuing, name the load-bearing assumption, identify the strongest sub-version, and produce a concrete next move that supersedes the original node's `next_action` now that we know more.

This is the final reasoning step before the (opt-in) paper draft. It must be **synthetic, decisive, and brief**. Do not re-litigate stage 3's verdicts. Do not soften them. Do not re-open the elaboration.

---

## Stage 2 output (elaborated direction)

{elaborated_idea}

## Stage 3 output (adversarial analysis)

{analysis}

---

## Synthesis rules

1. **No new evidence.** Do not introduce claims, papers, techniques, or counterarguments that did not appear in stages 2 or 3. If you find yourself wanting to, that's a signal stage 2 or 3 was incomplete — surface it as a `Needs follow-up` row in the *Recommended concrete next move* section rather than papering over it here.
2. **Stage 3 is authoritative on weaknesses.** Every con must cite a phase from stage 3 (e.g. `[Phase 1 reject reason 2]`, `[Phase 4 claim audit: <claim ID>]`). If a con doesn't trace back, drop it.
3. **Stage 2's *Refined direction* sentence is the unit of decision.** Pros / cons / verdict all attach to *that one commitment*, not to the broader area of research.
4. **No promotional softening.** If stage 3's Phase 5 trust scorecard was <7/10, the verdict is `needs another elaboration pass` — not `promising direction with some caveats`. Hiding a weak score loses ground later.
5. **The recommended next move replaces the node's original `next_action`.** The user clicked through to elaborate precisely because the original was loose. Your job is to hand back a sharper one.

---

## What to emit

A single markdown document with these six top-level sections, in this order, using these exact headers. Keep each section short — most are one paragraph or a short bullet list. Closing sharp beats closing comprehensive.

```
# Verdict

One of three labels followed by one sentence justification:

- `worth pursuing` — Phase 5 trust scorecard ≥ 8/10 AND fewer than 2 `unsupported` verdicts in Phase 4. Justify in one sentence naming the strongest anchor in stages 2+3.
- `worth pursuing with named caveats` — Phase 5 trust scorecard 7/10 OR 1–2 `unsupported` verdicts in Phase 4. Justify by naming the specific caveats from stage 3 that must be addressed concurrently.
- `needs another elaboration pass` — Phase 5 trust scorecard < 7/10 OR ≥ 3 `unsupported` verdicts. Justify by naming what would have to change in stage 2 to lift the score.

Do not invent a fourth label. If the picture is mixed, pick the more conservative of the two adjacent labels and explain in the justification.

# Pros

3–4 bullets. Each = one positive grounded in either stage 2's *Insights from the shortlist that apply* or stage 3's `supported` Phase 4 claims. Cite the source: `[stage 2: insight bullet N]` or `[Phase 4: claim ID]`. Do not bullet the same insight twice. Do not include "novelty" as a pro unless Phase 3's verdict was `likely no` (= novelty is defensible) — otherwise it's promotional handwave.

# Cons

3–4 bullets. Each = one weakness traced to stage 3. Format: `[Phase N: short pointer] <one sentence>`. At least one con must reference Phase 1 (reject summary); at least one must reference Phase 2 (mock-rejection table, highest P×I row); at least one must reference Phase 4 (an `unsupported` or `weak` verdict). If Phase 5 named a kill-switch-level concern (trust score < 7/10), surface it here as a separate bullet.

# Load-bearing assumption

**Exactly one bullet.** Of stage 2's *Load-bearing assumptions*, name the single one that, if false, invalidates the direction outright (not "weakens" — *invalidates*). If multiple compete for the spot, pick the one stage 3's claim audit flagged most aggressively. State why it's load-bearing in one sentence: what concretely fails if it's false. If stage 2 listed no assumptions or if none rises to "invalidating," say so explicitly — that itself is a finding.

# Strongest sub-version

One short paragraph (≤4 sentences). Given stage 3's audit, what is the narrowest version of the direction that survives the hardest critique? This is *not* the full elaborated direction with caveats; it is a deliberately scoped-down version. Format:

> *Smallest defensible commitment:* "<one-sentence claim narrower than stage 2's *Refined direction*>".
> *What this version drops vs the elaborated direction:* one sentence.
> *Why it survives stage 3:* one sentence citing the specific Phase 3 / Phase 4 evidence.

The sub-version is the fallback if the verdict is `worth pursuing with named caveats` and the user wants to de-risk. Stage 5's paper draft, if it runs, may use the sub-version as the primary contribution claim.

# Recommended concrete next move

This **replaces** the node's original `next_action`. It must be:

- More specific than the original.
- Executable as a thought-experiment / literature work / planning step (no real experiments — per skill scope).
- Aligned with the verdict: a `worth pursuing` verdict gets a sharpening next move; a `needs another elaboration pass` verdict gets a remediation next move (e.g. "rerun stage 1 with a narrower query targeting [specific gap]").

Format as a short numbered list, 1–3 items, each ≤20 words:

> 1. ...
> 2. ...
> 3. ...

If the verdict was `needs another elaboration pass`, the first item must be the remediation (what to fix in stage 2 or stage 1 before reconsidering). Add a single trailing line:

> *Original `next_action` for reference:* "<verbatim from stage 2's node context>"

so the user can see the sharpening at a glance.
```

---

## Tone

Brief and decisive. Stages 2 and 3 did the heavy lifting; this stage commits. A reader scanning only stage 4's output should be able to answer "should I pursue this, what's the riskiest assumption, and what should I do next" in under 60 seconds.

Single pass. Do not iterate within stage 4 — if you find yourself wanting to revise pros or cons after writing the verdict, that means an earlier section was wrong. Fix it and move on; do not introduce hedging language to bridge the inconsistency.

## Output

A single markdown document matching the six-section structure above. No preamble, no postamble, no fenced code block wrapping the whole thing — start at `# Verdict`. The downstream stitch step will concatenate stages 2, 3, and 4 into a single `notes.md` with stage headers — your section headers will live alongside theirs.
