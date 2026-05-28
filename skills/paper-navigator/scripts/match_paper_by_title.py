#!/usr/bin/env python3
"""Resolve paper title(s) to Semantic Scholar records via `/paper/search/match`.

Two orders of magnitude faster than full-text search for navigational
queries ("the AlphaGeometry paper", "BART by Lewis et al.") because S2
returns the single best exact-title match in one call instead of
ranking a hundred candidates.

Three modes:

* **single**  — `--title "..."` → one paper to stdout (markdown or JSON)
* **batch-file** — `--titles-file list.txt` (one title per line) →
  JSONL stream with one record per title (resolved or flagged miss)
* **batch-jsonl** — `--input papers.jsonl` (reads each row's `title`
  field) → JSONL output, carrying the original row's extra fields so
  gscholar / external lists get upgraded in place

When `/paper/search/match` returns no hit and `--fallback-search` is
set, falls back to the regular full-text search (top-1) so external
lists still resolve even when the title has a typo or punctuation
drift. Fallback hits are tagged `_source: "s2_search_fallback"`.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator

import httpx

from utils import (
    S2_BASE,
    RateLimitExhausted,
    add_output_args,
    emit_results,
    request_with_retry,
    s2_headers,
)

S2_FIELDS = (
    "paperId,corpusId,externalIds,title,authors,year,"
    "citationCount,influentialCitationCount,tldr,"
    "isOpenAccess,openAccessPdf,publicationVenue,abstract"
)


def match_title(client: httpx.Client, title: str) -> dict | None:
    """Call S2 `/paper/search/match` for a single title.

    Returns the matched paper dict on success, or None if S2 has no
    match (404 or empty data). Never raises for the no-match case —
    that's expected and handled in batch mode.
    """
    title = (title or "").strip()
    if not title:
        return None
    data = request_with_retry(
        client,
        f"{S2_BASE}/paper/search/match",
        params={"query": title, "fields": S2_FIELDS},
        headers=s2_headers(),
    )
    rows = (data or {}).get("data") or []
    if not rows:
        return None
    paper = rows[0]
    paper.setdefault("_source", "s2_match")
    return paper


def fallback_full_text(client: httpx.Client, title: str) -> dict | None:
    """Top-1 result from S2 full-text search. Used when match misses."""
    try:
        data = request_with_retry(
            client,
            f"{S2_BASE}/paper/search",
            params={"query": title, "limit": 1, "fields": S2_FIELDS},
            headers=s2_headers(),
        )
    except RateLimitExhausted:
        return None
    rows = (data or {}).get("data") or []
    if not rows:
        return None
    paper = rows[0]
    paper["_source"] = "s2_search_fallback"
    return paper


def resolve_one(
    client: httpx.Client, title: str, fallback: bool
) -> tuple[dict | None, str]:
    """Resolve a single title. Returns (paper, status).

    status ∈ {"matched", "fallback", "miss"}.
    """
    paper = match_title(client, title)
    if paper is not None:
        return paper, "matched"
    if fallback:
        fb = fallback_full_text(client, title)
        if fb is not None:
            return fb, "fallback"
    return None, "miss"


# ── Input readers ────────────────────────────────────────────────────


def _iter_titles_file(path: str) -> Iterator[tuple[str, dict]]:
    """Yield (title, extra_fields) from a plain-text one-title-per-line file."""
    with open(path) as f:
        for line in f:
            title = line.strip()
            if title:
                yield title, {}


def _iter_jsonl_titles(path: str) -> Iterator[tuple[str, dict]]:
    """Yield (title, original_row) from a JSONL file's `title` field.

    The original row is returned so we can merge match metadata back
    into it — downstream callers often want the resolved paperId
    attached to their existing fields (e.g. gscholar_search hits, a
    BibTeX dump with extra tags).
    """
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(
                    f"Warning: skipping malformed JSONL line: {line[:80]}",
                    file=sys.stderr,
                )
                continue
            title = (row.get("title") or "").strip()
            if title:
                yield title, row


# ── Output formatting (single mode) ──────────────────────────────────


def _truncate(text: str | None, max_len: int = 200) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


def format_paper(p: dict, idx: int | None = None) -> str:
    """Markdown formatter (mirrors scholar_search.format_paper layout)."""
    prefix = f"### {idx}. " if idx is not None else "### "
    title = p.get("title", "Unknown")
    year = p.get("year", "?")
    citations = p.get("citationCount")
    influential = p.get("influentialCitationCount")

    authors = p.get("authors") or []
    author_str = ", ".join(a.get("name", "") for a in authors[:5])
    if len(authors) > 5:
        author_str += f" et al. ({len(authors)} authors)"

    venue = ""
    if p.get("publicationVenue"):
        venue = p["publicationVenue"].get("name", "") or ""

    tldr = ""
    if p.get("tldr") and p["tldr"].get("text"):
        tldr = f"\n> **TLDR:** {p['tldr']['text']}"

    abstract = ""
    if not tldr and p.get("abstract"):
        abstract = f"\n> {_truncate(p['abstract'])}"

    pdf = ""
    if p.get("openAccessPdf") and p["openAccessPdf"].get("url"):
        pdf = f"\n📄 [Open Access PDF]({p['openAccessPdf']['url']})"

    paper_id = p.get("paperId", "") or ""
    ext = p.get("externalIds") or {}
    ids_line = f"S2: `{paper_id}`"
    if ext.get("ArXiv"):
        ids_line += f" | arXiv: `{ext['ArXiv']}`"
    if ext.get("DOI"):
        ids_line += f" | DOI: `{ext['DOI']}`"

    source_note = ""
    if p.get("_source") == "s2_search_fallback":
        source_note = "\n*(via full-text fallback — exact match missed)*"

    cit_str = (
        f"**{citations}** (influential: {influential})"
        if citations is not None
        else "N/A"
    )

    return f"""{prefix}{title}
