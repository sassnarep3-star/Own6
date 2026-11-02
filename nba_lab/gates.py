"""Every declared gate is enforced; missing evidence never counts as a pass."""
from __future__ import annotations

import math
from collections.abc import Sequence

from .contracts import Observation
from .registry import CONFIG, GATE_DEFINITIONS
from .statistics import (
    bonferroni,
    brier,
    calibration_bins,
    cluster_bootstrap,
    log_loss,
    max_drawdown,
    poisson_binomial_tail,
)

METRIC_KEYS = [
    "n", "events", "wins", "losses", "pushes", "win_rate", "roi", "roi_lower", "roi_upper",
    "clv_mean", "clv_lower", "clv_upper", "brier_model", "brier_market", "brier_edge_lower",
    "logloss_model", "logloss_market", "logloss_edge_lower", "breakeven_mean",
    "p_raw", "p_adjusted", "max_drawdown_units", "model_versions",
]


def empty_metrics() -> dict:
    return {key: None for key in METRIC_KEYS} | {"calibration": []}


def summarize(observations: Sequence[Observation], family_size: int = CONFIG["family_size"]) -> dict:
    """Compute event-clustered summary statistics; requires aligned, finite inputs."""
    if family_size < 1:
        raise ValueError("family size must be positive")
    if not observations:
        return empty_metrics()

    ordered = sorted(observations, key=lambda o: (o.event_start, o.observation_id))
    nonpush = [o for o in ordered if o.outcome != 0.5]
    groups = [o.event_id for o in ordered]
    returns = [o.net_return for o in ordered]

    roi = cluster_bootstrap(
        returns, groups,
        iterations=CONFIG["bootstrap_iterations"], seed=CONFIG["bootstrap_seed"], alpha=CONFIG["alpha"],
    )
    clv = cluster_bootstrap(
        [o.clv for o in ordered], groups,
        iterations=CONFIG["bootstrap_iterations"], seed=CONFIG["bootstrap_seed"] + 1, alpha=CONFIG["alpha"],
    )

    result = empty_metrics()
    result.update({
        "n": len(ordered), "events": len(set(groups)),
        "wins": sum(o.outcome == 1 for o in ordered), "losses": sum(o.outcome == 0 for o in ordered),
        "pushes": len(ordered) - len(nonpush), "roi": roi["mean"], "roi_lower": roi["lower"], "roi_upper": roi["upper"],
        "clv_mean": clv["mean"], "clv_lower": clv["lower"], "clv_upper": clv["upper"],
        "max_drawdown_units": max_drawdown(returns), "model_versions": len({o.model_version for o in ordered}),
    })

    if nonpush:
        p = [o.probability for o in nonpush]
        market_p = [o.market_probability for o in nonpush]
        y = [o.outcome for o in nonpush]
        ng = [o.event_id for o in nonpush]

        bm, bb = brier(p, y), brier(market_p, y)
        lm, lb = log_loss(p, y), log_loss(market_p, y)

        brier_edges = [(m0 - o.probability) ** 2 - (o.probability - o.outcome) ** 2
                       for o, m0 in zip(nonpush, market_p)]
        brier_edge = cluster_bootstrap(
            brier_edges, ng,
            iterations=CONFIG["bootstrap_iterations"], seed=CONFIG["bootstrap_seed"] + 2, alpha=CONFIG["alpha"],
        )

        logloss_edges = [
            -(o.outcome * math.log(o.market_probability) + (1 - o.outcome) * math.log1p(-o.market_probability))
            + (o.outcome * math.log(o.probability) + (1 - o.outcome) * math.log1p(-o.probability))
            for o in nonpush
        ]
        logloss_edge = cluster_bootstrap(
            logloss_edges, ng,
            iterations=CONFIG["bootstrap_iterations"], seed=CONFIG["bootstrap_seed"] + 3, alpha=CONFIG["alpha"],
        )

        null_p = [1 / o.decimal_odds for o in nonpush]
        wins = sum(o.outcome == 1 for o in nonpush)
        raw_p = poisson_binomial_tail(wins, null_p)

        result.update({
            "win_rate": wins / len(nonpush), "brier_model": bm, "brier_market": bb,
            "brier_edge_lower": brier_edge["lower"], "logloss_model": lm, "logloss_market": lb,
            "logloss_edge_lower": logloss_edge["lower"], "breakeven_mean": sum(null_p) / len(null_p),
            "p_raw": raw_p, "p_adjusted": bonferroni([raw_p] + [1.0] * (family_size - 1))["adjusted"][0],
            "calibration": calibration_bins(p, y),
        })

    return result


