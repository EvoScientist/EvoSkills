#!/usr/bin/env python3
"""Search for datasets via HuggingFace Datasets API."""

import argparse
import json
import sys

import httpx

from utils import HF_API, hf_headers, request_with_retry


def search_datasets(
    query: str, limit: int = 10, sort: str = "downloads"
) -> list[dict]:
    """Search HuggingFace datasets."""
    params: dict = {"search": query, "limit": min(limit, 100), "sort": sort}
    with httpx.Client() as client:
        data = request_with_retry(
            client, f"{HF_API}/datasets", params, hf_headers(), follow_redirects=True
        )
    return data if isinstance(data, list) else []


def format_dataset(d: dict, idx: int) -> str:
    dataset_id = d.get("id", "Unknown")
    # Short name: last part of id (e.g., "imagenet-1k" from "ILSVRC/imagenet-1k")
    name = dataset_id.split("/")[-1] if "/" in dataset_id else dataset_id
    downloads = d.get("downloads", 0)
    likes = d.get("likes", 0)
    author = d.get("author", "")
    desc = (d.get("description") or "")[:200]
    if len(d.get("description", "") or "") > 200:
        desc = desc.rsplit(" ", 1)[0] + "..."

    # Extract modalities from tags
    tags = d.get("tags", [])
    modalities = [t.replace("modality:", "") for t in tags if t.startswith("modality:")]
    modality_str = ", ".join(modalities[:3]) if modalities else ""

    # Extract task categories from tags
    tasks = [
        t.replace("task_categories:", "")
        for t in tags
        if t.startswith("task_categories:")
    ]
    task_str = ", ".join(tasks[:3]) if tasks else ""

    homepage = f"https://huggingface.co/datasets/{dataset_id}"

    lines = [f"{idx}. **{name}**"]
    if author:
        lines[0] += f" ({author})"
    lines.append(f"   Downloads: {downloads:,} | Likes: {likes} | ID: `{dataset_id}`")
    if modality_str:
        lines.append(f"   Modalities: {modality_str}")
    if task_str:
        lines.append(f"   Tasks: {task_str}")
    lines.append(f"   {homepage}")
    if desc:
        lines.append(f"   > {desc}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search datasets via HuggingFace")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Max results (default 10)"
    )
    parser.add_argument(
        "--sort",
        choices=["downloads", "likes", "trending"],
        default="downloads",
        help="Sort order (default: downloads)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    datasets = search_datasets(args.query, args.limit, args.sort)

    if not datasets:
        print(f"No datasets found for '{args.query}'", file=sys.stderr)
        sys.exit(0)

    datasets = datasets[: args.limit]

    if args.json:
        print(json.dumps(datasets, indent=2))
        return

    print(f'# Datasets: "{args.query}"\n')
    print(f"Found **{len(datasets)}** datasets\n")
    for i, d in enumerate(datasets, 1):
        print(format_dataset(d, i))


if __name__ == "__main__":
    main()
