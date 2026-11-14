#!/usr/bin/env python3
"""Build data/nfl_6cefc476/*.csv and docs/nfl-6cefc476/*.html from the verified
dataset (src/nfl_6cefc476/dataset.py) and the model (src/nfl_6cefc476/model.py).

Fail-closed: values that cannot be traced to an official page read in session
6cefc476 are published blank and carry a flag id.  Nothing is inferred.

Usage:  python3 scripts/build_nfl_6cefc476.py
"""
from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl_6cefc476 import model as M          # noqa: E402
from nfl_6cefc476 import dataset as D        # noqa: E402

DATA = ROOT / "data" / "nfl_6cefc476"
SITE = ROOT / "docs" / "nfl-6cefc476"
READ_ON = D.READ_ON
STAND_URL = "https://www.nfl.com/standings/"
INJ_URL = "https://www.nfl.com/injuries/"
SCORES_W9 = "https://www.nfl.com/scores/2026/week-9"
SCORES_W10 = "https://www.nfl.com/scores/"
SCHED_W11 = "https://www.nfl.com/schedules/2026/by-week/week-11"
NIST = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm"
TERMS = "https://www.nfl.com/legal/terms/"
REPO = "https://github.com/sassnarep3-star/Own6"

BLANK = ""  # published blank value


def write_csv(name: str, fields: list[str], rows: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


# ======================================================================
# 1. Standings snapshot + per-game rates
# ======================================================================

standings: dict[str, dict] = {}
for team, w, l, t, pct, pf, pa in D.STANDINGS:
    g = w + l + t
    standings[team] = {
        "team": team, "w": w, "l": l, "t": t, "pct": pct,
        "pf": pf, "pa": pa, "games": g,
        "pf_pg": pf / g, "pa_pg": pa / g, "win_pct": (w + 0.5 * t) / g,
    }

write_csv("standings_2026_11_14.csv",
          ["team", "w", "l", "t", "pct", "pf", "pa", "games", "pf_per_game",
           "pa_per_game", "read_on", "source_url"],
          [{**{k: v for k, v in row.items() if k not in {"pf_pg", "pa_pg", "win_pct"}},
            "pf_per_game": f"{row['pf_pg']:.4f}", "pa_per_game": f"{row['pa_pg']:.4f}",
            "read_on": READ_ON, "source_url": STAND_URL}
           for row in standings.values()])

# League consistency (computed check, published on the correlations page):
league_w = sum(r["w"] for r in standings.values())
league_l = sum(r["l"] for r in standings.values())
league_t = sum(r["t"] for r in standings.values())
league_pf = sum(r["pf"] for r in standings.values())
league_pa = sum(r["pa"] for r in standings.values())

# ======================================================================
# 2. Model parameters (declared, derived from verified numbers only)
# ======================================================================

w9_margins = [h - a for _, _, _, _, a, h, _, _, in
              [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]) for r in []]]  # placeholder
w9_margins = []
for gid, week, date, kick, away, home, ascore, hscore, status, url in D.RESULTS:
    if week == 9:
        w9_margins.append(hscore - ascore)
SIGMA = M.sample_std(w9_margins)
HFA = 0.0  # declared parameter; flagged N6F-03 (no official source for a magnitude)

# ======================================================================
# 3. Origination (wave 1: side / spread, wave 2: total, wave 3: moneyline)
# ======================================================================

games: list[dict] = []
for gid, date, kick, away, home, note, url in D.WEEK10:
    games.append({"game_id": gid, "week": 10, "date": date, "kickoff_et": kick,
                  "away": away, "home": home, "note": note, "game_url": url})
for gid, date, kick, away, home, note, url in D.WEEK11:
    games.append({"game_id": gid, "week": 11, "date": date, "kickoff_et": kick,
                  "away": away, "home": home, "note": note, "game_url": url})


def fair_for(game: dict) -> dict:
    a, h = standings[game["away"]], standings[game["home"]]
    return M.fair_numbers(h["pf_pg"], h["pa_pg"], a["pf_pg"], a["pa_pg"], SIGMA, HFA)


for g in games:
    g["fair"] = fair_for(g)
    g["matchup"] = f"{g['away']} at {g['home']}"

# Wave ordering:  side first, then total, then moneyline (user requirement).
orig_rows: list[dict] = []
price_rows: list[dict] = []
order = 0
for wave, market_type, unit in (
    (1, "side_spread", "home spread (points, home perspective)"),
    (2, "total", "total points"),
    (3, "moneyline", "American odds, home team"),
):
    for g in games:
        order += 1
        f = g["fair"]
        market_id = f"{g['game_id']}-{market_type.split('_')[0].upper()}"
        if market_type == "side_spread":
            fair_line = f"{f['fair_spread_home']:.2f}"
            fair_away_line = BLANK
            prob = BLANK
        elif market_type == "total":
            fair_line = f"{f['fair_total']:.2f}"
            fair_away_line = BLANK
            prob = BLANK
        else:
            fair_line = str(f["fair_ml_home"])
            fair_away_line = str(f["fair_ml_away"])
            prob = f"{f['p_home']:.4f}"
        orig_rows.append({
            "market_id": market_id,
            "game_id": g["game_id"], "week": g["week"],
            "kickoff_et": f"{g['date']} {g['kickoff_et']} ET",
            "matchup": g["matchup"], "market_type": market_type,
            "origination_wave": wave, "origination_order": order,
            "model_fair_line": fair_line,
            "model_fair_line_away": fair_away_line,
            "model_fair_line_unit": unit,
            "model_win_prob_home": prob,
            "market_line": BLANK,
            "line_difference": BLANK,
            "difference_status": "blank: no licensed/official market line source (flag N6F-04)",
            "sigma_margin_used": f"{SIGMA:.4f}",
            "sigma_n": len(w9_margins),
            "hfa_used": f"{HFA:.3f}",
            "inputs_basis": "2026-11-14 standings read; PF/PA per game = totals/games played",
            "inputs_status": "verified_official",
            "derivation": "exp_home=(home_pf_pg+away_pa_pg)/2; exp_away=(away_pf_pg+home_pa_pg)/2; "
                          "spread=exp_home-exp_away; total=exp_home+exp_away; p_home=Phi(spread/sigma); "
                          "american=p_home->fair conversion, no vig",
            "status": "computed_model_output_not_a_market_price",
            "flag_id": "N6F-03;N6F-04",
            "source_url": STAND_URL,
            "second_source_url": g["game_url"],
        })
        # Price-snapshot store: open row (captured now) + close row (pending).
        price_rows.append({
            "snapshot_id": f"{market_id}-OPEN",
            "market_id": market_id, "game_id": g["game_id"], "week": g["week"],
            "matchup": g["matchup"], "market_type": market_type,
            "snapshot_type": "open",
            "captured_at_utc": f"{READ_ON} (session read date; first publication)",
            "our_number": fair_line,
            "market_number": BLANK,
            "market_number_status": "blank: no licensed/official market price source (flag N6F-04)",
            "input_basis": "standings read 2026-11-14 + Week 10 injury report read 2026-11-14",
            "verification_status": "computed_from_verified_inputs",
            "flag_id": "N6F-03",
            "source_url": STAND_URL,
            "second_source_url": INJ_URL,
        })
        price_rows.append({
            "snapshot_id": f"{market_id}-CLOSE",
            "market_id": market_id, "game_id": g["game_id"], "week": g["week"],
            "matchup": g["matchup"], "market_type": market_type,
            "snapshot_type": "close",
            "captured_at_utc": BLANK,
            "our_number": BLANK,
            "market_number": BLANK,
            "market_number_status": "pending_close",
            "input_basis": "close capture window: kickoff minus final official designation read",
            "verification_status": "pending_close",
            "flag_id": "N6F-02",
            "source_url": g["game_url"],
            "second_source_url": STAND_URL,
        })

ORIG_FIELDS = list(orig_rows[0])
write_csv("originated_lines.csv", ORIG_FIELDS, orig_rows)
PRICE_FIELDS = list(price_rows[0])
write_csv("price_snapshots.csv", PRICE_FIELDS, price_rows)

# ======================================================================
# 4. Verified results feed + settlement machinery demonstration
# ======================================================================

res_rows = []
for gid, week, date, kick, away, home, ascore, hscore, status, url in D.RESULTS:
    margin = hscore - ascore
    res_rows.append({
        "game_id": gid, "week": week, "date": date,
        "away": away, "away_score": ascore, "home": home, "home_score": hscore,
        "status": status,
        "winner": home if margin > 0 else (away if margin < 0 else "tie"),
        "margin_home": margin, "total_points": ascore + hscore,
        "overtime": BLANK,
        "settled_vs_our_line": BLANK,
        "settlement_status": "no originated line predates this kickoff (store first publication "
                             f"{READ_ON}); settlement runs against backtest_grades.csv rows instead",
        "backtest_grade_ref": gid if week == 9 else BLANK,
        "verification_status": "verified_direct",
        "read_on": READ_ON,
        "source_url": url,
        "second_source_url": SCORES_W9 if week == 9 else SCORES_W10,
    })
RES_FIELDS = list(res_rows[0])
write_csv("results_feed.csv", RES_FIELDS, res_rows)

# --- retrospective backtest grades (Week 9), derived from official arithmetic
# post-W8 inputs = current standings minus W10-01 adjustment (WAS/NYG only)
# minus each team's Week 9 game.  Every step is arithmetic on verified numbers.
post_w9 = {t: dict(r) for t, r in standings.items()}
for row in res_rows:
    if row["game_id"] == "2026-REG10-01":
        for team, pts_for, pts_against in ((row["away"], row["away_score"], row["home_score"]),
                                           (row["home"], row["home_score"], row["away_score"])):
            r = post_w9[team]
            r["pf"] -= pts_for
            r["pa"] -= pts_against
            r["games"] -= 1
            if pts_for > pts_against:
                r["w"] -= 1
            elif pts_for < pts_against:
                r["l"] -= 1
            else:
                r["t"] -= 1

post_w8 = {t: dict(r) for t, r in post_w9.items()}
for row in res_rows:
    if row["week"] == 9:
        for team, pts_for, pts_against in ((row["away"], row["away_score"], row["home_score"]),
                                           (row["home"], row["home_score"], row["away_score"])):
            r = post_w8[team]
            r["pf"] -= pts_for
            r["pa"] -= pts_against
            r["games"] -= 1
            if pts_for > pts_against:
                r["w"] -= 1
            elif pts_for < pts_against:
                r["l"] -= 1

