# Stage 1 — Literature deepen via paper-navigator

**Shape note:** unlike the stage 2–5 references (which are slot-templates for the agent's *own* LLM call), this file is **orchestration prose**. The agent reads it, then constructs a brief for `paper-navigator` and invokes that skill. The output is `papers.json` — input to stages 2–5.

## Purpose

Take the chosen node's `context.json` (from pre-flight `extract_node_context`) and use it to drive `paper-navigator` to produce a ranked, evidence-grounded list of **10–20 papers specific to the node's `next_action`** — not a generic field survey, not a kitchen-sink reading list.

## Branch to invoke

**ITERATIVE branch.** This is the branch paper-navigator documents as "called from `research-survey` / `research-ideation`" — designed for sub-skill consumers, up to 3 rounds, breadth-first, ranked-table output. Idea-elaborate is the third such consumer.

The branch's own runbook and discipline live in paper-navigator itself; do not restate them here. References:
- `<EvoSkills>/skills/paper-navigator/SKILL.md` — branch selection, Five Red Lines, Paper Card format.
- `<EvoSkills>/skills/paper-navigator/references/iterative-collection.md` — the iterative-branch workflow.

## What to supply paper-navigator

From `context.json` produced by `extract_node_context`:

1. **Anchor references** — the chosen node's `references[]` array. These are URLs the idea-spark agent already canonicalized (full arxiv.org / doi.org links). Pass them to paper-navigator as known starts via the citation-graph traversal entry points — they're the user's anchor points for the direction; the tree they grow is the bulk of the shortlist.

2. **Concrete queries derived from `next_action`** — extract concrete technical elements from the next_action text (techniques, datasets, methods, evaluation regimes), one per query. Example: a `next_action` like *"Implement a three-stage fine-tuning pipeline starting from a base WavLM model and evaluate the learning curve on the far-field AMI dataset."* yields four single-concept queries: WavLM-based fine-tuning, three-stage fine-tuning protocols, learning curves under data scarcity, far-field AMI evaluation. **Do not stack keywords** — paper-navigator's own rule.

3. **Field context (do not query)** — the node's `description` and the ancestor chain titles. Supply these as **scoping context** to paper-navigator's briefing, not as query bodies. They tell paper-navigator what subfield to disambiguate within when names collide.

4. **Sibling titles as deduplication context** — pass the sibling-title list as "down-rank papers whose primary contribution is sibling angle X, since those will be elaborated separately." Keeps the stage 1 shortlist tight to *this* node.

5. **`focusing_phrase` if the user supplied one** — append as a scope constraint to all derived queries. *"…focus on data scarcity"* means every query carries an implicit low-resource / few-shot scope.

6. **Target budget** — set to `IDEA_ELABORATE_PAPER_BUDGET` env var, default **20**. Pass to paper-navigator as the iterative-branch shortlist target.

## What to NOT do

- **Do not invoke paper-navigator's LIST or POINT branches** for this stage. LIST stops at one rubric pass; we want the iterative breadth. POINT is for known papers; ours are unknown by design.
- **Do not feed paper-navigator a stacked-keyword query** like *"WavLM AMI fine-tuning learning curve"*. Split per its one-query-one-concept rule.
- **Do not call WebSearch / WebFetch as a shortcut for paper-navigator.** The skill ecosystem locks paper discovery to paper-navigator for quality — its Five Red Lines (track history, search-a-gap, one-query-one-concept, never hallucinate, quote-or-zero) exist precisely to prevent the hallucinations and low-quality blog results that generic web search produces.
- **Do not retry on empty results without changing the angle.** Paper-navigator's first Red Line forbids re-running the same query expecting a different outcome. If a round produces nothing, change the gap, not the synonyms.

## Output to write

Save paper-navigator's ranked-table output to:

```
./.idea-elaborate/<sid>/<node-id>/papers.json
```

Shape — a JSON array where each entry has at minimum:

```json
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
```

The `evidence_quote` / `evidence_field` columns are paper-navigator's quote-or-zero discipline — preserve them. Stages 2–4 will reference specific papers by `rank` index.

## Failure modes — surface and stop

- **paper-navigator not installed.** Stop and tell the user; stage 1 has no fallback. Idea-elaborate degrades to *"I can give you the node context and conclusions but cannot ground them in literature"* — that's a different deliverable and should be a user-confirmed pivot, not a silent fallback.
- **< 5 papers returned across all rounds.** Surface to the user before continuing to stage 2. The elaboration's grounding will be thin; the user might want to broaden the focusing phrase or accept the thin result explicitly.
- **Suspected hallucinated entries.** Paper-navigator's own quote-or-zero rule should prevent these; if they slip through, drop them and re-invoke with a tighter angle. Do not pass hallucinated entries to stage 2 — they corrupt every downstream stage.
