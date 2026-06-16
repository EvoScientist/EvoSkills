"""Pipeline data helpers (no LLM calls).

The skill is agent-driven: every LLM stage is the agent's responsibility
(it reads a template from ``references/<name>.md`` and calls its own
model). This module holds the deterministic data layer that the
``cli.py`` subcommands wrap — arxiv resolution, S2 / DeepXiv search,
section fetching, and the text formatters used to build prompt
inputs.

Functions:
    extract_arxiv_ids        — regex over the raw query
    resolve_seed_papers      — S2 lookup for arxiv IDs in the query
    _format_seed_block       — render seed papers into the {seed_block}
                               fragment for parse_query.md
    fetch_related_papers     — S2 multi-search + DeepXiv fallback
    _format_one_paper        — render one paper for the {papers_input}
                               prompt fragment
    _render_excerpt_block    — render a discussion/conclusion section
                               into the paper appendix blockquote
    _label_of                — classification label accessor
                               (defaults to CORE)
    _prefetch_paper_sections — best-effort paper_md fetch + section
                               extraction for the OC-source signal
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from typing import Any

import httpx

try:
    from . import prompts as P
    from . import paper_md
    from .config import ARXIV_ID_RE
    from .logger import Logger
    from .web_api import (
        _resolve_arxiv_paper_inner,
        _s2_search,
        _s2_paper_references,
        _s2_paper_citations,
        _deepxiv_search,
        _is_proceedings_volume,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    import prompts as P  # type: ignore
    import paper_md  # type: ignore
    from config import ARXIV_ID_RE  # type: ignore
    from logger import Logger  # type: ignore
    from web_api import (  # type: ignore
        _resolve_arxiv_paper_inner,
        _s2_search,
        _s2_paper_references,
        _s2_paper_citations,
        _deepxiv_search,
        _is_proceedings_volume,
    )


# ---------------------------------------------------------------------------
# Seed extraction + query parsing
# ---------------------------------------------------------------------------


def extract_arxiv_ids(text: str) -> list[str]:
    """Return unique arxiv IDs mentioned in ``text``, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for m in ARXIV_ID_RE.finditer(text):
        aid = m.group(1)
        if aid not in seen:
            seen.add(aid)
            out.append(aid)
    return out


async def resolve_seed_papers(
    client: httpx.AsyncClient,
    s2_key: str,
    query: str,
    logger: Logger | None = None,
) -> list[dict[str, Any]]:
    """Extract arxiv IDs from the query and resolve each via S2."""
    ids = extract_arxiv_ids(query)
    if logger is not None:
        logger.event("seed_extract", arxiv_ids=ids)
    resolved: list[dict[str, Any]] = []
    for aid in ids:
        paper: dict[str, Any] | None
        reason = None
        try:
            paper = await _resolve_arxiv_paper_inner(client, s2_key, aid)
        except httpx.HTTPStatusError as e:
            paper = None
            reason = f"http_{e.response.status_code}_after_retries"
        except httpx.HTTPError as e:
            paper = None
            reason = f"network_error: {type(e).__name__}"
        if logger is not None:
            logger.event(
                "seed_resolve",
                arxiv_id=aid,
                hit=paper is not None,
                title=paper["title"] if paper else None,
                reason=reason,
            )
        if paper is not None:
            resolved.append({**paper, "_source": "seed_arxiv"})
    return resolved


def _format_seed_block(seed_papers: list[dict[str, Any]]) -> str:
    if not seed_papers:
        return ""
    lines: list[str] = []
    for p in seed_papers:
        lines.append(
            f"- arxiv:{p.get('arxiv_id', '?')} | {p['title']} ({p['year']})\n"
            f"  Authors: {p['authors']}\n"
            f"  Abstract: {p['abstract'] or 'No abstract available.'}"
        )
    return P.SEED_PAPER_BLOCK.format(papers="\n".join(lines))


# ---------------------------------------------------------------------------
# Paper fetching
# ---------------------------------------------------------------------------


