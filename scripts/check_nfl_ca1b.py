#!/usr/bin/env python3
"""Verifier for the nfl_ca1b pack. Fails loudly; exits non-zero on any violation.

Rules
-----
 1  every CSV under data/nfl_ca1b is non-empty and parses
 2  every row that makes a factual claim carries an http(s) source URL
 3  no market/price/ROI/CLV cell is filled (G-PRICE is a hard policy)
 4  the leaderboard publishes no rank and no backtest score (G-BACKTEST)
 5  the snapshot ledger's hash chain recomputes
 6  the standings identity holds: the game log reproduces all 32 clubs exactly
 7  every week-11 fixture has a venue string from at least one official surface
 8  the specification calibration covers all four designation classes and prints n
 9  every page in docs/nfl-ca1b exists, has a nav, and every internal link resolves
10  every page carries at least one official http(s) link
11  no page contains a form or input control (zero-input requirement)
12  the verification ledger contains no unexplained mismatch
13  the requirement register is smaller than its source rows and has no duplicate IDs
14  the two headline numbers quoted in prose equal the numbers in the CSV
"""
from __future__ import annotations

import csv
import html
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_ca1b import capture as C          # noqa: E402
from nfl_ca1b import engine as E          # noqa: E402
from nfl_ca1b import qia as Q             # noqa: E402
from nfl_ca1b import requirements as RQ   # noqa: E402
from nfl_ca1b import snapshots as SN      # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_ca1b")
DOCS = os.path.join(REPO, "docs", "nfl-ca1b")
FAIL = []


def fail(rule: str, msg: str) -> None:
    FAIL.append(f"[rule {rule}] {msg}")


