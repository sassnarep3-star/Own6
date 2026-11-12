"""Correlation and joint-outcome estimation for combos, SGPs and parlays.

Rules implemented here:
  * A parlay price is NOT evidence that legs are independent. Multiplication is
    only allowed when an explicit dependence test fails to reject independence.
  * Same-game dependence is estimated from *paired* residuals, not from marginal
    rates, and every estimate carries a clustered bootstrap interval.
  * The joint probability used for combo pricing is the empirical (or copula)
    joint, floored at the Fréchet lower bound implied by the marginals.

References for the methods (definitions only, not validation of any edge):
  Pearson correlation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
  Bootstrap CI:        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
"""
from __future__ import annotations

import itertools
import math

import numpy as np


def pearson(x: np.ndarray, y: np.ndarray) -> float | None:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3 or len(y) < 3 or len(x) != len(y):
        return None
    sx, sy = x.std(), y.std()
    if sx == 0 or sy == 0:
        return None
    return float(np.mean((x - x.mean()) * (y - y.mean())) / (sx * sy))


def phi(binary_a: np.ndarray, binary_b: np.ndarray) -> float | None:
    """Phi coefficient for two binary legs (equivalent to Pearson on 0/1)."""
    return pearson(binary_a, binary_b)


def cluster_bootstrap_ci(values: np.ndarray, clusters: np.ndarray, stat, n_boot: int = 2000,
                         alpha: float = 0.05, seed: int = 20261112) -> tuple[float, float] | None:
    """Percentile CI of `stat` resampling whole clusters (games/slates), not rows."""
    values = np.asarray(values, dtype=float)
    if len(values) < 3:
        return None
    uniq = np.unique(clusters)
    if len(uniq) < 5:
        return None
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(clusters == c) for c in uniq]
    out = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        idx = np.concatenate([groups[i] for i in pick])
        v = stat(values[idx])
        if v is not None and np.isfinite(v):
            out.append(v)
    if len(out) < 100:
        return None
    lo, hi = np.percentile(out, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def fisher_z_ci(r: float, n: int, alpha: float = 0.05) -> tuple[float, float] | None:
    """Fisher z interval; used as a diagnostic alongside the clustered bootstrap."""
    if n <= 3 or abs(r) >= 1:
        return None
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    from scipy.stats import norm
    zc = norm.ppf(1 - alpha / 2)
    return float(math.tanh(z - zc * se)), float(math.tanh(z + zc * se))


def frechet_bounds(p_a: float, p_b: float) -> tuple[float, float]:
    """Feasible joint-probability range for two events with marginals p_a, p_b."""
    return max(0.0, p_a + p_b - 1.0), min(p_a, p_b)


def bivariate_normal_cdf(h: float, k: float, rho: float) -> float:
    """P(X <= h, Y <= k) for a standard bivariate normal with correlation rho.

    Uses the exact 1-D reduction
        Phi2(h, k; rho) = integral_{-inf}^{h} phi(x) Phi((k - rho x)/sqrt(1-rho^2)) dx
    evaluated by adaptive quadrature. scipy's `mvn.mvnun` was removed in 1.9,
    so this avoids a private API and is checked against the rho = 0 product and
    the rho -> 1 limit in the test suite.
    """
    import math as _m
    from scipy.integrate import quad
    from scipy.stats import norm
    if not (-1.0 < rho < 1.0):
        rho = 0.999999 if rho >= 1.0 else -0.999999
    if abs(rho) < 1e-12:
        return float(norm.cdf(h) * norm.cdf(k))
    scale = _m.sqrt(1.0 - rho * rho)
    inner = lambda x: norm.cdf((k - rho * x) / scale) * norm.pdf(x)
    val, _err = quad(inner, -8.0, h, limit=200)
    return float(min(max(val, 0.0), 1.0))


def joint_from_copula(p_a: float, p_b: float, rho: float) -> float | None:
    """Gaussian-copula joint for two threshold events, clipped to the Frechet bounds."""
    if rho is None or p_a is None or p_b is None:
        return None
    if not (0.0 < p_a < 1.0 and 0.0 < p_b < 1.0):
        return None
    from scipy.stats import norm
    za, zb = float(norm.ppf(p_a)), float(norm.ppf(p_b))
    joint = bivariate_normal_cdf(za, zb, float(rho))
    lo, hi = frechet_bounds(p_a, p_b)
    return float(min(max(joint, lo), hi))


def independence_test(binary_a: np.ndarray, binary_b: np.ndarray) -> dict:
    """Two-sided Fisher exact test on the 2x2 table of paired binary outcomes."""
    a = np.asarray(binary_a).astype(bool)
    b = np.asarray(binary_b).astype(bool)
    n11 = int(np.sum(a & b)); n10 = int(np.sum(a & ~b))
    n01 = int(np.sum(~a & b)); n00 = int(np.sum(~a & ~b))
    table = [[n11, n10], [n01, n00]]
    try:
        from scipy.stats import fisher_exact
        odds, p = fisher_exact(table)
    except Exception:  # pragma: no cover
        odds, p = float("nan"), float("nan")
    return {"n11": n11, "n10": n10, "n01": n01, "n00": n00, "odds_ratio": float(odds), "p_value": float(p)}


def required_n_for_r(r: float, power: float = 0.8, alpha: float = 0.05) -> int | None:
    """Approximate sample size to detect correlation r (Fisher z, two-sided)."""
    if r is None or abs(r) >= 1 or r == 0:
        return None
    from scipy.stats import norm
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    return int(math.ceil(((z_alpha + z_beta) / math.atanh(abs(r))) ** 2 + 3))


def parlay_prob(joint_p: float, payout_decimal: float) -> dict:
    """Expected value of a two-leg parlay, per 1 unit staked. No vig removal."""
    return {
        "joint_probability": joint_p,
        "fair_decimal_for_joint": (1.0 / joint_p) if joint_p > 0 else None,
        "offered_decimal": payout_decimal,
        "ev_per_unit": joint_p * payout_decimal - 1.0,
    }


def correlation_matrix(series: dict[str, np.ndarray], min_n: int = 30) -> dict:
    """Pairwise Pearson matrix with n; missing pairs stay None (never zero-filled)."""
    names = sorted(series)
    out = {}
    for a, b in itertools.combinations(names, 2):
        x, y = series[a], series[b]
        n = min(len(x), len(y))
        r = pearson(x[:n], y[:n]) if n >= min_n else None
        out[f"{a}|{b}"] = {"r": r, "n": int(n) if r is not None else None,
                           "ci_fisher": fisher_z_ci(r, n) if r is not None else None}
    return out
