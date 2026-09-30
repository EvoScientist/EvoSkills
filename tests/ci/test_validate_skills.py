"""Tests for .github/scripts/validate_skills.py.

Run from the repository root (needs pytest and pyyaml):
    pytest tests/ci -q
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".github" / "scripts" / "validate_skills.py"

SKILL_MD = """\
---
name: {name}
description: "A skill."
allowed-tools: "read_file"
metadata:
  author: Someone
  version: {version}
{extra}  tags: [a]
---

# Body
"""


def write_skill(
    root: Path, dirname: str, *, name=None, version="'1.0.0'", extra="", expert=False
):
    skill = root / "skills" / dirname
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        SKILL_MD.format(name=name or dirname, version=version, extra=extra),
        encoding="utf-8",
    )
    if expert:
        (skill / "EXPERT.md").write_text(
            "> scope line\n\n## Persona\n", encoding="utf-8"
        )
    return skill


def run(root: Path, *args: str):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=root, capture_output=True, text=True
    )
    return proc.returncode, proc.stdout + proc.stderr


def git(root: Path, *args: str):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )


def repo_with_main(root: Path):
    git(root, "init", "-q", "-b", "main")
    write_skill(root, "alpha")
    (root / "skills" / "alpha" / "references").mkdir()
    (root / "skills" / "alpha" / "references" / "guide.md").write_text("v1\n")
    (root / "skills" / "README.md").write_text("catalog\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    git(root, "switch", "-q", "-c", "feature")


# --- static checks ---------------------------------------------------------


def test_valid_skill_passes(tmp_path):
    write_skill(tmp_path, "alpha")
    code, out = run(tmp_path)
    assert code == 0, out


def test_name_different_from_directory_is_an_error(tmp_path):
    write_skill(tmp_path, "alpha", name="beta")
    code, out = run(tmp_path)
    assert code == 1
    assert "alpha" in out and "must match the directory name" in out


def test_non_numeric_version_is_an_error(tmp_path):
    write_skill(tmp_path, "alpha", version="'1.0.0-beta'")
    code, out = run(tmp_path)
    assert code == 1
    assert "version" in out and "dotted numbers" in out


def test_expert_md_without_expert_type_is_an_error(tmp_path):
    write_skill(tmp_path, "alpha", expert=True)
    code, out = run(tmp_path)
    assert code == 1
    assert "EXPERT.md" in out and "metadata.type" in out


def test_expert_type_without_expert_md_is_an_error(tmp_path):
    write_skill(tmp_path, "alpha", extra="  type: [skill, expert]\n")
    code, out = run(tmp_path)
    assert code == 1
    assert "EXPERT.md" in out and "metadata.type" in out


def test_expert_md_with_expert_type_passes(tmp_path):
    write_skill(tmp_path, "alpha", extra="  type: [skill, expert]\n", expert=True)
    code, out = run(tmp_path)
    assert code == 0, out


# --- version bump against a base ref ---------------------------------------


def test_changed_skill_without_version_bump_is_an_error(tmp_path):
    repo_with_main(tmp_path)
    (tmp_path / "skills" / "alpha" / "references" / "guide.md").write_text("v2\n")
    git(tmp_path, "commit", "-q", "-am", "edit reference")
    code, out = run(tmp_path, "--base", "main")
    assert code == 1
    assert "alpha" in out and "bump metadata.version" in out


def test_changed_skill_with_version_bump_passes(tmp_path):
    repo_with_main(tmp_path)
    (tmp_path / "skills" / "alpha" / "references" / "guide.md").write_text("v2\n")
    write_skill(tmp_path, "alpha", version="'1.0.1'")
    git(tmp_path, "commit", "-q", "-am", "edit + bump")
    code, out = run(tmp_path, "--base", "main")
    assert code == 0, out


def test_lower_version_than_base_is_an_error(tmp_path):
    repo_with_main(tmp_path)
    write_skill(tmp_path, "alpha", version="'0.9.0'")
    git(tmp_path, "commit", "-q", "-am", "regress")
    code, out = run(tmp_path, "--base", "main")
    assert code == 1
    assert "alpha" in out and "bump metadata.version" in out


def test_version_compare_is_numeric_not_lexical(tmp_path):
    repo_with_main(tmp_path)
    write_skill(tmp_path, "alpha", version="'1.0.10'")
    git(tmp_path, "commit", "-q", "-am", "bump to 1.0.10")
    git(tmp_path, "branch", "-f", "main", "HEAD")
    write_skill(tmp_path, "alpha", version="'1.0.9'")
    git(tmp_path, "commit", "-q", "-am", "1.0.9 is lower than 1.0.10")
    code, out = run(tmp_path, "--base", "main")
    assert code == 1
    assert "bump metadata.version" in out


def test_new_skill_needs_no_bump(tmp_path):
    repo_with_main(tmp_path)
    write_skill(tmp_path, "beta")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "new skill")
    code, out = run(tmp_path, "--base", "main")
    assert code == 0, out


def test_untouched_skill_needs_no_bump(tmp_path):
    repo_with_main(tmp_path)
    (tmp_path / "skills" / "README.md").write_text("catalog v2\n")
    git(tmp_path, "commit", "-q", "-am", "catalog only")
    code, out = run(tmp_path, "--base", "main")
    assert code == 0, out


def test_uncommitted_change_without_bump_is_an_error(tmp_path):
    repo_with_main(tmp_path)
    (tmp_path / "skills" / "alpha" / "references" / "guide.md").write_text("v2\n")
    code, out = run(tmp_path, "--base", "main")
    assert code == 1
    assert "bump metadata.version" in out


def test_unquoted_version_is_an_error(tmp_path):
    # YAML reads an unquoted 1.10 as the float 1.1, which hides the real version.
    write_skill(tmp_path, "alpha", version="1.10")
    code, out = run(tmp_path)
    assert code == 1
    assert "metadata.version" in out and "quoted" in out


def test_changed_skill_with_non_ascii_directory_name_still_needs_a_bump(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    write_skill(tmp_path, "skíll")
    (tmp_path / "skills" / "skíll" / "notes.md").write_text("v1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "switch", "-q", "-c", "feature")
    (tmp_path / "skills" / "skíll" / "notes.md").write_text("v2\n")
    git(tmp_path, "commit", "-q", "-am", "edit")
    code, out = run(tmp_path, "--base", "main")
    assert code == 1
    assert "bump metadata.version" in out
