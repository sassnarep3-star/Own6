"""Unit tests for the nfl_s11 pack (stdlib unittest; pytest is not installed in this sandbox)."""
import csv
import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_nfl_s11 as b  # noqa: E402
import check_nfl_s11 as c  # noqa: E402


class TranscriptionTests(unittest.TestCase):
    def test_pinned_counts(self):
        rows = b.read_transcription()
        self.assertEqual(len(rows), 347)
        self.assertEqual(len({r["game_no"] for r in rows}), 14)
        self.assertEqual(len({r["club"] for r in rows}), 28)

    def test_blank_status_stays_blank(self):
        rows = b.read_transcription()
        dup = [r for r in rows if r["player"] == "John Bates"][0]
        self.assertEqual(dup["game_status"], "")  # printed no game status; not filled

    def test_bad_field_count_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".psv", delete=False, encoding="utf-8") as fh:
            fh.write("|".join(b.PSV_FIELDS) + "\n1|x|ARI\n")
            name = fh.name
        try:
            with self.assertRaises(ValueError):
                b.read_transcription(name)
        finally:
            os.unlink(name)

    def test_bad_header_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".psv", delete=False, encoding="utf-8") as fh:
            fh.write("a|b\n")
            name = fh.name
        try:
            with self.assertRaises(ValueError):
                b.read_transcription(name)
        finally:
            os.unlink(name)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.trans = b.read_transcription()
        self.issues = b.reconcile(self.trans, b.read_d966())
        self.gaps = b.roster_gap_309921(self.trans, b.read_309921())

    def test_fourteen_players_twentyeight_fields(self):
        fields = [x for x in self.issues if x["kind"] == "field_mismatch"]
        self.assertEqual(len(fields), 28)
        self.assertEqual(len({(x["club"], x["player"]) for x in fields}), 14)

    def test_arden_key_page_values(self):
        key = [x for x in self.issues if x["player"] == "Arden Key"]
        self.assertEqual({x["field"] for x in key}, {"injuries", "game_status"})
        for x in key:
            self.assertEqual(x["page_value"], "")  # live page shows nothing for Key on these fields

    def test_cin_lawrence_gap_is_309921cc(self):
        names = [g for g in self.gaps if g["club"] == "CIN"]
        self.assertTrue(any(g["player"] == "Dexter Lawrence" for g in names))

    def test_roster_gaps_all_missing_in_309921cc(self):
        self.assertEqual(len(self.gaps), 21)
        self.assertTrue(all(g["kind"] == "missing_in_309921cc" for g in self.gaps))

    def test_club_code_mapping(self):
        self.assertEqual(b.club_norm("LA"), "LAR")
        self.assertEqual(b.club_norm("AZ"), "ARI")
        self.assertEqual(b.club_norm("KC"), "KC")


class VenueTests(unittest.TestCase):
    def test_thirteen_unique_venues_with_nfl_links(self):
        rows = b.read_csv(b.VENUES)
        self.assertEqual(len(rows), 13)
        self.assertEqual(len({r["game_id"] for r in rows}), 13)
        for r in rows:
            self.assertTrue(r["venue_source_url"].startswith("https://www.nfl.com/games/"))
            self.assertTrue(r["venue_stadium"].strip())


class CheckerTests(unittest.TestCase):
    def test_checker_passes_on_committed_state(self):
        errors = []
        trans = c.check_injuries(errors)
        c.check_reconciliation(errors, trans)
        c.check_venues(errors)
        c.check_flags_sources(errors)
        c.check_html(errors)
        self.assertEqual(errors, [])

    def test_no_input_controls_in_pages(self):
        for name in os.listdir(b.DOCS):
            if name.endswith(".html"):
                with open(os.path.join(b.DOCS, name), encoding="utf-8") as fh:
                    text = fh.read().lower()
                self.assertNotIn("<input", text, name)

    def test_every_injury_row_has_one_link(self):
        with open(os.path.join(b.DOCS, "injuries-w10.html"), encoding="utf-8") as fh:
            text = fh.read()
        tbody = text.split("<tbody>")[1].split("</tbody>")[0]
        self.assertEqual(tbody.count("<tr>"), 347)
        self.assertEqual(tbody.count('href="https://www.nfl.com/injuries/"'), 347)

    def test_flag_register_has_fourteen_rows(self):
        with open(b.FLAGGED, encoding="utf-8", newline="") as fh:
            self.assertEqual(len(list(csv.DictReader(fh))), 14)


if __name__ == "__main__":
    unittest.main()
