---
name: paper-graph
description: "Use this skill to map the **genealogical lineage and historical progression** of a research field. It is designed to visualize the **evolutionary path of ideas**, showing how technical challenges in earlier works were addressed by subsequent research improvements. The final deliverable is a Markdown file with embedded Mermaid diagrams the user can paste into a viewer or commit to their repo. Trigger this when the user needs to understand the **developmental trajectory of a topic**, the 'family tree' of a model, or how a research line matured over multiple years. Do NOT trigger for queries seeking **inventories of specific artifacts**, such as lists of common datasets, benchmarks, or libraries. Avoid this for finding a single 'latest' paper, performing simple keyword search, or conducting head-to-head technical comparisons between specific models. This skill is meant for synthesizing a **chronological narrative of improvement** across multiple works, not for cataloging currently available resources or one-off paper retrieval."
allowed-tools: "write_file edit_file read_file execute"
metadata:
  author: EvoScientist
  version: '0.1.1'
  tags: [research, literature-review, graph, mermaid]
---

# Paper Graph

Build a Markdown report with embedded Mermaid diagrams showing how research on a user-specified topic (or paper) evolved — clustered into challenges → solutions and traced as per-solution evolution paths.

The skill has no outbound LLM dependency. The host agent provides all LLM calls; the skill provides deterministic data fetchers (S2 / DeepXiv), prompt templates, markdown parsers, and Mermaid renderers. Run the runbook below step-by-step.

## When to Use This Skill

Trigger when the user asks something like:

- "Show me the history of <topic>" / "How did <topic> evolve?"
- "Where does <paper> stem from?" / "What did <paper> build on?"
- "What are significant improvements / follow-ups to <paper>?"
- "Trace the lineage of ideas in <field>" / "Give me a literature taxonomy of <field>"
- "Citation tree of <paper>" / "Idea trace of <topic>"

Skip when:
- The user just wants a one-paper summary or single search hit (no relational/evolutionary aspect).
- The request is for non-academic citation work.
- The user explicitly wants a plain bibliography rather than a graph.

---

## Inputs and Output

**Inputs:**
- A **research query**: a topic, a seed paper title/citation, or a hybrid. Free-form text.
- **Output path** (required): path for the final Markdown report. If not given, ask before running.
- *(Optional)* number of papers to fetch (`--n` flag on `fetch_papers`). Default **10**.
- *(Optional)* Mermaid theme `light` or `dark` (`--theme` on render steps, or `MERMAID_THEME` env). Default **light**.

**Output:** a single Markdown file at the user-specified path with these sections:
1. **Research goal** (extracted from the query)
2. **High-level taxonomy** — one Mermaid graph: root → challenges → solutions → paper references
3. **Per-solution evolution paths** — one Mermaid graph per solution, showing paper-to-paper "evolution from" edges, evolution points, open challenges
4. **Paper appendix** — the numbered list of papers with title / year / authors / abstract / conclusion excerpt

