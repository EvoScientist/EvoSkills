---
name: paper-navigator
description: "Find and read academic papers (S2 + arXiv). Disambiguate ambiguous queries, search by keyword + citation graph + recommendations + snippets, judge by author-graded rubric, and read with L1/L2/L3 strategy. Trigger phrases: find papers, search papers, related work, citation analysis, recent advances, read this paper, baseline with code. Do NOT use for: survey reports (research-survey), idea generation (research-ideation), Related Work sections (paper-writing)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '3.2.1'
  tags: [core, research, literature, papers, search, rubric]
---

# Paper Navigator

Find and read academic papers. Route by **intent**, judge by **author-graded rubric**.

```
        User
         │
         ▼
   ┌── Router ──┐
   │            │
   ▼            ▼
 POINT      LIST/ITERATIVE
(1 paper)   (rubric + 2–3 rounds)
```

The agent does relevance judgment — no LLM-as-judge is called. You author the rubric, you triage each paper, you sort.

## Setup

Scripts at `skills/paper-navigator/scripts/`. Run via `python skills/paper-navigator/scripts/<name>.py`.

arXiv access (`arxiv_monitor`, `scholar_search` fallback) uses the DeepXiv SDK: `pip install deepxiv-sdk`, then `deepxiv token` once to provision a **free** API token (saved to `~/.env`). The skill reads the token from `DEEPXIV_API_TOKEN`/`DEEPXIV_TOKEN` in the environment, or from `./.env` / `~/.env`.

| Env var | Used by | Notes |
|---|---|---|
| `S2_API_KEY` | All S2 scripts | Without it: `scholar_search` falls back to arXiv (via DeepXiv); `citation_traverse` / `recommend` / `snippet_search` are disabled |
| `DEEPXIV_API_TOKEN` | `arxiv_monitor`, `scholar_search` fallback | Get a free token: `deepxiv token` (writes `~/.env`). Also read from `DEEPXIV_TOKEN` and `./.env`/`~/.env`. ~10,000 req/day |
| `JINA_API_KEY` | `fetch_paper` | Free tier works without key |
| `GITHUB_TOKEN` | `github_search`, `find_code` | Higher rate limits |
| `PAPER_NAV_PAPERS_DIR` | `fetch_paper` full text | No default — set or pass `--metadata-only` |

Full env-var list: `references/env-vars.md`.

---

## Five Red Lines (always)

1. **Track history.** Don't re-run a query you already ran. Empty result → change angle, not synonyms.
2. **Search a gap, not a vibe.** Every query maps to one missing piece of information. No stacked-keyword bags.
3. **One query = one concept.** Split comparisons (`A vs B`), multi-property asks, and multi-year spans into separate calls.
4. **Never hallucinate.** Every fact (title, author, year, citation count, content) comes from a tool result.
5. **Quote-or-zero.** When you claim a paper meets a criterion, quote a ≤80-char span from its abstract / tldr / snippet. No quote → that criterion scores 0.

---

## Router

| Branch | User signal | Cadence | Output |
|---|---|---|---|
| **POINT** | Title quoted, URL, arXiv/DOI/PMID/S2 ID, "read this paper" | 1 call | Paper Card |
| **LIST** (default) | "find papers about X", "is there a paper that …?", "papers satisfying A and B" | 2 rounds + optional patch | Shortlist with per-criterion evidence |
| **ITERATIVE** | "survey of X", "30+ papers on Y", called from `research-survey` / `research-ideation` | up to 3 rounds, breadth-first | Ranked table (hand off to research-survey for the report) |

**Default to LIST when unsure.** Don't add `survey` / `review` to LIST queries — it down-ranks the canonical originals the user wants.

Ambiguous query (project nickname, codename, single capitalized word with zero hits) → run `scholar_search` exact + web/GitHub search first to resolve identifiers, then re-route.

---

## POINT branch (known paper)

