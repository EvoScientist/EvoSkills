#!/usr/bin/env python3
"""Monitor arXiv for new papers by category or keywords.

Uses the DeepXiv SDK (https://github.com/qhjqhj00/deepxiv_sdk) to fetch recent
papers from specific categories or matching keywords. DeepXiv replaces the
rate-limited arXiv API (3s delay, frequent HTTP 429): anonymous use allows
1,000 requests/day, or 10,000 with DEEPXIV_API_TOKEN set.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone

import deepxiv_client
from utils import (
    add_output_args,
    emit_results,
)


def _date_from(days: int) -> str:
    """ISO ``YYYY-MM-DD`` for the start of the look-back window."""
    start = datetime.now(timezone.utc) - timedelta(days=days)
    return start.strftime("%Y-%m-%d")


def _item_to_paper(item: dict) -> dict:
    """Map a DeepXiv result item to the monitor's paper dict."""
    arxiv_id = deepxiv_client.item_id(item)
    title = (item.get("title") or "").replace("\n", " ").strip()
    summary = (item.get("abstract") or item.get("tldr") or "").strip()
    published = item.get("date") or item.get("publish_at") or ""
    categories = item.get("categories") or item.get("category") or []
    if isinstance(categories, str):
        categories = [categories]
    pdf_url = item.get("src_url") or (
        f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else ""
    )
    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": deepxiv_client.item_authors(item),
        "summary": summary[:300],
        "categories": list(categories),
        "published": str(published),
        "updated": str(item.get("publish_at") or published or ""),
        "pdf_url": pdf_url,
        "comment": "",
    }


def fetch_by_categories(
    categories: list[str], days: int = 1, limit: int = 50
) -> list[dict]:
    """Fetch recent papers from specific arXiv categories via DeepXiv.

    DeepXiv search requires a text query, so the category labels double as the
    query while also being passed as a category filter.
    """
    items = deepxiv_client.search(
        query=" ".join(categories),
        limit=limit,
        categories=categories,
        date_from=_date_from(days),
    )
    return [_item_to_paper(it) for it in items]


def fetch_by_keywords(
    keywords: list[str],
    days: int = 7,
    limit: int = 50,
    match_mode: str = "flexible",
) -> list[dict]:
    """Fetch recent papers matching keywords via DeepXiv semantic search.

    Args:
        match_mode: Accepted for CLI compatibility but unused — DeepXiv ranks
            semantically rather than by exact/flexible token matching.
    """
    items = deepxiv_client.search(
        query=" ".join(k.strip() for k in keywords),
        limit=limit,
        date_from=_date_from(days),
    )
    return [_item_to_paper(it) for it in items]


def format_paper(p: dict, idx: int) -> str:
    title = p["title"]
    arxiv_id = p["arxiv_id"]
    authors = ", ".join(p["authors"][:3])
    if len(p["authors"]) > 3:
        authors += " et al."
    cats = ", ".join(p["categories"][:3])
    published = p["published"][:10] if p["published"] else "?"
    summary = p["summary"][:200]
    if len(p["summary"]) > 200:
        summary = summary.rsplit(" ", 1)[0] + "…"

    comment = f"\n  📝 {p['comment']}" if p["comment"] else ""

    return (
        f"{idx}. **{title}**\n"
        f"  {authors} | {published} | [{cats}]\n"
        f"  arXiv:`{arxiv_id}` | [PDF]({p['pdf_url']}){comment}\n"
        f"  > {summary}\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Monitor arXiv for new papers")
    parser.add_argument(
        "--categories", "-c", help="Comma-separated arXiv categories (e.g. cs.CL,cs.AI)"
    )
    parser.add_argument("--keywords", "-k", help="Comma-separated keywords to search")
    parser.add_argument(
        "--days", "-d", type=int, default=3, help="Look back N days (default 3)"
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=30, help="Max results (default 30)"
    )
    parser.add_argument(
        "--match-mode",
        choices=["exact", "flexible"],
        default="flexible",
        help="Accepted for compatibility; ignored (DeepXiv ranks semantically)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    add_output_args(parser)
    args = parser.parse_args()

    if not args.categories and not args.keywords:
        print("Error: --categories or --keywords required", file=sys.stderr)
        sys.exit(1)

    papers = []
    if args.categories:
        cats = [c.strip() for c in args.categories.split(",")]
        papers = fetch_by_categories(cats, args.days, args.limit)
    else:
        kws = [k.strip() for k in args.keywords.split(",")]
        papers = fetch_by_keywords(kws, args.days, args.limit, args.match_mode)

    if not papers:
        print("No new papers found.", file=sys.stderr)
        sys.exit(0)
    mode = (
        f"categories: {args.categories}"
        if args.categories
        else f"keywords: {args.keywords}"
    )
    emit_results(
        papers,
        args,
        format_fn=format_paper,
        title=f"arXiv Monitor: {mode} — last {args.days} days",
    )


if __name__ == "__main__":
    main()
