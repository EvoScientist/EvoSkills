# Environment Variables — paper-navigator

Full reference for environment variables consumed by paper-navigator scripts. The handful needed for everyday use are inlined in SKILL.md.

## Table

| Variable | Required for | Notes |
|----------|-------------|-------|
| `S2_API_KEY` | All S2 scripts (recommended) | [Request here](https://www.semanticscholar.org/product/api#api-key). Without it: `scholar_search` falls back to arXiv; `citation_traverse` / `recommend` / `snippet_search` are disabled. |
| `JINA_API_KEY` | `fetch_paper` | Free tier works without key |
| `GITHUB_TOKEN` | `github_search`, `find_code` | Higher rate limits |
| `HF_TOKEN` | `find_code`, `dataset_search`, `sota` | Higher rate limits |
| `UNPAYWALL_EMAIL` | `fetch_paper` (optional) | Email for the Unpaywall API. Default: `paper-navigator@users.noreply.github.com` |
| `PAPER_NAV_PAPERS_DIR` | `fetch_paper` (full-text save) | **Required to save full text.** No on-disk default — set explicitly, pass `--papers-dir`, or use `--metadata-only`. |
| `S2_DATE_CUTOFF` | All S2 scripts (optional) | `YYYY` or `YYYY-MM-DD`. When set, every S2 endpoint that accepts `publicationDateOrYear` is filtered to ≤ that date (search, citations, references, snippet, author papers). Explicit `--year-min/--year-max` / `year` in params always wins. Single-paper and `/paper/batch` lookups are unaffected. Use as a freshness fence for reproducible research. |
| `S2_CALL_LOG_DIR` / `S2_CALL_LOG` | All S2 scripts (debugging) | Set `_DIR` for full per-call body logging next to a `main.jsonl` index; set `_LOG` for the index only. Equivalent `ARXIV_*` and `OPENALEX_*` knobs exist. Default off. |

## Rate limits

| API | Without key | With key | When rate limited |
|-----|-------------|----------|-------------------|
| Semantic Scholar | 100 req/5min (~1 req/3s); **NO parallel calls** | 100 req/min; parallel OK | Auto-fallback to arXiv in `scholar_search`; global pacer enforces interval |
| arXiv | 1 req/3s (courtesy) | N/A | Primary fallback when S2 is limited; no auth needed |
| Jina Reader | Free tier | Higher with key | — |
| HuggingFace | 500 req / 300s | Higher with `HF_TOKEN` | — |
| GitHub | 10 req/min | 5,000 req/hr (set `GITHUB_TOKEN`) | — |
| Unpaywall | No auth needed (email param) | N/A | Fallback in `fetch_paper` when S2 has no OA URL |

All scripts retry on 429 and 5xx errors with exponential backoff (3s, 6s, 12s, 24s, 48s — 5 retries). A global S2 request pacer enforces minimum interval between calls. A **circuit breaker** opens after 5 consecutive S2 failures (rejecting requests for 60s) and auto-recovers.

For detailed API endpoints, query parameters, and field specifications, see `references/api-reference.md`.
