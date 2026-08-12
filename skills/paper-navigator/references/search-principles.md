# Search Principles

Read this when:
- Designing queries for ITERATIVE collection or a gap-driven follow-up in LIST
- Hit a rate limit (429) and need a fallback strategy
- Search returned 0 or <3 results and you need to broaden
- Working in an unfamiliar domain and unsure which terminology to use

---

## Gap Diagnosis (the "search what's missing" rule, operationalized)

Every query must map to one gap type. Picking the wrong gap type is the #1 reason searches waste budget.

| Gap type | When it applies | Strategy | Query design |
|---|---|---|---|
| **Structural** | You don't know the field's landscape, need taxonomy / evolution | Breadth-laying | Upper-concept + canonical terminology. E.g. `vision language model` (NOT `vision language model survey`) |
| **Evidence** | Framework is known, need specific empirical results, algorithms, or datasets | Detail dig | Specific entity name + property. E.g. `LoRA fine-tuning benchmark` |
| **Original work** | Need the *first* paper that introduced a concept | Detail dig | Bare entity name only, no `paper` / `original`. E.g. `induction head transformer` |
| **Multi-source verification** | Claim has only one supporting paper, need parallel work | Source verification | Swap to a different community's term. E.g. `chain of thought` → `step by step reasoning LLM` |
| **Recency / SOTA** | Need latest results or recent work | Year filter | Put recency in `--year-min` (last 2 years). Never put year words in the query. E.g. `code generation benchmark --year-min 2025` |
| **Dead end** | Same angle returned nothing for 2 consecutive rounds | Reasoning pivot | Switch to a completely different keyword angle. Synonyms don't help here. |

Apply this in: LIST follow-up rounds (R3 deepen / R4 close), ITERATIVE rounds. The Step 5 saturation gate in SKILL.md consumes these gap diagnoses.

**Default-ban `survey` / `review` / `tutorial` terms.** These bias results toward review papers and crowd out the canonical research papers the user usually wants. Only use them when the user **explicitly** asks for a survey/review ("survey of X", "review of Y", "taxonomy of Z").

---

## Query Design Discipline

Five hard rules. Violating any one of them is the most common cause of zero-recall.

1. **3-6 words.** Fewer than 3 is too broad (millions of hits, no signal). More than 6 dilutes relevance — the engine cannot weigh 7+ concepts. Split into multiple queries instead.
2. **English only.** Academic indices are English-first. Chinese / non-English queries have far worse recall on the same topic.
3. **No formal words.** Drop `paper`, `original paper`, `arxiv`, `pdf`, `download`, `论文`. They are noise — the index already knows you want papers.
4. **Atomic.** One query = one information gap. Comparisons, multi-property, year-spanning, "concept + specific method" must split into independent queries.
5. **No special syntax.** Do not use `"..."`, `(...)`, `OR`, `AND`, `|`, `site:`, `filetype:`. The scripts accept plain keyword strings only.

### Atomic split — when in doubt, split

| Pattern | Bad | Good (split) |
|---|---|---|
| Multi-entity compare | `A vs B comparison` | `A architecture` + `B architecture` |
| Multi-property | `transformer architecture applications` | `transformer architecture` + `transformer applications NLP` |
| Multi-year | `data pruning 2020 vs 2024 trends` | `data pruning pretraining` (`--year-max 2020`) + `data pruning pretraining` (`--year-min 2024`) |
| Concept + specific | `LoRA adapter PEFT` | `parameter efficient fine-tuning` + `LoRA low rank adaptation` |

### Reformulation axes (for ITERATIVE R2 breadth and R3 deepen)

A single query misses 30-50% of relevant work because research communities use different terms. Generate 4-6 variants along these axes:

| Axis | Example transformation |
|---|---|
| **Empirical ↔ theoretical** | "emergence of ICL" → "ICL theory linear attention" |
| **Mechanism ↔ condition** | "induction heads" → "pretraining data structure ICL" |
| **Method-keyword synonyms** | "data pruning" → "data selection" / "data filtering" / "data curation" |
| **Specificity** | broaden ("LLM pretraining") or narrow ("perplexity-based pruning LLM") |
| **Structural variant** | swap order, drop qualifier, add abbreviation |

A budget of 4-6 variants typically covers ~80% of the field's terminology.

---

## Good / Bad Query Examples

Internalize the patterns by contrast. Each example shows the most common mistake and the correction.

### Example 1: Concept overview (structural gap)

> User: "Tell me about LLM alignment techniques"

