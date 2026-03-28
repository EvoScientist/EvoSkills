#!/usr/bin/env python3
"""Shared utilities for paper-navigator scripts.

Provides common constants, HTTP retry logic, header builders,
and paper-ID normalization used across all scripts.
"""

import os
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

MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]

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
) -> Any:
    """GET with retry on 429/5xx.

    Returns parsed JSON (dict/list) by default.
    If parse_json=False, returns response text.
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )
            if resp.status_code == 429 or resp.status_code >= 500:
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
            raise
        except httpx.HTTPError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise SystemExit(f"Error: {e}") from e
    return {} if parse_json else ""


# ── Paper ID normalization ────────────────────────────────────────


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
            raw = raw[len(prefix) :].rstrip(".pdf")
            return f"ArXiv:{raw}"
    if raw.startswith("10."):
        return f"DOI:{raw}"
    return raw
