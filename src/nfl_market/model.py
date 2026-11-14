"""Own-line origination and market comparison.

Design
------
The model originates three markets per game in a fixed order:

1. **Side** (spread) -- because the side is the market the model's own inputs
   (points for / points against per game, opponent adjustment) explain best.
2. **Total** (over/under) -- second, because it needs the same two inputs in a
   different combination and therefore fails for the same reason the side fails.
3. **Moneyline** -- last, because it is a monotone transform of the fair spread
   plus a win-probability function; publishing it first would hide the fact that
   it inherits every error of the side.

Every originated market is published with three physically separate columns:

``model_fair_line``   what this model says the line is
``market_line``       what the market says, or blank + an explicit reason
``difference``        ``model_fair_line - market_line``, or blank when either
                      input is blank

The market line column is blank for the whole capture. This is not a bug and it
is not an omission to be "filled in later by inference": NFL.com publishes no
line. ``https://www.nfl.com/odds/`` returns the NFL 404 page (captured in
``nfl_market.capture.CAPTURES["odds_probe"]``). Filling that column from a
non-official source would break the project's own verification rule, so the
difference column is blank and the strategy competition is reported as
"signal only, no market comparison available" rather than pretending an edge
was measured.

Point estimation
----------------
Ratings are *walk-forward*: for week ``w`` only games from weeks ``< w`` are
used. Points for / against are per-team means over those games. The fair spread
is the opponent-adjusted net-points differential, shrunk by a fixed weight
because 8-9 games of history is a very short sample and an unshrunk estimator
produces absurd spreads.
"""

from __future__ import annotations

from . import capture as C

# Fixed, declared parameters. None of these are fitted to outcomes; they are
# published so that a reader can disagree with them and re-run.
PARAMS = {
    "shrink_weight": 0.75,  # multiply the raw differential by this
    "home_field_points": 2.0,  # league-typical home advantage, declared not fitted
    "min_games_to_originate": 4,  # below this, no line is originated
    "market_line": None,  # no official NFL line exists -- see module docstring
}

MARKET_ORDER = ("side", "total", "moneyline")
MARKET_ORDER_PREFIX = ("side", "total", "ml")

MARKET_LINE_STATUS = "unverified_no_official_price_source"


def season_totals(games, before_week=None):
    """Aggregate per-team points for/against from captured game rows.

    ``games`` is the ``(week, away, home, away_score, home_score, date, note)``
    rows from :mod:`nfl_market.capture`. Games with ``None`` scores are counted
    as unplayed and excluded from the aggregate but *are* counted in
    ``unplayed`` so the caller can see them.
    """
    agg = {}
    unplayed = 0
    for week, away, home, as_, hs, _date, _note in games:
        if before_week is not None and week >= before_week:
            continue
        for team in (away, home):
            agg.setdefault(team, {"games": 0, "pf": 0, "pa": 0})
        if as_ is None or hs is None:
            unplayed += 1
            continue
        agg[away]["games"] += 1
        agg[away]["pf"] += as_
        agg[away]["pa"] += hs
        agg[home]["games"] += 1
        agg[home]["pf"] += hs
        agg[home]["pa"] += as_
    for team, row in agg.items():
        row["ppg"] = row["pf"] / row["games"] if row["games"] else None
        row["papg"] = row["pa"] / row["games"] if row["games"] else None
    return agg, unplayed


