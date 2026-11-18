"""Scoring, uncertainty, multiplicity and the removal-of-luck panel for session 0ce967db.

Implements exactly §6 and §8 of ``data/nfl_0ce967db/preregistration.md``:

* percentile bootstrap over **week clusters** (weeks resampled with replacement, all games in a
  sampled week kept together), 2,000 resamples, seed 20261118, 95% interval;
* Brier skill ``1 - BS_candidate / BS_control`` against the registered control;
* Bonferroni over the frozen family of seven;
* McNemar-style paired discordance test on per-game Brier wins as a second, independent read.

Everything is deterministic: the bootstrap uses ``random.Random(20261118)`` and no wall clock.
"""
from __future__ import annotations

import math
import random

SEED = 20261118
RESAMPLES = 2000
ALPHA = 0.05
FAMILY_SIZE = 7


def brier(probs: list[float], outcomes: list[int]) -> float:
    if not probs:
        raise ValueError("no observations")
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def log_loss(probs: list[float], outcomes: list[int]) -> float:
    eps = 1e-12
    total = 0.0
    for p, y in zip(probs, outcomes):
        q = min(1.0 - eps, max(eps, p))
        total += -(y * math.log(q) + (1 - y) * math.log(1 - q))
    return total / len(probs)


def reliability(probs: list[float], outcomes: list[int], edges=(0.0, .2, .4, .5, .6, .8, 1.0)) -> list[dict]:
    """Binned calibration table. Small bins are published with their n and not smoothed."""
    bins = []
    for lo, hi in zip(edges, edges[1:]):
        idx = [i for i, p in enumerate(probs) if lo <= p < hi or (hi == 1.0 and p == 1.0)]
        if not idx:
            bins.append({"lo": lo, "hi": hi, "n": 0, "mean_p": None, "obs_rate": None})
            continue
        bins.append({
            "lo": lo, "hi": hi, "n": len(idx),
            "mean_p": sum(probs[i] for i in idx) / len(idx),
            "obs_rate": sum(outcomes[i] for i in idx) / len(idx),
        })
    return bins


def week_cluster_bootstrap(clusters: dict[int, list[int]], values: list[float], statistic) -> dict:
    """Percentile bootstrap over week clusters.

    ``clusters`` maps week -> row indices; ``values`` is aligned with the row order and
    ``statistic(index_list)`` returns the point statistic for a resampled index list.
    """
    rng = random.Random(SEED)
    weeks = sorted(clusters)
    if len(weeks) < 2:
        return {"point": statistic(list(range(len(values)))), "lo": None, "hi": None,
                "resamples": 0, "why_blank": "fewer than two week clusters"}
    points = []
    for _ in range(RESAMPLES):
        picks = [weeks[rng.randrange(len(weeks))] for _ in weeks]
        idx: list[int] = []
        for w in picks:
            idx.extend(clusters[w])
        points.append(statistic(idx))
    points.sort()
    lo = points[int(0.025 * len(points))]
    hi = points[int(0.975 * len(points)) - 1]
    return {"point": statistic(list(range(len(values)))), "lo": lo, "hi": hi,
            "resamples": RESAMPLES, "why_blank": ""}


def brier_skill(probs: list[float], outcomes: list[int], ctrl: list[float]) -> float:
    base = brier(ctrl, outcomes)
    if base == 0:
        raise ValueError("control has zero Brier score; skill undefined")
    return 1.0 - brier(probs, outcomes) / base


def bootstrap_bss(clusters: dict[int, list[int]], probs: list[float], outcomes: list[int],
                  ctrl: list[float]) -> dict:
    def stat(idx: list[int]) -> float:
        p = [probs[i] for i in idx]
        y = [outcomes[i] for i in idx]
        c = [ctrl[i] for i in idx]
        return brier_skill(p, y, c)

    return week_cluster_bootstrap(clusters, probs, stat)


