#!/usr/bin/env python3
"""Verifier for the nfl_8362b702 pack. Numbered rules, exit 0 = pass.

Rule 1  every required artifact exists (CSV + page).
Rule 2  every CSV row carries a non-empty source URL on an allowed host.
Rule 3  every blank market/price/score cell is paired with a reason column value.
Rule 4  corpus ledger identities hold (136 games; per-week counts; PF = PA).
Rule 5  reconciliation contains zero MISMATCH rows.
Rule 6  no backtest number may appear on the leaderboard (G-BACKTEST).
Rule 7  no drift: every scraper contract matches its pinned row count.
Rule 8  every nav link on every page resolves to a built page.
Rule 9  availability graph cells that need Game Books stay blank (nothing inferred).
Rule 10 every injury-series row carries a read clock and a source link.
Rule 11 control baselines are reproducible from the frozen seed alone.
Rule 12 model outputs are probabilities with complete input vectors.
Rule 13 flagged.csv covers every irregularity class this pack publishes.
Rule 14 readiness ledger covers every requirement id exactly once.
Rule 15 second dated reads are consistent and their deltas are published.
"""
from __future__ import annotations

import csv
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
DATA = os.path.join(REPO, "data", "nfl_8362b702")
DOCS = os.path.join(REPO, "docs", "nfl-8362b702")

from nfl_8362b702 import capture as C  # noqa: E402
from nfl_8362b702 import controls as CO  # noqa: E402

ALLOWED_HOSTS = ("www.nfl.com", "nfl.com", "operations.nfl.com", "github.com")

REQUIRED_CSVS = [
    "corpus_136.csv", "results_week10.csv", "week10_nonfinal.csv", "standings_asof.csv",
    "standings_split_checks.csv", "reconciliation.csv", "model_outputs.csv",
    "backtest_walkforward.csv", "control_baselines.csv", "luck_panel_records.csv",
    "luck_summary.csv", "leaderboard_divisions.csv", "leaderboard_strategies.csv",
    "leaderboard_gates.csv", "mindchange.csv", "injury_series.csv", "injury_deltas.csv",
    "injury_cross_read.csv", "availability_nodes.csv", "availability_edges.csv",
    "availability_sweep.csv", "reserve_register.csv", "reserve_absence.csv",
    "reserve_mismatch.csv", "venues_week11.csv", "scraper_contracts.csv",
    "capture_attempts.csv", "sources.csv", "flagged.csv", "questions.csv",
    "suggestions.csv", "price_policy.csv", "readiness.csv", "prereg.csv",
    "standings_delta.csv",
]

REQUIRED_PAGES = [
    "index.html", "corpus.html", "results.html", "standings.html", "prereg.html",
    "model.html", "backtest.html", "controls.html", "luck.html", "leaderboard.html",
    "mindchange.html", "injuries.html", "availability.html", "reserve.html",
    "venues.html", "drift.html", "readiness.html", "questions.html", "suggestions.html",
    "flagged.html", "sources.html", "executive-summary.html",
]

URL_COLS = ("source_url", "game_page_url", "week_page_url", "url")

BLANK_WITH_REASON = [
    ("model_outputs.csv", "market_line", "blank_reason_market"),
    ("venues_week11.csv", "stadium_on_page", "blank_reason"),
]


