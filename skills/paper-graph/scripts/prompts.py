"""Prompt template loader.

The prompt text itself lives in ``../references/<name>.md`` so it's
discoverable by the agent driving the skill (it can read those files
directly without importing Python). This module re-exposes each prompt
as a module-level constant for the existing pipeline code path, which
expects ``P.PARSE_QUERY_PROMPT`` etc.

When the skill moves fully to agent-driven orchestration (Phase 4),
this module goes away — the agent reads the .md files itself.
"""

from __future__ import annotations

from pathlib import Path

_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"


def _load(name: str) -> str:
    return (_REFERENCES_DIR / f"{name}.md").read_text(encoding="utf-8")


PARSE_QUERY_PROMPT = _load("parse_query")
SEED_PAPER_BLOCK = _load("seed_paper_block")
OUTLINE_PROMPT = _load("outline")
DETAIL_PROMPT = _load("detail")
CLASSIFY_PROMPT = _load("classify")
AUDIT_EDGE_PROMPT = _load("audit_edge")
