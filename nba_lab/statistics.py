"""Aligned scoring, event-clustered uncertainty and multiplicity controls.

The bootstrap resamples whole event clusters and uses total profit / total unit
stakes. It preserves within-event dependence but does not magically remove serial
dependence across dates. No interval eliminates luck or guarantees future profit.
"""
from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence

import numpy as np
from scipy.stats import binomtest


def _aligned(values: Sequence[float], outcomes: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    if len(values) != len(outcomes) or not len(values):
        raise ValueError("scores require equal-length, nonempty arrays")
    p = np.asarray(values, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    if not np.isfinite(p).all() or not np.isfinite(y).all():
        raise ValueError("scores require finite values")
    if np.any((p <= 0) | (p >= 1)) or np.any((y != 0) & (y != 1)):
        raise ValueError("probabilities must be in (0,1) and outcomes binary")
    return p, y


def brier(probs: Sequence[float], outcomes: Sequence[float]) -> float:
    p, y = _aligned(probs, outcomes)
    return float(np.mean((p - y) ** 2))


def log_loss(probs: Sequence[float], outcomes: Sequence[float]) -> float:
    p, y = _aligned(probs, outcomes)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log1p(-p)))


def calibration_bins(probs: Sequence[float], outcomes: Sequence[float], bins: int = 10) -> list[dict]:
    p, y = _aligned(probs, outcomes)
    if not isinstance(bins, int) or bins < 2:
        raise ValueError("bins must be an integer >= 2")
    result = []
    for i in range(bins):
        low, high = i / bins, (i + 1) / bins
        mask = (p >= low) & (p < high if i < bins - 1 else p <= high)
        n = int(mask.sum())
        result.append({
            "lower": low, "upper": high, "n": n,
            "mean_prediction": float(p[mask].mean()) if n else None,
            "observed_rate": float(y[mask].mean()) if n else None,
        })
    return result


def pearson_pair(xs: Sequence[float], ys: Sequence[float]) -> dict:
    if len(xs) != len(ys) or len(xs) < 3:
        raise ValueError("correlation requires equal-length samples of at least three pairs")
    x, y = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("correlation inputs must be finite")
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        raise ValueError("correlation is undefined for a constant series")
    r = float(np.corrcoef(x, y)[0, 1])
    return {"n": len(x), "estimate": r, "ci_low": None, "ci_high": None, "method": "Pearson/phi point estimate; interval requires event-clustered paired resampling; not causal."}


def cluster_bootstrap(values: Sequence[float], groups: Sequence[str], *, iterations: int = 10000, seed: int = 20261102, alpha: float = 0.05) -> dict:
    if len(values) != len(groups) or not len(values):
        raise ValueError("bootstrap requires aligned nonempty values and group IDs")
    if not isinstance(iterations, int) or iterations < 100:
        raise ValueError("bootstrap iterations must be an integer >= 100")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    totals: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for value, group in zip(values, groups):
        value = float(value)
        if not math.isfinite(value) or not isinstance(group, str) or not group:
            raise ValueError("bootstrap requires finite values and nonempty string group IDs")
        totals[group][0] += value
        totals[group][1] += 1
    arr = np.asarray(list(totals.values()), dtype=float)
    if np.any(arr[:, 1] <= 0):
        raise ValueError("empty cluster")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(iterations, len(arr)))
    means = arr[idx, 0].sum(axis=1) / arr[idx, 1].sum(axis=1)
    low, high = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    # One-sided bootstrap achievement p-value for H0: mean <= 0. This is an
    # approximate percentile-bootstrap diagnostic, not an exact randomization test.
    p_greater = float((1 + np.count_nonzero(means <= 0)) / (iterations + 1))
    return {"mean": float(arr[:, 0].sum() / arr[:, 1].sum()), "lower": float(low), "upper": float(high),
            "p_one_sided_greater": p_greater, "n_observations": len(values), "n_clusters": len(arr),
            "iterations": iterations, "seed": seed,
            "method": "Percentile bootstrap of whole clusters; serial dependence is not eliminated. p is approximate."}


