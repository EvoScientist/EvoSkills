"""The executed 5-aspect workflow must carry what SKILL.md's checklists say.

scripts/five_aspect_review.js copies checklist text into its seats ("Keep in
sync with SKILL.md"). These tests cover the Pre-Submission Final Checks, which
live in the clarity seat, and the envelope example in EXPERT.md.

Run from the repository root (needs pytest):
    pytest tests/paper-review -q
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "paper-review"
SKILL_MD = (SKILL / "SKILL.md").read_text(encoding="utf-8")
SCRIPT = (SKILL / "scripts" / "five_aspect_review.js").read_text(encoding="utf-8")
EXPERT_MD = (SKILL / "EXPERT.md").read_text(encoding="utf-8")

# Each item of "Pre-Submission Final Checks" in SKILL.md, and the words that
# must appear in the clarity seat for it. Changing an item in SKILL.md means
# changing it here and in the script.
FINAL_CHECKS = {
    'All references are complete (no "?" or missing entries)': "references complete",
    "Author information matches venue requirements": "author information",
    "Page count is within limits": "page count",
    "Supplementary material is properly referenced": "supplementary material",
    "No TODO markers remain in the paper": "TODO markers",
    "Acknowledgments section is appropriate": "acknowledgments",
    "No accidental double-blind violations (for anonymous review)": "double-blind",
    "All cited works have complete bibliographic entries (authors, title, venue, year)": "authors, title, venue, year",
    "No self-citations that break anonymity (for double-blind venues)": "self-citations",
    "Key related works cited — missing a prominent baseline paper can trigger rejection": "key related works cited",
}


def seat(name):
    """Checklist text of one seat in the script's CHECKLISTS object."""
    block = re.search(rf"^  {name}:\n(.*?)(?=^  \w+:\n|^\}};)", SCRIPT, re.M | re.S)
    assert block, f"seat {name} not found"
    pieces = re.findall(r'"((?:[^"\\]|\\.)*)"', block.group(1))
    return "".join(pieces).replace("\\n", "\n")


def final_check_items():
    section = re.search(
        r"^## Pre-Submission Final Checks\n(.*?)^---$", SKILL_MD, re.M | re.S
    )
    assert section, "Pre-Submission Final Checks not found"
    return re.findall(r"^- \[ \] (.+)$", section.group(1), re.M)


def test_every_final_check_in_skill_md_is_known_here():
    assert final_check_items() == list(FINAL_CHECKS)


@pytest.mark.parametrize("item", FINAL_CHECKS)
def test_clarity_seat_carries_each_final_check(item):
    assert FINAL_CHECKS[item].lower() in seat("clarity").lower()


def test_envelope_example_says_what_its_numbers_stand_for():
    envelope = EXPERT_MD.split("## Envelope")[1]
    example = re.search(r"```json\n(.*?)\n```", envelope, re.S).group(1)
    assert '"contribution": 0' in example, "the example changed; revisit this test"
    assert "placeholder" in envelope
    assert "1-5" in envelope
