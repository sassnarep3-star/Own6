"""Tests for the NFL originated-lines pack (session a411fed0).

These assert the properties that would otherwise fail silently: that the
origination runs in the required order, that unverifiable values stay blank,
that correlations publish n, and that gates fail closed rather than passing
by default.

Written without importing pytest so the same file runs both under pytest and
under the repository's dependency-free runner (``tools/run_tests.py``), which
imports every ``tests/test_*.py`` in a sandbox that has no pytest installed.
"""

from __future__ import annotations

import csv
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.nfl_a411fed0 import (  # noqa: E402
    correlate, dataset, depth, gates, model, questions, store, strategies,
)

DATA = os.path.join(ROOT, "data", "nfl_a411fed0")
DOCS = os.path.join(ROOT, "docs", "nfl-a411fed0")


def _read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="|"))


# ------------------------------------------------------------------ raw inputs
def test_results_feed_is_populated_and_internally_consistent():
    rows = list(csv.DictReader(
        open(os.path.join(DATA, "raw", "results_2026_w1_9.psv")), delimiter="|"))
    assert len(rows) >= 100
    for r in rows:
        assert r["home_score"].isdigit() and r["away_score"].isdigit()
        assert r["official_source_url"].startswith("https://www.nfl.com/")
    teams = {r["home_abbr"] for r in rows} | {r["away_abbr"] for r in rows}
    assert len(teams) == 32


def test_standings_cover_32_clubs():
    st = dataset.standings()
    assert len(st) == 32
    assert sum(r["w"] for r in st) + sum(r["t"] for r in st) == \
        sum(r["l"] for r in st) + sum(r["t"] for r in st)


# ---------------------------------------------------------------------- model
def test_ratings_sum_to_zero():
    games = model._games()
    side = model.fit_side(games)
    total = model.fit_total(games)
    assert abs(sum(side["rate"].values())) < 1e-6
    assert abs(sum(total["rate"].values())) < 1e-6
    assert len(side["rate"]) == 32


def test_residuals_are_unbiased():
    games = model._games()
    side = model.fit_side(games)
    total = model.fit_total(games)
    assert abs(sum(side["residuals"]) / len(side["residuals"])) < 0.05
    assert abs(sum(total["residuals"]) / len(total["residuals"])) < 1e-6


def test_origination_emits_all_three_markets_in_order():
    rows = model.originate()
    assert len(rows) == 14
    for r in rows:
        for mkt in ("step_1_side_spread_home", "step_2_game_total",
                    "step_3_moneyline_home"):
            assert r[f"origination_{mkt}_fair_line"] != ""
            assert r[f"origination_{mkt}_market_line"] == ""
            assert r[f"origination_{mkt}_difference"] == ""
            assert r[f"origination_{mkt}_market_line_status"] == \
                "unverified_no_official_price"


def test_moneyline_is_derived_from_the_side_not_fitted_separately():
    src = open(os.path.join(ROOT, "src", "nfl_a411fed0", "model.py")).read()
    assert "win_prob_empirical(m_hat" in src
    assert "origination_step_3" in src


def test_american_odds_round_trip():
    assert model.american(0.5) == "-100"
    assert model.american(0.75) == "-300"
    assert model.american(0.25) == "+300"
    assert model.american(0.0) == ""
    assert model.american(1.0) == ""


def test_walk_forward_covers_every_available_split():
    games = model._games()
    wf = model.walk_forward(games)
    assert len(wf) == 6
    for r in wf:
        assert r["train_n"] >= 24
        assert r["test_n"] == int(r["ats_side_direction_hit"].split("/")[1])
    total_tested = sum(r["test_n"] for r in wf)
    assert total_tested == 88


# ---------------------------------------------------------------- prices
def test_price_store_enumerates_every_market_with_no_prices():
    prices = store.build()
    assert len(prices) == 84          # 14 games x 6 market families
    for p in prices:
        assert p["opening_price"] == ""
        assert p["closing_price"] == ""
        assert p["opening_status"] == store.UNVERIFIED_PRICE
    cov = store.coverage(prices)
    assert cov["status"] == "fail_closed"


# ------------------------------------------------------------ correlations
def test_every_correlation_publishes_n():
    for c in correlate.build():
        assert c["n"] and int(c["n"]) > 0
        assert c["official_source_url"]
        if int(c["n"]) >= correlate.MIN_N_FOR_PRICING:
            assert c["ci95_low"] != "" and c["ci95_high"] != ""
            assert c["ci95_low"] <= c["r"] <= c["ci95_high"]


def test_pearson_handles_degenerate_input():
    assert correlate.pearson([1, 1, 1], [2, 3, 4])["r"] == ""
    assert correlate.pearson([1, 2], [3, 4])["n"] == 2


def test_insufficient_n_is_marked_not_silently_used():
    low = [c for c in correlate.build() if c["n_status"] != "sufficient_n"]
    assert low, "expected at least one underpowered correlation"
    for c in low:
        assert int(c["n"]) < correlate.MIN_N_FOR_PRICING


# ----------------------------------------------------------------- gates
def test_gates_never_pass_by_default():
    rows = gates.build_validation()
    assert len(rows) == 10
    for r in rows:
        assert r["status"] in ("pass", "fail", "fail_closed",
                               "fail_closed_no_bets")
        assert r["threshold"] and r["evidence"]
    assert not all(r["status"] == "pass" for r in rows)


def test_price_gate_fails_closed():
    g = {r["gate_id"]: r for r in gates.build_validation()}
    assert g["A4-G05"]["status"].startswith("fail")
    assert "unverified" in g["A4-G05"]["evidence"] or "no price" in \
        g["A4-G05"]["evidence"].lower()