| Input | Command | Output |
|---|---|---|
| URL | `python scripts/fetch_paper.py --url <URL>` | Paper Card + reading notes (see `references/reading-strategy.md` for L1/L2/L3) |
| Title quoted | `python scripts/match_paper_by_title.py --title "<title>"` (add `--fallback-search` for typos) | Paper Card |
| Bare ID (arXiv / DOI / S2 / CorpusId) | `python scripts/fetch_paper.py --paper-id <ID> --metadata-only` | Paper Card |

**Paper Card:**

```
📄 **<Title>**
Authors: <First Author> et al. | Year: <Y> | Venue: <V>
Citations: <N> | ID: <ArXiv:xxxx.xxxxx> | DOI: <...>
TLDR: <one sentence>
```

Stop here. Do not chain to citation expansion unless asked.

---

## LIST / ITERATIVE branch — 6 steps

### Step 1: Parse intent

State in one sentence: the **research object** (specific technique / concept) and the **constraints** (domain, task, recency, exclusions). Confirm the router branch.

### Step 2: Author the RUBRIC (via `think_tool`)

Emit a structured block before any search. It persists across rounds and every later step references it.

```
RUBRIC for "<user query verbatim>"
Branch: LIST | ITERATIVE
Criteria (2–4, atomic, weights sum to ≈1.0):
  C1 [w=0.45] <what the paper MUST do/be — one sentence>
  C2 [w=0.35] <...>
  C3 [w=0.20] <...>
Named entities to preserve verbatim: [<ent1>, <ent2>, ...]
Angle tags (3–5 sub-topic axes): [<tag1>, <tag2>, <tag3>]
Disqualifiers: [<auto-reject if abstract shows this>]
```

Rules:
- **Criteria** atomic (one condition each), weighted, non-redundant.
- **Named entities** = proper-noun / technical-term anchors from the user's query. Every entity appears verbatim in ≥1 query across Rounds 1+2.
- **Angle tags** = sub-topic axes (`method`, `task`, `dataset`, `evaluation`, `domain`, …). No two queries in the same round share a tag.
- **Disqualifiers** = "specifically X, **not** Y" exclusions. Tripping a disqualifier scores 0 on the related criterion.

For ITERATIVE, criteria can be lighter (e.g. `covers topic` + `is survey / canonical`); disqualifiers may be empty.

### Step 3: Search — Probe-then-Refine

**Do not author all queries upfront.** Round 1 surfaces named entities Round 2 needs.

**Round 1 — Probe** (2 parallel queries):
- `Q-broad` — canonical phrasing of the topic (angle: `general`)
- `Q-narrow` — a specific mechanism / sub-question / method (angle: tagged)

```bash
python scripts/scholar_search.py --query "<Q-broad>"  --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
python scripts/scholar_search.py --query "<Q-narrow>" --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
```

`--output --append` auto-dedupes by `paperId` across rounds (built into the script), so a paper found by two queries is written once. Read `/tmp/pool.jsonl` to inspect (Step 4 triage).

From Round 1 titles + tldrs, lift:
- recurring **named entities** (algorithm / benchmark / dataset / model names),
- **angle gaps** (Step-2 tags not seen),
- vocabulary from **adjacent communities**.

**Round 2 — Refine** (2–3 parallel queries):

| Tier | Count | Shape |
|---|---|---|
| Method / mechanism | 1–2 | Sub-mechanism on an uncovered angle tag |
| Named-entity | 1 | Entity verbatim from Round 1 titles + a modifier. Drop this tier if Round 1 surfaced no entities. |

```bash
python scripts/scholar_search.py --query "<refine 1: method, angle X>" --limit 15 --output /tmp/pool.jsonl --append
python scripts/scholar_search.py --query "<refine 2: method, angle Y>" --limit 15 --output /tmp/pool.jsonl --append
python scripts/scholar_search.py --query "<refine 3: lifted entity>"   --limit 15 --output /tmp/pool.jsonl --append
```

**Round 3 — Patch** (only if Step 5 gate says CONTINUE). One targeted query on the remaining gap.

