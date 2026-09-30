"""Tests for the deterministic half of skills/paper-graph (scripts/cli.py).

They drive the CLI the way the runbook does, with small fixture files, and
check what ends up in the rendered Mermaid and in the final report.

Run from the repository root (needs pytest, httpx and python-dotenv):
    pytest tests/paper-graph -q
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "paper-graph"
CLI = SKILL / "scripts" / "cli.py"

PAPERS = [
    {
        "title": "Manual Stream Alignment",
        "year": 2019,
        "authors": "A. Author",
        "venue": "V",
        "url": "https://example.org/1",
        "abstract": "Our method requires manual alignment of the sensor streams before training.",
        "_conclusion_section": "A remaining limitation is that alignment fails\nat long context lengths.",
    },
    {
        "title": "Dynamic Time Warping for Streams",
        "year": 2021,
        "authors": "B. Author",
        "venue": "V",
        "url": "https://example.org/2",
        "abstract": "We introduce dynamic time warping to remove the manual alignment step. The method doesn’t need labels.",
        "_conclusion_section": None,
    },
    {
        "title": "Learned Warps",
        "year": 2023,
        "authors": "C. Author",
        "venue": "V",
        "url": "https://example.org/3",
        "abstract": "We replace dynamic time warping with a learned warp that scales to long contexts.",
        "_conclusion_section": None,
    },
    {
        "title": "A Survey of Alignment",
        "year": 2020,
        "authors": "D. Author",
        "venue": "V",
        "url": "https://example.org/4",
        "abstract": "We survey alignment methods; nonetheless several questions remain open.",
        "_conclusion_section": None,
    },
]

CONTEXT = {
    "challenge_idx": 1,
    "challenge_name": "Aligning streams",
    "solution_key": [1, 1],
    "solution_key_str": "1.1",
    "solution_name": "Warping",
    "paper_nums": [1, 2, 3],
    "allowed": [1, 2, 3, 4],
}

DETAIL = """\
### Paper (1)
- Gap addressed: N/A
- Evolution from: (none - initial work)

### Paper (2)
- Gap addressed: (1) required manual alignment, so (2) introduced dynamic time warping
- Evolution from: (1)

