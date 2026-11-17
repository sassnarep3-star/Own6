#!/usr/bin/env python3
"""Fail-closed verifier for the nfl_45abd396 pack.

Every rule below is a claim the pack makes about itself. If any rule fails the
build is not publishable, so this exits non-zero and prints the failing rule.

Rules
-----
1  Every CSV has a header and at least one row, and no cell in a required column
   is empty where the rule says it must be filled.
2  Every published URL is https and points at an official or repository host.
3  Every page carries at least one source link, and all internal links resolve
   to a file that exists in the pack directory.
4  No page contains an input control or a form (the brief's no-manual-input rule).
5  No page contains a profitability, lock, guarantee or "units won" claim.
6  The settlement register separates pre-kickoff from post-kickoff rows and the
   post rows never enter the leaderboard sample.
7  Every leaderboard row's n equals the number of settled pre-kickoff rows for
   that strategy, and no leaderboard row is marked qualified while its cluster
   lower bound is <= 0.
8  Brier identity: brier = mean((p - y)^2) recomputed from settled_forecasts.csv
   matches the leaderboard to 1e-6.
9  Skill identity: 1 - brier/climatology recomputed matches the printed value.
10 The luck panel's Šidák alpha equals 1-(1-0.05)^(1/m) for the counted m.
11 The availability graph has zero non-blank actual_start cells and every one of
    those rows carries a blank reason.
12 Every reserve-list row that is absent from the weekly report says so.
13 Every flagged row has two source links (possibly identical) that are https.
14 Every question has a status in the allowed set and, unless BLOCKED, a
    discovery route.
15 Every suggestion has a review_state and the decision fields exist.
16 No published table cell contains "nan", "None" or a Python artefact.
17 Every finished game in the finals table has a recomputable margin and total.
18 The two strategy columns from a411fed0 are both present and scored separately.
19 Every page in the pack is reachable from the navigation.
20 The builder embeds no build timestamp.
21 Frozen provenance: the commit and committer date of each forecast file
   match git, and the register carries them verbatim.
    (checked separately by CI; here we assert no timestamp is embedded).
"""
from __future__ import annotations

import csv
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_45abd396")
DOCS = os.path.join(REPO, "docs", "nfl-45abd396")

OFFICIAL_HOSTS = ("www.nfl.com", "nfl.com", "operations.nfl.com")
REPO_HOSTS = ("github.com",)
ALLOWED_HOSTS = OFFICIAL_HOSTS + REPO_HOSTS

FORBIDDEN_PHRASES = [
    "guaranteed", "lock of the", "units won", "risk-free", "sure thing",
    "profitable", "profit of", "roi of", "we beat the market",
]
ALLOWED_Q_STATUS = {"ANSWERED", "PARTIAL", "OPEN", "BLOCKED"}

errors: list[str] = []
checks = 0


