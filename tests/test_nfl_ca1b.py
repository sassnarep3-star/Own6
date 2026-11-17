"""Tests for the nfl_ca1b pack. Pure stdlib; runnable with tools/run_tests.py or pytest."""
from __future__ import annotations

import csv
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_ca1b import availability as AV   # noqa: E402
from nfl_ca1b import capture as C         # noqa: E402
from nfl_ca1b import engine as E          # noqa: E402
from nfl_ca1b import requirements as RQ   # noqa: E402
from nfl_ca1b import snapshots as SN      # noqa: E402
from nfl_ca1b import verify as V          # noqa: E402


def _rows(name):
    with open(os.path.join(REPO, "data", "nfl_ca1b", name), newline="") as fh:
        return list(csv.DictReader(fh))


def test_standings_identity_reproduces_every_club():
    """The game log must reproduce all 32 clubs' W-L-T and PF/PA exactly."""
    games = E.load_games()
    assert len(games) == 149
    rec = {}
    for a, h, a_s, h_s, _ in games:
        for club, pf, pa in ((a, a_s, h_s), (h, h_s, a_s)):
            w, l, t, f, ag = rec.get(club, (0, 0, 0, 0, 0))
            rec[club] = (w + (pf > pa), l + (pf < pa), t + (pf == pa), f + pf, ag + pa)
    assert len(rec) == 32
    for club, want in C.STANDINGS.items():
        assert rec[club] == (want[0], want[1], want[2], want[3], want[4]), club
    assert sum(v[3] for v in C.STANDINGS.values()) == sum(v[4] for v in C.STANDINGS.values())


def test_win_probabilities_are_coherent():
    games = E.load_games()
    t = E.teams()
    wf = E.walk_forward(games, t)
    for r in wf:
        assert 0.0 < r["p_home"] < 1.0
        assert abs(r["p_home"] + (1 - r["p_home"]) - 1.0) < 1e-12
        assert r["k"] >= 1.0


def test_luck_tests_are_within_bounds():
    games = E.load_games()
    wf = E.walk_forward(games, E.teams())
    for r in wf:
        r["p_home_pick"] = max(r["p_home"], 1 - r["p_home"])
    lk = E.luck_rows(wf, "x", lambda r: (r["p_home"] >= 0.5, max(r["p_home"], 1 - r["p_home"])))
    assert 0.0 <= lk["exact_two_sided_p"] <= 1.0
    assert 0.0 <= lk["p_two_sided_vs_own_p"] <= 1.0
    assert lk["wilson_lo"] <= lk["hit_rate"] <= lk["wilson_hi"]


def test_leaderboard_publishes_no_rank_and_no_backtest_score():
    games = E.load_games()
    _, meta = E.originate_week11(games, E.teams())
    wf = E.walk_forward(games, E.teams())
    for row in E.leaderboard(wf, meta):
        for key in ("rank", "brier", "brier_skill_vs_coin", "cluster_boot_lo", "roi", "clv"):
            assert str(row.get(key, "")) == "", (row["strategy_id"], key)
        assert row["n_settled"] in (0, "0")


def test_market_columns_are_never_filled():
    for row in _rows("originated_lines_week11.csv"):
        for key in ("market_spread", "market_total", "market_ml_home", "market_ml_away",
                    "diff_spread", "diff_total", "diff_ml_home", "diff_ml_away"):
            assert row[key] == "", (row["game_id"], key)


def test_every_fixture_has_a_venue_from_an_official_surface():
    for row in _rows("venues_week11.csv"):
        assert row["venue_on_schedule_card"] or row["venue_on_game_centre"], row["game_id"]


def test_calibration_covers_every_designation_and_prints_n():
    cal, per = AV.designation_calibration()
    assert len(cal) == 4
    for row in cal:
        assert int(row["n_players_joined"]) > 0
        assert 0.0 <= float(row["observed_play_rate"]) <= 1.0
    # 'Out' must be a hard exclusion far more often than a play
    out = next(r for r in cal if r["game_designation"] == "Out")
    assert float(out["observed_play_rate"]) < 0.5


def test_snapshot_chain_is_intact_and_tamper_evident():
    entries = SN.chain()
    assert SN.verify_chain(entries) == []
    bad = [dict(e) for e in entries]
    bad[1]["content_hash"] = "0" * 32
    assert SN.verify_chain(bad) != []


def test_requirement_register_deduplicates_and_keeps_worst_status():
    merged = RQ.merge()
    s = RQ.summary(merged)
    assert s["distinct_requirements"] < s["rows_in_source_registers"]
    assert s["distinct_requirements"] == len(merged)
    ids = [m["req_id"] for m in merged]
    assert len(ids) == len(set(ids))


def test_cross_pack_verification_finds_no_contradiction():
    rows = V.standings_rows() + V.results_rows()
    assert len(rows) > 900
    assert [r for r in rows if r["status"] == "mismatch"] == []


def test_builder_is_byte_identical_on_rebuild():
    def snapshot():
        import hashlib
        out = {}
        for root in ("data/nfl_ca1b", "docs/nfl-ca1b"):
            for f in sorted(os.listdir(os.path.join(REPO, root))):
                p = os.path.join(REPO, root, f)
                out[f"{root}/{f}"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        return out
    before = snapshot()
    proc = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_ca1b.py")],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = snapshot()
    changed = [k for k in sorted(before) if before[k] != after[k]]
    # Name the files: a bare digest mismatch is undiagnosable in CI, where the
    # action log is not downloadable and only the assertion text survives.
    assert not changed, (
        "rebuild changed " + ", ".join(changed)
        + "\n--- builder stdout ---\n" + proc.stdout[-1500:]
        + "\n--- builder stderr ---\n" + proc.stderr[-1500:]
    )


def test_pack_verifier_passes():
    rc = subprocess.call([sys.executable, os.path.join(REPO, "scripts", "check_nfl_ca1b.py")],
                         stdout=subprocess.DEVNULL)
    assert rc == 0
