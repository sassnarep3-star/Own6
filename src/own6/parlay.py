"""Dependency-free correlation diagnostics and Gaussian-copula simulation.

Research utility, not a calibrated NBA model. ``corr`` is the correlation of
LATENT STANDARD NORMAL variables, not raw player scores or binary bet outcomes.
Estimate/validate that model separately on authorized, training-only data. A
Pearson estimate is not automatically a valid copula parameter. See
https://www.statsmodels.org/stable/generated/statsmodels.distributions.copula.api.GaussianCopula.html

Invalid or unsupported inputs raise ValueError; they are never repaired into
independence. Singular positive-semidefinite matrices are valid mathematical
models but are deliberately unsupported by this strict Cholesky implementation.
"""
from __future__ import annotations

import math
import random
from numbers import Real
from statistics import NormalDist

_NORMAL = NormalDist()
_PIVOT_MIN = 1e-12  # Project numerical safety policy, not an NBA/statistical fact.


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number (not bool)")
    try:
        value = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    return value


def _vector(values, name):
    try:
        return [_finite(x, name) for x in values]
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of finite real numbers") from exc


def _probabilities(marginals):
    probabilities = _vector(marginals, "marginals")
    if not probabilities or any(p < 0 or p > 1 for p in probabilities):
        raise ValueError("at least one marginal is required, each in [0, 1]")
    return probabilities


def pearson(xs, ys):
    """Aligned finite paired-sample Pearson point estimate; no skill/CI claim.

    At least two nonconstant pairs are required. Constant and near-constant
    samples are rejected, not reported as zero correlation. No missing pairs are
    silently dropped. Pairing by event/player/date remains the caller's duty.
    Formula/constant-input caveat: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
    """
    x, y = _vector(xs, "xs"), _vector(ys, "ys")
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Pearson requires equal-length samples of at least two pairs")

    def normalized_centered(values):
        # Rescale before centering/squaring to avoid overflow on large inputs.
        scale = max(map(abs, values))
        if scale == 0:
            raise ValueError("Pearson is undefined for constant input")
        scaled = [v / scale for v in values]
        mean = math.fsum(scaled) / len(scaled)
        centered = [v - mean for v in scaled]
        norm = math.hypot(*centered)
        if norm == 0 or norm < 1e-13 * abs(mean):
            raise ValueError("Pearson is undefined or numerically unsafe for constant/near-constant input")
        return [v / norm for v in centered]

    x, y = normalized_centered(x), normalized_centered(y)
    r = math.fsum(a * b for a, b in zip(x, y))
    return max(-1.0, min(1.0, r))  # Bound roundoff, not missing/invalid data.


def _cholesky(corr, k):
    try:
        matrix = [_vector(row, "corr") for row in corr]
    except TypeError as exc:
        raise ValueError("corr must be a square matrix") from exc
    if len(matrix) != k or any(len(row) != k for row in matrix):
        raise ValueError("corr must be square with one row/column per marginal")
    for i in range(k):
        if matrix[i][i] != 1.0:
            raise ValueError("corr must have unit diagonal")
        for j in range(k):
            if not -1 <= matrix[i][j] <= 1:
                raise ValueError("corr entries must be in [-1, 1]")
            if matrix[i][j] != matrix[j][i]:
                raise ValueError("corr must be symmetric; no automatic symmetrization")
    lower = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i + 1):
            remainder = matrix[i][j] - math.fsum(lower[i][t] * lower[j][t] for t in range(j))
            if i == j:
                if remainder <= _PIVOT_MIN:
                    raise ValueError("corr must be positive definite with every Cholesky pivot > 1e-12; singular/near-singular models are unsupported")
                lower[i][j] = math.sqrt(remainder)
            else:
                lower[i][j] = remainder / lower[j][j]
    return lower


def _norm_cdf(z):
    return _NORMAL.cdf(z)


def _norm_inv(p):
    p = _finite(p, "p")
    if not 0 < p < 1:
        raise ValueError("inverse normal requires p in (0, 1)")
    return _NORMAL.inv_cdf(p)


def joint_prob_report(marginals, corr, sims=20000, seed=6):
    """Simulate all-leg success with an explicitly supplied latent correlation.

    Returns a conditional model probability plus a 95% Wilson interval for
    MONTE CARLO error only. That interval ignores model, parameter, data,
    selection and market uncertainty; it cannot qualify a strategy. Endpoint
    marginals 0/1 are supported without evaluating inverse-normal endpoints.
    Reproducible for the same inputs, seed and Python random implementation.
    """
    probabilities = _probabilities(marginals)
    if isinstance(sims, bool) or not isinstance(sims, int) or sims <= 0:
        raise ValueError("sims must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer for reproducible simulation")
    k = len(probabilities)
    lower = _cholesky(corr, k)  # Validate even for deterministic marginals.
    thresholds = [(-math.inf if p == 0 else math.inf if p == 1 else _norm_inv(p)) for p in probabilities]
    rng = random.Random(seed)
    hits = 0
    for _ in range(sims):
        z = [rng.gauss(0, 1) for _ in range(k)]
        x = [math.fsum(lower[i][t] * z[t] for t in range(i + 1)) for i in range(k)]
        hits += all(value <= threshold for value, threshold in zip(x, thresholds))
    estimate = hits / sims
    z95 = _NORMAL.inv_cdf(0.975)
    denom = 1 + z95 * z95 / sims
    center = (estimate + z95 * z95 / (2 * sims)) / denom
    half = z95 * math.sqrt(estimate * (1 - estimate) / sims + z95 * z95 / (4 * sims * sims)) / denom
    return {
        "probability": estimate,
        "hits": hits,
        "sims": sims,
        "seed": seed,
        "mc_ci_low": max(0.0, center - half),
        "mc_ci_high": min(1.0, center + half),
        "interval_scope": "95% Wilson Monte Carlo error only; not NBA model/parameter uncertainty or evidence of skill",
        "correlation_scope": "latent standard-normal correlation, not observed score or binary-outcome correlation",
    }


def joint_prob(marginals, corr, sims=20000, seed=6):
    """Compatibility float result; prefer joint_prob_report for simulation error.

    Explicit correlation is mandatory. A zero/all-success Monte Carlo result is
    not proof of impossibility/certainty. No output is an official NBA value.
    """
    return joint_prob_report(marginals, corr, sims=sims, seed=seed)["probability"]


def independent_prob(marginals):
    """Product under an EXPLICIT independence assumption, for diagnostics only.

    Never use as a fallback when empirical dependence evidence is missing.
    """
    return math.prod(_probabilities(marginals))