def bonferroni(pvals: Sequence[float]) -> dict:
    if not len(pvals):
        raise ValueError("a nonempty frozen hypothesis family is required")
    p = np.asarray(pvals, dtype=float)
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("p-values must be finite and in [0,1]")
    adjusted = np.minimum(1.0, p * len(p))
    return {"adjusted": adjusted.tolist(), "family_size": len(p), "method": "Bonferroni across the complete frozen candidate family, including abandoned candidates."}


def poisson_binomial_tail(wins: int, probabilities: Sequence[float]) -> float:
    """Exact P(X >= wins) for independent, possibly unequal-price Bernoulli trials.

    Diagnostic only: clustered bets violate independence. The cluster-robust ROI,
    CLV and predictive-quality gates remain mandatory.
    """
    if not isinstance(wins, int) or not 0 <= wins <= len(probabilities):
        raise ValueError("wins must be an integer between 0 and the sample size")
    p = np.asarray(probabilities, dtype=float)
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("null probabilities must be in [0,1]")
    dist = np.zeros(len(p) + 1)
    dist[0] = 1.0
    for i, pi in enumerate(p, 1):
        dist[1:i + 1] = dist[1:i + 1] * (1 - pi) + dist[0:i] * pi
        dist[0] *= 1 - pi
    return float(min(1.0, max(0.0, dist[wins:].sum())))


def binomial_tail(wins: int, n: int, p: float) -> float:
    if not isinstance(n, int) or n <= 0 or not isinstance(wins, int) or not 0 <= wins <= n:
        raise ValueError("invalid binomial counts")
    if not 0 <= p <= 1:
        raise ValueError("invalid null probability")
    return float(binomtest(wins, n, p, alternative="greater").pvalue)


def max_drawdown(returns: Sequence[float]) -> float | None:
    if not returns:
        return None
    r = np.asarray(returns, dtype=float)
    if not np.isfinite(r).all():
        raise ValueError("returns must be finite")
    equity = np.concatenate(([0.0], np.cumsum(r)))
    peak = np.maximum.accumulate(equity)
    return float(np.max(peak - equity))


def cluster_correlation(xs: Sequence[float], ys: Sequence[float], groups: Sequence[str], *,
                        iterations: int = 10000, seed: int = 20261102, alpha: float = 0.05) -> dict:
    """Pearson/phi estimate with a paired whole-cluster percentile interval.

    Zero residuals are valid observations and are retained. Undefined resamples
    (a constant leg) are skipped; too many undefined resamples block the estimate.
    This interval assumes the supplied clusters are the relevant dependence unit.
    """
    point = pearson_pair(xs, ys)
    if len(groups) != len(xs):
        raise ValueError("correlation groups must align with paired observations")
    if not isinstance(iterations, int) or iterations < 100 or not 0 < alpha < 1:
        raise ValueError("invalid bootstrap configuration")
    by_group: dict[str, list[int]] = defaultdict(list)
    for i, group in enumerate(groups):
        if not isinstance(group, str) or not group:
            raise ValueError("cluster IDs must be nonempty strings")
        by_group[group].append(i)
    keys = sorted(by_group)
    x, y = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(keys), size=(iterations, len(keys)))
    estimates = []
    for draw in draws:
        idx = np.concatenate([np.asarray(by_group[keys[k]], dtype=int) for k in draw])
        xx, yy = x[idx], y[idx]
        if np.ptp(xx) == 0 or np.ptp(yy) == 0:
            continue
        estimates.append(float(np.corrcoef(xx, yy)[0, 1]))
    if len(estimates) < max(100, iterations // 2):
        raise ValueError("too many undefined correlation resamples; estimate is unstable")
    low, high = np.quantile(estimates, [alpha / 2, 1 - alpha / 2])
    return {**point, "ci_low": float(low), "ci_high": float(high), "n_clusters": len(keys),
            "valid_resamples": len(estimates), "iterations": iterations, "seed": seed,
            "method": "Paired Pearson/phi with whole-cluster percentile bootstrap; zeros retained; not causal."}