def evaluate_gates(strategy: dict, observations: Sequence[Observation], metrics: dict, evidence: dict) -> list[dict]:
    """Return one result for every gate definition, in registry order."""
    has_data = bool(observations)
    combo = strategy["market"] in {"prop_combo", "parlay"}
    checks = {
        "G01": (bool(evidence.get("rights_verified")), "No independently reviewed gambling-use/data rights and market permission."),
        "G02": (bool(evidence.get("provenance_verified")), "Structural source checks are not an independent provenance audit."),
        "G03": (bool(evidence.get("walk_forward_verified")), "No independent audit of feature availability, fit windows and untouched holdout."),
        "G04": (has_data and metrics["n"] >= CONFIG["min_bets"] and metrics["events"] >= CONFIG["min_events"]
                and (metrics["n"] - metrics["pushes"]) >= CONFIG["min_nonpush"],
                "Holdout bets, distinct events and non-push observations must all meet the frozen minimum."),
        "G05": (has_data and metrics["brier_edge_lower"] is not None and metrics["brier_edge_lower"] > 0
                and metrics["logloss_edge_lower"] > 0,
                "Both proper-score improvements need positive event-clustered lower bounds versus the market."),
        "G06": (has_data and metrics["roi"] > 0 and metrics["roi_lower"] > 0,
                "Post-vig ROI and its event-clustered lower bound must be positive."),
        "G07": (has_data and metrics["clv_mean"] > 0 and metrics["clv_lower"] > 0,
                "Identical-line closing-price evidence must be positive with a clustered lower bound above zero."),
        "G08": (has_data and metrics["p_adjusted"] is not None and metrics["p_adjusted"] < CONFIG["alpha"],
                "The heterogeneous-price luck diagnostic must survive correction across the entire frozen family."),
        "G09": ((bool(evidence.get("dependence_verified")) and all(o.dependence_evidence == "verified" for o in observations)) if combo else has_data,
                "Combo joint evidence is missing; singles still use event-clustered uncertainty."),
        "G10": (bool(evidence.get("ledger_audited")) and bool(evidence.get("preregistered")) and has_data and metrics["model_versions"] == 1,
                "Independent append-only timestamp/ledger audit, preregistration and one frozen model version are required."),
    }
    results = []
    for definition in GATE_DEFINITIONS:
        ok, failure = checks[definition["id"]]
        if ok:
            status, reason = "pass", "Requirement met by the supplied evidence and checks."
        elif not has_data and definition["id"] in {"G04", "G05", "G06", "G07", "G08"}:
            status, reason = "not_run", "No authorized holdout observations are available."
        elif not has_data and definition["id"] == "G09" and combo:
            status, reason = "blocked", failure
        else:
            status, reason = "fail" if has_data else "blocked", failure
        results.append({"id": definition["id"], "name": definition["name"], "status": status, "reason": reason, "source_url": definition["source_url"]})
    return results


def leaderboard(strategy_rows: Sequence[dict]) -> list[dict]:
    """Rank only full-gate qualifiers; lower bound of clustered holdout ROI first."""
    qualified = [r for r in strategy_rows if r["qualified"]]
    qualified.sort(key=lambda r: (-r["metrics"]["roi_lower"], r["id"]))
    return [{
        "rank": i, "strategy_id": r["id"], "name": r["name"],
        "score_roi_lower": r["metrics"]["roi_lower"],
        "source_url": r["source_url"], "reward": "research priority only",
    } for i, r in enumerate(qualified, 1)]
