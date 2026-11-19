---
name: symbolic-law-discovery
description: "Find a short, readable law (equation) for a table of designs and a measured response, and decide honestly whether one exists. Scores compressibility as the absolute held-out R2 of a bounded-complexity symbolic-regression search (greedy forward selection, node budget 10, cross-validated), measures effective dimensionality independently of the law (random-forest participation ratio), and checks a tuned black-box ceiling. Use when: a user wants an equation, an interpretable model, or 'which variables matter and how' from tabular experimental data (combinatorial strain, protein, materials, formulation or process designs; DOE screens; parameter sweeps), or asks whether a dataset can be explained by a simple law before or after a design campaign. Do NOT use for: discovering ODE/PDE dynamics from time series, models of images, text or sequence embeddings, pure accuracy tuning (use a black box), or plotting results (use paper-figures)."
allowed-tools: "read_file write_file edit_file execute think_tool"
metadata:
  author: Joshua Xu
  version: '0.1.0'
  tags: [symbolic-regression, interpretability, data-analysis, design-of-experiments, effective-dimensionality]
---

# Symbolic Law Discovery

Turn a table of designs and one measured response into a short, readable law, and report on an absolute scale whether such a law exists at all.

The method comes from a study of 82 combinatorial design landscapes (metabolic-engineering libraries, protein deep-mutational scans, a kinetic pathway simulator). Its finding sets the tone of this skill: a landscape compresses into a short law only when **few variables effectively govern the response** and **those variables combine simply**. Only one of the 82 landscapes fully compressed. Most datasets will not yield a good short law, so the main job here is an honest verdict with a reason, not an equation at any cost.

Script paths in this document are relative to this skill's directory.

## When to Use This Skill

- "Find an equation / formula / simple model for this data"
- "Which factors matter, and how do they combine?"
- "Can this screen be explained by a simple rule, or do we need a black box?"
- Before a campaign: "Will an interpretable model work on this design space?" (run it on a pilot sample)
- After a campaign: "Rank these candidate designs, and tell me whether to trust a readable model or a black box"

---

## Inputs and Output

**Inputs**
- A CSV with one row per design and one numeric response column. Design columns can be numeric (levels, concentrations, copy numbers), categorical (part identity, promoter name), or a single mutation-string column (`D40A:G41S`).
- Optional: a CSV of candidate designs to rank, with the same design columns (and the true response, if known).

**Output** (in the output directory, default `sld-out/`)
- `report.json`: every number, the status label, the diagnosis, the law, and warnings.
- `report.md`: the same, readable.
- `candidates_ranked.csv` when candidates were given.
- Your write-up for the user (Step 6), built only from `report.json`.

---

## Setup

**Dependencies**: `pip install numpy scipy pandas scikit-learn` (also listed in `requirements.txt` at the skill root). Install into the environment the user is working in.

---

## Core Workflow

```
Step 1: Frame the table                -> verify: one row per design, numeric response, no ID columns
Step 2: Run the scorer                 -> verify: report.json exists and every warning was read
Step 3: Read the verdict               -> verify: status and diagnosis copied from report.json
Step 4: Probe a low-dimensional miss   (only when the diagnosis is interaction-limited)
Step 5: Rank candidate designs         (optional)
Step 6: Write the report               -> verify: every number traces to report.json
```

### Status Labels

| Status | Held-out R2 of the law | Meaning |
|---|---|---|
| `COMPRESSIBLE` | at least 0.7 | A short law reproduces held-out responses. |
| `PARTIAL` | 0.5 to 0.7 | The law captures the main structure but misses a real share of the response. |
| `INCOMPRESSIBLE` | below 0.5 | No short law generalizes, although the response may be predictable by a black box. |
| `UNPREDICTABLE` | law and black box both below 0.2 | Nothing predicts held-out designs at this sample size. |

0.7 is the full-compression threshold of the source study; 0.5 and 0.2 are this skill's conventions. Where each threshold comes from: [references/interpretation.md](references/interpretation.md).

### Step 1: Frame the table

Look at the data before running anything: number of rows, columns, types, the response's range.

- **One row per design.** If designs were measured in replicate and the file lists each replicate, pass `--average-replicates`. Replicates of one design split across CV folds inflate the held-out score; the script warns when it sees repeated designs.
- **Only design variables.** Keep the variables someone chose when designing (the "knobs"). Drop identifiers, dates, plate positions and notes with `--drop`. Measured covariates (OD, growth rate) are not design variables: leave them out unless the user wants them as inputs, and say so in the report.
- **Raw scale first.** Score the response as measured. Transformed scales belong in Step 4.
- Convert Excel to CSV. For protein variants, use one mutation-string column with `--mutation-col`.

### Step 2: Run the scorer

```bash
python scripts/sld.py --data designs.csv --target titre --out sld-out/
```

| Flag | Use |
|---|---|
| `--drop a,b` | ignore these columns |
| `--features a,b,c` | use only these design columns |
| `--mutation-col mutant` | encode mutation strings instead of design columns |
| `--average-replicates` | average the response per unique design |
| `--fast` | small black-box grid for a first look; rerun without it before reporting |
| `--no-pareto` | skip the accuracy-vs-complexity sweep |
| `--transform-test` | Step 4 |
| `--candidates pool.csv --top-k 100` | Step 5 |
| `--seed 1` | seed of the subsample and the forest (CV splits are fixed) |

It takes seconds for a few hundred rows and several minutes at the 2,000-row cap with the full grid; larger tables are subsampled. The script prints a one-line JSON summary. Open `report.json` and read every entry under `warnings` before going on.