async def _s2_multi_search(
    client: httpx.AsyncClient,
    s2_key: str,
    searches: list[str],
    per_query_limit: int,
    logger: Logger | None = None,
) -> list[list[dict[str, Any]]]:
    """Run multiple S2 searches sequentially with a small inter-query delay.

    S2's free tier rate-limits aggressive bursts (we hit 429 during testing),
    so the calls are run sequentially with a small sleep between them. The
    return is a list-of-lists preserving each query's ranked order so the
    caller can round-robin merge.
    """
    out: list[list[dict[str, Any]]] = []
    for i, q in enumerate(searches):
        if i > 0:
            await asyncio.sleep(1.0)
        try:
            hits = await _s2_search(client, s2_key, q, per_query_limit)
        except httpx.HTTPError as e:
            if logger is not None:
                logger.event("s2_search_error", query=q, error=str(e))
            hits = []
        # Drop conference-proceedings volumes explicitly (they have no
        # abstract today, but the regex doesn't rely on that side-effect).
        dropped_proceedings = [p for p in hits if _is_proceedings_volume(p)]
        hits = [p for p in hits if not _is_proceedings_volume(p)]
        # Stamp rank + originating sub-query so the final provenance log
        # can answer "where did this paper come from?" by paper number.
        for rank, p in enumerate(hits, start=1):
            p["_query_index"] = i
            p["_source_query"] = q
            p["_rank"] = rank
        if logger is not None:
            logger.event(
                "s2_search",
                search_query=q,
                query_index=i,
                requested=per_query_limit,
                returned=len(hits) + len(dropped_proceedings),
                kept=len(hits),
                with_abstract=sum(1 for p in hits if p["abstract"]),
                dropped_proceedings=[p["title"][:100] for p in dropped_proceedings],
                titles=[p["title"] for p in hits],
            )
        out.append(hits)
    return out


def _round_robin_merge(
    ranked_lists: list[list[dict[str, Any]]],
    dedup_keys: set[str],
    take: int,
) -> list[dict[str, Any]]:
    """Round-robin pick from each ranked list, skipping duplicates.

    Duplicates are detected via ``paperId`` (falling back to ``title``).
    ``dedup_keys`` is updated in place — start with the keys of papers
    already in the final set (e.g. seed papers).
    """
    cursors = [0] * len(ranked_lists)
    result: list[dict[str, Any]] = []
    while len(result) < take:
        progressed = False
        for i, lst in enumerate(ranked_lists):
            if len(result) >= take:
                break
            # Advance cursor[i] past any duplicates or already-picked entries.
            while cursors[i] < len(lst):
                p = lst[cursors[i]]
                key = p.get("paperId") or p.get("title", "")
                cursors[i] += 1
                if key and key in dedup_keys:
                    continue
                # Found a fresh paper from this query. Preserve upstream
                # `_query_index` / `_rank` if already stamped (set by
                # _s2_multi_search for primary lexical results); only fall
                # back to the merge-position index when absent (refs/cites
                # path, where the list-of-lists shape is per-seed).
                dedup_keys.add(key)
                merged = {**p}
                merged.setdefault("_query_index", i)
                result.append(merged)
                progressed = True
                break
        if not progressed:
            break  # all queries exhausted
    return result


