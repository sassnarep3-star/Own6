"""Combo and parlay dependence analysis.

This module answers, with real historical games, the question a combo bettor must
answer before multiplying anything: **are the legs of this combo independent?**

Three concrete studies, all re-runnable offline:

  C1  Same-game, same-market-type combos: "home covers the spread AND the total goes
      over" — 2x2 table over every historical game with a closing line. Reports phi,
      the joint/independence ratio, the Frechet feasible interval, and a
      slate-clustered interval. If the interval excludes 0, independence multiplication
      is *disproven* for that combo and must not be used.

  C2  Cross-game parlays on one slate: two legs from different games. Because the legs
      cannot be dependent through game mechanics, the test is a baseline for how much
      apparent dependence sampling noise creates at real sample sizes.

  C3  Correlation between game margin and game total (a classic dependence source:
      blowouts are not independent of scoring level), reported with n and interval.
"""
from __future__ import annotations

import itertools

import numpy as np

from . import correlation


def _spread_cover(home_margin: float, home_spread: float) -> bool | None:
    """True if the home side covers. None on a push."""
    v = home_margin + home_spread
    if v == 0:
        return None
    return v > 0


def _with_market(g: dict) -> dict | None:
    """Normalise a raw game row to home-perspective market fields (or None)."""
    try:
        spread = g.get("market_spread")
        total = g.get("market_total")
        if spread in (None, ""):
            spread = -float(g["spread_line"])      # nflverse stores home-favoured as positive
        if total in (None, ""):
            total = float(g["total_line"])
        return {**g, "market_spread": float(spread), "market_total": float(total)}
    except (KeyError, TypeError, ValueError):
        return None


def c1_same_game_cover_over(games: list[dict]) -> dict:
    games = [x for x in (_with_market(g) for g in games) if x]
    rows = []
    for g in games:
        if not g.get("home_score") or not g.get("market_spread") or not g.get("market_total"):
            continue
        hm = float(g["home_score"]) - float(g["away_score"])
        cover = _spread_cover(hm, float(g["market_spread"]))
        total = float(g["home_score"]) + float(g["away_score"])
        line = float(g["market_total"])
        if cover is None or total == line:
            continue
        over = total > line
        rows.append((int(cover), int(over), g["gameday"]))
    if len(rows) < 50:
        return {"n": len(rows), "available": False}
    cover = np.array([r[0] for r in rows], dtype=float)
    over = np.array([r[1] for r in rows], dtype=float)
    cl = np.array([r[2] for r in rows])
    r = correlation.phi(cover, over)
    ci = correlation.cluster_bootstrap_ci(
        np.arange(len(rows), dtype=float), cl,
        lambda idx: correlation.phi(cover[idx.astype(int)], over[idx.astype(int)]))
    p_cover, p_over = float(cover.mean()), float(over.mean())
    joint = float((cover * over).mean())
    lo, hi = correlation.frechet_bounds(p_cover, p_over)
    return {
        "available": True, "n": len(rows), "clusters": int(len(set(cl))),
        "p_cover": p_cover, "p_over": p_over,
        "joint_observed": joint, "joint_if_independent": p_cover * p_over,
        "ratio_observed_to_independent": joint / (p_cover * p_over) if p_cover * p_over else None,
        "phi": r, "phi_ci": ci, "fisher_ci": correlation.fisher_z_ci(r, len(rows)) if r is not None else None,
        "frechet_bounds": (lo, hi), "fisher_exact": correlation.independence_test(cover, over),
        "verdict": ("dependence supported (CI excludes 0) — do not multiply"
                    if ci and (ci[0] > 0 or ci[1] < 0)
                    else "independence not rejected — multiplication still disclosed, not assumed"),
    }


