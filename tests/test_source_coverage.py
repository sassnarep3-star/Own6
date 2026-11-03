"""Structural provenance regressions: official-link presence never certifies values."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/source_coverage.py'
spec = importlib.util.spec_from_file_location('source_coverage', SCRIPT)
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)


class CoverageTests(unittest.TestCase):
    def parse(self, text):
        parser = coverage.Tables()
        parser.feed(text)
        parser.close()
        return sorted(parser.rows, key=lambda r: (r['table'], r['row']))

    def inspect(self, text):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / 'docs' / 'a.html'
            p.parent.mkdir()
            p.write_text(text)
            return coverage.inspect_page(p, root)

    def test_table_without_tbody_single_quoted_unquoted_links(self):
        page, rows = self.inspect("<table><tr><th>Header</th></tr><tr><td><a href='https://www.nba.com/stats'>x</a></td></tr><tr><td><a href=https://www.nist.gov/>x</a></td></tr></table>")
        self.assertEqual(page['data_rows'], 2)
        self.assertEqual([r['row'] for r in rows], [2, 3])
        self.assertTrue(all(r['coverage_status'] == 'official_reference_present' for r in rows))

    def test_every_value_remains_blank_even_when_official_link_exists(self):
        _, rows = self.inspect('<table><tr><td>made up ROI 999%</td><td><a href="https://nba.com">NBA</a></td></tr></table>')
        self.assertEqual(rows[0]['coverage_status'], 'official_reference_present')
        self.assertEqual(rows[0]['verified_value'], '')
        self.assertEqual(rows[0]['value_verification'], 'not_independently_verified_in_this_audit')

    def test_https_domain_boundaries_and_credentials(self):
        for url in ('https://nba.com.evil.test/', 'https://notnba.com/', 'https://nba.com@evil.test/', 'https://evil@nba.com/', 'http://nba.com', 'javascript:alert(1)', '//nba.com'):
            self.assertNotEqual(coverage.reference_kind(url), 'official', url)
        self.assertEqual(coverage.reference_kind('https://WWW.NBA.COM/stats'), 'official')
        self.assertEqual(coverage.reference_kind('https://docs.scipy.org/doc/'), 'official')
        self.assertEqual(coverage.reference_kind('https://www.espn.com/nba'), 'other')

    def test_arbitrary_github_repository_not_own6_evidence(self):
        self.assertEqual(coverage.reference_kind('https://github.com/sassnarep3-star/Own6/blob/main/README.md'), 'repository')
        self.assertEqual(coverage.reference_kind('https://github.com/sassnarep3-star/Own6-evil/a'), 'other')
        self.assertEqual(coverage.reference_kind('https://github.com/stranger/other'), 'other')
        self.assertEqual(coverage.reference_kind('https://api.github.com/repos/sassnarep3-star/Own6/pages'), 'repository')
        self.assertEqual(coverage.reference_kind('https://github.com'), 'other')

    def test_repository_only_and_secondary_only_and_missing(self):
        _, rows = self.inspect('<table><tr><td><a href="https://github.com/sassnarep3-star/Own6/">repo</a></td></tr><tr><td><a href="https://www.espn.com/">ESPN</a></td></tr><tr><td>https://nba.com</td></tr></table>')
        self.assertEqual([r['coverage_status'] for r in rows], list(coverage.STATUSES[1:]))

    def test_child_source_not_credited_to_parent(self):
        rows = self.parse('<table><tr><td>Parent<table><tr><td><a href="https://nba.com">child</a></td></tr></table></td></tr></table>')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['links'], [])
        self.assertEqual(rows[1]['links'], ['https://nba.com'])

    def test_optional_end_tags_and_eof(self):
        rows = self.parse('<table><tr><th>Head<tr><td>a<td>b<tr><td>c')
        self.assertEqual([r['cells'] for r in rows], [2, 1])

    def test_scripts_templates_and_styles_not_audited_as_visible_rows(self):
        rows = self.parse('<script>"<table><tr><td>fake</td></tr></table>"</script><template><table><tr><td>hidden</td></tr></table></template><table><tr><td>real</td></tr></table>')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['parts'], ['real'])

    def test_hash_changes_when_value_or_link_changes(self):
        source = '<table><tr><td>{}</td><td><a href="{}">source</a></td></tr></table>'
        base = self.parse(source.format('one', 'https://nba.com'))[0]['row_sha256']
        self.assertNotEqual(base, self.parse(source.format('two', 'https://nba.com'))[0]['row_sha256'])
        self.assertNotEqual(base, self.parse(source.format('one', 'https://nist.gov'))[0]['row_sha256'])

    def test_deterministic_generation_excludes_self_and_includes_all_other_sections(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for rel in ['index.html', 'docs/index.html', 'docs/legacy/a.html', 'docs/future/deep/a.html', 'docs/coverage/index.html']:
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('<table><tr><td>not verified</td></tr></table>')
            first, summary = coverage.artifacts(root)
            second, _ = coverage.artifacts(root)
            self.assertEqual(first, second)
            self.assertEqual(summary['pages'], 4)
            self.assertEqual(summary['data_rows'], 4)
            self.assertEqual(summary['independently_value_verified_by_this_audit'], 0)
            self.assertEqual(json.loads(first['data/source_coverage/summary.json']), summary)
            for filename, content in first.items():
                if filename.endswith('.html'):
                    # Every generated audit data row has primary repo/reference evidence.
                    for row in self.parse(content):
                        self.assertTrue(any(coverage.reference_kind(u) in {'official', 'repository'} for u in row['links']))


if __name__ == '__main__':
    unittest.main()
