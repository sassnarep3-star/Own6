"""Chronological out-of-sample qualification workflow.

Only the holdout split can qualify. Every candidate in the frozen family is
evaluated, including abandoned candidates. No synthetic data enters the report.
Correlations use a strict, training-only, one-row-per-event residual contract.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

from .assurance import file_sha256, load_evidence
from .contracts import ContractError, Observation, _hash, _url, load_ledger
from .gates import empty_metrics, evaluate_gates, leaderboard, summarize
from .pricing import empirical_joint
from .registry import CONFIG, CORRELATION_PAIRS, STRATEGIES, config_sha256
from .statistics import cluster_correlation

RESIDUAL_FIELDS = [
    "pair_id", "event_id", "cluster_id", "split", "leg_a", "leg_b",
    "feature_source_url", "feature_sha256", "license_id",
]
PAIR_IDS = {p["id"] for p in CORRELATION_PAIRS}


def holdout_for(strategy_id: str, observations: list[Observation]) -> list[Observation]:
    return [o for o in observations if o.strategy_id == strategy_id and o.split == "holdout"]


def evaluate_strategy(strategy: dict, observations: list[Observation], evidence: dict,
                      correlations: list[dict] | None = None) -> dict:
    holdout = holdout_for(strategy["id"], observations)
    metrics = summarize(holdout)
    gates = evaluate_gates(strategy, holdout, metrics, evidence, correlations)
    return {
        "id": strategy["id"], "name": strategy["name"], "category": strategy["category"],
        "market": strategy["market"], "metrics": metrics, "gates": gates,
        "qualified": all(g["status"] == "pass" for g in gates),
        "source_url": strategy["source_url"],
    }


def load_residuals(path: Path, rights_path: Path) -> dict[str, list[dict]]:
    """Load authorized training residuals; retain zeros and reject ambiguity."""
    from .contracts import load_rights
    approved, licenses = load_rights(rights_path)
    rows: dict[str, list[dict]] = {pid: [] for pid in PAIR_IDS}
    if not path.exists():
        return rows
    seen = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != RESIDUAL_FIELDS:
            raise ContractError("residual header does not match the strict training-only contract")
        for number, row in enumerate(reader, 2):
            pid = (row.get("pair_id") or "").strip()
            event_id = (row.get("event_id") or "").strip()
            cluster_id = (row.get("cluster_id") or "").strip()
            if pid not in PAIR_IDS or not event_id or not cluster_id:
                raise ContractError(f"residual row {number}: unknown pair or missing event/cluster ID")
            if (pid, event_id) in seen:
                raise ContractError(f"residual row {number}: duplicate pair/event")
            if (row.get("split") or "").strip() != "train":
                raise ContractError(f"residual row {number}: correlation file must contain training rows only")
            try:
                a, b = float(row["leg_a"]), float(row["leg_b"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ContractError(f"residual row {number}: missing/nonnumeric residual") from exc
            if not math.isfinite(a) or not math.isfinite(b):
                raise ContractError(f"residual row {number}: residuals must be finite; zeros are valid")
            if pid == "C-05" and (a not in (0.0, 1.0) or b not in (0.0, 1.0)):
                raise ContractError(f"residual row {number}: cross-game win indicators must be binary")
            license_id = (row.get("license_id") or "").strip()
            if license_id not in licenses:
                raise ContractError(f"residual row {number}: no reviewed rights record")
            source = _url(row, "feature_source_url", approved)
            digest = _hash(row, "feature_sha256")
            seen.add((pid, event_id))
            rows[pid].append({"event_id": event_id, "cluster_id": cluster_id, "leg_a": a, "leg_b": b,
                              "feature_source_url": source, "feature_sha256": digest, "license_id": license_id})
    return rows


def correlation_report(residuals_path: Path, rights_path: Path) -> list[dict]:
    """Training-only paired residual correlations; missing evidence stays blank."""
    grouped = load_residuals(residuals_path, rights_path)
    rows = []
    for pair in CORRELATION_PAIRS:
        result = {**pair, "source_dataset": "Strict authorized training residual file required; no holdout residuals are used.",
                  "joint": None, "n_clusters": None}
        data = grouped[pair["id"]]
        if not data:
            result.update({"status": "unverified", "reason": "No authorized paired training residuals are available. Do not infer independence."})
            rows.append(result)
            continue
        xs = [r["leg_a"] for r in data]
        ys = [r["leg_b"] for r in data]
        groups = [r["cluster_id"] for r in data]
        try:
            stats = cluster_correlation(xs, ys, groups, iterations=CONFIG["bootstrap_iterations"],
                                        seed=CONFIG["bootstrap_seed"], alpha=CONFIG["alpha"])
            result.update({k: v for k, v in stats.items() if k != "method"})
            result["method"] = pair["method"] + " Whole-cluster interval; zeros retained."
            result["status"] = "computed" if stats["n"] >= CONFIG["min_paired_events"] and stats["n_clusters"] >= CONFIG["min_slates"] else "unstable"
            result["source_url"] = data[0]["feature_source_url"]
            if pair["id"] == "C-01":
                result["joint"] = empirical_joint([int(x > 0) for x in xs], [int(y > 0) for y in ys])
            elif pair["id"] == "C-05":
                result["joint"] = empirical_joint(xs, ys)
        except (ValueError, ZeroDivisionError) as exc:
            result.update({"estimate": None, "n": None, "ci_low": None, "ci_high": None,
                           "status": "unverified", "reason": f"Paired residuals are unusable: {exc}"})
        rows.append(result)
    return rows


def build_report(ledger_path: Path, rights_path: Path, evidence_path: Path, residuals_path: Path) -> dict:
    """Build the complete fail-closed report. Empty authorized data yields not_run."""
    strategy_ids = {s["id"] for s in STRATEGIES}
    observations = load_ledger(ledger_path, rights_path, strategy_ids)
    cfg_hash = config_sha256()
    evidence = load_evidence(evidence_path, config_sha256=cfg_hash, ledger_sha256=file_sha256(ledger_path))
    correlations = correlation_report(residuals_path, rights_path)
    strategy_rows = [evaluate_strategy(s, observations, evidence, correlations) for s in STRATEGIES]
    ranked = leaderboard(strategy_rows)
    return {
        "status": "not_run" if not observations else "run",
        "config": CONFIG, "config_sha256": cfg_hash, "external_evidence": evidence,
        "n_observations": len(observations), "strategies": strategy_rows,
        "leaderboard": ranked, "correlations": correlations, "n_qualified": len(ranked),
    }
