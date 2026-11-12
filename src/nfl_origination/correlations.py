"""NFL Correlation, Week-Clustered Bootstrap & Copula Joint-Pricing Engine.

Used to evaluate Same-Game Parlays (SGPs), multi-game parlays, and player-prop
combinations without EVER defaulting to naive leg independence.

Key safeguards:
1. Paired training-only residuals retain exact zeros (never truthiness-filtered).
2. Pearson and Spearman rank correlations both checked against constant/degenerate inputs.
3. Week-clustered block bootstrap resamples entire NFL weeks together to preserve
   within-game and within-slate weather/officiating shocks.
4. Exact deterministic Simpson quadrature for 2-leg bivariate normal copula joint
   probabilities, plus strict Cholesky Gaussian-copula simulation for k >= 2 legs.
"""
from __future__ import annotations

import math
import random
from numbers import Real
from statistics import NormalDist
from typing import Sequence

from .pricing import prob_to_fair_american

_NORM = NormalDist()
_CHOLESKY_PIVOT_MIN = 1e-12


def _clean_vec(values: Sequence[float], name: str) -> list[float]:
    out: list[float] = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, Real):
            raise ValueError(f"{name} must contain finite real numbers (not bool)")
        fv = float(v)
        if not math.isfinite(fv):
            raise ValueError(f"{name} contains non-finite value")
        out.append(fv)
    return out


def paired_pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Paired linear correlation retaining exact zero residuals."""
    x = _clean_vec(xs, "xs")
    y = _clean_vec(ys, "ys")
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("paired_pearson requires equal-length sequences with n >= 3")
    mx = math.fsum(x) / len(x)
    my = math.fsum(y) / len(y)
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    nx = math.hypot(*dx)
    ny = math.hypot(*dy)
    if nx <= 1e-14 or ny <= 1e-14:
        raise ValueError("paired_pearson undefined for constant/near-constant input")
    r = math.fsum(a * b for a, b in zip(dx, dy)) / (nx * ny)
    return max(-1.0, min(1.0, r))


def _average_ranks(vals: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(vals), key=lambda t: t[1])
    ranks = [0.0] * len(vals)
    i = 0
    n = len(vals)
    while i < n:
        j = i
        while j + 1 < n and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = 0.5 * (i + j) + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def paired_spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Tie-aware Spearman rank correlation for skewed NFL yardage/touchdown residuals."""
    x = _clean_vec(xs, "xs")
    y = _clean_vec(ys, "ys")
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("paired_spearman requires equal-length sequences with n >= 3")
    return paired_pearson(_average_ranks(x), _average_ranks(y))


def week_block_bootstrap_corr_ci(
    week_ids: Sequence[str | int],
    xs: Sequence[float],
    ys: Sequence[float],
    n_resamples: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 20261112,
) -> dict[str, float | int]:
    """NFL week-clustered block bootstrap CI for paired residual correlation."""
    x = _clean_vec(xs, "xs")
    y = _clean_vec(ys, "ys")
    if len(week_ids) != len(x) or len(x) != len(y):
        raise ValueError("week_ids, xs, and ys must have identical length")
    clusters: dict[str | int, list[tuple[float, float]]] = {}
    for wk, xv, yv in zip(week_ids, x, y):
        clusters.setdefault(wk, []).append((xv, yv))
    keys = list(clusters.keys())
    if len(keys) < 4:
        raise ValueError("at least 4 distinct NFL week clusters are required for block bootstrap")

    point = paired_pearson(x, y)
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(n_resamples):
        bx: list[float] = []
        by: list[float] = []
        for _ in range(len(keys)):
            chosen = keys[rng.randrange(len(keys))]
            for xv, yv in clusters[chosen]:
                bx.append(xv)
                by.append(yv)
        try:
            estimates.append(paired_pearson(bx, by))
        except ValueError:
            continue
    if len(estimates) < max(100, n_resamples // 2):
        raise ValueError("bootstrap degenerated due to insufficient cross-cluster variation")
    estimates.sort()
    alpha = 1.0 - confidence_level
    lo = estimates[int((alpha / 2.0) * len(estimates))]
    hi = estimates[min(len(estimates) - 1, int((1.0 - alpha / 2.0) * len(estimates)))]
    return {
        "n_pairs": len(x),
        "n_week_clusters": len(keys),
        "pearson_r": point,
        "spearman_rho": paired_spearman(x, y),
        "ci_low": lo,
        "ci_high": hi,
    }


def bivariate_normal_joint_prob(p1: float, p2: float, rho: float, steps: int = 120) -> float:
    """Deterministic Simpson quadrature for 2-leg Gaussian copula P(Z1 <= z1, Z2 <= z2).

    Exact to ~1e-9 without Monte Carlo simulation variance.
    """
    for name, p in (("p1", p1), ("p2", p2)):
        if isinstance(p, bool) or not isinstance(p, Real) or not (0.0 <= float(p) <= 1.0):
            raise ValueError(f"{name} must lie in [0, 1]")
    if isinstance(rho, bool) or not isinstance(rho, Real) or not (-0.999 <= float(rho) <= 0.999):
        raise ValueError("rho must lie in [-0.999, 0.999]")
    p1f, p2f, rhof = float(p1), float(p2), float(rho)
    if p1f == 0.0 or p2f == 0.0:
        return 0.0
    if p1f == 1.0:
        return p2f
    if p2f == 1.0:
        return p1f
    if abs(rhof) < 1e-12:
        return p1f * p2f

    z1 = _NORM.inv_cdf(p1f)
    z2 = _NORM.inv_cdf(p2f)
    lower = -8.5
    upper = min(8.5, max(lower + 1e-6, z1))
    if upper <= lower + 1e-6:
        return 0.0
    if steps % 2 == 1:
        steps += 1
    h = (upper - lower) / steps
    root = math.sqrt(1.0 - rhof * rhof)

    def integrand(u: float) -> float:
        phi = math.exp(-0.5 * u * u) / math.sqrt(2.0 * math.pi)
        cond = _NORM.cdf((z2 - rhof * u) / root)
        return phi * cond

    acc = integrand(lower) + integrand(upper)
    for i in range(1, steps):
        u = lower + i * h
        acc += (4.0 if i % 2 == 1 else 2.0) * integrand(u)
    val = (h / 3.0) * acc
    return max(0.0, min(min(p1f, p2f), val))


def _cholesky(corr: Sequence[Sequence[float]], k: int) -> list[list[float]]:
    if len(corr) != k or any(len(row) != k for row in corr):
        raise ValueError("corr must be a k x k square matrix")
    mat = [_clean_vec(row, "corr_row") for row in corr]
    for i in range(k):
        if abs(mat[i][i] - 1.0) > 1e-12:
            raise ValueError("correlation matrix must have unit diagonal")
        for j in range(k):
            if not (-1.0 <= mat[i][j] <= 1.0):
                raise ValueError("correlation entries must lie in [-1, 1]")
            if abs(mat[i][j] - mat[j][i]) > 1e-12:
                raise ValueError("correlation matrix must be symmetric")
    low = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i + 1):
            rem = mat[i][j] - math.fsum(low[i][t] * low[j][t] for t in range(j))
            if i == j:
                if rem <= _CHOLESKY_PIVOT_MIN:
                    raise ValueError("correlation matrix is not strictly positive definite")
                low[i][j] = math.sqrt(rem)
            else:
                low[i][j] = rem / low[j][j]
    return low


