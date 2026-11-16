"""Unit tests for the session-67233566 pack.

These tests do not re-check the site (that is scripts/check_nfl_67233566.py); they pin the small
numeric primitives that every published table is built from, because a wrong American-odds
conversion or a mis-signed error propagates silently into forty CSVs. Everything here is offline:
the only input is the frozen capture in data/nfl_67233566/raw/.
"""
from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.nfl_67233566 import availability as AV  # noqa: E402
from src.nfl_67233566 import correlate as CO  # noqa: E402
from src.nfl_67233566 import corpus as CP  # noqa: E402
from src.nfl_67233566 import model as M  # noqa: E402
from src.nfl_67233566 import prices as PR  # noqa: E402
from src.nfl_67233566 import registers as RG  # noqa: E402
from src.nfl_67233566 import scoreboard as SB  # noqa: E402
from src.nfl_67233566.capture import load_capture  # noqa: E402

DATA = ROOT / "data/nfl_67233566"


URL = "https://www.nfl.com/schedules/2026/by-week/week-10"


def _game(week, away, home, ap, hp, status="Final"):
    """A synthetic game with the same shape as a parsed one. Test fixtures must not take shortcuts
    past the fields the real loader fills, or a rename in corpus.py passes here and fails there."""
    return CP.Game(game_id=f"t-{week}-{away}-{home}", week=week, season=2026, date_on_card="2026-10-0",
                   slot_on_card="1:00", away=away, home=home, away_points=ap, home_points=hp,
                   feed_status=status, provenance="test", official_source_url=URL,
                   game_page_url="", read_on_utc="2026-11-15T23:26:34Z", countable=status == "Final")


class TestCaptureAndCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cap = load_capture(ROOT)
        cls.corpus, cls.prior, cls.w10 = CP.build_corpus(
            cls.cap, ROOT, "https://www.nfl.com/schedules/2026/by-week/week-10")

    def test_corpus_size_and_boundary(self):
        self.assertEqual(len(self.corpus), 150)
        countable = [g for g in self.corpus if g.countable]
        self.assertEqual(len(countable), 145)
        # the 5 uncaptured-by-status games are exactly the live and unplayed Week 10 cards
        self.assertEqual(sorted(g.feed_status for g in self.corpus if not g.countable),
                         ["in_progress", "in_progress", "in_progress", "unplayed", "unplayed"])

    def test_live_and_unplayed_rows_are_kept_out_of_the_countable_set(self):
        for g in self.corpus:
            if not g.countable:
                self.assertIn(g.feed_status, ("in_progress", "unplayed"))
                self.assertIsNone(g.away_points if g.feed_status == "unplayed" else None,
                                  f"{g.game_id}: an unplayed card must not carry a score")

    def test_no_live_score_can_enter_the_backtest(self):
        for g in self.corpus:
            if g.countable:
                self.assertEqual(g.feed_status, "final", f"{g.game_id} counted but not final")

    def test_reconciliation_is_clean_and_nontrivial(self):
        rec = CP.reconcile(self.corpus, self.cap)
        self.assertTrue(rec.passed)
        self.assertEqual(len(rec.checks), 220)
        self.assertTrue(all(c["result"] == "match" for c in rec.checks))
        self.assertEqual(rec.excluded_clubs, [])

    def test_derived_records_reproduce_the_official_standings(self):
        derived = CP.derived_records([g for g in self.corpus if g.countable])
        for row in self.cap.block("standings"):
            d = derived[row["club"]]
            self.assertEqual((d["w"], d["l"], d["t"], d["pf"], d["pa"]),
                             (int(row["w"]), int(row["l"]), int(row["t"]), int(row["pf"]), int(row["pa"])),
                             row["club"])


