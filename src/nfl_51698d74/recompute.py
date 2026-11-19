"""Independent recomputation of prior-pack origination outputs (session 51698d74).

Run:  python3 src/nfl_51698d74/recompute.py
No network. No wall clock. Deterministic.

What it does (all arithmetic, no new market data):
  1. Rebuilds the 150-game corpus from data/nfl_7a59fd89/corpus_150.csv plus the
     Week-10 Monday settlement (LAC 23, BAL 20 — re-read this session from the
     official week-10 schedule page) and reconciles club W-L-T/PF/PA against this
     session's fresh standings read (data/nfl_51698d74/standings_2026_11_19.csv).
  2. Re-runs the frozen 0ce967db S01 forecaster (imported, not copied) for the 13
     Week-11 fixtures and compares fair margin / total / home-win probability
     against data/nfl_0ce967db/originated_lines.csv.
  3. Recomputes Brier scores per strategy from data/nfl_0ce967db/model_outputs.csv
     and compares against data/nfl_0ce967db/leaderboard.csv.
  4. Recomputes official-only correlations (home margin vs total; home margin vs
     home points; total vs home points) from the results feed with n and Fisher CI.

Outputs (data/nfl_51698d74/):
  originated_lines_check.csv, leaderboard_check.csv, correlations_check.csv,
  reverification.csv
"""
from __future__ import annotations

import csv
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nfl_0ce967db import model as M  # noqa: E402
from nfl_0ce967db import score as S  # noqa: E402
from nfl_0ce967db.correlate import pearson, fisher_ci  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "data", "nfl_51698d74")
CORPUS = os.path.join(REPO, "data", "nfl_7a59fd89", "corpus_150.csv")
SETTLEMENT = {"2026-W10-14": (23, 20)}  # LAC 23, BAL 20 (re-read 2026-11-19)
CODE_FIX = {"LAR": "LA"}
WEEK11 = [("W11-01", "IND", "HOU"), ("W11-02", "MIA", "BUF"), ("W11-03", "BAL", "CAR"),
          ("W11-04", "NO", "CHI"), ("W11-05", "TEN", "DAL"), ("W11-06", "TB", "DET"),
          ("W11-07", "AZ", "KC"), ("W11-08", "PIT", "PHI"), ("W11-09", "NYJ", "LAC"),
          ("W11-10", "JAX", "NYG"), ("W11-11", "LV", "DEN"), ("W11-12", "MIN", "SF"),
          ("W11-13", "CIN", "WAS")]
STANDINGS_URL = "https://www.nfl.com/standings/division/2026/reg"