### Paper (3)
- Gap addressed: (2) did not scale, so (3) introduced a learned warp
- Evolution from: (2)
"""

Q1 = "requires manual alignment of the sensor streams"
Q2 = "introduce dynamic time warping to remove the manual alignment"
Q2_AS_SOURCE = "We introduce dynamic time warping"
Q3 = "replace dynamic time warping with a learned warp"


def verdict(
    source_n, target_n, source_quote, target_quote, label="SUPPORTED_BY_ABSTRACT"
):
    return {
        "source_n": source_n,
        "target_n": target_n,
        "verdict": label,
        "source_quote": source_quote,
        "target_quote": target_quote,
        "reason": "test",
    }


GOOD_12 = verdict(1, 2, Q1, Q2)
GOOD_23 = verdict(2, 3, Q2_AS_SOURCE, Q3)


def cli(*args):
    return subprocess.run(
        [sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True
    )


def render(tmp_path, verdicts, papers=PAPERS, detail=DETAIL, context=CONTEXT):
    """Run render_detail_mermaid; ``verdicts=None`` omits the flag."""
    (tmp_path / "papers.json").write_text(json.dumps(papers), encoding="utf-8")
    (tmp_path / "ctx.json").write_text(json.dumps(context), encoding="utf-8")
    (tmp_path / "raw.md").write_text(detail, encoding="utf-8")
    out = tmp_path / "out.json"
    args = [
        "render_detail_mermaid",
        "--raw",
        tmp_path / "raw.md",
        "--context",
        tmp_path / "ctx.json",
        "--papers",
        tmp_path / "papers.json",
        "--out",
        out,
    ]
    if verdicts is not None:
        (tmp_path / "verdicts.json").write_text(json.dumps(verdicts), encoding="utf-8")
        args += ["--verdicts", tmp_path / "verdicts.json"]
    proc = cli(*args)
    result = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    return proc, result


def lineage_edges(mermaid):
    """Directed paper-to-paper edges in a rendered detail graph."""
    return {
        (int(a), int(b))
        for a, b in re.findall(r"_P(\d+) -->\|Gap[^|]*\| \w+_P(\d+)", mermaid)
    }


def paper_nodes(mermaid):
    return {int(n) for n in re.findall(r'^\s+\w+_P(\d+)\("', mermaid, flags=re.M)}


# --- the audit gate -------------------------------------------------------


def test_verified_edges_are_rendered(tmp_path):
    proc, out = render(tmp_path, [GOOD_12, GOOD_23])
    assert proc.returncode == 0, proc.stderr
    assert lineage_edges(out["mermaid"]) == {(1, 2), (2, 3)}


def test_verdicts_flag_is_required(tmp_path):
    proc, out = render(tmp_path, None)
    assert proc.returncode == 2
    assert out is None
    assert "--verdicts" in proc.stderr


def test_edge_without_a_verdict_record_is_not_rendered(tmp_path):
    proc, out = render(tmp_path, [])
    assert proc.returncode == 0, proc.stderr
    assert lineage_edges(out["mermaid"]) == set()


@pytest.mark.parametrize("label", ["INFERRED", "REJECT", "supported", ""])
def test_only_supported_labels_render(tmp_path, label):
    proc, out = render(tmp_path, [verdict(1, 2, Q1, Q2, label=label)])
    assert proc.returncode == 0, proc.stderr
    assert (1, 2) not in lineage_edges(out["mermaid"])


def test_missing_year_does_not_crash(tmp_path):
    papers = [dict(p) for p in PAPERS]
    papers[0]["year"] = "n.d."
    proc, out = render(tmp_path, [GOOD_12], papers=papers)
    assert proc.returncode == 0, proc.stderr
    assert (1, 2) in lineage_edges(out["mermaid"])
    assert any("chronology" in note["reason"] for note in out["audit_notes"])


def test_backwards_chronology_is_rejected(tmp_path):
    papers = [dict(p) for p in PAPERS]
    papers[0]["year"] = 2022
    proc, out = render(tmp_path, [GOOD_12], papers=papers)
    assert proc.returncode == 0, proc.stderr
    assert (1, 2) not in lineage_edges(out["mermaid"])
    assert any("chronology" in d["reason"] for d in out["audit_downgrades"])


@pytest.mark.parametrize(
    "bad_record",
    [
        {"target_n": 2, "verdict": "REJECT"},
        {"source_n": None, "target_n": 2, "verdict": "REJECT"},
        {"source_n": "1.1", "target_n": 2, "verdict": "REJECT"},
        "not an object",
        ["a", "list"],
    ],
)
def test_malformed_record_does_not_take_down_the_valid_ones(tmp_path, bad_record):
    proc, out = render(tmp_path, [GOOD_12, bad_record])
    assert proc.returncode == 0, proc.stderr
    assert (1, 2) in lineage_edges(out["mermaid"])
    assert len(out["audit_downgrades"]) == 1


def test_fractional_paper_number_is_not_truncated_onto_another_edge(tmp_path):
    record = verdict(2.7, 3, Q2_AS_SOURCE, Q3)
    proc, out = render(tmp_path, [record])
    assert proc.returncode == 0, proc.stderr
    assert (2, 3) not in lineage_edges(out["mermaid"])


@pytest.mark.parametrize(
    "source_quote, target_quote",
    [
        (" ", Q2),
        (Q1, "the"),
        ("to", "to"),
        ("NONE", Q2),
        (Q1, "None"),
        (Q1, ""),
        (Q1, "a sentence that is not in the target paper at all"),
    ],
)
def test_trivial_or_unverifiable_quotes_are_rejected(
    tmp_path, source_quote, target_quote
):
    proc, out = render(tmp_path, [verdict(1, 2, source_quote, target_quote)])
    assert proc.returncode == 0, proc.stderr
    assert (1, 2) not in lineage_edges(out["mermaid"])
    assert out["audit_downgrades"]


def test_none_sentinel_is_case_insensitive(tmp_path):
    # Paper 4's abstract contains "nonetheless", so a substring test would
    # accept the lowercase sentinel as evidence.
    detail = (
        "### Paper (4)\n- Gap addressed: N/A\n"
        "- Evolution from: (none - initial work)\n\n"
        "### Paper (3)\n- Gap addressed: g\n- Evolution from: (4)\n"
    )
    proc, out = render(tmp_path, [verdict(4, 3, "none", Q3)], detail=detail)
    assert proc.returncode == 0, proc.stderr
    assert (4, 3) not in lineage_edges(out["mermaid"])


@pytest.mark.parametrize(
    "source_n, target_n, source_quote, target_quote",
    [
        # the excerpt has a line break inside the quoted span
        (1, 3, "alignment fails at long context lengths", Q3),
        # straight apostrophe in the quote, typographic one in the abstract
        (2, 3, "The method doesn't need labels", Q3),
        # the audit prompt shows the title, so it is quotable evidence
        (2, 3, "Dynamic Time Warping for Streams", Q3),
    ],
)
def test_genuine_quotes_survive_whitespace_and_typography(
    tmp_path, source_n, target_n, source_quote, target_quote
):
    detail = (
        f"### Paper ({source_n})\n- Gap addressed: N/A\n"
        "- Evolution from: (none - initial work)\n\n"
        f"### Paper ({target_n})\n- Gap addressed: g\n"
        f"- Evolution from: ({source_n})\n"
    )
    record = verdict(source_n, target_n, source_quote, target_quote)
    proc, out = render(tmp_path, [record], detail=detail)
    assert proc.returncode == 0, proc.stderr
    assert (source_n, target_n) in lineage_edges(out["mermaid"])


def test_quote_spliced_across_title_and_abstract_is_rejected(tmp_path):
    # "...for Streams" ends the title and "We introduce..." starts the
    # abstract; no single field contains the span.
    spliced = "Warping for Streams We introduce dynamic time warping"
    proc, out = render(tmp_path, [GOOD_12, verdict(2, 3, spliced, Q3)])
    assert proc.returncode == 0, proc.stderr
    assert lineage_edges(out["mermaid"]) == {(1, 2)}


def test_supported_edges_that_form_a_cycle_are_not_drawn(tmp_path):
    papers = [dict(p) for p in PAPERS]
    papers[1]["year"] = papers[2]["year"] = 2021
    detail = (
        "### Paper (2)\n- Gap addressed: g\n- Evolution from: (3)\n\n"
        "### Paper (3)\n- Gap addressed: g\n- Evolution from: (2)\n"
    )
    records = [GOOD_23, verdict(3, 2, Q3, Q2)]
    proc, out = render(tmp_path, records, papers=papers, detail=detail)
    assert proc.returncode == 0, proc.stderr
    assert lineage_edges(out["mermaid"]) == set()
    assert {(e["source_n"], e["target_n"]) for e in out["edges_not_rendered"]} == {
        (2, 3),
        (3, 2),
    }
    assert "cycle" in proc.stdout


def test_verdict_for_an_edge_the_detail_does_not_claim_is_reported(tmp_path):
    # A verdict file that does not belong to this detail output (stale, or
    # written for another solution) must not pass unnoticed.
    stray = verdict(1, 3, Q1, Q3)
    proc, out = render(tmp_path, [GOOD_12, GOOD_23, stray])
    assert proc.returncode == 0, proc.stderr
    assert lineage_edges(out["mermaid"]) == {(1, 2), (2, 3)}
    assert out["verdicts_unmatched"] == [{"source_n": 1, "target_n": 3}]
    assert "(1)->(3)" in proc.stdout


def test_self_edge_is_rejected(tmp_path):
    detail = "### Paper (2)\n- Gap addressed: g\n- Evolution from: (2)\n"
    proc, out = render(tmp_path, [verdict(2, 2, Q2, Q2)], detail=detail)
    assert proc.returncode == 0, proc.stderr
    assert lineage_edges(out["mermaid"]) == set()


@pytest.mark.parametrize("order", ["bogus_first", "bogus_last"])
def test_conflicting_duplicate_verdicts_fail_closed(tmp_path, order):
    bogus = verdict(1, 2, "this sentence is nowhere in the source", Q2)
    records = [bogus, GOOD_12] if order == "bogus_first" else [GOOD_12, bogus]
    proc, out = render(tmp_path, records)
    assert proc.returncode == 0, proc.stderr
    assert (1, 2) not in lineage_edges(out["mermaid"])
    assert any("duplicate" in d["reason"] for d in out["audit_downgrades"])


def test_identical_duplicate_verdicts_still_render(tmp_path):
    proc, out = render(tmp_path, [GOOD_12, dict(GOOD_12)])
    assert proc.returncode == 0, proc.stderr
    assert (1, 2) in lineage_edges(out["mermaid"])


def test_supported_edge_from_a_paper_without_its_own_header(tmp_path):
    # With every CORE paper allowed as context, the detail step can name a
    # predecessor that has no "### Paper (N)" block of its own.
    detail = "### Paper (3)\n- Gap addressed: g\n- Evolution from: (2)\n"
    proc, out = render(tmp_path, [GOOD_23], detail=detail)
    assert proc.returncode == 0, proc.stderr
    mermaid = out["mermaid"]
    assert lineage_edges(mermaid) == {(2, 3)}
    assert paper_nodes(mermaid) == {2, 3}
    for n in paper_nodes(mermaid):
        assert re.search(rf"_P{n}\b.*(-->|---)|(-->|---).*_P{n}\b", mermaid), n


# --- nothing is silent ----------------------------------------------------


def test_dropped_edges_are_reported_on_stdout(tmp_path):
    bogus = verdict(1, 2, "this sentence is nowhere in the source", Q2)
    proc, _ = render(tmp_path, [bogus, GOOD_23])
    assert proc.returncode == 0, proc.stderr
    assert "(1)->(2)" in proc.stdout
    assert "source_quote" in proc.stdout


def test_help_and_schema_error_name_the_quote_fields(tmp_path):
    help_text = cli("render_detail_mermaid", "--help").stdout
    assert "source_quote" in help_text and "target_quote" in help_text
    proc, _ = render(tmp_path, {"not": "a list"})
    assert proc.returncode == 2
    assert "source_quote" in proc.stderr and "target_quote" in proc.stderr


def test_render_output_records_the_audit(tmp_path):
    bogus = verdict(2, 3, "this sentence is nowhere in the source", Q3)
    _, out = render(tmp_path, [GOOD_12, bogus])
    assert out["audited"] is True
    assert out["verdict_records"] == 2
    assert out["edges_rendered"] == 1
    assert [(d["source_n"], d["target_n"]) for d in out["audit_downgrades"]] == [(2, 3)]


# --- assemble_report ------------------------------------------------------


def assemble(tmp_path, details):
    details_dir = tmp_path / "details"
    details_dir.mkdir()
    for name, payload in details.items():
        (details_dir / name).write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "papers.json").write_text(json.dumps(PAPERS), encoding="utf-8")
    (tmp_path / "pq.json").write_text(json.dumps({"goal": "g"}), encoding="utf-8")
    (tmp_path / "outline.json").write_text(
        json.dumps({"root_title": "T", "mermaid": "graph LR"}), encoding="utf-8"
    )
    report = tmp_path / "report.md"
    proc = cli(
        "assemble_report",
        "--parsed-query",
        tmp_path / "pq.json",
        "--outline",
        tmp_path / "outline.json",
        "--details-dir",
        details_dir,
        "--papers",
        tmp_path / "papers.json",
        "--out",
        report,
    )
    return proc, report


RENDER = {
    "challenge_idx": 1,
    "solution_key": "1.1",
    "solution_name": "Warping",
    "mermaid": "graph LR\n    A --> B",
    "footnotes_md": "",
}


def test_assemble_refuses_a_render_without_the_audit_marker(tmp_path):
    proc, report = assemble(tmp_path, {"1.1.json": RENDER})
    assert proc.returncode == 2
    assert "1.1.json" in proc.stderr
    assert not report.exists()


def test_assemble_accepts_audited_renders_and_skips_other_json(tmp_path):
    proc, report = assemble(
        tmp_path,
        {"1.1.json": dict(RENDER, audited=True), "notes.json": {"edges": []}},
    )
    assert proc.returncode == 0, proc.stderr
    assert "A --> B" in report.read_text(encoding="utf-8")


# --- parse_outline --------------------------------------------------------


def parse_outline(tmp_path, outline):
    (tmp_path / "papers.json").write_text(json.dumps(PAPERS), encoding="utf-8")
    (tmp_path / "outline_raw.md").write_text(outline, encoding="utf-8")
    proc = cli(
        "parse_outline",
        "--raw",
        tmp_path / "outline_raw.md",
        "--papers",
        tmp_path / "papers.json",
        "--out",
        tmp_path / "outline.json",
        "--solutions-dir",
        tmp_path / "solutions",
    )
    summary = json.loads((tmp_path / "outline.json").read_text(encoding="utf-8"))
    return proc, summary


def render_outline(tmp_path):
    out = tmp_path / "outline_mermaid.json"
    proc = cli(
        "render_outline_mermaid",
        "--raw",
        tmp_path / "outline_raw.md",
        "--papers",
        tmp_path / "papers.json",
        "--out",
        out,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))["mermaid"]


def test_first_placement_of_a_repeated_paper_wins(tmp_path):
    outline = (
        "# T\n## Challenge 1: A\n### Solution 1.1: X\n- (1)\n- (2)\n"
        "## Challenge 2: B\n### Solution 2.1: Y\n- (2)\n- (3)\n"
    )
    proc, summary = parse_outline(tmp_path, outline)
    assert proc.returncode == 0, proc.stderr
    members = {s["solution_key"]: s["paper_nums"] for s in summary["solutions"]}
    assert members == {"1.1": [1, 2], "2.1": [3]}


def test_restated_solution_header_keeps_the_earlier_members(tmp_path):
    outline = (
        "# T\n## Challenge 1: A\n### Solution 1.1: X\n- (1)\n- (2)\n"
        "### Solution 1.1: X\n- (1)\n- (2)\n- (4)\n"
    )
    proc, summary = parse_outline(tmp_path, outline)
    assert proc.returncode == 0, proc.stderr
    assert [s["solution_key"] for s in summary["solutions"]] == ["1.1"]
    ctx = json.loads((tmp_path / "solutions" / "1.1.json").read_text(encoding="utf-8"))
    assert ctx["paper_nums"] == [1, 2, 4]
    assert render_outline(tmp_path).count("C1 --> S1_1[") == 1


def test_solution_left_without_members_is_pruned(tmp_path):
    outline = (
        "# T\n## Challenge 1: A\n### Solution 1.1: X\n- (1)\n- (2)\n"
        "## Challenge 2: B\n### Solution 2.1: Y\n- (1)\n### Solution 2.2: Z\n- (3)\n"
    )
    proc, summary = parse_outline(tmp_path, outline)
    assert proc.returncode == 0, proc.stderr
    assert [s["solution_key"] for s in summary["solutions"]] == ["1.1", "2.2"]
    assert not (tmp_path / "solutions" / "2.1.json").exists()
    assert "2.1" in proc.stdout
    assert "S2_1" not in render_outline(tmp_path)


def test_outline_without_any_solution_member_is_an_error(tmp_path):
    outline = "# T\n## Challenge 1: A\n### Solution 1.1: X\n- (99)\n"
    (tmp_path / "papers.json").write_text(json.dumps(PAPERS), encoding="utf-8")
    (tmp_path / "outline_raw.md").write_text(outline, encoding="utf-8")
    proc = cli(
        "parse_outline",
        "--raw",
        tmp_path / "outline_raw.md",
        "--papers",
        tmp_path / "papers.json",
        "--out",
        tmp_path / "outline.json",
    )
    assert proc.returncode == 4
    assert "1.1" in proc.stderr
    assert not (tmp_path / "outline.json").exists()


# --- the deterministic steps chained as in the runbook ---------------------


def test_report_contains_only_verified_lineage(tmp_path):
    outline = "# Stream alignment\n## Challenge 1: Aligning streams\n### Solution 1.1: Warping\n- (1)\n- (2)\n- (3)\n"
    proc, _ = parse_outline(tmp_path, outline)
    assert proc.returncode == 0, proc.stderr
    render_outline(tmp_path)
    (tmp_path / "details").mkdir()
    (tmp_path / "raw.md").write_text(DETAIL, encoding="utf-8")
    parsed = tmp_path / "parsed.json"
    proc = cli(
        "parse_detail",
        "--raw",
        tmp_path / "raw.md",
        "--context",
        tmp_path / "solutions" / "1.1.json",
        "--out",
        parsed,
    )
    assert proc.returncode == 0, proc.stderr
    claimed = json.loads(parsed.read_text(encoding="utf-8"))["edges"]
    assert {(e["source_n"], e["target_n"]) for e in claimed} == {(1, 2), (2, 3)}

    verdicts = [GOOD_12, verdict(2, 3, "NONE", Q3, label="INFERRED")]
    (tmp_path / "verdicts.json").write_text(json.dumps(verdicts), encoding="utf-8")
    proc = cli(
        "render_detail_mermaid",
        "--raw",
        tmp_path / "raw.md",
        "--context",
        tmp_path / "solutions" / "1.1.json",
        "--papers",
        tmp_path / "papers.json",
        "--verdicts",
        tmp_path / "verdicts.json",
        "--out",
        tmp_path / "details" / "1.1.json",
    )
    assert proc.returncode == 0, proc.stderr
    (tmp_path / "pq.json").write_text(json.dumps({"goal": "g"}), encoding="utf-8")
    report = tmp_path / "report.md"
    proc = cli(
        "assemble_report",
        "--parsed-query",
        tmp_path / "pq.json",
        "--outline",
        tmp_path / "outline_mermaid.json",
        "--details-dir",
        tmp_path / "details",
        "--papers",
        tmp_path / "papers.json",
        "--out",
        report,
    )
    assert proc.returncode == 0, proc.stderr
    text = report.read_text(encoding="utf-8")
    assert lineage_edges(text) == {(1, 2)}
    assert "inferred" not in text.lower()
