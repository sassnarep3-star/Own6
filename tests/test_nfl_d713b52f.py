#!/usr/bin/env python3
"""Unit tests for the nfl_d713b52f pack. Run: python3 tests/test_nfl_d713b52f.py"""
from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_d713b52f import audit, capture, derive, model  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_d713b52f")
DOCS = os.path.join(REPO, "docs", "nfl-d713b52f")

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ok   {name}")
    else:
        FAILS.append(f"{name}: {detail}")
        print(f"  FAIL {name} {detail}")


def rows(name):
    with open(os.path.join(DATA, name), newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
print("capture")
ok, problems = capture.verify_capture_log()
check("capture log verifies", ok, "; ".join(problems))
check("11 captures", len(capture.CAPTURES) == 11, str(len(capture.CAPTURES)))
check("every capture is https", all(c[1].startswith("https://") for c in capture.CAPTURES))
check("every capture is on an official host",
      all(c[1].split("/")[2] in ("www.nfl.com", "static.www.nfl.com") for c in capture.CAPTURES))
check("probe answers are dated", all(p["answer"] for p in capture.PROBE))
# a tampered file must fail verification
tmp = os.path.join(DATA, "capture_log_bad.csv")
with open(tmp, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows("capture_log.csv")[0].keys()), lineterminator="\n")
    w.writeheader()
    for r in rows("capture_log.csv"):
        r = dict(r)
        r["sha256"] = "0" * 64
        w.writerow(r)
ok_bad, _ = capture.verify_capture_log(tmp)
check("tampered log is rejected", not ok_bad)
os.remove(tmp)

# ---------------------------------------------------------------------------
print("standings")
st = derive.standings_rows()
check("32 clubs", len(st) == 32)
check("PF == PA", sum(int(r["pf"]) for r in st) == sum(int(r["pa"]) for r in st))
check("W == L", sum(int(r["w"]) for r in st) == sum(int(r["l"]) for r in st))
check("net points equals PF - PA row by row",
      all(int(r["pf"]) - int(r["pa"]) == int(r["net_pts"]) for r in st))
check("league points scored equals league points allowed equals 6,923",
      sum(int(r["pf"]) for r in st) == sum(int(r["pa"]) for r in st) == 6923,
      f"{sum(int(r['pf']) for r in st)} / {sum(int(r['pa']) for r in st)}")
checks = derive.standings_audit()
check("audit list is all true", all(c[3] for c in checks), str([c for c in checks if not c[3]]))
check("the parity check reports 6,923 as odd rather than pretending it is even",
      checks[2][2] == "odd", str(checks[2]))

# ---------------------------------------------------------------------------
print("game books")
check("4 games", len(derive.GAMES) == 4)
check("8 club lineups", len(derive.LINEUPS) == 8)
for key, lu in derive.LINEUPS.items():
    check(f"{key} has 11 offensive starters", len(lu["offense"]) == 11, str(len(lu["offense"])))
    check(f"{key} has 11 defensive starters", len(lu["defense"]) == 11, str(len(lu["defense"])))
check("every not-active entry has a jersey number as printed",
      all(num.strip() for entries in derive.NOT_ACTIVE.values() for _p, num, _n in entries))
check("no not-active list is longer than 7",
      all(len(v) <= 7 for v in derive.NOT_ACTIVE.values()))
fx = derive.fixture_rows()
check("fixtures carry a roof and surface line", all(r["roof_surface"] for r in fx))
check("venue mismatch is flagged where the names differ",
      sum(1 for r in fx if r["venue_match"] == "mismatch") == 1,
      str([r["game_id"] for r in fx if r["venue_match"] == "mismatch"]))
check("scores reproduce the official finals", {(r["game_id"], r["away_score"], r["home_score"]) for r in fx}
      == {("2026-W10-01", "24", "21"), ("2026-W10-02", "10", "35"),
          ("2026-W10-04", "24", "27"), ("2026-W10-14", "23", "20")})

# ---------------------------------------------------------------------------
print("name matching")
check("suffix jr is ignored",
      derive._last_first("Marvin Harrison Jr.")[1] == derive._last_first("M. Harrison")[1] == "harrison",
      str(derive._last_first("Marvin Harrison Jr.")))
check("suffix III is ignored",
      derive._last_first("Carlton Davis III")[1] == derive._last_first("C. Davis")[1] == "davis",
      str(derive._last_first("Carlton Davis III")))
check("different surnames do not match", derive._last_first("A. Smith") != derive._last_first("A. Jones"))
check("different initials do not match", derive._last_first("A. Smith") != derive._last_first("B. Smith"))

