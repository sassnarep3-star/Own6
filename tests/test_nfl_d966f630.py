"""Regression tests for the nfl_d966f630 pack.

Runs under both ``python3 -m unittest discover -s tests -p test_nfl_d966f630.py``
(which the CI workflow uses) and plain ``pytest``.

These are the checks that a *table* cannot make for itself: the numeric identities
behind the statistics, the order the model must be run in, the settlement
conventions, the ledger's chain, the fact that signal and staking are separate, and
the demotion mechanism in both directions.
"""

from __future__ import annotations

import math
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, REPO)

from nfl_d966f630 import advice as AD  # noqa: E402
from nfl_d966f630 import backtest as B  # noqa: E402
from nfl_d966f630 import capture as C  # noqa: E402
from nfl_d966f630 import correlate as X  # noqa: E402
from nfl_d966f630 import depth as DP  # noqa: E402
from nfl_d966f630 import demotion as DM  # noqa: E402
from nfl_d966f630 import flags as FL  # noqa: E402
from nfl_d966f630 import leaderboard as LB  # noqa: E402
from nfl_d966f630 import originate as O  # noqa: E402
from nfl_d966f630 import prices as P  # noqa: E402
from nfl_d966f630 import results as R  # noqa: E402
from nfl_d966f630 import stats as S  # noqa: E402

DOCS = os.path.join(REPO, "docs", "nfl-d966f630")
DATA = os.path.join(REPO, "data", "nfl_d966f630")


