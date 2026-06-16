"""Configuration: data-layer env vars, S2 endpoints, and one-time regexes.

Pure data + a single ``_require_env`` helper. No external state beyond
``os.environ`` and the user's ``.env`` (loaded by ``_require_env``). The
agent-driven architecture makes LLM provider configuration the host
agent's concern, not the skill's — this module only covers the
deterministic data fetchers.
"""

from __future__ import annotations

import os
import re
import sys

from dotenv import load_dotenv


S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_LOOKUP_URL = "https://api.semanticscholar.org/graph/v1/paper/{external_id}"
S2_REFS_URL = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references"
S2_CITES_URL = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
S2_FIELDS = "title,abstract,year,authors,citationCount,externalIds,venue"
# When fetching references/citations, the paper is nested under
# `citedPaper`/`citingPaper`. The field path uses dot notation.
S2_REL_FIELDS = ",".join(f"citedPaper.{f}" for f in S2_FIELDS.split(","))
S2_CITING_FIELDS = ",".join(f"citingPaper.{f}" for f in S2_FIELDS.split(","))

# S2 sometimes returns whole conference-proceedings volumes (e.g.
# "Progress in Pattern Recognition ... CIARP 2009 ... Proceedings") in
# response to broad ML keywords. They have no abstract and are useless
# input for the outline LLM. The "abstract != ''" filter catches most of
# them today by side-effect; this regex makes the intent explicit.
PROCEEDINGS_TITLE_RE = re.compile(r"\bproceedings\b", re.IGNORECASE)

# Matches:
#   https://arxiv.org/abs/2202.01855
#   https://arxiv.org/pdf/2202.01855v1.pdf
#   arxiv:2202.01855
#   arXiv:2202.01855v2
# Captures the bare ID. Old-style ("cs/0506075") not covered — modern only.
ARXIV_ID_RE = re.compile(
    r"(?:arxiv(?:\.org)?[/:](?:abs/|pdf/)?|arxiv:\s*)(\d{4}\.\d{4,5})(?:v\d+)?",
    re.IGNORECASE,
)

REQUIRED_ENV_VARS = ("S2_API_KEY",)


def _require_env() -> dict[str, str]:
    """Load .env and verify all required keys are present.

    Aborts loudly if any are missing — partial pipelines produce misleading
    graphs, which is worse than no graph.
    """
    load_dotenv(".env")
    missing = [k for k in REQUIRED_ENV_VARS if not os.getenv(k)]
    if missing:
        print(
            "ERROR: paper-graph requires the following env vars (load via .env):\n  - "
            + "\n  - ".join(missing)
            + "\nAdd them to .env in the current working directory and retry.",
            file=sys.stderr,
        )
        sys.exit(2)
    return {k: os.environ[k] for k in REQUIRED_ENV_VARS}
