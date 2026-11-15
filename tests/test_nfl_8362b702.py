"""Tests for the nfl_8362b702 pack.

Layer 1: the verifier (all 14 numbered rules) must pass on the built pack.
Layer 2: module-level identities, run independently of the CSV artifacts.
Layer 3: determinism — a second build overwrites every file byte for byte.
"""
from __future__ import annotations

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_8362b702 import capture as C
from nfl_8362b702 import controls as CO
from nfl_8362b702 import model as M
from nfl_8362b702 import results as R


def test_verifier_passes():
    out = subprocess.run([sys.executable,
                          os.path.join(REPO, "scripts", "check_nfl_8362b702.py")],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_corpus_identity():
    games = R.corpus_rows()
    assert len(games) == 136
    stats = R.team_totals(games)
    assert sum(s["w"] for s in stats.values()) == 135
    assert sum(s["l"] for s in stats.values()) == 135
    assert sum(s["t"] for s in stats.values()) == 2
    assert sum(s["pf"] for s in stats.values()) == 6246
    assert sum(s["pa"] for s in stats.values()) == 6246
    assert sum(1 for g in games if g["away_score"] == g["home_score"]) == 1


def test_reconciliation_no_mismatch():
    for r in R.reconcile_corpus_plus_w10():
        assert r["verdict"] != "MISMATCH", r


def test_standings_identities():
    i = R.standings_identities()
    assert i["clubs"] == 32 and i["w_equals_l"] and i["pf_equals_pa"]


def test_split_check_flags_min_only():
    bad = [r for r in R.split_identity_checks() if r["identity_holds"] == "NO"]
    assert [r["team_abbr"] for r in bad] == ["MIN"]


def test_controls_reproducible():
    assert CO.random_pick("W11-06") == CO.random_pick("W11-06")
    picks = [CO.random_pick(f"W11-{i:02d}") for i in range(1, 14)]
    assert set(picks) <= {"home", "away"}


def test_model_probabilities_sum_to_one():
    f, info = M.week11_forecasts()
    assert len(f) == 13
    for row in f:
        assert abs(row["p_home_win"] + row["p_away_win"] - 1.0) < 1e-9
    # neutral-site game (SF home, Mexico City) must see zero HFA
    neu = [r for r in f if r["inputs"]["neutral_site"]]
    assert neu and all(r["inputs"]["hfa_applied"] == 0.0 for r in neu)
    assert info["hfa"] is not None and info["sigma"] > 0


def test_backtest_never_eligible():
    wf = M.walk_forward(R.corpus_rows())
    assert len(wf) == 120  # weeks 2-9
    assert all(r["backtest"] is True for r in wf)
    f, _ = M.week11_forecasts()
    assert all(r["backtest"] is False for r in f)


def test_capture_contracts_no_drift():
    from nfl_8362b702 import contracts as K
    assert not K.any_drift()
    for r in K.drift_rows():
        assert r["verdict"] == "OK", r


def test_deterministic_build():
    def snap():
        import hashlib, glob
        h = hashlib.sha256()
        for p in sorted(glob.glob(os.path.join(REPO, "data", "nfl_8362b702", "*.csv")) +
                        glob.glob(os.path.join(REPO, "docs", "nfl-8362b702", "*.html"))):
            h.update(open(p, "rb").read())
        return h.hexdigest()
    before = snap()
    out = subprocess.run([sys.executable,
                          os.path.join(REPO, "scripts", "build_nfl_8362b702.py")],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
    assert snap() == before, "builder is not deterministic"


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"{len(fns) - failed}/{len(fns)} tests passed")
    sys.exit(1 if failed else 0)
