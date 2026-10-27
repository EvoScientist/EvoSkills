"""Tests for skills/nano-banana/scripts/edit_slide.py.

Run from the repository root (needs pytest and python-dotenv):
    pytest tests/nano-banana -q
"""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "nano-banana" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import edit_slide  # noqa: E402


def run_main(monkeypatch, tmp_path, result):
    monkeypatch.setattr(edit_slide, "edit_slide", lambda *args, **kwargs: result)
    monkeypatch.setattr(edit_slide, "check_dependencies", lambda provider: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["edit_slide.py", "--input", str(tmp_path / "a.png"), "--instruction", "x"],
    )
    return edit_slide.main()


def test_main_exits_one_when_the_edit_fails(monkeypatch, tmp_path):
    with pytest.raises(SystemExit) as info:
        run_main(monkeypatch, tmp_path, None)
    assert info.value.code == 1


def test_main_returns_normally_when_the_edit_succeeds(monkeypatch, tmp_path):
    assert run_main(monkeypatch, tmp_path, str(tmp_path / "a.png")) is None


def test_missing_library_is_reported_before_any_request(monkeypatch, capsys):
    real_import = __import__

    def without_pillow(name, *args, **kwargs):
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError("No module named 'PIL'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", without_pillow)
    with pytest.raises(SystemExit) as info:
        edit_slide.check_dependencies("atlas")
    assert info.value.code == 1
    assert "pillow" in capsys.readouterr().err