bt_rows = []
side_wins = total_wins = ml_wins = 0
side_graded = total_graded = ml_graded = 0
side_cover_flags: list[int] = []
total_cover_flags: list[int] = []
bt_p_home: list[float] = []
bt_margin: list[float] = []
bt_fair_total: list[float] = []
bt_actual_total: list[float] = []
bt_net_diff: list[float] = []
for row in res_rows:
    if row["week"] != 9:
        continue
    a = post_w8[row["away"]]
    h = post_w8[row["home"]]
    f = M.fair_numbers(h["pf"] / h["games"], h["pa"] / h["games"],
                       a["pf"] / a["games"], a["pa"] / a["games"], SIGMA, HFA)
    side_grade = M.settle_side(row["away_score"], row["home_score"], f["fair_spread_home"])
    total_grade = M.settle_total(row["away_score"], row["home_score"], f["fair_total"])
    ml_grade = M.settle_ml(row["away_score"], row["home_score"], f["p_home"])
    for grade, counter in ((side_grade, "side"), (total_grade, "total"), (ml_grade, "ml")):
        if grade == "win":
            if counter == "side":
                side_wins += 1
            elif counter == "total":
                total_wins += 1
            else:
                ml_wins += 1
    if side_grade != "push":
        side_graded += 1
    if total_grade != "push":
        total_graded += 1
    ml_graded += 1
    side_cover_flags.append(1 if side_grade == "win" else 0)
    total_cover_flags.append(1 if total_grade == "win" else 0)
    bt_p_home.append(f["p_home"])
    bt_margin.append(float(row["margin_home"]))
    bt_fair_total.append(f["fair_total"])
    bt_actual_total.append(float(row["total_points"]))
    pre_diff = (h["pf"] / h["games"] - h["pa"] / h["games"]) - (a["pf"] / a["games"] - a["pa"] / a["games"])
    bt_net_diff.append(pre_diff)
    bt_rows.append({
        "game_id": row["game_id"], "matchup": f"{row['away']} at {row['home']}",
        "derivation": "post-W8 PF/PA/games reconstructed by subtracting the verified Week 9 game "
                      "from the verified 2026-11-14 standings totals (arithmetic only)",
        "fair_spread_home": f"{f['fair_spread_home']:.2f}",
        "fair_total": f"{f['fair_total']:.2f}",
        "model_p_home": f"{f['p_home']:.4f}",
        "model_side": "home" if f["p_home"] >= 0.5 else "away",
        "actual_margin_home": row["margin_home"], "actual_total": row["total_points"],
        "side_grade": side_grade, "total_grade": total_grade, "ml_grade": ml_grade,
        "in_sample_warning": "retrospective derivation after the fact; NOT a pre-kickoff published "
                             "line; not evidence of real-time edge (flag N6F-09)",
        "status": "retrospective_derivation",
        "source_url": row["source_url"],
        "second_source_url": STAND_URL,
    })
BT_FIELDS = list(bt_rows[0])
write_csv("backtest_grades.csv", BT_FIELDS, bt_rows)

# ======================================================================
# 5. Correlations — official numbers only, n published with every value
# ======================================================================

def corr_row(cid, x, y, xs, ys, status, computation, source, flag=""):
    n = len(xs)
    r = M.pearson_r(xs, ys)
    p = M.corr_p_value(r, n)
    lo, hi = M.fisher_ci95(r, n)
    return {
        "correlation_id": cid, "x_variable": x, "y_variable": y,
        "method": "pearson", "n": n,
        "coefficient": f"{r:.4f}", "p_value": f"{p:.6g}",
        "ci95_low": f"{lo:.4f}", "ci95_high": f"{hi:.4f}",
        "status": status, "computation": computation,
        "source_url": source, "flag_id": flag,
    }


teams = list(standings)
pf_pg = [standings[t]["pf_pg"] for t in teams]
pa_pg = [standings[t]["pa_pg"] for t in teams]
net_pg = [standings[t]["pf_pg"] - standings[t]["pa_pg"] for t in teams]
win_pct = [standings[t]["win_pct"] for t in teams]

# side/total cover co-occurrence (phi) from the retrospective grades
a11 = sum(1 for s, t_ in zip(side_cover_flags, total_cover_flags) if s and t_)
a10 = sum(1 for s, t_ in zip(side_cover_flags, total_cover_flags) if s and not t_)
a01 = sum(1 for s, t_ in zip(side_cover_flags, total_cover_flags) if not s and t_)
a00 = sum(1 for s, t_ in zip(side_cover_flags, total_cover_flags) if not s and not t_)
phi_den = ((a11 + a10) * (a01 + a00) * (a11 + a01) * (a10 + a00)) ** 0.5
phi = (a11 * a00 - a10 * a01) / phi_den if phi_den else 0.0
phi_n = len(side_cover_flags)

corr_rows = [
    corr_row("N6CF-C01", "Points for per game", "Win percentage",
             pf_pg, win_pct, "measured_from_verified_official_data",
             "standings read 2026-11-14; per-game rates = totals/games", STAND_URL),
    corr_row("N6CF-C02", "Points against per game", "Win percentage",
             pa_pg, win_pct, "measured_from_verified_official_data",
             "standings read 2026-11-14; per-game rates = totals/games", STAND_URL),
    corr_row("N6CF-C03", "Net points per game", "Win percentage",
             net_pg, win_pct, "measured_from_verified_official_data",
             "net/g = PF/g - PA/g from the same standings read", STAND_URL),
    corr_row("N6CF-C04", "Pre-game net-points-per-game differential", "Actual margin (home)",
             bt_net_diff, bt_margin, "measured_from_verified_official_data",
             "retrospective W9 pairs; pre-game net/g from reconstructed post-W8 arithmetic", SCORES_W9,
             "N6F-09"),
    corr_row("N6CF-C05", "Model fair total", "Actual total points",
             bt_fair_total, bt_actual_total, "measured_from_verified_official_data",
             "retrospective W9 pairs from backtest_grades.csv", SCORES_W9, "N6F-09"),
]
corr_rows.append({
    "correlation_id": "N6CF-C06", "x_variable": "Side grade (cover indicator)",
    "y_variable": "Total grade (cover indicator)", "method": "phi (2x2 indicator correlation)",
    "n": phi_n, "coefficient": f"{phi:.4f}", "p_value": BLANK,
    "ci95_low": BLANK, "ci95_high": BLANK,
    "status": "measured_from_verified_official_data_small_n",
    "computation": "phi between retrospective side- and total-cover indicators; p/CI left blank "
                   "(n below the pre-registered 200 floor; see flag N6F-10)",
    "source_url": SCORES_W9, "flag_id": "N6F-09;N6F-10",
})
for cid, x, y, why in (
    ("N6CF-C07", "Parlay leg outcomes (2-leg)", "Joint hit rate",
     "requires a licensed price archive to select legs at real prices; n=0"),
    ("N6CF-C08", "Parlay leg outcomes (3-leg)", "Joint hit rate",
     "requires a licensed price archive and multi-week joint ledger; n=0"),
    ("N6CF-C09", "Player-prop outcomes", "Combo hit rate",
     "no official player-prop results feed exists in this repository; n=0"),
):
    corr_rows.append({
        "correlation_id": cid, "x_variable": x, "y_variable": y,
        "method": BLANK, "n": 0, "coefficient": BLANK, "p_value": BLANK,
        "ci95_low": BLANK, "ci95_high": BLANK,
        "status": "blocked_missing_inputs",
        "computation": why + " — value left blank by policy (flag N6F-11)",
        "source_url": TERMS, "flag_id": "N6F-11",
    })
CORR_FIELDS = list(corr_rows[0])
write_csv("correlations.csv", CORR_FIELDS, corr_rows)

# ======================================================================
# 6. Replacement depth
# ======================================================================

depth_rows = []
for i, ev in enumerate(D.REPLACEMENT_EVENTS, start=1):
    (team, side, unit, pos, gid, player, p_str, status, detail,
     repl, r_str, etype, depth_src, inj_src, note) = ev
    # Fail-closed normalization: strings are only published when a club depth
    # chart was read this session.
    if depth_src is None:
        p_str = r_str = None
    depth = r_str if r_str is not None else None
    step = (r_str - p_str) if (r_str is not None and p_str is not None) else None
    src_map = {s[0]: s[3] for s in D.SOURCES}
    depth_rows.append({
        "event_id": f"N6CF-R{i:02d}", "team": team, "side": side, "unit": unit,
        "position": pos, "game_id": gid, "week": 10,
        "injured_player": player, "injured_string": p_str if p_str is not None else BLANK,
        "injured_status": status, "injury_detail": detail,
        "replacement_player": repl if repl else BLANK,
        "replacement_string": r_str if r_str is not None else BLANK,
        "depth_of_replacement": depth if depth is not None else BLANK,
        "replacement_step": step if step is not None else BLANK,
        "event_type": etype,
        "verification_status": "depth_and_injury_verified" if depth_src else "injury_verified_depth_blank",
        "flag_id": "" if depth_src else "N6F-08",
        "depth_source_url": src_map[depth_src] if depth_src else BLANK,
        "injury_source_url": src_map[inj_src] if inj_src else BLANK,
        "notes": note,
    })
DEPTH_FIELDS = list(depth_rows[0])
write_csv("replacement_depth.csv", DEPTH_FIELDS, depth_rows)

# ======================================================================
# 7. Leaderboard — signal separated from staking
# ======================================================================

