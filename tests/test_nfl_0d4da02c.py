"""Tests for the nfl_0d4da02c pack.

Layer 1: the verifier (all numbered rules) must pass on the built pack.
Layer 2: module-level identities, checked independently of page artifacts.
Layer 3: determinism — a second build overwrites every page byte for byte.

Runs under plain `python3 tests/test_nfl_0d4da02c.py` (own harness) and under
pytest (plain assert functions).
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
DATA = os.path.join(REPO, "data", "nfl_0d4da02c")
DOCS = os.path.join(REPO, "docs", "nfl-0d4da02c")

from nfl_0d4da02c import analysis as AN  # noqa: E402
from nfl_0d4da02c import capture as CP  # noqa: E402
from nfl_0d4da02c import decisions as DC  # noqa: E402
from nfl_0d4da02c import flags as FL  # noqa: E402
from nfl_0d4da02c import register as RG  # noqa: E402

CONTROL_PAT = re.compile(r"<(input|select|textarea|button)\b", re.I)
LINK_PAT = re.compile(r'href="([^"]+)"')
OFFICIAL_HOSTS = {"www.nfl.com", "nfl.com", "operations.nfl.com", "api.weather.gov",
                  "github.com"}


def rows(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pages() -> list[str]:
    return sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))


# ---------------------------------------------------------------------------
# layer 1
# ---------------------------------------------------------------------------
def test_verifier_passes():
    rc = subprocess.call([sys.executable, "scripts/check_nfl_0d4da02c.py"], cwd=REPO)
    assert rc == 0, "pack verifier failed"


# ---------------------------------------------------------------------------
# layer 2 — capture
# ---------------------------------------------------------------------------
def test_practice_mapping_is_the_official_text():
    assert CP.PRACTICE == {
        "FP": "Full Participation in Practice",
        "LP": "Limited Participation in Practice",
        "DNP": "Did Not Participate In Practice",
    }


def test_injury_counts():
    total = sum(len(v[1]) for v in CP.INJURY.values())
    assert total == 347, total
    assert len(CP.INJURY) == 28, len(CP.INJURY)
    for club in ("CHI", "DEN", "PHI", "TB"):
        assert club not in CP.INJURY
        assert club in CP.WEEK10_ABSENT_CLUBS


def test_week11_covers_all_32_clubs():
    seen = set()
    for g in CP.WEEK11_GAMES:
        seen.add(g[3])   # away
        seen.add(g[5])   # home
    for club, _rec in CP.WEEK11_BYES:
        assert club not in seen, f"{club} is both playing and on bye"
        seen.add(club)
    assert len(seen) == 32, len(seen)
    assert len(CP.WEEK11_GAMES) == 13
    assert len(CP.WEEK11_BYES) == 6


def test_every_injury_code_is_known():
    for club, (_label, players) in CP.INJURY.items():
        for _p, _pos, _inj, prac, game in players:
            assert prac in CP.PRACTICE, (club, prac)
            assert game in ("", "Out", "Doubtful", "Questionable"), (club, game)


def test_transcript_hashes_are_stable():
    assert len(CP.transcript_injury()) > 0
    assert len(CP.transcript_schedule()) > 0
    assert len(CP.transcript_announcements()) > 0
    h = CP._sha(CP.transcript_injury())
    assert len(h) == 64 and h == CP._sha(CP.transcript_injury())


# ---------------------------------------------------------------------------
# layer 2 — register
# ---------------------------------------------------------------------------
def test_requirement_gates_all_defined():
    gate_ids = {g[0] for g in RG.GATES}
    for r in RG.REQUIREMENTS + RG.PROCESS:
        if r[4]:
            assert r[4] in gate_ids, (r[0], r[4])


def test_every_gate_has_a_clearing_number():
    for g in RG.GATES:
        assert g[4].strip(), g[0]


def test_requirement_ids_unique():
    ids = [r[0] for r in RG.REQUIREMENTS + RG.PROCESS]
    assert len(ids) == len(set(ids))


def test_status_vocabulary():
    vocab = {"cleared", "cleared_repo", "structural", "blocked", "rejected", "open",
             "partially cleared", "needs review", "in progress"}
    for r in RG.REQUIREMENTS + RG.PROCESS:
        assert r[3] in vocab, (r[0], r[3])


# ---------------------------------------------------------------------------
# layer 2 — decisions
# ---------------------------------------------------------------------------
def test_every_suggestion_has_at_least_two_options():
    counts: dict[str, int] = {}
    for o in DC.OPTIONS:
        counts[o[1]] = counts.get(o[1], 0) + 1
    for s in DC.SUGGESTIONS:
        assert counts.get(s[0], 0) >= 2, s[0]


def test_no_orphan_options():
    ids = {s[0] for s in DC.SUGGESTIONS}
    for o in DC.OPTIONS:
        assert o[1] in ids, o[0]


def test_decision_columns_ship_blank():
    for r in rows("suggestions.csv"):
        assert not (r["owner_decision"] or "").strip()
        assert not (r["decision_date"] or "").strip()
    for r in rows("suggestion_options.csv"):
        assert not (r["owner_choice"] or "").strip()


def test_question_and_gap_shapes():
    for q in DC.QIA:
        assert q[1].strip(), q[0]
        assert q[2].strip(), q[0]      # what we have
        assert q[4] is not None        # answer may legitimately be blank
        assert q[5].strip(), q[0]      # answer status is always stated
    for g in DC.GAPS:
        assert g[3].strip(), g[0]      # acquisition route
        assert g[4].strip(), g[0]      # clearing number


def test_flags_carry_a_source_or_say_they_do_not():
    for f in FL.FLAGS:
        assert f[1] in ("pack", "inherited"), f[0]
        assert f[2] in ("high", "medium", "low"), f[0]


# ---------------------------------------------------------------------------
# layer 2 — analysis
# ---------------------------------------------------------------------------
def test_designation_counts_sum_to_the_register():
    inj = rows("injury_report_2026_11_18.csv")
    counts = rows("designation_counts.csv")
    game_status = {r["value"]: int(r["n"]) for r in counts
                   if r["dimension"] == "game_status"}
    assert sum(game_status.values()) == len(inj)
    practice = {r["value"]: int(r["n"]) for r in counts
                if r["dimension"] == "practice_status"}
    assert sum(practice.values()) == len(inj)


def test_position_groups_partition_the_register():
    inj = rows("injury_report_2026_11_18.csv")
    groups = rows("position_group_counts.csv")
    assert sum(int(g["n_rows"]) for g in groups) == len(inj)
    covered = set()
    for _label, codes in AN.POSITION_GROUPS:
        covered.update(codes)
    for r in inj:
        assert r["position"] in covered, r["position"]


def test_club_counts_include_the_bye_clubs_as_blank():
    clubs = rows("club_injury_counts.csv")
    assert len(clubs) == 32
    blank_row_clubs = {r["club"] for r in clubs if not r["n_rows"].strip()}
    assert blank_row_clubs == {"CHI", "DEN", "PHI", "TB"}


def test_calibration_status_admits_the_missing_denominator():
    cal = rows("designation_calibration_status.csv")
    not_computable = [r for r in cal if r["status"] == "not computable"]
    assert not_computable, "the missing outcome leg must be recorded, not hidden"
    for r in not_computable:
        assert r["n_denominator"] == "0"


# ---------------------------------------------------------------------------
# layer 2 — pages
# ---------------------------------------------------------------------------
def test_pages_exist():
    assert len(pages()) == 14


def test_no_interactive_controls():
    for p in pages():
        text = open(os.path.join(DOCS, p), encoding="utf-8").read()
        assert not CONTROL_PAT.search(text), p


def test_internal_links_resolve():
    for p in pages():
        text = open(os.path.join(DOCS, p), encoding="utf-8").read()
        for href in LINK_PAT.findall(text):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = os.path.normpath(os.path.join(DOCS, href.split("?")[0].split("#")[0]))
            assert os.path.exists(target), f"{p} -> {href}"


def test_data_rows_all_carry_an_official_source():
    from urllib.parse import urlparse
    must = [("injury_report_2026_11_18.csv", "source_url"),
            ("week11_schedule.csv", "game_url"),
            ("starter_announcements.csv", "source_url")]
    for name, col in must:
        for r in rows(name):
            host = (urlparse(r[col]).hostname or "").lower()
            assert host in OFFICIAL_HOSTS, (name, r[col])


# ---------------------------------------------------------------------------
# layer 3 — determinism
# ---------------------------------------------------------------------------
def test_build_is_deterministic():
    before = {p: hashlib.sha256(open(os.path.join(DOCS, p), "rb").read()).hexdigest()
              for p in pages()}
    subprocess.run([sys.executable, "scripts/build_nfl_0d4da02c.py"], cwd=REPO,
                   capture_output=True, check=True)
    after = {p: hashlib.sha256(open(os.path.join(DOCS, p), "rb").read()).hexdigest()
             for p in pages()}
    assert before == after


# ---------------------------------------------------------------------------
def _main() -> int:
    tests = [(k, v) for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL {name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  ERR  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
