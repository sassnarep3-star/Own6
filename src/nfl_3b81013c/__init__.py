"""NFL Line Origination, Depth-Deficiency, Correlation & Skill-Gated Leaderboard package."""
from __future__ import annotations

from .correlations import (
    CorrelationEstimate,
    frechet_hoeffding_bounds,
    gaussian_copula_joint_prob,
    paired_residual_correlation,
)
from .depth import (
    DepthSlotStatus,
    UnitDeficiencyReport,
    check_gameday_active_limit,
    evaluate_unit_deficiency,
)
from .pricing import (
    american_to_implied_prob,
    devig_multiplicative,
    devig_shin_power,
    fair_prob_to_american,
    originate_nfl_game_lines,
    same_line_devig_clv,
)
from .validation import (
    GateResult,
    StrategyCandidate,
    evaluate_strategy_gates,
    holm_bonferroni_adjust,
    rank_skill_leaderboard,
)

__all__ = [
    "CorrelationEstimate",
    "DepthSlotStatus",
    "GateResult",
    "StrategyCandidate",
    "UnitDeficiencyReport",
    "american_to_implied_prob",
    "check_gameday_active_limit",
    "devig_multiplicative",
    "devig_shin_power",
    "evaluate_strategy_gates",
    "evaluate_unit_deficiency",
    "fair_prob_to_american",
    "frechet_hoeffding_bounds",
    "gaussian_copula_joint_prob",
    "holm_bonferroni_adjust",
    "originate_nfl_game_lines",
    "paired_residual_correlation",
    "rank_skill_leaderboard",
    "same_line_devig_clv",
]
