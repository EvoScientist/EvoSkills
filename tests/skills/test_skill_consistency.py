"""Consistency checks over every skill: descriptions, step numbering, file references, catalogs.

Run from the repository root (needs pytest and pyyaml):
    pytest tests/skills -q

Set SKILLS_ROOT to check another checkout (for example an extracted PR branch).
"""

import os
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(os.environ.get("SKILLS_ROOT") or Path(__file__).resolve().parents[2])
SKILLS = sorted(p for p in (REPO / "skills").iterdir() if p.is_dir())
NAMES = [p.name for p in SKILLS]

# Over the Agent Skills limit on main; paper-graph's description is rewritten by the open PR #44.
KNOWN_LONG_DESCRIPTIONS = {"paper-graph"}


def frontmatter(skill: Path) -> dict:
    return yaml.safe_load(
        (skill / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
    )


def normalise(name: str) -> str:
    name = re.sub(r"\s*->.*$", "", name)  # "-> verify: ..." gate
    name = re.sub(r"\s*\(.*\)\s*$", "", name)  # trailing parenthetical
    return name.replace("`", "").strip().lower()


def overview_and_sections(skill: Path):
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    block = re.search(r"## Core Workflow\n\n```\n(.*?)```", text, re.S)
    if not block:
        return None
    overview = re.findall(r"(?m)^Step ([\d.]+): (.+)$", block.group(1))
    sections = re.findall(r"(?m)^### Step ([\d.]+): (.+)$", text)
    if not overview or not sections:
        return None
    return overview, sections


WITH_STEP_OVERVIEW = [s.name for s in SKILLS if overview_and_sections(s)]


@pytest.mark.parametrize("name", NAMES)
def test_description_within_spec_limit(name):
    description = frontmatter(REPO / "skills" / name)["description"]
    if name in KNOWN_LONG_DESCRIPTIONS and len(description) > 1024:
        pytest.xfail(f"{name}: {len(description)} chars, tracked separately")
    assert len(description) <= 1024, f"{len(description)} characters"
    assert "<" not in description and ">" not in description


@pytest.mark.parametrize("name", WITH_STEP_OVERVIEW)
def test_overview_steps_have_the_same_numbers_as_sections(name):
    overview, sections = overview_and_sections(REPO / "skills" / name)
    assert [n for n, _ in overview] == [n for n, _ in sections]


@pytest.mark.parametrize("name", WITH_STEP_OVERVIEW)
def test_overview_steps_have_the_same_names_as_sections(name):
    overview, sections = overview_and_sections(REPO / "skills" / name)
    pairs = [
        (n, normalise(a), normalise(b)) for (n, a), (_, b) in zip(overview, sections)
    ]
    assert [(n, a) for n, a, _ in pairs] == [(n, b) for n, _, b in pairs]


def test_the_step_overview_checks_cover_the_expected_skills():
    assert {"paper-figures", "academic-slides"} <= set(WITH_STEP_OVERVIEW)


# paper-writing: the Artifact Sources table cites steps of the numbered writing process.
STOPWORDS = {
    "a", "an", "and", "the", "of", "to", "in", "for", "then", "on", "both", "while",
    "section", "sections", "subsection", "subsections", "write", "writing", "written",
    "plan", "plans", "draft", "step", "steps", "paper", "papers", "pivot", "overview",
}  # fmt: skip


def words(text: str) -> set[str]:
    """Significant lower-case words of *text*, with a plain plural 's' removed."""
    found = set()
    for word in re.findall(r"[a-z]+", text.lower()):
        singular = word[:-1] if word.endswith("s") and len(word) > 4 else word
        if word not in STOPWORDS and singular not in STOPWORDS:
            found.add(singular)
    return found


def paper_writing():
    text = (REPO / "skills" / "paper-writing" / "SKILL.md").read_text(encoding="utf-8")
    heading = re.search(r"## The (\d+)-Step Writing Process(.*?)\n## ", text, re.S)
    declared = int(heading.group(1))
    steps = {
        int(n): line for n, line in re.findall(r"(?m)^(\d+)\. (.+)$", heading.group(2))
    }
    table = re.search(r"## Artifact Sources(.*?)\n## ", text, re.S).group(1)
    rows = [
        [c.strip() for c in line.split("|")[1:-1]][2]
        for line in table.splitlines()
        if line.startswith("| `")
    ]
    return declared, steps, rows


def cited_steps(fragment: str) -> list[int]:
    numbers = []
    for part in re.findall(r"Steps? ([\d,\s-]+)", fragment):
        for token in part.split(","):
            token = token.strip()
            if "-" in token:
                low, high = token.split("-")
                numbers += list(range(int(low), int(high) + 1))
            elif token:
                numbers.append(int(token))
    return numbers


def test_paper_writing_step_list_matches_the_count_in_its_heading():
    declared, steps, _ = paper_writing()
    assert sorted(steps) == list(range(1, declared + 1))


def test_paper_writing_table_cites_only_existing_steps():
    _, steps, rows = paper_writing()
    assert rows
    for used_in in rows:
        for number in cited_steps(used_in):
            assert number in steps, used_in


def test_paper_writing_table_labels_describe_the_steps_they_cite():
    """In "Step 9 (Abstract)", the label must share a significant word with step 9's own text."""
    _, steps, rows = paper_writing()
    groups = [
        g
        for used_in in rows
        for g in re.findall(r"(Steps? [\d,\s-]+)\(([^)]*)\)", used_in)
    ]
    assert groups
    for steps_text, label in groups:
        for number in cited_steps(steps_text):
            assert words(label) & words(steps[number]), (
                f"{steps_text.strip()} ({label}): step {number} is {steps[number]!r}"
            )


REFERENCE = re.compile(
    r"(?<![\w/.-])((?:\.\./)?(?:references|assets|scripts|styles|templates)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)"
)
# Paths that name files the agent creates in the user's workspace, not files shipped with the skill.
# The check also reads code blocks (that is where script commands live), so add such a path here.
WORKSPACE_EXAMPLES = {"assets/gradient-bg.png"}
FENCED_BLOCK = re.compile(r"(?ms)^```.*?^```")
LINK = re.compile(r"\]\((<[^>]+>|[^)\s]+)\)")


@pytest.mark.parametrize("name", NAMES)
def test_file_references_resolve(name):
    root = REPO / "skills" / name
    missing = []
    for md in root.rglob("*.md"):
        for ref in REFERENCE.findall(md.read_text(encoding="utf-8", errors="replace")):
            if ref in WORKSPACE_EXAMPLES:
                continue
            if not (
                (root / ref).resolve().exists() or (md.parent / ref).resolve().exists()
            ):
                missing.append(f"{md.relative_to(REPO)}: {ref}")
    assert not missing, missing


@pytest.mark.parametrize("name", NAMES)
def test_relative_markdown_links_resolve(name):
    """Links such as [guide](references/guide.md) or [x](../other-skill/references/x.md)."""
    root = REPO / "skills" / name
    missing = []
    for md in root.rglob("*.md"):
        prose = FENCED_BLOCK.sub("", md.read_text(encoding="utf-8", errors="replace"))
        for target in LINK.findall(prose):
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]  # [text](<path with spaces.md>)
            if re.match(r"[a-z]+:", target) or target.startswith("#"):
                continue  # URL or in-page anchor
            if "/" not in target and "." not in target:
                continue  # placeholder such as (URL)
            if not (md.parent / target.split("#")[0]).resolve().exists():
                missing.append(f"{md.relative_to(REPO)}: {target}")
    assert not missing, missing


