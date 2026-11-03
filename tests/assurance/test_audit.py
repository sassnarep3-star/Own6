import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "assurance"


def rows(name):
    with (OUT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_source_register_is_official_and_scope_limited():
    sources = rows("sources.csv")
    assert len(sources) == 22
    assert len({r["id"] for r in sources}) == len(sources)
    assert all(urlparse(r["url"]).scheme == "https" for r in sources)
    assert all(r["does_not_support"] for r in sources)
    assert sum(r["status"] == "verified_direct" for r in sources) == 20
    assert sum(r["status"] == "partial" for r in sources) == 2


def test_legacy_values_are_not_certified_by_url_presence():
    audit = rows("row_audit.csv")
    legacy = [r for r in audit if r["category"] == "legacy_data"]
    assert len(legacy) >= 541
    assert all(r["value_verification"] == "unverified" for r in legacy)
    assert all(r["official_scope_reference"].startswith("https://www.nba.com/") for r in audit)
    assert all(r["record_url"].startswith("https://github.com/sassnarep3-star/Own6/") for r in audit)


def test_inventory_hashes_and_line_counts():
    inventory = rows("inventory.csv")
    assert len(inventory) >= 130
    for r in inventory:
        raw = (ROOT / r["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == r["sha256"], r["path"]
        assert len(raw.decode("utf-8").splitlines()) == int(r["lines"]), r["path"]


def test_legacy_american_conversion_defect_is_reproducible():
    # This is a pure arithmetic regression, not an NBA observation or a quote.
    def legacy_imp(ml):
        return 100.0 / ml if ml > 0 else -ml / 100.0
    def correct_imp(ml):
        return 100.0 / (ml + 100) if ml > 0 else -ml / (-ml + 100)
    assert round(legacy_imp(-110) / (legacy_imp(-110) + legacy_imp(110)), 4) == 0.5475
    assert correct_imp(-110) / (correct_imp(-110) + correct_imp(110)) == 11 / 21


def test_current_landing_has_no_conflict_markers():
    text = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert not any(line.startswith(("<<<<<<<", "=======", ">>>>>>>")) for line in text.splitlines())


def test_summary_does_not_claim_empirical_verification():
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["structural_anomalies"] == []
    assert summary["record_statuses"]["unverified"] == sum(r["category"] == "legacy_data" for r in rows("row_audit.csv"))
    assert "No authorized" in summary["rights_status"]
    assert "does not verify an external fact" in summary["external_source_policy"]
