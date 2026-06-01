#!/usr/bin/env python3
"""Shared utilities for paper-navigator scripts.

Provides common constants, HTTP retry logic, header builders,
and paper-ID normalization used across all scripts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import threading
import time
from typing import Any

import httpx


# ── argparse: print full --help on error ─────────────────────────
# Default argparse prints only 1-line "usage:" + error on bad flags. Agent
# callers (e.g. minimax-m2.7) then guess another flag, trigger another
# usage-only error, re-send the growing context, and loop. Full --help in
# the same turn lets the agent correct on the next step. Process-wide
# monkey-patch: every script that imports utils (all of them) benefits
# without per-script churn.
def _helpful_argparse_error(self, message):  # type: ignore[no-redef]
    self.print_help(sys.stderr)
    self.exit(2, f"\nerror: {message}\n")


argparse.ArgumentParser.error = _helpful_argparse_error  # type: ignore[method-assign]

# ── Constants ─────────────────────────────────────────────────────
S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_RECOMMEND_BASE = "https://api.semanticscholar.org/recommendations/v1"
HF_API = "https://huggingface.co/api"
GITHUB_API = "https://api.github.com/search/repositories"
JINA_PREFIX = "https://r.jina.ai/"
MARKXIV_PREFIX = "https://markxiv.com/"
COHERE_API = "https://api.cohere.com/v2"
OPENROUTER_API = "https://openrouter.ai/api/v1"

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


def _is_s2_url(url: str) -> bool:
    """Check if URL targets Semantic Scholar API."""
    return url.startswith(S2_BASE) or url.startswith(S2_RECOMMEND_BASE)


# ── External-API classifier (for call logging) ───────────────────
ARXIV_API = "https://export.arxiv.org/api/query"
OPENALEX_BASE = "https://api.openalex.org"


def _classify_api(url: str) -> str | None:
    """Return the API name (`S2`/`ARXIV`/`OPENALEX`) for logging, or None.

    Used by `request_with_retry` to decide whether the call should be
    recorded under `{API}_CALL_LOG_DIR` / `{API}_CALL_LOG`.
    """
    if _is_s2_url(url):
        return "S2"
    if url.startswith(ARXIV_API) or url.startswith("http://export.arxiv.org/api/query"):
        return "ARXIV"
    if url.startswith(OPENALEX_BASE):
        return "OPENALEX"
    return None


# ── S2 publication-date cutoff (eval/freshness fence) ─────────────
# When S2_DATE_CUTOFF is set in the environment, every S2 endpoint that
# accepts `publicationDateOrYear` will be filtered to ≤ that date.
#
# Format: YYYY or YYYY-MM-DD (validated once on first read).
#
# This is read by request_with_retry; callers do NOT need to plumb it
# through. If a caller already specifies `year` or `publicationDateOrYear`
# in params, the explicit value wins and the env var is ignored for that
# call.
_S2_DATE_CUTOFF_RE = re.compile(r"\A(\d{4})(-\d{2}-\d{2})?\Z")


def _read_s2_date_cutoff() -> str | None:
    """Return the S2_DATE_CUTOFF value formatted as `:YYYY[-MM-DD]`, or None.

    Raises ValueError on a malformed env var so misconfigurations surface
    immediately rather than silently disabling the cutoff.
    """
    raw = os.environ.get("S2_DATE_CUTOFF")
    if not raw:
        return None
    raw = raw.strip()
    if not _S2_DATE_CUTOFF_RE.match(raw):
        raise ValueError(f"S2_DATE_CUTOFF={raw!r} is not YYYY or YYYY-MM-DD")
    return f":{raw}"


# Endpoints that accept publicationDateOrYear. Single-paper / batch lookup
# endpoints don't accept the filter — injecting it would 400 the call.
_S2_DATE_FILTERABLE_PATTERNS = (
    "/paper/search",  # also matches /paper/search/match, /paper/search/bulk
    "/snippet/search",
    "/citations",  # /paper/{id}/citations
    "/references",  # /paper/{id}/references
    "/papers",  # /author/{id}/papers
)


def _s2_endpoint_accepts_date_filter(url: str) -> bool:
    """True if the S2 endpoint accepts `publicationDateOrYear`."""
    if not _is_s2_url(url):
        return False
    if "/paper/batch" in url:
        return False
    if url.rstrip("/").endswith("/papers/"):
        # POST /recommendations/v1/papers/ — body-based recommendations
        return False
    return any(pat in url for pat in _S2_DATE_FILTERABLE_PATTERNS)


def pace_s2_request() -> None:
    """Enforce minimum interval between Semantic Scholar API calls."""
    global _last_s2_request_time
    has_key = bool(os.environ.get("S2_API_KEY"))
    interval = S2_MIN_INTERVAL_WITH_KEY if has_key else S2_MIN_INTERVAL
    elapsed = time.time() - _last_s2_request_time
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_s2_request_time = time.time()


def _log_api_call(
    api: str,
    url: str,
    params: dict | None,
    method: str,
    *,
    output: Any = None,
    parse_json: bool = True,
    status_code: int | None = None,
    error: str | None = None,
) -> None:
    """Append a record to main.jsonl; optionally save body to output_path.

    `api` is the external-API tag (e.g. "S2", "ARXIV", "OPENALEX"). The
    helper reads `{API}_CALL_LOG_DIR` (full logging — body files saved
    next to main.jsonl) and `{API}_CALL_LOG` (main-jsonl only, no bodies).
    Both unset = no logging, no overhead.
    """
    log_dir = os.environ.get(f"{api}_CALL_LOG_DIR")
    log_file = os.environ.get(f"{api}_CALL_LOG")
    if not (log_dir or log_file):
        return
    import uuid
    from datetime import datetime

    rec = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "pid": os.getpid(),
        "script": os.path.basename(sys.argv[0]) if sys.argv else "",
        "api": api,
        "method": method,
        "url": url,
        "params": params or {},
    }
    if status_code is not None:
        rec["status_code"] = status_code
    if error:
        rec["error"] = error
    if log_dir and output is not None and not error:
        try:
            os.makedirs(log_dir, exist_ok=True)
            ext = "json" if parse_json else "txt"
            fname = (
                f"{int(time.time() * 1e6)}_{os.getpid()}_{uuid.uuid4().hex[:8]}.{ext}"
            )
            out_path = os.path.join(log_dir, fname)
            with open(out_path, "w") as f:
                if parse_json:
                    json.dump(output, f, default=str)
                else:
                    f.write(output if isinstance(output, str) else str(output))
            rec["output_path"] = out_path
        except Exception as e:
            rec["log_write_error"] = repr(e)
    main_path = log_file or os.path.join(log_dir, "main.jsonl")
    try:
        parent = os.path.dirname(main_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(main_path, "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        pass


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
    key = os.environ.get("JINA_API_KEY") or os.environ.get("JINA_TOKEN")
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


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
    api = _classify_api(url)
    if api == "S2":
        pace_s2_request()

    # Inject S2_DATE_CUTOFF as `publicationDateOrYear` for filterable
    # endpoints. Caller-supplied `year` or `publicationDateOrYear` always
    # wins; this is a default, not an override.
    if method == "GET" and _s2_endpoint_accepts_date_filter(url):
        cutoff = _read_s2_date_cutoff()
        if cutoff:
            params = dict(params or {})
            if "publicationDateOrYear" not in params and "year" not in params:
                params["publicationDateOrYear"] = cutoff

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
            result = resp.json() if parse_json else resp.text
            if api:
                _log_api_call(
                    api,
                    url,
                    params,
                    method,
                    output=result,
                    parse_json=parse_json,
                    status_code=resp.status_code,
                )
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                if api:
                    _log_api_call(
                        api, url, params, method, status_code=404, error="404"
                    )
                return {} if parse_json else ""
            if e.response.status_code == 429 and attempt == MAX_RETRIES - 1:
                if api:
                    _log_api_call(
                        api,
                        url,
                        params,
                        method,
                        status_code=429,
                        error="rate-limit-exhausted",
                    )
                raise RateLimitExhausted(
                    f"Rate limit exhausted after {MAX_RETRIES} retries: {url}"
                ) from e
            if api:
                _log_api_call(
                    api,
                    url,
                    params,
                    method,
                    status_code=e.response.status_code,
                    error=repr(e),
                )
            raise
        except httpx.HTTPError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            if api:
                _log_api_call(api, url, params, method, error=repr(e))
            raise SystemExit(f"Error: {e}") from e

    if last_was_rate_limited:
        if api:
            _log_api_call(
                api,
                url,
                params,
                method,
                error="rate-limit-exhausted-fallthrough",
            )
        raise RateLimitExhausted(
            f"Rate limit exhausted after {MAX_RETRIES} retries: {url}"
        )
    return {} if parse_json else ""


# ── Paper ID normalization ────────────────────────────────────────


def _strip_arxiv_version(arxiv_id: str) -> str:
    """Strip version suffix (e.g. v5) from arXiv ID."""
    return re.sub(r"v\d+$", "", arxiv_id)


def normalize_paper_id(raw: str) -> str:
    """Normalize paper ID: strip URL prefixes, add ArXiv:/DOI: prefix.

    Raises ValueError on a hex-only string shorter than the 40-char S2 SHA —
    truncated SHAs would otherwise silently 404 against the S2 API.
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
    if (
        raw
        and ":" not in raw
        and not raw.isdigit()
        and all(c in "0123456789abcdefABCDEF" for c in raw)
        and len(raw) != 40
    ):
        raise ValueError(
            f"Paper ID {raw!r} looks like a truncated S2 SHA "
            f"({len(raw)} hex chars; expected 40). Use the full SHA, or "
            f"prefix with ArXiv:/DOI:/CorpusId:."
        )
    return raw


