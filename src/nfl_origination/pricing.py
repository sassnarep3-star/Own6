"""Strict NFL odds conversion, vig removal, push-exact EV, and same-line CLV utilities."""
from __future__ import annotations

import math
from numbers import Real
from typing import Sequence


def _real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number (got {type(value).__name__})")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def american_to_decimal(odds: int | float) -> float:
    """Convert valid American odds (<= -100 or >= +100) to decimal payout odds."""
    val = _real(odds, "odds")
    if -100.0 < val < 100.0:
        raise ValueError(f"American odds cannot lie in (-100, 100); got {val}")
    if val >= 100.0:
        return 1.0 + (val / 100.0)
    return 1.0 + (100.0 / (-val))


def american_to_implied_prob(odds: int | float) -> float:
    """Convert valid American odds to raw implied break-even probability.

    Positive odds: 100 / (odds + 100).
    Negative odds: -odds / (-odds + 100).
    """
    val = _real(odds, "odds")
    if -100.0 < val < 100.0:
        raise ValueError(f"American odds cannot lie in (-100, 100); got {val}")
    if val >= 100.0:
        return 100.0 / (val + 100.0)
    return (-val) / ((-val) + 100.0)


def prob_to_fair_american(prob: float) -> int:
    """Convert a fair probability in (0, 1) to no-vig American odds."""
    p = _real(prob, "prob")
    if not (0.0 < p < 1.0):
        raise ValueError(f"prob must be strictly inside (0, 1); got {p}")
    if p >= 0.5:
        return round(-100.0 * p / (1.0 - p))
    return round(100.0 * (1.0 - p) / p)


def devig_multiplicative(probs_raw: Sequence[float]) -> tuple[float, ...]:
    """Proportional (multiplicative) vig removal across 2-way or 3-way markets."""
    cleaned = [_real(p, "probs_raw") for p in probs_raw]
    if len(cleaned) < 2:
        raise ValueError("at least 2 market outcomes are required to de-vig")
    if any(p <= 0.0 or p >= 1.0 for p in cleaned):
        raise ValueError("each raw implied probability must lie in (0, 1)")
    overround = math.fsum(cleaned)
    if overround < 1.0 - 1e-9:
        raise ValueError(f"sum of raw implied probabilities ({overround:.6f}) is below 1.0")
    return tuple(p / overround for p in cleaned)


def devig_power(probs_raw: Sequence[float], tol: float = 1e-12) -> tuple[float, ...]:
    """Power-method vig removal: solve sum_i (p_i ** k) == 1 for exponent k >= 1.

    Accounts for favorite-longshot bias in NFL moneylines and alternate lines.
    """
    cleaned = [_real(p, "probs_raw") for p in probs_raw]
    if len(cleaned) < 2:
        raise ValueError("at least 2 market outcomes are required to de-vig")
    if any(p <= 0.0 or p >= 1.0 for p in cleaned):
        raise ValueError("each raw implied probability must lie in (0, 1)")
    overround = math.fsum(cleaned)
    if overround < 1.0 - 1e-9:
        raise ValueError(f"sum of raw implied probabilities ({overround:.6f}) is below 1.0")
    if abs(overround - 1.0) <= tol:
        return tuple(cleaned)

    lo, hi = 1.0, 2.0
    while math.fsum(p ** hi for p in cleaned) > 1.0:
        hi *= 2.0
        if hi > 1024.0:
            raise ValueError("power de-vig failed to bracket root")

    for _ in range(100):
        mid = 0.5 * (lo + hi)
        s = math.fsum(p ** mid for p in cleaned)
        if abs(s - 1.0) <= tol:
            lo = hi = mid
            break
        if s > 1.0:
            lo = mid
        else:
            hi = mid
    k = 0.5 * (lo + hi)
    raw_power = [p ** k for p in cleaned]
    norm = math.fsum(raw_power)
    return tuple(v / norm for v in raw_power)


def push_aware_ev(
    p_win: float,
    p_loss: float,
    p_push: float,
    american_odds: int | float,
) -> float:
    """Exact expected return per 1.0 unit risked, explicitly accounting for pushes.

    Critical for NFL integer spreads (3, 7, 6, 10, 14) and integer totals where
    push mass is 5%–10% of all outcomes.
    """
    pw = _real(p_win, "p_win")
    pl = _real(p_loss, "p_loss")
    pp = _real(p_push, "p_push")
    if any(x < 0.0 or x > 1.0 for x in (pw, pl, pp)):
        raise ValueError("probabilities must lie in [0, 1]")
    total = pw + pl + pp
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"p_win + p_loss + p_push must equal 1.0 (got {total:.8f})")
    net_win_payout = american_to_decimal(american_odds) - 1.0
    return pw * net_win_payout - pl * 1.0 + pp * 0.0


def same_line_clv(
    entry_devig_prob: float,
    close_devig_prob: float,
    entry_line: float,
    close_line: float,
) -> float | None:
    """De-vigged Closing Line Value on identical spread/total numbers.

    If a spread moves across an NFL key number (e.g. -2.5 to -3.5), raw price
    comparison is invalid without a calibrated push/half-point distribution;
    returns None fail-closed unless entry_line == close_line.
    """
    pe = _real(entry_devig_prob, "entry_devig_prob")
    pc = _real(close_devig_prob, "close_devig_prob")
    le = _real(entry_line, "entry_line")
    lc = _real(close_line, "close_line")
    if not (0.0 < pe < 1.0 and 0.0 < pc < 1.0):
        raise ValueError("de-vigged probabilities must lie in (0, 1)")
    if le != lc:
        return None
    return pc - pe
