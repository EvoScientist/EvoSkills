You are auditing a single claimed evolution edge in a research-lineage
graph. The edge says: source paper (M) had a specific limitation that
target paper (N) addressed. Your job is to label the strength of textual
evidence for this edge.

--- Source paper (M) ---
({m_n}) {m_title} ({m_year})
Abstract: {m_abstract}
Discussion/Conclusion excerpt: {m_excerpt}

--- Target paper (N) ---
({n_n}) {n_title} ({n_year})
Abstract: {n_abstract}
Discussion/Conclusion excerpt: {n_excerpt}

--- Claimed gap ---
{gap_text}

--- Labels ---
Choose exactly one:

- SUPPORTED_BY_ABSTRACT — The source abstract explicitly establishes a
  mechanism, capability, or limitation, AND the target abstract explicitly
  introduces a concrete change addressing the same specific mechanism or
  limitation. Naming or citing the source is strongest but not mandatory;
  shared topic, chronology, or generic improvement language is not enough.
- SUPPORTED_BY_SECTION  — The supporting evidence for either side
  (lack on M, or fix on N) is in the Discussion/Conclusion excerpt
  rather than the abstract, but the textual evidence is still concrete.
- INFERRED              — The claim is plausible but neither the abstract
  nor the excerpt explicitly attests to one or both halves of the
  source-lack/target-fix pair. Record it as a possible relationship, but do
  NOT render it as a directed lineage edge.
- REJECT                — The abstracts or excerpts contradict the
  claimed gap (e.g., the source paper already does X, or the target
  paper does not actually address X), the target predates the source, or the
  papers are merely parallel approaches. The edge should not be rendered.

Use `INFERRED` only when the relationship is specifically plausible but textual
evidence is incomplete. Use `REJECT` for thematic similarity, forced chronology,
parallel methods, backwards chronology, or a misdescribed gap.

Quote one verbatim span from each paper. `source_quote` must establish the
source mechanism or limitation; `target_quote` must establish the target's
concrete change to that same mechanism or limitation. Use `NONE` when that side lacks evidence;
any verdict with `NONE` must be `INFERRED` or `REJECT`.

--- Output ---
Output ONLY a JSON object with this exact shape (no code fences, no
prose before or after):

{{"verdict": "<one of the four labels>",
  "source_quote": "<verbatim source evidence or NONE>",
  "target_quote": "<verbatim target evidence or NONE>",
  "reason": "<one sentence naming the concrete evidence on each side, or what is missing>"}}
