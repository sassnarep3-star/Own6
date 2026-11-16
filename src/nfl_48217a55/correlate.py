"""Correlations computed only from officially sourced numbers, with n published.

Rules enforced here:
  * every axis must be traceable to a row captured from an official page this session;
  * n is the number of paired observations actually used, and is published with the value;
  * an interval is published beside every point estimate;
  * a candidate that cannot be computed from official numbers is not estimated at all -
    it is published in `exclusions()` with the reason.

No correlation in this pack uses market prices, because no official or licensed source in
this environment publishes them.
"""

from __future__ import annotations

from . import capture as C
from . import injuries as IN
from . import model as M
from . import stats as S


def _out_counts():
    counts = {}
    for r in IN.club_rollup():
        counts[r["club"]] = r
    return counts


def _week10_pairs():
    """(club, outs, points_scored, points_allowed, margin) for the 9 completed Week 10 games."""
    counts = _out_counts()
    pairs = []
    for g in M.final_games():
        for club, own, opp in (
            (g["away"], g["away_points"], g["home_points"]),
            (g["home"], g["home_points"], g["away_points"]),
        ):
            c = counts.get(club)
            if not c:
                continue
            pairs.append(
                {
                    "club": club,
                    "outs": c["out"],
                    "questionable": c["questionable"],
                    "on_report": c["rows_on_report"],
                    "dnp": c["dnp"],
                    "points_for": own,
                    "points_against": opp,
                    "margin": own - opp,
                }
            )
    return pairs


def correlations(pit_rows):
    """Return the list of measured correlation rows."""
    out = []

    pairs = _week10_pairs()
    if len(pairs) >= 3:
        for label, ykey in (
            ("Week 10 points scored", "points_for"),
            ("Week 10 margin", "margin"),
            ("Week 10 points allowed", "points_against"),
        ):
            xs = [p[ykey] for p in pairs]
            ys = [p["outs"] for p in pairs]
            r = S.pearson(xs, ys)
            lo, hi = S.fisher_ci(r, len(pairs))
            out.append(
                {
                    "id": f"COR-{len(out) + 1:02d}",
                    "x_axis": label,
                    "y_axis": "players designated Out on the official Week 10 report",
                    "n": len(pairs),
                    "unit": "team-game",
                    "method": "Pearson r, Fisher z 95% interval",
                    "estimate": round(r, 4),
                    "ci_low": round(lo, 4),
                    "ci_high": round(hi, 4),
                    "p_value": round(S.t_pvalue_two_sided(r, len(pairs)), 4),
                    "x_source_url": C.SOURCE_URL["S2"],
                    "y_source_url": C.SOURCE_URL["S1"],
                    "caveat": "single week, 9 games; far below any threshold that would "
                              "support a feature decision",
                }
            )

    # --- season-to-date, reconstructed through Week 9 ----------------------
    counts = _out_counts()
    joined = [r for r in pit_rows if r["club"] in counts]
    if len(joined) >= 3:
        for label, key in (
            ("win percentage through Week 9", "win_pct"),
            ("net points per game through Week 9", "margin_per_game"),
        ):
            xs = [r[key] for r in joined]
            ys = [counts[r["club"]]["out"] for r in joined]
            r = S.pearson(xs, ys)
            lo, hi = S.fisher_ci(r, len(joined))
            out.append(
                {
                    "id": f"COR-{len(out) + 1:02d}",
                    "x_axis": label,
                    "y_axis": "players designated Out on the official Week 10 report",
                    "n": len(joined),
                    "unit": "club",
                    "method": "Pearson r, Fisher z 95% interval",
                    "estimate": round(r, 4),
                    "ci_low": round(lo, 4),
                    "ci_high": round(hi, 4),
                    "p_value": round(S.t_pvalue_two_sided(r, len(joined)), 4),
                    "x_source_url": C.SOURCE_URL["S3"],
                    "y_source_url": C.SOURCE_URL["S1"],
                    "caveat": "the Out count is a Week 10 snapshot while the record is "
                              "season-to-date; this is a contemporaneous association, not a "
                              "predictive result",
                }
            )

        xs = [r["pf_per_game"] for r in joined]
        ys = [r["win_pct"] for r in joined]
        r = S.pearson(xs, ys)
        lo, hi = S.fisher_ci(r, len(joined))
        out.append(
            {
                "id": f"COR-{len(out) + 1:02d}",
                "x_axis": "points scored per game through Week 9",
                "y_axis": "win percentage through Week 9",
                "n": len(joined),
                "unit": "club",
                "method": "Pearson r, Fisher z 95% interval",
                "estimate": round(r, 4),
                "ci_low": round(lo, 4),
                "ci_high": round(hi, 4),
                "p_value": round(S.t_pvalue_two_sided(r, len(joined)), 4),
                "x_source_url": C.SOURCE_URL["S3"],
                "y_source_url": C.SOURCE_URL["S3"],
                "caveat": "both axes are the same season's results; this is a description "
                          "of what happened, not a forecast input",
            }
        )

    return out


