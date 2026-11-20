"""Tests for skills/symbolic-law-discovery/scripts/sld.py.

The script needs numpy, scipy, pandas and scikit-learn (the skill's requirements.txt). Where
they are not installed the tests are skipped. Run from the repository root:
    pip install -r skills/symbolic-law-discovery/requirements.txt
    pytest tests/symbolic-law-discovery -q
"""

import json
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("scipy")
pytest.importorskip("sklearn")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skills" / "symbolic-law-discovery" / "scripts"))

import sld  # noqa: E402


def synthetic(n=150, d_active=2, d_decoy=6, seed=0):
    """Continuous design table: y = 2*x0 + 3*x0*x1 (+ small noise); decoys are inert."""
    rng = np.random.default_rng(seed)
    cols = {f"x{i}": rng.uniform(0.5, 2.0, n) for i in range(d_active + d_decoy)}
    df = pd.DataFrame(cols)
    df["y"] = 2 * df.x0 + 3 * df.x0 * df.x1 + rng.normal(0, 0.05, n)
    return df


def test_r2_det_is_not_a_squared_correlation():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert sld.r2_det(y, y) == 1.0
    assert sld.r2_det(y, np.full(4, y.mean())) == 0.0
    # perfectly correlated but shifted predictions: corr^2 = 1, R2 < 0
    assert sld.r2_det(y, y + 10) < 0


def test_categorical_encoding_drops_a_reference_level_and_counts_one_group():
    df = pd.DataFrame({"promoter": ["pA", "pB", "pC", "pA"], "copies": [1, 2, 3, 4]})
    enc = sld.Encoder(["promoter", "copies"]).fit(df)
    assert enc.names == ["promoter=pB", "promoter=pC", "copies"]
    assert enc.nominal_d == 2
    X = enc.transform(df)
    assert X.shape == (4, 3)
    assert X[0].tolist() == [0.0, 0.0, 1.0]


def test_mutation_encoding_groups_by_position():
    df = pd.DataFrame({"mutant": ["D40A", "D40G:G41S", "G41S", "D40A:G41C"]})
    enc = sld.Encoder(["mutant"], mutation_col="mutant").fit(df)
    assert enc.nominal_d == 2
    assert set(enc.groups) == {"p40", "p41"}
    assert enc.transform(df).shape == (4, len(enc.names))


def test_effective_d_ignores_inert_decoys():
    df = synthetic(n=400, d_active=2, d_decoy=10)
    features = [c for c in df.columns if c != "y"]
    enc = sld.Encoder(features).fit(df)
    eff = sld.effective_d(enc.transform(df), df.y.to_numpy(), enc.groups, seed=0)
    assert enc.nominal_d == 12
    assert eff < 4


def test_greedy_search_recovers_a_known_law():
    df = synthetic()
    features = [c for c in df.columns if c != "y"]
    enc = sld.Encoder(features).fit(df)
    X, y = enc.transform(df), df.y.to_numpy()
    law = sld.final_law(X, y, enc.names, allow_nonlinear=True)
    assert "x0*x1" in [t["term"] for t in law["terms"]]
    assert law["in_sample_r2"] > 0.99
    assert law["nodes"] <= sld.L_STAR


def test_node_budget_is_respected():
    df = synthetic()
    features = [c for c in df.columns if c != "y"]
    enc = sld.Encoder(features).fit(df)
    X, y = enc.transform(df), df.y.to_numpy()
    for budget in sld.PARETO_BUDGETS:
        law = sld.final_law(X, y, enc.names, True, budget)
        assert law["nodes"] <= budget


@pytest.mark.parametrize(
    "r2_law, r2_bb, eff_d, expected",
    [
        (0.92, 0.97, 1.3, ("COMPRESSIBLE", "none")),
        (0.67, 0.90, 2.9, ("PARTIAL", "interaction-limited")),
        (0.54, 0.58, 3.4, ("PARTIAL", "ceiling-limited")),
        (0.10, 0.40, 81.0, ("INCOMPRESSIBLE", "dimension-limited")),
        (-0.27, 0.13, 3.4, ("UNPREDICTABLE", "unpredictable")),
        (float("nan"), float("nan"), 2.0, ("UNPREDICTABLE", "unpredictable")),
    ],
)
def test_verdict(r2_law, r2_bb, eff_d, expected):
    assert sld.verdict(r2_law, r2_bb, eff_d) == expected


def test_selection_metrics():
    truth = np.array([1.0, 5.0, 3.0, 10.0])
    absolute, relative = sld.top1_regret(truth, np.array([0, 9, 1, 2]))
    assert absolute == 5.0 and relative == 0.5
    assert sld.top1_regret(truth, truth) == (0.0, 0.0)
    assert sld.topk_overlap(truth, truth, 2) == 2


def test_cli_writes_a_report_and_ranks_candidates(tmp_path):
    df = synthetic(n=120)
    data = tmp_path / "designs.csv"
    df.to_csv(data, index=False)
    pool = synthetic(n=60, seed=1)
    cand = tmp_path / "pool.csv"
    pool.to_csv(cand, index=False)
    out = tmp_path / "out"
    code = sld.main(
        [
            "--data",
            str(data),
            "--target",
            "y",
            "--fast",
            "--candidates",
            str(cand),
            "--top-k",
            "10",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    rep = json.loads((out / "report.json").read_text())
    assert rep["status"] == "COMPRESSIBLE"
    assert rep["nominal_d"] == 8
    assert rep["compressibility_r2"] > 0.95
    assert [p["budget"] for p in rep["pareto"]] == list(sld.PARETO_BUDGETS)
    assert rep["selection"]["law_topk_true_overlap"] >= 8
    ranked = pd.read_csv(out / "candidates_ranked.csv")
    assert {"law_pred", "blackbox_pred", "law_rank", "blackbox_rank"} <= set(ranked)
    assert (out / "report.md").read_text().startswith("# Symbolic-law report")


def test_cli_rejects_a_missing_target(tmp_path):
    data = tmp_path / "designs.csv"
    synthetic(n=20).to_csv(data, index=False)
    assert sld.main(["--data", str(data), "--target", "nope"]) == 2


def test_replicates_are_flagged_and_can_be_averaged(tmp_path):
    df = synthetic(n=40)
    df = pd.concat([df, df.iloc[:10]], ignore_index=True)
    data = tmp_path / "designs.csv"
    df.to_csv(data, index=False)
    out = tmp_path / "out"
    base = ["--data", str(data), "--target", "y", "--fast", "--no-pareto"]
    assert sld.main(base + ["--out", str(out)]) == 0
    rep = json.loads((out / "report.json").read_text())
    assert any("repeat an earlier design" in w for w in rep["warnings"])
    assert sld.main(base + ["--average-replicates", "--out", str(out)]) == 0
    rep = json.loads((out / "report.json").read_text())
    assert rep["n_rows_used"] == 40
