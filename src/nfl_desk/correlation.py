"""Correlation estimators with bootstrap intervals and permutation nulls.

Written from first principles so the published numbers can be recomputed by hand
from the same registers; no hidden library defaults.
"""
from __future__ import annotations

import math
import random

BOOTSTRAP_REPS = 4000
PERM_REPS = 20000
SEED = 20261113


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 3:
        raise ValueError("need equal-length series of at least 3")
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    syy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sxx == 0 or syy == 0:
        return float("nan")
    return sxy / (sxx * syy)


def ranks(xs: list[float]) -> list[float]:
    """Average ranks, ties shared - the definitional requirement for Spearman rho."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
    return pearson(ranks(xs), ranks(ys))


def bootstrap_ci(xs: list[float], ys: list[float], stat=pearson, reps: int = BOOTSTRAP_REPS,
                 seed: int = SEED, alpha: float = 0.05) -> tuple[float, float, float]:
    """Percentile bootstrap CI for a correlation; resamples whole clubs (the unit of analysis)."""
    rng = random.Random(seed)
    n = len(xs)
    values: list[float] = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        sx = [xs[i] for i in idx]
        sy = [ys[i] for i in idx]
        try:
            v = stat(sx, sy)
        except ValueError:
            continue
        if not math.isnan(v):
            values.append(v)
    if len(values) < 100:
        return (float("nan"), float("nan"), float("nan"))
    values.sort()
    lo = values[int(math.floor(alpha / 2 * len(values)))]
    hi = values[int(math.floor((1 - alpha / 2) * len(values))) - 1]
    return (lo, mean(values), hi)


def permutation_pvalue(xs: list[float], ys: list[float], stat=pearson, reps: int = PERM_REPS,
                       seed: int = SEED) -> float:
    """Two-sided exact-ish p-value by shuffling y; guards against a small-n false positive."""
    rng = random.Random(seed + 7)
    obs = stat(xs, ys)
    n = len(xs)
    y = list(ys)
    hits = 0
    for _ in range(reps):
        rng.shuffle(y)
        if abs(stat(xs, y)) >= abs(obs):
            hits += 1
    return (hits + 1) / (reps + 1)


def correlated_pairs(pairs: list[tuple[float, float]], label: str = "") -> dict:
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    r = pearson(xs, ys)
    rho = spearman(xs, ys)
    lo, mid, hi = bootstrap_ci(xs, ys, pearson)
    p_r = permutation_pvalue(xs, ys, pearson)
    p_rho = permutation_pvalue(xs, ys, spearman)
    return {
        "label": label, "n": len(pairs), "pearson_r": r, "spearman_rho": rho,
        "boot_ci_lo": lo, "boot_mean": mid, "boot_ci_hi": hi,
        "perm_p_pearson": p_r, "perm_p_spearman": p_rho,
        "r_squared": r * r,
    }
