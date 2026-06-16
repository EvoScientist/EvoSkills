You are auditing a single claimed evolution edge in a research-lineage
graph. The edge says: source paper (M) had a specific limitation that
target paper (N) addressed. Your job is to label the strength of textual
evidence for this edge.

--- Source paper (M) ---
({m_n}) {m_title}
Abstract: {m_abstract}
Discussion/Conclusion excerpt: {m_excerpt}

--- Target paper (N) ---
({n_n}) {n_title}
Abstract: {n_abstract}
Discussion/Conclusion excerpt: {n_excerpt}

--- Claimed gap ---
{gap_text}

--- Labels ---
Choose exactly one:

- SUPPORTED_BY_ABSTRACT — The source abstract explicitly states or
  clearly implies the limitation, AND the target abstract explicitly
  states or clearly implies the mechanism that addresses it.
- SUPPORTED_BY_SECTION  — The supporting evidence for either side
  (lack on M, or fix on N) is in the Discussion/Conclusion excerpt
  rather than the abstract, but the textual evidence is still concrete.
- INFERRED              — The claim is plausible but neither the abstract
  nor the excerpt explicitly attests to one or both halves of the
  source-lack/target-fix pair. Reasonable to leave on the graph as a
  weakly-supported edge, not as an authoritative claim.
- REJECT                — The abstracts or excerpts contradict the
  claimed gap (e.g., the source paper already does X, or the target
  paper does not actually address X). The edge should not be rendered.

--- Output ---
Output ONLY a JSON object with this exact shape (no code fences, no
prose before or after):

{{"verdict": "<one of the four labels>", "reason": "<one sentence
naming the concrete textual evidence on each side, or naming what
is missing>"}}
