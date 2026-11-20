#!/usr/bin/env python3
"""Symbolic-law discovery: does a tabular design -> response dataset compress into a short law?

For one table of designs (rows) and one measured response, this script reports:

1. a tuned black-box ceiling (RBF support-vector regression, nested CV): is the response
   predictable from the design variables at all?
2. the effective dimensionality: a random-forest participation ratio over design variables,
   computed independently of any law;
3. the compressibility: the absolute held-out R2 of the best law a bounded-complexity
   symbolic-regression search finds (greedy forward selection, node budget 10, 5-fold CV);
4. the law itself, refitted on all rows, with coefficients on the original scale;

and writes report.json and report.md with a status label and a diagnosis.

The scoring engine is a port of the audited real-data engine of
https://github.com/lystoris/compressible-design-laws, used in Xu, Tu & Xu, "Effective
dimensionality governs when combinatorial design landscapes compress into interpretable laws"
(manuscript under revision). With the same rows, seed and subsample cap it returns the same numbers.
That code is MIT-licensed: Copyright (c) 2026 Joshua Xu, Weiming Tu, Jiabao Xu.

Run:
    python scripts/sld.py --data designs.csv --target titre --out sld-out/
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

VERSION = "0.1.0"

L_STAR = 10  # node budget of a law: summed term costs + number of terms
N_OUTER = 5  # outer CV folds (held-out R2)
N_INNER = 3  # inner CV folds (black-box tuning)
TOP_K_VARS = 40  # variable pre-screen when there are more encoded columns than this
MAX_N = 2000  # subsample cap
PARETO_BUDGETS = (2, 4, 6, 8, 10)

# Verdict thresholds. FULL is the paper's full-compression threshold and LOW_EFF_D its
# low-dimensional cut; the rest are this skill's conventions (references/interpretation.md).
FULL = 0.7
PARTIAL = 0.5
PREDICTABLE = 0.2
LOW_EFF_D = 6.0
GAP = 0.2
LINK_GAIN = 0.15
KNEE_TOL = 0.02


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------------------------


def r2_det(y_true, y_pred) -> float:
    """Held-out coefficient of determination 1 - SSres/SStot. Not a squared correlation."""
    yt = np.asarray(y_true, float)
    yp = np.asarray(y_pred, float)
    ss_res = np.sum((yt - yp) ** 2)
    ss_tot = np.sum((yt - yt.mean()) ** 2)
    return np.nan if ss_tot <= 0 else float(1.0 - ss_res / ss_tot)


# ----------------------------------------------------------------------------------------
# Encoding: design table -> numeric matrix + group map (one design variable = one group)
# ----------------------------------------------------------------------------------------


def parse_mutations(entry) -> dict:
    """'D40A:G41S' -> {40: 'A', 41: 'S'}."""
    out = {}
    for tok in str(entry).split(":"):
        if len(tok) >= 3 and tok[1:-1].isdigit():
            out[int(tok[1:-1])] = tok[-1]
    return out


class Encoder:
    """Numeric columns are kept as they are (one group each). Categorical columns are one-hot
    encoded with the first sorted level dropped as reference (all indicators share one group).
    A mutation column ('D40A:G41S') is one-hot encoded per position, one group per position.
    Zero-variance columns are removed after encoding."""

    def __init__(self, features, mutation_col=None):
        self.features = list(features)
        self.mutation_col = mutation_col
        self.specs = []

    @property
    def names(self):
        return [s[3] for s in self.specs]

    @property
    def groups(self):
        return [s[4] for s in self.specs]

    @property
    def nominal_d(self):
        return len(set(self.groups))

    def fit(self, df):
        specs = []
        if self.mutation_col:
            muts = df[self.mutation_col].map(parse_mutations)
            positions = sorted({p for m in muts for p in m})
            for p in positions:
                letters = sorted({m.get(p, "_") for m in muts})
                if len(letters) < 2:
                    continue
                for letter in letters[1:]:
                    specs.append(("mut", p, letter, f"p{p}_{letter}", f"p{p}"))
        else:
            for c in self.features:
                s = df[c]
                if pd.api.types.is_numeric_dtype(s):
                    specs.append(("num", c, None, str(c), str(c)))
                else:
                    levels = sorted(s.astype(str).unique())
                    for level in levels[1:]:
                        specs.append(("cat", c, level, f"{c}={level}", str(c)))
        X = self._matrix(df, specs)
        keep = [i for i in range(X.shape[1]) if np.std(X[:, i]) > 1e-12]
        self.specs = [specs[i] for i in keep]
        return self

    def transform(self, df):
        return self._matrix(df, self.specs)

    def _matrix(self, df, specs):
        muts = df[self.mutation_col].map(parse_mutations) if self.mutation_col else None
        cols = []
        for kind, src, level, _name, _group in specs:
            if kind == "num":
                cols.append(df[src].to_numpy(dtype=float))
            elif kind == "cat":
                cols.append((df[src].astype(str) == level).to_numpy(dtype=float))
            else:
                cols.append(
                    np.array([1.0 if m.get(src, "_") == level else 0.0 for m in muts])
                )
        if not cols:
            return np.empty((len(df), 0))
        return np.column_stack(cols)


# ----------------------------------------------------------------------------------------
# Effective dimensionality (independent of the law)
# ----------------------------------------------------------------------------------------


def effective_d(X, y, groups, seed=0) -> float:
    """Participation ratio 1/sum(p^2) of random-forest importances summed per design variable."""
    rf = RandomForestRegressor(n_estimators=300, random_state=seed, n_jobs=-1).fit(X, y)
    imp = rf.feature_importances_.astype(float)
    g = pd.Series(imp).groupby(pd.Series(groups)).sum()
    s = g.values
    if s.sum() <= 0:
        return float(g.size)
    s = s / s.sum()
    return float(1.0 / np.sum(s**2))


# ----------------------------------------------------------------------------------------
# Bounded-complexity symbolic regression
# ----------------------------------------------------------------------------------------


def build_terms(d, names, allow_nonlinear=False, g=1e-6):
    """Term library. Linear terms cost 1; 1/x, x^2, x_i*x_j and x_i/x_j cost 3."""
    terms = [dict(name=names[i], cost=1, fn=(lambda X, i=i: X[:, i])) for i in range(d)]
    if allow_nonlinear:
        terms += [
            dict(
                name=f"1/{names[i]}",
                cost=3,
                den=i,
                fn=(lambda X, i=i: 1.0 / (X[:, i] + g)),
            )
            for i in range(d)
        ]
        terms += [
            dict(name=f"{names[i]}^2", cost=3, fn=(lambda X, i=i: X[:, i] ** 2))
            for i in range(d)
        ]
    terms += [
        dict(
            name=f"{names[i]}*{names[j]}",
            cost=3,
            fn=(lambda X, i=i, j=j: X[:, i] * X[:, j]),
        )
        for i, j in itertools.combinations(range(d), 2)
    ]
    if allow_nonlinear:
        terms += [
            dict(
                name=f"{names[i]}/{names[j]}",
                cost=3,
                den=j,
                fn=(lambda X, i=i, j=j: X[:, i] / (X[:, j] + g)),
            )
            for i, j in itertools.permutations(range(d), 2)
        ]
    return terms


def _design(X, terms):
    if not terms:
        return np.empty((X.shape[0], 0))
    M = np.column_stack([t["fn"](X) for t in terms])
    return np.where(np.isfinite(M), M, 0.0)


def _nodes(terms) -> int:
    return sum(t["cost"] for t in terms) + len(terms)


def _standardize(M):
    mu = M.mean(0)
    sd = M.std(0)
    sd = np.where(sd < 1e-12, 1, sd)
    return mu, sd


def greedy_sr_fit(Xtr, ytr, terms, budget=L_STAR):
    """Greedy forward selection: add the term that most improves training R2 (by > 1e-9),
    refit OLS on standardized terms, stop when nothing improves or the node budget is spent.
    Returns (selected terms, mu, sd, fitted model), or ([], None, None, mean) for no law."""
    sel = []
    rem = list(terms)
    best = r2_det(ytr, np.full_like(ytr, ytr.mean(), dtype=float))
    while True:
        cand, cand_r2 = None, best
        for t in rem:
            trial = sel + [t]
            if _nodes(trial) > budget:
                continue
            M = _design(Xtr, trial)
            mu, sd = _standardize(M)
            try:
                lr = LinearRegression().fit((M - mu) / sd, ytr)
                r = r2_det(ytr, lr.predict((M - mu) / sd))
            except Exception:
                continue
            if r > cand_r2 + 1e-9:
                cand_r2, cand = r, t
        if cand is None:
            break
        sel.append(cand)
        rem = [t for t in rem if t is not cand]
        best = cand_r2
        if _nodes(sel) >= budget:
            break
    if not sel:
        return [], None, None, float(ytr.mean())
    M = _design(Xtr, sel)
    mu, sd = _standardize(M)
    return sel, mu, sd, LinearRegression().fit((M - mu) / sd, ytr)


def greedy_sr_pred(Xte, sel, mu, sd, model):
    if not sel:
        return np.full(Xte.shape[0], model, dtype=float)
    return model.predict((_design(Xte, sel) - mu) / sd)


def screen(Xtr, ytr, k):
    """Indices of the k columns with the largest |Spearman| with y (training rows only)."""
    sc = np.array(
        [
            abs(stats.spearmanr(Xtr[:, j], ytr).correlation)
            if np.std(Xtr[:, j]) > 1e-12
            else 0
            for j in range(Xtr.shape[1])
        ]
    )
    sc = np.nan_to_num(sc)
    return np.argsort(-sc)[:k]


# ----------------------------------------------------------------------------------------
# Black-box ceiling
# ----------------------------------------------------------------------------------------


def tune_svr(Xtr, ytr, seed=0, fast=False):
    Cs = [1.0, 100.0] if fast else [1.0, 10.0, 100.0, 1000.0]
    Gs = ["scale", 0.1] if fast else ["scale", 0.01, 0.1, 1.0]
    Es = [0.1] if fast else [0.01, 0.1, 0.2]
    inner = KFold(min(N_INNER, max(2, len(ytr) // 3)), shuffle=True, random_state=seed)
    best, best_score = None, -np.inf
    for C in Cs:
        for gm in Gs:
            for e in Es:
                sc = []
                for a, b in inner.split(Xtr):
                    xs = StandardScaler().fit(Xtr[a])
                    ym = ytr[a].mean()
                    ys = ytr[a].std() or 1
                    m = SVR(kernel="rbf", C=C, gamma=gm, epsilon=e).fit(
                        xs.transform(Xtr[a]), (ytr[a] - ym) / ys
                    )
                    sc.append(r2_det(ytr[b], m.predict(xs.transform(Xtr[b])) * ys + ym))
                s = np.nanmean(sc)
                if s > best_score:
                    best_score, best = s, (C, gm, e)
    return dict(C=best[0], gamma=best[1], epsilon=best[2])


def svr_pred(Xtr, ytr, Xte, p):
    xs = StandardScaler().fit(Xtr)
    ym = ytr.mean()
    ys = ytr.std() or 1
    m = SVR(kernel="rbf", C=p["C"], gamma=p["gamma"], epsilon=p["epsilon"]).fit(
        xs.transform(Xtr), (ytr - ym) / ys
    )
    return m.predict(xs.transform(Xte)) * ys + ym


# ----------------------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------------------


def _screened(X, y, names):
    if X.shape[1] > TOP_K_VARS:
        kp = screen(X, y, TOP_K_VARS)
        return kp, [names[i] for i in kp]
    return np.arange(X.shape[1]), list(names)


def score(X, y, names, allow_nonlinear, budgets=(L_STAR,), ceiling=True, fast=False):
    """Held-out R2 of the law at each node budget (and of the black box), pooled over the
    out-of-fold predictions of a shuffled outer k-fold. The pre-screen is fitted on the
    training rows of each fold only."""
    n = X.shape[0]
    nf = min(N_OUTER, n) if n >= N_OUTER else max(2, n // 2)
    kf = KFold(nf, shuffle=True, random_state=0)
    law_pred = {b: np.full(n, np.nan) for b in budgets}
    n_terms = {b: [] for b in budgets}
    bb_pred = np.full(n, np.nan)
    for tr, te in kf.split(X):
        ytr = y[tr]
        kp, fn = _screened(X[tr], ytr, names)
        Xtr, Xte = X[tr][:, kp], X[te][:, kp]
        terms = build_terms(Xtr.shape[1], fn, allow_nonlinear)
        for b in budgets:
            sel, mu, sd, model = greedy_sr_fit(Xtr, ytr, terms, b)
            law_pred[b][te] = greedy_sr_pred(Xte, sel, mu, sd, model)
            n_terms[b].append(len(sel))
        if ceiling:
            bb_pred[te] = svr_pred(Xtr, ytr, Xte, tune_svr(Xtr, ytr, fast=fast))
    r2_law = {b: r2_det(y, law_pred[b]) for b in budgets}
    mean_terms = {b: float(np.mean(n_terms[b])) for b in budgets}
    r2_bb = r2_det(y, bb_pred) if ceiling else None
    return r2_law, mean_terms, r2_bb


def final_law(X, y, names, allow_nonlinear, budget=L_STAR):
    """The law refitted on all rows, with coefficients on the original scale of each term."""
    kp, fn = _screened(X, y, names)
    Xs = X[:, kp]
    sel, mu, sd, model = greedy_sr_fit(
        Xs, y, build_terms(Xs.shape[1], fn, allow_nonlinear), budget
    )
    if not sel:
        return dict(
            expression=f"y = {model:.4g}",
            intercept=model,
            terms=[],
            nodes=0,
            in_sample_r2=0.0,
            screened=bool(len(kp) < X.shape[1]),
            notes=["no term improved on the mean: the law is a constant"],
            _fit=(kp, [], None, None, model),
        )
    coef = model.coef_ / sd
    intercept = float(model.intercept_ - np.sum(model.coef_ * mu / sd))
    pieces = [f"{intercept:.4g}"]
    notes = []
    for t, c in zip(sel, coef):
        sign = "-" if c < 0 else "+"
        pieces.append(f"{sign} {abs(c):.4g}*({t['name']})")
        if "den" in t and np.any(np.abs(Xs[:, t["den"]]) < 1e-3):
            notes.append(
                f"term {t['name']}: its denominator is 0 for some designs, where the term "
                "becomes about 1e6 times its numerator; read it as a switch for those designs, "
                "not as a smooth ratio"
            )
    return dict(
        expression="y = " + " ".join(pieces),
        intercept=intercept,
        terms=[dict(term=t["name"], coef=float(c)) for t, c in zip(sel, coef)],
        nodes=_nodes(sel),
        in_sample_r2=r2_det(y, greedy_sr_pred(Xs, sel, mu, sd, model)),
        screened=bool(len(kp) < X.shape[1]),
        notes=notes,
        _fit=(kp, sel, mu, sd, model),
    )


def monotone_transforms(y):
    """log (shifted to be positive when needed) and rank-normal (rankit) versions of y."""
    lo, hi = float(np.min(y)), float(np.max(y))
    span = hi - lo if hi > lo else 1.0
    offset = 0.0 if lo > 0 else -lo + 1e-3 * span
    ranks = stats.rankdata(y)
    return {
        "log": np.log(y + offset),
        "rank-normal": stats.norm.ppf((ranks - 0.5) / len(y)),
    }


def top1_regret(y_true, y_pred):
    yt = np.asarray(y_true, float)
    pick = int(np.argmax(np.asarray(y_pred, float)))
    best = float(yt.max())
    absolute = best - float(yt[pick])
    return absolute, (absolute / best if best > 0 else None)


def topk_overlap(y_a, y_b, k):
    k = min(k, len(y_a))
    if k <= 0:
        return 0
    top_a = set(np.argpartition(-np.asarray(y_a, float), k - 1)[:k].tolist())
    top_b = set(np.argpartition(-np.asarray(y_b, float), k - 1)[:k].tolist())
    return len(top_a & top_b)


# ----------------------------------------------------------------------------------------
# Verdict
# ----------------------------------------------------------------------------------------


def verdict(r2_law, r2_bb, eff_d):
    """Status label + diagnosis from the absolute law R2, the ceiling and effective d."""
    law = -np.inf if r2_law is None or not np.isfinite(r2_law) else r2_law
    bb = -np.inf if r2_bb is None or not np.isfinite(r2_bb) else r2_bb
    if max(law, bb) < PREDICTABLE:
        return "UNPREDICTABLE", "unpredictable"
    if law >= FULL:
        return "COMPRESSIBLE", "none"
    status = "PARTIAL" if law >= PARTIAL else "INCOMPRESSIBLE"
    if eff_d > LOW_EFF_D:
        return status, "dimension-limited"
    if bb - law >= GAP:
        return status, "interaction-limited"
    return status, "ceiling-limited"


EXPLAIN = {
    "unpredictable": (
        "Neither the law nor a tuned black box predicts held-out designs. At this sample size "
        "the response is noise- or sampling-limited; no law claim can be made."
    ),
    "none": "A short law reproduces held-out responses. Read it, then use it.",
    "dimension-limited": (
        "Too many design variables carry signal for a short law. Expect no compact law; "
        "use a black box and denser sampling, or redesign toward fewer effective variables."
    ),
    "interaction-limited": (
        "Few variables matter, the black box predicts well, but the law cannot: the governing "
        "variables combine in ways the term budget cannot carry. Run --transform-test to "
        "separate a monotone link function from genuine high-order interaction."
    ),
    "ceiling-limited": (
        "The law already matches the black box; the data, not the law family, set the cap. "
        "More designs or less measurement noise would help more than a richer law."
    ),
}


# ----------------------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------------------


def _clean(obj):
    """JSON-safe copy: numpy scalars to Python, NaN/inf to None."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return float(obj) if np.isfinite(obj) else None
    return obj


