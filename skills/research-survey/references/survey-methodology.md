# Survey Generation Methodology

Multi-stage pipeline for producing high-quality academic literature surveys. Based on production-tested approach from Yiscientist1203.

## Pipeline Overview

```
Papers (from paper-navigator)
    ↓
Stage 1: Outline Generation (top-30 papers → adaptive structure)
    ↓
Stage 2: Draft Survey (outline + top-30 papers → full draft)
    ↓
Stage 3: Section Expansion (draft sections + all papers → deep content)
    ↓
Stage 4: Section Summaries (expanded sections → condensed summaries)
    ↓
Stage 5: Refine Summary Sections (Abstract/Intro/Conclusion + all summaries)
    ↓
Stage 6: Assemble Final Survey + References
```

## Stage 1: Outline Generation

The outline must be **query-type adaptive**. Analyze the user's query to determine the structure:

### Query Type A: Single-Topic Deep Dive
Example: "Catalyst design for electrochemical CO2 reduction"

Structure:
- Abstract
- Introduction
- Problem Definition / Background (formalize if quantitative field)
- **Main body (categorized by approach/mechanism/paradigm)**
- Evaluation / Assessment
- Challenges & Future Directions
- Conclusion

### Query Type B: Multi-Topic Parallel/Comparative
Example: "Drug resistance mechanisms and therapeutic strategies in cancer immunotherapy"

Structure:
- Abstract
- Introduction
- **Topic 1: [First Theme] (definition + methods + taxonomy)**
- **Topic 2: [Second Theme] (definition + methods + taxonomy)**
- Comprehensive Evaluation
- Comprehensive Challenges
- Conclusion

Key rule: For parallel topics, definitions and methods must be split into separate chapters per topic, NOT mixed together.

### Query Type C: Pipeline/Stage-Based
Example: "From sample preparation to data analysis in single-cell RNA sequencing"

Structure:
- Chapters organized by workflow/pipeline stages

**Note**: The section names, organization logic, and required tables must be adapted to the user's field. See `assets/survey-template.md` for field-specific conventions.

## Stage 2: Section Content Standards

Each section type has specific quality requirements:

### Abstract
- Structured narrative (NOT bullet points): Background → Gap → Scope → Key Findings → Outlook
- 300-500 words, coherent paragraph, no bold headers or labels

### Introduction
- Coherent narrative paragraph, no subsections
- Must cover: Research background → Necessity of core topic (why traditional methods fail) → Method summary → Scope & organization
- NO bullet points or bold subheadings

### Problem Definition
- Formalize with LaTeX: define input X, output Y, objective function
- Use `$$...$$` for display math

### Methods (most critical section)
- **Build taxonomy, don't enumerate**: Cluster papers by technical mechanism, not chronology
- **Paradigm comparison table required**: | Paradigm | Representative Work | Core Mechanism | Main Advantage | Fundamental Limitation |
- **Deep analysis per paradigm**: Explain WHY it works, WHAT trade-off it makes, WHERE it fails
- **Intra-paradigm comparison table**: Specific methods within each paradigm

### Evaluation
- Benchmarks: Narrative analysis by capability category + dataset comparison table
- Metrics: Cluster by dimension (performance, efficiency, semantic) + analyze limitations
- SOTA: Summarize current state-of-the-art with quantitative results table

### Challenges & Future Directions
Each challenge must have:
1. Problem definition (what exactly is difficult)
2. Evidence from literature [X, Y]
3. Strategic opportunity (what solving it unlocks)
4. Initial attempts (if any papers partially address it)

### Conclusion
- Summarize, respond to user's original research goal
- State which paradigm is currently most promising

## Stage 3: Section Expansion

### Word Count Targets by Section Type

| Section Type | Target Words | Keywords for Detection |
|---|---|---|
| Methodology | 6000 | method, technique, paradigm, mechanism, architecture, framework, algorithm, model |
| Evaluation | 3500 | evaluation, experiment, benchmark, test |
| Challenges | 3000 | challenge, future, direction, limitation |
| Applications | 3000 | application, case, scenario |
| Definitions | 2000 | definition, problem, formalization, concept, background |
| Other | 2500 | (default) |

### Expansion Rules
1. **Maintain thematic coherence**: Keep same themes, structure, narrative as draft
2. **Add technical depth**: Specific examples from papers, detailed comparisons, tables, critical analysis
3. **Cite comprehensively**: Use as many relevant papers as possible from the full collection
4. **Survey-grade quality**: Rigorous, objective, information-dense academic style

## Stage 4: Section Summaries

Generate condensed summaries of each expanded content section (Methodology, Evaluation, Challenges, etc.). These summaries serve as compact context for refining the summary sections in Stage 5.

1. For each expanded section, produce a 150-300 word condensed summary capturing the key findings, methods, and insights
2. Store summaries as intermediate context (not part of the final output)
3. All content sections must be summarized before proceeding to Stage 5

## Stage 5: Summary Section Refinement

Summary sections (Abstract, Introduction, Conclusion) are refined AFTER all content sections are expanded:

1. Generate condensed summaries of each expanded section
2. Use these summaries as context to refine the summary sections
3. This ensures Abstract/Intro/Conclusion accurately reflect the full survey content

## Quality Principles

1. **Build taxonomy, don't enumerate**: Methods organized by mechanism, not paper-by-paper
2. **Critical insight over description**: For each method, explain WHY it works, WHAT trade-off, WHERE it fails
3. **Strict citation grounding**: Every claim must have numbered citations [X]
4. **Visual structure**: Markdown tables for paradigm comparison, method comparison within paradigms
5. **Zero vagueness**: Specific method names, dataset names, metric values — no generic statements