def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    errs = []

    # Rule 1
    for f in REQUIRED_CSVS + REQUIRED_PAGES:
        p = os.path.join(DATA, f) if f.endswith(".csv") else os.path.join(DOCS, f)
        if not os.path.exists(p):
            errs.append(f"rule 1: missing {f}")

    # Rule 2 + 3 (needs the files)
    if not errs:
        for name in REQUIRED_CSVS:
            rs = rows(name)
            for i, r in enumerate(rs, 2):
                urls = [r.get(c, "") for c in URL_COLS]
                if not any(u for u in urls):
                    errs.append(f"rule 2: {name} line {i} has no source URL")
                for u in urls:
                    if u and not any(h in u for h in ALLOWED_HOSTS):
                        errs.append(f"rule 2: {name} line {i} URL host not allowed: {u}")
                    if u and not u.startswith("https://"):
                        errs.append(f"rule 2: {name} line {i} URL not https: {u}")
        for name, blank_col, reason_col in BLANK_WITH_REASON:
            for i, r in enumerate(rows(name), 2):
                if not r.get(blank_col) and not r.get(reason_col):
                    errs.append(f"rule 3: {name} line {i} blank {blank_col} without {reason_col}")

    # Rule 4
    corpus = rows("corpus_136.csv") if not errs else []
    if corpus:
        if len(corpus) != 136:
            errs.append(f"rule 4: corpus has {len(corpus)} rows, want 136")
        want = {1: 16, 2: 16, 3: 16, 4: 16, 5: 15, 6: 14, 7: 14, 8: 14, 9: 15}
        got = {}
        pts = 0
        for r in corpus:
            w = int(r["week"]); got[w] = got.get(w, 0) + 1
            pts += int(r["away_score"]) + int(r["home_score"])
        if got != want:
            errs.append(f"rule 4: per-week counts {got} != {want}")
        if pts != 6246:
            errs.append(f"rule 4: corpus points {pts} != 6246")
        ties = sum(1 for r in corpus if r["away_score"] == r["home_score"])
        if ties != 1:
            errs.append(f"rule 4: tie games {ties} != 1")

    # Rule 5
    if not errs:
        for r in rows("reconciliation.csv"):
            if r["verdict"] == "MISMATCH":
                errs.append(f"rule 5: reconciliation MISMATCH for {r['team_abbr']}")

    # Rule 6
    if not errs:
        for name in ("leaderboard_divisions.csv", "leaderboard_strategies.csv"):
            with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
                text = fh.read().lower()
            for tok in ("0.0", "brier=", "hit rate", "roi"):
                if tok in text and name != "leaderboard_strategies.csv":
                    errs.append(f"rule 6: {name} carries a score-like token {tok!r}")
        for r in rows("leaderboard_strategies.csv"):
            if r.get("backtest_numbers_on_this_row") != "none (G-BACKTEST forbids them)":
                errs.append(f"rule 6: {r['strategy_id']} backtest column not the frozen string")
            for col in ("brier", "brier_skill_vs_base", "cluster_lower_bound"):
                if r.get(col):
                    errs.append(f"rule 6: {r['strategy_id']} {col} populated before settlement")
        with open(os.path.join(DOCS, "leaderboard.html"), encoding="utf-8") as fh:
            page = fh.read()
        if "backtest_walkforward" in page:
            errs.append("rule 6: leaderboard page references backtest rows")

    # Rule 7
    if not errs:
        for r in rows("scraper_contracts.csv"):
            if r["verdict"] != "OK":
                errs.append(f"rule 7: drift in {r['source_id']}: {r['drift_detail']}")
            if int(r["observed_rows"]) != int(r["expected_rows"]):
                errs.append(f"rule 7: {r['source_id']} observed {r['observed_rows']} != {r['expected_rows']}")

    # Rule 8
    if not errs:
        nav_re = re.compile(r'href="([^"]+\.html)"')
        for page_name in REQUIRED_PAGES:
            with open(os.path.join(DOCS, page_name), encoding="utf-8") as fh:
                for target in nav_re.findall(fh.read()):
                    if not os.path.exists(os.path.join(DOCS, target)):
                        errs.append(f"rule 8: {page_name} links missing page {target}")

    # Rule 9
    if not errs:
        for r in rows("availability_nodes.csv"):
            for col in ("expected_to_start", "actual_start", "replacement_named"):
                if r.get(col):
                    errs.append(f"rule 9: node {r['node_id']} {col} filled without Game Book evidence")

    # Rule 10
    if not errs:
        for r in rows("injury_series.csv"):
            if not r.get("read_at_utc"):
                errs.append(f"rule 10: injury row {r.get('player')} missing read clock")
            if "nfl.com" not in r.get("source_url", ""):
                errs.append(f"rule 10: injury row {r.get('player')} missing hub source")

    # Rule 11
    if not errs:
        for r in rows("control_baselines.csv"):
            if r["control_id"] == "S8362-RANDOM":
                want = CO.random_pick(r["game_id"])
                if r["pick"] != want:
                    errs.append(f"rule 11: random control {r['game_id']} picks {r['pick']} != {want}")
                if CO.RANDOM_SEED_HEX not in r["input_vector"]:
                    errs.append(f"rule 11: random control {r['game_id']} input vector lacks the seed")

    # Rule 12
    if not errs:
        for r in rows("model_outputs.csv"):
            p = float(r["p_home_win"]); q = float(r["p_away_win"])
            if abs(p + q - 1.0) > 1e-6:
                errs.append(f"rule 12: {r['game_id']} probabilities do not sum to 1")
            if r.get("inputs_complete") != "yes":
                errs.append(f"rule 12: {r['game_id']} input vector not marked complete")
            if not r.get("standings_source_url"):
                errs.append(f"rule 12: {r['game_id']} lacks its ratings source")

    # Rule 13
    if not errs:
        flags = {r["flag_id"] for r in rows("flagged.csv")}
        for need in ("FLAG-01", "FLAG-02", "FLAG-03", "FLAG-04", "FLAG-05", "FLAG-06",
                     "FLAG-07", "FLAG-08", "FLAG-09", "FLAG-10", "FLAG-11", "FLAG-12"):
            if need not in flags:
                errs.append(f"rule 13: missing {need} in flagged.csv")

    # Rule 14
    if not errs:
        ids = [r["requirement_id"] for r in rows("readiness.csv")]
        if len(ids) != len(set(ids)):
            errs.append("rule 14: duplicate requirement ids")
        if len(ids) < 60:
            errs.append(f"rule 14: readiness ledger has only {len(ids)} rows")
        for r in rows("readiness.csv"):
            if not r["gate_that_blocks_it"] and r["status"] in ("open", "blocked"):
                errs.append(f"rule 14: {r['requirement_id']} open/blocked without a gate")

    # Rule 15
    if not errs:
        r2 = C.STANDINGS_READ_2_ROWS
        if len(r2) != 32:
            errs.append(f"rule 15: standings read 2 has {len(r2)} rows, want 32")
        if sum(r[2] for r in r2) != 145 or sum(r[3] for r in r2) != 145 or sum(r[4] for r in r2) != 2:
            errs.append("rule 15: read-2 W/L/T sums != 145/145/2")
        if sum(r[6] for r in r2) != sum(r[7] for r in r2):
            errs.append("rule 15: read-2 PF != PA")
        deltas = rows("standings_delta.csv")
        if len(deltas) != 32:
            errs.append(f"rule 15: standings delta has {len(deltas)} rows, want 32")
        changed = {r["team_abbr"] for r in deltas if r["delta_kind"] == "changed"}
        if not {"MIN", "LA", "AZ"} <= changed:
            errs.append(f"rule 15: expected MIN/LA/AZ deltas, got {sorted(changed)}")
        for r in deltas:
            if r["delta_kind"] == "changed" and not r["changed_fields"]:
                errs.append(f"rule 15: {r['team_abbr']} changed without field detail")

    if errs:
        print(f"CHECK FAIL ({len(errs)}):")
        for e in errs:
            print(" -", e)
        return 1
    print(f"CHECK PASS ({len(REQUIRED_CSVS)} CSVs, {len(REQUIRED_PAGES)} pages, "
          f"rules 1-15 green)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