**Per-query rules:**
- 4–7 words typical (up to 9 OK); <3 over-recalls, >9 dilutes ranking.
- English only.
- Bare entity names, no `paper` / `original` / `pdf`.
- Forbidden: `"…"`, `(..)`, `OR`, `AND`, `|`, `site:`, `filetype:`.
- No two queries in one round may share >60% of content tokens (after stop-words).

**Without `S2_API_KEY`:** swap `scholar_search` for `arxiv_monitor --keywords "<variant>" --match-mode flexible --days 3650`.

**Citation expansion** (ITERATIVE, or LIST after ≥3 strong seeds):
```bash
python scripts/citation_traverse.py --paper-id <SEED> --direction co-citation --limit 15 --output /tmp/pool.jsonl --append
python scripts/citation_traverse.py --paper-id <SEED> --direction forward --limit 20 --min-citations 20 --year-min 2022 --output /tmp/pool.jsonl --append
python scripts/recommend.py --positive <SEED1>,<SEED2> --limit 15 --output /tmp/pool.jsonl --append
```

### Step 4: Triage — PERFECT / GOOD / WEAK / IRREL

After every round, classify each new paper. Emit a `think_tool` block:

```
TRIAGE round=<n>  query="<q>"
  PERFECT (k): <paperId> "<title-≤60>" Y=<year> · [C1✓ C2✓ C3✓]
                evidence C1: "<≤80-char quote>"
                evidence C2: "<≤80-char quote>"
                evidence C3: "<≤80-char quote>"
  GOOD    (k): <paperId> "<title>" Y=<year> · [C1✓ C2~ C3✗]
                evidence C1: "<quote>"
  WEAK    (k): <paperId> "<title>" Y=<year> · [C1~ C2✗ C3✗]
  IRREL   (k): <paperId> "<title>"
```

| Tier | Required mask | Quotes |
|---|---|---|
| `PERFECT` | every high-weight criterion `✓`, no `✗` anywhere | one ≤80-char quote per criterion |
| `GOOD` | every high-weight (`w ≥ 0.3`) at least `~`, no `✗` on any high-weight | one quote per `✓` criterion |
| `WEAK` | one high-weight `✗` or only low-weight hits | none |
| `IRREL` | misses every high-weight or trips a disqualifier | none — drop from later rounds |

`✓` = abstract/tldr clearly supports. `~` = partial/inferable. `✗` = no support or contradicts.

Rules:
1. **Dedup across rounds** by `paperId` first, then normalised title. Keep the stronger mask.
2. **Disqualifier check** beats all other matches → IRREL.
3. **Re-diagnose gaps:** list any criterion with 0 PERFECT candidates → that's the next refine target.
4. **No fabrication:** missing abstract → mark `~`, do not infer from training data.

**Snippet upgrade** for borderline papers (abstract silent on a criterion): batch-fetch real body text:
```bash
python scripts/snippet_search.py --query "<criterion phrase>" \
  --paper-ids "CorpusId:1,CorpusId:2,..." --limit 50
```

### Step 5: Saturation Gate

Read the across-round pool from Step 4, apply the table, take the action — no other input.

**LIST branch after Round 1:**

| Pool | Action |
|---|---|
| ≥1 PERFECT | **STOP** → Step 6 |
| 0 PERFECT, ≥2 GOOD | **CONTINUE → Round 2** (lift entities from Round 1) |
| 0 PERFECT, <2 GOOD | **CONTINUE → Round 2**, plus ≥1 query on a *new* angle (rubric may be off) |

**LIST branch after Round 2:**

| Pool | Action |
|---|---|
| ≥1 new PERFECT, all high-weight criteria covered | **STOP** → Step 6 |
| ≥1 new PERFECT, but a high-weight criterion still has 0 PERFECT | **CONTINUE → Round 3 patch** |
| 0 new PERFECT+GOOD *and* Round 1 had 0 PERFECT | **STOP and re-decompose** — criteria are wrong. Report best Secondary candidate(s) + ask user to relax a criterion. |
| Empty recall on every Round 2 query | **STOP** — topic not in corpus or entities are wrong |

