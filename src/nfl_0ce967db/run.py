"""Build the results feed, model-output ledger and scored board for session 0ce967db.

Run order matters and is deliberately one-way:

    python3 src/nfl_0ce967db/run.py

Inputs (all committed, all read earlier from official pages):
    data/nfl_7a59fd89/corpus_150.csv              inherited rows weeks 1-10 (repo claim)
    data/nfl_0ce967db/raw/week10_finals_read_2026_11_18.txt  this session's settlement read

Outputs (all under data/nfl_0ce967db/):
    results_feed.csv, corpus_reconciliation.csv, model_outputs.csv, week11_forecasts.csv,
    leaderboard.csv, control_baselines.csv, luck_panel.csv, demotion_gate.csv,
    ablation_inputs.csv, metrics.csv

No network. No wall clock in any output. Re-running must reproduce every byte (tests assert it).
"""
from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nfl_0ce967db import model as M  # noqa: E402
from nfl_0ce967db import score as S  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "data", "nfl_0ce967db")
CORPUS = os.path.join(REPO, "data", "nfl_7a59fd89", "corpus_150.csv")
PREREG_COMMIT = "frozen in data/nfl_0ce967db/preregistration.md; registration commit is the first commit containing it"

# Week-10 finals read this session, verbatim from the raw artifact. Used ONLY to fill the
# one row the inherited corpus left blank because the game was live at that session's read.
WEEK10_SETTLEMENT = {"2026-W10-14": (23, 20)}  # LAC 23, BAL 20

OFFICIAL_STANDINGS = {  # data/nfl_0ce967db/standings_2026_11_18.csv, read 2026-11-18T03:43Z
    "BUF": (8, 1, 0, 287, 199), "NE": (5, 5, 0, 221, 242), "NYJ": (2, 8, 0, 194, 254),
    "MIA": (1, 8, 0, 148, 224), "CIN": (7, 2, 0, 278, 193), "PIT": (6, 3, 0, 198, 182),
    "CLE": (6, 4, 0, 188, 220), "BAL": (4, 6, 0, 209, 259), "JAX": (7, 2, 0, 269, 144),
    "HOU": (3, 6, 0, 233, 219), "IND": (3, 7, 0, 208, 271), "TEN": (1, 8, 0, 167, 239),
    "KC": (7, 2, 0, 237, 156), "DEN": (7, 2, 0, 198, 186), "LV": (4, 6, 0, 251, 289),
    "LAC": (1, 8, 0, 144, 239), "NYG": (5, 3, 1, 203, 196), "DAL": (4, 6, 0, 286, 282),
    "WAS": (3, 5, 1, 196, 223), "PHI": (2, 7, 0, 148, 221), "DET": (7, 2, 0, 257, 199),
    "MIN": (7, 2, 0, 176, 126), "CHI": (7, 2, 0, 241, 184), "GB": (6, 4, 0, 226, 221),
    "CAR": (4, 5, 0, 219, 236), "TB": (3, 6, 0, 202, 178), "NO": (3, 6, 0, 202, 236),
    "ATL": (3, 7, 0, 201, 258), "SF": (8, 1, 0, 281, 196), "SEA": (6, 4, 0, 223, 175),
    "LA": (6, 4, 0, 248, 187), "AZ": (3, 7, 0, 184, 289),
}

# Club-code irregularity found this session: the corpus writes LAR once, LA nine times.
# The official standings page uses LA. Nothing else in the corpus was altered.
CODE_FIX = {"LAR": "LA"}

WEEK11 = [  # data/nfl_0ce967db/week11_slate.csv (official read 2026-11-18T03:44Z)
    ("W11-01", "IND", "HOU"), ("W11-02", "MIA", "BUF"), ("W11-03", "BAL", "CAR"),
    ("W11-04", "NO", "CHI"), ("W11-05", "TEN", "DAL"), ("W11-06", "TB", "DET"),
    ("W11-07", "AZ", "KC"), ("W11-08", "PIT", "PHI"), ("W11-09", "NYJ", "LAC"),
    ("W11-10", "JAX", "NYG"), ("W11-11", "LV", "DEN"), ("W11-12", "MIN", "SF"),
    ("W11-13", "CIN", "WAS"),
]


