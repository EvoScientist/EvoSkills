---
name: idea-elaborate
description: |-
  Use this skill to transform a specific "next action" or node from an **idea-spark graph** into a deep research plan, narrative, or formal paper proposal. It bridges high-level graph nodes to manuscript-quality research plans. Trigger when the user wants to "flesh out," "deepen," "commit to," or "generate a detailed plan" for a specific direction already stored in a research tree.

  **Do NOT trigger for:**
  1. Expanding a tree with new branches or child nodes (use `idea-spark`).
  2. Brainstorming new directions from scratch (use `research-ideation`).
  3. Editing or writing sections of an actual manuscript (use `paper-writing`).
  4. General "what would you do" queries lacking a specific existing graph node reference.

  This skill requires a specific `node-id` context from `$MEMORIES_DIR/idea_spark_tree/`. Do not invoke for standalone ideation or general research topics without referencing a specific, previously generated graph node direction.
allowed-tools: "write_file edit_file read_file execute"
metadata:
  author: EvoScientist
  version: '0.1.0'
  tags: [research, elaboration, idea-spark, proposal]
---

# Idea Elaborate

Turn one idea-spark graph node's `next_action` into a manuscript-quality elaboration: gathered literature, deepened idea, adversarial analysis, conclusions, and (opt-in) a paper-draft proposal. The skill is a thin orchestration — heavy lifting is in the prompt templates and in one sub-skill (`paper-navigator`).

## Conventions

Two identifiers run through the entire runbook; they're defined once here:

- **`<sid>`** — the **sanitized graph id**, the directory name `graph.json` lives in (e.g. `bridging-representation-gaps-in-low-resource-diarization`). Same sanitization rules as `idea-spark` (lowercase, `[a-z0-9-]+`, ≤64 chars).
- **`<node-id>`** — the opaque `node-<hex>` identifier of the chosen node within that graph (e.g. `node-1a49dba91977c766`). Stable across skill runs.

Both ride in the WebUI's trigger message verbatim. For typed prompts, the agent extracts them per Pre-flight Step 1.

## When to Use This Skill

Trigger when the user asks something like:

