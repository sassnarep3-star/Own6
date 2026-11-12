"""Walk-forward evaluation harness: backtest, gates and the leaderboard payload.

The harness is intentionally small and auditable:

  1. choose a test season,
  2. fit ratings on every prior season (strictly before),
  3. publish a model line for every game of the test season (no market input),
  4. score strategy families that are *frozen in code before the run*:
       S1 model-vs-market spread
       S2 model-vs-market total
       S3 model moneyline vs market
       S4 "fade the public line move" (needs closing + opening; blocked here)
       S5 player-prop residual model (needs prop history; blocked here)
       S6 two-leg same-game parlay (needs same-game dependence sample; blocked here)
       S7 cross-game parlay (independence assumption must be tested; blocked here)
       S8 injury-shock re-pricing (needs timestamped depth + injury archive)
  5. compute clustered bootstrap intervals and a Bonferroni family across every
     candidate actually tested, then hand the results to validation.evaluate_candidate.
"""
from __future__ import annotations

import numpy as np

from . import correlation, pricing, ratings, validation

STRATEGY_FAMILY = [
    {"candidate_id": "S1", "name": "Model spread vs close (home side, |edge| filter)",
     "market": "spread", "bet_type": "single", "status": "testable"},
    {"candidate_id": "S2", "name": "Model total vs close (over side, |edge| filter)",
     "market": "total", "bet_type": "single", "status": "testable"},
    {"candidate_id": "S3", "name": "Model moneyline vs close (dog only)",
     "market": "moneyline", "bet_type": "single", "status": "testable"},
    {"candidate_id": "S4", "name": "Line-move fade (open vs close)",
     "market": "spread", "bet_type": "single", "status": "blocked", "blocked_by": "no verified opening-line archive"},
    {"candidate_id": "S5", "name": "Player prop residual model",
     "market": "prop", "bet_type": "single", "status": "blocked", "blocked_by": "no licensed prop history or prop lines"},
    {"candidate_id": "S6", "name": "Same-game parlay (QB pass yds + WR rec yds)",
     "market": "sgp", "bet_type": "parlay", "status": "blocked", "blocked_by": "no player-level prop outcomes to pair"},
    {"candidate_id": "S7", "name": "Cross-game 2-leg parlay (independent only if tested)",
     "market": "parlay", "bet_type": "parlay", "status": "blocked", "blocked_by": "no verified same-slate closing prices for both legs"},
    {"candidate_id": "S8", "name": "Injury-shock re-pricing (starter out)",
     "market": "spread", "bet_type": "single", "status": "blocked", "blocked_by": "no timestamped historical injury/depth archive"},
]

MIN_EDGE = 1.5          # points of model-vs-market disagreement required to place a paper bet
MARKET_ANCHOR = 0.35    # weight on the market line when orienting the model (0 = pure model)
SHRINK_TO_MARKET = 0.50 # shrink the model's market-relative edge toward zero (0 = none)
BET_UNIT = 1.0
SLATE_SEED = 20261112


def _american_payout(american: float) -> float:
    """Decimal payout (profit per 1 unit) for a winning American price."""
    return american / 100.0 if american > 0 else 100.0 / (-american)


def season_lines(rows: list[dict], test_season: int) -> dict:
    rat = ratings.fit_ratings(rows, test_season)
    out = []
    for r in rows:
        if int(r["season"]) != test_season or not r.get("gameday"):
            continue
        if not r.get("spread_line") or not r.get("total_line"):
            continue
        home, away = r["home_team"], r["away_team"]
        # Orientation step: the raw rating model is blended with the market line so a
        # team that is systematically mismeasured is pulled toward the consensus, and a
        # reversal can never silently invert the side. Blending uses only the SAME
        # pre-game line, and the blended number is what the backtest bets.
        market_margin = -float(r["spread_line"])   # home perspective
        raw_margin = rat.expected_margin(home, away)
        margin = (1.0 - MARKET_ANCHOR) * raw_margin + MARKET_ANCHOR * market_margin
        total = rat.expected_total(home, away)
        out.append({"game_id": r["game_id"], "gameday": r["gameday"], "home": home, "away": away,
                    "model_margin": margin, "model_total": total,
                    "market_spread": -float(r["spread_line"]),   # home-team spread; nflverse stores home-favoured as positive
                    "market_total": float(r["total_line"]),
                    "home_score": r.get("home_score") or "", "away_score": r.get("away_score") or "",
                    "home_ml": r.get("home_moneyline") or "", "away_ml": r.get("away_moneyline") or ""})
    return {"ratings": rat, "games": out}