async def fetch_related_papers(
    client: httpx.AsyncClient,
    keys: dict[str, str],
    searches: list[str],
    cite_number: int,
    seed_papers: list[dict[str, Any]] | None = None,
    logger: Logger | None = None,
) -> list[dict[str, Any]]:
    """Fetch ``cite_number`` papers across multiple S2 search phrases.

    Each phrase in ``searches`` is run as its own S2 paper-search call;
    results are deduped by ``paperId`` and merged round-robin (1st-from-q1,
    1st-from-q2, ..., then 2nd-from-q1, ...). If the union still underfills,
    Serper + Jina is used as before for the remaining slots.

    Any pre-resolved ``seed_papers`` (from arxiv-ID resolution) anchor the
    result at the front.
    """
    seeds = list(seed_papers or [])
    remaining = max(0, cite_number - len(seeds))
    # Dedup keys: seed paperIds (or titles when paperId is missing).
    dedup_keys: set[str] = {(p.get("paperId") or p.get("title", "")) for p in seeds}

    if remaining == 0:
        if logger is not None:
            logger.event(
                "fetch_papers_done",
                seed_count=len(seeds),
                primary_count=0,
                fallback_count=0,
                final_titles=[p["title"] for p in seeds],
                final_sources=[p.get("_source") for p in seeds],
            )
        return seeds

    # Per-paper provenance trail — one entry per final paper, so a single
    # `fetch_papers_done` record answers "where did paper (N) come from?
    # which sub-query, which rank, or which seed's refs/cites?"
    def _provenance(papers_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i, p in enumerate(papers_list, start=1):
            src = p.get("_source", "?")
            entry: dict[str, Any] = {
                "paper_n": i,
                "source": src,
                "paperId": p.get("paperId", ""),
                "title": p.get("title", ""),
            }
            if p.get("arxiv_id"):
                entry["arxiv_id"] = p["arxiv_id"]
            if src == "s2":
                entry["source_query_index"] = p.get("_query_index")
                entry["source_query"] = p.get("_source_query")
                entry["source_rank"] = p.get("_rank")
            elif src in ("s2_ref", "s2_cite"):
                entry["seed_id"] = p.get("_seed_id")
                entry["source_rank"] = p.get("_rank")
            elif src == "deepxiv":
                entry["source_rank"] = p.get("_rank")
            out.append(entry)
        return out

    # Per-query S2 budget: enough to give each phrase room to contribute
    # plus a margin for duplicates and abstract-less filtering.
    n_q = max(1, len(searches))
    per_query_limit = max(5, (remaining * 2) // n_q + 3)
    ranked = await _s2_multi_search(
        client, keys["S2_API_KEY"], searches, per_query_limit, logger=logger
    )

    # Drop papers without abstracts — the outline + detail LLMs read only
    # the abstract to place a paper in the taxonomy, so a paper without
    # one would force the LLM to guess from title alone. Proceedings
    # volumes were already filtered in _s2_multi_search; this catches
    # other abstract-less stubs.
    ranked_filtered = [[p for p in lst if p["abstract"]] for lst in ranked]

    primary = _round_robin_merge(ranked_filtered, dedup_keys, remaining)
    primary = [{**p, "_source": "s2"} for p in primary]

    if len(primary) >= remaining:
        result = seeds + primary
        if logger is not None:
            logger.event(
                "fetch_papers_done",
                seed_count=len(seeds),
                primary_count=len(primary),
                refcite_count=0,
                fallback_count=0,
                final_titles=[p["title"] for p in result],
                final_sources=[p.get("_source") for p in result],
                final_query_indices=[p.get("_query_index") for p in result],
                provenance=_provenance(result),
            )
        return result

    # ------------------------------------------------------------------
    # Refs + cites fallback (only if a seed paper was resolved).
    # Lateral lexical search couldn't fill the budget; use the citation
    # graph instead. References = ancestors, citations = descendants.
    # ------------------------------------------------------------------
    refcite_papers: list[dict[str, Any]] = []
    needed_after_lexical = remaining - len(primary)
    if needed_after_lexical > 0 and seeds:
        ref_lists: list[list[dict[str, Any]]] = []
        for seed in seeds:
            seed_id = seed.get("paperId")
            if not seed_id:
                continue
            try:
                refs = await _s2_paper_references(client, keys["S2_API_KEY"], seed_id)
            except httpx.HTTPError as e:
                if logger is not None:
                    logger.event("s2_refs_error", seed_id=seed_id, error=str(e))
                refs = []
            await asyncio.sleep(1.0)
            try:
                cites = await _s2_paper_citations(client, keys["S2_API_KEY"], seed_id)
            except httpx.HTTPError as e:
                if logger is not None:
                    logger.event("s2_cites_error", seed_id=seed_id, error=str(e))
                cites = []
            # Drop proceedings volumes & abstract-less; sort each list by
            # citation count desc so the most influential ancestors /
            # descendants come first.
            refs = sorted(
                (p for p in refs if p["abstract"] and not _is_proceedings_volume(p)),
                key=lambda p: p.get("citationCount", 0),
                reverse=True,
            )
            cites = sorted(
                (p for p in cites if p["abstract"] and not _is_proceedings_volume(p)),
                key=lambda p: p.get("citationCount", 0),
                reverse=True,
            )
            if logger is not None:
                logger.event(
                    "s2_refs",
                    seed_id=seed_id,
                    kept=len(refs),
                    titles=[p["title"] for p in refs[:20]],
                )
                logger.event(
                    "s2_cites",
                    seed_id=seed_id,
                    kept=len(cites),
                    titles=[p["title"] for p in cites[:20]],
                )
            ref_lists.append(
                [
                    {**p, "_source": "s2_ref", "_seed_id": seed_id, "_rank": r}
                    for r, p in enumerate(refs, start=1)
                ]
            )
            ref_lists.append(
                [
                    {**p, "_source": "s2_cite", "_seed_id": seed_id, "_rank": r}
                    for r, p in enumerate(cites, start=1)
                ]
            )

        if ref_lists:
            picked = _round_robin_merge(ref_lists, dedup_keys, needed_after_lexical)
            refcite_papers.extend(picked)

    if len(primary) + len(refcite_papers) >= remaining:
        result = seeds + primary + refcite_papers
        if logger is not None:
            logger.event(
                "fetch_papers_done",
                seed_count=len(seeds),
                primary_count=len(primary),
                refcite_count=len(refcite_papers),
                fallback_count=0,
                final_titles=[p["title"] for p in result],
                final_sources=[p.get("_source") for p in result],
            )
        return result

    # Fallback — top up via DeepXiv arXiv search. Single call on the joined
    # search string (DeepXiv is broad enough that per-phrase runs would just
    # eat budget without adding coverage). Items are pre-shaped by
    # _normalize_deepxiv_item to look like S2 results, so dedup_keys +
    # the round-robin merger work without branching on source.
    needed = remaining - len(primary) - len(refcite_papers)
    fallback_query = " ".join(searches)
    fallbacks: list[dict[str, Any]] = []
    try:
        deepxiv_hits = await _deepxiv_search(fallback_query, limit=needed * 3)
    except Exception as e:
        deepxiv_hits = []
        if logger is not None:
            logger.event(
                "deepxiv_search_error",
                query=fallback_query,
                error=f"{type(e).__name__}: {e}",
            )
    # Apply the same filters that S2 results get: drop proceedings volumes
    # and abstract-less stubs (DeepXiv occasionally returns those too).
    deepxiv_hits = [
        p for p in deepxiv_hits if p["abstract"] and not _is_proceedings_volume(p)
    ]
    for rank, p in enumerate(deepxiv_hits, start=1):
        if len(fallbacks) >= needed:
            break
        key = p.get("paperId") or p.get("title", "")
        if key and key in dedup_keys:
            continue
        dedup_keys.add(key)
        fallbacks.append({**p, "_source": "deepxiv", "_rank": rank})
    if logger is not None:
        logger.event(
            "deepxiv_search",
            search_query=fallback_query,
            needed=needed,
            returned=len(deepxiv_hits),
            kept=len(fallbacks),
            titles=[p["title"] for p in fallbacks],
        )
    result = seeds + primary + refcite_papers + fallbacks
    if logger is not None:
        logger.event(
            "fetch_papers_done",
            seed_count=len(seeds),
            primary_count=len(primary),
            refcite_count=len(refcite_papers),
            fallback_count=len(fallbacks),
            final_titles=[p["title"] for p in result],
            final_sources=[p.get("_source") for p in result],
            provenance=_provenance(result),
        )
    return result


# ---------------------------------------------------------------------------
# Paper formatting for prompts + appendix
# ---------------------------------------------------------------------------


def _format_one_paper(n: int, p: dict[str, Any]) -> str:
    """Single paper entry for an LLM prompt. URL is shown so the model can
    cite verifiable sources and so a downstream reader can click through.

    When a Discussion/Conclusion/Limitations excerpt has been prefetched
    (see ``_prefetch_paper_sections``), it is appended after the abstract.
    The detail prompt prefers this excerpt over the abstract for Open
    Challenge sourcing, because abstracts overwhelmingly state contributions
    while excerpts often name limitations and future work.
    """
    base = (
        f"({n}) {p['title']} ({p['year']})\n"
        f"URL: {p.get('url') or 'N/A'}\n"
        f"Authors: {p['authors']}\n"
        f"{p['abstract'] or 'No abstract available.'}"
    )
    section = p.get("_conclusion_section")
    if section:
        # Trim to keep per-paper prompt size predictable. Most OC-relevant
        # signal (limitations bullets, future-work calls) appears early.
        excerpt = section if len(section) <= 1500 else section[:1500].rstrip() + "…"
        base += f"\n\nDiscussion/Conclusion excerpt:\n{excerpt}"
    return base


def _render_excerpt_block(section: str) -> str:
    """Format a paper's conclusion / discussion / limitations section as a
    labeled blockquote suitable for the Paper Appendix.

    Strips the section's own leading heading (e.g. ``## 5 Limitations``)
    and surfaces it as the human-readable label so the heading does not
    pollute the outer document's TOC. The rest of the section body is
    rewritten with ``> `` blockquote prefixes so eval_report.py's
    ``parse_appendix`` can pick it up alongside the abstract.
    """
    lines = section.splitlines()
    # First non-empty line is typically the section header (e.g. "## 5 Limitations").
    label = "discussion / conclusion / limitations section"
    body_start = 0
    for i, ln in enumerate(lines):
        if ln.strip():
            m = re.match(r"^#{1,2}\s+(.+?)\s*$", ln)
            if m:
                # Drop any leading section number ("5 ", "5.1 ", "VI ").
                raw = re.sub(r"^[\dIVXivx]+(?:\.\d+)*\s+", "", m.group(1)).strip()
                if raw:
                    label = "§ " + raw
                body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    if not body:
        return ""
    quoted = "\n".join(f"> {ln}" if ln else ">" for ln in body.splitlines())
    return f"**Excerpt from {label}:**\n\n{quoted}\n\n"


# ---------------------------------------------------------------------------
# Classification accessor
# ---------------------------------------------------------------------------


def _label_of(p: dict[str, Any]) -> str:
    """Return the classification label for a paper, defaulting to CORE.

    The default matters when classification fell back (every paper marked
    CORE in ``_classify_papers``) and for any legacy code path that runs
    before classification has annotated the dicts.
    """
    return (p.get("_classification") or {}).get("label") or "CORE"


async def _prefetch_paper_sections(
    client: httpx.AsyncClient,
    papers: list[dict[str, Any]],
    logger: Logger,
) -> None:
    """Best-effort: fetch each paper's full-text markdown via paper_md and
    stash the conclusion-like section on the paper dict as
    ``_conclusion_section`` (None when unavailable). Failures are silent —
    a paper without a section just provides no OC anchor downstream."""
    # Skip REJECT papers — they are dropped from the final report and would
    # only burn arxiv2md quota for no downstream consumer.
    targets = [p for p in papers if p.get("arxiv_id") and _label_of(p) != "REJECT"]
    if not targets:
        logger.event(
            "paper_sections_fetched",
            attempted=0,
            with_section=0,
            without_section=0,
            without_arxiv_id=len(papers),
        )
        return
    bodies = await asyncio.gather(
        *(paper_md.fetch_paper_md(client, p["arxiv_id"]) for p in targets),
        return_exceptions=True,
    )
    with_section = 0
    errors: list[str] = []
    for p, body in zip(targets, bodies):
        if isinstance(body, Exception):
            p["_conclusion_section"] = None
            errors.append(f"{p.get('arxiv_id')}: {type(body).__name__}: {body}")
            continue
        if body is None:
            p["_conclusion_section"] = None
            continue
        try:
            section = paper_md.extract_section(body)
        except Exception as e:
            p["_conclusion_section"] = None
            errors.append(
                f"{p.get('arxiv_id')}: extract_section: {type(e).__name__}: {e}"
            )
            continue
        p["_conclusion_section"] = section
        if section:
            with_section += 1
    logger.event(
        "paper_sections_fetched",
        attempted=len(targets),
        with_section=with_section,
        without_section=len(targets) - with_section,
        without_arxiv_id=len(papers) - len(targets),
        errors=errors,
    )