def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:.{nd}f}"


def write_markdown(rep, path):
    lines = [
        f"# Symbolic-law report: `{rep['target']}`",
        "",
        f"**Status: {rep['status']}** (diagnosis: {rep['diagnosis']})",
        "",
        rep["explanation"],
        "",
        "| Quantity | Value |",
        "|---|---|",
        f"| Rows used | {rep['n_rows_used']} (of {rep['n_rows_input']} input) |",
        f"| Nominal d (design variables) | {rep['nominal_d']} |",
        f"| Effective d (RF participation ratio) | {_fmt(rep['effective_d'], 2)} |",
        f"| Compressibility: held-out R2 of the law (L*={L_STAR}) | {_fmt(rep['compressibility_r2'])} |",
        f"| Black-box ceiling: held-out R2 (RBF SVR, {rep['ceiling_grid']} grid) | {_fmt(rep['ceiling_r2'])} |",
        f"| Nonlinear terms enabled | {rep['nonlinear_terms']} |",
        "",
        "## Law (refitted on all rows)",
        "",
        "```",
        rep["law"]["expression"],
        "```",
        "",
        f"In-sample R2 {_fmt(rep['law']['in_sample_r2'])}; this is not the compressibility "
        "score, which is the held-out value above.",
    ]
    if rep.get("pareto"):
        lines += [
            "",
            "## Accuracy vs complexity",
            "",
            "| Node budget | Held-out R2 | Mean terms |",
            "|---|---|---|",
        ]
        for p in rep["pareto"]:
            lines.append(f"| {p['budget']} | {_fmt(p['r2'])} | {p['mean_terms']:.1f} |")
        lines.append("")
        lines.append(
            f"Smallest budget within {KNEE_TOL} of the L*={L_STAR} score: {rep['knee_budget']}"
        )
    if rep.get("short_law"):
        lines += [
            "",
            f"## Shorter law at node budget {rep['knee_budget']} (refitted on all rows)",
            "",
            "```",
            rep["short_law"]["expression"],
            "```",
        ]
    if rep.get("transform_test"):
        tt = rep["transform_test"]
        lines += ["", "## Monotone-transform test", ""]
        for k, v in tt["r2"].items():
            lines.append(f"- {k}: {_fmt(v)}")
        lines.append(f"- reading: {tt['reading']}")
    if rep.get("selection"):
        s = rep["selection"]
        lines += ["", "## Candidate ranking", ""]
        for k, v in s.items():
            lines.append(f"- {k}: {v}")
    if rep["warnings"]:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in rep["warnings"]]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------


