#!/usr/bin/env python3
"""Independently cross-check the luck engine against SciPy / statsmodels.

This is the numerical verification evidence for ``src/own6/power.py``: the same
quantity is computed by two independent implementations and the difference is
recorded.  It needs third-party libraries installed in the development
virtualenv (``pip install numpy scipy statsmodels``) and is therefore not part
of the stdlib CI job; the results are committed to
``data/luck/numerics_crosscheck.json`` so reviewers can read them without
installing anything.

Run: python3 scripts/verify_luck_numerics.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from own6 import power  # noqa: E402

OUT = ROOT / "data" / "luck" / "numerics_crosscheck.json"


def main() -> int:
    try:
        import numpy as np
        import scipy
        from scipy import stats
        from statsmodels.stats.multitest import multipletests
        from statsmodels.stats.proportion import proportion_confint
    except Exception as exc:  # pragma: no cover
        print(f"SKIP: third-party libraries unavailable ({exc})")
        return 2

    results: dict[str, object] = {
        "libraries": None,
        "generated_for": "2026-11-05",
        "purpose": "Independent numerical cross-check of src/own6/power.py; not NBA data.",
    }

    # 1. Normal quantiles
    z_diff = max(
        abs(power._z(alpha, sides) - float(stats.norm.ppf(1 - alpha / sides)))
        for alpha in (0.001, 0.005, 0.01, 0.05, 0.10)
        for sides in (1, 2)
    )

    # 2. Binomial p-values over a grid of records and prices
    binomial_diff = 0.0
    checked_binomial = 0
    for moneyline in (-300, -150, -110, 105, 250):
        p0 = power.break_even_probability(power.decimal_from_american(moneyline))
        for n in (20, 50, 100, 250, 1000):
            for wins in {int(round(n * f)) for f in (0.45, 0.5, 0.52, 0.55, 0.58, 0.62)}:
                if not 0 <= wins <= n:
                    continue
                want = float(stats.binomtest(wins, n, p0, alternative="greater").pvalue)
                got = power.binomial_p_value(wins, n, p0, sides=1)
                binomial_diff = max(binomial_diff, abs(got - want))
                checked_binomial += 1

    # 3. Wilson intervals
    wilson_diff = 0.0
    for wins, n in ((10, 20), (55, 100), (110, 200), (540, 1000), (560, 1000)):
        low, high = power.wilson_interval(wins, n)
        want_low, want_high = proportion_confint(wins, n, alpha=0.05, method="wilson")
        wilson_diff = max(wilson_diff, abs(low - float(want_low)), abs(high - float(want_high)))

    # 4. Benjamini-Hochberg q-values on random p-value vectors
    rng = np.random.default_rng(20261105)
    bh_diff = 0.0
    for size in (5, 10, 50, 200):
        p_values = rng.uniform(0.0001, 0.999, size=size)
        got = power.bh_qvalues([float(p) for p in p_values])
        want = multipletests(p_values, alpha=0.05, method="fdr_bh")[1]
        bh_diff = max(bh_diff, max(abs(a - float(b)) for a, b in zip(got, want)))

    # 5. Sample size vs SciPy formula, and Fisher z
    size_diff = 0
    for roi in (0.01, 0.02, 0.05):
        for moneyline in (-300, -110, 150):
            d = power.decimal_from_american(moneyline)
            p = (1 + roi) / d
            _, variance = power.bet_moments(p, d)
            expected = math.ceil(((stats.norm.ppf(0.95) + stats.norm.ppf(0.80)) ** 2) * variance / roi**2)
            size_diff = max(size_diff, abs(power.required_bets_for_roi(roi, d) - expected))

    fisher_diff = max(
        abs(
            power.fisher_required_pairs(r)
            - math.ceil(((stats.norm.ppf(0.975) + stats.norm.ppf(0.80)) / math.atanh(r)) ** 2 + 3)
        )
        for r in (0.05, 0.1, 0.2, 0.3, 0.5)
    )

    results.update(
        {
            "libraries": {
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "python": sys.version.split()[0],
            },
            "checks": [
                {
                    "check": "normal quantiles vs scipy.stats.norm.ppf",
                    "max_abs_difference": round(z_diff, 12),
                    "tolerance": "1e-10",
                    "pass": z_diff < 1e-10,
                },
                {
                    "check": "one-sided exact binomial p-value vs scipy.stats.binomtest",
                    "grid_points": checked_binomial,
                    "max_abs_difference": binomial_diff,
                    "tolerance": "1e-9",
                    "pass": binomial_diff < 1e-9,
                },
                {
                    "check": "Wilson interval vs statsmodels proportion_confint(method='wilson')",
                    "max_abs_difference": wilson_diff,
                    "tolerance": "1e-9",
                    "pass": wilson_diff < 1e-9,
                },
                {
                    "check": "Benjamini-Hochberg q-values vs statsmodels multipletests(fdr_bh)",
                    "max_abs_difference": bh_diff,
                    "tolerance": "1e-9",
                    "pass": bh_diff < 1e-9,
                },
                {
                    "check": "required-bets sample size vs closed form using scipy quantiles",
                    "max_abs_difference_bets": size_diff,
                    "tolerance": "0 bets",
                    "pass": size_diff == 0,
                },
                {
                    "check": "Fisher-z required pairs vs closed form using scipy quantiles",
                    "max_abs_difference_pairs": fisher_diff,
                    "tolerance": "0 pairs",
                    "pass": fisher_diff == 0,
                },
            ],
        }
    )
    results["all_pass"] = all(check["pass"] for check in results["checks"])
    OUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for check in results["checks"]:
        status = "PASS" if check["pass"] else "FAIL"
        print(f"{status} {check['check']}")
    print(f"all_pass={results['all_pass']} -> data/luck/numerics_crosscheck.json")
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
