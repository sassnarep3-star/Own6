#!/usr/bin/env python3
"""Unit tests for the nfl_2dd0cbcb pack. Stdlib only; no network, no clock reads.

Run either way:
    python3 tests/test_nfl_2dd0cbcb.py
    python3 -m pytest tests/test_nfl_2dd0cbcb.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_2dd0cbcb")
RAW = os.path.join(DATA, "raw")
DOCS = os.path.join(REPO, "docs", "nfl-2dd0cbcb")
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from nfl_2dd0cbcb import capture  # noqa: E402
import build_nfl_2dd0cbcb_data as BD  # noqa: E402

PAGES = ["index.html", "requirements.html", "captures.html", "depth.html", "flags.html",
         "sources.html"]


def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def raw(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as f:
        return f.read()


class TestTranscriptionParsing(unittest.TestCase):
    def test_venue_lines_all_parse(self):
        lines = [l for l in raw("week12_venues_2026-11-19.md").splitlines() if l.startswith("VENUE|")]
        self.assertEqual(len(lines), 16)
        for ln in lines:
            self.assertEqual(len(ln.split("|")), 9, ln)

    def test_normalization_rule(self):
        self.assertEqual(BD.norm_venue("LEVI'S® STADIUM"), BD.norm_venue("Levis Stadium"))
        self.assertEqual(BD.norm_venue("U.S. BANK STADIUM"), BD.norm_venue("US Bank Stadium"))
        self.assertNotEqual(BD.norm_venue("ACRISURE STADIUM"), BD.norm_venue("Heinz Field Stadium"))
        self.assertNotEqual(BD.norm_venue("RELIANT STADIUM"), BD.norm_venue("NRG Stadium"))
        self.assertNotEqual(BD.norm_venue("EVERBANK STADIUM"), BD.norm_venue("TIAA Bank Field"))

    def test_derived_csv_row_counts_match_raw(self):
        for name, prefix, expected in (
                ("week12_venues.csv", "VENUE|", 16),
                ("thursday_status_reg11.csv", "THUR|", 26),
                ("reserve_rows.csv", "RES|", 25)):
            src = {"week12_venues.csv": "week12_venues_2026-11-19.md",
                   "thursday_status_reg11.csv": "week12_injuries_probe_2026-11-19.md",
                   "reserve_rows.csv": "reserve_list_2026-11-19.md"}[name]
            n = sum(1 for l in raw(src).splitlines() if l.startswith(prefix))
            self.assertEqual(n, expected, name)
            self.assertEqual(len(rows(name)), expected, f"{name} rows != raw rows")
        self.assertEqual(len(rows("depth_retest.csv")), 3)

    def test_reserve_rows_reproduce_verbatim(self):
        """Every transcribed reserve row appears in the CSV with the same fields."""
        pairs = []
        for ln in raw("reserve_list_2026-11-19.md").splitlines():
            if ln.startswith("RES|"):
                _, d, n, c, t = ln.split("|")
                pairs.append((d, n, c, t))
        csvpairs = [(r["date"], r["name"], r["club"], r["transaction"]) for r in rows("reserve_rows.csv")]
        self.assertEqual(len(pairs), 25)
        self.assertEqual(pairs, csvpairs[:len(pairs)])

    def test_thursday_status_counts(self):
        r = rows("thursday_status_reg11.csv")
        self.assertEqual(sum(1 for x in r if x["game_status"]), 16)
        self.assertEqual(sum(1 for x in r if not x["game_status"]), 10)
        self.assertEqual({x["club"] for x in r}, {"IND", "HOU"})
        blanks = {x["player"] for x in r if not x["game_status"]}
        self.assertIn("Jaylon Carlies", blanks)
        self.assertIn("Azeez Al-Shaair", blanks)

    def test_venue_flags_recomputed(self):
        """The two comparison columns are derived, not asserted."""
        for r in rows("week12_venues.csv"):
            self.assertEqual(
                r["venue_mismatch_after_normalization"],
                "yes" if BD.norm_venue(r["venue_stadium_gamecentre"])
                != BD.norm_venue(r["venue_hotel_param_schedulepage"]) else "no")
        mism = {(r["away"], r["home"]) for r in rows("week12_venues.csv")
                 if r["venue_mismatch_after_normalization"] == "yes"}
        self.assertEqual(mism, {("DEN", "PIT"), ("BAL", "HOU"), ("TEN", "JAX")})


class TestCaptureLog(unittest.TestCase):
    def test_hashes_match_artifact_bytes(self):
        self.assertEqual(capture.verify_capture_log(), [])

    def test_raw_dir_holds_only_declared_transcriptions(self):
        names = sorted(f for f in os.listdir(RAW))
        self.assertEqual(len(names), 5, names)
        for fn in names:
            body = raw(fn)
            self.assertIn("TRANSCRIPTION", body[:400], f"{fn}: does not declare itself a transcription")
            self.assertIn("2dd0cbcb", body, f"{fn}: not attributed to this session")
            for host in re.findall(r"https?://([^/\s)]+)", body):
                self.assertTrue(
                    host.endswith(("nfl.com", "azcardinals.com", "packers.com",
                                   "houstontexans.com", "github.com")),
                    f"{fn}: offlist host {host}")
            listed = [r["artifact_path"].split("/")[-1] for r in rows("capture_log.csv")]
            self.assertIn(fn, listed, f"{fn}: written but not logged")

    def test_log_states_what_the_hash_cannot_prove(self):
        log = rows("capture_log.csv")
        self.assertEqual(len(log), 7)
        for r in log:
            self.assertIn("transcription artifact", r["artifact_sha_covers"])
            self.assertIn("cannot prove", r["artifact_sha_covers"])
            self.assertRegex(r["read_on_utc"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertIn("upper bound", r["note"], "write-clock caveat must be in the row")

    def test_tampering_is_detected(self):
        path = os.path.join(RAW, "reserve_list_2026-11-19.md")
        original = open(path, encoding="utf-8").read()
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write("\nRES|11/19|Some Extra Row|XX|Planted after the fact\n")
            problems = capture.verify_capture_log()
        finally:
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)
        self.assertTrue(any("sha256 drift" in p for p in problems), problems)
        self.assertEqual(capture.verify_capture_log(), [], "restore did not return to verified state")

    def test_write_raw_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write("hello")
            self.assertEqual(capture.sha256_file(p),
                             hashlib.sha256(b"hello").hexdigest())


class TestRegisters(unittest.TestCase):
    def test_requirements_shape(self):
        r = rows("requirements.csv")
        self.assertEqual(len(r), 80)
        self.assertEqual([x["req_id"] for x in r], [f"R{i:02d}" for i in range(1, 81)])
        for x in r:
            self.assertTrue(x["brief_line"].strip())
            self.assertTrue(x["blocking_gate"].strip())
            self.assertTrue(x["evidence_pointer"].strip())
            if not x["evidence_pointer"].startswith("http"):
                self.assertTrue(os.path.exists(os.path.join(REPO, x["evidence_pointer"])),
                                f"{x['req_id']}: dangling pointer {x['evidence_pointer']}")

    def test_satisfied_rows_are_anchored_to_files(self):
        for x in rows("requirements.csv"):
            if x["status"].startswith("satisfied"):
                self.assertFalse(x["evidence_pointer"].startswith("data/nfl_2dd0cbcb/raw/"),
                                 f"{x['req_id']}: satisfied on a raw transcription alone")

    def test_questions_blanks_are_meaningful(self):
        r = rows("questions.csv")
        self.assertEqual(len(r), 8)
        for x in r:
            if x["status"].strip() == "open":
                self.assertEqual(x["answer"], "", f"{x['q_id']}: open question must stay unanswered")
                self.assertEqual(x["answered_by"], "")
                self.assertEqual(x["answered_on"], "")
            else:
                self.assertTrue(x["answer"].strip() and x["answered_on"].strip())

    def test_suggestions_never_self_approve(self):
        r = rows("suggestions.csv")
        self.assertEqual(len(r), 13)
        for x in r:
            for field in ("decision", "decided_by", "decided_on"):
                self.assertEqual(x[field].strip(), "", f"{x['s_id']}: {field} is the owner's to fill")

    def test_flags_never_block(self):
        r = rows("flagged.csv")
        self.assertEqual(len(r), 10)
        self.assertTrue(all(x["blocking_merge"] == "no" for x in r))
        self.assertTrue(all(x["source_urls"].strip() for x in r))
        self.assertTrue(all(x["severity"] in ("high", "medium", "low", "info") for x in r))

    def test_rechecks_have_findings(self):
        r = rows("rechecks.csv")
        self.assertEqual(len(r), 20)
        self.assertEqual(len({x["flag_id"] for x in r}), 20)
        self.assertTrue(all(x["finding"].strip() for x in r))
        for x in r:
            self.assertTrue(x["method"].strip(), f"{x['flag_id']}: no method stated")

    def test_depth_image_only_has_no_rows(self):
        for x in rows("depth_retest.csv"):
            if x["render"] == "image-only":
                self.assertEqual(x["text_rows_count"], "0")
                self.assertEqual(x["qb_group_as_read"], "")


class TestSite(unittest.TestCase):
    def test_pages_exist_and_are_deterministic(self):
        have = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
        self.assertEqual(have, sorted(PAGES))
        before = {p: hashlib.sha256(open(os.path.join(DOCS, p), "rb").read()).hexdigest()
                  for p in PAGES}
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_2dd0cbcb.py")],
                       check=True, capture_output=True)
        after = {p: hashlib.sha256(open(os.path.join(DOCS, p), "rb").read()).hexdigest()
                 for p in PAGES}
        self.assertEqual(before, after, "site rebuild changed bytes")

    def test_no_form_controls_and_no_script_tags(self):
        for p in PAGES:
            text = open(os.path.join(DOCS, p), encoding="utf-8").read()
            for tag in ("<input", "<select", "<textarea", "<button", "<form", "<script", "onclick"):
                self.assertNotIn(tag, text, f"{p}: {tag}")

    def test_no_claim_vocabulary_in_prose(self):
        banned = re.compile(r"\b(units won|guaranteed|expected return|buy now|profitable)\b", re.I)
        for p in PAGES:
            text = open(os.path.join(DOCS, p), encoding="utf-8").read()
            m = banned.search(text)
            self.assertIsNone(m, f"{p}: {m.group(0) if m else ''}")

    def test_acronyms_confined_to_the_brief_lines(self):
        for p in PAGES:
            if p == "requirements.html":
                continue
            text = open(os.path.join(DOCS, p), encoding="utf-8").read()
            self.assertNotRegex(text, r"\b(ROI|CLV)\b", f"{p}: claim acronym outside the brief table")

    def test_external_hosts_are_allowlisted(self):
        ok = ("nfl.com", "azcardinals.com", "packers.com", "houstontexans.com", "github.com")
        for p in PAGES:
            text = open(os.path.join(DOCS, p), encoding="utf-8").read()
            for href in re.findall(r'href="(https?://[^"]+)"', text):
                self.assertTrue(href.startswith("https://"), href)
                host = href.split("/")[2]
                self.assertTrue(any(host == d or host.endswith("." + d) for d in ok),
                                f"{p}: offlist host {host}")
                self.assertNotIn("aliyuncs", host)

    def test_blank_cells_are_labelled(self):
        """A blank in a register never renders as an empty cell."""
        text = open(os.path.join(DOCS, "captures.html"), encoding="utf-8").read()
        self.assertNotIn("<td></td>", text)
        self.assertIn('class="blank"', text)


class TestIntegration(unittest.TestCase):
    def test_hub_and_landing_reference_this_pack(self):
        for p in ("docs/index.html", "index.html", "README.md"):
            text = open(os.path.join(REPO, p), encoding="utf-8").read()
            self.assertIn("nfl-2dd0cbcb", text.replace("docs/nfl-2dd0cbcb", "nfl-2dd0cbcb"),
                          f"{p}: pack not linked from the hub/landing")

    def test_ci_workflow_covers_the_pack(self):
        path = os.path.join(REPO, ".github", "workflows", "nfl-2dd0cbcb-ci.yml")
        self.assertTrue(os.path.exists(path), "pack has no CI workflow")
        text = open(path, encoding="utf-8").read()
        for need in ("build_nfl_2dd0cbcb_data.py", "build_nfl_2dd0cbcb.py",
                     "check_nfl_2dd0cbcb.py", "test_nfl_2dd0cbcb.py",
                     "git diff --exit-code -- data/nfl_2dd0cbcb",
                     "git diff --exit-code -- docs/nfl-2dd0cbcb"):
            self.assertIn(need, text, f"CI missing: {need}")

    def test_checker_passes(self):
        r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_nfl_2dd0cbcb.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
