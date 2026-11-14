"""Walk-forward backtest, price-snapshot store and verified-results feed.

Three separate concerns live here because they are useless apart:

``price snapshot store``
    Opening and closing numbers for every originated market. The store is real
    (it has a schema, a row per originated market, an opening row and a closing
    row, and a status field), but every price cell is blank because no official
    NFL price source exists. See ``price_snapshot_rows``.

``verified results feed``
    Final scores transcribed from NFL.com schedule pages. This is the piece that
    makes ROI computable *at all*: without a verified result there is no
    outcome to score. ``results_rows`` emits one row per captured game with the
    official URL it came from.

``walk-forward backtest``
    For week w, originate using only weeks < w, then grade against the verified
    result. No leakage: ``season_totals(..., before_week=w)`` is the only path
    into the model.

The ROI figures are computed against the model's own fair line, at a declared
flat stake with declared -110 pricing, because no official market line exists.
This measures **model calibration**, and is labelled that way in every table.
"""

from __future__ import annotations

import itertools

from . import capture as C
from . import model as M
from . import stats as S

FLAT_STAKE = 1.0
AMERICAN_PRICE = -110  # declared convention, not an observed market price
PAYOUT_PER_UNIT = 100.0 / 110.0  # 0.909090...

BACKTEST_WEEKS = [5, 6, 7, 8, 9]  # weeks with >=4 prior games per team


def results_rows():
    """Verified results feed: one row per captured game."""
    rows = []
    for week, away, home, as_, hs, date, note in C.GAMES:
        url = "https://www.nfl.com/schedules/2026/by-week/week-%d" % week
        played = as_ is not None and hs is not None
        rows.append(
            {
                "game_id": "R%d-%s-%s" % (week, away, home),
                "season": 2026,
                "week": week,
                "game_date": date,
                "away_team": away,
                "home_team": home,
                "away_score": "" if not played else as_,
                "home_score": "" if not played else hs,
                "total_points": "" if not played else as_ + hs,
                "home_margin": "" if not played else hs - as_,
                "winner": ("" if not played else (home if hs > as_ else away if as_ > hs else "TIE")),
                "result_status": "final_verified" if played else "not_rendered",
                "official_source_url": url,
                "retrieved_utc": C.CAPTURE_DATE,
                "note": note,
            }
        )
    return rows


def backtest_week(week):
    """Originate every completed game of ``week`` from data strictly before it."""
    agg, _ = M.season_totals(C.GAMES, before_week=week)
    out = []
    for w, away, home, as_, hs, date, _note in C.GAMES:
        if w != week or as_ is None or hs is None:
            continue
        m = M.originate_game(agg, away, home)
        margin = hs - as_
        total = as_ + hs
        row = {
            "week": week,
            "game_date": date,
            "away": away,
            "home": home,
            "away_score": as_,
            "home_score": hs,
            "actual_total": total,
            "actual_margin_home": margin,
        }
        for market in ("side", "total"):
            line = m[market]["model_fair_line"]
            g = None if line is None else M.grade(market, line, margin, total)
            row[market + "_line"] = line
            row[market + "_grade"] = g
        p_home = m["moneyline"].get("model_home_win_prob")
        row["ml_prob_home"] = p_home
        row["ml_pick"] = None if p_home is None else ("home" if p_home > 0.5 else "away")
        if row["ml_pick"] is None or margin == 0:
            row["ml_grade"] = None
        else:
            picked_home = row["ml_pick"] == "home"
            won = (margin > 0) if picked_home else (margin < 0)
            row["ml_grade"] = 1 if won else 0
        row["ml_brier"] = None if p_home is None else M.grade_ml(p_home, margin > 0)
        out.append(row)
    return out


def backtest_all():
    rows = []
    for w in BACKTEST_WEEKS:
        rows.extend(backtest_week(w))
    return rows


def summarize(grades, price_applicable=True):
    """Record, win rate, Wilson interval, one-sided p and flat-stake ROI.

    ``price_applicable=False`` (used for the moneyline) blanks every money
    column. A moneyline cannot be priced at the flat -110 spread convention:
    a -150 favourite and a +120 underdog are not the same bet, and this capture
    contains no observed moneyline price. Reporting a -110 ROI for the
    moneyline would be a fabricated number, so it is left blank.
    """
    gs = [g for g in grades if g is not None]
    n = len(gs)
    pushes = len([g for g in grades if g is None])
    wins = sum(gs)
    losses = n - wins
    lo, hi = S.wilson_interval(wins, n) if n else (None, None)
    p = S.binomial_one_sided_p(wins, n) if n else None
    profit = wins * PAYOUT_PER_UNIT - losses if price_applicable else None
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": None if not n else round(wins / n, 4),
        "ci_low": None if lo is None else round(lo, 4),
        "ci_high": None if hi is None else round(hi, 4),
        "p_one_sided_fair_coin": None if p is None else round(p, 4),
        "profit_units": None if profit is None or not n else round(profit, 4),
        "roi": None if profit is None or not n else round(profit / (n * FLAT_STAKE), 4),
        "price_basis": ("flat_stake_-110_declared_convention" if price_applicable
                        else "no_price_basis_moneyline"),
    }


