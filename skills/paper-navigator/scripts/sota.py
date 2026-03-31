#!/usr/bin/env python3
"""Query top models by task via HuggingFace Models API.

Finds top models by task, sorted by downloads or likes.
For detailed benchmark scores, see:
https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
"""

import argparse
import json
import sys

import httpx

from utils import HF_API, hf_headers, request_with_retry

# Common HuggingFace pipeline tags (task categories)
PIPELINE_TAGS = [
    "text-generation",
    "text-classification",
    "token-classification",
    "question-answering",
    "summarization",
    "translation",
    "fill-mask",
    "text2text-generation",
    "feature-extraction",
    "image-classification",
    "object-detection",
    "image-segmentation",
    "image-to-text",
    "text-to-image",
    "text-to-video",
    "automatic-speech-recognition",
    "text-to-speech",
    "reinforcement-learning",
    "sentence-similarity",
    "zero-shot-classification",
    "table-question-answering",
]


def search_models(
    query: str,
    limit: int = 10,
    sort: str = "downloads",
    pipeline_tag: str | None = None,
) -> list[dict]:
    """Search HuggingFace models by query and/or pipeline tag."""
    params: dict = {"limit": min(limit, 100), "sort": sort}
    if pipeline_tag:
        params["pipeline_tag"] = pipeline_tag
    if query:
        params["search"] = query

    with httpx.Client() as client:
        data = request_with_retry(
            client, f"{HF_API}/models", params, hf_headers(), follow_redirects=True
        )
    return data if isinstance(data, list) else []


def list_tasks(query: str | None = None) -> list[str]:
    """List available pipeline tags (task categories), optionally filtered."""
    if query:
        q = query.lower()
        return [t for t in PIPELINE_TAGS if q in t]
    return PIPELINE_TAGS


def format_model(m: dict, idx: int) -> str:
    model_id = m.get("modelId", m.get("id", "Unknown"))
    downloads = m.get("downloads", 0)
    likes = m.get("likes", 0)
    pipeline = m.get("pipeline_tag", "")
    library = m.get("library_name", "")
    last_modified = (m.get("lastModified") or "")[:10]

    # Extract arXiv papers from tags
    tags = m.get("tags", [])
    papers = [t.replace("arxiv:", "") for t in tags if t.startswith("arxiv:")]
    paper_str = (
        f" | Papers: {', '.join(f'`{p}`' for p in papers[:3])}" if papers else ""
    )

    url = f"https://huggingface.co/{model_id}"

    return (
        f"{idx}. **{model_id}**\n"
        f"   \U0001f4e5 {downloads:,} downloads | \u2764\ufe0f {likes} likes | "
        f"{pipeline} | {library}\n"
        f"   Updated: {last_modified}{paper_str}\n"
        f"   {url}\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Query top models by task via HuggingFace",
        epilog="For detailed SOTA benchmarks, visit: "
        "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
    )
    parser.add_argument(
        "--task",
        "-t",
        required=True,
        help="Task name or pipeline tag (e.g. 'text-generation', 'machine translation')",
    )
    parser.add_argument(
        "--sort",
        "-s",
        choices=["downloads", "likes", "trending"],
        default="downloads",
        help="Sort order (default: downloads)",
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Max results (default 10)"
    )
    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="List available pipeline tags matching the query",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if args.list_tasks:
        tasks = list_tasks(args.task)
        if args.json:
            print(json.dumps(tasks, indent=2))
            return
        print(f'# Pipeline Tags matching: "{args.task}"\n')
        for i, t in enumerate(tasks, 1):
            print(f"{i}. `{t}`")
        if not tasks:
            print("No matching pipeline tags. Try a broader search term.")
        return

    # Check if task matches a pipeline tag exactly
    pipeline_tag = args.task if args.task in PIPELINE_TAGS else None
    search_query = args.task if not pipeline_tag else ""

    models = search_models(search_query, args.limit, args.sort, pipeline_tag)

    if not models:
        print(f"No models found for '{args.task}'", file=sys.stderr)
        # Suggest matching pipeline tags
        suggestions = list_tasks(args.task)
        if suggestions:
            print("\nTry one of these pipeline tags:", file=sys.stderr)
            for t in suggestions[:5]:
                print(f"  --task {t}", file=sys.stderr)
        sys.exit(0)

    models = models[: args.limit]

    if args.json:
        print(json.dumps(models, indent=2))
        return

    tag_label = f" (pipeline: `{pipeline_tag}`)" if pipeline_tag else ""
    print(f'# Top Models: "{args.task}"{tag_label}\n')
    print(f"Sorted by: {args.sort} | Showing **{len(models)}** models\n")
    for i, m in enumerate(models, 1):
        print(format_model(m, i))

    print("---")
    print("*For detailed benchmark scores, visit:*")
    print("*https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard*")


if __name__ == "__main__":
    main()
