"""idea-elaborate CLI: pre-flight context extraction + final stitch of stage outputs.

Two main subcommands:
- ``extract_node_context``: read an idea-spark ``graph.json``, build a structured
  context blob (chosen node + ancestor chain + sibling titles + thread_id) per
  notes/idea-elaborate-design.md, write to a workspace JSON file. Consumed by
  stages 2-5's LLM templates.
- ``stitch_notes``: take per-stage markdown outputs from the workspace and
  concatenate into the final ``notes.md`` (+ ``refs.json``) under the graph's
  ``elaborations/<node-id>/`` directory.

``sanitize_id`` is reused (same semantics as idea-spark's CLI) for graph-id
resolution from a user-typed display name.

State the skill writes lives under ``$MEMORIES_DIR/idea_spark_tree/<sid>/``.
``$MEMORIES_DIR`` defaults to ``~/.evoscientist/memories`` — the same default
``idea-spark`` uses.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Shared helpers (mirror idea-spark/scripts/cli.py — keep semantics aligned)
# ---------------------------------------------------------------------------

_SANITIZE_RE = re.compile(r"[^a-z0-9-]+")


def memories_dir() -> Path:
    env = os.environ.get("EVOSCIENTIST_MEMORIES_DIR") or os.environ.get(
        "EVOSCIENTIST_MEMORY_DIR"
    )
    if env:
        return Path(env).expanduser()
    data = os.environ.get("EVOSCIENTIST_DATA_DIR")
    if data:
        return Path(data).expanduser() / "memories"
    return Path.home() / ".evoscientist" / "memories"


def graph_dir_for(graph_id: str) -> Path:
    return memories_dir() / "idea_spark_tree" / graph_id


def sanitize_graph_id(name: str) -> str:
    lowered = name.strip().lower()
    sub = _SANITIZE_RE.sub("-", lowered).strip("-")
    return sub[:64]


def _virtual_memories_path(p: Path) -> str:
    """Rewrite a host path under MEMORIES_DIR to its virtual-mount form.

    Mirrors the helper in idea-spark: the EvoScientist sandbox's
    FilesystemBackend (ls, read_file) only dereferences ``/memories/...``.
    Printing virtual paths lets the agent navigate to what we wrote.
    """
    try:
        base = memories_dir().resolve()
        rel = p.resolve().relative_to(base)
    except ValueError:
        return str(p)
    rel_str = str(rel)
    return "/memories" if rel_str == "." else f"/memories/{rel_str}"


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_json(path: Path, data: object) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def utcnow_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Context extraction
# ---------------------------------------------------------------------------


def _index_nodes(graph: dict) -> dict[str, dict]:
    return {n["id"]: n for n in graph.get("nodes", []) if isinstance(n, dict)}


def _walk_ancestors(node: dict, by_id: dict[str, dict]) -> list[dict]:
    """Return the ancestor chain root → parent (excluding the node itself)."""
    chain: list[dict] = []
    cur = by_id.get(node.get("parent_id")) if node.get("parent_id") else None
    while cur is not None:
        chain.append(cur)
        cur = by_id.get(cur.get("parent_id")) if cur.get("parent_id") else None
    chain.reverse()
    return chain


def _siblings(node: dict, by_id: dict[str, dict]) -> list[dict]:
    parent_id = node.get("parent_id")
    if parent_id is None:
        return []
    return [
        n
        for n in by_id.values()
        if n.get("parent_id") == parent_id and n.get("id") != node.get("id")
    ]


def _project_node_full(n: dict) -> dict:
    """Project a node into the 'full content' shape used for the chosen node."""
    out = {
        "id": n.get("id"),
        "title": n.get("title", ""),
        "description": n.get("description", ""),
        "next_action": n.get("next_action", ""),
        "references": n.get("references", []) or [],
        "thread_id": n.get("thread_id", ""),
    }
    return out


def _project_node_ancestor(n: dict) -> dict:
    """Project a node into the ancestor shape (title + description only)."""
    return {
        "id": n.get("id"),
        "title": n.get("title", ""),
        "description": n.get("description", ""),
    }


def _project_node_sibling(n: dict) -> dict:
    """Project a node into the sibling shape (title only — design decision)."""
    return {"id": n.get("id"), "title": n.get("title", "")}


def build_context(graph: dict, node_id: str) -> dict:
    by_id = _index_nodes(graph)
    node = by_id.get(node_id)
    if node is None:
        raise SystemExit(
            f"ERROR: node '{node_id}' not found in graph "
            f"'{graph.get('id', '?')}'. Known node ids: "
            + ", ".join(sorted(by_id.keys())[:8])
            + ("..." if len(by_id) > 8 else "")
        )
    # Refuse to extract context for rejected nodes — stage 3 of SKILL.md
    # explicitly says the agent should not silently elaborate on a rejected
    # direction. This is the CLI-side defense.
    if node.get("rejected") is True:
        raise SystemExit(
            f"ERROR: node '{node_id}' is rejected (rejected=true on the node "
            "itself). idea-elaborate refuses to extract context for rejected "
            "nodes; surface to the user and pick a different direction."
        )
    # Walk ancestors and check for any rejected ancestor — the Phase 2 cascade
    # rule from idea-spark means any descendant of a rejected node is also
    # effectively rejected, even if the per-node flag is missing.
    ancestors = _walk_ancestors(node, by_id)
    rejected_ancestor = next((a for a in ancestors if a.get("rejected") is True), None)
    if rejected_ancestor is not None:
        raise SystemExit(
            f"ERROR: node '{node_id}' has a rejected ancestor "
            f"'{rejected_ancestor.get('id')}' "
            f"(title: '{rejected_ancestor.get('title', '?')}'). The Phase 2 "
            "cascade treats descendants of rejected nodes as rejected. "
            "Surface to the user and pick a different direction."
        )
    return {
        "graph_id": graph.get("id"),
        "graph_name": graph.get("name"),
        "node": _project_node_full(node),
        "ancestors": [_project_node_ancestor(a) for a in ancestors],
        "siblings": [_project_node_sibling(s) for s in _siblings(node, by_id)],
        "extracted_at": utcnow_iso(),
    }


def cmd_extract_node_context(args: argparse.Namespace) -> int:
    graph_path = graph_dir_for(args.graph_id) / "graph.json"
    if not graph_path.exists():
        print(
            f"ERROR: graph '{args.graph_id}' not found at "
            f"{_virtual_memories_path(graph_path.parent)}. Run idea-spark "
            "first, or check the sanitized graph-id matches an existing tree.",
            file=sys.stderr,
        )
        return 3
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    context = build_context(graph, args.node_id)
    out_path = Path(args.out)
    atomic_write_json(out_path, context)
    print(
        json.dumps(
            {
                "graph_id": context["graph_id"],
                "node_id": context["node"]["id"],
                "ancestor_count": len(context["ancestors"]),
                "sibling_count": len(context["siblings"]),
                "context_path": str(out_path),
            }
        )
    )
    return 0


# ---------------------------------------------------------------------------
# Stitch — final notes.md + refs.json under elaborations/<node-id>/
# ---------------------------------------------------------------------------

# Match a level-1 markdown header (`# Something`) at the start of a line.
# Used to downgrade per-stage headers when concatenating into notes.md so the
# final document has a single top-level header for the elaboration.
_H1_LINE = re.compile(r"^(#)(\s)", re.MULTILINE)


def _downgrade_headers(md: str) -> str:
    """Promote every level-1 header to level-2 (so concatenation nests cleanly)."""
    return _H1_LINE.sub(r"##\2", md)


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def build_notes(node_title: str, stage_md: dict[str, str]) -> str:
    """Build notes.md from the three stage markdown blocks.

    stage_md keys: 'elaborate', 'analyze', 'conclude' — each is the raw
    markdown the LLM produced. Missing keys yield a section that explicitly
    says the stage was not run; this preserves the structural verification
    contract (notes.md always has Elaboration / Analysis / Conclusions).
    """
    sections = [f"# Elaboration: {node_title.strip()}", ""]
    for label, key in [
        ("Elaboration", "elaborate"),
        ("Analysis", "analyze"),
        ("Conclusions", "conclude"),
    ]:
        body = stage_md.get(key)
        sections.append(f"## {label}")
        sections.append("")
        if body is None:
            sections.append(f"*Stage {key} output not present at stitch time.*")
        else:
            sections.append(_downgrade_headers(body.rstrip()))
        sections.append("")
    return "\n".join(sections).rstrip() + "\n"


def cmd_stitch_notes(args: argparse.Namespace) -> int:
    workspace = Path(args.elaboration_dir)
    if not workspace.exists():
        print(
            f"ERROR: elaboration workspace '{workspace}' does not exist. "
            "Did you run stages 2-4 and write their outputs there?",
            file=sys.stderr,
        )
        return 4

    # Load graph + node for the notes title
    graph_path = graph_dir_for(args.graph_id) / "graph.json"
    if not graph_path.exists():
        print(
            f"ERROR: graph '{args.graph_id}' not found at "
            f"{_virtual_memories_path(graph_path.parent)}.",
            file=sys.stderr,
        )
        return 3
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    node = next(
        (n for n in graph.get("nodes", []) if n.get("id") == args.node_id),
        None,
    )
    if node is None:
        print(
            f"ERROR: node '{args.node_id}' not found in graph '{args.graph_id}'.",
            file=sys.stderr,
        )
        return 4

    # Read per-stage outputs from the workspace
    stage_md = {
        "elaborate": _read_optional(workspace / "2_elaborate.md"),
        "analyze": _read_optional(workspace / "3_analyze.md"),
        "conclude": _read_optional(workspace / "4_conclude.md"),
    }
    if all(v is None for v in stage_md.values()):
        print(
            "ERROR: no stage outputs (2_elaborate.md / 3_analyze.md / "
            f"4_conclude.md) found under {workspace}. Nothing to stitch.",
            file=sys.stderr,
        )
        return 5

    # Read papers.json from stage 1 (optional — refs.json is best-effort)
    papers_path = workspace / "papers.json"
    refs = None
    if papers_path.exists():
        try:
            refs = json.loads(papers_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(
                f"WARNING: papers.json present but unparseable ({e}); refs.json "
                "will be omitted.",
                file=sys.stderr,
            )

    # Compose and write the final artifacts
    notes_md = build_notes(node.get("title", "(untitled)"), stage_md)
    elab_dir = graph_dir_for(args.graph_id) / "elaborations" / args.node_id
    notes_out = elab_dir / "notes.md"
    atomic_write_text(notes_out, notes_md)
    written: list[str] = [str(notes_out)]
    if refs is not None:
        refs_out = elab_dir / "refs.json"
        atomic_write_json(refs_out, refs)
        written.append(str(refs_out))

    print(
        json.dumps(
            {
                "graph_id": args.graph_id,
                "node_id": args.node_id,
                "elaboration_path": _virtual_memories_path(elab_dir),
                "wrote": [_virtual_memories_path(Path(p)) for p in written],
                "stages_present": [k for k, v in stage_md.items() if v is not None],
            }
        )
    )
    return 0


# ---------------------------------------------------------------------------
# sanitize_id (identical semantics to idea-spark)
# ---------------------------------------------------------------------------


def cmd_sanitize_id(args: argparse.Namespace) -> int:
    sid = sanitize_graph_id(args.name)
    if not sid:
        print(
            f"ERROR: '{args.name}' sanitizes to empty; pick a different name",
            file=sys.stderr,
        )
        return 2
    print(sid)
    return 0


# ---------------------------------------------------------------------------
# Argparse dispatch
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(prog="idea-elaborate", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser(
        "sanitize_id",
        help="apply the SCHEMA.md graph-id sanitization rules; print result",
    )
    s.add_argument("--name", required=True)
    s.set_defaults(func=cmd_sanitize_id)

    s = sub.add_parser(
        "extract_node_context",
        help="read graph.json, build context.json with chosen node + ancestors + siblings",
    )
    s.add_argument("--graph-id", required=True, help="sanitized graph id")
    s.add_argument("--node-id", required=True, help="opaque node-<hex> identifier")
    s.add_argument("--out", required=True, help="output path for context.json")
    s.set_defaults(func=cmd_extract_node_context)

    s = sub.add_parser(
        "stitch_notes",
        help="concatenate stage 2-4 outputs into notes.md + copy papers.json to refs.json",
    )
    s.add_argument("--graph-id", required=True)
    s.add_argument("--node-id", required=True)
    s.add_argument(
        "--elaboration-dir",
        required=True,
        help="workspace dir containing 2_elaborate.md / 3_analyze.md / 4_conclude.md / papers.json",
    )
    s.set_defaults(func=cmd_stitch_notes)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
