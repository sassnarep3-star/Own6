"""NFL Fair-Line Origination Model (Regime-Aware, Key-Number & OT-Tie Exact).

Never hardcodes NFL home-field advantage, margin standard deviation, key-number
masses, or 2025+ Dynamic Kickoff / regular-season overtime tie rates from memory.
All structural parameters must be supplied via an audited training-only fit
(`NFLRegimeParams`); if absent, empirical line outputs remain fail-closed (`None`).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Mapping

from .pricing import prob_to_fair_american

_NORM = NormalDist()


@dataclass(frozen=True)
class NFLRegimeParams:
    """Parameters fitted strictly on post-2025-rule-regime training folds."""

    league_mean_pts_per_drive: float
    mean_drives_per_team: float
    hfa_points: float
    margin_sd: float
    total_sd: float
    reg_ot_tie_prob_when_close: float
    dynamic_kickoff_35yd_active: bool
    both_teams_possess_ot_active: bool
    key_number_pmf_weights: Mapping[int, float] | None = None

    def __post_init__(self) -> None:
        if self.margin_sd <= 0.0 or self.total_sd <= 0.0:
            raise ValueError("margin_sd and total_sd must be strictly positive")
        if self.mean_drives_per_team <= 0.0 or self.league_mean_pts_per_drive <= 0.0:
            raise ValueError("mean_drives_per_team and league_mean_pts_per_drive must be positive")
        if not (0.0 <= self.reg_ot_tie_prob_when_close < 0.25):
            raise ValueError("reg_ot_tie_prob_when_close must lie in [0, 0.25)")


@dataclass(frozen=True)
class NFLGameInput:
    game_id: str
    away_team: str
    home_team: str
    neutral_site: bool
    away_off_pts_per_drive: float | None = None
    away_def_pts_per_drive: float | None = None
    home_off_pts_per_drive: float | None = None
    home_def_pts_per_drive: float | None = None
    away_depth_pts_delta: float = 0.0
    home_depth_pts_delta: float = 0.0


def _discrete_margin_pmf(
    mean_margin: float,
    margin_sd: float,
    tie_prob_close: float,
    key_weights: Mapping[int, float] | None,
    max_margin: int = 75,
) -> dict[int, float]:
    """Construct an integer-margin PMF combining Gaussian base, NFL key numbers, and OT tie mass."""
    dist = NormalDist(mu=mean_margin, sigma=margin_sd)
    raw: dict[int, float] = {}
    for m in range(-max_margin, max_margin + 1):
        base_p = dist.cdf(m + 0.5) - dist.cdf(m - 0.5)
        if m == 0:
            # Under 2025+ regular-season 10-minute both-teams-possess OT, ties remain non-zero
            proximity = math.exp(-0.5 * (mean_margin / margin_sd) ** 2)
            raw[0] = max(base_p * 0.15, tie_prob_close * proximity)
        else:
            mult = 1.0
            if key_weights and abs(m) in key_weights:
                mult = float(key_weights[abs(m)])
            raw[m] = base_p * mult
    total = math.fsum(raw.values())
    return {m: p / total for m, p in raw.items()}


def originate_nfl_game(
    game: NFLGameInput,
    regime: NFLRegimeParams | None,
    target_spread_home: float | None = None,
) -> dict[str, object]:
    """Originate fair NFL spread, total, 3-way win/loss/tie probabilities, and key-number push mass.

    Fail-closed behavior: if `regime` is None or any team offensive/defensive efficiency
    is None (unverified), returns `status="unverified_missing_inputs"` with `None` lines.
    """
    if (
        regime is None
        or game.away_off_pts_per_drive is None
        or game.away_def_pts_per_drive is None
        or game.home_off_pts_per_drive is None
        or game.home_def_pts_per_drive is None
    ):
        return {
            "game_id": game.game_id,
            "status": "unverified_missing_inputs",
            "fair_spread_home": None,
            "fair_total": None,
            "home_win_prob": None,
            "away_win_prob": None,
            "tie_prob": None,
            "fair_home_ml": None,
            "fair_away_ml": None,
            "spread_cover_probs": None,
        }

    lg = regime.league_mean_pts_per_drive
    drives = regime.mean_drives_per_team
    hfa = 0.0 if game.neutral_site else regime.hfa_points

    exp_home_raw = drives * (game.home_off_pts_per_drive * game.away_def_pts_per_drive / lg)
    exp_away_raw = drives * (game.away_off_pts_per_drive * game.home_def_pts_per_drive / lg)

    exp_home = max(3.0, exp_home_raw + 0.5 * hfa + game.home_depth_pts_delta)
    exp_away = max(3.0, exp_away_raw - 0.5 * hfa + game.away_depth_pts_delta)

    pmf = _discrete_margin_pmf(
        mean_margin=exp_home - exp_away,
        margin_sd=regime.margin_sd,
        tie_prob_close=regime.reg_ot_tie_prob_when_close,
        key_weights=regime.key_number_pmf_weights,
    )
    expected_margin = math.fsum(m * p for m, p in pmf.items())
    fair_spread_home = -expected_margin
    fair_total = exp_home + exp_away

    p_home_win = math.fsum(p for m, p in pmf.items() if m > 0)
    p_away_win = math.fsum(p for m, p in pmf.items() if m < 0)
    p_tie = pmf.get(0, 0.0)

    # Conditional two-way moneyline (push on tie per standard US sportsbook 2-way NFL ML rules)
    denom_no_tie = p_home_win + p_away_win
    p_home_2way = p_home_win / denom_no_tie
    p_away_2way = p_away_win / denom_no_tie

    cover_probs = None
    if target_spread_home is not None:
        # Home covers if HomeMargin + target_spread_home > 0; pushes if == 0
        p_cov = math.fsum(p for m, p in pmf.items() if (m + target_spread_home) > 1e-9)
        p_loss = math.fsum(p for m, p in pmf.items() if (m + target_spread_home) < -1e-9)
        p_push = math.fsum(p for m, p in pmf.items() if abs(m + target_spread_home) <= 1e-9)
        cover_probs = {
            "line_home": target_spread_home,
            "p_cover": p_cov,
            "p_loss": p_loss,
            "p_push": p_push,
        }

    return {
        "game_id": game.game_id,
        "status": "computed_from_supplied_inputs",
        "exp_home_pts": exp_home,
        "exp_away_pts": exp_away,
        "fair_spread_home": fair_spread_home,
        "fair_total": fair_total,
        "home_win_prob": p_home_win,
        "away_win_prob": p_away_win,
        "tie_prob": p_tie,
        "home_ml_no_tie_prob": p_home_2way,
        "fair_home_ml": prob_to_fair_american(p_home_2way),
        "fair_away_ml": prob_to_fair_american(p_away_2way),
        "key_3_mass": pmf.get(3, 0.0) + pmf.get(-3, 0.0),
        "key_7_mass": pmf.get(7, 0.0) + pmf.get(-7, 0.0),
        "spread_cover_probs": cover_probs,
    }