def paired_discordance(probs: list[float], outcomes: list[int], ctrl: list[float]) -> dict:
    """Count games where the candidate beat the control on squared error, and vice versa.

    This is the input to an exact sign test; it is reported beside the bootstrap because the
    two answer different questions (magnitude vs. direction of per-game wins).
    """
    better = worse = tie = 0
    for p, y, c in zip(probs, outcomes, ctrl):
        a = (p - y) ** 2
        b = (c - y) ** 2
        if a < b - 1e-15:
            better += 1
        elif a > b + 1e-15:
            worse += 1
        else:
            tie += 1
    n = better + worse
    p_value = 1.0 if n == 0 else _exact_sign_two_sided(better, n)
    return {"games_better": better, "games_worse": worse, "games_tied": tie,
            "n_discordant": n, "sign_test_p": p_value}


def _exact_sign_two_sided(k: int, n: int) -> float:
    """Two-sided exact binomial test at p=0.5."""
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def bonferroni(p_value: float, family: int = FAMILY_SIZE, alpha: float = ALPHA) -> dict:
    threshold = alpha / family
    return {"alpha": alpha, "family": family, "threshold": threshold,
            "passes": p_value < threshold, "p_times_family": min(1.0, p_value * family)}


def bootstrap_mae(clusters: dict[int, list[int]], errors: list[float]) -> dict:
    def stat(idx: list[int]) -> float:
        return sum(abs(errors[i]) for i in idx) / len(idx)

    return week_cluster_bootstrap(clusters, errors, stat)


def bootstrap_rmse(clusters: dict[int, list[int]], errors: list[float]) -> dict:
    def stat(idx: list[int]) -> float:
        return math.sqrt(sum(errors[i] ** 2 for i in idx) / len(idx))

    return week_cluster_bootstrap(clusters, errors, stat)


def bootstrap_mean_difference(clusters: dict[int, list[int]], a: list[float], b: list[float]) -> dict:
    """Paired mean difference a-b with a week-cluster percentile interval (ablation tool)."""
    diffs = [x - y for x, y in zip(a, b)]

    def stat(idx: list[int]) -> float:
        return sum(diffs[i] for i in idx) / len(idx)

    return week_cluster_bootstrap(clusters, diffs, stat)


def variance_decomposition(probs: list[float], outcomes: list[int]) -> dict:
    """Removal-of-luck panel inputs for one forecaster.

    The Murphy decomposition is exact only when forecasts are grouped by their *exact* value:
    grouping into coarse bins loses the within-bin spread and the identity
    ``Brier = reliability - resolution + uncertainty`` then fails. The first version of this
    function binned the probabilities and the identity failed by 0.0008; a test caught it and
    this is the corrected version. The binned table is still returned separately, because it is
    the readable calibration display, and it is labelled as an approximation.

    * ``reliability`` — the part of the score caused by miscalibration (luck);
    * ``resolution`` — the part earned by separating good games from bad (skill);
    * ``uncertainty`` — irreducible base-rate variance;
    * ``luck_share`` — reliability / Brier.
    """
    base = sum(outcomes) / len(outcomes)
    groups: dict[float, list[int]] = {}
    for p, y in zip(probs, outcomes):
        groups.setdefault(round(p, 9), []).append(y)
    rel = res = 0.0
    for p, ys in groups.items():
        obs = sum(ys) / len(ys)
        rel += len(ys) * (p - obs) ** 2
        res += len(ys) * (obs - base) ** 2
    n = len(outcomes)
    rel /= n
    res /= n
    unc = base * (1 - base)
    bs = brier(probs, outcomes)
    return {
        "n": n, "base_rate": base, "brier": bs,
        "reliability": rel, "resolution": res, "uncertainty": unc,
        "brier_from_decomposition": rel - res + unc,
        "luck_share": rel / bs if bs else None,
        "bins": reliability(probs, outcomes),
        "distinct_forecast_values": len(groups),
    }
