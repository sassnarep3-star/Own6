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
spec = spec_from_file_location("hub_gate", ROOT / "tools/hub_reference_gate.py")
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

    def test_width_mismatch_fails(self):
        self.assertTrue(any("cells for" in e for e in self.fixture('<tr><td>Only one cell</td></tr>')))

    def test_github_dot_segments_are_rejected(self):
        self.assertFalse(gate.project_record("https://github.com/sassnarep3-star/Own6/blob/main/../secret"))

    def test_explicit_source_role_must_match_host(self):
        issues = self.fixture('<tr><td>Record</td><td><a href="https://www.espn.com/nba" '
                              'data-source-kind="official-reference">Official</a></td></tr>')
        self.assertTrue(any("source role" in e for e in issues))

    def test_external_links_must_use_https_even_when_not_primary(self):
        issues = self.fixture('<tr><td>Record</td><td><a href="http://www.espn.com/nba">Archive</a>'
                              '<a href="https://www.nba.com/termsofuse">Terms</a></td></tr>')
        self.assertTrue(any("safe HTTPS" in e for e in issues))

    def test_pinned_method_sources_not_arbitrary_github(self):
        self.assertTrue(all(gate.official_reference(url) for url in gate.METHOD_REFERENCES))
        self.assertFalse(gate.official_reference("https://github.com/scipy/scipy/blob/main/unknown.csv"))

    def test_unlabelled_primary_reference_is_not_value_verification(self):
        self.assertTrue(gate.qualifies("https://www.nba.com/termsofuse", None))
        self.assertFalse(gate.qualifies("https://www.espn.com/nba", None))

    def test_missing_project_blob_rejected(self):
        issues = self.fixture('<tr><td>Record</td><td><a href="https://github.com/sassnarep3-star/Own6/blob/main/missing.csv">Record</a></td></tr>')
        self.assertTrue(any("missing project source file" in e for e in issues))

    def test_owner_blank_attribute_supported(self):
        self.assertFalse(self.fixture('<tr><td data-field="price" data-state="unverified"></td><td>'
                         '<a href="https://www.nba.com/termsofuse">Terms</a></td></tr>'))
        issues = self.fixture('<tr><td data-field="price" data-state="unverified">123</td><td>'
                              '<a href="https://www.nba.com/termsofuse">Terms</a></td></tr>')
        self.assertTrue(any("nonblank unverified" in e for e in issues))


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


if __name__ == "__main__":
    unittest.main()
