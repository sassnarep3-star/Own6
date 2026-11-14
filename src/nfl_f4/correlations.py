"""Correlations computed only from officially sourced numbers, published with n.

What "officially sourced" means here
------------------------------------
Every observation entering a correlation must trace to a page published by the
league (nfl.com / operations.nfl.com) or to the operator's own settled price.
Derived intermediate values (model numbers, proposals, other sessions' computed
columns) never enter. If an input cannot be traced, the pair is not computed —
it is reported as ``uncomputable`` with the reason, rather than defaulted to 0.

Why n is printed on every row
-----------------------------
A correlation without a sample size is a rumour. With n=137 team-games the 95%
interval around r=0 is roughly +/-0.17, so a "finding" of r=0.12 is noise. This
module therefore prints n, and a two-sided p-value, and refuses to call anything
material below the declared floor of 100 observations.

Pairs attempted (each justified by a use case)
----------------------------------------------
* margin vs total points, same game — drives side/total correlation in parlays
  and same-game parlay pricing.
* team points-for vs points-against, same game — tests whether a team-game's
  offensive and defensive outputs move together (they should not).
* rest-differential vs margin — needs a verified rest column; NOT captured in
  this pack, so it is reported uncomputable. This is deliberate: it is the
  single most used "signal" in public NFL handicapping and it has no verified
  input here.
* depth-deficiency points vs margin — the injury question. Uncomputable at
  n<100 slates of depth snapshots; reported as such.
"""

from __future__ import annotations

import csv
import math
import os
from typing import Dict, List, Optional, Tuple

from . import results as R

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "nfl_f4")

MIN_N = 100
FIELDS = [
    "corr_id", "pair", "x_label", "y_label", "use", "n", "pearson_r",
    "r_squared", "ci95_low", "ci95_high", "p_value_two_sided",
    "n_floor", "meets_floor", "material", "source_x", "source_y",
    "status", "note",
]

RESULTS_URLS = {
    "scores": "https://www.nfl.com/schedules/2026/by-week/week-{w}",
    "standings": "https://www.nfl.com/standings/",
}


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs)


def pearson(xs: List[float], ys: List[float]) -> Tuple[float, float, float, float]:
    """Return (r, r^2, ci_low, ci_high) with a Fisher-z interval."""
    n = len(xs)
    mx, my = _mean(xs), _mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    r = sxy / math.sqrt(sxx * syy)
    # Clamp only inside the Fisher transform: a perfect correlation has an
    # undefined z, but the correlation itself must be reported exactly.
    if abs(r) >= 1.0:
        # A perfect correlation has no Fisher interval; report the point itself
        # rather than a narrow interval that excludes it.
        return r, r * r, r, r
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3) if n > 3 else float("nan")
    lo = math.tanh(z - 1.96 * se)
    hi = math.tanh(z + 1.96 * se)
    return r, r * r, lo, hi


def p_two_sided(r: float, n: int) -> float:
    """Two-sided p for H0: rho=0 via the Fisher-z normal approximation."""
    if n < 4 or math.isnan(r):
        return float("nan")
    z = 0.5 * math.log((1 + r) / (1 - r)) * math.sqrt(n - 3)
    return math.erfc(abs(z) / math.sqrt(2.0))


