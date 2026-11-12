from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_nfl", ROOT / "scripts" / "check_nfl.py")
assert SPEC and SPEC.loader
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class NFLResearchTests(unittest.TestCase):
    def setUp(self) -> None:
        CHECK.ERRORS.clear()

    def test_all_sources_are_official_https_and_rows_resolve(self) -> None:
        sources = CHECK.check_sources()
        count = CHECK.check_data(sources)
        self.assertGreater(count, 40)
        self.assertFalse(CHECK.ERRORS, "\n".join(CHECK.ERRORS))

    def test_all_rendered_table_rows_have_official_source_links(self) -> None:
        sources = CHECK.check_sources()
        rows, local_links = CHECK.check_site(sources)
        self.assertGreater(rows, 90)
        self.assertGreater(local_links, 20)
        self.assertFalse(CHECK.ERRORS, "\n".join(CHECK.ERRORS))

    def test_empirical_values_and_injury_live_values_remain_blank(self) -> None:
        sources = CHECK.check_sources()
        CHECK.check_data(sources)
        from csv import DictReader
        with (ROOT / "data/nfl/correlations.csv").open(newline="", encoding="utf-8") as f:
            self.assertTrue(all(not r["reported value"].strip() for r in DictReader(f)))
        with (ROOT / "data/nfl/leaderboard.csv").open(newline="", encoding="utf-8") as f:
            rows = list(DictReader(f))
        self.assertTrue(rows)
        self.assertTrue(all(r["qualification"] == "not eligible" for r in rows))
        self.assertTrue(all(not r["rank"].strip() and not r["score"].strip() for r in rows))
        with (ROOT / "data/nfl/injury_fields.csv").open(newline="", encoding="utf-8") as f:
            self.assertTrue(all(not r["live value"].strip() for r in DictReader(f)))

    def test_candidate_registry_covers_required_bet_types(self) -> None:
        from csv import DictReader
        with (ROOT / "data/nfl/strategies.csv").open(newline="", encoding="utf-8") as f:
            rows = list(DictReader(f))
        bet_types = {row["bet_type"] for row in rows}
        self.assertTrue({"single", "player prop", "same-game parlay", "cross-game parlay"}.issubset(bet_types))
        self.assertTrue(all(not row["performance result"].strip() for row in rows))


if __name__ == "__main__":
    unittest.main()
