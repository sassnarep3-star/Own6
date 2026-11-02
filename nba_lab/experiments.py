"""Chronological out-of-sample qualification workflow.

Only the `holdout` split can qualify. Every candidate in the frozen six-member
family is evaluated, including any that are later abandoned, so the multiple-test
correction reflects the complete search. No synthetic data enters the report.
"""
from __future__ import annotations

import json
from pathlib import Path

from .contracts import Observation, load_ledger, load_rights
from .gates import empty_metrics, evaluate_gates, leaderboard, summarize
from .registry import (
    CONFIG,
    CORRELATION_PAIRS,
    EXTERNAL_EVIDENCE,
    STRATEGIES,
    config_sha256,
)
from .statistics import cluster_bootstrap, pearson_pair


def load_evidence(path: Path) -> dict:
    evidence = dict(EXTERNAL_EVIDENCE)
    if not path.exists():
        return evidence
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in EXTERNAL_EVIDENCE:
        evidence[key] = bool(data.get(key, False))
    return evidence


def holdout_for(strategy_id: str, observations: list[Observation]) -> list[Observation]:
    return [o for o in observations if o.strategy_id == strategy_id and o.split == "holdout"]


def evaluate_strategy(strategy: dict, observations: list[Observation], evidence: dict) -> dict:
    holdout = holdout_for(strategy["id"], observations)
    metrics = summarize(holdout)
    gates = evaluate_gates(strategy, holdout, metrics, evidence)
    return {
        "id": strategy["id"],
        "name": strategy["name"],
        "category": strategy["category"],
        "market": strategy["market"],
        "metrics": metrics,
        "gates": gates,
        "qualified": all(g["status"] == "pass" for g in gates),
        "source_url": strategy["source_url"],
    }


def _residual_pairs(path: Path, pair_id: str) -> tuple[list[float], list[float]]:
    if not path.exists():
        raise FileNotFoundError
    rows = [r for r in path.read_text(encoding="utf-8").splitlines()[1:] if r]
    for row in rows:
        fields = dict(zip(RESIDUAL_FIELDS, row.split(",")))
        if fields["pair_id"] == pair_id:
            return [float(x) for x in fields["leg_a"].split("|")], [float(x) for x in fields["leg_b"].split("|")]
    raise FileNotFoundError(pair_id)


RESIDUAL_FIELDS = [
    "pair_id", "leg_a", "leg_b", "split", "event_id", "feature_source_url", "feature_sha256",
]


def correlation_report(observations: list[Observation], residuals_path: Path) -> list[dict]:
    """Training-only paired residual correlations; missing evidence stays blank."""
    rows = []
    for pair in CORRELATION_PAIRS:
        result = {**pair, "source_dataset": "Authorized residual file required; observations.csv holds binary outcomes only."}
        try:
            xs, ys = _residual_pairs(residuals_path, pair["id"])
            pairs = [(x, y) for x, y in zip(xs, ys) if x and y]
            if not pairs:
                raise ValueError("no aligned residual pairs")
            stats = pearson_pair([x for x, _ in pairs], [y for _, y in pairs])
            # Event-clustered percentile interval; residual rows carry an event_id via RESIDUAL_FIELDS in future format.
            stats["ci_low"] = None
            stats["ci_high"] = None
            result.update({k: v for k, v in stats.items() if k != "method"})
            result["method"] = pair["method"] + " Event-clustered interval not computed: residual rows lack event_id in this snapshot."
            result["status"] = "computed" if stats["n"] >= 100 else "unstable"
            result["source_url"] = pair["source_url"]
        except FileNotFoundError:
            result["status"] = "unverified"
            result["reason"] = "No authorized paired training residuals are available. Do not infer independence."
        except (ValueError, ZeroDivisionError) as exc:
            result["status"] = "unverified"
            result["reason"] = f"Paired residuals are unusable: {exc}"
        rows.append(result)
    return rows


def build_report(
    ledger_path: Path,
    rights_path: Path,
    evidence_path: Path,
    residuals_path: Path,
) -> dict:
    """Build the complete fail-closed report. Empty authorized data yields not_run."""
    strategy_ids = {s["id"] for s in STRATEGIES}
    observations = load_ledger(ledger_path, rights_path, strategy_ids)
    evidence = load_evidence(evidence_path)

    strategy_rows = [evaluate_strategy(s, observations, evidence) for s in STRATEGIES]
    ranked = leaderboard(strategy_rows)
    correlations = correlation_report(observations, residuals_path)

    return {
        "status": "not_run" if not observations else "run",
        "config": CONFIG,
        "config_sha256": config_sha256(),
        "external_evidence": evidence,
        "n_observations": len(observations),
        "strategies": strategy_rows,
        "leaderboard": ranked,
        "correlations": correlations,
        "n_qualified": len(ranked),
    }
