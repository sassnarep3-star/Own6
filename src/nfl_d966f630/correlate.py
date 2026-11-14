"""Correlations, computed only from officially sourced numbers, with n on every row.

Three rules, all enforced by the checker rather than asserted in prose:

1. **Both** axes of a published correlation must come from an official NFL page
   read this session (or from arithmetic on such numbers). No third-party
   aggregate, no model output used as if it were a measurement.
2. Every row publishes ``n``, the sample unit, the method, the Fisher confidence
   interval and the source URL of each axis. A correlation without ``n`` cannot be
   weighed, so the row would fail the gate.
3. Candidates that cannot satisfy rule 1 are published in
   ``correlation_exclusions.csv`` with the reason - a rejected candidate is a
   finding, not a gap to hide.

Parlay pricing depends on this table: two legs from the same game share the same
two team totals, and two legs from the same week share a slate. Both dependences
are measured here, then carried into ``backtest.parlay_probability`` so the
"correlation discount" on a combined price is a number from the feed rather than a
guessed 5%.
"""

from __future__ import annotations

import math

from . import capture as C
from . import results as R
from . import stats as S

MIN_N = 20  # declared floor for publishing a coefficient at all

# Rows: id, label, x_source, y_source, x_axis, y_axis, sample_unit, note
_PAIRS: list[dict[str, str]] = [
    {
        "correlation_id": "D966-COR-01",
        "x_variable": "home club points in a game",
        "y_variable": "away club points in the same game",
        "sample_unit": "game",
        "x_source": "SCHED-W7", "y_source": "SCHED-W9",
        "method": "pearson",
        "interpretation": "the dependence between the two halves of a game total; it is the quantity that makes same-game side-plus-total parlays deviate from the product of their legs",
    },
    {
        "correlation_id": "D966-COR-02",
        "x_variable": "home margin in a game",
        "y_variable": "game total of the same game",
        "sample_unit": "game",
        "x_source": "SCHED-W7", "y_source": "SCHED-W9",
        "method": "pearson",
        "interpretation": "dependence between the two legs of the most common same-game parlay; near zero means the naive product is a good baseline for that pairing",
    },
    {
        "correlation_id": "D966-COR-03",
        "x_variable": "two clubs' margins in different games of the same week",
        "y_variable": "the same pair's margins",
        "sample_unit": "same-week unordered game pair",
        "x_source": "SCHED-W7", "y_source": "SCHED-W9",
        "method": "pearson",
        "interpretation": "the cross-game dependence a two-game parlay is exposed to; pairs within a week are not independent draws, and that is stated on the row",
    },
    {
        "correlation_id": "D966-COR-04",
        "x_variable": "net points per game",
        "y_variable": "winning percentage",
        "sample_unit": "club, season through the read date",
        "x_source": "STANDINGS", "y_source": "STANDINGS",
        "method": "pearson",
        "interpretation": "the Pythagorean-style link that any scoring-rate model leans on; measured here rather than assumed",
    },
    {
        "correlation_id": "D966-COR-05",
        "x_variable": "points scored per game",
        "y_variable": "points allowed per game",
        "sample_unit": "club, season through the read date",
        "x_source": "STANDINGS", "y_source": "STANDINGS",
        "method": "pearson",
        "interpretation": "how much attack and defence are separable; a strong positive value would say a club's two rates carry much the same information",
    },
    {
        "correlation_id": "D966-COR-06",
        "x_variable": "club offensive tiers-dropped lower bound on the official Week 10 report",
        "y_variable": "club points scored per game for the season",
        "sample_unit": "club, 28 clubs on the Week 10 slate",
        "x_source": "INJURIES", "y_source": "STANDINGS",
        "method": "pearson",
        "interpretation": "does a deeper injury list line up with a worse scoring rate? Cross-sectional, single-week availability against a season-long rate - the mismatch is stated, not smoothed over",
    },
    {
        "correlation_id": "D966-COR-07",
        "x_variable": "club defensive tiers-dropped lower bound on the official Week 10 report",
        "y_variable": "club points allowed per game for the season",
        "sample_unit": "club, 28 clubs on the Week 10 slate",
        "x_source": "INJURIES", "y_source": "STANDINGS",
        "method": "pearson",
        "interpretation": "the defensive half of the same test, which is what the brief asked the system to know about second, third and fourth string units",
    },
    {
        "correlation_id": "D966-COR-08",
        "x_variable": "club total tiers-dropped lower bound (offence + defence + specialists)",
        "y_variable": "net points per game",
        "sample_unit": "club, 28 clubs on the Week 10 slate",
        "x_source": "INJURIES", "y_source": "STANDINGS",
        "method": "spearman",
        "interpretation": "rank test of whether the clubs with the deepest replacement chains are the same clubs already losing by the season rate; if they largely are, depth adds little to the existing inputs, if they are not, it is information the model is missing",
    },
]