# ── Circuit breaker ──────────────────────────────────────────────


class S2CircuitBreaker:
    """Circuit breaker for the Semantic Scholar API.

    CLOSED  — normal, requests pass through
    OPEN    — too many failures, requests rejected
    HALF_OPEN — cooldown expired, one probe allowed
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3,
    ):
        self._state = self.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._success_threshold = success_threshold
        self._last_failure_time: float = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == self.OPEN:
                if time.monotonic() - self._last_failure_time >= self._recovery_timeout:
                    self._state = self.HALF_OPEN
                    self._success_count = 0
            return self._state

    def allow_request(self) -> bool:
        s = self.state
        return s != self.OPEN

    def record_success(self) -> None:
        with self._lock:
            if self._state == self.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._success_threshold:
                    self._state = self.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    print("S2 circuit breaker CLOSED — API recovered.", file=sys.stderr)
            else:
                self._failure_count = 0

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == self.HALF_OPEN:
                self._state = self.OPEN
                print("S2 circuit breaker re-OPENED — probe failed.", file=sys.stderr)
            elif self._failure_count >= self._failure_threshold:
                self._state = self.OPEN
                print(
                    f"S2 circuit breaker OPENED after {self._failure_count} failures. "
                    f"Rejecting requests for {self._recovery_timeout}s.",
                    file=sys.stderr,
                )


s2_circuit_breaker = S2CircuitBreaker()


def check_s2_circuit() -> None:
    """Raise RuntimeError if circuit breaker is open."""
    if not s2_circuit_breaker.allow_request():
        raise RuntimeError(
            "Semantic Scholar API circuit breaker is OPEN — "
            "too many consecutive failures. Try again later."
        )


# ── Citation pagination helpers ──────────────────────────────────

# Fields not supported on the S2 citations/references endpoint
_CITATIONS_UNSUPPORTED_FIELDS = {"tldr", "publicationVenue"}


def _citation_safe_fields(fields: str) -> str:
    """Strip fields unsupported by the S2 citations/references endpoint."""
    parts = [f.strip() for f in fields.split(",")]
    safe = [f for f in parts if f not in _CITATIONS_UNSUPPORTED_FIELDS]
    return ",".join(safe)


def fetch_citations_paginated(
    paper_id: str,
    direction: str,
    limit: int,
    fields: str,
    year_from: int | None = None,
    year_to: int | None = None,
    min_citations: int = 0,
) -> list[dict]:
    """Fetch citations with offset-based pagination up to limit.

    For large citation sets (>1000), uses year-sliced parallel scanning
    to bypass the S2 API offset cap.

    Args:
        fields: S2 field string for the nested paper objects (varies per caller).
    """
    endpoint = "citations" if direction == "forward" else "references"
    nested_key = "citingPaper" if direction == "forward" else "citedPaper"

    # First, get total count to decide strategy
    check_s2_circuit()

    with httpx.Client() as client:
        try:
            meta = request_with_retry(
                client,
                f"{S2_BASE}/paper/{paper_id}",
                {"fields": "citationCount,year"},
                s2_headers(),
            )
            s2_circuit_breaker.record_success()
        except Exception as e:
            s2_circuit_breaker.record_failure()
            print(f"Failed to get paper metadata: {e}", file=sys.stderr)
            return []

    total = meta.get("citationCount", 0) if direction == "forward" else limit
    paper_year = meta.get("year", 2020)

    if total > 10000:
        print(
            f"Warning: Paper has {total} citations, exceeding S2 API's 10K offset cap. "
            f"Using year-sliced scanning to maximize coverage, but some citations may be missed.",
            file=sys.stderr,
        )

    if total <= 1000 or limit <= 1000:
        all_papers = _fetch_citations_simple(
            paper_id, endpoint, nested_key, limit, fields
        )
    else:
        y_from = year_from or paper_year
        y_to = year_to or 2026
        all_papers = asyncio.run(
            _fetch_citations_by_year(
                paper_id, endpoint, nested_key, y_from, y_to, fields
            )
        )

    # Apply filters
    if min_citations > 0:
        all_papers = [
            p for p in all_papers if (p.get("citationCount") or 0) >= min_citations
        ]
    if year_from:
        all_papers = [p for p in all_papers if (p.get("year") or 0) >= year_from]
    if year_to:
        all_papers = [p for p in all_papers if (p.get("year") or 9999) <= year_to]

    all_papers.sort(key=lambda p: p.get("citationCount", 0), reverse=True)
    return all_papers[:limit]


def _fetch_citations_simple(
    paper_id: str,
    endpoint: str,
    nested_key: str,
    limit: int,
    fields: str,
) -> list[dict]:
    """Simple offset-based pagination, up to 9000 offset."""
    safe_fields = _citation_safe_fields(fields)
    all_papers = []
    offset = 0
    page_size = min(limit, 1000)

    with httpx.Client() as client:
        while len(all_papers) < limit and offset < 9000:
            check_s2_circuit()
            url = f"{S2_BASE}/paper/{paper_id}/{endpoint}"

            params = {
                "fields": safe_fields,
                "limit": page_size,
                "offset": offset,
            }
            try:
                data = request_with_retry(client, url, params, s2_headers())
                s2_circuit_breaker.record_success()
            except Exception as e:
                s2_circuit_breaker.record_failure()
                print(f"Citation fetch failed at offset {offset}: {e}", file=sys.stderr)
                break

            batch = [
                item[nested_key]
                for item in (data.get("data") or [])
                if item.get(nested_key)
            ]
            if not batch:
                break
            all_papers.extend(batch)
            offset += len(batch)

            if "next" not in data:
                break

    return all_papers


async def _fetch_year_slice(
    paper_id: str,
    endpoint: str,
    nested_key: str,
    year: int,
    sem: asyncio.Semaphore,
    fields: str,
) -> list[dict]:
    """Fetch all citations for a single year."""
    safe_fields = _citation_safe_fields(fields)
    papers = []
    offset = 0

    async with sem:
        async with httpx.AsyncClient() as client:
            while offset < 9000:
                check_s2_circuit()
                url = f"{S2_BASE}/paper/{paper_id}/{endpoint}"

                params = {
                    "fields": safe_fields,
                    "limit": 1000,
                    "offset": offset,
                    "year": str(year),
                }
                try:
                    resp = await client.get(
                        url,
                        params=params,
                        headers=s2_headers(),
                        timeout=30,
                    )
                    if resp.status_code == 429 or resp.status_code >= 500:
                        await asyncio.sleep(3)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    _log_api_call(
                        "S2",
                        url,
                        params,
                        "GET",
                        output=data,
                        parse_json=True,
                        status_code=resp.status_code,
                    )
                    s2_circuit_breaker.record_success()
                except Exception as e:
                    _log_api_call("S2", url, params, "GET", error=repr(e))
                    s2_circuit_breaker.record_failure()
                    print(f"Year {year} offset {offset} failed: {e}", file=sys.stderr)
                    break

                batch = [
                    item[nested_key]
                    for item in (data.get("data") or [])
                    if item.get(nested_key)
                ]
                if not batch:
                    break
                papers.extend(batch)
                offset += len(batch)

                if "next" not in data:
                    break

    return papers


async def _fetch_citations_by_year(
    paper_id: str,
    endpoint: str,
    nested_key: str,
    year_from: int,
    year_to: int,
    fields: str,
) -> list[dict]:
    """Fetch citations across year slices in parallel."""
    sem = asyncio.Semaphore(5)
    tasks = [
        _fetch_year_slice(paper_id, endpoint, nested_key, year, sem, fields)
        for year in range(year_from, year_to + 1)
    ]
    results = await asyncio.gather(*tasks)
    all_papers = [p for batch in results for p in batch]
    return dedup_papers(all_papers)


# ── JSONL file helpers ───────────────────────────────────────────


def write_jsonl(path: str, records: list[dict], append: bool = False) -> int:
    """Write records to a JSONL file. Returns count written."""
    mode = "a" if append else "w"
    with open(path, mode) as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    return len(records)


def read_jsonl(path: str) -> list[dict]:
    """Read all records from a JSONL file."""
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def dedup_papers(papers: list[dict], key: str = "paperId") -> list[dict]:
    """Deduplicate papers by a key field, preserving order.

    Special `key` values:
    - "corpusId": match on top-level `corpusId` if present, else fall back to
      `externalIds.CorpusId`. Rows without either are kept (they cannot
      collide anyway).
    - "paperId" or any other key: exact match on that top-level field.
      Rows with a missing/None/empty key value are dropped (legacy behavior).
    """
    seen: set[str] = set()
    result = []
    for p in papers:
        if key == "corpusId":
            k = p.get("corpusId")
            if not k:
                ext = p.get("externalIds") or {}
                k = ext.get("CorpusId")
            k = str(k) if k else None
            if k is None:
                result.append(p)  # keep — can't collide with anything
                continue
        else:
            k = p.get(key)
            if not k:
                continue  # legacy: drop rows without a valid key
        if k not in seen:
            seen.add(k)
            result.append(p)
    return result


# ── Reranker clients ─────────────────────────────────────────────


def cohere_headers() -> dict:
    """Cohere API headers."""
    key = os.environ.get("COHERE_API_KEY", "")
    if not key:
        raise RuntimeError("COHERE_API_KEY not set")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def openrouter_headers() -> dict:
    """OpenRouter API headers."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def rerank_cohere(
    query: str,
    documents: list[str],
    top_n: int = 50,
    model: str = "rerank-v3.5",
) -> list[dict]:
    """Rerank documents using Cohere Rerank API.

    Returns list of {"index": int, "relevance_score": float}
    sorted by score descending.
    """
    with httpx.Client() as client:
        resp = client.post(
            f"{COHERE_API}/rerank",
            headers=cohere_headers(),
            json={
                "model": model,
                "query": query,
                "documents": documents,
                "top_n": top_n,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])


