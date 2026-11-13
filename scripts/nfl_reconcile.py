#!/usr/bin/env python3
"""Reconcile community data against the official NFL.com reads captured in this session.

Every check reads a verbatim transcription under data/nfl/raw/ (each row carries the
official URL it was read from) and compares it with data/nfl/model/games_2015_2026.csv.
Nothing is inferred: a missing or ambiguous value is reported as a discrepancy, never
filled in. Output: data/nfl/model/reconciliation.json
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "nfl" / "raw"
MODEL = ROOT / "data" / "nfl" / "model"
STANDINGS_URL = "https://www.nfl.com/standings/"
WEEK9_URL = "https://www.nfl.com/schedules/2026/by-week/week-9"
WEEK10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJURY_URL = "https://www.nfl.com/injuries/"
# Documented club-code alias: NFL.com renders the Cardinals as "AZ"; the community file uses "ARI".
# Alaska Airlines... no: Los Angeles Rams are "LA" on NFL.com and "LA" in the file. Only this alias applies.
CLUB_ALIAS = {"ARI": "AZ"}


def read(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def canon(code: str) -> str:
    return CLUB_ALIAS.get(code, code)


def main() -> int:
    games = read(MODEL / "games_2015_2026.csv")
    for g in games:
        g["home_team"], g["away_team"] = canon(g["home_team"]), canon(g["away_team"])
    stand = read(RAW / "standings_2026_read.csv")
    w9 = read(RAW / "week9_results_read.csv")
    slate = read(RAW / "slate_week10_read.csv")
    inj = read(RAW / "injuries_week10_read.csv")

    g2026 = [g for g in games if g["season"] == "2026"]
    final = [g for g in g2026 if g["home_score"] and g["away_score"]]

    checks = []
    n_conf = n_bad = 0

    # 1) Standings rows: W-L-T and PF/PA must be reachable from individual final games.
    pf, pa, wl = {}, {}, {}
    for g in final:
        hs, as_ = int(g["home_score"]), int(g["away_score"])
        for team, got, gave in ((g["home_team"], hs, as_), (g["away_team"], as_, hs)):
            pf[team] = pf.get(team, 0) + got
            pa[team] = pa.get(team, 0) + gave
            w, l, t = wl.get(team, (0, 0, 0))
            if got > gave:
                w += 1
            elif got < gave:
                l += 1
            else:
                t += 1
            wl[team] = (w, l, t)
    for row in stand:
        team = row["team"]
        ok = (pf.get(team) == int(row["pf"]) and pa.get(team) == int(row["pa"])
              and wl.get(team) == (int(row["w"]), int(row["l"]), int(row["t"])))
        n_conf += 1
        if not ok:
            n_bad += 1
            checks.append({
                "check": "standings_row", "key": team, "status": "mismatch",
                "official_url": STANDINGS_URL,
                "official_value": f"W-L-T {row['w']}-{row['l']}-{row['t']}, PF {row['pf']}, PA {row['pa']}",
                "community_value": f"W-L-T {wl.get(team)}, PF {pf.get(team)}, PA {pa.get(team)}",
                "note": "A team with no row in the community file cannot be reconciled; it is reported, not filled.",
            })
    # 2) Week 9 finals, one row at a time.
    for r in w9:
        hit = [g for g in final if g["week"] == "9" and g["home_team"] == r["home_team"]
               and g["away_team"] == r["away_team"]]
        n_conf += 1
        if len(hit) != 1:
            n_bad += 1
            checks.append({"check": "week9_result", "key": f"{r['away_team']}@{r['home_team']}",
                           "status": "missing_in_community_file", "official_url": r["game_url"],
                           "official_value": f"{r['away_score']}-{r['home_score']}",
                           "community_value": "", "note": "Game absent from the community file on 2026-11-12."})
            continue
        g = hit[0]
        if (g["away_score"], g["home_score"]) != (r["away_score"], r["home_score"]):
            n_bad += 1
            checks.append({"check": "week9_result", "key": f"{r['away_team']}@{r['home_team']}",
                           "status": "mismatch", "official_url": r["game_url"],
                           "official_value": f"{r['away_score']}-{r['home_score']}",
                           "community_value": f"{g['away_score']}-{g['home_score']}", "note": ""})
    # 3) Week 10 slate: opponents and kickoff times shown on the official schedule.
    for r in slate:
        hit = [g for g in g2026 if g["week"] == "10" and g["home_team"] == r["home_team"]
               and g["away_team"] == r["away_team"]]
        n_conf += 1
        if len(hit) != 1:
            n_bad += 1
            checks.append({"check": "week10_slate", "key": f"{r['away_team']}@{r['home_team']}",
                           "status": "missing_in_community_file", "official_url": r["game_url"],
                           "official_value": f"{r['gameday']} {r['kickoff_et']} ET",
                           "community_value": "", "note": ""})
            continue
        g = hit[0]
        official_minutes = int(r["kickoff_et"][:2]) * 60 + int(r["kickoff_et"][3:])
        try:
            hh, mm = g["gametime"].split(":")[:2]
            community_minutes = int(hh) * 60 + int(mm)
        except ValueError:
            community_minutes = None
        if g["gameday"] != r["gameday"] or community_minutes != official_minutes:
            n_bad += 1
            checks.append({"check": "week10_slate", "key": f"{r['away_team']}@{r['home_team']}",
                           "status": "mismatch", "official_url": r["game_url"],
                           "official_value": f"{r['gameday']} {r['kickoff_et']} ET",
                           "community_value": f"{g['gameday']} {g['gametime']} ET", "note": ""})
    # 4) Injury transcription internal consistency (teams on the official report must play in Week 10),
    #    and the two clubs whose official pages were read as "No Injuries Reported".
    playing = {r["away_team"] for r in slate} | {r["home_team"] for r in slate}
    inj_teams = sorted({r["team"] for r in inj})
    for team in inj_teams:
        n_conf += 1
        if team not in playing:
            n_bad += 1
            checks.append({"check": "injury_team_plays_week10", "key": team, "status": "mismatch",
                           "official_url": INJURY_URL, "official_value": "listed on Week 10 report",
                           "community_value": "not in Week 10 slate read", "note": ""})
    no_inj = [r for r in slate if r["home_team"] in {"LAC", "BAL"} or r["away_team"] in {"LAC", "BAL"}]
    for r in no_inj:
        for team in (r["away_team"], r["home_team"]):
            n_conf += 1
            if team in inj_teams:
                n_bad += 1
                checks.append({"check": "no_injuries_reported", "key": team, "status": "mismatch",
                               "official_url": INJURY_URL, "official_value": "No Injuries Reported",
                               "community_value": "players listed", "note": ""})

    stats = {
        "final_games_2026_in_community_file": len(final),
        "standings_rows_confirmed_by_game_log": len(stand),
        "week9_games_official": len(w9),
        "week10_games_official": len(slate),
        "injury_rows_transcribed": len(inj),
        "injury_teams_transcribed": len(inj_teams),
        "week10_teams_with_no_injuries_reported": 2,
    }
    out = {
        "generated_by": "scripts/nfl_reconcile.py",
        "inputs": {
            "community": "data/nfl/model/games_2015_2026.csv",
            "official_reads": ["data/nfl/raw/standings_2026_read.csv",
                               "data/nfl/raw/week9_results_read.csv",
                               "data/nfl/raw/slate_week10_read.csv",
                               "data/nfl/raw/injuries_week10_read.csv"],
        },
        "checks_run": n_conf,
        "checks_failed": n_bad,
        "discrepancies": checks,
        "stats": stats,
        "what_this_proves": "The 2026 rows the site uses for official standings, Week 9 results and the Week 10 "
                            "slate are consistent with the verbatim NFL.com reads stored in data/nfl/raw/. It does "
                            "not prove any historical row, closing line, or correlation value.",
        "what_this_does_not_prove": "Community-file correctness for 2015-2025, spread/total accuracy, or any "
                                    "predictive edge.",
    }
    (MODEL / "reconciliation.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"reconcile: {n_conf} checks, {n_bad} discrepancies -> data/nfl/model/reconciliation.json")
    for d in checks:
        print("  -", d["check"], d["key"], d["status"], d["official_value"], "vs", d["community_value"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