What it computes (details in [references/method.md](references/method.md)):
1. Encodes the design variables; **nominal d** is their number.
2. **Effective d**: a random-forest participation ratio over design variables, computed without looking at any law.
3. **Compressibility**: the 5-fold held-out R2 of a greedy symbolic-regression law with node budget 10. Terms are linear and pairwise products, plus 1/x, x^2 and x_i/x_j when fewer than half the encoded columns are binary.
4. **Ceiling**: the held-out R2 of a tuned RBF support-vector regressor in the same folds.
5. The law refitted on all rows with original-scale coefficients, and held-out R2 at node budgets 2 to 10.

### Step 3: Read the verdict

Copy `status` and `diagnosis` from `report.json`. Do not upgrade a verdict because the law looks plausible or its in-sample R2 is high.

| Diagnosis | Condition | What to tell the user |
|---|---|---|
| `none` | COMPRESSIBLE | Present the law and what each term says in the user's variable names. |
| `dimension-limited` | effective d above 6 | Too many variables carry signal for a short law. Use a black box and denser sampling, or redesign the library toward fewer effective variables. |
| `interaction-limited` | effective d at most 6, black box beats the law by 0.2 or more | Few variables matter but combine in a tangled way. Run Step 4. |
| `ceiling-limited` | the law is within 0.2 of the black box | The data set the cap, not the law family. More designs or less measurement noise would help more than a richer law. |
| `unpredictable` | nothing predicts | No law claim. Check noise, sample size, and whether the governing variables were recorded at all. |

Then read the accuracy-vs-complexity table. If a smaller budget is within 0.02 of the full score (`knee_budget` below 10), the report also contains `short_law`: prefer it when presenting, and say that it scores almost the same.

### Step 4: Probe a low-dimensional miss

Only when the diagnosis is `interaction-limited`:

```bash
python scripts/sld.py --data designs.csv --target titre --transform-test --out sld-out/
```

This refits the law on log(y) and on rank-normal(y).

- If either raises the held-out R2 by 0.15 or more, a monotone link (saturating readout, global epistasis) hides a simpler law. Report the law on that scale, and state that its score is on the transformed scale.
- If not, the governing variables interact at a higher order than a short law can carry. Report this as a finding. The Poelwijk eqFP611 landscape behaves this way: effective d 4.0 and a black box at 0.93, but this script's law reaches 0.32 (about 0.6 with the source study's wider search), and log or rank-normal transforms move it by less than 0.1.

### Step 5: Rank candidate designs

```bash
python scripts/sld.py --data designs.csv --target titre --candidates pool.csv --top-k 100 --out sld-out/
```

`candidates_ranked.csv` holds the predictions and ranks of both the law and the black box.

- **No true responses in the pool:** report how much the two top-k sets agree. Where they disagree, the next experiments are most informative.
- **True responses in the pool** (simulator, held-out library): report top-1 regret and top-k overlap with the truth for both models.
- Prefer the law's picks only when the status is COMPRESSIBLE or PARTIAL. In the source study's kinetic simulator (PARTIAL, R2 0.67), the three-enzyme law recovered more of the true top 100 designs than a tuned black box (about 17 to 27 against 9 to 14). For INCOMPRESSIBLE, rank with the black box.
- Heed the extrapolation warnings: laws with 1/x or ratio terms can swing far outside the training range.

### Step 6: Write the report

1. **Verdict**: status and one sentence of diagnosis.
2. **Numbers**: rows used, nominal d, effective d, compressibility R2, ceiling R2, each taken from `report.json`.
3. **The law**: for COMPRESSIBLE or PARTIAL, the expression and a plain reading of each term. Otherwise show it only as "best short law found, not predictive", or leave it out.
4. **Next action** from the diagnosis table.
5. **Warnings**, verbatim.
6. **Method**, one sentence, citing the source study (below).

---

## Rules That Keep the Analysis Honest

1. **Report compressibility on the absolute scale.** Never as a ratio to the black box: a law at 0.40 next to a black box at 0.45 scores 0.89 on the ratio and still explains less than half the response.
2. **Never count effective d from the law.** "Few variables give a short law" is true by construction if the variables are counted in the law. Report the forest estimate.
3. **Held-out R2 only.** It is 1 - SSres/SStot on held-out designs, can be negative, and is not a squared correlation. In-sample R2 is printed for reference and is never the score.
4. **The number of knobs is not the diagnostic.** In the source study a 59-position library (effective d 2.1) partly compressed, while a 4-position one (effective d 3.9) did not compress at all.
5. **Low effective d is necessary, not sufficient.** 18 of the 19 source landscapes with effective d at most 6 still missed 0.7. Do not promise a law because effective d is small.
6. **A law describes; it does not prove mechanism.** Terms are associations within the sampled design space. Write "consistent with", not "shows that", unless the user has independent mechanistic evidence.
7. **Small samples are noisy.** Below about 30 rows the 5-fold estimate is noisy. Do not argue over 0.69 against 0.71; if the verdict sits on a threshold, say so, and for subsampled tables rerun with other `--seed` values.
8. **Comparing many datasets** needs the precautions in [references/interpretation.md](references/interpretation.md): partial correlations, and one point per independent study.

---

## References

- [references/method.md](references/method.md): definitions, defaults, what was ported, and the reproduction check against the published numbers
- [references/interpretation.md](references/interpretation.md): thresholds and their provenance, diagnoses, worked examples, reading a law

## Source

Xu J., Tu W., Xu J. "Effective dimensionality governs when combinatorial design landscapes compress into interpretable laws." Manuscript under revision, 2026. Code: https://github.com/lystoris/compressible-design-laws. Data: https://doi.org/10.5281/zenodo.21238983.
