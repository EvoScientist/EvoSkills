"""Markdown → Mermaid rendering: outline + detail trees + label hygiene.

Pure functions of LLM-produced Markdown and paper-metadata dicts. No I/O.
Punctuation handling is configurable via ``MERMAID_PUNCT`` (ESCAPE
default; FULLWIDTH for legacy renderers).
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .logger import Logger
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from logger import Logger  # type: ignore


# Theme palettes. Selected per-invocation via the `theme` kwarg on
# outline/detail renderers, or globally via the MERMAID_THEME env var.
# Explicit kwarg > env > "light" default. The palettes themselves were
# tuned against the warm-ivory (#faf8f3) and warm-charcoal (#23211d) UI
# backgrounds — see diagram_colors/{light,dark}.md for the reference
# renderings the skill output matches.
@dataclass(frozen=True)
class Theme:
    name: str
    init_block: str  # `%%{init: ...}%%` directive injected at top
    root_classdef: str  # classDef body (no leading "classDef X")
    challenge_classdef: str
    solution_classdef: str
    paper_classdef: str
    dotted_link_style: str  # linkStyle body for dotted edges
    open_challenge_color: str  # inline `<font color="...">` for OC nodes


_LIGHT_INIT = (
    "%%{init: {'theme':'base','themeVariables':{"
    "'background':'#faf8f3',"
    "'primaryColor':'#ffffff',"
    "'primaryBorderColor':'#555555',"
    "'primaryTextColor':'#1a1a1a',"
    "'lineColor':'#8a7960',"
    "'secondaryColor':'#f5efde',"
    "'tertiaryColor':'#ece4cf'"
    "}}}%%"
)

_DARK_INIT = (
    "%%{init: {'theme':'base','themeVariables':{"
    "'background':'#23211d',"
    "'primaryColor':'#2e2a25',"
    "'primaryBorderColor':'#a89880',"
    "'primaryTextColor':'#e8e3d8',"
    "'lineColor':'#a89880',"
    "'secondaryColor':'#3a342c',"
    "'tertiaryColor':'#4a3f24'"
    "}}}%%"
)

LIGHT_THEME = Theme(
    name="light",
    init_block=_LIGHT_INIT,
    root_classdef="fill:#fff2cc,stroke:#d6b656,stroke-width:4px,color:#3d2f00",
    challenge_classdef="fill:#dae8fc,stroke:#6c8ebf,color:#1a2940",
    solution_classdef="fill:#d5e8d4,stroke:#82b366,stroke-width:2px,color:#1d3a1f",
    paper_classdef="fill:#ffffff,stroke:#555555,stroke-width:1px,color:#1a1a1a",
    dotted_link_style="stroke:#8a7960,stroke-width:1.8px,stroke-dasharray:8 4",
    open_challenge_color="#b00020",
)

DARK_THEME = Theme(
    name="dark",
    init_block=_DARK_INIT,
    root_classdef="fill:#4a3f24,stroke:#d6b656,stroke-width:4px,color:#f4e6b8",
    challenge_classdef="fill:#2d3a52,stroke:#6c8ebf,color:#d8e4f5",
    solution_classdef="fill:#2d4530,stroke:#82b366,stroke-width:2px,color:#d5e8d4",
    paper_classdef="fill:#2e2a25,stroke:#a89880,stroke-width:1px,color:#e8e3d8",
    dotted_link_style="stroke:#c4b59a,stroke-width:1.8px,stroke-dasharray:8 4",
    open_challenge_color="#ff8a8a",
)

_THEMES: dict[str, Theme] = {"light": LIGHT_THEME, "dark": DARK_THEME}


def _resolve_theme(name: str | None) -> Theme:
    """Resolve a Theme by name, env, then default.

    Precedence: explicit ``name`` arg > ``MERMAID_THEME`` env > ``"light"``.
    A CLI flag passing ``--theme=dark`` therefore overrides any
    ``MERMAID_THEME`` set in the shell for that single invocation.
    """
    raw = name if name is not None else os.environ.get("MERMAID_THEME", "light")
    key = raw.lower()
    if key not in _THEMES:
        raise ValueError(
            f"unknown MERMAID theme: {raw!r}; expected one of {sorted(_THEMES)}"
        )
    return _THEMES[key]


def parse_outline_markdown(
    markdown_text: str,
    allowed: set[int] | None = None,
    logger: Logger | None = None,
) -> tuple[
    str | None,
    dict[int, str],
    dict[int, list[tuple[int, int, str, list[int]]]],
]:
    """Return (root_title, challenges_by_num, challenge_to_solutions).

    Each solution is ``(s_major, s_minor, name, paper_nums)``.

    If ``allowed`` is provided, any paper number `(N)` the LLM emitted that is
    NOT in this set is treated as a hallucination and dropped — keeps the
    final graph anchored on real input papers.
    """
    root_title: str | None = None
    challenges: dict[int, str] = {}
    challenge_solutions: dict[int, list[tuple[int, int, str, list[int]]]] = {}
    current_c: int | None = None
    current_s: tuple[int, int] | None = None
    dropped: list[int] = []

    for raw in markdown_text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith("# ") and not line.startswith("##"):
            root_title = line[2:].strip()
            continue

        m = re.match(r"^##\s+Challenge\s+(\d+):\s*(.+)$", line)
        if m:
            current_c = int(m.group(1))
            challenges[current_c] = m.group(2).strip()
            challenge_solutions.setdefault(current_c, [])
            current_s = None
            continue

        m = re.match(r"^###\s+Solution\s+(\d+)\.(\d+):\s*(.+)$", line)
        if m and current_c is not None:
            s_major, s_minor = int(m.group(1)), int(m.group(2))
            sol_name = m.group(3).strip()
            current_s = (s_major, s_minor)
            challenge_solutions[current_c].append((s_major, s_minor, sol_name, []))
            continue

        m = re.match(r"^-\s+(?:Paper:\s*)?\((\d+)\)", line)
        if m and current_c is not None and current_s is not None:
            paper_num = int(m.group(1))
            if allowed is not None and paper_num not in allowed:
                dropped.append(paper_num)
                continue
            sols = challenge_solutions[current_c]
            if sols:
                s_major, s_minor, sol_name, paper_nums = sols[-1]
                if (s_major, s_minor) == current_s:
                    paper_nums.append(paper_num)
                    sols[-1] = (s_major, s_minor, sol_name, paper_nums)
            continue

    if logger is not None and dropped:
        logger.event("outline_dropped_paper_nums", dropped=dropped)
    return root_title, challenges, challenge_solutions


def outline_to_mermaid(
    markdown_text: str,
    allowed: set[int] | None = None,
    theme: str | None = None,
) -> str:
    """Convert the outline Markdown to a Mermaid ``graph LR`` definition."""
    th = _resolve_theme(theme)
    root_title, challenges, challenge_solutions = parse_outline_markdown(
        markdown_text,
        allowed=allowed,
    )

    parts: list[str] = [th.init_block, "graph LR"]
    if root_title:
        parts.append(f'    ROOT[("{root_title}")]')

    for c_num, c_name in sorted(challenges.items()):
        parts.append(f"    C{c_num}{{{{<b>{c_name}</b>}}}}")
        if root_title:
            parts.append(f"    ROOT --> C{c_num}")

    paper_idx_per_challenge: dict[int, int] = {}
    for c_num in sorted(challenges):
        paper_idx_per_challenge[c_num] = 1
        for s_major, s_minor, sol_name, paper_nums in challenge_solutions.get(
            c_num, []
        ):
            parts.append(f"    C{c_num} --> S{s_major}_{s_minor}[{sol_name}]")
            for paper_num in paper_nums:
                idx = paper_idx_per_challenge[c_num]
                parts.append(
                    f'    S{s_major}_{s_minor} --- P{c_num}_{idx}["({paper_num})"]'
                )
                paper_idx_per_challenge[c_num] += 1

    parts.extend(
        [
            f"    classDef rootNode {th.root_classdef}",
            f"    classDef challengeNode {th.challenge_classdef}",
            f"    classDef solutionNode {th.solution_classdef}",
            f"    classDef paperNode {th.paper_classdef}",
        ]
    )
    if root_title:
        parts.append("    class ROOT rootNode")
    if challenges:
        parts.append(
            "    class "
            + ",".join(f"C{n}" for n in sorted(challenges))
            + " challengeNode"
        )
    solution_ids = [
        f"S{s_major}_{s_minor}"
        for c_num in challenges
        for s_major, s_minor, _, _ in challenge_solutions.get(c_num, [])
    ]
    if solution_ids:
        parts.append("    class " + ",".join(solution_ids) + " solutionNode")
    paper_ids = [
        f"P{c_num}_{i}"
        for c_num, count in paper_idx_per_challenge.items()
        for i in range(1, count)
    ]
    if paper_ids:
        parts.append("    class " + ",".join(paper_ids) + " paperNode")

    return "\n".join(parts)


# Mermaid-bound text gets two passes:
#   1. Normalize any full-width / look-alike punctuation back to ASCII so
#      whatever the LLM emitted lands in a known shape.
#   2. Replace the ASCII Mermaid-significant characters using one of two
#      strategies, selectable via the MERMAID_PUNCT env var:
#        - "ESCAPE"    (default): decimal entity codes like `#40;` —
#                      the documented Mermaid escape syntax, see
#                      https://mermaid.ai/open-source/syntax/flowchart.html#entity-codes-to-escape-characters
#                      Decoded by every modern Mermaid renderer; ASCII
#                      `(`, `)`, `|`, `"` appear in the rendered diagram.
#        - "FULLWIDTH"          : substitute full-width Unicode look-alikes
#                      (U+FF08 etc.). Workaround for older renderers that
#                      leave entity codes undecoded; the visible characters
#                      are full-width glyphs, not ASCII.
_FULLWIDTH_TO_ASCII = str.maketrans(
    {
        "（": "(",
        "）": ")",  # U+FF08 / U+FF09 full-width parens
        "｜": "|",
        "│": "|",  # U+FF5C full-width pipe + U+2502 box-drawing pipe
        "＂": '"',  # U+FF02 full-width double-quote
        "［": "[",
        "］": "]",  # U+FF3B / U+FF3D full-width square brackets
        "；": ";",  # U+FF1B full-width semicolon
        "：": ":",  # U+FF1A full-width colon
        "｛": "{",
        "｝": "}",  # U+FF5B / U+FF5D full-width curly braces
        "＃": "#",  # U+FF03 full-width number sign
    }
)
# Mermaid-significant ASCII characters that can confuse the parser inside
# node labels or edge labels. Escaping is single-pass and the output
# entity codes themselves contain `#` and `;` — that's fine because we
# never re-apply _mermaid_safe to its own output; Mermaid decodes the
# entities back to ASCII at render time, so any `#` / `;` the LLM emitted
# round-trips correctly (e.g. `#tag;` → `#35;tag#59;` → rendered `#tag;`).
# Notably NOT escaped: `<` and `>`, because our own labels use `<b>`,
# `<br/>`, `<font color=red>` HTML tags inside node bodies.
_MERMAID_ESCAPE_TABLE = str.maketrans(
    {
        "(": "#40;",
        ")": "#41;",
        "|": "#124;",
        '"': "#34;",
        "[": "#91;",
        "]": "#93;",
        ";": "#59;",
        ":": "#58;",
        "{": "#123;",
        "}": "#125;",
        "#": "#35;",
    }
)
_MERMAID_FULLWIDTH_TABLE = str.maketrans(
    {
        "(": "\uff08",  # （
        ")": "\uff09",  # ）
        "|": "\u2502",  # │ (box-drawing pipe; chosen historically)
        '"': "\uff02",  # ＂
        "[": "\uff3b",  # ［
        "]": "\uff3d",  # ］
        ";": "\uff1b",  # ；
        ":": "\uff1a",  # ：
        "{": "\uff5b",  # ｛
        "}": "\uff5d",  # ｝
        "#": "\uff03",  # ＃
    }
)


def _select_mermaid_punct_table() -> dict[int, str]:
    raw = os.environ.get("MERMAID_PUNCT", "ESCAPE").upper()
    if raw == "FULLWIDTH":
        return _MERMAID_FULLWIDTH_TABLE
    return _MERMAID_ESCAPE_TABLE  # "ESCAPE" and any unknown value default here


_MERMAID_PUNCT_TABLE = _select_mermaid_punct_table()


def _to_ascii_punct(text: str) -> str:
    """Normalize full-width / look-alike punctuation back to ASCII."""
    return text.translate(_FULLWIDTH_TO_ASCII)


def _mermaid_safe(text: str) -> str:
    """Make ``text`` safe to embed inside a Mermaid edge label or shape body.

    Normalizes full-width punctuation back to ASCII, then applies the
    Mermaid-significant substitution selected by ``MERMAID_PUNCT`` (default
    ``ESCAPE``). In either mode the source text we hand to Mermaid never
    contains a raw `(`, `)`, `|`, or `"` that could close a label.
    """
    return _to_ascii_punct(text).translate(_MERMAID_PUNCT_TABLE)


LABEL_CAP = 80


def _capped_label(text: str, footnotes: list[str]) -> str:
    """Return a Mermaid-safe label, possibly truncated with a footnote pointer.

    When ``text`` is longer than ``LABEL_CAP``, the full (pre-substitution)
    text is appended to ``footnotes`` and the visible label is a short
    prefix followed by ``… [note N]`` pointing into the list. The caller
    renders the collected footnotes as Markdown prose below the Mermaid
    block. Length is measured on the ASCII-normalized text so the cap
    matches user-visible character count regardless of the chosen
    Mermaid-substitution strategy.
    """
    cleaned = _to_ascii_punct(text)
    if len(cleaned) <= LABEL_CAP:
        return cleaned.translate(_MERMAID_PUNCT_TABLE)
    footnotes.append(cleaned)
    # Reserve ~12 chars for the `… [note NN]` suffix so the visible label
    # stays under LABEL_CAP after the marker is appended.
    short = cleaned[: LABEL_CAP - 12].rstrip() + f"… [note {len(footnotes)}]"
    return short.translate(_MERMAID_PUNCT_TABLE)


def _parse_detail_markdown(
    markdown_text: str,
    allowed: set[int] | None = None,
    logger: Logger | None = None,
    challenge_idx: int | None = None,
    solution_key: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Parse a detail-tree Markdown block into structured data.

    Single source of truth for the detail parser — both
    ``detail_to_mermaid`` (rendering) and the ``parse_detail`` CLI
    subcommand (post-processing / edge audit) call this helper.

    Strips scratchpad / reasoning blocks, then walks ``### Paper (N)``,
    ``### Evolution Point N``, and ``### Open Challenge N`` headers
    plus their bullet bodies. Any paper number not in ``allowed`` is
    dropped as a hallucination — those drops are surfaced via a
    ``detail_dropped_hallucinations`` log event when a ``logger`` is
    supplied.

    Returns a dict with keys:
        papers              dict[int, {gap, evolution_from}]
        evolution_points    list[{num, description, related}]
        open_challenges     list[{num, description, related}]
        edges               list[{source_n, target_n, gap}]   # derived
        scratchpad          str          # captured reasoning block text
        scratchpad_truncated bool        # True when </scratchpad> missing
        dropped_paper_headers list[int]
        dropped_edges       list[(source_n, target_n)]
        dropped_related     list[int]
    """
    scratchpad_match = re.search(
        r"<scratchpad>(.*?)</scratchpad>",
        markdown_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if scratchpad_match is None:
        # Possibly truncated mid-scratchpad — capture everything from the
        # opening tag to end-of-text so we don't lose the partial reasoning.
        partial = re.search(
            r"<scratchpad>(.*)\Z",
            markdown_text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        scratchpad_text = partial.group(1).strip() if partial else ""
        scratchpad_truncated = bool(partial)
    else:
        scratchpad_text = scratchpad_match.group(1).strip()
        scratchpad_truncated = False
    if scratchpad_text and logger is not None:
        sk_str = (
            f"{solution_key[0]}.{solution_key[1]}" if solution_key is not None else None
        )
        logger.event(
            "detail_scratchpad",
            challenge_idx=challenge_idx,
            solution_key=sk_str,
            scratchpad=scratchpad_text,
            truncated=scratchpad_truncated,
        )

    # Strip scratchpad / reasoning blocks before the line-by-line parse so
    # internal "(M) -> (N)" mentions don't show up as false edges.
    markdown_text = re.sub(
        r"<scratchpad>.*?</scratchpad>",
        "",
        markdown_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    markdown_text = re.sub(
        r"<(thinking|analysis|reasoning)>.*?</\1>",
        "",
        markdown_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Truncation safety net: unterminated <scratchpad> means max_tokens hit
    # mid-block. Strip everything from the opening tag to EOF; there's
    # nothing parseable after it anyway. Same for reasoning-tag variants.
    markdown_text = re.sub(
        r"<scratchpad>.*\Z",
        "",
        markdown_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    markdown_text = re.sub(
        r"<(thinking|analysis|reasoning)>.*\Z",
        "",
        markdown_text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    def _is_allowed(n: int) -> bool:
        return allowed is None or n in allowed

    papers: dict[int, dict[str, Any]] = {}
    evolution_points: list[dict[str, Any]] = []
    open_challenges: list[dict[str, Any]] = []
    current_paper: int | None = None
    current_ep: dict[str, Any] | None = None
    current_oc: dict[str, Any] | None = None
    dropped_paper_headers: list[int] = []
    dropped_edges: list[tuple[int, int]] = []
    dropped_related: list[int] = []

    paper_hdr_re = re.compile(r"^###\s+Paper\s+\((\d+)\)\s*[:.]?\s*(.*)$")

    for raw in markdown_text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue

        m = paper_hdr_re.match(line)
        if m:
            n = int(m.group(1))
            if not _is_allowed(n):
                dropped_paper_headers.append(n)
                current_paper = None
                current_ep = None
                current_oc = None
                continue
            current_paper = n
            papers[current_paper] = {"gap": None, "evolution_from": None}
            current_ep = None
            current_oc = None
            continue

        if line.startswith("- Gap addressed:"):
            if current_paper is not None and current_paper in papers:
                papers[current_paper]["gap"] = line[len("- Gap addressed:") :].strip()
            continue

        if line.startswith("- Evolution from:"):
            m = re.search(r"\((\d+)\)", line)
            if m and current_paper is not None and current_paper in papers:
                ef = int(m.group(1))
                if _is_allowed(ef):
                    papers[current_paper]["evolution_from"] = ef
                else:
                    dropped_edges.append((ef, current_paper))
            continue

        m = re.match(r"^###\s+Evolution\s+Point\s+(\d+)$", line)
        if m:
            current_ep = {"num": int(m.group(1)), "description": None, "related": []}
            evolution_points.append(current_ep)
            current_oc = None
            current_paper = None
            continue

        m = re.match(r"^###\s+Open\s+Challenge\s+(\d+)$", line)
        if m:
            current_oc = {"num": int(m.group(1)), "description": None, "related": []}
            open_challenges.append(current_oc)
            current_ep = None
            current_paper = None
            continue

        if line.startswith("- Description:"):
            desc = line[len("- Description:") :].strip()
            if current_ep is not None:
                current_ep["description"] = desc
            elif current_oc is not None:
                current_oc["description"] = desc
            continue

        if line.startswith("- Related papers:"):
            nums = [int(n) for n in re.findall(r"\((\d+)\)", line)]
            kept = [n for n in nums if _is_allowed(n)]
            for n in nums:
                if not _is_allowed(n):
                    dropped_related.append(n)
            if current_ep is not None:
                current_ep["related"] = kept
            elif current_oc is not None:
                current_oc["related"] = kept
            continue

    if logger is not None and (
        dropped_paper_headers or dropped_edges or dropped_related
    ):
        sk_str = (
            f"{solution_key[0]}.{solution_key[1]}" if solution_key is not None else None
        )
        logger.event(
            "detail_dropped_hallucinations",
            challenge_idx=challenge_idx,
            solution_key=sk_str,
            dropped_paper_headers=dropped_paper_headers,
            dropped_edges=dropped_edges,
            dropped_related=dropped_related,
        )

    edges = [
        {
            "source_n": info["evolution_from"],
            "target_n": pn,
            "gap": info.get("gap") or "",
        }
        for pn, info in papers.items()
        if info.get("evolution_from") is not None
    ]

    return {
        "papers": papers,
        "evolution_points": evolution_points,
        "open_challenges": open_challenges,
        "edges": edges,
        "scratchpad": scratchpad_text,
        "scratchpad_truncated": scratchpad_truncated,
        "dropped_paper_headers": dropped_paper_headers,
        "dropped_edges": dropped_edges,
        "dropped_related": dropped_related,
    }


def detail_to_mermaid(
    markdown_text: str,
    challenge_idx: int,
    solution_key: tuple[int, int],
    allowed: set[int] | None = None,
    paper_urls: dict[int, str] | None = None,
    paper_labels: dict[int, str] | None = None,
    logger: Logger | None = None,
    edge_verdicts: dict[tuple[int, int], str] | None = None,
    theme: str | None = None,
) -> tuple[str, str]:
    """Convert a detail-tree Markdown block into a Mermaid graph fragment.

    Returns ``(mermaid_body, footnotes_md)``. The Mermaid body is the
    `graph LR` block content (without the surrounding code fence). The
    footnotes block is non-empty when any gap / EP / OC description
    exceeded ``LABEL_CAP`` characters and was truncated in the diagram
    — full text lives in the footnotes for human reference.

    ``allowed``: paper numbers the LLM was permitted to reference. Any
    ``### Paper (N)`` header with N not in this set is dropped (treated as
    hallucination). Same for ``- Evolution from: (N)`` and related-papers
    lists in EP/OC nodes.

    ``paper_urls``: maps paper number → canonical URL. Appended to each
    paper node's Mermaid label so the reader can verify the citation.

    ``paper_labels``: maps paper number → display label (e.g.
    ``"2024 — BEST-RQ: Bi-Level Random Quantization..."``). Built by the
    caller from the appendix, NOT from the LLM's output — this removes
    label hallucination as a possible failure mode. The LLM only emits
    structural connectivity; the renderer fills the names from the
    canonical paper metadata.
    """
    th = _resolve_theme(theme)
    s_major, s_minor = solution_key
    prefix = f"D{challenge_idx}_{s_major}_{s_minor}"

    parsed = _parse_detail_markdown(
        markdown_text,
        allowed=allowed,
        logger=logger,
        challenge_idx=challenge_idx,
        solution_key=solution_key,
    )
    papers = parsed["papers"]
    evolution_points = parsed["evolution_points"]
    open_challenges = parsed["open_challenges"]

    def _label_for(pn: int) -> str:
        # Label comes from the appendix (paper_labels), NOT the LLM. The
        # LLM only emitted `### Paper (N)` — the title, year, and URL are
        # filled in here from the canonical paper metadata so they're
        # always consistent across trees and impossible to hallucinate.
        # Title may contain ASCII parens/pipes/quotes (e.g. *"Attention is
        # All You Need"* style titles); run through _mermaid_safe so they
        # don't accidentally close the Mermaid node-label string.
        url = (paper_urls or {}).get(pn, "")
        title_year = (paper_labels or {}).get(pn) or f"paper ({pn})"
        head = f"({pn}) {_mermaid_safe(title_year)}"
        if url:
            return f"{head}<br/>{url}"
        return head

    # Apply audit verdicts: REJECT edges are dropped (target reverts to
    # initial work); INFERRED edges keep their evolution_from but render
    # dotted; SUPPORTED_* and unaudited edges render solid.
    if edge_verdicts:
        for pn, info in papers.items():
            ef = info.get("evolution_from")
            if ef and edge_verdicts.get((ef, pn)) == "REJECT":
                info["evolution_from"] = None

    # Collect full text for any label that exceeds LABEL_CAP; each one is
    # replaced by a short prefix + `[note N]` marker in the diagram, with
    # the full text rendered below the Mermaid block as a numbered list.
    footnotes: list[str] = []

    out: list[str] = [th.init_block, "graph LR"]
    edge_index = 0
    dotted_indices: list[int] = []

    def _emit_edge(line: str, dotted: bool) -> None:
        nonlocal edge_index
        out.append(line)
        if dotted:
            dotted_indices.append(edge_index)
        edge_index += 1

    for pn in sorted(papers):
        out.append(f'    {prefix}_P{pn}("{_label_for(pn)}")')
    for pn in sorted(papers):
        info = papers[pn]
        ef = info.get("evolution_from")
        if ef and ef in papers:
            gap = _capped_label(info.get("gap") or "Evolution", footnotes)
            verdict = (edge_verdicts or {}).get((ef, pn))
            if verdict == "INFERRED":
                # Dotted edge + visible marker so the reader sees that the
                # source/target textual evidence didn't fully attest the gap.
                _emit_edge(
                    f"    {prefix}_P{ef} -.->|Gap #40;inferred#41;: {gap}| {prefix}_P{pn}",
                    dotted=True,
                )
            else:
                _emit_edge(
                    f"    {prefix}_P{ef} -->|Gap: {gap}| {prefix}_P{pn}",
                    dotted=False,
                )

    orphaned_eps: list[int] = []
    orphaned_ocs: list[int] = []

    for ep in evolution_points:
        # An EP/OC with no in-tree related papers becomes a free-floating
        # node in the rendered graph — defined but unreachable, visually
        # confusing. Skip entirely; record for the audit log.
        connected = [pn for pn in ep["related"] if pn in papers]
        if not connected:
            orphaned_eps.append(ep["num"])
            continue
        desc = _capped_label(
            ep["description"] or f"Evolution Point {ep['num']}",
            footnotes,
        )
        node_id = f"{prefix}_EP{ep['num']}"
        out.append(f"    {node_id}[[<b>Evolution Point:</b><br/>{desc}]]")
        for pn in connected:
            _emit_edge(f"    {prefix}_P{pn} -.-> {node_id}", dotted=True)

    for oc in open_challenges:
        connected = [pn for pn in oc["related"] if pn in papers]
        if not connected:
            orphaned_ocs.append(oc["num"])
            continue
        desc = _capped_label(
            oc["description"] or f"Open Challenge {oc['num']}",
            footnotes,
        )
        node_id = f"{prefix}_OC{oc['num']}"
        out.append(
            f'    {node_id}[[<b><font color="{th.open_challenge_color}">Open Challenge:</font></b><br/>{desc}]]'
        )
        for pn in connected:
            _emit_edge(f"    {prefix}_P{pn} -.-> {node_id}", dotted=True)

    if logger is not None and (orphaned_eps or orphaned_ocs):
        logger.event(
            "detail_dropped_orphans",
            challenge_idx=challenge_idx,
            solution_key=f"{s_major}.{s_minor}",
            orphan_eps=orphaned_eps,
            orphan_ocs=orphaned_ocs,
        )

    # If parsing yielded no paper nodes, the rendered subgraph will be
    # essentially empty (just the solution box from the outline). This is
    # almost always a truncation / cap-hit failure — surface it loudly
    # so it shows up in the per-run audit instead of silently producing
    # a blank Mermaid block.
    if not papers and logger is not None:
        logger.event(
            "detail_empty_tree",
            challenge_idx=challenge_idx,
            solution_key=f"{s_major}.{s_minor}",
            reason="no paper headers after parse (likely truncated mid-scratchpad)",
            input_chars=len(markdown_text),
        )

    # Connect solution node to root papers (those with no evolution_from).
    sol_id = f"S{s_major}_{s_minor}"
    roots = [pn for pn, info in papers.items() if not info.get("evolution_from")]
    if roots:
        for pn in sorted(roots):
            _emit_edge(f"    {sol_id} --- {prefix}_P{pn}", dotted=False)
    elif papers:
        first = sorted(papers)[0]
        _emit_edge(f"    {sol_id} --- {prefix}_P{first}", dotted=False)

    if dotted_indices:
        idx_list = ",".join(str(i) for i in dotted_indices)
        out.append(f"    linkStyle {idx_list} {th.dotted_link_style}")

    if footnotes:
        # Collapsible block keeps the visual flow clean while still
        # surfacing the full text of any truncated label. The numbered
        # items correspond to the `[note N]` markers inside the diagram.
        items = "\n".join(f"{i}. {t}" for i, t in enumerate(footnotes, start=1))
        footnotes_md = (
            "<details>\n<summary>Full text of truncated diagram labels</summary>\n\n"
            f"{items}\n\n</details>\n\n"
        )
    else:
        footnotes_md = ""

    return "\n".join(out), footnotes_md
