#!/usr/bin/env python3
"""Shared utilities for paper-navigator scripts.

Provides common constants, HTTP retry logic, header builders,
and paper-ID normalization used across all scripts.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

# ── Constants ─────────────────────────────────────────────────────
S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_RECOMMEND_BASE = "https://api.semanticscholar.org/recommendations/v1"
HF_API = "https://huggingface.co/api"
GITHUB_API = "https://api.github.com/search/repositories"
JINA_PREFIX = "https://r.jina.ai/"

MAX_RETRIES = 5
RETRY_DELAYS = [3, 6, 12, 24, 48]

# ── S2 Global Rate Pacer ────────────────────────────────────────
# Free tier: ~100 req/5min (~1 req/3s). With API key: ~100 req/min.
S2_MIN_INTERVAL = 3.0  # seconds between S2 requests (no key)
S2_MIN_INTERVAL_WITH_KEY = 0.5  # seconds between S2 requests (with key)
_last_s2_request_time: float = 0.0

# ── arXiv Global Rate Pacer ─────────────────────────────────────
# arXiv asks API clients to avoid bursts and keep request starts at least
# 3 seconds apart. Unlike the in-process S2 pacer, this one must coordinate
# independent agent processes, so it stores the last request timestamp in /tmp.
ARXIV_API_HOST = "export.arxiv.org"
ARXIV_API_PATH = "/api/query"
ARXIV_MIN_INTERVAL = 3.0
_last_arxiv_request_time: float = 0.0


class RateLimitExhausted(Exception):
    """All retries exhausted due to rate limiting (429)."""

    pass


def _is_s2_url(url: str) -> bool:
    """Check if URL targets Semantic Scholar API."""
    return url.startswith(S2_BASE) or url.startswith(S2_RECOMMEND_BASE)


def _is_arxiv_url(url: str) -> bool:
    """Check if URL targets the arXiv API endpoint."""
    parsed = urlparse(url)
    return parsed.netloc == ARXIV_API_HOST and parsed.path == ARXIV_API_PATH


def pace_s2_request() -> None:
    """Enforce minimum interval between Semantic Scholar API calls."""
    global _last_s2_request_time
    has_key = bool(os.environ.get("S2_API_KEY"))
    interval = S2_MIN_INTERVAL_WITH_KEY if has_key else S2_MIN_INTERVAL
    elapsed = time.time() - _last_s2_request_time
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_s2_request_time = time.time()


def _arxiv_min_interval() -> float:
    raw = os.environ.get("PAPER_NAVIGATOR_ARXIV_MIN_INTERVAL")
    if not raw:
        return ARXIV_MIN_INTERVAL
    try:
        return max(0.0, float(raw))
    except ValueError:
        return ARXIV_MIN_INTERVAL


def _arxiv_pacer_paths() -> tuple[Path, Path]:
    base = Path(
        os.environ.get(
            "PAPER_NAVIGATOR_ARXIV_PACER_DIR",
            str(Path(tempfile.gettempdir()) / "paper-navigator"),
        )
    )
    return base / "arxiv-api.lock", base / "arxiv-api.last"


def _read_arxiv_next_allowed(state_path: Path) -> float:
    try:
        return float(state_path.read_text().strip() or "0")
    except (OSError, ValueError):
        return 0.0


def _reserve_arxiv_slot(state_path: Path, interval: float) -> None:
    """Reserve the next arXiv request slot under an already-held lock."""
    next_allowed = _read_arxiv_next_allowed(state_path)
    now = time.time()
    if now < next_allowed:
        time.sleep(next_allowed - now)
        now = time.time()

    state_path.write_text(f"{now + interval:.6f}\n")


def _with_arxiv_lock(callback) -> None:
    lock_path, state_path = _arxiv_pacer_paths()
    try:
        import fcntl

        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            callback(state_path)
            fcntl.flock(lock_file, fcntl.LOCK_UN)
    except (ImportError, OSError):
        callback(None)


def pace_arxiv_request() -> None:
    """Enforce a cross-process interval between arXiv API request starts."""
    global _last_arxiv_request_time

    interval = _arxiv_min_interval()
    if interval <= 0:
        return

    def reserve(state_path: Path | None) -> None:
        global _last_arxiv_request_time
        if state_path is None:
            # Best-effort fallback for platforms without fcntl or writable temp dirs.
            now = time.time()
            if now < _last_arxiv_request_time:
                time.sleep(_last_arxiv_request_time - now)
                now = time.time()
            _last_arxiv_request_time = now + interval
            return
        _reserve_arxiv_slot(state_path, interval)

    _with_arxiv_lock(reserve)


def defer_arxiv_requests(wait_seconds: int | float) -> None:
    """Push the shared arXiv next-allowed time forward after a 429."""
    wait = max(0.0, float(wait_seconds))
    if wait <= 0:
        return

    def defer(state_path: Path | None) -> None:
        global _last_arxiv_request_time
        next_allowed = time.time() + wait
        if state_path is None:
            _last_arxiv_request_time = max(_last_arxiv_request_time, next_allowed)
            return
        current = _read_arxiv_next_allowed(state_path)
        state_path.write_text(f"{max(current, next_allowed):.6f}\n")

    _with_arxiv_lock(defer)


_S2_TIP_SHOWN = False


def print_s2_key_tip() -> None:
    """Print a one-time tip nudging the user toward registering an S2 API key.

    Called from scripts that detected missing `S2_API_KEY` and routed to arXiv.
    Tip is printed at most once per process to stderr.
    """
    global _S2_TIP_SHOWN
    if _S2_TIP_SHOWN:
        return
    if os.environ.get("S2_API_KEY"):
        return  # already has key
    _S2_TIP_SHOWN = True
    print(
        "\n💡 Tip: this search ran in arXiv-only mode (no S2_API_KEY).\n"
        "   Register a FREE Semantic Scholar API key at https://www.semanticscholar.org/product/api\n"
        "   to unlock: citation counts in results, TLDR summaries, and the citation_traverse /\n"
        "   recommend / trending / author_search tools (all S2-bound, disabled without a key).\n"
        "   Then set: export S2_API_KEY='your-key-here'",
        file=sys.stderr,
    )


DEFAULT_USER_AGENT = "EvoScientist/1.0 (paper-navigator)"


# ── Header builders ───────────────────────────────────────────────


def s2_headers() -> dict:
    """Semantic Scholar API headers with optional API key."""
    h = {"User-Agent": DEFAULT_USER_AGENT}
    key = os.environ.get("S2_API_KEY")
    if key:
        h["x-api-key"] = key
    return h


def hf_headers() -> dict:
    """HuggingFace API headers with optional token."""
    h = {"User-Agent": DEFAULT_USER_AGENT}
    token = os.environ.get("HF_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def github_headers() -> dict:
    """GitHub API headers with optional token for higher rate limits."""
    h = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/vnd.github.v3+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"token {token}"
    return h


def jina_headers() -> dict:
    """Jina Reader headers with optional API key."""
    h = {"Accept": "text/markdown"}
    key = os.environ.get("JINA_API_KEY")
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def arxiv_headers() -> dict:
    """arXiv API headers."""
    return {"User-Agent": DEFAULT_USER_AGENT}


# ── HTTP with retry ───────────────────────────────────────────────


def request_with_retry(
    client: httpx.Client,
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 30,
    parse_json: bool = True,
    follow_redirects: bool = False,
    method: str = "GET",
    json_body: dict | None = None,
) -> Any:
    """HTTP request with retry on 429/5xx.

    Returns parsed JSON (dict/list) by default.
    If parse_json=False, returns response text.
    Raises RateLimitExhausted if all retries fail on 429.
    """
    # Apply global rate pacer for Semantic Scholar API
    if _is_s2_url(url):
        pace_s2_request()
    is_arxiv_url = _is_arxiv_url(url)

    last_was_rate_limited = False
    for attempt in range(MAX_RETRIES):
        try:
            if is_arxiv_url:
                pace_arxiv_request()
            resp = client.request(
                method,
                url,
                params=params,
                headers=headers,
                json=json_body,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                last_was_rate_limited = resp.status_code == 429
                if attempt < MAX_RETRIES - 1:
                    retry_after = resp.headers.get("Retry-After")
                    wait = int(retry_after) if retry_after else RETRY_DELAYS[attempt]
                    if is_arxiv_url and resp.status_code == 429:
                        defer_arxiv_requests(wait)
                    print(
                        f"Rate limited. Waiting {wait}s before retry...",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    continue
                if is_arxiv_url and resp.status_code == 429:
                    defer_arxiv_requests(RETRY_DELAYS[-1])
            resp.raise_for_status()
            return resp.json() if parse_json else resp.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {} if parse_json else ""
            if e.response.status_code == 429 and attempt == MAX_RETRIES - 1:
                raise RateLimitExhausted(
                    f"Rate limit exhausted after {MAX_RETRIES} retries: {url}"
                ) from e
            raise
        except httpx.HTTPError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise SystemExit(f"Error: {e}") from e

    if last_was_rate_limited:
        raise RateLimitExhausted(
            f"Rate limit exhausted after {MAX_RETRIES} retries: {url}"
        )
    return {} if parse_json else ""


# ── Paper ID normalization ────────────────────────────────────────


def _strip_arxiv_version(arxiv_id: str) -> str:
    """Strip version suffix (e.g. v5) from arXiv ID."""
    return re.sub(r"v\d+$", "", arxiv_id)


_ARXIV_BARE_PATTERN = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")


def normalize_paper_id(raw: str) -> str:
    """Normalize paper ID: strip URL prefixes, add ArXiv:/DOI: prefix.

    Handles: arXiv URLs, ArXiv:/arxiv: prefixed IDs, DOIs (10.x),
    and bare arXiv IDs (e.g. '1706.03762' or '1706.03762v3').
    """
    raw = raw.strip()
    for prefix in [
        "https://arxiv.org/abs/",
        "http://arxiv.org/abs/",
        "https://arxiv.org/pdf/",
        "http://arxiv.org/pdf/",
    ]:
        if raw.startswith(prefix):
            raw = _strip_arxiv_version(raw[len(prefix) :].removesuffix(".pdf"))
            return f"ArXiv:{raw}"
    if raw.startswith("ArXiv:") or raw.startswith("arxiv:"):
        id_part = _strip_arxiv_version(raw[6:])
        return f"ArXiv:{id_part}"
    if raw.startswith("10."):
        return f"DOI:{raw}"
    # Bare arXiv ID (e.g. "1706.03762" or "1706.03762v3")
    if _ARXIV_BARE_PATTERN.match(raw):
        return f"ArXiv:{_strip_arxiv_version(raw)}"
    return raw
