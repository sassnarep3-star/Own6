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
    "n", "events", "slates", "wins", "losses", "pushes", "win_rate", "roi", "roi_lower", "roi_upper",
    "clv_mean", "clv_lower", "clv_upper", "brier_model", "brier_market", "brier_edge_lower",
    "logloss_model", "logloss_market", "logloss_edge_lower", "breakeven_mean",
    "p_raw", "p_adjusted", "roi_p", "brier_p", "logloss_p", "clv_p", "qualification_p_adjusted",
    "max_drawdown_units", "model_versions",
]
COMBO_PAIR = {"C1": "C-01", "X1": "C-05"}


def empty_metrics() -> dict:
    return {key: None for key in METRIC_KEYS} | {"calibration": []}


def _empty_clv() -> dict:
    return {"mean": None, "lower": None, "upper": None, "p_one_sided_greater": None}


def summarize(observations: Sequence[Observation], family_size: int = CONFIG["family_size"]) -> dict:
    """Compute slate-clustered statistics; requires aligned, finite inputs."""
    if not isinstance(family_size, int) or family_size < 1:
        raise ValueError("family size must be a positive integer")
    if not observations:
        return empty_metrics()

    ordered = sorted(observations, key=lambda o: (o.event_start, o.observation_id))
    nonpush = [o for o in ordered if o.outcome != 0.5]
    groups = [o.cluster_id for o in ordered]
    returns = [o.net_return for o in ordered]

    roi = cluster_bootstrap(
        returns, groups,
        iterations=CONFIG["bootstrap_iterations"], seed=CONFIG["bootstrap_seed"], alpha=CONFIG["alpha"],
    )
    clv_values = [o.clv for o in ordered]
    clv = _empty_clv() if any(v is None for v in clv_values) else cluster_bootstrap(
        clv_values, groups,
        iterations=CONFIG["bootstrap_iterations"], seed=CONFIG["bootstrap_seed"] + 1, alpha=CONFIG["alpha"],
    )

    result = empty_metrics()
    result.update({
        "n": len(ordered), "events": len({o.event_id for o in ordered}), "slates": len(set(groups)),
        "wins": sum(o.outcome == 1 for o in ordered), "losses": sum(o.outcome == 0 for o in ordered),
        "pushes": len(ordered) - len(nonpush), "roi": roi["mean"], "roi_lower": roi["lower"], "roi_upper": roi["upper"],
        "roi_p": roi["p_one_sided_greater"],
        "clv_mean": clv["mean"], "clv_lower": clv["lower"], "clv_upper": clv["upper"], "clv_p": clv["p_one_sided_greater"],
        "max_drawdown_units": max_drawdown(returns), "model_versions": len({o.model_version for o in ordered}),
    })

    if nonpush:
        p = [o.probability for o in nonpush]
        market_p = [o.market_probability for o in nonpush]
        y = [o.outcome for o in nonpush]
        ng = [o.cluster_id for o in nonpush]

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

        # Adjust the actual qualification statistics, not just a win-count
        # diagnostic. Missing candidates/tests are padded as p=1 so abandoning a
        # candidate cannot shrink the family. Bonferroni is valid under arbitrary
        # dependence when the input p-values are valid; bootstrap p-values are
        # approximate and remain subject to the cluster/precision gates.
        tests = [roi["p_one_sided_greater"], brier_edge["p_one_sided_greater"],
                 logloss_edge["p_one_sided_greater"], clv["p_one_sided_greater"]]
        present = [v for v in tests if v is not None]
        family_tests = family_size * CONFIG["qualification_tests_per_strategy"]
        padded = present + [1.0] * (family_tests - len(present))
        adjusted = bonferroni(padded)["adjusted"][:len(present)]

        result.update({
            "win_rate": wins / len(nonpush), "brier_model": bm, "brier_market": bb,
            "brier_edge_lower": brier_edge["lower"], "brier_p": brier_edge["p_one_sided_greater"],
            "logloss_model": lm, "logloss_market": lb,
            "logloss_edge_lower": logloss_edge["lower"], "logloss_p": logloss_edge["p_one_sided_greater"],
            "breakeven_mean": sum(null_p) / len(null_p),
            "p_raw": raw_p, "p_adjusted": bonferroni([raw_p] + [1.0] * (family_size - 1))["adjusted"][0],
            "qualification_p_adjusted": max(adjusted) if adjusted else None,
            "calibration": calibration_bins(p, y),
        })
    return result


