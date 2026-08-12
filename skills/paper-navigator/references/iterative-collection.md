# Iterative Collection (ITERATIVE branch)

Read this only when the user wants **30+ papers** for a survey, ideation, or comprehensive corpus. For one-shot "find me papers about X", stay in SKILL.md LIST.

ITERATIVE shares the same flow shape as LIST — **Probe + up to 3 paper rounds (R2 breadth / R3 deepen / R4 close)**, the same RUBRIC / TRIAGE blocks, and the same Step 5 saturation gate. The differences are scale (≥30 papers), intent (caller is usually `research-survey` / `research-ideation`), and a heavier citation-expansion step. **Round cap is 3 paper rounds; there is no R5.**

## Why a state machine

Collection is iterative: each search round informs the next (which gaps to fill, which seeds to expand). Without explicit states, agents either stop too early (under-collection) or run extra rounds past saturation (over-collection). The four phases below map onto the SKILL.md rounds and have explicit exit conditions driven by the Step 5 gate.

## Phases → SKILL.md round mapping

```
Probe (prerequisite, 2 queries)
   │
   ▼
R2 BREADTH  ── (Step 5 gate: CONTINUE?) ──┐
   │                                      │
   ▼                                      │
R3 DEEPEN + CITATION EXPAND  ─ (gate) ──┤   loop back only when a
   │                                      │   [core] criterion or angle tag
   ▼                                      │   still has 0 papers (R4 fills it)
R4 CLOSE (final gap fill)
   │
   ▼
FINALIZE — rank, filter, hand off
```

**Setup:** Before Probe, create a TodoWrite list with these items so progress is visible to the user.

---

## Probe — prerequisite (NOT counted in the 3 rounds)

**Goal:** Establish a comprehensive understanding of the need and lift named entities / angle gaps before authoring R2 queries.

**Action (2 parallel queries):**
- `Q-broad` — canonical phrasing of the topic (angle: `general`)
- `Q-narrow` — a specific mechanism / sub-question / method (angle: tagged)

```bash
python scripts/scholar_search.py --query "<Q-broad>"  --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
python scripts/scholar_search.py --query "<Q-narrow>" --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
```

From Probe titles + tldrs, lift: recurring **named entities** (algorithm / benchmark / dataset / model names), **angle gaps** (Step-2 rubric tags not seen), and vocabulary from **adjacent communities**.

**Output:** `subtopics[]`, named-entity list, angle-gap list (stored in the TodoWrite todo or scratchpad).

**Exit:** 2 probe queries returned ≥3 sensible results → author RUBRIC and proceed to R2. If probe is empty, switch terminology or see `disambiguation.md`.

---

## R2 — BREADTH (mandatory, 2–3 parallel queries)

**Goal:** Identify 3-5 sub-topics within the user's query, run broad academic queries on the core object + canonical terms lifted from Probe. Build the initial pool (~60 candidates for ideation, ~20-30 for survey).

**Why:** Different research communities use different terms for the same idea. A single query misses 50%+ of relevant work. Cross-community recall is the bottleneck.

**Action:**
1. Write 2-3 queries covering different sub-topics / angles from the rubric. At least one query per sub-topic.
2. For each query:
   - `scholar_search --query "<q>" --limit 20 --sort-by relevance --output /tmp/pool.jsonl --append`
   - If `S2_API_KEY` is set → parallel OK; if not → run sequentially (parallel S2 without key exhausts rate limit and falls back to lower-quality arXiv search; check with `echo $S2_API_KEY`).
3. In parallel with the above, run `arxiv_monitor --keywords "<v1,v2,v3>" --match-mode flexible --days 365`. The scripts use a shared arXiv pacer, so concurrent agents will queue arXiv API requests instead of bursting.
4. Deduplicate by `paperId` first, then normalised title (`--output --append` auto-dedupes by `paperId`).
5. Filter by title + abstract relevance. Reject if abstract < 20 words or off-topic.

**Per-query rules (from SKILL.md Step 3):**
- 3-6 words, English academic terms.
- **Do NOT add `survey` / `review` / `tutorial` terms** — they bias toward review papers and crowd out the research papers the user wants. Only use them when the user explicitly asks for a survey/review.
- Bare entity names; no `paper` / `pdf` / `arxiv` / `original`.
- Split comparisons / multi-property; if short of 2-3 queries, fill with upper-topic or representative method.
- Time intent goes into `--year-min/max`, never year words in the query.
- Forbidden: `"..."`, `(...)`, `OR`, `AND`, `|`, `site:`, `filetype:`.
- No two queries in one round may share >60% of content tokens.

**Recency trigger:** If the user query contains 最新 / 近年 / 近期 / 近两年 / 前沿 / SOTA / latest / recent / state-of-the-art, set `--year-min` to last 2 years from R2 onward.

**Output:** `pool[]` of ~40-60 candidates with `{title, authors, year, venue, citations, id, abstract}`.

**Exit (Step 5 gate):** Triage with the TRIAGE block. Proceed to R3 if any [core] criterion has 0 All-core papers, any angle tag has 0 All-core/Partial, or a key claim rests on a single source. If every [core] criterion and angle tag is covered and no claim rests on a single source → STOP, go to FINALIZE.