- ❌ `LLM alignment all methods comparison` — too broad, stacking
- ❌ `RLHF DPO PPO alignment survey 2024` — multiple method names crammed with `survey`; rarely returns the canonical papers
- ✅ Split 3: `large language model alignment` + `RLHF reinforcement learning human feedback` + `direct preference optimization DPO`

**Why:** The user asked for "techniques", not a survey — so do **not** add `survey`. The upper-concept query surfaces the landmark papers; method-name queries get each representative work. Splitting lets each query precision-target.

### Example 2: Tracking SOTA (recency gap)

> User: "Latest progress in code generation"

- ❌ `code generation best paper` — `paper` is a formal word; no time anchor
- ❌ `latest code generation 2024` — year words in the query are not how the scripts filter
- ✅ `code generation benchmark` + `code generation LLM` (both with `--year-min 2025` from R2 onward)

**Why:** `scholar_search.py` supports `--year-min` / `--year-max` — put recency intent in those params, never year words in the query. Year words dilute relevance ranking.

### Example 3: Finding the original work

> User: "Which paper introduced induction heads?"

- ❌ `induction head original paper Anthropic` — formal word + org name dilute relevance
- ❌ `who proposed induction head transformer` — natural-language phrasing
- ✅ `induction head transformer` — bare entity, let relevance ranking surface the foundational work (S2 relevance already weights citation signal; explicit `--sort-by citations` is only needed when the user asked for canonical work specifically)

**Why:** Academic indices rank bare-concept queries best. Modifiers create noise.

### Example 4: Multi-entity comparison

> User: "Compare LoRA and Adapter in PEFT"

- ❌ `LoRA vs Adapter PEFT comparison` — engine doesn't parse `vs`; "comparison" rarely returns comparative papers
- ✅ Split 3: `LoRA low rank adaptation` + `adapter parameter efficient fine-tuning` + `parameter efficient fine-tuning`

**Why:** Get both sides' representative papers separately, plus the umbrella-concept query for the broader view. Do **not** add `survey` — the user wants the comparison, not a survey. Synthesize the comparison yourself from abstracts.

---

## Domain Terminology Drift (cross-discipline)

Different communities use different vocabulary for the same idea. Picking the wrong community's term drops recall from ~80% to ~10%. Consult these tables when:
- The query crosses fields (CS + biology, ML + neuroscience)
- The initial English query returns suspiciously few hits
- You're researching in a new field

### CS / AI / ML

| You want | Use | Avoid |
|---|---|---|
| Survey / review paper | **Only add `survey`/`review` when the user explicitly asked for a survey.** Default: drop these terms — the canonical research papers are usually what the user wants. | `overview` (returns noise) |
| Evaluation | `benchmark` / `evaluation` | `comparison test` |
| Model architecture | `architecture` | `structure` (too broad) |
| Training method | `fine-tuning` / `pretraining` | `training method` |
| Inference optimization | `inference` / `decoding` | `prediction` |

Typical: `vision language model`, `multimodal benchmark`, `LoRA fine-tuning`. (Add `--year-min` for recency, not year words.)

### Biomedical

| You want | Use | Avoid |
|---|---|---|
| Survey / review paper | **Only add `systematic review` / `meta-analysis` when the user explicitly asked for a survey.** Default: drop these terms. | `overview` (returns noise) |
| Clinical validation | `randomized controlled trial` / `RCT` | `experiment` (too broad) |
| Mechanism | `pathway` / `mechanism` | `how it works` |
| Efficacy | `efficacy` / `outcome` | `effect` (too broad) |

Typical: `GLP-1 trial`, `Alzheimer biomarker pathway`.

### Physics / Materials

| You want | Use | Avoid |
|---|---|---|
| Survey / review paper | **Only add `review` when the user explicitly asked for a survey.** Default: drop these terms. | `overview` (returns noise) |
| Experimental measurement | `measurement` / `observation` | `test` |
| Theory | `theoretical framework` / `first principles` | `theory` (too broad) |

### Cross-domain concept drift (high-frequency traps)

The same concept gets renamed across fields. If a user's question spans fields, you must search both terminologies.

| Concept | CS | Physics / Math | Neuroscience |
|---|---|---|---|
| Attention | `attention mechanism` | — | `selective attention` |
| Memory | `memory module` / `KV cache` | — | `working memory` / `engram` |
| Gradient learning | `gradient descent` | `optimization` | `synaptic plasticity` |

**Use:** If the user asks "how does AI mimic human memory?", run **both** `memory augmented neural network` and `engram neuroscience` — searching only one side misses half the literature.