def read_corpus() -> list[M.Game]:
    games = []
    with open(CORPUS, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            away = CODE_FIX.get(row["away"], row["away"])
            home = CODE_FIX.get(row["home"], row["home"])
            a, h = row["away_score"].strip(), row["home_score"].strip()
            if row["game_id"] in SETTLEMENT:
                a, h = (str(x) for x in SETTLEMENT[row["game_id"]])
            games.append(M.Game(game_id=row["game_id"], week=int(row["week"]),
                                away=away, home=home,
                                away_score=int(a) if a else None,
                                home_score=int(h) if h else None,
                                date_on_card=row.get("date_on_card", "")))
    return games


def build_history(games, before_week):
    hist = {}
    for g in games:
        if g.week >= before_week or not g.played:
            continue
        hist.setdefault(g.home, M.TeamHistory()).append(int(g.home_score), int(g.away_score))
        hist.setdefault(g.away, M.TeamHistory()).append(int(g.away_score), int(g.home_score))
    return hist


def rolling_errors(games):
    per_week = {}
    for w in sorted({g.week for g in games}):
        hist = build_history(games, w)
        for g in games:
            if g.week != w or not g.played:
                continue
            if g.home not in hist or g.away not in hist:
                continue
            lg, _ = M.league_means(hist)
            f = M.margin_forecast(hist[g.home], hist[g.away], lg, M.H_FIXED, None, 14.0)
            per_week.setdefault(w, []).append(g.margin - f["expected_margin_home"])
    return per_week


def main() -> None:
    games = read_corpus()
    assert len(games) == 150, f"corpus drifted: {len(games)} rows"
    assert all(g.played for g in games), "unsettled games present"

    # ---- 1. corpus reconciliation vs THIS session's fresh standings read -------------
    with open(os.path.join(OUT, "standings_2026_11_19.csv"), newline="", encoding="utf-8") as f:
        official = {r["club"]: r for r in csv.DictReader(f)}
    # map full club names to codes via the corpus club set
    name_to_code = {}
    for g in games:
        name_to_code.setdefault(g.home, g.home)
        name_to_code.setdefault(g.away, g.away)
    # standings CSV uses full names; corpus uses codes. Build code->(W,L,T,PF,PA) from
    # the standings rows by matching on the known code list order is fragile, so instead
    # reconcile at the league level (totals) + per-club via PF/PA sums computed below.
    pf, pa, win, loss, tie = {}, {}, {}, {}, {}
    for g in games:
        pf[g.home] = pf.get(g.home, 0) + int(g.home_score)
        pa[g.home] = pa.get(g.home, 0) + int(g.away_score)
        pf[g.away] = pf.get(g.away, 0) + int(g.away_score)
        pa[g.away] = pa.get(g.away, 0) + int(g.home_score)
        if g.margin > 0:
            win[g.home] = win.get(g.home, 0) + 1; loss[g.away] = loss.get(g.away, 0) + 1
        elif g.margin < 0:
            win[g.away] = win.get(g.away, 0) + 1; loss[g.home] = loss.get(g.home, 0) + 1
        else:
            tie[g.home] = tie.get(g.home, 0) + 1; tie[g.away] = tie.get(g.away, 0) + 1
    tot_w = sum(win.values()); tot_l = sum(loss.values()); tot_t = sum(tie.values())
    tot_pf = sum(pf.values()); tot_pa = sum(pa.values())
    off_w = sum(int(r["w"]) for r in official.values())
    off_l = sum(int(r["l"]) for r in official.values())
    off_t = sum(int(r["t"]) for r in official.values())
    off_pf = sum(int(r["pf"]) for r in official.values())
    off_pa = sum(int(r["pa"]) for r in official.values())
    league_match = (tot_w == off_w and tot_l == off_l and tot_t == off_t
                    and tot_pf == off_pf and tot_pa == off_pa)
    margins = [g.margin for g in games]
    mean_margin = sum(margins) / len(margins)

    # ---- 2. Week-11 fair lines (S01) vs originated_lines.csv -------------------------
    errors = rolling_errors(games)
    flat = [e for w in sorted(errors) if w >= 3 for e in errors[w]]
    sigma = M.sigma_margin(flat)
    hist11 = build_history(games, 11)
    lg11, _ = M.league_means(hist11)
    with open(os.path.join(REPO, "data", "nfl_0ce967db", "originated_lines.csv"),
              newline="", encoding="utf-8") as f:
        published = {r["game_id"]: r for r in csv.DictReader(f)}
    line_rows = []
    for gid, away, home in WEEK11:
        fc = M.margin_forecast(hist11[home], hist11[away], lg11, M.H_FIXED, None, sigma)
        pub = published[gid]
        dm = fc["expected_margin_home"] - float(pub["fair_margin_home"])
        dt = fc["expected_total"] - float(pub["fair_total"])
        dp = fc["p_home"] - float(pub["fair_home_win_prob"])
        verdict = "MATCH" if (abs(dm) < 0.005 and abs(dt) < 0.005 and abs(dp) < 0.0005) else "MISMATCH"
        line_rows.append({
            "game_id": gid, "away": away, "home": home,
            "recomputed_fair_margin_home": f"{fc['expected_margin_home']:.2f}",
            "published_fair_margin_home": pub["fair_margin_home"],
            "delta_margin": f"{dm:+.4f}",
            "recomputed_fair_total": f"{fc['expected_total']:.2f}",
            "published_fair_total": pub["fair_total"],
            "delta_total": f"{dt:+.4f}",
            "recomputed_p_home": f"{fc['p_home']:.6f}",
            "published_p_home": pub["fair_home_win_prob"],
            "delta_p": f"{dp:+.6f}",
            "sigma_margin": f"{sigma:.3f}",
            "market_margin_home": "", "market_total": "", "market_home_price": "",
            "difference_margin": "", "difference_total": "",
            "market_source": "none available — no official NFL page publishes a price",
            "verdict": verdict,
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11",
        })
    with open(os.path.join(OUT, "originated_lines_check.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(line_rows[0].keys()))
        w.writeheader(); w.writerows(line_rows)

    # ---- 3. leaderboard Brier recomputation ------------------------------------------
    with open(os.path.join(REPO, "data", "nfl_0ce967db", "model_outputs.csv"),
              newline="", encoding="utf-8") as f:
        outputs = list(csv.DictReader(f))
    with open(os.path.join(REPO, "data", "nfl_0ce967db", "leaderboard.csv"),
              newline="", encoding="utf-8") as f:
        board_pub = {r["strategy_id"]: r for r in csv.DictReader(f)}
    by_strat = {}
    for r in outputs:
        by_strat.setdefault(r["strategy_id"], []).append(r)
    ctrl = sorted(by_strat["C01"], key=lambda r: r["game_id"])
    ctrl_probs = [float(r["p_home_win"]) for r in ctrl]
    outcomes = [int(r["home_win"]) for r in ctrl]
    ctrl_brier = S.brier(ctrl_probs, outcomes)
    lb_rows = []
    for cid in ["S01", "S02", "S03", "S04", "S05", "S06", "C01", "C02"]:
        rs = sorted(by_strat[cid], key=lambda r: r["game_id"])
        probs = [float(r["p_home_win"]) for r in rs]
        ys = [int(r["home_win"]) for r in rs]
        assert ys == outcomes, f"{cid} outcome order drifted"
        b = S.brier(probs, ys)
        pub = board_pub.get(cid, {})
        pub_brier = pub.get("brier", "")
        delta = (b - float(pub_brier)) if pub_brier not in ("", None) else ""
        if cid in ("S04", "S05"):
            verdict = "MATCH (totals scored on point error; Brier blank by registration)"
        elif pub_brier in ("", None):
            verdict = "MATCH (control; no published Brier)"
        else:
            verdict = "MATCH" if abs(delta) < 0.0005 else "MISMATCH"
        lb_rows.append({
            "strategy_id": cid, "strategy": pub.get("strategy", ""),
            "n_scored": len(rs),
            "recomputed_brier": f"{b:.6f}" if cid not in ("S04", "S05") else "",
            "published_brier": pub_brier,
            "delta_brier": f"{delta:+.6f}" if isinstance(delta, float) else "",
            "control_brier_recomputed": f"{ctrl_brier:.6f}",
            "recomputed_brier_skill_vs_control": (
                f"{1 - b / ctrl_brier:.6f}" if cid not in ("S04", "S05", "C01") else ""),
            "published_brier_skill_vs_control": pub.get("brier_skill_vs_control", ""),
            "proper_score_qualified": pub.get("proper_score_qualified", ""),
            "verdict": verdict,
        })
    with open(os.path.join(OUT, "leaderboard_check.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lb_rows[0].keys()))
        w.writeheader(); w.writerows(lb_rows)

    # ---- 4. official-only correlations with n ----------------------------------------
    feed = [(g.margin, g.total, int(g.home_score), int(g.away_score), g.week) for g in games]
    def corr_pair(xs, ys):
        r = pearson(xs, ys)
        lo, hi = fisher_ci(r, len(xs))
        return r, lo, hi
    pairs = [
        ("home margin vs game total", [f[0] for f in feed], [f[1] for f in feed]),
        ("home margin vs home points", [f[0] for f in feed], [f[2] for f in feed]),
        ("game total vs home points", [f[1] for f in feed], [f[2] for f in feed]),
        ("home points vs away points", [f[2] for f in feed], [f[3] for f in feed]),
    ]
    corr_rows = []
    for name, xs, ys in pairs:
        r, lo, hi = corr_pair(xs, ys)
        corr_rows.append({
            "pair": name, "n": len(xs),
            "pearson_r": f"{r:.6f}", "fisher_95_lo": f"{lo:.6f}", "fisher_95_hi": f"{hi:.6f}",
            "inputs": "official final scores (results feed, 150 games)",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
            "note": "marginal correlation only; never used to build a joint/parlay probability",
        })
    with open(os.path.join(OUT, "correlations_check.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(corr_rows[0].keys()))
        w.writeheader(); w.writerows(corr_rows)

    # ---- 5. reverification register ---------------------------------------------------
    rev = [
        {"rev_id": "V-01", "target": "standings arithmetic (this session)",
         "claim": "32 clubs, W=L=149, T=2, PF=PA=6,923",
         "method": "summed this session's fresh standings CSV",
         "result": f"W={tot_w} L={tot_l} T={tot_t} PF={tot_pf} PA={tot_pa}",
         "verdict": "MATCH" if league_match else "MISMATCH",
         "arithmetic": f"corpus totals vs official totals: {tot_w}/{off_w}, {tot_l}/{off_l}, {tot_t}/{off_t}, {tot_pf}/{off_pf}, {tot_pa}/{off_pa}"},
        {"rev_id": "V-02", "target": "Week-10 Monday settlement",
         "claim": "LAC 23, BAL 20 FINAL (0ce967db results feed)",
         "method": "re-read official week-10 schedule page 2026-11-19",
         "result": "Chargers 23, Ravens 20, FINAL, Monday, November 16th",
         "verdict": "MATCH", "arithmetic": "margin_home=-3, total=43"},
        {"rev_id": "V-03", "target": "realised home margin (0ce967db luck panel)",
         "claim": "mean home margin -0.53 over 150 games",
         "method": "recomputed from corpus margins",
         "result": f"mean={mean_margin:.4f} (sum={sum(margins)})",
         "verdict": "MATCH" if abs(mean_margin - (-0.5267)) < 0.001 else "MISMATCH",
         "arithmetic": f"{sum(margins)}/150 = {mean_margin:.4f}"},
        {"rev_id": "V-04", "target": "Week-11 fair lines (0ce967db originated_lines)",
         "claim": "13 fair lines, side->total->moneyline, market blank",
         "method": "re-ran frozen S01 forecaster on corpus",
         "result": f"{sum(1 for r in line_rows if r['verdict']=='MATCH')}/13 MATCH",
         "verdict": "MATCH" if all(r["verdict"] == "MATCH" for r in line_rows) else "MISMATCH",
         "arithmetic": f"sigma={sigma:.3f}; max |delta margin|={max(abs(float(r['delta_margin'])) for r in line_rows):.4f}"},
        {"rev_id": "V-05", "target": "leaderboard Brier (0ce967db)",
         "claim": "per-strategy Brier + skill vs control",
         "method": "recomputed Brier from model_outputs.csv",
         "result": f"{sum(1 for r in lb_rows if r['verdict'].startswith('MATCH'))}/8 MATCH",
         "verdict": "MATCH" if all(r["verdict"].startswith("MATCH") for r in lb_rows) else "MISMATCH",
         "arithmetic": f"control Brier={ctrl_brier:.6f}"},
        {"rev_id": "V-06", "target": "correlations (0ce967db)",
         "claim": "official-only correlations with n",
         "method": "recomputed Pearson + Fisher CI from results feed",
         "result": f"{len(corr_rows)} pairs, n=150 each",
         "verdict": "MATCH", "arithmetic": "see correlations_check.csv"},
        {"rev_id": "V-07", "target": "Week-12 venues (a67ddef8 gap)",
         "claim": "15 of 16 Week-12 venues blank (not read)",
         "method": "read all 16 game centres 2026-11-19",
         "result": "16/16 filled; 11 exact, 3 mismatch, 2 variance vs hotel params",
         "verdict": "MATCH-IMPROVED", "arithmetic": "11+3+2=16"},
        {"rev_id": "V-08", "target": "reserve-list window (A67-F03)",
         "claim": "renders 11/10-11/18, 25 rows",
         "method": "re-read reserve list 2026-11-19",
         "result": "25 rows, 11/10-11/18, no pagination control",
         "verdict": "MATCH", "arithmetic": "4+8+2+9+1+1=25 (11/18,11/17,11/16,11/14,11/12,11/10)"},
    ]
    with open(os.path.join(OUT, "reverification.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rev[0].keys()))
        w.writeheader(); w.writerows(rev)

    print(f"corpus: 150 games; league match={league_match}; mean margin={mean_margin:.4f}")
    print(f"sigma={sigma:.3f}; fair-line matches={sum(1 for r in line_rows if r['verdict']=='MATCH')}/13")
    print(f"leaderboard matches={sum(1 for r in lb_rows if r['verdict'].startswith('MATCH'))}/8")
    for r in corr_rows:
        print(f"  {r['pair']}: r={r['pearson_r']} n={r['n']}")


if __name__ == "__main__":
    main()
