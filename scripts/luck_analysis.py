#!/usr/bin/env python3
"""Generate the luck-exclusion tables in ``data/luck/``.

Everything written here is arithmetic from :mod:`own6.power`.  No NBA score,
sportsbook price, projection, correlation estimate or return is observed,
scraped or inferred.  The tables state *requirements* ("how many bets would be
needed to tell this apart from luck"), which is the one class of number this
project can publish while verified market data is unavailable.

Run by hand:      python3 scripts/luck_analysis.py
Reproducibility:  python3 scripts/luck_analysis.py --check
The data is deterministic; ``--check`` fails if the committed files differ.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from own6 import power  # noqa: E402

OUT = ROOT / "data" / "luck"
GENERATED_FOR = "2026-11-05"
ALPHA = 0.05
POWER = 0.80

PRICE_LEVELS = [
    ("Standard spread/total", -110),
    ("Slight underdog", 120),
    ("Moderate favourite", -150),
    ("Heavy favourite", -300),
    ("Longshot moneyline", 400),
]
ROI_LEVELS = [0.01, 0.02, 0.03, 0.05, 0.10]


def fmt(value: float, places: int = 6) -> str:
    return f"{value:.{places}f}"


def required_bets_table() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for label, american in PRICE_LEVELS:
        decimal_odds = power.decimal_from_american(american)
        for roi in ROI_LEVELS:
            n = power.required_bets_for_roi(roi, decimal_odds, alpha=ALPHA, power=POWER, sides=1)
            n_bonf = power.bonferroni_required_bets(n, 200, alpha=ALPHA, power=POWER, sides=1)
            win_probability = (1.0 + roi) / decimal_odds
            _, variance = power.bet_moments(win_probability, decimal_odds)
            rows.append(
                {
                    "scenario": label,
                    "american_odds": str(american),
                    "decimal_odds": fmt(decimal_odds),
                    "true_roi_per_bet": fmt(roi, 4),
                    "true_win_probability": fmt(win_probability, 6),
                    "break_even_probability": fmt(power.break_even_probability(decimal_odds), 6),
                    "per_bet_variance": fmt(variance, 6),
                    "required_bets_alpha_0.05_power_0.80": str(n),
                    "required_bets_bonferroni_200_candidates": str(n_bonf),
                    "assumption": "one-sided test; independent fixed-price bets; stated ROI is the true edge, not an estimate",
                }
            )
    return rows


def detectable_roi_table() -> list[dict[str, object]]:
    decimal_odds = power.decimal_from_american(-110)
    # Variance depends on the true win rate; use the break-even rate so the
    # requirement is stated at the null, which is the conservative choice for
    # a small edge and keeps the row independent of any assumed edge.
    breakeven = power.break_even_probability(decimal_odds)
    _, variance = power.bet_moments(breakeven, decimal_odds)
    rows = []
    for n in (50, 100, 200, 500, 1000, 2000, 5000, 10000):
        mdr = power.minimum_detectable_roi(n, variance, alpha=ALPHA, power=POWER, sides=1)
        rows.append(
            {
                "bets": str(n),
                "american_odds": "-110",
                "decimal_odds": fmt(decimal_odds),
                "per_bet_variance_at_break_even": fmt(variance, 6),
                "minimum_detectable_roi": fmt(mdr, 6),
                "minimum_detectable_roi_percent": fmt(100.0 * mdr, 3),
                "interpretation": "ROI smaller than this is indistinguishable from luck at alpha 0.05 with 80% power",
            }
        )
    return rows


def parlay_table() -> list[dict[str, object]]:
    rows = []
    leg_american = -110
    leg_odds = power.decimal_from_american(leg_american)
    per_leg_edge = 0.02
    per_leg_true = (1.0 + per_leg_edge) / leg_odds
    for legs in (1, 2, 3, 4, 6):
        parlay_odds = leg_odds**legs
        independent_probability = per_leg_true**legs
        _, variance = power.bet_moments(independent_probability, parlay_odds)
        roi = independent_probability * parlay_odds - 1.0
        n = power.required_bets(roi, variance, alpha=ALPHA, power=POWER, sides=1)
        rows.append(
            {
                "legs": str(legs),
                "leg_price": str(leg_american),
                "parlay_decimal_odds": fmt(parlay_odds, 6),
                "true_joint_probability_independent": fmt(independent_probability, 8),
                "true_roi_per_parlay": fmt(roi, 6),
                "per_parlay_variance": fmt(variance, 6),
                "required_parlays": str(n),
                "assumption": "independent legs, equal 2% true edge per leg; dependence would change the joint probability and is NOT assumed",
            }
        )
    return rows


def correlation_table() -> list[dict[str, object]]:
    rows = []
    for r in (0.05, 0.10, 0.20, 0.30, 0.50, 0.70):
        pairs = power.fisher_required_pairs(r, alpha=ALPHA, power=POWER, sides=2)
        rows.append(
            {
                "true_correlation": fmt(r, 3),
                "required_paired_observations": str(pairs),
                "alpha": fmt(ALPHA, 3),
                "power": fmt(POWER, 2),
                "method": "Fisher z transform, two-sided test",
                "interpretation": "fewer paired observations than this cannot establish the dependence at the stated power",
            }
        )
    return rows


def multiple_testing_table() -> list[dict[str, object]]:
    decimal_odds = power.decimal_from_american(-110)
    base = power.required_bets_for_roi(0.03, decimal_odds, alpha=ALPHA, power=POWER, sides=1)
    rows = []
    for m in (1, 10, 50, 200, 1000):
        adjusted = power.bonferroni_alpha(ALPHA, m)
        rows.append(
            {
                "candidate_strategies": str(m),
                "family_alpha": fmt(ALPHA, 3),
                "per_test_alpha_bonferroni": fmt(adjusted, 8),
                "expected_false_positives_if_all_noise": fmt(power.expected_false_positives(m, ALPHA), 4),
                "required_bets_3pct_edge": str(power.bonferroni_required_bets(base, m, alpha=ALPHA, power=POWER, sides=1)),
                "interpretation": "searching more strategies raises both the false-positive count and the sample each winner must show",
            }
        )
    return rows


def luck_verdict_table() -> list[dict[str, object]]:
    rows = []
    for wins, bets in ((55, 100), (60, 100), (110, 200), (540, 1000), (560, 1000), (1120, 2000)):
        record = power.luck_verdict(wins, bets, power.decimal_from_american(-110))
        rows.append(
            {
                "wins": str(wins),
                "bets": str(bets),
                "american_odds": "-110",
                "observed_win_rate": fmt(record["observed_win_rate"], 6),
                "break_even_probability": fmt(float(record["break_even_probability"]), 6),
                "roi": fmt(float(record["roi"]), 6),
                "exact_binomial_p_value_one_sided": fmt(float(record["p_value"]), 8),
                "wilson_95_low": fmt(float(record["wilson_low"]), 6),
                "wilson_95_high": fmt(float(record["wilson_high"]), 6),
                "verdict": str(record["verdict"]),
                "interpretation": "exceeds_luck requires p < alpha AND the Wilson lower bound above break-even; illustrative arithmetic only, not a real record",
            }
        )
    return rows


def bh_example() -> dict[str, object]:
    p_values = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    q_values = power.bh_qvalues(p_values)
    return {
        "note": "Benjamini-Hochberg worked example; p-values are an arbitrary illustration of the correction, not measured strategies",
        "p_values": p_values,
        "q_values": [round(q, 6) for q in q_values],
        "rejected_at_0.05": [i for i, q in enumerate(q_values) if q <= 0.05],
    }


def build() -> dict[str, list[dict[str, object]]]:
    return {
        "required_bets.csv": required_bets_table(),
        "detectable_roi.csv": detectable_roi_table(),
        "parlay_requirements.csv": parlay_table(),
        "correlation_requirements.csv": correlation_table(),
        "multiple_testing.csv": multiple_testing_table(),
        "luck_verdicts.csv": luck_verdict_table(),
    }


def meta() -> dict[str, object]:
    return {
        "generated_for": GENERATED_FOR,
        "alpha": ALPHA,
        "power": POWER,
        "sides": 1,
        "engine": "src/own6/power.py",
        "engine_version": getattr(power, "__version__", "1.0.0"),
        "statement": (
            "All values are closed-form statistical requirements computed from the formulas in "
            "src/own6/power.py. They are not NBA observations, sportsbook prices, model estimates "
            "or evidence of an edge. No value on this page is a prediction."
        ),
        "method_sources": [
            {
                "name": "SciPy pearsonr (Fisher z reference)",
                "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html",
                "read_this_session": False,
                "note": "reference link; the doc page was not reachable from this sandbox (egress restricted to GitHub/PyPI). SciPy itself was installed from PyPI and used numerically in tests.",
            },
            {
                "name": "NIST/SEMATECH e-Handbook — confidence intervals / proportions",
                "url": "https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm",
                "read_this_session": False,
                "note": "reference link only; not read this session (egress restricted).",
            },
            {
                "name": "statsmodels multipletests (Benjamini-Hochberg)",
                "url": "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html",
                "read_this_session": False,
                "note": "reference link only; not read this session (egress restricted).",
            },
        ],
    }


def write_all() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tables = build()
    for name, rows in tables.items():
        with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    (OUT / "meta.json").write_text(json.dumps(meta(), indent=2) + "\n", encoding="utf-8")
    (OUT / "bh_example.json").write_text(json.dumps(bh_example(), indent=2) + "\n", encoding="utf-8")


def check() -> list[str]:
    problems = []
    tables = build()
    for name, rows in tables.items():
        path = OUT / name
        if not path.exists():
            problems.append(f"missing data/luck/{name}")
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
        expected = [{k: str(v) for k, v in row.items()} for row in rows]
        if existing != expected:
            problems.append(f"data/luck/{name} is out of date; run python3 scripts/luck_analysis.py")
    meta_path = OUT / "meta.json"
    if not meta_path.exists() or json.loads(meta_path.read_text(encoding="utf-8")) != json.loads(json.dumps(meta())):
        problems.append("data/luck/meta.json is out of date")
    example_path = OUT / "bh_example.json"
    if not example_path.exists() or json.loads(example_path.read_text(encoding="utf-8")) != json.loads(json.dumps(bh_example())):
        problems.append("data/luck/bh_example.json is out of date")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed data is up to date")
    args = parser.parse_args(argv)
    if args.check:
        problems = check()
        for problem in problems:
            print(f"FAIL {problem}")
        if problems:
            return 1
        print("OK: luck-exclusion data is deterministic and up to date")
        return 0
    write_all()
    print(f"wrote {len(build())} tables + meta to data/luck/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
