"""Atlas Cloud image generation helpers for the nano-banana skill."""

import json
import mimetypes
import os
import re
import secrets
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional


API_BASE_URL = "https://api.atlascloud.ai"
GENERATE_PATH = "/api/v1/model/generateImage"
PREDICTION_PATH = "/api/v1/model/prediction"
UPLOAD_PATH = "/api/v1/model/uploadMedia"
DEFAULT_GENERATE_MODEL = "google/nano-banana-2-lite/text-to-image"
DEFAULT_EDIT_MODEL = "google/nano-banana-2-lite/edit"
POLL_INTERVAL_SECONDS = 3
MAX_POLLS = 60
# Atlas Cloud sits behind Cloudflare, which rejects urllib's default
# "Python-urllib" User-Agent with HTTP 403, so every request sends its own.
USER_AGENT = "evoskills-nano-banana/1.0"


class _RedirectPolicy(urllib.request.HTTPRedirectHandler):
    """Refuse redirects, or follow them only to an https:// target.

    API requests carry the Authorization header and are never redirected.
    Image downloads carry no credential and may follow a redirect as long
    as it stays on https.
    """

    def __init__(self, allow_https: bool) -> None:
        super().__init__()
        self.allow_https = allow_https

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not self.allow_https or not newurl.startswith("https://"):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENERS = {
    "none": urllib.request.build_opener(_RedirectPolicy(allow_https=False)),
    "https": urllib.request.build_opener(_RedirectPolicy(allow_https=True)),
}


def _urlopen(
    request: urllib.request.Request, timeout: int = 60, redirects: str = "none"
):
    """Open ``request`` under the named redirect policy."""
    return _OPENERS[redirects].open(request, timeout=timeout)


def _api_key(explicit_key: Optional[str]) -> str:
    key = (explicit_key or os.environ.get("ATLASCLOUD_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "No Atlas Cloud API key provided. Pass --api-key or set ATLASCLOUD_API_KEY."
        )
    # A key with a line break would make urllib echo the whole header in
    # its error; never let the key reach any message.
    if not key.isprintable() or any(c.isspace() for c in key):
        raise RuntimeError(
            "The Atlas Cloud API key contains whitespace or control characters."
        )
    return key


def _scrub(text: str, api_key: str) -> str:
    """Remove the key from text that will be printed."""
    return text.replace(api_key, "***") if api_key else text


def _json_request(
    url: str,
    api_key: str,
    method: str = "GET",
    body: Optional[bytes] = None,
    content_type: Optional[str] = None,
) -> Dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": USER_AGENT,
    }
    if content_type:
        headers["Content-Type"] = content_type

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with _urlopen(request, timeout=60, redirects="none") as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Atlas Cloud request failed with HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Atlas Cloud request failed: {_scrub(str(exc), api_key)}"
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Atlas Cloud returned an invalid response")
    if payload.get("code") not in (None, 0, 200):
        message = payload.get("message") or payload.get("msg") or "unknown error"
        raise RuntimeError(f"Atlas Cloud API error: {_scrub(str(message), api_key)}")
    return payload


def upload_media(path: str, api_key: Optional[str] = None) -> str:
    """Upload a local image once and return its temporary HTTPS URL."""
    source = Path(path)
    if not source.is_file():
        raise RuntimeError(f"Input image not found: {path}")

    key = _api_key(api_key)
    boundary = f"----evoskills-{secrets.token_hex(16)}"
    content_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    # The name goes into a multipart header; keep it to characters that
    # cannot break or extend that header.
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", source.name) or "upload"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'
            ).encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            source.read_bytes(),
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    payload = _json_request(
        f"{API_BASE_URL}{UPLOAD_PATH}",
        key,
        method="POST",
        body=body,
        content_type=f"multipart/form-data; boundary={boundary}",
    )
    url = payload.get("data", {}).get("download_url")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError("Atlas Cloud upload did not return an HTTPS URL")
    return url


def _output_url(data: Dict[str, Any]) -> Optional[str]:
    outputs = data.get("outputs")
    if isinstance(outputs, list) and outputs and isinstance(outputs[0], str):
        return outputs[0]
    output = data.get("output")
    if isinstance(output, str):
        return output
    return None


def _save_png(url: str, output_path: str) -> str:
    if not url.startswith("https://"):
        raise RuntimeError("Atlas Cloud returned a non-HTTPS image URL")

    from PIL import Image

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # A fresh temporary name, so nothing that already exists is touched.
    handle = tempfile.NamedTemporaryFile(
        dir=destination.parent,
        prefix=destination.name + ".",
        suffix=".download",
        delete=False,
    )
    handle.close()
    temporary = Path(handle.name)
    try:
        download = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with _urlopen(download, timeout=60, redirects="https") as response:
            temporary.write_bytes(response.read())
        with Image.open(temporary) as image:
            image.save(destination, format="PNG")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Unable to save Atlas Cloud image: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return str(destination)


def generate_image(
    prompt: str,
    output_path: str,
    model: str,
    input_path: Optional[str] = None,
    api_key: Optional[str] = None,
    max_polls: int = MAX_POLLS,
) -> str:
    """Submit one generation request, then poll only the prediction endpoint."""
    key = _api_key(api_key)
    request_data: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "resolution": "1k",
    }
    if input_path:
        request_data["images"] = [upload_media(input_path, key)]

    # Generation POSTs are intentionally never retried.
    submitted = _json_request(
        f"{API_BASE_URL}{GENERATE_PATH}",
        key,
        method="POST",
        body=json.dumps(request_data).encode("utf-8"),
        content_type="application/json",
    )
    data = submitted.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Atlas Cloud generation response has no data object")

    output_url = _output_url(data)
    if data.get("status") == "completed" and output_url:
        return _save_png(output_url, output_path)

    prediction_id = data.get("id")
    if not isinstance(prediction_id, str) or not prediction_id:
        raise RuntimeError("Atlas Cloud generation response has no prediction id")

    for _ in range(max_polls):
        time.sleep(POLL_INTERVAL_SECONDS)
        prediction = _json_request(
            f"{API_BASE_URL}{PREDICTION_PATH}/{prediction_id}", key
        )
        prediction_data = prediction.get("data")
        if not isinstance(prediction_data, dict):
            raise RuntimeError("Atlas Cloud prediction response has no data object")

        status = prediction_data.get("status")
        if status == "completed":
            output_url = _output_url(prediction_data)
            if not output_url:
                raise RuntimeError("Atlas Cloud completed without an image URL")
            return _save_png(output_url, output_path)
        if status == "failed":
            message = prediction_data.get("error") or "generation failed"
            raise RuntimeError(
                f"Atlas Cloud generation failed: {_scrub(str(message), key)}"
            )

    raise RuntimeError("Atlas Cloud generation timed out while polling")
