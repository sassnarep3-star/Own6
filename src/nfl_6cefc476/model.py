"""Model mathematics, settlement, and gate evaluation for the 6cefc476 pack.

Everything here is either (a) standard mathematics referenced to the NIST/SEMATECH
e-handbook, or (b) a declared model parameter published in the data files with its
derivation.  Nothing in this module invents external facts.

Model definition (published on the lines page):
  exp_away_pts = (away_PF_per_game + home_PA_per_game) / 2
  exp_home_pts = (home_PF_per_game + away_PA_per_game) / 2 + HFA
  fair_total   = exp_home_pts + exp_away_pts
  fair_spread_home = exp_home_pts - exp_away_pts      (home perspective)
  p_home = Phi(fair_spread_home / sigma_margin)
  fair American odds from p_home (standard no-vig conversion, no margin added).

HFA is a declared parameter set to 0.000 (flagged: no official source supplies a
home-field magnitude).  sigma_margin is a declared parameter derived from the 15
verified Week 9 home-away margins (n published beside every use).
"""
from __future__ import annotations

import math
from statistics import NormalDist

_NORMAL = NormalDist()


# ---------------------------------------------------------------- basic math

def norm_cdf(x: float) -> float:
    """Standard normal CDF."""
    return _NORMAL.cdf(x)


def expected_points(pf_pg: float, pa_pg: float, opp_pf_pg: float, opp_pa_pg: float,
                    hfa: float = 0.0) -> tuple[float, float]:
    """Return (expected_home_points, expected_away_points)."""
    exp_home = (pf_pg + opp_pa_pg) / 2.0 + hfa
    exp_away = (opp_pf_pg + pa_pg) / 2.0
    return exp_home, exp_away


def fair_numbers(pf_home: float, pa_home: float, pf_away: float, pa_away: float,
                 sigma: float, hfa: float = 0.0) -> dict[str, float]:
    """All fair-line numbers for one game.  Spread is home-perspective."""
    exp_home, exp_away = expected_points(pf_home, pa_home, pf_away, pa_away, hfa)
    spread = exp_home - exp_away
    total = exp_home + exp_away
    p_home = norm_cdf(spread / sigma) if sigma > 0 else 0.5
    return {
        "exp_home_pts": exp_home,
        "exp_away_pts": exp_away,
        "fair_spread_home": spread,
        "fair_total": total,
        "p_home": p_home,
        "fair_ml_home": fair_american(p_home),
        "fair_ml_away": fair_american(1.0 - p_home),
    }


def fair_american(p: float) -> int:
    """Fair American odds for probability p (no vig, no margin).  Blank-safe."""
    if p <= 0.0 or p >= 1.0:
        raise ValueError("probability out of range")
    if p >= 0.5:
        return round(-100.0 * p / (1.0 - p))
    return round(100.0 * (1.0 - p) / p)


def sample_std(values: list[float]) -> float:
    """Sample standard deviation (n-1 denominator)."""
    n = len(values)
    if n < 2:
        raise ValueError("need at least 2 values")
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))


# ------------------------------------------------- correlation statistics

def pearson_r(xs: list[float], ys: list[float]) -> float:
    """Pearson product-moment correlation coefficient."""
    n = len(xs)
    if n != len(ys) or n < 3:
        raise ValueError("need paired vectors with n >= 3")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        raise ValueError("zero variance")
    return sxy / math.sqrt(sxx * syy)


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    tiny = 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 201):
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
        if abs(delta - 1.0) < 3e-12:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_bt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(ln_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def corr_p_value(r: float, n: int) -> float:
    """Two-sided p-value for Pearson r via the t statistic, t ~ Student(n-2).

    p = I_{df/(df+t^2)}(df/2, 1/2) with t = r*sqrt(df)/sqrt(1-r^2).
    """
    if n < 4:
        raise ValueError("need n >= 4")
    df = n - 2
    if abs(r) >= 1.0:
        return 0.0
    t = r * math.sqrt(df) / math.sqrt(1.0 - r * r)
    x = df / (df + t * t)
    return _betai(df / 2.0, 0.5, x)


def fisher_ci95(r: float, n: int) -> tuple[float, float]:
    """Fisher z confidence interval for Pearson r (NIST/SEMATECH e-handbook)."""
    if n < 4:
        raise ValueError("need n >= 4")
    if abs(r) >= 1.0:
        return (1.0, 1.0) if r > 0 else (-1.0, -1.0)
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    half = 1.959963984540054 * se
    return math.tanh(z - half), math.tanh(z + half)


# ------------------------------------------------------------- settlement

def settle_side(away_score: int, home_score: int, fair_spread_home: float) -> str:
    """Grade the model side against the model's own fair spread.

    The model side is home when fair_spread_home < 0 (home favored).  Pushes on
    the exact fair number are recorded as 'push'.
    """
    margin_home = home_score - away_score
    if abs(margin_home + fair_spread_home) < 1e-9:
        return "push"
    home_covers = (margin_home + fair_spread_home) > 0
    if fair_spread_home <= 0:  # model side: home
        return "win" if home_covers else "loss"
    return "win" if not home_covers else "loss"


def settle_total(away_score: int, home_score: int, fair_total: float) -> str:
    """Grade over/under against the model's own fair total (model side: over)."""
    total = away_score + home_score
    if abs(total - fair_total) < 1e-9:
        return "push"
    return "win" if total > fair_total else "loss"


def settle_ml(away_score: int, home_score: int, p_home: float) -> str:
    """Grade the moneyline pick (the higher model probability side)."""
    home_wins = home_score > away_score
    pick_home = p_home >= 0.5
    return "win" if home_wins == pick_home else "loss"


# ------------------------------------------------------ replacement depth

def depth_of_replacement(injured_string: int, replacement_string: int) -> dict[str, int]:
    """Quantify a replacement event.

    depth_of_replacement: the string level of the player who steps in (the
    'depth' being relied on).  replacement_step: how many strings down the
    unit moves (replacement_string - injured_string).
    """
    if replacement_string < 1 or injured_string < 1:
        raise ValueError("strings are 1-based")
    return {
        "depth_of_replacement": replacement_string,
        "replacement_step": replacement_string - injured_string,
    }


# ----------------------------------------------------------- demotion gate

def evaluate_demotion(stats: dict[str, float | int | bool]) -> list[str]:
    """Return the ids of demotion rules that fire given live-strategy stats.

    Rule inputs (all must be present; missing input means the rule cannot be
    evaluated and returns no trigger — the validation gate blocks promotion
    before that can matter):
      clv_mean, clv_n, roi_lb95, graded_n, drawdown_sigma,
      input_stale_days, feed_integrity_ok, regime_break_review_ok
    """
    fired: list[str] = []
    clv_n = int(stats.get("clv_n", 0))
    graded_n = int(stats.get("graded_n", 0))
    if clv_n >= 100 and float(stats.get("clv_mean", 0.0)) < 0.0:
        fired.append("DG-01")
    if graded_n >= 200 and float(stats.get("roi_lb95", 0.0)) < 0.0:
        fired.append("DG-02")
    if float(stats.get("drawdown_sigma", 0.0)) > 3.0:
        fired.append("DG-03")
    if int(stats.get("input_stale_days", 0)) > 7:
        fired.append("DG-04")
    if not bool(stats.get("feed_integrity_ok", True)):
        fired.append("DG-05")
    if not bool(stats.get("regime_break_review_ok", True)):
        fired.append("DG-06")
    return fired