---

## Multi-Source Search

Use ≥2 sources per discovery task in ITERATIVE, ≥1 in LIST/POINT:
- **Primary:** `scholar_search.py` (Semantic Scholar, with arXiv fallback on 429)
- **Secondary:** `arxiv_monitor.py --keywords ... --match-mode flexible` (broader recall on recent preprints)
- **Tertiary (when S2 is down):** web search for blog posts, surveys, GitHub READMEs that reference papers

Reason: S2 has citation signal but lags on preprints; arXiv has all preprints but no citation ranking. Combined recall is 1.5-2× single-source.

## S2 Parallelization Rule

Semantic Scholar limits: **100 req/5min without API key (~1 req/3s)**, **100 req/min with key**.

- **With `S2_API_KEY` set** → parallel S2 calls are fine.
- **Without key** → run S2 calls **sequentially**, one at a time. Parallel calls without a key exhaust the budget within seconds and trigger 429 → automatic fallback to arXiv search (lower quality: no citation counts, weaker relevance ranking).

Check before starting: `echo $S2_API_KEY`. If empty, switch to sequential mode for all S2-dependent scripts: `scholar_search`, `citation_traverse`, `recommend`, `author_search`, `trending`.

`arxiv_monitor` is independent from S2 and can run in parallel with S2 calls. Multiple arXiv callers on the same machine are serialized by a shared pacer, so expect them to queue rather than start at the same instant.

## Rate-Limit Fallback Chain

When you hit 429 or empty results:

1. `scholar_search` falls back to arXiv automatically — accept the lower-quality result and continue.
2. If still empty, run `arxiv_monitor --keywords "<variants>" --match-mode flexible --days 365` for broader recall.
3. If arXiv also fails, web search for blog posts / surveys / GitHub repos that cite papers in the area.
4. For `citation_traverse` and `recommend`, space calls ≥5s apart and reduce `--limit` to 10.

Built-in retries: all scripts retry on 429/5xx with exponential backoff (3s, 6s, 12s, 24s, 48s — 5 retries), use a global S2 pacer, and serialize arXiv API request starts across local processes.

## When to Use Each Discovery Path

| Path | Strongest signal | Use case |
|---|---|---|
| **Keyword search** (`scholar_search`) | Term matching | Always the starting point |
| **arXiv monitor** | Recency | Recent preprints; topics breaking onto arXiv before publication |
| **Co-citation** (`citation_traverse --direction co-citation`) | Frequently-cited-together | Finding related work that uses different terms — strongest single signal |
| **Forward citation** | "Who cited this" | Follow-up work, applications |
| **Backward citation** | "What did this cite" | Foundational work, alternative formulations |
| **Recommend** | Embedding similarity + co-occurrence | Serendipitous semantic neighbors not in citation graph |
| **Author search** | Author identity | Track a researcher; find their less-cited recent work |
| **Trending** | Citation velocity | Hot topics, what's breaking out |
| **GitHub search** | Code/release lag | Industry papers released as code first |

## When to Stop Searching

Stop conditions depend on branch:

**POINT** — stop after the target paper is found with high-confidence ranking (top 1-3 result). Do not chain.

**LIST** — Probe + up to 3 paper rounds (R2 breadth / R3 deepen / R4 close). Stop when the Step 5 saturation gate (SKILL.md) returns STOP — ≥1 All-core paper (covering every [core] criterion) exists AND every angle tag has ≥1 All-core/Partial AND no key claim rests on a single source. Going beyond 3 rounds requires re-decomposing the rubric or escalating to ITERATIVE.

**ITERATIVE** — see `iterative-collection.md`. The flow is the same Probe + up to 3 paper rounds (R2/R3/R4); the saturation gate (Step 5) is the same. Most over-search comes from skipping the gate check and instead running more keyword variants — the gate check is cheaper and higher-yield. **Round cap is 3 paper rounds (R2/R3/R4); there is no R5.** If not saturated at the cap, tell the user which criteria / angle tags are under-covered rather than burn more budget.

**Universal stop signal** (override all the above): every key claim has ≥2 abstract-level supporting papers AND no contradictions are unresolved AND remaining unknowns are nice-to-have. If true, you're done — stop searching.

## Paper ID Formats

All scripts accept and normalize:
- S2 ID (e.g., `235959867`)
- arXiv (`ArXiv:1706.03762` / `1706.03762` / URL)
- DOI (`DOI:10.18653/v1/N18-3011`)
