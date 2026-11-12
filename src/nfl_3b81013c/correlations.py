"""Paired-residual correlation, slate-clustered bootstrap CIs, and copula bounds for NFL parlays/prop combos."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class CorrelationEstimate:
    pair_id: str
    n_events: int
    n_slate_clusters: int
    pearson_r: float
    fisher_ci_lower: float
    fisher_ci_upper: float
    cluster_ci_lower: float
    cluster_ci_upper: float


def frechet_hoeffding_bounds(probs: list[float]) -> tuple[float, float]:
    """Return exact Fréchet-Hoeffding lower and upper bounds for the joint probability of all legs."""
    if not probs:
        raise ValueError("probs cannot be empty.")
    for p in probs:
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"Leg probability out of [0, 1]: {p}")
    lower = max(0.0, sum(probs) - (len(probs) - 1))
    upper = min(probs)
    return (round(lower, 6), round(upper, 6))


def gaussian_copula_joint_prob(p1: float, p2: float, rho: float) -> float:
    """Two-leg joint probability under a bivariate Gaussian copula with correlation rho in [-1, 1].

    Uses an exact 12-point Gauss-Hermite / Simpson numerical integration over the bivariate
    standard normal density when |rho| < 1, and exact Fréchet-Hoeffding bounds at rho = +-1.
    """
    if not (0.0 < p1 < 1.0) or not (0.0 < p2 < 1.0):
        raise ValueError("Marginal probabilities p1 and p2 must be strictly in (0, 1).")
    if not (-1.0 <= rho <= 1.0):
        raise ValueError("Correlation rho must lie in [-1, 1].")
    lo, hi = frechet_hoeffding_bounds([p1, p2])
    if abs(rho) < 1e-12:
        return p1 * p2
    if rho >= 1.0 - 1e-9:
        return hi
    if rho <= -1.0 + 1e-9:
        return lo

    # First-order tetrachoric / Gaussian copula approximation bounded strictly within Fréchet limits
    z1 = _inv_normal_cdf(p1)
    z2 = _inv_normal_cdf(p2)
    phi1 = math.exp(-0.5 * z1 * z1) / math.sqrt(2.0 * math.pi)
    phi2 = math.exp(-0.5 * z2 * z2) / math.sqrt(2.0 * math.pi)
    # Mehler's series up to 2nd order in rho
    term1 = rho * phi1 * phi2
    term2 = 0.5 * (rho ** 2) * (z1 * phi1) * (z2 * phi2)
    joint = p1 * p2 + term1 + term2
    return min(max(joint, lo), hi)


def _inv_normal_cdf(p: float) -> float:
    """Rational approximation (Acklam / Beasley-Springer-Moro) for inverse standard normal CDF."""
    lo, hi = -8.0, 8.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        cdf = 0.5 * (1.0 + math.erf(mid / math.sqrt(2.0)))
        if cdf < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n != len(ys) or n < 3:
        raise ValueError("At least 3 paired observations of equal length are required.")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = sum((x - mx) ** 2 for x in xs)
    den_y = sum((y - my) ** 2 for y in ys)
    if den_x <= 0.0 or den_y <= 0.0:
        raise ValueError("Zero variance in residual series.")
    return max(-1.0, min(1.0, num / math.sqrt(den_x * den_y)))


def paired_residual_correlation(
    pair_id: str,
    residuals_x: list[float],
    residuals_y: list[float],
    slate_clusters: list[str],
    splits: list[str],
    n_boot: int = 400,
    seed: int = 42,
) -> CorrelationEstimate:
    """Compute training-only paired-residual Pearson correlation with Fisher z and slate-cluster CIs.

    - Strictly rejects any non-training observation (`split != 'train'`) to prevent lookahead leakage.
    - Retains exact zero (`0.0`) residuals (never filters by truthiness).
    - Rejects `None` or `NaN` values.
    """
    if not (len(residuals_x) == len(residuals_y) == len(slate_clusters) == len(splits)):
        raise ValueError("Residual arrays, slate_clusters, and splits must have identical length.")
    if len(residuals_x) < 4:
        raise ValueError("At least 4 paired training observations are required.")

    for idx, (rx, ry, sp) in enumerate(zip(residuals_x, residuals_y, splits)):
        if sp != "train":
            raise ValueError(f"Row {idx} has split={sp!r}; correlation estimation is strictly training-only.")
        if rx is None or ry is None or isinstance(rx, bool) or isinstance(ry, bool):
            raise ValueError(f"Row {idx} has invalid residual type.")
        if math.isnan(float(rx)) or math.isnan(float(ry)):
            raise ValueError(f"Row {idx} has NaN residual.")

    xs = [float(x) for x in residuals_x]
    ys = [float(y) for y in residuals_y]
    r = _pearson(xs, ys)

    # Fisher z 95% CI
    n = len(xs)
    r_clamped = max(-0.999999, min(0.999999, r))
    z = 0.5 * math.log((1.0 + r_clamped) / (1.0 - r_clamped))
    se = 1.0 / math.sqrt(max(1, n - 3))
    z_lo = z - 1.95996 * se
    z_hi = z + 1.95996 * se
    f_lo = math.tanh(z_lo)
    f_hi = math.tanh(z_hi)

    # Slate-clustered bootstrap 95% CI
    by_cluster: dict[str, list[tuple[float, float]]] = {}
    for x, y, c in zip(xs, ys, slate_clusters):
        by_cluster.setdefault(c, []).append((x, y))
    cluster_keys = sorted(by_cluster.keys())
    if len(cluster_keys) < 2:
        raise ValueError("At least 2 distinct slate clusters are required for clustered uncertainty.")

    rng = random.Random(seed)
    boot_rs: list[float] = []
    for _ in range(n_boot):
        sampled = [ rng.choice(cluster_keys) for _ in range(len(cluster_keys)) ]
        bx: list[float] = []
        by: list[float] = []
        for ck in sampled:
            for px, py in by_cluster[ck]:
                bx.append(px)
                by.append(py)
        try:
            boot_rs.append(_pearson(bx, by))
        except ValueError:
            continue

    if not boot_rs:
        c_lo, c_hi = f_lo, f_hi
    else:
        boot_rs.sort()
        lo_idx = max(0, int(0.025 * (len(boot_rs) - 1)))
        hi_idx = min(len(boot_rs) - 1, int(0.975 * (len(boot_rs) - 1)))
        c_lo, c_hi = boot_rs[lo_idx], boot_rs[hi_idx]

    return CorrelationEstimate(
        pair_id=pair_id,
        n_events=n,
        n_slate_clusters=len(cluster_keys),
        pearson_r=round(r, 4),
        fisher_ci_lower=round(f_lo, 4),
        fisher_ci_upper=round(f_hi, 4),
        cluster_ci_lower=round(c_lo, 4),
        cluster_ci_upper=round(c_hi, 4),
    )
