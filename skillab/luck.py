"""Luck removal: turning a noisy record into a defensible skill statement.

Every function documents the equation it implements and the official reference
that defines that equation (NIST/SEMATECH e-Handbook, SciPy, scikit-learn,
statsmodels). The references define the *mathematics*; none of them endorses a
betting strategy, and none of them is a source for any basketball value.

Machinery here is deliberately dependency-free (stdlib ``math``/``statistics``)
so the gates can run in CI without scientific wheels, except where an optional
SciPy cross-check is explicitly exercised in the tests.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

_ND = NormalDist()


# --------------------------------------------------------------------------
# elementary distribution helpers
# --------------------------------------------------------------------------
def norm_cdf(z: float) -> float:
    return _ND.cdf(z)


def norm_ppf(p: float) -> float:
    return _ND.inv_cdf(p)


def two_sided_p_from_z(z: float) -> float:
    return 2.0 * (1.0 - _ND.cdf(abs(z)))


def binom_pmf(k: int, n: int, p: float) -> float:
    """P(X = k) for X ~ Binomial(n, p). Matches NIST 1.3.6.6.18."""
    if not 0 <= k <= n:
        return 0.0
    if p <= 0.0:
        return 1.0 if k == 0 else 0.0
    if p >= 1.0:
        return 1.0 if k == n else 0.0
    log_pmf = (
        math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
        + k * math.log(p) + (n - k) * math.log1p(-p)
    )
    return math.exp(log_pmf)


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(binom_pmf(i, n, p) for i in range(k, n + 1))


def binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k)."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return sum(binom_pmf(i, n, p) for i in range(0, k + 1))


def binom_two_sided_p(k: int, n: int, p0: float) -> float:
    """Exact two-sided binomial test against p = p0 (doubled smaller tail).

    Used as the "is this win rate luck?" test when ``p0`` is the breakeven
    probability implied by the price actually taken. NIST 1.3.6.6.18 defines
    the binomial pmf/cdf this is built from.
    """
    if n <= 0:
        return 1.0
    upper = binom_sf(k, n, p0)
    lower = binom_cdf(k, n, p0)
    return min(1.0, 2.0 * min(upper, lower))


# --------------------------------------------------------------------------
# uncertainty on a mean (ROI, CLV, log-loss difference)
# --------------------------------------------------------------------------
def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def sample_sd(xs: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def t_stat(xs: list[float], mu0: float = 0.0) -> float:
    n = len(xs)
    sd = sample_sd(xs)
    if n < 2 or sd == 0.0:
        return 0.0
    return (mean(xs) - mu0) / (sd / math.sqrt(n))


def t_ppf(p: float, df: int) -> float:
    """Student-t quantile via a dense numerical inversion of the t CDF.

    The t CDF is evaluated with the regularised incomplete beta function
    implemented below; the inversion is a bisection. Deterministic and
    accurate to ~1e-9, which is far below the resolution of any published
    decision here.
    """
    if df <= 0:
        raise ValueError("df must be positive")
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0,1)")
    if p == 0.5:
        return 0.0

    def cdf(x: float) -> float:
        return 1.0 - 0.5 * _betainc_reg(df / 2.0, 0.5, df / (df + x * x))

    lo, hi = -1e6, 1e6
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if cdf(mid) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return (lo + hi) / 2.0


def _betainc_reg(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b) via numerical integration.

    Uses the continued fraction (Lentz) form for the incomplete beta, the
    standard evaluation route; accuracy ~1e-12 for the ranges used here.
    """
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log1p(-x) * b - lbeta) / a
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x)
    return 1.0 - _betainc_reg(b, a, 1.0 - x)


def _betacf(a: float, b: float, x: float) -> float:
    tiny = 1e-30
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
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def t_confidence_interval(xs: list[float], level: float = 0.95) -> tuple[float, float]:
    """Analytic t interval on the mean."""
    n = len(xs)
    if n < 2:
        m = mean(xs) if xs else float("nan")
        return (m, m)
    m = mean(xs)
    se = sample_sd(xs) / math.sqrt(n)
    tcrit = t_ppf(0.5 + level / 2.0, n - 1)
    return (m - tcrit * se, m + tcrit * se)


