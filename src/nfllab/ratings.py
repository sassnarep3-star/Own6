"""NFL line origination: opponent-adjusted team ratings, home field, dispersion.

Design notes (all deliberately conservative):
  * Ratings are fit only on games strictly before the evaluation window
    (walk-forward); nothing from the test season informs the test season.
  * Shrinkage pulls small samples toward league average, so a 2-game team is not
    treated like a full season.
  * Two-parameter structure: offense (points scored above league average, opponent
    adjusted) and defense (points allowed above league average, opponent adjusted,
    positive = worse defense).
  * Parameters carry an explicit standard error; the line published for a game is
    the model expectation, and the *interval* is what drives cover probabilities.

No market data is used to fit anything in this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

LEAGUE_POINTS_FALLBACK = 21.8  # only used if a training window is empty
SHRINK_GAMES = 6.0             # empirical-Bayes prior strength, in games
SEASON_DECAY = 0.55            # weight of a season d years back: DECAY**d


@dataclass
class Ratings:
    mu: float
    hfa: float
    off: dict
    deff: dict
    games: dict
    off_se: dict = field(default_factory=dict)
    deff_se: dict = field(default_factory=dict)
    sigma_margin: float = 13.5
    fitted_rows: int = 0
    seasons: tuple = ()

    def expected_points(self, home: str, away: str) -> tuple[float, float]:
        off_h = self.off.get(home, 0.0)
        off_a = self.off.get(away, 0.0)
        d_h = self.deff.get(home, 0.0)
        d_a = self.deff.get(away, 0.0)
        ph = self.mu + off_h + d_a + self.hfa / 2.0
        pa = self.mu + off_a + d_h - self.hfa / 2.0
        return ph, pa

    def expected_margin(self, home: str, away: str) -> float:
        ph, pa = self.expected_points(home, away)
        return ph - pa

    def expected_total(self, home: str, away: str) -> float:
        ph, pa = self.expected_points(home, away)
        return ph + pa

    def margin_se(self, home: str, away: str) -> float:
        """Standard error of the *expected* margin from parameter uncertainty."""
        var = (self.off_se.get(home, 0.0) ** 2 + self.off_se.get(away, 0.0) ** 2
               + self.deff_se.get(home, 0.0) ** 2 + self.deff_se.get(away, 0.0) ** 2)
        return float(np.sqrt(var))


def _wk(weight: np.ndarray) -> float:
    return float(weight.sum())


def fit_ratings(rows: list[dict], asof_season: int, sigma_prior: float = 13.5,
                iterations: int = 25) -> Ratings:
    """Fit ratings from rows whose season < asof_season (strict walk-forward)."""
    usable = []
    for r in rows:
        try:
            season = int(r["season"])
        except (TypeError, ValueError):
            continue
        if season >= asof_season:
            continue
        if not r.get("home_score") or not r.get("away_score"):
            continue
        usable.append((season, r))
    if not usable:
        return Ratings(mu=LEAGUE_POINTS_FALLBACK, hfa=0.0, off={}, deff={}, games={}, sigma_margin=sigma_prior)
    latest = max(s for s, _ in usable)
    w = np.array([SEASON_DECAY ** (latest - s) for s, _ in usable], dtype=float)
    hs = np.array([float(r["home_score"]) for _, r in usable])
    as_ = np.array([float(r["away_score"]) for _, r in usable])
    home = [r["home_team"] for _, r in usable]
    away = [r["away_team"] for _, r in usable]
    teams = sorted(set(home) | set(away))
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    mu = float((w * (hs + as_) / 2.0).sum() / w.sum())
    hfa = float((w * (hs - as_)).sum() / w.sum())

    off = np.zeros(n)
    deff = np.zeros(n)
    gsum = np.zeros(n)
    for k in range(len(usable)):
        gsum[idx[home[k]]] += w[k]
        gsum[idx[away[k]]] += w[k]

    for _ in range(iterations):
        num_off = np.zeros(n)
        num_def = np.zeros(n)
        for k in range(len(usable)):
            h, a = idx[home[k]], idx[away[k]]
            ph = hs[k] - (mu + hfa / 2.0)
            pa = as_[k] - (mu - hfa / 2.0)
            num_off[h] += w[k] * (ph - deff[a])
            num_off[a] += w[k] * (pa - deff[h])
            num_def[h] += w[k] * (pa - off[a])
            num_def[a] += w[k] * (ph - off[h])
        new_off = np.divide(num_off, gsum, out=np.zeros(n), where=gsum > 0)
        new_def = np.divide(num_def, gsum, out=np.zeros(n), where=gsum > 0)
        shrink = gsum / (gsum + SHRINK_GAMES)
        off = new_off * shrink
        deff = new_def * shrink
        off -= np.average(off, weights=np.maximum(gsum, 1e-9))
        deff -= np.average(deff, weights=np.maximum(gsum, 1e-9))

    # Residual dispersion of the fitted model on the training window itself is
    # optimistic; callers must not use it as an out-of-sample estimate. It is kept
    # only as a floor for the predictive sigma when a holdout is unavailable.
    resid = []
    for k in range(len(usable)):
        h, a = idx[home[k]], idx[away[k]]
        pred = (mu + off[h] + deff[a] + hfa / 2.0) - (mu + off[a] + deff[h] - hfa / 2.0)
        resid.append(hs[k] - as_[k] - pred)
    resid = np.array(resid)
    sigma = float(np.sqrt((w * resid ** 2).sum() / w.sum()))

    # Parameter standard errors: weighted residual variance / effective sample size.
    eff = np.maximum(gsum, 1.0)
    off_se = np.sqrt(2.0 * sigma ** 2 / eff)
    deff_se = off_se.copy()
    return Ratings(
        mu=mu, hfa=hfa,
        off={t: float(off[idx[t]]) for t in teams},
        deff={t: float(deff[idx[t]]) for t in teams},
        games={t: float(gsum[idx[t]]) for t in teams},
        off_se={t: float(off_se[idx[t]]) for t in teams},
        deff_se={t: float(deff_se[idx[t]]) for t in teams},
        sigma_margin=sigma, fitted_rows=len(usable), seasons=tuple(sorted({s for s, _ in usable})),
    )


def holdout_sigma(rows: list[dict], test_season: int) -> float:
    """Out-of-sample margin residual SD: fit on prior seasons, evaluate on test_season."""
    train = [r for r in rows if int(r["season"]) < test_season]
    rat = fit_ratings(train, test_season)
    resid = []
    for r in rows:
        if int(r["season"]) != test_season or not r.get("home_score"):
            continue
        pred = rat.expected_margin(r["home_team"], r["away_team"])
        resid.append(float(r["home_score"]) - float(r["away_score"]) - pred)
    return float(np.sqrt(np.mean(np.square(resid)))) if resid else rat.sigma_margin
