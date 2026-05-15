#!/usr/bin/env python3
"""Fetch full paper text using Semantic Scholar metadata + Jina Reader.

Resolves paper ID to a URL, then uses Jina Reader (r.jina.ai) to
convert the paper page to clean Markdown.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

from utils import (
    S2_BASE,
    JINA_PREFIX,
    s2_headers,
    jina_headers,
    request_with_retry,
    normalize_paper_id,
    _strip_arxiv_version,
    print_s2_key_tip,
)

PAPERS_DIR = Path(os.environ.get("PAPERS_DIR", str(Path.home() / "papers")))


def resolve_paper_url(paper_id: str) -> tuple[str, dict]:
    """Resolve paper ID to best available URL + metadata."""
    pid = normalize_paper_id(paper_id)

    # No-key fast path: if S2_API_KEY unset AND we have a direct arXiv ID,
    # skip the S2 metadata fetch (which costs ~45s under no-key rate limit).
    # The arxiv URL works directly with Jina Reader, and arxiv ID is all we need.
    no_key = not os.environ.get("S2_API_KEY")
    if no_key and pid.startswith("ArXiv:"):
        arxiv_id = pid[6:]
        print(
            "ℹ️  No S2_API_KEY — skipping S2 metadata fetch, using arXiv URL directly.",
            file=sys.stderr,
        )
        result = (
            f"https://arxiv.org/abs/{arxiv_id}",
            {
                "externalIds": {"ArXiv": arxiv_id},
                "title": "(metadata not fetched in no-key mode; use --paper-id with key for full TLDR/citations)",
            },
        )
        print_s2_key_tip()
        return result

    fields = "paperId,externalIds,title,authors,year,citationCount,tldr,isOpenAccess,openAccessPdf,abstract"

    with httpx.Client() as client:
        meta = request_with_retry(
            client, f"{S2_BASE}/paper/{pid}", {"fields": fields}, s2_headers()
        )

    # Determine best URL
    url = ""
    # Prefer OA PDF
    if meta.get("openAccessPdf") and meta["openAccessPdf"].get("url"):
        url = meta["openAccessPdf"]["url"]
    # Fallback: arXiv abstract page (Jina handles HTML well)
    elif meta.get("externalIds", {}).get("ArXiv"):
        arxiv_id = meta["externalIds"]["ArXiv"]
        url = f"https://arxiv.org/abs/{arxiv_id}"
    # Fallback: DOI
    elif meta.get("externalIds", {}).get("DOI"):
        doi = meta["externalIds"]["DOI"]
        url = f"https://doi.org/{doi}"

    return url, meta


def fetch_via_jina(url: str, limit_chars: int = 50000) -> str:
    """Fetch URL content as Markdown via Jina Reader."""
    jina_url = f"{JINA_PREFIX}{url}"

    with httpx.Client() as client:
        text = request_with_retry(
            client,
            jina_url,
            headers=jina_headers(),
            timeout=60,
            parse_json=False,
            follow_redirects=True,
        )

    if len(text) > limit_chars:
        text = (
            text[:limit_chars] + f"\n\n---\n*[Truncated at {limit_chars} characters]*"
        )
    return text


def format_metadata(meta: dict) -> str:
    """Format paper metadata header."""
    title = meta.get("title", "Unknown")
    authors = meta.get("authors", [])
    author_str = ", ".join(a.get("name", "") for a in authors[:5])
    if len(authors) > 5:
        author_str += f" et al. ({len(authors)} authors)"
    year = meta.get("year", "?")
    citations = meta.get("citationCount", 0)

    tldr = ""
    if meta.get("tldr") and meta["tldr"].get("text"):
        tldr = f"\n> **TLDR:** {meta['tldr']['text']}\n"

    ext = meta.get("externalIds", {})
    ids = []
    if ext.get("ArXiv"):
        ids.append(f"arXiv: `{ext['ArXiv']}`")
    if ext.get("DOI"):
        ids.append(f"DOI: `{ext['DOI']}`")
    ids.append(f"S2: `{meta.get('paperId', '')}`")

    return (
        f"# {title}\n\n"
        f"**{author_str}** ({year}) | Citations: {citations}\n"
        f"{' | '.join(ids)}\n"
        f"{tldr}\n---\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Fetch paper full text via Jina Reader"
    )
    parser.add_argument("--paper-id", "-p", help="Paper ID (S2, ArXiv:, DOI:, or URL)")
    parser.add_argument("--url", "-u", help="Direct URL to fetch (skip S2 lookup)")
    parser.add_argument(
        "--limit-chars",
        type=int,
        default=50000,
        help="Max output characters (default 50000)",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Only show metadata, skip full text",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Use $PAPERS_DIR/<id>/content.md cache (read if exists, write after fetch)",
    )
    args = parser.parse_args()

    if not args.paper_id and not args.url:
        print("Error: --paper-id or --url required", file=sys.stderr)
        sys.exit(1)

    if args.url:
        # Direct URL mode
        url = args.url
        meta = {}
        # Try to get metadata from S2 if it looks like an arXiv URL
        if "arxiv.org" in url:
            arxiv_id = url.split("/abs/")[-1].split("/pdf/")[-1].removesuffix(".pdf")
            arxiv_id = _strip_arxiv_version(arxiv_id)
            try:
                _, meta = resolve_paper_url(f"ArXiv:{arxiv_id}")
            except Exception:
                pass
    else:
        url, meta = resolve_paper_url(args.paper_id)

    if args.json:
        output = {"metadata": meta, "url": url}
        if not args.metadata_only and url:
            content = fetch_via_jina(url, args.limit_chars)
            output["content"] = content
        print(json.dumps(output, indent=2, default=str))
        return

    if meta:
        print(format_metadata(meta))

    if args.metadata_only:
        if meta.get("abstract"):
            print(f"## Abstract\n\n{meta['abstract']}\n")
        return

    if not url:
        print("Error: no accessible URL found for this paper", file=sys.stderr)
        if meta.get("abstract"):
            print(f"\n## Abstract (full text not available)\n\n{meta['abstract']}\n")
        sys.exit(1)

    # Cache lookup (if --cache and we have an arxiv id key)
    arxiv_id = None
    ext = (meta or {}).get("externalIds", {}) or {}
    if ext.get("ArXiv"):
        arxiv_id = _strip_arxiv_version(ext["ArXiv"])

    if args.cache and arxiv_id:
        cached_md = PAPERS_DIR / arxiv_id / "content.md"
        if cached_md.exists():
            print(f"*Cache hit: {cached_md}*\n", file=sys.stderr)
            print(cached_md.read_text())
            return

    print(f"*Fetching from: {url}*\n", file=sys.stderr)
    content = fetch_via_jina(url, args.limit_chars)
    print(content)

    # Cache write (if --cache and we have an arxiv id key)
    if args.cache and arxiv_id:
        cache_dir = PAPERS_DIR / arxiv_id
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "content.md").write_text(content)
        print(f"\n*Cached to {cache_dir / 'content.md'}*", file=sys.stderr)


if __name__ == "__main__":
    main()
