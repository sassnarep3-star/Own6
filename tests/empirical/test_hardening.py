"""Adversarial tests for the hardened fail-closed engine.

All fixtures here are synthetic and confined to tests. They never enter the
published report or claim to be NBA observations.
"""
import csv
import json
import math
from dataclasses import replace
from pathlib import Path

import pytest

from nba_lab.assurance import load_evidence
from nba_lab.contracts import FIELDS, ContractError, Observation, load_ledger
from nba_lab.experiments import RESIDUAL_FIELDS, correlation_report, load_residuals
from nba_lab.gates import empty_metrics, evaluate_gates, summarize
from nba_lab.models import shrunk_prop_projection
from nba_lab.pricing import american_to_implied, prob_to_american
from nba_lab.registry import STRATEGIES
from nba_lab.statistics import cluster_bootstrap, cluster_correlation

IDS = {s["id"] for s in STRATEGIES}
HOSTS = {"provider.example"}
LICENSES = {"lic-test"}


def row(**overrides):
    base = {
        "observation_id": "obs-1", "event_id": "event-1", "strategy_id": "L1", "split": "holdout",
        "event_start_utc": "2026-11-03T00:00:00+00:00", "forecast_time_utc": "2026-11-02T20:00:00+00:00",
        "features_asof_utc": "2026-11-02T19:00:00+00:00", "market": "moneyline", "selection": "HOME",
        "line": "", "probability": "0.60", "market_probability": "0.55", "decimal_odds": "2.0",
        "closing_decimal_odds": "1.9", "closing_line": "", "outcome": "1",
        "odds_source_url": "https://provider.example/odds", "close_source_url": "https://provider.example/close",
        "result_source_url": "https://provider.example/result", "feature_source_url": "https://provider.example/features",
        "odds_sha256": "a" * 64, "close_sha256": "b" * 64, "result_sha256": "c" * 64, "feature_sha256": "d" * 64,
        "license_id": "lic-test", "settlement_url": "https://provider.example/rules",
        "model_version": "test-v1", "dependence_evidence": "not_required",
    }
    base.update(overrides)
    return base


def obs(**overrides):
    return Observation.from_row(row(**overrides), IDS, HOSTS, LICENSES)


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def rights_file(tmp_path):
    path = tmp_path / "rights.json"
    path.write_text(json.dumps({
        "approved_hosts": ["provider.example"],
        "rows": [{"id": "lic-test", "provider": "Synthetic test", "status": "rights_reviewed",
                  "contract_url": "https://provider.example/contract", "contract_sha256": "e" * 64,
                  "reviewed_by": "test", "reviewed_on": "2026-11-03",
                  "use_scope": ["model_research", "public_summary"]}],
    }))
    return path


def test_fair_american_price_has_no_invented_vig():
    assert prob_to_american(0.5) == 100
    assert prob_to_american(0.6) == -150
    assert prob_to_american(0.4) == 150
    assert american_to_implied(prob_to_american(0.6)) == pytest.approx(0.6)


def test_zero_minute_history_is_retained():
    proj = shrunk_prop_projection([0, 20, 30], [0, 20, 30], league_rate=1.0)
    assert proj["n_prior_games"] == 3
    assert proj["projected_minutes"] == pytest.approx(50 / 3)
    with pytest.raises(ValueError):
        shrunk_prop_projection([0, 0], [0, 0], league_rate=1.0)
    with pytest.raises(ValueError):
        shrunk_prop_projection([0, 20], [1, 20], league_rate=1.0)


def test_market_must_match_strategy():
    with pytest.raises(ContractError, match="market does not match"):
        obs(strategy_id="L2", market="moneyline")


def test_selection_edge_and_ev_are_enforced():
    with pytest.raises(ContractError, match="probability edge"):
        obs(probability="0.56", market_probability="0.55")
    with pytest.raises(ContractError, match="EV threshold"):
        obs(probability="0.55", market_probability="0.50", decimal_odds="1.85")


def test_combo_push_requires_leg_contract():
    with pytest.raises(ContractError, match="partial-void"):
        obs(strategy_id="X1", market="parlay", dependence_evidence="verified", outcome="0.5")


