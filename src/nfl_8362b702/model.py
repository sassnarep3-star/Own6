"""Pre-registered singles-only shadow baseline (S8362-SHADOW-v1).

The specification below is the registration. It was frozen in git before any
week-11 kickoff (registration commit recorded by ``prereg.py``; first week-11
kickoff is 2026-11-19 20:15 ET). Forecast rows store the probability AND the
complete input vector used to produce it.

Team strength (per club, from the 136-game corpus only):
    S_t = (PF_t - PA_t) / G_t          net points per game
Game margin forecast (home perspective):
    m = S_home - S_away + HFA          HFA = corpus mean home margin,
                                       0 for neutral-site games (the page's own
                                       event mark names the international city)
Probability:
    p_home_win = Phi(m / sigma)        sigma = sd of walk-forward residuals
                                       over corpus weeks 2-9 (out-of-sample)
Ties score 0.5 in every proper score. Units are probabilities only; no price,
stake, payout or ROI column exists in this model's outputs.
"""
from __future__ import annotations

import math

from .capture import WEEK11_GAMES
from .results import corpus_rows

MODEL_ID = "S8362-SHADOW-v1"
SPEC_TEXT = (
    "S_t=(PF-PA)/G from the 136-game corpus (weeks 1-9); "
    "m = S_home - S_away + HFA; HFA = corpus mean home margin, 0 on "
    "neutral-site games (page event mark names the city); "
    "p_home = Phi(m/sigma); sigma = sd of weeks 2-9 walk-forward residuals; "
    "ties score 0.5; no price input; singles only."
)


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def ratings(games):
    """S_t = net points per game over the given game list."""
    pf, pa, g = {}, {}, {}
    for gm in games:
        for t, s, o in ((gm["away"], gm["away_score"], gm["home_score"]),
                        (gm["home"], gm["home_score"], gm["away_score"])):
            pf[t] = pf.get(t, 0) + s
            pa[t] = pa.get(t, 0) + o
            g[t] = g.get(t, 0) + 1
    return {t: {"pf": pf[t], "pa": pa[t], "g": g[t],
                "off_ppg": pf[t] / g[t], "def_ppg": pa[t] / g[t],
                "strength": (pf[t] - pa[t]) / g[t]} for t in g}


def corpus_hfa(games):
    """Mean home margin over non-neutral corpus games (derived value)."""
    hm = [g["margin_home"] for g in games if not g["event_mark_on_card"]]
    return sum(hm) / len(hm), len(hm)


def is_neutral(game) -> bool:
    return bool(game.get("event_mark_on_card"))


def forecast(game, rat, hfa, sigma):
    """Probability + full input vector for one game (home perspective)."""
    sh, sa = rat[game["home"]]["strength"], rat[game["away"]]["strength"]
    hfa_used = 0.0 if is_neutral(game) else hfa
    m = sh - sa + hfa_used
    p = _phi(m / sigma)
    return {
        "game_id": game["game_id"], "away": game["away"], "home": game["home"],
        "p_home_win": p, "p_away_win": 1.0 - p,
        "inputs": {
            "s_home": sh, "s_away": sa, "hfa_applied": hfa_used,
            "hfa_corpus": hfa, "sigma": sigma, "margin_hat": m,
            "home_pf": rat[game["home"]]["pf"], "home_pa": rat[game["home"]]["pa"],
            "home_g": rat[game["home"]]["g"], "away_pf": rat[game["away"]]["pf"],
            "away_pa": rat[game["away"]]["pa"], "away_g": rat[game["away"]]["g"],
            "neutral_site": is_neutral(game),
        },
    }


def walk_forward(games):
    """Rolling re-fit: forecast week k with ratings fit on weeks < k.

    Week 1 games have no prior data and are skipped (documented). Returns
    forecast rows for weeks 2-9 with their realised outcomes — BACKTEST rows.
    """
    out = []
    weeks = sorted({g["week"] for g in games})
    for k in weeks[1:]:
        train = [g for g in games if g["week"] < k]
        rat = ratings(train)
        hfa, _ = corpus_hfa(train)
        prior = [g for g in games if g["week"] < k]
        # sigma from one-step residuals computed the same way on prior weeks
        sig = residual_sigma(prior, rat, hfa) or 13.0
        for g in games:
            if g["week"] != k:
                continue
            f = forecast(g, rat, hfa, sig)
            home_win = g["home_score"] > g["away_score"]
            tie = g["home_score"] == g["away_score"]
            y = 1.0 if home_win else (0.5 if tie else 0.0)
            f["outcome_home"] = y
            f["backtest"] = True
            out.append(f)
    return out


def residual_sigma(prior, rat, hfa):
    if not prior:
        return None
    res = []
    for g in prior:
        if g["home"] not in rat or g["away"] not in rat:
            continue
        mhat = rat[g["home"]]["strength"] - rat[g["away"]]["strength"] + (
            0.0 if is_neutral(g) else hfa)
        res.append(g["margin_home"] - mhat)
    if len(res) < 4:
        return None
    mu = sum(res) / len(res)
    var = sum((r - mu) ** 2 for r in res) / (len(res) - 1)
    return math.sqrt(var)


def week11_forecasts():
    """Prospective forecasts for the week-11 slate, fit on the 136-game corpus.

    These rows were produced before any week-11 kickoff. They belong on the
    leaderboard as registered prospective entries awaiting settlement; the
    walk-forward rows never do.
    """
    games = corpus_rows()
    rat = ratings(games)
    hfa, hfa_n = corpus_hfa(games)
    sig = residual_sigma(games, rat, hfa)
    out = []
    for gid, slug, date, kickoff, network, away, home, ar, hr, mark, url in WEEK11_GAMES:
        game = {"game_id": gid, "away": away, "home": home,
                "event_mark_on_card": mark}
        f = forecast(game, rat, hfa, sig)
        f["backtest"] = False
        f["kickoff_on_card"] = f"{date} {kickoff}"
        f["game_page_url"] = url
        out.append(f)
    return out, {"hfa": hfa, "hfa_n": hfa_n, "sigma": sig}
