# Elo Ranking Guide

Detailed guide for running the pairwise Elo tournament in Phase 2 of the Idea Tournament. Covers the formula, the 4-dimension rubric, Swiss-system pairing, and convergence criteria.

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

**Why K=32?** This is the standard K-factor for new players. It means a single match can move a rating by up to 32 points. For 4-5 rounds of matches with 15-21 candidates, this produces sufficient differentiation while remaining stable.

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

## Swiss-System Pairing

Swiss-system is more efficient than round-robin (which requires N×(N-1)/2 matches). For 15-21 candidates, Swiss produces reliable rankings in 4-5 rounds.

### Pairing Algorithm

**Round 1**: Random pairing. If odd number of candidates, one gets a bye (automatic win against a phantom opponent with rating 1500).

**Round 2+**:
1. Sort all candidates by current Elo rating (descending)
2. Starting from the top, pair each candidate with the nearest-rated candidate they haven't faced yet
3. If no valid pairing exists (all nearby candidates already faced), pair with the next available
4. Continue until all candidates are paired (or one gets a bye)

### Number of Rounds

| Candidates | Recommended Rounds | Rationale |
|------------|-------------------|-----------|
| 10-14 | 4 | Enough for top-3 to stabilize |
| 15-21 | 5 | Standard for this range |
| 22-30 | 5-6 | Additional round for larger fields |

### Convergence Check

After each round, check if the top-3 rankings have stabilized:
- If the top-3 are the same as after the previous round → rankings are stable, can stop early
- If there's significant movement in the top-5 → run another round
- After 5 rounds, stop regardless — further rounds have diminishing returns

## Structuring the Pairwise Comparison

Each match should follow this structured comparison format:

### Comparison Prompt Template

```
Compare these two research ideas:

**Idea A**: [Full description from idea tree]
**Idea B**: [Full description from idea tree]

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

## Handling Edge Cases

### Ties

If both ideas have identical composite scores, score the match as a draw (S = 0.5 for both). Ratings move less: each shifts by K × (0.5 - E) instead of K × (1 - E).

### Close Ratings

If two ideas are within 50 Elo points of each other after 4+ rounds, they are effectively equivalent. Note this in the rankings — the direction summary should treat them as co-equal options.

### Suspiciously Dominant Ideas

If one idea reaches 1700+ (200 points above start) after just 2-3 rounds, it's likely genuinely strong — but verify by checking its match quality. Did it face strong opponents (those with above-average ratings)? A high rating earned against weak opponents is less reliable.