def _combo_dependence_ok(strategy: dict, observations: Sequence[Observation], evidence: dict,
                         correlations: Sequence[dict] | None) -> bool:
    if not evidence.get("dependence_verified") or not observations:
        return False
    if not all(o.dependence_evidence == "verified" for o in observations):
        return False
    pair_id = COMBO_PAIR.get(strategy["id"])
    row = next((c for c in (correlations or []) if c["id"] == pair_id), None)
    return bool(
        row and row.get("status") == "computed"
        and row.get("n", 0) >= CONFIG["min_paired_events"]
        and row.get("n_clusters", 0) >= CONFIG["min_slates"]
        and row.get("ci_low") is not None and row.get("ci_high") is not None
        and (row.get("joint") or {}).get("p_joint") is not None
        and (row.get("joint") or {}).get("p_joint", 0) > 0
    )


def evaluate_gates(strategy: dict, observations: Sequence[Observation], metrics: dict, evidence: dict,
                   correlations: Sequence[dict] | None = None) -> list[dict]:
    """Return one result for every gate definition, in registry order."""
    has_data = bool(observations)
    combo = strategy["market"] in {"prop_combo", "parlay"}
    checks = {
        "G01": (bool(evidence.get("rights_verified")), "No artifact-bound gambling-use/data rights and market permission audit."),
        "G02": (bool(evidence.get("provenance_verified")), "Structural source checks are not an independent provenance audit."),
        "G03": (bool(evidence.get("walk_forward_verified")), "No artifact-bound audit of feature availability, fit windows and untouched holdout."),
        "G04": (has_data and metrics["n"] >= CONFIG["min_bets"] and metrics["events"] >= CONFIG["min_events"]
                and metrics["slates"] >= CONFIG["min_slates"]
                and (metrics["n"] - metrics["pushes"]) >= CONFIG["min_nonpush"]
                and bool(evidence.get("power_verified")),
                "Holdout counts, slate clusters and a training-only power/precision audit must all meet the frozen policy."),
        "G05": (has_data and metrics["brier_edge_lower"] is not None and metrics["brier_edge_lower"] > 0
                and metrics["logloss_edge_lower"] > 0,
                "Both proper-score improvements need positive slate-clustered lower bounds versus the market."),
        "G06": (has_data and metrics["roi"] is not None and metrics["roi"] > 0 and metrics["roi_lower"] > 0,
                "Post-vig ROI and its slate-clustered lower bound must be positive."),
        "G07": (has_data and metrics["clv_mean"] is not None and metrics["clv_mean"] > 0 and metrics["clv_lower"] > 0,
                "Comparable de-vigged identical-line CLV must be positive with a slate-clustered lower bound above zero; moved/missing lines block."),
        "G08": (has_data and metrics["qualification_p_adjusted"] is not None
                and metrics["qualification_p_adjusted"] < CONFIG["alpha"],
                "The actual qualification statistics must survive Bonferroni across the full frozen candidate/test family."),
        "G09": (_combo_dependence_ok(strategy, observations, evidence, correlations) if combo else has_data,
                "Combo joint residual evidence, clustered interval and paired sample are missing; singles still use slate clustering."),
        "G10": (bool(evidence.get("ledger_audited")) and bool(evidence.get("preregistered")) and has_data and metrics["model_versions"] == 1,
                "Artifact-bound ledger audit, preregistration and one frozen model version are required."),
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