def originate_game(agg, away, home, params=None):
    """Originate side, total and moneyline for one game.

    Returns a dict with ``side``, ``total`` and ``moneyline`` sub-dicts. Each
    carries ``model_fair_line``, ``market_line`` (None -> published blank),
    ``difference`` and a status string explaining why a value is blank.
    """
    p = dict(PARAMS)
    if params:
        p.update(params)

    a, h = agg.get(away), agg.get(home)
    out = {"away": away, "home": home}

    def _blank(reason):
        return {
            "model_fair_line": None,
            "market_line": None,
            "difference": None,
            "status": reason,
        }

    if not a or not h:
        return {
            "away": away,
            "home": home,
            "side": _blank("insufficient_history_missing_team"),
            "total": _blank("insufficient_history_missing_team"),
            "moneyline": _blank("insufficient_history_missing_team"),
        }
    if min(a["games"], h["games"]) < p["min_games_to_originate"]:
        return {
            "away": away,
            "home": home,
            "side": _blank("insufficient_history_below_min_games"),
            "total": _blank("insufficient_history_below_min_games"),
            "moneyline": _blank("insufficient_history_below_min_games"),
        }

    # --- 1. SIDE -----------------------------------------------------------
    # Net points per game for each club, opponent-adjusted by simple averaging:
    # the model compares each offence with the other defence.
    a_expect = (a["ppg"] + h["papg"]) / 2.0
    h_expect = (h["ppg"] + a["papg"]) / 2.0
    raw_margin_home = (h_expect - a_expect) + p["home_field_points"]
    fair_spread_home = -raw_margin_home * p["shrink_weight"]
    side = {
        "model_fair_line": round(fair_spread_home, 2),
        "market_line": p["market_line"],
        "difference": None if p["market_line"] is None else round(fair_spread_home - p["market_line"], 2),
        "status": "originated_signal_only" if p["market_line"] is None else "originated_compared",
        "expected_away_points": round(a_expect, 2),
        "expected_home_points": round(h_expect, 2),
    }

    # --- 2. TOTAL ----------------------------------------------------------
    fair_total = a_expect + h_expect
    total = {
        "model_fair_line": round(fair_total, 2),
        "market_line": None,
        "difference": None,
        "status": "originated_signal_only",
    }

    # --- 3. MONEYLINE ------------------------------------------------------
    # Normal approximation with a declared sigma. sigma is the residual standard
    # deviation of NFL game margins and is declared, not fitted here.
    sigma = 13.5
    from .stats import norm_cdf

    p_home = norm_cdf(raw_margin_home / sigma)
    if p_home <= 0.0 or p_home >= 1.0:
        ml = _blank("degenerate_probability")
    else:
        ml = {
            "model_fair_line": _prob_to_american(p_home),
            "model_home_win_prob": round(p_home, 4),
            "market_line": None,
            "difference": None,
            "status": "originated_signal_only",
        }

    out.update({"side": side, "total": total, "moneyline": ml})
    return out


def _prob_to_american(p):
    """Convert a win probability to American odds (no vig applied)."""
    if p <= 0.5:
        return round(-100.0 * (1 - p) / p, 0)
    return round(100.0 * p / (1 - p), 0)


def originate_slate(games, slate, before_week):
    """Originate every game on ``slate`` using only prior-week results."""
    agg, unplayed = season_totals(games, before_week=before_week)
    rows = []
    for week, day, date, kickoff, network, away, home in slate:
        model = originate_game(agg, away, home)
        rows.append(
            {
                "week": week,
                "day": day,
                "date": date,
                "kickoff_et": kickoff,
                "network": network,
                "away": away,
                "home": home,
                "model": model,
            }
        )
    return rows, agg, unplayed


def grade(market, line, actual_margin_home, actual_total):
    """Grade one originated market against the verified final score.

    No vig, no stake: this returns 1 for a win, 0 for a loss and ``None`` for a
    push. The ROI columns downstream apply the declared flat-stake convention.

    ``line`` is the model's own fair line. Grading against the model's own line
    measures *calibration of the model*, not profit against a bookmaker; because
    no official market line exists, this is the only honest grading available
    and it is labelled as such everywhere it appears.
    """
    if market == "side":
        home_cover = actual_margin_home + line
        if abs(home_cover) < 1e-9:
            return None
        return 1 if home_cover > 0 else 0
    if market == "total":
        over = actual_total - line
        if abs(over) < 1e-9:
            return None
        return 1 if over > 0 else 0
    raise ValueError("grade() handles side and total only; moneyline uses grade_ml")


def grade_ml(p_home, home_won):
    """Brier-style score contribution for the moneyline."""
    return (p_home - (1.0 if home_won else 0.0)) ** 2


if __name__ == "__main__":  # pragma: no cover
    agg, _ = season_totals(C.GAMES, before_week=10)
    assert len(agg) == 32, len(agg)
    g = originate_game(agg, "NE", "DET")
    assert g["side"]["model_fair_line"] is not None
    assert g["total"]["model_fair_line"] is not None
    assert g["side"]["market_line"] is None
    assert g["side"]["difference"] is None
    print("model.py self-check OK:", g["side"]["model_fair_line"], g["total"]["model_fair_line"])
