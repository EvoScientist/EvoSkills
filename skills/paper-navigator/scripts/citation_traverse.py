#!/usr/bin/env python3
"""Traverse citation graphs via Semantic Scholar API.

Supports forward citations (who cited this), backward citations
(references), and co-citation discovery.
"""

from __future__ import annotations

import argparse
import re
import sys
import time

import httpx

from utils import (
    S2_BASE,
    s2_headers,
    request_with_retry,
    normalize_paper_id,
    add_output_args,
    emit_results,
    fetch_citations_paginated,
)


# Generic English + paper-title filler words. Keep the list small — the
# goal of the seed-sanity check is to detect 0% topical overlap between
# the seed title and the returned papers, not to do real NLP. Stopwords
# get dropped from both sides of the comparison.
_TITLE_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "for",
        "with",
        "in",
        "on",
        "at",
        "to",
        "from",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "via",
        "based",
        "using",
        "use",
        "uses",
        "applied",
        "approach",
        "approaches",
        "method",
        "methods",
        "study",
        "studies",
        "analysis",
        "analyses",
        "review",
        "reviews",
        "survey",
        "surveys",
        "novel",
        "new",
        "paper",
        "papers",
        "research",
        "work",
        "works",
        "model",
        "models",
        "system",
        "systems",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "as",
        "but",
        "if",
        "into",
        "across",
        "between",
        "among",
        "than",
        "such",
        "more",
        "most",
        "very",
        "much",
        "less",
        "least",
    }
)


def _seed_title_tokens(title: str) -> set[str]:
    """Tokenize a paper title into the set of distinguishing words.

    Lowercases, drops stopwords, drops pure-numeric tokens, drops anything
    under 4 chars. The remaining tokens are what we expect ANY topically
    related citer/reference to share with the seed. Accepts tokens that
    start with a digit ("4Diffusion", "3D-aware") as long as they also
    contain at least one letter.
    """
    if not title:
        return set()
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]*", title.lower())
    keepers: set[str] = set()
    for tok in tokens:
        if len(tok) < 4:
            continue
        if tok in _TITLE_STOPWORDS:
            continue
        # Drop pure-numeric tokens (years, version numbers).
        if not re.search(r"[a-z]", tok):
            continue
        keepers.add(tok)
    return keepers


def _fetch_seed_title(paper_id: str) -> str | None:
    """Look up just the seed paper's title via S2. Returns None on any
    failure — the sanity check is best-effort and never blocks the
    main fetch path."""
    try:
        with httpx.Client(timeout=10) as client:
            data = request_with_retry(
                client,
                f"{S2_BASE}/paper/{paper_id}",
                {"fields": "title"},
                s2_headers(),
            )
        title = data.get("title")
        return title if isinstance(title, str) and title.strip() else None
    except Exception:
        return None


# Sample size below which the 0-overlap signal is too noisy to act on.
# A 1- or 2-paper return is often a legitimately empty / sparse seed,
# not a wrong-id smell.
_SEED_SANITY_MIN_RETURNED = 5


def _seed_sanity_check(
    seed_paper_id: str,
    returned_papers: list[dict],
    direction: str,
) -> None:
    """Warn loudly when 0 of N returned papers share any distinguishing
    title token with the seed.

    Catches the typo'd / truncated CorpusId failure mode where the wrong
    seed silently returns unrelated papers (e.g. a video-generation seed
    suddenly producing valve-defect-detection citers). The check is cheap
    (one S2 metadata call) and only fires when the signal is strong
    (≥5 returned papers, 0 of which share any seed token) — false
    positives on a legitimately niche seed are unlikely because even
    cross-domain citers usually share some technical vocabulary with
    their seed.
    """
    if len(returned_papers) < _SEED_SANITY_MIN_RETURNED:
        return
    seed_title = _fetch_seed_title(seed_paper_id)
    if not seed_title:
        return
    seed_tokens = _seed_title_tokens(seed_title)
    if not seed_tokens:
        return  # title is all stopwords / short tokens — uninformative

    matched = 0
    for p in returned_papers:
        ptitle = (p.get("title") or "").lower()
        if not ptitle:
            continue
        if any(tok in ptitle for tok in seed_tokens):
            matched += 1
    if matched > 0:
        return  # at least some signal — assume real

    # Loud warning — the agent probably typed the wrong id.
    sample_titles = [
        (p.get("title") or "")[:80].strip()
        for p in returned_papers[:3]
        if p.get("title")
    ]
    print(
        "\n🚨 SEED SANITY WARNING — citation_traverse may be on the wrong seed",
        file=sys.stderr,
    )
    print(
        f"  Seed paper_id: {seed_paper_id!r}",
        file=sys.stderr,
    )
    print(
        f"  Seed title:    {seed_title[:120]!r}",
        file=sys.stderr,
    )
    print(
        f"  Direction:     {direction}; returned {len(returned_papers)} papers",
        file=sys.stderr,
    )
    print(
        f"  Seed tokens checked: {sorted(seed_tokens)[:10]}"
        + (" …" if len(seed_tokens) > 10 else ""),
        file=sys.stderr,
    )
    print(
        "  None of the returned titles share any distinguishing seed "
        "token. Sample returned titles:",
        file=sys.stderr,
    )
    for t in sample_titles:
        print(f"    - {t!r}", file=sys.stderr)
    print(
        "  NEXT: verify the seed id is correct (typo? truncated SHA? "
        'wrong CorpusId?). Use `match_paper_by_title.py --title "..."` '
        'or `scholar_search.py --query "..."` to look up the canonical id.\n',
        file=sys.stderr,
    )