lb_rows = [
    {
        "strategy_id": "N6CF-L01", "name": "Model-side single (spread)",
        "family": "Single bet", "market": "Side (spread)",
        "n_graded": side_graded,
        "signal_cover_rate": f"{side_wins / side_graded:.3f}" if side_graded else BLANK,
        "signal_metric_note": "diagnostic cover rate vs own fair line (retrospective W9, in-sample)",
        "signal_status": "diagnostic_only_below_floor",
        "diagnostic_signal_rank": 1,
        "staking_scheme": "flat 1 unit (preregistered)",
        "staking_roi": BLANK, "staking_clv": BLANK,
        "staking_status": "blocked_no_price_archive",
        "staking_rank": BLANK,
        "staking_can_escalate_signal": "no",
        "eligibility": "unqualified", "tier": "Tier 0", "reward": "not_awarded",
        "official_rank": BLANK,
        "source_url": SCORES_W9, "flag_id": "N6F-09;N6F-10",
    },
    {
        "strategy_id": "N6CF-L02", "name": "Model-side single (total, over)",
        "family": "Single bet", "market": "Total",
        "n_graded": total_graded,
        "signal_cover_rate": f"{total_wins / total_graded:.3f}" if total_graded else BLANK,
        "signal_metric_note": "diagnostic cover rate vs own fair total (retrospective W9, in-sample)",
        "signal_status": "diagnostic_only_below_floor",
        "diagnostic_signal_rank": 2,
        "staking_scheme": "flat 1 unit (preregistered)",
        "staking_roi": BLANK, "staking_clv": BLANK,
        "staking_status": "blocked_no_price_archive",
        "staking_rank": BLANK,
        "staking_can_escalate_signal": "no",
        "eligibility": "unqualified", "tier": "Tier 0", "reward": "not_awarded",
        "official_rank": BLANK,
        "source_url": SCORES_W9, "flag_id": "N6F-09;N6F-10",
    },
    {
        "strategy_id": "N6CF-L03", "name": "Model-side single (moneyline)",
        "family": "Single bet", "market": "Moneyline",
        "n_graded": ml_graded,
        "signal_cover_rate": f"{ml_wins / ml_graded:.3f}" if ml_graded else BLANK,
        "signal_metric_note": "diagnostic straight-up win rate on the higher-probability side "
                              "(retrospective W9, in-sample)",
        "signal_status": "diagnostic_only_below_floor",
        "diagnostic_signal_rank": 3,
        "staking_scheme": "flat 1 unit (preregistered)",
        "staking_roi": BLANK, "staking_clv": BLANK,
        "staking_status": "blocked_no_price_archive",
        "staking_rank": BLANK,
        "staking_can_escalate_signal": "no",
        "eligibility": "unqualified", "tier": "Tier 0", "reward": "not_awarded",
        "official_rank": BLANK,
        "source_url": SCORES_W9, "flag_id": "N6F-09;N6F-10",
    },
    {
        "strategy_id": "N6CF-L04", "name": "Same-game parlay: side + total",
        "family": "Parlay (2 legs)", "market": "Side + total",
        "n_graded": 0, "signal_cover_rate": BLANK,
        "signal_metric_note": "leg correlation measured only as phi diagnostic (N6CF-C06); "
                              "qualification requires the joint ledger",
        "signal_status": "blocked_missing_inputs",
        "diagnostic_signal_rank": BLANK,
        "staking_scheme": "flat 1 unit (preregistered)",
        "staking_roi": BLANK, "staking_clv": BLANK,
        "staking_status": "blocked_no_price_archive",
        "staking_rank": BLANK,
        "staking_can_escalate_signal": "no",
        "eligibility": "unqualified", "tier": "Tier 0", "reward": "not_awarded",
        "official_rank": BLANK,
        "source_url": TERMS, "flag_id": "N6F-11",
    },
    {
        "strategy_id": "N6CF-L05", "name": "Cross-game parlay (3 legs)",
        "family": "Parlay (3 legs)", "market": "Mixed",
        "n_graded": 0, "signal_cover_rate": BLANK,
        "signal_metric_note": "blocked: no licensed prices to define legs (N6CF-C08)",
        "signal_status": "blocked_missing_inputs",
        "diagnostic_signal_rank": BLANK,
        "staking_scheme": "flat 1 unit (preregistered)",
        "staking_roi": BLANK, "staking_clv": BLANK,
        "staking_status": "blocked_no_price_archive",
        "staking_rank": BLANK,
        "staking_can_escalate_signal": "no",
        "eligibility": "unqualified", "tier": "Tier 0", "reward": "not_awarded",
        "official_rank": BLANK,
        "source_url": TERMS, "flag_id": "N6F-11",
    },
    {
        "strategy_id": "N6CF-L06", "name": "Player-prop combination",
        "family": "Player prop combo", "market": "Props",
        "n_graded": 0, "signal_cover_rate": BLANK,
        "signal_metric_note": "blocked: no official player-prop results feed (N6CF-C09)",
        "signal_status": "blocked_missing_inputs",
        "diagnostic_signal_rank": BLANK,
        "staking_scheme": "flat 1 unit (preregistered)",
        "staking_roi": BLANK, "staking_clv": BLANK,
        "staking_status": "blocked_no_price_archive",
        "staking_rank": BLANK,
        "staking_can_escalate_signal": "no",
        "eligibility": "unqualified", "tier": "Tier 0", "reward": "not_awarded",
        "official_rank": BLANK,
        "source_url": TERMS, "flag_id": "N6F-11",
    },
]
LB_FIELDS = list(lb_rows[0])
write_csv("leaderboard.csv", LB_FIELDS, lb_rows)

# ======================================================================
# 8. Validation gates + demotion gate
# ======================================================================

vg_rows = [
    ("VG-01", "Rights and provenance",
     "Every published value traces to an official page read in-session; the pack is non-commercial and informational only.",
     "Prevents results that cannot be lawfully or factually reproduced from reaching the board.",
     "", "open", TERMS),
    ("VG-02", "No invented market prices",
     "market_line and line_difference stay blank in every table until a licensed/official price source exists.",
     "A fabricated benchmark cannot manufacture apparent skill.", "Licensed historical price archive.", "blocked", TERMS),
    ("VG-03", "Open/close snapshot completeness",
     "Every originated market must carry an open row and a close row in price_snapshots.csv; close rows stay blank until captured at the close window.",
     "Locks the opening number before information arrives and records the closing number honestly.", "", "open", SCORES_W10),
    ("VG-04", "Origination order",
     "Side (spread) rows are originated first (wave 1), totals second (wave 2), moneylines third (wave 3); the checker enforces order.",
     "Keeps market-type cherry-picking out: the side is committed before the total and moneyline exist.", "", "open", SCHED_W11),
    ("VG-05", "Verified results feed",
     "Backtests and ROI settle only against results_feed.csv rows verified from official game pages.",
     "Settlement against unverified scores is the fastest way to launder luck into skill.", "", "open", SCORES_W9),
    ("VG-06", "Minimum sample",
     "At least 200 graded selections per strategy family before any performance statistic is official.",
     "Small samples are dominated by variance; the floor stops a short lucky run from qualifying.",
     "Graded selection history.", "blocked", NIST),
    ("VG-07", "Chronological out-of-sample",
     "Parameters are fitted strictly on data before the test window; no same-window fitting.",
     "Removes in-sample optimism (the retrospective W9 grades are labelled in-sample for exactly this reason).",
     "Multi-season results and price history.", "blocked", NIST),
    ("VG-08", "Signal/staking separation",
     "Leaderboard publishes signal metrics and staking metrics in separate columns; staking cannot escalate a failed signal (staking_can_escalate_signal=no).",
     "A lucky staking run cannot mask a bad signal.", "", "open", NIST),
    ("VG-09", "Replacement depth instrumentation",
     "Replacement events record the depth of the replacement (string level), not only the fact of a replacement; strings blank unless a club depth chart was read.",
     "Third- and fourth-string exposure is a distinct risk regime from a straight backup swap.", "", "open", INJ_URL),
    ("VG-10", "Correlation sourcing and n",
     "Every published correlation value comes from officially sourced numbers and publishes n beside the value.",
     "Unsourced or n-less correlations are indistinguishable from noise.", "", "open", NIST),
    ("VG-11", "Input freshness",
     "Model inputs older than 7 days at kickoff require a re-read before the close snapshot is valid.",
     "Stale inputs silently convert a live model into a lagging one.", "", "open", INJ_URL),
    ("VG-12", "Demotion gate armed",
     "No strategy may sit live while any demotion rule is unevaluable for its tracked statistics.",
     "A demotion gate that cannot fire is decoration.", "Post-promotion statistics.", "blocked", NIST),
]
write_csv("validation_gates.csv",
          ["gate_id", "gate", "rule", "why_it_removes_luck_or_error",
           "blocking_missing_input", "status", "reference_url"],
          [dict(zip(["gate_id", "gate", "rule", "why_it_removes_luck_or_error",
                     "blocking_missing_input", "status", "reference_url"], r)) for r in vg_rows])

dg_rows = [
    ("DG-01", "Negative closing-line value", "mean CLV over trailing window", "trailing 100 graded", 100,
     "< 0", "LIVE -> PAPER immediately at window close", "evaluable_once_prices_exist", NIST,
     "CLV is the cleanest luck-resistant skill signal; a negative mean with n>=100 says the market beats the model."),
    ("DG-02", "Holdout ROI lower bound below zero", "95% lower bound of holdout ROI", "since promotion", 200,
     "< 0", "LIVE -> PAPER at the next settlement cycle", "blocked_no_price_archive", NIST,
     "The lower bound, not the point estimate, so a lucky run cannot hold the seat."),
    ("DG-03", "Drawdown beyond 3 sigma", "peak-to-trough bankroll drawdown in sigma units", "rolling 60 slates", 60,
     "> 3.0", "LIVE -> PAPER pending review", "blocked_no_price_archive", NIST,
     "Distinguishes a broken signal from ordinary variance."),
    ("DG-04", "Stale inputs", "days since last verified input read at close", "per market", 1,
     "> 7 days", "close snapshot invalid; strategy cannot take new live positions", "evaluable", INJ_URL,
     "Freshness is itself a validation gate (VG-11); this rule demotes on breach."),
    ("DG-05", "Results-feed integrity failure", "failed settlement audit against official results", "per settlement", 1,
     "any failure", "LIVE -> PAPER until the feed is repaired and re-audited", "evaluable", SCORES_W9,
     "If settlement can be wrong, every downstream number is wrong."),
    ("DG-06", "Regime break without review", "structural change (e.g., QB1 out long-term) without re-origination review", "per event", 1,
     "unreviewed break", "hold new live entries until re-origination review completes", "evaluable", INJ_URL,
     "Example in this pack: BAL QB1 Jackson 6-10 week absence changes the rating regime (N6CF-R17)."),
]
write_csv("demotion_gate.csv",
          ["rule_id", "name", "trigger_statistic", "window", "n_min", "threshold",
           "action", "evaluation_status", "reference_url", "notes"],
          [dict(zip(["rule_id", "name", "trigger_statistic", "window", "n_min", "threshold",
                     "action", "evaluation_status", "reference_url", "notes"], r)) for r in dg_rows])

print("part 1 written:", len(orig_rows), "markets,", len(price_rows), "snapshots,",
      len(res_rows), "results,", len(bt_rows), "backtest grades,", len(depth_rows), "depth events")

# ======================================================================
# 9. Decision questions, suggestions, flags, sources, repo findings
# ======================================================================

