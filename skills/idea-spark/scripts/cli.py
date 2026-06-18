"""idea-spark CLI: persist/extend the Idea Spark research-idea tree.

Canonical state lives in graph.json at
    $MEMORIES_DIR/idea_spark_tree/<graph_id>/graph.json
with a derived Mermaid projection at graph.md (rewritten on every change).

Writer contract (SCHEMA.md):
- preserve every existing node's id and parent_id
- assign fresh ids only to newly-added nodes
- atomic file replace via .tmp + rename
- never delete (cleanup is a user op)
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import re
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = 1


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


_SANITIZE_RE = re.compile(r"[^a-z0-9-]+")
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
# References get normalized to canonical URLs so the WebUI's defensive
# resolver isn't load-bearing. Matches the three shapes the WebUI knows:
#   bare arxiv id ("2406.08207" or "2406.08207v2") or "arXiv:" prefix
#   bare doi ("10.NNNN/...") or "doi:" prefix
#   anything already a URL passes through unchanged
_ARXIV_ID_RE = re.compile(r"^(?:arXiv:)?(\d{4}\.\d{4,5})(v\d+)?$", re.IGNORECASE)
_DOI_RE = re.compile(r"^(?:doi:)?(10\.\d+/\S+)$", re.IGNORECASE)
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _normalize_reference(s: str) -> str:
    """Canonicalize a reference string to a URL when possible.

    Unrecognized forms (titles, free text, malformed ids) pass through
    unchanged — the WebUI renders them as plain text, which is preferable
    to dropping data the writer believed was useful.
    """
    s = s.strip()
    if not s or _URL_RE.match(s):
        return s
    m = _ARXIV_ID_RE.match(s)
    if m:
        return f"https://arxiv.org/abs/{m.group(1)}{m.group(2) or ''}"
    m = _DOI_RE.match(s)
    if m:
        return f"https://doi.org/{m.group(1)}"
    return s


def _uuid_thread_id(value: str) -> str:
    if not _UUID_RE.match(value):
        raise argparse.ArgumentTypeError(
            f"--thread-id {value!r} is not a UUID. The skill expects the canonical "
            "LangGraph thread id from runtime.execution_info.thread_id "
            "(UUIDv7 shape like '019ed4cf-5c0d-7812-acb8-ce13992e82f4'). "
            "Check the host's thread-id discovery path."
        )
    return value


def _current_workspace_dir() -> str:
    """Resolve the workspace dir the same way EvoScientist.sessions does.

    Mirrors `EvoScientist/sessions.py:_api_workspace_dir` (a private helper, so
    we duplicate the trivial logic instead of importing it). Used to scope the
    sessions.db lookup to threads owned by the workspace serving this call —
    sessions.db is machine-global, so unscoped lookups would race against
    threads from other workspaces.
    """
    ws = os.environ.get("EVOSCIENTIST_WORKSPACE_DIR", "").strip()
    if ws:
        return str(Path(ws).expanduser().resolve())
    return str(Path.cwd().resolve())


def _discover_thread_id_from_session_db() -> str | None:
    """Return the most recent thread_id for this workspace, or None.

    Reads `EvoScientist.sessions.list_threads()` — a public function — and
    filters by `workspace_dir`. This is the production discovery path: the
    LangGraph orchestrator and the WebUI both write through the
    `_ApiPruningCheckpointer` that stamps `workspace_dir` onto every thread's
    metadata, so the most recent matching row IS the calling agent's thread
    in the single-conversation-per-workspace flow.

    Edge case: if two threads in the same workspace are concurrently active
    (multi-tab WebUI), the most-recent row may be a sibling thread's, not the
    caller's. Phase 1 accepts this — the alternative is harness wiring.

    Returns None if EvoScientist isn't importable (dev / eval / CI), if the
    sessions.db is missing, or if no thread in this workspace is found —
    callers fall through to require an explicit --thread-id.
    """
    try:
        from EvoScientist.sessions import list_threads
    except ImportError:
        return None

    workspace = _current_workspace_dir()
    try:
        threads = asyncio.run(list_threads(limit=20))
    except Exception:
        return None
    for t in threads:
        if t.get("workspace_dir") == workspace:
            tid = t.get("thread_id")
            if isinstance(tid, str) and _UUID_RE.match(tid):
                return tid
    return None


def resolve_thread_id(arg_value: str | None) -> str:
    """Resolve thread_id: explicit --thread-id override → workspace-scoped
    discovery from EvoScientist's sessions.db → hard fail.

    --thread-id wins when present (already shape-validated by argparse). When
    absent, we ask the production source of truth (sessions.db) for the most
    recent thread owned by this workspace. We never read env or invent — the
    agent has no slot in this chain to substitute a fabricated value.
    """
    if arg_value:
        return arg_value
    discovered = _discover_thread_id_from_session_db()
    if discovered:
        return discovered
    raise SystemExit(
        "ERROR: thread_id unavailable. Tried:\n"
        "  1. --thread-id arg: not provided\n"
        "  2. EvoScientist.sessions.list_threads() workspace lookup: no match\n"
        "Either pass --thread-id <uuid> explicitly (when the user is pointing "
        "at a specific existing graph), or invoke the skill from inside an "
        "active EvoScientist conversation so the sessions-db lookup can "
        "resolve. Do NOT fabricate a UUID."
    )


def sanitize_graph_id(name: str) -> str:
    lowered = name.strip().lower()
    sub = _SANITIZE_RE.sub("-", lowered).strip("-")
    return sub[:64]


def new_node_id() -> str:
    return f"node-{secrets.token_hex(8)}"


def utcnow_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# Mirrors paper-graph/scripts/mermaid.py _MERMAID_ESCAPE_TABLE so titles
# survive Mermaid parsing the same way across the two skills.
_MERMAID_ESCAPE = str.maketrans(
    {
        "(": "#40;",
        ")": "#41;",
        "|": "#124;",
        '"': "#34;",
        "[": "#91;",
        "]": "#93;",
        ";": "#59;",
        ":": "#58;",
        "{": "#123;",
        "}": "#125;",
        "#": "#35;",
    }
)


def mermaid_safe(title: str) -> str:
    return title.translate(_MERMAID_ESCAPE)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_json(path: Path, data: dict) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_graph(graph_id: str) -> dict | None:
    p = graph_dir_for(graph_id) / "graph.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _virtual_memories_path(p: Path) -> str:
    """Rewrite a host path under MEMORIES_DIR to its virtual-mount form.

    The EvoScientist sandbox's FilesystemBackend (ls, read_file) only
    dereferences `/memories/...`; the host-absolute form is opaque to it.
    Printing virtual paths lets the agent navigate to what we just wrote
    without an extra path-translation round.

    Falls back to the literal path string when *p* is outside MEMORIES_DIR —
    shouldn't happen for this skill, but keeps the helper safe to reuse.
    """
    try:
        base = memories_dir().resolve()
        rel = p.resolve().relative_to(base)
    except ValueError:
        return str(p)
    rel_str = str(rel)
    return "/memories" if rel_str == "." else f"/memories/{rel_str}"


def _summarize_existing_graph(graph_dir: Path) -> str:
    """One-line description of the existing graph at graph_dir.

    Used in the `init` "already exists" error to tell the agent what's
    actually on disk — name, node count, last update — so it can choose
    between extending via merge_children vs picking a new graph-id.
    """
    json_path = graph_dir / "graph.json"
    try:
        g = json.loads(json_path.read_text(encoding="utf-8"))
        name = g.get("name", "(unnamed)")
        nodes = g.get("nodes", [])
        updated = g.get("updated_at", "(unknown)")
        return f"name={name!r}, nodes={len(nodes)}, updated_at={updated}"
    except (OSError, json.JSONDecodeError):
        return "(graph.json missing or unreadable — possibly a half-finished prior run)"


def render_mermaid(graph: dict) -> str:
    lines = ["graph LR"]
    for n in graph["nodes"]:
        lines.append(f'  {n["id"]}["{mermaid_safe(n["title"])}"]')
    for n in graph["nodes"]:
        if n["parent_id"] is not None:
            lines.append(f"  {n['parent_id']} --> {n['id']}")
    body = "\n".join(lines)
    return f"# {graph['name']}\n\n```mermaid\n{body}\n```\n"


def write_graph(graph: dict) -> None:
    d = graph_dir_for(graph["id"])
    atomic_write_json(d / "graph.json", graph)
    atomic_write_text(d / "graph.md", render_mermaid(graph))


@contextlib.contextmanager
def _graph_lock(graph_dir: Path):
    """Hold an exclusive `graph.lock` on the graph dir for a write.

    The WebUI checks for this file: while present, Reject/Restore controls
    are disabled. Released on both success and failure so the UI restores
    interactivity in either case. No staleness heuristic — legitimate skill
    runs can take arbitrary time, and false-positive takeover would corrupt
    an in-progress write. If a `graph.lock` is genuinely stuck after a
    crash, the user removes it manually.

    Filename is `graph.lock`, not `.lock`: the WebUI doesn't list hidden
    (dot-prefixed) entries through its memory backend, so the dotfile form
    would be invisible to the polling logic that disables the controls.
    """
    graph_dir.mkdir(parents=True, exist_ok=True)
    lock_path = graph_dir / "graph.lock"
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        existing = ""
        with contextlib.suppress(OSError):
            existing = lock_path.read_text(encoding="utf-8").strip()
        raise SystemExit(
            f"ERROR: graph at {_virtual_memories_path(graph_dir)} is locked "
            f"by another skill run (holder={existing!r}). Wait for it to "
            "finish, or remove the graph.lock file manually if you know the "
            "holder is dead."
        ) from None
    try:
        os.write(fd, f"{os.getpid()} {utcnow_iso()}\n".encode())
        os.close(fd)
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            lock_path.unlink()


def _node_content_fields(payload: dict) -> dict:
    """Extract the schema-recognized content fields of a node from a host dict.

    "Content fields" = the per-node payload the host (LLM) supplies and the
    skill validates. Distinct from the structural fields (`id`, `parent_id`,
    `thread_id`, `created_at`, `rejected`) which the skill mints itself.

    Required: title. Optional: description, next_action, references[].
    Unknown keys are dropped — the host can stash whatever it likes in the
    JSON it hands us, only schema-recognized fields land on disk.
    """
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise SystemExit("node payload missing non-empty 'title'")
    out: dict = {"title": title.strip()}
    for k in ("description", "next_action"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()
    refs = payload.get("references")
    if isinstance(refs, list):
        cleaned = [
            _normalize_reference(r) for r in refs if isinstance(r, str) and r.strip()
        ]
        cleaned = [r for r in cleaned if r]  # defensive: normalize may produce empty
        if cleaned:
            out["references"] = cleaned
    return out


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


def cmd_format_init_context(args: argparse.Namespace) -> int:
    parts: list[str] = []
    if args.topic:
        parts.append("## User topic\n" + args.topic.strip())
    if args.paper:
        parts.append(
            "## Seed papers / links\n" + "\n".join(f"- {p}" for p in args.paper)
        )
    if args.paper_graph_node:
        parts.append(
            "## Reference graph nodes (from paper-graph)\n"
            + "\n".join(f"- {n}" for n in args.paper_graph_node)
        )
    if args.note:
        parts.append("## Additional context\n" + args.note.strip())
    if not parts:
        print(
            "ERROR: pass at least one of --topic / --paper / --paper-graph-node / --note",
            file=sys.stderr,
        )
        return 2
    text = "\n\n".join(parts) + "\n"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote seed block ({len(parts)} sections) to {out}")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    sid = sanitize_graph_id(args.graph_id)
    if not sid:
        print(
            f"ERROR: graph-id '{args.graph_id}' sanitizes to empty",
            file=sys.stderr,
        )
        return 2
    if graph_dir_for(sid).exists():
        existing_dir = graph_dir_for(sid)
        existing = _summarize_existing_graph(existing_dir)
        print(
            f"ERROR: graph '{sid}' already exists at "
            f"{_virtual_memories_path(existing_dir)}\n"
            f"  Existing: {existing}\n"
            "  If this is your prior attempt for this direction, extend it "
            "via the merge_children subcommand instead of re-running init. "
            "Otherwise pick a different graph-id or have the user remove "
            "the directory.",
            file=sys.stderr,
        )
        return 3
    thread_id = resolve_thread_id(args.thread_id)
    root_payload = json.loads(Path(args.root_json).read_text(encoding="utf-8"))
    root_fields = _node_content_fields(root_payload)
    now = utcnow_iso()
    root = {
        "id": new_node_id(),
        "parent_id": None,
        "thread_id": thread_id,
        "created_at": now,
        "rejected": False,
        **root_fields,
    }
    graph = {
        "schema_version": SCHEMA_VERSION,
        "id": sid,
        "name": args.name,
        "created_at": now,
        "updated_at": now,
        "nodes": [root],
    }
    with _graph_lock(graph_dir_for(sid)):
        write_graph(graph)
    print(
        json.dumps(
            {
                "graph_id": sid,
                "root_node_id": root["id"],
                "path": _virtual_memories_path(graph_dir_for(sid)),
            }
        )
    )
    return 0


def cmd_format_expand_context(args: argparse.Namespace) -> int:
    graph = load_graph(args.graph_id)
    if graph is None:
        print(f"ERROR: graph '{args.graph_id}' not found", file=sys.stderr)
        return 3
    by_id = {n["id"]: n for n in graph["nodes"]}
    parent = by_id.get(args.parent_node_id)
    if parent is None:
        print(
            f"ERROR: parent node '{args.parent_node_id}' not found in graph "
            f"'{args.graph_id}'",
            file=sys.stderr,
        )
        return 4
    chain: list[dict] = []
    cur: dict | None = parent
    while cur is not None:
        chain.append(cur)
        cur = by_id.get(cur["parent_id"]) if cur["parent_id"] else None
    chain.reverse()
    existing = [n for n in graph["nodes"] if n["parent_id"] == parent["id"]]
    parts = [f"## Research direction\n{graph['name']}"]
    chain_lines = []
    for i, node in enumerate(chain):
        indent = "  " * i
        chain_lines.append(f"{indent}- **{node['title']}**")
        if desc := node.get("description"):
            chain_lines.append(f"{indent}  {desc}")
    parts.append("## Ancestor chain (root → parent)\n" + "\n".join(chain_lines))
    if existing:
        parts.append(
            "## Existing children of parent (avoid duplicating)\n"
            + "\n".join(f"- {c['title']}" for c in existing)
        )
    if refs := parent.get("references"):
        parts.append("## Parent references\n" + "\n".join(f"- {r}" for r in refs))
    text = "\n\n".join(parts) + "\n"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(
        f"wrote parent context (depth={len(chain)}, existing_children={len(existing)}) to {out}"
    )
    return 0


def cmd_merge_children(args: argparse.Namespace) -> int:
    graph = load_graph(args.graph_id)
    if graph is None:
        print(f"ERROR: graph '{args.graph_id}' not found", file=sys.stderr)
        return 3
    by_id = {n["id"]: n for n in graph["nodes"]}
    if args.parent_node_id not in by_id:
        print(
            f"ERROR: parent node '{args.parent_node_id}' not found",
            file=sys.stderr,
        )
        return 4
    thread_id = resolve_thread_id(args.thread_id)
    payload = json.loads(Path(args.children_json).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "children" in payload:
        children_raw = payload["children"]
    else:
        children_raw = payload
    if not isinstance(children_raw, list) or not children_raw:
        print("ERROR: children-json must be a non-empty list", file=sys.stderr)
        return 5
    now = utcnow_iso()
    added: list[dict] = []
    for c in children_raw:
        fields = _node_content_fields(c)
        node = {
            "id": new_node_id(),
            "parent_id": args.parent_node_id,
            "thread_id": thread_id,
            "created_at": now,
            "rejected": False,
            **fields,
        }
        added.append(node)
    graph["nodes"].extend(added)
    graph["updated_at"] = now
    with _graph_lock(graph_dir_for(graph["id"])):
        write_graph(graph)
    print(
        json.dumps(
            {
                "graph_id": graph["id"],
                "parent_node_id": args.parent_node_id,
                "added": [n["id"] for n in added],
            }
        )
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="idea-spark", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sanitize_id", help="apply SCHEMA.md sanitization to a name")
    s.add_argument("--name", required=True)
    s.set_defaults(func=cmd_sanitize_id)

    s = sub.add_parser(
        "format_init_context", help="build the {seed_block} for references/init.md"
    )
    s.add_argument("--topic", help="bare topic string")
    s.add_argument(
        "--paper",
        action="append",
        default=[],
        help="paper title, arxiv id, or link; repeatable",
    )
    s.add_argument(
        "--paper-graph-node",
        action="append",
        default=[],
        help="title of a node from an existing paper-graph artifact; repeatable",
    )
    s.add_argument("--note", help="freeform extra context from the user")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_format_init_context)

    s = sub.add_parser("init", help="create a fresh graph with a single root node")
    s.add_argument(
        "--graph-id",
        required=True,
        help="user-supplied display name; will be sanitized into the dir name",
    )
    s.add_argument(
        "--name", required=True, help="unsanitized display name (verbatim from user)"
    )
    s.add_argument(
        "--thread-id",
        type=_uuid_thread_id,
        help="LangGraph thread id of the calling agent (UUID; v4 or v7). "
        "Optional override — when omitted, read from EVOSCIENTIST_THREAD_ID.",
    )
    s.add_argument(
        "--root-json",
        required=True,
        help="path to JSON with root node fields (title/description/next_action/references)",
    )
    s.set_defaults(func=cmd_init)

    s = sub.add_parser(
        "format_expand_context",
        help="build {parent_context} for references/expand.md from current graph",
    )
    s.add_argument("--graph-id", required=True, help="already sanitized")
    s.add_argument("--parent-node-id", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_format_expand_context)

    s = sub.add_parser(
        "merge_children", help="append validated children under a parent node"
    )
    s.add_argument("--graph-id", required=True)
    s.add_argument("--parent-node-id", required=True)
    s.add_argument(
        "--thread-id",
        type=_uuid_thread_id,
        help="LangGraph thread id of the calling agent (UUID; v4 or v7). "
        "Optional override — when omitted, read from EVOSCIENTIST_THREAD_ID.",
    )
    s.add_argument(
        "--children-json",
        required=True,
        help="path to JSON list (or {children: [...]}) of new node payloads",
    )
    s.set_defaults(func=cmd_merge_children)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
