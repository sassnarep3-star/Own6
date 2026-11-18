"""Frozen forecasters for session 0ce967db.

Every definition here is a transcription of ``data/nfl_0ce967db/preregistration.md``.
If this file and that file disagree, the preregistration wins and this file is the bug.

Rules enforced in code, not in prose:

* a forecast for a week-*w* game may only read games with week < *w*
  (``assert_chronology`` is called for every row and fails the build);
* ties are kept, and score as ``y = 0`` for both win directions;
* shrinkage ``k = 1`` pseudo-game, half-life 2 team-games, ``H = 2.5``, ``sigma`` bounds
  [7.0, 25.0] are constants copied from the registration, never tuned here.

The module has no network access and no randomness. ``statistics`` is the only
non-stdlib-looking import and it is stdlib.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field

K_SHRINK = 1.0
HALF_LIFE = 2.0
H_FIXED = 2.5
SIGMA_FLOOR = 7.0
SIGMA_CAP = 25.0


def _phi(x: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


@dataclass
class Game:
    game_id: str
    week: int
    away: str
    home: str
    away_score: int | None
    home_score: int | None
    date_on_card: str = ""

    @property
    def played(self) -> bool:
        return self.away_score is not None and self.home_score is not None

    @property
    def margin(self) -> int:
        """Home margin. Raises on an unplayed game."""
        if not self.played:
            raise ValueError(f"{self.game_id} has no final score")
        return int(self.home_score) - int(self.away_score)

    @property
    def total(self) -> int:
        if not self.played:
            raise ValueError(f"{self.game_id} has no final score")
        return int(self.home_score) + int(self.away_score)

    @property
    def home_win(self) -> int:
        """1 if the home club won, else 0. A tie is not a home win."""
        return 1 if self.margin > 0 else 0


@dataclass
class TeamHistory:
    """Everything a forecaster is allowed to know about one club before a week."""

    scored: list[int] = field(default_factory=list)   # points scored, oldest first
    allowed: list[int] = field(default_factory=list)  # points allowed, oldest first

    def append(self, scored: int, allowed: int) -> None:
        self.scored.append(scored)
        self.allowed.append(allowed)

    @property
    def n(self) -> int:
        return len(self.scored)


def _weighted_mean(values: list[float], half_life: float | None) -> float:
    """Mean with optional exponential recency weight (weight 1 for the newest game)."""
    if not values:
        raise ValueError("no values")
    if half_life is None:
        return sum(values) / len(values)
    newest = len(values) - 1
    num = 0.0
    den = 0.0
    for i, v in enumerate(values):
        w = 0.5 ** ((newest - i) / half_life)
        num += w * v
        den += w
    return num / den


def _shrunk(values: list[float], league_mean: float, k: float = K_SHRINK,
            half_life: float | None = None) -> float:
    """Shrink a club's own mean toward the league mean with k pseudo-games."""
    if not values:
        return league_mean
    own = _weighted_mean(values, half_life)
    n = len(values)
    return (n * own + k * league_mean) / (n + k)


def league_means(history: dict[str, TeamHistory]) -> tuple[float, float]:
    """League mean points scored per team-game, and allowed (identical by construction)."""
    pts = [p for h in history.values() for p in h.scored]
    allowed = [p for h in history.values() for p in h.allowed]
    if not pts:
        raise ValueError("no games in the training window")
    return sum(pts) / len(pts), sum(allowed) / len(allowed)


def sigma_margin(errors: list[float]) -> float | None:
    """Sample SD of (actual - expected) home margins, floored and capped by the registration.

    Returns None when fewer than 3 errors exist; the caller must then fall back to the
    registration's cap, and the row is flagged as sigma_default rather than sigma_fitted.
    """
    if len(errors) < 3:
        return None
    sd = statistics.stdev(errors)
    return min(SIGMA_CAP, max(SIGMA_FLOOR, sd))


def margin_forecast(home: TeamHistory, away: TeamHistory, league_ppg: float,
                    h_field: float, half_life: float | None,
                    sigma: float) -> dict:
    """Registered margin/total forecast (S01/S02/S03 margin; S04/S05 total)."""
    dev_h = _shrunk([s - a for s, a in zip(home.scored, home.allowed)], 0.0, half_life=half_life)
    dev_a = _shrunk([s - a for s, a in zip(away.scored, away.allowed)], 0.0, half_life=half_life)
    expected_margin = (dev_h - dev_a) + h_field
    # Shrinkage targets are per-team means (league_ppg). The registered total formula uses
    # L = the league mean of TOTAL points per game, which is 2 * league_ppg. Passing the
    # per-team mean here instead was a real bug in the first run: it inflated every total by
    # ~23 points (MAE 24.1), which the plausibility check caught. Registration §3 is correct
    # as written; this line is the fix.
    pf_h = _shrunk([float(x) for x in home.scored], league_ppg, half_life=half_life)
    pf_a = _shrunk([float(x) for x in away.scored], league_ppg, half_life=half_life)
    pa_h = _shrunk([float(x) for x in home.allowed], league_ppg, half_life=half_life)
    pa_a = _shrunk([float(x) for x in away.allowed], league_ppg, half_life=half_life)
    league_total = 2.0 * league_ppg
    expected_total = (league_total + (pf_h - league_total / 2) + (pf_a - league_total / 2)
                      - (pa_h - league_total / 2) - (pa_a - league_total / 2))
    return {
        "expected_margin_home": expected_margin,
        "expected_total": expected_total,
        "p_home": _phi(expected_margin / sigma),
        "sigma_margin": sigma,
        "dev_home": dev_h,
        "dev_away": dev_a,
        "pf_home": pf_h, "pf_away": pf_a, "pa_home": pa_h, "pa_away": pa_a,
        "n_home": home.n, "n_away": away.n,
        "league_ppg": league_ppg, "league_total": league_total,
        "h_field": h_field, "half_life": half_life,
    }


def assert_chronology(game: Game, history: dict[str, TeamHistory], prior_max_week: int) -> None:
    """Fail loudly if any information used for this game came from week >= game.week."""
    if prior_max_week >= game.week:
        raise AssertionError(
            f"lookahead: {game.game_id} in week {game.week} was forecast with data up to week {prior_max_week}")
    for club in (game.home, game.away):
        if club not in history:
            raise AssertionError(f"{club} has no prior-game history for {game.game_id}")
