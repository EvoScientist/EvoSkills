---
name: research-survey
description: "Generates structured literature survey reports from collected papers using a multi-stage pipeline: outline generation (query-type adaptive) → draft survey → section-by-section expansion → summary section refinement → final assembly. Produces survey-grade output with taxonomy-based method analysis, LaTeX formalizations, comparative tables, and dense citations. Use when: user wants a literature review, research survey, field overview, or systematic synthesis of multiple papers. Do NOT use for finding/searching papers (use paper-navigator), generating research ideas (use research-ideation), or writing a paper's Related Work section (use paper-writing)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '2.0.0'
  tags: [core, research, literature, survey, synthesis]
---

# Research Survey

Generates high-quality, survey-grade literature reviews from papers collected by `paper-navigator`.

```
paper-navigator (collect 30-120 papers)
    ↓
Stage 1: Generate Outline (query-type adaptive structure)
    ↓
Stage 2: Draft Survey (outline + top-30 papers)
    ↓
Stage 3: Expand Sections (draft + all papers, section-by-section)
    ↓
Stage 4: Refine Summary Sections (Abstract/Intro/Conclusion)
    ↓
Stage 5: Assemble + References
```

## When to Use

- User asks for a "literature review", "survey", "field overview", or "systematic review"
- User has collected papers and wants them synthesized into a structured report
- User wants to understand the full landscape of a research field

## When NOT to Use

- **Finding papers** → use `paper-navigator` first, then come here
- **Generating research ideas** → use `research-ideation`
- **Writing a Related Work section for a paper** → use `paper-writing`

## Dependency: paper-navigator

This skill requires papers as input. If the user hasn't provided papers, **first invoke `paper-navigator`** (Workflow 1, target 30-120 papers) to collect them.

**CRITICAL: All paper discovery MUST use the `paper-navigator` skill and its scripts (scholar_search, citation_traverse, arxiv_monitor, recommend, etc.). Using WebSearch, WebFetch, or any generic web search tool for finding papers is PROHIBITED.** Generic web search cannot access Semantic Scholar, citation graphs, or academic recommendation systems. Only `paper-navigator` provides the academic search infrastructure needed for survey-quality literature collection.

---

## Stage 1: Generate Outline

**This is a two-phase process.** Different fields have different survey conventions — a clinical systematic review looks nothing like a CS methods survey. First generate a domain-appropriate template, then create the detailed outline.

### Phase 1A: Generate Domain-Specific Survey Template

Before outlining, identify the field and adapt the structure:

1. **Identify the field** from the user's goal and collected papers
2. **Select section names and organization logic** using the field-specific conventions in `assets/survey-template.md` (e.g., medicine organizes by intervention type and follows PRISMA; chemistry organizes by reaction class; social sciences organize by theoretical perspective)
3. **Add field-specific sections** (e.g., Risk of Bias Assessment for medicine, Structure-Property Relationships for materials, Ethical Considerations for human-subjects research)
4. **Determine comparison table dimensions** appropriate to the field

### Phase 1B: Create Detailed Outline

With the domain-specific template as the framework, generate the outline:

#### Query Type Classification

| Type | Example | Structure |
|------|---------|-----------|
| **A: Single-topic deep dive** | "Catalyst design for electrochemical CO2 reduction" | Intro → Problem Definition → **Methods (by mechanism/approach)** → Evaluation → Challenges → Conclusion |
| **B: Multi-topic parallel** | "Drug resistance mechanisms and therapeutic strategies in cancer immunotherapy" | Intro → **Topic 1 (definition + methods)** → **Topic 2 (definition + methods)** → Evaluation → Challenges → Conclusion |
| **C: Pipeline/stage-based** | "From sample preparation to data analysis in single-cell RNA sequencing" | Chapters organized by workflow stages |

#### Outline Requirements

The outline is NOT a simple heading list — it's a **blueprint with meta-instructions** for each section. For each `## Section`:

- Include `[Instruction: ...]` specifying what the section must contain
- Specify required tables with field-appropriate columns
- For main body sections: mandate taxonomy by underlying principle/mechanism, NOT chronology
- Include any field-required elements (e.g., PRISMA flowchart for medical systematic reviews, mathematical formalism for physics)

See `references/survey-methodology.md` for full outline generation rules and `assets/survey-template.md` for field-specific conventions.

---

## Stage 2: Draft Survey