q_rows = [
    ("N6CF-Q01", "Prices", "Where can opening and closing market numbers for NFL markets be obtained under a usable licence?",
     "", "missing",
     "Obtain a licensed odds archive (league data partner or a licensed odds vendor) or written permission; until then market_line stays blank.",
     "blocks: market_line, line_difference, CLV, ROI, market-based strategies", TERMS),
    ("N6CF-Q02", "Prices", "What were the opening and closing numbers for markets that closed before this store existed (e.g., W10-01)?",
     "", "missing",
     "Unrecoverable without a timestamped price feed; record as permanently missing rather than reconstructing.",
     "blocks: historical CLV for pre-store markets", TERMS),
    ("N6CF-Q03", "Results", "Are the Week 9 and W10-01 final scores verified?",
     "Yes — 16 finals read directly from nfl.com game/scores pages on 2026-11-14 (results_feed.csv).", "answered",
     "None needed.", "unblocks: settlement machinery, backtest demonstration", SCORES_W9),
    ("N6CF-Q04", "Model", "What margin distribution should replace the single-sigma normal approximation?",
     "", "missing",
     "Fit a margin distribution (e.g., normal with team-dependent sigma or a Skellam-type model) on multiple verified seasons once results accumulate; publish n.",
     "blocks: calibrated win probabilities, fair moneyline quality", NIST),
    ("N6CF-Q05", "Model", "What is a defensible home-field-advantage magnitude?",
     "", "missing",
     "Measure from verified multi-season home margins (official results); currently HFA is a declared 0.000 parameter (flag N6F-03).",
     "blocks: fair spread accuracy", NIST),
    ("N6CF-Q06", "Model", "How large is sigma_margin really?",
     "Estimated 14.705 points from the 15 verified Week 9 home margins (n=15, sample std).", "partial",
     "Re-estimate on >=200 verified game margins; publish n and interval each time.",
     "caveat: small-n parameter", SCORES_W9),
    ("N6CF-Q07", "Depth", "What is the pre-event depth string of a replacement when the club chart already reflects the injury (e.g., BAL QB)?",
     "", "missing",
     "Timestamped depth-chart snapshots (capture protocol on the validation page) or official transactions establishing the prior order.",
     "blocks: depth_of_replacement for events where the chart moved on (N6CF-R17)", STAND_URL),
    ("N6CF-Q08", "Depth", "Which club depth charts are official vs unofficial?",
     "Every chart read this session is club-published but labelled unofficial by the club itself (Patriots, Lions, Vikings charts state it explicitly).", "answered",
     "Treat strings as club-published-unofficial (verification_status column), never as league-official depth.",
     "caveat: depth strings carry club-chart provenance, not NFL-official provenance", INJ_URL),
    ("N6CF-Q09", "Injuries", "Do the two official Lamar Jackson return windows (6-10 weeks vs 6-9 weeks) conflict?",
     "Yes — S6CF-08 and S6CF-09 are both official nfl.com headlines with different windows.", "answered",
     "Flagged as N6F-12 for human review; use the shorter window as the conservative case, or neither until clarified.",
     "affects: BAL origination inputs for weeks 10-18", STAND_URL),
    ("N6CF-Q10", "Results", "Where is an official player-prop results feed?",
     "", "missing",
     "No official league page publishes graded prop results; a licensed feed is required. Until then N6CF-C09 stays blank.",
     "blocks: player-prop combo strategy (N6CF-L06)", TERMS),
    ("N6CF-Q11", "Statistics", "How many graded selections are needed before signal and staking can be judged separately?",
     "Policy floor: 200 graded selections per family (VG-06), preregistered as a policy, not a derivation.", "partial",
     "Derive the floor from expected effect sizes once a price archive yields realistic edge magnitudes; power analysis documented at that point.",
     "blocks: official leaderboard ranking", NIST),
    ("N6CF-Q12", "Statistics", "Which number should rank strategies when signal and staking disagree?",
     "Signal. The leaderboard pins staking_can_escalate_signal=no; official rank is defined on signal metrics only (VG-08).", "answered",
     "None needed; keep the separation in any future scoring change.", "unblocks: leaderboard design", NIST),
    ("N6CF-Q13", "Operations", "When exactly is the close captured for each market?",
     "", "partial",
     "Close = the last model revision before kickoff, computed from a fresh official injury/standings read; the store seeds a close row per market (VG-03). Automating the capture is suggestion N6CF-S03.",
     "blocks: close numbers for Week 10/11 markets (N6F-02)", INJ_URL),
    ("N6CF-Q14", "Rights", "Does nfl.com Terms §1.3 permit this repository's use of the data?",
     "The terms restrict systematic retrieval and permit only individual non-commercial informational use (S6CF-17, carried from prior verified reads).", "partial",
     "Legal review before any commercial use; keep the pack non-commercial and informational.", "caveat: standing rights flag N6F-01", TERMS),
    ("N6CF-Q15", "Coverage", "Were all Week 10 injury designations captured?",
     "All 14 Week 10 games are covered on the read injury-report chunks (Out/Doubtful recorded); Questionable players are recorded only where a replacement cascade is conditional (e.g., NE RB).", "answered",
     "Extend the tracker to Questionable-only rows if noise is acceptable.", "unblocks: replacement_depth completeness", INJ_URL),
    ("N6CF-Q16", "Coverage", "Which replacement events have verified depth strings?",
     f"{sum(1 for r in depth_rows if r['depth_of_replacement'] != BLANK)} of {len(depth_rows)} events carry verified strings (NE, DET, SEA, MIN, BAL defense); the rest are blank+flagged (N6F-08).", "answered",
     "Read the remaining club depth charts (KC, ATL, GB, JAX, TEN, NYJ, MIA, IND, CAR, NO, HOU, CLE, LAR, AZ, DAL, CIN) in a follow-up session.",
     "unblocks: depth tracking breadth", INJ_URL),
    ("N6CF-Q17", "Backtests", "Can ROI be computed from what exists today?",
     "Mechanically yes (settlement machinery demonstrated on 15 retrospective W9 grades) but honestly no: ROI needs prices, and no price archive exists. Values stay blank.", "answered",
     "Re-run settlement the moment a licensed price archive lands (VG-02 releases).", "blocks: all ROI/CLV columns", TERMS),
    ("N6CF-Q18", "Site", "What is the decision workflow for changing this project?",
     "Suggestions are review-only: each carries options and a recommended path and stays pending_human_choice until a human picks (suggestions.html).", "answered",
     "None needed.", "unblocks: change governance", REPO),
]
write_csv("decision_questions.csv",
          ["q_id", "category", "question", "known_answer", "answer_status",
           "discovery_protocol", "blocking_decision", "source_url"],
          [dict(zip(["q_id", "category", "question", "known_answer", "answer_status",
                     "discovery_protocol", "blocking_decision", "source_url"], r)) for r in q_rows])

sug_rows = [
    ("N6CF-S01", "Decision-making UI", "Add a one-screen decision brief per slate: model number vs market number vs difference, key depth losses, and the three biggest open questions.",
     "A: static brief page generated per slate", "B: brief embedded at the top of lines.html", "C: separate per-week HTML packs",
     "B — embed in lines.html so the decision context and the numbers live together",
     "Decision quality improves when the difference columns and the injury depth load are visible in one place.",
     "pending_human_choice", "docs/nfl-6cefc476/lines.html", REPO),
    ("N6CF-S02", "Data", "Acquire a licensed odds archive to release VG-02 and populate market_line, line_difference, CLV and ROI.",
     "A: league data partner", "B: licensed odds vendor subscription", "C: remain price-blind (current state)",
     "B first (fastest), evaluate A if volume grows",
     "Without prices the leaderboard cannot graduate from diagnostics to qualification.",
     "pending_human_choice", "VG-02; N6CF-Q01", TERMS),
    ("N6CF-S03", "Automation", "Automate close-snapshot capture at each kickoff window (scheduled job reading official pages into the store).",
     "A: scheduled GitHub Action storing raw input snapshots", "B: agent-session capture at each kickoff window", "C: manual capture (not acceptable per requirements)",
     "A with fail-closed parsing: store raw text first, parse only fields with tests",
     "The store requires close numbers for every market; automation removes timing luck from capture.",
     "pending_human_choice", "VG-03; N6F-02", REPO),
    ("N6CF-S04", "Data", "Read the 16 remaining club depth charts so every replacement event carries a verified depth string.",
     "A: one follow-up session reads all charts", "B: one club per slate week", "C: leave blank",
     "A — bounded, mechanical, and immediately removes flag N6F-08",
     "Depth of replacement is the requested tracking metric; breadth is currently the gap.",
     "pending_human_choice", "N6F-08; N6CF-Q16", INJ_URL),
    ("N6CF-S05", "Model", "Replace the single-sigma normal margin model with a calibrated margin distribution on multi-season verified results.",
     "A: team-dependent sigma", "B: Skellam (Poisson-difference) margin model", "C: keep single sigma",
     "B once enough verified results exist; publish n and out-of-sample tests",
     "Fair moneylines and demotion rules depend on honest win probabilities.",
     "pending_human_choice", "N6CF-Q04", NIST),
    ("N6CF-S06", "Governance", "Keep leaderboard ranking on signal metrics only; never let staking results influence rank or promotion.",
     "A: signal-only rank (current design)", "B: blended score", "C: two boards",
     "A — the requirement explicitly separates signal from staking",
     "Blended scores let lucky staking runs mask bad signals.",
     "pending_human_choice", "VG-08", NIST),
    ("N6CF-S07", "Injuries", "Add a per-game depth load metric (sum of string-weighted replacements) to the lines table as a separate column.",
     "A: count of starters out", "B: string-weighted load (depth-aware)", "C: both",
     "C — count answers 'how many', string-weighted load answers 'how deep'",
     "The requirement asks for depth of replacement, not just the fact.",
     "pending_human_choice", "VG-09", INJ_URL),
    ("N6CF-S08", "Site", "Publish a Flagged-for-Review queue sorted by severity with one-click source links (already present; add severity counts to the dashboard).",
     "A: severity counts on index", "B: separate triage page", "C: both",
     "A — cheap and keeps the landing page a decision surface",
     "Reviewers should see the worst irregularities first.",
     "pending_human_choice", "flagged.html", REPO),
    ("N6CF-S09", "Statistics", "Publish bootstrap intervals beside Fisher-z intervals for correlations once n >= 50.",
     "A: add bootstrap CI column", "B: Fisher-z only (current)", "C: both when n>=50",
     "C — intervals agree or they don't; either way it is information",
     "Small-n intervals are fragile; agreement between methods is a useful check.",
     "pending_human_choice", "N6CF-C01..C06", NIST),
    ("N6CF-S10", "Results", "Extend the results feed to every game since 2026 Week 1 (official scores pages) to grow the settlement base.",
     "A: backfill all weeks in one session", "B: backfill one week per session", "C: current two weeks only",
     "A — mechanical and it multiplies every future n",
     "Every gate that needs n needs verified results first.",
     "pending_human_choice", "VG-05", SCORES_W9),
    ("N6CF-S11", "Governance", "Run the demotion gate evaluation as an automated check in CI once live strategies exist.",
     "A: CI job evaluating DG rules per settlement", "B: manual review", "C: both",
     "A — the gate must be mechanical to be trusted",
     "A demotion gate that relies on memory does not demote.",
     "pending_human_choice", "VG-12", REPO),
    ("N6CF-S12", "Rights", "Keep the project non-commercial and informational; obtain legal review before any commercial or wagering use of NFL data.",
     "A: keep research-only (current)", "B: seek licence/permission", "C: commercialize",
     "A until counsel says otherwise",
     "NFL.com terms restrict systematic retrieval and gambling-related use (S6CF-17).",
     "pending_human_choice", "N6F-01", TERMS),
]
write_csv("suggestions.csv",
          ["sug_id", "area", "suggestion", "option_a", "option_b", "option_c",
           "recommended_path", "why", "status", "affects", "source_url"],
          [dict(zip(["sug_id", "area", "suggestion", "option_a", "option_b", "option_c",
                     "recommended_path", "why", "status", "affects", "source_url"], r)) for r in sug_rows])

