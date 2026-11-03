"""Regression tests: warnings never substitute for blank unverified values."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hub_checker", ROOT / "scripts/check_hub.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class HubPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "docs", self.root / "docs")
        shutil.copytree(ROOT / "data", self.root / "data")

    def mutate(self, page, old, new):
        path = self.root / "docs/hub" / (page + ".html")
        content = path.read_text()
        self.assertIn(old, content)
        path.write_text(content.replace(old, new, 1))

    def errors(self):
        return checker.check(self.root)[0]

    def test_published_site_passes(self):
        self.assertEqual(self.errors(), [])

    def test_unverified_number_is_rejected_even_with_badge(self):
        self.mutate("lines", 'aria-label="Unverified; value withheld"></td>',
                    'aria-label="Unverified; value withheld">-4.5</td>')
        self.assertTrue(any("nonblank" in e for e in self.errors()))

    def test_zero_is_not_a_blank(self):
        self.mutate("correlations", 'aria-label="Unverified; value withheld"></td>',
                    'aria-label="Unverified; value withheld">0</td>')
        self.assertTrue(any("nonblank" in e for e in self.errors()))

    def test_nested_hidden_value_rejected(self):
        self.mutate("props", 'aria-label="Unverified; value withheld"></td>',
                    'aria-label="Unverified; value withheld"><input value="30.5"></td>')
        self.assertTrue(any("nonblank" in e for e in self.errors()))

    def test_removed_field_marker_rejected(self):
        self.mutate("lines", 'data-field="market_spread"', 'class="number"')
        self.assertTrue(any("field coverage" in e for e in self.errors()))

    def test_missing_dataset_row_rejected(self):
        self.mutate("results", 'data-record="1" data-verification="unverified"',
                    'data-record="999" data-verification="unverified"')
        self.assertTrue(any("identity/status" in e for e in self.errors()))

    def test_hidden_attribute_rejected(self):
        self.mutate("lines", 'data-field="market_spread"', 'data-field="market_spread" title="-4.5"')
        self.assertTrue(any("unsupported attributes" in e for e in self.errors()))

    def test_policy_override_rejected(self):
        path = self.root / "data/hub_publication_policy.json"
        policy = json.loads(path.read_text())
        policy["accepted_value_evidence"] = [{"claim": "trust badge"}]
        path.write_text(json.dumps(policy))
        self.assertTrue(any("fail closed" in e for e in self.errors()))

    def test_secondary_market_link_rejected(self):
        self.mutate("lines", 'href="https://www.nba.com/termsofuse"',
                    'href="https://sports.core.api.espn.com/odds"')
        self.assertTrue(any("non-primary" in e for e in self.errors()))

    def test_official_url_boundary(self):
        self.assertTrue(checker.official("https://www.nba.com/games"))
        self.assertTrue(checker.official("https://github.com/sassnarep3-star/Own6/blob/main/README.md"))
        for url in ["http://www.nba.com/games", "https://www.nba.com.evil.test/games",
                    "https://www.nba.com@evil.test/", "https://www.nba.com:444/games",
                    "https://github.com/unrelated/Own6/", "//www.nba.com/games"]:
            with self.subTest(url=url):
                self.assertFalse(checker.official(url))

    def test_broken_link_rejected(self):
        self.mutate("index", 'href="summary.html"', 'href="does-not-exist.html"')
        self.assertTrue(any("broken/escaping" in e for e in self.errors()))

    def test_page_removal_rejected(self):
        (self.root / "docs/hub/correlations.html").unlink()
        self.assertTrue(any("Missing or unexpected" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
