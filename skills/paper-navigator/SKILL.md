---
name: paper-navigator
description: "Find, read, download, and locally cache academic papers. Disambiguate ambiguous queries, discover via keyword search / citation traversal / recommendations / arXiv monitoring / trending / GitHub search, evaluate (TLDR, citations, code, SOTA), read using a 3-level strategy, and save PDFs to a local library for offline reuse. Use when finding a specific paper, listing papers on a topic, tracking recent advances, finding a baseline with code, reading or downloading a paper by URL, searching the local PDF library, or collecting a corpus for survey/ideation. Trigger phrases include: find/search papers, related work, citation analysis, latest research, download paper, save paper, my local library. Do NOT use for generating survey reports (use research-survey), generating research ideas (use research-ideation), writing a Related Work section (use paper-writing), comparing/ranking ideas (use research-ideation), or planning paper structure (use paper-planning)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '2.4.5'
  tags: [core, research, search, literature, download, local-library]
---

# Paper Navigator

Find and read academic papers. The skill routes by **intent** into three branches; cost should match intent.

## Core Principles (apply to every branch)

These four rules override branch-specific instructions when they conflict — they exist because every paper-search failure mode reduces to one of them.

1. **Track history** — before each new search, recall queries already run and what they returned. Identical or near-identical queries waste budget; if a query returned nothing, change angle, not synonyms.
2. **Search what's missing, not what you know** — every query must map to an explicit information gap (see `references/search-principles.md` § "Gap Diagnosis"). Stacking broad terms ("deep learning survey trends future") dilutes the relevance signal and returns noise.
3. **Atomize multi-concept queries** — one query = one gap. Comparisons ("A vs B"), multi-property requests (mechanism + application), or year-spanning asks must be split into independent queries. The search engine cannot weigh two intents at once.
4. **Never hallucinate** — every factual claim (title, author, year, citation count) must come from a tool result. Do not fill in from training data, even for famous papers — verify first.

For the **query-design rules** (3-6 words, English-only, no formal words, banned symbols) and **domain terminology tables** that make these principles operational, see `references/search-principles.md`.

```
       User request
            │
            ▼
   ┌─── Intent Router ───┐
   │                     │
   ▼          ▼          ▼
 POINT      LIST    ITERATIVE
(1 paper) (N≤~10)  (corpus, state machine)
   │          │          │
   ▼          ▼          ▼
Paper Card  Paper Table  references/iterative-collection.md
```

## Intent Router

