"""Correlations computed **only** from officially sourced numbers.

Every row published by this module carries:

* ``n``              - the number of paired observations actually used,
* ``r``              - Pearson correlation,
* ``ci_low/ci_high`` - 95% Fisher-z confidence interval,
* ``source_url``     - the official page the observations were read from.

A correlation with ``n < 30`` is published but is explicitly marked
``insufficient_n`` and must not be used to price a parlay leg.
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence

from . import dataset, model

MIN_N_FOR_PRICING = 30


def pearson(xs: Sequence[float], ys: Sequence[float]) -> Dict[str, float]:
    n = len(xs)
    if n != len(ys) or n < 3:
        return {"n": n, "r": "", "ci_low": "", "ci_high": ""}
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return {"n": n, "r": "", "ci_low": "", "ci_high": ""}
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.999999, min(0.999999, r))
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.96 * se, z + 1.96 * se
    return {"n": n, "r": round(r, 4),
            "ci_low": round(math.tanh(lo), 4), "ci_high": round(math.tanh(hi), 4)}


def _games():
    return model._games()


def build() -> List[Dict[str, object]]:
    games = _games()
    side = model.fit_side(games)
    total = model.fit_total(games)
    out: List[Dict[str, object]] = []

    def add(cid, a_name, b_name, a, b, desc, url, used_for):
        st = pearson(a, b)
        ok = "sufficient_n" if st["n"] >= MIN_N_FOR_PRICING else "insufficient_n"
        out.append({
            "correlation_id": cid, "quantity_a": a_name, "quantity_b": b_name,
            "n": st["n"], "r": st["r"], "ci95_low": st["ci_low"],
            "ci95_high": st["ci_high"], "n_status": ok,
            "what_it_means": desc, "used_for": used_for,
            "official_source_url": url,
        })
        return st

    # 1. calibration of the side model
    pred_m = [side["rate"][g["home"]] - side["rate"][g["away"]] + side["hfa"] for g in games]
    act_m = [g["margin"] for g in games]
    add("A4-C01", "originated fair margin", "verified final margin", pred_m, act_m,
        "In-sample correlation between the originated fair margin and the "
        "verified final margin. It measures fit, not predictive skill.",
        "https://www.nfl.com/scores/2026/week-1", "model fit diagnostics"),

    # 2. calibration of the total model
    pred_t = [total["rate"][g["home"]] + total["rate"][g["away"]] + total["intercept"]
              for g in games]
    act_t = [g["total"] for g in games]
    add("A4-C02", "originated fair total", "verified final total", pred_t, act_t,
        "In-sample correlation between the originated fair total and the "
        "verified final total.",
        "https://www.nfl.com/scores/2026/week-1", "model fit diagnostics")

    # 3. the parlay-critical one: margin residual vs total residual
    add("A4-C03", "margin-model residual", "total-model residual", side["residuals"], total["residuals"],
        "Correlation of the two models' errors within the same game. This is "
        "the number a same-game parlay (side + total) must be priced with; if "
        "it is positive, a favourite/over parlay is more likely than the "
        "independent-product price implies.",
        "https://www.nfl.com/scores/2026/week-1", "same-game parlay pricing")

    # 4. home score vs away score within a game
    add("A4-C04", "home team points", "away team points", [g["home_score"] for g in games], [g["away_score"] for g in games],
        "Within-game correlation of the two teams' scores. Negative values "
        "mean game script is competitive (one team's scoring suppresses the "
        "other's).",
        "https://www.nfl.com/scores/2026/week-1", "totals modelling")

    # 5/6/7. team-season relationships from the official standings
    st = dataset.standings()
    pf = [r["pf_per_game"] for r in st]
    pa = [r["pa_per_game"] for r in st]
    net = [r["net_pts_per_game"] for r in st]
    winp = [(r["w"] + 0.5 * r["t"]) / r["games_played"] for r in st]
    add("A4-C05", "points for per game", "points against per game", pf, pa,
        "Across the 32 clubs, correlation of points scored per game with "
        "points allowed per game (official standings PF/PA).",
        dataset.STANDINGS_URL, "team-strength sanity check")
    add("A4-C06", "net points per game", "winning percentage", net, winp,
        "Correlation of net points per game with winning percentage. A high "
        "value is expected and is a check that the standings were transcribed "
        "correctly.",
        dataset.STANDINGS_URL, "transcription check")
    add("A4-C07", "points for per game", "winning percentage", pf, winp,
        "Correlation of offensive scoring rate with winning percentage, "
        "compared against C08 (defensive) to show which side of the ball "
        "explains more of the standings.",
        dataset.STANDINGS_URL, "signal research")
    add("A4-C08", "points against per game", "winning percentage", pa, winp,
        "Correlation of points allowed per game with winning percentage "
        "(expected to be negative).",
        dataset.STANDINGS_URL, "signal research")

    # 9. stability of team scoring margin: first half of the captured season
    #    vs second half.  This is the 'skill vs luck' split.
    early = [g for g in games if g["week"] <= 3]
    late = [g for g in games if g["week"] >= 7]
    def margin_map(gs):
        acc = {t: [0.0, 0] for t in dataset.TEAMS}
        for g in gs:
            acc[g["home"]][0] += g["margin"]; acc[g["home"]][1] += 1
            acc[g["away"]][0] -= g["margin"]; acc[g["away"]][1] += 1
        return {t: (v[0] / v[1] if v[1] else None) for t, v in acc.items()}
    e, l = margin_map(early), margin_map(late)
    teams = sorted(t for t in dataset.TEAMS if e[t] is not None and l[t] is not None)
    add("A4-C09", "avg margin weeks 1-3", "avg margin weeks 7-9", [e[t] for t in teams], [l[t] for t in teams],
        "Split-season stability of average scoring margin (weeks 1-3 vs "
        "weeks 7-9). A low value means early-season margin is mostly noise "
        "and must not be used as a stand-alone signal.",
        "https://www.nfl.com/scores/2026/week-1", "luck removal")

    # 10. injury load vs season points allowed
    inj = dataset.injuries()
    outs = {r["team_abbr"]: 0 for r in inj}
    for r in inj:
        if r["game_status"] == "Out":
            outs[r["team_abbr"]] += 1
    pa_by = {r["team_abbr"]: r["pa_per_game"] for r in st}
    q = sorted(t for t in outs if t in pa_by)
    add("A4-C10", "players ruled Out (Week 10)", "points allowed per game", [float(outs[t]) for t in q], [pa_by[t] for t in q],
        "Correlation between the number of players ruled Out on the official "
        "Week 10 injury report and the club's season points-allowed rate. "
        "n is the number of clubs on the Week 10 report (28 of 32; the four "
        "bye clubs are not listed).",
        "https://www.nfl.com/injuries/", "injury-load signal (exploratory)")
    return out
