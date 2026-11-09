"""Offline regressions for issue #68 (no API keys or network calls required).

Run from the repository root: pytest tests/paper-navigator -q
"""

import copy
import importlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "paper-navigator"
SCRIPTS = SKILL / "scripts"


@pytest.fixture
def modules(monkeypatch):
    """Keep generic script module names from leaking into other skill tests."""
    names = (
        "utils",
        "deepxiv_client",
        "scholar_search",
        "recommend",
        "citation_traverse",
        "literature_report",
        "match_paper_by_title",
        "trending",
    )
    saved = {name: sys.modules.pop(name) for name in names if name in sys.modules}
    monkeypatch.syspath_prepend(str(SCRIPTS))
    try:
        yield SimpleNamespace(**{name: importlib.import_module(name) for name in names})
    finally:
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(saved)


@pytest.mark.parametrize(
    "tldr",
    [None, {}, {"text": None}, {"text": ""}, {"text": "  "}, {"text": 0}],
)
@pytest.mark.parametrize("mode", ["jsonl", "json", "markdown"])
def test_empty_tldr_is_omitted_without_mutating_input(
    modules, tmp_path, capsys, tldr, mode
):
    paper = {
        "paperId": "paper-1",
        "title": "Example",
        "abstract": "An available abstract.",
        "tldr": tldr,
    }
    original = copy.deepcopy(paper)
    target = tmp_path / "pool.jsonl"
    args = SimpleNamespace(
        output=str(target) if mode == "jsonl" else None,
        append=False,
        json=mode == "json",
    )
    modules.utils.emit_results(
        [paper], args, format_fn=modules.scholar_search.format_paper
    )
    output = capsys.readouterr().out
    assert paper == original
    if mode == "markdown":
        assert "An available abstract." in output
        assert "TLDR:" not in output
        return
    emitted = (
        json.loads(target.read_text()) if mode == "jsonl" else json.loads(output)[0]
    )
    assert "tldr" not in emitted
    assert emitted["abstract"] == original["abstract"]
    # The consumer from #68 must not concatenate a null dict.text value.
    tl = emitted.get("tldr")
    assert isinstance(
        "TLDR: " + (tl.get("text") if isinstance(tl, dict) else str(tl)), str
    )


@pytest.mark.parametrize("tldr", [{"text": "A summary", "model": "s2"}, "A summary"])
def test_nonempty_tldr_preserves_object_format_and_existing_consumers(
    modules, tmp_path, capsys, tldr
):
    paper = {"paperId": "paper-1", "title": "Example", "tldr": tldr}
    target = tmp_path / "pool.jsonl"
    modules.utils.emit_results(
        [paper], SimpleNamespace(output=str(target), append=False)
    )
    emitted = json.loads(target.read_text())
    assert emitted["tldr"]["text"] == "A summary"
    if isinstance(tldr, dict):
        assert emitted["tldr"] == tldr
    for formatter in (
        modules.scholar_search.format_paper,
        modules.recommend.format_paper,
        modules.citation_traverse.format_paper,
        modules.match_paper_by_title.format_paper,
        modules.trending.format_paper,
    ):
        assert "A summary" in formatter(emitted, 1)
    assert modules.literature_report._get_tldr(emitted) == "A summary"


def test_missing_tldr_stays_missing(modules):
    paper = {"paperId": "paper-1", "title": "Example"}
    assert modules.utils._normalize_tldr(paper) == paper


def test_documented_pool_paths_share_workspace_directory():
    paths = []
    for document in (SKILL / "SKILL.md", SKILL / "references/iterative-collection.md"):
        text = document.read_text()
        assert "/tmp/pool.jsonl" not in text
        for match in re.finditer(r'--output\s+("[^"]+"|\S+)', text):
            path = shlex.split(match.group(1))[0]
            if path.endswith("pool.jsonl"):
                assert not Path(path).is_absolute()
                assert Path(path).parts[0] == "paper-navigator"
                paths.append(path)
    assert len(paths) == 8
    assert set(paths) == {"./paper-navigator/<run-id>/pool.jsonl"}
    skill_text = (SKILL / "SKILL.md").read_text()
    assert 'mkdir -p "./paper-navigator/<run-id>"' in skill_text
    assert "read_file" in skill_text
    assert "working directory at the task workspace" in skill_text


def test_documented_setup_and_search_write_read_round_trip(tmp_path):
    """Run the real CLI/JSONL writer in a separate workspace with mocked search."""
    setup = 'mkdir -p "./paper-navigator/<run-id>"'.replace(
        "<run-id>", "regression-run"
    )
    subprocess.run(shlex.split(setup), cwd=tmp_path, check=True)
    pool = "./paper-navigator/regression-run/pool.jsonl"
    script = f"""
import sys
from unittest.mock import patch
sys.path.insert(0, {str(SCRIPTS)!r})
import scholar_search
paper = {{'paperId': 'p1', 'title': 'Example', 'tldr': {{'text': None}}}}
sys.argv = ['scholar_search.py', '--query', 'example', '--output', {pool!r}, '--append']
with patch.object(scholar_search, 'search', return_value=[paper]):
    scholar_search.main()
    scholar_search.main()
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    summaries = [json.loads(line) for line in proc.stdout.splitlines()]
    assert [row["written"] for row in summaries] == [1, 0]
    assert [row["total"] for row in summaries] == [1, 1]
    assert all(row["output"] == pool for row in summaries)
    records = [json.loads(line) for line in (tmp_path / pool).read_text().splitlines()]
    assert records == [{"paperId": "p1", "title": "Example"}]
