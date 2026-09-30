"""Deterministic verification of edge-audit verdicts against ``papers.json``.

The audit LLM only proposes a verdict with a quote from each paper. This
module decides what the renderer may draw: a directed lineage edge needs a
SUPPORTED label, both quotes found in the paper's own text, and a source
that is not newer than its target. Everything else is downgraded, and every
downgrade is reported. Pure functions, no I/O.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Any

SUPPORTED_VERDICTS = frozenset({"SUPPORTED_BY_ABSTRACT", "SUPPORTED_BY_SECTION"})
VALID_VERDICTS = SUPPORTED_VERDICTS | {"INFERRED", "REJECT"}

# A quote shorter than this cannot establish a mechanism or a limitation
# (" ", "the" and "to" are all substrings of any abstract).
MIN_QUOTE_CHARS = 20

# The text the audit prompt shows for each paper. A quote must lie inside one
# of these fields; it may not run from the end of one into the next.
EVIDENCE_FIELDS = ("title", "abstract", "_conclusion_section")

_TYPOGRAPHY = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "‐": "-",
        "‑": "-",
        "–": "-",
        "—": "-",
    }
)


def normalize_evidence(text: str) -> str:
    """Fold the differences a verbatim quote picks up in transit.

    Line breaks and runs of spaces collapse to one space, compatibility
    forms are unified (NFKC) and typographic quotes and dashes become their
    ASCII forms. Case and wording are left alone.
    """
    text = unicodedata.normalize("NFKC", text).translate(_TYPOGRAPHY)
    return re.sub(r"\s+", " ", text).strip()


def _paper_number(value: Any) -> int | None:
    """Return a paper number, or None when ``value`` does not name one.

    ``3`` and ``"3"`` are paper 3. ``3.7`` is not paper 3, and neither is
    ``True``.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _year(value: Any) -> int | None:
    """Return a publication year, or None when it is missing (``"n.d."``)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}", value.strip()):
        return int(value.strip())
    return None


def _quote_problem(quote: Any, paper: dict[str, Any]) -> str | None:
    """Return why ``quote`` is not evidence from ``paper``, or None if it is."""
    if not isinstance(quote, str):
        return "missing"
    normalized = normalize_evidence(quote)
    if not normalized or normalized.upper() == "NONE":
        return "missing"
    if len(normalized) < MIN_QUOTE_CHARS:
        return f"shorter than {MIN_QUOTE_CHARS} characters"
    if not any(
        normalized in normalize_evidence(str(paper.get(field) or ""))
        for field in EVIDENCE_FIELDS
    ):
        return "not found in the paper's title, abstract or excerpt"
    return None


def cycle_edges(edges: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    """Return the edges that lie on a directed cycle.

    Each edge can be verified on its own and the set can still be circular
    (papers of the same year, or with a missing year). A cycle is not a
    lineage, so none of its edges should be drawn.
    """
    edge_set = set(edges)
    successors: dict[int, set[int]] = {}
    for source, target in edge_set:
        successors.setdefault(source, set()).add(target)

    def _reaches(start: int, goal: int) -> bool:
        seen: set[int] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node == goal:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(successors.get(node, ()))
        return False

    return {(s, t) for s, t in edge_set if _reaches(t, s)}


def verify_verdicts(
    records: list[Any], papers: list[dict[str, Any]]
) -> tuple[dict[tuple[int, int], str], list[dict[str, Any]], list[dict[str, Any]]]:
    """Check audit verdict records against the papers they cite.

    Returns ``(edge_verdicts, downgrades, notes)``:

    - ``edge_verdicts`` maps ``(source_n, target_n)`` to the label the
      renderer should apply. Only a SUPPORTED label draws an edge.
    - ``downgrades`` lists every record that was dropped or turned into
      REJECT, with the reason. ``source_n`` / ``target_n`` are None when the
      record does not name an edge at all.
    - ``notes`` lists things that were accepted but could not be checked,
      such as chronology when a year is missing.

    A malformed record never raises: it is reported and the other records
    are still applied. When several records name the same edge, the edge is
    drawn only if every one of them is a verified SUPPORTED verdict.
    """
    edge_verdicts: dict[tuple[int, int], str] = {}
    downgrades: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []

    def _downgrade(index: int, source: int | None, target: int | None, why: str):
        downgrades.append(
            {"record": index, "source_n": source, "target_n": target, "reason": why}
        )

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            _downgrade(index, None, None, "record is not a JSON object")
            continue
        source_n = _paper_number(record.get("source_n"))
        target_n = _paper_number(record.get("target_n"))
        if source_n is None or target_n is None:
            _downgrade(index, None, None, "source_n / target_n is not a paper number")
            continue

        raw_label = record.get("verdict")
        verdict = raw_label.strip() if isinstance(raw_label, str) else ""
        reason: str | None = None
        if verdict not in VALID_VERDICTS:
            reason = f"unknown verdict label {raw_label!r}"
        elif not (1 <= source_n <= len(papers) and 1 <= target_n <= len(papers)):
            reason = "paper number outside papers.json"
        elif source_n == target_n:
            reason = "self-edge"
        elif verdict in SUPPORTED_VERDICTS:
            source, target = papers[source_n - 1], papers[target_n - 1]
            source_year, target_year = (
                _year(source.get("year")),
                _year(target.get("year")),
            )
            if source_year is None or target_year is None:
                notes.append(
                    {
                        "record": index,
                        "source_n": source_n,
                        "target_n": target_n,
                        "reason": "chronology not checked: a year is missing",
                    }
                )
            elif source_year > target_year:
                reason = "backwards chronology"
            if reason is None:
                problem = _quote_problem(record.get("source_quote"), source)
                if problem:
                    reason = f"source_quote {problem}"
            if reason is None:
                problem = _quote_problem(record.get("target_quote"), target)
                if problem:
                    reason = f"target_quote {problem}"
        if reason is not None:
            verdict = "REJECT"
            _downgrade(index, source_n, target_n, reason)

        key = (source_n, target_n)
        previous = edge_verdicts.get(key)
        if previous is None:
            edge_verdicts[key] = verdict
        elif (previous in SUPPORTED_VERDICTS) != (verdict in SUPPORTED_VERDICTS):
            # Conflicting records for one edge: keep the one that does not
            # draw it, whichever order they came in.
            if previous in SUPPORTED_VERDICTS:
                edge_verdicts[key] = verdict
            _downgrade(
                index,
                source_n,
                target_n,
                "duplicate verdict records disagree; the edge is not drawn",
            )

    return edge_verdicts, downgrades, notes