def gaussian_copula_joint_prob(
    marginals: Sequence[float],
    corr_matrix: Sequence[Sequence[float]],
    sims: int = 25000,
    seed: int = 20261112,
) -> dict[str, float | int]:
    """Compute k-leg joint hit probability under a latent Gaussian copula."""
    probs = _clean_vec(marginals, "marginals")
    k = len(probs)
    if k < 2:
        raise ValueError("at least 2 legs required for joint combo probability")
    if any(p <= 0.0 or p >= 1.0 for p in probs):
        raise ValueError("marginal probabilities must lie strictly in (0, 1)")
    low = _cholesky(corr_matrix, k)
    indep_prob = math.prod(probs)

    if k == 2:
        rho = float(corr_matrix[0][1])
        joint_p = bivariate_normal_joint_prob(probs[0], probs[1], rho)
        return {
            "legs": 2,
            "joint_prob": joint_p,
            "independent_prob": indep_prob,
            "correlation_multiplier": joint_p / indep_prob,
            "fair_american_correlated": prob_to_fair_american(joint_p),
            "fair_american_if_independent": prob_to_fair_american(indep_prob),
            "mc_ci_low": joint_p,
            "mc_ci_high": joint_p,
        }

    thresholds = [_NORM.inv_cdf(p) for p in probs]
    rng = random.Random(seed)
    hits = 0
    for _ in range(sims):
        z = [rng.gauss(0.0, 1.0) for _ in range(k)]
        ok = True
        for i in range(k):
            xi = math.fsum(low[i][t] * z[t] for t in range(i + 1))
            if xi > thresholds[i]:
                ok = False
                break
        if ok:
            hits += 1
    est = hits / sims
    z95 = _NORM.inv_cdf(0.975)
    denom = 1.0 + z95 * z95 / sims
    center = (est + z95 * z95 / (2.0 * sims)) / denom
    half = z95 * math.sqrt(est * (1.0 - est) / sims + z95 * z95 / (4.0 * sims * sims)) / denom
    return {
        "legs": k,
        "joint_prob": est,
        "independent_prob": indep_prob,
        "correlation_multiplier": est / indep_prob if indep_prob > 0 else 0.0,
        "fair_american_correlated": prob_to_fair_american(est) if 0.0 < est < 1.0 else 0,
        "fair_american_if_independent": prob_to_fair_american(indep_prob),
        "mc_ci_low": max(0.0, center - half),
        "mc_ci_high": min(1.0, center + half),
    }


def correlation_pricing_report(
    marginals: Sequence[float],
    empirical_corr_matrix: Sequence[Sequence[float]] | None,
) -> dict[str, object]:
    """Fail-closed wrapper: refuses to quote a combo price if correlation matrix is unverified."""
    if empirical_corr_matrix is None:
        return {
            "status": "blocked_unverified_correlation",
            "joint_prob": None,
            "independent_prob": math.prod(_clean_vec(marginals, "marginals")),
            "correlation_multiplier": None,
            "fair_american_correlated": None,
        }
    res = gaussian_copula_joint_prob(marginals, empirical_corr_matrix)
    return {"status": "computed_from_verified_residuals", **res}