EXCLUSIONS = [
    {
        "candidate_id": "D966-CX-01",
        "candidate": "model edge against the market line versus settled result",
        "status": "excluded",
        "reason": "no official or licensed source in this environment publishes a market line, so one axis of the candidate does not exist",
        "what_would_unlock_it": "a licensed closing-price feed, or a published operator archive with redistribution rights",
        "suggestion_id": "D966-S01",
        "official_source_url": C.link_for("SCHED-W10"),
    },
    {
        "candidate_id": "D966-CX-02",
        "candidate": "player-prop leg versus team-score leg inside a prop combo",
        "status": "excluded",
        "reason": "prop legs settle on per-player statistics, which were not read in this session; team final scores were",
        "what_would_unlock_it": "ingest official per-game player statistics for the graded weeks and re-run the same gate",
        "suggestion_id": "D966-S04",
        "official_source_url": C.link_for("SCHED-W9"),
    },
    {
        "candidate_id": "D966-CX-03",
        "candidate": "stake size versus win",
        "status": "excluded_by_design",
        "reason": "staking is separated from signal in this pack; correlating them would let a staking run look like a model quality",
        "what_would_unlock_it": "nothing - the exclusion is the requirement",
        "suggestion_id": "",
        "official_source_url": C.link_for("REPO"),
    },
    {
        "candidate_id": "D966-CX-04",
        "candidate": "snap-count-weighted depth replacement",
        "status": "excluded",
        "reason": "playing time is not published on the pages this pack is allowed to use as official sources; the depth bound here is a designation count, and it is labelled as one",
        "what_would_unlock_it": "an official play-by-play or Next Gen Stats source with redistribution rights",
        "suggestion_id": "D966-S05",
        "official_source_url": C.link_for("INJURIES"),
    },
    {
        "candidate_id": "D966-CX-05",
        "candidate": "weeks 1-6 margins against later weeks",
        "status": "excluded_until_backfill",
        "reason": "the results feed holds Weeks 7-10 only, so any longer-series correlation would be published on a sample that is not what it claims to be",
        "what_would_unlock_it": "run scripts/ingest_nfl_d966f630.py week-by-week back to Week 1",
        "suggestion_id": "D966-S02",
        "official_source_url": C.link_for("SCHED-W7"),
    },
]


def _club_axis() -> dict[str, dict[str, float]]:
    return R.as_of(9)


