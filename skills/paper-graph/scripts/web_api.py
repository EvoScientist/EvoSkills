"""HTTP layer: retry decorator + Semantic Scholar + DeepXiv fallback.

Pure I/O. Every HTTP call goes through ``retry_http`` so transient
429/5xx are absorbed. S2 is the primary source; ``_deepxiv_search``
fills the budget from arXiv (via the DeepXiv SDK) when S2 returns too
few hits or 429-quotas us. DeepXiv items are reshaped into the same
dict shape ``_normalize_s2_paper`` produces so downstream callers
don't need to branch on source.
"""

from __future__ import annotations

import asyncio
import functools
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable, TypeVar

import httpx

try:
    from .config import (
        S2_SEARCH_URL,
        S2_LOOKUP_URL,
        S2_REFS_URL,
        S2_CITES_URL,
        S2_FIELDS,
        S2_REL_FIELDS,
        S2_CITING_FIELDS,
        PROCEEDINGS_TITLE_RE,
    )
    from . import deepxiv_client
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import (  # type: ignore
        S2_SEARCH_URL,
        S2_LOOKUP_URL,
        S2_REFS_URL,
        S2_CITES_URL,
        S2_FIELDS,
        S2_REL_FIELDS,
        S2_CITING_FIELDS,
        PROCEEDINGS_TITLE_RE,
    )
    import deepxiv_client  # type: ignore


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

# Retryable transient statuses: rate-limit + common 5xx blips.
RETRY_STATUSES = frozenset({429, 502, 503, 504})


