"""Tests for the nfl_dfc0c1bc pack.

Layer 1 — the verifier (all 15 rules) passes on the built pack.
Layer 2 — module identities that do not depend on the CSVs: register loading, theme assignment,
          the scoring formula, and the rule that the owner's columns are empty.
Layer 3 — determinism: a second build overwrites every file byte for byte.

Run: python3 tests/test_nfl_dfc0c1bc.py   (or pytest tests/test_nfl_dfc0c1bc.py)
"""
from __future__ import annotations

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_dfc0c1bc import consolidate as CO  # noqa: E402
from nfl_dfc0c1bc import metrics as ME  # noqa: E402
from nfl_dfc0c1bc import reads as RD  # noqa: E402
from nfl_dfc0c1bc import registers as RG  # noqa: E402
from nfl_dfc0c1bc import themes as TH  # noqa: E402


def test_verifier_passes():
    out = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_nfl_dfc0c1bc.py")],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_registers_are_all_found_and_hashed():
    inv = RG.iter_registers()
    assert len(inv) >= 20
    kinds = {i["kind"] for i in inv}
    assert kinds == {"suggestions", "questions"}
    for i in inv:
        assert len(i["sha256"]) == 64
        assert int(i["rows"]) > 0
        assert os.path.exists(os.path.join(REPO, i["path"]))


def test_alias_field_picks_the_first_present_name():
    row = {"suggestion_id": "S1", "title": "t", "official_source_url": "https://www.nfl.com/x"}
    assert RG.field(row, "id") == "S1"
    assert RG.field(row, "statement") == ""          # not present under any alias
    assert RG.field(row, "source_url").endswith("/x")
    assert RG.field({"question_id": "Q1", "suggestion": "s"}, "id") == "Q1"
    assert RG.field({"suggestion": "s"}, "statement") == "s"


def test_every_row_lands_on_a_defined_theme():
    inv = RG.iter_registers()
    rows = CO.assign_themes(RG.load_rows(inv))
    valid = set(TH.THEME_IDS)
    for r in rows:
        assert r["theme_id"] in valid, f"{r['file']}#{r['local_id']} -> {r['theme_id']}"
    counts = CO.group_by_theme([r for r in rows if r["kind"] == "suggestions"])
    assert not counts.get("T00"), "unclassified suggestion rows must be assigned by hand, not dropped"


def test_theme_assignment_is_reproducible():
    inv = RG.iter_registers()
    first = [(r["file"], r["local_id"], r["theme_id"]) for r in CO.assign_themes(RG.load_rows(inv))]
    second = [(r["file"], r["local_id"], r["theme_id"]) for r in CO.assign_themes(RG.load_rows(inv))]
    assert first == second


def test_paths_scored_by_the_published_formula():
    inv = RG.iter_registers()
    rows = CO.assign_themes(RG.load_rows(inv))
    sug = CO.group_by_theme([r for r in rows if r["kind"] == "suggestions"])
    que = CO.group_by_theme([r for r in rows if r["kind"] == "questions"])
    paths = CO.decision_paths(sug, que, RD.answers(), RD.observations())
    assert len(paths) == len(TH.THEMES)
    for p in paths:
        value = 2 * int(p["packs_raising_it"]) + int(p["suggestion_rows"]) + int(p["question_rows"]) \
            + 2 * int(p["evidence_rows_this_session"])
        assert int(p["value"]) == value, (p["theme_id"], p["value"], value)
        # the ratio is published rounded to two decimals, so the identity is checked at that precision
        assert p["ratio"] == f"{value / int(p['effort_score']):.2f}", (p["theme_id"], p["ratio"])
    seq = [int(p["sequence"]) for p in paths]
    assert seq == sorted(seq) and seq[0] == 1
    ratios = [float(p["ratio"]) for p in paths]
    assert ratios == sorted(ratios, reverse=True)


def test_owner_columns_are_empty_by_construction():
    inv = RG.iter_registers()
    rows = CO.assign_themes(RG.load_rows(inv))
    master = CO.suggestions_master([r for r in rows if r["kind"] == "suggestions"])
    assert all(m["owner_decision"] == "" and m["owner_notes"] == "" for m in master)
    assert all(m["master_id"].startswith("SM-") for m in master)
    assert len({m["master_id"] for m in master}) == len(master)


def test_read_evidence_is_quoted_and_host_checked():
    reads = RD.reads()
    assert len(reads) >= 9
    assert RD.read_hosts_ok()
    for r in reads:
        assert r["verbatim_excerpt"], r["read_id"]
        assert r["url"].startswith("https://" + r["host"])
    obs = RD.observations()
    ids = {r["read_id"] for r in reads}
    for o in obs:
        assert all(part in ids for part in o["read_id"].split("|"))
    assert {a["theme"] for a in RD.answers()} <= set(TH.THEME_IDS)


def test_metrics_never_invent_a_number_for_a_missing_file():
    met = {m["metric_id"]: m for m in ME.compute()}
    missing = [m for m in met.values() if m["exists"] == "no"]
    for m in missing:
        assert m["rows"] == "", f"{m['metric_id']} counted a file that is not there"
        assert m["rows"] == "" and "not in the tree" in m["note"]
    # the corpus metric must report each pack separately, not a pooled total
    files = {m["file"] for m in met.values() if m["kind"] == "results"}
    assert len(files) >= 8
    sem = ME.price_semantics()
    assert {x["pack"] for x in sem} == {"nfl_309921cc", "nfl_67233566", "nfl_6cefc476",
                                        "nfl_8362b702", "nfl_d966f630", "nfl_f4"}


def test_lions_check_reads_the_file_it_cites():
    lions = ME.lions_cells()
    assert [l["player"] for l in lions] == ["Kerby Joseph", "Cade Mays", "D.J. Reed"]
    src = ME.load("data/nfl_48217a55/injury_report_2026_11_15.csv") or []
    for l in lions:
        hit = [r for r in src if r.get("player", "").strip() == l["player"]]
        assert (hit[0]["game_status"] if hit else "") == l["game_status_in_file"]


def test_rebuild_is_byte_identical():
    import hashlib

    def digest():
        h = {}
        for base in (os.path.join(REPO, "data", "nfl_dfc0c1bc"), os.path.join(REPO, "docs", "nfl-dfc0c1bc")):
            for root, _, files in os.walk(base):
                for f in sorted(files):
                    p = os.path.join(root, f)
                    with open(p, "rb") as fh:
                        h[p] = hashlib.sha256(fh.read()).hexdigest()
        return h

    before = digest()
    subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_dfc0c1bc.py")],
                   check=True, capture_output=True)
    assert digest() == before


def _run():
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except AssertionError as exc:
                failed += 1
                print(f"  FAIL {name}: {exc}")
    print(f"{'ALL PASS' if not failed else str(failed) + ' FAILED'} "
          f"({len([1 for k, v in globals().items() if k.startswith('test_') and callable(v)])} tests)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