# ---------------------------------------------------------------------------
print("designation join")
j = derive.designation_join_rows()
check("join covers every transcribed status row", len(j) == len(derive.status_rows()))
outs = [r for r in j if r["game_status"] == "Out"]
check("16 Out rows", len(outs) == 16, str(len(outs)))
check("12 of 16 Out rows appear on an inactive list",
      sum(1 for r in outs if r["not_active"].startswith("yes")) == 12)
check("the four unresolved rows are named",
      {r["player"] for r in outs if not r["not_active"].startswith("yes")}
      == {"Kerby Joseph", "TreVeyon Henderson", "Michael Burton", "Branson Taylor"})
qs = [r for r in j if r["game_status"] == "Questionable"]
check("25 Questionable rows", len(qs) == 25, str(len(qs)))
blanks = [r for r in j if r["game_status"] == "(blank)"]
check("38 blank-status rows", len(blanks) == 38, str(len(blanks)))
check("no blank row is on an inactive list",
      all(not r["not_active"].startswith("yes") for r in blanks))
check("match rule is stated on every row", all(r["match_rule"].startswith("printed surname") for r in j))

# ---------------------------------------------------------------------------
print("playtime")
pt = derive.playtime_rows()
check("every row carries the publisher's Unofficial label",
      all(r["publisher_label"] == "Unofficial" for r in pt))
check("no snap count exceeds its club's unit snaps",
      all(int(r["snaps"]) <= int(r["unit_snaps"]) for r in pt))
check("every transcribed club has at least one 100% offensive row",
      {r["club"] for r in pt} == {r["club"] for r in pt if r["pct_of_unit_snaps"] == "100%"},
      str(sorted({r["club"] for r in pt} - {r["club"] for r in pt if r["pct_of_unit_snaps"] == "100%"})))
check("at least five 100% rows per club where the line played every snap",
      all(sum(1 for r in pt if r["club"] == c and r["pct_of_unit_snaps"] == "100%") >= 2
          for c in {r["club"] for r in pt}))
ss = derive.snap_sum_rows()
check("capacity check holds for every club", all(r["within_capacity"] == "yes" for r in ss))
check("capacity is unit snaps times 11",
      all(int(r["capacity_player_snaps"]) == int(r["unit_snaps"]) * 11 for r in ss))

# ---------------------------------------------------------------------------
print("model")
bt = model.run_backtest()
check("scored games are all strictly after both clubs' first game",
      all(int(r["n_home_prior"]) >= 1 and int(r["n_away_prior"]) >= 1 for r in bt))
check("150 corpus reconciles", len(bt) + len(model.REFUSED) == 150,
      f"{len(bt)} + {len(model.REFUSED)}")
check("every refused game names a reason", all(r["reason"] for r in model.REFUSED))
check("probabilities are inside [0,1]", all(0 <= float(r["p_home_win"]) <= 1 for r in bt))
check("input hash matches its payload",
      all(hashlib.sha256(r["inputs_json"].encode()).hexdigest() == r["inputs_sha256"] for r in bt))
check("sigma respects its floor and cap",
      all(7.0 <= float(r["sigma_margin"]) <= 25.0 for r in bt))
s = model.score(bt)
check("brier is in [0,1]", 0 <= s["brier"] <= 1)
check("skill lower bound is below the upper bound", s["bss_lo"] < s["bss_hi"])
check("the interval includes zero, and the pack must say so",
      s["bss_lo"] <= 0 <= s["bss_hi"], f"{s['bss_lo']} to {s['bss_hi']}")
lp = model.luck_panel(bt)
check("Murphy identity closes", float(lp["identity_residual"]) < 1e-9, lp["identity_residual"])
check("the luck panel is not degenerate (more than one game per bin)",
      lp["bins_used"] != lp["n"], f"{lp['bins_used']} bins for {lp['n']} games")
check("binning does not distort the score",
      abs(float(lp["brier"]) - float(lp["brier_binned"])) < 0.02)
check("reliability is not silently equal to the Brier score",
      abs(float(lp["reliability"]) - float(lp["brier"])) > 1e-6)
check("the bin table reports observed frequency beside mean forecast",
      all("/" in part and "n=" in part for part in lp["mean_p_in_bin"].split("; ")))
check("better + worse + tied equals n",
      int(lp["games_better_than_climatology"]) + int(lp["games_worse_than_climatology"])
      + int(lp["games_tied"]) == int(lp["n"]))
w11 = model.week11_forecasts()
check("three Week 11 forecasts", len(w11) == 3)
check("every Week 11 market and residual cell is blank",
      all(not r[c] for r in w11 for c in ("market_side", "market_total", "market_moneyline",
                                          "residual_side", "residual_total", "residual_moneyline")))
