# Interpreting a Symbolic-Law Report

How to read `report.json`: where the thresholds come from, what each diagnosis means, how the source study's datasets came out, and how to read a law without over-reading it.

## Thresholds and Their Provenance

| Constant | Value | Source |
|---|---|---|
| Full compression | law R2 at least 0.7 | Source study. One of 82 landscapes reached it. |
| Partial compression | law R2 at least 0.5 | This skill's convention. The source study called 0.33 to 0.43 "low" and 0.65 to 0.67 "partial". |
| Predictable | law or black box R2 at least 0.2 | This skill's convention. |
| Low effective d | at most 6 | Source study. 18 of the 19 landscapes at or below it still missed 0.7. |
| Interaction gap | black box minus law at least 0.2 | This skill's convention. |
| Link-function gain | transform raises law R2 by at least 0.15 | This skill's convention. In the source study's Poelwijk probe, transforms moved the fit by less than 0.1. |
| Knee tolerance | within 0.02 of the 10-node score | This skill's convention. |

These are reading aids, not significance tests. A value near a threshold should be reported as near it.

## Two Conditions, One Measured

A short law can spend only a few terms, so compression needs two things:

1. **Few governing variables.** Effective d measures this.
2. **Simple combination** of those variables. Nothing in the report measures this directly; it shows up as a gap between the black box and the law when effective d is low.

| | Simple combination | Tangled combination |
|---|---|---|
| **Low effective d** | compresses (source study: beta-carotene, effective d 1.3, R2 0.92) | `interaction-limited` (Poelwijk eqFP611, effective d 4.0) |
| **High effective d** | does not compress | does not compress |

Effective d, not the nominal number of knobs, sets the ceiling. In controlled landscapes where inert decoy variables inflated the nominal count, effective d explained 73% of the variance in compressibility and the nominal count 0.4%. A large design space with redundant or inert parts can be low-dimensional; a small one in which every position interacts can be high-dimensional.

## Diagnoses

**`none` (COMPRESSIBLE).** Present the law. Check that its terms make sense to someone who knows the system; if a term looks like an artifact (see "Reading a Law" below), say so.

**`dimension-limited`.** Effective d above 6: the importance is spread over many design variables, and a 10-node law cannot carry them all. Advise a black box with denser sampling, or a library redesign that concentrates control in fewer variables (orthogonal, modular parts).

**`interaction-limited`.** Few variables carry the signal and a black box predicts well, yet the law falls short by 0.2 or more. Either a monotone link hides an additive signal, or the variables genuinely interact at high order. `--transform-test` separates the two. If the transforms do not help, report that the response needs more interacting terms than a short law can spend.

**`ceiling-limited`.** The law is within 0.2 of the black box: the data, not the law family, cap the fit. Measurement noise or too few designs. A richer model will not help much; more or cleaner data will.

**`unpredictable`.** Neither model predicts held-out designs. Possible reasons: noise dominates, the sample is too small, the governing variables were not recorded, or the design columns were encoded in a way that hides them (check Step 1).

## Worked Examples: the Source Study's Curated Panel

Output of this script on the source study's curated datasets (`--seed 3`, 2,000-row cap, full grid). The numbers match the published panel exactly; see [method.md](method.md).

| Dataset | Nominal d | Effective d | Law R2 | Ceiling R2 | Status | Diagnosis |
|---|---|---|---|---|---|---|
| beta-carotene | 3 | 1.26 | 0.920 | 0.975 | COMPRESSIBLE | none |
| vanlent-simulator | 7 | 2.85 | 0.670 | 0.902 | PARTIAL | interaction-limited |
| jervis-RBS | 14 | 3.38 | 0.540 | 0.577 | PARTIAL | ceiling-limited |
| vanlent-pCA | 19 | 5.79 | 0.493 | 0.513 | INCOMPRESSIBLE | ceiling-limited |
| pca-paperA | 5 | 2.07 | 0.380 | 0.690 | INCOMPRESSIBLE | interaction-limited |
| poelwijk | 13 | 4.02 | 0.318 | 0.932 | INCOMPRESSIBLE | interaction-limited |
| isoprenol | 121 | 12.10 | 0.432 | 0.449 | INCOMPRESSIBLE | dimension-limited |
| limonene | 9 | 6.17 | 0.390 | 0.625 | INCOMPRESSIBLE | dimension-limited |
| aav | 28 | 22.98 | 0.214 | 0.563 | INCOMPRESSIBLE | dimension-limited |
| avgfp | 233 | 80.81 | 0.102 | 0.396 | INCOMPRESSIBLE | dimension-limited |
| tryptophan | 5 | 3.39 | -0.269 | 0.133 | UNPREDICTABLE | unpredictable |
| gb1 | 4 | 3.93 | -0.114 | 0.132 | UNPREDICTABLE | unpredictable |
| smanski-nif | 115 | 48.68 | 0.040 | -0.017 | UNPREDICTABLE | unpredictable |

The protein assays (gb1, avgfp, aav) are fitted with linear and pairwise-product terms only, because their one-hot columns are binary.

## Why Not a Ratio to the Black Box

A ratio such as law R2 divided by black-box R2 looks reasonable and misleads exactly where it matters. On hard landscapes the black box is weak too, so a law that explains little scores well on the ratio. In the source study, three metabolic-engineering anchors scored 0.62 to 0.95 on such a ratio while their absolute compressibility was 0.33 to 0.43. Report the absolute held-out R2, and give the ceiling as context.

## Why Effective d Must Be Independent of the Law

If the number of governing variables is read off the fitted law, "few variables give a short law" is true by definition and says nothing. The script estimates effective d from a random forest that never sees the law: importances summed per design variable, normalized to a distribution p, and turned into a participation ratio 1/sum(p^2). It returns the nominal count when importance is spread evenly and a small number when a few variables dominate. In the source study it recovered the set effective d (2, 3, 5 or 9 active variables among 12) on additive, saturating and random-function landscapes.

It is one estimator. A second, mechanistically different one (Sobol indices, active subspaces) is the natural cross-check when a conclusion rests on effective d.

## Comparing Many Datasets

When the user scores a collection of datasets and asks what drives compressibility:

- **Use partial correlations.** Effective and nominal d are correlated. Rank-transform compressibility and both dimensionalities, regress out the third variable, and correlate the residuals. In the source study the partial Spearman correlation with effective d (holding nominal d) was -0.70 on the curated panel, while the one with nominal d (holding effective d) was +0.55.
- **Do not let one study dominate.** 50 of the 69 protein assays in the source study came from one megascale study. Report the relationship within the dominant study, across the other studies, and with each study collapsed to one point, rather than one pooled number.

## Reading a Law

- **Coefficients are on the original scale** of each term, so their sizes depend on units. Compare terms by their contribution over the observed range, not by coefficient size.
- **Correlated terms share credit.** If two design variables move together in the library, the law may pick either one; the other is not irrelevant.
- **Ratios and reciprocals with zeros.** The script guards denominators with 1e-6, so where a denominator variable is 0 the term becomes about 1e6 times its numerator and acts as a switch for those designs. The report warns when this happens; read such a term as "when this variable is absent", not as a smooth ratio.
- **Extrapolation.** A law is fitted inside the sampled ranges. 1/x and ratio terms can swing far outside them.
- **Screening.** With more than 40 encoded columns the search sees only the 40 most correlated with the response (`law.screened` is true). A variable missing from the law may have been screened out, not found irrelevant.
