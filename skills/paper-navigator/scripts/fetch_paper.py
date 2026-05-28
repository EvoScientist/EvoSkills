#!/usr/bin/env python3
"""Fetch full paper text using Semantic Scholar metadata + Jina Reader.

Resolves paper ID to a URL, then uses Jina Reader (r.jina.ai) to
convert the paper page to clean Markdown.

By default, saves full text to artifacts/papers/{paper_id}.md and
prints only a compact summary (metadata + abstract) to stdout.
Use --full-stdout to print the full text to stdout instead.
"""

import argparse
import json
import os
import re
import sys

import httpx

from utils import (
    S2_BASE,
    JINA_PREFIX,
    s2_headers,
    jina_headers,
    request_with_retry,
    normalize_paper_id,
    _strip_arxiv_version,
)


def _resolve_papers_dir(cli_arg: str | None) -> str | None:
    """Resolve the papers directory: CLI flag > env var > None.

    No on-disk default — `fetch_paper` previously dumped MB-sized
    Markdown files into ./artifacts/papers/ from any working directory,
    which leaked disk fast across many runs. The user must opt in via
    either --papers-dir or PAPER_NAV_PAPERS_DIR, since dumping fulltext
    into the user's cwd silently is worse than erroring.
    """
    if cli_arg:
        return cli_arg
    return os.environ.get("PAPER_NAV_PAPERS_DIR") or None


# Sentinel for argparse default — distinguishes "no flag passed" from "passed empty"
_PAPERS_DIR_UNSET = object()


UNPAYWALL_API = "https://api.unpaywall.org/v2"


def _unpaywall_lookup(doi: str) -> str | None:
    """Query Unpaywall for an OA copy of a paper by DOI.

    Returns the best OA URL or None. Free API, no auth — just an email param.
    """
    email = os.environ.get(
        "UNPAYWALL_EMAIL", "paper-navigator@users.noreply.github.com"
    )
    url = f"{UNPAYWALL_API}/{doi}?email={email}"
    try:
        with httpx.Client() as client:
            resp = client.get(url, timeout=10, follow_redirects=True)
            if resp.status_code != 200:
                return None
            data = resp.json()
            # best_oa_location has the most usable OA copy
            best = data.get("best_oa_location") or {}
            oa_url = best.get("url_for_pdf") or best.get("url") or ""
            if oa_url:
                print(f"Unpaywall: found OA copy → {oa_url}", file=sys.stderr)
                return oa_url
    except Exception as e:
        print(f"Unpaywall lookup failed: {e}", file=sys.stderr)
    return None


def resolve_paper_url(paper_id: str) -> tuple[str, dict]:
    """Resolve paper ID to best available URL + metadata.

    Fallback chain:
      S2 openAccessPdf → arXiv → Unpaywall (by DOI) → DOI URL
    """
    pid = normalize_paper_id(paper_id)

    fields = "paperId,corpusId,externalIds,title,authors,year,citationCount,tldr,isOpenAccess,openAccessPdf,abstract"

    with httpx.Client() as client:
        meta = request_with_retry(
            client, f"{S2_BASE}/paper/{pid}", {"fields": fields}, s2_headers()
        )

    # Determine best URL
    url = ""
    doi = (meta.get("externalIds") or {}).get("DOI", "")

    # 1. Prefer S2's OA PDF
    if meta.get("openAccessPdf") and meta["openAccessPdf"].get("url"):
        url = meta["openAccessPdf"]["url"]
    # 2. Fallback: arXiv abstract page (Jina handles HTML well)
    elif (meta.get("externalIds") or {}).get("ArXiv"):
        arxiv_id = meta["externalIds"]["ArXiv"]
        url = f"https://arxiv.org/abs/{arxiv_id}"
    # 3. Fallback: Unpaywall (often finds green OA copies S2 missed)
    elif doi:
        oa_url = _unpaywall_lookup(doi)
        if oa_url:
            url = oa_url
        else:
            # 4. Last resort: DOI URL (may hit a paywall, but Jina can sometimes extract)
            url = f"https://doi.org/{doi}"

    return url, meta