| User signal | Branch | Typical cost | Section |
|---|---|---|---|
| Title / URL / arXiv ID / "read this paper" / "what is paper X" | **POINT** | 1 call | [Branch 1](#branch-1--point) |
| "find papers about X" / "papers on Y" / author+year / "what's trending" / "baseline for W" | **LIST** | 1-3 calls | [Branch 2](#branch-2--list) |
| "survey X" / "30+ papers on Y" / called from `research-survey` or `research-ideation` | **ITERATIVE** | state machine | [Branch 3](#branch-3--iterative) |

**Default to LIST when unsure.** Offer to escalate to ITERATIVE if results look thin. Simple "find papers about X" should never trigger iterative collection — that wastes API budget and user time.

If the query is ambiguous (project nickname, codename, single capitalized word with zero hits) → read `references/disambiguation.md` first, then re-enter the router.

---

## Branch 0 — LOCAL-FIRST (run before any external search)

Why this exists: repeat queries on already-seen papers should not burn API quota. If the user has a local library at `$PAPERS_DIR` (default `~/papers/`), a previous download already has the answer.

**When to run**: any POINT or LIST query, before the external scripts. Skip for ITERATIVE (a fresh corpus collection should not be biased by what happens to be downloaded).

**How**: `python scripts/library_search.py --query "<topic or title>"` (or `--arxiv-id <ID>` for direct lookup). Returns a Paper Table from `$PAPERS_DIR/index.json`; zero network.

**Decision**:
- **Cache hit** that matches user intent → return the Paper Card / Paper Table, mark each row's source as "(local)", and stop. Mention the local path so the user can open the PDF.
- **Cache miss or no library yet** → proceed to POINT / LIST routing as normal.
- **Partial hit** (1 paper of 5 requested found locally) → use the local one + search externally for the rest; blend in output.

---

## Branch 1 — POINT

User has a specific paper in mind, or wants to read a known paper.

**Steps:**
1. **URL given** → `python scripts/fetch_paper.py --url <URL>`. Choose reading depth (L1/L2/L3, see `references/reading-strategy.md`). Output a reading note using `assets/paper-summary-template.md`. Save to `artifacts/paper-notes/<paper-id>.md`.
2. **Title or arXiv ID** → `python scripts/scholar_search.py --query "<title>" --limit 3` → return top hit as **Paper Card**.
3. **Ambiguous name** → `references/disambiguation.md`.

**Output — Paper Card:**
```
📄 **<Title>**
Authors: <First Author> et al. | Year: <Y> | Venue: <V>
Citations: <N> | ID: <arXiv:xxxx.xxxxx> | DOI: <...>
TLDR: <one sentence>
```

**Stop here.** Do not chain to citation expansion unless the user explicitly asks "what else should I read".

**Optional persist** — if the user says "download" / "save offline" / "keep this", run `python scripts/download_paper.py --paper-id <ID>` after the card. Saves PDF + metadata to `$PAPERS_DIR`.

---

## Branch 2 — LIST

User wants a manageable list (≤~10) on a topic. One search round, no iterative loop.

**Steps:**
1. **Light decomposition** — name 2-3 sub-angles of the topic (saves you from a single-keyword blind spot, no need for full reformulation).
2. **Search** — typically 1-2 calls:
   - `python scripts/scholar_search.py --query "<topic>" --limit 15 --sort-by relevance` (start here)
   - Only swap to `--sort-by citations` when the user explicitly asks for *seminal / foundational / most-cited / canonical* work. Citation order on a 15-paper window crowds out actually-on-topic papers with older popular ones — especially harmful for recent or niche topics.
   - Optional: `python scripts/arxiv_monitor.py --keywords "<topic variants>" --match-mode flexible --days 365` (broader recall on preprints)
3. **Filter** by title + abstract relevance; deduplicate by title and arXiv ID.
4. **Output — Paper Table:**
   ```
   | # | Title | Authors | Year | Venue | Citations | ID |
   |---|-------|---------|------|-------|-----------|----|
   ```

**Variants of LIST:**
- *Metadata search* (author + year): `python scripts/author_search.py --name "<A>" --papers --sort-by year` then filter by year/venue.
- *Track recent advances*: `python scripts/arxiv_monitor.py --categories cs.CL --days 7` or `python scripts/trending.py --query "<topic>" --period 90`.
- *Baseline with code*: top result + `python scripts/find_code.py` + `python scripts/sota.py --task <task>` → output as Baseline Recommendation (`references/output-formats.md`).

**Gap-driven follow-up (when first round is insufficient).** If step 2 returned < N relevant papers or the user says "find more / something different", do **one** focused follow-up query targeting the specific missing angle. Pick from `references/search-principles.md` § "Gap Diagnosis":
- Returned 0 results → change keyword angle (not synonyms)
- Returned single-source claims → multi-source verification query (different community's term)
- Returned outdated work → add year anchor (`2024`, `2025`)
- Returned only one sub-topic → search the missing sub-topic explicitly

One follow-up call only. If still insufficient, propose Branch 3 escalation to the user — don't loop silently.

**Escalation triggers** — switch to Branch 3 ITERATIVE when:
- User asks for "comprehensive coverage", "survey", "everything on X"
- User requests >15 papers
- This skill is invoked from `research-survey` or `research-ideation`

---

## Branch 3 — ITERATIVE

Multi-round collection with explicit state machine. **Read `references/iterative-collection.md` and execute its 5 states (S1 DECOMPOSE → S2 MULTI_SEARCH → S3 CITATION_EXPAND → S4 GAP_CHECK → S5 FINALIZE).** Use TodoWrite to track state progress.

This is the only branch where citation expansion and gap check are required — they are too expensive for Branch 2.

Profile selection (sets recency bias, venue strictness, target N):
- **Survey** — 30-80 papers, include foundational older work, top venues preferred
- **Ideation** — 30-50 papers, 2020+ strong bias, top venues only
- **User-specified N** — match user's number, apply nearest profile's quality

After collection completes, hand off:
| User goal | Next skill |
|---|---|
| Survey report | `research-survey` |
| Idea generation | `research-ideation` |
| Quick summary table | `python scripts/literature_report.py --paper-ids <ids> --intent quick_scan` |
| Related Work draft | `paper-writing` |
| Baseline + experiment | `experiment-pipeline` |
| Offline corpus (download all) | Write IDs to `artifacts/collected_ids.txt`, then `python scripts/download_paper.py --bulk-file artifacts/collected_ids.txt` — saves PDFs and grows the local library for future Branch 0 hits. |

---

## Tool Cheat Sheet

| Need | Script | Notes |
|---|---|---|
| Keyword search | `scholar_search.py` | S2 with arXiv fallback on 429 |
| New arXiv | `arxiv_monitor.py` | `--categories` or `--keywords` |
| Citation graph | `citation_traverse.py` | `--direction forward/backward/co-citation` |
| Similar papers | `recommend.py` | seed-based, optionally with negatives |
| Author papers | `author_search.py` | filter by year/venue |
| Trending | `trending.py` | by citation velocity |
| **Canonical repo (from paper)** | `find_code.py --arxiv-id <ID>` | **PREFERRED** for finding the official repo of a known paper. Uses paperswithcode's "Official" tag. |
| Unpublished / industry repo | `github_search.py` | Use when no arXiv ID exists, or finding new tools/datasets. Note: keyword search may rank derivative repos above the original when derivatives have more stars (e.g. "mamba" returns Vim/VMamba ahead of state-spaces/mamba) — if this happens, get the arXiv ID and switch to `find_code.py`. |
| Fetch full text | `fetch_paper.py` | URL/ID → markdown |
| SOTA | `sota.py` | HuggingFace leaderboard, sorted by downloads — reliable |
| **Canonical dataset** | `dataset_search.py --query "<short-name>"` | Query by known short-name (`imdb`, `sst2`, `mnli`, `squad`) — NOT by task description. Task-description queries (e.g. "sentiment analysis") return mostly small community uploads and miss IMDB/SST-2/etc. even with `--sort downloads`. If you don't know the short-name, check paperswithcode/Datasets first. |
| Quick report | `literature_report.py` | brief table of N papers |
| **Local library search** | `library_search.py --query "..."` (or `--arxiv-id <ID>`) | **Branch 0** entry point. Reads `$PAPERS_DIR/index.json`. Zero network. |
| **Download PDF** | `download_paper.py --arxiv-id <ID>` (or `--paper-id`/`--bulk`/`--bulk-file`) | Saves to `$PAPERS_DIR/<id>/paper.pdf` + `metadata.json` + index update. Rejects <10KB blobs; 1s rate limit. |
| **Read with cache** | `fetch_paper.py --cache --paper-id <ID>` | Cache hit → 0 network; miss → fetch via Jina + persist `content.md`. |

All scripts output Markdown to stdout, accept `--json` and `--limit`. Paper IDs accepted in S2/arXiv/DOI form, including **bare arXiv** (`1706.03762`, since v2.4.0).

**Canonical vs. recent — choose the right tool:**
- *Recent / trending work*: `recommend.py`, `trending.py`, `arxiv_monitor.py`, `citation_traverse.py --direction forward` (default sort by recency).
- *Canonical / high-citation work*: `scholar_search.py --sort-by citations`, `citation_traverse.py --direction backward` (references), or `--direction co-citation`. S2's forward-citation and recommend endpoints surface **newest-first** results — for foundational seeds (≥10k citations) they will return only recent 0-cite preprints. Use scholar_search by topic when you want BERT/GPT-style impactful descendants.

**Fallback query budget**: when a tool's warning suggests a `scholar_search` fallback, run at most **3-4 well-chosen queries** total — each targeting a *different* sub-topic of the seed (e.g., for Transformer: one for "language model architecture", one for "vision transformer", one for "efficient attention"). More queries past 4 add wall-clock without new canonical results; merge and rank what you have instead.

**Setup:** Scripts at `skills/paper-navigator/scripts/`. Optional env vars for higher rate limits: `S2_API_KEY`, `JINA_API_KEY`, `GITHUB_TOKEN`, `HF_TOKEN`.

**Rate limits & query design** — when hit by 429 or designing multi-query searches, read `references/search-principles.md`. Built-in retries use 3s/6s/12s/24s/48s exponential backoff. A global S2 pacer enforces a 3s interval when no API key is set; a cross-process arXiv pacer enforces 3s between arXiv API request starts across concurrent agents.

### No-S2-key Operating Mode (`$S2_API_KEY` unset)

Why this section exists: without an S2 API key, each S2 call costs ~10s after exponential backoff vs ~1.5s with a key. Heavy S2-dependent workflows become unusable.

**Detection**: `scholar_search.py` auto-detects missing `$S2_API_KEY` and routes to arXiv API directly (skipping the 10s+ S2 backoff). It prints `ℹ️ No S2_API_KEY detected — using arXiv as primary search...` to stderr.

**Trade-offs in no-key mode**:
| What you lose | What still works |
|---|---|
| S2 TLDR field; citation counts in search results | All arxiv-indexed papers; arXiv metadata |
| `citation_traverse.py`, `recommend.py`, `trending.py`, `author_search.py` (all S2-bound) | `arxiv_monitor.py`, `github_search.py`, `sota.py`, `dataset_search.py`, `library_search.py`, `download_paper.py` (uses arxiv.org/pdf directly) |
| Forward/backward citations | Keyword search, recency filter, code search, HF lookup |

**Routing under no-key**:
- POINT / LIST → use `scholar_search` (auto-arxiv) + `arxiv_monitor` — both work without S2
- Branch 0 LOCAL-FIRST → unchanged (offline)
- Branch 3 ITERATIVE → restrict to `scholar_search` + `arxiv_monitor`; skip citation_traverse and recommend; tell the user S2 features unavailable
- Download / cache → unchanged (`download_paper.py` uses arxiv.org/pdf, not S2)

**When you must use citation/recommend without a key**: do at most 1-2 calls (each costs 10+s with retries), space them, and accept that fallback to arxiv may still trigger.

**Surface the S2 key registration tip to the user**: when `scholar_search.py` or `fetch_paper.py` print the no-key tip on stderr (look for `💡 Tip: ... register a FREE Semantic Scholar API key`), include it (or paraphrase) in your final response to the user. Show it **once** per session, not after every call. This is the only legitimate way a user discovers they should register a key for better search quality.

---

## Output Formats

- **Paper Card** (Branch 1) — defined above
- **Paper Table** (Branch 2/3) — defined above
- **Baseline Recommendation / Disambiguation Report / Reading Notes / Citation Graph** — see `references/output-formats.md`

---

## Reference Files

| File | Read when |
|---|---|
| `references/search-principles.md` | Designing queries (3-6 word rule, atomic split, banned syntax); diagnosing the information gap; cross-discipline query (CS↔neuroscience etc.); hit a rate limit; need to broaden after low recall |
| `references/iterative-collection.md` | Branch 3 (survey / ideation / large N) — contains the 5-state machine |
| `references/disambiguation.md` | Query looks like a project nickname or codename |
| `references/output-formats.md` | Need baseline / disambiguation / reading-note / mermaid graph format |
| `references/reading-strategy.md` | Reading a paper — L1/L2/L3 framework |
| `references/api-reference.md` | Need full script flag / API details |
| `references/arxiv-categories.md` | Picking arXiv category codes |

Reference files are self-contained. Do not chain between references — if a sub-task spans two refs, return to this SKILL.md and re-route.