**Example (topic: "data pruning for LLM pretraining"):**
- Subtopics: (a) selection methods, (b) quality metrics, (c) scaling effects
- R2 queries: `data pruning pretraining LLM`, `data selection language model`, `training data curation quality`

---

## R3 — DEEPEN + CITATION EXPAND (optional, when the Step 5 gate says CONTINUE)

**Goal:** Use targeted queries + the citation graph to fill the specific gaps Step 4 triage exposed. This is where iterative collection earns its cost.

**Why:** Co-citation is the single strongest signal for finding related work using different terminology. Forward citations find follow-ups. Backward finds foundations.

**Action — Part A: targeted deepen queries (2-3 parallel).** Driven by the Step 4 gap→strategy map (SKILL.md):
| Gap surfaced by triage | R3 strategy |
|---|---|
| Foundational work drowned by recent papers | `--year-max`, search the original mechanism / early terminology |
| User wants SOTA / frontier, or R2 skewed old | `--year-min` last 2 years |
| Thin single-source evidence | swap terminology / team / benchmark for multi-source corroboration |
| Incomplete A-vs-B comparison | separately fill A, B, and an upper-topic query (no `survey`/`review` terms) |
| Contradictory findings | verification query, prefer authoritative venue / high-cite / direct experiment |

**Action — Part B: citation expansion.** Rank pool by **relevance to the user's query** (semantic match on title + abstract); use citation count only as a tiebreaker among comparably-relevant candidates. Pick top 3 as seeds, prefer seeds from *different sub-topics* (from the rubric) for diversity. Citation count alone selects locally-famous but topically-distant papers, which then bias co-citation traversal away from the actual query.

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

**Exit (Step 5 gate):** Proceed to R4 if a [core] criterion or angle tag is still uncovered. Otherwise STOP, go to FINALIZE. If R2 returned 0 All-core across the board → re-decompose the rubric (see SKILL.md Step 5).

---

## R4 — CLOSE (optional, final gap fill)

**Goal:** Fill whatever key gap remains after R3 — a missing representative work, a strong baseline, a counter-example, or an uncovered sub-direction.

**Action (2-3 parallel queries):** One targeted `scholar_search` per remaining gap, diagnosed via the Step 4 gap→strategy map. For cross-discipline gaps (e.g., topic spans CS and neuroscience), consult the terminology drift tables in `search-principles.md` to pick the right community's vocabulary. If the gap is "dead end" (2 rounds returned nothing on that angle), switch keyword angle entirely; do NOT just try synonyms.

If a targeted search returns ≥2 new relevant papers, optionally one more `recommend` or `citation_traverse` on the new finds.

**Output:** Final `pool[]`.

**Exit:** This is the last round — the cap is 3 paper rounds (R2/R3/R4), no R5. After R4, go to FINALIZE regardless. If still not saturated, report which criteria / angle tags are under-covered in the FINALIZE output.

---

## FINALIZE

**Goal:** Apply quality filter, rank by relevance, take top N, return.

**Action:**
1. **Rank by relevance (model-judged, no numeric score).** Order papers by how directly each answers the user's question; All-core before Partial; [core] before [secondary]. This is a judgment call, not a formula — **do not compute a weighted_total**.
2. **Recency tie-break.** When the RUBRIC flagged a recency signal, break ties / near-ties in favor of the more recent paper (`year` DESC), applied after relevance.
3. Apply profile-specific filter:

| Profile | Recency | Venue | Target N |
|---|---|---|---|
| **Survey** | include foundational older work | moderate (top venues preferred) | 30-80 |
| **Ideation** | strong bias toward recent (via `--year-min`, not query words) | top-tier only | 30-50 |
| **User-specified N** | match user request | match user signals | user-specified |

4. Output as a ranked Paper Table (see SKILL.md output format). K is a soft cap (≤10 for ITERATIVE) — surplus relevant papers sit in an "Also relevant (not ranked)" list, never pad the ranked list.
5. Hand off to the next skill based on user intent:
   - Survey report → `research-survey`
   - Idea generation → `research-ideation`
   - User just wanted a list → done.

**Exit:** Table delivered. Skill terminates.

---

## Failure escape hatches

- **API completely down (429 + arXiv fallback also failing):** stop iteration, return what's in `pool[]` with a warning, suggest user retry later.
- **All searches return <3 results:** the topic may be too narrow or use non-standard terms. Drop to `references/disambiguation.md` and consider web search for blog posts / GitHub repos that reference papers.
- **Pool > 200 candidates after R3:** you over-searched. Tighten relevance filter, prefer top-venue + recent papers, advance to FINALIZE.

---

## TodoWrite integration

Before Probe, create:
```
- [ ] Probe: 2 queries (Q-broad + Q-narrow), lift named entities + angle gaps
- [ ] R2 Breadth: 2-3 queries across sub-topics, build pool to ~40-60 candidates
- [ ] R3 Deepen + Citation expand: targeted gap-fill + co-citation/forward/backward/recommend
- [ ] R4 Close: final gap fill (only if Step 5 gate says CONTINUE)
- [ ] Finalize: rank by relevance, filter, output table, hand off
```

Mark each completed before advancing. This makes the state visible to the user and prevents accidentally skipping the saturation gate (the most commonly-skipped step).
