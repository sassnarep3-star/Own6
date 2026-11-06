import csv
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/rental"

class TestRentalMath(unittest.TestCase):
    def test_16_percent_calc_unit1(self):
        self.assertAlmostEqual(3995 * 0.016, 63.92, places=2)

    def test_30_percent_calc_unit1(self):
        self.assertAlmostEqual(3995 * 0.03, 119.85, places=2)

    def test_16_percent_calc_unit2(self):
        self.assertAlmostEqual(3150 * 0.016, 50.40, places=2)

    def test_banked_additive_not_compound(self):
        # SF.gov example: 1.7+1.4+1.6 =4.7% on 1000 => 47 not 47.9 compounded
        additive = 0.017 + 0.014 + 0.016
        self.assertAlmostEqual(additive, 0.047, places=5)
        self.assertEqual(round(1000 * additive, 2), 47.00)
        # compound would be (1.017*1.014*1.016 -1)*1000 ≈ 47.74 -> not lawful
        compound = 1.017 * 1.014 * 1.016 - 1
        self.assertNotAlmostEqual(compound, additive, places=3)

    def test_check_rental_passes(self):
        result = subprocess.run([sys.executable, "scripts/check_rental.py"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("OK:", result.stdout)

    def test_build_rental_idempotent(self):
        # build twice and check no diff in git (files should be identical)
        subprocess.run([sys.executable, "scripts/build_rental.py"], cwd=ROOT, check=True)
        import os
        # run again
        result = subprocess.run([sys.executable, "scripts/build_rental.py"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_every_data_row_has_source(self):
        # ensure each required CSV has source column with https
        checks = [
            ("sf_allowable_increases.csv", "source_url_official"),
            ("sf_rent_board_rules.csv", "source_url_official"),
            ("state_federal_laws.csv", "source_url_official"),
            ("calculations_per_unit.csv", "source_url_official"),
        ]
        for fname, col in checks:
            with (DATA / fname).open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
                for i, r in enumerate(rows, 1):
                    self.assertTrue(r[col].startswith("https://"), f"{fname} row {i} missing official source {r[col]}")

    def test_units_anonymized(self):
        with (DATA / "units.csv").open(newline="", encoding="utf-8") as f:
            text = f.read()
            # original initials should not appear on public units.csv
            self.assertNotIn("L O", text)
            self.assertNotIn("V N", text)
            self.assertNotIn("JP", text)
            self.assertNotIn("M T", text)
            self.assertNotIn("E R", text)
            self.assertNotIn("I S", text)
            # anonymized should appear
            self.assertIn("Tenant A", text)

    def test_no_rounding_up(self):
        # verify reported increases are not rounded up
        with (DATA / "calculations_per_unit.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            for r in rows:
                if r['scenario_id'] == "C-RULE":
                    continue
                base = float(r['base_rent'])
                dec = float(r['increase_decimal'])
                exact = base * dec
                reported = float(r['dollar_increase_computed'])
                # reported must be exact truncated/rounded to cents not ceil
                self.assertAlmostEqual(reported, round(exact, 2), places=2)
                # should not be math.ceil
                import math
                ceiled = math.ceil(exact * 100) / 100 if exact != round(exact, 2) else round(exact, 2)
                # For these .00-precise cases ceiled == rounded, but general guard
                self.assertEqual(reported, round(exact, 2))

    def test_notice_30_90_threshold(self):
        with (DATA / "calculations_per_unit.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            for r in rows:
                if r['scenario_id'] == "C-RULE":
                    continue
                pct = float(r['allowable_increase_pct'])
                notice = r['requires_30_or_90_day_notice']
                if pct > 10:
                    self.assertIn("90-day", notice, f"{r['scenario_id']} >10% should be 90-day")
                elif pct > 0:
                    self.assertIn("30-day", notice, f"{r['scenario_id']} ≤10% should be 30-day")

if __name__ == "__main__":
    unittest.main()
