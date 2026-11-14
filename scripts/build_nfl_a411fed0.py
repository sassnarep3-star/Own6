#!/usr/bin/env python3
"""Build every artifact for the NFL originated-lines pack (session a411fed0).

Reads only ``data/nfl_a411fed0/raw/**`` (verbatim captures from official NFL
and NFL club pages), writes the derived CSV/PSV tables to
``data/nfl_a411fed0/`` and renders the dashboard to ``docs/nfl-a411fed0/``.

Nothing is fetched and nothing is inferred: any value that cannot be traced
to an official page is written blank with an explicit ``unverified_*`` status.
"""
from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nfl_a411fed0 import (  # noqa: E402
    correlate, dataset, depth, gates, model, questions, site, store, strategies,
)

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "nfl_a411fed0")


def write(name: str, rows, cols=None) -> int:
    rows = list(rows)
    path = os.path.join(DATA, name)
    if not rows:
        open(path, "w").write("")
        print(f"  {name}: 0 rows")
        return 0
    cols = cols or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore",
                           delimiter="|")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c, None) is None else r.get(c, ""))
                        for c in cols})
    print(f"  {name}: {len(rows)} rows x {len(cols)} cols")
    return len(rows)


def main() -> int:
    print("Fitting on verified results ...")
    games = model._games()
    side = model.fit_side(games)
    total = model.fit_total(games)
    print(f"  {len(games)} games, margin resid sd "
          f"{model._sd(side['residuals']):.2f}, HFA {side['hfa']:.2f}")

    rec = {t[0]: f"{t[4]}-{t[5]}-{t[6]}" for t in dataset.STANDINGS_THRU_W9}

    print("Writing data tables ...")
    write("results_2026_verified.psv", [
        {"season": 2026, "week": g["week"], "game_slug": g["game_slug"],
         "home_abbr": g["home"], "away_abbr": g["away"],
         "home_score": g["home_score"], "away_score": g["away_score"],
         "final_margin_home": g["margin"], "final_total": g["total"],
         "result_status": "verified_final",
         "official_source_url": g["source_url"]} for g in games])
    write("standings_2026_thru_w9.psv", dataset.standings())
    write("origination_2026_w10.psv", model.originate(games, side, total))
    write("power_ratings_2026.psv", [
        {"team_abbr": t, "margin_rating": round(side["rate"][t], 3),
         "total_rating": round(total["rate"][t], 3),
         "record_thru_w9": rec.get(t, ""),
         "rating_kind": "least_squares_sum_to_zero_from_verified_finals",
         "training_games_n": len(games),
         "official_source_url": "https://www.nfl.com/scores/2026/week-1"}
        for t in sorted(side["rate"])])
    write("walk_forward_validation.psv", model.walk_forward(games))
    write("correlations.psv", correlate.build())

    prices = store.build(games)
    write("price_snapshots_2026_w10.psv", prices)
    write("price_snapshot_coverage.psv", [store.coverage(prices)])

    drows = depth.build()
    write("injuries_2026_w10.psv", drows)
    write("depth_deficiency_2026_w10.psv", depth.summarise(drows))

    write("strategy_leaderboard.psv", strategies.build_leaderboard())
    write("signal_calibration.psv", strategies.build_calibration())

    write("validation_gates.psv", gates.build_validation())
    write("demotion_gate.psv", gates.build_demotion())
    write("luck_threshold.psv", gates.build_luck_math())
    write("feed_completeness.psv", gates._feed_completeness()["rows"])

    write("questions.psv", questions.build_questions())
    write("suggestions.psv", questions.build_suggestions())
    write("open_inputs.psv", questions.build_open_inputs())

    print("Rendering site ...")
    site.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
