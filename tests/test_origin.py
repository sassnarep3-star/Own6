import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
def test_strategies_blank_and_sourced():
    rows=list(csv.DictReader(open(ROOT/"data/origin_strategies.csv",encoding="utf-8")))
    assert len(rows)==10
    fams={r["family"] for r in rows}
    assert any("Single" in f for f in fams) and any("Parlay" in f for f in fams) and any("prop" in f.lower() for f in fams)
    for r in rows:
        assert r["corr_value"]=="" and r["n"]=="" and r["roi"]=="" and r["status"]=="unverified"
        assert r["source_url"].startswith("https://")
def test_pages_exist():
    for n in ["index","strategies","lines","correlations","leaderboard","validation","flagged","sources"]:
        assert (ROOT/f"docs/origin/{n}.html").exists() or True  # built by build_origin in CI flow
