"""Tests for the nfl-4c8cf5a6 pack: builder determinism and register consistency."""
import csv
import hashlib
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_4c8cf5a6")
DOCS = os.path.join(REPO, "docs", "nfl-4c8cf5a6")


def read(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pages():
    return sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))


class BuildDeterminism(unittest.TestCase):
    def test_pages_exist(self):
        expected = [
            "index.html", "requirements.html", "gates.html", "questions.html",
            "gaps.html", "suggestions.html", "strategies.html", "leaderboard.html",
            "price-snapshot.html", "results-feed.html", "originated-lines.html",
            "depth.html", "injuries.html", "correlations.html", "validation.html",
            "snapshot-ledger.html", "flagged.html", "sources.html",
            "repo-review.html", "executive-summary.html",
        ]
        for name in expected:
            self.assertIn(name, pages(), f"missing page {name}")

    def test_deterministic_rebuild(self):
        before = {p: hashlib.sha256(
            open(os.path.join(DOCS, p), "rb").read()).hexdigest() for p in pages()}
        subprocess.run([sys.executable, "scripts/build_nfl_4c8cf5a6.py"], cwd=REPO,
                       capture_output=True, check=True)
        after = {p: hashlib.sha256(
            open(os.path.join(DOCS, p), "rb").read()).hexdigest() for p in pages()}
        self.assertEqual(before, after, "rebuild is not byte-identical")

    def test_no_interactive_controls(self):
        import re
        pat = re.compile(r"<\s*(input|select|textarea|button)\b", re.I)
        for p in pages():
            text = open(os.path.join(DOCS, p), encoding="utf-8").read()
            self.assertNotRegex(text, pat, f"interactive control in {p}")


class RegisterConsistency(unittest.TestCase):
    def test_requirement_statuses(self):
        vocab = {"cleared", "cleared_repo", "structural", "blocked", "rejected", "open",
                 "partially cleared", "needs review", "in progress"}
        reqs = read("requirements.csv")
        self.assertGreater(len(reqs), 0)
        bad = {r["status"] for r in reqs} - vocab
        self.assertEqual(bad, set(), f"unknown statuses {bad}")
        gates = {g["gate_id"] for g in read("gates.csv")}
        dangling = {r["blocking_gate"] for r in reqs if r["blocking_gate"]} - gates
        self.assertEqual(dangling, set(), f"undefined gates referenced {dangling}")
        for g in read("gates.csv"):
            self.assertTrue(g["clearing_number"].strip(),
                            f"gate {g['gate_id']} has no clearing number")

    def test_suggestion_options(self):
        sug = read("suggestions.csv")
        opts = read("suggestion_options.csv")
        counts = {}
        for o in opts:
            counts[o["suggestion_id"]] = counts.get(o["suggestion_id"], 0) + 1
        for s in sug:
            self.assertGreaterEqual(counts.get(s["suggestion_id"], 0), 2,
                                    f"suggestion {s['suggestion_id']} needs >= 2 options")
        self.assertEqual(set(counts), {s["suggestion_id"] for s in sug},
                         "orphan options present")
        for s in sug:
            self.assertEqual(s.get("owner_decision", "").strip(), "",
                             f"decision column filled for {s['suggestion_id']}")
        for o in opts:
            self.assertEqual(o.get("owner_choice", "").strip(), "",
                             f"choice column filled for {o['option_id']}")

    def test_strategies_not_registered(self):
        strat = read("strategies.csv")
        self.assertEqual(len(strat), 10)
        for s in strat:
            self.assertIn(s["status"], {"declared", "registered", "qualified", "demoted",
                                        "rejected"})
            if s["status"] == "registered":
                self.assertTrue(s["registration_commit"].strip(),
                                f"strategy {s['strategy_id']} registered without commit")
        lb = read("leaderboard.csv")
        self.assertEqual(len(lb), 0, "leaderboard should be empty by design")


if __name__ == "__main__":
    unittest.main()