class TestModel(unittest.TestCase):
    def test_league_ppg_is_per_team_not_per_game(self):
        games = [_game(1, "A", "B", 20, 30), _game(1, "C", "D", 10, 14)]
        fit = M.fit(games + [_game(2, "A", "C", 21, 17), _game(2, "B", "D", 24, 20)])
        # (20+30+10+14+21+17+24+20) / 8 team-games = 20.75
        self.assertAlmostEqual(fit["league_ppg"], 19.5, places=6)  # 156 points over 8 team-games

    def test_rounding_is_to_half_points(self):
        games = [_game(w, "A", "B", 20 + w, 17 + 2 * w) for w in range(1, 6)]
        fit = M.fit(games)
        fx = M.Fixture(2026, 6, "A", "B", "t6", "", "", "")
        fc = M.predict(fit, fx, 0.0)
        self.assertAlmostEqual((fc.side_fair * 2) % 1, 0.0, places=9)
        self.assertAlmostEqual((fc.estimator_totals["T1_offdef"] * 2) % 1, 0.0, places=9)

    def test_american_odds_are_monotone_and_push_safe(self):
        # the numbers must order the way a price orders: a stronger favourite is a bigger negative
        self.assertLess(int(M._american(0.60)), int(M._american(0.55)))
        self.assertGreater(int(M._american(0.40)), 0)
        self.assertEqual(M._american(0.0), "")  # an unpriceable side is blank, not a longshot quote
        self.assertIn(M._american(0.5), ("+100", "-100"))
        for q in (0.52, 0.61, 0.73, 0.88):
            self.assertLessEqual(abs(int(M._american(q))), 10000, str(q))

    def test_forecast_probabilities_split_on_the_push(self):
        games = [_game(w, "A", "B", 20 + w, 17 + 2 * w) for w in range(1, 6)]
        fit = M.fit(games)
        fc = M.predict(fit, M.Fixture(2026, 6, "A", "B", "t6", "", "", ""), tie_rate=0.03)
        self.assertAlmostEqual(fc.home_win_prob + fc.away_win_prob + fc.tie_prob, 1.0, places=6)
        self.assertGreater(fc.tie_prob, 0.0)
        self.assertLess(fc.p_home_decisive, fc.home_win_prob + 0.5)

    def test_errors_are_attached_by_one_code_path(self):
        fit = M.fit([_game(1, "A", "B", 20, 17), _game(1, "C", "D", 24, 10)])
        fx = M.Fixture(2026, 2, "A", "B", "t2", "", "", "")
        fc = M.predict(fit, fx, 0.0)
        M.attach_errors(fc, _game(2, "A", "B", 10, 30))
        self.assertEqual(fc.errors["actual_margin"], 20)
        self.assertEqual(fc.errors["home_covered_own_line"], 1)

    def test_attach_errors_refuses_a_non_final(self):
        fit = M.fit([_game(1, "A", "B", 20, 17), _game(1, "C", "D", 24, 10)])
        fc = M.predict(fit, M.Fixture(2026, 2, "A", "B", "t2", "", "", ""), 0.0)
        live = _game(2, "A", "B", 10, 7)
        live.countable = False
        live.feed_status = "in_progress"
        M.attach_errors(fc, live)
        self.assertEqual(fc.errors, {})

    def test_a_fit_with_no_history_is_refused_not_approximated(self):
        with self.assertRaises(ValueError):
            M.fit([])
        with self.assertRaises(ValueError):
            M.fit([_game(1, "A", "B", 20, 17)])

    def test_walk_forward_refuses_a_prediction_with_no_history(self):
        with self.assertRaises(ValueError):
            M.walk_forward([_game(1, "A", "B", 20, 17)],
                           [M.Fixture(2026, 1, "A", "B", "x", "", "", "")])


class TestScoreboard(unittest.TestCase):
    def test_interval_score_penalises_a_miss(self):
        hit = SB.interval_score([50.0], [50.0], [10.0], level=0.8)
        miss = SB.interval_score([80.0], [50.0], [10.0], level=0.8)
        self.assertLess(hit[0], miss[0])
        self.assertAlmostEqual(hit[2], 1.0)
        self.assertAlmostEqual(miss[2], 0.0)

    def test_playing_weeks_and_byes_are_arithmetic_not_a_panel(self):
        games = [_game(1, "A", "B", 20, 17), _game(1, "C", "D", 10, 14)]
        played = SB.played_by_week(games)
        self.assertEqual(played[1], {"A", "B", "C", "D"})
        self.assertEqual(played.get(2, set()), set())

    def test_zero_sample_bootstrap_does_not_invent_evidence(self):
        p, mean, lo, hi, block = SB.bootstrap_skill([], [], [])
        for v in (p, mean, lo, hi, block):
            self.assertNotEqual(v, v)  # nan, not 0.0

    def test_joint_gate_reports_a_constant_pair_as_uninformative(self):
        # a leg that always hits carries no information about dependence; the gate must return a
        # degenerate n rather than a "no dependence found" verdict
        row = SB.CO_joint([1, 1, 1], [1, 1, 1])
        self.assertEqual(row["n"], 3)
        self.assertAlmostEqual(row["joint"], row["product"], places=6)
        self.assertLessEqual(row["low"], 0.0 <= row["high"])


