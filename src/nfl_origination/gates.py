"""12-Gate NFL Validation & Luck-Filtering Engine (`NFL-G01`..`NFL-G12`).

Random outcome variance in a 272-game regular season cannot be literally eliminated
ex-ante, so this engine removes luck from strategy qualification by rejecting small
samples, in-sample fits, unclustered standard errors, unadjusted multiple testing,
and win-rate heaters that lack statistically significant de-vigged Closing Line Value
(CLV) and proper-score superiority over the closing market.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import NormalDist
from typing import Sequence

_NORM = NormalDist()

NFL_VALIDATION_GATES: tuple[tuple[str, str, str], ...] = (
    (
        "NFL-G01",
        "Data Rights & Terms Gate",
        "Authorized NFL play-by-play and sportsbook quote license required; NFL.com Terms §§1.3 & 12 prohibit unauthorized scraping or wagering use.",
    ),
    (
        "NFL-G02",
        "90-Minute Inactive & Timestamp Gate",
        "Every feature, injury status, and depth-chart state must carry an immutable timestamp strictly preceding bet logging and the 90-minute pre-kickoff inactive deadline.",
    ),
    (
        "NFL-G03",
        "Regime-Consistent Walk-Forward Gate",
        "Strict chronological expanding-window walk-forward (`TimeSeriesSplit` by NFL week); models must explicitly account for 2025+ 35-yd Dynamic Kickoff and 10-min both-possess OT rules.",
    ),
    (
        "NFL-G04",
        "Sample Floor & Slate Breadth Gate",
        "Minimum N >= 250 settled single bets or N >= 400 prop/parlay combos spanning >= 18 distinct NFL slate weeks.",
    ),
    (
        "NFL-G05",
        "Key-Number & Push-Exact Settlement Gate",
        "Whole-number spreads (3, 7, 6, 10, 14), totals, and regular-season OT ties must be priced and settled with exact push probabilities rather than continuous Gaussian approximations alone.",
    ),
    (
        "NFL-G06",
        "Strictly Proper Scoring Rules Gate",
        "Out-of-sample Brier score AND log-loss must both be strictly lower (better) than the de-vigged closing market baseline on the exact same events.",
    ),
    (
        "NFL-G07",
        "De-Vigged Same-Line CLV Gate",
        "Mean same-line de-vigged Closing Line Value > 0 with week-clustered t-statistic >= 2.50 (separates repeatable pricing skill from post-snap fumble/tip-drill outcome luck).",
    ),
    (
        "NFL-G08",
        "NFL Week-Clustered Bootstrap ROI Gate",
        "95% week-block bootstrap confidence interval for out-of-sample holdout ROI must have lower bound strictly > 0.0.",
    ),
    (
        "NFL-G09",
        "Family-Wise Multiple-Testing Gate",
        "Holm-Bonferroni and one-step Bonferroni adjusted p-value < 0.05 across the entire frozen family M of candidate strategies and hyperparameter variants.",
    ),
    (
        "NFL-G10",
        "Starter/Backup Depth Reconciliation Gate",
        "Offensive and defensive starter vs. 2nd/3rd/4th-string replacement inputs must reconcile club injury designations, 47/48 active rules, PS elevations, and post-game snap shares.",
    ),
    (
        "NFL-G11",
        "Joint Residual Correlation & Copula Gate",
        "Mandatory for all parlays and player-prop combos: positive-definite training-only residual correlation matrix with week-clustered CIs; naive independence is automatically rejected.",
    ),
    (
        "NFL-G12",
        "Immutable Pre-Kickoff Ledger Audit Gate",
        "SHA-256 pre-game ledger hash, config hash, and independent reviewer artifact bound to every settled observation; zero retroactive deletions or selective reporting.",
    ),
)


def brier_score(probs: Sequence[float], outcomes: Sequence[int | float]) -> float:
    if len(probs) != len(outcomes) or not probs:
        raise ValueError("probs and outcomes must be non-empty and equal length")
    total = 0.0
    for p, o in zip(probs, outcomes):
        if not (0.0 <= p <= 1.0) or o not in (0, 1, 0.0, 1.0):
            raise ValueError("invalid probability or binary outcome in brier_score")
        total += (float(p) - float(o)) ** 2
    return total / len(probs)


def log_loss_score(probs: Sequence[float], outcomes: Sequence[int | float], eps: float = 1e-12) -> float:
    if len(probs) != len(outcomes) or not probs:
        raise ValueError("probs and outcomes must be non-empty and equal length")
    total = 0.0
    for p, o in zip(probs, outcomes):
        if not (0.0 <= p <= 1.0) or o not in (0, 1, 0.0, 1.0):
            raise ValueError("invalid probability or binary outcome in log_loss_score")
        pc = min(1.0 - eps, max(eps, float(p)))
        total += -(float(o) * math.log(pc) + (1.0 - float(o)) * math.log(1.0 - pc))
    return total / len(probs)


def bonferroni_holm_adjust(p_values: Sequence[float]) -> tuple[list[float], list[float]]:
    """Return (bonferroni_adjusted, holm_stepdown_adjusted) p-values across M candidates."""
    m = len(p_values)
    if m == 0:
        raise ValueError("p_values must be non-empty")
    for p in p_values:
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"invalid p-value: {p}")
    bonf = [min(1.0, float(p) * m) for p in p_values]
    order = sorted(range(m), key=lambda idx: p_values[idx])
    holm = [0.0] * m
    running_max = 0.0
    for rank, idx in enumerate(order):
        adj = min(1.0, float(p_values[idx]) * (m - rank))
        running_max = max(running_max, adj)
        holm[idx] = running_max
    return bonf, holm


def week_block_bootstrap_mean_ci(
    week_ids: Sequence[str | int],
    values: Sequence[float],
    n_resamples: int = 4000,
    confidence_level: float = 0.95,
    seed: int = 20261112,
) -> dict[str, float | int]:
    """NFL week-clustered block bootstrap mean, SE, t-stat, one-sided p-value, and CI."""
    if len(week_ids) != len(values) or not values:
        raise ValueError("week_ids and values must be non-empty and equal length")
    clusters: dict[str | int, list[float]] = {}
    for wk, v in zip(week_ids, values):
        clusters.setdefault(wk, []).append(float(v))
    keys = list(clusters.keys())
    g = len(keys)
    if g < 4:
        raise ValueError("at least 4 distinct NFL week clusters required")

    overall_mean = math.fsum(values) / len(values)
    cluster_sums = [math.fsum(clusters[k]) for k in keys]
    cluster_ns = [len(clusters[k]) for k in keys]
    n_total = len(values)
    # Cluster-robust variance of sample mean across G NFL weeks
    u_vals = [cs - cn * overall_mean for cs, cn in zip(cluster_sums, cluster_ns)]
    var_mean = (g / (g - 1.0)) * math.fsum(u * u for u in u_vals) / (n_total * n_total)
    se = math.sqrt(max(0.0, var_mean))
    t_stat = overall_mean / se if se > 1e-15 else 0.0
    one_sided_p = 1.0 - _NORM.cdf(t_stat)

    rng = random.Random(seed)
    boot_means: list[float] = []
    for _ in range(n_resamples):
        s_val = 0.0
        s_n = 0
        for _ in range(g):
            chosen = rng.randrange(g)
            s_val += cluster_sums[chosen]
            s_n += cluster_ns[chosen]
        boot_means.append(s_val / s_n)
    boot_means.sort()
    alpha = 1.0 - confidence_level
    lo = boot_means[int((alpha / 2.0) * n_resamples)]
    hi = boot_means[min(n_resamples - 1, int((1.0 - alpha / 2.0) * n_resamples))]
    return {
        "n": n_total,
        "n_weeks": g,
        "mean": overall_mean,
        "cluster_se": se,
        "t_stat": t_stat,
        "p_value_one_sided": one_sided_p,
        "ci_low": lo,
        "ci_high": hi,
    }


@dataclass(frozen=True)
class StrategyEvidence:
    strategy_id: str
    is_combo_or_parlay: bool
    has_data_license: bool = False
    has_pre_kickoff_timestamps: bool = False
    is_walk_forward_regime_consistent: bool = False
    n_observations: int = 0
    n_nfl_weeks: int = 0
    has_push_exact_settlement: bool = False
    model_brier: float | None = None
    market_brier: float | None = None
    model_log_loss: float | None = None
    market_log_loss: float | None = None
    clv_mean: float | None = None
    clv_week_cluster_t: float | None = None
    roi_mean: float | None = None
    roi_week_cluster_ci_low: float | None = None
    raw_p_value: float | None = None
    family_size_m: int = 10
    has_depth_reconciliation: bool = False
    has_verified_copula_correlations: bool = False
    has_sha256_ledger_audit: bool = False


def evaluate_strategy_gates(ev: StrategyEvidence) -> dict[str, object]:
    """Evaluate all 12 NFL validation gates fail-closed."""
    min_n = 400 if ev.is_combo_or_parlay else 250
    g01 = bool(ev.has_data_license)
    g02 = bool(ev.has_pre_kickoff_timestamps)
    g03 = bool(ev.is_walk_forward_regime_consistent)
    g04 = ev.n_observations >= min_n and ev.n_nfl_weeks >= 18
    g05 = bool(ev.has_push_exact_settlement)
    g06 = (
        ev.model_brier is not None
        and ev.market_brier is not None
        and ev.model_log_loss is not None
        and ev.market_log_loss is not None
        and ev.model_brier < ev.market_brier
        and ev.model_log_loss < ev.market_log_loss
    )
    g07 = (
        ev.clv_mean is not None
        and ev.clv_week_cluster_t is not None
        and ev.clv_mean > 0.0
        and ev.clv_week_cluster_t >= 2.50
    )
    g08 = ev.roi_week_cluster_ci_low is not None and ev.roi_week_cluster_ci_low > 0.0
    bonf_alpha = 0.05 / max(1, ev.family_size_m)
    g09 = ev.raw_p_value is not None and ev.raw_p_value < bonf_alpha
    g10 = bool(ev.has_depth_reconciliation)
    g11 = True if not ev.is_combo_or_parlay else bool(ev.has_verified_copula_correlations)
    g12 = bool(ev.has_sha256_ledger_audit)

    gates = {
        "NFL-G01": g01,
        "NFL-G02": g02,
        "NFL-G03": g03,
        "NFL-G04": g04,
        "NFL-G05": g05,
        "NFL-G06": g06,
        "NFL-G07": g07,
        "NFL-G08": g08,
        "NFL-G09": g09,
        "NFL-G10": g10,
        "NFL-G11": g11,
        "NFL-G12": g12,
    }
    passed_count = sum(1 for v in gates.values() if v)
    qualified = passed_count == 12
    return {
        "strategy_id": ev.strategy_id,
        "gates": gates,
        "gates_passed": passed_count,
        "gates_total": 12,
        "qualified": qualified,
        "status": "QUALIFIED_SKILL_VERIFIED" if qualified else "UNQUALIFIED_BLOCKED",
    }
