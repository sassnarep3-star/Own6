"""Pure-stdlib statistics for the NFL-309921cc pack.

No third-party dependency. Every routine is deterministic: the only random
source is ``random.Random`` seeded explicitly by the caller, so a rebuild
reproduces identical numbers.

Conventions
-----------
* ``n`` is the number of paired observations.
* Correlations return ``None`` when undefined (n < 3 or zero variance) rather
  than a fabricated number.
* p-values are two-sided.
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence, Tuple

__all__ = [
    "mean", "sd", "pearson", "spearman", "rank", "fisher_z_ci",
    "t_sf_two_sided", "ols_simple", "percentile_bootstrap_ci",
    "binomial_two_sided_p", "normal_cdf", "log_loss", "brier",
]


# --------------------------------------------------------------------------
# Descriptive
# --------------------------------------------------------------------------
def mean(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("mean of empty sequence")
    return sum(xs) / len(xs)


def sd(xs: Sequence[float], ddof: int = 1) -> Optional[float]:
    n = len(xs) - ddof
    if n <= 0:
        return None
    m = mean(xs)
    ss = sum((x - m) ** 2 for x in xs)
    return math.sqrt(ss / n)


def rank(xs: Sequence[float]) -> List[float]:
    """Average ranks, ties shared (the standard Spearman pre-step)."""
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


# --------------------------------------------------------------------------
# Correlation
# --------------------------------------------------------------------------
def pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0.0 or syy <= 0.0:
        return None
    r = sxy / math.sqrt(sxx * syy)
    return max(-1.0, min(1.0, r))


def spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    return pearson(rank(xs), rank(ys))


# --------------------------------------------------------------------------
# Student-t tail probability (regularized incomplete beta, Lentz continued fraction)
# --------------------------------------------------------------------------
def _betacf(a: float, b: float, x: float) -> float:
    tiny, eps = 1e-30, 3e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_sf_two_sided(t: float, df: float) -> float:
    """Two-sided p-value for Student-t."""
    if df <= 0:
        return float("nan")
    return _betai(df / 2.0, 0.5, df / (df + t * t))


def fisher_z_ci(r: float, n: int, level: float = 0.95) -> Optional[Tuple[float, float]]:
    """Fisher z confidence interval for a Pearson correlation."""
    if n < 4 or r is None or abs(r) >= 1.0:
        return None
    z = 0.5 * math.log((1.0 + r) / (1.0 - r))
    se = 1.0 / math.sqrt(n - 3.0)
    # 1.959964 for 95%; use the normal quantile via erf inverse approximation
    zc = _normal_quantile(1.0 - (1.0 - level) / 2.0)
    lo = math.tanh(z - zc * se)
    hi = math.tanh(z + zc * se)
    return (lo, hi)


def _normal_quantile(p: float) -> float:
    """Inverse standard normal CDF (Acklam-style rational approximation)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0,1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# --------------------------------------------------------------------------
# Regression
# --------------------------------------------------------------------------
def ols_simple(xs: Sequence[float], ys: Sequence[float]) -> dict:
    """Simple least squares y = a + b x, with inference on the slope and R^2."""
    n = len(xs)
    if n != len(ys) or n < 4:
        raise ValueError("ols_simple needs >= 4 paired observations")
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0.0:
        raise ValueError("zero variance in x")
    b = sxy / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    sse = sum(r * r for r in resid)
    syy = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - sse / syy if syy > 0 else float("nan")
    df = n - 2
    s2 = sse / df if df > 0 else float("nan")
    se_b = math.sqrt(s2 / sxx) if df > 0 else float("nan")
    t_b = b / se_b if se_b and se_b > 0 else float("nan")
    p_b = t_sf_two_sided(t_b, df) if se_b and se_b > 0 else float("nan")
    return {
        "n": n, "intercept": a, "slope": b, "r2": r2,
        "residual_sd": math.sqrt(s2) if df > 0 else float("nan"),
        "se_slope": se_b, "t_slope": t_b, "p_slope": p_b, "df": df,
        "residuals": resid, "sse": sse,
    }


# --------------------------------------------------------------------------
# Resampling
# --------------------------------------------------------------------------
def percentile_bootstrap_ci(xs: Sequence[float], ys: Sequence[float],
                            stat=pearson, draws: int = 10000,
                            seed: int = 20261113,
                            level: float = 0.95) -> Optional[Tuple[float, float]]:
    """Percentile bootstrap CI for a paired statistic (default: Pearson r)."""
    n = len(xs)
    if n < 4 or n != len(ys):
        return None
    rng = random.Random(seed)
    vals: List[float] = []
    for _ in range(draws):
        idx = [rng.randrange(n) for _ in range(n)]
        s = stat([xs[i] for i in idx], [ys[i] for i in idx])
        if s is not None:
            vals.append(s)
    if len(vals) < 100:
        return None
    vals.sort()
    lo = vals[int(((1 - level) / 2) * len(vals))]
    hi = vals[int((1 - (1 - level) / 2) * len(vals)) - 1]
    return (lo, hi)


# --------------------------------------------------------------------------
# Discrete / scoring
# --------------------------------------------------------------------------
def binomial_two_sided_p(k: int, n: int, p: float = 0.5) -> float:
    """Exact two-sided binomial test (used for win/loss skill tests)."""
    if n <= 0:
        return float("nan")
    probs = [_binom_pmf(i, n, p) for i in range(n + 1)]
    obs = probs[k]
    return min(1.0, sum(pr for pr in probs if pr <= obs * (1 + 1e-12)))


def _binom_pmf(k: int, n: int, p: float) -> float:
    return math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                    + k * math.log(p) + (n - k) * math.log(1 - p))


def brier(pairs: Sequence[Tuple[float, int]]) -> Optional[float]:
    """Mean squared error of probability forecasts against 0/1 outcomes."""
    if not pairs:
        return None
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def log_loss(pairs: Sequence[Tuple[float, int]], eps: float = 1e-9) -> Optional[float]:
    if not pairs:
        return None
    tot = 0.0
    for p, y in pairs:
        p = min(1 - eps, max(eps, p))
        tot += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return tot / len(pairs)
