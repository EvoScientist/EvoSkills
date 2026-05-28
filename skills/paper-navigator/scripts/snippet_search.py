#!/usr/bin/env python3
"""Search for text snippets within papers using Semantic Scholar API.

Finds ~500-word passages matching a query within specific papers
or across the corpus. Useful for finding specific claims, methods,
or results within papers.
"""

from __future__ import annotations

import argparse
import sys

import httpx

from utils import (
    S2_BASE,
    s2_headers,
    request_with_retry,
    normalize_paper_id,
    check_s2_circuit,
    s2_circuit_breaker,
    add_output_args,
    emit_results,
)


def _has_body_snippet(results: list[dict]) -> bool:
    """True if at least one result is a body-text snippet (not just title/abstract)."""
    for r in results:
        snippet = r.get("snippet") or {}
        if isinstance(snippet, dict) and snippet.get("snippetKind") == "body":
            return True
    return False


def snippet_search(
    query: str,
    paper_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Search for text snippets matching query.

    If paper_id is given, searches within that paper.
    Otherwise searches across the corpus.

    Uses the S2 snippet search endpoint which returns ~500-word
    passages from paper title, abstract, and body text.
    """
    check_s2_circuit()

    pid: str | None = None
    if paper_id:
        pid = normalize_paper_id(paper_id)
        if pid.isdigit():
            pid = f"CorpusId:{pid}"

    url = f"{S2_BASE}/snippet/search"
    params: dict = {
        "query": query,
        "limit": min(limit, 100),
    }
    if pid:
        params["paperIds"] = pid

    with httpx.Client() as client:
        try:
            data = request_with_retry(client, url, params, s2_headers())
            s2_circuit_breaker.record_success()
        except Exception as e:
            s2_circuit_breaker.record_failure()
            print(f"Snippet search failed: {e}", file=sys.stderr)
            return []

    results = data.get("data") or []

    # Upgrade fulltext_status to 'indexed' for papers where we got real body text.
    return results


def snippet_search_multi(
    query: str,
    paper_ids: list[str],
    limit: int = 50,
    fallback_per_paper: bool = True,
    per_paper_limit: int = 5,
) -> list[dict]:
    """Search snippets across corpus, filter to specific papers client-side.

    Instead of calling the snippet API once per paper (1 req/sec rate limit),
    this does a single corpus-wide search and filters results by corpusId.
    Turns N API calls into 1.

    Fallback: when the corpus-wide query returns zero matches for ANY of the
    requested papers (a common sharp edge of the S2 snippet API when too many
    paperIds are passed at once), automatically retry per-paper. Papers
    already marked `fulltext_status='not_indexed'` in the registry are
    skipped by `snippet_search` itself, so the per-paper path is cheap for
    pools that have been probed.
    """
    all_results = snippet_search(query, paper_id=None, limit=limit)

    # Normalize target IDs: "CorpusId:123" → "123", plain "123" → "123"
    target_ids = set()
    for pid in paper_ids:
        clean = pid.replace("CorpusId:", "").strip()
        target_ids.add(clean)

    filtered = [
        r
        for r in all_results
        if str(r.get("paper", {}).get("corpusId", "")) in target_ids
    ]

    if filtered or not fallback_per_paper:
        return filtered

    print(
        f"snippet_search_multi: corpus-wide query matched 0 of {len(paper_ids)} "
        "papers; falling back to per-paper calls",
        file=sys.stderr,
    )
    collected: list[dict] = []
    for pid in paper_ids:
        per = snippet_search(query, paper_id=pid, limit=per_paper_limit)
        collected.extend(per)
    return collected


def format_snippet(s: dict, idx: int) -> str:
    """Format a snippet result as Markdown."""
    paper = s.get("paper", {})
    title = paper.get("title", "Unknown")
    year = paper.get("year", "?")
    pid = paper.get("paperId", "")

    snippet_text = s.get("snippet", {}).get("text", "")
    score = s.get("score", 0)

    return (
        f"{idx}. **{title}** ({year}) — S2:`{pid[:12]}...`\n"
        f"   Score: {score:.3f}\n"
        f"   > {snippet_text}\n"
    )


def format_snippet_summary(s: dict, idx: int) -> str:
    """Format a snippet as a compact one-line summary.

    Shows paper title, year, corpusId, snippet kind, score, and a
    short preview (~60 chars). Keeps context usage ~10x smaller than
    full snippets — use for browsing before fetching full text via
    snippet_match.
    """
    paper = s.get("paper", {})
    title = paper.get("title", "Unknown")
    year = paper.get("year", "?")
    corpus_id = paper.get("corpusId", "?")

    raw = s.get("snippet", {})
    if isinstance(raw, dict):
        text = raw.get("text", "")
        kind = raw.get("snippetKind", "?")
    else:
        text = str(raw)
        kind = "?"

    score = s.get("score", 0)
    preview = text[:60].replace("\n", " ")
    if len(text) > 60:
        preview += "..."

    return f'{idx}. [{score:.2f}] [{kind}] {title[:70]} ({year}) CID:{corpus_id}  "{preview}"'


def main():
    parser = argparse.ArgumentParser(
        description="Search for text snippets within papers"
    )
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument(
        "--paper-id", "-p", help="Search within specific paper (direct API filter)"
    )
    parser.add_argument(
        "--paper-ids",
        help="Comma-separated CorpusIds to filter to (corpus-wide search + client-side filter, 1 API call)",
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Max results (default 10)"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Compact one-line-per-result output (~10x smaller context). "
        "Shows title, year, corpusId, kind, score, and 60-char preview. "
        "Use for browsing before fetching full text via snippet_match.",
    )
    add_output_args(parser)
    args = parser.parse_args()

    if args.paper_ids:
        ids = [pid.strip() for pid in args.paper_ids.split(",") if pid.strip()]
        results = snippet_search_multi(args.query, ids, args.limit)
    else:
        results = snippet_search(args.query, args.paper_id, args.limit)

    if not results:
        print("No snippets found.", file=sys.stderr)
        sys.exit(0)

    fmt = format_snippet_summary if args.summary else format_snippet
    emit_results(
        results,
        args,
        format_fn=fmt,
        title=f'Snippet Search: "{args.query}"',
    )


if __name__ == "__main__":
    main()
