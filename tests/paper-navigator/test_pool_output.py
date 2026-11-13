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
        "arxiv_monitor",
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
    assert "read_file" in skill_text
    assert "working directory at the task workspace" in skill_text


@pytest.mark.parametrize(
    "module_name, fetch_function, arguments",
    [
        ("scholar_search", "search", ["--query", "example"]),
        ("recommend", "recommend", ["--positive", "p1"]),
        (
            "citation_traverse",
            "get_citations",
            ["--paper-id", "p1", "--direction", "forward", "--no-sanity-check"],
        ),
    ],
)
def test_documented_pool_writers_write_read_round_trip(
    tmp_path, module_name, fetch_function, arguments
):
    """Run each real CLI/JSONL writer in a fresh workspace with mocked retrieval."""
    assert not (tmp_path / "paper-navigator").exists()
    pool = "./paper-navigator/regression-run/pool.jsonl"
    script = f"""
import sys
from unittest.mock import patch
sys.path.insert(0, {str(SCRIPTS)!r})
import {module_name} as writer
paper = {{'paperId': 'p1', 'title': 'Example', 'tldr': {{'text': None}}}}
sys.argv = [{module_name!r} + '.py'] + {arguments!r} + ['--output', {pool!r}, '--append']
with patch.object(writer, {fetch_function!r}, return_value=[paper]):
    writer.main()
    writer.main()
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


@pytest.mark.parametrize("append", [False, True])
@pytest.mark.parametrize("path", ["pool.jsonl", "new/nested/pool.jsonl"])
def test_write_jsonl_creates_parents_and_preserves_write_modes(
    modules, tmp_path, monkeypatch, append, path
):
    monkeypatch.chdir(tmp_path)
    first = {"paperId": "p1"}
    second = {"paperId": "p2"}
    assert not Path(path).exists()
    assert modules.utils.write_jsonl(path, [first], append=append) == 1
    assert modules.utils.read_jsonl(path) == [first]
    assert modules.utils.write_jsonl(path, [second], append=append) == 1
    assert modules.utils.read_jsonl(path) == ([first, second] if append else [second])


def test_runbooks_name_pool_writers_and_exclude_arxiv_monitor():
    for document in (SKILL / "SKILL.md", SKILL / "references/iterative-collection.md"):
        text = document.read_text()
        setup = next(
            line
            for line in text.splitlines()
            if line.startswith(("**Workspace pool:**", "**Setup:**"))
        )
        for writer in ("scholar_search", "citation_traverse", "recommend"):
            assert f"`{writer}`" in setup
        assert "`arxiv_monitor`" in setup
        assert "./paper-navigator/<run-id>/pool.jsonl" in setup
        for line in text.splitlines():
            if "python scripts/arxiv_monitor.py" in line:
                assert "--output" not in line
                assert "--append" not in line
    assert "All discovery scripts:" not in (SKILL / "SKILL.md").read_text()


@pytest.mark.parametrize("json_output", [False, True])
def test_arxiv_monitor_stdout_preserves_rows_without_paper_id(
    modules, tmp_path, monkeypatch, capsys, json_output
):
    paper = {
        "arxiv_id": "2601.00001",
        "title": "An arXiv example",
        "authors": ["Example Author"],
        "categories": ["cs.AI"],
        "published": "2026-01-01",
        "summary": "Example summary",
        "comment": "",
        "pdf_url": "https://arxiv.org/pdf/2601.00001",
    }
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(modules.arxiv_monitor, "fetch_by_keywords", lambda *a: [paper])
    argv = ["arxiv_monitor.py", "--keywords", "example"]
    monkeypatch.setattr(sys, "argv", argv + (["--json"] if json_output else []))
    modules.arxiv_monitor.main()
    output = capsys.readouterr().out
    if json_output:
        assert json.loads(output) == [paper]
    else:
        assert paper["title"] in output
        assert paper["arxiv_id"] in output
    assert list(tmp_path.iterdir()) == []