def _strip_boilerplate(text: str) -> str:
    """Strip common website boilerplate (cookie consent, navigation) from fetched text.

    Looks for the first Markdown heading that signals actual paper content
    (Abstract, Introduction, Summary) and drops everything before it.
    """
    # Find the first content heading (## Abstract, ## Introduction, etc.)
    match = re.search(
        r"^(#+\s*(?:Abstract|Introduction|Summary|Background|1\s))",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    if match and match.start() > 200:
        # Only strip if there's significant boilerplate (>200 chars) before the heading
        text = text[match.start() :]
    return text


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

    text = _strip_boilerplate(text)

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


def _safe_filename(paper_id: str) -> str:
    """Convert paper ID to a safe filename."""
    return re.sub(r"[^\w\-.]", "_", paper_id)


def save_full_text(
    paper_id: str, metadata_header: str, content: str, papers_dir: str
) -> str:
    """Save full text to file. Returns the file path."""
    os.makedirs(papers_dir, exist_ok=True)
    filename = _safe_filename(paper_id) + ".md"
    filepath = os.path.join(papers_dir, filename)
    with open(filepath, "w") as f:
        f.write(metadata_header)
        f.write("\n")
        f.write(content)
    return filepath


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
        help="Max paper text length in characters (default 50000)",
    )
    parser.add_argument(
        "--max-output",
        type=int,
        default=2000,
        help="Max stdout output chars (default 2000). Full text saved to file regardless.",
    )
    parser.add_argument(
        "--full-stdout",
        action="store_true",
        help="Print full text to stdout (old behavior, not recommended for agent use)",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Only show metadata, skip full text",
    )
    parser.add_argument(
        "--papers-dir",
        default=None,
        help="Directory to save full text files. Defaults to "
        "$PAPER_NAV_PAPERS_DIR. No on-disk fallback — pass this or "
        "the env var, or use --metadata-only / --full-stdout to skip "
        "file writes.",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not args.paper_id and not args.url:
        print("Error: --paper-id or --url required", file=sys.stderr)
        sys.exit(1)

    # Resolve where to save full text. Required unless we're not saving.
    papers_dir = _resolve_papers_dir(args.papers_dir)
    will_save_full_text = not args.metadata_only
    if will_save_full_text and not papers_dir:
        print(
            "Error: no papers directory configured. Either:\n"
            "  • set PAPER_NAV_PAPERS_DIR=/your/path explicitly,\n"
            "  • pass --papers-dir /your/path, or\n"
            "  • use --metadata-only / --full-stdout to skip file writes.",
            file=sys.stderr,
        )
        sys.exit(2)

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
            # Save to file
            pid = meta.get("paperId", args.paper_id or args.url)
            filepath = save_full_text(
                pid, format_metadata(meta) if meta else "", content, papers_dir
            )
            output["full_text_path"] = filepath
            if not args.full_stdout:
                output["content"] = (
                    content[: args.max_output] + "..."
                    if len(content) > args.max_output
                    else content
                )
            else:
                output["content"] = content
        print(json.dumps(output, indent=2, default=str))
        return

    metadata_header = format_metadata(meta) if meta else ""

    if args.metadata_only:
        if metadata_header:
            print(metadata_header)
        if meta.get("abstract"):
            print(f"## Abstract\n\n{meta['abstract']}\n")
        return

    if not url:
        print("Error: no accessible URL found for this paper", file=sys.stderr)
        if meta.get("abstract"):
            print(f"\n## Abstract (full text not available)\n\n{meta['abstract']}\n")
        sys.exit(1)

    print(f"*Fetching from: {url}*\n", file=sys.stderr)
    content = fetch_via_jina(url, args.limit_chars)

    # Save full text to file
    pid = meta.get("paperId", args.paper_id or args.url)
    filepath = save_full_text(pid, metadata_header, content, papers_dir)
    print(f"Full text saved to: {filepath}", file=sys.stderr)

    if args.full_stdout:
        # Old behavior: print everything to stdout
        if metadata_header:
            print(metadata_header)
        print(content)
    else:
        # New default: compact stdout output
        if metadata_header:
            print(metadata_header)
        if meta.get("abstract"):
            print(f"## Abstract\n\n{meta['abstract']}\n")
        print(f"**Full text ({len(content)} chars) saved to:** `{filepath}`")
        print(f"Use `read_file {filepath}` to read the full text.")


if __name__ == "__main__":
    main()
