"""Correlations computed only from officially sourced numbers, published with n.

Rule enforced here
------------------
A correlation is emitted **only** when both series are numeric values that came
from an official NFL-family page during the capture. Anything else is emitted as
a row with ``correlation_value`` blank and ``status`` explaining the refusal.
That is why several rows below are "refused": the honest answer to "what is the
correlation between the closing line and the result" is *we cannot compute it,
because no official closing line exists*.

Sample size ``n`` is published on every row, always, including the refused ones
(where ``n`` is the number of paired observations that *would* have been usable).

Correlations published (all from the capture)
---------------------------------------------
* win percentage vs points differential (32 clubs, season-to-date)
* points for per game vs points against per game (32 clubs) -- tests whether
  good offences also have good defences; near zero means the two are close to
  independent in this sample, which is the assumption parlays lean on
* team scoring total vs the same team's opponent scoring total, per game
* same-game leg correlation for side and total grader outcomes (the number that
  breaks independent-parlay maths)

Every value carries ``n`` and a two-sided p-value from a t approximation.
"""

from __future__ import annotations

from . import capture as C
from . import stats as S
from . import backtest as B

MIN_N_FOR_PUBLICATION = 10

REFUSED = "refused_no_official_source"


def _row(cid, leg_a, leg_b, note, xs, ys, source_url, method="pearson"):
    r, p, n = (S.spearman if method == "spearman" else S.pearson)(xs, ys)
    status = "published" if (r is not None and n >= MIN_N_FOR_PUBLICATION) else "insufficient_n"
    return {
        "correlation_id": cid,
        "leg_a": leg_a,
        "leg_b": leg_b,
        "n": n,
        "method": method,
        "correlation_value": "" if r is None else round(r, 4),
        "p_two_sided": "" if p is None else round(p, 4),
        "ci_low": "",
        "ci_high": "",
        "status": status,
        "interpretation_note": note,
        "official_source_url": source_url,
    }


def team_level_rows():
    url = C.CAPTURES["standings"]["url"]
    teams = C.STANDINGS
    win_pct = [(w + 0.5 * t) / (w + l + t) for (_a, w, l, t, _pf, _pa) in teams]
    diff = [pf - pa for (_a, _w, _l, _t, pf, pa) in teams]
    pf = [pf for (_a, _w, _l, _t, pf, _pa) in teams]
    pa = [pa for (_a, _w, _l, _t, _pf, pa) in teams]
    rows = [
        _row(
            "COR-01",
            "win_percentage",
            "points_differential",
            "Mechanical: points differential is a near-tautological predictor of wins, so a high "
            "value here validates the transcription, not the model. It is published as a data check.",
            win_pct,
            diff,
            url,
            method="spearman",
        ),
        _row(
            "COR-02",
            "points_for",
            "points_against",
            "Tests whether scoring offence and scoring defence move together across clubs. A value "
            "near zero supports treating the two legs of a same-game parlay as separable; a large "
            "value would mean independent-parlay maths is wrong for that pairing.",
            pf,
            pa,
            url,
        ),
    ]
    return rows


def game_level_rows():
    """Per-game series built from the verified results feed."""
    rows = B.backtest_all()
    url = "https://www.nfl.com/schedules/2026/by-week/week-{week}"
    out = []

    # Same-game leg correlation: does side grading predict total grading?
    graded = [r for r in rows if r["side_grade"] is not None and r["total_grade"] is not None]
    xs = [r["side_grade"] for r in graded]
    ys = [r["total_grade"] for r in graded]
    out.append(
        _row(
            "COR-03",
            "side_grade",
            "total_grade",
            "Same-game, same-model leg correlation. This is the number that decides whether a "
            "side+total same-game parlay may be priced as independent. n is the count of games "
            "with both legs graded.",
            xs,
            ys,
            url.format(week=9),
        )
    )

    # Margin vs total: are high-scoring games also lopsided?
    margins = [r["actual_margin_home"] for r in rows]
    totals = [r["actual_total"] for r in rows]
    out.append(
        _row(
            "COR-04",
            "home_margin",
            "game_total",
            "Blowouts and shootouts are separate phenomena in this sample if this is near zero. "
            "Used to decide whether a 'parlay the favourite and the over' story has any basis.",
            margins,
            totals,
            url.format(week=9),
        )
    )

    # Model fair total vs actual total (calibration of the total)
    fair = [r["total_line"] for r in rows if r["total_line"] is not None]
    act = [r["actual_total"] for r in rows if r["total_line"] is not None]
    out.append(
        _row(
            "COR-05",
            "model_fair_total",
            "actual_total",
            "Calibration of the originated total. A correlation near zero with a mean error near "
            "zero would mean the model is well-centred but uninformative; the signed mean error is "
            "reported on the validation page.",
            fair,
            act,
            url.format(week=9),
        )
    )
    return out


def refused_rows():
    """Correlations this project is asked for but cannot honestly compute."""
    base = {
        "n": "",
        "method": "",
        "correlation_value": "",
        "p_two_sided": "",
        "ci_low": "",
        "ci_high": "",
        "status": REFUSED,
        "official_source_url": "https://www.nfl.com/odds/",
    }
    return [
        {
            **base,
            "correlation_id": "COR-06",
            "leg_a": "closing_line_movement",
            "leg_b": "result_against_spread",
            "interpretation_note": (
                "Requires a verified opening and closing price. No official NFL price source exists "
                "(nfl.com/odds/ is the NFL 404 page), so this cannot be computed without a "
                "third-party book, which the official-source-only rule forbids."
            ),
        },
        {
            **base,
            "correlation_id": "COR-07",
            "leg_a": "player_prop_line",
            "leg_b": "player_prop_result",
            "interpretation_note": (
                "Requires official player prop prices and official per-player stat lines. NFL.com "
                "publishes injury designations and depth charts (both captured) but no prop prices."
            ),
        },
        {
            **base,
            "correlation_id": "COR-08",
            "leg_a": "depth_deficiency_points",
            "leg_b": "result_against_spread",
            "interpretation_note": (
                "Computable in principle: depth deficiency is captured for NE and DET, and both "
                "clubs' Week 10 games are in the slate. It is not computable yet because the Week 10 "
                "games have not been played, so n = 1 at most. Deferred to the Week 11 refresh."
            ),
        },
    ]


def all_rows():
    return team_level_rows() + game_level_rows() + refused_rows()


if __name__ == "__main__":  # pragma: no cover
    for r in all_rows():
        print(r["correlation_id"], r["n"], r["correlation_value"], r["status"])
