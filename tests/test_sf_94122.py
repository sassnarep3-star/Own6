"""Adversarial regression tests for the SF Outer Sunset (94122) compliance suite."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_sf_94122  # noqa: E402


class TestSF94122Suite(unittest.TestCase):
    def test_current_tree_passes_all_gates(self) -> None:
        errors, stats = check_sf_94122.run_checks(ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(stats["html_pages"], 6)
        self.assertGreaterEqual(stats["html_rows"], 60)

    def test_exact_statutory_math_invariants(self) -> None:
        # Unit 1 ($3,995.00): 1.6% = $63.92 -> $4,058.92; 3.0% = $119.85 -> $4,114.85
        self.assertEqual(Decimal("3995.00") * Decimal("0.016"), Decimal("63.92000"))
        self.assertEqual(Decimal("3995.00") + Decimal("63.92"), Decimal("4058.92"))
        self.assertEqual(Decimal("3995.00") * Decimal("0.030"), Decimal("119.85000"))
        self.assertEqual(Decimal("3995.00") + Decimal("119.85"), Decimal("4114.85"))

        # Unit 2 ($3,150.00): 1.6% = $50.40 -> $3,200.40; 6-year banked (11.5%) + 1.6% = 13.1% ($412.65 -> $3,562.65)
        banked = sum(Decimal(x) for x in ("1.8", "0.7", "2.3", "3.6", "1.7", "1.4"))
        self.assertEqual(banked, Decimal("11.5"))
        self.assertEqual(Decimal("3150.00") * Decimal("0.016"), Decimal("50.40000"))
        self.assertEqual(Decimal("3150.00") * Decimal("0.131"), Decimal("412.65000"))
        self.assertEqual(Decimal("3150.00") + Decimal("412.65"), Decimal("3562.65"))

    def test_privacy_scanner_rejects_spaced_and_compact_initials(self) -> None:
        self.assertTrue(check_sf_94122.check_privacy_text("sample", "Occupant A B signed lease"))
        self.assertTrue(check_sf_94122.check_privacy_text("sample", "Occupant ZX signed lease"))
        self.assertEqual(check_sf_94122.check_privacy_text("sample", "Tenant 1A and Tenant 2B in SF CA"), [])

    def test_adversarial_mutations_caught(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            troot = Path(tmp)
            shutil.copytree(ROOT / "data" / "sf_94122", troot / "data" / "sf_94122")
            shutil.copytree(ROOT / "docs" / "sf-94122", troot / "docs" / "sf-94122")
            (troot / "research").mkdir()
            (troot / "audit").mkdir()
            shutil.copy2(ROOT / "research" / "SF_94122_EXECUTIVE_SUMMARY.md", troot / "research" / "SF_94122_EXECUTIVE_SUMMARY.md")
            shutil.copy2(ROOT / "audit" / "SF_94122_REPO_AND_SOURCE_AUDIT.md", troot / "audit" / "SF_94122_REPO_AND_SOURCE_AUDIT.md")

            # 1. Inject non-blank value into an unverified HTML cell & dead 404 URL
            idx_path = troot / "docs" / "sf-94122" / "index.html"
            orig = idx_path.read_text(encoding="utf-8")
            mutated = orig.replace('<td class="empty-cell"></td>', '<td class="empty-cell">guessed</td>', 1)
            mutated = mutated.replace(
                "https://www.sf.gov/learn-about-rent-increases-san-francisco",
                "https://sf.gov/information/find-out-if-san-franciscos-rental-law-applies-you",
                1,
            )
            idx_path.write_text(mutated, encoding="utf-8")

            errs, _ = check_sf_94122.run_checks(troot)
            self.assertTrue(any("does not leave its value cell blank" in e for e in errs))
            self.assertTrue(any("HTTP-404 URL" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