def retry_http(
    attempts: int = 3,
    base: float = 1.0,
    statuses: frozenset[int] = RETRY_STATUSES,
) -> Callable[[F], F]:
    """Retry an async httpx call with exponential backoff on transient statuses.

    Decorated function must call ``r.raise_for_status()`` (or otherwise raise
    ``httpx.HTTPStatusError`` on retryable failures). Anything not in
    ``statuses`` propagates immediately; after the final attempt, the last
    error propagates as well — callers that want soft-fail-to-None should
    wrap with their own ``try/except httpx.HTTPError``.
    """

    def deco(fn: F) -> F:
        @functools.wraps(fn)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            for i in range(attempts):
                try:
                    return await fn(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code not in statuses or i == attempts - 1:
                        raise
                await asyncio.sleep(base * (2**i))  # 1s, 2s, 4s by default
            raise RuntimeError("retry_http: unreachable")  # pragma: no cover

        return wrapped  # type: ignore[return-value]

    return deco


# ---------------------------------------------------------------------------
# URL / paper-shape helpers
# ---------------------------------------------------------------------------


def _is_proceedings_volume(paper: dict[str, Any]) -> bool:
    """Heuristic: title literally contains the word 'proceedings'."""
    title = paper.get("title") or ""
    return bool(PROCEEDINGS_TITLE_RE.search(title))


def _build_paper_url(item: dict[str, Any]) -> str:
    """Best-effort canonical URL for an S2 paper.

    Order: arxiv > DOI > S2 paper page. Always returns a non-empty string
    if the paper has any of these identifiers — used downstream so the
    LLM sees a verifiable link for every paper and the reader of the
    final graph can click through.
    """
    ext = item.get("externalIds") or {}
    arxiv = ext.get("ArXiv") or ext.get("arxiv") or ext.get("arXiv")
    if arxiv:
        return f"https://arxiv.org/abs/{arxiv}"
    doi = ext.get("DOI") or ext.get("doi")
    if doi:
        return f"https://doi.org/{doi}"
    pid = item.get("paperId") or ""
    if pid:
        return f"https://www.semanticscholar.org/paper/{pid}"
    return ""


def _normalize_s2_paper(item: dict[str, Any]) -> dict[str, Any]:
    """Flatten an S2 paper JSON into the shape used throughout this script."""
    authors = ", ".join(a.get("name", "") for a in (item.get("authors") or []))
    ext = item.get("externalIds") or {}
    arxiv_id = ext.get("ArXiv") or ext.get("arxiv") or ext.get("arXiv") or ""
    return {
        "paperId": item.get("paperId") or "",
        "title": item.get("title") or "Untitled",
        "year": item.get("year") or "n.d.",
        "abstract": item.get("abstract") or "",
        "authors": authors or "N/A",
        "venue": item.get("venue") or "",
        "citationCount": item.get("citationCount") or 0,
        "arxiv_id": arxiv_id,
        "url": _build_paper_url(item),
    }


# ---------------------------------------------------------------------------
# Semantic Scholar
# ---------------------------------------------------------------------------


@retry_http()
async def _resolve_arxiv_paper_inner(
    client: httpx.AsyncClient, s2_key: str, arxiv_id: str
) -> dict[str, Any]:
    url = S2_LOOKUP_URL.format(external_id=f"ARXIV:{arxiv_id}")
    r = await client.get(
        url,
        params={"fields": S2_FIELDS},
        headers={"x-api-key": s2_key},
        timeout=30.0,
    )
    r.raise_for_status()
    item = r.json()
    return {**_normalize_s2_paper(item), "arxiv_id": arxiv_id}


@retry_http()
async def _s2_search(
    client: httpx.AsyncClient,
    s2_key: str,
    search_query: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Semantic Scholar paper search."""
    params = {"query": search_query, "limit": limit, "fields": S2_FIELDS}
    headers = {"x-api-key": s2_key}
    r = await client.get(S2_SEARCH_URL, params=params, headers=headers, timeout=60.0)
    r.raise_for_status()
    data = r.json()
    return [_normalize_s2_paper(item) for item in (data.get("data") or [])]


@retry_http()
async def _s2_paper_references(
    client: httpx.AsyncClient,
    s2_key: str,
    paper_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Papers cited by ``paper_id`` (ancestors)."""
    url = S2_REFS_URL.format(paper_id=paper_id)
    params = {"limit": limit, "fields": S2_REL_FIELDS}
    headers = {"x-api-key": s2_key}
    r = await client.get(url, params=params, headers=headers, timeout=60.0)
    r.raise_for_status()
    out: list[dict[str, Any]] = []
    for item in r.json().get("data") or []:
        nested = item.get("citedPaper") or {}
        if nested.get("paperId"):
            out.append(_normalize_s2_paper(nested))
    return out


@retry_http()
async def _s2_paper_citations(
    client: httpx.AsyncClient,
    s2_key: str,
    paper_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Papers citing ``paper_id`` (descendants)."""
    url = S2_CITES_URL.format(paper_id=paper_id)
    params = {"limit": limit, "fields": S2_CITING_FIELDS}
    headers = {"x-api-key": s2_key}
    r = await client.get(url, params=params, headers=headers, timeout=60.0)
    r.raise_for_status()
    out: list[dict[str, Any]] = []
    for item in r.json().get("data") or []:
        nested = item.get("citingPaper") or {}
        if nested.get("paperId"):
            out.append(_normalize_s2_paper(nested))
    return out


# ---------------------------------------------------------------------------
# DeepXiv (arXiv) fallback
# ---------------------------------------------------------------------------


def _normalize_deepxiv_item(item: dict[str, Any]) -> dict[str, Any]:
    """Reshape a DeepXiv result into the same shape ``_normalize_s2_paper``
    produces, so the round-robin merger and the classifier don't need to
    branch on source.

    Fills ``paperId`` with the synthetic ``arxiv:<id>`` form (matches
    paper-navigator's convention) so dedup-by-paperId still works when
    the same paper appears in both S2 and DeepXiv result sets.
    """
    arxiv_id = deepxiv_client.item_id(item)
    title = (item.get("title") or "Untitled").replace("\n", " ").strip()
    abstract = (item.get("abstract") or "").replace("\n", " ").strip()
    authors_list = deepxiv_client.item_authors(item)
    authors = ", ".join(authors_list) if authors_list else "N/A"
    published = item.get("date") or item.get("publish_at") or ""
    year: Any = "n.d."
    if published:
        try:
            year = int(str(published)[:4])
        except (ValueError, IndexError):
            pass
    url = (
        f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else (item.get("src_url") or "")
    )
    return {
        "paperId": f"arxiv:{arxiv_id}" if arxiv_id else "",
        "title": title,
        "year": year,
        "abstract": abstract,
        "authors": authors,
        "venue": "arXiv",
        "citationCount": item.get("citation_count") or item.get("citation") or 0,
        "arxiv_id": arxiv_id,
        "url": url,
    }


async def _deepxiv_search(query: str, limit: int) -> list[dict[str, Any]]:
    """Run a DeepXiv arXiv search and return S2-shaped paper dicts.

    The DeepXiv SDK is synchronous, so the call is wrapped in
    ``run_in_executor`` to keep the event loop responsive. SDK errors
    propagate so the caller can soft-fail or log them.
    """
    loop = asyncio.get_running_loop()
    items = await loop.run_in_executor(
        None, lambda: deepxiv_client.search(query=query, limit=limit)
    )
    return [_normalize_deepxiv_item(it) for it in items]
