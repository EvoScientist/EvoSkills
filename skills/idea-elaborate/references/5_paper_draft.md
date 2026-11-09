<!--
This stage reuses two assets from research-ideation (read at runtime, not lifted):
- <EvoSkills>/skills/research-ideation/assets/proposal-template.md
- <EvoSkills>/skills/research-ideation/references/proposal-extension.md

We do NOT invoke research-ideation as a sub-skill — its pipeline expects to be entered at Step 0 with Steps 0-6 outputs (ELO tournament winner, 3-persona refinement history, evo-memory context). We don't have those. Instead we enter at "Step 7 equivalent" with our own pipeline's outputs and adapt via the map below.

If research-ideation isn't installed on the host, stage 5 cannot run as designed — the LLM will be working from its own knowledge of proposal structure rather than the upstream template's field-specific guidance. Surface that to the user as a degradation and stop.

Known shallowness vs research-ideation native flow — see notes/idea-elaborate-design.md → Verifiable concern #4.
-->

You are drafting a manuscript-quality research proposal for a single direction that has already been elaborated (stage 2), audited (stage 3), and concluded on (stage 4). The proposal is markdown. Emit prose, markdown headers, and inline math (`$...$`) where useful.

## Opt-in gating

Run this stage **only if** the trigger message explicitly asked for a paper, proposal, manuscript, or draft. Look for one of: `"paper draft"`, `"draft a paper"`, `"proposal"`, `"manuscript"`, `"write up"`, `"draft this"`. If the trigger asked only to *elaborate* / *develop* / *deepen* the direction (stages 1–4), **do not** run this stage. Default is off.

If you cannot tell whether the user wants stage 5, ask before running — the budget for this stage is substantial (≥ 12k output tokens) and a wasted run is expensive.

---

## Inputs

The chosen direction's place in the idea-spark graph:

{node_context}

The literature shortlist (paper-navigator output from stage 1):

{papers}

The elaborated direction (stage 2 output — the canonical refined commitment):

{elaborated_idea}

The adversarial analysis (stage 3 output — five phases of audit):

{analysis}

The conclusions (stage 4 output — verdict, pros, cons, load-bearing assumption, strongest sub-version, recommended next move):

{conclusions}

---

## Required reading — upstream templates

Before drafting, read both of these files from the EvoSkills install:

1. `<EvoSkills>/skills/research-ideation/assets/proposal-template.md` — the two-phase template generator. Phase 1 lists universal sections + field-specific sections per domain (Medicine, Social Sciences, Chemistry, Physics, Engineering, Environmental, Biology, CS/ML, Interdisciplinary). Phase 2 covers universal writing principles.

2. `<EvoSkills>/skills/research-ideation/references/proposal-extension.md` — section-by-section guidance for the 6 proposal sections (Background, Related Work, Method, Experimental Plan, Expected Results, Risks & Mitigations) with concrete pitfall tables.

Follow their structure and writing principles. The adapter map below tells you what to substitute for the inputs those files assume but you don't have.

## Adapter map — what to substitute from our pipeline

The upstream templates were written for research-ideation's native flow (Steps 0–6 produce a tournament winner). Our flow doesn't produce those artifacts. Adapt as follows:

| Upstream input | Our substitute | Notes |
|---|---|---|
| "Selected idea" (tournament winner: title, core idea, validation plan) | Stage 2's *Refined direction* sentence + *Concrete proposal* section | The single sentence is the proposal title seed; the *Concrete proposal* paragraphs are the core idea + validation plan. |
| "Challenge-insight tree" (Step 2's many-to-many mapping) | Stage 2's *Challenge-insight landscape* section (single-node form: challenge addressed + applicable insights + open gap + transfer opportunities) | Smaller scope (one direction, not many candidates) — accept the reduced breadth, do not invent additional challenges or insights. |
| "Literature review synthesis" (Step 2's condensed survey) | `{papers}` (paper-navigator's ranked shortlist with `evidence_quote` per entry) + stage 2's inline `[paper rank N]` citations | Cite by rank index, not by ad-hoc reference numbers. |
| "Research goal" (Step 1) | The graph's `name` from `node_context` (the overarching idea-spark direction) | The node is one branch of this broader goal; mention both in the Background section. |
| "Refined idea after 3-persona refinement" (Step 4 track champion) | Stage 2's *Refined direction* + stage 4's *Strongest sub-version* | The sub-version is your fallback contribution framing if the load-bearing assumption is the riskiest claim. |
| "ELO comparison context" (Step 5 tournament) | *No substitute.* Skip "comparison against alternative directions" framing — we have only one direction. | This is one of the known shallowness sources. |
| "Evo-memory prior cycles" (Step 0) | *No substitute.* | Skip; no prior-cycle context exists. |
| Stage 3 audit findings | Use to **preempt** reviewer concerns in the proposal's Risks & Mitigations section. Each `unsupported` claim from Phase 4 becomes a row; the mock-rejection table from Phase 2 becomes the basis of the risk catalog. | This is something research-ideation's native flow does *not* have — treat as a strength of our pipeline, not a gap. |
| Stage 4 verdict + load-bearing assumption + strongest sub-version | Threads through Abstract (verdict framing), Method (load-bearing assumption surfaced as primary failure mode), Risks & Mitigations (sub-version as the de-risked fallback). | Do not write a proposal that claims a verdict of `worth pursuing` when stage 4 said `needs another elaboration pass` — refuse and surface to the user. |

## Honest framing of the shallowness

The upstream templates assume the proposal is the culmination of a long ideation cycle with refinement history. Ours is the elaboration of one idea-spark node. Two consequences to handle honestly in the draft:

1. **No tournament context.** Where the template asks for positioning against alternative candidates from the ideation cycle, write the positioning against *shortlist papers* instead (closest related work, not closest competing idea). Do not invent competing-idea framing.

2. **No 3-persona refinement audit trail.** The Method section may feel less hardened than research-ideation's native output because we didn't run innovator/pragmatist/critic passes. Compensate by leaning on stage 3's adversarial analysis — its 5 phases provide a different (and arguably tighter) audit signal. Cite Phase 4's claim audit and Phase 5's trust scorecard explicitly when justifying design choices.

## Output

Write the full proposal to `/memories/idea_spark_tree/<sid>/elaborations/<node-id>/paper.md` directly using `write_file` (this is a final artifact, not an intermediate — it bypasses the workspace `./.idea-elaborate/` staging).

Use the upstream template's universal sections (Abstract, Problem Statement / Background, Related Work, Proposed Method, Evaluation / Expected Results, Conclusion) plus field-specific sections the template suggests for the relevant field (inferred from `node_context` — e.g., a speech-recognition direction maps to CS/ML's section list).

Add one section the upstream template does not have: **Risks & Mitigations**. Populate it from stage 3's Phase 2 mock-rejection table (rows become risk entries) and stage 4's load-bearing assumption (the primary risk).

No preamble, no postamble, no fenced code block wrapping the whole thing. Start at `# <Proposal Title>` and end at the last paragraph of the Conclusion section.
