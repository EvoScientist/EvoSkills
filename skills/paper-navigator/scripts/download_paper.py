#!/usr/bin/env python3
"""Download paper PDFs to $PAPERS_DIR with metadata sidecar + index.

Single source of truth for moving a paper from "found on the web" to
"on disk and indexed". Other scripts (library_search, fetch_paper --cache)
read the index this writes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

from utils import (
    S2_BASE,
    s2_headers,
    request_with_retry,
    normalize_paper_id,
    _strip_arxiv_version,
)


PAPERS_DIR = Path(os.environ.get("PAPERS_DIR", str(Path.home() / "papers")))
INDEX_PATH = PAPERS_DIR / "index.json"

MIN_PDF_KB = 10  # arxiv skill convention: reject sub-10KB error pages
RATE_LIMIT_S = 1.0  # arxiv skill convention: 1s between downloads
DEFAULT_MAX_MB = 50  # skip oversized PDFs (huge appendices etc.)


def resolve_metadata(paper_id: str) -> dict:
    """Fetch S2 metadata for a paper. Returns dict with externalIds, openAccessPdf, etc."""
    pid = normalize_paper_id(paper_id)
    fields = (
        "paperId,externalIds,title,authors,year,citationCount,"
        "tldr,isOpenAccess,openAccessPdf,abstract,venue"
    )
    with httpx.Client() as client:
        meta = request_with_retry(
            client, f"{S2_BASE}/paper/{pid}", {"fields": fields}, s2_headers()
        )
    return meta


def choose_pdf_url(meta: dict) -> tuple[str, str]:
    """Pick best PDF URL + canonical key.

    Returns (url, key) where key is the directory name under PAPERS_DIR.
    Preference: arxiv.org/pdf/<id>.pdf (most reliable) > openAccessPdf.url.
    Raises ValueError if neither available.
    """
    ext = meta.get("externalIds", {}) or {}
    arxiv_id_raw = ext.get("ArXiv")
    if arxiv_id_raw:
        arxiv_id = _strip_arxiv_version(arxiv_id_raw)
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf", arxiv_id

    oa = (meta.get("openAccessPdf") or {}).get("url")
    if oa:
        # Use S2 paperId as key when no arXiv ID
        key = meta.get("paperId") or "unknown"
        return oa, key

    raise ValueError("no open-access PDF URL (paper likely paywalled)")


def load_index() -> dict:
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text())
        except Exception:
            pass
    return {"version": 1, "papers": []}


def save_index(idx: dict) -> None:
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = INDEX_PATH.with_suffix(".json.tmp")
    idx["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    tmp.write_text(json.dumps(idx, indent=2))
    tmp.replace(INDEX_PATH)  # atomic on POSIX


def update_index(key: str, meta: dict, size: int) -> None:
    idx = load_index()
    idx["papers"] = [p for p in idx["papers"] if p.get("key") != key]
    ext = meta.get("externalIds", {}) or {}
    idx["papers"].append(
        {
            "key": key,
            "arxiv_id": _strip_arxiv_version(ext["ArXiv"])
            if ext.get("ArXiv")
            else None,
            "doi": ext.get("DOI"),
            "s2_id": meta.get("paperId"),
            "title": meta.get("title"),
            "authors": [a.get("name") for a in (meta.get("authors") or [])],
            "year": meta.get("year"),
            "citations": meta.get("citationCount"),
            "venue": meta.get("venue"),
            "tldr": (meta.get("tldr") or {}).get("text"),
            "abstract": meta.get("abstract"),
            "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "size_bytes": size,
            "has_pdf": True,
        }
    )
    save_index(idx)


def download_one(
    paper_id: str, force: bool = False, max_mb: int = DEFAULT_MAX_MB
) -> dict:
    """Download a single paper. Returns status dict."""
    try:
        meta = resolve_metadata(paper_id)
    except Exception as e:
        return {"status": "metadata_failed", "id": paper_id, "error": str(e)}

    if not meta:
        return {"status": "not_found", "id": paper_id}

    try:
        pdf_url, key = choose_pdf_url(meta)
    except ValueError as e:
        return {
            "status": "no_oa_pdf",
            "id": paper_id,
            "title": meta.get("title"),
            "reason": str(e),
        }

    out_dir = PAPERS_DIR / key
    pdf_path = out_dir / "paper.pdf"
    meta_path = out_dir / "metadata.json"

    if pdf_path.exists() and not force:
        return {
            "status": "cached",
            "key": key,
            "path": str(pdf_path),
            "size_bytes": pdf_path.stat().st_size,
            "title": meta.get("title"),
        }

    # Download
    try:
        with httpx.Client(follow_redirects=True, timeout=60) as c:
            r = c.get(
                pdf_url, headers={"User-Agent": "EvoScientist/1.0 (paper-navigator)"}
            )
            r.raise_for_status()
            content = r.content
    except Exception as e:
        return {
            "status": "download_failed",
            "id": paper_id,
            "url": pdf_url,
            "error": str(e),
        }

    # Validate
    size_kb = len(content) / 1024
    if size_kb < MIN_PDF_KB:
        return {
            "status": "too_small",
            "id": paper_id,
            "size_bytes": len(content),
            "reason": f"< {MIN_PDF_KB}KB (likely error page)",
        }
    if size_kb / 1024 > max_mb:
        return {
            "status": "too_large",
            "id": paper_id,
            "size_mb": size_kb / 1024,
            "reason": f"> {max_mb}MB",
        }

    # Save
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(content)
    meta_path.write_text(json.dumps(meta, indent=2))
    update_index(key, meta, len(content))

    return {
        "status": "downloaded",
        "key": key,
        "path": str(pdf_path),
        "size_bytes": len(content),
        "title": meta.get("title"),
        "url": pdf_url,
    }


def main():
    p = argparse.ArgumentParser(
        description="Download paper PDFs to $PAPERS_DIR with index."
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--paper-id", "-p", help="Single paper ID (S2, ArXiv:, DOI:, or URL)"
    )
    g.add_argument("--arxiv-id", "-a", help="Single arXiv ID (e.g. 1706.03762)")
    g.add_argument("--bulk", "-b", help="Comma-separated paper IDs")
    g.add_argument("--bulk-file", help="File with one paper ID per line")
    p.add_argument(
        "--force", "-f", action="store_true", help="Re-download even if cached"
    )
    p.add_argument(
        "--max-mb",
        type=int,
        default=DEFAULT_MAX_MB,
        help=f"Skip PDFs over N MB (default {DEFAULT_MAX_MB})",
    )
    p.add_argument("--json", action="store_true", help="Emit results as JSON")
    args = p.parse_args()

    # Build ID list
    ids: list[str] = []
    if args.paper_id:
        ids.append(args.paper_id)
    elif args.arxiv_id:
        ids.append(f"ArXiv:{args.arxiv_id}")
    elif args.bulk:
        ids.extend([s.strip() for s in args.bulk.split(",") if s.strip()])
    elif args.bulk_file:
        text = Path(args.bulk_file).read_text()
        ids.extend(
            [
                line.strip()
                for line in text.splitlines()
                if line.strip() and not line.startswith("#")
            ]
        )

    if not ids:
        print("Error: no IDs provided", file=sys.stderr)
        sys.exit(1)

    print(f"Downloading {len(ids)} paper(s) to {PAPERS_DIR}", file=sys.stderr)

    results = []
    for i, pid in enumerate(ids):
        print(f"[{i + 1}/{len(ids)}] {pid}...", file=sys.stderr)
        r = download_one(pid, force=args.force, max_mb=args.max_mb)
        results.append(r)
        s = r["status"]
        if s == "downloaded":
            print(
                f"  ✓ downloaded ({r['size_bytes'] // 1024}KB) → {r['path']}",
                file=sys.stderr,
            )
        elif s == "cached":
            print(
                f"  = already cached ({r['size_bytes'] // 1024}KB) → {r['path']}",
                file=sys.stderr,
            )
        else:
            print(
                f"  ✗ {s}: {r.get('error') or r.get('reason') or ''}", file=sys.stderr
            )
        # Rate limit (arxiv skill convention)
        if i < len(ids) - 1 and s == "downloaded":
            time.sleep(RATE_LIMIT_S)

    # Output
    if args.json:
        print(json.dumps({"papers_dir": str(PAPERS_DIR), "results": results}, indent=2))
        return

    # Markdown summary
    ok = sum(1 for r in results if r["status"] in ("downloaded", "cached"))
    print("\n## Download Summary\n")
    print(f"**{ok}/{len(ids)} succeeded** — saved to `{PAPERS_DIR}`\n")
    print("| # | Status | Size | Title |")
    print("|---|--------|------|-------|")
    for i, r in enumerate(results, 1):
        size = f"{r.get('size_bytes', 0) // 1024} KB" if r.get("size_bytes") else "—"
        title = (r.get("title") or r.get("id") or "")[:70]
        print(f"| {i} | {r['status']} | {size} | {title} |")


if __name__ == "__main__":
    main()
