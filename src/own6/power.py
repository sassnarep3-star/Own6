"""Luck-exclusion arithmetic for betting strategies.

The purpose of this module is narrow and deliberate: it answers "how much
evidence would be needed before a result stops being explainable by luck?"
using closed-form statistics.  It does **not** contain, require or imply any
NBA data, sportsbook quote, projection or performance claim.

Every number produced here is a *computation of the stated formula* — a
statistical requirement, not an observation.  A requirement can therefore be
published without inventing an observation, which is why this is the one part
of the project that can be populated while verified odds are unavailable.

Conventions
-----------
* Stakes are 1 unit.  A winning bet at decimal odds ``d`` returns ``d - 1``;
  a losing bet returns ``-1``.
* Expected ROI ``mu`` is per unit staked, so ``mu = p * d - 1``.
* Tests are one-sided by default (the only interesting hypothesis for a
  candidate strategy is "the edge is positive"); two-sided is available.
* ``alpha`` is the significance level, ``power = 1 - beta``.

Only the Python standard library is used, so the module runs in CI without
third-party wheels.  ``tests/test_power.py`` cross-checks the results against
SciPy when SciPy is installed.
"""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Iterable, Sequence

__all__ = [
    "decimal_from_american",
    "american_from_decimal",
    "implied_probability",
    "break_even_probability",
    "bet_moments",
    "required_bets",
    "required_bets_for_roi",
    "minimum_detectable_roi",
    "bonferroni_alpha",
    "bonferroni_required_bets",
    "expected_false_positives",
    "bh_qvalues",
    "binomial_sf",
    "binomial_p_value",
    "wilson_interval",
    "minimum_detectable_probability",
    "fisher_required_pairs",
    "require_monotone",
    "luck_verdict",
]

_NORMAL = NormalDist()


