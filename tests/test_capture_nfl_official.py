"""Tests for scripts/capture_nfl_official.py (session 79fd4958).

All HTML here is SYNTHETIC: invented club/player names, written only to exercise
the parser and the drift checks. No official NFL text is stored in this file.
"""
import csv
import hashlib
import os
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import capture_nfl_official as cap  # noqa: E402

HEADER = "<tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr>"


def _page(title="Official NFL Injury Report for Players - Week 11 of the 2026 Season | NFL.com",
          tables=8, rows_per_table=14, header=HEADER, bad_row=False, blank_game=True):
    parts = [f"<html><head><title>{title}</title></head><body>"]
    for t in range(tables):
        parts.append(f"<h2>Club {t}</h2><table>{header}")
        for r in range(rows_per_table):
            status = "" if blank_game else "Out"
            if bad_row and r == 0:
                parts.append("<tr><td>Only Three</td><td>LB</td><td>Calf</td></tr>")
                continue
            parts.append(
                f"<tr><td><a href='/p/x'>Synthetic Player {t}-{r}</a></td><td>LB</td>"
                f"<td>Calf</td><td>Did Not Participate In Practice</td><td>{status}</td></tr>")
        parts.append("</table>")
    parts.append("</body></html>")
    return "".join(parts).encode("utf-8")


class EvaluateTests(unittest.TestCase):
    def test_valid_page_passes_and_counts_rows(self):
        ev = cap.evaluate(_page(), 200)
        self.assertEqual(ev["status"], "ok", ev["failure_reason"])
        self.assertEqual(ev["week_label"], "Week 11 of the 2026 Season")
        self.assertEqual(ev["injury_tables"], 8)
        self.assertEqual(ev["player_rows"], 8 * 14)
        self.assertEqual(ev["blank_game_status_rows"], 8 * 14)

    def test_blank_game_status_is_counted_not_filled(self):
        ev = cap.evaluate(_page(blank_game=False), 200)
        self.assertEqual(ev["status"], "ok")
        self.assertEqual(ev["blank_game_status_rows"], 0)

    def test_header_drift_fails_loudly(self):
        bad = "<tr><th>Player</th><th>Pos</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr>"
        ev = cap.evaluate(_page(header=bad), 200)
        self.assertEqual(ev["status"], "fail")
        self.assertIn("header_drift_tables=8", ev["failure_reason"])
        self.assertIn("injury_tables=0<min8", ev["failure_reason"])

    def test_missing_title_marker_fails(self):
        ev = cap.evaluate(_page(title="Some other page - Week 11 of the 2026 Season"), 200)
        self.assertIn("title_missing_injury_report", ev["failure_reason"])

    def test_missing_week_label_fails(self):
        ev = cap.evaluate(_page(title="Official NFL Injury Report for Players | NFL.com"), 200)
        self.assertIn("week_label_missing", ev["failure_reason"])

    def test_row_shape_drift_fails(self):
        ev = cap.evaluate(_page(bad_row=True), 200)
        self.assertEqual(ev["status"], "fail")
        self.assertIn("row_shape_drift_rows=8", ev["failure_reason"])

    def test_too_few_player_rows_fails(self):
        ev = cap.evaluate(_page(tables=8, rows_per_table=1), 200)
        self.assertIn("player_rows=8<min100", ev["failure_reason"])

    def test_non_200_fails(self):
        ev = cap.evaluate(_page(), 503)
        self.assertIn("http_status=503", ev["failure_reason"])

    def test_empty_html_fails_without_exception(self):
        ev = cap.evaluate(b"", 200)
        self.assertEqual(ev["status"], "fail")


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raw = os.path.join(self.tmp.name, "raw")
        self.index = os.path.join(self.tmp.name, "index.csv")
        self.clock_values = iter(["2026-11-19T16:00:00Z", "2026-11-20T16:00:00Z",
                                  "2026-11-21T16:00:00Z"])

    def tearDown(self):
        self.tmp.cleanup()

    def clock(self):
        return next(self.clock_values)

    def _fetch(self, body, status=200):
        return lambda url: (status, url, body)

    def _rows(self):
        with open(self.index, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def test_success_writes_raw_hash_and_ok_row(self):
        body = _page()
        code, row = cap.capture("https://example.invalid/i", self.raw, self.index,
                                fetch_fn=self._fetch(body), clock=self.clock)
        self.assertEqual(code, 0)
        self.assertEqual(row["sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(row["changed_vs_previous"], "first")
        raw_path = os.path.join(self.raw, row["raw_file"])
        with open(raw_path, "rb") as fh:
            self.assertEqual(fh.read(), body)
        rows = self._rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "ok")

    def test_identical_bytes_are_flagged_unchanged(self):
        body = _page()
        cap.capture("u", self.raw, self.index, fetch_fn=self._fetch(body), clock=self.clock)
        code, row = cap.capture("u", self.raw, self.index, fetch_fn=self._fetch(body), clock=self.clock)
        self.assertEqual(code, 0)
        self.assertEqual(row["changed_vs_previous"], "no")

    def test_changed_bytes_are_flagged_changed(self):
        cap.capture("u", self.raw, self.index, fetch_fn=self._fetch(_page()), clock=self.clock)
        code, row = cap.capture("u", self.raw, self.index,
                                fetch_fn=self._fetch(_page(blank_game=False)), clock=self.clock)
        self.assertEqual(code, 0)
        self.assertEqual(row["changed_vs_previous"], "yes")

    def test_index_is_append_only(self):
        cap.capture("u", self.raw, self.index, fetch_fn=self._fetch(_page()), clock=self.clock)
        with open(self.index, "rb") as fh:
            before = fh.read()
        cap.capture("u", self.raw, self.index, fetch_fn=self._fetch(_page()), clock=self.clock)
        with open(self.index, "rb") as fh:
            after = fh.read()
        self.assertTrue(after.startswith(before))
        self.assertEqual(len(self._rows()), 2)

    def test_drift_writes_failure_row_and_exit_1(self):
        code, row = cap.capture("u", self.raw, self.index,
                                fetch_fn=self._fetch(_page(header="<tr><th>Name</th></tr>")),
                                clock=self.clock)
        self.assertEqual(code, 1)
        self.assertEqual(row["status"], "fail")
        self.assertEqual(self._rows()[-1]["status"], "fail")

    def test_fetch_exception_is_recorded_not_swallowed(self):
        def boom(url):
            raise RuntimeError("network down")
        code, row = cap.capture("u", self.raw, self.index, fetch_fn=boom, clock=self.clock)
        self.assertEqual(code, 1)
        self.assertEqual(row["failure_reason"], "fetch_error:RuntimeError")
        self.assertEqual(self._rows()[-1]["sha256"], "")

    def test_empty_body_is_a_failure(self):
        code, row = cap.capture("u", self.raw, self.index, fetch_fn=self._fetch(b"", 403),
                                clock=self.clock)
        self.assertEqual(code, 1)
        self.assertIn("empty_body", row["failure_reason"])


if __name__ == "__main__":
    unittest.main()
