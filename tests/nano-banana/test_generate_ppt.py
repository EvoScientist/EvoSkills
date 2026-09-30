"""Tests for skills/nano-banana/scripts/generate_ppt.py.

The Gemini client and Pillow are replaced by small stand-ins on PYTHONPATH,
so the script runs end to end without a network call or an API key.

Run from the repository root (needs pytest and python-dotenv):
    pytest tests/nano-banana -q
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "nano-banana"
SCRIPT = SKILL / "scripts" / "generate_ppt.py"

FAKE_GENAI = """\
from . import types


class _Image:
    def save(self, path, **kwargs):
        with open(path, "wb") as f:
            f.write(b"image")


class _Part:
    inline_data = object()

    def as_image(self):
        return _Image()


class _Response:
    def __init__(self, parts):
        self.parts = parts


class _Models:
    def generate_content(self, model, contents, config):
        # A slide whose content carries the marker gets no image back.
        return _Response([] if "NO_IMAGE_FOR_THIS_SLIDE" in contents else [_Part()])


class Client:
    def __init__(self, api_key=None):
        self.models = _Models()
"""

FAKE_TYPES = """\
class GenerateContentConfig:
    def __init__(self, **kwargs):
        pass


class ImageConfig:
    def __init__(self, **kwargs):
        pass
"""

FAKE_PIL_IMAGE = """\
import builtins


class _Opened:
    def save(self, path, format=None):
        with builtins.open(path, "wb") as f:
            f.write(b"png")


def open(path):
    return _Opened()
"""


@pytest.fixture
def fake_modules(tmp_path):
    root = tmp_path / "fake"
    (root / "google" / "genai").mkdir(parents=True)
    (root / "PIL").mkdir()
    (root / "google" / "__init__.py").write_text("", encoding="utf-8")
    (root / "google" / "genai" / "__init__.py").write_text(FAKE_GENAI, encoding="utf-8")
    (root / "google" / "genai" / "types.py").write_text(FAKE_TYPES, encoding="utf-8")
    (root / "PIL" / "__init__.py").write_text("", encoding="utf-8")
    (root / "PIL" / "Image.py").write_text(FAKE_PIL_IMAGE, encoding="utf-8")
    return root


def generate(tmp_path, fake_modules, contents):
    plan = {
        "title": "Deck",
        "slides": [
            {"slide_number": i, "page_type": "content", "content": text}
            for i, text in enumerate(contents, start=1)
        ],
    }
    (tmp_path / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    out = tmp_path / "out"
    env = dict(
        os.environ, PYTHONPATH=str(fake_modules), GOOGLE_API_KEY="not-a-real-key"
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--plan",
            str(tmp_path / "plan.json"),
            "--style",
            str(SKILL / "styles" / "lineal-color.md"),
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    return proc, out


def test_all_slides_generated_exits_zero(tmp_path, fake_modules):
    proc, out = generate(tmp_path, fake_modules, ["first", "second"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "2/2 slides generated" in proc.stdout
    assert sorted(p.name for p in (out / "images").iterdir()) == [
        "slide-01.png",
        "slide-02.png",
    ]


def test_no_slide_generated_is_a_failure(tmp_path, fake_modules):
    marker = "NO_IMAGE_FOR_THIS_SLIDE"
    proc, _ = generate(tmp_path, fake_modules, [marker, marker])
    assert proc.returncode == 1
    assert "0/2 slides generated" in proc.stdout


def test_partly_generated_deck_is_reported_with_its_missing_slides(
    tmp_path, fake_modules
):
    proc, out = generate(
        tmp_path, fake_modules, ["first", "NO_IMAGE_FOR_THIS_SLIDE", "third"]
    )
    assert proc.returncode == 2
    assert "2/3 slides generated" in proc.stdout
    assert "Failed slides: 2" in proc.stderr
    # The deck that did come out is still written for review and editing.
    assert (out / "images" / "slide-01.png").exists()
    assert (out / "images" / "slide-03.png").exists()
    assert (out / "index.html").exists()
    prompts = json.loads((out / "prompts.json").read_text(encoding="utf-8"))
    assert [s["image_path"] is None for s in prompts["slides"]] == [False, True, False]


def test_plan_without_slides_is_a_failure(tmp_path, fake_modules):
    proc, _ = generate(tmp_path, fake_modules, [])
    assert proc.returncode == 1
    assert "no slides" in (proc.stdout + proc.stderr).lower()


@pytest.mark.parametrize(
    "script", sorted((SKILL / "scripts").glob("*.py")), ids=lambda p: p.name
)
def test_usage_examples_use_skill_relative_paths(script):
    text = script.read_text(encoding="utf-8")
    assert "skills/nano-banana/" not in text
