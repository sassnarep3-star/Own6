"""NFL Fair-Line Origination, Depth-Deficiency, Correlation & Skill-Gated Leaderboard Package.

Pure Python 3.11 standard-library implementation (zero external runtime dependencies)
so both dependency-free CI (`tools/run_tests.py`) and pytest suites (`pytest tests`)
execute identically and deterministically.

Research & analytical verification framework only — no betting advice, no scraped
or fabricated sportsbook lines, and fail-closed `None` outputs whenever empirical
calibration data are unverified.
"""
from __future__ import annotations

from .correlations import (
    bivariate_normal_joint_prob,
    correlation_pricing_report,
    gaussian_copula_joint_prob,
    paired_pearson,
    paired_spearman,
    week_block_bootstrap_corr_ci,
)
from .depth import (
    DepthSlot,
    GamedayRosterCheck,
    UnitDeficiencySummary,
    evaluate_unit_deficiency,
    validate_nfl_gameday_roster,
)
from .gates import (
    NFL_VALIDATION_GATES,
    StrategyEvidence,
    bonferroni_holm_adjust,
    brier_score,
    evaluate_strategy_gates,
    log_loss_score,
    week_block_bootstrap_mean_ci,
)
from .leaderboard import LeaderboardEntry, rank_nfl_leaderboard
from .lines import NFLGameInput, NFLRegimeParams, originate_nfl_game
from .pricing import (
    american_to_decimal,
    american_to_implied_prob,
    devig_multiplicative,
    devig_power,
    prob_to_fair_american,
    push_aware_ev,
    same_line_clv,
)

__all__ = [
    "DepthSlot",
    "GamedayRosterCheck",
    "LeaderboardEntry",
    "NFLGameInput",
    "NFLRegimeParams",
    "NFL_VALIDATION_GATES",
    "StrategyEvidence",
    "UnitDeficiencySummary",
    "american_to_decimal",
    "american_to_implied_prob",
    "bivariate_normal_joint_prob",
    "bonferroni_holm_adjust",
    "brier_score",
    "correlation_pricing_report",
    "devig_multiplicative",
    "devig_power",
    "evaluate_strategy_gates",
    "evaluate_unit_deficiency",
    "gaussian_copula_joint_prob",
    "log_loss_score",
    "originate_nfl_game",
    "paired_pearson",
    "paired_spearman",
    "prob_to_fair_american",
    "push_aware_ev",
    "rank_nfl_leaderboard",
    "same_line_clv",
    "validate_nfl_gameday_roster",
    "week_block_bootstrap_corr_ci",
    "week_block_bootstrap_mean_ci",
]