**ITERATIVE branch:** keep searching while any angle tag has 0 PERFECT+GOOD or any key claim has only one source. Stop when every angle tag has ≥2 PERFECT+GOOD.

**Round caps:** LIST 2+1, ITERATIVE 3, POINT 1. If still not saturated at the cap, go to Step 6 and report which criteria / angle tags were not covered.

**The gate is mechanical** — do not skip rounds because "the results look right".

### Step 6: Rerank and Output

**Gather:** every PERFECT and GOOD from across all rounds (dedup by `paperId`, keep stronger mask). Add WEAK only if PERFECT+GOOD < 3 (fallback fill). Drop IRREL.

**Score** each criterion 0 / 0.25 / 0.5 / 0.75 / 1.0:

| Score | Meaning |
|---|---|
| `1.0` | quote directly satisfies the criterion |
| `0.75` | strong implication (one inference from quote) |
| `0.5` | partial — topic match, not the specific condition |
| `0.25` | adjacent — same field, off-criterion |
| `0` | no quoted evidence, contradicts, or trips a disqualifier |

**Compute** `weighted_total = Σ (criterion_score × criterion_weight)` ∈ [0, 1]. Sort DESC by `weighted_total`, tie-break by `citationCount` DESC → `year` DESC.

**Tier the output:**

| Tier | `weighted_total` | Use |
|---|---|---|
| Primary | ≥ 0.7 | The answer. Eligible for top-K. |
| Secondary | 0.5 – 0.7 | "May also be relevant"; never promoted to Primary. |
| Drop | < 0.5 | Exclude. |

**Rank-1 quality bar.** For single-recommendation queries ("is there a paper that …?", "recommend a paper", "what's the canonical X") the bolded top-1 must have `weighted_total ≥ 0.85` AND every high-weight criterion (w ≥ 0.3) must score `≥ 0.75`. Rank 1 carries disproportionate weight in user perception and in downstream evaluation; promoting a 0.71 Primary to top-1 reads as a confident wrong answer. If no candidate clears the bar, lead with "No fully-matching paper found" and present the strongest near-miss honestly with its per-criterion gaps.

If Primary is empty after the round cap, report "no fully-matching paper found", list strongest Secondary candidates + their per-criterion gaps, stop.

**K to return:**

| Question shape | K |
|---|---|
| "Exactly N papers" | N (pad with Secondary only if Primary < N) |
| "Is there a paper that …?" / "Recommend a paper" | 1–2 (bold top-1) |
| "Find papers about …" | 3–5 |
| "Survey of …" / ITERATIVE | up to 10 + 1–2 surveys |

**Output formats:**

LIST (shortlist with evidence):
```
**Primary answer (weighted_total = 0.92):**
- **<paperId>** "<Title>" — <Authors> et al., <Year>, <Venue>. <URL>
  - C1 (0.45): "<quote>" → 1.0
  - C2 (0.35): "<quote>" → 1.0
  - C3 (0.20): "<quote>" → 0.5

**May also be relevant:**
- <paperId> "<Title>" — total 0.62; missed C2 (no evidence in abstract).
```

ITERATIVE (ranked table):
```
| # | Title | Authors | Year | Venue | Link | Score |
|---|-------|---------|------|-------|------|-------|
| 1 | …    | … et al. | 2024 | NeurIPS | <URL> | 0.88 |
```

POINT: Paper Card (above).

**Pre-output checklist (mandatory).** Before emitting the answer, verify each box. The dominant failure mode of this skill is skipping the rerank and emitting the last round's top-K verbatim — this checklist exists to make that impossible.

