"""Adversarial source/provenance regressions; no external fetch or fabricated data."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import csv
import json
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("hub_gate", ROOT / "scripts/check_hub.py")
gate = module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.mark.parametrize("url", [
    "https://evilnba.com/fact", "https://nba.com.example.org/fact",
    "https://www.nba.com@evil.org/fact", "http://www.nba.com/fact",
    "//www.nba.com/fact", "https://nba.com:444/fact", "https://user@nba.com/fact",
    "https://nba.com\\@evil.org/fact", "https://nba.com/a b",
])
def test_official_reference_rejects_spoofs(url):
    assert not gate.official_reference(url)


def test_source_role_is_not_inferred_from_https():
    assert gate.qualifies("https://www.nba.com/termsofuse", "official-reference")
    assert not gate.qualifies("https://www.espn.com/nba", "official-reference")
    assert not gate.qualifies("https://www.nba.com/termsofuse", "secondary-record")
    assert not gate.qualifies("https://github.com/stranger/claims/blob/main/odds.csv", "project-record")
    assert not gate.qualifies("https://github.com/sassnarep3-star/Own6-evil/blob/main/x", "project-record")
    assert not gate.qualifies("https://github.com/sassnarep3-star/Own6/blob/main/%2e%2e/x", "project-record")
    assert gate.qualifies("https://github.com/sassnarep3-star/Own6/blob/main/README.md", "project-record")


def fixture(tmp_path, row, tid="test"):
    page = tmp_path / "test.html"
    page.write_text(f'<h1>Test</h1><table id="{tid}"><thead><tr><th>Value</th><th>Source</th></tr></thead>'
                    f'<tbody>{row}</tbody></table>', encoding="utf-8")
    return gate.check_page(page, tmp_path)[0]


def test_secondary_only_row_fails(tmp_path):
    issues = fixture(tmp_path, '<tr><td>Record</td><td><a href="https://www.espn.com/nba" '
                     'data-source-kind="secondary-record">ESPN</a></td></tr>')
    assert any("lacks a scoped" in e for e in issues)


@pytest.mark.parametrize("value", ["123.4", "0", "<span>123</span>", "<img src='value.svg'>"])
def test_nonempty_unverified_field_fails(tmp_path, value):
    issues = fixture(tmp_path, f'<tr><td data-evidence="unverified">{value}</td><td>'
                     '<a href="https://www.nba.com/termsofuse" data-source-kind="official-reference">Terms</a></td></tr>')
    assert any("nonblank unverified" in e for e in issues)


def test_truly_empty_unverified_field_passes(tmp_path):
    assert not fixture(tmp_path, '<tr><td data-evidence="unverified" aria-label="blank, unverified"></td><td>'
                       '<a href="https://www.nba.com/termsofuse" data-source-kind="official-reference">Terms</a></td></tr>')


def test_removing_provenance_does_not_enable_publishing(tmp_path):
    issues = fixture(tmp_path, '<tr><td>Legacy value</td><td>123</td></tr>', "standings")
    assert any("lacks required blank provenance" in e for e in issues)


def test_width_mismatch_fails(tmp_path):
    issues = fixture(tmp_path, '<tr><td>Only one cell</td></tr>')
    assert any("cells for" in e for e in issues)


def test_hub_rebuild_is_deterministic():
    paths = sorted((ROOT / "docs/hub").glob("*.html"))
    before = {p.name: p.read_bytes() for p in paths}
    subprocess.run([sys.executable, str(ROOT / "scripts/build_hub.py")], check=True)
    assert {p.name: p.read_bytes() for p in paths} == before


def read_csv(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def table_rows(page, table):
    parsed = gate.Page()
    parsed.feed((ROOT / "docs/hub" / page).read_text(encoding="utf-8"))
    return [r for r in parsed.rows if r["table"] == table]


@pytest.mark.parametrize("page,table,inputs", [
    ("results.html", "results", ["data/games_results_2026-27.csv", "data/results_2026-11-02.csv"]),
    ("standings.html", "standings", ["data/standings_live_2026-11-03.csv"]),
    ("standings.html", "ratings", ["data/team_ratings_2026-27.csv"]),
    ("lines.html", "lines", ["data/market_lines_2026-11-02.csv"]),
    ("props.html", "props", ["data/player_props_2026-11-02.csv"]),
    ("forward-test.html", "forward-games", ["data/forward_test_2026-11-02.csv"]),
    ("forward-test.html", "forward-summary", ["data/forward_test_summary_2026-11-02.csv"]),
])
def test_every_input_record_preserved_and_values_blank(page, table, inputs):
    rows = table_rows(page, table)
    assert len(rows) == sum(len(read_csv(path)) for path in inputs)
    for row in rows:
        for column in gate.WITHHELD_COLUMNS[table]:
            assert row["cells"][column]["unverified"]
            assert not row["cells"][column]["text"].strip()
            assert not row["cells"][column]["markup"]


def test_no_correlation_or_reward_value_promoted():
    corr = table_rows("correlations.html", "correlations")
    report = json.loads((ROOT / "data/empirical/report.json").read_text())
    assert len(corr) == len(read_csv("data/correlation_findings.csv")) + len(report["correlations"])
    for row in corr:
        assert all(row["cells"][i]["unverified"] for i in (2, 3, 4))
    for row in table_rows("strategies.html", "strategies"):
        assert all(row["cells"][i]["unverified"] for i in (4, 5, 6))


def test_all_historical_flags_retained():
    expected = (len(read_csv("data/hub_evidence_flags.csv")) + len(read_csv("data/hub_flags.csv"))
                + len(json.loads((ROOT / "data/flags.json").read_text())["rows"])
                + len(read_csv("data/flagged_items.csv")) + len(read_csv("data/empirical/repo_findings.csv")))
    assert len(table_rows("flagged.html", "flags")) == expected


def test_no_generic_sample_size_or_raw_correlation_qualification():
    text = (ROOT / "docs/hub/correlations.html").read_text()
    assert 'class="b ok">usable' not in text
    assert "Zero Pearson correlation does not prove independence" in text


def test_complete_hub_passes_scoped_gate():
    issues, pages, rows = gate.check_hub(ROOT)
    assert not issues, issues
    assert pages == 12 and rows > 300