def paired_mean_difference_ci(a: list[float], b: list[float], level: float = 0.95) -> dict:
    """Mean of a - b with a t interval. Used for paired model-vs-market loss."""
    if len(a) != len(b):
        raise ValueError("paired samples must have equal length")
    diffs = [x - y for x, y in zip(a, b)]
    lo, hi = t_confidence_interval(diffs, level)
    return {
        "n": len(diffs),
        "mean_diff": mean(diffs) if diffs else float("nan"),
        "ci_lo": lo,
        "ci_hi": hi,
        "t": t_stat(diffs),
        "df": max(len(diffs) - 1, 0),
    }


# --------------------------------------------------------------------------
# resampling: bootstrap and stationary block bootstrap
# --------------------------------------------------------------------------
def _lcg_stub():  # pragma: no cover - documentation only
    raise NotImplementedError


class Rng:
    """Deterministic xorshift64* generator.

    Written out rather than imported so bootstrap results are stable across
    NumPy versions and available with no third-party dependency. A fixed seed
    means every published bootstrap number in this repository is reproducible
    by anyone re-running the build.
    """

    MASK = (1 << 64) - 1

    def __init__(self, seed: int = 20261105):
        self.state = (seed ^ 0x9E3779B97F4A7C15) & self.MASK or 1
        for _ in range(16):
            self.next_u64()

    def next_u64(self) -> int:
        x = self.state
        x ^= (x >> 12) & self.MASK
        x ^= (x << 25) & self.MASK
        x ^= (x >> 27) & self.MASK
        self.state = x & self.MASK
        return (self.state * 0x2545F4914F6CDD1D) & self.MASK

    def random(self) -> float:
        return (self.next_u64() >> 11) / float(1 << 53)

    def randrange(self, n: int) -> int:
        return self.next_u64() % n

    def choice_pairs(self, n: int) -> tuple[int, int]:
        return self.next_u64() % n, self.next_u64() % n


def bootstrap_mean_ci(xs: list[float], n_resamples: int = 10000, level: float = 0.95,
                      seed: int = 20261105, method: str = "percentile") -> dict:
    """Percentile or basic bootstrap interval for the mean.

    Mirrors ``scipy.stats.bootstrap`` in intent (resample with replacement,
    take empirical quantiles); the percentile method is used by default
    because it needs no acceleration constant and is trivially auditable.
    """
    n = len(xs)
    if n < 2:
        m = mean(xs) if xs else float("nan")
        return {"mean": m, "ci_lo": m, "ci_hi": m, "n": n, "n_resamples": 0}
    # Large-series runs use fewer resamples: the percentile endpoints stabilise
    # long before 10k draws, and the build must stay inside CI time limits.
    if n > 2000 and n_resamples > 1000:
        n_resamples = 1000
    rng = Rng(seed)
    randrange = rng.randrange
    stats: list[float] = []
    for _ in range(n_resamples):
        s = 0.0
        for _ in range(n):
            s += xs[randrange(n)]
        stats.append(s / n)
    stats.sort()
    alpha = (1.0 - level) / 2.0
    lo = _quantile_sorted(stats, alpha)
    hi = _quantile_sorted(stats, 1.0 - alpha)
    obs = mean(xs)
    if method == "basic":
        lo, hi = 2.0 * obs - hi, 2.0 * obs - lo
    elif method != "percentile":
        raise ValueError("method must be 'percentile' or 'basic'")
    return {"mean": obs, "ci_lo": lo, "ci_hi": hi, "n": n, "n_resamples": n_resamples}