**{author_str}** ({year}) — {venue}
Citations: {cit_str}
{ids_line}{tldr}{abstract}{pdf}{source_note}
"""


# ── CLI ──────────────────────────────────────────────────────────────


def _run_single(args) -> int:
    with httpx.Client() as client:
        paper, status = resolve_one(client, args.title, fallback=args.fallback_search)

    if paper is None:
        print(f"No match for: {args.title!r}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(paper, indent=2))
    else:
        print(format_paper(paper))
        if status == "fallback":
            print(
                "*(resolved via fallback search — exact title missed)*", file=sys.stderr
            )
    return 0


def _run_batch(args) -> int:
    # Collect input
    if args.titles_file and args.input:
        print(
            "Error: --titles-file and --input are mutually exclusive", file=sys.stderr
        )
        return 1
    if args.titles_file:
        pairs = list(_iter_titles_file(args.titles_file))
    else:
        pairs = list(_iter_jsonl_titles(args.input))

    if not pairs:
        print("No titles to resolve.", file=sys.stderr)
        return 1

    print(
        f"Resolving {len(pairs)} title(s) via /paper/search/match"
        + (" (with full-text fallback)" if args.fallback_search else "")
        + "...",
        file=sys.stderr,
    )

    resolved: list[dict] = []
    matched = fallback_used = missed = 0
    with httpx.Client() as client:
        for title, original in pairs:
            paper, status = resolve_one(client, title, fallback=args.fallback_search)
            if paper is None:
                missed += 1
                if args.keep_misses:
                    resolved.append(
                        {
                            "_query_title": title,
                            "_status": "miss",
                            **original,
                        }
                    )
                continue
            if status == "fallback":
                fallback_used += 1
            else:
                matched += 1
            # Preserve caller-supplied fields (e.g. gscholar link), with
            # match result taking precedence on overlap.
            merged = {**original, **paper}
            merged["_query_title"] = title
            merged["_status"] = status
            resolved.append(merged)

    print(
        f"Match: {matched} exact, {fallback_used} fallback, {missed} miss",
        file=sys.stderr,
    )
    emit_results(
        resolved,
        args,
        format_fn=format_paper,
        title=f"Title-match results ({len(resolved)}/{len(pairs)})",
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Resolve paper title(s) to Semantic Scholar records via "
            "/paper/search/match. ~100× faster than full-text search for "
            'navigational queries ("the AlphaGeometry paper", '
            '"BART by Lewis et al.").'
        ),
    )
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--title", "-t", help="Single title to resolve")
    group.add_argument(
        "--titles-file",
        help="Plain-text file with one title per line (batch mode).",
    )
    group.add_argument(
        "--input",
        "-i",
        help=(
            "JSONL file; each row must have a `title` field. Row fields "
            "carry through into the output (lets external lists be "
            "upgraded in place)."
        ),
    )
    ap.add_argument(
        "--fallback-search",
        action="store_true",
        help=(
            "When exact match misses, fall back to /paper/search top-1 "
            "(catches typos / punctuation drift). Fallback hits are tagged "
            '`_source: "s2_search_fallback"`.'
        ),
    )
    ap.add_argument(
        "--keep-misses",
        action="store_true",
        help=(
            "In batch mode, include unresolved titles as "
            "{_query_title, _status: 'miss', ...} rows."
        ),
    )
    ap.add_argument("--json", action="store_true", help="Output raw JSON.")
    add_output_args(ap)
    args = ap.parse_args()

    if args.title:
        return _run_single(args)
    return _run_batch(args)


if __name__ == "__main__":
    sys.exit(main())
