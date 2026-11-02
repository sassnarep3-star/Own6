#!/usr/bin/env python3
"""Line-by-line verification of collected NBA data.

Checks (against official-source rows only):
  1. Recompute every team's W-L record from games_results_2026-27.csv and
     compare with standings_2026-27.csv (transcribed from nba.com/standings).
  2. Compare games played per team against standings GP consistency.
  3. Compare standings W/L against team_ratings GP/W/L (nba.com/stats advanced).
  4. Verify every CSV row carries a source_url.
Outputs verification/verification_report.csv + prints a summary.
"""
import csv, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "verification")
os.makedirs(OUT, exist_ok=True)

def load(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))

games = load("games_results_2026-27.csv")
standings = load("standings_2026-27.csv")
ratings = load("team_ratings_2026-27.csv")

report = []
def check(item, scope, expected, actual, source, status, note=""):
    report.append(dict(item=item, scope=scope, expected=expected, actual=actual,
                       source=source, status=status, note=note))

# 0. source_url presence
for row in games:
    ok = bool(row.get("source_url", "").startswith("http"))
    check(f"game {row['game_id']}", "source link", "URL present",
          row.get("source_url", ""), row.get("source_url", ""),
          "PASS" if ok else "FAIL")
for row in standings:
    ok = bool(row.get("source_url", "").startswith("http"))
    check(f"standings {row['team_abbr']}", "source link", "URL present",
          row.get("source_url", ""), row.get("source_url", ""),
          "PASS" if ok else "FAIL")
for row in ratings:
    ok = bool(row.get("source_url", "").startswith("http"))
    check(f"ratings {row['team_abbr']}", "source link", "URL present",
          row.get("source_url", ""), row.get("source_url", ""),
          "PASS" if ok else "FAIL")

# 1. recompute records from game results
wins = collections.Counter()
gp = collections.Counter()
for g in games:
    a, h, as_, hs = g["away_team"], g["home_team"], int(g["away_score"]), int(g["home_score"])
    gp[a] += 1; gp[h] += 1
    if as_ > hs: wins[a] += 1
    elif hs > as_: wins[h] += 1
    else:
        check(f"game {g['game_id']}", "decisive result", "no ties in NBA", f"{as_}-{hs}",
              g["source_url"], "FAIL", "tie found")

for s in standings:
    t = s["team_abbr"]
    exp_w, exp_l = int(s["w"]), int(s["l"])
    act_w, act_l = wins[t], gp[t] - wins[t]
    ok = (exp_w == act_w and exp_l == act_l)
    check(f"standings {t}", "W-L recomputed from game results",
          f"{exp_w}-{exp_l}", f"{act_w}-{act_l}", s["source_url"],
          "PASS" if ok else "FAIL")

# 2. ratings vs standings consistency (both official pages, cross-page check)
r_by = {r["team_abbr"]: r for r in ratings}
s_by = {s["team_abbr"]: s for s in standings}
for t, s in s_by.items():
    r = r_by.get(t)
    if not r:
        check(f"ratings {t}", "team present in advanced stats", "present", "missing",
              "https://www.nba.com/stats/teams/advanced", "FAIL")
        continue
    ok = (r["w"] == s["w"] and r["l"] == s["l"] and r["gp"] == str(int(s["w"]) + int(s["l"])))
    check(f"ratings {t}", "W-L matches standings",
          f"{s['w']}-{s['l']} (GP {int(s['w'])+int(s['l'])})",
          f"{r['w']}-{r['l']} (GP {r['gp']})",
          "https://www.nba.com/stats/teams/advanced", "PASS" if ok else "FAIL")

# 3. totals sanity: sum of team games must be even (= 2 x games)
total_team_games = sum(gp.values())
check("schedule", "sum of team GP = 2 x games",
      f"{2*len(games)}", str(total_team_games),
      "https://www.nba.com/standings", "PASS" if total_team_games == 2*len(games) else "FAIL")

# 4. every team covered
for t in s_by:
    if gp[t] == 0:
        check(f"schedule {t}", "team has games in results", ">0", "0",
              "https://www.nba.com/standings", "FAIL")

with open(os.path.join(OUT, "verification_report.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["item", "scope", "expected", "actual", "source", "status", "note"])
    w.writeheader(); w.writerows(report)

fails = [r for r in report if r["status"] != "PASS"]
print(f"checks={len(report)} pass={len(report)-len(fails)} fail={len(fails)}")
for r in fails:
    print("FAIL:", r["item"], "|", r["scope"], "| expected", r["expected"], "| actual", r["actual"], "|", r["note"])
sys.exit(1 if fails else 0)