- [ ] **Pool gathered** from every Step-5 triage block across all rounds, deduped by `paperId` (keep the stronger mask), IRREL excluded.
- [ ] **weighted_total computed** for every Primary and Secondary candidate — the actual `Σ (criterion_score × criterion_weight)`, not estimated, not eyeballed.
- [ ] **Sorted** DESC by `weighted_total` → `citationCount` → `year`.
- [ ] **Rank-1 clears the bar** (`≥ 0.85` total AND every high-weight criterion `≥ 0.75`) for single-recommendation queries — or you've reported "No fully-matching paper found" instead of fronting a weak candidate.
- [ ] **Every Primary paper has ≥1 evidence quote per high-weight criterion** (quote-or-zero rule, Red Line 5).

If any box is unchecked, return to Step 6 — do not output.

---

## Tool Cheat Sheet

| Need | Script | Notes |
|---|---|---|
| Keyword search | `scholar_search.py` | S2 → arXiv fallback on missing key / 429 |
| Title → record | `match_paper_by_title.py` | S2 exact-match; `--fallback-search` for typos |
| Citation graph | `citation_traverse.py` | `--direction forward/backward/co-citation`; `--min-citations`; `--year-min/max`; `--smart-sort`; `--enrich` |
| Similar papers | `recommend.py` | seed-based; `--per-seed` for diverse seeds |
| Author papers | `author_search.py` | `--sort-by year/citations` |
| New arXiv | `arxiv_monitor.py` | `--categories cs.CL` or `--keywords "x,y" --match-mode flexible` |
| Trending | `trending.py` | citation velocity |
| Body-text snippets | `snippet_search.py` | `--paper-ids c1,c2,c3 --limit 50` (1 call, not N) |
| Fetch full text | `fetch_paper.py` | Saves to `$PAPER_NAV_PAPERS_DIR/<id>.md`; stdout truncated to 2000 chars |
| Code repo (known paper) | `find_code.py --arxiv-id <ID>` | Official repo lookup |
| Code repo (unpublished) | `github_search.py` | When no arXiv ID exists |
| HF leaderboard / SOTA | `sota.py` | sorted by downloads |
| HF datasets | `dataset_search.py` | Query short-name (`imdb`, `sst2`), not task description |
| Saturation gate (optional) | `saturation.py` | JSONL log of per-round yields; `estimate` returns STOP/CONTINUE |

All discovery scripts: `--limit N`, `--json`, `--output FILE`, `--append`; accept S2 / arXiv / DOI / CorpusId IDs. `--output --append` auto-dedupes by `paperId` across rounds (within-batch + cross-file), so the pool stays clean.

---

## Rate limits

| API | Without key | With key |
|---|---|---|
| Semantic Scholar | ~1 req / 3s, no parallel | 100 req/min, parallel OK |
| arXiv | 1 req / 3s (courtesy) | N/A |
| GitHub | 10 req/min | 5,000 req/hr |
| HuggingFace | 500 req / 300s | Higher with `HF_TOKEN` |

Global S2 pacer + circuit breaker (5 failures → 60s cooldown). Retries: 3s / 6s / 12s / 24s / 48s.

Without `S2_API_KEY`: use `scholar_search` (arXiv fallback) + `arxiv_monitor`. Skip `citation_traverse` / `recommend` / `snippet_search` — they're S2-only; do not retry.

---

## References

| File | Read when |
|---|---|
| `references/env-vars.md` | Setting environment variables |
| `references/search-principles.md` | Per-query rules, gap diagnosis, rate-limit recovery |
| `references/disambiguation.md` | Query is a project nickname / codename |
| `references/reading-strategy.md` | L1 / L2 / L3 reading framework |
| `references/api-reference.md` | S2 / arXiv / Jina / HF / GitHub endpoint details |
| `references/arxiv-categories.md` | arXiv category codes |
| `references/output-formats.md` | Baseline / Disambiguation / Reading-Notes / Citation-Graph templates |

References are self-contained. Don't chain between them — return here to re-route.

---

## Hand off to

| Goal | Skill |
|---|---|
| Survey report | `research-survey` |
| Idea generation | `research-ideation` |
| Related Work section | `paper-writing` |
| Baseline + experiment | `experiment-pipeline` |