def test_event_timestamp_consistency(tmp_path):
    ledger = tmp_path / "observations.csv"
    write_csv(ledger, FIELDS, [row(), row(observation_id="obs-2", event_start_utc="2026-11-03T01:00:00+00:00")])
    with pytest.raises(ContractError, match="inconsistent event_start"):
        load_ledger(ledger, rights_file(tmp_path), IDS)


def test_devig_clv_and_moved_line_blank(tmp_path):
    o = obs()
    assert o.clv is None
    ledger = tmp_path / "observations.csv"
    closing = tmp_path / "closing_probabilities.csv"
    write_csv(ledger, FIELDS, [row()])
    write_csv(closing, ["observation_id", "closing_market_probability"], [{"observation_id": "obs-1", "closing_market_probability": "0.60"}])
    loaded = load_ledger(ledger, rights_file(tmp_path), IDS)
    assert loaded[0].clv == pytest.approx(math.log(0.60 / 0.55))
    moved = row(strategy_id="L2", market="spread", line="-3.5", closing_line="-4.0")
    write_csv(ledger, FIELDS, [moved])
    write_csv(closing, ["observation_id", "closing_market_probability"], [{"observation_id": "obs-1", "closing_market_probability": ""}])
    assert load_ledger(ledger, rights_file(tmp_path), IDS)[0].clv is None
    write_csv(closing, ["observation_id", "closing_market_probability"], [{"observation_id": "obs-1", "closing_market_probability": "0.60"}])
    with pytest.raises(ContractError, match="moved line"):
        load_ledger(ledger, rights_file(tmp_path), IDS)


def test_evidence_requires_structured_artifact_binding(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({"rights_verified": True}))
    with pytest.raises(ValueError, match="schema_version"):
        load_evidence(path, config_sha256="f" * 64, ledger_sha256="0" * 64)
    path.write_text(json.dumps({"schema_version": 2, "records": []}))
    assert load_evidence(path, config_sha256="f" * 64, ledger_sha256="0" * 64)["rights_verified"] is False
    record = {"key": "rights_verified", "status": "verified", "reviewer": "test", "reviewed_on": "2026-11-03",
              "artifact_url": "https://provider.example/audit", "artifact_sha256": "1" * 64,
              "config_sha256": "f" * 64, "ledger_sha256": "0" * 64, "scope": ["all"]}
    path.write_text(json.dumps({"schema_version": 2, "records": [record]}))
    assert load_evidence(path, config_sha256="f" * 64, ledger_sha256="0" * 64)["rights_verified"] is True
    with pytest.raises(ValueError, match="not bound"):
        load_evidence(path, config_sha256="2" * 64, ledger_sha256="0" * 64)


def test_residuals_keep_zeros_and_reject_holdout(tmp_path):
    residuals = tmp_path / "residuals.csv"
    rights = rights_file(tmp_path)
    r = {"pair_id": "C-01", "event_id": "e1", "cluster_id": "s1", "split": "train", "leg_a": "0", "leg_b": "2",
         "feature_source_url": "https://provider.example/features", "feature_sha256": "d" * 64, "license_id": "lic-test"}
    write_csv(residuals, RESIDUAL_FIELDS, [r])
    loaded = load_residuals(residuals, rights)
    assert loaded["C-01"][0]["leg_a"] == 0.0
    write_csv(residuals, RESIDUAL_FIELDS, [{**r, "split": "holdout"}])
    with pytest.raises(ContractError, match="training rows only"):
        load_residuals(residuals, rights)


def test_cluster_correlation_retains_zero_pairs():
    xs, ys = [0, 1, 2, 3, 4, 5], [0, 2, 1, 4, 3, 6]
    result = cluster_correlation(xs, ys, ["a", "a", "b", "b", "c", "c"], iterations=500, seed=7)
    assert result["n"] == 6
    assert result["ci_low"] <= result["estimate"] <= result["ci_high"]
    assert result["n_clusters"] == 3


def test_combo_gate_not_satisfied_by_string_alone():
    o = obs(strategy_id="X1", market="parlay", dependence_evidence="verified")
    gates = evaluate_gates(STRATEGIES[-1], [o], summarize([o]), {"dependence_verified": True}, correlations=[])
    assert next(g for g in gates if g["id"] == "G09")["status"] == "fail"


def test_empty_gates_still_fail_closed():
    gates = evaluate_gates(STRATEGIES[0], [], empty_metrics(), {})
    assert all(g["status"] in {"blocked", "not_run"} for g in gates)