def read_corpus() -> list[M.Game]:
    games: list[M.Game] = []
    with open(CORPUS, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            away = CODE_FIX.get(row["away"], row["away"])
            home = CODE_FIX.get(row["home"], row["home"])
            a = row["away_score"].strip()
            h = row["home_score"].strip()
            if row["game_id"] in WEEK10_SETTLEMENT:
                a, h = (str(x) for x in WEEK10_SETTLEMENT[row["game_id"]])
            games.append(M.Game(
                game_id=row["game_id"], week=int(row["week"]), away=away, home=home,
                away_score=int(a) if a else None, home_score=int(h) if h else None,
                date_on_card=row.get("date_on_card", "")))
    return games


def build_history(games: list[M.Game], before_week: int) -> dict[str, M.TeamHistory]:
    hist: dict[str, M.TeamHistory] = {}
    for g in games:
        if g.week >= before_week or not g.played:
            continue
        hist.setdefault(g.home, M.TeamHistory()).append(int(g.home_score), int(g.away_score))
        hist.setdefault(g.away, M.TeamHistory()).append(int(g.away_score), int(g.home_score))
    return hist


def rolling_errors(games: list[M.Game]) -> dict[int, list[float]]:
    """Per-week list of (actual - expected) home margins using only prior weeks, H=2.5 fixed.

    Computed with the same S01 machinery so the sigma used to score a week is the sigma that
    week's own forecast would have been allowed to know.
    """
    per_week: dict[int, list[float]] = {}
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
    unplayed = [g.game_id for g in games if not g.played]
    assert not unplayed, f"unsettled games present: {unplayed}"

    # ---- 1. results feed + reconciliation ------------------------------------------------
    with open(os.path.join(OUT, "results_feed.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["game_id", "week", "away", "home", "away_score", "home_score",
                    "margin_home", "total", "provenance", "source_url", "read_on_utc"])
        for g in games:
            prov = ("settled this session from the week-10 finals read"
                    if g.game_id in WEEK10_SETTLEMENT else "inherited from data/nfl_7a59fd89/corpus_150.csv")
            url = ("https://www.nfl.com/schedules/2026/by-week/week-10"
                   if g.game_id in WEEK10_SETTLEMENT
                   else f"https://www.nfl.com/schedules/2026/by-week/week-{g.week}")
            clock = ("2026-11-18T03:46:00Z" if g.game_id in WEEK10_SETTLEMENT
                     else "2026-11-17T01:26:00Z (inherited read clock)")
            w.writerow([g.game_id, g.week, g.away, g.home, g.away_score, g.home_score,
                        g.margin, g.total, prov, url, clock])

    # club-level reconciliation against today's official standings
    pf: dict[str, int] = {c: 0 for c in OFFICIAL_STANDINGS}
    pa: dict[str, int] = {c: 0 for c in OFFICIAL_STANDINGS}
    win: dict[str, int] = {c: 0 for c in OFFICIAL_STANDINGS}
    loss: dict[str, int] = {c: 0 for c in OFFICIAL_STANDINGS}
    tie: dict[str, int] = {c: 0 for c in OFFICIAL_STANDINGS}
    for g in games:
        pf[g.home] += int(g.home_score); pa[g.home] += int(g.away_score)
        pf[g.away] += int(g.away_score); pa[g.away] += int(g.home_score)
        if g.margin > 0:
            win[g.home] += 1; loss[g.away] += 1
        elif g.margin < 0:
            win[g.away] += 1; loss[g.home] += 1
        else:
            tie[g.home] += 1; tie[g.away] += 1
    with open(os.path.join(OUT, "corpus_reconciliation.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["club", "corpus_w", "corpus_l", "corpus_t", "corpus_pf", "corpus_pa",
                    "official_w", "official_l", "official_t", "official_pf", "official_pa",
                    "record_match", "pf_match", "pa_match", "source_url", "read_on_utc"])
        for c, (W, L, T, P, A) in OFFICIAL_STANDINGS.items():
            w.writerow([c, win[c], loss[c], tie[c], pf[c], pa[c], W, L, T, P, A,
                        "yes" if (win[c], loss[c], tie[c]) == (W, L, T) else "NO",
                        "yes" if pf[c] == P else "NO", "yes" if pa[c] == A else "NO",
                        "https://www.nfl.com/standings/division/2026/reg", "2026-11-18T03:43:00Z"])

    # ---- 2. model outputs + scores -------------------------------------------------------
    errors = rolling_errors(games)
    scorer_weeks = [w for w in sorted(errors) if w >= 3]
    errors_flat: list[float] = []
    for w in scorer_weeks:
        errors_flat.extend(errors[w])
    sigma_fitted = M.sigma_margin(errors_flat)

    candidates = {
        "S01": ("ML-SEASON", dict(h=M.H_FIXED, half_life=None)),
        "S02": ("ML-FITHFA", dict(h="fitted", half_life=None)),
        "S03": ("ML-RECENCY", dict(h=M.H_FIXED, half_life=M.HALF_LIFE)),
        "S04": ("TOT-SEASON", dict(h=M.H_FIXED, half_life=None)),
        "S05": ("TOT-RECENCY", dict(h=M.H_FIXED, half_life=M.HALF_LIFE)),
        # Amendment A1: rolling home field, defined AFTER the backtest was seen. Scored rows are
        # post-hoc diagnostics, excluded from every leaderboard column and from the promotion sample.
        "S06": ("ML-ROLLING-HFA", dict(h="rolling", half_life=None)),
    }

    rows: list[dict] = []
    for cid, (name, cfg) in candidates.items():
        for g in games:
            if g.week < 3:
                continue  # registration §5: weeks 1-2 are training data only
            hist = build_history(games, g.week)
            if g.home not in hist or g.away not in hist:
                continue
            M.assert_chronology(g, hist, prior_max_week=g.week - 1)
            lg, _ = M.league_means(hist)
            h_field = cfg["h"]
            if h_field == "rolling":
                prior_margins = [gg.margin for gg in games if gg.week < g.week and gg.played]
                h_field = sum(prior_margins) / len(prior_margins)
            elif h_field == "fitted":
                prior_margins = [gg.margin for gg in games if gg.week < g.week and gg.played]
                assert prior_margins, "no prior margins to fit H on"
                h_field = sum(prior_margins) / len(prior_margins)
            # registration §3: ONE sigma_M from the training window, identical for every candidate
            sigma = sigma_fitted
            fc = M.margin_forecast(hist[g.home], hist[g.away], lg, h_field, cfg["half_life"], sigma)
            rows.append({
                "strategy_id": cid, "strategy": name, "game_id": g.game_id, "week": g.week,
                "home": g.home, "away": g.away,
                "p_home_win": fc["p_home"],
                "expected_margin_home": fc["expected_margin_home"],
                "expected_total": fc["expected_total"],
                "sigma_margin": sigma,
                "h_field_used": h_field,
                "half_life": "" if cfg["half_life"] is None else cfg["half_life"],
                "shrink_k": M.K_SHRINK,
                "league_ppg_used": fc["league_ppg"],
                "n_home_prior": fc["n_home"], "n_away_prior": fc["n_away"],
                "dev_home": fc["dev_home"], "dev_away": fc["dev_away"],
                "actual_margin_home": g.margin, "actual_total": g.total, "home_win": g.home_win,
                "inputs_rule": "week<" + str(g.week) + "; no market price, no injuries, no personnel",
                "prereg": PREREG_COMMIT,
            })

    # controls: C01 climatology (training-window home-win rate) and C02 always-home
    for g in games:
        if g.week < 3:
            continue
        prior = [x.home_win for x in games if x.week < g.week]
        rows.append({
            "strategy_id": "C01", "strategy": "CONTROL-CLIMATOLOGY", "game_id": g.game_id,
            "week": g.week, "home": g.home, "away": g.away,
            "p_home_win": sum(prior) / len(prior), "expected_margin_home": "",
            "expected_total": "", "sigma_margin": "", "h_field_used": "",
            "half_life": "", "shrink_k": "", "league_ppg_used": "",
            "n_home_prior": "", "n_away_prior": "", "dev_home": "", "dev_away": "",
            "actual_margin_home": g.margin, "actual_total": g.total, "home_win": g.home_win,
            "inputs_rule": "week<" + str(g.week) + "; training-window home-win rate only",
            "prereg": PREREG_COMMIT})
        rows.append({
            "strategy_id": "C02", "strategy": "CONTROL-HOME-ALWAYS", "game_id": g.game_id,
            "week": g.week, "home": g.home, "away": g.away, "p_home_win": 1.0,
            "expected_margin_home": "", "expected_total": "", "sigma_margin": "",
            "h_field_used": "", "half_life": "", "shrink_k": "", "league_ppg_used": "",
            "n_home_prior": "", "n_away_prior": "", "dev_home": "", "dev_away": "",
            "actual_margin_home": g.margin, "actual_total": g.total, "home_win": g.home_win,
            "inputs_rule": "no inputs", "prereg": PREREG_COMMIT})

    fields = ["strategy_id", "strategy", "game_id", "week", "home", "away", "p_home_win",
              "expected_margin_home", "expected_total", "sigma_margin", "h_field_used",
              "half_life", "shrink_k", "league_ppg_used", "n_home_prior", "n_away_prior",
              "dev_home", "dev_away", "actual_margin_home", "actual_total", "home_win",
              "inputs_rule", "prereg"]
    with open(os.path.join(OUT, "model_outputs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    # ---- 3. score every candidate ---------------------------------------------------------
    by_strategy: dict[str, list[dict]] = {}
    for r in rows:
        by_strategy.setdefault(r["strategy_id"], []).append(r)
    order = sorted((r for r in rows if r["strategy_id"] == "C01"), key=lambda r: r["game_id"])
    ctrl_probs = [float(r["p_home_win"]) for r in order]
    outcomes = [r["home_win"] for r in order]
    weeks = [r["week"] for r in order]
    clusters: dict[int, list[int]] = {}
    for i, w in enumerate(weeks):
        clusters.setdefault(w, []).append(i)

    board = []
    luck = []
    for cid, name, kind in [("S01", "ML-SEASON", "margin"), ("S02", "ML-FITHFA", "margin"),
                            ("S03", "ML-RECENCY", "margin"), ("S04", "TOT-SEASON", "total"),
                            ("S05", "TOT-RECENCY", "total"), ("S06", "ML-ROLLING-HFA", "posthoc"),
                            ("C01", "CONTROL-CLIMATOLOGY", "control"),
                            ("C02", "CONTROL-HOME-ALWAYS", "control")]:
        rs = sorted(by_strategy[cid], key=lambda r: r["game_id"])
        probs = [float(r["p_home_win"]) for r in rs]
        ys = [r["home_win"] for r in rs]
        assert ys == outcomes, f"{cid} row order drifted"
        entry = {
            "strategy_id": cid, "strategy": name, "kind": kind,
            "division": ("singles-total" if kind == "total" else
                         "singles-moneyline-posthoc-diagnostic" if kind == "posthoc"
                         else "singles-moneyline"),
            "n_scored": len(rs), "weeks": len(clusters),
        }
        if kind == "total":
            # A total is not a win probability. The registration §4 scores totals on error in
            # points, so moneyline Brier cells stay blank for S04/S05 rather than being a copy
            # of the margin model's win probability (which is what a bug produced in run 1).
            errs = [float(r["expected_total"]) - float(r["actual_total"]) for r in rs]
            bias = S.bootstrap_mean_difference(clusters, [float(r["expected_total"]) for r in rs],
                                               [float(r["actual_total"]) for r in rs])
            mae = S.bootstrap_mae(clusters, errs)
            rmse = S.bootstrap_rmse(clusters, errs)
            entry.update({
                "brier": "", "brier_reference_control": "", "brier_skill_vs_control": "",
                "bss_lower_95_week_cluster": "", "bss_upper_95_week_cluster": "",
                "bootstrap_resamples": S.RESAMPLES, "bootstrap_seed": S.SEED,
                "log_loss": "", "games_better_than_control": "", "games_worse_than_control": "",
                "games_tied_on_squared_error": "", "sign_test_p_two_sided": "",
                "bonferroni_threshold_family7": "", "bonferroni_p": "", "bonferroni_pass": "",
                "proper_score_qualified": "no",
                "qualification_note": "totals are scored on point error; no registered win-probability test applies",
                "totals_n": len(errs), "totals_mae_points": mae["point"],
                "totals_mae_lower_95": mae["lo"], "totals_mae_upper_95": mae["hi"],
                "totals_rmse_points": rmse["point"], "totals_rmse_lower_95": rmse["lo"],
                "totals_rmse_upper_95": rmse["hi"], "totals_mean_error_points": bias["point"],
                "totals_mean_error_lower_95": bias["lo"], "totals_mean_error_upper_95": bias["hi"],
            })
            # paired comparison of the two registered totals estimators (the gap column)
            if cid == "S05":
                e4 = [abs(float(r["expected_total"]) - float(r["actual_total"]))
                      for r in sorted(by_strategy["S04"], key=lambda r: r["game_id"])]
                e5 = [abs(float(r["expected_total"]) - float(r["actual_total"])) for r in rs]
                gap = S.bootstrap_mean_difference(clusters, e4, e5)
                entry.update({"gap_vs_S04_abs_error_points": gap["point"],
                              "gap_vs_S04_lower_95": gap["lo"],
                              "gap_vs_S04_upper_95": gap["hi"]})
            board.append(entry)
            luck.append({"strategy_id": cid, "strategy": name, "n": len(rs),
                         "base_rate": "", "brier": "", "reliability": "", "resolution": "",
                         "uncertainty": "", "luck_share": "",
                         "mean_probability": "", "distinct": "",
                         "note": "not a probability forecaster"})
            continue
        bs = S.brier(probs, ys)
        ll = S.log_loss(probs, ys)
        bss = S.brier_skill(probs, ys, ctrl_probs)
        boot = S.bootstrap_bss(clusters, probs, ys, ctrl_probs)
        disc = S.paired_discordance(probs, ys, ctrl_probs)
        bonf = S.bonferroni(disc["sign_test_p"])
        qualifies = bool(boot["lo"] is not None and boot["lo"] > 0 and bonf["passes"])
        entry.update({
            "brier": bs, "brier_reference_control": S.brier(ctrl_probs, outcomes),
            "brier_skill_vs_control": bss,
            "bss_lower_95_week_cluster": boot["lo"], "bss_upper_95_week_cluster": boot["hi"],
            "bootstrap_resamples": boot["resamples"], "bootstrap_seed": S.SEED,
            "log_loss": ll,
            "games_better_than_control": disc["games_better"],
            "games_worse_than_control": disc["games_worse"],
            "games_tied_on_squared_error": disc["games_tied"],
            "sign_test_p_two_sided": disc["sign_test_p"],
            "bonferroni_threshold_family7": bonf["threshold"],
            "bonferroni_p": bonf["p_times_family"],
            "bonferroni_pass": "yes" if bonf["passes"] else "no",
            "proper_score_qualified": "yes" if qualifies else "no",
            "totals_n": "", "totals_mae_points": "", "totals_mae_lower_95": "",
            "totals_mae_upper_95": "", "totals_rmse_points": "", "totals_rmse_lower_95": "",
            "totals_rmse_upper_95": "", "totals_mean_error_points": "",
            "totals_mean_error_lower_95": "", "totals_mean_error_upper_95": "",
            "gap_vs_S04_abs_error_points": "", "gap_vs_S04_lower_95": "",
            "gap_vs_S04_upper_95": "",
            "qualification_note": ("backtest only; the prospective board stays empty until week-11 "
                                   "forecasts are scored"),
        })
        if kind == "posthoc":
            entry["proper_score_qualified"] = "no"
            entry["qualification_note"] = ("post_hoc_diagnostic: defined in amendment A1 after the "
                                           "backtest was seen; excluded from every leaderboard column "
                                           "and from the 100-game promotion sample")
        entry.update({"roi": "", "clv": "", "units": "",
                      "why_no_roi": "no official page publishes a price; registration §4 forbids inventing one",
                      "leaderboard_state": "not_eligible: backtest numbers are barred from the prospective board"})
        board.append(entry)
        lk = S.variance_decomposition(probs, ys)
        luck.append({"strategy_id": cid, "strategy": name, "n": lk["n"],
                     "base_rate": lk["base_rate"], "brier": lk["brier"],
                     "reliability": lk["reliability"], "resolution": lk["resolution"],
                     "uncertainty": lk["uncertainty"], "luck_share": lk["luck_share"],
                     "distinct": lk["distinct_forecast_values"],
                     "mean_probability": sum(probs) / len(probs),
                     "note": "exact per-value Murphy decomposition (binned table is the readable approximation)"})

    fields_b = sorted({k for e in board for k in e})
    # a diagnostic must not be readable as a qualification
    for e in board:
        if e.get("kind") == "posthoc":
            e["bonferroni_pass"] = "n/a (post-hoc diagnostic)"
            e["sign_test_p_two_sided"] = ""
    with open(os.path.join(OUT, "leaderboard.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields_b)
        w.writeheader()
        for e in board:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in e.items()})

    with open(os.path.join(OUT, "control_baselines.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields_b)
        w.writeheader()
        for e in board:
            if e["kind"] == "control":
                w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in e.items()})

    with open(os.path.join(OUT, "luck_panel.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["strategy_id", "strategy", "n", "mean_probability", "observed_home_win_rate",
                    "base_rate", "brier", "reliability", "resolution", "uncertainty",
                    "luck_share_reliability_over_brier", "distinct_forecast_values", "note"])
        def fmt(v, nd=6):
            return f"{v:.{nd}f}" if isinstance(v, (int, float)) else ""

        for l in luck:
            w.writerow([l["strategy_id"], l["strategy"], l["n"], fmt(l["mean_probability"]),
                        fmt(l["base_rate"]), fmt(l["base_rate"]), fmt(l["brier"]),
                        fmt(l["reliability"]), fmt(l["resolution"]), fmt(l["uncertainty"]),
                        fmt(l["luck_share"]), l["distinct"], l["note"]])

    # ---- 4. week-11 prospective forecasts (registered before kickoff) --------------------
    hist = build_history(games, 11)
    lg, _ = M.league_means(hist)
    with open(os.path.join(OUT, "week11_forecasts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["game_id", "away", "home", "p_home_win_S01", "p_home_win_S03",
                    "expected_margin_home_S01", "expected_total_S04", "expected_total_S05",
                    "sigma_margin", "n_away_prior", "n_home_prior", "league_ppg",
                    "market_line_home", "market_total", "difference_vs_market",
                    "state", "registered_before_kickoff_utc", "prereg"])
        for gid, away, home in WEEK11:
            f1 = M.margin_forecast(hist[home], hist[away], lg, M.H_FIXED, None, sigma_fitted)
            f3 = M.margin_forecast(hist[home], hist[away], lg, M.H_FIXED, M.HALF_LIFE, sigma_fitted)
            f4 = M.margin_forecast(hist[home], hist[away], lg, M.H_FIXED, None, sigma_fitted)
            f5 = M.margin_forecast(hist[home], hist[away], lg, M.H_FIXED, M.HALF_LIFE, sigma_fitted)
            w.writerow([gid, away, home, f"{f1['p_home']:.6f}", f"{f3['p_home']:.6f}",
                        f"{f1['expected_margin_home']:.2f}", f"{f4['expected_total']:.2f}",
                        f"{f5['expected_total']:.2f}", f"{sigma_fitted:.3f}",
                        hist[away].n, hist[home].n, f"{lg:.3f}",
                        "", "", "", "paper",
                        "2026-11-18T03:50:00Z (before the 2026-11-19T01:15Z TNF kickoff)",
                        PREREG_COMMIT])

    # ---- 5. demotion gate state ----------------------------------------------------------
    with open(os.path.join(OUT, "demotion_gate.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["strategy_id", "state", "promotion_rule", "demotion_rule",
                    "prospective_scored", "promotion_needs", "blocking_gate", "next_eligible_utc"])
        for cid in ["S01", "S02", "S03", "S04", "S05"]:
            w.writerow([cid, "paper",
                        "prospective n>=100 AND week-cluster BSS lower bound>0 AND Bonferroni pass",
                        "trailing-50 prospective BSS lower bound<0 -> paper (automatic)",
                        0, 100,
                        "week-11 games are not yet played; no prospective forecast has been scored",
                        "2026-11-24T00:00:00Z (after the week-11 Monday game)"])
    print("wrote results_feed, corpus_reconciliation, model_outputs, leaderboard, controls, "
          "luck_panel, week11_forecasts, demotion_gate")
    print(f"scored rows per candidate: {len(order)}  sigma_fitted={sigma_fitted}")
    def g(v, spec):
        return format(v, spec) if isinstance(v, (int, float)) else "n/a"

    for e in board:
        print(f"  {e['strategy_id']:4} {e['strategy']:22} BSS={g(e['brier_skill_vs_control'], '+.4f')} "
              f"lo={g(e['bss_lower_95_week_cluster'], '.4f')} mae={g(e['totals_mae_points'], '.2f')} "
              f"bonf={e['bonferroni_pass'] or 'n/a'}")


if __name__ == "__main__":
    main()