S2_FIELDS = "paperId,corpusId,externalIds,title,authors,year,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf"

# Extended fields for smart sorting — includes citation context metadata
S2_CITATION_FIELDS = "paperId,externalIds,title,authors,year,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,contexts,isInfluential"

# Full fields for enrichment (includes tldr, abstract, venue)
ENRICH_FIELDS = "paperId,externalIds,title,authors,year,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,tldr,abstract,publicationVenue"


def _paged_citation_fetch(
    c: httpx.Client,
    paper_id: str,
    endpoint: str,
    nested_key: str,
    fields: str,
    smart: bool,
    limit: int,
) -> list[dict]:
    """Page through /paper/{id}/{citations|references} until ``limit`` items
    are collected or the API reports no more (`next` absent).

    Honors smart mode by attaching `_is_influential` / `_context_count` per
    paper. Page size = min(remaining, 1000). Bounded at offset 9000 to match
    the cap S2 enforces on these endpoints.
    """
    results: list[dict] = []
    offset = 0
    while len(results) < limit and offset < 9000:
        page_size = min(limit - len(results), 1000)
        params = {"fields": fields, "limit": page_size, "offset": offset}
        data = request_with_retry(
            c, f"{S2_BASE}/paper/{paper_id}/{endpoint}", params, s2_headers()
        )
        page = data.get("data") or []
        if not page:
            break
        for item in page:
            paper = item.get(nested_key)
            if not paper:
                continue
            if smart:
                paper["_is_influential"] = bool(item.get("isInfluential"))
                contexts = item.get("contexts") or []
                paper["_context_count"] = len(contexts)
            results.append(paper)
        nxt = data.get("next")
        if nxt is None:
            break
        offset = nxt
    return results


