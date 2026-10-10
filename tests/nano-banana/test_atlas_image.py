"""Tests for skills/nano-banana/scripts/atlas_image.py.

urllib is replaced by a recorder, so nothing touches the network and neither an
API key nor Pillow is needed.

Run from the repository root:
    pytest tests/nano-banana -q
"""

import io
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "nano-banana" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import atlas_image  # noqa: E402


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _json_response(payload):
    return _Response(json.dumps(payload).encode("utf-8"))


@pytest.fixture
def recorded(monkeypatch):
    """Record every urllib request and answer from a queue of JSON payloads."""
    requests = []
    answers = []

    def fake_urlopen(request, timeout=None):
        requests.append(request)
        return _json_response(answers.pop(0))

    monkeypatch.setattr(atlas_image.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(atlas_image, "POLL_INTERVAL_SECONDS", 0)
    return requests, answers


def test_requests_send_their_own_user_agent(recorded):
    """Cloudflare answers HTTP 403 to urllib's default Python-urllib agent."""
    requests, answers = recorded
    answers.append({"code": 200, "data": {}})

    atlas_image._json_request("https://api.atlascloud.ai/x", "synthetic-key")

    agent = requests[0].get_header("User-agent")
    assert agent == atlas_image.USER_AGENT
    assert "python-urllib" not in agent.lower()
    assert requests[0].get_header("Authorization") == "Bearer synthetic-key"


def test_generate_submits_once_then_polls_prediction(recorded, monkeypatch, tmp_path):
    requests, answers = recorded
    answers.append({"code": 200, "data": {"id": "pred-1", "status": "processing"}})
    answers.append({"code": 200, "data": {"status": "processing"}})
    answers.append(
        {"code": 200, "data": {"status": "completed", "outputs": ["https://example.test/a.png"]}}
    )
    saved = []
    monkeypatch.setattr(
        atlas_image, "_save_png", lambda url, path: saved.append((url, path)) or path
    )

    result = atlas_image.generate_image(
        "a slide", str(tmp_path / "out.png"), atlas_image.DEFAULT_GENERATE_MODEL, api_key="k"
    )

    assert result == str(tmp_path / "out.png")
    assert saved == [("https://example.test/a.png", str(tmp_path / "out.png"))]
    assert [r.get_method() for r in requests] == ["POST", "GET", "GET"]
    body = json.loads(requests[0].data)
    assert body["model"] == atlas_image.DEFAULT_GENERATE_MODEL
    assert body["prompt"] == "a slide"
    assert all(r.get_header("User-agent") == atlas_image.USER_AGENT for r in requests)


def test_failed_prediction_raises_with_the_provider_message(recorded, tmp_path):
    requests, answers = recorded
    answers.append({"code": 200, "data": {"id": "pred-1", "status": "processing"}})
    answers.append({"code": 200, "data": {"status": "failed", "error": "synthetic failure"}})

    with pytest.raises(RuntimeError, match="synthetic failure"):
        atlas_image.generate_image(
            "a slide", str(tmp_path / "out.png"), atlas_image.DEFAULT_GENERATE_MODEL, api_key="k"
        )


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("ATLASCLOUD_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ATLASCLOUD_API_KEY"):
        atlas_image._api_key(None)
