"""Skill-Only NFL Strategy Leaderboard & Non-Monetary Research Reward Engine.

Treats NFL line origination & signal generation across Singles, Parlays, and
Player-Prop Combos as a gated competition:
- Unqualified strategies (failing ANY of `NFL-G01`..`NFL-G12`) receive `score=None`,
  `rank=None`, and `reward_tier="NONE_UNQUALIFIED"`.
- Qualified strategies are ranked strictly by a conservative composite skill index:
  `SkillScore = 100 * ROI_WeekCluster_LCB95 + 50 * Mean_SameLine_CLV + 25 * Brier_Skill_Edge`,
  preventing high-variance parlay heaters or small-sample luck from winning rewards.
- Rewards are strictly non-monetary research priority & compute allocation tiers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .gates import StrategyEvidence, evaluate_strategy_gates


@dataclass(frozen=True)
class LeaderboardEntry:
    strategy_id: str
    category: str
    qualified: bool
    gates_passed: int
    n_observations: int
    skill_score: float | None
    rank: int | None
    reward_tier: str


def compute_skill_score(ev: StrategyEvidence) -> float | None:
    gate_report = evaluate_strategy_gates(ev)
    if not gate_report["qualified"]:
        return None
    assert ev.roi_week_cluster_ci_low is not None
    assert ev.clv_mean is not None
    assert ev.market_brier is not None and ev.model_brier is not None
    brier_edge = ev.market_brier - ev.model_brier
    return 100.0 * ev.roi_week_cluster_ci_low + 50.0 * ev.clv_mean + 25.0 * brier_edge


def rank_nfl_leaderboard(
    candidates: Sequence[tuple[str, StrategyEvidence]],
) -> list[LeaderboardEntry]:
    """Rank NFL candidate strategies; unqualified candidates never receive a rank or reward."""
    scored: list[tuple[str, StrategyEvidence, dict[str, object], float | None]] = []
    for category, ev in candidates:
        rep = evaluate_strategy_gates(ev)
        sc = compute_skill_score(ev)
        scored.append((category, ev, rep, sc))

    qualified_items = [item for item in scored if item[3] is not None]
    qualified_items.sort(key=lambda item: float(item[3]), reverse=True)  # type: ignore[arg-type]

    rank_map: dict[str, tuple[int, str]] = {}
    for idx, (_, ev, _, _) in enumerate(qualified_items, 1):
        if idx == 1:
            reward = "TIER_1_GOLD_COMPUTE_AND_PAPER_ALLOCATION"
        elif idx == 2:
            reward = "TIER_2_SILVER_SHADOW_ORIGINATION_SLOT"
        elif idx == 3:
            reward = "TIER_3_BRONZE_FEATURE_PROMOTION_REVIEW"
        else:
            reward = "QUALIFIED_BENCHMARK_POOL"
        rank_map[ev.strategy_id] = (idx, reward)

    out: list[LeaderboardEntry] = []
    for category, ev, rep, sc in scored:
        if ev.strategy_id in rank_map:
            rk, rw = rank_map[ev.strategy_id]
        else:
            rk, rw = None, "NONE_UNQUALIFIED"
        out.append(
            LeaderboardEntry(
                strategy_id=ev.strategy_id,
                category=category,
                qualified=bool(rep["qualified"]),
                gates_passed=int(rep["gates_passed"]),  # type: ignore[arg-type]
                n_observations=ev.n_observations,
                skill_score=sc,
                rank=rk,
                reward_tier=rw,
            )
        )
    out.sort(key=lambda e: (0 if e.rank is not None else 1, e.rank or 9999, e.strategy_id))
    return out
