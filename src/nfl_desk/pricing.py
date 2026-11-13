"""De-vigging and CLV arithmetic. Implemented and unit-tested; unusable until a licensed feed exists."""
from __future__ import annotations


def american_to_decimal(american: int) -> float:
    """-110 -> 1.9091 and +150 -> 2.5; the two halves of the convention are different formulas."""
    if american == 0:
        raise ValueError("american odds cannot be zero")
    if american < 0:
        return 1.0 + 100.0 / abs(american)
    return 1.0 + american / 100.0


def implied_prob_american(american: int) -> float:
    return 1.0 / american_to_decimal(american)


def devig_multiplicative(prices: list[int]) -> list[float]:
    """Remove vig by proportional scaling; sum of returned probabilities is exactly 1."""
    raw = [implied_prob_american(p) for p in prices]
    s = sum(raw)
    return [r / s for r in raw]


def breakeven_win_prob(american: int) -> float:
    """Cost-adjusted break-even: 11/21 = 52.380952% at -110."""
    return 1.0 / american_to_decimal(american)


def same_line_clv(our_prob: float, close_probs: list[float]) -> dict:
    """Mean signed difference against de-vigged closes, plus a t statistic. Requires >=2 quotes."""
    n = len(close_probs)
    if n < 2:
        raise ValueError("need at least two closing quotes")
    diffs = [our_prob - c for c in close_probs]
    m = sum(diffs) / n
    var = sum((d - m) ** 2 for d in diffs) / (n - 1)
    sd = var ** 0.5
    t = m / (sd / n ** 0.5) if sd > 0 else float("inf")
    return {"n": n, "mean_clv": m, "t": t, "passes_gate": abs(t) >= 2.5 and m > 0}


def brier(probs: list[float], outcomes: list[int]) -> float:
    if len(probs) != len(outcomes) or not probs:
        raise ValueError("mismatched series")
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)


def log_loss(probs: list[float], outcomes: list[int]) -> float:
    import math
    if len(probs) != len(outcomes) or not probs:
        raise ValueError("mismatched series")
    eps = 1e-9
    total = 0.0
    for p, o in zip(probs, outcomes):
        q = min(max(p, eps), 1 - eps)
        total += -(o * math.log(q) + (1 - o) * math.log(1 - q))
    return total / len(probs)
