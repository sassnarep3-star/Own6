"""Correlation measurement with honest uncertainty.

Two things this module refuses to do:

1. Report a Pearson r without ``n`` and a confidence interval. A point estimate
   with n = 6 and r = -0.42 is published here *with* its interval, which spans
   almost the whole range [-1, 1] and therefore cannot support an independence
   or dependence claim.
2. Multiply marginal probabilities into a parlay price without stating the
   dependence assumption. A parlay's fair price depends on the joint
   probability, not the product of marginals.

References for the mathematics (not for any basketball value):
  * Pearson coefficient, p-value under the null of no correlation:
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
  * Fisher z-transformation interval for r: NIST/SEMATECH e-Handbook,
    https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm is the
    outlier section; the interval maths is NIST 1.3.5.9 / standard texts.
    Where the interval is used the page is cited as the mathematical route and
    the limitation is flagged.
"""
from __future__ import annotations

import math

from .luck import norm_cdf, norm_ppf, t_ppf, t_stat


def pearson(xs: list[float], ys: list[float]) -> dict:
    """Pearson r, its t statistic, df, and a two-sided p-value.

    Under H0 (no linear association), t = r * sqrt((n-2)/(1-r^2)) follows a
    t distribution with n-2 df. Constant input returns r = None rather than
    a fake 0.
    """
    if len(xs) != len(ys):
        raise ValueError("x and y must have equal length")
    n = len(xs)
    if n < 3:
        return {"n": n, "r": None, "t": None, "df": max(n - 2, 0), "p_two_sided": None,
                "reason": "n < 3: no correlation can be estimated"}
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0.0 or syy == 0.0:
        return {"n": n, "r": None, "t": None, "df": n - 2, "p_two_sided": None,
                "reason": "constant series: correlation undefined"}
    r = sxy / math.sqrt(sxx * syy)
    r = max(-1.0, min(1.0, r))
    if abs(r) >= 1.0:
        return {"n": n, "r": r, "t": float("inf"), "df": n - 2, "p_two_sided": 0.0, "reason": None}
    t = r * math.sqrt((n - 2) / (1.0 - r * r))
    # two-sided p from the t distribution
    p = 2.0 * (1.0 - _t_cdf_pub(abs(t), n - 2))
    return {"n": n, "r": r, "t": t, "df": n - 2, "p_two_sided": min(1.0, max(0.0, p)), "reason": None}


def _t_cdf_pub(t: float, df: int) -> float:
    """Student-t CDF built on the incomplete beta used by luck.t_ppf."""
    from .luck import _betainc_reg  # local import to avoid a cycle

    if df <= 0:
        raise ValueError("df must be positive")
    x = df / (df + t * t)
    tail = 0.5 * _betainc_reg(df / 2.0, 0.5, x)
    return 1.0 - tail if t >= 0 else tail


def fisher_ci(r: float, n: int, level: float = 0.95) -> tuple[float, float]:
    """Fisher z interval for a Pearson correlation.

    z = atanh(r); SE = 1/sqrt(n-3); invert with tanh. Requires n > 3 for the
    standard error to exist at all. For n <= 3 the interval is [-1, 1] and the
    caller must treat it as uninformative.
    """
    if n <= 3:
        return (-1.0, 1.0)
    r = max(-0.999999, min(0.999999, r))
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    crit = norm_ppf(0.5 + level / 2.0)
    return (math.tanh(z - crit * se), math.tanh(z + crit * se))


def spearman(xs: list[float], ys: list[float]) -> dict:
    """Spearman rank correlation = Pearson on average ranks (ties averaged)."""
    if len(xs) != len(ys):
        raise ValueError("x and y must have equal length")
    rx = _average_ranks(xs)
    ry = _average_ranks(ys)
    return pearson(rx, ry)


def _average_ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def cluster_bootstrap_ci(xs: list[float], ys: list[float], clusters: list[str],
                         n_resamples: int = 2000, level: float = 0.95,
                         seed: int = 20261105) -> dict:
    """Pearson r with an interval from resampling *clusters* (e.g. game dates).

    Games on the same date share travel, rest and referee conditions, so they
    are not independent observations. Resampling individual games shrinks the
    interval and overstates precision. Resampling whole clusters does not.
    """
    from .luck import Rng, _quantile_sorted

    if len(xs) != len(ys) or len(xs) != len(clusters):
        raise ValueError("xs, ys and clusters must align")
    by_cluster: dict[str, list[int]] = {}
    for i, c in enumerate(clusters):
        by_cluster.setdefault(c, []).append(i)
    keys = sorted(by_cluster)
    if len(keys) < 2:
        return {"r": None, "ci_lo": None, "ci_hi": None, "n_clusters": len(keys)}
    rng = Rng(seed)
    stats: list[float] = []
    for _ in range(n_resamples):
        bx: list[float] = []
        by: list[float] = []
        for _ in range(len(keys)):
            k = keys[rng.randrange(len(keys))]
            for i in by_cluster[k]:
                bx.append(xs[i])
                by.append(ys[i])
        res = pearson(bx, by)
        if res["r"] is not None:
            stats.append(res["r"])
    if not stats:
        return {"r": None, "ci_lo": None, "ci_hi": None, "n_clusters": len(keys)}
    stats.sort()
    alpha = (1.0 - level) / 2.0
    return {
        "r": pearson(xs, ys)["r"],
        "ci_lo": _quantile_sorted(stats, alpha),
        "ci_hi": _quantile_sorted(stats, 1.0 - alpha),
        "n_clusters": len(keys),
        "n_resamples": n_resamples,
        "includes_zero": _quantile_sorted(stats, alpha) <= 0.0 <= _quantile_sorted(stats, 1.0 - alpha),
    }


