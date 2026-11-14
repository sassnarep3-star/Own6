"""Pure-Python statistics helpers.

No third-party dependency is used anywhere in this package so that the
verification gate can run in a bare CI container. Every routine here is either
an exact closed form or a documented resampling procedure; nothing is fitted
silently.

Conventions
-----------
* Two-sided p-values unless the name says ``one_sided``.
* A p-value of ``None`` means "not computable from the data supplied" and is
  published as a blank cell, never as 0 or 1.
"""

from __future__ import annotations

import math
import random

# ---------------------------------------------------------------- descriptors


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def stdev(xs, ddof=1):
    """Sample standard deviation. Returns None when n <= ddof."""
    xs = list(xs)
    n = len(xs)
    if n <= ddof:
        return None
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / (n - ddof)
    return math.sqrt(var)


def pearson(xs, ys):
    """Pearson r plus its two-sided p-value via a t approximation.

    Returns ``(r, p, n)``. ``r`` is None when either series is constant or n < 3.
    """
    xs, ys = list(xs), list(ys)
    if len(xs) != len(ys):
        raise ValueError("pearson: length mismatch")
    n = len(xs)
    if n < 3:
        return None, None, n
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None, None, n
    r = sxy / math.sqrt(sxx * syy)
    r = max(-1.0, min(1.0, r))
    if abs(r) >= 1.0:
        return r, 0.0, n
    t = r * math.sqrt((n - 2) / (1 - r * r))
    p = 2 * (1 - _student_t_cdf(abs(t), n - 2))
    return r, p, n


def spearman(xs, ys):
    """Spearman rank correlation. Returns ``(rho, p, n)``."""
    xs, ys = list(xs), list(ys)
    if len(xs) != len(ys) or len(xs) < 3:
        return None, None, len(xs)
    return pearson(_rank(xs), _rank(ys))


def _rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


# ------------------------------------------------------------- distributions


def _student_t_cdf(t, df):
    """Student-t CDF via the regularized incomplete beta function."""
    if df <= 0:
        return float("nan")
    x = df / (df + t * t)
    ib = _betainc(df / 2.0, 0.5, x)
    tail = 0.5 * ib
    return 1 - tail if t > 0 else tail


def _betainc(a, b, x):
    """Regularized incomplete beta I_x(a,b) (continued fraction, Lentz)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x)
    return 1 - math.exp(math.log(1 - x) * b + math.log(x) * a - lbeta) / b * _betacf(b, a, 1 - x)


def _betacf(a, b, x, iters=300, eps=3e-14):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, iters + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def binomial_one_sided_p(successes, n, p0=0.5):
    """P(X >= successes | n, p0) for a fair-coin null. None when n == 0."""
    if n <= 0:
        return None
    if successes < 0 or successes > n:
        raise ValueError("binomial_one_sided_p: successes out of range")
    tail = sum(math.comb(n, k) * (p0 ** k) * ((1 - p0) ** (n - k)) for k in range(successes, n + 1))
    return min(1.0, tail)


def wilson_interval(successes, n, z=1.959963985):
    """Wilson score interval for a binomial proportion. None when n == 0."""
    if n <= 0:
        return None, None
    phat = successes / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------- resampling


def bootstrap_ci(xs, stat=mean, iters=2000, alpha=0.05, seed=20261114):
    """Percentile bootstrap CI for ``stat``. Deterministic for a fixed seed."""
    xs = list(xs)
    if len(xs) < 3:
        return None, None
    rng = random.Random(seed)
    n = len(xs)
    draws = []
    for _ in range(iters):
        sample = [xs[rng.randrange(n)] for _ in range(n)]
        draws.append(stat(sample))
    draws.sort()
    lo = draws[int((alpha / 2) * iters)]
    hi = draws[min(iters - 1, int((1 - alpha / 2) * iters))]
    return lo, hi


def paired_bootstrap_p(wins_a, wins_b, iters=4000, seed=20261114):
    """One-sided bootstrap p that mean(a) < mean(b) on paired differences.

    ``wins_a`` and ``wins_b`` are the two paired loss series (a = challenger,
    b = baseline). Smaller is better. Returns P(mean(a-b) >= 0) under
    resampling of the paired difference, i.e. the p-value against the
    hypothesis that the challenger is at least as good as the baseline.
    """
    diffs = [a - b for a, b in zip(wins_a, wins_b)]
    if len(diffs) < 3:
        return None
    obs = sum(diffs) / len(diffs)
    rng = random.Random(seed)
    n = len(diffs)
    hits = 0
    for _ in range(iters):
        s = sum(diffs[rng.randrange(n)] for _ in range(n)) / n
        if s >= 0:
            hits += 1
    return (hits + 1) / (iters + 1)


if __name__ == "__main__":  # pragma: no cover - smoke test
    assert abs(norm_cdf(0) - 0.5) < 1e-12
    assert abs(_student_t_cdf(2.0, 10) - 0.963306) < 1e-4
    lo, hi = wilson_interval(14, 20)
    # Reference: Wilson 95% interval for 14/20 is approximately (0.481, 0.855).
    assert abs(lo - 0.48103) < 1e-4 and abs(hi - 0.85452) < 1e-4
    print("stats.py self-check OK")