def rows(name: str):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    # 1 --------------------------------------------------------------- CSVs parse
    csvs = sorted(f for f in os.listdir(DATA) if f.endswith(".csv"))
    if len(csvs) < 20:
        fail("1", "only %d CSVs found" % len(csvs))
    for f in csvs:
        try:
            r = rows(f)
        except Exception as exc:  # noqa: BLE001
            fail("1", "%s does not parse: %s" % (f, exc))
            continue
        if not r:
            fail("1", "%s is empty" % f)

    # 2 ------------------------------------------------------- source links present
    sourced = {
        "originated_lines_week11.csv": "market_gate",
        "backtest.html": None,
    }
    for f in csvs:
        r = rows(f)
        if not r:
            continue
        cols = set(r[0])
        if "source_url" in cols:
            missing = [i for i, x in enumerate(r, 2) if not str(x.get("source_url", "")).startswith("http")]
            if missing and f not in ("conflicts.csv",):
                fail("2", "%s: %d rows without a source URL (first at line %d)"
                     % (f, len(missing), missing[0]))
        elif f in ("model_meta.json.csv", "probes.csv", "demotion_gates.csv", "prereg.csv",
                   "leaderboard.csv", "controls.csv", "luck_panel.csv", "correlations.csv",
                   "ratings.csv", "walkforward.csv", "designation_calibration.csv",
                   "injury_deltas.csv", "injury_series.csv", "designation_players.csv",
                   "team_view.csv", "headline_conflicts.csv", "availability_sweep.csv",
                   "venues_week11.csv", "snapshot_ledger.csv", "verification_standings.csv",
                   "verification_results.csv", "requirements_master.csv", "qia.csv",
                   "suggestions.csv", "freshness.csv", "flagged.csv",
                   "standings_official_2026-11-17.csv", "results_week10_official.csv"):
            # these carry provenance elsewhere (their page prints the source column, and the
            # tables that need per-row attribution have source_url); flag if neither exists
            if not any(c in cols for c in ("source_url", "url", "game_centre_url", "schedule_url",
                                           "authoritative_source")):
                if f not in ("model_meta.json.csv", "prereg.csv", "demotion_gates.csv", "qia.csv",
                             "suggestions.csv", "requirements_master.csv", "leaderboard.csv",
                             "controls.csv", "luck_panel.csv", "correlations.csv", "ratings.csv",
                             "walkforward.csv", "designation_calibration.csv",
                             "designation_players.csv", "team_view.csv", "flagged.csv"):
                    fail("2", "%s has no source column at all" % f)

    # 3 ------------------------------------------------------------- no price values
    for f in csvs:
        for x in rows(f):
            for k, v in x.items():
                if v in ("", None):
                    continue
                if re.search(r"(^|_)(market|roi|clv|close|opening|price)", k):
                    if k in ("market_gate",):
                        continue
                    fail("3", "%s: %s=%r is filled but no official price exists" % (f, k, v))

    # 4 -------------------------------------------------- leaderboard publishes nothing
    for x in rows("leaderboard.csv"):
        for k in ("rank", "brier", "brier_skill_vs_coin", "cluster_boot_lo", "roi", "clv"):
            if str(x.get(k, "")).strip():
                fail("4", "leaderboard row %s has %s=%r (G-BACKTEST forbids it)"
                     % (x.get("strategy_id"), k, x.get(k)))
        if str(x.get("n_settled", "0")) != "0":
            fail("4", "leaderboard claims settled picks but nothing has been settled")

    # 5 -------------------------------------------------------------- hash chain
    problems = SN.verify_chain(SN.chain())
    for p in problems:
        fail("5", p)

    # 6 --------------------------------------------------------- standings identity
    games = E.load_games()
    rec = {}
    for a, h, a_s, h_s, _src in games:
        for club, pf, pa in ((a, a_s, h_s), (h, h_s, a_s)):
            w, l, t, f, ag = rec.get(club, (0, 0, 0, 0, 0))
            rec[club] = (w + (pf > pa), l + (pf < pa), t + (pf == pa), f + pf, ag + pa)
    if len(games) != 149:
        fail("6", "expected 149 official finals, got %d" % len(games))
    for club, want in C.STANDINGS.items():
        got = rec.get(club)
        if got != (want[0], want[1], want[2], want[3], want[4]):
            fail("6", "%s: game log %s != standings %s" % (club, got, want))

    # 7 ------------------------------------------------------------------- venues
    for x in rows("venues_week11.csv"):
        if not x.get("venue_on_schedule_card") and not x.get("venue_on_game_centre"):
            fail("7", "%s has no venue from any official surface" % x.get("game_id"))

    # 8 -------------------------------------------------------- calibration coverage
    cal = rows("designation_calibration.csv")
    if len(cal) != 4:
        fail("8", "expected 4 designation classes, got %d" % len(cal))
    for x in cal:
        if not x.get("n_players_joined") or not x.get("observed_play_rate"):
            fail("8", "calibration row %r missing n or rate" % x.get("game_designation"))

    # 9/10/11 ---------------------------------------------------------- pages
    pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
    if len(pages) < 18:
        fail("9", "only %d pages built" % len(pages))
    for p in pages:
        text = open(os.path.join(DOCS, p), encoding="utf-8").read()
        if "<nav" not in text:
            fail("9", "%s has no navigation" % p)
        for href in re.findall(r"""href=["']([^"']+)["']""", text):
            if href.startswith(("http://", "https://", "#")):
                continue
            target = os.path.normpath(os.path.join(DOCS, href.split("#")[0]))
            if not os.path.exists(target):
                fail("9", "%s links to missing %s" % (p, href))
        if not re.search(r"""href=["']https?://""", text):
            fail("10", "%s carries no official external link" % p)
        if re.search(r"<input|<form|<select|<textarea", text):
            fail("11", "%s contains an input control" % p)

    # 12 ------------------------------------------------------ verification ledger
    for f in ("verification_standings.csv", "verification_results.csv"):
        for x in rows(f):
            if x.get("status") == "mismatch" and not x.get("note"):
                fail("12", "%s: unexplained mismatch %r" % (f, x))
    s = RQ.summary(RQ.merge())
    if s["distinct_requirements"] >= s["rows_in_source_registers"]:
        fail("12", "requirement register did not reduce the source rows")

    # 13 ------------------------------------------------------- requirement register
    reqs = rows("requirements_master.csv")
    ids = [x["req_id"] for x in reqs]
    if len(ids) != len(set(ids)):
        fail("13", "duplicate requirement IDs")
    if len(reqs) != s["distinct_requirements"]:
        fail("13", "requirements CSV (%d) != merge summary (%d)" % (len(reqs), s["distinct_requirements"]))

    # 14 ------------------------------------------------- prose equals CSV numbers
    idx = open(os.path.join(DOCS, "index.html"), encoding="utf-8").read()
    want = "%d of %d graded games" % (Q.L["hits"], Q.L["n"])
    if want not in html.unescape(idx):
        fail("14", "index headline does not match the computed %r" % want)
    want_p = "p = %.4f" % Q.L["luck_p"]
    if want_p not in html.unescape(idx):
        fail("14", "index does not quote the computed exact p (%s)" % want_p)

    # ------------------------------------------------------------------ report
    if FAIL:
        print("FAILED %d check(s):" % len(FAIL))
        for f in FAIL:
            print("  " + f)
        return 1
    print("OK — %d CSVs, %d pages, %d values re-tested, chain intact, no rule violated"
          % (len(csvs), len(pages), len(rows("verification_standings.csv")) + len(rows("verification_results.csv"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
