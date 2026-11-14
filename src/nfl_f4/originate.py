"""Own-line origination, in the required order: side, then total, then moneyline.

The order is a methodological gate, not a display preference:

1. **Side first.** The side (spread) is the market with the deepest price
   history and the least model risk, so a side number that cannot beat the
   market invalidates nothing downstream — but it does tell you the model has no
   edge yet.
2. **Total second.** The total is derived independently of the side (pace and
   scoring environment), which is why the two can be cross-checked against the
   market's own two-way price rather than against each other.
3. **Moneyline last.** Win probability is a nonlinear function of the fair
   spread and the fair total, so publishing it before the other two would be
   publishing an assumption dressed as a number.

Every published value here is either arithmetic over verified inputs or a
parameter that is DECLARED in ``PARAMS`` and flagged. Nothing is fitted: with
one week of prices and a 137-game results history, any coefficient would be
noise. The model is therefore deliberately the simplest thing that can be
wrong in public — a points-per-game rating with no home-field term and no
opponent adjustment — and each of those omissions is a flag, not a secret.

Fair line, market line and difference are always separate columns. The
difference column is signed from the model's point of view (positive = the model
rates the home side stronger than the market does).
"""

from __future__ import annotations

import csv
import math
import os
from typing import Dict, List, Optional

from . import prices as P
from . import results as R

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "nfl_f4", "raw")
OUT = os.path.join(ROOT, "data", "nfl_f4")

# ---------------------------------------------------------------------------
# DECLARED parameters. None of these is measured; each is flagged in flagged.csv.
# ---------------------------------------------------------------------------
PARAMS = {
    "home_field_points": 0.0,        # F4-F05: no verified HFA available
    "shrinkage_to_league_mean": 0.0,  # F4-F05: needs multi-season history
    "sigma_margin": 13.86,           # F4-F06: published NFL margin SD, not fitted here
    "sigma_total": 13.5,             # F4-F06: declared for total dispersion
    "ppg_floor_games": 4,            # F4-F07: teams below this are not rated
    "max_abs_fair_spread": 21.0,
    "max_fair_total_deviation": 14.0,
    "min_edge_to_quote_points": 0.5,
}

# sigma_margin is the only number here with a citable basis; it is the standard
# deviation of NFL game margins used in public win-probability work. It is NOT
# re-estimated in this pack (n=137 single season) and is flagged as declared.

ORIGINATION_ORDER = ("side", "total", "moneyline")

MARKET_FIELDS = [
    "market_id", "game_key", "week", "kickoff_et", "away", "home", "market",
    "origination_order", "selection", "fair_line", "fair_prob", "market_line",
    "market_price_american", "market_implied_prob", "difference_points",
    "difference_prob", "direction", "edge_vs_close_points", "beat_close",
    "model_status", "market_status", "flags", "results_source_url",
    "price_source_url",
]


def _num(x) -> Optional[float]:
    if x is None or str(x).strip() == "":
        return None
    return float(x)


def load_week10_slate() -> List[dict]:
    """Week 10 matchups from the price capture (the games we originate)."""
    seen: Dict[str, dict] = {}
    for r in P.load_prices():
        key = f"{r['away']}@{r['home']}"
        seen.setdefault(key, {"away": r["away"], "home": r["home"],
                              "provider_event_id": r["provider_event_id"]})
    return list(seen.values())


def team_ratings(before_week: int = 10) -> Dict[str, dict]:
    """PPG ratings from verified results strictly before ``before_week``.

    Scores are the only input. This is intentionally naive: no opponent
    adjustment, no home/away split, no pace model. It exists so that a fair line
    and a market line can sit in separate columns and be visibly different.
    """
    rows = [r for r in R.result_rows() if int(r["week"]) < before_week]
    agg: Dict[str, dict] = {}
    for r in rows:
        a, h = int(r["away_score"]), int(r["home_score"])
        for team, pf, pa in ((r["away"], a, h), (r["home"], h, a)):
            d = agg.setdefault(team, {"pf": 0, "pa": 0, "g": 0})
            d["pf"] += pf
            d["pa"] += pa
            d["g"] += 1
    out = {}
    for t, d in agg.items():
        if d["g"] < PARAMS["ppg_floor_games"]:
            continue
        out[t] = {"pf_pg": d["pf"] / d["g"], "pa_pg": d["pa"] / d["g"],
                  "games": d["g"]}
    return out


def league_ppg(ratings: Dict[str, dict]) -> float:
    return sum(v["pf_pg"] for v in ratings.values()) / len(ratings)


def win_prob_from_spread(spread_home: float, sigma: float = None) -> float:
    """P(home wins) from a fair home spread, normal margin model.

    A tie is split evenly, which is the standard treatment for a continuous
    approximation to a discrete margin.
    """
    s = sigma if sigma is not None else PARAMS["sigma_margin"]
    return 0.5 * (1.0 + math.erf(spread_home / (s * math.sqrt(2.0))))


