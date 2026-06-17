---
name: idea-spark
description: "Use this skill to grow a persistent, branching tree of research ideas the user can explore interactively. Trigger when the user wants to **brainstorm research directions** off a topic, a seed paper, or an existing paper-graph node, and have the candidate ideas **persist in a graph the WebUI can render**. Two operations: create a new idea-spark tree from a seed (topic / paper / paper-graph nodes), or expand an existing node into N candidate child ideas. State lives at `$MEMORIES_DIR/idea_spark_tree/<graph_id>/graph.{json,md}` per the locked SCHEMA.md contract. Do NOT trigger for one-paper summaries, literature surveys without an ideation step, or single-shot brainstorming the user just wants in chat — only when the user wants the ideas captured into the persistent tree."
allowed-tools: "write_file edit_file read_file execute"
metadata:
  author: EvoScientist
  version: '0.1.3'
  tags: [research, ideation, graph, mermaid, webui]
---

# Idea Spark

Grow a persistent tree of research ideas the user can explore via the WebUI. The skill is the **writer** of the contract documented in `SCHEMA.md` — the WebUI is the reader.

The skill has no outbound LLM dependency. The host agent provides the LLM calls; the skill provides the deterministic CLI (state IO, id generation, atomic writes, Mermaid projection) and the prompt templates the host substitutes into.

## When to Use This Skill

Trigger when the user asks something like:

- "Here is a paper on `<topic>` — what are new directions we could explore?"
- "Two branches in the paper-graph stem from the same paper — could they be merged into one direction?"
- "I want to push further in `<field>` — I recently read `<paper>`. Where could this go?"
- "Expand the `<node>` idea — give me a few child directions."
- "Start an Idea Spark on `<topic>`."

Skip when:
- The user just wants a one-paper summary or a single brainstorm reply in chat (no persistence).
- The user wants a literature survey but no ideation step on top.
- The request is to render or read an existing tree (that's the WebUI's job).

## Inputs and Output

