#!/usr/bin/env python3
"""Search GitHub repositories to find papers/projects that may not yet be on arXiv.

Uses the GitHub REST API (unauthenticated, public repos) to search for
relevant repositories by keyword, with sorting by stars, recency, or relevance.
"""

import argparse
import json
import sys
import time

import httpx

GITHUB_API = "https://api.github.com/search/repositories"

MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]

_UA = {"User-Agent": "EvoScientist/1.0 (paper-navigator)", "Accept": "application/vnd.github.v3+json"}


def _request_with_retry(client: httpx.Client, url: str, params: dict | None = None) -> dict:
    """GET with retry on 429/5xx and rate-limit awareness."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.get(url, params=params, headers=_UA, timeout=30)
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt < MAX_RETRIES - 1:
                    # Respect Retry-After header if present
                    retry_after = resp.headers.get("Retry-After")
                    wait = int(retry_after) if retry_after else RETRY_DELAYS[attempt]
                    print(f"Rate limited. Waiting {wait}s before retry...", file=sys.stderr)
                    time.sleep(wait)
                    continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {}
            raise
        except httpx.HTTPError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise SystemExit(f"Error: {e}") from e
    return {}


def _print_rate_limit_info(resp_headers: dict) -> None:
    """Print GitHub rate limit info to stderr."""
    remaining = resp_headers.get("x-ratelimit-remaining", "?")
    limit = resp_headers.get("x-ratelimit-limit", "?")
    reset = resp_headers.get("x-ratelimit-reset", "?")
    print(f"GitHub API rate limit: {remaining}/{limit} remaining", file=sys.stderr)
    if reset != "?":
        from datetime import datetime, timezone
        reset_ts = int(reset)
        reset_dt = datetime.fromtimestamp(reset_ts, tz=timezone.utc)
        print(f"  Resets at: {reset_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}", file=sys.stderr)


def search_repos(query: str, limit: int = 10, sort: str = "stars") -> tuple[list[dict], dict]:
    """Search GitHub repositories.

    Returns (repos_list, response_headers).
    """
    params: dict = {
        "q": query,
        "per_page": min(limit, 100),
        "page": 1,
    }
    if sort in ("stars", "updated"):
        params["sort"] = sort
        params["order"] = "desc"

    with httpx.Client(follow_redirects=True) as client:
        resp = client.get(GITHUB_API, params=params, headers=_UA, timeout=30)

        # Print rate limit info
        _print_rate_limit_info(resp.headers)

        if resp.status_code == 429:
            raise SystemExit("Error: GitHub API rate limit exceeded. Try again later or use an API token.")

        resp.raise_for_status()
        data = resp.json()
        return data.get("items", []), dict(resp.headers)


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

    return (f"{idx}. **{full_name}** — {description}\n"
            f"   ⭐ {stars:,} | {language} | Created: {created} | Updated: {updated}\n"
            f"   {html_url}{topics_str}\n")


def main():
    parser = argparse.ArgumentParser(description="Search GitHub repositories")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max results (default 10)")
    parser.add_argument("--sort", choices=["stars", "updated", "relevance"],
                        default="stars", help="Sort order (default: stars)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    repos, headers = search_repos(args.query, args.limit, args.sort)

    if not repos:
        print(f"No repositories found for '{args.query}'", file=sys.stderr)
        sys.exit(0)

    if args.json:
        print(json.dumps(repos, indent=2))
        return

    print(f"# GitHub Search: \"{args.query}\"\n")
    print(f"Found **{len(repos)}** repositories\n")
    for i, repo in enumerate(repos, 1):
        print(format_repo(repo, i))


if __name__ == "__main__":
    main()
