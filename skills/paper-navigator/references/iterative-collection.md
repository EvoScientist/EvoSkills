# Iterative Collection (Branch 3 State Machine)

Read this only when the user wants **30+ papers** for a survey, ideation, or comprehensive corpus. For one-shot "find me papers about X", stay in SKILL.md Branch 2.

## Why a state machine

Collection is iterative: each search round informs the next (which gaps to fill, which seeds to expand). Without explicit states, agents either stop too early (under-collection) or loop forever (over-collection). The five states below have explicit exit conditions.

## States

```
S1 DECOMPOSE → S2 MULTI_SEARCH → S3 CITATION_EXPAND → S4 GAP_CHECK → S5 FINALIZE
                     ↑                                       │
                     └───── (gap found, targeted search) ────┘
```

**Setup:** Before entering S1, create a TodoWrite list with these 5 items so progress is visible to the user.

---

## S1 — DECOMPOSE

**Goal:** Identify 3-5 sub-topics within the user's query, generate 4-6 variant queries covering them.

**Why:** Different research communities use different terms for the same idea. A single query misses 50%+ of relevant work. Cross-community recall is the bottleneck.

**Action:**
1. List sub-topics along these axes (pick what fits):
   - Empirical vs. theoretical
   - Mechanism vs. condition
   - Method-keyword variants ("data pruning" / "data selection" / "data filtering")
   - Adjacent formulations ("in-context learning" / "few-shot")
2. Write 4-6 queries, at least one per sub-topic.

**Output:** `subtopics[]`, `queries[]` (stored in the TodoWrite todo or scratchpad).

**Exit:** ≥3 sub-topics named AND ≥4 queries written → S2.

**Example (topic: "data pruning for LLM pretraining"):**
- Subtopics: (a) selection methods, (b) quality metrics, (c) scaling effects
- Queries: `"data pruning pretraining LLM"`, `"data selection language model"`, `"training data curation quality"`, `"perplexity-based filtering pretraining"`

---

## S2 — MULTI_SEARCH

**Goal:** Run searches across ≥2 sources to build the initial pool (~60 candidates for ideation, ~20-30 for survey).

**Why:** S2 alone misses recent arXiv preprints; arXiv alone lacks citation signal. Combined recall is 1.5-2× single-source.

**Action:**
1. For each query from S1:
   - `scholar_search --query "<q>" --limit 20 --sort-by relevance`
   - If `S2_API_KEY` is set → parallel OK; if not → run sequentially (parallel S2 without key exhausts rate limit and falls back to lower-quality arXiv search; check with `echo $S2_API_KEY`).
2. In parallel with the above, run `arxiv_monitor --keywords "<v1,v2,v3>" --match-mode flexible --days 365` (arXiv has no parallelism constraint).
3. Deduplicate by normalized title and arXiv ID.
4. Filter by title + abstract relevance. Reject if abstract < 20 words or off-topic.

**Output:** `pool[]` of ~40-60 candidates with `{title, authors, year, venue, citations, id, abstract}`.

**Exit:** ≥3 strongly relevant seeds in pool → S3. If <3, run 1-2 more targeted queries before giving up.

---

## S3 — CITATION_EXPAND

**Goal:** Use the citation graph to find papers keyword search cannot reach. This is where iterative collection earns its cost.

**Why:** Co-citation is the single strongest signal for finding related work using different terminology. Forward citations find follow-ups. Backward finds foundations.

**Action:** Rank pool by **relevance to the user's query** (semantic match on title + abstract); use citation count only as a tiebreaker among comparably-relevant candidates. Pick top 3 as seeds, prefer seeds from *different sub-topics* (from S1) for diversity. Citation count alone selects locally-famous but topically-distant papers, which then bias co-citation traversal away from the actual query.

1. **Co-citation** on the most-relevant seed:
   `citation_traverse --paper-id <seed1> --direction co-citation --limit 15`
2. **Forward** on top 2 seeds:
   `citation_traverse --paper-id <seed1> --direction forward --limit 20`
   `citation_traverse --paper-id <seed2> --direction forward --limit 20`
3. **Backward** on 1-2 diverse seeds:
   `citation_traverse --paper-id <seedN> --direction backward --limit 20`
4. **Recommendations** with diverse seeds:
   `recommend --positive <seed1>,<seed2>,<seed3> --limit 15`

If no `S2_API_KEY`: space these calls ≥5s apart. Reduce `--limit` if 429 appears.

**Output:** `pool[]` expanded by 30-60 new papers, still deduplicated.

**Exit:** All 4 traversal calls completed (or rate-limited fallback used) → S4.

---

## S4 — GAP_CHECK

**Goal:** Audit coverage against the sub-topics from S1. Catch systematic blind spots.

**Why:** Even with citation expansion, an entire research perspective can be missing if all initial queries shared a bias. This step is lightweight (1-2 calls), high ROI.

**Action:**
1. Count papers in `pool[]` per sub-topic from S1.
2. For each sub-topic with **0-1 papers**, diagnose which gap type applies (see `search-principles.md` § "Gap Diagnosis") — usually "multi-source verification" (different community's term) or "dead end" (need a completely different angle).
3. Run one targeted `scholar_search` for the gap. If gap type is "dead end", switch keyword angle entirely; do NOT just try synonyms.
4. If the targeted search returns ≥2 new relevant papers → optionally one more `recommend` or `citation_traverse` on the new finds.

For cross-discipline gaps (e.g., topic spans CS and neuroscience), consult the terminology drift tables in `search-principles.md` to pick the right community's vocabulary.

**Output:** Final `pool[]`.

**Exit:** Every sub-topic from S1 has ≥2 papers, OR you ran one targeted search per gap and accepted the remainder → S5.

---

## S5 — FINALIZE

**Goal:** Apply quality filter, take top N, return.

**Action:**
1. Sort by relevance (semantic match to user goal, judged by title + abstract).
2. Apply profile-specific filter:

| Profile | Recency | Venue | Target N |
|---|---|---|---|
| **Survey** | include foundational older work | moderate (top venues preferred) | 30-80 |
| **Ideation** | strong bias toward 2020+ | top-tier only | 30-50 |
| **User-specified N** | match user request | match user signals | user-specified |

3. Output as a Paper Table (see SKILL.md output format).
4. Hand off to the next skill based on user intent:
   - Survey report → `research-survey`
   - Idea generation → `research-ideation`
   - User just wanted a list → done.

**Exit:** Table delivered. Skill terminates.

---

## Failure escape hatches

- **API completely down (429 + arXiv fallback also failing):** stop iteration, return what's in `pool[]` with a warning, suggest user retry later.
- **All searches return <3 results:** the topic may be too narrow or use non-standard terms. Drop to `references/disambiguation.md` and consider web search for blog posts / GitHub repos that reference papers.
- **Pool > 200 candidates after S3:** you over-searched. Tighten relevance filter, prefer top-venue + recent papers, advance to S5.

---

## TodoWrite integration

Before entering S1, create:
```
- [ ] S1: Decompose topic into 3-5 subtopics + 4-6 queries
- [ ] S2: Multi-source search (S2 + arXiv) and filter to ~40-60 candidates
- [ ] S3: Citation expansion (co-citation + forward + backward + recommend)
- [ ] S4: Gap check against subtopics
- [ ] S5: Finalize, output table, hand off
```

Mark each completed before advancing. This makes the state visible to the user and prevents accidentally skipping S4 (the most commonly-skipped step).
