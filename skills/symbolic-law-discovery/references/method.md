# Method

What `scripts/sld.py` computes, with every default. The scoring engine is a port of the audited real-data engine of the source study (https://github.com/lystoris/compressible-design-laws, MIT licence); with the same rows, seed and subsample cap it returns the published numbers (see "Reproduction Check").

## Encoding

Each design variable becomes one **group** of columns, so that a categorical variable spread over several indicator columns is still counted once.

- **Numeric column**: kept as it is, one group.
- **Categorical column**: one-hot, with the first level in sorted order dropped as reference; all indicators share the variable's group. A missing value is its own level (`nan`).
- **Mutation-string column** (`D40A:G41S`, with `--mutation-col`): parsed to an amino-acid identity per position; each mutated position is one-hot encoded, one group per position, first sorted level dropped. Unmutated positions take the placeholder `_`.
- Columns with zero variance are removed after encoding.

**Nominal d** is the number of groups that remain.

Rows with a missing response, or a missing numeric design value, are dropped. Above 2,000 rows (`--max-n`) a random subsample is drawn with `--seed`.

## Effective Dimensionality

A random forest (300 trees, `random_state=seed`) is fitted to predict the response from all encoded columns. Its impurity importances are summed within each group and normalized to a distribution p over design variables. Effective d is the participation ratio 1/sum(p^2): it equals the nominal d when importance is spread evenly and approaches 1 when one variable dominates. The forest never sees a law.

## Term Library

| Term | Cost | Included |
|---|---|---|
| x | 1 | always |
| x_i * x_j (all pairs) | 3 | always |
| 1/x | 3 | nonlinear gate open |
| x^2 | 3 | nonlinear gate open |
| x_i / x_j (all ordered pairs) | 3 | nonlinear gate open |

Denominators are guarded as x + 1e-6. **Nonlinear gate**: open when fewer than half of the encoded columns are binary (`frac_binary < 0.5`), because reciprocals, squares and ratios are degenerate on 0/1 indicators. One-hot protein data is therefore fitted with linear and pairwise-product terms only.

## Search

Greedy forward selection. At each step, every remaining term that keeps the law within the **node budget** is tried: the terms are standardized, an ordinary least-squares model is refitted, and the term that raises training R2 most (by more than 1e-9) is added. The search stops when no term improves the fit or the budget is spent.

Node count = summed term costs + number of terms. The budget is L* = 10, so a law holds at most five linear terms, or for example two products and one linear term.

**Pre-screen**: with more than 40 encoded columns, only the 40 with the largest absolute Spearman correlation with the response are offered to the search. The screen is fitted on training rows only.

## Compressibility

The held-out coefficient of determination R2 = 1 - SSres/SStot of the law, computed on out-of-fold predictions pooled over a shuffled 5-fold split (`KFold(5, shuffle=True, random_state=0)`; with fewer than 5 rows, max(2, n // 2) folds). In each fold the screen and the law are fitted on the training part only. The score is absolute: near 1 when a short law reproduces held-out responses, 0 or below when no law beats the mean.

The **accuracy-vs-complexity sweep** repeats the search at node budgets 2, 4, 6, 8 and 10 in the same folds. `knee_budget` is the smallest budget whose score is within 0.02 of the 10-node score.

The **reported law** is the search refitted on all rows (with the screen fitted on all rows), its coefficients converted back to the original scale of each term. Its in-sample R2 is printed for reference and is not the compressibility score.

## Black-Box Ceiling

An RBF support-vector regressor on standardized inputs and a standardized response, trained in the same outer folds and on the same screened columns as the law. Hyperparameters are tuned per outer fold by an inner 3-fold split over C in {1, 10, 100, 1000}, gamma in {scale, 0.01, 0.1, 1}, epsilon in {0.01, 0.1, 0.2}. `--fast` shrinks the grid to C in {1, 100}, gamma in {scale, 0.1}, epsilon = 0.1. The ceiling only answers "is this response predictable at all?"; it is not part of the compressibility score.

## Transform Test

`--transform-test` reruns the law search (not the black box) on two monotone transforms of the response: log(y), shifted by -min(y) + 0.001 x range when y is not positive, and the rank-normal transform Phi^-1((rank - 0.5) / n). Scores are on the transformed scale. These definitions are this skill's; the source study reported the same two transforms for its Poelwijk probe.

## Candidate Ranking

`--candidates` encodes the pool with the training encoding (levels unseen in training fall back to the reference level, with a warning), predicts it with the all-rows law and with a black box tuned on all rows, and writes both rankings. With the true response in the pool it reports, for each model, the top-1 regret (true best minus the true value of the model's top pick, divided by the true best when that is positive) and the overlap of the predicted and true top-k sets.

## Seeds and Determinism

`--seed` sets the subsample and the forest. The CV splits (`random_state=0`) and inner tuning splits are fixed, so two runs on the same rows give the same law and scores. To see the variability that subsampling introduces, run several seeds.

## Not Included in This Version

The source study also used a depth-budgeted recursive grammar (with saturating x/(1+|x|) leaves) for its synthetic sweep and an enumerative operator search for its simulator. Neither is included; this script carries the engine the study applied to real data.

## Reproduction Check

Run on the source study's curated panel (data: https://doi.org/10.5281/zenodo.21238983) with `--seed 3 --max-n 2000 --no-pareto`, the script reproduced the published trajectory-3 table (`results/panel_t3.csv` in the source repository) on all 13 datasets: identical rows used, nominal d, effective d (2 decimals), law R2 and ceiling R2 (3 decimals). The values are tabulated in [interpretation.md](interpretation.md).

## Known Limitations

- Effective d rests on one estimator; a second, mechanistically different estimator is the natural cross-check.
- Greedy selection is not a global search: a better law within the budget can exist.
- The reference level of a categorical variable is chosen alphabetically; the law's terms for that variable are contrasts against it.
- Held-out R2 from 5 folds is noisy on small tables (below about 30 rows).