def designation_calibration():
    """Empirical play rate for the 'Questionable' designation.

    This is the number the brief asks for instead of a folklore percentage. It is computed
    from the only rows this session could read where an official page published both the
    designation and the resolution: the Sunday pregame page (S4).

    The sample is *not* random - it is the set of players about whom NFL.com published a
    note, which skews toward starters and toward players whose status was genuinely in
    doubt. That selection effect is stated on the row rather than corrected for, because
    no official page publishes the population of all Questionable players with outcomes.
    """
    definite = [r for r in C.WEEK10_PREGAME if r[5] in ("active", "inactive")]
    active = sum(1 for r in definite if r[5] == "active")
    n_def = len(definite)
    lo, hi = S.wilson_interval(active, n_def)
    rows = [
        {
            "designation": "Questionable",
            "sample": "official Sunday pregame page, Week 10",
            "n_published_resolutions": len(C.WEEK10_PREGAME),
            "n_definite": n_def,
            "n_active": active,
            "n_inactive": n_def - active,
            "play_rate": round(active / n_def, 4) if n_def else "",
            "ci_low": round(lo, 4),
            "ci_high": round(hi, 4),
            "method": "Wilson score interval on the definite subset",
            "selection_warning": "non-random sample: only players NFL.com wrote a note about; "
                                 "skews to starters and to genuinely doubtful cases",
            "usable_as_feature": "no",
            "blocking_gate": "G6",
            "source_url": C.SOURCE_URL["S4"],
        }
    ]
    for des in ("Out", "Doubtful"):
        rows.append(
            {
                "designation": des,
                "sample": "",
                "n_published_resolutions": "",
                "n_definite": "",
                "n_active": "",
                "n_inactive": "",
                "play_rate": "",
                "ci_low": "",
                "ci_high": "",
                "method": "",
                "selection_warning": "no official page read this session publishes a "
                                     "designation-to-outcome join for this designation",
                "usable_as_feature": "no",
                "blocking_gate": "G6",
                "source_url": C.SOURCE_URL["S4"],
            }
        )
    return rows


def exclusions():
    """Candidate correlations that were *not* estimated, and why."""
    return [
        {
            "id": "EXC-01",
            "candidate": "originated fair line vs market closing line",
            "why_not": "no official or licensed source in this environment publishes operator "
                       "prices; an estimated price would be a fabricated input",
            "what_would_clear_it": "a licensed price feed, or a written data-use agreement "
                                   "with an operator, recorded in the price-data policy",
            "source_url": C.SOURCE_URL["S2"],
        },
        {
            "id": "EXC-02",
            "candidate": "parlay leg correlation (same-game props)",
            "why_not": "requires a joint outcome sample for the same game; the pack has "
                       "game-level results only, and multiplying marginals would be invalid "
                       "under dependence",
            "what_would_clear_it": "joint settlement records for combo tickets, with the "
                                   "operator's void/push rules",
            "source_url": C.SOURCE_URL["S2"],
        },
        {
            "id": "EXC-03",
            "candidate": "injury designation -> snaps played",
            "why_not": "no snap-count source was read this session; the official roster page "
                       "publishes no snap counts and the per-club depth route is a 404",
            "what_would_clear_it": "an official snap-count source verified for all 32 clubs, "
                                   "or the club-hosted depth pages verified club by club",
            "source_url": C.SOURCE_URL["S8"],
        },
        {
            "id": "EXC-04",
            "candidate": "replacement depth tier -> points allowed",
            "why_not": "the report names no replacement and gives no depth order, so a tier "
                       "would have to be inferred from jersey number, experience or salary",
            "what_would_clear_it": "a dated, attributed depth register for all 32 clubs",
            "source_url": C.SOURCE_URL["S1"],
        },
        {
            "id": "EXC-05",
            "candidate": "closing line value vs realised return",
            "why_not": "both axes need operator prices",
            "what_would_clear_it": "same as EXC-01",
            "source_url": C.SOURCE_URL["S2"],
        },
    ]
