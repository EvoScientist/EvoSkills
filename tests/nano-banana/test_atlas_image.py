"""Tests for skills/nano-banana/scripts/atlas_image.py.

urllib is replaced by a recorder, so nothing touches the network and neither an
API key nor Pillow is needed.

Run from the repository root:
    pytest tests/nano-banana -q
"""

import io
import urllib.request
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

    def fake_urlopen(request, timeout=None, redirects="none"):
        requests.append(request)
        return _json_response(answers.pop(0))

    monkeypatch.setattr(atlas_image, "_urlopen", fake_urlopen)
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
        {
            "code": 200,
            "data": {"status": "completed", "outputs": ["https://example.test/a.png"]},
        }
    )
    saved = []
    monkeypatch.setattr(
        atlas_image, "_save_png", lambda url, path: saved.append((url, path)) or path
    )

    result = atlas_image.generate_image(
        "a slide",
        str(tmp_path / "out.png"),
        atlas_image.DEFAULT_GENERATE_MODEL,
        api_key="k",
    )

    assert result == str(tmp_path / "out.png")
    assert saved == [("https://example.test/a.png", str(tmp_path / "out.png"))]
    assert [r.get_method() for r in requests] == ["POST", "GET", "GET"]
    assert requests[0].full_url.endswith(atlas_image.GENERATE_PATH)
    assert all(
        r.full_url.endswith(f"{atlas_image.PREDICTION_PATH}/pred-1")
        for r in requests[1:]
    )
    body = json.loads(requests[0].data)
    assert body["model"] == atlas_image.DEFAULT_GENERATE_MODEL
    assert body["prompt"] == "a slide"
    assert all(r.get_header("User-agent") == atlas_image.USER_AGENT for r in requests)


def test_failed_prediction_raises_with_the_provider_message(recorded, tmp_path):
    requests, answers = recorded
    answers.append({"code": 200, "data": {"id": "pred-1", "status": "processing"}})
    answers.append(
        {"code": 200, "data": {"status": "failed", "error": "synthetic failure"}}
    )

    with pytest.raises(RuntimeError, match="synthetic failure"):
        atlas_image.generate_image(
            "a slide",
            str(tmp_path / "out.png"),
            atlas_image.DEFAULT_GENERATE_MODEL,
            api_key="k",
        )


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("ATLASCLOUD_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ATLASCLOUD_API_KEY"):
        atlas_image._api_key(None)


# --- the key never reaches the output --------------------------------------


def test_key_with_control_characters_is_rejected_without_echoing_it():
    with pytest.raises(RuntimeError) as info:
        atlas_image._api_key("abc\ndef")
    assert "abc" not in str(info.value)


def test_key_surrounding_whitespace_is_dropped():
    assert atlas_image._api_key("  synthetic-key \n") == "synthetic-key"


def test_provider_error_message_does_not_echo_the_key(recorded):
    requests, answers = recorded
    answers.append({"code": 400, "message": "key synthetic-key-123 was rejected"})
    with pytest.raises(RuntimeError) as info:
        atlas_image._json_request("https://api.atlascloud.ai/x", "synthetic-key-123")
    assert "synthetic-key-123" not in str(info.value)
    assert "rejected" in str(info.value)


def test_failed_prediction_message_does_not_echo_the_key(recorded, tmp_path):
    requests, answers = recorded
    answers.append({"code": 200, "data": {"id": "pred-1", "status": "processing"}})
    answers.append(
        {
            "code": 200,
            "data": {"status": "failed", "error": "key synthetic-key-123 rejected"},
        }
    )
    with pytest.raises(RuntimeError) as info:
        atlas_image.generate_image(
            "a slide",
            str(tmp_path / "out.png"),
            atlas_image.DEFAULT_GENERATE_MODEL,
            api_key="synthetic-key-123",
        )
    assert "synthetic-key-123" not in str(info.value)
    assert "rejected" in str(info.value)


# --- redirects -------------------------------------------------------------


def _redirect(policy, target):
    request = urllib.request.Request("https://api.atlascloud.ai/x")
    return policy.redirect_request(request, None, 302, "Found", {}, target)


def test_api_requests_never_follow_a_redirect():
    policy = atlas_image._RedirectPolicy(allow_https=False)
    assert _redirect(policy, "https://api.atlascloud.ai/y") is None
    assert _redirect(policy, "http://api.atlascloud.ai/y") is None


def test_downloads_follow_https_redirects_only():
    policy = atlas_image._RedirectPolicy(allow_https=True)
    assert _redirect(policy, "http://cdn.example.test/a.png") is None
    followed = _redirect(policy, "https://cdn.example.test/a.png")
    assert (
        followed is not None and followed.full_url == "https://cdn.example.test/a.png"
    )


# --- files on disk ---------------------------------------------------------


@pytest.fixture
def fake_pillow(monkeypatch):
    import types

    class _Opened:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def save(self, destination, format=None):
            Path(destination).write_bytes(b"png")

    image = types.ModuleType("PIL.Image")
    image.open = _Opened
    pil = types.ModuleType("PIL")
    pil.Image = image
    monkeypatch.setitem(sys.modules, "PIL", pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", image)


def test_download_leaves_other_files_alone_and_cleans_its_own(
    monkeypatch, tmp_path, fake_pillow
):
    monkeypatch.setattr(
        atlas_image,
        "_urlopen",
        lambda request, timeout=None, redirects="none": _Response(b"image-bytes"),
    )
    bystander = tmp_path / "out.png.download"
    bystander.write_text("keep me", encoding="utf-8")

    atlas_image._save_png("https://cdn.example.test/a.png", str(tmp_path / "out.png"))

    assert (tmp_path / "out.png").read_bytes() == b"png"
    assert bystander.read_text(encoding="utf-8") == "keep me"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.png", "out.png.download"]


def test_upload_filename_is_sanitized_in_the_multipart_body(recorded, tmp_path):
    requests, answers = recorded
    source = tmp_path / 'odd "name".png'
    source.write_bytes(b"img")
    answers.append({"code": 200, "data": {"download_url": "https://u.example.test/x"}})

    atlas_image.upload_media(str(source), api_key="k")

    body = requests[0].data
    assert b'filename="odd__name_.png"' in body
    assert b'"name"' not in body