def test_demotion_gate_is_armed():
    d = gates.build_demotion()
    assert len(d) == 6
    for r in d:
        assert r["threshold"] and r["action"] and r["trigger"]
    assert any(r["status"] == "armed_blocking_promotion" for r in d)


def test_required_n_grows_as_the_claimed_edge_shrinks():
    assert gates.required_n(0.5238, 0.08) < gates.required_n(0.5238, 0.05)
    assert gates.required_n(0.5238, 0.05) < gates.required_n(0.5238, 0.02)
    assert gates.required_n(0.5238, 0.05) > 1000


def test_feed_completeness_detects_the_missing_week():
    fc = gates._feed_completeness()
    assert fc["captured_games"] == 120
    assert fc["teams_short"], "every club should be short at least one game"


# ------------------------------------------------------------------ depth
def test_depth_resolution_leaves_unknowns_blank_rather_than_guessing():
    rows = depth.build()
    assert len(rows) == 347
    for r in rows:
        if r["status"] == "resolved":
            assert r["replacement_player"] != ""
            assert 1 <= int(r["replacement_depth"]) <= 4
        elif r["status"] == "partial_string_known_player_not_listed":
            # we know how deep the club has to reach, but not who steps in
            assert r["replacement_player"] == ""
            assert r["replacement_string"] != ""
        else:
            assert r["replacement_player"] == ""
            assert r["replacement_string"] == ""


def test_depth_summary_labels_its_weights_as_proposed():
    s = depth.summarise(depth.build())
    assert s
    for r in s:
        assert r["score_kind"] == "proposed_weight_not_observed"


def test_name_matching_tolerates_suffixes():
    assert depth._same("Ivan Pace Jr.", "Ivan Pace")
    assert depth._same("Marvin Harrison Jr.", "Marvin Harrison Jr")
    assert not depth._same("Josh Jacobs", "Josh Jones")


# ------------------------------------------------------------- strategies
def test_leaderboard_separates_signal_from_staking():
    lb = strategies.build_leaderboard()
    assert len(lb) == 10
    for r in lb:
        for c in ("staking_flat_1u_units", "staking_kelly_quarter_units",
                  "staking_martingale_units"):
            assert c in r
        assert "hypothetical" in r["staking_note"]


def test_strategies_with_signals_are_marked_unproven_without_prices():
    lb = strategies.build_leaderboard()
    for r in lb:
        if r["signal_n"]:
            assert r["signal_verdict"].startswith("unproven")
            assert r["status"] == "paper_only"


def test_a_losing_signal_can_show_a_staking_profit():
    """The cautionary case the signal/staking split exists to expose.

    A9-S05 hits only 34% of its picks and loses money under flat staking, but
    under a doubling-up plan its running bankroll reached a positive peak
    before a drawdown far larger than any bankroll would survive. Same signal,
    opposite headline - which is why the two are never merged into one column.
    """
    lb = {r["strategy_id"]: r for r in strategies.build_leaderboard()}
    s05 = lb["A9-S05"]
    assert float(s05["signal_direction_hit_rate"]) < 0.40
    assert float(s05["staking_flat_1u_units"]) < 0
    assert float(s05["staking_martingale_peak_units"]) > 0
    assert float(s05["staking_martingale_max_drawdown"]) > 100


def test_player_prop_family_is_registered_but_blocked():
    lb = {r["strategy_id"]: r for r in strategies.build_leaderboard()}
    assert lb["A9-S10"]["family"] == "player prop combo"
    assert lb["A9-S10"]["signal_n"] == ""
    assert lb["A9-S10"]["signal_verdict"] == "not evaluable"


# ------------------------------------------------- questions & suggestions
def test_questions_split_have_and_have_not():
    q = questions.build_questions()
    assert len(q) >= 15
    assert any(x["have_it"] == "no" for x in q)
    for x in q:
        if x["have_it"] == "no":
            assert x["how_to_get_it"], f"{x['question_id']} has no route"
        assert x["official_source_url"]


def test_suggestions_are_a_review_queue_not_a_work_log():
    s = questions.build_suggestions()
    assert s
    for x in s:
        assert x["reasoning"] and x["recommended_path"] and x["priority"]
    for x in s:
        assert x["status"] in ("not_started", "blocked_on_prices",
                               "requested_via_coordination")
        if x["status"] == "blocked_on_prices":
            assert x["suggestion_id"] == "A10-S06"


# ------------------------------------------------------------------- site
def test_every_page_exists_and_is_linked():
    pages = sorted(os.path.basename(p)
                   for p in glob.glob(os.path.join(DOCS, "*.html")))
    assert len(pages) >= 12
    assert "index.html" in pages
    assert "flagged.html" in pages
    nav = open(os.path.join(DOCS, "index.html")).read()
    for p in pages:
        assert f'href="{p}"' in nav or p == "index.html"


def test_pages_link_only_to_official_domains():
    official = ("nfl.com", "packers.com", "seahawks.com", "vikings.com",
                "dallascowboys.com", "houstontexans.com")
    for p in glob.glob(os.path.join(DOCS, "*.html")):
        txt = open(p).read()
        for url in _hrefs(txt):
            assert any(o in url for o in official), f"{p}: {url}"


def _hrefs(txt):
    import re
    return re.findall(r'href="(https?://[^"]+)"', txt)


def test_every_data_row_cites_a_source():
    for name in sorted(os.listdir(DATA)):
        if not name.endswith(".psv"):
            continue
        rows = _read(name)
        if not rows:
            continue
        url_keys = [k for k in rows[0].keys() if "url" in k.lower()]
        assert url_keys, f"{name} has no source-url column"
        for i, r in enumerate(rows):
            assert any((r.get(k) or "").strip() for k in url_keys), \
                f"{name} row {i} has no source url"
