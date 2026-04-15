#!/usr/bin/env python3
"""Shared utilities for paper-navigator scripts.

Provides common constants, HTTP retry logic, header builders,
and paper-ID normalization used across all scripts.
"""

from __future__ import annotations

import os
import re
import sys
import time
from typing import Any

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


class RateLimitExhausted(Exception):
    """All retries exhausted due to rate limiting (429)."""

    pass


class MissingSemanticScholarKey(Exception):
    """Semantic Scholar access requested without S2_API_KEY configured."""

    pass


def _is_s2_url(url: str) -> bool:
    """Check if URL targets Semantic Scholar API."""
    return url.startswith(S2_BASE) or url.startswith(S2_RECOMMEND_BASE)


def has_s2_api_key() -> bool:
    """Return whether Semantic Scholar API access is configured."""
    return bool(os.environ.get("S2_API_KEY"))


def pace_s2_request() -> None:
    """Enforce minimum interval between Semantic Scholar API calls."""
    global _last_s2_request_time
    interval = S2_MIN_INTERVAL_WITH_KEY if has_s2_api_key() else S2_MIN_INTERVAL
    elapsed = time.time() - _last_s2_request_time
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_s2_request_time = time.time()


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
        if not has_s2_api_key():
            raise MissingSemanticScholarKey(
                "S2_API_KEY is not set. Ask the user to provide a Semantic Scholar "
                "API key, or continue with non-S2 sources."
            )
        pace_s2_request()

    last_was_rate_limited = False
    for attempt in range(MAX_RETRIES):
        try:
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
                    print(
                        f"Rate limited. Waiting {wait}s before retry...",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    continue
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


def normalize_paper_id(raw: str) -> str:
    """Normalize paper ID: strip URL prefixes, add ArXiv:/DOI: prefix."""
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
    return raw