def _check_probability(value: float, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be strictly between 0 and 1, got {value!r}")
    return float(value)


def _check_positive(value: float, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and positive, got {value!r}")
    return float(value)


def _check_sides(sides: int) -> int:
    if sides not in (1, 2):
        raise ValueError(f"sides must be 1 or 2, got {sides!r}")
    return sides


def _z(alpha: float, sides: int) -> float:
    """Critical value for a one- or two-sided test at level ``alpha``."""
    _check_probability(alpha, "alpha")
    return _NORMAL.inv_cdf(1.0 - alpha) if _check_sides(sides) == 1 else _NORMAL.inv_cdf(1.0 - alpha / 2.0)


# --------------------------------------------------------------------------
# Price conversions
# --------------------------------------------------------------------------
def decimal_from_american(moneyline: float) -> float:
    """Convert American odds to decimal odds (stake included).

    ``-110 -> 1.9090909...``, ``+150 -> 2.5``.  A moneyline of 0 is invalid.
    """
    if not isinstance(moneyline, (int, float)) or isinstance(moneyline, bool):
        raise TypeError("moneyline must be a real number")
    if not math.isfinite(moneyline) or moneyline == 0:
        raise ValueError(f"moneyline must be finite and non-zero, got {moneyline!r}")
    if moneyline > 0:
        return 1.0 + moneyline / 100.0
    return 1.0 + 100.0 / abs(moneyline)


def american_from_decimal(decimal_odds: float) -> float:
    """Convert decimal odds (> 1) back to American odds."""
    _check_positive(decimal_odds, "decimal_odds")
    if decimal_odds <= 1.0:
        raise ValueError(f"decimal_odds must exceed 1, got {decimal_odds!r}")
    if decimal_odds >= 2.0:
        return round(100.0 * (decimal_odds - 1.0), 6)
    return round(-100.0 / (decimal_odds - 1.0), 6)


def implied_probability(moneyline: float) -> float:
    """Break-even probability of a single moneyline price, i.e. ``1 / d``.

    This is the raw (vig-inclusive) implied probability.  De-vigging a
    two-sided market requires both sides and is intentionally not attempted
    here.
    """
    return 1.0 / decimal_from_american(moneyline)


def break_even_probability(decimal_odds: float) -> float:
    """Probability at which the expected ROI of a bet is exactly zero."""
    _check_positive(decimal_odds, "decimal_odds")
    if decimal_odds <= 1.0:
        raise ValueError(f"decimal_odds must exceed 1, got {decimal_odds!r}")
    return 1.0 / decimal_odds


# --------------------------------------------------------------------------
# Per-bet moments
# --------------------------------------------------------------------------
def bet_moments(win_probability: float, decimal_odds: float) -> tuple[float, float]:
    """Return ``(mean, variance)`` of the per-bet profit at 1-unit stakes."""
    p = _check_probability(win_probability, "win_probability")
    d = _check_positive(decimal_odds, "decimal_odds")
    if d <= 1.0:
        raise ValueError(f"decimal_odds must exceed 1, got {d!r}")
    win = d - 1.0
    mean = p * d - 1.0
    second_moment = p * win * win + (1.0 - p)
    variance = second_moment - mean * mean
    # Guard against a tiny negative value from floating-point cancellation.
    if variance < 0.0 and variance > -1e-12:
        variance = 0.0
    return mean, variance


# --------------------------------------------------------------------------
# Sample-size requirements
# --------------------------------------------------------------------------
def required_bets(
    mean_roi: float,
    per_bet_variance: float,
    alpha: float = 0.05,
    power: float = 0.80,
    sides: int = 1,
) -> int:
    """Bets needed to detect ``mean_roi`` with the given size and power.

    Normal-approximation sample size::

        n = ceil( ((z_{1-alpha'} + z_{power}) * sigma / mu)^2 )

    where ``alpha' = alpha`` for a one-sided test and ``alpha / 2`` for a
    two-sided test.  Returns ``inf``-free integers; a non-positive mean raises.
    """
    if not isinstance(mean_roi, (int, float)) or isinstance(mean_roi, bool):
        raise TypeError("mean_roi must be a real number")
    if not math.isfinite(mean_roi) or mean_roi <= 0.0:
        raise ValueError("mean_roi must be finite and positive")
    _check_probability(power, "power")
    variance = _check_positive(per_bet_variance, "per_bet_variance")
    z_alpha = _z(alpha, sides)
    z_beta = _NORMAL.inv_cdf(power)
    n = ((z_alpha + z_beta) ** 2) * variance / (mean_roi**2)
    return int(math.ceil(n))


def required_bets_for_roi(
    roi: float,
    decimal_odds: float,
    alpha: float = 0.05,
    power: float = 0.80,
    sides: int = 1,
) -> int:
    """Bets needed to detect a true per-bet ROI of ``roi`` at a fixed price."""
    d = _check_positive(decimal_odds, "decimal_odds")
    if d <= 1.0:
        raise ValueError(f"decimal_odds must exceed 1, got {d!r}")
    if not isinstance(roi, (int, float)) or isinstance(roi, bool):
        raise TypeError("roi must be a real number")
    if not math.isfinite(roi):
        raise ValueError("roi must be finite")
    win_probability = (1.0 + float(roi)) / d
    if not 0.0 < win_probability < 1.0:
        raise ValueError(
            f"roi {roi!r} at decimal odds {d!r} implies win probability "
            f"{win_probability!r}, which is not a valid probability"
        )
    _, variance = bet_moments(win_probability, d)
    return required_bets(float(roi), variance, alpha=alpha, power=power, sides=sides)


def minimum_detectable_roi(
    n: int,
    per_bet_variance: float,
    alpha: float = 0.05,
    power: float = 0.80,
    sides: int = 1,
) -> float:
    """Smallest per-bet ROI distinguishable from luck at this sample size.

    Inverse of :func:`required_bets`::

        mu_min = (z_{1-alpha'} + z_{power}) * sigma / sqrt(n)

    Anything smaller cannot be separated from noise, however good it looks.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be a positive integer")
    variance = _check_positive(per_bet_variance, "per_bet_variance")
    z_alpha = _z(alpha, sides)
    z_beta = _NORMAL.inv_cdf(_check_probability(power, "power"))
    return (z_alpha + z_beta) * math.sqrt(variance) / math.sqrt(n)


# --------------------------------------------------------------------------
# Multiple testing
# --------------------------------------------------------------------------
def bonferroni_alpha(alpha: float, tests: int) -> float:
    """Family-wise error rate split across ``tests`` independent hypotheses."""
    _check_probability(alpha, "alpha")
    if not isinstance(tests, int) or isinstance(tests, bool) or tests < 1:
        raise ValueError("tests must be a positive integer")
    return alpha / tests


def bonferroni_required_bets(
    base_n: int,
    tests: int,
    alpha: float = 0.05,
    power: float = 0.80,
    sides: int = 1,
) -> int:
    """Sample size once the per-test alpha is Bonferroni-corrected.

    The requirement scales by ``(z_{1-alpha/m} + z_{power})^2 /
    (z_{1-alpha} + z_{power})^2``; with 200 candidates the penalty is large,
    which is the honest cost of searching many strategies.
    """
    if not isinstance(base_n, int) or isinstance(base_n, bool) or base_n < 1:
        raise ValueError("base_n must be a positive integer")
    _check_probability(power, "power")
    adjusted = bonferroni_alpha(alpha, tests)
    z_base = _z(alpha, sides) + _NORMAL.inv_cdf(power)
    z_adj = _z(adjusted, sides) + _NORMAL.inv_cdf(power)
    return int(math.ceil(base_n * (z_adj / z_base) ** 2))


def expected_false_positives(tests: int, alpha: float) -> float:
    """Expected number of pure-noise strategies that pass at level ``alpha``."""
    if not isinstance(tests, int) or isinstance(tests, bool) or tests < 1:
        raise ValueError("tests must be a positive integer")
    return tests * _check_probability(alpha, "alpha")


def bh_qvalues(p_values: Sequence[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values (q-values), order preserved.

    Steps: sort ascending, ``q_(i) = min_{j >= i} (m / j) * p_(j)``, cap at 1.
    """
    values = [_check_probability(float(p), "p_value") for p in p_values]
    m = len(values)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: values[i])
    adjusted = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        index = order[rank - 1]
        candidate = values[index] * m / rank
        running = min(running, candidate)
        adjusted[index] = min(1.0, running)
    return adjusted


# --------------------------------------------------------------------------
# Observed results: is this distinguishable from luck?
# --------------------------------------------------------------------------
def _log_pmf(k: int, n: int, p: float) -> float:
    """Log binomial pmf, computed in log space so large n cannot overflow."""
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log1p(-p)
    )


def binomial_sf(k: int, n: int, probability: float) -> float:
    """Exact ``P(X >= k)`` for ``X ~ Binomial(n, probability)``.

    Evaluated in log space and combined with a log-sum-exp shift, so the result
    is accurate for n in the thousands where ``comb(n, k)`` overflows a float.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n must be a non-negative integer")
    if not isinstance(k, int) or isinstance(k, bool) or k < 0:
        raise ValueError("k must be a non-negative integer")
    if k > n:
        return 0.0
    if k == 0:
        return 1.0
    p = _check_probability(probability, "probability")
    logs = [_log_pmf(i, n, p) for i in range(k, n + 1)]
    peak = max(logs)
    total = peak + math.log(math.fsum(math.exp(value - peak) for value in logs))
    return min(1.0, max(0.0, math.exp(total)))


def binomial_p_value(wins: int, bets: int, break_even: float, sides: int = 1) -> float:
    """Exact binomial p-value against a break-even rate.

    One-sided (default) is the upper tail ``P(X >= wins)``.  Two-sided follows
    the exact SciPy convention: sum the probability of every outcome whose
    likelihood is no greater than the observed one.  Use
    ``break_even = 1 / decimal_odds``.  A p-value above ``alpha`` means the
    record is still explainable by luck at that level.
    """
    p0 = _check_probability(break_even, "break_even")
    upper_tail = binomial_sf(wins, bets, p0)
    if _check_sides(sides) == 1:
        return upper_tail
    observed = _log_pmf(wins, bets, p0)
    tolerance = observed + 1e-7
    total = math.fsum(
        math.exp(value)
        for value in (_log_pmf(i, bets, p0) for i in range(bets + 1))
        if value <= tolerance
    )
    return min(1.0, max(0.0, total))


def _pmf(k: int, n: int, p: float) -> float:
    """Exact binomial pmf in log space (kept for callers and tests)."""
    return math.exp(_log_pmf(k, n, p))


def wilson_interval(wins: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (no continuity fix)."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be a positive integer")
    if not isinstance(wins, int) or isinstance(wins, bool) or wins < 0 or wins > n:
        raise ValueError("wins must be an integer between 0 and n")
    _check_positive(z, "z")
    phat = wins / n
    denominator = 1.0 + z * z / n
    centre = (phat + z * z / (2.0 * n)) / denominator
    half = (z / denominator) * math.sqrt(phat * (1.0 - phat) / n + z * z / (4.0 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half)


def minimum_detectable_probability(n: int, z: float = 1.959963984540054) -> float:
    """Half-width of a normal-approximation 95% interval on a proportion.

    At ``n = 100`` the interval is roughly +/-9.8 points even at a 50%
    proportion: that is the resolution limit of a small record.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be a positive integer")
    _check_positive(z, "z")
    return z * math.sqrt(0.25 / n)