- *"Please elaborate on the next action for `<node title>` in the `<graph name>` idea-spark graph."* (the WebUI's pre-filled trigger phrasing)
- *"Deepen the `<node>` idea — develop a proposal for this direction."*
- *"Take the next action `<…>` and turn it into a research narrative."*
- *"Draft a paper proposal for the `<node>` direction in `<graph>`."* (this implicitly opts in to stage 5)
- *"Follow up on the `<node>` branch — what would the concrete study look like?"*

Skip when:

- *"Expand the `<node>` idea — give me a few more child directions."* → this grows the tree with new candidates; that's `idea-spark`'s `expand`. Idea-elaborate goes deeper on one node, not wider.
- *"What are some new research directions I could explore in `<field>`?"* → brainstorming a fresh direction without an existing node; that's `research-ideation`.
- *"Find me recent papers on `<topic>`."* / *"Read this paper."* → standalone literature task; that's `paper-navigator`.
- *"Plan the experiments for / review my draft of / write the related-work section of my paper."* → operates on a real manuscript, not a graph node; that's `paper-planning` / `paper-review` / `paper-writing`.

## Inputs and Output

**Inputs:**
- A **graph reference**: `<sid>` and `<node-id>` (see Conventions). Both ride in the WebUI's trigger message; for typed prompts the agent extracts them from chat context or asks the user.
- *(Optional)* a **focusing phrase** the user appends to the trigger ("…focus on data scarcity"). If present, the agent threads it through stages 2 and 3 as scope constraint.
- *(Optional)* an **explicit "draft a paper" request** in the trigger. Without it, stage 5 is skipped.

**Outputs (always):**
- `/memories/idea_spark_tree/<sid>/elaborations/<node-id>/notes.md` — stages 2–4 stitched: elaborated idea, adversarial analysis, conclusions.
- `/memories/idea_spark_tree/<sid>/elaborations/<node-id>/refs.json` — paper metadata cached from stage 1 for later inspection / re-use.

**Output (opt-in):**
- `/memories/idea_spark_tree/<sid>/elaborations/<node-id>/paper.md` — a manuscript-quality markdown proposal. Renderable to LaTeX/PDF downstream if needed; emitted as markdown so the user can verify content without a render step.

## Setup

**Env:**
- `IDEA_ELABORATE_PAPER_BUDGET` (optional) — soft cap on the number of papers stage 1 asks `paper-navigator` to surface. Default **20**.

**LLM:** the host agent uses its own model and API key. The skill emits prompt templates (`references/1_lit_deepen.md` … `references/5_paper_draft.md`) and validates what the host hands back; it does not authenticate or call any LLM provider itself.

**Working directory:** intermediates (extracted node context, per-stage LLM outputs before stitching) go under `./.idea-elaborate/<sid>/<node-id>/` — workspace-relative, one subdir per (graph, node), hidden so the workspace root stays tidy.

**Invocation discipline:**

- **Write JSON / markdown intermediates with the `write_file` tool, not shell heredocs.** Chains like `cat <<'EOF' > file ... EOF && uv run python …` are fragile: if the `EOF` marker sits on the same line as the next command, the shell keeps consuming, the file ends up containing the next invocation as literal text, the CLI then crashes on malformed input, and the error is easily mistaken for success when buried in a long compound output. `write_file` is unambiguous and atomic.
- **Run each `uv run python EvoScientist/skills/idea-elaborate/scripts/cli.py …` invocation as its own `execute` call.** Do not chain it with `ls`, `cat`, file creation, or another CLI subcommand using `&&`. A failure mid-chain produces stderr that is hard to attribute and easy to misread as success.
- **After every CLI call or LLM call, read the actual stdout/stderr before continuing.** Do not assume success because the runbook says success normally prints a JSON object — check that the JSON is present in the output you just received.
- **Use only two path shapes.** `/memories/...` for inspecting graph state and writing final elaboration artifacts (via the sandbox shell — `ls /memories/idea_spark_tree/<sid>/`, `read_file /memories/...`). `./.idea-elaborate/<sid>/<node-id>/...` for your own intermediates. Do not construct or pass any other path shape.

## Runbook

The skill orchestrates five **stages** bookended by a pre-flight extraction and a stitch. Each stage has its own LLM-prompt template under `references/`. Run sequentially; do not parallelize stages (later stages depend on earlier ones).

### Pre-flight Step 1 — Identify the graph and node

If the trigger came from the WebUI pre-fill, `<sid>` and `<node-id>` are present verbatim. If the user typed a free-form request and only named the graph + direction colloquially, resolve them: sanitize the graph name (per `idea-spark`'s `sanitize_id` semantics — or by listing `/memories/idea_spark_tree/` and matching against each graph's `graph.json` `name` field), then resolve the node by title-matching against that graph's `nodes[]`. Confirm with the user before proceeding if the lookup is ambiguous.

**Refuse to elaborate on a rejected node.** If `graph.json` shows `nodes[].rejected == true` for the chosen node or any of its ancestors (per the Phase 2 cascade rule), stop and surface to the user: do not silently expand a direction the user rejected.

### Pre-flight Step 2 — `extract_node_context` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/idea-elaborate/scripts/cli.py extract_node_context \
    --graph-id <sid> \
    --node-id <node-id> \
    --out ./.idea-elaborate/<sid>/<node-id>/context.json
```

Reads `/memories/idea_spark_tree/<sid>/graph.json` and produces a structured context blob: the chosen node's title / description / next_action / references; the full ancestor chain root → parent (titles + descriptions); sibling titles only (no descriptions); the node's `thread_id`. This is the canonical input for stages 2–5. Subsequent stages read it; do not re-derive the context downstream.

### Stage 1 — Literature deepen (invoke `paper-navigator`)

Read `references/1_lit_deepen.md` for the briefing to give `paper-navigator`. Invoke its **ITERATIVE branch** (the one designed for being called from another skill, up to 3 rounds, ranked-table output). Seed paper-navigator with:
- the chosen node's `references[]` (already canonical URLs after idea-spark's normalization),
- search terms derived from the `next_action` text,
- the focusing phrase if the user provided one.

Target a paper budget of `IDEA_ELABORATE_PAPER_BUDGET` (default 20). Save paper-navigator's ranked output to `./.idea-elaborate/<sid>/<node-id>/papers.json`.

Do NOT use WebSearch / WebFetch as a shortcut for paper-navigator — the skill ecosystem locks paper discovery to paper-navigator for quality reasons (its Five Red Lines discipline). If paper-navigator isn't installed, stop and tell the user; stage 1 has no fallback.

### Stage 2 — Idea elaboration (LLM)

Read `references/2_elaborate.md`. Substitute:
- `{node_context}` — contents of `context.json` from pre-flight step 2.
- `{papers}` — contents of `papers.json` from stage 1.
- `{focusing_phrase}` — the user-supplied focus if any, else empty.

Call the LLM (temperature ~0.3 — moderate, refining a fixed idea rather than divergent brainstorming). Strip code fences. Save the elaborated narrative to `./.idea-elaborate/<sid>/<node-id>/2_elaborate.md`.

### Stage 3 — Analysis (LLM)

Read `references/3_analyze.md`. Substitute:
- `{elaborated_idea}` — the file from stage 2.
- `{papers}` — same as stage 1.
- `{focusing_phrase}` — same as stage 2.

This stage runs adversarial protocols lifted from `paper-review` and `paper-planning` (rejection-risk table, reject-first summary, novelty stress test, claim-evidence audit, trust scorecard, limitation promotion). The template carries the discipline prose; the agent's job is substitution + LLM call + parse. Call the LLM (temperature ~0.2 — low, the protocols are structured). Strip code fences. Save to `./.idea-elaborate/<sid>/<node-id>/3_analyze.md`.

### Stage 4 — Conclusions (LLM)

Read `references/4_conclude.md`. Substitute:
- `{elaborated_idea}` — file from stage 2.
- `{analysis}` — file from stage 3.

Synthesize: pros / cons / load-bearing assumption / strongest sub-version / recommended concrete first move. Single pass, no iteration. Call the LLM (temperature ~0.2). Save to `./.idea-elaborate/<sid>/<node-id>/4_conclude.md`.

### Stage 5 — Paper draft (opt-in, LLM)

Run this stage **only if the user explicitly asked for a paper / proposal / manuscript** in the trigger message. Default off.

Read `references/5_paper_draft.md` for the input-adaptation prose, then read the two upstream assets it points at:
- `<EvoSkills>/skills/research-ideation/assets/proposal-template.md` — universal sections + field-specific table.
- `<EvoSkills>/skills/research-ideation/references/proposal-extension.md` — section-by-section guidance.

Substitute:
- `{node_context}`, `{papers}`, `{elaborated_idea}`, `{analysis}`, `{conclusions}` — files from earlier stages.

Call the LLM (temperature ~0.2, allow ~12000 max tokens — full proposal is long). Strip code fences. Save to `/memories/idea_spark_tree/<sid>/elaborations/<node-id>/paper.md` directly (this is a final artifact, not an intermediate).

Known limitation: research-ideation's proposal template assumes upstream context (challenge-insight tree, tournament-winning idea) that we don't have. Our adapter substitutes "selected idea" with the elaborated direction from stage 2; the resulting paper may read as somewhat less grounded than research-ideation in its native flow. This is the v1 trade-off — see Verifiable Concern #4 in `notes/idea-elaborate-design.md`.

### Final Step — `stitch_notes` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/idea-elaborate/scripts/cli.py stitch_notes \
    --graph-id <sid> \
    --node-id <node-id> \
    --elaboration-dir ./.idea-elaborate/<sid>/<node-id>/
```

Reads `2_elaborate.md`, `3_analyze.md`, `4_conclude.md` from the working dir and `papers.json` from stage 1. Stitches into:
- `/memories/idea_spark_tree/<sid>/elaborations/<node-id>/notes.md` — the combined narrative with section headers per stage.
- `/memories/idea_spark_tree/<sid>/elaborations/<node-id>/refs.json` — re-shaped paper metadata for the WebUI's discovery.

Prints `{sid, node_id, elaboration_path}` on success. The elaboration dir is created if it doesn't exist; existing content is overwritten (re-elaboration is a deliberate user action, not a guarded operation).

## Verification

After the final stitch step:
- The success-line JSON on stdout names the affected `<node-id>` and its virtual elaboration path.
- `notes.md` opens with `# Elaboration: <node title>` and has three top-level sections (`## Elaboration`, `## Analysis`, `## Conclusions`).
- `refs.json` parses; `papers[]` non-empty (unless paper-navigator returned nothing, in which case stage 1 should have failed loud — recheck).
- If stage 5 ran: `paper.md` exists in the elaboration dir and has the universal sections (Abstract / Problem / Related Work / Method / Evaluation / Conclusion) plus any field-specific ones the template added.

If any of those fail, the most likely cause is malformed LLM output upstream. Re-run the offending stage's LLM call once; on second failure, simplify the focusing phrase or narrow the node context and try again.
