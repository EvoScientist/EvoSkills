# Section Quality Checklist

Use this checklist to verify each section meets survey-grade standards before finalizing.

## Universal Checks (All Sections)

- [ ] Every factual claim has numbered citations [X] or [X, Y]
- [ ] No vague statements — all methods, datasets, metrics named specifically
- [ ] Terminology matches user's goal exactly (no conceptual drift)
- [ ] Markdown formatting is correct and consistent
- [ ] Content directly serves the user's research goal

## Abstract

- [ ] Written as continuous narrative (NO bullet points, NO bold labels)
- [ ] Covers: background → gap → scope → key findings → outlook
- [ ] 300-500 words
- [ ] Contains key citations

## Introduction

- [ ] Continuous narrative (NO subsections, NO bullet points)
- [ ] Explains why traditional methods fail → motivates the research topic
- [ ] Outlines survey scope and chapter organization
- [ ] References foundational papers

## Problem Definition

- [ ] Core task formalized with LaTeX: input X, output Y, objective
- [ ] Uses `$$...$$` for display math
- [ ] Mathematical constraints and common assumptions stated

## Methods

- [ ] Papers clustered by technical mechanism (NOT chronology)
- [ ] Paradigm comparison table present: paradigm | representative work | mechanism | advantage | limitation
- [ ] Each paradigm has multi-paragraph technical narrative (NOT bullet points)
- [ ] Each paradigm analyzed for: why it works, trade-offs, failure modes
- [ ] Intra-paradigm comparison tables present
- [ ] Cross-paradigm connections and evolution discussed

## Evaluation

- [ ] Benchmarks categorized by capability tested
- [ ] Benchmark comparison table present
- [ ] Metrics clustered by dimension (performance / efficiency / semantic)
- [ ] Metric limitations analyzed
- [ ] SOTA results summarized with quantitative table

## Challenges & Future Directions

- [ ] 3-5 specific challenges identified
- [ ] Each has: problem definition + evidence [X, Y] + strategic opportunity + initial attempts
- [ ] Ordered by importance/impact

## Conclusion

- [ ] Summarizes key findings
- [ ] States which paradigm is most promising
- [ ] Responds to user's original research goal
- [ ] Provides clear "next step" recommendation
