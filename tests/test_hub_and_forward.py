"""Regression tests for the fixes found in the 2026-11-03 integration audit."""
import csv, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rd(*a):
    with open(os.path.join(ROOT, *a), newline="") as f:
        return list(csv.DictReader(f))


def imp(ml):
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def test_implied_probability_known_values():
    assert abs(imp(-110) - 0.5238095) < 1e-6
    assert abs(imp(100) - 0.5) < 1e-12
    assert abs(imp(-179) / (imp(-179) + imp(150)) - 0.6160) < 5e-4  # OKC@CLE slate row


def test_published_lines_use_correct_devig():
    for r in rd("data", "our_lines_2026-11-02.csv"):
        a, b = imp(int(r["fav_ml_current"])), imp(int(r["dog_ml_current"]))
        assert abs(a / (a + b) - float(r["market_fav_fair_prob"])) < 1e-4


def test_brier_published_matches_recomputation():
    bt = rd("data", "backtest_walkforward.csv")
    pub = {r["metric"]: float(r["value"]) for r in rd("verification", "backtest_metrics.csv") if r["value"].replace(".", "").isdigit()}
    assert abs(sum(float(x["brier_model"]) for x in bt) / len(bt) - pub["brier_model"]) < 5e-5


def test_integration_audit_passes():
    p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "audit_integration.py")], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout


def test_hub_check_passes():
    p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_hub.py")], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout
