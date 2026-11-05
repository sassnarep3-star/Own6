"""Power and minimum-sample-size calculations.

The honest question for any new strategy is not "did it make money?" but
"how many bets would it take before a real edge of size X could be detected
at all?" Below those sample sizes, a positive record is uninformative.

Math used:
  * Two-sided z-test power for a mean: the standard normal approximation to
    the t-test (NIST/SEMATECH e-Handbook, 1.3.6.6.1 normal distribution and
    1.3.6.6.18 binomial distribution pages).
  * Bet outcomes are bounded, so the per-bet standard deviation is at most
    ~1.0 unit for even-money stakes; for a break-even bettor at decimal odds d
    with win probability p = 1/d the variance is p(1-p)(d)^2... computed
    exactly below rather than assumed.
"""
from __future__ import annotations

import math

from .luck import norm_ppf


def bet_sd(american: float, p_win: float) -> float:
    """Exact per-bet profit standard deviation at a given true win probability."""
    from .pricing import american_to_decimal

    b = american_to_decimal(american) - 1.0
    ev = p_win * b - (1.0 - p_win)
    var = p_win * (b - ev) ** 2 + (1.0 - p_win) * (-1.0 - ev) ** 2
    return math.sqrt(var)


def z_power(effect: float, sd: float, n: int, alpha: float = 0.05) -> float:
    """Power of a two-sided one-sample z-test for mean = ``effect``."""
    if sd <= 0 or n <= 0:
        return 0.0
    se = sd / math.sqrt(n)
    crit = norm_ppf(1.0 - alpha / 2.0)
    return _norm_cdf(effect / se - crit) + _norm_cdf(-effect / se - crit)


def n_for_power(effect: float, sd: float, power: float = 0.80, alpha: float = 0.05) -> int:
    """Smallest n reaching the requested power for a two-sided test."""
    if effect <= 0 or sd <= 0:
        return 10 ** 9
    z_beta = norm_ppf(power)
    z_alpha = norm_ppf(1.0 - alpha / 2.0)
    n = ((z_alpha + z_beta) * sd / effect) ** 2
    return int(math.ceil(n))


def minimum_detectable_effect(sd: float, n: int, power: float = 0.80, alpha: float = 0.05) -> float:
    """Smallest true mean detectable with the given n at the given power."""
    if n <= 0:
        return float("inf")
    z_beta = norm_ppf(power)
    z_alpha = norm_ppf(1.0 - alpha / 2.0)
    return (z_alpha + z_beta) * sd / math.sqrt(n)


def roi_table(american: float = -110, target_edges=(0.01, 0.02, 0.03, 0.05),
              power: float = 0.80, alpha: float = 0.05) -> list[dict]:
    """Required sample size for a range of true edges at a standard price.

    At -110, a break-even bettor wins 52.38%. A 'true edge' of e means a true
    win probability of 0.5238 + e/EQUIV, expressed here directly as extra ROI.
    """
    from .pricing import american_to_decimal, breakeven_probability

    p0 = breakeven_probability(american)
    d = american_to_decimal(american)
    rows = []
    for edge in target_edges:
        # ROI per unit = p*d - 1, so p = (1+edge)/d
        p = (1.0 + edge) / d
        sd = bet_sd(american, p)
        n = n_for_power(edge, sd, power, alpha)
        rows.append({
            "target_roi": edge,
            "true_win_prob": p,
            "breakeven_win_prob": p0,
            "per_bet_sd": sd,
            "required_n": n,
            "required_n_rounded": _round_up_hundred(n),
            "detected_power_at_200": z_power(edge, sd, 200, alpha),
            "detected_power_at_1000": z_power(edge, sd, 1000, alpha),
        })
    return rows


def _round_up_hundred(n: int) -> int:
    if n >= 10 ** 9:
        return n
    return int(math.ceil(n / 100.0) * 100)


def _norm_cdf(z: float) -> float:
    from .luck import norm_cdf

    return norm_cdf(z)


def false_discovery_after_tries(alpha: float, tries: int) -> float:
    """P(at least one false positive) when testing ``tries`` independent strategies.

    1 - (1 - alpha)^tries. With alpha = 0.05 this exceeds 50% by 14 tries and
    90% by 45 tries — the reason a leaderboard must correct for family size.
    """
    return 1.0 - (1.0 - alpha) ** tries


def tries_for_fwer(target: float, alpha: float = 0.05) -> int:
    """Number of independent strategies that pushes FWER past ``target``."""
    if alpha <= 0:
        return 0
    if target >= 1.0:
        return 10 ** 9
    return int(math.ceil(math.log(1.0 - target) / math.log(1.0 - alpha)))
