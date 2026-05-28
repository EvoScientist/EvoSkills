#!/usr/bin/env python3
"""Get paper recommendations from Semantic Scholar.

Given seed papers (positive examples, optionally negative examples),
returns semantically similar papers.
"""

from __future__ import annotations

import argparse
import sys

import httpx

from utils import (
    S2_BASE,
    S2_RECOMMEND_BASE,
    s2_headers,
    request_with_retry,
    normalize_paper_id,
    add_output_args,
    emit_results,
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


def _request_recommendations(
    client: httpx.Client, pos_s2: list[str], neg_s2: list[str], limit: int
) -> list[dict]:
    body: dict = {"positivePaperIds": pos_s2}
    if neg_s2:
        body["negativePaperIds"] = neg_s2
    data = request_with_retry(
        client,
        f"{S2_RECOMMEND_BASE}/papers/",
        params={"fields": S2_FIELDS, "limit": min(limit, 500)},
        headers=s2_headers(),
        method="POST",
        json_body=body,
    )
    return data.get("recommendedPapers", [])


def recommend(
    positive_ids: list[str],
    negative_ids: list[str] | None = None,
    limit: int = 10,
    per_seed: bool = False,
) -> list[dict]:
    """Get recommendations based on seed papers.

    With ``per_seed=False`` (default): one S2 API call with all
    positives in the request body — S2 returns papers near the
    centroid of the seed cluster. Cheaper but tends to wash out
    sub-niches.

    With ``per_seed=True``: one S2 API call per positive seed, results
    concatenated. Each seed surfaces its own neighborhood. Higher recall
    on a diverse seed set at the cost of N API calls. Returned list
    keeps the first occurrence of each ``paperId`` so the caller sees a
    deduped stream; downstream registry insert is also dedup-safe via
    the ``paper_id`` PK.
    """
    with httpx.Client() as client:
        pos_s2 = [
            _resolve_to_s2_id(client, normalize_paper_id(pid)) for pid in positive_ids
        ]
        neg_s2 = [
            _resolve_to_s2_id(client, normalize_paper_id(pid))
            for pid in (negative_ids or [])
        ]

        if not per_seed or len(pos_s2) <= 1:
            return _request_recommendations(client, pos_s2, neg_s2, limit)

        seen: set[str] = set()
        merged: list[dict] = []
        for sid in pos_s2:
            results = _request_recommendations(client, [sid], neg_s2, limit)
            for p in results:
                pid = p.get("paperId") or ""
                if pid and pid in seen:
                    continue
                if pid:
                    seen.add(pid)
                merged.append(p)
        return merged


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
    parser.add_argument(
        "--per-seed",
        action="store_true",
        help=(
            "Fire one API call per positive seed and concatenate (deduped). "
            "Default is one combined call near the seed centroid; per-seed "
            "surfaces each seed's own neighborhood at the cost of N calls."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    add_output_args(parser)
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

    papers = recommend(positive, negative, args.limit, per_seed=args.per_seed)

    if not papers:
        print("No recommendations found.", file=sys.stderr)
        sys.exit(0)
    emit_results(
        papers,
        args,
        format_fn=format_paper,
        title="Paper Recommendations",
    )


if __name__ == "__main__":
    main()
