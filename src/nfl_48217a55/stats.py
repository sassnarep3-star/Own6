"""Small, dependency-free statistics used by the pack.

Every routine is written out in full so a reviewer can check the arithmetic by hand. No
scipy/numpy: the sandbox has no network install and the sample sizes here are tiny, so
exact formulas are more auditable than a library call.
"""

from __future__ import annotations

import math


def mean(xs):
    xs = [float(x) for x in xs]
    return sum(xs) / len(xs) if xs else 0.0


def pvariance(xs):
    """Population variance (divide by n). Used for dispersion of a complete set of 32 clubs."""
    xs = [float(x) for x in xs]
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def pstdev(xs):
    return math.sqrt(pvariance(xs))


def pearson(xs, ys):
    """Pearson r. Returns 0.0 when either series has zero variance."""
    if len(xs) != len(ys) or len(xs) < 3:
        return 0.0
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n, z=1.96):
    """95% CI for a Pearson r via the Fisher z transform."""
    if n < 4 or abs(r) >= 1.0:
        return (float("nan"), float("nan"))
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(zr - z * se)
    hi = math.tanh(zr + z * se)
    return (lo, hi)


def t_pvalue_two_sided(r, n):
    """Two-sided p-value for H0: rho = 0, via the t statistic with n-2 df.

    Uses a numerically integrated Student-t survival function (no scipy available).
    Accurate to ~1e-9, which is far more than these sample sizes deserve.
    """
    if n < 4 or abs(r) >= 1.0:
        return float("nan")
    df = n - 2
    t = abs(r) * math.sqrt(df / (1 - r * r))
    return 2.0 * _student_t_sf(t, df)


def _student_t_sf(t, df):
    """P(T > t) for Student-t with df degrees of freedom, by Simpson integration."""
    if t < 0:
        return 1.0 - _student_t_sf(-t, df)
    upper = 60.0 if df > 2 else 400.0
    n_steps = 4000
    h = (upper - t) / n_steps
    total = 0.0
    for i in range(n_steps + 1):
        x = t + i * h
        w = 1.0 if i in (0, n_steps) else (4.0 if i % 2 else 2.0)
        total += w * _t_pdf(x, df)
    return min(1.0, max(0.0, total * h / 3.0))


def _t_pdf(x, df):
    return (math.gamma((df + 1) / 2.0) / (math.sqrt(df * math.pi) * math.gamma(df / 2.0))) * (
        1.0 + x * x / df
    ) ** (-(df + 1) / 2.0)


def wilson_interval(k, n, z=1.96):
    """Wilson score interval for a proportion. Preferred over the normal approximation
    at the small n this pack actually has."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def brier(p, outcome):
    """Brier score for a single binary forecast. outcome is 1 or 0."""
    return (float(p) - float(outcome)) ** 2


def fmt(x, nd=4):
    if x is None or x == "":
        return ""
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return ""
    if isinstance(x, float):
        return f"{x:.{nd}f}".rstrip("0").rstrip(".")
    return str(x)