def rerank_openrouter(
    query: str,
    documents: list[str],
    top_n: int = 50,
    model: str = "cohere/rerank-v3.5",
) -> list[dict]:
    """Rerank documents using a reranker model via OpenRouter.

    Returns list of {"index": int, "relevance_score": float}
    sorted by score descending.
    """
    with httpx.Client() as client:
        resp = client.post(
            f"{OPENROUTER_API}/rerank",
            headers=openrouter_headers(),
            json={
                "model": model,
                "query": query,
                "documents": documents,
                "top_n": top_n,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])


def rerank(
    query: str,
    documents: list[str],
    top_n: int = 50,
    provider: str | None = None,
    model: str | None = None,
) -> list[dict]:
    """Rerank documents using available provider (Cohere or OpenRouter).

    Auto-detects provider from available env vars if not specified.
    Returns list of {"index": int, "relevance_score": float}.
    """
    if provider is None:
        if os.environ.get("COHERE_API_KEY"):
            provider = "cohere"
        elif os.environ.get("OPENROUTER_API_KEY"):
            provider = "openrouter"
        else:
            raise RuntimeError(
                "No reranker available. Set COHERE_API_KEY or OPENROUTER_API_KEY."
            )

    if provider == "cohere":
        return rerank_cohere(query, documents, top_n, model or "rerank-v3.5")
    elif provider == "openrouter":
        return rerank_openrouter(query, documents, top_n, model or "cohere/rerank-v3.5")
    else:
        raise ValueError(f"Unknown rerank provider: {provider}")


