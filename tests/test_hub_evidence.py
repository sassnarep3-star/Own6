"""Stdlib regressions, also discoverable by pytest; no network or test fixtures."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import csv
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("hub_gate", ROOT / "scripts/check_hub.py")
gate = module_from_spec(spec)
spec.loader.exec_module(gate)


def read_csv(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def table_rows(page, table):
    parsed = gate.Page()
    parsed.feed((ROOT / "docs/hub" / page).read_text(encoding="utf-8"))
    return [r for r in parsed.rows if r["table"] == table]


class HubEvidenceTests(unittest.TestCase):
    def fixture(self, row, tid="test"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "test.html"
            page.write_text(f'<h1>Test</h1><table id="{tid}"><thead><tr><th>Value</th><th>Source</th></tr></thead>'
                            f'<tbody>{row}</tbody></table>', encoding="utf-8")
            return gate.check_page(page, root)[0]

    def test_source_role_is_not_inferred_from_https(self):
        self.assertTrue(gate.qualifies("https://www.nba.com/termsofuse", "official-reference"))
        self.assertFalse(gate.qualifies("https://www.espn.com/nba", "official-reference"))
        self.assertFalse(gate.qualifies("https://www.nba.com/termsofuse", "secondary-record"))
        for url in [
            "https://github.com/stranger/claims/blob/main/odds.csv",
            "https://github.com/sassnarep3-star/Own6-evil/blob/main/x",
            "https://github.com/sassnarep3-star/Own6/blob/main/%2e%2e/x",
        ]:
            self.assertFalse(gate.qualifies(url, "project-record"))
        self.assertTrue(gate.qualifies("https://github.com/sassnarep3-star/Own6/blob/main/README.md", "project-record"))

    def test_secondary_only_row_fails(self):
        issues = self.fixture('<tr><td>Record</td><td><a href="https://www.espn.com/nba" '
                              'data-source-kind="secondary-record">ESPN</a></td></tr>')
        self.assertTrue(any("lacks a scoped" in e for e in issues))

    def test_truly_empty_unverified_field_passes(self):
        self.assertFalse(self.fixture('<tr><td data-evidence="unverified" aria-label="blank, unverified"></td><td>'
                         '<a href="https://www.nba.com/termsofuse" data-source-kind="official-reference">Terms</a></td></tr>'))

    def test_removing_provenance_does_not_enable_publishing(self):
        issues = self.fixture('<tr><td>Legacy value</td><td>123</td></tr>', "standings")
        self.assertTrue(any("lacks required blank provenance" in e for e in issues))

    def test_width_mismatch_fails(self):
        self.assertTrue(any("cells for" in e for e in self.fixture('<tr><td>Only one cell</td></tr>')))

    def test_hub_rebuild_is_deterministic(self):
        paths = sorted((ROOT / "docs/hub").glob("*.html"))
        before = {p.name: p.read_bytes() for p in paths}
        subprocess.run([sys.executable, str(ROOT / "scripts/build_hub.py")], check=True)
        self.assertEqual({p.name: p.read_bytes() for p in paths}, before)

    def test_no_correlation_or_reward_value_promoted(self):
        corr = table_rows("correlations.html", "correlations")
        report = json.loads((ROOT / "data/empirical/report.json").read_text())
        self.assertEqual(len(corr), len(read_csv("data/correlation_findings.csv")) + len(report["correlations"]))
        for row in corr:
            self.assertTrue(all(row["cells"][i]["unverified"] for i in (2, 3, 4)))
        for row in table_rows("strategies.html", "strategies"):
            self.assertTrue(all(row["cells"][i]["unverified"] for i in (4, 5, 6)))

    def test_all_historical_flags_retained(self):
        expected = (len(read_csv("data/hub_evidence_flags.csv")) + len(read_csv("data/hub_flags.csv"))
                    + len(json.loads((ROOT / "data/flags.json").read_text())["rows"])
                    + len(read_csv("data/flagged_items.csv")) + len(read_csv("data/empirical/repo_findings.csv")))
        self.assertEqual(len(table_rows("flagged.html", "flags")), expected)

    def test_no_generic_sample_size_or_raw_correlation_qualification(self):
        text = (ROOT / "docs/hub/correlations.html").read_text()
        self.assertNotIn('class="b ok">usable', text)
        self.assertIn("Zero Pearson correlation does not prove independence", text)

    def test_complete_hub_passes_scoped_gate(self):
        issues, pages, rows = gate.check_hub(ROOT)
        self.assertFalse(issues, issues)
        self.assertEqual(pages, 12)
        self.assertGreater(rows, 300)


# Separate dynamically named test methods retain granular reporting without a
# pytest dependency. The project's dependency-free runner can import this module.
def spoof_test(url):
    def test(self):
        self.assertFalse(gate.official_reference(url), url)
    return test


for i, url in enumerate([
    "https://evilnba.com/fact", "https://nba.com.example.org/fact",
    "https://www.nba.com@evil.org/fact", "http://www.nba.com/fact",
    "//www.nba.com/fact", "https://nba.com:444/fact", "https://user@nba.com/fact",
    "https://nba.com\\@evil.org/fact", "https://nba.com/a b",
]):
    setattr(HubEvidenceTests, f"test_official_reference_rejects_spoof_{i}", spoof_test(url))


def nonempty_test(value):
    def test(self):
        issues = self.fixture(f'<tr><td data-evidence="unverified">{value}</td><td>'
                              '<a href="https://www.nba.com/termsofuse" data-source-kind="official-reference">Terms</a></td></tr>')
        self.assertTrue(any("nonblank unverified" in e for e in issues))
    return test


for i, value in enumerate(["123.4", "0", "<span>123</span>", "<img src='value.svg'>"]):
    setattr(HubEvidenceTests, f"test_nonempty_unverified_field_fails_{i}", nonempty_test(value))


def coverage_test(page, table, inputs):
    def test(self):
        rows = table_rows(page, table)
        self.assertEqual(len(rows), sum(len(read_csv(path)) for path in inputs))
        for row in rows:
            for column in gate.WITHHELD_COLUMNS[table]:
                self.assertTrue(row["cells"][column]["unverified"])
                self.assertFalse(row["cells"][column]["text"].strip())
                self.assertFalse(row["cells"][column]["markup"])
    return test


for page, table, inputs in [
    ("results.html", "results", ["data/games_results_2026-27.csv", "data/results_2026-11-02.csv"]),
    ("standings.html", "standings", ["data/standings_live_2026-11-03.csv"]),
    ("standings.html", "ratings", ["data/team_ratings_2026-27.csv"]),
    ("lines.html", "lines", ["data/market_lines_2026-11-02.csv"]),
    ("props.html", "props", ["data/player_props_2026-11-02.csv"]),
    ("forward-test.html", "forward-games", ["data/forward_test_2026-11-02.csv"]),
    ("forward-test.html", "forward-summary", ["data/forward_test_summary_2026-11-02.csv"]),
]:
    setattr(HubEvidenceTests, "test_all_records_retained_" + table.replace("-", "_"), coverage_test(page, table, inputs))


if __name__ == "__main__":
    unittest.main()
