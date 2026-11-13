"""Skill-vs-luck decomposition on verified season records.

Why this exists: a record is the part of a strategy a bettor can see, but it is
itself noisy. Pythagorean expectation (points for and against) is the part that is
stable; the residual is chance. Measuring that residual on official data is what
lets the leaderboard reward skill and refuse to reward a hot streak.
"""
from __future__ import annotations

import math
import random

from .league import Club
from .correlation import pearson, spearman, mean

BOOTSTRAP_REPS = 4000
SEED = 20261113


def pyth_win_prob(pf: float, pa: float, exp: float) -> float:
    if pf <= 0 or pa <= 0:
        raise ValueError("points must be positive")
    return (pf ** exp) / (pf ** exp + pa ** exp)


def bootstrap_ci(values: list[float], reps: int = BOOTSTRAP_REPS, seed: int = SEED,
                 alpha: float = 0.05) -> tuple[float, float, float]:
    rng = random.Random(seed)
    n = len(values)
    stats = []
    for _ in range(reps):
        stats.append(mean([values[rng.randrange(n)] for _ in range(n)]))
    stats.sort()
    lo = stats[int(math.floor(alpha / 2 * len(stats)))]
    hi = stats[int(math.floor((1 - alpha / 2) * len(stats))) - 1]
    return (lo, mean(values), hi)


def _fit_objective(clubs: list[Club], exp: float) -> tuple[float, list[float]]:
    sse = 0.0
    expected: list[float] = []
    for c in clubs:
        p = pyth_win_prob(c.pf / c.gp, c.pa / c.gp, exp)
        e = p * c.gp
        expected.append(e)
        sse += (e - c.wins_adj) ** 2
    return sse, expected


def pythagorean_fit(clubs: list[Club], lo: float = 0.5, hi: float = 4.0, step: float = 0.001) -> dict:
    """Golden-section-free grid fit: reproducible by re-running the same grid."""
    best_exp, best_sse, best_expected = lo, float("inf"), []
    e = lo
    while e <= hi + 1e-12:
        sse, expected = _fit_objective(clubs, e)
        if sse < best_sse:
            best_exp, best_sse, best_expected = e, sse, expected
        e += step
    actual = [c.wins_adj for c in clubs]
    n = len(clubs)
    r = pearson(best_expected, actual)
    tot_ss = sum((a - mean(actual)) ** 2 for a in actual)
    return {
        "n": n, "exponent": round(best_exp, 3), "sse": best_sse,
        "mae": best_sse and math.sqrt(best_sse / n),
        "pearson_r": r, "r_squared": r * r, "spearman_rho": spearman(best_expected, actual),
        "expected_wins": best_expected,
        "total_ss": tot_ss,
        "residual_ss": best_sse,
    }


def luck_table(clubs: list[Club], exponent: float | None = None) -> list[dict]:
    fit = None
    if exponent is None:
        fit = pythagorean_fit(clubs)
        exponent = fit["exponent"]
    out = []
    for c in clubs:
        p = pyth_win_prob(c.pf / c.gp, c.pa / c.gp, exponent)
        exp_wins = p * c.gp
        resid = c.wins_adj - exp_wins
        binom_sd = math.sqrt(c.gp * p * (1 - p))
        out.append({
            "abbr": c.abbr, "club": c.club, "gp": c.gp, "wins_adj": c.wins_adj,
            "pyth_prob": p, "expected_wins": exp_wins, "luck_wins": resid,
            "luck_z": resid / binom_sd if binom_sd else float("nan"),
        })
    out.sort(key=lambda r: -r["luck_wins"])
    return out


def luck_share(clubs: list[Club], exponent: float) -> dict:
    """How much of the spread in records is chance? Compare residual scatter with binomial noise."""
    resid: list[float] = []
    noise_var = 0.0
    for c in clubs:
        p = pyth_win_prob(c.pf / c.gp, c.pa / c.gp, exponent)
        resid.append(c.wins_adj - p * c.gp)
        noise_var += c.gp * p * (1 - p)
    n = len(clubs)
    obs_var = sum(r * r for r in resid) / (n - 1)
    expected_noise = noise_var / (n - 1)
    return {
        "residual_variance": obs_var,
        "binomial_noise_variance": expected_noise,
        "excess_over_noise": obs_var - expected_noise,
        "luck_share_of_residual": min(1.0, expected_noise / obs_var) if obs_var else float("nan"),
        "sd_residual_wins": math.sqrt(obs_var),
        "sd_noise_wins": math.sqrt(expected_noise),
    }


def required_games_for_edge(edge_ppg: float, sd_margin: float, alpha: float = 0.05,
                            power: float = 0.80) -> float:
    """Sample size for a two-sided z-test on a mean margin edge - how long 'luck' takes to wash out."""
    za = 1.959963984540054 if abs(alpha - 0.05) < 1e-9 else _z(alpha / 2)
    zb = _z(1 - power)
    if edge_ppg <= 0 or sd_margin <= 0:
        return float("inf")
    return ((za + zb) * sd_margin / edge_ppg) ** 2


def _z(p: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation), for power maths only."""
    a = [-3.969683028667437e+01, 2.209460984245205e+02, -2.759285104469687e+02,
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
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