def c2_cross_game_pairs(games: list[dict], seed: int = 20261112) -> dict:
    games = [x for x in (_with_market(g) for g in games) if x]
    by_slate: dict[str, list[dict]] = {}
    for g in games:
        if g.get("home_score") and g.get("market_spread"):
            by_slate.setdefault(g["gameday"], []).append(g)
    rng = np.random.default_rng(seed)
    pair_rows = []
    for slate, gs in sorted(by_slate.items()):
        if len(gs) < 2:
            continue
        a, b = rng.choice(len(gs), size=2, replace=False)
        ga, gb = gs[int(a)], gs[int(b)]
        ha = float(ga["home_score"]) - float(ga["away_score"]) + float(ga["market_spread"])
        hb = float(gb["home_score"]) - float(gb["away_score"]) + float(gb["market_spread"])
        if ha == 0 or hb == 0:
            continue
        pair_rows.append((int(ha > 0), int(hb > 0), slate))
    if len(pair_rows) < 50:
        return {"available": False, "n": len(pair_rows)}
    a = np.array([r[0] for r in pair_rows], dtype=float)
    b = np.array([r[1] for r in pair_rows], dtype=float)
    cl = np.array([r[2] for r in pair_rows])
    r = correlation.phi(a, b)
    ci = correlation.cluster_bootstrap_ci(np.arange(len(a), dtype=float), cl,
                                         lambda idx: correlation.phi(a[idx.astype(int)], b[idx.astype(int)]))
    return {"available": True, "n": len(pair_rows), "clusters": int(len(set(cl))),
            "phi": r, "phi_ci": ci, "fisher_exact": correlation.independence_test(a, b),
            "note": "Cross-game legs cannot share game mechanics; any apparent dependence here is noise."}


def c3_margin_total(games: list[dict]) -> dict:
    m, t, cl = [], [], []
    for g in games:
        if not g.get("home_score"):
            continue
        m.append(abs(float(g["home_score"]) - float(g["away_score"])))
        t.append(float(g["home_score"]) + float(g["away_score"]))
        cl.append(g["gameday"])
    if len(m) < 50:
        return {"available": False, "n": len(m)}
    m = np.array(m, dtype=float)
    t = np.array(t, dtype=float)
    cl = np.array(cl)
    r = correlation.pearson(m, t)
    ci = correlation.cluster_bootstrap_ci(np.arange(len(m), dtype=float), cl,
                                         lambda idx: correlation.pearson(m[idx.astype(int)], t[idx.astype(int)]))
    return {"available": True, "n": len(m), "r": r, "clustered_ci": ci, "fisher_ci": correlation.fisher_z_ci(r, len(m)),
            "interpretation": "Absolute margin vs total points scored, all games in the window."}


def c4_rating_split_half(season_pairs: list[tuple[str, float]]) -> dict:
    """Reliability of team ratings: correlation of a team's rating in one window vs the next."""
    if len(season_pairs) < 30:
        return {"available": False, "n": len(season_pairs)}
    a = np.array([p[1] for p in season_pairs[0::2]], dtype=float)
    b = np.array([p[1] for p in season_pairs[1::2]], dtype=float)
    n = min(len(a), len(b))
    r = correlation.pearson(a[:n], b[:n])
    return {"available": True, "n": n, "r": r, "fisher_ci": correlation.fisher_z_ci(r, n) if r is not None else None,
            "required_n_for_r_0_3": correlation.required_n_for_r(0.3)}


def combo_price_table(p_leg1: float, p_leg2: float, rho: float | None, offered_decimals: list[float]) -> list[dict]:
    """Price a 2-leg combo three ways and show what the payout must clear."""
    lo, hi = correlation.frechet_bounds(p_leg1, p_leg2)
    copula = correlation.joint_from_copula(p_leg1, p_leg2, rho) if rho is not None else None
    rows = []
    for label, p in (("independence (only if tested)", p_leg1 * p_leg2),
                     ("copula with measured rho", copula),
                     ("Frechet max (best case)", hi),
                     ("Frechet min (worst case)", lo)):
        if p is None:
            rows.append({"method": label, "joint": None, "fair_american": None, "ev_at_offered": None})
            continue
        if p <= 0:
            fair = None
        elif p >= 0.5:
            fair = round(-100.0 * p / (1.0 - p), 0)
        else:
            fair = round(100.0 * (1.0 - p) / p, 0)
        rows.append({"method": label, "joint": p, "fair_american": fair,
                     "ev_at_offered": {d: p * d - 1.0 for d in offered_decimals}})
    return rows