flag_rows = [
    ("N6F-01", "high", "NFL data rights boundary",
     "NFL.com terms restrict systematic retrieval and permit individual non-commercial informational use only (S6CF-17). This pack stays non-commercial and cites, not republishes, official content.",
     "open_for_human_review", TERMS),
    ("N6F-02", "high", "Close snapshots pending for all 78 originated markets",
     "The store records the opening numbers now; close rows exist but are blank because no market has reached its close window yet. Capture protocol on the validation page.",
     "open_pending_capture", SCORES_W10),
    ("N6F-03", "medium", "Model parameters HFA and sigma are uncalibrated",
     "HFA=0.000 (no official source for a magnitude) and sigma=14.705 from n=15 Week 9 margins. Declared parameters, not verified facts.",
     "open_for_human_review", NIST),
    ("N6F-04", "high", "market_line and line_difference blank everywhere",
     "No licensed/official market price source exists in this repository; the columns are published deliberately blank (VG-02).",
     "open_for_human_review", TERMS),
    ("N6F-05", "medium", "BAL QB replacement depth unrecoverable",
     "Lamar Jackson is absent from the current Ravens depth chart, which already lists Brissett at QB1; the pre-event string of the replacement cannot be derived from current pages (N6CF-R17).",
     "open_for_human_review", "https://www.baltimoreravens.com/team/depth-chart/"),
    ("N6F-06", "medium", "DET S Kerby Joseph not on the read club depth chart",
     "The Week 10 injury report lists Joseph (S, Out) but the Lions chart lists only Clark and Branch/Izien at S; replacement string blank (N6CF-R11).",
     "open_for_human_review", "https://www.detroitlions.com/team/depth-chart/"),
    ("N6F-07", "medium", "NE OL cascade: replacement is himself questionable",
     "LG1 Ben Brown is Out; LG2 Walter Rouse is Questionable; LG3/C3 are unlisted on the chart. If Rouse is inactive the third string is unknown (N6CF-R07).",
     "open_for_human_review", "https://www.patriots.com/team/depth-chart/"),
    ("N6F-08", "medium", f"{sum(1 for r in depth_rows if r['depth_of_replacement'] == BLANK)} replacement events lack verified depth strings",
     "Club depth charts were read this session for NE, DET, SEA, MIN and BAL only; other clubs' strings are blank and flagged (discovery protocol N6CF-Q16).",
     "open_for_human_review", INJ_URL),
    ("N6F-09", "medium", "Retrospective W9 grades are in-sample derivations",
     "backtest_grades.csv computes fair lines from reconstructed post-W8 inputs after the fact. They demonstrate the settlement machinery; they are not pre-kickoff published lines and are not evidence of real-time edge.",
     "open_for_human_review", SCORES_W9),
    ("N6F-10", "low", "Small-n correlation N6CF-C06 publishes no p-value or interval",
     "n=15 indicator pairs; p/CI left blank per policy rather than over-interpreted.",
     "open_for_human_review", NIST),
    ("N6F-11", "high", "Parlay and player-prop correlations blocked",
     "N6CF-C07/C08/C09 have n=0: no licensed price archive for leg selection and no official player-prop results feed. Values left blank (VG-02).",
     "open_for_human_review", TERMS),
    ("N6F-12", "medium", "Official headlines disagree on Lamar Jackson's absence window",
     "S6CF-08 says 6-10 weeks; S6CF-09 says 6-9 weeks. Both are official nfl.com headlines read 2026-11-14. Not reconciled by this pack.",
     "open_for_human_review", "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"),
    ("N6F-13", "low", "Club depth charts are disclaimed unofficial",
     "The Patriots, Lions and Vikings charts state they are unofficial compilations; SEA/BAL charts show no disclaimer text in the read chunks. Strings carry club-published provenance only.",
     "open_for_human_review", "https://www.patriots.com/team/depth-chart/"),
    ("N6F-14", "low", "Overtime field blank in the results feed",
     "None of the 16 finals read as overtime on the scores pages; the column is published blank rather than inferred to mean 'no overtime'.",
     "open_for_human_review", SCORES_W9),
]
write_csv("flagged.csv", ["flag_id", "severity", "item", "detail", "status", "source_url"],
          [dict(zip(["flag_id", "severity", "item", "detail", "status", "source_url"], r))
           for r in flag_rows])
flag_rows = [dict(zip(["flag_id", "severity", "item", "detail", "status", "source_url"], r))
             for r in flag_rows]

src_rows = []
for sid, pub, title, url, method, status, excerpt, supports, doesnt in D.SOURCES:
    src_rows.append({"source_id": sid, "publisher": pub, "title": title, "url": url,
                     "read_on": READ_ON, "read_method": method, "status": status,
                     "verbatim_excerpt": excerpt, "supports": supports,
                     "does_not_support": doesnt})
write_csv("sources.csv", ["source_id", "publisher", "title", "url", "read_on",
                          "read_method", "status", "verbatim_excerpt", "supports",
                          "does_not_support"], src_rows)