def _split(arg):
    return [s.strip() for s in arg.split(",") if s.strip()] if arg else []


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True, help="CSV with one row per design")
    ap.add_argument("--target", required=True, help="response column")
    ap.add_argument(
        "--features", default="", help="comma list; default: all other columns"
    )
    ap.add_argument(
        "--drop", default="", help="comma list of columns to ignore (IDs, notes)"
    )
    ap.add_argument(
        "--mutation-col", default="", help="column of 'D40A:G41S' mutation strings"
    )
    ap.add_argument(
        "--max-n", type=int, default=MAX_N, help="subsample cap (default 2000)"
    )
    ap.add_argument(
        "--seed", type=int, default=0, help="seed for the subsample and the forest"
    )
    ap.add_argument(
        "--fast", action="store_true", help="small black-box grid (quick look)"
    )
    ap.add_argument("--no-pareto", action="store_true", help="skip the budget sweep")
    ap.add_argument(
        "--transform-test", action="store_true", help="refit on log / rank-normal y"
    )
    ap.add_argument(
        "--average-replicates", action="store_true", help="mean y per unique design"
    )
    ap.add_argument(
        "--candidates", default="", help="CSV of designs to rank with law and black box"
    )
    ap.add_argument("--top-k", type=int, default=100, help="k for top-k overlaps")
    ap.add_argument("--out", default="sld-out", help="output directory")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    warnings.filterwarnings("ignore")
    args = parse_args(argv)
    t0 = time.time()
    notes = []
    df = pd.read_csv(args.data)
    if args.target not in df.columns:
        log(f"error: target column {args.target!r} not in {list(df.columns)}")
        return 2
    if not pd.api.types.is_numeric_dtype(df[args.target]):
        log(f"error: target column {args.target!r} is not numeric")
        return 2
    mutation_col = args.mutation_col or None
    dropped = set(_split(args.drop))
    if mutation_col:
        features = [mutation_col]
    else:
        features = _split(args.features) or [
            c for c in df.columns if c != args.target and c not in dropped
        ]
    missing = [c for c in features if c not in df.columns]
    if missing:
        log(f"error: columns not found: {missing}")
        return 2
    n_input = len(df)
    df = df[features + [args.target]].dropna(subset=[args.target])
    numeric = [c for c in features if pd.api.types.is_numeric_dtype(df[c])]
    n_na = int(df[numeric].isna().any(axis=1).sum()) if numeric else 0
    if n_na:
        df = df.dropna(subset=numeric)
        notes.append(f"{n_na} rows with missing numeric design values were dropped")
    if any(df[c].isna().any() for c in features if c not in numeric):
        notes.append(
            "missing values in categorical columns are treated as their own level ('nan')"
        )
    if len(df) < 10:
        log(f"error: only {len(df)} usable rows; at least 10 are needed")
        return 2
    dup = int(df.duplicated(subset=features).sum())
    if dup and args.average_replicates:
        df = df.groupby(features, sort=False, dropna=False, as_index=False)[
            args.target
        ].mean()
        notes.append(f"{dup} replicate rows averaged into their unique designs")
    elif dup:
        notes.append(
            f"{dup} rows repeat an earlier design; replicates leak across CV folds. "
            "Rerun with --average-replicates unless the repeats are distinct designs"
        )
    if not mutation_col:
        for c in features:
            s = df[c]
            if not pd.api.types.is_numeric_dtype(s) and s.nunique() == len(s) > 10:
                notes.append(
                    f"column {c!r} has a distinct value in every row; probably an ID, pass --drop {c}"
                )
    if len(df) > args.max_n:
        df = df.sample(args.max_n, random_state=args.seed)
        notes.append(f"subsampled to {args.max_n} rows (seed {args.seed})")
    if len(df) < 30:
        notes.append(
            f"only {len(df)} rows: held-out R2 from {min(N_OUTER, len(df))}-fold CV is noisy"
        )

    enc = Encoder(features, mutation_col).fit(df)
    X = enc.transform(df)
    y = df[args.target].to_numpy(dtype=float)
    if X.shape[1] == 0:
        log("error: no design column varies across rows")
        return 2
    frac_binary = float(
        np.mean([np.unique(X[:, j]).size <= 2 for j in range(X.shape[1])])
    )
    allow_nl = frac_binary < 0.5
    log(
        f"encoded {len(y)} rows x {X.shape[1]} columns ({enc.nominal_d} design variables)"
    )

    eff = effective_d(X, y, enc.groups, seed=args.seed)
    log(f"effective d = {eff:.2f}")
    budgets = (L_STAR,) if args.no_pareto else PARETO_BUDGETS
    r2_law, mean_terms, r2_bb = score(
        X, y, enc.names, allow_nl, budgets, True, args.fast
    )
    comp = r2_law[L_STAR]
    log(f"compressibility R2 = {_fmt(comp)}; ceiling R2 = {_fmt(r2_bb)}")
    status, diagnosis = verdict(comp, r2_bb, eff)
    law = final_law(X, y, enc.names, allow_nl)
    fit = law.pop("_fit")
    notes.extend(law["notes"])

    rep = dict(
        skill_version=VERSION,
        data=str(args.data),
        target=args.target,
        n_rows_input=n_input,
        n_rows_used=len(y),
        seed=args.seed,
        encoding="mutation_list" if mutation_col else "design_matrix",
        nominal_d=enc.nominal_d,
        encoded_columns=X.shape[1],
        frac_binary=round(frac_binary, 3),
        nonlinear_terms=allow_nl,
        effective_d=eff,
        compressibility_r2=comp,
        ceiling_r2=r2_bb,
        ceiling_grid="fast" if args.fast else "full",
        status=status,
        diagnosis=diagnosis,
        explanation=EXPLAIN[diagnosis],
        law=law,
        pareto=None,
        knee_budget=None,
        short_law=None,
        transform_test=None,
        selection=None,
        warnings=notes,
    )
    if not args.no_pareto:
        rep["pareto"] = [
            dict(budget=b, r2=r2_law[b], mean_terms=mean_terms[b]) for b in budgets
        ]
        rep["knee_budget"] = next(
            (
                b
                for b in budgets
                if np.isfinite(r2_law[b]) and r2_law[b] >= comp - KNEE_TOL
            ),
            L_STAR,
        )
        if rep["knee_budget"] < L_STAR:
            short = final_law(X, y, enc.names, allow_nl, rep["knee_budget"])
            short.pop("_fit")
            rep["short_law"] = short

    if args.transform_test:
        r2s = {"raw": comp}
        for name, yt in monotone_transforms(y).items():
            r2s[name] = score(X, yt, enc.names, allow_nl, (L_STAR,), False)[0][L_STAR]
        gain = max(r2s["log"], r2s["rank-normal"]) - comp
        reading = (
            "a monotone link function explains much of the gap; fit and report the law on the transformed scale"
            if gain >= LINK_GAIN
            else "transforms barely move the fit; the cap is interaction order, not a link function"
        )
        rep["transform_test"] = dict(r2=r2s, gain=gain, reading=reading)

    if args.candidates:
        cdf = pd.read_csv(args.candidates)
        need = [c for c in features if c not in cdf.columns]
        if need:
            log(f"error: candidate file lacks design columns {need}")
            return 2
        cdf = cdf.dropna(subset=numeric).reset_index(drop=True)
        if not mutation_col:
            for c in features:
                if not pd.api.types.is_numeric_dtype(df[c]):
                    unseen = set(cdf[c].astype(str)) - set(df[c].astype(str))
                    if unseen:
                        notes.append(
                            f"candidate levels of {c!r} unseen in training are scored as the reference level: {sorted(unseen)[:5]}"
                        )
            for c in numeric:
                lo, hi = df[c].min(), df[c].max()
                n_out = int(((cdf[c] < lo) | (cdf[c] > hi)).sum())
                if n_out:
                    notes.append(
                        f"{n_out} candidates have {c!r} outside the training range "
                        f"[{lo:g}, {hi:g}]; predictions there are extrapolations"
                    )
        Xc = enc.transform(cdf)
        kp, sel, mu, sd, model = fit
        law_c = (
            greedy_sr_pred(Xc[:, kp], sel, mu, sd, model)
            if sel
            else np.full(len(cdf), model)
        )
        Xk = X[:, kp]
        bb_c = svr_pred(Xk, y, Xc[:, kp], tune_svr(Xk, y, fast=args.fast))
        out_c = cdf.copy()
        out_c["law_pred"] = law_c
        out_c["blackbox_pred"] = bb_c
        out_c["law_rank"] = stats.rankdata(-law_c, method="min").astype(int)
        out_c["blackbox_rank"] = stats.rankdata(-bb_c, method="min").astype(int)
        sel_rep = dict(
            n_candidates=len(cdf),
            k=min(args.top_k, len(cdf)),
            law_vs_blackbox_topk_agreement=topk_overlap(law_c, bb_c, args.top_k),
        )
        if args.target in cdf.columns and cdf[args.target].notna().all():
            truth = cdf[args.target].to_numpy(dtype=float)
            for label, pred in (("law", law_c), ("blackbox", bb_c)):
                absolute, rel = top1_regret(truth, pred)
                sel_rep[f"{label}_top1_regret"] = rel if rel is not None else absolute
                sel_rep[f"{label}_topk_true_overlap"] = topk_overlap(
                    truth, pred, args.top_k
                )
            if truth.max() <= 0:
                notes.append(
                    "true best response <= 0: top-1 regret is reported unnormalized"
                )
        rep["selection"] = sel_rep
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_c.sort_values("law_rank").to_csv(
            out_dir / "candidates_ranked.csv", index=False
        )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rep["runtime_s"] = round(time.time() - t0, 1)
    (out_dir / "report.json").write_text(
        json.dumps(_clean(rep), indent=2), encoding="utf-8"
    )
    write_markdown(rep, out_dir / "report.md")
    print(
        json.dumps(
            _clean(
                dict(
                    status=status,
                    diagnosis=diagnosis,
                    compressibility_r2=comp,
                    ceiling_r2=r2_bb,
                    effective_d=eff,
                    nominal_d=enc.nominal_d,
                    law=law["expression"],
                    report=str(out_dir / "report.md"),
                )
            )
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
