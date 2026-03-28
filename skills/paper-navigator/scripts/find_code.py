#!/usr/bin/env python3
"""Find code implementations for papers via HuggingFace Papers API + GitHub search."""

import argparse
import json
import sys

import httpx

from utils import HF_API, GITHUB_API, hf_headers, github_headers, request_with_retry


def _find_via_hf(
    client: httpx.Client, arxiv_id: str | None = None, title: str | None = None
) -> dict | None:
    """Find paper's GitHub repo via HuggingFace Papers API."""
    headers = hf_headers()

    if arxiv_id:
        # Clean arXiv ID
        arxiv_id = arxiv_id.strip().replace("ArXiv:", "").replace("arxiv:", "")
        for prefix in ["https://arxiv.org/abs/", "http://arxiv.org/abs/"]:
            if arxiv_id.startswith(prefix):
                arxiv_id = arxiv_id[len(prefix) :]

        data = request_with_retry(
            client,
            f"{HF_API}/papers/{arxiv_id}",
            headers=headers,
            follow_redirects=True,
        )
        if data and data.get("githubRepo"):
            return {
                "url": data["githubRepo"],
                "stars": data.get("githubStars", 0),
                "framework": "",
                "is_official": True,
                "description": data.get("title", ""),
            }

    if title:
        # Search by title
        data = request_with_retry(
            client,
            f"{HF_API}/papers/search",
            {"q": title, "limit": 3},
            headers,
            follow_redirects=True,
        )
        results = data if isinstance(data, list) else []
        for item in results:
            paper = item.get("paper", item)
            if paper.get("githubRepo"):
                return {
                    "url": paper["githubRepo"],
                    "stars": paper.get("githubStars", 0),
                    "framework": "",
                    "is_official": True,
                    "description": paper.get("title", ""),
                }

    return None


def _find_via_github(client: httpx.Client, query: str, limit: int = 5) -> list[dict]:
    """Search GitHub for paper implementations."""
    params = {"q": query, "per_page": min(limit, 30), "sort": "stars", "order": "desc"}
    data = request_with_retry(
        client, GITHUB_API, params, github_headers(), follow_redirects=True
    )
    repos = []
    for r in data.get("items", [])[:limit]:
        repos.append(
            {
                "url": r.get("html_url", ""),
                "stars": r.get("stargazers_count", 0),
                "framework": r.get("language", "unknown"),
                "is_official": False,
                "description": (r.get("description") or "")[:150],
            }
        )
    return repos


def find_code(
    arxiv_id: str | None = None, title: str | None = None, limit: int = 5
) -> list[dict]:
    """Find code repos for a paper using HuggingFace + GitHub."""
    repos = []
    with httpx.Client() as client:
        # Try HuggingFace first (official repo)
        hf_repo = _find_via_hf(client, arxiv_id, title)
        if hf_repo:
            repos.append(hf_repo)

        # Supplement with GitHub search
        search_query = title or arxiv_id or ""
        if search_query:
            gh_repos = _find_via_github(client, f"{search_query} implementation", limit)
            # Deduplicate by URL
            seen_urls = {r["url"] for r in repos}
            for r in gh_repos:
                if r["url"] not in seen_urls:
                    repos.append(r)
                    seen_urls.add(r["url"])

    # Sort by stars (official first via high-priority, then by stars)
    repos.sort(key=lambda r: (r["is_official"], r["stars"]), reverse=True)
    return repos[:limit]


def format_repo(r: dict, idx: int) -> str:
    url = r.get("url", "")
    stars = r.get("stars", 0)
    framework = r.get("framework", "unknown")
    is_official = r.get("is_official", False)
    desc = r.get("description", "")[:150]

    official_tag = " 🏷️ **Official**" if is_official else ""
    framework_str = f" | Framework: {framework}" if framework else ""

    return (
        f"{idx}. [{url}]({url}){official_tag}\n"
        f"   ⭐ {stars:,}{framework_str}\n"
        f"   {desc}\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Find code implementations via HuggingFace + GitHub"
    )
    parser.add_argument("--arxiv-id", "-a", help="arXiv ID (e.g. 1706.03762)")
    parser.add_argument("--title", "-t", help="Paper title to search")
    parser.add_argument(
        "--limit", "-l", type=int, default=5, help="Max repos (default 5)"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not args.arxiv_id and not args.title:
        print("Error: --arxiv-id or --title required", file=sys.stderr)
        sys.exit(1)

    repos = find_code(args.arxiv_id, args.title, args.limit)

    if not repos:
        query = args.arxiv_id or args.title
        print(f"No code found for '{query}'", file=sys.stderr)
        sys.exit(0)

    if args.json:
        print(json.dumps(repos, indent=2))
        return

    query = args.arxiv_id or args.title
    print(f"# Code Implementations: {query}\n")
    print(f"Found **{len(repos)}** repositories\n")
    for i, r in enumerate(repos, 1):
        print(format_repo(r, i))


if __name__ == "__main__":
    main()
