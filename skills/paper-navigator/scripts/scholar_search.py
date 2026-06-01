#!/usr/bin/env python3
"""Search academic papers via Semantic Scholar API.

Returns paper metadata including title, authors, year, citation count,
TLDR summary, and open-access PDF links.
"""

from __future__ import annotations

import argparse
import sys

import httpx

import deepxiv_client
from utils import (
    S2_BASE,
    s2_headers,
    request_with_retry,
    RateLimitExhausted,
    add_output_args,
    emit_results,
)

S2_FIELDS = "paperId,corpusId,externalIds,title,authors,year,citationCount,influentialCitationCount,tldr,isOpenAccess,openAccessPdf,publicationVenue,abstract"


def _fallback_arxiv_search(
    query: str,
    limit: int = 10,
    year_min: int | None = None,
    year_max: int | None = None,
) -> list[dict]:
    """Fallback arXiv search via DeepXiv when S2 is rate limited.

    DeepXiv (https://github.com/qhjqhj00/deepxiv_sdk) replaces the rate-limited
    arXiv API. Returns results in S2-compatible dict format.
    """
    date_from = f"{year_min}-01-01" if year_min else None
    date_to = f"{year_max}-12-31" if year_max else None

    items = deepxiv_client.search(
        query=query,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
    )

    papers = []
    for item in items:
        arxiv_id = deepxiv_client.item_id(item)
        published = item.get("date") or item.get("publish_at") or ""
        year = None
        if published:
            try:
                year = int(str(published)[:4])
            except (ValueError, IndexError):
                pass

        pdf_url = item.get("src_url") or (
            f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else ""
        )
        categories = item.get("categories") or item.get("category") or []
        if isinstance(categories, str):
            categories = [categories]

        # Convert to S2-compatible dict format
        papers.append(
            {
                "paperId": f"arxiv:{arxiv_id}",
                "externalIds": {"ArXiv": arxiv_id},
                "title": (item.get("title") or "").replace("\n", " ").strip(),
                "authors": [{"name": n} for n in deepxiv_client.item_authors(item)],
                "year": year,
                "citationCount": item.get("citation_count", item.get("citation")),
                "influentialCitationCount": None,
                "tldr": None,
                "isOpenAccess": True,
                "openAccessPdf": {"url": pdf_url} if pdf_url else None,
                "publicationVenue": None,
                "abstract": (item.get("abstract") or item.get("tldr") or "").strip(),
                "_source": "arxiv",  # Marker for fallback origin (now via DeepXiv)
                "_comment": "",
                "_categories": list(categories),
            }
        )
    return papers


def search(
    query: str,
    limit: int = 10,
    year_min: int | None = None,
    year_max: int | None = None,
    open_access_only: bool = False,
) -> list[dict]:
    """Search S2 for papers matching query. Falls back to arXiv on rate limit."""
    try:
        params: dict = {
            "query": query,
            "limit": min(limit, 100),
            "fields": S2_FIELDS,
        }
        if year_min or year_max:
            lo = year_min or ""
            hi = year_max or ""
            params["year"] = f"{lo}-{hi}"
        if open_access_only:
            params["openAccessPdf"] = ""

        with httpx.Client() as client:
            data = request_with_retry(
                client, f"{S2_BASE}/paper/search", params, s2_headers()
            )
        return data.get("data", [])
    except RateLimitExhausted:
        print(
            "⚠️  S2 rate limited after all retries. Falling back to arXiv search...",
            file=sys.stderr,
        )
        return _fallback_arxiv_search(query, limit, year_min, year_max)


def get_paper(paper_id: str) -> dict:
    """Get single paper details by S2 paper ID or external ID."""
    with httpx.Client() as client:
        return request_with_retry(
            client, f"{S2_BASE}/paper/{paper_id}", {"fields": S2_FIELDS}, s2_headers()
        )


def _truncate(text: str | None, max_len: int = 200) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


def format_paper(p: dict, idx: int | None = None) -> str:
    """Format a single paper as Markdown."""
    prefix = f"### {idx}. " if idx is not None else "### "
    title = p.get("title", "Unknown")
    year = p.get("year", "?")
    citations = p.get("citationCount", 0)
    influential = p.get("influentialCitationCount", 0)

    authors = p.get("authors", [])
    author_str = ", ".join(a.get("name", "") for a in authors[:5])
    if len(authors) > 5:
        author_str += f" et al. ({len(authors)} authors)"

    venue = ""
    if p.get("publicationVenue"):
        venue = p["publicationVenue"].get("name", "")

    tldr = ""
    if p.get("tldr") and p["tldr"].get("text"):
        tldr = f"\n> **TLDR:** {p['tldr']['text']}"

    abstract = ""
    if not tldr and p.get("abstract"):
        abstract = f"\n> {_truncate(p['abstract'])}"

    pdf = ""
    if p.get("openAccessPdf") and p["openAccessPdf"].get("url"):
        pdf = f"\n📄 [Open Access PDF]({p['openAccessPdf']['url']})"

    paper_id = p.get("paperId", "")
    ext_ids = p.get("externalIds", {})
    arxiv_id = ext_ids.get("ArXiv", "")
    doi = ext_ids.get("DOI", "")

    ids_line = f"S2: `{paper_id}`"
    if arxiv_id:
        ids_line += f" | arXiv: `{arxiv_id}`"
    if doi:
        ids_line += f" | DOI: `{doi}`"

    # Mark arXiv fallback results
    source_note = ""
    if p.get("_source") == "arxiv":
        source_note = "\n*(via arXiv fallback — citation counts unavailable)*"

    cit_str = f"**{citations}** (influential: {influential})"
    if citations is None:
        cit_str = "N/A (arXiv)"

    return f"""{prefix}{title}
**{author_str}** ({year}) — {venue}
Citations: {cit_str}
{ids_line}{tldr}{abstract}{pdf}{source_note}
"""


def main():
    parser = argparse.ArgumentParser(description="Search papers via Semantic Scholar")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Max results (default 10)"
    )
    parser.add_argument("--year-min", type=int, help="Minimum publication year")
    parser.add_argument("--year-max", type=int, help="Maximum publication year")
    parser.add_argument(
        "--open-access-only", action="store_true", help="Only return OA papers"
    )
    parser.add_argument(
        "--sort-by",
        choices=["citations", "year", "relevance"],
        default="relevance",
        help="Sort order",
    )
    parser.add_argument(
        "--paper-id", help="Get single paper by ID instead of searching"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    add_output_args(parser)
    args = parser.parse_args()

    if not args.query and not args.paper_id:
        print("Error: --query or --paper-id required", file=sys.stderr)
        sys.exit(1)

    if args.paper_id:
        paper = get_paper(args.paper_id)
        emit_results([paper], args, format_fn=format_paper, title="Paper Details")
        return

    fetch_limit = 100 if args.sort_by != "relevance" else args.limit
    papers = search(
        args.query, fetch_limit, args.year_min, args.year_max, args.open_access_only
    )

    if not papers:
        print(f"No papers found for '{args.query}'", file=sys.stderr)
        sys.exit(0)

    if args.sort_by == "citations":
        papers.sort(key=lambda p: p.get("citationCount") or 0, reverse=True)
    elif args.sort_by == "year":
        papers.sort(key=lambda p: p.get("year") or 0, reverse=True)

    papers = papers[: args.limit]
    emit_results(
        papers,
        args,
        format_fn=format_paper,
        title=f'Search Results: "{args.query}"',
    )


if __name__ == "__main__":
    main()
