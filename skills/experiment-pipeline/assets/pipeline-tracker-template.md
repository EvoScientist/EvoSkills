# Experiment Pipeline Tracker

## Project Info

- **Project**: [Research project name]
- **Research Question**: [One-sentence description]
- **Start Date**: [YYYY-MM-DD]
- **Source**: [Link to research proposal from research-ideation, if applicable]

## Pipeline Status

| Stage | Status | Attempts Used | Budget | Gate Met? |
|-------|--------|---------------|--------|-----------|
| 1. Initial Implementation | [ ] Not started / [ ] In progress / [ ] Complete | 0 / 20 | ≤20 | [ ] |
| 2. Hyperparameter Tuning | [ ] Not started / [ ] In progress / [ ] Complete | 0 / 12 | ≤12 | [ ] |
| 3. Proposed Method | [ ] Not started / [ ] In progress / [ ] Complete | 0 / 12 | ≤12 | [ ] |
| 4. Ablation Study | [ ] Not started / [ ] In progress / [ ] Complete | 0 / 18 | ≤18 | [ ] |

**Total Attempts**: 0 / 62

## Stage Details

### Stage 1: Initial Implementation
- **Baseline**: [Paper/method being reproduced]
- **Target Metric**: [Reported value ± 2%]
- **Best Result**: [Your best reproduction result]
- **Status Notes**: [Brief notes]

### Stage 2: Hyperparameter Tuning
- **Key Parameters**: [Parameters being tuned]
- **Best Config**: [Optimal configuration found]
- **Stability**: [Variance across 3 seeds]
- **Status Notes**: [Brief notes]

### Stage 3: Proposed Method
- **Method**: [Your novel method name/description]
- **vs Baseline**: [Improvement over tuned baseline]
- **Integration Status**: [Which components are integrated]
- **Status Notes**: [Brief notes]

### Stage 4: Ablation Study
- **Components Tested**: [List of ablated components]
- **Key Finding**: [Which components matter most]
- **Status Notes**: [Brief notes]

## Backtracking Log

Record any stage regressions (e.g., discovering a Stage 1 issue during Stage 3):

| Date | From Stage | To Stage | Reason | Resolution |
|------|-----------|----------|--------|------------|
| | | | | |

## Cross-Stage Insights

- [Insight 1 that spans multiple stages]
- [Insight 2]

## Results Summary

| Method | Primary Metric | Secondary Metric 1 | Secondary Metric 2 |
|--------|---------------|--------------------|--------------------|
| Published baseline | [reported] | [reported] | [reported] |
| Reproduced baseline | [your result] | [your result] | [your result] |
| Tuned baseline | [tuned result] | [tuned result] | [tuned result] |
| Proposed method | [your method] | [your method] | [your method] |

## Evolution Memory Triggers

- [ ] Pipeline succeeded → Trigger ESE (Experiment Strategy Evolution)
- [ ] No executable code within budget, or method underperforms baseline → Trigger IVE (Idea Validation Evolution)
- [ ] Evolution report written to `/memory/evolution-reports/`

## Handoff Checklist

- [ ] All stage logs complete
- [ ] Trajectory logs saved
- [ ] Results tables ready for paper-writing
- [ ] Ablation table ready
- [ ] Key implementation details documented
- [ ] evo-memory updated
