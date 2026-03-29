#!/usr/bin/env python3
"""
Nano Banana - Generate presentation slide images using Google Gemini API.

This script generates presentation slide images based on a slide plan and style template,
then creates an HTML viewer for playback.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


# =============================================================================
# Constants
# =============================================================================

DEFAULT_RESOLUTION = "2K"
DEFAULT_MODEL = "gemini-3-pro-image-preview"
OUTPUT_BASE_DIR = "ppt_output"

SUPPORTED_MODELS = [
    "gemini-3-pro-image-preview",  # Best quality, moderate speed
    "gemini-3.1-flash-image-preview",  # Fast, good quality
    "gemini-2.5-flash-image",  # Fastest, basic quality
]

# Skill root directory (nano-banana/)
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_PATH = str(SKILL_ROOT / "templates" / "viewer.html")


# =============================================================================
# Environment Configuration
# =============================================================================


def find_and_load_env() -> bool:
    """
    Load .env file from current working directory if present.

    When running inside EvoScientist, API keys are already set in the
    environment via apply_config_to_env(). This function only loads a
    local .env file as a convenience for standalone usage.

    Returns:
        True always (environment is ready either way).
    """
    load_dotenv(override=True)
    return True


# =============================================================================
# Style Template
# =============================================================================


def load_style_template(style_path: str) -> dict:
    """
    Load and parse style template file.

    Extracts:
    - base: content of '## 基础提示词模板' section
    - cover: per-page template for cover slides
    - content: per-page template for content slides
    - data: per-page template for data/summary slides

    Args:
        style_path: Path to the style template markdown file.

    Returns:
        Dict with keys 'base', 'cover', 'content', 'data'.
    """
    with open(style_path, "r", encoding="utf-8") as f:
        raw = f.read()

    def extract_section(text: str, header: str) -> str:
        """Extract text between a ## header and the next ## header."""
        start = text.find(f"\n{header}\n")
        if start == -1:
            start = text.find(f"\n{header}")
        if start == -1:
            return ""
        start += len(header) + 1
        end = text.find("\n## ", start)
        return text[start:end].strip() if end != -1 else text[start:].strip()

    def extract_subsection(text: str, header: str) -> str:
        """Extract text between a ### header and the next ### or ## header."""
        start = text.find(f"\n{header}\n")
        if start == -1:
            start = text.find(f"\n{header}")
        if start == -1:
            return ""
        start += len(header) + 1
        end_candidates = [text.find("\n### ", start), text.find("\n## ", start)]
        end = (
            min(e for e in end_candidates if e != -1)
            if any(e != -1 for e in end_candidates)
            else -1
        )
        return text[start:end].strip() if end != -1 else text[start:].strip()

    def strip_code_fence(text: str) -> str:
        """Remove markdown code fences from a block."""
        lines = text.strip().splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    # Support both English and Chinese section headers
    base = extract_section(raw, "## Base Prompt") or extract_section(
        raw, "## 基础提示词模板"
    )

    examples_section = extract_section(raw, "## Examples") or extract_section(
        raw, "## 使用示例"
    )
    cover_raw = extract_subsection(examples_section, "### Cover") or extract_subsection(
        examples_section, "### 生成封面页"
    )
    content_raw = extract_subsection(
        examples_section, "### Content"
    ) or extract_subsection(examples_section, "### 生成内容页")
    data_raw = extract_subsection(examples_section, "### Data") or extract_subsection(
        examples_section, "### 生成数据页"
    )

    cover = strip_code_fence(cover_raw) if cover_raw else ""
    content = strip_code_fence(content_raw) if content_raw else ""
    data = strip_code_fence(data_raw) if data_raw else ""

    # Fallback: if no per-type templates found, use page-type template descriptions
    if not cover:
        cover_desc = extract_subsection(
            raw, "### Cover Template"
        ) or extract_subsection(raw, "### 封面页模板")
        cover = f"{base}\n\nPlease generate a cover slide.\n{cover_desc}"
    if not content:
        content_desc = extract_subsection(
            raw, "### Content Template"
        ) or extract_subsection(raw, "### 内容页模板")
        content = f"{base}\n\nPlease generate a content slide.\n{content_desc}"
    if not data:
        data_desc = extract_subsection(raw, "### Data Template") or extract_subsection(
            raw, "### 数据页模板"
        )
        data = f"{base}\n\nPlease generate a data/summary slide.\n{data_desc}"

    return {"base": base, "cover": cover, "content": content, "data": data}


# =============================================================================
# Prompt Generation
# =============================================================================


