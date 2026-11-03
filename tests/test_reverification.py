"""Tests for the line-by-line reverification source file and generated page.

Loaded by tools/run_tests.py (stdlib runner, no pytest needed).
"""
from __future__ import annotations

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "build_reverification", ROOT / "scripts" / "build_reverification.py"
)
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)


def _base_row(**overrides):
    row = {
        "id": "T01",
        "area": "test",
        "claim_location": "test",
        "claim_as_published": "test claim",
        "official_source_url": "https://www.nba.com/termsofuse",
        "official_source_read_on": "2026-11-03",
        "official_evidence": "quoted text",
        "result": "verified",
        "action": "",
    }
    row.update(overrides)
    return row


def test_csv_rows_validate():
    rows = br.load_rows()
    assert len(rows) >= 30, "expected the reviewed row set"
    errors = br.validate_all(rows)
    assert errors == [], errors


def test_every_row_has_https_official_source():
    for row in br.load_rows():
        url = row["official_source_url"]
        assert url.startswith("https://"), row["id"]
        host = url.split("/")[2]
        assert host in br.ALLOWED_HOSTS, (row["id"], host)


def test_committed_page_matches_generator():
    rows = br.load_rows()
    page = br.render(rows)
    committed = br.OUT_PATH.read_text(encoding="utf-8")
    assert committed == page, "run python3 scripts/build_reverification.py"


def test_rejects_disallowed_host():
    errs = br.validate_row(_base_row(official_source_url="https://example.com/x"))
    assert any("allowed official host" in e for e in errs), errs


def test_rejects_non_https_source():
    errs = br.validate_row(_base_row(official_source_url="http://www.nba.com/x"))
    assert any("https" in e for e in errs), errs


def test_rejects_verified_without_evidence_or_date():
    errs = br.validate_row(_base_row(official_evidence="", official_source_read_on=""))
    assert any("needs an ISO read date" in e for e in errs), errs
    assert any("quoted official_evidence" in e for e in errs), errs


def test_not_checked_must_not_carry_evidence_or_date():
    errs = br.validate_row(
        _base_row(result="not_checked", action="explain", official_evidence="x", official_source_read_on="")
    )
    assert any("must not carry evidence" in e for e in errs), errs
    errs = br.validate_row(
        _base_row(result="not_checked", action="explain", official_evidence="", official_source_read_on="2026-11-03")
    )
    assert any("must not carry a read date" in e for e in errs), errs


def test_mismatch_requires_action():
    errs = br.validate_row(_base_row(result="mismatch", action=""))
    assert any("needs an action" in e for e in errs), errs


def test_unknown_result_rejected():
    errs = br.validate_row(_base_row(result="maybe"))
    assert any("unknown result" in e for e in errs), errs


def test_repo_blob_link_must_exist():
    errs = br.validate_row(
        _base_row(official_source_url=br.REPO_BLOB_PREFIX + "does/not/exist.md")
    )
    assert any("repo file does not exist" in e for e in errs), errs


def test_duplicate_ids_rejected():
    errs = br.validate_all([_base_row(), _base_row()])
    assert any("duplicate id" in e for e in errs), errs