def correlations() -> list[dict[str, str]]:
    games = R.team_points()                      # (home, away, week) for 44 finals
    margins = R.margin_pairs()                    # (home margin, total, week)
    home = [h for h, _a, _w in games]
    away = [a for _h, a, _w in games]
    marg = [m for m, _t, _w in margins]
    tot = [t for _m, t, _w in margins]
    tab = _club_axis()

    pairs_cross = []
    for wk in sorted({w for _m, _t, w in margins}):
        same = [(m, i) for i, (m, _t, w) in enumerate(margins) if w == wk]
        for a in range(len(same)):
            for b in range(a + 1, len(same)):
                pairs_cross.append((same[a][0], same[b][0]))

    clubs = sorted(tab)
    depth = _depth_by_club()
    xs = {
        "D966-COR-01": (home, away),
        "D966-COR-02": (marg, tot),
        "D966-COR-03": ([a for a, _b in pairs_cross], [b for _a, b in pairs_cross]),
        "D966-COR-04": ([tab[c]["netpg"] for c in clubs], [tab[c]["win_pct"] for c in clubs]),
        "D966-COR-05": ([tab[c]["ppg"] for c in clubs], [tab[c]["papg"] for c in clubs]),
        "D966-COR-06": None,
        "D966-COR-07": None,
        "D966-COR-08": None,
    }
    # club-level axes that combine the injury report with the standings
    slate_clubs = sorted({row[4] for row in C.WEEK10_SLATE} | {row[5] for row in C.WEEK10_SLATE})
    off = [depth.get(c, {}).get("offence", 0.0) for c in slate_clubs]
    defs = [depth.get(c, {}).get("defence", 0.0) for c in slate_clubs]
    both = [depth.get(c, {}).get("total", 0.0) for c in slate_clubs]
    ppg = [R.as_of(9)[c]["ppg"] for c in slate_clubs]
    papg = [R.as_of(9)[c]["papg"] for c in slate_clubs]
    net = [R.as_of(9)[c]["netpg"] for c in slate_clubs]
    xs["D966-COR-06"] = (off, ppg)
    xs["D966-COR-07"] = (defs, papg)
    xs["D966-COR-08"] = (both, net)

    out: list[dict[str, str]] = []
    for spec in _PAIRS:
        x, y = xs[spec["correlation_id"]]
        n = min(len(x), len(y))
        row = dict(spec)
        if n < 4:
            row.update({"n": str(n), "coefficient": "", "status": "insufficient_sample",
                        "flag_id": "D966-F08"})
        else:
            r = S.spearman(x[:n], y[:n]) if spec["method"] == "spearman" else S.pearson(x[:n], y[:n])
            lo, hi = S.fisher_ci(r, n)
            p = S.pearson_p(r, n)
            status = "measured_from_official_data" if n >= MIN_N else "measured_below_published_floor"
            row.update({
                "n": str(n),
                "coefficient": f"{r:.4f}",
                "ci95_low": S.fmt(lo, 4),
                "ci95_high": S.fmt(hi, 4),
                "p_value_normal_approx": f"{p:.4g}" if not math.isnan(p) else "",
                "status": status,
                "flag_id": "D966-F08" if n < MIN_N else "",
            })
        row.update({
            "x_official_source_url": C.link_for(spec["x_source"]),
            "y_official_source_url": C.link_for(spec["y_source"]),
            "official_source_url": C.link_for(spec["x_source"]),
            "read_on_utc": C.CAPTURE_DATE_UTC,
            "p_value_note": "two-sided p from a normal approximation to the t statistic; conservative (the exact t tail is lighter) at these n",
            "independence_note": ("pairs within a week share a slate; treated as one cluster, so the interval is understated for that row"
                                  if spec["correlation_id"] == "D966-COR-03" else
                                  "one observation per game, games are independent within the feed window"
                                  if spec["sample_unit"] == "game" else
                                  "one observation per club"),
        })
        out.append(row)
    return out


def _depth_by_club() -> dict[str, dict[str, float]]:
    from . import depth as D
    agg: dict[str, dict[str, float]] = {}
    for row in D.group_depth():
        club = row["club"]
        bucket = agg.setdefault(club, {"offence": 0.0, "defence": 0.0, "special": 0.0, "total": 0.0})
        bucket[row["unit"]] = bucket.get(row["unit"], 0.0) + int(row["tiers_dropped_lower_bound"])
        bucket["total"] += int(row["tiers_dropped_lower_bound"])
    return agg


def parlay_probability(leg_probs: list[float], rho: float | None) -> dict[str, object]:
    """Independent product and a correlation-adjusted joint probability.

    For a two-leg parlay on a standardised bivariate Normal at thresholds chosen
    so that each marginal equals its leg probability, the joint is a bivariate
    Normal CDF. ``rho`` is the measured correlation for the pairing (see the
    correlations table); ``None`` means no measurement is available and only the
    independence baseline is returned, with the gap stated.
    """
    product = 1.0
    for p in leg_probs:
        product *= p
    out: dict[str, object] = {
        "leg_probs": leg_probs,
        "independent_product": product,
        "rho_used": "" if rho is None else f"{rho:.4f}",
        "rho_source": "" if rho is None else "measured on the verified results feed (correlations table)",
    }
    if rho is None or len(leg_probs) != 2:
        out["joint_bivariate"] = ""
        out["joint_status"] = "not_computed: needs exactly two legs and a measured rho"
        return out
    z1, z2 = S.normal_ppf(leg_probs[0]), S.normal_ppf(leg_probs[1])
    joint = S.bivariate_normal_cdf(z1, z2, rho)
    out["joint_bivariate"] = joint
    out["joint_minus_independent"] = joint - product
    out["joint_status"] = "computed_from_measured_rho"
    return out
