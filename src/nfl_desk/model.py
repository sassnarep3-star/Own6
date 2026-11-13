"""Own-line origination from verified scoring inputs only.

Model (fully stated, fully recomputable):
  base_home_points = 0.5 * (club_home.points_per_game + club_away.points_allowed_per_game)
  base_away_points = 0.5 * (club_away.points_per_game + club_home.points_allowed_per_game)
  expected_total     = base_home_points + base_away_points
  expected_margin    = base_home_points - base_away_points + home_field_points
  each team's points ~ Poisson(lambda)  (assumption, labelled as such)
Line and prob are then read off the exact margin distribution of the two Poissons,
so push / one-score / tie mass is explicit instead of hidden by a normal curve.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MAX_POINTS = 80  # truncation point; residual mass renormalised (documented)


def poisson_pmf(lam: float, kmax: int = MAX_POINTS) -> list[float]:
    if lam <= 0:
        raise ValueError("lambda must be positive")
    pmf = [math.exp(-lam)]
    for k in range(1, kmax + 1):
        pmf.append(pmf[-1] * lam / k)
    total = sum(pmf)
    return [p / total for p in pmf]


def margin_pmf(lam_home: float, lam_away: float, kmax: int = MAX_POINTS) -> dict[int, float]:
    """Exact distribution of (home points - away points) for two independent Poissons."""
    ph = poisson_pmf(lam_home, kmax)
    pa = poisson_pmf(lam_away, kmax)
    out: dict[int, float] = {}
    for m in range(-kmax, kmax + 1):
        acc = 0.0
        if m >= 0:
            for k in range(0, kmax - m + 1):
                acc += ph[k + m] * pa[k]
        else:
            for k in range(0, kmax + m + 1):
                acc += ph[k] * pa[k - m]
        if acc:
            out[m] = acc
    s = sum(out.values())
    return {m: p / s for m, p in out.items()}


@dataclass(frozen=True)
class GameLine:
    spread_home: float          # negative = home club favoured, in points
    spread_rounded: float
    total: float
    total_rounded: float
    home_win_prob: float
    tie_prob: float             # P(margin = 0), the regulation-tie mass
    push_prob_quoted_line: float  # push probability on the rounded line actually published
    fav_cover_prob: float
    margin_expected: float


def key_number_mass(mpmf: dict[int, float]) -> dict[int, float]:
    return {k: mpmf.get(k, 0.0) + (mpmf.get(-k, 0.0) if k != 0 else 0.0) for k in range(0, 15)}


def game_line(home_ppg: float, home_papg: float, away_ppg: float, away_papg: float,
              *, home_field_points: float = 0.0, tick: float = 0.5) -> tuple[GameLine, dict[int, float]]:
    base_home = 0.5 * (home_ppg + away_papg)
    base_away = 0.5 * (away_ppg + home_papg)
    hfa = 0.0 if home_field_points == 0 else home_field_points
    lam_home = max(base_home + hfa / 2.0, 0.5)
    lam_away = max(base_away - hfa / 2.0, 0.5)
    mpmf = margin_pmf(lam_home, lam_away)
    p_home = sum(p for m, p in mpmf.items() if m > 0)
    p_tie = mpmf.get(0, 0.0)
    p_away = sum(p for m, p in mpmf.items() if m < 0)
    exp_margin = sum(m * p for m, p in mpmf.items())
    spread = -exp_margin          # published spread is on the favourite side of the margin
    kn = key_number_mass(mpmf)
    total = base_home + base_away
    # probability that the club favoured by the rounded line covers, ignoring the push
    r = round_half(spread, tick)
    if abs(r) < 1e-9:
        cover = p_home
    elif r < 0:
        cover = sum(p for m, p in mpmf.items() if m > -r)
    else:
        cover = sum(p for m, p in mpmf.items() if m < -r) + p_tie
    # a whole-number line pushes when the margin equals the spread exactly; a half-number line cannot push
    push_quoted = mpmf.get(-int(round(r)), 0.0) if float(r).is_integer() else 0.0
    line = GameLine(
        spread_home=spread, spread_rounded=r, total=total, total_rounded=round_half(total, tick),
        home_win_prob=(p_home + 0.5 * p_tie), tie_prob=p_tie, push_prob_quoted_line=push_quoted,
        fav_cover_prob=cover,
        margin_expected=exp_margin,
    )
    assert abs((p_home + p_away + p_tie) - 1.0) < 1e-9
    return line, kn


def round_half(x: float, tick: float = 0.5) -> float:
    return math.floor(x / tick + 0.5) * tick