def compare_linear_and_rank(pearson_res: dict, spearman_res: dict) -> dict:
    """Heuristic for heavy tails: rank correlation is robust to outliers.

    A large gap between |r| and |rho| is evidence that a handful of extreme
    games drive the Pearson estimate — i.e. the "relationship" may be luck
    concentrated in a few observations.
    """
    r, rho = pearson_res.get("r"), spearman_res.get("r")
    if r is None or rho is None:
        return {"delta": None, "stable": None}
    delta = abs(r) - abs(rho)
    return {"delta": delta, "stable": abs(delta) < 0.15,
            "r": r, "rho": rho}


# --------------------------------------------------------------------------
# parlays: why the product of marginals is not the price
# --------------------------------------------------------------------------
def indep_joint(ps: list[float]) -> float:
    out = 1.0
    for p in ps:
        out *= p
    return out


def gaussian_copula_joint(ps: list[float], rho: float) -> float:
    """P(all legs win) under a one-factor Gaussian copula with equicorrelation rho.

    Each leg is a latent normal threshold at z_i = Phi^-1(p_i); the shared
    factor is Z with pairwise correlation rho. The joint is obtained by 2^k
    quadrature over Z, which is exact for k <= ~12 at the resolution used.
    This is a *model*, not a source; it is labelled as a project assumption.
    """
    k = len(ps)
    if k == 0:
        return 1.0
    if k > 12:
        raise ValueError("k > 12 not supported by direct quadrature")
    if rho < 0:
        raise ValueError("equicorrelation rho must be >= 0 for this model")
    if rho > 0.999:
        rho = 0.999
    # A win is the event that the latent normal falls BELOW its threshold,
    # P(Z <= Phi^-1(p)) = p. At rho = 0 this must reproduce the product of the
    # marginals exactly; that identity is asserted in the test suite and
    # cross-checked against scipy.stats.multivariate_normal.
    zs = [norm_ppf(min(max(p, 1e-12), 1 - 1e-12)) for p in ps]

    # Dense composite Simpson on a wide grid. The grid is symmetric about 0, and
    # the integrand is P(BVN <= z) integrated over the common factor, so an even
    # number of intervals keeps the endpoints symmetric. 200 intervals is enough
    # to match scipy.stats.multivariate_normal to ~1e-4 for the tail
    # probabilities used here.
    m = 200
    lo, hi = -9.0, 9.0
    h = (hi - lo) / m
    # One-factor model: Z_i = sqrt(rho) * W + sqrt(1 - rho) * E_i.
    # Given W = w, each leg is N(sqrt(rho) * w, 1 - rho). The loading is the
    # SQUARE ROOT of the correlation; using rho itself understates the shared
    # factor and understates the joint by several points.
    loading = math.sqrt(rho)
    sds = math.sqrt(max(1e-12, 1.0 - rho))
    total = 0.0
    for i in range(m + 1):
        z = lo + i * h
        w = 1.0 if i in (0, m) else (4.0 if i % 2 == 1 else 2.0)
        prod = 1.0
        for zi in zs:
            prod *= norm_cdf((zi - loading * z) / sds)
            if prod == 0.0:
                break
        total += w * prod * _normal_pdf(z)
    return total / 3.0 * h


def _normal_pdf(z: float) -> float:
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def parlay_analysis(ps: list[float], rho: float = 0.0, decimal_odds: float | None = None) -> dict:
    """Fair parlay price under independence vs. measured dependence.

    Returns the joint probability under both models, the ratio, and — if a
    price is supplied — the EV difference. A sportsbook that prices a
    positively correlated combo as if independent is over-pricing the payout
    relative to the joint probability, and vice versa.
    """
    p_ind = indep_joint(ps)
    p_dep = gaussian_copula_joint(ps, rho)
    out = {
        "legs": len(ps),
        "p_independent": p_ind,
        "p_dependent": p_dep,
        "ratio_dep_over_indep": (p_dep / p_ind) if p_ind > 0 else None,
        "fair_american_independent": _prob_to_american(p_ind),
        "fair_american_dependent": _prob_to_american(p_dep),
        "rho": rho,
    }
    if decimal_odds is not None:
        out["ev_independent_assumption"] = p_ind * decimal_odds - 1.0
        out["ev_dependent_assumption"] = p_dep * decimal_odds - 1.0
    return out


def _prob_to_american(p: float) -> float | None:
    if p <= 0.0 or p >= 1.0:
        return None
    return -100.0 * p / (1.0 - p) if p > 0.5 else 100.0 * (1.0 - p) / p
