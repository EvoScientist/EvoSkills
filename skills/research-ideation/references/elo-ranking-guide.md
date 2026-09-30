# Elo Ranking Guide

Detailed guide for running the pairwise Elo tournament in Step 5 of the `research-ideation` pipeline. Covers the formula, the 4-dimension rubric, round-robin pairing, and tie handling.

## The Elo Rating System

Originally designed for chess, the Elo system works for any competitive comparison. Each idea starts with a rating of 1500. After each pairwise match, ratings update based on the outcome and the expected outcome.

### Core Formula

**Expected score** (probability of winning):
```
E_A = 1 / (1 + 10^((R_B - R_A) / 400))
```

**Rating update** after a match:
```
R_A' = R_A + K × (S_A - E_A)
```

Where:
- `R_A`, `R_B` = current ratings of ideas A and B
- `E_A` = expected score for A (between 0 and 1)
- `K` = 32 (K-factor; controls how much a single match affects ratings)
- `S_A` = actual score: 1 (win), 0.5 (draw), 0 (loss)

**Why K=32?** This is the standard K-factor for new players. It means a single match can move a rating by up to 32 points. With three champions and one match per pair, that separates a champion that wins both matches from one that loses both by about 60 points, while a split result stays close.

### Understanding the Scale

| Rating Difference | Higher-Rated Win Probability |
|-------------------|------------------------------|
| 0 | 50% |
| 100 | 64% |
| 200 | 76% |
| 400 | 91% |

A 200-point gap means the higher-rated idea is expected to win 76% of the time. This translates to: "clearly stronger but not dominant."

## The Four-Dimension Rubric

Each pairwise match evaluates both ideas on four dimensions. Score each dimension on a 1-10 scale.

### 1. Novelty (Weight: 25%)

| Score | Interpretation |
|-------|---------------|
| 9-10 | Proposes a fundamentally new approach not seen in existing literature |
| 7-8 | Combines existing techniques in a non-obvious way |
| 5-6 | Applies known techniques to a new setting with meaningful adaptation |
| 3-4 | Incremental improvement over existing work |
| 1-2 | Essentially replicates existing approaches |

**Key question**: "Would a well-read researcher in this field say 'I haven't seen this combination before'?"

### 2. Feasibility (Weight: 25%)

| Score | Interpretation |
|-------|---------------|
| 9-10 | Can be fully implemented and validated within 2-3 months with available resources |
| 7-8 | Achievable within 4-6 months; some minor resource or expertise gaps |
| 5-6 | Possible but requires significant effort, new infrastructure, or learning |
| 3-4 | Major challenges in implementation, data access, or computational requirements |
| 1-2 | Requires resources or capabilities not realistically available |

**Key question**: "If I started tomorrow, could I produce publishable results within one research cycle?"

### 3. Relevance (Weight: 25%)

| Score | Interpretation |
|-------|---------------|
| 9-10 | Addresses a top-3 open problem in the field; high community interest |
| 7-8 | Addresses a recognized problem; moderate community attention |
| 5-6 | Relevant but not among the most pressing problems |
| 3-4 | Niche interest; limited audience would care about results |
| 1-2 | Largely irrelevant to current research priorities |

**Key question**: "Would the top venues in my field want to see a paper on this topic?"

### 4. Clarity (Weight: 25%)

| Score | Interpretation |
|-------|---------------|
| 9-10 | Problem is precisely defined; methodology is clear; evaluation metrics are obvious |
| 7-8 | Well-defined with minor ambiguities that can be resolved quickly |
| 5-6 | General direction is clear but key details need investigation |
| 3-4 | Vague; requires significant problem definition work before starting |
| 1-2 | Unclear what exactly the problem is or how to approach it |

**Key question**: "Could I write the experiment plan for this idea right now?"

## Round-Robin Pairing

The tournament input is the 3 track champions from Step 4 — one per research direction. Every champion meets the other two once:

1. Champion 1 vs Champion 2
2. Champion 1 vs Champion 3
3. Champion 2 vs Champion 3

For each match, score both ideas on the four dimensions, take the composite (the mean of the four scores), and the higher composite wins. Update both ratings after every match, in the order above, before scoring the next one.

Three matches are the whole tournament: there are no byes and no further rounds. All three champions are presented to the user; the tournament decides their order and records the per-dimension reasons.

**Why only the champions?** Entering every refined version from Step 4 (up to 27) into a larger tournament was tested. It costs about 50 comparisons instead of 3, tends to fill the top 3 with two versions of the same direction, and a blind judge preferred the three-champion shortlist.

## Structuring the Pairwise Comparison

Each match should follow this structured comparison format:

### Comparison Prompt Template

```
Compare these two research ideas:

**Idea A**: [Full refined idea of one track champion]
**Idea B**: [Full refined idea of another track champion]

Score each on four dimensions (1-10 scale):

1. Novelty: How different is this from existing work?
2. Feasibility: Can this be implemented and validated with available resources?
3. Relevance: Does this address an important open problem?
4. Clarity: Is the idea well-defined enough to start immediately?

For each dimension, provide a brief justification (1-2 sentences) before the score.
Then determine the overall winner.
```

### Recording Results

Use the ranking scorecard template (see [../assets/ranking-scorecard-template.md](../assets/ranking-scorecard-template.md)) for each match.

## Worked Example

**Idea A** (Rating: 1500): "Context-aware pruning for 100K+ token inputs"
**Idea B** (Rating: 1500): "Reasoning-preserving distillation via chain-of-thought"

| Dimension | Idea A Score | Idea B Score |
|-----------|-------------|-------------|
| Novelty | 7 | 8 |
| Feasibility | 8 | 6 |
| Relevance | 9 | 8 |
| Clarity | 7 | 7 |
| **Composite** | **7.75** | **7.25** |

**Winner**: Idea A

**Elo update**:
- Expected score for A: E_A = 1 / (1 + 10^((1500 - 1500) / 400)) = 0.5
- A wins, S_A = 1
- New R_A = 1500 + 32 × (1 - 0.5) = 1516
- New R_B = 1500 + 32 × (0 - 0.5) = 1484

After this single match, Idea A is rated 1516 and Idea B is rated 1484 — a 32-point gap.

**Full round-robin**: suppose Idea A also beats a third champion, Idea C, and Idea B then beats Idea C.

| Match | Result | Ratings after the match |
|-------|--------|-------------------------|
| A vs B | A wins (E_A = 0.500) | A 1516.0, B 1484.0, C 1500.0 |
| A vs C | A wins (E_A = 0.523) | A 1531.3, B 1484.0, C 1484.7 |
| B vs C | B wins (E_B = 0.499) | A 1531.3, B 1500.0, C 1468.7 |

Final order: A (1531), B (1500), C (1469).

## Handling Edge Cases

### Ties

If both ideas have identical composite scores, score the match as a draw (S = 0.5 for both). Ratings move less: each shifts by K × (0.5 - E) instead of K × (1 - E).

### Equal or Near-Equal Final Ratings

If two champions finish with the same rating, order them by their mean composite score across their two matches; if that is also equal, keep track order.

If each champion wins one match and loses one (A beats B, B beats C, C beats A), all three finish within a few points of 1500, and those few points come only from the order the matches were played in. The tournament has not separated them: ignore the rating differences, order them by mean composite score (then track order), and say in the direction summary that they are co-equal options.
