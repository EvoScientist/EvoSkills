"""Thin wrapper around the DeepXiv SDK for arXiv paper search.

Replaces direct calls to the arXiv API (``export.arxiv.org/api/query``), which
enforce a 3-second delay and frequently return HTTP 429. DeepXiv
(https://github.com/qhjqhj00/deepxiv_sdk) is a token-based, agent-oriented API
that returns pre-parsed, structured results.

Auth is optional: anonymous use allows 1,000 requests/day. Set
``DEEPXIV_API_TOKEN`` (or ``DEEPXIV_TOKEN``) for 10,000/day.

The DeepXiv ``Reader`` is imported lazily inside ``get_reader`` so that:
  * the dependency is only required when an arXiv search actually runs, and
  * tests can monkeypatch ``get_reader`` without installing the SDK.
"""

from __future__ import annotations

import os
from typing import Any

# Checked in priority order. DEEPXIV_API_TOKEN is the name used by this skill
# (and by issue #19); DEEPXIV_TOKEN is the name the SDK's own CLI reads.
TOKEN_ENV_VARS = ("DEEPXIV_API_TOKEN", "DEEPXIV_TOKEN")


def deepxiv_token() -> str | None:
    """Return the DeepXiv API token from the environment, or None if unset."""
    for var in TOKEN_ENV_VARS:
        val = os.environ.get(var)
        if val:
            return val
    return None


def get_reader(timeout: int = 30):
    """Construct a DeepXiv ``Reader``. Imported lazily (see module docstring)."""
    from deepxiv_sdk import Reader

    return Reader(token=deepxiv_token(), timeout=timeout)


def search(
    query: str,
    *,
    limit: int = 10,
    categories: list[str] | None = None,
    authors: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    reader: Any = None,
) -> list[dict]:
    """Run a DeepXiv arXiv search and return the list of raw result items.

    Args:
        query: Search query (required; DeepXiv rejects empty queries).
        limit: Max results, clamped to the DeepXiv-supported range 1..100.
        categories: arXiv category filter, e.g. ``["cs.CL", "cs.AI"]``.
        authors: Author-name filter.
        date_from / date_to: ``YYYY-MM-DD`` bounds. The SDK maps a pair to a
            ``between`` filter, a lone ``date_from`` to ``after``, etc.
        reader: Optional pre-built reader (used by tests). Defaults to
            ``get_reader()``.

    Returns:
        The ``result`` list from the DeepXiv response (possibly empty). Each
        item is a dict with keys such as ``arxiv_id``, ``title``, ``abstract``,
        ``authors``, ``date``/``publish_at``, ``categories``, ``src_url``.
    """
    if reader is None:
        reader = get_reader()
    res = reader.search(
        query=query,
        size=max(1, min(limit, 100)),
        categories=categories or None,
        authors=authors or None,
        date_from=date_from,
        date_to=date_to,
    )
    if isinstance(res, dict):
        return res.get("result") or []
    return []


def item_id(item: dict) -> str:
    """Extract the arXiv (or bio/medRxiv) id from a DeepXiv result item."""
    return (
        item.get("arxiv_id") or item.get("biorxiv_id") or item.get("medrxiv_id") or ""
    )


def item_authors(item: dict) -> list[str]:
    """Normalize a DeepXiv item's authors to a list of name strings."""
    raw = item.get("authors") or []
    names: list[str] = []
    for a in raw:
        if isinstance(a, dict):
            name = a.get("name") or a.get("full_name") or ""
        else:
            name = str(a)
        if name:
            names.append(name)
    return names