# ── Checkpoint helpers ───────────────────────────────────────────


def load_checkpoint(path: str) -> dict | None:
    """Load checkpoint state from a JSON file, or None if not found."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save_checkpoint(path: str, state: dict) -> None:
    """Save checkpoint state to a JSON file (atomic via tmp+rename)."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, default=str)
    os.replace(tmp, path)


# ── S2 citation-count enrichment ────────────────────────────────


def _best_s2_lookup_id(paper: dict) -> str | None:
    """Pick the best external ID to query S2 /paper/batch with.

    Priority: arXiv > DOI (excluding arXiv-shadow ``10.48550/arXiv.*`` which
    S2 rejects) > existing S2 paperId (if not an OpenAlex W-ID) > CorpusId.

    Returns a pre-prefixed ID suitable for S2's batch endpoint
    (``ARXIV:1706.03762``, ``DOI:10.x``, ``CorpusId:123``), or the bare S2
    paperId when that is what we have.
    """
    ext = paper.get("externalIds") or {}
    arxiv = ext.get("ArXiv")
    if arxiv:
        return f"ARXIV:{arxiv}"
    doi = ext.get("DOI")
    if doi and not str(doi).lower().startswith("10.48550/arxiv"):
        return f"DOI:{doi}"
    pid = paper.get("paperId") or ""
    if pid and not re.fullmatch(r"W\d+", pid):
        return pid
    cid = paper.get("corpusId") or ext.get("CorpusId")
    if cid:
        return f"CorpusId:{cid}"
    return None


