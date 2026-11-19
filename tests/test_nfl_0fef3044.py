"""Stdlib unit tests for the 0fef3044 injury-capture parser and drift alarm (no network)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_nfl_0fef3044 as b  # noqa: E402

GAME = "GAME|Sun Nov 22|1:00 PM ET|CBS|AZ|Cardinals|3-7|KC|Chiefs|7-2\n"


def block(club_rows):
    return GAME + "TEAM|AZ|Cardinals\n" + club_rows


class ParserTests(unittest.TestCase):
    def test_parses_blank_cells_without_filling(self):
        p = b.parse(block("AZ|Budda Baker|S||Did Not Participate In Practice|\n"))
        r = p["rows"][0]
        self.assertEqual(r["injury"], "")
        self.assertEqual(r["game_status"], "")
        self.assertEqual(r["practice_status"], "Did Not Participate In Practice")

    def test_designation_is_kept_verbatim(self):
        p = b.parse(block("AZ|Max Melton|CB|Hamstring|Limited Participation in Practice|Questionable\n"))
        self.assertEqual(p["rows"][0]["game_status"], "Questionable")

    def test_row_outside_its_team_block_is_rejected(self):
        with self.assertRaises(b.ParseError):
            b.parse(block("KC|Trey Smith|G||Did Not Participate In Practice|\n"))

    def test_wrong_field_count_is_rejected(self):
        with self.assertRaises(b.ParseError):
            b.parse(block("AZ|Budda Baker|S|Did Not Participate In Practice\n"))

    def test_team_not_in_game_is_rejected(self):
        with self.assertRaises(b.ParseError):
            b.parse(GAME + "TEAM|DEN|Broncos\n")

    def test_clean_club_line_is_kept_as_status_not_player(self):
        p = b.parse(GAME + "TEAM|AZ|Cardinals\nAZ|NO INJURIES REPORTED\n")
        self.assertEqual(p["rows"], [])
        self.assertEqual(p["club_status"][0]["status"], "No Injuries Reported")


class DriftAlarmTests(unittest.TestCase):
    def test_missing_game_header_fails_validation(self):
        p = b.parse(open(b.RAW, encoding="utf-8").read())
        p["games"] = p["games"][:-1]
        self.assertTrue(any("game headers" in x for x in b.validate(p)))

    def test_unexpected_game_status_fails_validation(self):
        p = b.parse(open(b.RAW, encoding="utf-8").read())
        p["rows"][0]["game_status"] = "Probable"
        self.assertTrue(any("unexpected game status" in x for x in b.validate(p)))

    def test_blank_club_or_player_fails_validation(self):
        p = b.parse(open(b.RAW, encoding="utf-8").read())
        p["rows"][0]["practice_status"] = ""
        self.assertTrue(any("practice_status" in x for x in b.validate(p)))

    def test_official_capture_passes_validation(self):
        p = b.parse(open(b.RAW, encoding="utf-8").read())
        self.assertEqual(b.validate(p), [])


if __name__ == "__main__":
    unittest.main()
