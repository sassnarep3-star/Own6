"""Pricing and line construction from model expectations.

Every function states its assumption; none of them imports a market price.
"""
from __future__ import annotations

import math

from scipy.stats import norm


def american_to_prob(american: float) -> float:
    """Implied probability of an American price, including vig (no de-vig here)."""
    if american is None or math.isnan(american) or american == 0:
        raise ValueError("invalid American price")
    if american > 0:
        return 100.0 / (american + 100.0)
    return (-american) / (-american + 100.0)


def prob_to_american(p: float) -> float | None:
    """Fair American price for probability p (no margin added, none removed)."""
    if not (0.0 < p < 1.0):
        return None
    if p >= 0.5:
        return round(-100.0 * p / (1.0 - p), 1)
    return round(100.0 * (1.0 - p) / p, 1)


def devig_pair(p_home_raw: float, p_away_raw: float) -> tuple[float, float]:
    total = p_home_raw + p_away_raw
    return p_home_raw / total, p_away_raw / total


def _threshold_probs(mean: float, threshold: float, sd: float) -> dict:
    """P(x > threshold), P(x < threshold), P(push) for integer-valued x ~ N(mean, sd).

    Continuity correction: a whole-number threshold has a push band of one unit,
    a half-point threshold has none. Pushes are reported separately and never
    split between the two sides.
    """
    if sd <= 0:
        raise ValueError("sd must be positive")
    whole = abs(threshold - round(threshold)) < 1e-9
    lower = threshold - 0.5 if whole else threshold
    upper = threshold + 0.5 if whole else threshold
    p_above = 1.0 - norm.cdf((upper - mean) / sd)
    p_below = norm.cdf((lower - mean) / sd)
    push = (1.0 - p_above - p_below) if whole else 0.0
    return {"above": float(p_above), "below": float(p_below), "push": float(push)}


def cover_probability(margin: float, line: float, sd: float) -> dict:
    """P(home covers) given the home spread `line` (negative = home favoured).

    Convention used everywhere in this repository:
      * `margin` is the expected HOME margin (home points - away points);
      * `line` is the home spread as a book writes it, so -6.5 means the home
        team must win by more than 6.5.
    The home side covers when margin + line > 0, i.e. margin > -line.
    `p_home + p_away + push == 1`, and a push is never split 50/50.
    """
    r = _threshold_probs(margin, -line, sd)
    return {"p_home": r["above"], "p_away": r["below"], "push": r["push"]}


def total_over_probability(total_mean: float, line: float, sd: float) -> dict:
    """P(over), P(under), P(push) for a total line, same conventions as above."""
    r = _threshold_probs(total_mean, line, sd)
    return {"p_over": r["above"], "p_under": r["below"], "push": r["push"]}


def win_probability(margin: float, sd: float) -> dict:
    """Home win probability, plus tie probability for completeness."""
    p_home = 1.0 - norm.cdf((0.0 - margin) / sd)
    tie = norm.cdf(0.5 / sd) - norm.cdf(-0.5 / sd)
    return {"p_home": p_home - tie / 2.0, "p_away": 1.0 - p_home - tie / 2.0, "tie": tie}


def kelly_fraction(p: float, american: float) -> float:
    """Full-Kelly stake fraction for a win-probability p at price `american`.

    Research-only sizing diagnostic; the site publishes stakes divided by 4
    (quarter Kelly) and never recommends a wager.
    """
    b = american / 100.0 if american > 0 else 100.0 / (-american)
    return max(0.0, (p * (b + 1.0) - 1.0) / b)


def alternate_lines(margin: float, total: float, sd_margin: float, sd_total: float,
                    spread_lines: list[float], total_lines: list[float]) -> dict:
    return {
        "spreads": {ln: cover_probability(margin, ln, sd_margin) for ln in spread_lines},
        "totals": {ln: total_over_probability(total, ln, sd_total) for ln in total_lines},
    }