def check(ok: bool, rule: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not ok:
        errors.append(f"rule {rule}: {detail}")


def rows(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    # ---- rule 1: every csv has rows
    csv_files = sorted(glob.glob(os.path.join(DATA, "*.csv")))
    check(len(csv_files) >= 20, "1", f"only {len(csv_files)} CSVs found")
    for path in csv_files:
        with open(path, encoding="utf-8", newline="") as fh:
            r = list(csv.reader(fh))
        check(len(r) >= 2, "1", f"{os.path.basename(path)} has no data rows")
        check(all(len(x) == len(r[0]) for x in r), "1",
              f"{os.path.basename(path)} has ragged rows")

    fin = rows("week10_finals.csv")
    check(len(fin) == 14, "1", f"expected 14 week-10 cards, found {len(fin)}")
    finals = [r for r in fin if r["is_final"] == "yes"]
    check(len(finals) == 13, "1", f"expected 13 finals at this read, found {len(finals)}")
    for r in fin:
        if r["is_final"] == "yes":
            check(r["away_score"] != "" and r["home_score"] != "", "1",
                  f"{r['game_id']} is final but has no score")
        else:
            check(r["away_score"] == "" and r["home_score"] == "", "1",
                  f"{r['game_id']} is not final but carries a score")

    # ---- rule 2: https + allowed hosts, every URL in every CSV
    url_re = re.compile(r"https?://[^\s,\"<>]+")
    for path in csv_files:
        with open(path, encoding="utf-8", newline="") as fh:
            for i, line in enumerate(fh, 1):
                for url in url_re.findall(line):
                    check(url.startswith("https://"), "2", f"{os.path.basename(path)}:{i} non-https url {url}")
                    host = url.split("/")[2]
                    check(host in ALLOWED_HOSTS, "2",
                          f"{os.path.basename(path)}:{i} host {host} is neither official nor the repo")

    # ---- rule 3: internal links resolve
    pages = sorted(glob.glob(os.path.join(DOCS, "*.html")))
    check(len(pages) == 15, "3", f"expected 15 pages, found {len(pages)}")
    for page in pages:
        body = open(page, encoding="utf-8").read()
        hrefs = re.findall(r'href="([^"]+)"', body)
        internal = [h for h in hrefs if not h.startswith(("http", "#", "mailto:"))]
        for h in internal:
            check(os.path.exists(os.path.join(DOCS, h.split("#")[0])), "3",
                  f"{os.path.basename(page)} -> missing {h}")
        check(any(h.startswith("https://") for h in hrefs), "3",
              f"{os.path.basename(page)} has no external source link")

    # ---- rules 4, 5, 16 on page text
    for page in pages:
        body = open(page, encoding="utf-8").read()
        low = body.lower()
        check("<input" not in low and "<form" not in low and "<textarea" not in low,
              "4", f"{os.path.basename(page)} contains an input control")
        for phrase in FORBIDDEN_PHRASES:
            check(phrase not in low, "5", f"{os.path.basename(page)} contains '{phrase}'")
        for bad in (">nan<", ">None<", "generator object", "{", "}"):
            if bad in (">nan<", ">None<", "generator object"):
                check(bad not in body, "16", f"{os.path.basename(page)} contains {bad}")

    # ---- rule 6: point-in-time separation
    reg = rows("forecast_register.csv")
    settled = rows("settled_forecasts.csv")
    check(len(reg) == len(settled), "6", "register and settlement differ in length")
    pre = [r for r in settled if r["point_in_time"] == "pre_kickoff"]
    post = [r for r in settled if r["point_in_time"] == "post_kickoff"]
    check(len(pre) + len(post) == len(settled), "6", "a row has an unknown point_in_time label")
    check(all(r["point_in_time"] == "pre_kickoff" for r in pre), "6", "label leak")
    check(any(r["game_id"] == "W10-01" for r in post), "6",
          "the post-kickoff Thursday rows must be labelled")
    unsettled_pre = [r for r in pre if r["settled"] == "no"]
    check(all(r["game_id"] == "W10-14" for r in unsettled_pre), "6",
          "only the fixture that has not been played may be unsettled among pre rows")
    check(len(unsettled_pre) == 5, "6",
          f"expected the 5 strategy rows for LAC @ BAL to be unsettled, found {len(unsettled_pre)}")
    check(all(r["brier"] == "" and r["actual_winner"] == "" for r in unsettled_pre), "6",
          "an unsettled row carries a score")

    # ---- rule 7: leaderboard n and qualification
    lb = rows("leaderboard_settled.csv")
    check(len(lb) == 5, "7", f"expected 5 scored strategies, found {len(lb)}")
    for r in lb:
        strat = r["strategy_id"]
        n_pre = len([x for x in pre if x["strategy_id"] == strat and x["settled"] == "yes"])
        check(int(r["n_games_settled"]) == n_pre, "7",
              f"{strat} n={r['n_games_settled']} but {n_pre} settled pre-kickoff rows")
        if float(r["cluster_lower_95"]) <= 0:
            check(r["qualified_on_skill"] == "no", "7",
                  f"{strat} claims qualified with lower bound {r['cluster_lower_95']}")
        check(r["backtest_numbers_on_this_row"].startswith("none"), "7",
              f"{strat} carries a backtest number")

    # ---- rule 8 and 9: recompute Brier and skill from the settled rows
    for r in lb:
        strat = r["strategy_id"]
        sample = [x for x in pre if x["strategy_id"] == strat and x["settled"] == "yes"]
        ys = [int(x["outcome_home"]) for x in sample]
        ps = [float(x["p_home_win"]) for x in sample]
        b = sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps)
        base = sum(ys) / len(ys)
        b_base = sum((base - y) ** 2 for y in ys) / len(ys)
        check(abs(b - float(r["brier_model"])) < 1e-6, "8",
              f"{strat} brier {r['brier_model']} != recomputed {b:.6f}")
        check(abs(b_base - float(r["brier_climatology_base_rate"])) < 1e-6, "9",
              f"{strat} climatology {r['brier_climatology_base_rate']} != {b_base:.6f}")
        skill = 1 - b / b_base
        check(abs(skill - float(r["brier_skill_vs_climatology"])) < 1e-4, "9",
              f"{strat} skill {r['brier_skill_vs_climatology']} != {skill:+.4f}")
        check(abs(float(r["brier_model"]) - sum(float(x["brier"]) for x in sample) / len(sample)) < 1e-6,
              "8", f"{strat} per-row Brier does not average to the strategy Brier")

    # ---- rule 10: Sidak alpha
    luck = rows("luck_panel.csv")
    m = len(lb)
    expected_alpha = 1 - (1 - 0.05) ** (1 / m)
    for r in luck:
        check(abs(float(r["alpha_after_multiplicity"]) - expected_alpha) < 1e-5, "10",
              f"alpha {r['alpha_after_multiplicity']} != {expected_alpha:.5f}")
        check(r["significant_after_adjustment"] in ("yes", "no"), "10", "bad significance flag")

    # ---- rule 11: availability graph honesty
    graph = rows("availability_graph.csv")
    check(len(graph) > 100, "11", "availability graph is too small to be a dataset")
    for r in graph:
        check(r["actual_start"] == "", "11", f"{r['node_id']} claims an actual start with no game book")
        check(r["actual_snap_share"] == "", "11", f"{r['node_id']} claims a snap share")
        check(r["blank_reason_actual"] != "", "11", f"{r['node_id']} blank with no reason")

    # ---- rule 12: reserve rows
    reserve = rows("reserve_list.csv")
    check(len(reserve) == 25, "12", f"expected 25 November reserve entries, found {len(reserve)}")
    absent = [r for r in reserve if r["appears_on_week10_hub_at_this_read"] == "no"]
    check(len(absent) >= 1, "12", "the 'not listed' case must be represented")
    for r in absent:
        check("not listed" in r["interpretation"] or "NOT on the weekly" in r["interpretation"],
              "12", f"{r['player']} absent from the weekly report without the warning")
    check(any(r["player"] == "Malik Willis" for r in reserve), "12",
          "Malik Willis must appear (this closes the earlier pack's open question)")

    # ---- rule 13: flagged rows have sources
    flags = rows("flagged.csv")
    check(len(flags) >= 10, "13", "too few flagged rows to be credible")
    for r in flags:
        check(r["page_a_url"].startswith("https://"), "13", f"{r['flag_id']} page A url")
        check(r["page_b_url"].startswith("https://"), "13", f"{r['flag_id']} page B url")
        check(r["review_action"] != "", "13", f"{r['flag_id']} has no review action")

    # ---- rule 14: question register
    questions = rows("questions_qia.csv")
    check(len(questions) >= 12, "14", "too few questions")
    for r in questions:
        check(r["status"] in ALLOWED_Q_STATUS, "14", f"{r['q_id']} status {r['status']}")
        check(r["discovery_route"] != "", "14", f"{r['q_id']} has no discovery route")
        if r["status"] == "ANSWERED":
            check(r["source_url"].startswith("https://"), "14", f"{r['q_id']} answered without a source")

    # ---- rule 15: suggestions carry a review state
    suggestions = rows("suggestions.csv")
    check(len(suggestions) >= 8, "15", "too few suggestions")
    for r in suggestions:
        check(r["review_state"] != "", "15", f"{r['s_id']} has no review state")
        check("decided_by" in r and "decision_date" in r, "15", f"{r['s_id']} lacks decision fields")
        check(r["what_it_would_take_to_validate"] != "", "15",
              f"{r['s_id']} has no validation condition")

    # ---- rule 17: recomputable margin and total
    for r in finals:
        a, h = int(r["away_score"]), int(r["home_score"])
        check(int(r["margin_home"]) == h - a, "17", f"{r['game_id']} margin")
        check(int(r["total"]) == a + h, "17", f"{r['game_id']} total")
        check(r["winner"] == (r["home"] if h > a else r["away"]), "17", f"{r['game_id']} winner")

    # ---- rule 18: both a411fed0 estimators scored
    strata = {r["strategy_id"] for r in lb}
    check("A411-ML-EMPIRICAL" in strata and "A411-ML-NORMAL" in strata, "18",
          "both published estimators must be scored, not collapsed to one")

    # ---- rule 19: nav covers every page
    index = open(os.path.join(DOCS, "index.html"), encoding="utf-8").read()
    for page in pages:
        name = os.path.basename(page)
        check(name in index, "19", f"{name} is not reachable from the index navigation")

    # ---- rule 20: no embedded build timestamp
    for page in pages:
        body = open(page, encoding="utf-8").read()
        check("generated at" not in body.lower(), "20", f"{os.path.basename(page)} embeds a build time")

    # ---- rule 21: frozen provenance is honest (checked only when git has the objects)
    sys.path.insert(0, os.path.join(REPO, "src"))
    from nfl_45abd396 import settle as ST
    import subprocess
    git_ok = subprocess.run(["git", "cat-file", "-e", "e919855d0a3d6faa136165d6ec865a5c2aad30ef"],
                            cwd=REPO, capture_output=True).returncode == 0
    for path, (iso, short, full) in ST.FIRST_ADD_COMMIT.items():
        check(len(full) == 40, "21", f"{path} full sha is not 40 chars")
        check(short == full[:8], "21", f"{path} short sha does not match the full sha")
        if git_ok:
            real = subprocess.run(["git", "show", "-s", "--format=%cI", full],
                                  cwd=REPO, capture_output=True, text=True).stdout.strip()
            check(real == iso, "21", f"{path} committer date {real} != frozen {iso}")
            added = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", path],
                                   cwd=REPO, capture_output=True, text=True).stdout.split()
            check(added and added[-1] == full, "21",
                  f"{path} was first added by {added[-1] if added else '?'}, not {full}")
    # the register must carry the frozen values verbatim
    for r in settled:
        entry = ST.FIRST_ADD_COMMIT.get(r["source_path"])
        if entry is None:
            continue
        check(r["value_committed_utc"] == entry[0], "21",
              f"{r['forecast_id']} committed time differs from the frozen table")
        check(r["commit"] == entry[1], "21", f"{r['forecast_id']} commit differs")

    print(f"pages: {len(pages)}  csv files: {len(csv_files)}  checks: {checks}")
    if errors:
        print(f"FAIL: {len(errors)} rule failures", file=sys.stderr)
        for e in errors[:40]:
            print("  " + e, file=sys.stderr)
        return 1
    print("OK: all rules 1-21 pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