Mermaid is just text inside ```` ```mermaid ```` fences — the file renders directly in GitHub, Obsidian, VS Code with the Mermaid extension, etc.

---

## Setup

**Required env (the skill fails verbosely if missing):**
- `S2_API_KEY` — Semantic Scholar API key.

**Optional env:**
- `DEEPXIV_API_TOKEN` (or `DEEPXIV_TOKEN`) — DeepXiv arXiv search fallback. Install with `pip install deepxiv-sdk`; auto-provision with `deepxiv token`. Without it, S2 must fill the cite-number budget on its own.
- `MERMAID_THEME` — `light` (default) or `dark`. Overridden by `--theme` on each render call.

**LLM:** the host agent uses its own model and API key. The skill emits prompt templates and parses responses; it does not authenticate or call any LLM provider.

**Working directory:** create one dir per run, anchored **relative to your current working directory** (e.g. `./<basename>.work/`). Avoid absolute system paths like `/tmp/...` — some harnesses sandbox the shell and the file-read tools to different filesystem roots, so an absolute path can appear writable to one and missing to the other. A cwd-relative path works the same everywhere. Run `pwd` once at the start if unsure.

Suggested layout (assuming final report goes to `<output>`):

```
<output>.work/
├── query.txt                user query (verbatim)
├── seed.json                resolve_seed_papers
├── seed_block.txt           format_seed_block
├── parsed_query.json        LLM: parse_query output
├── goal_block.txt           build_goal_block (reused in steps 8, 10, 11)
├── papers.json              fetch_papers → prefetch_sections → classify-merged
├── papers_input.txt         format_papers (full set)
├── classify_raw.json        LLM: classify output (consumed by merge_classifications)
├── core_filter.json         compute_core_filter (+ core_filter.json.allowed.txt)
├── papers_input_core.txt    format_papers (CORE-only; + papers_input_core.txt.allowed.txt)
├── outline_raw.md           LLM: outline output
├── outline.json             parse_outline summary
├── outline_mermaid.json     render_outline_mermaid
├── solutions/<key>.json     per-solution context (one file per solution)
├── parsed/<key>.json        parse_detail output (used by step 11 audit)
├── details/
│   ├── <key>_input.txt      format_papers (per-solution allowed set; + .allowed.txt sibling)
│   ├── <key>_raw.md         LLM: detail output
│   └── <key>.json           render_detail_mermaid (consumed by assemble)
├── verdicts/<key>.json      [{source_n, target_n, verdict}] from audit
└── <run>.log.jsonl files    one next to each subcommand output, default-on
```

Filenames are agent-chosen — these are recommendations to match what the runbook below references. `<key>` is the solution key string `<s_major>.<s_minor>` (e.g. `1.1`). Every `format_papers` call writes a sibling `<out>.allowed.txt` containing the `(N), (N), ...` form ready to drop into a `{allowed_numbers}` placeholder.

---

## Runbook

Each step is either a **CLI** call (`uv run python EvoScientist/skills/paper-graph/scripts/cli.py <subcmd> …`) or an **LLM** call (the host agent reads a template from `references/`, substitutes the placeholders, and calls its model). Run sequentially; the detail step (step 10) and the audit step (step 11) can fan out per-solution / per-edge if the host supports concurrent tool calls.

**Placeholder syntax in `references/*.md`.** Single-brace `{name}` is a template slot the host must substitute. Double-brace `{{...}}` is an escaped literal brace — it appears in the prompt body when the example JSON the LLM is asked to emit contains braces. Substitute only single-brace slots; leave `{{` and `}}` alone (they're for the LLM to read as `{` and `}` in its output).

### Step 1 — Save the user query

Write the user's verbatim query to `<workdir>/query.txt`. Do not paraphrase. Multi-line queries are fine.

### Step 2 — `resolve_seed_papers` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py resolve_seed_papers \
    --query-file <workdir>/query.txt \
    --out <workdir>/seed.json
```

Outputs a JSON array of S2-shape paper records for any arxiv IDs detected in the query. Empty array when none are present or all lookups fail.

### Step 3 — `format_seed_block` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py format_seed_block \
    --seed <workdir>/seed.json \
    --out <workdir>/seed_block.txt
```

Renders the seed papers into the `{seed_block}` prompt fragment used in step 4. Empty input → empty output (the placeholder collapses cleanly).

### Step 4 — `parse_query` (LLM)

Read `EvoScientist/skills/paper-graph/references/parse_query.md`. Substitute `{seed_block}` with the contents of `<workdir>/seed_block.txt` and `{query}` with the contents of `<workdir>/query.txt`. Call the LLM (low temperature, ~0.1).

Parse the response as JSON with this exact shape:

```json
{"goal": "<one sentence>",
 "searches": ["<keyword phrase 1>", "<keyword phrase 2>", "..."],
 "definitions": {"<term>": "<one-sentence definition>", "...": "..."}}
```

Per the prompt's own instructions, `searches` should contain 2–4 phrases each of 2–5 keywords (these are two different counts — phrases vs. keywords-per-phrase).

Strip code fences if the model added them. Validate that `goal` is non-empty and `searches` is a non-empty list of strings. If the response is malformed, re-prompt the LLM once; on second failure, abort with a clear error message.

Save the validated JSON to `<workdir>/parsed_query.json`.

### Step 5 — `fetch_papers` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py fetch_papers \
    --parsed-query <workdir>/parsed_query.json \
    --seed <workdir>/seed.json \
    --n 10 \
    --out <workdir>/papers.json
```

Uses S2 multi-search (one S2 query per `searches[]` entry) with DeepXiv fallback to top up to `--n` papers. Output is a JSON array of S2-shape paper dicts. If S2 returns nothing and DeepXiv is unavailable, exits non-zero — re-prompt step 4 with sharper search phrases.

### Step 6 — `classify` (LLM)

First build the full `{papers_input}` block:

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py format_papers \
    --papers <workdir>/papers.json \
    --out <workdir>/papers_input.txt
```

Read `references/classify.md`. Substitute `{goal}` with the `goal_sentence` (the single-sentence string at `parsed_query.json["goal"]` — bare, no definitions block here) and `{papers_input}` with the text file above. Call the LLM (low temperature, no reasoning needed — it's a discrete cataloging decision). Strip any leading/trailing code fences if the model added them.

Save the raw response verbatim to `<workdir>/classify_raw.json`. Expected shape:

```json
{"classifications": [
  {"n": 1, "label": "CORE", "reason": "..."},
  {"n": 2, "label": "ADJACENT", "reason": "..."},
  {"n": 3, "label": "REJECT", "reason": "..."},
  ...
]}
```

Then merge into papers.json via the CLI (validates shape + applies failure-soft fallback to every-CORE if validation fails):

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py merge_classifications \
    --classifications <workdir>/classify_raw.json \
    --papers <workdir>/papers.json \
    --out <workdir>/papers.json
```

`merge_classifications` always exits 0; on validation failure it applies an all-CORE safety-net and prints a `… (FALLBACK: <reason>)` suffix on the stdout success line. When you see that suffix, re-prompt the LLM once; if the second attempt also falls back, accept the all-CORE result and proceed — every paper just feeds the outline as CORE. On a clean run the success line shows the per-label counts and no FALLBACK suffix. Downstream subcommands (`parse_outline`, the renderers, `assemble_report`) read these labels via `_label_of`.

### Step 7 — `prefetch_sections` (CLI, deterministic, best-effort)

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py prefetch_sections \
    --in <workdir>/papers.json \
    --out <workdir>/papers.json
```

Mutates each paper dict in place by setting `_conclusion_section`. REJECT-labeled papers are skipped to save quota. Failures are silent; a paper without an arxiv ID or without a fetchable section just gets `_conclusion_section: null`.

After this step, any subsequent `format_papers` call automatically embeds each paper's `_conclusion_section` into the formatted block (under a `Discussion/Conclusion excerpt:` header) — that's how the outline and detail prompts get the OC-source signal the prompt templates reference. No extra step required.

### Step 8 — `outline` (LLM)

Materialize the two prompt fragments that recur from here on — `goal_block` (the `{goal}` substitution) and `core_filter` (the CORE-only filter + its `{allowed_numbers}` sidecar) — as files on disk. Steps 10 and 11 read these files back, so the agent never has to carry them as conversation state.

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py build_goal_block \
    --parsed-query <workdir>/parsed_query.json \
    --out <workdir>/goal_block.txt

uv run python EvoScientist/skills/paper-graph/scripts/cli.py compute_core_filter \
    --papers <workdir>/papers.json \
    --out <workdir>/core_filter.json
```

`compute_core_filter` writes the index JSON to `--out` and the matching `(N), (N), ...` `{allowed_numbers}` form to a sibling `<out>.allowed.txt`. On a no-CORE classifier outcome it falls back to every paper and prints `(FALLBACK: …)` — the run continues.

Build the CORE-only `{papers_input}` (also emits a sibling `.allowed.txt`, redundant here but consistent with Step 10):

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py format_papers \
    --papers <workdir>/papers.json \
    --filter <workdir>/core_filter.json \
    --out <workdir>/papers_input_core.txt
```

Read `references/outline.md`. Substitute:
- `{goal}` — contents of `<workdir>/goal_block.txt`.
- `{papers_input}` — contents of `<workdir>/papers_input_core.txt`.
- `{allowed_numbers}` — contents of `<workdir>/core_filter.json.allowed.txt`.

Call the LLM (low temperature, ~0.2; allow ~8000 max tokens). Strip any leading/trailing code fences from the response — the prompt instructs the model to emit raw Markdown but a fence sometimes slips through. Save the cleaned Markdown to `<workdir>/outline_raw.md`.

### Step 9 — `parse_outline` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py parse_outline \
    --raw <workdir>/outline_raw.md \
    --papers <workdir>/papers.json \
    --out <workdir>/outline.json \
    --solutions-dir <workdir>/solutions
```

Writes the outline summary plus one `solutions/<key>.json` context file per solution. Schema of each context file (consumed in steps 10 and 12):

```json
{
  "challenge_idx": 1,
  "challenge_name": "Quality of random-projection targets",
  "solution_key": [1, 1],
  "solution_key_str": "1.1",
  "solution_name": "Optimization of the BEST-RQ pre-training objective",
  "paper_nums": [1, 3, 99],
  "allowed": [1, 3]
}
```

`paper_nums` is the verbatim LLM-emitted set; `allowed` is the same set filtered to keep only valid CORE indices (note above: `99` was an LLM hallucination, dropped from `allowed`), with a fallback to **all** CORE indices when filtering would otherwise empty the list. `format_papers --filter <solutions/key.json>` and `parse_detail --context <solutions/key.json>` both read `allowed` out of this file automatically — never `paper_nums`.

Exits with code 4 and a stderr diagnostic if the outline contained no parseable `## Challenge N:` headers. Re-prompt step 8 once; on second failure, lower `--n` in step 5 or sharpen the query.

### Step 10 — `detail` (LLM, per solution)

> **CRITICAL — read "Fan-out task brief" below BEFORE delegating this step to subagents.** A subagent prompt that points at SKILL.md or asks to "run paper-graph for solution X" will restart the whole workflow from Step 1 in a separate workdir, and its output will be unusable by the parent run.

Read `references/detail.md` **once** at the start of this step; substitute per-solution in the orchestrator. The subagents you fan out to never read templates themselves.

For each `<workdir>/solutions/<key>.json` produced in step 9:

(a) Build the per-solution `{papers_input}`. `format_papers --filter` accepts a solution context file directly (it reads the `allowed` array out of it); the matching `{allowed_numbers}` string lands in the `.allowed.txt` sibling.

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py format_papers \
    --papers <workdir>/papers.json \
    --filter <workdir>/solutions/<key>.json \
    --out <workdir>/details/<key>_input.txt
```

(b) Substitute into `references/detail.md`:
- `{goal}` — contents of `<workdir>/goal_block.txt` (the file built in Step 8).
- `{challenge_name}` — from the solution context (`challenge_name`).
- `{solution_name}` — from the solution context (`solution_name`).
- `{papers_input}` — from `<workdir>/details/<key>_input.txt`.
- `{allowed_numbers}` — from `<workdir>/details/<key>_input.txt.allowed.txt`.

Call the LLM (temperature ~0.2; allow ~12000 max tokens to fit scratchpad + tree). Save the raw response to `<workdir>/details/<key>_raw.md`.

(c) Parse it (output goes to a sibling `parsed/` dir, not `details/`, so step 13's `assemble_report` doesn't pick up parse outputs as render outputs):

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py parse_detail \
    --raw <workdir>/details/<key>_raw.md \
    --context <workdir>/solutions/<key>.json \
    --out <workdir>/parsed/<key>.json
```

The parsed JSON's `edges` list is the input to Step 11.

If the host supports concurrent tool calls, fan all per-solution LLM calls + their parse_detail follow-ups out in parallel.

**Fan-out task brief (when delegating step 10b to a subagent per solution).** The subagent's prompt must be self-contained: do **not** point the subagent at SKILL.md, do **not** instruct it to "run paper-graph for solution X," and do **not** give it any CLI invocation to run. The orchestrator does the substitution itself and hands the subagent only:
- The fully-substituted prompt string (already with `{goal}`, `{challenge_name}`, `{solution_name}`, `{papers_input}`, `{allowed_numbers}` filled in).
- The expected response shape: raw Markdown evolution tree per `references/detail.md`'s output spec.
- An explicit instruction: *"Call your LLM with the prompt below and return only the raw Markdown response. Do not read any other file, do not run any shell command, do not invoke any other skill."*

Do **not** point the subagent at SKILL.md, do **not** instruct it to "run paper-graph for solution X", and do **not** give it any CLI invocation to run. The subagent returns the Markdown text; the orchestrator writes it to `<workdir>/details/<key>_raw.md` and runs `parse_detail` itself. **A subagent that re-reads SKILL.md will restart the whole workflow from step 1** — the fix is to keep the subagent prompt bounded as above.

### Step 11 — `audit_edge` (LLM, per edge)

> **CRITICAL — read "Fan-out task brief" below BEFORE delegating this step to subagents.** Same orchestration failure mode as Step 10: a subagent pointed at SKILL.md restarts the whole workflow.

Read `references/audit_edge.md` **once** at the start of this step; substitute per-edge in the orchestrator. The subagents you fan out to never read templates themselves.

For each `<workdir>/parsed/<key>.json`'s `edges` list, audit each edge against the source / target abstracts and conclusion excerpts.

For every `{source_n, target_n, gap}` edge in the solution:
- Look up source paper = `papers[source_n - 1]` and target = `papers[target_n - 1]` from `<workdir>/papers.json`.
- Substitute the placeholders in `references/audit_edge.md`: `{m_n}`, `{m_title}`, `{m_abstract}` (truncated to 1500 chars), `{m_excerpt}` (the `_conclusion_section` or `(no excerpt)`, truncated to 1500 chars), `{n_n}`, `{n_title}`, `{n_abstract}`, `{n_excerpt}`, `{gap_text}`.
- Call the LLM (low temperature ~0.1, reasoning off, ~600 max tokens). Parse the response:

```json
{"verdict": "SUPPORTED_BY_ABSTRACT" | "SUPPORTED_BY_SECTION" | "INFERRED" | "REJECT",
 "reason": "<one sentence>"}
```

On parse failure, default the verdict to `INFERRED` (the edge survives rendering but is visibly marked).

**Fan-out task brief (when delegating per edge or per solution to subagents).** Same discipline as step 10: do **not** point the subagent at SKILL.md, do **not** instruct it to "run paper-graph audit," and do **not** give it any CLI invocation. The orchestrator does the substitution itself and hands the subagent only:
- The fully-substituted prompt string (already with `{m_n}`, `{m_title}`, `{m_abstract}`, `{m_excerpt}`, `{n_n}`, `{n_title}`, `{n_abstract}`, `{n_excerpt}`, `{gap_text}` filled in).
- The expected response shape: a JSON object `{"verdict": "...", "reason": "..."}`.
- An explicit instruction: *"Call your LLM with the prompt below and return only the JSON verdict object. Do not read any other file, do not run any shell command, do not invoke any other skill."*

The subagent returns the verdict JSON; the orchestrator aggregates per-solution lists into `<workdir>/verdicts/<key>.json`. A subagent given a prompt that references SKILL.md will restart the workflow from step 1 — keep the brief bounded.

Collect all per-solution verdicts into `<workdir>/verdicts/<key>.json` as a flat list:

```json
[{"source_n": 1, "target_n": 3, "verdict": "SUPPORTED_BY_ABSTRACT"}, ...]
```

### Step 12 — `render_outline_mermaid` + `render_detail_mermaid` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py render_outline_mermaid \
    --raw <workdir>/outline_raw.md \
    --papers <workdir>/papers.json \
    --out <workdir>/outline_mermaid.json \
    [--theme dark]
```

For each solution:

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py render_detail_mermaid \
    --raw <workdir>/details/<key>_raw.md \
    --context <workdir>/solutions/<key>.json \
    --papers <workdir>/papers.json \
    --verdicts <workdir>/verdicts/<key>.json \
    --out <workdir>/details/<key>.json \
    [--theme dark]
```

### Step 13 — `assemble_report` (CLI, deterministic)

```bash
uv run python EvoScientist/skills/paper-graph/scripts/cli.py assemble_report \
    --parsed-query <workdir>/parsed_query.json \
    --outline <workdir>/outline_mermaid.json \
    --details-dir <workdir>/details \
    --papers <workdir>/papers.json \
    --out <user-supplied output path>
```

Walks `details/` for every render JSON, sorts by `(challenge_idx, s_major, s_minor)`, writes the final Markdown report at the user-supplied output path. Only `*.json` files containing a `mermaid` field are consumed — `*_raw.md`, `*_input.txt`, and any non-render JSON sitting alongside are skipped (and counted on stdout if any). This is why parse_detail outputs go to a sibling `parsed/` dir per the workdir layout, not into `details/`.

---

## Verification

After step 13 completes, read the first ~40 lines of the report to confirm:
- The taxonomy has at least 2 challenges and each has at least 1 solution.
- Each Mermaid block opens with ```` ```mermaid ```` and closes with ```` ``` ````.
- The paper appendix exists at the bottom of the file.

If any of those fail, the most likely cause is the outline LLM (step 8) returning malformed Markdown. Re-run step 8; if it fails twice, lower `--n` on step 5 or sharpen the query.

---

## Design notes (for editors of this skill, not the runtime agent)

- **No outbound LLM dependency**: the skill exposes data fetchers, prompt templates (`references/*.md`), parsers, and renderers. The host agent is the LLM provider. This is why there's no `OPENROUTER_API_KEY` requirement and no `llm.py`.
- **Single source of truth for the detail parser**: `mermaid._parse_detail_markdown` is called by both `detail_to_mermaid` (rendering) and the `parse_detail` CLI subcommand. Any change to scratchpad stripping, paper/EP/OC extraction, or hallucination dropping propagates to both.
- **`references/seed_paper_block.md` is an internal template fragment** consumed by `format_seed_block`; the runtime agent never substitutes its placeholders directly. The other five `references/*.md` files are the agent-facing templates the runbook references.
- **Themed Mermaid**: `mermaid.py` defines `LIGHT_THEME` and `DARK_THEME`. The renderer subcommands resolve the theme by name (CLI arg) → `MERMAID_THEME` env → `"light"`. Each render emits a self-contained Mermaid graph (init directive + classDefs + linkStyle).
- **JSONL logging is default-on**: every subcommand writes `<out>.log.jsonl` next to its output unless `--log none` is passed. These logs are for the human developer iterating on the skill — the runtime agent should not read them back.
- **Failure mode preference**: loud over silent. Missing keys, malformed LLM output, zero papers from search — all abort with a printed reason rather than producing a degraded artifact.
- **English-only**: the upstream `paper-graph` prompts emitted bilingual labels; this skill strips Chinese and keeps English only.