def backtest(rows: list[dict], test_season: int, sigma_margin: float, sigma_total: float,
             edge: float = MIN_EDGE) -> dict:
    data = season_lines(rows, test_season)
    rat = data["ratings"]
    per_bet = {k: [] for k in ("S1", "S2", "S3")}
    clusters = {k: [] for k in per_bet}
    detail = []
    for g in data["games"]:
        if not g["home_score"]:
            continue
        hs, as_ = float(g["home_score"]), float(g["away_score"])
        actual_margin = hs - as_
        actual_total = hs + as_
        # Market spread is stored from the HOME perspective (negative = home favoured).
        model_spread = -g["model_margin"]      # home spread implied by the model
        diff = (g["market_spread"] - model_spread) * (1.0 - SHRINK_TO_MARKET)
        side = None
        if abs(diff) >= edge:
            side = "home" if diff > 0 else "away"
            line = g["market_spread"]
            won = (actual_margin + line) > 0 if side == "home" else (actual_margin + line) < 0
            push = (actual_margin + line) == 0
            if not push:
                # Offered price is unknown for historical rows: use a standard -110 and
                # label the assumption in the output (never presented as a verified price).
                price = -110.0
                ret = _american_payout(price) if won else -BET_UNIT
                per_bet["S1"].append(ret)
                clusters["S1"].append(g["gameday"])
                detail.append({"strategy": "S1", "game_id": g["game_id"], "side": side, "line": line,
                               "model_margin": round(g["model_margin"], 2), "result": "win" if won else "loss",
                               "price_used": price, "price_verified": False})
        diff_t = (g["market_total"] - g["model_total"]) * (1.0 - SHRINK_TO_MARKET)
        if abs(diff_t) >= edge:
            side_t = "over" if diff_t > 0 else "under"
            won = actual_total > g["market_total"] if side_t == "over" else actual_total < g["market_total"]
            push = actual_total == g["market_total"]
            if not push:
                price = -110.0
                ret = _american_payout(price) if won else -BET_UNIT
                per_bet["S2"].append(ret)
                clusters["S2"].append(g["gameday"])
                detail.append({"strategy": "S2", "game_id": g["game_id"], "side": side_t, "line": g["market_total"],
                               "model_total": round(g["model_total"], 2), "result": "win" if won else "loss",
                               "price_used": price, "price_verified": False})
        # S3: moneyline on the underdog only, priced at the stored (community) moneyline.
        try:
            hml, aml = float(g["home_ml"]), float(g["away_ml"])
        except (TypeError, ValueError):
            hml = aml = None
        if hml and aml:
            p_home_model = pricing.win_probability(g["model_margin"], sigma_margin)["p_home"]
            home_is_dog = hml > aml
            p, price = (p_home_model, hml) if home_is_dog else (1 - p_home_model, aml)
            fair = pricing.prob_to_american(p)
            edge_pp = p - pricing.american_to_prob(price)
            if edge_pp >= 0.03 and fair is not None:
                won = (actual_margin > 0) if home_is_dog else (actual_margin < 0)
                ret = _american_payout(price) if won else -BET_UNIT
                per_bet["S3"].append(ret)
                clusters["S3"].append(g["gameday"])
                detail.append({"strategy": "S3", "game_id": g["game_id"],
                               "side": "home" if home_is_dog else "away", "line": price,
                               "model_edge_pp": round(edge_pp, 4), "result": "win" if won else "loss",
                               "price_used": price, "price_verified": False})

    results = {}
    for sid, returns in per_bet.items():
        arr = np.array(returns, dtype=float)
        cl = np.array(clusters[sid])
        if len(arr) == 0:
            results[sid] = {"n_bets": 0, "n_events": 0, "n_clusters": 0, "roi": None, "roi_ci": None,
                            "returns": arr, "detail": []}
            continue
        roi = float(arr.mean())            # stake = 1 unit, so mean return = ROI
        roi_ci = correlation.cluster_bootstrap_ci(arr, cl, lambda v: float(np.mean(v)))
        results[sid] = {
            "n_bets": int(len(arr)), "n_events": int(len(arr)), "n_clusters": int(len(set(cl))),
            "roi": roi, "roi_ci": roi_ci,
            "win_rate": float((arr > 0).mean()),
            "returns": arr,
            "detail": [d for d in detail if d["strategy"] == sid],
        }
    return {"test_season": test_season, "ratings": rat, "results": results, "detail": detail,
            "sigma_margin": sigma_margin, "sigma_total": sigma_total}


def gate_board(test: dict, n_trials: int, license_status: str = "unverified") -> list[dict]:
    boards = []
    p_values = []
    for cand in STRATEGY_FAMILY:
        sid = cand["candidate_id"]
        base = {"candidate_id": sid, "name": cand["name"], "market": cand["market"],
                "source_url": "https://github.com/leesharpe/nfldata/blob/master/data/games.csv",
                "license_status": "unverified", "rows_with_urls": 0, "rows_total": 0}
        if cand["status"] != "testable":
            boards.append(validation.evaluate_candidate(base, None))
            continue
        r = test["results"].get(sid, {})
        if not r or r["n_bets"] == 0:
            boards.append(validation.evaluate_candidate(base, None))
            continue
        # A one-sided binomial test that the win rate beats the market-implied rate.
        try:
            from scipy.stats import binomtest
            p0 = pricing.american_to_prob(-110.0) if sid in ("S1", "S2") else 0.5
            k = int((r["returns"] > 0).sum())
            pv = float(binomtest(k, len(r["returns"]), p0, alternative="greater").pvalue)
        except Exception:  # pragma: no cover
            pv = 1.0
        p_values.append(pv)
        results = {
            "train_seasons": list(test["ratings"].seasons), "test_season": test["test_season"],
            "n_bets": r["n_bets"], "n_events": r["n_events"], "n_clusters": r["n_clusters"],
            "bss": None, "bss_ci": None,             # no market probability series for calibration here
            "roi": r["roi"], "roi_ci": r["roi_ci"],
            "clv": None, "clv_ci": None,             # no opening/closing probability sidecar
            "p_values": [], "r": None, "r_n": 0, "r_ci": None,
            "returns": r["returns"], "n_trials": n_trials,
        }
        boards.append(validation.evaluate_candidate(base, results))
    # Multiplicity: recompute the family gate with the full p list on every testable board.
    if p_values:
        g = validation.gate_multiplicity(p_values, "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm")
        for b in boards:
            for row in b["gates"]:
                if row["gate_id"] == "G08":
                    row.update(g.as_row())
        for b in boards:
            if any(row["status"] == "fail" for row in b["gates"]):
                b["status"] = "rejected"
            elif all(row["status"] == "pass" for row in b["gates"]):
                b["status"] = "qualifies"
    return boards