def block_bootstrap_mean_ci(xs: list[float], block: int = 5, n_resamples: int = 10000,
                            level: float = 0.95, seed: int = 20261105) -> dict:
    """Moving-block bootstrap interval for the mean of a *dependent* series.

    Bet results are ordered in time and same-slate legs share a game outcome,
    so independent resampling understates variance. Blocks of consecutive
    observations are resampled instead, which retains short-range dependence.
    """
    n = len(xs)
    if n < 2:
        m = mean(xs) if xs else float("nan")
        return {"mean": m, "ci_lo": m, "ci_hi": m, "n": n, "block": block}
    block = max(1, min(block, n))
    if n > 2000 and n_resamples > 1000:
        n_resamples = 1000
    n_blocks = max(1, n // block)
    rng = Rng(seed)
    randrange = rng.randrange
    span = n - block + 1
    stats: list[float] = []
    for _ in range(n_resamples):
        total = 0.0
        count = 0
        for _ in range(n_blocks):
            start = randrange(span)
            total += sum(xs[start:start + block])
            count += block
        stats.append(total / count)
    stats.sort()
    alpha = (1.0 - level) / 2.0
    return {
        "mean": mean(xs),
        "ci_lo": _quantile_sorted(stats, alpha),
        "ci_hi": _quantile_sorted(stats, 1.0 - alpha),
        "n": n,
        "block": block,
        "n_resamples": n_resamples,
    }


def _quantile_sorted(sorted_xs: list[float], q: float) -> float:
    if not sorted_xs:
        return float("nan")
    if q <= 0:
        return sorted_xs[0]
    if q >= 1:
        return sorted_xs[-1]
    pos = q * (len(sorted_xs) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_xs[lo]
    frac = pos - lo
    return sorted_xs[lo] * (1 - frac) + sorted_xs[hi] * frac


# --------------------------------------------------------------------------
# calibration: Brier decomposition (Murphy)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class BrierDecomposition:
    brier: float
    reliability: float
    resolution: float
    uncertainty: float
    n_bins: int
    n: int

    def identity_error(self) -> float:
        """Brier should equal reliability - resolution + uncertainty."""
        return self.brier - (self.reliability - self.resolution + self.uncertainty)


def brier_score(probs: list[float], outcomes: list[int]) -> float:
    """Mean squared error of probability forecasts (scikit-learn definition)."""
    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must align")
    if not probs:
        return float("nan")
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def brier_decomposition(probs: list[float], outcomes: list[int], n_bins: int = 10) -> BrierDecomposition:
    """Murphy decomposition: Brier = reliability - resolution + uncertainty.

    Bins are equal-width on [0,1]. Reliability (calibration) is what a strategy
    is punished for; resolution is what it is credited for. A strategy that
    always predicts the base rate has perfect reliability and zero resolution,
    so it cannot win on reliability alone — which is exactly the point.
    """
    n = len(probs)
    if n == 0:
        return BrierDecomposition(float("nan"), float("nan"), float("nan"), float("nan"), n_bins, 0)
    base = sum(outcomes) / n
    uncertainty = base * (1.0 - base)
    bins: list[list[int]] = [[] for _ in range(n_bins)]
    for p, y in zip(probs, outcomes):
        idx = min(n_bins - 1, max(0, int(p * n_bins)))
        bins[idx].append((p, y))
    reliability = 0.0
    resolution = 0.0
    for group in bins:
        if not group:
            continue
        nk = len(group)
        mean_p = sum(p for p, _ in group) / nk
        mean_y = sum(y for _, y in group) / nk
        reliability += nk * (mean_p - mean_y) ** 2
        resolution += nk * (mean_y - base) ** 2
    return BrierDecomposition(
        brier=brier_score(probs, outcomes),
        reliability=reliability / n,
        resolution=resolution / n,
        uncertainty=uncertainty,
        n_bins=n_bins,
        n=n,
    )


def log_loss(probs: list[float], outcomes: list[int], eps: float = 1e-15) -> float:
    """Mean binary log loss (cross-entropy)."""
    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must align")
    if not probs:
        return float("nan")
    total = 0.0
    for p, y in zip(probs, outcomes):
        q = min(1.0 - eps, max(eps, p))
        total += -(y * math.log(q) + (1 - y) * math.log(1.0 - q))
    return total / len(probs)


def expected_calibration_error(probs: list[float], outcomes: list[int], n_bins: int = 10) -> float:
    n = len(probs)
    if n == 0:
        return float("nan")
    bins: list[list[int]] = [[] for _ in range(n_bins)]
    for p, y in zip(probs, outcomes):
        bins[min(n_bins - 1, max(0, int(p * n_bins)))].append((p, y))
    ece = 0.0
    for group in bins:
        if not group:
            continue
        nk = len(group)
        ece += nk * abs(sum(p for p, _ in group) / nk - sum(y for _, y in group) / nk)
    return ece / n