def generate_prompt(
    style_template: dict,
    page_type: str,
    content_text: str,
    slide_number: int,
    total_slides: int,
) -> str:
    """
    Generate a prompt for a single slide using templates from the style file.

    Args:
        style_template: Dict with 'base', 'cover', 'content', 'data' templates.
        page_type: Type of page (cover, data, content).
        content_text: Text content for the slide.
        slide_number: Current slide number (1-indexed).
        total_slides: Total number of slides.

    Returns:
        Complete prompt string for image generation.
    """
    is_cover = page_type == "cover" or slide_number == 1
    is_data = page_type == "data"

    if is_cover:
        template = style_template.get("cover", "")
    elif is_data:
        template = style_template.get("data", "")
    else:
        template = style_template.get("content", "")

    base = style_template.get("base", "")

    # Replace placeholder tokens in the template
    prompt = template.replace("{Base Prompt}", base)
    prompt = prompt.replace("{基础提示词模板}", base)
    prompt = prompt.replace("[Title]", content_text)
    prompt = prompt.replace("[Content]", content_text)
    prompt = prompt.replace("[标题文本]", content_text)
    prompt = prompt.replace("[内容文本]", content_text)

    # If the template didn't embed the base, prepend it
    if base and base not in prompt:
        prompt = f"{base}\n\n{prompt}"

    # Append the actual slide content if not already present
    if content_text not in prompt:
        prompt = f"{prompt}\n\nSlide content:\n{content_text}"

    return prompt


# =============================================================================
# Image Generation
# =============================================================================


def get_gemini_client(api_key: Optional[str] = None):
    """
    Initialize and return Gemini API client.

    API key priority: --api-key arg > GOOGLE_API_KEY env > GEMINI_API_KEY env.

    Args:
        api_key: Explicit API key (from --api-key argument).

    Returns:
        Configured genai.Client instance.

    Raises:
        SystemExit: If google-genai is not installed or API key is missing.
    """
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
        print("Options:")
        print("  1. Pass --api-key <key>")
        print("  2. EvoSci config set google_api_key <key>")
        print("  3. export GOOGLE_API_KEY='your-api-key'")
        sys.exit(1)

    return genai.Client(api_key=key)


def generate_slide(
    prompt: str,
    slide_number: int,
    total_slides: int,
    output_dir: str,
    resolution: str = DEFAULT_RESOLUTION,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> Optional[str]:
    """
    Generate a single PPT slide image using Gemini API.

    Args:
        prompt: The generation prompt.
        slide_number: Slide number for filename.
        total_slides: Total number of slides (for progress display).
        output_dir: Output directory path.
        resolution: Image resolution (2K or 4K).
        api_key: Explicit API key (optional).
        model: Gemini model name.

    Returns:
        Path to saved image, or None if generation failed.
    """
    from google.genai import types

    try:
        client = get_gemini_client(api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size=resolution,
                ),
            ),
        )

        for part in response.parts:
            if part.inline_data is not None:
                from PIL import Image

                image_path = os.path.join(
                    output_dir, "images", f"slide-{slide_number:02d}.png"
                )
                # Save raw image first, then re-save as true PNG
                tmp_path = image_path + ".tmp"
                part.as_image().save(tmp_path)
                Image.open(tmp_path).save(image_path, format="PNG")
                os.remove(tmp_path)
                print(f"[{slide_number}/{total_slides}] OK: {image_path}")
                return image_path

        print(f"[{slide_number}/{total_slides}] FAIL: No image data")
        return None

    except Exception as e:
        print(f"[{slide_number}/{total_slides}] FAIL: {e}")
        return None


# =============================================================================
# Output Generation
# =============================================================================