def enrich_citation_counts_from_s2(
    papers: list[dict],
    *,
    fields: str = "paperId,corpusId,externalIds,citationCount,influentialCitationCount",
    chunk_size: int = 500,
) -> list[dict]:
    """In-place enrich papers with S2 citation counts and IDs.

    For each paper, resolves the best external ID (DOI preferred, arXiv
    fallback), batches lookups via ``/paper/batch``, and then:

    - Sets ``citationCount = max(existing, s2_count)`` — **never lowers**.
    - Copies ``influentialCitationCount`` from S2 when absent.
    - Merges missing ``externalIds`` and ``corpusId`` from the S2 record.
    - If the paper's ``paperId`` was an OpenAlex W-ID, replaces it with
      the S2 paperId so downstream registry rows line up with other
      S2-origin papers.
    - Stamps ``_enrichment = "ok" | "miss"`` per paper.

    If the S2 circuit breaker is open, stamps every paper with
    ``_enrichment = "failed"`` and leaves counts untouched. Emits a loud
    stderr warning so callers know ``--min-citations`` is running against
    the raw source count.

    Returns the same list (enriched in place).
    """
    if not papers:
        return papers

    if not s2_circuit_breaker.allow_request():
        print(
            "⚠️  S2 circuit breaker OPEN — citation-count enrichment skipped. "
            "Downstream --min-citations / --sort-by citations will use raw "
            "source counts.",
            file=sys.stderr,
        )
        for p in papers:
            p["_enrichment"] = "failed"
        return papers

    # Build lookup ID per paper, remember index so we can map results back.
    lookup_ids: list[str] = []
    idx_for_id: dict[str, list[int]] = {}
    for i, p in enumerate(papers):
        lid = _best_s2_lookup_id(p)
        if not lid:
            p["_enrichment"] = "miss"
            continue
        idx_for_id.setdefault(lid, []).append(i)
        lookup_ids.append(lid)

    if not lookup_ids:
        return papers

    # Dedup while preserving order; the batch endpoint returns positional
    # results, so duplicate IDs just waste payload.
    seen: set[str] = set()
    unique_ids: list[str] = []
    for lid in lookup_ids:
        if lid not in seen:
            seen.add(lid)
            unique_ids.append(lid)

    results_by_id: dict[str, dict] = {}
    with httpx.Client() as client:
        for start in range(0, len(unique_ids), chunk_size):
            chunk = unique_ids[start : start + chunk_size]
            try:
                check_s2_circuit()
                data = request_with_retry(
                    client,
                    f"{S2_BASE}/paper/batch",
                    params={"fields": fields},
                    headers=s2_headers(),
                    method="POST",
                    json_body={"ids": chunk},
                )
                s2_circuit_breaker.record_success()
            except Exception as e:
                s2_circuit_breaker.record_failure()
                print(
                    f"⚠️  S2 batch enrichment failed at chunk {start}: {e}",
                    file=sys.stderr,
                )
                # Mark the whole remaining tail as failed but keep going —
                # partial enrichment is still useful.
                for lid in chunk:
                    for idx in idx_for_id.get(lid, []):
                        papers[idx]["_enrichment"] = "failed"
                continue

            if not isinstance(data, list):
                continue
            # S2 returns nulls positionally for unresolved IDs.
            for lid, row in zip(chunk, data):
                if row:
                    results_by_id[lid] = row

    for lid, row in results_by_id.items():
        for idx in idx_for_id.get(lid, []):
            p = papers[idx]
            # citationCount: take the max; never clobber a higher existing
            # value with a lower S2 value (and vice versa).
            cur = p.get("citationCount") or 0
            s2_count = row.get("citationCount") or 0
            p["citationCount"] = max(cur, s2_count)
            if row.get("influentialCitationCount") is not None and p.get(
                "influentialCitationCount"
            ) in (None, 0):
                p["influentialCitationCount"] = row["influentialCitationCount"]
            # Merge externalIds and corpusId.
            merged = dict(row.get("externalIds") or {})
            merged.update(p.get("externalIds") or {})
            p["externalIds"] = merged
            if row.get("corpusId") and not p.get("corpusId"):
                p["corpusId"] = row["corpusId"]
            # Replace paperId when we started with an OpenAlex W-ID.
            s2_pid = row.get("paperId")
            if s2_pid and re.fullmatch(r"W\d+", p.get("paperId") or ""):
                # Preserve the OA ID under externalIds for round-tripping.
                if "OpenAlex" not in p["externalIds"]:
                    p["externalIds"]["OpenAlex"] = p["paperId"]
                p["paperId"] = s2_pid
            p["_enrichment"] = "ok"

    # Anything still without _enrichment got a lookup_id but no result.
    for p in papers:
        p.setdefault("_enrichment", "miss")

    return papers


