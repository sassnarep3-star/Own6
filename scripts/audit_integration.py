#!/usr/bin/env python3
"""Repeatable integration audit (session f58e0178). Stdlib only. Exit 1 on any FAIL.

Checks things earlier per-site checkers did not: committed merge-conflict markers, published
metrics vs. recomputation, market-probability arithmetic, and result/schedule consistency.
"""
import csv, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
fails = []

def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        fails.append(name)

def rd(*a):
    with open(P(*a), newline="") as f:
        return list(csv.DictReader(f))

# 1. conflict markers in tracked text files
tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
bad = []
for t in tracked:
    if not t or not t.endswith((".html", ".md", ".py", ".csv", ".json", ".yml", ".txt", ".css", ".js")):
        continue
    try:
        txt = open(P(t), encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        continue
    if re.search(r"^(<<<<<<< |>>>>>>> )", txt, re.M):
        bad.append(t)
check("no committed merge-conflict markers", not bad, ", ".join(bad))

# 2. published backtest metrics == recomputation from game-level rows
bt = rd("data", "backtest_walkforward.csv")
pub = {r["metric"]: r["value"] for r in rd("verification", "backtest_metrics.csv")}
mean = lambda k: sum(float(x[k]) for x in bt) / len(bt)
for k, pk in (("brier_model", "brier_model"), ("brier_coin", "brier_coin"), ("logloss_model", "logloss_model"), ("sign_hit", "sign_accuracy_model_fav")):
    check(f"backtest {k} recomputes to published {pk}", abs(mean(k) - float(pub[pk])) < 5e-5, f"{mean(k):.5f} vs {pub[pk]}")
vm = open(P("research", "validation.md"), encoding="utf-8").read()
check("research/validation.md Brier row matches recomputation", "0.2408" in vm and "0.6654" not in vm)

# 3. market fair probability arithmetic (American odds -> probability, proportional de-vig)
imp = lambda ml: 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)
ok = True
for r in rd("data", "our_lines_2026-11-02.csv"):
    a, b = imp(int(r["fav_ml_current"])), imp(int(r["dog_ml_current"]))
    fair = a / (a + b)
    if abs(fair - float(r["market_fav_fair_prob"])) > 1e-4:
        ok = False
check("our_lines market_fav_fair_prob = proportional de-vig of current moneylines", ok)

# 4. results file vs official schedule ids / teams
games = json.load(open(P("data", "games.json")))["rows"]
res = rd("data", "results_2026-11-02.csv")
check("results: 15 rows, ids match schedule", sorted(r["game_id"] for r in res) == sorted(g["game_id"] for g in games))
check("results: every row has an nba.com source link", all(r["source_url"].startswith("https://www.nba.com/game/") for r in res))
check("results: scores are integers, no ties", all(int(r["home_score"]) != int(r["away_score"]) for r in res))

# 5. re-verified historical rows still equal the main results file
base = {r["game_id"]: r for r in rd("data", "games_results_2026-27.csv")}
ok = all(all(base[r["game_id"]][k] == r[k] for k in ("away_team", "away_score", "home_team", "home_score")) for r in rd("data", "reverification_results_2026-11-03.csv"))
check("re-verified rows equal data/games_results_2026-27.csv", ok)

# 5b. W-L recomputed from all 107 result rows == official standings read 2026-11-03
tot = {}
for fn in ("games_results_2026-27.csv", "results_2026-11-02.csv"):
    for g in rd("data", fn):
        a, h = g["away_team"], g["home_team"]
        win, lose = (h, a) if int(g["home_score"]) > int(g["away_score"]) else (a, h)
        tot.setdefault(win, [0, 0])[0] += 1
        tot.setdefault(lose, [0, 0])[1] += 1
live = {r["team_abbr"]: [int(r["w"]), int(r["l"])] for r in rd("data", "standings_live_2026-11-03.csv")}
check("recomputed W-L (107 games) == official standings for all 30 teams", len(live) == 30 and tot == live)

# 6. forward-test file reproducible
before = open(P("data", "forward_test_summary_2026-11-02.csv")).read()
subprocess.run([sys.executable, P("scripts", "forward_test.py")], capture_output=True, check=True)
check("forward test is deterministic", before == open(P("data", "forward_test_summary_2026-11-02.csv")).read())

print("\nRESULT:", "FAIL: " + "; ".join(fails) if fails else "all checks passed")
sys.exit(1 if fails else 0)
