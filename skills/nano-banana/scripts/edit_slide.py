#!/usr/bin/env python3
"""
Slide Editor - Edit existing PPT slide images using Gemini or Atlas Cloud.

Takes an existing slide image and a text instruction, generates an edited
version using the selected provider's image editing capability.
"""

import argparse
import os
import sys
from typing import Optional

from dotenv import load_dotenv


# =============================================================================
# Constants
# =============================================================================

DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-3-pro-image-preview"
ATLAS_MODEL = "google/nano-banana-2-lite/edit"

SUPPORTED_MODELS = [
    "gemini-3-pro-image-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-2.5-flash-image",
]


def resolve_model(provider: str, model: Optional[str]) -> str:
    """Resolve a provider-specific model and reject incompatible choices."""
    if provider == "atlas":
        selected_model = model or ATLAS_MODEL
        if selected_model != ATLAS_MODEL:
            raise ValueError(f"Atlas provider requires model {ATLAS_MODEL}")
        return selected_model

    selected_model = model or DEFAULT_MODEL
    if selected_model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported Gemini model: {selected_model}")
    return selected_model


# =============================================================================
# API Client
# =============================================================================


def get_gemini_client(api_key: Optional[str] = None):
    """Initialize Gemini API client. Priority: arg > GOOGLE_API_KEY > GEMINI_API_KEY."""
    try:
        from google import genai
    except ImportError:
        print("Error: google-genai library not installed")
        print("Please run: pip install google-genai")
        sys.exit(1)

    key = (
        api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    )
    if not key:
        print("Error: No API key provided.")
        print("Options: --api-key <key> | GOOGLE_API_KEY env | GEMINI_API_KEY env")
        sys.exit(1)

    return genai.Client(api_key=key)


# =============================================================================
# Image Editing
# =============================================================================


def edit_slide(
    input_path: str,
    instruction: str,
    output_path: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = DEFAULT_PROVIDER,
) -> Optional[str]:
    """
    Edit a slide image based on text instruction.

    Args:
        input_path: Path to the original slide image.
        instruction: Text instruction describing the edit.
        output_path: Path to save the edited image.
        model: Provider model name.
        api_key: Explicit API key (optional).
        provider: Image provider (gemini or atlas).

    Returns:
        Path to saved edited image, or None if failed.
    """
    try:
        model = resolve_model(provider, model)
        if provider == "atlas":
            from atlas_image import generate_image

            result = generate_image(
                instruction,
                output_path,
                model,
                input_path=input_path,
                api_key=api_key,
            )
            print(f"OK: {result}")
            return result

        from google.genai import types
        from PIL import Image

        client = get_gemini_client(api_key)
        original = Image.open(input_path)

        response = client.models.generate_content(
            model=model,
            contents=[instruction, original],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size="2K",
                ),
            ),
        )

        for part in response.parts:
            if part.inline_data is not None:
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                # Save raw image first, then re-save as true PNG
                tmp_path = output_path + ".tmp"
                part.as_image().save(tmp_path)
                Image.open(tmp_path).save(output_path, format="PNG")
                os.remove(tmp_path)
                print(f"OK: {output_path}")
                return output_path

        print("FAIL: No image data returned")
        return None

    except Exception as e:
        print(f"FAIL: {e}")
        return None


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Edit PPT slide images using Gemini or Atlas Cloud",
        epilog="""
Example usage:
  python skills/nano-banana/scripts/edit_slide.py \\
    --input ppt_output/images/slide-01.png \\
    --instruction "Remove the footer text at the bottom" \\
    --output ppt_output/images/slide-01.png
""",
    )
    parser.add_argument("--input", required=True, help="Path to original slide image")
    parser.add_argument("--instruction", required=True, help="Edit instruction text")
    parser.add_argument("--output", help="Output path (default: overwrite input)")
    parser.add_argument(
        "--provider",
        choices=["gemini", "atlas"],
        default=DEFAULT_PROVIDER,
    )
    parser.add_argument(
        "--model", help="Image editing model (default depends on provider)"
    )
    parser.add_argument("--api-key", help="Provider API key")

    args = parser.parse_args()
    load_dotenv(override=True)
    try:
        args.model = resolve_model(args.provider, args.model)
    except ValueError as exc:
        parser.error(str(exc))

    output = args.output or args.input
    edit_slide(
        args.input,
        args.instruction,
        output,
        args.model,
        args.api_key,
        args.provider,
    )


if __name__ == "__main__":
    main()
