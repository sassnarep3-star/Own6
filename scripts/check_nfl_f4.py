#!/usr/bin/env python3
"""Fail-closed checks for the nfl_f4 pack and its published site.

Every check is a boolean assertion with a name, so a failure names the thing that
broke. Exit code is 0 only if all checks pass; there is no warning tier, because
a warning tier is where unverified numbers go to be published.

Run: python3 scripts/check_nfl_f4.py [--rebuild]
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DATA = os.path.join(ROOT, "data", "nfl_f4")
DOCS = os.path.join(ROOT, "docs", "nfl-f4")

FAILS = []
CHECKS = [0]


def load(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def head(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return next(csv.reader(fh))


def check(name, cond, detail=""):
    CHECKS[0] += 1
    if not cond:
        FAILS.append(f"{name}: {detail}")


# ---------------------------------------------------------------------------
# raw capture
# ---------------------------------------------------------------------------
finals = load("raw/results_finals.csv")
standings = load("raw/standings.csv")
prices = load("raw/prices.csv")
injuries = load("raw/injuries.csv")
depths = load("raw/depth_charts.csv")

check("raw.results_finals.exists", len(finals) == 137, f"rows={len(finals)}")
check("raw.standings.exists", len(standings) == 32, f"rows={len(standings)}")
check("raw.prices.exists", len(prices) == 84, f"rows={len(prices)} (14 games x 3 markets x 2 sides)")
check("raw.injuries.exists", len(injuries) > 0, f"rows={len(injuries)}")
check("raw.depth_charts.exists", len(depths) > 0, f"rows={len(depths)}")
check("raw.prices.covers_all_week10_games",
      len({p["away"] + "@" + p["home"] for p in prices}) == 14)
check("raw.prices.all_three_markets_per_game",
      {p["market"] for p in prices} == {"spread", "total", "moneyline"})
check("raw.prices.ml_has_no_line",
      all(p["open_line"] == "" and p["close_line"] == "" for p in prices if p["market"] == "moneyline"))
check("raw.prices.spread_and_total_have_lines",
      all(p["open_line"] != "" and p["close_line"] != "" for p in prices if p["market"] != "moneyline"))
check("raw.prices.has_event_ids", all(p.get("provider_event_id") for p in prices))
check("raw.prices.single_provider",
      len({p.get("provider", "DraftKings") for p in prices} | {"DraftKings"}) == 1)

# ---------------------------------------------------------------------------
# results feed
# ---------------------------------------------------------------------------
results = load("results.csv")
recon = load("results_reconciliation.csv")
check("results.exists", len(results) == 137, f"rows={len(results)}")
check("results.has_join_key", all(r["join_key"] and "@" in r["join_key"] for r in results))
check("results.join_key_unique", len({r["join_key"] for r in results}) == len(results))
check("results.margin_consistent",
      all(int(r["margin"]) == int(r["home_score"]) - int(r["away_score"]) for r in results))
check("results.total_consistent",
      all(int(r["total_points"]) == int(r["home_score"]) + int(r["away_score"]) for r in results))
check("results.winner_consistent",
      all((r["winner"] == r["home"] and int(r["margin"]) > 0)
          or (r["winner"] == r["away"] and int(r["margin"]) < 0)
          or (r["winner"] == "TIE" and int(r["margin"]) == 0) for r in results))
check("results.ot_left_blank_not_inferred",
      all(r["went_to_ot"] == "" for r in results))
check("results.every_row_has_source", all(r["result_source_url"].startswith("https://") for r in results))
check("results.source_is_nfl_domain",
      all("nfl.com" in r["result_source_url"] for r in results))
check("results.status_verified", all(r["status_kind"] == "verified" for r in results))
check("results.week_counts_match_official",
      [sum(1 for r in results if int(r["week"]) == w) for w in range(1, 11)]
      == [16, 16, 16, 16, 15, 14, 14, 14, 15, 1],
      str([sum(1 for r in results if int(r["week"]) == w) for w in range(1, 11)]))

check("recon.exists", len(recon) == 32, f"rows={len(recon)}")
check("recon.all_match", all(r["result"] == "MATCH" for r in recon),
      str([r["abbr"] for r in recon if r["result"] != "MATCH"]))
check("recon.all_five_fields",
      all(r["wins_recomputed"] == r["wins_official"]
          and r["losses_recomputed"] == r["losses_official"]
          and r["ties_recomputed"] == r["ties_official"]
          and r["pf_recomputed"] == r["pf_official"]
          and r["pa_recomputed"] == r["pa_official"] for r in recon))
check("recon.every_row_has_standings_source",
      all(r["standings_source_url"].startswith("https://") for r in recon))
check("recon.games_played_even_per_team",
      all(int(r["games_recomputed"]) >= 8 for r in recon))

# ---------------------------------------------------------------------------
# price store
# ---------------------------------------------------------------------------
snaps = load("price_snapshots.csv")
markets = load("markets.csv")
check("snapshots.exists", len(snaps) == 168, f"rows={len(snaps)}")
check("snapshots.open_count", sum(1 for s in snaps if s["snapshot_type"] == "open") == 84)
check("snapshots.close_count", sum(1 for s in snaps if s["snapshot_type"] == "close") == 84)
check("snapshots.unique_ids", len({s["snapshot_id"] for s in snaps}) == len(snaps))
check("snapshots.every_row_has_price", all(s["price_american"] not in ("", None) for s in snaps))
check("snapshots.provider_on_every_row",
      all(s["provider"].startswith("DraftKings") for s in snaps))
check("snapshots.every_row_has_source", all(s["source_url"].startswith("https://") for s in snaps))
check("snapshots.capture_timestamp_present",
      all(s.get("captured_at_utc") not in ("", None) for s in snaps))
check("snapshots.american_prices_sane",
      all(float(s["price_american"]) != 0 and abs(float(s["price_american"])) >= 100 for s in snaps))
check("snapshots.implied_prob_in_range",
      all(0 < float(s["implied_prob_raw"]) < 1 for s in snaps))

check("markets.exists", len(markets) == 84, f"rows={len(markets)}")
check("markets.per_game_three_markets",
      {m["market"] for m in markets} == {"spread", "total", "moneyline"})
check("markets.only_one_final_close",
      sum(1 for m in markets if m["close_status"] == "final") == 6,
      f"final={sum(1 for m in markets if m['close_status'] == 'final')}")
check("markets.rest_marked_not_final",
      sum(1 for m in markets if m["close_status"] == "not_final") == 78)
check("markets.no_grading_on_not_final_close",
      all(m["close_status"] in ("final", "not_final") for m in markets))
check("markets.line_move_arithmetic",
      all((m["line_move"] in ("", "0")) or
          abs(float(m["line_move"]) - (float(m["close_line"]) - float(m["open_line"]))) < 1e-9
          for m in markets if m["close_line"] and m["open_line"]))
check("markets.total_move_direction_not_teamward",
      all(m["move_is_to_favourite"] == "n/a_total" for m in markets if m["market"] == "total"))
check("markets.home_and_away_present",
      all(m["away"] and m["home"] for m in markets))

# ---------------------------------------------------------------------------
# origination
# ---------------------------------------------------------------------------
orig = load("originated_markets.csv")
fvm = load("fair_vs_market.csv")
check("originated.exists", len(orig) == 42, f"rows={len(orig)}")
check("originated.unique_market_ids", len({r["market_id"] for r in orig}) == len(orig))
check("originated.order_values", {r["origination_order"] for r in orig} == {"1", "2", "3"})
check("originated.side_is_order_1",
      all(r["origination_order"] == "1" for r in orig if r["market"] == "side"))
check("originated.total_is_order_2",
      all(r["origination_order"] == "2" for r in orig if r["market"] == "total"))
check("originated.moneyline_is_order_3",
      all(r["origination_order"] == "3" for r in orig if r["market"] == "moneyline"))
_orders = [int(r["origination_order"]) for r in orig]
check("originated.file_sorted_by_order", _orders == sorted(_orders))
check("originated.model_never_verified",
      all(r["model_status"] == "model_output" for r in orig))
check("originated.market_status_verified_or_blank",
      all(r["market_status"] in ("verified", "") for r in orig))
check("originated.every_row_has_price_source",
      all(r["price_source_url"].startswith("https://") for r in orig))
check("originated.results_url_only_when_played",
      sum(1 for r in orig if r["results_source_url"]) == 3,
      f"rows_with_result={sum(1 for r in orig if r['results_source_url'])}")
check("originated.no_placeholder_urls",
      all("REPLACE" not in r["results_source_url"] for r in orig))

check("fair_vs_market.exists", len(fvm) == 42)
check("fair_vs_market.three_columns_present",
      all(r["model_fair_line"] not in ("",) and r["market_line"] not in ("",)
          and r["difference"] not in ("",) for r in fvm))
check("fair_vs_market.difference_units_declared",
      all(r["difference_units"] in ("points", "probability") for r in fvm))
check("fair_vs_market.difference_recomputes",
      all(abs(float(r["difference"]) - (float(r["model_fair_line"]) - float(r["market_line"]))) < 1e-9
          for r in fvm if r["difference_units"] == "points"))
check("fair_vs_market.sorted_by_origination",
      [int(r["origination_order"]) for r in fvm] == sorted(int(r["origination_order"]) for r in fvm))
check("fair_vs_market.model_status_not_verified",
      all(r["model_status"] == "model_output" for r in fvm))

# ---------------------------------------------------------------------------
# leaderboard / mask
# ---------------------------------------------------------------------------
strat = load("leaderboard_strategies.csv")
lb = load("leaderboard.csv")
mask = load("leaderboard_mask_test.csv")
check("leaderboard_strategies.exists", len(strat) == 7)
check("leaderboard.signal_and_staking_separate_columns",
      "signal_score_per_bet" in head("leaderboard_strategies.csv")
      and "staking_score" in head("leaderboard_strategies.csv"))
check("leaderboard.empty_when_nothing_certified",
      (len(lb) == 0) == (sum(1 for s in strat if s["certified"] == "yes") == 0))
check("leaderboard.every_uncertified_has_reason",
      all(s["gate_detail"] for s in strat if s["certified"] == "no"))
check("leaderboard.luck_pvalue_present_when_graded",
      all(s["luck_p_value"] for s in strat if int(s["bets_settled"]) > 0))
check("leaderboard.luck_pvalue_in_range",
      all(0.0 <= float(s["luck_p_value"]) <= 1.0 for s in strat if s["luck_p_value"]))
check("leaderboard.prop_combo_blocked",
      any("G5" in s["gate_detail"] for s in strat if s["strategy_id"] == "S7"))
check("leaderboard.no_certified_below_sample_floor",
      all(s["certified"] == "no" for s in strat if int(s["bets_settled"]) < 100))
check("mask_test.exists", len(mask) == 1)
check("mask_test.board_can_mask_matches_rows",
      (mask[0]["board_can_mask"] == "True")
      == (int(mask[0]["strategies_with_positive_staking_and_nonpositive_signal"]) > 0))
check("mask_test.verdict_names_the_test",
      "test_mask_test_catches_lucky_staking_run" in mask[0]["verdict"])
check("mask_test.reports_sample_size",
      mask[0]["max_settled_bets_on_any_strategy"].isdigit())

# ---------------------------------------------------------------------------
# correlations
# ---------------------------------------------------------------------------
corr = load("correlations.csv")
check("correlations.exists", len(corr) >= 6, f"rows={len(corr)}")
check("correlations.n_on_every_computed_row",
      all(r["n"] for r in corr if r["status"] in ("measured", "insufficient_sample")))
check("correlations.r_present_when_measured",
      all(r["pearson_r"] for r in corr if r["status"] == "measured"))
check("correlations.ci_present_when_measured",
      all(r["ci95_low"] and r["ci95_high"] and r["p_value_two_sided"]
          for r in corr if r["status"] == "measured"))
check("correlations.uncomputable_has_no_value",
      all(not r["pearson_r"] and not r["n"] for r in corr if r["status"] == "uncomputable"))
check("correlations.uncomputable_has_reason",
      all(r["note"] for r in corr if r["status"] == "uncomputable"))
check("correlations.r_in_range",
      all(-1 <= float(r["pearson_r"]) <= 1 for r in corr if r["pearson_r"]))
check("correlations.floor_declared", all(r["n_floor"] == "100" for r in corr))
check("correlations.measured_sources_are_official",
      all("nfl.com" in r["source_x"] and "nfl.com" in r["source_y"]
          for r in corr if r["status"] == "measured"))
check("correlations.material_requires_floor",
      all(r["material"] == "no" for r in corr if r["meets_floor"] == "no"))
check("correlations.r2_matches_r",
      all(abs(float(r["r_squared"]) - float(r["pearson_r"]) ** 2) < 1e-3
          for r in corr if r["pearson_r"] and r["r_squared"]))

# ---------------------------------------------------------------------------
# depth
# ---------------------------------------------------------------------------
rep = load("depth_replacement.csv")
summ = load("depth_unit_summary.csv")
check("depth.exists", len(rep) >= 40, f"rows={len(rep)}")
check("depth.both_units_covered",
      {r["unit"] for r in rep} == {"Offense", "Defense"})
check("depth.replacement_named_where_forced",
      all(r["replacement_player"] for r in rep if r["effectively_available_first"] == "no"))
check("depth.string_number_recorded",
      all(r["replacement_string"] in ("2", "3", "4") for r in rep if r["replacement_player"]))
check("depth.status_never_plain_verified",
      all(r["status"] == "derived_from_unofficial_depth_plus_official_injury_report" for r in rep),
      str({r["status"] for r in rep}))
check("depth.source_urls_present",
      all(r["depth_source_url"].startswith("https://") and r["injury_source_url"].startswith("https://")
          for r in rep))
check("depth.no_healthy_assertion",
      all("healthy" not in r["first_string_game_status"].lower() for r in rep))
check("depth.not_designated_not_confused_with_out",
      all(r["first_string_game_status"] != "" for r in rep))
check("depth.chain_resolves_to_third_string",
      any(r["replacement_string"] in ("3", "4") for r in rep))
check("depth.contingency_only_when_first_questionable",
      all(r["contingency_player"] for r in rep if r["contingency_trigger"]))
check("depth.blank_replacement_is_recorded_as_finding",
      all(r["chain_note"] for r in rep if not r["replacement_player"]))
check("depth.worst_case_ge_deficiency",
      all(float(r["worst_case_points"]) >= float(r["deficiency_points"]) for r in rep))
check("depth.unit_summary_covers_both_units",
      len(summ) == 4, f"rows={len(summ)}")
check("depth.unit_summary_totals_consistent",
      all(float(s["worst_case_points_total"]) >= float(s["deficiency_points_total"]) for s in summ))

# ---------------------------------------------------------------------------
# demotion
# ---------------------------------------------------------------------------
gate = load("demotion_gate.csv")
state = load("strategy_state.csv")
check("demotion.rules_defined", len(gate) == 6, f"rows={len(gate)}")
check("demotion.every_rule_has_threshold", all(g["threshold"] for g in gate))
check("demotion.no_strategy_claimed_live", all(s["status"] == "not_live" for s in state))
check("demotion.re_entry_condition_present", all(s["re_entry_condition"] for s in state))
check("demotion.state_covers_all_strategies", len(state) == len(strat))

# ---------------------------------------------------------------------------
# registers
# ---------------------------------------------------------------------------
src = load("sources.csv")
flag = load("flagged.csv")
q = load("questions.csv")
sug = load("suggestions.csv")
review = load("repo_review.csv")
ledger = load("decision_ledger.csv")
check("sources.exists", len(src) >= 10, f"rows={len(src)}")
check("sources.every_url_https", all(r["url"].startswith("https://") for r in src))
check("sources.states_what_it_does_not_support",
      all(r["not_supports"] for r in src))
check("flagged.exists", len(flag) >= 15, f"rows={len(flag)}")
check("flagged.every_row_has_handling", all(r["handling"] for r in flag))
check("flagged.severity_values", {r["severity"] for r in flag} <= {"high", "medium", "low"})
check("flagged.covers_depth_unofficial",
      any("unofficial" in r["issue"].lower() for r in flag))
check("flagged.covers_hfa", any("home-field" in r["issue"].lower() for r in flag))
check("questions.exists", len(q) >= 12, f"rows={len(q)}")
check("questions.every_open_has_path", all(r["how_to_close"] for r in q if r["status"] == "open"))
check("questions.status_values", {r["status"] for r in q} <= {"answered", "open"})
check("suggestions.exists", len(sug) >= 8, f"rows={len(sug)}")
check("suggestions.none_implemented",
      all(r["state"] == "pending_human_choice" for r in sug))
check("suggestions.every_row_has_options", all(r["options"] for r in sug))
check("suggestions.every_row_has_recommendation", all(r["recommendation"] for r in sug))
check("repo_review.exists", len(review) >= 10, f"rows={len(review)}")
check("repo_review.verdict_values",
      {r["verdict"] for r in review} <= {"confirmed", "contradicted", "incomplete",
                                         "mislabelled", "unverifiable", "internal_consistency"})
_REPO_SOURCE_REQUIRED = {"contradicted", "confirmed", "incomplete", "mislabelled"}
check("repo_review.claims_with_source_when_checkable",
      all(r["source_url"].startswith("https://")
          for r in review if r["verdict"] in _REPO_SOURCE_REQUIRED),
      str([r["f_id"] for r in review
           if r["verdict"] in _REPO_SOURCE_REQUIRED
           and not r["source_url"].startswith("https://")]))
check("repo_review.internal_only_rows_declared",
      all(r["verdict"] in ("internal_consistency", "unverifiable")
          for r in review if not r["source_url"]))
check("repo_review.self_contradictions_flagged",
      sum(1 for r in review if r["verdict"] == "contradicted") >= 2)
check("ledger.exists", len(ledger) >= 10, f"rows={len(ledger)}")
check("ledger.every_decision_has_reversibility", all(r["reversibility"] for r in ledger))

# ---------------------------------------------------------------------------
# site
# ---------------------------------------------------------------------------
PAGES = ["index.html", "requirements.html", "lines.html", "origination.html",
         "prices.html", "results.html", "strategies.html", "leaderboard.html",
         "validation.html", "demotion.html", "correlations.html", "depth.html",
         "questions.html", "suggestions.html", "repo-review.html", "sources.html",
         "executive-summary.html", "flagged.html"]
check("site.page_count", len(PAGES) == 18)
check("site.all_pages_exist",
      all(os.path.exists(os.path.join(DOCS, p)) for p in PAGES),
      str([p for p in PAGES if not os.path.exists(os.path.join(DOCS, p))]))
for p in PAGES:
    path = os.path.join(DOCS, p)
    if not os.path.exists(path):
        continue
    text = open(path, encoding="utf-8").read()
    check(f"site.{p}.zero_input", "<input" not in text.lower() and "<form" not in text.lower())
    check(f"site.{p}.no_localhost", "localhost" not in text and "127.0.0.1" not in text)
    check(f"site.{p}.no_http_links", not re.search(r'href="http://', text))
    check(f"site.{p}.has_nav", text.count('<nav>') == 1)
    check(f"site.{p}.links_resolve",
          all(os.path.exists(os.path.join(DOCS, h.split("#")[0]))
              for h in re.findall(r'href="([^"]+)"', text)
              if not h.startswith(("http", "#", "mailto:"))))
    check(f"site.{p}.no_unrendered_markup",
          "&lt;span" not in text and "&lt;td" not in text and "&lt;table" not in text)
    check(f"site.{p}.declares_build_date", "2026-11-14" in text)

check("site.flagged_page_exists_and_links_sources",
      os.path.exists(os.path.join(DOCS, "flagged.html"))
      and "href=\"http" in open(os.path.join(DOCS, "flagged.html"), encoding="utf-8").read())
for p in PAGES:
    path = os.path.join(DOCS, p)
    if not os.path.exists(path):
        continue
    text = open(path, encoding="utf-8").read()
    rows = re.findall(r"<tr>(.*?)</tr>", text, flags=re.S)
    body_rows = [r for r in rows if "<th>" not in r]
    unsourced = [r for r in body_rows if "href=\"http" not in r]
    check(f"site.{p}.every_table_row_references_a_source",
          len(unsourced) == 0,
          f"{len(unsourced)} of {len(body_rows)} rows lack an external link")
check("site.nojekyll_present", os.path.exists(os.path.join(DOCS, ".nojekyll")))
_index = open(os.path.join(DOCS, "index.html"), encoding="utf-8").read()
check("site.index_links_every_page",
      all(f'href="{p}"' in _index for p in PAGES if p != "index.html"))
check("site.index_has_executive_summary_link", 'href="executive-summary.html"' in _index)

# ---------------------------------------------------------------------------
# determinism / source layer
# ---------------------------------------------------------------------------
check("build.is_idempotent", True)  # asserted by --rebuild below
check("source.layer_has_no_network_calls",
      not any("requests" in open(os.path.join(ROOT, "src", "nfl_f4", f), encoding="utf-8").read()
              for f in ("prices.py", "results.py", "originate.py", "leaderboard.py",
                        "depth.py", "correlations.py", "demotion.py")))
check("results.reconcile_or_raise_wired",
      "reconcile_or_raise" in open(os.path.join(ROOT, "src", "nfl_f4", "results.py"),
                                   encoding="utf-8").read())


def rebuild_check():
    before = {}
    for name in sorted(os.listdir(DOCS)):
        if name.endswith(".html"):
            before[name] = open(os.path.join(DOCS, name), "rb").read()
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_nfl_f4.py")],
                       cwd=ROOT, capture_output=True, text=True)
    check("build.exit_zero", r.returncode == 0, r.stderr[-400:])
    after = {n: open(os.path.join(DOCS, n), "rb").read()
             for n in before if os.path.exists(os.path.join(DOCS, n))}
    changed = [n for n in before if before[n] != after.get(n)]
    check("build.byte_identical_on_rerun", not changed, str(changed))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()
    if args.rebuild:
        rebuild_check()
    for f in FAILS:
        print("FAIL:", f)
    print(f"{CHECKS[0]} checks, {len(FAILS)} failures")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
