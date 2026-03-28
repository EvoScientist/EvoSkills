#!/usr/bin/env python3
"""Search GitHub repositories to find papers/projects that may not yet be on arXiv.

Uses the GitHub REST API to search for relevant repositories by keyword,
with sorting by stars, recency, or relevance.
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import httpx

from utils import GITHUB_API, github_headers, request_with_retry


def _print_rate_limit_info(resp_headers: dict) -> None:
    """Print GitHub rate limit info to stderr."""
    remaining = resp_headers.get("x-ratelimit-remaining", "?")
    limit = resp_headers.get("x-ratelimit-limit", "?")
    reset = resp_headers.get("x-ratelimit-reset", "?")
    print(f"GitHub API rate limit: {remaining}/{limit} remaining", file=sys.stderr)
    if reset != "?":
        reset_ts = int(reset)
        reset_dt = datetime.fromtimestamp(reset_ts, tz=timezone.utc)
        print(
            f"  Resets at: {reset_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            file=sys.stderr,
        )


def search_repos(query: str, limit: int = 10, sort: str = "stars") -> list[dict]:
    """Search GitHub repositories."""
    params: dict = {
        "q": query,
        "per_page": min(limit, 100),
        "page": 1,
    }
    if sort in ("stars", "updated"):
        params["sort"] = sort
        params["order"] = "desc"

    headers = github_headers()
    with httpx.Client(follow_redirects=True) as client:
        data = request_with_retry(client, GITHUB_API, params, headers)

    return data.get("items", [])


def _format_date(date_str: str | None) -> str:
    """Format ISO date to YYYY-MM-DD."""
    if not date_str:
        return "?"
    return date_str[:10]


def format_repo(r: dict, idx: int) -> str:
    """Format a single repository as Markdown."""
    full_name = r.get("full_name", "unknown/repo")
    description = r.get("description", "") or "No description"
    stars = r.get("stargazers_count", 0)
    language = r.get("language", "?")
    created = _format_date(r.get("created_at"))
    updated = _format_date(r.get("updated_at"))
    html_url = r.get("html_url", "")
    topics = r.get("topics", [])

    topics_str = ""
    if topics:
        topics_str = "\n   Topics: " + ", ".join(f"`{t}`" for t in topics[:8])

    # Truncate description
    if len(description) > 120:
        description = description[:117] + "..."

    return (
        f"{idx}. **{full_name}** — {description}\n"
        f"   ⭐ {stars:,} | {language} | Created: {created} | Updated: {updated}\n"
        f"   {html_url}{topics_str}\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Search GitHub repositories")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Max results (default 10)"
    )
    parser.add_argument(
        "--sort",
        choices=["stars", "updated", "relevance"],
        default="stars",
        help="Sort order (default: stars)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    repos = search_repos(args.query, args.limit, args.sort)

    if not repos:
        print(f"No repositories found for '{args.query}'", file=sys.stderr)
        sys.exit(0)

    if args.json:
        print(json.dumps(repos, indent=2))
        return

    print(f'# GitHub Search: "{args.query}"\n')
    print(f"Found **{len(repos)}** repositories\n")
    for i, repo in enumerate(repos, 1):
        print(format_repo(repo, i))


if __name__ == "__main__":
    main()
