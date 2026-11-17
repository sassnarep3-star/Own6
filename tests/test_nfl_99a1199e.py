"""Tests for the nfl_99a1199e 32-club roster-sweep pack.

Layer 1: the verifier (all 10 numbered rules) must pass on the built pack.
Layer 2: module-level identities, run independently of the CSV artifacts.
Layer 3: determinism — a second build overwrites every file byte for byte.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_99a1199e import roster_data as RD  # noqa: E402
from nfl_99a1199e import sweep as S  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_99a1199e")
DOCS = os.path.join(REPO, "docs", "nfl-99a1199e")

NFL_CLUBS = {"ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
             "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
             "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
             "TEN", "WAS"}


def _rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_verifier_passes():
    out = subprocess.run([sys.executable,
                          os.path.join(REPO, "scripts", "check_nfl_99a1199e.py")],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_module_covers_32_clubs_with_consistent_tallies():
    assert len(RD.ROSTER) == 32
    assert {e[0] for e in RD.ROSTER} == NFL_CLUBS
    for club, _slug, _read, total, active, codes, reserve in RD.ROSTER:
        assert total == active + len(reserve), club
        observed = {"ACT"} | {r[2] for r in reserve}
        assert set(codes.split(",")) == observed, club
        for name, position, status in reserve:
            assert name and position and status, (club, name)


def test_sweep_rows_match_module():
    sweep = S.sweep_rows()
    assert len(sweep) == 32
    for r in sweep:
        e = next(x for x in RD.ROSTER if x[0] == r["club"])
        assert r["total_rows"] == e[3]
        assert r["active_count"] == e[4]
        assert r["reserve_count"] == len(e[6])
        assert r["roster_url"] == f"https://www.nfl.com/teams/{e[1]}/roster/"


def test_register_reconciles_per_club():
    register = S.register_rows()
    assert len(register) == sum(len(e[6]) for e in RD.ROSTER)
    per_club = {}
    for r in register:
        assert r["status_code"] != "ACT", r
        per_club[r["club"]] = per_club.get(r["club"], 0) + 1
    for club, _slug, _read, _total, _active, _codes, reserve in RD.ROSTER:
        assert per_club.get(club, 0) == len(reserve), club


def test_code_tally_sums_to_totals():
    tally = {t["status_code"]: t["rows"] for t in S.code_tally()}
    assert tally["ACT"] == sum(e[4] for e in RD.ROSTER)
    assert sum(tally.values()) == sum(e[3] for e in RD.ROSTER)
    # the rare codes observed on exactly one page stay in the tally
    assert tally["EXE"] == 1  # SEA
    assert tally["RLS"] == 1  # SF


def test_flags_cover_every_irregularity_note():
    flags = S.flagged_rows()
    flagged_clubs = {f["club"] for f in flags}
    for club in S.IRREGULARITY_NOTES:
        assert club in flagged_clubs, club
    cats = {f["category"] for f in flags}
    assert {"name_slug_mismatch", "unusual_status", "embedded_quotes",
            "unlinked_row", "reconciliation", "cross_club_repeat"} <= cats


def test_cross_club_repeats_are_derived_and_specific():
    repeats = S.cross_club_repeats()
    # a few pairs verified by hand while reading the pages
    joined = "\n".join(r["issue"] for r in repeats)
    for name in ("Terell Smith", "Nick Broeker", "Jimmy Ciarlo", "Jakob Robinson",
                 "Josiah Deguara", "Evan Beerntsen", "James Brockermeyer", "E.J. Jenkins"):
        assert name in joined, name
    for r in repeats:
        clubs = [c for c in r["club"].split(", ")]
        assert len(clubs) >= 2, r


def test_no_forbidden_values_in_outputs():
    import re
    pat = re.compile(r"\b(price|odds|ROI|CLV|profit|profitability)\b", re.IGNORECASE)
    for path in glob.glob(os.path.join(DATA, "*.csv")):
        with open(path, newline="", encoding="utf-8") as fh:
            for i, row in enumerate(csv.reader(fh), 2):
                for cell in row:
                    c = cell.strip()
                    if c and " " not in c and pat.fullmatch(c):
                        raise AssertionError(f"{os.path.basename(path)} line {i}: {c!r}")


def test_all_urls_are_official_https():
    for path in glob.glob(os.path.join(DATA, "*.csv")):
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for key, val in row.items():
                    if key.endswith("_url") or key == "url":
                        assert val.startswith("https://www.nfl.com/"), (path, key, val)


def test_deterministic_build():
    def snap():
        h = hashlib.sha256()
        for p in sorted(glob.glob(os.path.join(DATA, "*.csv")) +
                        glob.glob(os.path.join(DOCS, "*.html"))):
            h.update(open(p, "rb").read())
        return h.hexdigest()
    before = snap()
    out = subprocess.run([sys.executable,
                          os.path.join(REPO, "scripts", "build_nfl_99a1199e.py")],
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
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
