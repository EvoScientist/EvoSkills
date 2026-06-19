"""paper-graph subcommand CLI (Phase 2).

Each subcommand is a thin wrapper around a pipeline helper. The agent
driving the skill calls these in sequence per the SKILL.md runbook,
passing structured state between stages as JSON files on disk. No
outbound LLM calls happen here — every LLM step is the agent's
responsibility (it reads the prompt template from ``references/``,
substitutes the variables, calls its own LLM, and saves the response
for the next subcommand).

Stdout: one short success line per invocation. Stderr: errors only.
JSONL trace is optional via ``--log <path>``.

Run:
    uv run python EvoScientist/skills/paper-graph/scripts/cli.py <subcmd> [flags]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

try:
    from .config import _require_env
    from .logger import Logger
    from . import pipeline
    from . import mermaid as mermaid_mod
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import _require_env  # type: ignore
    from logger import Logger  # type: ignore
    import pipeline  # type: ignore
    import mermaid as mermaid_mod  # type: ignore


def _make_logger(log_arg: str | None, default_out: Path) -> Logger:
    """Resolve the JSONL log path.

    Precedence: explicit ``--log <path>`` > default ``<out>.log.jsonl`` next
    to the subcommand's output > ``--log none`` disables it. JSONL logging
    is on by default because every subcommand is a debugging surface — the
    log file is the only persistent record of what the data layer did.
    """
    if log_arg is None:
        return Logger(
            default_out.with_name(default_out.name + ".log.jsonl"), verbose=False
        )
    if log_arg.lower() == "none":
        return Logger(None, verbose=False)
    return Logger(Path(log_arg), verbose=False)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# resolve_seed_papers
# ---------------------------------------------------------------------------


def _cmd_resolve_seed_papers(args: argparse.Namespace) -> None:
    """Resolve any arxiv IDs found in the query → seed paper records.

    The query lives in a file (not on the CLI) so agent-supplied text never
    has to be shell-escaped. Output is a JSON array of S2-shape paper dicts
    (empty array when no arxiv IDs are present or all lookups fail).
    """
    keys = _require_env()
    query = Path(args.query_file).read_text(encoding="utf-8").strip()
    logger = _make_logger(args.log, Path(args.out))

    async def _run() -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            return await pipeline.resolve_seed_papers(
                client,
                keys["S2_API_KEY"],
                query,
                logger=logger,
            )

    try:
        seed = asyncio.run(_run())
    finally:
        logger.close()

    _write_json(Path(args.out), seed)
    print(f"resolve_seed_papers: {len(seed)} seed paper(s) -> {args.out}")


# ---------------------------------------------------------------------------
# fetch_papers
# ---------------------------------------------------------------------------


def _cmd_fetch_papers(args: argparse.Namespace) -> None:
    """Fetch N related papers via S2 (with DeepXiv fallback).

    Inputs:
      --parsed-query  JSON produced by the agent after running the
                      parse_query LLM stage. Must contain a ``searches``
                      array (the only field consumed here).
      --seed          Optional JSON array of seed papers from
                      resolve_seed_papers. When provided, they're
                      prepended to the result and reserved against the
                      cite-number budget.
      --n             Total number of papers to return (default 10).

    Output: JSON array of S2-shape paper dicts, length up to ``--n``.
    """
    keys = _require_env()
    parsed = _read_json(Path(args.parsed_query))
    if "searches" not in parsed or not isinstance(parsed["searches"], list):
        print(
            "ERROR: parsed-query JSON must contain a 'searches' array.\n"
            f"  got keys: {sorted(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__}",
            file=sys.stderr,
        )
        sys.exit(2)
    searches = parsed["searches"]

    seed_papers: list[dict[str, Any]] | None = None
    if args.seed:
        loaded = _read_json(Path(args.seed))
        if loaded:  # treat empty array as "no seeds" rather than passing []
            seed_papers = loaded

    logger = _make_logger(args.log, Path(args.out))

    async def _run() -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            return await pipeline.fetch_related_papers(
                client,
                keys,
                searches,
                args.n,
                seed_papers=seed_papers,
                logger=logger,
            )

    try:
        papers = asyncio.run(_run())
    finally:
        logger.close()

    _write_json(Path(args.out), papers)
    by_src: dict[str, int] = {}
    for p in papers:
        by_src[p.get("_source", "?")] = by_src.get(p.get("_source", "?"), 0) + 1
    src_str = ", ".join(f"{k}={v}" for k, v in sorted(by_src.items()))
    print(f"fetch_papers: {len(papers)}/{args.n} papers ({src_str}) -> {args.out}")


# ---------------------------------------------------------------------------
# prefetch_sections
# ---------------------------------------------------------------------------


def _cmd_prefetch_sections(args: argparse.Namespace) -> None:
    """Best-effort fetch of each paper's conclusion/discussion section.

    Reads a papers JSON array, mutates each entry by setting
    ``_conclusion_section`` (string or None), writes the augmented array
    back out. ``--in`` and ``--out`` may point to the same file for
    in-place mutation.

    Papers already labeled REJECT (via ``_classification.label``) are
    skipped — the upstream classify step should have run before this
    one for the optimization to kick in, but it's not required: with no
    classification present every paper is treated as CORE and fetched.
    """
    papers = _read_json(Path(args.in_path))
    if not isinstance(papers, list):
        print(
            f"ERROR: --in must point to a JSON array of paper dicts (got {type(papers).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)
    logger = _make_logger(args.log, Path(args.out))

    async def _run() -> None:
        async with httpx.AsyncClient() as client:
            await pipeline._prefetch_paper_sections(client, papers, logger)

    try:
        asyncio.run(_run())
    finally:
        logger.close()

    _write_json(Path(args.out), papers)
    n_sec = sum(1 for p in papers if p.get("_conclusion_section"))
    print(f"prefetch_sections: {n_sec}/{len(papers)} papers with section -> {args.out}")


# ---------------------------------------------------------------------------
# format_seed_block
# ---------------------------------------------------------------------------


def _cmd_format_seed_block(args: argparse.Namespace) -> None:
    """Render a seed-paper JSON array into the ``{seed_block}`` prompt fragment.

    The agent stuffs the output into ``references/parse_query.md`` at the
    ``{seed_block}`` placeholder. Empty seed → empty output file (the
    placeholder collapses cleanly in that case).
    """
    seed = _read_json(Path(args.seed))
    if not isinstance(seed, list):
        print(
            f"ERROR: --seed must point to a JSON array (got {type(seed).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)
    logger = _make_logger(args.log, Path(args.out))

    block = pipeline._format_seed_block(seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(block, encoding="utf-8")
    logger.event(
        "format_seed_block",
        seed_count=len(seed),
        out_chars=len(block),
        empty=(block == ""),
    )
    logger.close()
    print(f"format_seed_block: {len(seed)} seed(s), {len(block)} chars -> {args.out}")


# ---------------------------------------------------------------------------
# format_papers
# ---------------------------------------------------------------------------


def _cmd_format_papers(args: argparse.Namespace) -> None:
    """Render a papers JSON array into the ``{papers_input}`` prompt fragment.

    Output is a numbered list ``(1) ... (2) ...`` joined by blank lines,
    each entry produced by ``_format_one_paper``. When ``--filter`` points
    at a JSON file containing a list of 1-based indices, only those
    papers are emitted; original numbering is preserved so the LLM's
    references remain stable across stages.
    """
    papers = _read_json(Path(args.papers))
    if not isinstance(papers, list):
        print(
            f"ERROR: --papers must point to a JSON array (got {type(papers).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.filter:
        raw_filt = _read_json(Path(args.filter))
        # Accept either a flat [n, ...] array or any JSON object with an
        # ``allowed`` key (the shape parse_outline writes per solution).
        # The latter lets the agent pass a solutions/<key>.json directly.
        if isinstance(raw_filt, dict) and isinstance(raw_filt.get("allowed"), list):
            filt = raw_filt["allowed"]
        else:
            filt = raw_filt
        if not isinstance(filt, list) or not all(isinstance(n, int) for n in filt):
            print(
                "ERROR: --filter must be either a JSON array of 1-based integer "
                "indices, or a JSON object with an 'allowed' array of such indices.",
                file=sys.stderr,
            )
            sys.exit(2)
        bad = [n for n in filt if not (1 <= n <= len(papers))]
        if bad:
            print(
                f"ERROR: filter contains out-of-range indices: {bad} "
                f"(papers length: {len(papers)})",
                file=sys.stderr,
            )
            sys.exit(2)
        indices = sorted(set(filt))
    else:
        indices = list(range(1, len(papers) + 1))

    logger = _make_logger(args.log, Path(args.out))

    block = "\n\n".join(pipeline._format_one_paper(n, papers[n - 1]) for n in indices)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(block, encoding="utf-8")

    # Always emit the `{allowed_numbers}` prompt fragment as a sibling so the
    # agent can substitute it directly without rebuilding the string.
    allowed_str = ", ".join(f"({n})" for n in indices)
    allowed_path = Path(args.out).with_suffix(Path(args.out).suffix + ".allowed.txt")
    allowed_path.write_text(allowed_str, encoding="utf-8")

    logger.event(
        "format_papers",
        total_papers=len(papers),
        selected=len(indices),
        indices=indices,
        out_chars=len(block),
        allowed_out=str(allowed_path),
    )
    logger.close()
    print(
        f"format_papers: {len(indices)}/{len(papers)} papers, "
        f"{len(block)} chars -> {args.out} (+ {allowed_path.name})"
    )


# ---------------------------------------------------------------------------
# compute_core_filter
# ---------------------------------------------------------------------------


def _cmd_compute_core_filter(args: argparse.Namespace) -> None:
    """Write the CORE-filter JSON array + matching ``{allowed_numbers}`` text.

    Consumed by Step 8: ``--out`` plugs straight into ``format_papers --filter``,
    and ``<out>.allowed.txt`` plugs into the ``{allowed_numbers}`` placeholder in
    ``references/outline.md``. Falls back to every paper when no paper is
    labeled CORE (e.g. all-REJECT classifier or a classify fallback).
    """
    papers = _read_json(Path(args.papers))
    if not isinstance(papers, list):
        print(
            f"ERROR: --papers must point to a JSON array (got {type(papers).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)

    indices = [
        i + 1
        for i, p in enumerate(papers)
        if isinstance(p, dict)
        and isinstance(p.get("_classification"), dict)
        and p["_classification"].get("label") == "CORE"
    ]
    fallback = False
    if not indices:
        indices = list(range(1, len(papers) + 1))
        fallback = True

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(indices), encoding="utf-8")

    allowed_str = ", ".join(f"({n})" for n in indices)
    allowed_path = Path(args.out).with_suffix(Path(args.out).suffix + ".allowed.txt")
    allowed_path.write_text(allowed_str, encoding="utf-8")

    logger = _make_logger(args.log, Path(args.out))
    logger.event(
        "compute_core_filter",
        total_papers=len(papers),
        core_count=len(indices),
        indices=indices,
        fallback_no_core=fallback,
        allowed_out=str(allowed_path),
    )
    logger.close()

    suffix = " (FALLBACK: no CORE — using all papers)" if fallback else ""
    print(
        f"compute_core_filter: {len(indices)}/{len(papers)} CORE "
        f"-> {args.out} (+ {allowed_path.name}){suffix}"
    )


# ---------------------------------------------------------------------------
# build_goal_block
# ---------------------------------------------------------------------------


def _cmd_build_goal_block(args: argparse.Namespace) -> None:
    """Materialize the ``{goal}`` prompt fragment for steps 8, 10, and 11.

    Reads ``parsed_query.json`` from Step 4 and writes the multi-line block
    (goal sentence + optional Key Term Definitions) to ``--out``. Downstream
    steps substitute this file verbatim into the ``{goal}`` placeholder of
    ``references/outline.md`` and ``references/detail.md``.
    """
    parsed = _read_json(Path(args.parsed_query))
    if not isinstance(parsed, dict) or not isinstance(parsed.get("goal"), str):
        print(
            "ERROR: --parsed-query must point to a JSON object with a string 'goal'.",
            file=sys.stderr,
        )
        sys.exit(2)

    goal = parsed["goal"].strip()
    definitions = parsed.get("definitions") or {}
    if isinstance(definitions, dict) and definitions:
        lines = [goal, "", "**Key Term Definitions:**"]
        lines.extend(f"- {term}: {body}" for term, body in definitions.items())
        block = "\n".join(lines)
    else:
        block = goal

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(block, encoding="utf-8")

    logger = _make_logger(args.log, Path(args.out))
    logger.event(
        "build_goal_block",
        goal_chars=len(goal),
        definition_count=len(definitions) if isinstance(definitions, dict) else 0,
        out_chars=len(block),
    )
    logger.close()
    print(f"build_goal_block: {len(block)} chars -> {args.out}")


# ---------------------------------------------------------------------------
# merge_classifications
# ---------------------------------------------------------------------------


_CLASSIFICATION_LABELS = ("CORE", "ADJACENT", "REJECT")


def _cmd_merge_classifications(args: argparse.Namespace) -> None:
    """Merge a classify-LLM JSON result into papers.json in place.

    Inputs:
      --classifications  Raw JSON the agent saved from the classify LLM
                         call. Expected shape:
                             {"classifications": [
                                 {"n": int, "label": str, "reason": str},
                                 ...
                             ]}
      --papers           Papers JSON to mutate.
      --out              Output papers JSON (may equal --papers for
                         in-place mutation).

    Validation matches the standalone pipeline: every paper number 1..N
    must appear once with a label in {CORE, ADJACENT, REJECT}. Any
    failure falls back to labeling every paper CORE (the failure-soft
    default the renderers already assume); the fallback is logged and
    surfaced in stdout so the host can decide whether to re-prompt.
    """
    raw = _read_json(Path(args.classifications))
    papers = _read_json(Path(args.papers))
    if not isinstance(papers, list):
        print(
            f"ERROR: --papers must point to a JSON array (got {type(papers).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)

    logger = _make_logger(args.log, Path(args.out))

    items = raw.get("classifications") if isinstance(raw, dict) else None
    fallback_reason: str | None = None
    by_n: dict[int, dict[str, Any]] = {}
    if not isinstance(items, list):
        fallback_reason = "missing or non-list 'classifications' field"
    else:
        for it in items:
            try:
                n = int(it.get("n"))
            except (TypeError, ValueError, AttributeError):
                continue
            label = str(it.get("label") or "").upper().strip()
            if label not in _CLASSIFICATION_LABELS:
                continue
            if not (1 <= n <= len(papers)):
                continue
            by_n[n] = {"label": label, "reason": str(it.get("reason") or "")}
        missing = [n for n in range(1, len(papers) + 1) if n not in by_n]
        if missing:
            fallback_reason = f"classifier omitted papers: {missing}"

    if fallback_reason is not None:
        by_n = {
            n: {"label": "CORE", "reason": f"fallback: {fallback_reason}"}
            for n in range(1, len(papers) + 1)
        }

    for n, rec in by_n.items():
        papers[n - 1]["_classification"] = rec

    _write_json(Path(args.out), papers)
    by_label = {
        lbl: sum(
            1 for p in papers if (p.get("_classification") or {}).get("label") == lbl
        )
        for lbl in _CLASSIFICATION_LABELS
    }
    logger.event(
        "merge_classifications",
        n=len(papers),
        by_label=by_label,
        fell_back=fallback_reason is not None,
        fallback_reason=fallback_reason,
    )
    logger.close()
    suffix = f" (FALLBACK: {fallback_reason})" if fallback_reason else ""
    print(
        f"merge_classifications: {len(papers)} papers, "
        f"CORE={by_label['CORE']} ADJACENT={by_label['ADJACENT']} REJECT={by_label['REJECT']}"
        f"{suffix} -> {args.out}"
    )


# ---------------------------------------------------------------------------
# parse_outline
# ---------------------------------------------------------------------------


def _cmd_parse_outline(args: argparse.Namespace) -> None:
    """Parse the outline LLM's Markdown output into structured JSON.

    Inputs:
      --raw     Raw outline markdown from the agent's outline LLM call.
      --papers  Papers JSON. Used to derive the CORE-only ``allowed`` set
                via each paper's ``_classification.label`` (defaults to
                CORE when classification was skipped, so the parser still
                works without a prior classify step).

    Outputs:
      --out             Summary JSON with root_title, challenges,
                        solutions[], and core_indices.
      --solutions-dir   One context file per solution at
                        ``<dir>/<s_major>.<s_minor>.json``. Defaults to
                        ``<out>.parent/solutions/``. Each file is the
                        ``--context`` input for the per-solution
                        parse_detail / render_detail_mermaid steps later.

    Exits non-zero if the outline contained no parseable challenges
    (the LLM's most common failure mode for this stage).
    """
    raw = Path(args.raw).read_text(encoding="utf-8")
    papers = _read_json(Path(args.papers))
    if not isinstance(papers, list):
        print(
            f"ERROR: --papers must point to a JSON array (got {type(papers).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)

    core_indices = [
        i for i, p in enumerate(papers, start=1) if pipeline._label_of(p) == "CORE"
    ]
    if not core_indices:
        # Defensive (matches generate_graph.py fallback): no CORE papers
        # after classification means treat everything as CORE so the
        # pipeline can still produce something rather than dying here.
        core_indices = list(range(1, len(papers) + 1))
    core_set = set(core_indices)

    logger = _make_logger(args.log, Path(args.out))

    root_title, challenges, challenge_solutions = mermaid_mod.parse_outline_markdown(
        raw,
        allowed=core_set,
        logger=logger,
    )

    if not challenges:
        # Expected terminal state — the LLM produced markdown the parser
        # could not anchor to ``## Challenge N:`` headers. Surface a
        # focused diagnostic so the agent can re-prompt or fail upstream.
        logger.event("error", reason="outline_unparseable", raw_tail=raw[-500:])
        logger.close()
        print(
            "ERROR: outline LLM produced no parseable challenges.\n"
            f"raw output (tail): {raw[-500:]!r}",
            file=sys.stderr,
        )
        sys.exit(4)

    solutions_dir = (
        Path(args.solutions_dir)
        if args.solutions_dir
        else (Path(args.out).parent / "solutions")
    )
    solutions_dir.mkdir(parents=True, exist_ok=True)

    solutions_summary: list[dict[str, Any]] = []
    for c_num in sorted(challenges):
        for s_major, s_minor, sol_name, paper_nums in challenge_solutions.get(
            c_num, []
        ):
            valid = sorted(
                {n for n in paper_nums if 1 <= n <= len(papers) and n in core_set}
            )
            allowed = valid if valid else core_indices
            solution_key_str = f"{s_major}.{s_minor}"
            ctx_path = solutions_dir / f"{solution_key_str}.json"
            ctx = {
                "challenge_idx": c_num,
                "challenge_name": challenges[c_num],
                "solution_key": [s_major, s_minor],
                "solution_key_str": solution_key_str,
                "solution_name": sol_name,
                "paper_nums": paper_nums,
                "allowed": allowed,
            }
            _write_json(ctx_path, ctx)
            solutions_summary.append(
                {
                    "challenge_idx": c_num,
                    "solution_key": solution_key_str,
                    "name": sol_name,
                    "paper_nums": paper_nums,
                    "context_path": str(ctx_path),
                }
            )

    outline_summary = {
        "root_title": root_title,
        "challenges": {str(k): v for k, v in challenges.items()},
        "solutions": solutions_summary,
        "core_indices": core_indices,
    }
    _write_json(Path(args.out), outline_summary)

    logger.event(
        "outline_parsed",
        root_title=root_title,
        n_challenges=len(challenges),
        n_solutions=len(solutions_summary),
        core_indices=core_indices,
    )
    logger.close()
    print(
        f"parse_outline: {len(challenges)} challenge(s), "
        f"{len(solutions_summary)} solution(s) -> {args.out} "
        f"(+ {len(solutions_summary)} context files in {solutions_dir})"
    )


# ---------------------------------------------------------------------------
# parse_detail
# ---------------------------------------------------------------------------


def _cmd_parse_detail(args: argparse.Namespace) -> None:
    """Parse one solution's detail LLM Markdown into structured JSON.

    Inputs:
      --raw      Raw detail markdown from the agent's per-solution LLM call.
      --context  The ``solutions/<key>.json`` file produced by parse_outline.
                 Provides ``challenge_idx``, ``solution_key``, and ``allowed``
                 (the paper-number set the LLM was permitted to reference).

    Output JSON shape (also used as the input for the edge-audit step):
        {
          "challenge_idx": int,
          "solution_key": str,            # "1.1"
          "papers":            {"N": {"gap": str|null, "evolution_from": int|null}},
          "evolution_points":  [{"num", "description", "related"}],
          "open_challenges":   [...],
          "edges":             [{"source_n", "target_n", "gap"}],
          "scratchpad":        str,
          "scratchpad_truncated": bool,
          "dropped":           {paper_headers, edges, related}
        }
    """
    raw = Path(args.raw).read_text(encoding="utf-8")
    ctx = _read_json(Path(args.context))
    challenge_idx = ctx["challenge_idx"]
    sk_list = ctx["solution_key"]
    solution_key = (sk_list[0], sk_list[1])
    allowed = set(ctx["allowed"])

    logger = _make_logger(args.log, Path(args.out))
    parsed = mermaid_mod._parse_detail_markdown(
        raw,
        allowed=allowed,
        logger=logger,
        challenge_idx=challenge_idx,
        solution_key=solution_key,
    )

    out = {
        "challenge_idx": challenge_idx,
        "solution_key": ctx.get("solution_key_str") or f"{sk_list[0]}.{sk_list[1]}",
        "papers": {str(k): v for k, v in parsed["papers"].items()},
        "evolution_points": parsed["evolution_points"],
        "open_challenges": parsed["open_challenges"],
        "edges": parsed["edges"],
        "scratchpad": parsed["scratchpad"],
        "scratchpad_truncated": parsed["scratchpad_truncated"],
        "dropped": {
            "paper_headers": parsed["dropped_paper_headers"],
            "edges": parsed["dropped_edges"],
            "related": parsed["dropped_related"],
        },
    }
    _write_json(Path(args.out), out)
    logger.close()

    print(
        f"parse_detail: solution {out['solution_key']} -> "
        f"{len(out['papers'])} papers, {len(out['edges'])} edges, "
        f"{len(out['evolution_points'])} EPs, "
        f"{len(out['open_challenges'])} OCs -> {args.out}"
    )


# ---------------------------------------------------------------------------
# render_outline_mermaid
# ---------------------------------------------------------------------------


def _cmd_render_outline_mermaid(args: argparse.Namespace) -> None:
    """Render the outline raw markdown into a themed Mermaid graph.

    Outputs a JSON object with ``root_title`` and ``mermaid`` keys; the
    Mermaid string includes its own ``%%{init}%%`` directive and classDef
    palette per the selected theme, ready to drop into a fenced block.
    """
    raw = Path(args.raw).read_text(encoding="utf-8")
    papers = _read_json(Path(args.papers))
    if not isinstance(papers, list):
        print(
            f"ERROR: --papers must point to a JSON array (got {type(papers).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)

    core_indices = [
        i for i, p in enumerate(papers, start=1) if pipeline._label_of(p) == "CORE"
    ]
    if not core_indices:
        core_indices = list(range(1, len(papers) + 1))

    logger = _make_logger(args.log, Path(args.out))
    # outline_to_mermaid re-parses the raw to walk challenges/solutions —
    # cheap (regex over a few KB) and keeps the renderer self-contained.
    mermaid_text = mermaid_mod.outline_to_mermaid(
        raw,
        allowed=set(core_indices),
        theme=args.theme,
    )
    root_title, _, _ = mermaid_mod.parse_outline_markdown(
        raw,
        allowed=set(core_indices),
    )

    out = {"root_title": root_title, "mermaid": mermaid_text}
    _write_json(Path(args.out), out)
    logger.event(
        "render_outline_mermaid",
        theme=args.theme or os.environ.get("MERMAID_THEME") or "light",
        chars=len(mermaid_text),
        root_title=root_title,
    )
    logger.close()
    print(
        f"render_outline_mermaid: {len(mermaid_text)} chars "
        f"(theme={args.theme or 'env/default'}) -> {args.out}"
    )


# ---------------------------------------------------------------------------
# render_detail_mermaid
# ---------------------------------------------------------------------------


def _cmd_render_detail_mermaid(args: argparse.Namespace) -> None:
    """Render one solution's detail markdown into a themed Mermaid graph.

    Inputs:
      --raw        Raw detail markdown.
      --context    ``solutions/<key>.json`` from parse_outline.
      --papers     Papers JSON (for per-node URLs + display labels).
      --verdicts   Optional JSON array of
                   ``[{source_n, target_n, verdict}, ...]`` from the
                   edge-audit step, filtered to this solution.
      --theme      light | dark; falls back to MERMAID_THEME env then 'light'.

    Output JSON shape (consumed by assemble_report):
        {
          "challenge_idx": int,
          "solution_key": "C.M.N"-style str,
          "solution_name": str,
          "mermaid":      str,   # full graph with %%init%% + linkStyle
          "footnotes_md": str    # rendered footnotes block or ""
        }
    """
    raw = Path(args.raw).read_text(encoding="utf-8")
    ctx = _read_json(Path(args.context))
    papers = _read_json(Path(args.papers))
    if not isinstance(papers, list):
        print(
            f"ERROR: --papers must point to a JSON array (got {type(papers).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)

    challenge_idx = ctx["challenge_idx"]
    sk_list = ctx["solution_key"]
    solution_key = (sk_list[0], sk_list[1])
    allowed = set(ctx["allowed"])
    solution_key_str = ctx.get("solution_key_str") or f"{sk_list[0]}.{sk_list[1]}"

    edge_verdicts: dict[tuple[int, int], str] | None = None
    if args.verdicts:
        records = _read_json(Path(args.verdicts))
        if not isinstance(records, list):
            print(
                "ERROR: --verdicts must be a JSON list of "
                "{source_n, target_n, verdict} records.",
                file=sys.stderr,
            )
            sys.exit(2)
        edge_verdicts = {
            (int(r["source_n"]), int(r["target_n"])): str(r["verdict"]) for r in records
        }

    # Derive per-node URLs + labels from papers.json (matches the standalone
    # generate_graph.py logic — labels come from canonical metadata, never
    # from the LLM, so titles can't be hallucinated at render time).
    paper_urls = {i + 1: (p.get("url") or "") for i, p in enumerate(papers)}

    def _node_label(p: dict[str, Any]) -> str:
        title = p.get("title") or "Untitled"
        if len(title) > 100:
            title = title[:97] + "…"
        year = p.get("year") or "n.d."
        return f"{year} — {title}"

    paper_labels = {i + 1: _node_label(p) for i, p in enumerate(papers)}

    logger = _make_logger(args.log, Path(args.out))
    mermaid_body, footnotes_md = mermaid_mod.detail_to_mermaid(
        raw,
        challenge_idx,
        solution_key,
        allowed=allowed,
        paper_urls=paper_urls,
        paper_labels=paper_labels,
        logger=logger,
        edge_verdicts=edge_verdicts,
        theme=args.theme,
    )

    out = {
        "challenge_idx": challenge_idx,
        "solution_key": solution_key_str,
        "solution_name": ctx.get("solution_name", ""),
        "mermaid": mermaid_body,
        "footnotes_md": footnotes_md,
    }
    _write_json(Path(args.out), out)
    logger.event(
        "render_detail_mermaid",
        challenge_idx=challenge_idx,
        solution_key=solution_key_str,
        theme=args.theme or os.environ.get("MERMAID_THEME") or "light",
        mermaid_chars=len(mermaid_body),
        footnotes_chars=len(footnotes_md),
        verdicts_applied=len(edge_verdicts) if edge_verdicts else 0,
    )
    logger.close()
    print(
        f"render_detail_mermaid: solution {solution_key_str}, "
        f"{len(mermaid_body)} mermaid chars"
        + (f", {len(footnotes_md)} footnotes chars" if footnotes_md else "")
        + f" -> {args.out}"
    )


# ---------------------------------------------------------------------------
# assemble_report
# ---------------------------------------------------------------------------


def _cmd_assemble_report(args: argparse.Namespace) -> None:
    """Stitch staged JSON outputs into the final Markdown report.

    Inputs:
      --parsed-query  Agent's parse_query LLM result; provides goal +
                      definitions for the header section.
      --outline       JSON from render_outline_mermaid; provides
                      root_title + outline Mermaid body.
      --details-dir   Directory of render_detail_mermaid JSON outputs
                      (one per solution). Files are sorted by
                      (challenge_idx, s_major, s_minor) for the report.
      --papers        Papers JSON (with _classification baked in to
                      split CORE vs ADJACENT for the appendix).
      --out           Path to write the assembled .md report.

    Output mirrors the standalone generate_graph.py layout: header →
    high-level taxonomy → per-solution evolution paths → core
    appendix → related applications appendix.
    """
    parsed_query = _read_json(Path(args.parsed_query))
    goal = parsed_query.get("goal", "")
    definitions = parsed_query.get("definitions", {}) or {}

    outline_render = _read_json(Path(args.outline))
    root_title = outline_render.get("root_title")
    outline_mermaid = outline_render.get("mermaid", "")

    papers = _read_json(Path(args.papers))
    if not isinstance(papers, list):
        print(
            f"ERROR: --papers must point to a JSON array (got {type(papers).__name__}).",
            file=sys.stderr,
        )
        sys.exit(2)

    details_dir = Path(args.details_dir)
    if not details_dir.is_dir():
        print(
            f"ERROR: --details-dir is not a directory: {details_dir}",
            file=sys.stderr,
        )
        sys.exit(2)

    # Load every JSON in details_dir that looks like a render_detail_mermaid
    # output (must contain a non-empty ``mermaid`` field). Files that don't
    # match are skipped — keeps the loader robust against parse_detail /
    # sidecar files an agent may have written into the same directory.
    detail_files = sorted(
        p for p in details_dir.glob("*.json") if not p.name.endswith(".log.jsonl")
    )
    details: list[tuple[int, int, int, dict[str, Any]]] = []
    skipped: list[str] = []
    for fp in detail_files:
        d = _read_json(fp)
        if not isinstance(d, dict) or "mermaid" not in d:
            skipped.append(fp.name)
            continue
        sk_str = str(d.get("solution_key", ""))
        try:
            sm, sn = (int(x) for x in sk_str.split("."))
        except (ValueError, AttributeError):
            sm, sn = 0, 0
        details.append((int(d.get("challenge_idx", 0)), sm, sn, d))
    details.sort(key=lambda x: (x[0], x[1], x[2]))

    logger = _make_logger(args.log, Path(args.out))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"# Paper Graph: {root_title or '(untitled)'}\n\n")
        if goal:
            f.write(f"**Research goal.** {goal}\n\n")
        if definitions:
            f.write("**Key terms.**\n\n")
            for term, defn in definitions.items():
                f.write(f"- *{term}* — {defn}\n")
            f.write("\n")

        f.write("## High-Level Taxonomy\n\n")
        f.write("```mermaid\n")
        f.write(outline_mermaid)
        f.write("\n```\n\n")

        f.write("## Per-Solution Evolution Paths\n\n")
        for c_num, sm, sn, d in details:
            sol_name = d.get("solution_name", "")
            f.write(f"### Challenge {c_num} · Solution {sm}.{sn}: {sol_name}\n\n")
            f.write("```mermaid\n")
            f.write(d.get("mermaid", ""))
            f.write("\n```\n\n")
            footnotes = d.get("footnotes_md", "")
            if footnotes:
                f.write(footnotes)

        def _render_paper_entry(i: int, p: dict[str, Any]) -> None:
            title = p["title"]
            url = p.get("url") or ""
            title_md = f"[{title}]({url})" if url else title
            f.write(f"**({i}) {title_md}** — {p['year']}  \n")
            f.write(f"_{p['authors']}_")
            if p.get("venue"):
                f.write(f" · {p['venue']}")
            f.write("\n\n")
            if p["abstract"]:
                f.write(f"> {p['abstract']}\n\n")
            section = p.get("_conclusion_section")
            if section:
                f.write(pipeline._render_excerpt_block(section))

        core_entries = [
            (i, p)
            for i, p in enumerate(papers, start=1)
            if pipeline._label_of(p) == "CORE"
        ]
        adjacent_entries = [
            (i, p)
            for i, p in enumerate(papers, start=1)
            if pipeline._label_of(p) == "ADJACENT"
        ]

        f.write("## Paper Appendix (Core lineage)\n\n")
        for i, p in core_entries:
            _render_paper_entry(i, p)

        if adjacent_entries:
            f.write("## Related Applications\n\n")
            f.write(
                "_These papers use the subject as a tool or apply it to "
                "a downstream task. They are listed for context but are "
                "not part of the evolution graph above._\n\n"
            )
            for i, p in adjacent_entries:
                _render_paper_entry(i, p)

    size = out_path.stat().st_size
    logger.event(
        "assemble_report",
        root_title=root_title,
        n_solutions=len(details),
        n_skipped_files=len(skipped),
        skipped_files=skipped,
        n_core=len(core_entries),
        n_adjacent=len(adjacent_entries),
        output_bytes=size,
    )
    logger.close()
    skipped_note = f", skipped {len(skipped)} non-render file(s)" if skipped else ""
    print(
        f"assemble_report: {len(details)} solution block(s){skipped_note}, "
        f"{len(core_entries)} core + {len(adjacent_entries)} adjacent paper(s) "
        f"-> {args.out} ({size} bytes)"
    )


# ---------------------------------------------------------------------------
# dispatcher
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        prog="paper-graph",
        description=(
            "paper-graph skill subcommand dispatcher. Each subcommand is a "
            "single deterministic step in the agent-driven workflow; chain "
            "them per SKILL.md."
        ),
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser(
        "resolve_seed_papers",
        help="Look up any arxiv IDs in the user's query (deterministic, no LLM).",
    )
    p.add_argument(
        "--query-file",
        required=True,
        help="Path to a text file containing the raw user query.",
    )
    p.add_argument(
        "--out", required=True, help="Path to write the seed-paper JSON array."
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_resolve_seed_papers)

    p = sub.add_parser(
        "fetch_papers",
        help="Fetch related papers via Semantic Scholar (+ DeepXiv fallback).",
    )
    p.add_argument(
        "--parsed-query",
        required=True,
        help="Path to the JSON from the agent's parse_query LLM call.",
    )
    p.add_argument(
        "--seed",
        default=None,
        help="Optional path to seed-paper JSON from resolve_seed_papers.",
    )
    p.add_argument(
        "--n", type=int, default=10, help="Number of papers to fetch (default: 10)."
    )
    p.add_argument(
        "--out", required=True, help="Path to write the fetched-paper JSON array."
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_fetch_papers)

    p = sub.add_parser(
        "prefetch_sections",
        help="Fetch each paper's conclusion/discussion section (in-place mutation safe).",
    )
    p.add_argument(
        "--in", dest="in_path", required=True, help="Path to the input papers JSON."
    )
    p.add_argument(
        "--out",
        required=True,
        help="Path to write the augmented papers JSON (may equal --in).",
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_prefetch_sections)

    p = sub.add_parser(
        "format_seed_block",
        help="Render seed-paper JSON into the {seed_block} prompt fragment.",
    )
    p.add_argument(
        "--seed",
        required=True,
        help="Path to the seed-paper JSON array (from resolve_seed_papers).",
    )
    p.add_argument(
        "--out", required=True, help="Path to write the rendered text block."
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_format_seed_block)

    p = sub.add_parser(
        "format_papers",
        help="Render papers JSON into the {papers_input} numbered prompt block.",
    )
    p.add_argument("--papers", required=True, help="Path to the papers JSON array.")
    p.add_argument(
        "--filter",
        default=None,
        help="Optional JSON file with a 1-based index list to include.",
    )
    p.add_argument(
        "--out", required=True, help="Path to write the rendered text block."
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_format_papers)

    p = sub.add_parser(
        "compute_core_filter",
        help="Write the CORE-only index list (+ allowed_numbers sidecar).",
    )
    p.add_argument("--papers", required=True, help="Path to the merged papers JSON.")
    p.add_argument(
        "--out",
        required=True,
        help="Output JSON path (e.g. <workdir>/core_filter.json). "
        "Sibling '<out>.allowed.txt' is also written for {allowed_numbers}.",
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_compute_core_filter)

    p = sub.add_parser(
        "build_goal_block",
        help="Materialize the {goal} prompt fragment from parsed_query.json.",
    )
    p.add_argument(
        "--parsed-query",
        required=True,
        help="Path to parsed_query.json (Step 4 output).",
    )
    p.add_argument(
        "--out",
        required=True,
        help="Output text path (e.g. <workdir>/goal_block.txt).",
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_build_goal_block)

    p = sub.add_parser(
        "merge_classifications",
        help="Merge a classify-LLM JSON result into papers.json in place.",
    )
    p.add_argument(
        "--classifications",
        required=True,
        help="Path to the raw JSON the agent saved from the classify LLM call.",
    )
    p.add_argument("--papers", required=True, help="Path to the input papers JSON.")
    p.add_argument(
        "--out",
        required=True,
        help="Path to write the merged papers JSON (may equal --papers).",
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_merge_classifications)

    p = sub.add_parser(
        "parse_outline",
        help="Parse outline LLM Markdown → structured JSON + per-solution context files.",
    )
    p.add_argument(
        "--raw",
        required=True,
        help="Raw outline markdown from the agent's outline LLM call.",
    )
    p.add_argument(
        "--papers",
        required=True,
        help="Papers JSON (with _classification baked in, when available).",
    )
    p.add_argument(
        "--out", required=True, help="Path to write the outline summary JSON."
    )
    p.add_argument(
        "--solutions-dir",
        default=None,
        help="Directory for per-solution context files. "
        "Defaults to '<out>.parent/solutions'.",
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_parse_outline)

    p = sub.add_parser(
        "parse_detail",
        help="Parse one solution's detail-tree Markdown into structured JSON.",
    )
    p.add_argument(
        "--raw",
        required=True,
        help="Raw detail markdown from the agent's per-solution LLM call.",
    )
    p.add_argument(
        "--context",
        required=True,
        help="Path to solutions/<key>.json produced by parse_outline.",
    )
    p.add_argument("--out", required=True, help="Path to write the parsed-detail JSON.")
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_parse_detail)

    p = sub.add_parser(
        "render_outline_mermaid",
        help="Render outline markdown into a themed Mermaid graph JSON.",
    )
    p.add_argument(
        "--raw",
        required=True,
        help="Raw outline markdown from the agent's outline LLM call.",
    )
    p.add_argument(
        "--papers",
        required=True,
        help="Papers JSON (with _classification baked in, when available).",
    )
    p.add_argument(
        "--out", required=True, help="Path to write the JSON {root_title, mermaid}."
    )
    p.add_argument(
        "--theme",
        choices=["light", "dark"],
        default=None,
        help="Mermaid theme. Falls back to MERMAID_THEME env, then 'light'.",
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_render_outline_mermaid)

    p = sub.add_parser(
        "render_detail_mermaid",
        help="Render one solution's detail markdown into a themed Mermaid graph JSON.",
    )
    p.add_argument(
        "--raw",
        required=True,
        help="Raw detail markdown from the agent's per-solution LLM call.",
    )
    p.add_argument(
        "--context",
        required=True,
        help="Path to solutions/<key>.json produced by parse_outline.",
    )
    p.add_argument(
        "--papers",
        required=True,
        help="Papers JSON (for per-node URLs and display labels).",
    )
    p.add_argument(
        "--verdicts",
        default=None,
        help="Optional JSON list [{source_n, target_n, verdict}] for this solution.",
    )
    p.add_argument(
        "--out",
        required=True,
        help="Path to write the JSON {challenge_idx, solution_key, solution_name, mermaid, footnotes_md}.",
    )
    p.add_argument(
        "--theme",
        choices=["light", "dark"],
        default=None,
        help="Mermaid theme. Falls back to MERMAID_THEME env, then 'light'.",
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_render_detail_mermaid)

    p = sub.add_parser(
        "assemble_report",
        help="Stitch staged JSON outputs into the final Markdown report.",
    )
    p.add_argument(
        "--parsed-query",
        required=True,
        help="Path to the parsed_query JSON (for goal + definitions).",
    )
    p.add_argument(
        "--outline", required=True, help="Path to render_outline_mermaid output JSON."
    )
    p.add_argument(
        "--details-dir",
        required=True,
        help="Directory of render_detail_mermaid output JSON files.",
    )
    p.add_argument(
        "--papers",
        required=True,
        help="Papers JSON (for the appendix and CORE/ADJACENT split).",
    )
    p.add_argument(
        "--out", required=True, help="Path to write the assembled .md report."
    )
    p.add_argument(
        "--log",
        default=None,
        help="JSONL log path. Defaults to '<out>.log.jsonl'. Pass 'none' to disable.",
    )
    p.set_defaults(func=_cmd_assemble_report)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