def readme_sections(filename: str) -> dict[str, list[str]]:
    """Bullet lines of each per-skill section, keyed by skill name."""
    text = (REPO / filename).read_text(encoding="utf-8")
    sections = {}
    for match in re.finditer(r"(?m)^### \S+ `([a-z0-9-]+)` — .*$", text):
        body = text[match.end() :]
        end = re.search(r"(?m)^(### |## |<p )", body)
        body = body[: end.start()] if end else body
        sections[match.group(1)] = [
            line for line in body.splitlines() if line.startswith("- ")
        ]
    return sections


def test_both_readmes_describe_every_skill_with_the_same_number_of_bullets():
    english, chinese = readme_sections("README.md"), readme_sections("README.zh-CN.md")
    assert sorted(english) == NAMES
    assert sorted(chinese) == NAMES
    assert {n: len(b) for n, b in english.items()} == {
        n: len(b) for n, b in chinese.items()
    }


@pytest.mark.parametrize(
    "catalog", ["README.md", "README.zh-CN.md", "skills/README.md"]
)
def test_every_skill_has_a_row_in_the_catalog_table(catalog):
    text = (REPO / catalog).read_text(encoding="utf-8")
    missing = [
        n for n in NAMES if not re.search(rf"(?m)^\| \[`{re.escape(n)}`\]\(", text)
    ]
    assert not missing, missing
