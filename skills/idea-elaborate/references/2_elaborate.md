You are elaborating a single research direction from an idea-spark graph into a concrete, literature-grounded proposal. The direction is **fixed** — your job is not to brainstorm alternatives, evaluate competing candidates, or pivot. Your job is to sharpen *this* direction: what it concretely proposes, which technical challenge it addresses, which existing insights it builds on, and which open gap it exploits.

The output is markdown, structured so that downstream stages (adversarial analysis, conclusions, optional paper draft) can consume it section-by-section.

---

## Node context

The chosen direction's place in the idea-spark graph — title, description, next_action, references, ancestor chain, sibling titles:

{node_context}

## Literature (from paper-navigator)

Ranked shortlist of papers gathered specifically for this direction's `next_action`. Each entry includes a `rank` you can cite as `[paper rank N]` inline, plus an `evidence_quote` that grounds why that paper was included:

{papers}

## Focusing phrase (optional)

{focusing_phrase}

If the focusing phrase is empty, ignore this section. If non-empty, treat it as a hard scope constraint: every claim and every cited insight must remain within that scope.

---

## Adapted challenge-insight framing

The `research-ideation` skill builds a multi-direction challenge-insight tree as a *search space* over candidate ideas. You are NOT doing that. You are using the same primitive — extracting challenges from each paper and the insights that address them — but applied to a single fixed direction as a *landscape*:

- The chosen direction's `next_action` corresponds to one (or two) **specific technical challenge(s)**. Name them precisely.
- The papers' insights either **build the case for this direction** (insight + challenge = current state) or **highlight an open gap** (challenge without sufficient insight in the literature shortlist).
- Adjacent insights — techniques from the shortlist applied to other challenges — are **transfer opportunities** this direction could leverage.

Use this framing to produce the structured output below. Do not include the tree as a separate artifact; let it shape the proposal.

---

## What to emit

A single markdown document with these sections, in this order, with the exact headers shown. Each section's purpose is for a downstream consumer — keep the content specific, not promotional.

```
# Refined direction

One sentence (≤25 words) that sharpens the node's `next_action` into a single concrete commitment. This sentence is what stage 3 will attack and what stage 5 (if it runs) will paraphrase into the proposal's title.

# Concrete proposal

3–5 paragraphs:
- **Technique** — exactly what method/architecture/protocol is being proposed. Cite specific papers from the shortlist by `[paper rank N]`. If you cannot ground a technical choice in the literature, say so explicitly rather than handwave.
- **Data and evaluation regime** — datasets, splits, metrics. Use the `next_action`'s named regime if present; otherwise commit to a specific one and justify against the shortlist.
- **Expected outcomes** — concrete deltas you expect to see (e.g. "≥3 pp DER improvement on AMI far-field vs WavLM-CTC baseline"), not "improved performance." If you cannot commit to a number, write down the qualitative shape (monotone-better, plateau-after-N, no-improvement-baseline-already-saturated) — these are what stage 3 will stress-test.

# Challenge-insight landscape

Three short subsections — each is a list with brief annotations, not prose. Cite papers by rank.

## Specific challenge this direction addresses
- 1–2 bullets. Name the technical challenge in literature-style terms (e.g. "representation divergence between phonetic-heavy SSL codebooks and identity-heavy downstream tasks"). Each bullet cites at least one shortlist paper that frames the challenge.

## Insights from the shortlist that apply
- 3–6 bullets. Each bullet = one insight from one paper from the shortlist, plus one line on how it applies to *this* direction. Format: `[paper rank N] <insight summary> → applies here as <one line>`.

## Open gap this direction exploits
- 1–2 bullets. State the gap as a *claim about the shortlist's coverage* — e.g. "no shortlist paper applies VPC's variational term specifically to overlapping-speaker pretext tasks." If you cannot find such a gap, say so explicitly — that is itself a finding stage 3 will use.

## Transfer opportunities (adjacent insights worth considering)
- 0–3 bullets. Insights from the shortlist applied to other challenges that this direction could borrow. Each bullet = `[paper rank N] originally addresses <X>; could be transferred as <one line>`. Omit the section if there are no plausible candidates — do not invent transfers.

# Falsifiability

3–5 bullets. Each = one concrete observation that would invalidate the refined direction. Examples: "If the WavLM residual probe shows ≤1 pp DER on AMI far-field, the residue-mining premise is wrong." Stage 3 will use these as the claim-evidence audit anchor.

# Load-bearing assumptions

2–4 bullets. Each = one assumption the proposal relies on that is *not* yet supported by the shortlist. Stage 3 will attack these. Examples: "Assumes VPC's variational term is differentiable through a multi-speaker masking pretext (not demonstrated in shortlist)." If you can support an assumption with a shortlist paper, move it to *Insights from the shortlist that apply* instead.

# Confidence

Single line: low / medium / high, plus a half-sentence on what would raise the confidence one level. Example: `medium — would be high if at least one shortlist paper had directly evaluated the proposed technique on the named evaluation regime.`
```

## Tone

Rigorous, not promotional. The proposal is being audited next stage; making it sound impressive now buys nothing and loses ground in stage 3. Specific is more defensible than ambitious. *"Improve DER by ≥3 pp on AMI far-field by applying the VPC variational term to the multi-speaker masking pretext"* survives adversarial review better than *"unlock a new paradigm for low-resource diarization."*

If the literature shortlist does not let you commit to a specific technique or regime, say so in the *Concrete proposal* section explicitly. A grounded *"the literature does not yet specify X; the smallest defensible commitment is Y"* is stronger than an ungrounded confident proposal.

## Output

A single markdown document matching the section structure above. No preamble, no postamble, no fenced code block wrapping the whole thing — start at `# Refined direction`.
