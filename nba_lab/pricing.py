"""Strict price conversions and direct two-leg empirical joint pricing.

All probabilities are model inputs, not verified NBA facts. No independence is
assumed by the joint estimator. A fair price is not an executable sportsbook quote.
"""
from __future__ import annotations

import math
from collections.abc import Sequence


def _finite(value: float, name: str) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def probability(value: float, name: str = "probability", *, strict: bool = True) -> float:
    value = _finite(value, name)
    if (strict and not 0 < value < 1) or (not strict and not 0 <= value <= 1):
        raise ValueError(f"{name} is outside its probability range")
    return value


def decimal_price(value: float) -> float:
    value = _finite(value, "decimal odds")
    if value <= 1:
        raise ValueError("decimal odds must exceed 1")
    return value


def american_to_implied(odds: float) -> float:
    odds = _finite(odds, "American odds")
    if abs(odds) < 100:
        raise ValueError("American odds must be <= -100 or >= +100")
    return 100 / (odds + 100) if odds > 0 else -odds / (-odds + 100)


def decimal_to_implied(odds: float) -> float:
    return 1 / decimal_price(odds)


def prob_to_american(p: float) -> int:
    """Fair American price; no sportsbook margin is added.

    Even money is represented as +100. The inverse of the official operator
    conversion is used; an arbitrary -10 offset would invent vig.
    """
    p = probability(p)
    return round(-100 * p / (1 - p)) if p > 0.5 else round(100 * (1 - p) / p)


def fair_decimal(p: float) -> float:
    return 1 / probability(p)


def devig_two_way(a: float, b: float) -> tuple[float, float]:
    a, b = probability(a, "side A"), probability(b, "side B")
    total = a + b
    return a / total, b / total


def expected_value(p_win: float, odds: float, p_loss: float | None = None) -> float:
    """Unit-stake EV; supply p_loss explicitly when pushes are possible."""
    p_win = probability(p_win, "win probability")
    odds = decimal_price(odds)
    p_loss = 1 - p_win if p_loss is None else probability(p_loss, "loss probability", strict=False)
    if p_win + p_loss > 1 + 1e-12:
        raise ValueError("win and loss probabilities cannot exceed 1")
    return p_win * (odds - 1) - p_loss


def fair_home_spread(expected_home_margin: float) -> float:
    return -_finite(expected_home_margin, "expected home margin")


def fair_total(expected_home_points: float, expected_away_points: float) -> float:
    home = _finite(expected_home_points, "home points")
    away = _finite(expected_away_points, "away points")
    if home < 0 or away < 0:
        raise ValueError("expected points cannot be negative")
    return home + away


def _binary_pairs(a: Sequence[float], b: Sequence[float]) -> tuple[list[float], list[float]]:
    if len(a) != len(b) or len(a) < 3:
        raise ValueError("joint outcomes require equal-length samples of at least three events")
    aa = [probability(x, "leg A outcome", strict=False) for x in a]
    bb = [probability(x, "leg B outcome", strict=False) for x in b]
    if any(x not in (0.0, 1.0) for x in aa + bb):
        raise ValueError("joint hit outcomes must be binary 0/1; pushes need a settlement-specific model")
    return aa, bb


def empirical_joint(a: Sequence[float], b: Sequence[float]) -> dict:
    """Direct P(A and B), with phi correlation when both marginals vary.

    This estimates association, not causation. Small samples and zero joint counts
    are not evidence of a safe price; qualification gates are applied separately.
    """
    aa, bb = _binary_pairs(a, b)
    n = len(aa)
    pa, pb = sum(aa) / n, sum(bb) / n
    pab = sum(x * y for x, y in zip(aa, bb)) / n
    denominator = math.sqrt(pa * (1 - pa) * pb * (1 - pb))
    rho = (pab - pa * pb) / denominator if denominator > 0 else None
    return {
        "n": n, "p_a": pa, "p_b": pb, "p_joint": pab,
        "independent_reference": pa * pb,
        "correlation_adjustment": pab - pa * pb,
        "rho": rho,
        "fair_decimal": 1 / pab if pab > 0 else None,
        "method": "Direct paired hit frequency; no independence or Gaussian-copula assumption.",
    }
