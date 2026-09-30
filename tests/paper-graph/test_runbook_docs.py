"""The paper-graph runbook must describe what the scripts and templates do.

Run from the repository root (needs pytest):
    pytest tests/paper-graph -q
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "paper-graph"
SKILL_MD = (SKILL / "SKILL.md").read_text(encoding="utf-8")


def reference(name):
    return (SKILL / "references" / name).read_text(encoding="utf-8")


def step(number):
    """Text of one '### Step N' section of the runbook."""
    match = re.search(
        rf"^### Step {number} —.*?(?=^### Step \d+ —|^---$)", SKILL_MD, re.M | re.S
    )
    assert match, f"Step {number} not found"
    return match.group(0)


def placeholders(template):
    """Single-brace {slots}; {{...}} is an escaped literal brace."""
    return set(re.findall(r"(?<!\{)\{([a-z_]+)\}(?!\})", template))


def brief_placeholders(section):
    # The bullet may be wrapped: take it up to the next bullet.
    item = re.search(
        r"^- The fully-substituted prompt string.*?(?=^- )", section, re.M | re.S
    )
    assert item, "fan-out brief not found"
    return set(re.findall(r"\{([a-z_]+)\}", item.group(0)))


def test_detail_fanout_brief_lists_every_placeholder_of_the_template():
    assert placeholders(reference("detail.md")) <= brief_placeholders(step(10))


def test_audit_fanout_brief_lists_every_placeholder_of_the_template():
    assert placeholders(reference("audit_edge.md")) <= brief_placeholders(step(11))


def test_workdir_layout_shows_the_full_verdict_record():
    line = next(
        ln
        for ln in SKILL_MD.splitlines()
        if ln.startswith(("├── verdicts/<key>.json", "└── verdicts/<key>.json"))
    )
    assert "source_quote" in line and "target_quote" in line


def test_detail_scratchpad_rule_accepts_excerpts_like_the_edge_test():
    text = reference("detail.md")
    assert "from the abstracts, drop the edge" not in text
    assert "from the abstracts or excerpts, drop the edge" in text


def test_audit_call_budget_fits_two_quotes_and_quotes_are_capped():
    budget = re.search(r"~(\d+) max tokens", step(11))
    assert budget and int(budget.group(1)) >= 1000
    assert "300 characters" in reference("audit_edge.md")


def test_render_step_passes_verdicts_and_says_it_is_required():
    section = step(12)
    assert "--verdicts <workdir>/verdicts/<key>.json" in section
    assert "required" in section


def test_detail_grounding_rule_covers_excerpts():
    text = reference("detail.md")
    assert "not present in the abstracts above" not in text
    assert "not present in the abstracts or excerpts above" in text