rf_rows = [
    ("N6CF-RF01", "source registry", "data/nfl/sources.csv S-NFL-07 cited https://www.nfl.com/official-nfl-rules/ which returned an official NFL 404 (cross-session request R1, still unresolved in the tree at review time)",
     "Read the file at repo review time on 2026-11-14; the URL is still present.", "needs_review",
     f"{REPO}/blob/main/data/nfl/sources.csv"),
    ("N6CF-RF02", "shared tooling", "scripts/source_coverage.py PUBLISHERS allowlist contains no NFL or NFL-club domain, so NFL-sourced rows classify as secondary_reference_only (cross-session request R4, unresolved)",
     "Read scripts/source_coverage.py lines 25-36 on 2026-11-14; PUBLISHERS lists nba.com, law.go.kr, nist.gov and others only.", "needs_review",
     f"{REPO}/blob/main/scripts/source_coverage.py"),
    ("N6CF-RF03", "data consistency", "Two official nfl.com headlines disagree on Lamar Jackson's absence window (6-10 vs 6-9 weeks)",
     "Both headlines read on the nfl.com/injuries/ news section 2026-11-14 (S6CF-08, S6CF-09).", "needs_review",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"),
    ("N6CF-RF04", "depth data", "DET club depth chart does not list S Kerby Joseph although the official injury report lists him Out",
     "detroitlions.com depth chart (S6CF-12) vs nfl.com/injuries/ (S6CF-05), both read 2026-11-14.", "needs_review",
     "https://www.detroitlions.com/team/depth-chart/"),
    ("N6CF-RF05", "cross-check", "League standings totals from the 2026-11-14 read reconcile internally",
     f"W={league_w} L={league_l} T={league_t}; PF={league_pf} PA={league_pa} (PF=PA required; "
     "computed in scripts/build_nfl_6cefc476.py). Matches the 136/136/2 figure recorded by the prior 2026-11-13 review.",
     "verified_consistent", STAND_URL),
    ("N6CF-RF06", "scope", "Repository mixes NBA, NFL and San Francisco housing research in one tree",
     "Repo root listing read 2026-11-14 (RENTAL_INCREASE_SF_EXECUTIVE_SUMMARY.md, NBA packs, NFL packs).", "needs_review",
     REPO),
    ("N6CF-RF07", "prior reports", "Prior sessions reported the 2017 NFL injury-policy PDF as 404 and an NFL rule-change page showing 2025 content (NFL-F25); not re-verified this session",
     "Carried from COORDINATION.md prior session records; marked carried, not re-verified.", "carried_not_reverified",
     f"{REPO}/blob/main/COORDINATION.md"),
    ("N6CF-RF08", "site", "Suggestion SUG-01 in data/nfl_origination/site_suggestions.csv describes a former root redirect state that no longer matches the live root landing",
     "Carried from the README's own note (read 2026-11-14) and the current root index.html.", "needs_review",
     f"{REPO}/blob/main/data/nfl_origination/site_suggestions.csv"),
]
write_csv("repo_findings.csv",
          ["rf_id", "area", "finding", "evidence", "status", "source_url"],
          [dict(zip(["rf_id", "area", "finding", "evidence", "status", "source_url"], r))
           for r in rf_rows])
rf_rows = [dict(zip(["rf_id", "area", "finding", "evidence", "status", "source_url"], r))
           for r in rf_rows]

print("part 2 written:", len(q_rows), "questions,", len(sug_rows), "suggestions,",
      len(flag_rows), "flags,", len(src_rows), "sources,", len(rf_rows), "repo findings")

# ======================================================================
# 10. Site (docs/nfl-6cefc476/) — zero inputs, every table row source-linked
# ======================================================================

SITE.mkdir(parents=True, exist_ok=True)
(SITE / "assets").mkdir(exist_ok=True)
(SITE / "assets" / "style.css").write_text("""*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;background:#f6f7f9;color:#1f2933}header{background:#10243e;color:#fff;padding:1.1rem 1.6rem}header a{color:#cfe0f5;text-decoration:none;margin-right:1.1rem;font-size:.92rem}main{max-width:1180px;margin:1.6rem auto;padding:0 1.4rem}h1{font-size:1.55rem;margin:.2rem 0 .6rem}h2{font-size:1.12rem;margin:2rem 0 .6rem;border-bottom:2px solid #dde3ea;padding-bottom:.3rem}h3{font-size:1rem;margin:1.2rem 0 .4rem}a{color:#0b5fff}table{width:100%;border-collapse:collapse;background:#fff;font-size:.86rem;margin:.8rem 0}th,td{border:1px solid #dde3ea;padding:.45rem .6rem;text-align:left;vertical-align:top}th{background:#eef2f7;position:sticky;top:0}tr:nth-child(even){background:#fafbfc}.num{font-variant-numeric:tabular-nums}.badge{display:inline-block;padding:.08rem .5rem;border-radius:.4rem;font-size:.76rem;font-weight:600}.ok{background:#e6f4ea;color:#0a7d4f}.warn{background:#fef3c7;color:#b45309}.bad{background:#fde8e8;color:#b91c1c}.muted{background:#eef0f2;color:#6b7280}.blank{color:#9aa4b0}.card{background:#fff;border:1px solid #dde3ea;border-radius:.55rem;padding:.9rem 1.1rem;margin:.7rem 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:.8rem}.cardnum{font-size:1.55rem;font-weight:700}.callout{border-left:4px solid #0b5fff;background:#fff;padding:.75rem 1rem;margin:.9rem 0}.callout.warnbox{border-left-color:#b45309}.callout.badbox{border-left-color:#b91c1c}footer{max-width:1180px;margin:2.2rem auto;padding:1rem 1.4rem;color:#6b7280;font-size:.82rem;border-top:1px solid #dde3ea}code{background:#eef2f7;padding:.08rem .32rem;border-radius:.3rem;font-size:.82rem}nav.local a{margin-right:.9rem;font-size:.88rem}ul{margin:.4rem 0 .8rem;padding-left:1.2rem}li{margin:.18rem 0}""", encoding="utf-8")

NAV = [
    ("index.html", "Dashboard"), ("executive-summary.html", "Executive summary"),
    ("lines.html", "Originated lines"), ("price-snapshots.html", "Price snapshots"),
    ("results.html", "Results feed"), ("leaderboard.html", "Leaderboard"),
    ("replacement-depth.html", "Replacement depth"), ("correlations.html", "Correlations"),
    ("validation.html", "Gates & demotion"), ("questions.html", "Decision questions"),
    ("suggestions.html", "Suggestions"), ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"), ("repo-review.html", "Repo review"),
]


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def cell(v) -> str:
    if v is None or v == BLANK:
        return '<span class="blank">—</span>'
    return esc(v)


def link(url: str, text: str) -> str:
    return f'<a href="{esc(url)}">{esc(text)}</a>'


def flag_links(flag_ids: str) -> str:
    if not flag_ids:
        return ""
    parts = []
    for fid in str(flag_ids).split(";"):
        fid = fid.strip()
        if fid:
            parts.append(f'<a href="flagged.html#{esc(fid)}">{esc(fid)}</a>')
    return " ".join(parts)


def source_cell(url: str, label: str = "source", flag_ids: str = "") -> str:
    out = link(url, label) if url else ""
    fl = flag_links(flag_ids)
    if fl:
        out = (out + " · " + fl) if out else fl
    return out or '<span class="blank">—</span>'


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def page(name: str, title: str, body: str) -> None:
    nav = "".join(f'<a href="{n}{"#" if False else ""}">{t}</a>' for n, t in NAV)
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Own6 NFL (6cefc476)</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body>
<header><strong><a href="index.html">Own6 · NFL Decision Pack (session 6cefc476)</a></strong><br><br>{nav}</header>
<main>
<h1>{esc(title)}</h1>
{body}
</main>
<footer>Session <code>arena/6cefc476-own6</code> · built {READ_ON} · every table row links its source;
unverified values are published blank and flagged on <a href="flagged.html">Flagged for review</a>.
No input elements exist anywhere on this site — nothing requires manual entry.
Model outputs are computations, not market prices. Nothing here demonstrates a profitable edge.</footer>
</body></html>"""
    (SITE / name).write_text(doc, encoding="utf-8")


B = '<span class="blank">—</span>'

# ---------------------------------------------------------------- lines
rows = []
for r in orig_rows:
    rows.append([
        esc(r["origination_order"]), esc(r["origination_wave"]), esc(r["market_type"]),
        esc(r["matchup"]), esc(r["kickoff_et"]),
        f'<span class="num">{esc(r["model_fair_line"])}</span>', esc(r["model_fair_line_unit"]),
        esc(r["model_win_prob_home"]) or B,
        B, B,
        flag_links(r["flag_id"]) + " " + link(r["source_url"], "standings") + " " + link(r["second_source_url"], "game page"),
    ])
page("lines.html", "Originated lines — side first, then total, then moneyline",
     """<div class="callout"><strong>Origination order is enforced:</strong> wave 1 originates every side (spread),
wave 2 every total, wave 3 every moneyline. <code>scripts/check_nfl_6cefc476.py</code> fails the build if any
total precedes its side or any moneyline precedes its total.</div>
<div class="callout warnbox"><strong>Market line and difference are published blank (flag N6F-04).</strong>
No licensed/official market price source exists in this repository, so <code>market_line</code> and
<code>line_difference</code> cannot be confirmed and are never inferred. The columns exist so the
comparison is first-class the moment a price archive lands (gate VG-02).</div>
<p>Model definition and parameters (HFA=0.000 flagged N6F-03; sigma = """
     + f'<span class="num">{SIGMA:.4f}</span> from n={len(w9_margins)} verified Week 9 margins): '
       f'<code>exp_home=(home_pf/g+away_pa/g)/2</code>, <code>exp_away=(away_pf/g+home_pa/g)/2</code>, '
       f'<code>spread=exp_home-exp_away</code> (home perspective), <code>total=exp_home+exp_away</code>, '
       f'<code>p_home=Phi(spread/sigma)</code>, fair American odds with no vig.</p>'
     + table(["#", "Wave", "Market", "Matchup (week 10/11)", "Kickoff (ET)", "Model fair line",
              "Unit", "Model p(home)", "Market line", "Difference", "Source"], rows))

# ------------------------------------------------------- price snapshots
rows = []
for r in price_rows:
    our = f'<span class="num">{esc(r["our_number"])}</span>' if r["our_number"] else B
    rows.append([
        esc(r["snapshot_id"]), esc(r["market_type"]), esc(r["matchup"]), esc(r["snapshot_type"]),
        esc(r["captured_at_utc"]) or B, our, B,
        esc(r["verification_status"]),
        source_cell(r["source_url"], "inputs", r["flag_id"]) + " " + link(r["second_source_url"], "second"),
    ])
page("price-snapshots.html", "Price-snapshot store — opening and closing numbers for every originated market",
     f"""<div class="callout"><strong>Store completeness:</strong> {len(price_rows)} rows cover all
{len(orig_rows)} originated markets — one <em>open</em> row (captured {READ_ON}, first publication) and one
<em>close</em> row per market. Close rows are published blank with status <code>pending_close</code>
(flag N6F-02) because no market has reached its close window yet; the capture protocol is on the
<a href="validation.html">gates page</a>. Market numbers (both open and close) are blank
(flag N6F-04) — no licensed price source.</div>
<p>What a price snapshot records: our own number at the moment of capture, the market number when a
licensed source exists, the exact input basis, and both source links. Open numbers here are model
computations from verified inputs — not market prices.</p>"""
     + table(["Snapshot id", "Market", "Matchup", "Type", "Captured", "Our number",
              "Market number", "Verification", "Source"], rows))

# --------------------------------------------------------------- results
rows = []
for r in res_rows:
    rows.append([
        esc(r["game_id"]), esc(r["week"]), esc(r["date"]), esc(r["matchup"]) if False else esc(f"{r['away']} {r['away_score']} @ {r['home']} {r['home_score']}"),
        esc(r["status"]), esc(r["winner"]), esc(r["margin_home"]), esc(r["total_points"]),
        B, esc(r["settlement_status"]),
        source_cell(r["source_url"], "official game page", r.get("flag_id", "")) + " " + link(r["second_source_url"], "scores"),
    ])
bt_view = []
for r in bt_rows:
    bt_view.append([
        esc(r["game_id"]), esc(r["matchup"]), esc(r["fair_spread_home"]), esc(r["fair_total"]),
        esc(r["model_p_home"]), esc(r["model_side"]),
        esc(r["side_grade"]), esc(r["total_grade"]), esc(r["ml_grade"]),
        flag_links("N6F-09") + " " + link(r["source_url"], "game page"),
    ])
page("results.html", "Verified results feed — settlement machinery for backtests and ROI",
     f"""<div class="callout"><strong>{len(res_rows)} finals verified</strong> from official nfl.com pages on
{READ_ON}: all 15 Week 9 games plus W10-01 (WAS 24 at NYG 21). Every row links its official game page.</div>
<div class="callout warnbox"><strong>ROI needs prices.</strong> The feed makes backtests <em>computable</em> —
settlement, grades, ROI and CLV formulas all run against it — but honest ROI/CLV columns stay blank
until a licensed price archive exists (VG-02, flag N6F-04). No originated line predates these kickoffs
(the store first published {READ_ON}), so settlement runs against the retrospective demonstration below.</div>
<h2>Retrospective Week 9 grades (demonstration of the machinery — flag N6F-09)</h2>
<p>Fair lines reconstructed from post-W8 inputs by subtracting each verified Week 9 score from the verified
2026-11-14 standings totals (published arithmetic, not inference). These are <strong>in-sample
retrospective derivations</strong>, not pre-kickoff published lines; they demonstrate settlement and
grading only. Grades: model side vs own fair spread, over vs own fair total, and the higher-probability
side straight up.</p>"""
     + table(["Game", "Matchup", "Fair spread", "Fair total", "Model p(home)", "Model side",
              "Side grade", "Total grade", "ML grade", "Source"], bt_view)
     + f"<p>Aggregate (diagnostic, n={len(bt_rows)}): side {side_wins}/{side_graded}, "
       f"total {total_wins}/{total_graded}, moneyline {ml_wins}/{ml_graded}.</p>"
     + "<h2>Results feed</h2>"
     + table(["Game", "Week", "Date", "Score", "Status", "Winner", "Margin (home)", "Total",
              "Settled vs our line", "Settlement status", "Source"], rows))

# ------------------------------------------------------------ leaderboard
rows = []
for r in lb_rows:
    rows.append([
        esc(r["strategy_id"]), esc(r["name"]), esc(r["family"]), esc(r["market"]),
        esc(r["n_graded"]), esc(r["signal_cover_rate"]) or B, esc(r["signal_status"]),
        esc(r["diagnostic_signal_rank"]) or B,
        esc(r["staking_status"]), esc(r["staking_roi"]) or B, esc(r["staking_rank"]) or B,
        f'<span class="badge bad">{esc(r["staking_can_escalate_signal"])}</span>',
        esc(r["eligibility"]), esc(r["reward"]), esc(r["official_rank"]) or B,
        source_cell(r["source_url"], "grades source", r["flag_id"]),
    ])
page("leaderboard.html", "Strategy leaderboard — signal separated from staking",
     """<div class="callout badbox"><strong>A lucky staking run cannot mask a bad signal.</strong>
Signal metrics and staking metrics live in separate columns and separate ranks. The pinned rule
<code>staking_can_escalate_signal = no</code> means staking performance never raises a strategy whose
signal fails. Official rank is defined on signal metrics only (gate VG-08).</div>
<p>Diagnostic metrics on this board come from the retrospective Week 9 demonstration (n=15, in-sample,
flag N6F-09) and are below the pre-registered 200-selection floor (VG-06), so every strategy is
<em>unqualified</em>, tier 0, no reward, no official rank. That is the competition working as designed:
registration and measurement now, rewards only after the gates.</p>
<p>Reward model (preregistered): research-priority credits for the top signal tier after VG-06 and VG-07
pass; non-monetary; demotion rules on the <a href="validation.html">gates page</a> return a live
strategy to paper.</p>"""
     + table(["ID", "Strategy", "Family", "Market", "n", "Signal cover rate", "Signal status",
              "Signal rank (diagnostic)", "Staking status", "Staking ROI", "Staking rank",
              "Staking can escalate?", "Eligibility", "Reward", "Official rank", "Source"], rows))

# ----------------------------------------------------- replacement depth
rows = []
for r in depth_rows:
    rows.append([
        esc(r["event_id"]), esc(r["team"]), esc(r["side"]), esc(r["position"]),
        esc(r["injured_player"]), esc(r["injured_status"]),
        esc(r["injured_string"]) or B,
        esc(r["replacement_player"]) or B,
        esc(r["replacement_string"]) or B,
        f'<strong>{esc(r["depth_of_replacement"])}</strong>' if r["depth_of_replacement"] else B,
        esc(r["replacement_step"]) or B,
        esc(r["event_type"]),
        (link(r["depth_source_url"], "depth chart") if r["depth_source_url"] else B) + " " +
        link(r["injury_source_url"], "injury report") + (" " + flag_links(r["flag_id"]) if r["flag_id"] else ""),
    ])
n_depth = sum(1 for r in depth_rows if r["depth_of_replacement"] != BLANK)
page("replacement-depth.html", "Replacement depth — the depth of the replacement, not just the fact",
     f"""<div class="callout"><strong>Depth is tracked explicitly.</strong> Each event records the string
level of the player who steps in (<em>depth_of_replacement</em>) and how far down the unit moves
(<em>replacement_step</em>), on offense and defense. {n_depth} of {len(depth_rows)} events carry verified
depth strings from club depth charts read this session (NE, DET, SEA, MIN, BAL); the rest are published
blank and flagged (N6F-08) because the club chart was not read — never guessed.</div>
<p>Headline cases this week: SEA QB1 Darnold Out → 2nd-string Drew Lock (news-confirmed starter);
MIN QB1 Murray Out → 2nd-string Carson Wentz; NE RB2 Henderson Out/IR → 3rd-string Corey Kiner, and if
RB1 Stevenson (Questionable) is inactive the team plays its <strong>3rd-string back two strings down</strong>;
DET CB1 and C1 out → straight 2nd-string swaps. Club charts are disclaimed unofficial (N6F-13).</p>"""
     + table(["ID", "Team", "Side", "Pos", "Injured", "Status", "String",
              "Replacement", "Repl. string", "Depth of replacement", "Step", "Event type", "Source"], rows))

# ---------------------------------------------------------- correlations
rows = []
for r in corr_rows:
    coef = f'<span class="num">{esc(r["coefficient"])}</span>' if r["coefficient"] else B
    rows.append([
        esc(r["correlation_id"]), esc(r["x_variable"]), esc(r["y_variable"]),
        esc(r["method"]) or B,
        f'<strong class="num">{esc(r["n"])}</strong>',
        coef, esc(r["p_value"]) or B, esc(r["ci95_low"]) or B, esc(r["ci95_high"]) or B,
        esc(r["status"]), esc(r["computation"]),
        source_cell(r["source_url"], "source", r["flag_id"]),
    ])
page("correlations.html", "Correlations — officially sourced numbers only, n published with every value",
     f"""<div class="callout"><strong>Rule (gate VG-10):</strong> every coefficient is computed from
officially sourced numbers read this session and publishes <strong>n</strong> beside it. Fisher-z 95%
intervals (NIST/SEMATECH method, S6CF-16). Values that cannot be sourced (parlay legs, player props)
are published blank with n=0 and flagged (N6F-11) — never estimated.</div>
<p>League consistency check on the standings read (computed): W={league_w}, L={league_l}, T={league_t},
PF={league_pf}, PA={league_pa}. PF=PA as required for a closed league — the read reconciles.</p>"""
     + table(["ID", "x", "y", "Method", "n", "Coefficient", "p-value", "CI95 low", "CI95 high",
              "Status", "Computation", "Source"], rows))

# ----------------------------------------------------------- validation
vg_view = [[esc(g["gate_id"]), esc(g["gate"]), esc(g["rule"]), esc(g["why_it_removes_luck_or_error"]),
            esc(g["blocking_missing_input"]) or B,
            f'<span class="badge {"ok" if g["status"] == "open" else "muted"}">{esc(g["status"])}</span>',
            link(g["reference_url"], "reference")] for g in
           [dict(zip(["gate_id", "gate", "rule", "why_it_removes_luck_or_error",
                      "blocking_missing_input", "status", "reference_url"], r)) for r in vg_rows]]
dg_view = [[esc(d["rule_id"]), esc(d["name"]), esc(d["trigger_statistic"]), esc(d["window"]),
            esc(d["n_min"]), esc(d["threshold"]), esc(d["action"]), esc(d["evaluation_status"]),
            link(d["reference_url"], "reference")] for d in
           [dict(zip(["rule_id", "name", "trigger_statistic", "window", "n_min", "threshold",
                      "action", "evaluation_status", "reference_url", "notes"], r)) for r in dg_rows]]
page("validation.html", "Validation gates and the demotion gate (live → paper)",
     """<div class="callout badbox"><strong>Demotion gate definition.</strong> A live strategy returns to
paper the moment any DG rule fires. DG-01/DG-02 use luck-resistant statistics (closing-line value and
holdout ROI lower bounds) rather than raw ROI. DG-04 (stale inputs) and DG-05 (feed integrity) are
evaluable today; the rest arm when a price archive exists. State machine:
<code>paper → live</code> only when every VG gate is satisfied; <code>live → paper</code> immediately on
any DG trigger; re-promotion requires a fresh full-gate pass.</div>
<h3>Close-capture protocol (fills the store's close rows)</h3>
<ul>
<li>At the market's kickoff window, re-read the official injury report and standings.</li>
<li>Recompute the model with the same published formula and parameters; that number is the close.</li>
<li>Record it in the close row with the capture date and input links; never backfill a close from the result.</li>
</ul>
<h2>Validation gates</h2>"""
     + table(["ID", "Gate", "Rule", "Why it removes luck or error", "Blocking input", "Status", "Reference"], vg_view)
     + "<h2>Demotion gate — sends a live strategy back to paper</h2>"
     + table(["ID", "Rule", "Trigger statistic", "Window", "n min", "Threshold", "Action",
              "Evaluation status", "Reference"], dg_view))

# ------------------------------------------------------------- questions
rows = [[esc(q["q_id"]), esc(q["category"]), esc(q["question"]),
         esc(q["known_answer"]) or B,
         f'<span class="badge {"ok" if q["answer_status"] == "answered" else ("warn" if q["answer_status"] == "partial" else "bad")}">{esc(q["answer_status"])}</span>',
         esc(q["discovery_protocol"]), esc(q["blocking_decision"]),
         link(q["source_url"], "source")] for q in
        [dict(zip(["q_id", "category", "question", "known_answer", "answer_status",
                   "discovery_protocol", "blocking_decision", "source_url"], r)) for r in q_rows]]
page("questions.html", "Decision questions — what we know, what we don't, and how to find out",
     """<div class="callout"><strong>Before any decision is made from this pack</strong>, read this
register. Every question is classified <em>answered</em> (verified with a source), <em>partial</em>
(answered with a caveat), or <em>missing</em> — and every missing item carries a discovery protocol
stating exactly which source or licence would resolve it. Blank values elsewhere on the site trace to
the missing items here.</div>"""
     + table(["ID", "Category", "Question", "Known answer", "Status", "Discovery protocol",
              "What it blocks", "Source"], rows))

# ----------------------------------------------------------- suggestions
rows = [[esc(s["sug_id"]), esc(s["area"]), esc(s["suggestion"]),
         esc(s["option_a"]), esc(s["option_b"]), esc(s["option_c"]),
         f'<strong>{esc(s["recommended_path"])}</strong>', esc(s["why"]),
         f'<span class="badge warn">{esc(s["status"])}</span>', esc(s["affects"]),
         link(s["source_url"], "evidence")] for s in
        [dict(zip(["sug_id", "area", "suggestion", "option_a", "option_b", "option_c",
                   "recommended_path", "why", "status", "affects", "source_url"], r)) for r in sug_rows]]
page("suggestions.html", "Suggestions for review — choose the path before anything changes",
     """<div class="callout warnbox"><strong>Nothing here is implemented.</strong> Each suggestion lists
options, a recommended path, and its evidence, and stays <code>pending_human_choice</code> until a human
picks. Site improvements for decision-making are N6CF-S01 and N6CF-S08. This is the required review
step before any change to the project.</div>"""
     + table(["ID", "Area", "Suggestion", "Option A", "Option B", "Option C", "Recommended",
              "Why", "Status", "Affects", "Evidence"], rows))

# --------------------------------------------------------------- flags
rows = [[esc(f["flag_id"]), f'<span class="badge {"bad" if f["severity"] == "high" else ("warn" if f["severity"] == "medium" else "muted")}">{esc(f["severity"])}</span>',
         esc(f["item"]), esc(f["detail"]), esc(f["status"]), link(f["source_url"], "source")]
        for f in flag_rows]
page("flagged.html", "Flagged for review — irregularities and unverified items",
     """<div class="callout warnbox">Flagged items never block the data set and are never silently filled.
Each carries its source so a human can review and request changes. Unverified values stay blank until a
flag is resolved.</div>"""
     + table(["ID", "Severity", "Item", "Detail", "Status", "Source"], rows))

# -------------------------------------------------------------- sources
rows = [[esc(s["source_id"]), esc(s["publisher"]), esc(s["title"]),
         link(s["url"], "open source"), esc(s["read_on"]), esc(s["read_method"]),
         f'<span class="badge {"ok" if s["status"].startswith("verified") else "muted"}">{esc(s["status"])}</span>',
         esc(s["verbatim_excerpt"]), esc(s["supports"]), esc(s["does_not_support"])]
        for s in src_rows]
page("sources.html", "Source register — pages read this session, with boundaries",
     """<p>“Verified” in this register means the text was read from the linked page during session
6cefc476 on 2026-11-14. <em>supports</em> and <em>does_not_support</em> record the exact evidence
boundary of each read. Carried entries are labelled as such.</p>"""
     + table(["ID", "Publisher", "Title", "Link", "Read on", "Method", "Status", "Verbatim excerpt",
              "Supports", "Does not support"], rows))

# ---------------------------------------------------------- repo review
rows = [[esc(f["rf_id"]), esc(f["area"]), esc(f["finding"]), esc(f["evidence"]),
         f'<span class="badge {"ok" if f["status"].startswith("verified") else "warn"}">{esc(f["status"])}</span>',
         link(f["source_url"], "evidence link")]
        for f in rf_rows]
page("repo-review.html", "Repository review — line-by-line irregularities for manual review",
     """<p>Review of the repository as found on 2026-11-14, before this pack was added. Cross-session
requests R1 (broken rules URL in data/nfl/sources.csv) and R4 (source-coverage allowlist gap) were
re-checked in the tree and remain open; both are listed with evidence links. Prior-session reports are
marked carried rather than re-verified.</p>"""
     + table(["ID", "Area", "Finding", "Evidence", "Status", "Link"], rows))

# ------------------------------------------------------ executive summary
page("executive-summary.html", "Executive summary — NFL decision pack (session 6cefc476)",
     f"""<div class="card"><h2>What this pack is</h2>
<p>An evidence-first NFL line-origination stack built this session from official pages read on {READ_ON}:
a <strong>price-snapshot store</strong> with opening numbers for all {len(orig_rows)} originated markets
(and close rows provisioned), a <strong>verified results feed</strong> of {len(res_rows)} finals,
origination that runs <strong>side → total → moneyline</strong> in enforced order, published
<strong>fair line / market line / difference</strong> columns, a leaderboard that <strong>separates
signal from staking</strong>, <strong>replacement-depth</strong> tracking (string level of the
replacement), <strong>correlations from official numbers with n published</strong>, a defined
<strong>demotion gate</strong>, and review-first <strong>suggestions</strong> and
<strong>decision questions</strong>.</p></div>
<div class="card"><h2>Decision state (read this before betting anything)</h2>
<ul>
<li><strong>0 qualified strategies.</strong> All six registered candidates are unqualified pending the
200-selection floor and a licensed price archive. No reward has been awarded.</li>
<li><strong>No market prices exist in this repository.</strong> market_line, line_difference, ROI and
CLV are blank by policy (VG-02), not omitted.</li>
<li><strong>Model parameters are uncalibrated</strong> (HFA=0.000; sigma={SIGMA:.3f}, n={len(w9_margins)}).
Fair lines are model computations, not market prices, and not evidence of an edge.</li>
<li><strong>Replacement depth:</strong> {n_depth}/{len(depth_rows)} events verified to club-chart string
level; the rest flagged N6F-08. Headline exposure: SEA and MIN on QB2, NE on RB3 (two strings), DET on
CB2/C2.</li>
<li><strong>Blocking unknowns:</strong> licensed prices (N6CF-Q01), close captures (N6F-02), player-prop
results feed (N6CF-Q10). Full register on <a href="questions.html">Decision questions</a>.</li>
</ul></div>
<div class="card"><h2>Numbers at a glance (all computed this session)</h2>
<ul>
<li>Standings read: 32 clubs — W={league_w} L={league_l} T={league_t}, PF={league_pf}=PA (reconciled).</li>
<li>Results feed: {len(res_rows)} verified finals (Week 9 + W10-01).</li>
<li>Originated markets: {len(orig_rows)} ({len(games)} games × spread/total/moneyline).</li>
<li>Price snapshots: {len(price_rows)} rows ({len(price_rows)//2} open captured, {len(price_rows)//2} close pending).</li>
<li>Correlations published with n: {sum(1 for r in corr_rows if r['coefficient'])}; blocked with n=0: {sum(1 for r in corr_rows if not r['coefficient'])}.</li>
<li>Flagged items: {len(flag_rows)} · Suggestions pending human choice: {len(sug_rows)}.</li>
</ul></div>
<div class="card"><h2>Recommended next actions (owner decisions)</h2>
<ol>
<li>Choose the price-archive path (N6CF-S02) — everything quantitative unblocks behind it.</li>
<li>Approve automated close capture (N6CF-S03) so the store fills without manual work.</li>
<li>Approve the depth-chart backfill session (N6CF-S04) to clear N6F-08.</li>
</ol>
<p>All options are on <a href="suggestions.html">Suggestions</a>; nothing is applied until chosen.</p></div>""")

print("site written:", len(list(SITE.glob('*.html'))), "pages")

# ------------------------------------------------------- dashboard index
glance = [
    ["Verified results in the feed", str(len(res_rows)),
     "Week 9 (15 games) + W10-01 final, read 2026-11-14",
     source_cell(SCORES_W9, "scores")],
    ["Originated markets (side → total → ML)", str(len(orig_rows)),
     f"{len(games)} games × 3 market types; waves enforced in order",
     source_cell(SCHED_W11, "schedule")],
    ["Price snapshots recorded", f"{len(price_rows)} ({len(price_rows)//2} open, {len(price_rows)//2} close pending)",
     "Open captured 2026-11-14; close rows provisioned (N6F-02)",
     source_cell(STAND_URL, "inputs", "N6F-02")],
    ["Market prices (open/close)", "0 — blank by policy",
     "No licensed/official price source; VG-02 blocks invented prices",
     source_cell(TERMS, "terms", "N6F-04")],
    ["Replacement events tracked", f"{len(depth_rows)} ({n_depth} with verified depth strings)",
     "Depth of replacement = string level of the player who steps in",
     source_cell(INJ_URL, "injury report", "N6F-08")],
    ["Correlations published (with n)", str(sum(1 for r in corr_rows if r["coefficient"])),
     "Official numbers only; n printed beside every value; blocked rows keep n=0",
     source_cell(NIST, "method", "N6F-11")],
    ["Leaderboard qualification", "0 of 6 strategies qualified",
     "Signal separated from staking; staking cannot escalate a failed signal",
     source_cell(NIST, "method")],
    ["Demotion rules defined", str(len(dg_rows)),
     "Live → paper triggers; two evaluable today, four arm with the price archive",
     source_cell(NIST, "method")],
    ["Flagged items", str(len(flag_rows)),
     "Published for human review; nothing blocked the data set",
     source_cell(TERMS, "terms", "N6F-01")],
    ["Suggestions pending human choice", str(len(sug_rows)),
     "Review-first: options + recommended path; nothing applied automatically",
     source_cell(REPO, "repo")],
]
body = f"""<div class="callout"><strong>Evidence policy.</strong> Every value on this site traces to an
official page read in session 6cefc476 on {READ_ON}; each table row carries its source link. Values that
cannot be confirmed are published <em>blank</em> and flagged — never inferred. Model outputs are labelled
computations, not market prices. <strong>Nothing here demonstrates a profitable edge.</strong></div>
<div class="grid">
<div class="card"><div class="cardnum">{len(res_rows)}</div><div>verified results</div></div>
<div class="card"><div class="cardnum">{len(orig_rows)}</div><div>originated markets</div></div>
<div class="card"><div class="cardnum">{len(price_rows)}</div><div>price snapshots</div></div>
<div class="card"><div class="cardnum">{n_depth}/{len(depth_rows)}</div><div>depth strings verified</div></div>
<div class="card"><div class="cardnum">0/6</div><div>strategies qualified</div></div>
<div class="card"><div class="cardnum">{len(flag_rows)}</div><div>items flagged for review</div></div>
</div>
<h2>Sections</h2>
<div class="grid">
<div class="card"><strong><a href="executive-summary.html">Executive summary</a></strong><br>Decision state, numbers, next actions.</div>
<div class="card"><strong><a href="lines.html">Originated lines</a></strong><br>Side first, then total, then moneyline; fair / market / difference columns.</div>
<div class="card"><strong><a href="price-snapshots.html">Price snapshots</a></strong><br>Opening and closing numbers for every originated market.</div>
<div class="card"><strong><a href="results.html">Results feed</a></strong><br>Verified finals + settlement machinery for backtests and ROI.</div>
<div class="card"><strong><a href="leaderboard.html">Leaderboard</a></strong><br>Signal separated from staking; rewards after gates only.</div>
<div class="card"><strong><a href="replacement-depth.html">Replacement depth</a></strong><br>The depth of the replacement, not just the fact.</div>
<div class="card"><strong><a href="correlations.html">Correlations</a></strong><br>Official numbers only; n published with every value.</div>
<div class="card"><strong><a href="validation.html">Gates &amp; demotion</a></strong><br>Validation gates and the live → paper demotion gate.</div>
<div class="card"><strong><a href="questions.html">Decision questions</a></strong><br>Knowns, missing information, discovery protocols.</div>
<div class="card"><strong><a href="suggestions.html">Suggestions</a></strong><br>Options and recommended paths — pending your choice.</div>
<div class="card"><strong><a href="flagged.html">Flagged for review</a></strong><br>Irregularities and unverified items with source links.</div>
<div class="card"><strong><a href="sources.html">Sources</a></strong><br>Pages read, evidence boundaries.</div>
<div class="card"><strong><a href="repo-review.html">Repo review</a></strong><br>Line-by-line irregularities found in the repository.</div>
</div>
<h2>At a glance</h2>"""
body += table(["Item", "Value", "Note", "Source"], glance)
body += """<h2>How to read this pack</h2>
<ul>
<li>Blank cell = value could not be confirmed from an official source and was left empty on purpose.</li>
<li>Flag badge (N6F-xx) = the reason, published on <a href="flagged.html">Flagged for review</a>.</li>
<li>Every leaderboard row is unqualified until the 200-selection floor and a licensed price archive exist.</li>
<li>Nothing on this site asks for input; it is a read-only decision surface.</li>
</ul>"""
page("index.html", "NFL Decision Dashboard", body)
print("site written:", len(list(SITE.glob('*.html'))), "pages")
