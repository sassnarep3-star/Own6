"""Tests for the independent recheck helpers and the generated recheck site."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recheck = load_module("reverify_official", "scripts/reverify_official.py")


def test_cholesky_solves_a_known_system():
    # 2x + y = 5 ; x + 3y = 10  ->  x = 1, y = 3
    matrix = [[2.0, 1.0], [1.0, 3.0]]
    solution = recheck.chol_solve(recheck.cholesky(matrix), [5.0, 10.0])
    assert abs(solution[0] - 1.0) < 1e-9
    assert abs(solution[1] - 3.0) < 1e-9


def test_pearson_matches_a_hand_computed_example():
    xs = [1.0, 2.0, 3.0, 4.0]
    ys = [2.0, 4.0, 6.0, 9.0]
    result = recheck.pearson(xs, ys)
    assert result["n"] == 4
    assert 0.98 < result["r"] <= 1.0
    assert result["ci95_low"] < result["r"] < result["ci95_high"]


def test_pearson_handles_a_zero_variance_series():
    result = recheck.pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])
    assert result["r"] == 0.0


def test_exact_binomial_is_one_for_a_perfect_split():
    assert recheck.exact_binomial_p(5, 10) == 1.0


def test_exact_binomial_rejects_a_twelve_to_one_run():
    assert recheck.exact_binomial_p(1, 12) < 0.01


def test_records_counts_home_and_away_wins():
    games = [
        {"home": "AAA", "away": "BBB", "home_score": 110, "away_score": 100},
        {"home": "BBB", "away": "AAA", "home_score": 90, "away_score": 95},
    ]
    table = recheck.records(games)
    assert table["AAA"] == [2, 0]
    assert table["BBB"] == [0, 2]


def test_compare_scalar_classifies_states():
    assert recheck.compare_scalar([], "x", "c", "s", "f", "1", "1", "u")["status"] == "match"
    assert recheck.compare_scalar([], "x", "c", "s", "f", "1", "2", "u")["status"] == "mismatch"
    assert recheck.compare_scalar([], "x", "c", "s", "f", "1", "", "u")["status"] == "unverified"


def test_report_records_zero_contradictions_or_lists_them():
    report = json.loads((ROOT / "data/reverify_2026_11_05/report.json").read_text(encoding="utf-8"))
    verdict = report["verdict"]
    mismatches = [
        r
        for r in report["reconciliation"]["open_items"]
        if r["status"] in {"mismatch", "unverified"}
    ]
    assert verdict["published_values_contradicted"] == len(mismatches)
    assert verdict["qualified_strategies"] == 0
    assert verdict["authorized_observations"] == 0


def test_every_reconciliation_row_has_an_official_https_source():
    import csv

    with (ROOT / "data/reverify_2026_11_05/reconciliation.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows, "reconciliation must not be empty"
    for row in rows:
        assert row["source_url"].startswith("https://"), row["check_id"]
        assert row["status"] in {"match", "mismatch", "verified_text", "unverified"}, row["check_id"]


def test_site_checker_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_reverify.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
