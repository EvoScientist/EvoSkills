# API Reference

Quick reference for APIs used by paper-navigator scripts.

## Semantic Scholar (S2) API

**Base URL:** `https://api.semanticscholar.org/graph/v1`

**Auth:** Optional `S2_API_KEY` env var (header: `x-api-key`)
- Without key: ~100 requests / 5 minutes
- With key: ~1 request / second sustained

### Paper ID Formats

| Format | Example | Usage |
|--------|---------|-------|
| S2 ID | `649def34f8be52c8b66281af98ae884c09aef38b` | Default internal ID |
| ArXiv | `ArXiv:1706.03762` | Prefix with `ArXiv:` |
| DOI | `DOI:10.18653/v1/N18-3011` | Prefix with `DOI:` |
| ACL | `ACL:N18-3011` | Prefix with `ACL:` |
| PubMed | `PMID:19872477` | Prefix with `PMID:` |
| URL | `https://arxiv.org/abs/1706.03762` | Full URL also accepted |

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/paper/search?query=...&fields=...&limit=N` | GET | Search papers |
| `/paper/{id}?fields=...` | GET | Single paper details |
| `/paper/{id}/citations?fields=...&limit=N` | GET | Papers citing this paper |
| `/paper/{id}/references?fields=...&limit=N` | GET | Papers this paper cites |
| `/author/search?query=...` | GET | Search authors |
| `/author/{id}/papers?fields=...` | GET | Author's papers |

### Recommendations API

**Base URL:** `https://api.semanticscholar.org/recommendations/v1`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/papers/` | POST | `{"positivePaperIds": [...], "negativePaperIds": [...]}` |

### Useful Fields

```
paperId,externalIds,title,authors,year,citationCount,
influentialCitationCount,tldr,isOpenAccess,openAccessPdf,
publicationVenue,abstract,publicationDate
```

---

## arXiv API

**Base URL:** `http://export.arxiv.org/api/query`

**Auth:** None required
**Rate limit:** Max 1 request per 3 seconds (courtesy). `request_with_retry` enforces this with a local cross-process pacer so concurrent agents share one arXiv request lane.

### Query Parameters

| Param | Example | Description |
|-------|---------|-------------|
| `search_query` | `cat:cs.CL AND ti:transformer` | Search query |
| `sortBy` | `submittedDate` / `relevance` | Sort order |
| `sortOrder` | `descending` / `ascending` | Sort direction |
| `max_results` | `50` | Limit (max 2000) |

### Query Syntax

- `ti:` — title
- `abs:` — abstract
- `au:` — author
- `cat:` — category
- `submittedDate:` — date range `[YYYYMMDD0000 TO YYYYMMDD2359]`
- Boolean: `AND`, `OR`, `ANDNOT`
- Exact phrase: `"chain of thought"`

### Response Format

Returns Atom XML. Namespace: `{http://www.w3.org/2005/Atom}`

---

## Jina Reader

**URL pattern:** `https://r.jina.ai/{target_url}`

**Auth:** Optional `JINA_API_KEY` (header: `Authorization: Bearer <key>`)
**Header:** `Accept: text/markdown`

Returns the target URL content as clean Markdown. Works with:
- arXiv abstract pages (HTML → Markdown)
- PDF URLs (extracts text)
- Any web page

---

## HuggingFace API

**Base URL:** `https://huggingface.co/api`

**Auth:** Optional `HF_TOKEN` env var (header: `Authorization: Bearer <token>`)
**Rate limit:** 500 requests / 300 seconds per IP

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/papers/{arxiv_id}` | GET | Paper metadata (title, authors, githubRepo, githubStars) |
| `/papers/search?q=...&limit=N` | GET | Hybrid semantic + full-text paper search |
| `/daily_papers?date=YYYY-MM-DD` | GET | Daily papers feed |
| `/models?search=...&sort=downloads` | GET | Search models |
| `/models?pipeline_tag=...&sort=likes` | GET | Models by task category |
| `/models?filter=arxiv:{id}` | GET | Models linked to a paper |
| `/datasets?search=...&limit=N` | GET | Search datasets |
| `/datasets?filter=arxiv:{id}` | GET | Datasets linked to a paper |

### Paper Page (Markdown)

Fetch paper content as Markdown:
```
GET https://huggingface.co/papers/{arxiv_id}.md
```

### Pipeline Tags (Task Categories)

Common tags: `text-generation`, `text-classification`, `image-classification`, `object-detection`, `automatic-speech-recognition`, `text-to-image`, `translation`, `summarization`, `question-answering`, `fill-mask`

---

## GitHub API

**Base URL:** `https://api.github.com`

**Auth:** Optional `GITHUB_TOKEN` env var (header: `Authorization: token <token>`)
**Rate limit:** 10 req/min unauthenticated, 5,000 req/hr with token

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search/repositories?q=...&sort=stars` | GET | Search repos by keyword |

---

## S2 Author Multi-ID Handling (added v2.3.0)

A single researcher often holds multiple Semantic Scholar author IDs. Causes: co-author-network disambiguation artifacts, institutional moves, or name-collision merges later split. Example: Yann LeCun has both `1688882` (primary, 403 papers) and `2270469816` (secondary, 33 papers including the top-cited 2024 work).

**Symptom**: `author_search.py --name "<X>"` returns far fewer recent papers than expected for a prolific author.

**Resolution** (used by Eval 12 in iter-4):
1. `scholar_search.py --query "<full name> <recent topic>" --limit 5 --json` — inspect the `authors[].authorId` field to discover all S2 IDs attached to the name.
2. For each unique ID, run `author_search.py --author-id <ID> --year-min <YYYY>`.
3. Merge results, deduplicate by `paperId` or `arxiv_id`.

**Why this matters**: a single-ID lookup of Yann LeCun missed the top 3 most-cited 2024 papers (Navigation World Models, DINO-WM, etc.) until both IDs were merged. The expected behavior — "one author = one ID" — is wrong for ~10-20% of senior researchers.

---

## Local Library Files (added v2.3.0)

`$PAPERS_DIR` (default `~/papers/`) is owned by `download_paper.py` / `library_search.py` / `fetch_paper.py --cache`. Layout:

```
$PAPERS_DIR/
├── index.json                ← single-file index, atomically written
├── <arxiv_id>/
│   ├── paper.pdf             ← downloaded PDF (≥10 KB validated)
│   ├── metadata.json         ← S2 metadata snapshot at download time
│   └── content.md            ← optional Jina-extracted text (fetch_paper --cache)
└── ...
```

`index.json` schema:
```json
{
  "version": 1,
  "updated_at": "ISO8601",
  "papers": [
    {
      "key": "<arxiv_id or s2_id>",
      "arxiv_id": "1706.03762",
      "doi": null,
      "s2_id": "...",
      "title": "...",
      "authors": ["..."],
      "year": 2017,
      "citations": 175716,
      "venue": "NeurIPS",
      "tldr": "...",
      "abstract": "...",
      "downloaded_at": "ISO8601",
      "size_bytes": 2215244,
      "has_pdf": true
    }
  ]
}
```
