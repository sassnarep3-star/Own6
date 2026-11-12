#!/usr/bin/env python3
"""Build every NFL artefact for the site (no network, no manual input).

Outputs
  data/nfl/model/backtest.json      walk-forward lines, results, gates, leaderboard
  data/nfl/model/correlations.json  C1-C4 dependence studies
  data/nfl/model/week10.json        own-line origination for the Week 10 slate
  data/nfl/model/availability.json  starter/backup deficiency board
  data/nfl/model/summary.json       one-page evidence state

Run:  python3 scripts/nfl_analysis.py
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfllab import availability, calibration, combos, correlation, harness, pricing, ratings, validation  # noqa: E402

DATA = ROOT / "data" / "nfl"
MODEL = DATA / "model"
TEST_SEASON = 2025           # fully completed season: the only honest holdout available offline
PRIOR_SEASON = 2024          # secondary holdout for stability
DEPTH_TEAMS = ("WAS", "NYG", "DET")


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def canon(games):
    for g in games:
        if g["home_team"] == "ARI":
            g["home_team"] = "AZ"
        if g["away_team"] == "ARI":
            g["away_team"] = "AZ"
    return games


def main() -> int:
    games = canon(read_csv(MODEL / "games_2015_2026.csv"))
    meta = json.loads((MODEL / "games_2015_2026.meta.json").read_text())
    recon = json.loads((MODEL / "reconciliation.json").read_text())

    # ---------- 1. Walk-forward backtest ----------
    sigma_m = ratings.holdout_sigma(games, TEST_SEASON)
    sigma_t = sigma_m * 1.06
    main_test = harness.backtest(games, TEST_SEASON, sigma_m, sigma_t)
    prior_test = harness.backtest(games, PRIOR_SEASON, ratings.holdout_sigma(games, PRIOR_SEASON),
                                  ratings.holdout_sigma(games, PRIOR_SEASON) * 1.06)
    boards = harness.gate_board(main_test, n_trials=len(harness.STRATEGY_FAMILY))
    main_games = harness.season_lines(games, TEST_SEASON)["games"]
    scores = {sid: {"roi_lower": (r["roi_ci"][0] if r["roi_ci"] else None)} for sid, r in main_test["results"].items()}
    board_rows = validation.leaderboard(boards, scores)

    # Calibration of the model's cover probability against the market probability, per tested game.
    cal_rows = []
    cover_probs, cover_out, market_probs = [], [], []
    for g in main_games:
        if not g["home_score"]:
            continue
        p = pricing.cover_probability(g["model_margin"], g["market_spread"], sigma_m)
        if p["push"] > 0:
            continue
        cover_probs.append(p["p_home"])
        cover_out.append(1.0 if (float(g["home_score"]) - float(g["away_score"]) + g["market_spread"]) > 0 else 0.0)
        market_probs.append(0.5)
    if cover_probs:
        bss = calibration.brier_skill_score(cover_probs, cover_out, market_probs)
        ece = calibration.expected_calibration_error(cover_probs, cover_out)
        rel = calibration.reliability(cover_probs, cover_out)
    else:
        bss, ece, rel = {}, None, []
    cal_rows = reliability_rows = rel

    backtest = {
        "test_season": TEST_SEASON,
        "prior_season_check": PRIOR_SEASON,
        "package_version": __import__("nfllab").__version__,
        "data_input": {"file": "data/nfl/model/games_2015_2026.csv", "sha256": meta["sha256"],
                       "rows": meta["rows"], "source": meta["repository"], "commit": meta["commit"],
                       "license": meta["license"], "license_status": meta["license_status"]},
        "reconciliation": {"checks": recon["checks_run"], "failed": recon["checks_failed"]},
        "configuration": {
            "market_anchor": harness.MARKET_ANCHOR,
            "shrink_to_market": harness.SHRINK_TO_MARKET,
            "min_edge_points": harness.MIN_EDGE,
            "sigma_margin": round(sigma_m, 4),
            "sigma_total": round(sigma_t, 4),
            "season_decay": ratings.SEASON_DECAY,
            "shrink_games": ratings.SHRINK_GAMES,
            "bet_price_assumption": "-110 for historical spread/total bets (NOT a verified price)",
            "holdout": "2025 regular season; fit window 2015-2024 only",
        },
        "results": {
            sid: {k: v for k, v in r.items() if k not in ("returns", "detail")}
            for sid, r in main_test["results"].items()
        },
        "prior_season_results": {
            sid: {k: v for k, v in r.items() if k not in ("returns", "detail")}
            for sid, r in prior_test["results"].items()
        },
        "calibration": {**bss, "ece": ece,
                        "note": "Market probability is taken as 0.5 at the closing line; this understates the "
                                "market's own information and is disclosed as a limitation, not a result."},
        "reliability": reliability_rows,
        "bets_logged": len(main_test["detail"]),
        "detail_sample": main_test["detail"][:400],
        "team_ratings": sorted(
            ({"team": t, "off": round(main_test["ratings"].off[t], 3),
              "def": round(main_test["ratings"].deff[t], 3),
              "games_weighted": round(main_test["ratings"].games[t], 2),
              "off_se": round(main_test["ratings"].off_se[t], 3)}
             for t in main_test["ratings"].off), key=lambda r: r["team"]),
        "hfa": round(main_test["ratings"].hfa, 3),
        "league_mean_points": round(main_test["ratings"].mu, 3),
        "fitted_rows": main_test["ratings"].fitted_rows,
        "gates": boards,
        "leaderboard": board_rows,
        "qualifiers": [b for b in board_rows if b["status"] == "qualifies"],
    }

    # ---------- 2. Week 10 own lines ----------
    slate = read_csv(DATA / "raw" / "slate_week10_read.csv")
    rat = harness.season_lines(games, TEST_SEASON)["ratings"]
    week10 = []
    for g in slate:
        home, away = g["home_team"], g["away_team"]
        raw_margin = rat.expected_margin(home, away)
        raw_total = rat.expected_total(home, away)
        margin = raw_margin          # no market anchor is applied pre-game: this is the model's own line
        se = rat.margin_se(home, away)
        live = {
            "spread": round(-margin * 2) / 2.0,
            "total": round(raw_total * 2) / 2.0,
            "moneyline_home": pricing.prob_to_american(pricing.win_probability(margin, sigma_m)["p_home"]),
            "moneyline_away": pricing.prob_to_american(pricing.win_probability(margin, sigma_m)["p_away"]),
            "win_prob_home": pricing.win_probability(margin, sigma_m)["p_home"],
            "win_prob_tie": pricing.win_probability(margin, sigma_m)["tie"],
        }
        alt = pricing.alternate_lines(margin, raw_total, sigma_m, sigma_t,
                                      [live["spread"], -3.0, -2.5, 2.5, 3.0],
                                      [live["total"], live["total"] - 3, live["total"] + 3])
        week10.append({
            "gameday": g["gameday"], "kickoff_et": g["kickoff_et"], "away": away, "away_club": g["away_club"],
            "home": home, "home_club": g["home_club"], "game_url": g["game_url"],
            "model_margin_home": round(margin, 2), "model_margin_se": round(se, 2),
            "model_total": round(raw_total, 2),
            "own_spread_home": live["spread"], "own_total": live["total"],
            "own_ml_home": live["moneyline_home"], "own_ml_away": live["moneyline_away"],
            "p_home_win": round(live["win_prob_home"], 4), "p_tie": round(live["win_prob_tie"], 4),
            "spread_interval": [round(-(margin + 1.96 * sigma_m), 1), round(-(margin - 1.96 * sigma_m), 1)],
            "total_interval": [round(raw_total - 1.96 * sigma_t, 1), round(raw_total + 1.96 * sigma_t, 1)],
            "alt_lines": {str(k): {kk: round(vv, 4) for kk, vv in v.items()} for k, v in alt["spreads"].items()},
            "market_spread": "", "market_total": "", "market_source": "",
            "market_status": "blank_unverified: no official NFL line feed; see Flagged for Review",
            "notes": "Own line = model expectation only. Not a recommendation, not validated.",
        })

    # ---------- 3. Availability / depth deficiency ----------
    injuries = availability.load_injuries(DATA / "raw" / "injuries_week10_read.csv")
    depth = availability.load_depth(DATA / "raw" / "depth_charts_read.csv")
    avail_rows = []
    for team in DEPTH_TEAMS:
        for row in availability.depth_deficiency(injuries, depth, team):
            avail_rows.append(row)
    team_index = {t: availability.team_deficiency([r for r in avail_rows if r["team"] == t]) for t in DEPTH_TEAMS}
    availability_out = {
        "clubs_with_official_depth_chart_and_injury_report": list(DEPTH_TEAMS),
        "clubs_missing_depth_chart": sorted({i.team for i in injuries} - set(DEPTH_TEAMS)),
        "rows": avail_rows,
        "team_index": {t: round(v, 4) for t, v in team_index.items()},
        "parameters": {"position_weight": availability.POSITION_WEIGHT,
                       "string_penalty": availability.STRING_PENALTY,
                       "practice_risk": availability.PRACTICE_RISK,
                       "status_certainty": availability.STATUS_CERTAINTY,
                       "points_per_index": 3.0, "cap_points": 3.0},
        "missing_data": "No snap-share, PFF grade, or expected-points-lost feed is configured, so the index is a "
                        "transparent weight x string-gap x status-risk product, not a measured effect.",
    }

    # ---------- 4. Dependence studies ----------
    hist = [g for g in games if g["season"] != "2026"]
    corr = {
        "C1_same_game_cover_over": combos.c1_same_game_cover_over(hist),
        "C2_cross_game_pairs": combos.c2_cross_game_pairs(hist),
        "C3_abs_margin_total": combos.c3_margin_total(hist),
        "window": {"seasons": "2015-2025", "games": len(hist)},
        "combo_pricing_example": combos.combo_price_table(0.52, 0.55, None, [2.61, 2.7]),
    }

    # ---------- 5. Summary ----------
    summary = {
        "generated_by": "scripts/nfl_analysis.py",
        "as_of": "2026-11-12",
        "reconciliation": {"checks": recon["checks_run"], "discrepancies": recon["checks_failed"]},
        "holdout_season": TEST_SEASON,
        "candidates": len(harness.STRATEGY_FAMILY),
        "testable_candidates": sum(1 for c in harness.STRATEGY_FAMILY if c["status"] == "testable"),
        "qualified_strategies": len(backtest["qualifiers"]),
        "leaderboard_entries": len([r for r in board_rows if r["rank"] is not None]),
        "own_lines_published": len(week10),
        "own_lines_with_market_cell_blank": sum(1 for r in week10 if r["market_spread"] == ""),
        "injury_rows_published": len(injuries),
        "depth_rows_published": len(depth),
        "availability_rows": len(avail_rows),
        "dependence_studies_available": sum(1 for k in ("C1_same_game_cover_over", "C2_cross_game_pairs", "C3_abs_margin_total")
                                            if corr[k].get("available")),
        "no_profitability_claim": True,
    }

    for name, payload in (("backtest", backtest), ("week10", {"games": week10, "as_of": "2026-11-12"}),
                          ("correlations", corr), ("availability", availability_out), ("summary", summary)):
        (MODEL / f"{name}.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"analysis: holdout {TEST_SEASON} sigma={sigma_m:.2f} bets={len(main_test['detail'])} "
          f"qualified={summary['qualified_strategies']} C1_phi="
          f"{corr['C1_same_game_cover_over'].get('phi')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
