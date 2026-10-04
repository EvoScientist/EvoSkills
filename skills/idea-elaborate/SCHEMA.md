# Idea Elaborate — skill schema (v1)

> **Design rationale:** [`notes/idea-elaborate-design.md`](../../../notes/idea-elaborate-design.md) — five-stage pipeline, input scope, accepted trade-offs.
> **WebUI read-side contract:** [`notes/idea-elaborate-webui-contract.md`](../../../notes/idea-elaborate-webui-contract.md) — trigger template, discovery, missing-skill behavior.

## Scope

This document is the canonical contract between the `idea-elaborate` skill (writer) and the EvoScientist WebUI (reader) for the **per-node elaboration artifacts** that live alongside an `idea-spark` graph. It covers **v1 only** — the read-only artifact view: notes + (opt-in) paper draft + refs.

Out of scope here, to land in later schema bumps:

- Linking elaboration artifacts back into `graph.json` via an explicit `nodes[].elaboration_path` field (currently the contract is loose-linked by directory naming convention).
- Cross-thread elaboration of the same node from a different thread (currently single-thread per the WebUI contract).
- Per-stage incremental writes / progress streaming (currently the skill writes only on completion).

## Memory layout

Elaboration artifacts live as a sibling directory inside the same `idea_spark_tree/<sid>/` directory that `idea-spark` writes to. `MEMORIES_DIR` is the global EvoScientist memory root (see `EvoScientist/paths.py`; default `~/.evoscientist/memories/`).

```
$MEMORIES_DIR/
  idea_spark_tree/
    <sid>/
      graph.json                     # idea-spark — canonical graph state
      graph.md                       # idea-spark — Mermaid projection
      graph.lock                     # idea-spark — present while idea-spark writes
      elaborations/
        <node-id>/
          notes.md                   # idea-elaborate — always written
          paper.md                   # idea-elaborate — written only if user opted in to stage 5
          refs.json                  # idea-elaborate — written if stage 1 produced papers
```

- `<sid>` is the sanitized graph id (same sanitization as `idea-spark` uses — see `idea-spark/SCHEMA.md`).
- `<node-id>` is the opaque `node-<hex>` identifier of the chosen node from `graph.json`. The directory name is the literal node id, preserving the round-trip to `nodes[].id`.

The `elaborations/` directory is created on first write and exists only for graphs that have been elaborated at least once. Its absence is **not** an error — it means no node in this graph has been elaborated yet.

## `notes.md` — stitched stage narrative

Authored by `idea-elaborate`. Written on every successful skill run. Plain markdown, structured so a WebUI can render it directly or extract sections by header.

### Structure

```markdown
# Elaboration: <node title>

## Elaboration
<stage 2 content — refined direction, concrete proposal, challenge-insight landscape, falsifiability, load-bearing assumptions, confidence>

## Analysis
<stage 3 content — 5 phases: reject-first, mock-rejection table, novelty stress, claim-evidence audit, trust scorecard>

## Conclusions
<stage 4 content — verdict, pros, cons, load-bearing assumption, strongest sub-version, recommended concrete next move>
```

### Rules