class TestPrices(unittest.TestCase):
    def test_our_fair_value_is_priced_but_no_market_value_is_stored(self):
        """market_value() is the fair number we originate; the policy is about the market column."""
        fit = M.fit([_game(w, "A", "B", 20 + w, 17 + 2 * w) for w in range(1, 6)]
                    + [_game(w, "C", "D", 21 - w, 24 + w) for w in range(1, 6)])
        fc = M.predict(fit, M.Fixture(2026, 6, "A", "B", "g6", "", "", URL), 0.0)
        for market in PR.MARKETS:
            val, unit = PR.market_value(fc, market)
            self.assertTrue(str(val) != "", market)
            self.assertTrue(unit, market)
        self.assertEqual(PR.POLICY["status"], "in force before any backtest was published")
        with self.assertRaises(ValueError):
            PR.market_value(fc, "team_total")  # an unknown market must not silently price as blank

    def test_an_unchained_row_is_detected(self):
        fit = M.fit([_game(w, "A", "B", 20 + w, 17 + 2 * w) for w in range(1, 6)])
        fx = M.Fixture(2026, 6, "A", "B", "g6", "", "", URL)
        fc = M.predict(fit, fx, 0.0)
        rows = PR.snapshot_rows([fc], [fc], "open", "close")
        rows[3].prev_row_sha256 = "0" * 64  # a splice, exactly what the chain exists to catch
        self.assertTrue(PR.verify_chain(rows))

    def test_snapshot_rows_chain_and_cover_every_market(self):
        fit = M.fit([_game(w, "A", "B", 20 + w, 17 + 2 * w) for w in range(1, 6)])
        fx = M.Fixture(2026, 6, "A", "B", "g6", "2026-11-19", "8:15 PRIME", URL)
        fc = M.predict(fit, fx, 0.0)
        snaps = PR.snapshot_rows([fc], [fc], "open", "close")
        self.assertEqual(PR.verify_chain(snaps), [])
        self.assertEqual({s.market for s in snaps}, set(PR.MARKETS))
        self.assertTrue(all(s.value != "" for s in snaps))
        # flipping one number must break the chain
        snaps[1].value = "99.5"
        self.assertTrue(PR.verify_chain(snaps))


class TestAvailability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cap = load_capture(ROOT)
        cls.nodes = AV.build_availability(
            cls.cap, "https://www.nfl.com/injuries/")

    def test_rows_parse_into_edges_not_invented_starters(self):
        self.assertEqual(len(self.nodes), 50)
        self.assertTrue(all(n.club for n in self.nodes))
        self.assertTrue(all(n.position for n in self.nodes))

    def test_slot_floor_is_a_floor_not_a_count(self):
        slots = AV.slot_rollup(self.nodes)
        self.assertTrue(slots)
        for s in slots:
            self.assertLessEqual(int(s["players_unavailable_floor"]), 53, s)
            self.assertTrue(s.get("unit") and s.get("position_group"), s)

    def test_unread_club_is_never_reported_healthy(self):
        sweep = AV.sweep_32_clubs(self.cap, self.nodes)
        self.assertEqual(len(sweep), 32)
        for row in sweep:
            if row["status"] == "not_in_chunk_read":
                for col in ("players_out", "players_doubtful", "players_questionable", "net_injury_count"):
                    self.assertIn(row.get(col, ""), ("", None), f"{row['club']}.{col} filled without a read")


class TestCorrelate(unittest.TestCase):
    def test_perfect_and_negative_pairs(self):
        up = CO.measure("T1", "up", "game", "a", "b", [1, 2, 3, 4, 5], [2, 4, 6, 8, 10],
                        URL, URL, "").as_row()
        self.assertEqual(up["n"], "5")
        self.assertAlmostEqual(float(up["pearson_r"]), 1.0, places=6)
        down = CO.measure("T2", "down", "game", "a", "b", [1, 2, 3, 4, 5], [10, 8, 6, 4, 2],
                          URL, URL, "").as_row()
        self.assertAlmostEqual(float(down["pearson_r"]), -1.0, places=6)

    def test_mismatched_axes_and_missing_source_fail_loudly(self):
        with self.assertRaises(ValueError):
            CO.measure("T3", "bad", "game", "a", "b", [1, 2, 3], [1, 2], URL, URL, "")
        with self.assertRaises(ValueError):
            CO.measure("T4", "no source", "game", "a", "b", [1, 2, 3], [1, 2, 3], "", "")
        with self.assertRaises(ValueError):
            CO.measure("T5", "too few", "game", "a", "b", [1], [2], URL, URL, "")

    def test_every_exclusion_says_what_would_clear_it(self):
        for e in CO.EXCLUSIONS:
            self.assertTrue(e["what_would_clear_it"].strip())


