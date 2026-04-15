#!/usr/bin/env python3
"""Search academic papers via Semantic Scholar API.

Returns paper metadata including title, authors, year, citation count,
TLDR summary, and open-access PDF links.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from xml.parsers.expat import ExpatError

import httpx

from utils import (
    S2_BASE,
    MissingSemanticScholarKey,
    RateLimitExhausted,
    arxiv_headers,
    normalize_paper_id,
    request_with_retry,
    s2_headers,
)

S2_FIELDS = "paperId,externalIds,title,authors,year,citationCount,influentialCitationCount,tldr,isOpenAccess,openAccessPdf,publicationVenue,abstract"

ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _fallback_arxiv_search(
    query: str,
    limit: int = 10,
    year_min: int | None = None,
    year_max: int | None = None,
) -> list[dict]:
    """Fallback search via arXiv API when S2 is rate limited.

    Uses flexible AND-of-words matching in title and abstract.
    Returns results in S2-compatible dict format.
    """
    # Split query into words, use AND logic for title/abstract matching
    words = query.split()
    if len(words) > 1:
        ti_clause = " AND ".join(f"ti:{w}" for w in words)
        abs_clause = " AND ".join(f"abs:{w}" for w in words)
        kw_query = f"({ti_clause}) OR ({abs_clause})"
    else:
        kw_query = f"ti:{words[0]} OR abs:{words[0]}"

    # Date filtering
    date_parts = []
    if year_min or year_max:
        end = datetime.now(timezone.utc)
        start_year = year_min or 2000
        start = datetime(start_year, 1, 1, tzinfo=timezone.utc)
        if year_max:
            end = datetime(year_max, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        date_range = f"[{start.strftime('%Y%m%d')}0000 TO {end.strftime('%Y%m%d')}2359]"
        date_parts.append(f"submittedDate:{date_range}")

    search_query = kw_query
    if date_parts:
        search_query = f"({kw_query}) AND {date_parts[0]}"

    params = {
        "search_query": search_query,
        "sortBy": "relevance",
        "sortOrder": "descending",
        "max_results": min(limit, 500),
    }

    with httpx.Client() as client:
        xml_text = request_with_retry(
            client, ARXIV_API, params, arxiv_headers(), parse_json=False
        )

    if not xml_text:
        return []

    # Parse arXiv XML and convert to S2-compatible format
    # Reject XML with DTD/entity declarations before parsing to avoid XXE-style inputs.
    if "<!DOCTYPE" in xml_text or "<!ENTITY" in xml_text:
        raise ValueError("Unsafe XML payload from arXiv API")

    try:
        root = ET.fromstring(xml_text)
    except (ET.ParseError, ExpatError) as exc:
        raise ValueError("Invalid XML payload from arXiv API") from exc
    entries = root.findall("atom:entry", ARXIV_NS)
    papers = []
    for entry in entries:
        title = entry.findtext("atom:title", "", ARXIV_NS).replace("\n", " ").strip()
        summary = entry.findtext("atom:summary", "", ARXIV_NS).strip()
        published = entry.findtext("atom:published", "", ARXIV_NS)

        id_url = entry.findtext("atom:id", "", ARXIV_NS)
        arxiv_id = id_url.split("/abs/")[-1] if "/abs/" in id_url else id_url

        authors = []
        for author in entry.findall("atom:author", ARXIV_NS):
            name = author.findtext("atom:name", "", ARXIV_NS)
            if name:
                authors.append({"name": name})

        categories = []
        for cat in entry.findall("atom:category", ARXIV_NS):
            term = cat.get("term", "")
            if term:
                categories.append(term)

        pdf_url = ""
        for link in entry.findall("atom:link", ARXIV_NS):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", "")

        year = None
        if published:
            try:
                year = int(published[:4])
            except (ValueError, IndexError):
                pass

        comment = ""
        comment_el = entry.find("arxiv:comment", ARXIV_NS)
        if comment_el is not None and comment_el.text:
            comment = comment_el.text.strip()

        # Convert to S2-compatible dict format
        papers.append(
            {
                "paperId": f"arxiv:{arxiv_id}",
                "externalIds": {"ArXiv": arxiv_id},
                "title": title,
                "authors": authors,
                "year": year,
                "citationCount": None,  # Not available from arXiv
                "influentialCitationCount": None,
                "tldr": None,
                "isOpenAccess": True,
                "openAccessPdf": {"url": pdf_url} if pdf_url else None,
                "publicationVenue": None,
                "abstract": summary,
                "_source": "arxiv",  # Marker for fallback origin
                "_comment": comment,
                "_categories": categories,
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
    except MissingSemanticScholarKey:
        print(
            "⚠️  S2_API_KEY is not set. Skipping Semantic Scholar and using arXiv "
            "search instead...",
            file=sys.stderr,
        )
        return _fallback_arxiv_search(query, limit, year_min, year_max)
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
    args = parser.parse_args()

    if not args.query and not args.paper_id:
        print("Error: --query or --paper-id required", file=sys.stderr)
        sys.exit(1)

    if args.paper_id:
        try:
            paper = get_paper(normalize_paper_id(args.paper_id))
        except MissingSemanticScholarKey:
            print(
                "⚠️  S2_API_KEY is not set. Cannot fetch paper by S2 ID without a key.\n"
                "Provide a direct arXiv ID (e.g. ArXiv:2501.12948), DOI, or use "
                "--url with fetch_paper instead.",
                file=sys.stderr,
            )
            sys.exit(0)
        if args.json:
            print(json.dumps(paper, indent=2))
        else:
            print(format_paper(paper))
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

    if args.json:
        print(json.dumps(papers, indent=2))
        return

    print(f'# Search Results: "{args.query}"\n')
    print(f"Found **{len(papers)}** papers\n")
    for i, p in enumerate(papers, 1):
        print(format_paper(p, i))


if __name__ == "__main__":
    main()
