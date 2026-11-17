"""Tests for the nfl_7a59fd89 pack.

Layer 1: the verifier (all 14 numbered rules) must pass on the built pack.
Layer 2: module-level identities, run independently of page artifacts.
Layer 3: determinism — a second build overwrites every page byte for byte.

Runs both under plain `python3 tests/test_nfl_7a59fd89.py` (own harness) and
under pytest (plain assert functions with module-level setup kept side-effect
free where possible).
"""
from __future__ import annotations

import csv
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
DATA = os.path.join(REPO, "data", "nfl_7a59fd89")
DOCS = os.path.join(REPO, "docs", "nfl-7a59fd89")

from nfl_7a59fd89 import crosscheck as CC  # noqa: E402
from nfl_7a59fd89 import injury as IJ  # noqa: E402
from nfl_7a59fd89 import results as RS  # noqa: E402
from nfl_7a59fd89 import sweep as SW  # noqa: E402


def _rd(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_verifier_passes():
    out = subprocess.run([sys.executable,
                          os.path.join(REPO, "scripts", "check_nfl_7a59fd89.py")],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_sweep_register_consistency():
    reg = SW.load_register()
    swp = SW.load_sweep()
    assert len(reg) == 1142
    assert len(swp) == 32
    assert SW.verify(reg, swp) == []


def test_sweep_rejects_corrupted_block():
    reg = SW.load_register()
    swp = SW.load_sweep()
    swp[0]["res_rows"] = str(int(swp[0]["res_rows"]) + 1)
    assert SW.verify(reg, swp), "verifier must fail on a corrupted tally"


def test_league_code_totals():
    reg = SW.load_register()
    codes = {}
    for r in reg:
        codes[r["status_code"]] = codes.get(r["status_code"], 0) + 1
    assert codes == {"CUT": 160, "DEV": 511, "EXE": 1, "PUP": 19, "RES": 256, "RLS": 1,
                     "RSN": 6, "RSR": 31, "TRC": 82, "TRD": 58, "TRT": 17}


def test_injury_delta_is_name_variant_only():
    rows = IJ.delta_rows(IJ.load(IJ.PRIOR_DEFAULT), IJ.load(IJ.CURRENT_DEFAULT))
    kinds = [r["delta_kind"] for r in rows]
    assert kinds == ["NAME_VARIANT"]
    assert rows[0]["club"] == "LAR"
    assert rows[0]["player_current"] == "Kamren Curl"


def test_corpus_extension_arithmetic():
    finals = RS.load(RS.FINALS_DEFAULT)
    rows = RS.finals_to_corpus_rows(finals)
    assert len(rows) == 14
    kc = next(r for r in rows if r["away"] == "KC")
    assert (kc["away_score"], kc["home_score"]) == ("35", "13")
    assert kc["margin_home"] == "-22" and kc["total"] == "48"
    mnf = [r for r in rows if r["away"] == "LAC"]
    assert mnf and mnf[0]["away_score"] == "" and mnf[0]["margin_home"] == ""


def test_crosscheck_conflict_counts():
    rows = CC.conflicts(SW.load_register(), IJ.load(CC.HUB_DEFAULT))
    kinds = {}
    for r in rows:
        kinds[r["conflict_kind"]] = kinds.get(r["conflict_kind"], 0) + 1
    assert kinds == {"ACT_VS_HUB_OUT": 3, "DISPLAY_SLUG_MISMATCH": 5, "HUB_ABSENT": 4,
                     "NEWS_VS_TABLE": 1, "RESERVE_CODE_VS_HUB_STATUS": 32,
                     "SAME_SLUG_MULTI_PAGE": 51}
    assert all(r["disposition"].startswith("flagged") for r in rows)


def test_conflicts_csv_on_disk_matches_module():
    rows = CC.conflicts(SW.load_register(), IJ.load(CC.HUB_DEFAULT))
    disk = _rd("availability_conflicts.csv")
    assert len(rows) == len(disk) == 96
    assert [r["conflict_id"] for r in disk] == [r["conflict_id"] for r in rows]


def test_build_determinism():
    tmp = tempfile.mkdtemp()
    try:
        snap = os.path.join(tmp, "a"), os.path.join(tmp, "b")
        for snapdir in snap:
            out = subprocess.run([sys.executable,
                                  os.path.join(REPO, "scripts", "build_nfl_7a59fd89.py")],
                                 capture_output=True, text=True, cwd=REPO)
            assert out.returncode == 0, out.stdout + out.stderr
            shutil.rmtree(snapdir, ignore_errors=True)
            shutil.copytree(DOCS, snapdir)
        d1, d2 = snap
        names = sorted(os.listdir(d1))
        assert names == sorted(os.listdir(d2))
        for n in names:
            assert filecmp.cmp(os.path.join(d1, n), os.path.join(d2, n), shallow=False), \
                f"non-deterministic page: {n}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