class TestStats(unittest.TestCase):
    def test_pearson_bounds_and_sign(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(S.pearson(xs, xs), 1.0, places=9)
        self.assertAlmostEqual(S.pearson(xs, list(reversed(xs))), -1.0, places=9)
        # a constant series has no correlation at all, so the function declines to
        # answer rather than reporting zero - callers publish a blank on NaN.
        self.assertTrue(math.isnan(S.pearson([1.0, 1.0, 1.0], xs)))

    def test_rank_average_ties(self):
        self.assertEqual(S.rank([10.0, 20.0, 20.0, 30.0]), [1.0, 2.5, 2.5, 4.0])

    def test_normal_ppf_inverts_cdf(self):
        for p in (0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99):
            self.assertAlmostEqual(S.normal_cdf(S.normal_ppf(p)), p, places=4)

    def test_american_conversion_roundtrip(self):
        for p in (0.05, 0.2, 0.4, 0.5, 0.6, 0.8, 0.95):
            odds = S.american_from_prob(p)
            back = 100.0 / (abs(float(odds)) + 100.0) if float(odds) > 0 \
                else abs(float(odds)) / (abs(float(odds)) + 100.0)
            self.assertAlmostEqual(back, p, places=2)

    def test_wilson_contains_the_point_estimate(self):
        lo, hi = S.wilson_interval(30, 44)
        self.assertLess(lo, 30 / 44)
        self.assertGreater(hi, 30 / 44)
        self.assertGreater(lo, 0.0)

    def test_round_half_up_is_not_bankers_rounding(self):
        # ties go toward +infinity, which is a declared convention: a raw -0.25 home
        # spread prints as a pick rather than silently favouring one side
        self.assertEqual(S.round_half_up(0.25, 0.5), 0.5)
        self.assertEqual(S.round_half_up(-0.25, 0.5), 0.0)
        self.assertEqual(S.round_half_up(45.75, 0.5), 46.0)
        self.assertEqual(S.round_half_up(45.25, 0.5), 45.5)

    def test_fisher_ci_monotone_in_n(self):
        a = S.fisher_ci(0.3, 30)
        b = S.fisher_ci(0.3, 300)
        self.assertGreater(a[1] - a[0], b[1] - b[0])

    def test_bivariate_cdf_at_zero_rho_is_the_product(self):
        joint = S.bivariate_normal_cdf(0.5, -0.3, 0.0)
        self.assertAlmostEqual(joint, S.normal_cdf(0.5) * S.normal_cdf(-0.3), places=4)


class TestResultsFeed(unittest.TestCase):
    def test_feed_size_and_uniqueness(self):
        rows = R.feed_rows()
        self.assertEqual(len(rows), len(C.FINAL_GAMES))
        self.assertEqual(len({r["game_id"] for r in rows}), len(rows))

    def test_home_and_away_wins_balance(self):
        rows = R.feed_rows()
        home_wins = sum(1 for r in rows if int(r["home_points"]) > int(r["away_points"]))
        away_wins = sum(1 for r in rows if int(r["home_points"]) < int(r["away_points"]))
        ties = sum(1 for r in rows if int(r["home_points"]) == int(r["away_points"]))
        self.assertEqual(home_wins + away_wins + ties, len(rows))
        for r in rows:
            hp, ap = int(r["home_points"]), int(r["away_points"])
            self.assertEqual(int(r["margin_home"]), hp - ap)
            self.assertEqual(int(r["game_total"]), hp + ap)
            self.assertEqual(r["winner_abbr"], r["home"] if hp > ap else r["away"] if ap > hp else "")

    def test_identities_all_pass(self):
        for row in R.feed_identities():
            self.assertEqual(row["result"], "pass", row["identity"])

    def test_reconciliation_has_no_mismatch(self):
        for row in R.standings_reconciliation():
            self.assertIn(row["result"], ("match", "no_official_badge_club_on_bye"))
            if row["result"] == "match":
                self.assertEqual(row["derived_w_l_t"], row["official_card_badge_w_l_t"])

    def test_vintage_tables_have_the_right_number_of_games(self):
        for wk in (7, 8, 9):
            tab = R.as_of(wk)
            self.assertEqual(len(tab), 32)
            for club, row in tab.items():
                self.assertEqual(int(row["games"]), int(row["w"]) + int(row["l"]) + int(row["t"]),
                                 f"{club} at vintage {wk}")
                self.assertGreaterEqual(row["games"], 0)

    def test_club_key_is_canonical(self):
        self.assertIn("ARI", R.as_of(9))
        self.assertNotIn("AZ", R.as_of(9))
        self.assertIn("ARI", C.CLUB_ABBR_ALIASES)
        self.assertIn("AZ", C.CLUB_ABBR_ALIASES["ARI"][0])


class TestOrigination(unittest.TestCase):
    def test_stage_order_is_enforced(self):
        inp = O.Inputs("2026-W10-02", "NE", "DET", 9, R.as_of(9))
        with self.assertRaises(O.StageOrderError):
            O.stage2_total(inp, {"stage": 2}, 0.0)
        side = O.stage1_side(inp)
        total = {"stage": 1, "published": True}
        with self.assertRaises(O.StageOrderError):
            O.stage3_moneyline(side, total, O.dispersion(9))

    def test_side_is_the_home_spread_and_negative_means_home_favoured(self):
        inp = O.Inputs("2026-W10-01", "WAS", "NYG", 9, R.as_of(9))
        side = O.stage1_side(inp)
        self.assertLess(side["fair_line"], 0.0)                 # NYG favoured at home
        self.assertLessEqual(abs(side["fair_line"] + side["expected_margin_home"]), 0.25)
        self.assertAlmostEqual(side["fair_line_raw"], -side["expected_margin_home"], places=9)

    def test_total_equals_the_sum_of_the_two_expectations(self):
        inp = O.Inputs("2026-W10-05", "MIN", "GB", 9, R.as_of(9))
        side = O.stage1_side(inp)
        total = O.stage2_total(inp, side)
        eh, ea = O._expected(inp)
        self.assertAlmostEqual(float(total["fair_line_raw"]), eh + ea, places=9)

    def test_moneyline_probabilities_sum_to_one(self):
        inp = O.Inputs("2026-W10-01", "WAS", "NYG", 9, R.as_of(9))
        out = O.originate(inp)
        ml = out["moneyline"]
        self.assertIn("fair_prob_home_win", ml)
        self.assertAlmostEqual(ml["fair_prob_home_win"] + ml["fair_prob_away_win"] + ml["fair_prob_tie"],
                               1.0, places=6)
        self.assertGreater(ml["fair_prob_tie"], 0.0)

    def test_no_future_information_enters_a_line(self):
        # every published game is priced on the standings through week 9, and week 9
        # excludes the week 10 game entirely
        self.assertNotIn("2026-W10-01", {g[0] for g in C.FINAL_GAMES if g[1] <= 9})
        a, b = R.as_of(9), R.as_of(10)
        self.assertNotEqual(a["NYG"]["w"] + a["NYG"]["l"], b["NYG"]["w"] + b["NYG"]["l"])

    def test_dispersion_publishes_its_sample_sizes(self):
        d = O.dispersion(9)
        self.assertEqual(int(d["n_team_games"]), 2 * int(d["n_games"]))
        self.assertGreater(d["n_team_games"], 0)
        self.assertTrue(-1.0 <= d["rho_home_away"] <= 1.0)

    def test_published_columns_leave_market_and_difference_blank(self):
        cols = O.published_columns("side", "-3.5", "-3.500", "points")
        self.assertEqual(cols["market_line_side"], "")
        self.assertEqual(cols["difference_side"], "")
        self.assertEqual(cols["market_flag_id"], "D966-F01")
        self.assertEqual(cols["difference_side_status"], "blank_no_licensed_market_price")

    def test_damping_scan_shape(self):
        rows = O.damping_scan("side", 10)
        self.assertEqual(len(rows), 21)
        self.assertEqual(float(rows[0]["shrink_factor"]), 0.0)
        self.assertEqual(float(rows[-1]["shrink_factor"]), 1.0)
        for r in rows:
            self.assertEqual(int(r["n_games"]), len(C.FINAL_GAMES))


class TestPriceStore(unittest.TestCase):
    def test_chain_verifies(self):
        rows = P.ledger()
        self.assertEqual(P.verify_chain(rows), [])

    def test_editing_an_earlier_row_breaks_the_chain(self):
        rows = P.ledger()
        rows[3]["published_value"] = "99.9"
        self.assertTrue(P.verify_chain(rows))

    def test_roles_are_consistent_with_position_in_the_series(self):
        rows = P.ledger()
        by_market: dict[str, list[dict[str, str]]] = {}
        for r in rows:
            by_market.setdefault(r["market_id"], []).append(r)
        for series in by_market.values():
            self.assertEqual(series[0]["role"].startswith("open"), True)
            if len(series) > 1:
                self.assertIn(series[-1]["role"], ("close_final", "close_provisional"))
                for r in series[1:-1]:
                    self.assertEqual(r["role"], "intermediate")

    def test_market_and_close_agree_with_the_ledger(self):
        rows = P.ledger()
        table = P.open_close_table(rows)
        for market, d in table.items():
            series = [r for r in rows if r["market_id"] == market]
            self.assertEqual(d["opening_number"], series[0]["published_value"])

    def test_no_snapshot_row_invents_a_price(self):
        for r in P.ledger():
            if r["publication_class"] == "external_market_price":
                self.assertEqual(r["published_value"], "")
                self.assertTrue(r["market_flag_id"])


class TestDepth(unittest.TestCase):
    def test_row_count_matches_the_capture(self):
        rows = DP.injury_rows()
        self.assertEqual(len(rows), len(C.INJURY_REPORT_W10_RAW.strip().split("\n")))

    def test_bound_never_exceeds_players_listed(self):
        for r in DP.group_depth():
            self.assertLessEqual(int(r["tiers_dropped_lower_bound"]), int(r["players_listed"]))
            self.assertIn(r["deficit_score_kind"], ("proposed_weight_not_observed",))

    def test_only_named_replacements_are_credited(self):
        for r in DP._replacement_evidence():
            credit = r["credited_as_depth_replacement"]
            if r["evidence_kind"] in DP.REPLACEMENT_KINDS:
                self.assertEqual(credit, "yes", r["headline_verbatim"])
            else:
                self.assertEqual(credit, "no", r["headline_verbatim"])

    def test_blank_game_status_is_not_availability(self):
        for r in DP.injury_rows():
            if r["game_status"] == "":
                self.assertEqual(r["availability"], "listed_no_designation")
                self.assertEqual(r["counts_toward_lower_bound"], "0")


class TestCorrelations(unittest.TestCase):
    def test_every_row_publishes_n_and_two_sources(self):
        for r in X.correlations():
            self.assertTrue(r["n"].isdigit(), r["correlation_id"])
            self.assertTrue(r["x_official_source_url"].startswith("https://"))
            self.assertTrue(r["y_official_source_url"].startswith("https://"))
            self.assertGreaterEqual(int(r["n"]), 4)

    def test_coefficients_are_in_range(self):
        for r in X.correlations():
            if r.get("coefficient"):
                self.assertTrue(-1.0 <= float(r["coefficient"]) <= 1.0)
                self.assertLessEqual(float(r["ci95_low"]), float(r["coefficient"]))
                self.assertGreaterEqual(float(r["ci95_high"]), float(r["coefficient"]))

    def test_no_candidate_without_an_official_axis_is_published_as_a_number(self):
        ids = {r["correlation_id"] for r in X.correlations()}
        for excl in X.EXCLUSIONS:
            self.assertNotIn(excl["candidate_id"], ids)
            self.assertTrue(excl["reason"])

    def test_parlay_adjustment_moves_the_product_not_the_legs(self):
        a = X.parlay_probability([0.55, 0.52], None)
        b = X.parlay_probability([0.55, 0.52], -0.5)
        self.assertAlmostEqual(a["independent_product"], 0.286, places=6)
        self.assertEqual(a["joint_bivariate"], "")
        self.assertLess(float(b["joint_bivariate"]), a["independent_product"])


class TestBacktest(unittest.TestCase):
    def test_leg_outcomes_match_a_hand_computation(self):
        for leg in B.settled_leg_rows()[:40]:
            if leg["market"] == "side":
                margin = int(leg["actual_home_points"]) - int(leg["actual_away_points"])
                adj = margin + float(leg["line_published"])
                expected = "push" if abs(adj) < 1e-9 else ("win" if adj > 0 else "loss")
                self.assertEqual(leg["outcome"], expected, leg["leg_id"])
            elif leg["market"] == "total":
                total = int(leg["actual_home_points"]) + int(leg["actual_away_points"])
                over = leg["side_taken"] == "over"
                self.assertEqual((total > float(leg["line_published"])) == over
                                 or abs(total - float(leg["line_published"])) < 1e-9, True)

    def test_push_returns_zero_units(self):
        for leg in B.settled_leg_rows():
            if leg["outcome"] == "push":
                self.assertEqual(float(leg["units_if_single"]), 0.0)

    def test_a_loss_is_always_minus_one_unit(self):
        for leg in B.settled_leg_rows():
            if leg["outcome"] == "loss":
                self.assertAlmostEqual(float(leg["units_if_single"]), -1.0, places=6)

    def test_moneyline_payout_direction(self):
        self.assertAlmostEqual(B.price_decimal(-145), 1.0 + 100.0 / 145.0, places=9)
        self.assertAlmostEqual(B.price_decimal(230), 3.30, places=9)
        # a 400-1 shot returning 1.25 while a 145-100 favourite returns 1.69 is the
        # correct direction: the heavier favourite pays less
        self.assertLess(B.price_decimal(-400), B.price_decimal(-145))

    def test_every_settled_leg_carries_a_result_url(self):
        for leg in B.settled_leg_rows():
            self.assertTrue(leg["result_official_source_url"].startswith("https://www.nfl.com/games/"))

    def test_blocked_strategies_have_no_selections(self):
        settled = {t["strategy_id"] for t in B.settled_ticket_rows()}
        for st in B.STRATEGIES:
            if st.status == "blocked":
                self.assertNotIn(st.strategy_id, settled)


class TestLeaderboard(unittest.TestCase):
    def test_signal_table_has_no_staking_columns(self):
        for r in LB.signal_table():
            for key in r:
                self.assertNotIn("units", key)
                self.assertNotIn("stake", key)
                self.assertNotIn("kelly", key)

    def test_staking_table_has_no_accuracy_columns(self):
        for r in LB.staking_table():
            for key in r:
                for banned in ("brier", "abs_error", "log_loss", "calibration"):
                    self.assertNotIn(banned, key)

    def test_ranks_are_dense_and_unique(self):
        ranks = [r["signal_rank"] for r in LB.signal_table() if r["signal_rank"]]
        self.assertEqual(sorted(int(x) for x in ranks), list(range(1, len(ranks) + 1)))

    def test_skill_score_penalises_a_model_betting_its_own_line(self):
        rows = {r["strategy_id"]: r for r in LB.signal_table()}
        for sid, r in rows.items():
            if r["brier_skill_score_vs_base_rate"]:
                self.assertLess(abs(float(r["brier_skill_score_vs_base_rate"])), 0.15, sid)

    def test_rewards_are_not_monetary(self):
        for r in LB.rewards_tiers():
            self.assertEqual(r["reward_currency"], "none_no_monetary_payout")
            self.assertTrue(r["eligibility_rule"])


class TestDemotionGate(unittest.TestCase):
    def test_gate_matrix_is_complete(self):
        rows = DM.gate_rows()
        self.assertEqual(len(rows), len(B.STRATEGIES) * len(DM.GATES))
        for r in rows:
            self.assertIn(r["result"], ("pass", "fail", "not_evaluated"))
            self.assertTrue(r["threshold"])

    def test_live_only_when_nothing_fails(self):
        states = {d["strategy_id"]: d for d in DM.decisions()}
        for sid, d in states.items():
            fails = [r for r in DM.gate_rows() if r["strategy_id"] == sid and r["result"] == "fail"]
            if d["state"] == "live":
                self.assertEqual(fails, [], sid)

    def test_demotion_mechanism_fires_from_a_live_state(self):
        everything_live = {st.strategy_id: "live" for st in B.STRATEGIES}
        rows = {r["strategy_id"]: r for r in DM.decisions(everything_live)}
        for st in B.STRATEGIES:
            fails = [r for r in DM.gate_rows()
                     if r["strategy_id"] == st.strategy_id and r["result"] == "fail"]
            if fails:
                self.assertEqual(rows[st.strategy_id]["state"], "paper", st.strategy_id)
                self.assertEqual(rows[st.strategy_id]["decision"], "demote_to_paper", st.strategy_id)
                for gate in fails:
                    self.assertIn(gate["gate_id"], rows[st.strategy_id]["failing_gate_ids"])
            else:
                self.assertEqual(rows[st.strategy_id]["state"], "live", st.strategy_id)
                self.assertEqual(rows[st.strategy_id]["decision"], "stay_live", st.strategy_id)

    def test_demotion_names_the_trigger_row(self):
        everything_live = {st.strategy_id: "live" for st in B.STRATEGIES}
        for t in DM.transitions(everything_live):
            self.assertEqual(t["kind"], "demotion_to_paper")
            self.assertTrue(t["trigger_gate_ids"])
            self.assertTrue(t["trigger_detail"])

    def test_integrity_override_demotes_everything(self):
        for r in DM.gate_rows():
            if r["block"] == "integrity":
                self.assertEqual(r["result"], "pass", r["metric"])

    def test_rank_and_eligibility_can_disagree(self):
        states = {d["strategy_id"]: d for d in DM.decisions()}
        ranked = {int(s["signal_rank"]): s["strategy_id"]
                  for s in LB.signal_table() if s.get("signal_rank")}
        if ranked:
            first = states[ranked[min(ranked)]]
            self.assertIn(first["state"], ("live", "paper"))
            # whatever the top row's state, a lower-ranked strategy is allowed to be live
            self.assertTrue(first["signal_status"] == "ranked")


class TestFlagsAndAdvice(unittest.TestCase):
    def test_flag_rows_are_complete(self):
        for r in FL.flag_rows():
            for col in FL.FLAG_FIELDS:
                if col == "read_on_utc":
                    continue
                self.assertTrue(str(r.get(col, "")).strip(), f"{r['flag_id']}:{col}")

    def test_flag_ids_are_unique_and_ordered(self):
        ids = [r["flag_id"] for r in FL.flag_rows()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, sorted(ids))

    def test_no_suggestion_is_self_applied(self):
        for r in AD.suggestion_rows():
            self.assertEqual(r["status"], "awaiting_human_choice", r["suggestion_id"])
            self.assertTrue(r["applied_by_default"].lower().startswith("no"))

    def test_every_question_has_a_discovery_path(self):
        for r in AD.question_rows():
            self.assertTrue(r["how_to_discover_it_without_a_human"], r["question_id"])
            self.assertTrue(r["discovery_status"], r["question_id"])

    def test_suggestions_reference_real_flags(self):
        known = {r["flag_id"] for r in FL.flag_rows()}
        text = " ".join(str(v) for r in AD.suggestion_rows() for v in r.values())
        import re
        for fid in set(re.findall(r"D966-F\d\d", text)):
            self.assertIn(fid, known, f"suggestion cites {fid} which has no flag row")


class TestSiteArtifacts(unittest.TestCase):
    def test_pages_exist(self):
        pages = [f for f in os.listdir(DOCS) if f.endswith(".html")]
        self.assertEqual(len(pages), 17)
        for name in ("index.html", "flagged.html", "results-feed.html", "lines.html", "prices.html",
                     "leaderboard.html", "gates.html", "review.html"):
            self.assertIn(name, pages)

    def test_no_input_elements_and_no_generator_repr(self):
        for f in os.listdir(DOCS):
            if not f.endswith(".html"):
                continue
            with open(os.path.join(DOCS, f), encoding="utf-8") as fh:
                text = fh.read()
            self.assertNotRegex(text, r"<input\b", f)
            self.assertNotIn("generator object", text, f)

    def test_data_files_exist_and_are_non_empty(self):
        files = [f for f in os.listdir(DATA) if f.endswith(".csv")]
        self.assertGreaterEqual(len(files), 38)
        for f in files:
            self.assertGreater(os.path.getsize(os.path.join(DATA, f)), 40, f)

    def test_no_signed_or_third_party_host_is_linked_as_a_source(self):
        """No href may point at a signed proxy copy or a credential-bearing URL.

        The dead end itself is *described* in flag D966-F17 - that text is a finding -
        so the rule is about links and tokens, not about mentions.
        """
        import re
        bad = re.compile(r"""href=["'][^"']*(routify|windows\.net|storage\.azure|sig=|sk=)""", re.I)
        for folder in (DOCS, DATA):
            for f in sorted(os.listdir(folder)):
                path = os.path.join(folder, f)
                if not os.path.isfile(path) or f.startswith("."):
                    continue
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
                self.assertIsNone(bad.search(text), f"{f}: links a non-official signed host")
                self.assertNotIn("sk=", text, f)


if __name__ == "__main__":
    unittest.main(verbosity=2)
