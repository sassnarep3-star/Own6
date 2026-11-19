"""Regression tests for the consolidated decision-review registers (metadata only)."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_nfl_0f3037e8.py"
SPEC = importlib.util.spec_from_file_location("check_nfl_0f3037e8", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load checker from {MODULE_PATH}")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class DecisionReviewFreshnessTests(unittest.TestCase):
    def test_register_counts_match_frozen_portal_counts(self) -> None:
        self.assertEqual(gate.EXPECTED, gate.row_counts())

    def test_generated_decision_board_has_current_counts_and_destinations(self) -> None:
        self.assertEqual([], gate.check())
        board = gate.BOARD.read_text(encoding="utf-8")
        for target in gate.BOARD_TARGETS:
            with self.subTest(target=target):
                self.assertIn(f'href="{target}"', board)
                self.assertTrue((gate.BOARD.parent / target).is_file())

    def test_other_session_portal_requests_are_non_blocking_warnings(self) -> None:
        # The current coordination record assigns the shared root/README files to another
        # integration; surface that gap without failing this pack's independent check.
        warnings = gate.portal_warnings()
        self.assertIsInstance(warnings, list)
        self.assertTrue(all(item.startswith("U-F") for item in warnings))


if __name__ == "__main__":
    unittest.main()