# --------------------------------------------------------- strategy families


def strategy_results(rows):
    """Per-strategy outcomes for singles, parlays and combo families.

    ``rows`` is the output of :func:`backtest_all`. Each strategy is graded on
    its own legs; parlays are graded with the *declared independence
    assumption* and the realised leg correlation is reported separately in
    :mod:`nfl_market.correlations` so the independence claim is auditable.
    """
    families = {}

    # ---- singles: one leg per game, per market ----
    for market in M.MARKET_ORDER_PREFIX:
        key = "single_%s" % ("moneyline" if market == "ml" else market)
        families[key] = [r[market + "_grade"] for r in rows]

    # ---- two-leg parlays: side + total of the SAME game (player-prop-style
    #      same-event combo, which is where correlation actually bites) ----
    same_game_both = []
    for r in rows:
        a, b = r["side_grade"], r["total_grade"]
        if a is None or b is None:
            same_game_both.append(None)
        else:
            same_game_both.append(1 if (a == 1 and b == 1) else 0)
    families["parlay_2leg_same_game_side_total"] = same_game_both

    # ---- two-leg parlays: two singles across DIFFERENT games (near-independent) ----
    cross = []
    half = len(rows) // 2
    for i in range(half):
        a, b = rows[i]["side_grade"], rows[i + half]["side_grade"]
        if a is None or b is None:
            cross.append(None)
        else:
            cross.append(1 if (a == 1 and b == 1) else 0)
    families["parlay_2leg_cross_game_side"] = cross

    # ---- three-leg parlay across games ----
    third = len(rows) // 3
    tri = []
    for i in range(third):
        a, b, c = rows[i]["side_grade"], rows[i + third]["side_grade"], rows[i + 2 * third]["side_grade"]
        tri.append(None if None in (a, b, c) else (1 if a == b == c == 1 else 0))
    families["parlay_3leg_cross_game_side"] = tri

    return families


def family_table(rows):
    fams = strategy_results(rows)
    out = []
    for key, grades in fams.items():
        s = summarize(grades, price_applicable="moneyline" not in key)
        s["strategy_id"] = key
        out.append(s)
    return out


# -------------------------------------------------------- price snapshot store


def price_snapshot_rows(rows):
    """Opening and closing numbers for every originated market.

    Emits two rows per (game, market): one ``OPEN`` and one ``CLOSE``. All price
    fields are blank and ``snapshot_status`` records why. The row count is real,
    so coverage of the store itself is auditable even while the prices are not
    available.
    """
    out = []
    for r in rows:
        for market in ("side", "total", "moneyline"):
            ln = r.get(market + "_line")
            if market == "moneyline":
                ln = None if r.get("ml_prob_home") is None else r["ml_pick"]
            out.append(
                {
                    "game_id": "R%d-%s-%s" % (r["week"], r["away"], r["home"]),
                    "market": market,
                    "model_fair_line": "" if ln is None else ln,
                    "opening_price": "",
                    "closing_price": "",
                    "price_units": "american",
                    "opening_captured_utc": "",
                    "closing_captured_utc": "",
                    "snapshot_status": M.MARKET_LINE_STATUS,
                    "status_detail": (
                        "No official NFL price source. https://www.nfl.com/odds/ returns the "
                        "NFL 404 page (captured 2026-11-14). A third-party book would breach the "
                        "project's official-source-only rule, so the cells stay blank."
                    ),
                    "official_source_url": "https://www.nfl.com/odds/",
                }
            )
    return out


# ------------------------------------------------------------- luck removal


def luck_index(grades):
    """How much of a record is explainable as coin-flip variance.

    Two views, both published:

    * ``p_fair_coin`` -- one-sided binomial p against a 50% null. Large p means
      the record is indistinguishable from luck.
    * ``luck_share`` -- ``p_fair_coin`` clipped to [0,1]. This is deliberately
      *not* a probability of luck; it is a bounded, monotone summary used only
      for ranking, and the leaderboard prints ``p`` next to it so nobody has to
      trust the summary alone.
    """
    s = summarize(grades)
    p = s["p_one_sided_fair_coin"]
    if p is None:
        return {**s, "luck_share": None, "verdict": "insufficient_sample"}
    luck = max(0.0, min(1.0, p))
    if s["n"] < 30:
        verdict = "not_decision_grade_sample_too_small"
    elif p >= 0.05:
        verdict = "indistinguishable_from_luck"
    elif p >= 0.01:
        verdict = "weak_evidence"
    else:
        verdict = "survives_fair_coin_null"
    return {**s, "luck_share": round(luck, 4), "verdict": verdict}


if __name__ == "__main__":  # pragma: no cover
    rows = backtest_all()
    print("backtest rows:", len(rows))
    for t in family_table(rows):
        print(t["strategy_id"], t["n"], t["wins"], t["win_rate"], t["p_one_sided_fair_coin"])
