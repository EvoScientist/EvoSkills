#!/usr/bin/env python3
"""Search the local paper library — zero network, reads $PAPERS_DIR/index.json.

Used by Branch 0 LOCAL-FIRST routing in SKILL.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PAPERS_DIR = Path(os.environ.get("PAPERS_DIR", str(Path.home() / "papers")))
INDEX_PATH = PAPERS_DIR / "index.json"


def load_index() -> list[dict]:
    if not INDEX_PATH.exists():
        return []
    try:
        return json.loads(INDEX_PATH.read_text()).get("papers", [])
    except Exception:
        return []


def match_query(paper: dict, q_tokens: set[str]) -> int:
    """Return overlap count of query tokens with paper title + authors + tldr."""
    haystack = " ".join(
        filter(
            None,
            [
                paper.get("title") or "",
                " ".join(paper.get("authors") or []),
                paper.get("tldr") or "",
                paper.get("venue") or "",
            ],
        )
    ).lower()
    haystack_tokens = set(haystack.replace(",", " ").replace(".", " ").split())
    return len(q_tokens & haystack_tokens)


def search(
    query: str | None = None,
    arxiv_id: str | None = None,
    title: str | None = None,
    min_overlap: int = 2,
) -> list[dict]:
    papers = load_index()
    if not papers:
        return []

    if arxiv_id:
        return [p for p in papers if p.get("arxiv_id") == arxiv_id]

    if title:
        target = title.lower().strip()
        # exact substring match
        hits = [p for p in papers if target in (p.get("title") or "").lower()]
        return sorted(hits, key=lambda p: p.get("citations") or 0, reverse=True)

    if query:
        q_tokens = set(query.lower().split())
        # Auto-relax min_overlap for short queries (1-token can only match 1 token).
        # Without this, `library_search --query "BERT"` returns 0 even when BERT is indexed.
        effective_min = min(min_overlap, len(q_tokens))
        scored = [(match_query(p, q_tokens), p) for p in papers]
        scored = [(s, p) for s, p in scored if s >= effective_min and s > 0]
        scored.sort(key=lambda sp: (sp[0], sp[1].get("citations") or 0), reverse=True)
        return [p for _, p in scored]

    return papers  # list all


def main():
    p = argparse.ArgumentParser(
        description="Search local paper library ($PAPERS_DIR/index.json)."
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument(
        "--query", "-q", help="Keyword query (matches title + authors + TLDR)"
    )
    g.add_argument("--arxiv-id", "-a", help="Exact arXiv ID match")
    g.add_argument("--title", "-t", help="Substring match on title")
    g.add_argument("--list", action="store_true", help="List all cached papers")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument(
        "--min-overlap",
        type=int,
        default=2,
        help="Min token overlap for keyword match (default 2)",
    )
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if not INDEX_PATH.exists():
        print(
            f"No local library at {PAPERS_DIR} (index.json missing).", file=sys.stderr
        )
        print("Run download_paper.py to populate.", file=sys.stderr)
        if args.json:
            print(
                json.dumps(
                    {"papers_dir": str(PAPERS_DIR), "results": [], "exists": False}
                )
            )
        sys.exit(1 if not args.json else 0)

    results = search(
        query=args.query if not args.list else None,
        arxiv_id=args.arxiv_id,
        title=args.title,
        min_overlap=args.min_overlap,
    )
    results = results[: args.limit]

    if args.json:
        print(
            json.dumps(
                {
                    "papers_dir": str(PAPERS_DIR),
                    "results": results,
                    "count": len(results),
                },
                indent=2,
            )
        )
        return

    if not results:
        print(f"No matches in local library at {PAPERS_DIR}.")
        sys.exit(0)

    # Paper Table (matches SKILL.md Branch 2 format)
    print(f"# Local Library — {len(results)} match(es) in `{PAPERS_DIR}`\n")
    print("| # | Title | Authors | Year | Citations | arXiv | Path |")
    print("|---|-------|---------|------|-----------|-------|------|")
    for i, r in enumerate(results, 1):
        title = (r.get("title") or "")[:60]
        authors = (
            ((r.get("authors") or [""])[0] + " et al.") if r.get("authors") else ""
        )
        year = r.get("year") or "—"
        cites = r.get("citations") or 0
        aid = r.get("arxiv_id") or "—"
        path = f"{r.get('key')}/paper.pdf"
        print(f"| {i} | {title} | {authors} | {year} | {cites} | {aid} | {path} |")


if __name__ == "__main__":
    main()