- Exactly one level-1 (`#`) header at the top, containing the chosen node's `title` (verbatim from `graph.json`).
- Exactly three level-2 (`##`) headers in this order: `Elaboration`, `Analysis`, `Conclusions`. The WebUI may safely split on these.
- Per-stage sub-headers are level 3+ (the skill downgrades the stage templates' `#` to `##` and their `##` to `###` at stitch time).
- If a stage was not run (rare — only possible if the run was aborted between stages), the corresponding section contains a single italic line: `*Stage <key> output not present at stitch time.*`. Readers MUST tolerate this.

## `paper.md` — manuscript-quality proposal (opt-in)

Authored by `idea-elaborate` **only when the user explicitly asked for a paper / proposal / manuscript / draft** in the trigger message. Absent otherwise.

Plain markdown — no LaTeX preamble, no document-class declarations. Renderable to LaTeX / PDF downstream if the user wants; emitted as markdown so the content is verifiable without a render step.

### Structure

Follows the universal sections from `research-ideation`'s `assets/proposal-template.md`:

- Title (level-1, the proposal's own title — likely a polished variant of the node's `title`)
- Abstract / Summary
- Problem Statement / Background
- Related Work
- Proposed Method / Approach
- Evaluation / Expected Results
- Conclusion

Plus field-specific sections inferred from the node's subject domain (CS/ML, Medicine, etc. — see the upstream template), plus one section the upstream does **not** have:

- **Risks & Mitigations** — populated from stage 3's Phase 2 mock-rejection risk table + stage 4's load-bearing assumption.

### Rules

- The skill MUST refuse to emit `paper.md` if stage 4's verdict was `needs another elaboration pass` — surface to the user and stop. Do not draft a paper for a direction that has not survived the audit.
- Reader (WebUI) MUST tolerate `paper.md` being absent — its absence means the user didn't ask for a draft, not that the elaboration failed.

## `refs.json` — paper metadata cache

Authored by `idea-elaborate` whenever stage 1 (literature deepen) produced a non-empty paper list. Absent otherwise.

JSON array. Each entry is one paper from paper-navigator's ranked iterative-branch output:

```json
[
  {
    "rank": 1,
    "title": "...",
    "authors": ["..."],
    "year": 2024,
    "venue": "...",
    "url": "https://arxiv.org/abs/...",
    "abstract": "...",
    "tldr": "...",
    "evidence_quote": "≤80 chars from abstract / tldr / snippet that supports inclusion",
    "evidence_field": "abstract|tldr|snippet"
  }
]
```

Field reference:

| Field | Type | Required | Notes |
|---|---|---|---|
| `rank` | integer | yes | 1-based ranking from paper-navigator. `notes.md` cites by `[paper rank N]`. |
| `title` | string | yes | Paper title. |
| `authors` | array of string | recommended | First-author last name suffices when the field is sparse. |
| `year` | integer | recommended | |
| `venue` | string | optional | Conference / journal / arxiv id when no venue. |
| `url` | string | yes | Canonical URL (arxiv.org / doi.org). Idea-spark's reference normalization rules apply. |
| `abstract` | string | optional | Full abstract when available. |
| `tldr` | string | optional | Semantic Scholar / paper-navigator TL;DR if available. |
| `evidence_quote` | string | yes | The ≤80-char span from `evidence_field` that grounds the paper's inclusion (paper-navigator's quote-or-zero discipline). |
| `evidence_field` | string | yes | One of `abstract` / `tldr` / `snippet` — the source the quote came from. |

Readers MUST tolerate extra fields (paper-navigator may add more downstream).

## Update contract

- Writes are **atomic**: serialize the new content to `<file>.tmp`, then `rename` to `<file>`. This prevents the WebUI from reading a half-written file.
- **`idea-elaborate` is the only writer** for `elaborations/<node-id>/`. The WebUI is the reader; user edits are not persisted back through this contract in v1.
- **Re-elaboration overwrites.** A second `idea-elaborate` run on the same `<node-id>` replaces all four files (`notes.md`, `paper.md` if opted in, `refs.json`). Re-elaboration is a deliberate user action — the skill does not guard against it. To preserve a previous elaboration, the user copies the directory before re-running.
- **No lock.** Unlike `graph.lock`, there is no `elaboration.lock`. Elaboration writes do not modify `graph.json`, so the `graph.lock` mechanism does not apply. Concurrent re-elaboration of the same node would race on `notes.md` / `paper.md`; this is accepted in v1 since elaboration is user-triggered (no automation re-runs) and the only collision vector is a user double-clicking the "Next action" affordance within the same minute.
- **The skill never deletes** the `elaborations/` directory or files within it. Cleanup is a user operation.

## Open questions for review

1. **Explicit linkback on the graph node.** Currently the WebUI must directory-poll for `elaborations/<node-id>/`. A future schema bump could add an optional `nodes[].elaboration_path` field on `graph.json` so a WebUI can surface "elaboration available" without polling. Costs: one schema bump for `idea-spark`, one new write site for `idea-elaborate`. Defer until WebUI integration tells us the poll is actually a problem.
2. **Per-stage incremental writes.** Long elaborations (~12k tokens for stage 5) finish in minutes. A future schema could let `idea-elaborate` write `notes.md` after stages 2–4 and `paper.md` later, so the WebUI can show partial results sooner. Costs: stitching logic gets messier, atomicity guarantees per-section rather than per-file. v1 punts on this.
3. **Cross-thread elaboration provenance.** The chosen node's `thread_id` is preserved in `context.json` (workspace) but not currently surfaced in `notes.md` / `paper.md`. If WebUI users want "this elaboration was produced from thread X" attribution, add a thread-id line to the top of `notes.md`. Cheap, no schema bump.