**Inputs for a new tree (`init`):**
- A **research-direction name** — verbatim user phrasing (will be sanitized into the dir name).
- A **seed** — any combination of: a topic string, one or more paper titles / arxiv ids / links, or one or more node titles lifted from an existing `paper-graph` artifact.
- The current LangGraph **thread id** — **the CLI discovers it itself** by querying `EvoScientist.sessions.list_threads()` (a public function over `sessions.db`) and picking the most recent thread whose `workspace_dir` matches `EVOSCIENTIST_WORKSPACE_DIR` (or `cwd` when unset). Both the CLI and the WebUI write through the same `_ApiPruningCheckpointer`, so this resolves to the calling conversation's thread for the single-conversation-per-workspace flow. The agent does NOT pass `--thread-id` in normal operation. **Never invent a UUID.**

  Pass `--thread-id <uuid>` only when the user has explicitly pointed at a specific existing graph (the override case). Shape-validated as UUID v4 or v7; arg wins over discovery when both could resolve.

  Edge case: multiple WebUI tabs concurrently active in the same workspace — discovery may attribute to whichever sibling thread checkpointed most recently, not the calling thread. Phase 1 accepts this; cross-tab tightening would require harness wiring (passing the runtime thread id explicitly through deepagents' subprocess boundary), which the team has scoped out.

**Inputs for extending a tree (`expand`):**
- The (already sanitized) `graph_id` of an existing tree.
- The `id` of the node to expand.
- The current thread id.
- *(Optional)* number of children to generate (`--n` on the LLM call, defaults to `IDEA_SPARK_CHILDREN` env, fallback **4**).

**Outputs (on every run):**
- `$MEMORIES_DIR/idea_spark_tree/<graph_id>/graph.json` — canonical state.
- `$MEMORIES_DIR/idea_spark_tree/<graph_id>/graph.md` — derived Mermaid view.

Both are written atomically (`.tmp` + `rename`). `graph.md` is a pure projection rewritten in full each time; `graph.json` is read-extend-rewrite.

## Setup

**Env (all optional):**
- `EVOSCIENTIST_WORKSPACE_DIR` — workspace that scopes the sessions.db thread-id lookup. Set by the EvoScientist harness; falls back to `cwd` when missing. The skill doesn't write it.
- `EVOSCIENTIST_MEMORIES_DIR` — overrides the memories root. Default `~/.evoscientist/memories/`.
- `IDEA_SPARK_CHILDREN` — default branching factor for `expand` when the user doesn't specify. Default **4**.
- `MERMAID_PUNCT` — `ESCAPE` (default) or `FULLWIDTH`. Same semantics as paper-graph; affects how titles render inside Mermaid labels.

**LLM:** the host agent uses its own model and API key. The skill emits prompt templates (`references/init.md`, `references/expand.md`) and validates the JSON the host hands back; it does not authenticate or call any LLM provider itself.

**Working directory:** none. `graph.json` is the source of truth; the only intermediates are the short text files passed to the LLM (seed block, parent context) which can live in a tmp dir of the agent's choice.

## Runbook — `init` (new tree)

### Step 1 — Confirm the research-direction name and seed with the user

The user names the direction (e.g. "Self-supervised speech recognition"). Capture:
- the verbatim `name` (preserved on disk for display),
- any seed material — topic string, paper links/arxiv ids, paper-graph node titles, freeform notes.

Ask if any of these are missing or ambiguous. Don't proceed with an empty seed.

### Step 2 — `sanitize_id` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/idea-spark/scripts/cli.py sanitize_id \
    --name "<verbatim research-direction name>"
```

Prints the sanitized id to stdout (lowercase, `[a-z0-9-]+`, ≤64 chars). Non-zero exit if it sanitizes to empty — ask the user for a different name.

### Step 3 — `format_init_context` (CLI, deterministic)

Build the `{seed_block}` substitution for the init prompt:

```bash
uv run python EvoScientist/skills/idea-spark/scripts/cli.py format_init_context \
    --topic "<topic if any>" \
    --paper "<paper1>" --paper "<paper2>" \
    --paper-graph-node "<existing node title>" \
    --note "<freeform extra context>" \
    --out /tmp/<sid>_seed_block.txt
```

At least one of `--topic / --paper / --paper-graph-node / --note` is required. `--paper` and `--paper-graph-node` are repeatable. Sections are emitted only for inputs the host supplies.

### Step 4 — `init` LLM call (host substitutes `references/init.md`)

Read `EvoScientist/skills/idea-spark/references/init.md`. Substitute:
- `{research_direction_name}` — the verbatim user-supplied name (not the sanitized id).
- `{seed_block}` — contents of the file from Step 3.

Call the LLM (low temperature, ~0.2). Strip any code fences the model may have wrapped around the JSON. Parse as a single object with `title` (required, non-empty) and optional `description / next_action / references[]`.

Save the parsed JSON to `/tmp/<sid>_root.json`.

### Step 5 — `init` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/idea-spark/scripts/cli.py init \
    --graph-id "<verbatim name>" \
    --name "<verbatim name>" \
    --root-json /tmp/<sid>_root.json
```

The CLI auto-discovers the thread id from sessions.db; do not pass `--thread-id` in normal runs. Writes `graph.json` + `graph.md` atomically. Exits with code 3 if the graph dir already exists (Phase 1 forbids overwriting — pick a different name or have the user remove the dir manually). Prints `{graph_id, root_node_id, path}` on success.

## Runbook — `expand` (extend an existing tree)

### Step 1 — Identify the parent node

The user names the node to expand — either by `id` (if they have it from the WebUI) or by description ("expand the LLM-as-diarizer branch"). If by description, look it up in `graph.json` first and confirm the match with the user before proceeding.

### Step 2 — `format_expand_context` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/idea-spark/scripts/cli.py format_expand_context \
    --graph-id <sid> \
    --parent-node-id <parent_id> \
    --out /tmp/<sid>_<parent_id>_context.txt
```

Builds `{parent_context}` for the expand prompt: research-direction name + the ancestor chain from root to parent (with descriptions where available) + any existing direct children of the parent (so the LLM doesn't duplicate them) + the parent's references.

### Step 3 — `expand` LLM call (host substitutes `references/expand.md`)

Read `EvoScientist/skills/idea-spark/references/expand.md`. Substitute:
- `{n_children}` — the user-requested branching factor, or `IDEA_SPARK_CHILDREN`, or **4**.
- `{parent_context}` — contents of the file from Step 2.

Call the LLM (temperature ~0.4 — slightly warmer than `init` to encourage divergent branches). Strip code fences. Parse as `{"children": [...]}` and validate each child has a non-empty `title`. Save to `/tmp/<sid>_<parent_id>_children.json`.

### Step 4 — `merge_children` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/idea-spark/scripts/cli.py merge_children \
    --graph-id <sid> \
    --parent-node-id <parent_id> \
    --children-json /tmp/<sid>_<parent_id>_children.json
```

The CLI auto-discovers the thread id from sessions.db. Reads `graph.json`, validates each child (drops unknown keys, fails loud on missing `title`), assigns a fresh node id per child, appends, and atomically rewrites both `graph.json` and `graph.md`. Prints `{graph_id, parent_node_id, added: [ids...]}`. New children carry the discovered thread id; existing nodes keep theirs — a graph extended across conversations will hold a mix of thread ids per node, which is exactly the provenance the WebUI uses to route click-throughs.

## Verification

After `init` or `merge_children`:

- The success-line JSON on stdout names the affected node ids.
- `graph.json` parses; `nodes[]` has the expected count.
- `graph.md` opens with `# <name>` followed by a fenced `mermaid` block whose node ids match `graph.json` exactly.

If any of those fail, the most likely cause is malformed LLM output upstream. Re-run the LLM call once; on second failure, simplify the seed / parent context and try again.

## Design notes (for editors of this skill, not the runtime agent)

- **SCHEMA.md is the contract with the WebUI.** Any change to `graph.json` field semantics has to land there first. Optional node fields (`description`, `next_action`, `references`, `created_at`) are writer-only in Phase 1 — the WebUI ignores them — but they're persisted so Phase 2/3 can surface them without a re-run.
- **Single source of truth for Mermaid escaping.** `mermaid_safe()` in `scripts/cli.py` duplicates the minimal punctuation table from `paper-graph/scripts/mermaid.py:_MERMAID_ESCAPE_TABLE`. If paper-graph adds an entry, mirror it here.
- **Node ids are opaque.** `node-<16 hex>` from `secrets.token_hex(8)`. Provenance lives in `thread_id`. The WebUI only needs them to round-trip click events back to the JSON; no semantic encoding.
- **Append-only.** No re-parent, no rename, no delete — even with a flag. SCHEMA.md says cleanup is a user op; the skill honors that.
- **No concurrency lock.** Two simultaneous runs on the same `<graph_id>` race per SCHEMA.md open question #1. Acceptable for Phase 1.
- **Stderr is for errors only.** Success-path subcommands write a one-line summary (or JSON) to stdout and leave stderr empty. Hosts that tail stderr for failure signals can rely on that.
