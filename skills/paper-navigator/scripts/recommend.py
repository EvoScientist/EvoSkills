#!/usr/bin/env python3
"""Get paper recommendations from Semantic Scholar.

Given seed papers (positive examples, optionally negative examples),
returns semantically similar papers.
"""

import argparse
import json
import sys
import time

import httpx

from utils import (
    S2_BASE,
    S2_RECOMMEND_BASE,
    MAX_RETRIES,
    RETRY_DELAYS,
    s2_headers,
    request_with_retry,
    normalize_paper_id,
)

S2_FIELDS = "paperId,externalIds,title,authors,year,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf"


def _resolve_to_s2_id(client: httpx.Client, paper_id: str) -> str:
    """Resolve any paper ID format to S2 paperId."""
    try:
        data = request_with_retry(
            client, f"{S2_BASE}/paper/{paper_id}", {"fields": "paperId"}, s2_headers()
        )
        return data.get("paperId", paper_id)
    except Exception:
        return paper_id


def recommend(
    positive_ids: list[str], negative_ids: list[str] | None = None, limit: int = 10
) -> list[dict]:
    """Get recommendations based on seed papers."""
    with httpx.Client() as client:
        # Resolve all IDs to S2 format
        pos_s2 = [
            _resolve_to_s2_id(client, normalize_paper_id(pid)) for pid in positive_ids
        ]
        neg_s2 = [
            _resolve_to_s2_id(client, normalize_paper_id(pid))
            for pid in (negative_ids or [])
        ]

        body: dict = {
            "positivePaperIds": pos_s2,
        }
        if neg_s2:
            body["negativePaperIds"] = neg_s2

        # POST request — keep inline retry (request_with_retry is GET-only)
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.post(
                    f"{S2_RECOMMEND_BASE}/papers/",
                    json=body,
                    params={"fields": S2_FIELDS, "limit": min(limit, 500)},
                    headers=s2_headers(),
                    timeout=30,
                )
                if resp.status_code == 429 or resp.status_code >= 500:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAYS[attempt])
                        continue
                resp.raise_for_status()
                return resp.json().get("recommendedPapers", [])
            except httpx.HTTPStatusError:
                raise
            except httpx.HTTPError as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                raise SystemExit(f"Error: {e}") from e
    return []


def format_paper(p: dict, idx: int) -> str:
    title = p.get("title", "Unknown")
    year = p.get("year", "?")
    citations = p.get("citationCount", 0)
    authors = p.get("authors", [])
    author_str = ", ".join(a.get("name", "") for a in authors[:3])
    if len(authors) > 3:
        author_str += " et al."

    tldr = ""
    if p.get("tldr") and p["tldr"].get("text"):
        tldr = f"\n  > {p['tldr']['text']}"

    ext = p.get("externalIds", {})
    arxiv = ext.get("ArXiv", "")
    pid = p.get("paperId", "")
    id_str = f"arXiv:`{arxiv}`" if arxiv else f"S2:`{pid[:12]}…`"

    pdf = ""
    if p.get("openAccessPdf") and p["openAccessPdf"].get("url"):
        pdf = " 📄"

    return f"{idx}. **{title}** — {author_str} ({year}) — ⭐{citations}{pdf} — {id_str}{tldr}"


def main():
    parser = argparse.ArgumentParser(
        description="Get paper recommendations from Semantic Scholar"
    )
    parser.add_argument(
        "--positive",
        "-p",
        required=True,
        help="Comma-separated seed paper IDs (positive examples)",
    )
    parser.add_argument(
        "--negative",
        "-n",
        help="Comma-separated paper IDs to avoid (negative examples)",
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Max results (default 10)"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    positive = [p.strip() for p in args.positive.split(",") if p.strip()]
    negative = (
        [p.strip() for p in args.negative.split(",") if p.strip()]
        if args.negative
        else None
    )

    if not positive:
        print("Error: at least one positive paper ID required", file=sys.stderr)
        sys.exit(1)

    papers = recommend(positive, negative, args.limit)

    if not papers:
        print("No recommendations found.", file=sys.stderr)
        sys.exit(0)

    if args.json:
        print(json.dumps(papers, indent=2))
        return

    print("# Paper Recommendations\n")
    print(f"Seeds: {', '.join(f'`{p}`' for p in positive)}")
    if negative:
        print(f"Avoid: {', '.join(f'`{n}`' for n in negative)}")
    print(f"\nFound **{len(papers)}** recommendations\n")
    for i, p in enumerate(papers, 1):
        print(format_paper(p, i))
    print()


if __name__ == "__main__":
    main()