# ── Output helpers ───────────────────────────────────────────────


def add_output_args(parser: "argparse.ArgumentParser") -> None:
    """Add common --output and --append arguments to a parser."""

    parser.add_argument(
        "--output",
        "-o",
        help="Write results to JSONL file instead of stdout",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to output file instead of overwriting",
    )
    parser.add_argument(
        "--dedup-by",
        choices=["paperId", "corpusId"],
        default=None,
        help="Deduplicate results by paperId or corpusId before emitting "
        "(default: auto — paperId with corpusId fallback when --append is used)",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable auto-dedup in --append mode (keeps duplicate rows)",
    )


def _extract_id(p: dict, key: str) -> "str | None":
    """Extract normalized ID (paperId or corpusId) from a paper record."""
    if key == "corpusId":
        k = p.get("corpusId")
        if not k:
            ext = p.get("externalIds") or {}
            k = ext.get("CorpusId")
        return str(k) if k else None
    k = p.get(key)
    return str(k) if k else None


def _read_existing_ids(path: str, key: str) -> "set[str]":
    """Read paperId/corpusId values already present in a JSONL file."""
    ids: set[str] = set()
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                pid = _extract_id(r, key) or _extract_id(r, "paperId")
                if pid:
                    ids.add(pid)
                # Always also record corpusId so we catch cross-key collisions
                cid = _extract_id(r, "corpusId")
                if cid:
                    ids.add(cid)
    except FileNotFoundError:
        pass
    return ids


