"""Own-line origination, uncertainty and correlation maths for the NFL W11 pack.

Pure Python standard library only, so the numbers can be reproduced anywhere with
``python3`` and re-derived by a reviewer without installing anything.

All model outputs produced here are LABELLED COMPUTATIONS. They are not official NFL
figures, they are not market prices, and nothing here is evidence of a betting edge.
"""

from __future__ import annotations

import math


# --------------------------------------------------------------------------------------
# Distribution helpers
# --------------------------------------------------------------------------------------
def norm_cdf(x: float) -> float:
    """Standard normal CDF (Abramowitz & Stegun 7.1.26 via erf)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    """Inverse standard normal CDF by bisection (no scipy dependency)."""
    if not (0.0 < p < 1.0):
        raise ValueError("p must be in (0,1)")
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def win_prob_from_margin(margin: float, sigma: float) -> float:
    """P(home win) from a projected margin; ties are split, as is standard for NFL lines."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    return norm_cdf(margin / sigma)


def margin_from_win_prob(p: float, sigma: float) -> float:
    return norm_ppf(p) * sigma


def american_from_prob(p: float) -> int:
    """Fair American odds for a probability. Returns 0 for p outside (0,1)."""
    if not (0.0 < p < 1.0):
        return 0
    if p >= 0.5:
        return -int(round(100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def prob_from_american(a: int) -> float:
    if a == 0:
        raise ValueError("American odds cannot be 0")
    if a > 0:
        return 100.0 / (100.0 + a)
    return (-a) / ((-a) + 100.0)


def devig_multiplicative(home_american: int, away_american: int) -> tuple[float, float, float]:
    """Two-way de-vig by normalisation. Returns (home_p, away_p, booksum)."""
    ph = prob_from_american(home_american)
    pa = prob_from_american(away_american)
    s = ph + pa
    return ph / s, pa / s, s


def cover_prob(own_line: float, market_line: float, sigma: float) -> float:
    """P(the market side covers) when our own line is `own_line` and the market is at `market_line`.

    A home handicap of -3 means the home side must win by more than 3. If our own line is the
    fair line, the market side's cover probability is P(margin > market_line) evaluated on
    N(own_line, sigma).
    """
    return 1.0 - norm_cdf((market_line - own_line) / sigma)


# --------------------------------------------------------------------------------------
# Down-weighting historic points for roster change
# --------------------------------------------------------------------------------------
def effective_half_life(weeks_of_history: int, identity_score: float, floor: float = 0.35) -> float:
    """Shorten how far back the model looks when the roster has changed.

    identity_score is the share of the club's listed starters (from the club chart) that are
    also available this week. A fully intact roster keeps the default look-back; a heavily
    depleted one gets a shorter effective half-life, because old results describe players who
    are no longer on the field. This is a disclosed modelling choice, not an official metric.
    """
    if not (0.0 <= identity_score <= 1.0):
        raise ValueError("identity_score must be in [0,1]")
    base = max(weeks_of_history, 1) / 4.0
    return max(floor, base * identity_score)


def geometric_weights(n: int, half_life: float) -> list[float]:
    """Weights for the n most recent games, newest first, decaying with the given half-life."""
    if half_life <= 0:
        raise ValueError("half_life must be positive")
    decay = 0.5 ** (1.0 / half_life)
    w = [decay ** i for i in range(n)]
    s = sum(w)
    return [x / s for x in w]


def weighted_mean(values: list[float], weights: list[float]) -> float | None:
    if not values or len(values) != len(weights):
        return None
    return sum(v * w for v, w in zip(values, weights))


def weighted_var(values: list[float], weights: list[float]) -> float | None:
    m = weighted_mean(values, weights)
    if m is None:
        return None
    return sum(w * (v - m) ** 2 for v, w in zip(values, weights))


# --------------------------------------------------------------------------------------
# Correlation with a confidence interval
# --------------------------------------------------------------------------------------
def pearson(x: list[float], y: list[float]) -> float | None:
    """Pearson correlation. Returns None when it is undefined (n<3 or zero variance)."""
    n = len(x)
    if n != len(y) or n < 3:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r: float, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Fisher z confidence interval for a correlation. None when it is undefined."""
    if n <= 3 or abs(r) >= 1.0:
        return None
    zr = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = math.tanh(zr - z * se), math.tanh(zr + z * se)
    return lo, hi


# --------------------------------------------------------------------------------------
# Skill vs luck
# --------------------------------------------------------------------------------------
def brier(p: float, outcome: int) -> float:
    return (p - outcome) ** 2


def brier_skill_score(model_brier: float, baseline_brier: float) -> float | None:
    """Brier skill score of a model against a reference. Positive means better than reference."""
    if baseline_brier <= 0:
        return None
    return 1.0 - (model_brier / baseline_brier)


def log_loss(p: float, outcome: int) -> float:
    p = min(max(p, 1e-15), 1 - 1e-15)
    return -math.log(p) if outcome == 1 else -math.log(1 - p)


def per_game_profit(prob: float, american: int, outcome: int) -> float:
    """Return on a 1-unit stake at the given American price. Used only for variance analysis."""
    if outcome == 1:
        return (100.0 / -american) if american < 0 else (american / 100.0)
    return -1.0


def prob_of_positive_over_n(p: float, n: int, american: int = -110) -> float | None:
    """Approximate P(total stake profit > 0) over n independent identical bets.

    Placeholder for the luck test. Returns None: the function is intentionally unimplemented
    because no licensed price archive exists, so any value it produced would be a fabricated
    performance statistic. See validation gate VG-03.
    """
    return None
