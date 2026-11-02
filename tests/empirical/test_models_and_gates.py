import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from nba_lab.contracts import load_ledger, load_rights
from nba_lab.experiments import build_report
from nba_lab.gates import empty_metrics, evaluate_gates, summarize
from nba_lab.models import RidgeLineModel, empirical_over_probability, shrunk_prop_projection
from nba_lab.registry import STRATEGIES

ROOT = Path(__file__).resolve().parents[2]


def test_ridge_and_prop():
    x = [[1.0, 0.0], [2.0, 1.0], [3.0, 0.0], [4.0, 1.0], [5.0, 0.0], [6.0, 1.0]]
    y = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    m = RidgeLineModel().fit(x, y)
    assert m.predict([3.0, 0.0]) == pytest.approx(4.0, abs=0.5)
    assert 0 < m.win_probability(2.0) < 1
    proj = shrunk_prop_projection([20, 22, 18], [25, 28, 20], league_rate=1.1)
    assert proj["projection"] > 0
    over = empirical_over_probability([1.0, -1.0, 2.0], 2.0, 2.5)
    assert 0 < over < 1


def test_ridge_rejects():
    with pytest.raises(ValueError):
        RidgeLineModel().fit([[1.0, 2.0]], [1.0])
    with pytest.raises(ValueError):
        RidgeLineModel(0.0).fit([[1.0, 2.0], [2.0, 3.0]], [1.0, 2.0])


def test_contract_loads_empty_ledger():
    approved, license_ids = load_rights(ROOT / "data/empirical/licenses.json")
    observations = load_ledger(ROOT / "data/empirical/observations.csv", ROOT / "data/empirical/licenses.json", {s["id"] for s in STRATEGIES})
    assert observations == []
    assert approved == set()
    assert license_ids == set()


def test_gates_fail_closed_on_empty_data():
    strategy = STRATEGIES[0]
    metrics = empty_metrics()
    gates = evaluate_gates(strategy, [], metrics, {"rights_verified": False, "provenance_verified": False, "walk_forward_verified": False, "ledger_audited": False, "preregistered": False, "dependence_verified": False})
    assert all(g["status"] in {"blocked", "not_run"} for g in gates)
    assert not any(g["status"] == "pass" for g in gates)


def test_full_report_is_fail_closed():
    report = build_report(
        ROOT / "data/empirical/observations.csv",
        ROOT / "data/empirical/licenses.json",
        ROOT / "data/empirical/evidence.json",
        ROOT / "data/empirical/residuals.csv",
    )
    assert report["status"] == "not_run"
    assert report["n_observations"] == 0
    assert report["leaderboard"] == []
    assert report["n_qualified"] == 0
    assert all(not s["qualified"] for s in report["strategies"])
    assert all(c["status"] == "unverified" for c in report["correlations"])
