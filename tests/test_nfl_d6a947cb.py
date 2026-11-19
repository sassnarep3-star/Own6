"""Tests for the d6a947cb pack. Run: python3 -m unittest tests/test_nfl_d6a947cb.py  (or pytest)."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl_d6a947cb"
SITE = ROOT / "docs" / "nfl-d6a947cb"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


derive = load("derive_d6", "src/nfl_d6a947cb/derive.py")
checker = load("check_d6", "scripts/check_nfl_d6a947cb.py")
builder = load("build_d6", "scripts/build_nfl_d6a947cb.py")


class DeriveTests(unittest.TestCase):
    def test_requirements_rebuild_is_byte_identical(self):
        before = (DATA / "requirements.csv").read_bytes()
        derive.build_requirements()  # pure function: must not change the file
        rows = derive.build_requirements()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "requirements.csv"
            derive.write_csv(out, rows)
            self.assertEqual(out.read_bytes(), before)

    def test_duplicates_point_at_canonical_rows(self):
        rows = read_csv(DATA / "requirements.csv")
        dup = [r for r in rows if r["duplicate_of"]]
        self.assertEqual(len(dup), 8)
        canon = {r["req_id"] for r in rows}
        for r in dup:
            self.assertIn(r["duplicate_of"], canon)

    def test_every_requirement_has_a_category(self):
        rows = read_csv(DATA / "requirements.csv")
        self.assertNotIn("UNCATEGORIZED", {r["category"] for r in rows})

    def test_capture_hashes_match_raw_files(self):
        for r in read_csv(DATA / "capture_log.csv"):
            digest = hashlib.sha256((ROOT / r["file"]).read_bytes()).hexdigest()
            self.assertEqual(digest, r["sha256"], r["file"])


class RegisterTests(unittest.TestCase):
    def test_checker_passes_on_committed_tree(self):
        self.assertEqual(checker.main(), 0)

    def test_suggestions_are_pending_and_not_implemented(self):
        for r in read_csv(DATA / "suggestions.csv"):
            self.assertEqual(r["pending_human_choice"], "yes")
            self.assertEqual(r["implemented"], "no")

    def test_flagged_items_do_not_block_merge(self):
        for r in read_csv(DATA / "repo_findings.csv"):
            self.assertEqual(r["blocks_merge"], "no")

    def test_ragged_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.csv"
            bad.write_text('a,b\n1,2,3\n', encoding="utf-8")
            saved = checker.DATA
            checker.DATA = Path(tmp)
            try:
                with self.assertRaises(ValueError):
                    checker.rows("bad.csv")
            finally:
                checker.DATA = saved

    def test_hash_mismatch_is_reported(self):
        # The checker must fail when a raw excerpt changes after its hash was logged.
        raw = DATA / "raw" / "terms_nfl_com_s1_3_2026_11_19.txt"
        original = raw.read_bytes()
        try:
            raw.write_bytes(original + b"tamper\n")
            self.assertNotEqual(checker.main(), 0)
        finally:
            raw.write_bytes(original)


class SiteTests(unittest.TestCase):
    def test_landing_counts_match_registers(self):
        reqs = read_csv(DATA / "requirements.csv")
        idx = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'<div class="n">{len(reqs)}</div>', idx)
        met = sum(1 for r in reqs if r["d6a_status"] == "met")
        self.assertIn(f'<div class="n">{met}</div>', idx)

    def test_tables_are_balanced(self):
        for page in SITE.glob("*.html"):
            text = page.read_text(encoding="utf-8")
            self.assertEqual(text.count("<table"), text.count("</table>"), page.name)
            self.assertEqual(text.count("<tr>"), text.count("</tr>"), page.name)

    def test_no_promotional_wording(self):
        for page in list(SITE.glob("*.html")) + [ROOT / "NFL_D6A947CB_EXECUTIVE_SUMMARY.md"]:
            text = page.read_text(encoding="utf-8")
            for pat in checker.BANNED:
                self.assertIsNone(re.search(pat, text, flags=re.I), (page.name, pat))

    def test_builder_is_deterministic(self):
        before = {p.name: p.read_bytes() for p in SITE.glob("*.html")}
        builder.main()
        after = {p.name: p.read_bytes() for p in SITE.glob("*.html")}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
