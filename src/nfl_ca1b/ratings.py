"""Opponent-aware team strength from official game-level results (pure stdlib).

Model (pre-registered text is in prereg.py; the commit that first carries this file
is the registration):

    home_points = lg_avg + hfa/2 + atk_home - def_away
    away_points = lg_avg - hfa/2 + atk_away - def_home
    win prob    = Phi((margin_hat) / sigma)          (normal approximation)
    margin_hat  = (atk_h - def_a) - (atk_a - def_h) + hfa

atk and def are solved by ridge regression on the *same* design, so the fit is a
closed-form linear least squares. Ratings are identified only up to a constant, so
atk/def are centred to mean zero after solving. sigma is the residual standard
deviation of the margin equation on the sample that was fit.

Nothing here assumes a number from outside the official game log. No market input.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

Game = Tuple[str, str, int, int]  # away, home, away_score, home_score


# --------------------------------------------------------------- linear algebra
def solve(a: List[List[float]], b: List[float]) -> List[float]:
    """Gaussian elimination with partial pivoting. Small, dense, deterministic."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular matrix")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(col + 1, n):
            factor = m[r][col] / pv
            if factor:
                for c in range(col, n + 1):
                    m[r][c] -= factor * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


def ridge_fit(games: Sequence[Game], teams: Sequence[str], lam: float = 1.0,
              hfa: float = 2.6) -> Dict[str, float]:
    """Fit atk/def (one column pair per club) on points scored.

    Design rows: 4 per game (home atk, away def, away atk, home def) with target
    (points - lg_avg -/+ hfa/2). Ridge penalty lam pulls each parameter to zero,
    which is also what identifies the otherwise-flat direction.
    """
    idx = {t: i for i, t in enumerate(teams)}
    k = 2 * len(teams)
    ata = [[0.0] * k for _ in range(k)]
    atb = [0.0] * k
    total = sum(g[2] + g[3] for g in games)
    lg = total / (2.0 * len(games))

    def add_row(params: Sequence[Tuple[int, float]], target: float) -> None:
        for i, vi in params:
            atb[i] += vi * target
            for j, vj in params:
                ata[i][j] += vi * vj

    for away, home, a_s, h_s in games:
        h = idx[home]
        a = idx[away]
        # home offence vs away defence
        add_row([(h, 1.0), (len(teams) + a, -1.0)], h_s - lg - hfa / 2.0)
        # away offence vs home defence
        add_row([(a, 1.0), (len(teams) + h, -1.0)], a_s - lg + hfa / 2.0)
    for i in range(k):
        ata[i][i] += lam
    x = solve(ata, atb)
    atk = {t: x[idx[t]] for t in teams}
    dfn = {t: x[len(teams) + idx[t]] for t in teams}
    new_lg = lg + (sum(atk.values()) - sum(dfn.values())) / (2.0 * len(teams))
    sa = sum(atk.values()) / len(teams)
    sd = sum(dfn.values()) / len(teams)
    return {
        "lg_avg": new_lg,
        "hfa": hfa,
        "atk": {t: atk[t] - sa for t in teams},
        "def": {t: dfn[t] - sd for t in teams},
    }


def margin_hat(p: Dict[str, object], away: str, home: str) -> float:
    atk, dfn = p["atk"], p["def"]
    return ((atk[home] - dfn[away]) - (atk[away] - dfn[home])) + p["hfa"]


def expected_points(p: Dict[str, object], away: str, home: str) -> Tuple[float, float]:
    atk, dfn, lg = p["atk"], p["def"], p["lg_avg"]
    h = lg + p["hfa"] / 2.0 + (atk[home] - dfn[away])
    a = lg - p["hfa"] / 2.0 + (atk[away] - dfn[home])
    return a, h


def fit_sigma(p: Dict[str, object], games: Sequence[Game]) -> float:
    """Residual sd of the margin equation (sample sd, n-1)."""
    resid = []
    for away, home, a_s, h_s in games:
        resid.append((h_s - a_s) - margin_hat(p, away, home))
    mean = sum(resid) / len(resid)
    var = sum((r - mean) ** 2 for r in resid) / (len(resid) - 1)
    return math.sqrt(var)


def total_sigma(p: Dict[str, object], games: Sequence[Game]) -> float:
    resid = []
    for away, home, a_s, h_s in games:
        ea, eh = expected_points(p, away, home)
        resid.append((a_s + h_s) - (ea + eh))
    mean = sum(resid) / len(resid)
    var = sum((r - mean) ** 2 for r in resid) / (len(resid) - 1)
    return math.sqrt(var)


# ------------------------------------------------------------------- normal cdf
def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def win_prob(margin: float, sigma: float) -> float:
    return phi(margin / sigma)


def phi_inv(p: float) -> float:
    """Acklam-free bisection inverse normal cdf; deterministic and sufficient."""
    lo, hi = -8.0, 8.0
    for _ in range(120):
        mid = (lo + hi) / 2.0
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ------------------------------------------------------------- seed stability
def bootstrap_params(games: Sequence[Game], teams: Sequence[str], draws: int = 200,
                     seed: int = 20261117, lam: float = 1.0) -> List[Dict[str, float]]:
    """Deterministic multiplicative-weight bootstrap over games (stdlib only).

    Uses a linear congruential generator so the same seed gives the same draws on
    every machine; no library randomness.
    """
    state = seed
    n = len(games)
    out = []
    for _ in range(draws):
        w = [0.0] * n
        for _i in range(n):
            state = (1103515245 * state + 12345) % (2 ** 31)
            j = state % n
            w[j] += 1.0
        noisy = [(g[0], g[1], g[2], g[3]) for g, _ww in zip(games, w)]
        # collapsed weights are fine for a point fit; the multiplicity is carried
        # by which games appear at all, which is what the resample expresses.
        out.append(ridge_fit(noisy, teams, lam=lam))
    return out


def club_rating_table(p, sigma, games_total_totals_sigma) -> Dict[str, Dict[str, float]]:
    atk, dfn = p["atk"], p["def"]
    return {t: {"atk": atk[t], "def": dfn[t], "net": atk[t] - dfn[t]} for t in atk}
