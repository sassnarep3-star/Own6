#!/usr/bin/env python3
"""Run the fail-closed Own6 empirical lab. No manual input, network, or fabrication.

Usage:
    python scripts/run_lab.py

Writes data/empirical/report.json and report.csv. With the bundled empty
observation ledger it deterministically reports status=not_run. Adding authorized
holdout rows does not automatically qualify anything: every gate must pass.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nba_lab.experiments import build_report  # noqa: E402
from nba_lab.registry import STRATEGIES  # noqa: E402

METRIC_FIELDS = [
    "n", "events", "wins", "losses", "pushes", "win_rate", "roi", "roi_lower", "roi_upper",
    "clv_mean", "clv_lower", "clv_upper", "brier_model", "brier_market", "brier_edge_lower",
    "logloss_model", "logloss_market", "logloss_edge_lower", "breakeven_mean", "p_raw", "p_adjusted",
]


def fmt(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return value


def write_csv(path: Path, report: dict) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "strategy_id", "name", "status", "qualified",
            *METRIC_FIELDS,
            *[f"gate_{g['id']}" for g in report["strategies"][0]["gates"]],
            "source_url",
        ])
        for row in report["strategies"]:
            writer.writerow([
                row["id"], row["name"], report["status"], row["qualified"],
                *[fmt(row["metrics"].get(key)) for key in METRIC_FIELDS],
                *[g["status"] for g in row["gates"]],
                row["source_url"],
            ])


def main() -> int:
    report = build_report(
        ROOT / "data/empirical/observations.csv",
        ROOT / "data/empirical/licenses.json",
        ROOT / "data/empirical/evidence.json",
        ROOT / "data/empirical/residuals.csv",
    )
    out = ROOT / "data/empirical"
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out / "report.csv", report)

    if report["status"] == "not_run":
        print(f"FAIL-CLOSED: {report['n_observations']} authorized observations; status=not_run, leaderboard empty.")
        print(f"Strategies: {len(report['strategies'])}; gates: {len(report['strategies'][0]['gates'])}.")
        print("Report written to data/empirical/report.json and report.csv.")
        return 0

    qualified = [r for r in report["leaderboard"]]
    print(f"RUN: {report['n_observations']} observations; {report['n_qualified']} qualified strategy(s).")
    for row in qualified:
        print(f"  rank {row['rank']}: {row['strategy_id']} {row['name']} ROI lower={row['score_roi_lower']:.6g}")
    print("Report written to data/empirical/report.json and report.csv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
