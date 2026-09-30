"""papers.json is the input of every deterministic step of skills/paper-graph.

A malformed file must stop a step with a message that names the problem,
and the per-solution prompt input must be what the runbook says it is.

Run from the repository root (needs pytest, httpx and python-dotenv):
    pytest tests/paper-graph -q
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / "skills" / "paper-graph" / "scripts" / "cli.py"

PAPER = {
    "title": "A Paper",
    "year": 2021,
    "authors": "A. Author",
    "venue": "V",
    "url": "https://example.org/1",
    "abstract": "An abstract that is long enough to be shown.",
    "_conclusion_section": None,
}
OUTLINE = "# T\n## Challenge 1: A\n### Solution 1.1: X\n- (1)\n- (2)\n"
DETAIL = (
    "### Paper (1)\n- Gap addressed: N/A\n- Evolution from: (none - initial work)\n"
)
CONTEXT = {
    "challenge_idx": 1,
    "challenge_name": "A",
    "solution_key": [1, 1],
    "solution_key_str": "1.1",
    "solution_name": "X",
    "paper_nums": [1],
    "allowed": [1, 2],
}


def cli(*args):
    return subprocess.run(
        [sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True
    )


def write(path, payload):
    path.write_text(
        payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8"
    )
    return path


def commands(tmp):
    """Every subcommand that reads papers.json, with the other inputs it needs."""
    papers = tmp / "papers.json"
    outline = write(tmp / "outline_raw.md", OUTLINE)
    detail = write(tmp / "detail_raw.md", DETAIL)
    context = write(tmp / "ctx.json", CONTEXT)
    verdicts = write(tmp / "verdicts.json", [])
    classes = write(tmp / "classify.json", {"classifications": []})
    parsed_query = write(tmp / "pq.json", {"goal": "g"})
    outline_render = write(
        tmp / "outline_mermaid.json", {"root_title": "T", "mermaid": "graph LR"}
    )
    (tmp / "details").mkdir()
    out = tmp / "out.json"
    return {
        "prefetch_sections": ["--in", papers, "--out", out],
        "format_papers": ["--papers", papers, "--out", tmp / "out.txt"],
        "compute_core_filter": ["--papers", papers, "--out", out],
        "merge_classifications": [
            "--classifications",
            classes,
            "--papers",
            papers,
            "--out",
            out,
        ],
        "parse_outline": ["--raw", outline, "--papers", papers, "--out", out],
        "render_outline_mermaid": ["--raw", outline, "--papers", papers, "--out", out],
        "render_detail_mermaid": [
            "--raw",
            detail,
            "--context",
            context,
            "--papers",
            papers,
            "--verdicts",
            verdicts,
            "--out",
            out,
        ],
        "assemble_report": [
            "--parsed-query",
            parsed_query,
            "--outline",
            outline_render,
            "--details-dir",
            tmp / "details",
            "--papers",
            papers,
            "--out",
            tmp / "report.md",
        ],
    }


SUBCOMMANDS = [
    "prefetch_sections",
    "format_papers",
    "compute_core_filter",
    "merge_classifications",
    "parse_outline",
    "render_outline_mermaid",
    "render_detail_mermaid",
    "assemble_report",
]


@pytest.mark.parametrize("subcommand", SUBCOMMANDS)
def test_entry_that_is_not_a_paper_object_is_named(tmp_path, subcommand):
    args = commands(tmp_path)[subcommand]
    write(tmp_path / "papers.json", [PAPER, None, PAPER, "oops"])
    proc = cli(subcommand, *args)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
    assert "2, 4" in proc.stderr


@pytest.mark.parametrize("subcommand", SUBCOMMANDS)
def test_papers_file_that_is_not_a_list_is_rejected(tmp_path, subcommand):
    args = commands(tmp_path)[subcommand]
    write(tmp_path / "papers.json", {"papers": [PAPER]})
    proc = cli(subcommand, *args)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
    assert "JSON array" in proc.stderr


def test_per_solution_prompt_input_equals_the_core_input(tmp_path):
    """Every solution's ``allowed`` is the CORE pool, so Step 10 can reuse Step 8's file."""
    papers = [
        dict(PAPER, title="One"),
        dict(PAPER, title="Two", _classification={"label": "ADJACENT"}),
        dict(PAPER, title="Three"),
    ]
    write(tmp_path / "papers.json", papers)
    write(
        tmp_path / "outline_raw.md",
        "# T\n## Challenge 1: A\n### Solution 1.1: X\n- (1)\n- (3)\n",
    )
    for args in (
        [
            "compute_core_filter",
            "--papers",
            tmp_path / "papers.json",
            "--out",
            tmp_path / "core_filter.json",
        ],
        [
            "format_papers",
            "--papers",
            tmp_path / "papers.json",
            "--filter",
            tmp_path / "core_filter.json",
            "--out",
            tmp_path / "papers_input_core.txt",
        ],
        [
            "parse_outline",
            "--raw",
            tmp_path / "outline_raw.md",
            "--papers",
            tmp_path / "papers.json",
            "--out",
            tmp_path / "outline.json",
            "--solutions-dir",
            tmp_path / "solutions",
        ],
        [
            "format_papers",
            "--papers",
            tmp_path / "papers.json",
            "--filter",
            tmp_path / "solutions" / "1.1.json",
            "--out",
            tmp_path / "solution_input.txt",
        ],
    ):
        proc = cli(*args)
        assert proc.returncode == 0, proc.stderr
    core = (tmp_path / "papers_input_core.txt").read_text(encoding="utf-8")
    assert "Two" not in core and "One" in core and "Three" in core
    assert (tmp_path / "solution_input.txt").read_text(encoding="utf-8") == core
    assert (tmp_path / "solution_input.txt.allowed.txt").read_text(
        encoding="utf-8"
    ) == (tmp_path / "papers_input_core.txt.allowed.txt").read_text(encoding="utf-8")