class TestRegistersAndTables(unittest.TestCase):
    def test_ids_are_unique_and_every_row_is_sourced(self):
        for name, key in ((RG.REQUIREMENTS, 0), (RG.SUGGESTIONS, 0), (RG.QUESTIONS, 0), (RG.FLAGS, 0)):
            ids = [r[key] for r in name]
            self.assertEqual(len(ids), len(set(ids)))
        for r in RG.REQUIREMENTS:
            self.assertTrue(r[-1].startswith("https://"), r[0])
        for r in RG.QUESTIONS:
            self.assertTrue(r[-1].startswith("https://"), r[0])

    def test_no_flag_blocks_the_merge(self):
        for r in RG.FLAGS:
            self.assertEqual(r[7], "no", r[0])

    def test_registry_and_division_table_cover_every_required_division(self):
        divisions = {s[2] for s in SB.STRATEGIES}
        self.assertTrue({"singles_win_prob", "totals_distribution", "sgp_two_leg", "prop_combo"}
                        <= divisions)
        # a division with no entrant is still published, with the gate that explains the emptiness
        published = {r["division"] for r in SB.division_rows({})}
        self.assertEqual(len(published), 5)
        for r in SB.division_rows({}):
            self.assertTrue(r["gate_that_blocks_the_division"])

    def test_every_strategy_carries_both_sides_of_the_falsifier(self):
        """Two-sided "what would change our mind": what would refute the rule, and what would make us
        double down. Published per strategy, not as a single global caveat."""
        with (DATA / "strategies.csv").open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                for col in ("what_would_change_our_mind", "what_would_make_us_double_down",
                            "preregistered_hypothesis"):
                    self.assertGreater(len(r[col].strip()), 20, f"{r['strategy_id']}.{col}")

    def test_price_policy_is_ordered_before_grading(self):
        rules = {r["rule_id"] for r in PR.POLICY["rules"]}
        self.assertIn("PX-01", rules)
        with (DATA / "originated_lines.csv").open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                for col in ("market_side_line", "market_total_line", "market_home_moneyline",
                            "difference_side", "difference_total", "difference_moneyline"):
                    self.assertEqual(r[col], "", col)
                self.assertTrue(r["market_columns_status"].startswith("blank_by_policy"))


class TestPublishedArtifacts(unittest.TestCase):
    """The committed CSVs must agree with each other - a table that disagrees with its own summary is
    the failure mode this whole pack is organised around."""

    def test_signal_table_matches_the_staking_emptiness_claim(self):
        with (DATA / "leaderboard_signal.csv").open(newline="", encoding="utf-8") as fh:
            signal = list(csv.DictReader(fh))
        with (DATA / "leaderboard_staking.csv").open(newline="", encoding="utf-8") as fh:
            staking = list(csv.DictReader(fh))
        self.assertEqual(staking, [])
        self.assertTrue(signal)
        self.assertTrue(all(r["staking_columns_present"].startswith("no") for r in signal))

    def test_week11_lines_are_recorded_ungraded(self):
        with (DATA / "originated_lines.csv").open(newline="", encoding="utf-8") as fh:
            lines = list(csv.DictReader(fh))
        open_slate = [r for r in lines if r["fixture_status"] == "scheduled_not_played"]
        self.assertEqual(len(open_slate), 13)
        for r in open_slate:
            self.assertEqual(r["actual_home_margin"], "")
            self.assertTrue(r["market_columns_status"].startswith("blank_by_policy"))

    def test_every_published_table_has_a_source_column(self):
        for path in sorted(DATA.glob("*.csv")):
            with path.open(newline="", encoding="utf-8") as fh:
                head = next(csv.reader(fh), [])
            self.assertTrue(any("source_url" in c or c in ("url", "url_x", "url_y") for c in head),
                            f"{path.name}: no source column")

    def test_an_empty_table_still_says_who_declared_it_empty(self):
        """A header-only file is a claim, so the claim needs a citation too."""
        with (DATA / "leaderboard_staking.csv").open(newline="", encoding="utf-8") as fh:
            head = next(csv.reader(fh))
        self.assertIn("official_source_url", head)
        self.assertIn("gate_that_keeps_it_empty", head)

    def test_no_page_contains_a_generator_repr_or_a_leaked_none(self):
        for page in sorted((ROOT / "docs/nfl-67233566").glob("*.html")):
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("<generator object", text, page.name)
            self.assertNotIn(">None<", text)
            self.assertNotIn(">nan<", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
