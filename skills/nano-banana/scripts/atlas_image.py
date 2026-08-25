"""Atlas Cloud image generation helpers for the nano-banana skill."""

import json
import mimetypes
import os
import secrets
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


def _api_key(explicit_key: Optional[str]) -> str:
    key = explicit_key or os.environ.get("ATLASCLOUD_API_KEY")
    if not key:
        raise RuntimeError(
            "No Atlas Cloud API key provided. Pass --api-key or set ATLASCLOUD_API_KEY."
        )
    return key


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
    }
    if content_type:
        headers["Content-Type"] = content_type

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Atlas Cloud request failed with HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Atlas Cloud request failed: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Atlas Cloud returned an invalid response")
    if payload.get("code") not in (None, 0, 200):
        message = payload.get("message") or payload.get("msg") or "unknown error"
        raise RuntimeError(f"Atlas Cloud API error: {message}")
    return payload


def upload_media(path: str, api_key: Optional[str] = None) -> str:
    """Upload a local image once and return its temporary HTTPS URL."""
    source = Path(path)
    if not source.is_file():
        raise RuntimeError(f"Input image not found: {path}")

    key = _api_key(api_key)
    boundary = f"----evoskills-{secrets.token_hex(16)}"
    content_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="file"; filename="{source.name}"\r\n'
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
    temporary = destination.with_suffix(destination.suffix + ".download")
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
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
            raise RuntimeError(f"Atlas Cloud generation failed: {message}")

    raise RuntimeError("Atlas Cloud generation timed out while polling")