Generate a complete draft from the outline using the **top-30 most relevant papers**.

- Use numbered citations [1], [2, 3] throughout
- Follow the outline's meta-instructions strictly
- Each methods section must build a taxonomy and include comparison tables
- Problem definition must include LaTeX formalization (`$$...$$`)

---

## Stage 3: Expand Sections

Expand each non-summary section using **all collected papers** (30-120). This is where survey-grade depth is achieved.

### Section Expansion Targets

| Section Type | Target Length | Focus |
|---|---|---|
| **Methods** | 6000+ words per paradigm chapter | Technical narratives, mechanism analysis, comparison tables |
| **Evaluation** | 3500+ words | Benchmark taxonomy, metric analysis, SOTA summary |
| **Challenges** | 3000+ words | Problem definition + evidence + opportunity per challenge |
| **Applications** | 3000+ words | Real-world use cases with specific achievements |
| **Problem Definition** | 2000+ words | LaTeX formalization, constraints, assumptions |
| **Other** | 2500+ words | Default |

### Expansion Rules

1. **Thematic coherence**: Keep same themes and narrative flow as draft — don't introduce unrelated topics
2. **Cite comprehensively**: Use as many relevant papers from the full collection as possible
3. **Survey-grade depth**: Multi-paragraph technical narratives per method family, not shallow bullet points
4. **For each paradigm/method family, include**:
   - Technical narrative: How it works, theoretical assumptions, nuances between papers
   - Critical analysis: Why effective, trade-offs, failure modes
   - Comparative analysis table: Method | Core Mechanism | Key Advantage | Limitation | Performance

---

## Stage 4: Refine Summary Sections

After all content sections are expanded, refine the **summary sections** (Abstract, Introduction, Conclusion):

1. Generate a condensed summary of each expanded section
2. Use all section summaries as context to rewrite Abstract, Introduction, Conclusion
3. This ensures summary sections accurately reflect the full survey content

### Summary Section Standards

**Abstract** (300-500 words):
- Continuous narrative, NO bullet points or bold labels
- Must cover: background → gap → scope → key findings → outlook

**Introduction**:
- Continuous narrative, NO subsections or bullet points
- Must cover: research background → why traditional methods fail → method summary → scope & organization

**Conclusion**:
- Summarize findings, state which paradigm is most promising
- Respond to user's original research goal
- Provide clear "next step" recommendation

---

## Stage 5: Assemble Final Survey

Assemble sections in outline order, then append formatted references:

```
**1. Title** (Year). _Authors_. *Venue*. Citations: N. [[Link]](url)
```

Save to `/artifacts/survey-{topic}-{date}.md`.

---

## Core Quality Principles

1. **Build taxonomy, don't enumerate**: Cluster papers by technical mechanism, not chronology. This is the defining characteristic of a survey vs. a summary.

2. **Critical insight over description**: For EVERY method, analyze WHY it works, WHAT trade-off it makes, WHERE it fails. This separates survey-grade writing from shallow summaries.

3. **Goal-centric filtering**: Every piece of information must answer "How does this help achieve the research goal?" Discard information that doesn't serve the goal, even if it's interesting.

4. **Strict terminology fidelity**: Use the user's exact technical terms. Do NOT drift to related but different concepts.

5. **Dense citations**: Ground ALL claims with numbered citations [X]. Nearly every sentence should reference at least one paper.

6. **Zero vagueness**: Replace generic statements with specific method names, dataset names, metric values, and problem descriptions.

7. **Visual structure**: Use Markdown tables extensively — paradigm comparison, intra-paradigm method comparison, benchmark tables, metric tables.

---

## Reference Materials

| Resource | Location | Purpose |
|----------|----------|---------|
| Multi-stage pipeline details | `references/survey-methodology.md` | Full methodology: outline rules, section standards, expansion targets |
| Section quality checklist | `references/section-quality-checklist.md` | Per-section verification checklist before finalizing |
| Survey output template | `assets/survey-template.md` | English Markdown template with section structure, table formats, and placeholder guidance |

---

## Handoff

| From → To | When |
|-----------|------|
| `paper-navigator` → here | Papers collected, user wants synthesis |
| Here → `research-ideation` | Survey reveals research gaps worth pursuing |
| Here → `paper-writing` | Survey informs Related Work section of a paper |
| Here → `paper-planning` | Survey provides literature context for story design |