def emit_results(
    papers: list[dict],
    args: Any,
    format_fn: Any = None,
    title: str = "",
) -> None:
    """Output results to file or stdout based on args.

    If args.output is set, writes JSONL to file.
    Otherwise prints JSON (if args.json) or formatted markdown.

    Dedup behavior:
    - If `args.dedup_by` is set explicitly, dedup within the batch by that key.
    - In `--append` mode (and `args.no_dedup` not set), also cross-file dedup:
      read existing paperId/corpusId values from the target file and drop
      any incoming paper whose ID already exists. This prevents the common
      case where repeated `--append` runs (10 scholar queries, 3 citation
      traversals, etc.) leave the same paper 4–5× in the pool.
    - Pass `--no-dedup` to keep the old behavior (raw append, duplicates OK).
    """
    no_dedup = getattr(args, "no_dedup", False)
    append = bool(getattr(args, "append", False))
    output = getattr(args, "output", None)
    dedup_by = getattr(args, "dedup_by", None)

    # Within-batch dedup if explicitly requested
    if dedup_by:
        before = len(papers)
        papers = dedup_papers(papers, key=dedup_by)
        if before != len(papers):
            print(
                f"Deduplicated {before} → {len(papers)} papers (by {dedup_by})",
                file=sys.stderr,
            )

    # Auto-dedup in append mode: within-batch + cross-file
    if append and output and not no_dedup:
        # Within-batch: if not already deduped explicitly, do paperId+corpusId
        if not dedup_by:
            before = len(papers)
            # Dedup by paperId first, then by corpusId (catches cross-key dupes)
            papers = dedup_papers(papers, key="paperId")
            papers = dedup_papers(papers, key="corpusId")
            dropped_intra = before - len(papers)
        else:
            dropped_intra = 0

        # Cross-file: skip papers whose ID is already in the target
        existing = _read_existing_ids(output, key="paperId")
        if existing:
            kept = []
            dropped_cross = 0
            for p in papers:
                pid = _extract_id(p, "paperId") or _extract_id(p, "corpusId")
                cid = _extract_id(p, "corpusId")
                if (pid and pid in existing) or (cid and cid in existing):
                    dropped_cross += 1
                    continue
                kept.append(p)
            if dropped_intra or dropped_cross:
                print(
                    f"Dedup: dropped {dropped_intra} within-batch + "
                    f"{dropped_cross} already-in-file duplicates "
                    f"(pass --no-dedup to disable)",
                    file=sys.stderr,
                )
            papers = kept
        elif dropped_intra:
            print(
                f"Dedup: dropped {dropped_intra} within-batch duplicates "
                f"(pass --no-dedup to disable)",
                file=sys.stderr,
            )

    if output:
        count = write_jsonl(output, papers, append=append)
        total = count
        if getattr(args, "append", False) and os.path.exists(args.output):
            total = sum(1 for _ in open(args.output))
        # Human-readable summary goes to stderr (as before).
        print(
            f"Wrote {count} papers to {args.output}"
            + (f" ({total} total)" if getattr(args, "append", False) else ""),
            file=sys.stderr,
        )
        # Machine-readable summary goes to stdout, so callers using shell
        # redirection (`script.py ... > run.json`) capture something non-empty
        # and programmatic pipelines can consume the count without grepping
        # stderr. The structure is deliberately minimal and stable.
        summary = {
            "status": "ok",
            "written": count,
            "total": total,
            "output": args.output,
            "appended": bool(getattr(args, "append", False)),
        }
        print(json.dumps(summary))
        return

    if getattr(args, "json", False):
        print(json.dumps(papers, indent=2))
        return

    if title:
        print(f"# {title}\n")
    print(f"Found **{len(papers)}** papers\n")
    if format_fn:
        for i, p in enumerate(papers, 1):
            print(format_fn(p, i))
    else:
        print(json.dumps(papers, indent=2))