def generate_viewer_html(
    output_dir: str,
    slide_count: int,
    template_path: str,
) -> str:
    """
    Generate HTML viewer for slides playback.

    Args:
        output_dir: Output directory path.
        slide_count: Total number of slides.
        template_path: Path to HTML template.

    Returns:
        Path to generated HTML file.
    """
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    # Generate image list
    slides_list = [f"'images/slide-{i:02d}.png'" for i in range(1, slide_count + 1)]

    # Replace placeholders
    html_content = html_template.replace(
        "/* IMAGE_LIST_PLACEHOLDER */",
        ",\n            ".join(slides_list),
    )
    html_content = html_content.replace(
        "/* PLAN_PATH_PLACEHOLDER */",
        os.path.basename(output_dir),
    )

    html_path = os.path.join(output_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Viewer: {html_path}")
    return html_path


def save_prompts(output_dir: str, prompts_data: Dict[str, Any]) -> str:
    """
    Save all prompts to JSON file.

    Args:
        output_dir: Output directory path.
        prompts_data: Dictionary containing all prompts and metadata.

    Returns:
        Path to saved JSON file.
    """
    prompts_path = os.path.join(output_dir, "prompts.json")
    with open(prompts_path, "w", encoding="utf-8") as f:
        json.dump(prompts_data, f, ensure_ascii=False, indent=2)
    print(f"Prompts: {prompts_path}")
    return prompts_path


# =============================================================================
# Main Entry Point
# =============================================================================


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Nano Banana - Generate slide images using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python skills/nano-banana/scripts/generate_ppt.py \\
    --plan slides_plan.json \\
    --style skills/nano-banana/styles/lineal-color.md \\
    --output ppt_output

Environment variables (checked in order):
  GOOGLE_API_KEY: Google AI API key (set by EvoScientist config)
  GEMINI_API_KEY: Fallback for standalone usage
""",
    )

    parser.add_argument(
        "--plan",
        required=True,
        help="Path to slides plan JSON file (generated by Skill)",
    )
    parser.add_argument(
        "--style",
        required=True,
        help="Path to style template file",
    )
    parser.add_argument(
        "--api-key",
        help="Google API key (overrides GOOGLE_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        choices=SUPPORTED_MODELS,
        default=DEFAULT_MODEL,
        help=f"Image generation model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--resolution",
        choices=["2K", "4K"],
        default=DEFAULT_RESOLUTION,
        help=f"Image resolution (default: {DEFAULT_RESOLUTION})",
    )
    parser.add_argument(
        "--output",
        help="Output directory path (default: outputs/TIMESTAMP)",
    )
    parser.add_argument(
        "--template",
        default=DEFAULT_TEMPLATE_PATH,
        help=f"HTML template path (default: {DEFAULT_TEMPLATE_PATH})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for slide generation (default: 1, max recommended: 5)",
    )

    return parser


def main() -> None:
    """Main entry point for PPT generation."""
    # Load environment variables
    find_and_load_env()

    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Load slides plan
    with open(args.plan, "r", encoding="utf-8") as f:
        slides_plan = json.load(f)

    # Load style template
    style_template = load_style_template(args.style)

    # Create output directory
    if args.output:
        output_dir = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"{OUTPUT_BASE_DIR}/{timestamp}"

    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

    slides = slides_plan["slides"]
    total_slides = len(slides)
    print(f"Generating {total_slides} slides to {output_dir}/")

    # Initialize prompts data
    prompts_data: Dict[str, Any] = {
        "metadata": {
            "title": slides_plan.get("title", "Untitled Presentation"),
            "total_slides": total_slides,
            "resolution": args.resolution,
            "style": args.style,
            "generated_at": datetime.now().isoformat(),
        },
        "slides": [],
    }

    # Prepare all slide tasks
    slide_tasks = []
    for slide_info in slides:
        slide_number = slide_info["slide_number"]
        page_type = slide_info.get("page_type", "content")
        content_text = slide_info["content"]
        prompt = generate_prompt(
            style_template,
            page_type,
            content_text,
            slide_number,
            total_slides,
        )
        slide_tasks.append(
            {
                "slide_number": slide_number,
                "page_type": page_type,
                "content": content_text,
                "prompt": prompt,
            }
        )

    # Generate slides (serial or parallel)
    workers = min(args.workers, len(slide_tasks))
    results = {}

    if workers > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        print(f"Using {workers} parallel workers")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    generate_slide,
                    task["prompt"],
                    task["slide_number"],
                    total_slides,
                    output_dir,
                    args.resolution,
                    args.api_key,
                    args.model,
                ): task["slide_number"]
                for task in slide_tasks
            }
            for future in as_completed(futures):
                num = futures[future]
                results[num] = future.result()
    else:
        for task in slide_tasks:
            results[task["slide_number"]] = generate_slide(
                task["prompt"],
                task["slide_number"],
                total_slides,
                output_dir,
                args.resolution,
                args.api_key,
                args.model,
            )

    # Record prompt data (in slide order)
    for task in slide_tasks:
        prompts_data["slides"].append(
            {
                "slide_number": task["slide_number"],
                "page_type": task["page_type"],
                "content": task["content"],
                "prompt": task["prompt"],
                "image_path": results.get(task["slide_number"]),
            }
        )

    # Save prompts
    save_prompts(output_dir, prompts_data)

    # Generate viewer HTML
    generate_viewer_html(output_dir, total_slides, args.template)

    failed = sum(1 for s in prompts_data["slides"] if s["image_path"] is None)
    print(
        f"Done. {total_slides - failed}/{total_slides} slides generated. Output: {output_dir}/"
    )


if __name__ == "__main__":
    main()