def fisher_required_pairs(
    correlation: float,
    alpha: float = 0.05,
    power: float = 0.80,
    sides: int = 2,
) -> int:
    """Paired observations needed to detect a correlation via the Fisher z test.

    ``n = ((z_{1-alpha'} + z_{power}) / atanh(r))^2 + 3``.  A correlation of
    0.10 needs roughly 780 pairs at 80% power; small samples cannot establish
    dependence whatever the sample coefficient says.
    """
    if not isinstance(correlation, (int, float)) or isinstance(correlation, bool):
        raise TypeError("correlation must be a real number")
    if not math.isfinite(correlation) or not -1.0 < correlation < 1.0:
        raise ValueError("correlation must lie strictly between -1 and 1")
    if correlation == 0.0:
        raise ValueError("correlation must be non-zero")
    z_alpha = _z(alpha, sides)
    z_beta = _NORMAL.inv_cdf(_check_probability(power, "power"))
    n = ((z_alpha + z_beta) / math.atanh(correlation)) ** 2 + 3.0
    return int(math.ceil(n))


def luck_verdict(
    wins: int,
    bets: int,
    decimal_odds: float,
    alpha: float = 0.05,
    sides: int = 1,
) -> dict[str, float | int | bool | str]:
    """Return the luck-exclusion decision record for an observed record.

    The verdict is ``"exceeds_luck"`` only when the lower Wilson bound of the
    win rate also clears the price's break-even probability.  Both conditions
    are required: a p-value with a lower bound below 1/d is not separation.
    """
    d = _check_positive(decimal_odds, "decimal_odds")
    if d <= 1.0:
        raise ValueError(f"decimal_odds must exceed 1, got {d!r}")
    breakeven = break_even_probability(d)
    p_value = binomial_p_value(wins, bets, breakeven, sides=sides)
    low, high = wilson_interval(wins, bets)
    roas = (wins * (d - 1.0) - (bets - wins)) / bets
    exceeds = bool(p_value < alpha and low > breakeven)
    if exceeds:
        label = "exceeds_luck"
    elif p_value < alpha:
        label = "significant_but_interval_not_separated"
    else:
        label = "explainable_by_luck"
    return {
        "wins": wins,
        "bets": bets,
        "decimal_odds": d,
        "break_even_probability": breakeven,
        "observed_win_rate": wins / bets,
        "roi": roas,
        "p_value": p_value,
        "wilson_low": low,
        "wilson_high": high,
        "verdict": label,
        "exceeds_luck": exceeds,
    }


def require_monotone(values: Iterable[float]) -> bool:
    """Helper used by the checkers: true when a sequence never decreases."""
    iterator = iter(values)
    try:
        previous = next(iterator)
    except StopIteration:
        return True
    for value in iterator:
        if value < previous:
            return False
        previous = value
    return True