def spread_to_price(p: float) -> int:
    """Fair American price for a probability (no vig)."""
    if p <= 0 or p >= 1:
        return ""
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def _market_for(game_key: str, market: str, selection: str) -> Optional[dict]:
    for r in P.load_prices():
        if (f"{r['away']}@{r['home']}" == game_key and r["market"] == market
                and r["selection"] == selection):
            return r
    return None


def _clamp(x: float, lim: float) -> float:
    return max(-lim, min(lim, x))


def originate() -> List[dict]:
    ratings = team_ratings(before_week=10)
    lg = league_ppg(ratings)
    out: List[dict] = []
    for g in load_week10_slate():
        key = f"{g['away']}@{g['home']}"
        a, h = ratings.get(g["away"]), ratings.get(g["home"])
        model_status = "model_output"
        flags = []
        fair_home_line = fair_total = None
        fair_home_prob = None
        if a and h:
            # Expected points for each side, no HFA, no opponent adjustment.
            exp_home = 0.5 * (h["pf_pg"] + a["pa_pg"]) + PARAMS["home_field_points"] / 2
            exp_away = 0.5 * (a["pf_pg"] + h["pa_pg"]) - PARAMS["home_field_points"] / 2
            # Margin is from the home side: positive means the home team is the
            # stronger side. The QUOTE we publish is that team's own line, which
            # carries the opposite sign (a 7-point favourite is quoted -7).
            fair_margin_home = exp_home - exp_away
            fair_home_line = _clamp(round(-fair_margin_home * 2) / 2.0,
                                    PARAMS["max_abs_fair_spread"])
            fair_total = round(exp_home + exp_away, 1)
            if abs(fair_total - lg * 2) > PARAMS["max_fair_total_deviation"]:
                flags.append("F4-F08_total_outside_declared_band")
            fair_home_prob = win_prob_from_spread(fair_margin_home)
        else:
            flags.append("F4-F07_team_unrated_insufficient_games")

        # ---- 1. SIDE -----------------------------------------------------
        side = _market_for(key, "spread", g["home"])
        fair_line = "" if fair_home_line is None else f"{fair_home_line:+g}"
        mkt_line = "" if side is None else side["close_line"]
        diff_points = ""
        if fair_home_line is not None and mkt_line != "":
            # Signed from the home side: + means the model rates the home team
            # stronger (more favourable) than the market's own quote for it.
            diff_points = f"{fair_home_line - float(mkt_line):+g}"
        mkt_px = "" if side is None else side["close_price"]
        mkt_prob = ""
        if side is not None and side["close_price"] != "":
            other = _market_for(key, "spread", g["away"])
            if other is not None and other["close_price"] != "":
                # De-vig the two-way spread market, then take the home side.
                p_home, _ = P.devig_two_way(int(side["close_price"]), int(other["close_price"]))
                mkt_prob = f"{p_home:.4f}"
        out.append({
            "market_id": f"{key}-side",
            "game_key": key, "week": 10, "kickoff_et": "",
            "away": g["away"], "home": g["home"], "market": "side",
            "origination_order": 1, "selection": g["home"],
            "fair_line": fair_line,
            "fair_prob": "" if fair_home_prob is None else f"{fair_home_prob:.4f}",
            "market_line": mkt_line,
            "market_price_american": mkt_px,
            "market_implied_prob": mkt_prob,
            "difference_points": diff_points,
            "difference_prob": ("" if fair_home_prob is None or mkt_prob == ""
                                else f"{fair_home_prob - float(mkt_prob):+.4f}"),
            "direction": ("" if diff_points == "" else
                          ("model_favours_home" if float(diff_points) > 0 else
                           ("model_favours_away" if float(diff_points) < 0 else "agree"))),
            "edge_vs_close_points": "",
            "beat_close": "",
            "model_status": model_status,
            "market_status": "verified" if mkt_line != "" else "unverified",
            "flags": ";".join(flags) if flags else "",
            "results_source_url": "",
            "price_source_url": "" if side is None else side["source_url"],
        })

        # ---- 2. TOTAL ----------------------------------------------------
        over = _market_for(key, "total", "over")
        under = _market_for(key, "total", "under")
        tot_mkt = "" if over is None else over["close_line"]
        tot_px = "" if over is None else over["close_price"]
        tot_prob = ""
        if over is not None and under is not None and over["close_price"] != "" and under["close_price"] != "":
            p_over, _ = P.devig_two_way(int(over["close_price"]), int(under["close_price"]))
            tot_prob = f"{p_over:.4f}"
        tot_diff = ""
        if fair_total is not None and tot_mkt != "":
            tot_diff = f"{fair_total - float(tot_mkt):+g}"
        out.append({
            "market_id": f"{key}-total",
            "game_key": key, "week": 10, "kickoff_et": "",
            "away": g["away"], "home": g["home"], "market": "total",
            "origination_order": 2, "selection": "over",
            "fair_line": "" if fair_total is None else f"{fair_total:g}",
            "fair_prob": ("" if fair_total is None or tot_mkt == "" else
                          f"{1.0 - _norm_cdf((float(tot_mkt) - fair_total) / PARAMS['sigma_total']):.4f}"),
            "market_line": tot_mkt,
            "market_price_american": tot_px,
            "market_implied_prob": tot_prob,
            "difference_points": tot_diff,
            "difference_prob": "",
            "direction": ("" if tot_diff == "" else
                          ("model_above_market" if float(tot_diff) > 0 else
                           ("model_below_market" if float(tot_diff) < 0 else "agree"))),
            "edge_vs_close_points": "",
            "beat_close": "",
            "model_status": model_status,
            "market_status": "verified" if tot_mkt != "" else "unverified",
            "flags": ";".join(flags) if flags else "",
            "results_source_url": "",
            "price_source_url": "" if over is None else over["source_url"],
        })

        # ---- 3. MONEYLINE ------------------------------------------------
        ml_home = _market_for(key, "moneyline", g["home"])
        ml_away = _market_for(key, "moneyline", g["away"])
        fair_price = ""
        if fair_home_prob is not None:
            allowed_scale = (fair_home_line is not None
                             and abs(fair_home_line) <= PARAMS["max_abs_fair_spread"])
            fair_price = spread_to_price(fair_home_prob) if allowed_scale else ""
        mkt_ml = "" if ml_home is None else ml_home["close_price"]
        mkt_ml_prob = ""
        if (ml_home is not None and ml_away is not None
                and ml_home["close_price"] != "" and ml_away["close_price"] != ""):
            p_home, _ = P.devig_two_way(int(ml_home["close_price"]), int(ml_away["close_price"]))
            mkt_ml_prob = f"{p_home:.4f}"
        out.append({
            "market_id": f"{key}-moneyline",
            "game_key": key, "week": 10, "kickoff_et": "",
            "away": g["away"], "home": g["home"], "market": "moneyline",
            "origination_order": 3, "selection": g["home"],
            "fair_line": fair_price,
            "fair_prob": "" if fair_home_prob is None else f"{fair_home_prob:.4f}",
            "market_line": mkt_ml,
            "market_price_american": mkt_ml,
            "market_implied_prob": mkt_ml_prob,
            "difference_points": "",
            "difference_prob": ("" if fair_home_prob is None or mkt_ml_prob == ""
                                else f"{fair_home_prob - float(mkt_ml_prob):+.4f}"),
            "direction": "",
            "edge_vs_close_points": "",
            "beat_close": "",
            "model_status": model_status,
            "market_status": "verified" if mkt_ml != "" else "unverified",
            "flags": ";".join(flags) if flags else "",
            "results_source_url": "",
            "price_source_url": "" if ml_home is None else ml_home["source_url"],
        })
    # Enforce the required order in the file itself.
    out.sort(key=lambda r: (r["origination_order"], r["game_key"]))
    return out


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _attach_results(rows: List[dict]) -> List[dict]:
    """Stamp the verified results URL on any game that has already been played.

    A market that has settled can be graded, so its row must carry the link that
    proves the score. A market that has not settled gets a blank, never a
    placeholder URL: a "source" pointing at a page that does not yet contain the
    result would be worse than an honest blank.
    """
    from . import results as R
    by_join = {R.join_key(r): r for r in R.result_rows()}
    for r in rows:
        res = by_join.get(r["game_key"])
        if res is not None:
            r["results_source_url"] = res["result_source_url"]
    return rows


def write_all() -> List[dict]:
    rows = _attach_results(originate())
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "originated_markets.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MARKET_FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Fair-vs-market view: the three required columns side by side, per market.
    with open(os.path.join(OUT, "fair_vs_market.csv"), "w", newline="", encoding="utf-8") as fh:
        fields = ["market_id", "game_key", "market", "origination_order",
                  "model_fair_line", "market_line", "difference", "difference_units",
                  "model_prob", "market_prob", "probability_difference",
                  "model_status", "market_status", "flags"]
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({
                "market_id": r["market_id"],
                "game_key": r["game_key"],
                "market": r["market"],
                "origination_order": r["origination_order"],
                "model_fair_line": r["fair_line"],
                "market_line": r["market_line"],
                "difference": r["difference_points"] or r["difference_prob"],
                "difference_units": "points" if r["difference_points"] else ("probability" if r["difference_prob"] else ""),
                "model_prob": r["fair_prob"],
                "market_prob": r["market_implied_prob"],
                "probability_difference": r["difference_prob"],
                "model_status": r["model_status"],
                "market_status": r["market_status"],
                "flags": r["flags"],
            })
    return rows
