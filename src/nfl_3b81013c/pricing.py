"""NFL line origination, fair American odds conversion, de-vigging, and same-line CLV.

All probability and pricing formulas are deterministic, dependency-light, and never
invent synthetic sportsbook vig or fabricate closing line value when lines move.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


# Empirical NFL key-number push mass weights (3 and 7 dominate NFL scoring margins)
NFL_KEY_MARGIN_WEIGHTS: dict[int, float] = {
    3: 0.092,
    7: 0.068,
    6: 0.045,
    10: 0.042,
    4: 0.038,
    14: 0.035,
    1: 0.031,
    2: 0.028,
}


def american_to_implied_prob(odds: int | float) -> float:
    """Convert American odds to raw implied probability.

    Rejects invalid odds in (-100, 100).
    Uses official conversion:
      - Negative odds (-X): (-odds) / (-odds + 100)
      - Positive odds (+X): 100 / (odds + 100)
    """
    if isinstance(odds, bool) or not isinstance(odds, (int, float)) or math.isnan(odds) or math.isinf(odds):
        raise ValueError(f"Invalid American odds: {odds!r}")
    if -100 < odds < 100:
        raise ValueError(f"American odds cannot lie in (-100, 100): {odds}")
    if odds < 0:
        neg = -float(odds)
        return neg / (neg + 100.0)
    return 100.0 / (float(odds) + 100.0)


def fair_prob_to_american(prob: float) -> int:
    """Convert fair probability in (0, 1) to no-vig fair American odds.

    Even money (p = 0.5) maps to +100 (never -110).
    """
    if isinstance(prob, bool) or not isinstance(prob, (int, float)) or math.isnan(prob):
        raise ValueError(f"Invalid probability: {prob!r}")
    if not (0.0 < prob < 1.0):
        raise ValueError(f"Probability must be strictly in (0, 1): {prob}")
    if abs(prob - 0.5) < 1e-12:
        return 100
    if prob > 0.5:
        return -round(100.0 * prob / (1.0 - prob))
    return round(100.0 * (1.0 - prob) / prob)


def devig_multiplicative(odds_list: list[int | float]) -> list[float]:
    """Remove sportsbook overround proportionally across mutually exclusive outcomes."""
    if len(odds_list) < 2:
        raise ValueError("At least two mutually exclusive outcomes are required to de-vig.")
    raw = [american_to_implied_prob(o) for o in odds_list]
    overround = sum(raw)
    if overround <= 0.0:
        raise ValueError("Invalid sum of implied probabilities.")
    return [p / overround for p in raw]


def devig_shin_power(odds_list: list[int | float], tol: float = 1e-9) -> list[float]:
    """Power-method de-vigging (solves sum(raw_i^k) = 1 for k >= 1).

    Accounts for favorite-longshot bias where bookmakers load proportionally more
    margin onto longshots/underdogs.
    """
    if len(odds_list) < 2:
        raise ValueError("At least two mutually exclusive outcomes are required.")
    raw = [american_to_implied_prob(o) for o in odds_list]
    if abs(sum(raw) - 1.0) < tol:
        return raw
    lo, hi = 0.01, 20.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        total = sum(p ** mid for p in raw)
        if total > 1.0:
            lo = mid
        else:
            hi = mid
        if abs(total - 1.0) < tol:
            break
    k = 0.5 * (lo + hi)
    probs = [p ** k for p in raw]
    s = sum(probs)
    return [p / s for p in probs]


def same_line_devig_clv(
    bet_side_index: int,
    bet_line: float,
    close_line: float,
    bet_market_odds: list[int | float],
    close_market_odds: list[int | float],
) -> float | None:
    """Compute de-vigged same-line Closing Line Value (CLV) in probability space.

    If `bet_line != close_line` (e.g., spread moved from -2.5 to -3.5), returns `None`
    so moved-line observations remain blank until an authorized push/key-number bridge
    is certified.
    """
    if abs(float(bet_line) - float(close_line)) > 1e-9:
        return None
    if not (0 <= bet_side_index < len(bet_market_odds)) or len(bet_market_odds) != len(close_market_odds):
        raise ValueError("Invalid side index or mismatched market outcome count.")
    p_bet = devig_multiplicative(bet_market_odds)[bet_side_index]
    p_close = devig_multiplicative(close_market_odds)[bet_side_index]
    return p_close - p_bet


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


@dataclass(frozen=True)
class OriginatedGameLine:
    home_team: str
    away_team: str
    projected_home_points: float
    projected_away_points: float
    fair_home_spread: float
    fair_total: float
    home_win_prob: float
    away_win_prob: float
    fair_home_ml: int
    fair_away_ml: int


def originate_nfl_game_lines(
    home_team: str,
    away_team: str,
    home_off_epa_per_play: float,
    home_def_epa_per_play: float,
    away_off_epa_per_play: float,
    away_def_epa_per_play: float,
    neutral_plays_per_team: float = 63.0,
    league_baseline_points_per_team: float = 22.4,
    home_field_advantage_pts: float = 1.75,
    neutral_site: bool = False,
    home_depth_delta_pts: float = 0.0,
    away_depth_delta_pts: float = 0.0,
    weather_total_delta_pts: float = 0.0,
    margin_sd: float = 13.45,
) -> OriginatedGameLine:
    """Originate fair NFL spread, total, and moneyline from opponent-adjusted EPA/play
    and starter/backup depth-chart adjustments.
    """
    if margin_sd <= 0.0 or neutral_plays_per_team <= 0.0:
        raise ValueError("margin_sd and neutral_plays_per_team must be positive.")

    hfa = 0.0 if neutral_site else home_field_advantage_pts
    # Matchup net EPA per play for each offense against opposing defense
    home_matchup_epa = 0.5 * (home_off_epa_per_play - away_def_epa_per_play)
    away_matchup_epa = 0.5 * (away_off_epa_per_play - home_def_epa_per_play)

    proj_home = (
        league_baseline_points_per_team
        + home_matchup_epa * neutral_plays_per_team
        + 0.5 * hfa
        + home_depth_delta_pts
        + 0.5 * weather_total_delta_pts
    )
    proj_away = (
        league_baseline_points_per_team
        + away_matchup_epa * neutral_plays_per_team
        - 0.5 * hfa
        + away_depth_delta_pts
        + 0.5 * weather_total_delta_pts
    )
    proj_home = max(3.0, proj_home)
    proj_away = max(3.0, proj_away)

    expected_home_margin = proj_home - proj_away
    # Standard sportsbook convention: negative spread means home team is favored
    fair_home_spread = round(-expected_home_margin, 2)
    fair_total = round(proj_home + proj_away, 2)

    home_win_prob = min(max(_normal_cdf(expected_home_margin / margin_sd), 0.001), 0.999)
    away_win_prob = 1.0 - home_win_prob

    return OriginatedGameLine(
        home_team=home_team,
        away_team=away_team,
        projected_home_points=round(proj_home, 2),
        projected_away_points=round(proj_away, 2),
        fair_home_spread=fair_home_spread,
        fair_total=fair_total,
        home_win_prob=round(home_win_prob, 4),
        away_win_prob=round(away_win_prob, 4),
        fair_home_ml=fair_prob_to_american(home_win_prob),
        fair_away_ml=fair_prob_to_american(away_win_prob),
    )
