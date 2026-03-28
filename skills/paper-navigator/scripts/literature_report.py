#!/usr/bin/env python3
"""Generate a structured literature report from a list of paper IDs.

Uses Semantic Scholar API to fetch paper metadata and generates
intent-adapted reports: survey, quick_scan, deep_dive, or baseline_hunt.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone

import httpx

from utils import S2_BASE, s2_headers, request_with_retry

S2_FIELDS = (
    "paperId,externalIds,title,authors,year,citationCount,"
    "influentialCitationCount,tldr,abstract,"
    "isOpenAccess,openAccessPdf,publicationVenue,publicationDate"
)


def fetch_papers(paper_ids: list[str]) -> list[tuple[str, dict | None]]:
    """Fetch metadata for multiple papers. Returns list of (id, data|None)."""
    results = []
    with httpx.Client() as client:
        for pid in paper_ids:
            try:
                data = request_with_retry(
                    client,
                    f"{S2_BASE}/paper/{pid}",
                    {"fields": S2_FIELDS},
                    s2_headers(),
                )
                if not data or "paperId" not in data:
                    print(
                        f"Warning: Paper '{pid}' not found, skipping", file=sys.stderr
                    )
                    results.append((pid, None))
                else:
                    results.append((pid, data))
                # Rate limit: ~100 req/5min without key
                time.sleep(0.3)
            except SystemExit:
                results.append((pid, None))
    return results


def _get_tldr(paper: dict) -> str:
    """Extract TLDR text from paper data."""
    if paper.get("tldr") and paper["tldr"].get("text"):
        return paper["tldr"]["text"]
    if paper.get("abstract"):
        abstract = paper["abstract"]
        if len(abstract) > 200:
            return abstract[:197] + "..."
        return abstract
    return "No summary available"


def _get_authors(paper: dict) -> str:
    """Format authors string."""
    authors = paper.get("authors", [])
    names = [a.get("name", "") for a in authors[:5] if a.get("name")]
    if len(authors) > 5:
        names.append(f"et al. ({len(authors)} authors)")
    return ", ".join(names) if names else "Unknown"


def _get_ext_ids(paper: dict) -> dict:
    """Extract external IDs."""
    return paper.get("externalIds", {})


def _get_arxiv_id(paper: dict) -> str:
    return _get_ext_ids(paper).get("ArXiv", "")


def _get_doi(paper: dict) -> str:
    return _get_ext_ids(paper).get("DOI", "")


def _get_venue(paper: dict) -> str:
    venue = paper.get("publicationVenue")
    if venue and isinstance(venue, dict):
        return venue.get("name", "")
    return ""


def _get_year(paper: dict) -> str:
    return str(paper.get("year", "?"))


def _reading_level(paper: dict) -> str:
    """Recommend a reading level based on citation count and recency."""
    citations = paper.get("citationCount", 0)
    year = paper.get("year", 0)
    current_year = datetime.now(timezone.utc).year
    age = current_year - year if year else 999

    if citations >= 1000:
        return "L1 Technical" if age <= 2 else "L2 Analytical"
    elif citations >= 100:
        return "L2 Analytical"
    elif citations >= 10:
        return "L3 Contextual"
    else:
        return "L3 Contextual (recent)"


def _novelty_class(paper: dict) -> tuple[str, str]:
    """Classify novelty based on citation patterns."""
    citations = paper.get("citationCount", 0)
    influential = paper.get("influentialCitationCount", 0)
    ratio = influential / citations if citations > 0 else 0

    if citations >= 5000 and ratio >= 0.3:
        return "1 — Milestone", "Defines a new task or paradigm"
    elif citations >= 500 or ratio >= 0.2:
        return "2 — New Pipeline", "New data representation or pipeline"
    elif citations >= 50:
        return "3 — New Module", "New component or technique"
    else:
        return "4 — Incremental", "Improvement on existing approach"


# ── Report generators ──────────────────────────────────────────────


def _report_quick_scan(papers: list[tuple[str, dict]]) -> str:
    """Brief table with title, citations, TLDR only."""
    lines = ["# Quick Scan Report\n"]
    lines.append("| # | Title | Authors | Year | Citations | TLDR |")
    lines.append("|---|-------|---------|------|-----------|------|")
    for i, (pid, paper) in enumerate(papers, 1):
        if paper is None:
            lines.append(f"| {i} | *{pid}* (not found) | — | — | — | — |")
            continue
        title = paper.get("title", "Unknown")
        authors = _get_authors(paper)
        year = _get_year(paper)
        citations = paper.get("citationCount", 0)
        tldr = _get_tldr(paper)
        # Escape pipe in tldr
        tldr = tldr.replace("|", "\\|")
        lines.append(f"| {i} | {title} | {authors} | {year} | {citations} | {tldr} |")
    return "\n".join(lines)


def _report_survey(papers: list[tuple[str, dict]]) -> str:
    """Full survey with summary, paper list, citation analysis, novelty tree, recommendations."""
    lines = ["# Literature Survey Report\n"]

    # ── Summary ──
    found = sum(1 for _, p in papers if p is not None)
    total_citations = sum(p.get("citationCount", 0) for _, p in papers if p)
    years = [p.get("year") for _, p in papers if p and p.get("year")]
    year_range = f"{min(years)}–{max(years)}" if years else "?"
    lines.append("## Summary\n")
    lines.append(f"- **Papers:** {found} found, {len(papers) - found} not found")
    lines.append(f"- **Total citations:** {total_citations:,}")
    lines.append(f"- **Year range:** {year_range}\n")

    # ── Paper List ──
    lines.append("## Paper List\n")
    for i, (pid, paper) in enumerate(papers, 1):
        if paper is None:
            lines.append(f"### {i}. *{pid}* — Not Found\n")
            continue
        title = paper.get("title", "Unknown")
        authors = _get_authors(paper)
        year = _get_year(paper)
        citations = paper.get("citationCount", 0)
        influential = paper.get("influentialCitationCount", 0)
        venue = _get_venue(paper)
        arxiv_id = _get_arxiv_id(paper)
        doi = _get_doi(paper)
        tldr = _get_tldr(paper)
        oa_pdf = ""
        if paper.get("openAccessPdf") and paper["openAccessPdf"].get("url"):
            oa_pdf = f"\n📄 [Open Access PDF]({paper['openAccessPdf']['url']})"

        ids_parts = []
        if arxiv_id:
            ids_parts.append(f"arXiv: `{arxiv_id}`")
        if doi:
            ids_parts.append(f"DOI: `{doi}`")
        ids_str = " | ".join(ids_parts)

        lines.append(f"### {i}. {title}\n")
        lines.append(f"**{authors}** ({year}) — {venue}")
        lines.append(f"Citations: **{citations}** (influential: {influential})")
        if ids_str:
            lines.append(ids_str)
        lines.append(f"\n> {tldr}{oa_pdf}\n")

    # ── Citation Analysis ──
    lines.append("## Citation Analysis\n")
    sorted_papers = sorted(
        [(pid, p) for pid, p in papers if p is not None],
        key=lambda x: x[1].get("citationCount", 0),
        reverse=True,
    )
    lines.append("| Rank | Title | Citations | Influential | Year |")
    lines.append("|------|-------|-----------|-------------|------|")
    for rank, (pid, paper) in enumerate(sorted_papers, 1):
        title = paper.get("title", "Unknown")[:60]
        citations = paper.get("citationCount", 0)
        influential = paper.get("influentialCitationCount", 0)
        year = _get_year(paper)
        lines.append(f"| {rank} | {title} | {citations:,} | {influential:,} | {year} |")

    # ── Novelty Classification ──
    lines.append("\n## Novelty Classification\n")
    for pid, paper in papers:
        if paper is None:
            continue
        title = paper.get("title", "Unknown")
        novelty_type, description = _novelty_class(paper)
        lines.append(f"- **{title}** → Type {novelty_type}: {description}")

    # ── Challenge-Insight Tree ──
    lines.append("\n## Challenge-Insight Tree\n")
    lines.append(
        "*Note: This section is agent-driven. The following is auto-generated from paper metadata.*\n"
    )
    for pid, paper in papers:
        if paper is None:
            continue
        title = paper.get("title", "Unknown")
        tldr = _get_tldr(paper)
        lines.append(f"**{title}**")
        lines.append(f"└── Key insight: {tldr}\n")

    # ── Recommendations ──
    lines.append("## Recommendations\n")
    if sorted_papers:
        top = sorted_papers[0][1]
        lines.append(
            f"- **Must-read:** {top.get('title', 'Unknown')} (highest citations)"
        )
        if len(sorted_papers) > 1:
            recent = sorted_papers[-1][1]
            lines.append(f"- **Watch:** {recent.get('title', 'Unknown')} (most recent)")
    lines.append("- Use `citation_traverse` on key papers to discover related work")
    lines.append("- Use `find_code` to check reproducibility of promising papers")

    return "\n".join(lines)


def _report_deep_dive(papers: list[tuple[str, dict]]) -> str:
    """Full survey + per-paper reading level recommendations + detailed notes."""
    lines = [_report_survey(papers)]
    lines.append("\n\n---\n\n")
    lines.append("# Deep Dive: Per-Paper Analysis\n")

    for i, (pid, paper) in enumerate(papers, 1):
        if paper is None:
            continue
        title = paper.get("title", "Unknown")
        citations = paper.get("citationCount", 0)
        influential = paper.get("influentialCitationCount", 0)
        year = _get_year(paper)
        level = _reading_level(paper)
        novelty_type, novelty_desc = _novelty_class(paper)
        arxiv_id = _get_arxiv_id(paper)

        lines.append(f"## {i}. {title}\n")
        lines.append(f"- **Reading level:** {level}")
        lines.append(f"- **Novelty:** {novelty_type} — {novelty_desc}")
        lines.append(f"- **Citations:** {citations:,} (influential: {influential:,})")
        lines.append(f"- **Year:** {year}")
        lines.append(f"- **arXiv:** `{arxiv_id}`" if arxiv_id else "")

        # Reading recommendation rationale
        if citations >= 1000:
            lines.append(
                "\n**Why read this:** High-impact paper with broad influence. Essential for understanding the field."
            )
        elif citations >= 100:
            lines.append(
                "\n**Why read this:** Well-cited paper. Good for understanding established techniques."
            )
        elif citations >= 10:
            lines.append(
                "\n**Why read this:** Moderate impact. Read if directly relevant to your work."
            )
        else:
            lines.append(
                "\n**Why read this:** Recent or niche paper. Scan for novel ideas applicable to your research."
            )

        lines.append(f"\n**TLDR:** {_get_tldr(paper)}\n")

        # Suggested related actions
        lines.append("**Suggested next steps:**")
        if arxiv_id:
            lines.append(
                f"- `citation_traverse --paper-id ArXiv:{arxiv_id} --direction forward`"
            )
            lines.append(
                f"- `citation_traverse --paper-id ArXiv:{arxiv_id} --direction co-citation`"
            )
        lines.append(
            f"- `find_code --arxiv-id {arxiv_id}`"
            if arxiv_id
            else f'- `find_code --title "{title}""'
        )
        lines.append("")

    return "\n".join(lines)


def _report_baseline_hunt(papers: list[tuple[str, dict]]) -> str:
    """Focus on code availability, SOTA position, reproducibility."""
    lines = ["# Baseline Hunt Report\n"]

    for i, (pid, paper) in enumerate(papers, 1):
        if paper is None:
            lines.append(f"## {i}. *{pid}* — Not Found\n")
            continue
        title = paper.get("title", "Unknown")
        authors = _get_authors(paper)
        year = _get_year(paper)
        citations = paper.get("citationCount", 0)
        arxiv_id = _get_arxiv_id(paper)
        doi = _get_doi(paper)
        venue = _get_venue(paper)
        is_oa = paper.get("isOpenAccess", False)
        oa_pdf = paper.get("openAccessPdf", {})
        pdf_url = oa_pdf.get("url", "") if oa_pdf else ""

        lines.append(f"## {i}. {title}\n")
        lines.append(f"**{authors}** ({year}) — {venue}")
        lines.append(f"Citations: **{citations}**")

        # IDs
        ids_parts = []
        if arxiv_id:
            ids_parts.append(f"arXiv: `{arxiv_id}`")
        if doi:
            ids_parts.append(f"DOI: `{doi}`")
        if ids_parts:
            lines.append(" | ".join(ids_parts))

        # Code availability check
        lines.append("\n**Code Availability:**")
        lines.append(
            f"- Run: `python scripts/find_code.py --arxiv-id {arxiv_id}`"
            if arxiv_id
            else f'- Run: `python scripts/find_code.py --title "{title}""'
        )
        lines.append(
            f'- GitHub search: `python scripts/github_search.py --query "{title}""'
        )

        # Open Access
        lines.append("\n**Open Access:**")
        if is_oa and pdf_url:
            lines.append(f"✅ Available: [{pdf_url}]({pdf_url})")
        elif is_oa:
            lines.append("✅ Open access (PDF link not in S2)")
        else:
            lines.append("❌ Not open access. Check publisher or preprint servers.")

        # Reproducibility indicators
        lines.append("\n**Reproducibility Indicators:**")
        score = 0
        if is_oa:
            score += 1
            lines.append("- ✅ Open access paper available")
        else:
            lines.append("- ❌ Paper behind paywall")
        if arxiv_id:
            score += 1
            lines.append("- ✅ arXiv preprint available (version history)")
        else:
            lines.append("- ⚠️ No arXiv preprint found")
        lines.append("- ⏳ Code check needed (run find_code above)")

        # SOTA position
        lines.append("\n**SOTA Position:**")
        lines.append('- Run: `python scripts/sota.py --task "<relevant task>"`')
        lines.append(f'- Run: `python scripts/dataset_search.py --query "{title}""')

        # Overall score
        lines.append(f"\n**Reproducibility Score: {score}/3**")
        lines.append("")

    return "\n".join(lines)


def generate_report(papers: list[tuple[str, dict]], intent: str) -> str:
    """Generate report based on intent."""
    generators = {
        "quick_scan": _report_quick_scan,
        "survey": _report_survey,
        "deep_dive": _report_deep_dive,
        "baseline_hunt": _report_baseline_hunt,
    }
    generator = generators.get(intent, _report_survey)
    return generator(papers)


def main():
    parser = argparse.ArgumentParser(
        description="Generate literature report from paper IDs"
    )
    parser.add_argument(
        "--paper-ids",
        required=True,
        help="Comma-separated paper IDs (e.g., ArXiv:2601.07372,ArXiv:2501.12948)",
    )
    parser.add_argument(
        "--intent",
        choices=["survey", "quick_scan", "deep_dive", "baseline_hunt"],
        default="survey",
        help="Report type (default: survey)",
    )
    parser.add_argument(
        "--output", "-o", help="Output file path (also prints to stdout)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON of fetched papers"
    )
    args = parser.parse_args()

    paper_ids = [pid.strip() for pid in args.paper_ids.split(",") if pid.strip()]

    if not paper_ids:
        print("Error: No paper IDs provided", file=sys.stderr)
        sys.exit(1)

    print(
        f"Fetching {len(paper_ids)} paper(s) from Semantic Scholar...", file=sys.stderr
    )
    results = fetch_papers(paper_ids)

    if args.json:
        output = {}
        for pid, paper in results:
            output[pid] = paper
        json_str = json.dumps(output, indent=2)
        print(json_str)
        if args.output:
            with open(args.output, "w") as f:
                f.write(json_str + "\n")
            print(f"Saved to {args.output}", file=sys.stderr)
        return

    report = generate_report(results, args.intent)
    print(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report + "\n")
        print(f"\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