def get_citations(
    paper_id: str,
    limit: int = 20,
    client: httpx.Client | None = None,
    smart: bool = False,
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[dict]:
    """Forward citations: papers that cite this paper.

    Pages via offset until ``limit`` items are collected or the API reports
    no more. For year-filtered or very large requests, delegates to
    fetch_citations_paginated which year-slices to bypass the 10K offset cap.

    Note: S2 returns citations in a stable but roughly reverse-chronological
    order. For high-citation seeds, recent citers dominate the first page;
    use ``smart=True`` and re-rank by ``smart_score`` to surface influential
    older citers within the fetched window.
    """
    # Year-filtered or oversized requests need year-slicing
    if not smart and (limit > 1000 or year_from is not None or year_to is not None):
        return fetch_citations_paginated(
            paper_id,
            "forward",
            limit,
            S2_FIELDS,
            year_from=year_from,
            year_to=year_to,
        )

    fields = (
        f"contexts,isInfluential,citingPaper.{S2_FIELDS}"
        if smart
        else f"citingPaper.{S2_FIELDS}"
    )

    if client:
        return _paged_citation_fetch(
            client,
            paper_id,
            "citations",
            "citingPaper",
            fields,
            smart,
            limit,
        )
    with httpx.Client() as c:
        return _paged_citation_fetch(
            c,
            paper_id,
            "citations",
            "citingPaper",
            fields,
            smart,
            limit,
        )


def get_references(
    paper_id: str,
    limit: int = 20,
    client: httpx.Client | None = None,
    smart: bool = False,
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[dict]:
    """Backward citations: papers this paper references.

    Pages via offset until ``limit`` items are collected or the API reports
    no more. Year-filtered or oversized requests delegate to
    fetch_citations_paginated.
    """
    if not smart and (limit > 1000 or year_from is not None or year_to is not None):
        return fetch_citations_paginated(
            paper_id,
            "backward",
            limit,
            S2_FIELDS,
            year_from=year_from,
            year_to=year_to,
        )

    fields = (
        f"contexts,isInfluential,citedPaper.{S2_FIELDS}"
        if smart
        else f"citedPaper.{S2_FIELDS}"
    )

    if client:
        return _paged_citation_fetch(
            client,
            paper_id,
            "references",
            "citedPaper",
            fields,
            smart,
            limit,
        )
    with httpx.Client() as c:
        return _paged_citation_fetch(
            c,
            paper_id,
            "references",
            "citedPaper",
            fields,
            smart,
            limit,
        )


def get_co_citations(paper_id: str, limit: int = 15) -> list[dict]:
    """Co-citation: papers frequently cited alongside this paper.

    Strategy: get forward citations, collect their references,
    find most common papers (excluding the seed).
    """
    with httpx.Client() as client:
        # Get papers that cite the seed
        citers = get_citations(paper_id, limit=50, client=client)
        if not citers:
            return []

        # Sample up to 10 citers to stay within rate limits
        sample = citers[:10]
        ref_counts: dict[str, dict] = {}

        for citer in sample:
            citer_id = citer.get("paperId")
            if not citer_id:
                continue
            try:
                refs = get_references(citer_id, limit=100, client=client)
                for ref in refs:
                    rid = ref.get("paperId")
                    if rid and rid != paper_id:
                        if rid not in ref_counts:
                            ref_counts[rid] = {"paper": ref, "count": 0}
                        ref_counts[rid]["count"] += 1
                time.sleep(0.5)  # Rate limit courtesy
            except Exception:
                continue

    # Sort by co-citation frequency
    sorted_refs = sorted(ref_counts.values(), key=lambda x: x["count"], reverse=True)
    return [r["paper"] for r in sorted_refs[:limit]]


def smart_score(p: dict) -> float:
    """Compute composite score for smart sorting.

    Based on ASTA paper finder's snowball scoring:
      score = influential_weight × is_influential
            + context_weight × context_count
            - citation_penalty × citation_count

    Higher is better. Favors influential citations with many contexts,
    slightly penalizes extremely highly-cited papers (likely generic).
    """
    is_influential = 1.0 if p.get("_is_influential") else 0.0
    context_count = min(p.get("_context_count", 0), 10)  # cap at 10
    citation_count = p.get("citationCount") or 0

    score = (
        0.3 * is_influential
        + 0.1 * context_count
        - 0.005 * min(citation_count, 1000)  # cap penalty
    )
    return score


def enrich_papers(papers: list[dict]) -> list[dict]:
    """Batch-fetch full metadata to add tldr/abstract to citation results.

    The S2 citations endpoint doesn't return tldr/abstract on nested objects.
    This does a follow-up batch lookup via /paper/batch.
    """
    ids = [p["paperId"] for p in papers if p.get("paperId")]
    if not ids:
        return papers

    enriched_map: dict[str, dict] = {}
    with httpx.Client() as client:
        for i in range(0, len(ids), 500):
            chunk = ids[i : i + 500]
            try:
                data = request_with_retry(
                    client,
                    f"{S2_BASE}/paper/batch",
                    params={"fields": ENRICH_FIELDS},
                    headers=s2_headers(),
                    method="POST",
                    json_body={"ids": chunk},
                )
                if isinstance(data, list):
                    for p in data:
                        if p and p.get("paperId"):
                            enriched_map[p["paperId"]] = p
            except Exception as e:
                print(f"Enrich batch failed for chunk {i}: {e}", file=sys.stderr)

    # Merge: overlay enriched data, preserve smart-sort private fields
    result = []
    for p in papers:
        pid = p.get("paperId")
        if pid and pid in enriched_map:
            merged = enriched_map[pid]
            for key in ("_is_influential", "_context_count", "_smart_score"):
                if key in p:
                    merged[key] = p[key]
            result.append(merged)
        else:
            result.append(p)
    return result


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

    pid = p.get("paperId", "")
    ext = p.get("externalIds", {})
    arxiv = ext.get("ArXiv", "")
    id_str = f"S2:`{pid[:8]}…`"
    if arxiv:
        id_str = f"arXiv:`{arxiv}`"

    smart_info = ""
    if p.get("_is_influential") is not None:
        inf = "✓" if p.get("_is_influential") else "✗"
        ctx = p.get("_context_count", 0)
        sc = p.get("_smart_score", 0)
        smart_info = f" | influential:{inf} contexts:{ctx} score:{sc:.3f}"

    return f"{idx}. **{title}** — {author_str} ({year}) — ⭐{citations} — {id_str}{smart_info}{tldr}"


def main():
    parser = argparse.ArgumentParser(
        description="Traverse citation graphs via Semantic Scholar"
    )
    parser.add_argument(
        "--paper-id", "-p", required=True, help="Paper ID (S2, ArXiv:, DOI:, or URL)"
    )
    parser.add_argument(
        "--direction",
        "-d",
        required=True,
        choices=["forward", "backward", "co-citation"],
        help="Traversal direction",
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=20, help="Max results (default 20)"
    )
    parser.add_argument(
        "--min-citations", type=int, default=0, help="Minimum citation count filter"
    )
    parser.add_argument(
        "--year-min",
        type=int,
        default=None,
        help="Minimum publication year (inclusive)",
    )
    parser.add_argument(
        "--year-max",
        type=int,
        default=None,
        help="Maximum publication year (inclusive)",
    )
    parser.add_argument(
        "--smart-sort",
        action="store_true",
        help="Use composite scoring (influential citations, context count, citation penalty) instead of raw citation count",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Follow up with S2 batch lookup to add tldr/abstract to results",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument(
        "--no-sanity-check",
        action="store_true",
        help="Skip the seed-sanity check that warns when 0 of N returned "
        "titles share any token with the seed title (the smell test for a "
        "typo'd / truncated paper-id). Use when the seed is intentionally "
        "in a different topic from its citers/refs.",
    )
    add_output_args(parser)
    args = parser.parse_args()

    paper_id = normalize_paper_id(args.paper_id)

    direction_labels = {
        "forward": "Forward Citations (papers citing this paper)",
        "backward": "Backward Citations (papers referenced by this paper)",
        "co-citation": "Co-cited Papers (frequently cited alongside this paper)",
    }

    print(f"Fetching {args.direction} citations for {paper_id}...", file=sys.stderr)

    if args.direction == "forward":
        papers = get_citations(
            paper_id,
            args.limit,
            smart=args.smart_sort,
            year_from=args.year_min,
            year_to=args.year_max,
        )
    elif args.direction == "backward":
        papers = get_references(
            paper_id,
            args.limit,
            smart=args.smart_sort,
            year_from=args.year_min,
            year_to=args.year_max,
        )
    else:
        print(
            "Co-citation requires multiple API calls (may be slow)...",
            file=sys.stderr,
        )
        papers = get_co_citations(paper_id, args.limit)

    # Seed-sanity check: warn loudly if 0 of N returned titles share any
    # distinguishing token with the seed title. Fires BEFORE filtering so
    # the warning sees the raw API response, not a min-citations-filtered
    # subset that could artificially shrink to 0 papers.
    if not args.no_sanity_check:
        _seed_sanity_check(paper_id, papers, args.direction)

    # Filter by min citations
    if args.min_citations > 0:
        papers = [
            p for p in papers if (p.get("citationCount") or 0) >= args.min_citations
        ]

    # Apply year filters (client-side, for cases where paginated fetch wasn't used)
    if args.year_min is not None:
        papers = [p for p in papers if (p.get("year") or 0) >= args.year_min]
    if args.year_max is not None:
        papers = [p for p in papers if (p.get("year") or 9999) <= args.year_max]

    # Sort
    if args.smart_sort and args.direction in ("forward", "backward"):
        for p in papers:
            p["_smart_score"] = smart_score(p)
        papers.sort(key=lambda p: p["_smart_score"], reverse=True)
    else:
        papers.sort(key=lambda p: p.get("citationCount") or 0, reverse=True)
    papers = papers[: args.limit]

    # Enrich with tldr/abstract if requested
    if args.enrich and papers:
        print(f"Enriching {len(papers)} papers with tldr/abstract...", file=sys.stderr)
        papers = enrich_papers(papers)

    if not papers:
        print("No papers found.", file=sys.stderr)
        sys.exit(0)
    emit_results(
        papers,
        args,
        format_fn=format_paper,
        title=f"{direction_labels[args.direction]}",
    )


if __name__ == "__main__":
    main()
