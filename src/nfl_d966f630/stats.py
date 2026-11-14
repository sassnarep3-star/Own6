"""Small, dependency-free statistics used by the pack.

Every function here is plain arithmetic so a reviewer can recompute any published
number with nothing but the Python standard library. Sources for the *methods*
(the standard formulas) are named in ``method_reference`` on each published row;
no method source is presented as evidence about football.
"""

from __future__ import annotations

import math
from typing import Sequence


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def sd(xs: Sequence[float]) -> float:
    """Sample standard deviation (n-1 denominator)."""
    n = len(xs)
    if n < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = min(len(xs), len(ys))
    if n < 3:
        return float("nan")
    mx, my = mean(xs[:n]), mean(ys[:n])
    sxx = sum((x - mx) ** 2 for x in xs[:n])
    syy = sum((y - my) ** 2 for y in ys[:n])
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs[:n], ys[:n]))
    if sxx == 0 or syy == 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def rank(vals: Sequence[float]) -> list[float]:
    """Average ranks, ties shared (used for Spearman)."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    return pearson(rank(list(xs)), rank(list(ys)))


def fisher_ci(r: float, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Fisher z 95% confidence interval for a Pearson correlation."""
    if n < 4 or not (-1.0 < r < 1.0):
        return (float("nan"), float("nan"))
    z = atanh(r)
    se = 1.0 / math.sqrt(n - 3.0)
    crit = normal_ppf(1.0 - alpha / 2.0)
    return (tanh(z - crit * se), tanh(z + crit * se))


def pearson_p(r: float, n: int) -> float:
    """Two-sided p-value for a Pearson correlation via the t distribution,
    using a normal approximation for the critical value when n is small enough
    that scipy is unavailable. Documented as an approximation on the page."""
    if n < 4 or abs(r) >= 1.0:
        return float("nan")
    t = r * math.sqrt((n - 2.0) / (1.0 - r * r))
    # Normal approximation to the t tail (conservative for small n: the true
    # two-sided p is larger, which is stated wherever a p-value is published).
    return 2.0 * (1.0 - normal_cdf(abs(t)))


def wilson_interval(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (no continuity correction)."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2.0 * n)
    m = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return ((c - m) / d, (c + m) / d)


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def normal_ppf(p: float) -> float:
    """Inverse standard normal CDF by bisection on normal_cdf.

    Deterministic and dependency-free; accurate to ~1e-12 in x for any p in
    (0, 1) that the bracket covers. Used for Wilson intervals and Fisher CIs.
    """
    if not (0.0 < p < 1.0):
        raise ValueError("p must be in (0,1)")
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if normal_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def atanh(x: float) -> float:
    return 0.5 * math.log((1.0 + x) / (1.0 - x))


def tanh(x: float) -> float:
    return math.tanh(x)


def bivariate_normal_cdf(h: float, k: float, rho: float, nodes: int = 121) -> float:
    """P(X <= h, Y <= k) for a standard bivariate normal with correlation rho.

    Gauss-Legendre quadrature of the standard one-dimensional integral
        P = int_{-inf}^{h} phi(x) * Phi((k - rho x)/sqrt(1-rho^2)) dx
    Truncated to [-8, 8]; deterministic, no randomness, no dependencies.
    """
    if not (-1.0 < rho < 1.0):
        raise ValueError("rho must be strictly inside (-1, 1)")
    lo, hi = -8.0, min(h, 8.0)
    if hi <= lo:
        return 0.0
    n = nodes if nodes % 2 == 1 else nodes + 1
    xs, ws = leggauss(n)
    half = (hi - lo) / 2.0
    mid = (hi + lo) / 2.0
    s = math.sqrt(max(1.0 - rho * rho, 1e-12))
    total = 0.0
    for xi, wi in zip(xs, ws):
        x = mid + half * xi
        total += wi * half * normal_pdf(x) * normal_cdf((k - rho * x) / s)
    return max(0.0, min(1.0, total))


def leggauss(n: int) -> tuple[list[float], list[float]]:
    """Legendre nodes/weights on [-1,1] by Newton iteration (n odd, n <= 199)."""
    nodes, weights = [], []
    for i in range(1, (n // 2) + 1):
        x = math.cos(math.pi * (i - 0.25) / (n + 0.5))
        for _ in range(60):
            p0 = 1.0
            p1 = x
            for k in range(2, n + 1):
                p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
            dp = n * (x * p1 - p0) / (x * x - 1.0)
            dx = -p1 / dp
            x += dx
            if abs(dx) < 1e-15:
                break
        nodes.extend([-x, x])
        w = 2.0 / ((1.0 - x * x) * dp * dp)
        weights.extend([w, w])
    order = sorted(range(len(nodes)), key=lambda j: nodes[j])
    return [nodes[j] for j in order], [weights[j] for j in order]


def american_from_prob(p: float) -> str:
    """No-vig American odds for a probability, rounded to the nearest 5."""
    if not (0.0 < p < 1.0):
        return ""
    if p >= 0.5:
        return f"-{int(round(100.0 * p / (1.0 - p) / 5.0) * 5)}"
    return f"+{int(round(100.0 * (1.0 - p) / p / 5.0) * 5)}"


def round_half_up(x: float, step: float = 0.5) -> float:
    return math.floor(x / step + 0.5) * step


def fmt(x: float | None, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return f"{x:.{nd}f}"


def logloss(ps: Sequence[float], ys: Sequence[int]) -> float:
    if not ps:
        return float("nan")
    eps = 1e-12
    tot = 0.0
    for p, y in zip(ps, ys):
        p = min(max(p, eps), 1 - eps)
        tot += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return tot / len(ps)


def brier(ps: Sequence[float], ys: Sequence[int]) -> float:
    if not ps:
        return float("nan")
    return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps)