def _fmt(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return f"{x:.4f}"


def game_level_pairs() -> Tuple[List[float], List[float], List[float], List[int]]:
    """(margin, total, abs_margin, week) per verified game."""
    margins, totals, abs_m, weeks = [], [], [], []
    for r in R.result_rows():
        m = float(r["margin"])
        margins.append(m)
        totals.append(float(r["total_points"]))
        abs_m.append(abs(m))
        weeks.append(int(r["week"]))
    return margins, totals, abs_m, weeks


def build_rows() -> List[dict]:
    margins, totals, _abs_m, _weeks = game_level_pairs()
    n_games = len(margins)
    rows = []

    # 1. margin vs total
    r, r2, lo, hi = pearson(margins, totals)
    rows.append({
        "corr_id": "C1",
        "pair": "game_margin vs game_total",
        "x_label": "final margin (home - away, points)",
        "y_label": "final total points",
        "use": "Side/total dependence inside same-game parlays.",
        "n": n_games, "pearson_r": _fmt(r), "r_squared": _fmt(r2),
        "ci95_low": _fmt(lo), "ci95_high": _fmt(hi),
        "p_value_two_sided": _fmt(p_two_sided(r, n_games)),
        "n_floor": MIN_N, "meets_floor": "yes" if n_games >= MIN_N else "no",
        "material": "no" if abs(r) < 0.3 or n_games < MIN_N else "yes",
        "source_x": RESULTS_URLS["scores"], "source_y": RESULTS_URLS["scores"],
        "status": "measured",
        "note": ("Both inputs are final scores read from the official weekly "
                 "schedule pages; no model output enters."),
    })

    # 2. team points-for vs points-against within the same game
    pf, pa = [], []
    for r_row in R.result_rows():
        a, h = int(r_row["away_score"]), int(r_row["home_score"])
        pf.extend([a, h])
        pa.extend([h, a])
    r, r2, lo, hi = pearson(pf, pa)
    rows.append({
        "corr_id": "C2",
        "pair": "team_points_for vs team_points_against (same team-game)",
        "x_label": "points scored",
        "y_label": "points allowed",
        "use": "Tests whether one team-game's offence and defence move together; "
               "if they do not, offence and defence must be modelled separately.",
        "n": len(pf), "pearson_r": _fmt(r), "r_squared": _fmt(r2),
        "ci95_low": _fmt(lo), "ci95_high": _fmt(hi),
        "p_value_two_sided": _fmt(p_two_sided(r, len(pf))),
        "n_floor": MIN_N, "meets_floor": "yes" if len(pf) >= MIN_N else "no",
        "material": "no" if abs(r) < 0.3 or len(pf) < MIN_N else "yes",
        "source_x": RESULTS_URLS["scores"], "source_y": RESULTS_URLS["scores"],
        "status": "measured",
        "note": "Each team contributes two observations (one per game played).",
    })

    # 3. abs margin vs total (the version that actually matters for totals)
    abs_m = [abs(m) for m in margins]
    r, r2, lo, hi = pearson(abs_m, totals)
    rows.append({
        "corr_id": "C3",
        "pair": "abs(game_margin) vs game_total",
        "x_label": "absolute final margin",
        "y_label": "final total points",
        "use": "Blowout/total dependence; informs whether totals are safer in "
               "mismatched games.",
        "n": n_games, "pearson_r": _fmt(r), "r_squared": _fmt(r2),
        "ci95_low": _fmt(lo), "ci95_high": _fmt(hi),
        "p_value_two_sided": _fmt(p_two_sided(r, n_games)),
        "n_floor": MIN_N, "meets_floor": "yes" if n_games >= MIN_N else "no",
        "material": "no" if abs(r) < 0.3 or n_games < MIN_N else "yes",
        "source_x": RESULTS_URLS["scores"], "source_y": RESULTS_URLS["scores"],
        "status": "measured",
        "note": "",
    })

    # 4. rest differential vs margin -- needs a verified rest column we do not have
    rows.append({
        "corr_id": "C4",
        "pair": "rest_differential vs game_margin",
        "x_label": "rest days differential (home - away)",
        "y_label": "final margin (home - away)",
        "use": "The most cited public NFL signal; needs a verified rest column.",
        "n": "", "pearson_r": "", "r_squared": "", "ci95_low": "",
        "ci95_high": "", "p_value_two_sided": "", "n_floor": MIN_N,
        "meets_floor": "no", "material": "no",
        "source_x": "", "source_y": RESULTS_URLS["scores"],
        "status": "uncomputable",
        "note": ("Bye weeks are visible on the weekly schedule pages, but per-team "
                 "rest days are not published there. Not inferred from game dates "
                 "because Thursday/Monday games already encode rest and doing so "
                 "would smuggle an assumption into a 'measured' value."),
    })

    # 5. depth deficiency vs margin -- needs a depth snapshot per played game
    rows.append({
        "corr_id": "C5",
        "pair": "depth_deficiency_points vs game_margin",
        "x_label": "proposed depth deficiency points (Week 10 snapshot)",
        "y_label": "final margin (home - away)",
        "use": "The injury question the brief asks for.",
        "n": "", "pearson_r": "", "r_squared": "", "ci95_low": "",
        "ci95_high": "", "p_value_two_sided": "", "n_floor": MIN_N,
        "meets_floor": "no", "material": "no",
        "source_x": "https://www.nfl.com/injuries/",
        "source_y": RESULTS_URLS["scores"],
        "status": "uncomputable",
        "note": ("The pack holds one week of depth snapshots (two clubs) and the "
                 "official injury report for Week 10 only. A correlation would need "
                 "the deficiency score and the margin for the same games across "
                 f">= {MIN_N} observations. Not estimated, not extrapolated."),
    })

    # 6. closing price vs outcome -- is the market efficient at the close?
    rows.append({
        "corr_id": "C6",
        "pair": "closing_spread vs final_margin (one settled game)",
        "x_label": "closing home spread",
        "y_label": "final margin (home - away)",
        "use": "Market efficiency sanity check; needs >=100 settled games with a "
               "captured close.",
        "n": 1, "pearson_r": "", "r_squared": "", "ci95_low": "", "ci95_high": "",
        "p_value_two_sided": "", "n_floor": MIN_N, "meets_floor": "no",
        "material": "no",
        "source_x": ("https://sports.core.api.espn.com/v2/sports/football/leagues/"
                     "nfl/events/401873052/competitions/401873052/odds"),
        "source_y": RESULTS_URLS["scores"],
        "status": "insufficient_sample",
        "note": ("Only one Week 10 game had settled when the prices were read, so "
                 "no correlation is defined. The store is built to accumulate this."),
    })
    return rows


def write_all() -> None:
    rows = build_rows()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "correlations.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