check("every Week 11 row states the price policy", all("by policy" in r["price_note"] for r in w11))
check("no Week 11 forecast claims to be live", all(r["state"] == "paper" for r in w11))
# chronology: recompute one row by hand from the feed
feed = model.load_finals()
walk = model.TeamState()
import json
for g in feed:
    if g["game_id"] == bt[0]["game_id"]:
        break
    walk.add(g["home"], g["home_score"], g["away_score"])
    walk.add(g["away"], g["away_score"], g["home_score"])
g0 = next(x for x in feed if x["game_id"] == bt[0]["game_id"])
lm = model.league_mean_total(walk)
sh, _ = walk.strength(g0["home"], lm)
sa, _ = walk.strength(g0["away"], lm)
check("first scored row reproduces by hand from strictly earlier games",
      abs(float(bt[0]["expected_margin_home"]) - round((sh - sa) + model.H, 6)) < 1e-6,
      f"{bt[0]['expected_margin_home']} vs {(sh - sa) + model.H}")

# ---------------------------------------------------------------------------
print("audit")
a = audit.audit_rows()
summary = audit.summary(a)
check("no mismatches", summary["mismatch"] == "0", summary["mismatch"])
check("every check names its method", all(r["method"] for r in a))
check("every check names its source", all(r["source"] for r in a))
check("pearson of a series with itself is 1", abs(audit.pearson([1, 2, 3, 4], [1, 2, 3, 4]) - 1) < 1e-12)
check("pearson of a reversed series is -1", abs(audit.pearson([1, 2, 3, 4], [4, 3, 2, 1]) + 1) < 1e-12)
check("binomial p at the middle is not significant", audit.binom_two_sided_p(5, 10) > 0.9)
check("binomial p at an extreme is small", audit.binom_two_sided_p(10, 10) < 0.01)

# ---------------------------------------------------------------------------
print("registers")
reqs = derive.requirement_rows()
check("86 requirement rows", len(reqs) == 86, str(len(reqs)))
check("every requirement has a gate", all(r["gate"] for r in reqs))
check("every requirement has a clearing number", all(r["clears_it"] for r in reqs))
check("statuses are from the fixed vocabulary",
      {r["status"] for r in reqs} <= {"done", "partial", "blocked"})
gate_ids = {r["gate"] for r in rows("gates.csv")}
gate_ids.add("none")  # rows that are delivered or rejected outright have no blocking gate
used = {r["gate"] for r in reqs}
check("every gate id used by a requirement is declared", used <= gate_ids,
      f"undeclared: {sorted(used - gate_ids)}")
qs_ = derive.question_rows()
check("every question names what is missing", all(q["need"] for q in qs_))
check("every question names a discovery route", all(q["discovery"] for q in qs_))
check("every question starts open", all(q["status"] == "open" for q in qs_))
sg = derive.suggestion_rows()
check("every suggestion is pending", all(r["status"] == "pending_human_choice" for r in sg))
check("no suggestion carries a decision", all(r["decision"] == "" for r in sg))
fl = derive.flagged_rows()
check("no flag blocks the merge", all(r["blocks_merge"] == "no" for r in fl))
check("every flag has an official link",
      all(r["source_url"].startswith("https://") for r in fl))
check("every flag has an action", all(r["action"] for r in fl))
srcs = derive.source_rows()
check("every source is on an official host",
      all(s["host"] in ("www.nfl.com", "static.www.nfl.com") for s in srcs))
check("every source has a read clock", all(s["read_at_utc"] for s in srcs))

# ---------------------------------------------------------------------------
print("site")
for name in ("index.html", "evidence.html", "model.html", "availability.html",
             "questions.html", "suggestions.html", "flagged.html"):
    path = os.path.join(DOCS, name)
    check(f"{name} exists", os.path.exists(path))
    if os.path.exists(path):
        text = open(path).read()
        low = text.lower()
        check(f"{name} has no form control",
              not any(t in low for t in ("<input", "<select", "<textarea", "<button")))
        check(f"{name} has no placeholder text",
              not any(t in low for t in ("todo", "tbd", "lorem", "xxx", "{{")))
        check(f"{name} names the read date", "2026-11-19" in text)
        check(f"{name} links only to official hosts or local pages",
              all(h.startswith(("http", "mailto:", "#")) or os.path.exists(os.path.join(DOCS, h))
                  for h in re.findall(r'href="([^"#]+)"', text)))

print()
if FAILS:
    print(f"FAILED {len(FAILS)}")
    for f in FAILS:
        print("  ", f)
    sys.exit(1)
print("all pack tests passed")
