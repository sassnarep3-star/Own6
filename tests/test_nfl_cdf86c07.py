"""Tests for pack cdf86c07: verifier passes, verifier catches seeded defects, build is deterministic."""
import csv
import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_nfl_cdf86c07 as chk  # noqa: E402

DATA = ROOT / "data" / "nfl_cdf86c07"


def test_verifier_passes_on_committed_pack():
    assert chk.check() == []


def test_standings_match_prior_independent_read():
    prior = ROOT / "data" / "nfl_51698d74" / "standings_2026_11_19.csv"
    if not prior.exists():
        pytest.skip("prior pack absent")
    a = {r["club"]: r for r in csv.DictReader(open(DATA / "standings_2026_11_19.csv", encoding="utf-8"))}
    b = {r["club"]: r for r in csv.DictReader(open(prior, encoding="utf-8"))}
    assert set(a) == set(b)
    for k in a:
        for f in ("w", "l", "t", "pf", "pa", "net_pts"):
            assert a[k][f] == b[k][f], (k, f)


def test_league_totals():
    st = list(csv.DictReader(open(DATA / "standings_2026_11_19.csv", encoding="utf-8")))
    assert sum(int(r["w"]) for r in st) == 149
    assert sum(int(r["t"]) for r in st) == 2
    assert sum(int(r["pf"]) for r in st) == sum(int(r["pa"]) for r in st) == 6923


def test_seeded_bad_standings_is_caught(tmp_path, monkeypatch):
    src = DATA / "standings_2026_11_19.csv"
    lines = src.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1].replace(",0.889,", ",0.900,", 1)
    fake = tmp_path / "data"
    fake.mkdir()
    for f in DATA.iterdir():
        shutil.copy(f, fake / f.name)
    (fake / "standings_2026_11_19.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(chk, "DATA", fake)
    errs = chk.check()
    assert any("pct mismatch" in e for e in errs) or any("sha256" in e for e in errs)


def test_non_official_source_is_caught(tmp_path, monkeypatch):
    fake = tmp_path / "data"
    fake.mkdir()
    for f in DATA.iterdir():
        shutil.copy(f, fake / f.name)
    text = (fake / "flagged.csv").read_text(encoding="utf-8").replace("https://www.nfl.com/", "https://example.com/", 1)
    (fake / "flagged.csv").write_text(text, encoding="utf-8")
    monkeypatch.setattr(chk, "DATA", fake)
    assert any("non-official" in e for e in chk.check())


def test_build_is_deterministic(tmp_path):
    before = {f.name: f.read_bytes() for f in DATA.iterdir()}
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_nfl_cdf86c07.py")], check=True, cwd=ROOT)
    after = {f.name: f.read_bytes() for f in DATA.iterdir()}
    assert before == after


def test_site_has_no_inputs_and_eight_pages():
    pages = sorted(p.name for p in (ROOT / "docs" / "nfl-cdf86c07").glob("*.html"))
    assert len(pages) == 8
    for p in pages:
        assert "<input" not in (ROOT / "docs" / "nfl-cdf86c07" / p).read_text(encoding="utf-8")
