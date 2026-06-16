"""Fetch a paper's full-text markdown by arXiv ID.

Strategy
--------
Primary:  arxiv2md.org   (JSON endpoint — gives us {arxiv_id, title, content})
Fallback: markxiv.org    (when arxiv2md returns < 2000 bytes — empirically
                          its sign that arxiv2md choked on a low-quality PDF)

A persistent disk cache makes re-runs free. Header conventions differ
between the two services (arxiv2md uses `## N Section`, markxiv uses
`# Section`) — the section extractor handles both.

Standalone usage:
    uv run python EvoScientist/skills/paper-graph/scripts/paper_md.py <arxiv_id>
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx


PRIMARY_URL = "https://arxiv2md.org/api/json?url={arxiv_id}"
FALLBACK_URL = "https://markxiv.org/abs/{arxiv_id}"

# Empirical floor: arxiv2md responses under this are usually just an
# appendix table (the PDF was too low-quality to render the body).
PRIMARY_MIN_BYTES = 2000

REQUEST_TIMEOUT = 15.0
MAX_CONCURRENCY = 2

# Section preference (most informative first). Matched against the
# header text after stripping any leading "N " / "5.1 " / "VI " prefix.
SECTION_PRIORITY = ("limitation", "future", "remarks", "discussion", "conclusion")

_HEADER_RE = re.compile(r"^(#{1,2})\s+(.+?)\s*$", re.MULTILINE)
_HEADER_NUM_PREFIX = re.compile(r"^(?:[\dIVXivx]+(?:\.\d+)*\s+)?(.*)$")

_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    return _semaphore


def default_cache_dir() -> Path:
    raw = os.environ.get("PAPER_MD_CACHE")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".cache" / "evoscientist" / "paper_md"


def _cache_path(cache_dir: Path, arxiv_id: str) -> Path:
    # arxiv IDs are already filesystem-safe (digits + dot).
    return cache_dir / f"{arxiv_id}.md"


def _normalize_header(raw: str) -> str:
    """Strip a leading section number ("5", "5.1", "VI") so the priority
    match works for `## 5 Conclusion` and `# Conclusion` alike."""
    m = _HEADER_NUM_PREFIX.match(raw.strip())
    return (m.group(1) if m else raw).strip().lower()


def extract_section(md: str) -> str | None:
    """Return the best conclusion-like H1/H2 section, or None.

    Preference: Limitations > Future Work > Final Remarks > Discussion >
    Conclusion. Section text spans from its header to the next header of
    equal-or-shallower depth.
    """
    headers: list[tuple[int, int, str, str]] = []  # (start_pos, level, raw, normalized)
    for m in _HEADER_RE.finditer(md):
        level = len(m.group(1))
        raw = m.group(2)
        headers.append((m.start(), level, raw, _normalize_header(raw)))
    if not headers:
        return None

    # Pick best candidate by priority order.
    best_idx: int | None = None
    best_rank = len(SECTION_PRIORITY)
    for i, (_, _, _, norm) in enumerate(headers):
        for rank, keyword in enumerate(SECTION_PRIORITY):
            if keyword in norm and rank < best_rank:
                best_rank = rank
                best_idx = i
                break
    if best_idx is None:
        return None

    start_pos, level, _, _ = headers[best_idx]
    # End: next header with depth <= level.
    end_pos = len(md)
    for j in range(best_idx + 1, len(headers)):
        if headers[j][1] <= level:
            end_pos = headers[j][0]
            break
    return md[start_pos:end_pos].strip()


async def _get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    sem = _get_semaphore()
    async with sem:
        return await client.get(url, timeout=REQUEST_TIMEOUT)


async def _fetch_primary(client: httpx.AsyncClient, arxiv_id: str) -> str | None:
    # Best-effort path: anything that fails (HTTP error, malformed JSON,
    # encoding glitch, etc.) returns None so the caller can fall back or
    # abstain. We never want this to break the pipeline.
    try:
        r = await _get(client, PRIMARY_URL.format(arxiv_id=arxiv_id))
        if r.status_code != 200:
            return None
        payload: dict[str, Any] = r.json()
    except Exception:
        return None
    content = payload.get("content") if isinstance(payload, dict) else None
    if not isinstance(content, str) or len(content) < PRIMARY_MIN_BYTES:
        return None
    return content


async def _fetch_fallback(client: httpx.AsyncClient, arxiv_id: str) -> str | None:
    try:
        r = await _get(client, FALLBACK_URL.format(arxiv_id=arxiv_id))
        if r.status_code != 200:
            return None
        body = r.text or ""
    except Exception:
        return None
    return body if len(body) >= PRIMARY_MIN_BYTES else None


async def fetch_paper_md(
    client: httpx.AsyncClient,
    arxiv_id: str,
    *,
    cache_dir: Path | None = None,
    use_cache: bool = True,
) -> str | None:
    """Return the paper's markdown body, or None on any failure / too-short.

    Tries arxiv2md.org first; falls back to markxiv.org if the primary
    response is shorter than ``PRIMARY_MIN_BYTES``. Result is cached to
    disk on success.
    """
    if not arxiv_id:
        return None
    cache_dir = cache_dir if cache_dir is not None else default_cache_dir()
    cache_path = _cache_path(cache_dir, arxiv_id)
    if use_cache and cache_path.is_file():
        return cache_path.read_text()
    body = await _fetch_primary(client, arxiv_id)
    if body is None:
        body = await _fetch_fallback(client, arxiv_id)
    if body is None:
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(body)
    return body


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


async def _amain(arxiv_id: str, *, no_cache: bool, full: bool) -> int:
    async with httpx.AsyncClient() as client:
        body = await fetch_paper_md(client, arxiv_id, use_cache=not no_cache)
    if body is None:
        print(f"ERROR: no markdown for {arxiv_id}", file=sys.stderr)
        return 1
    if full:
        sys.stdout.write(body)
        return 0
    section = extract_section(body)
    if section is None:
        print(f"ERROR: no conclusion-like section found in {arxiv_id}", file=sys.stderr)
        return 2
    sys.stdout.write(section + "\n")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("arxiv_id", help="e.g. 2006.11477")
    ap.add_argument("--no-cache", action="store_true", help="bypass the disk cache")
    ap.add_argument(
        "--full",
        action="store_true",
        help="print the whole document instead of the section",
    )
    args = ap.parse_args()
    sys.exit(asyncio.run(_amain(args.arxiv_id, no_cache=args.no_cache, full=args.full)))


if __name__ == "__main__":
    main()
