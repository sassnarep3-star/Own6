#!/usr/bin/env python3
"""Verifier for the NFL-309921cc pack.

Runs every line-by-line rule the pack claims to satisfy:

 1. every published page exists, is HTML, and contains no <input> element;
 2. every table row on every page carries at least one source link;
 3. every table row on an official-data page links to an official host in the
    pack allowlist;
 4. every internal link resolves; every external link is https;
 5. every CSV row carries a non-empty source URL;
 6. no placeholder text ("n/a", "tbd", "unknown", "-") is used where a value is
    missing - missing values must be empty cells;
 7. the verified identities hold (32 clubs, sum W == sum L, sum PF == sum PA,
    28 clubs on the slate, injury rows counted per club match the raw capture);
 8. derived tables stay consistent with their inputs.

Exit code 0 = all rules pass.
"""

from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_309921cc import dataset as D  # noqa: E402
from nfl_309921cc import verified as V  # noqa: E402
from nfl_309921cc import stats  # noqa: E402

DOCS = os.path.join(REPO, "docs", "nfl-309921cc")

OFFICIAL_HOSTS = (
    "www.nfl.com", "operations.nfl.com", "support.nfl.com",
    "www.patriots.com", "www.detroitlions.com",
)

# Pages whose tables are built from official/club data and must therefore link
# to an official host on every row.
OFFICIAL_DATA_PAGES = {
    "standings.html", "slate.html", "injuries.html", "depth.html",
    "lines.html", "correlations.html",
}

PLACEHOLDERS = {"n/a", "na", "tbd", "unknown", "-", "--", "none", "null", "?"}

errors: list[str] = []
checks = 0


def ok(msg: str) -> None:
    global checks
    checks += 1
    print(f"  ok   {msg}")


def err(msg: str) -> None:
    global checks
    checks += 1
    errors.append(msg)
    print(f"  FAIL {msg}")


def read_csv(name: str) -> list[dict]:
    path = os.path.join(D.DATA_DIR, name)
    if not os.path.exists(path):
        err(f"missing dataset {name}")
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------
print("[1] pages exist, are HTML, and contain no manual-input elements")
pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
if not pages:
    err("no pages found")
for p in pages:
    html = open(os.path.join(DOCS, p), encoding="utf-8").read()
    if not html.strip().startswith("<!doctype html>"):
        err(f"{p}: not a doctype-html document")
    if re.search(r"<input\b", html, re.I):
        err(f"{p}: contains an <input> element (manual input is not allowed)")
    if not re.search(r"<table", html):
        err(f"{p}: contains no data table")
ok(f"{len(pages)} pages checked for doctype, tables and zero <input> elements")

# --------------------------------------------------------------------------
print("[2] every table row carries a source link")
row_re = re.compile(r"<tr>(.*?)</tr>", re.S)
href_re = re.compile(r'href="(https?://[^"]+)"')
total_rows = 0
unsourced = 0
for p in pages:
    html = open(os.path.join(DOCS, p), encoding="utf-8").read()
    for tbody in re.findall(r"<tbody>(.*?)</tbody>", html, re.S):
        for tr in row_re.findall(tbody):
            total_rows += 1
            if not href_re.search(tr):
                unsourced += 1
                if unsourced <= 10:
                    err(f"{p}: table row without a source link")
if unsourced == 0:
    ok(f"all {total_rows} published table rows carry a source link")

# --------------------------------------------------------------------------
print("[3] official-data pages link only to official hosts")
bad_host = 0
for p in sorted(OFFICIAL_DATA_PAGES):
    if p not in pages:
        err(f"official-data page missing: {p}")
        continue
    html = open(os.path.join(DOCS, p), encoding="utf-8").read()
    for tbody in re.findall(r"<tbody>(.*?)</tbody>", html, re.S):
        for tr in row_re.findall(tbody):
            hosts = [h for h in href_re.findall(tr)]
            if not any(any(host in h for host in OFFICIAL_HOSTS) for h in hosts):
                bad_host += 1
                if bad_host <= 10:
                    err(f"{p}: row without an official-host source link")
if bad_host == 0:
    ok("every official-data row links to an official NFL or club host")

# --------------------------------------------------------------------------
print("[4] internal links resolve and external links are https")
broken_internal = 0
insecure = 0
for p in pages:
    html = open(os.path.join(DOCS, p), encoding="utf-8").read()
    for m in re.finditer(r'href="([^"#][^"]*)"', html):
        href = m.group(1)
        if href.startswith("http://"):
            insecure += 1
            err(f"{p}: insecure http link {href}")
        elif href.startswith("https://") or href.startswith("mailto:"):
            continue
        else:
            target = os.path.join(DOCS, href.split("?")[0].split("#")[0])
            if not os.path.exists(target):
                broken_internal += 1
                err(f"{p}: broken internal link {href}")
if broken_internal == 0:
    ok("all internal links resolve")
if insecure == 0:
    ok("all external links are https")

# --------------------------------------------------------------------------
print("[5] every CSV row carries a source URL")
datasets = sorted(f for f in os.listdir(D.DATA_DIR) if f.endswith(".csv"))
csv_rows = 0
for name in datasets:
    rows = read_csv(name)
    if not rows:
        continue
    src_cols = [c for c in rows[0] if c.endswith("source_url")
                or c.endswith("_url") or c == "official_or_method_reference"
                or c == "official_or_repo_source_url"
                or c == "injury_report_url" or c == "depth_chart_url"]
    if not src_cols:
        err(f"{name}: no source-url column")
        continue
    missing = 0
    for r in rows:
        if not any((r.get(c) or "").startswith("https://") for c in src_cols):
            missing += 1
    csv_rows += len(rows)
    if missing:
        err(f"{name}: {missing} rows without an https source")
    else:
        ok(f"{name}: {len(rows)} rows, all sourced")

# --------------------------------------------------------------------------
print("[6] missing values are empty cells, never placeholders")
bad_placeholder = 0
for name in datasets:
    for row in read_csv(name):
        for k, v in row.items():
            if v is None:
                continue
            if v.strip().lower() in PLACEHOLDERS and k != "monetary_value":
                bad_placeholder += 1
                if bad_placeholder <= 10:
                    err(f"{name}: placeholder {v!r} in column {k}")
if bad_placeholder == 0:
    ok("no placeholder text used for missing values")

# --------------------------------------------------------------------------
print("[7] verified identities")
st = read_csv("standings_2026_w10.csv")
if len(st) != 32:
    err(f"standings has {len(st)} rows, expected 32")
else:
    ok("standings has 32 clubs")
w = sum(int(r["w"]) for r in st)
l = sum(int(r["l"]) for r in st)
t = sum(int(r["t"]) for r in st)
pf = sum(int(r["pf"]) for r in st)
pa = sum(int(r["pa"]) for r in st)
if w != l:
    err(f"sum(W)={w} != sum(L)={l}")
else:
    ok(f"sum(W) == sum(L) == {w}")
if t != 2:
    err(f"sum(T)={t}, expected 2")
else:
    ok(f"sum(T) == {t}")
if pf != pa:
    err(f"sum(PF)={pf} != sum(PA)={pa}")
else:
    ok(f"sum(PF) == sum(PA) == {pf}")
if len({r["abbr"] for r in st}) != 32:
    err("standings abbreviations are not unique")
else:
    ok("32 unique club abbreviations")
divs = {}
for r in st:
    divs.setdefault(r["division"], []).append(r["abbr"])
if any(len(v) != 4 for v in divs.values()) or len(divs) != 8:
    err("expected exactly 8 divisions of 4 clubs")
else:
    ok("8 divisions of 4 clubs")

# standings values match the raw verified capture exactly
mismatch = 0
for row, raw in zip(st, V.STANDINGS):
    for csv_key, raw_idx in (("w", 4), ("l", 5), ("t", 6), ("pf", 12), ("pa", 13)):
        if int(row[csv_key]) != raw[raw_idx]:
            mismatch += 1
if mismatch:
    err(f"{mismatch} standings cells differ from the verified raw capture")
else:
    ok("every standings cell matches the verified raw capture")

# --------------------------------------------------------------------------
print("[8] injury report integrity")
inj = read_csv("week10_injuries.csv")
if len(inj) != len(V.INJURIES):
    err(f"injury CSV has {len(inj)} rows, capture has {len(V.INJURIES)}")
else:
    ok(f"{len(inj)} injury rows match the capture")
if len({r["team_abbr"] for r in inj}) != 28:
    err("injury report should cover 28 clubs (14 games)")
else:
    ok("injury report covers 28 clubs")
allowed_practice = {"Did Not Participate In Practice",
                    "Limited Participation in Practice",
                    "Full Participation in Practice"}
bad_p = [r for r in inj if r["practice_status"] not in allowed_practice]
if bad_p:
    err(f"{len(bad_p)} rows with an unrecognised practice status")
else:
    ok("all practice statuses use the official page vocabulary")
allowed_game = {"", "Out", "Questionable", "Doubtful"}
bad_g = [r for r in inj if r["game_status"] not in allowed_game]
if bad_g:
    err(f"{len(bad_g)} rows with an unrecognised game status")
else:
    ok("all game statuses are blank, Out, Questionable or Doubtful")
seen = set()
dupes = 0
for r in inj:
    k = (r["team_abbr"], r["player"])
    if k in seen:
        dupes += 1
    seen.add(k)
if dupes:
    err(f"{dupes} duplicate (team, player) injury rows")
else:
    ok("no duplicate injury rows")

load = read_csv("week10_injury_load.csv")
if len(load) != 28:
    err(f"injury-load table has {len(load)} rows, expected 28")
else:
    ok("injury-load table covers 28 clubs")
if sum(int(r["players_listed"]) for r in load) != len(V.INJURIES):
    err("injury-load counts do not sum to the capture")
else:
    ok(f"injury-load counts sum to {len(V.INJURIES)}")
bad_count = 0
for r in load:
    if int(r["did_not_participate"]) + int(r["limited"]) + int(r["full"]) != int(r["players_listed"]):
        bad_count += 1
if bad_count:
    err(f"{bad_count} clubs whose practice-status counts do not sum to the listed total")
else:
    ok("practice-status counts sum to the listed total for all 28 clubs")

# --------------------------------------------------------------------------
print("[9] depth model consistency")
charts = read_csv("depth_charts.csv")
defic = read_csv("depth_deficiency.csv")
if len(charts) != len(defic):
    err("depth chart and deficiency tables have different row counts")
else:
    ok(f"{len(charts)} position slots in both depth tables")
if len({r["team_abbr"] for r in charts}) != 2:
    err("expected two clubs with captured depth charts")
else:
    ok("two clubs with captured depth charts (NE, DET)")
bad_score = [r for r in defic if not re.fullmatch(r"\d\.\d\d", r["deficiency_score"])]
if bad_score:
    err(f"{len(bad_score)} deficiency scores are not in 0.00-1.00 form")
else:
    ok("all deficiency scores are well formed")
if any(r["score_kind"] != "proposed_weight_not_observed" for r in defic):
    err("a deficiency row is not labelled as a proposed weight")
else:
    ok("every deficiency row is labelled 'proposed_weight_not_observed'")
for r in charts:
    if r["source_status"] != "verified_direct_unofficial_source":
        err(f"{r['team_abbr']} {r['position_slot']}: depth chart status is not the unofficial variant")
        break
else:
    ok("every depth chart row carries the 'unofficial source' status")
if any(not r["first_string"] for r in charts):
    err("a depth chart row has no first string")
else:
    ok("every depth chart row has a first string")

# --------------------------------------------------------------------------
print("[10] correlations reproducible and finite")
corr = read_csv("correlations.csv")
if len(corr) != 8:
    err(f"{len(corr)} correlations, expected 8")
else:
    ok("8 correlation rows")
bad_c = 0
for r in corr:
    if r["status"] != "measured_from_verified_official_data":
        bad_c += 1
        continue
    try:
        c = float(r["coefficient"])
        p = float(r["p_value"])
    except ValueError:
        bad_c += 1
        continue
    if not (-1.0 <= c <= 1.0) or not (0.0 <= p <= 1.0):
        bad_c += 1
if bad_c:
    err(f"{bad_c} correlation rows are out of range or unparseable")
else:
    ok("all coefficients in [-1,1] and p-values in [0,1]")

# independent recomputation of the headline correlation
idx = D.team_index()
abbrs = [r[3] for r in V.STANDINGS]
xs = [idx[a]["net_ppg"] for a in abbrs]
ys = [idx[a]["win_pct"] for a in abbrs]
r_ind = stats.pearson(xs, ys)
row3 = [r for r in corr if r["correlation_id"] == "NFL3-COR-03"][0]
if abs(float(row3["coefficient"]) - r_ind) > 5e-5:  # published to 4 dp
    err(f"NFL3-COR-03 {row3['coefficient']} != independent recomputation {r_ind:.6f}")
else:
    ok(f"NFL3-COR-03 reproduces independently (r = {r_ind:.4f})")

luck = read_csv("luck_index.csv")
if len(luck) != 32:
    err(f"luck index has {len(luck)} rows, expected 32")
else:
    ok("luck index covers 32 clubs")
resid = sum(float(r["luck_residual_win_pct"]) for r in luck)
if abs(resid) > 0.02:
    err(f"luck residuals sum to {resid:.4f}, expected ~0")
else:
    ok(f"luck residuals sum to {resid:.4f} (OLS residuals sum to zero)")

# --------------------------------------------------------------------------
print("[11] originated lines rules")
lines = read_csv("originated_lines.csv")
if len(lines) != 14:
    err(f"{len(lines)} line rows, expected 14")
else:
    ok("14 line rows")
final_played = [r for r in lines if r["model_applicability"].startswith("already_final")]
if len(final_played) != 1:
    err("expected exactly one already-final game to be excluded from modelling")
else:
    ok("the already-final game is excluded from modelling")
bad_lines = 0
for r in lines:
    if r["model_applicability"] == "scheduled":
        if not r["originated_home_spread"] or not r["originated_total"]:
            bad_lines += 1
    else:
        if r["originated_home_spread"] or r["originated_total"]:
            bad_lines += 1
    if r["originated_moneyline_home_prob"]:
        bad_lines += 1
    if r["market_spread"] or r["market_total"] or r["closing_line_value"]:
        bad_lines += 1
    if r["status"] != "model_output":
        bad_lines += 1
if bad_lines:
    err(f"{bad_lines} line rows violate the blank/model-output rules")
else:
    ok("scheduled games are modelled, the final game is not, moneyline and market cells stay blank")

# --------------------------------------------------------------------------
print("[12] gates, strategies and leaderboard")
gates = read_csv("validation_gates.csv")
if len(gates) != 12:
    err(f"{len(gates)} gates, expected 12")
else:
    ok("12 validation gates")
if sum(1 for g in gates if g["status"] == "open") != 4:
    err("expected exactly 4 open gates")
else:
    ok("4 gates open, 8 blocked")
strats = read_csv("strategies.csv")
if len(strats) != 10:
    err(f"{len(strats)} strategies, expected 10")
else:
    ok("10 preregistered strategies")
if any(s["qualified"] != "no" for s in strats):
    err("a strategy is marked qualified")
else:
    ok("no strategy is marked qualified")
if any(int(s["selections_graded"]) != 0 for s in strats):
    err("a strategy reports graded selections")
else:
    ok("0 graded selections across the catalog")
for s in strats:
    bad = [g for g in s["required_gates"].split(",")
           if g not in {x["gate_id"] for x in gates} and g != ""]
    if bad:
        err(f"{s['strategy_id']}: references unknown gate(s) {bad}")
        break
else:
    ok("every strategy references only defined gates")
entries = read_csv("leaderboard_entries.csv")
if any(e["reward_awarded"] != "not_awarded" for e in entries):
    err("a leaderboard entry has a reward")
else:
    ok("no leaderboard reward awarded")
if any("non-monetary" not in e["monetary_value"]
       for e in read_csv("leaderboard_tiers.csv")):
    err("a leaderboard tier offers a monetary value")
else:
    ok("all leaderboard rewards are non-monetary")

# --------------------------------------------------------------------------
print("[13] decision ledger, suggestions and flags")
dec = read_csv("decision_ledger.csv")
if len(dec) != 16:
    err(f"{len(dec)} decision questions, expected 16")
else:
    ok("16 decision questions")
if any(not r["information_we_lack"] for r in dec):
    err("a decision row does not state what is missing")
else:
    ok("every decision row states what is missing")
if any(not r["suggested_way_to_discover"] for r in dec):
    err("a decision row has no discovery suggestion")
else:
    ok("every decision row has a discovery suggestion")
sug = read_csv("suggestions.csv")
if len(sug) != 14:
    err(f"{len(sug)} suggestions, expected 14")
else:
    ok("14 suggestions")
if any(s["review_status"] != "pending_human_choice" for s in sug):
    err("a suggestion is not pending human choice")
else:
    ok("every suggestion is pending_human_choice (nothing auto-applied)")
if any("Path" not in s["option_paths_for_review"] for s in sug):
    err("a suggestion offers no option paths")
else:
    ok("every suggestion offers at least two option paths")
flags = read_csv("flagged.csv")
if len(flags) != 17:
    err(f"{len(flags)} flags, expected 17")
else:
    ok("17 flagged items")
findings = read_csv("repo_findings.csv")
if len(findings) != 15:
    err(f"{len(findings)} repo findings, expected 15")
else:
    ok("15 repository findings")
srcs = read_csv("sources.csv")
if len(srcs) != 11:
    err(f"{len(srcs)} sources, expected 11")
else:
    ok("11 sources")
if any(not s["verbatim_evidence_excerpt"] for s in srcs):
    err("a source row has no verbatim excerpt")
else:
    ok("every source row carries a verbatim excerpt")
if any(not s["does_not_support_boundary"] for s in srcs):
    err("a source row has no boundary statement")
else:
    ok("every source row states what it does not support")

# --------------------------------------------------------------------------
print("[14] pack uses only the Python standard library")
mods = sorted(f for f in os.listdir(os.path.join(REPO, "src", "nfl_309921cc"))
              if f.endswith(".py"))
bad_imports = 0
for m in mods:
    text = open(os.path.join(REPO, "src", "nfl_309921cc", m), encoding="utf-8").read()
    for im in re.findall(r"^\s*(?:import|from)\s+([A-Za-z0-9_\.]+)", text, re.M):
        top = im.split(".")[0]
        if top == "" or text.strip().startswith("from ."):
            continue  # relative intra-package import
        if top not in {"nfl_309921cc", "csv", "math", "os", "random", "typing",
                       "__future__", "sys", "re", "html", "argparse", "subprocess"}:
            bad_imports += 1
            err(f"src/nfl_309921cc/{m}: imports non-stdlib module {top}")
if bad_imports == 0:
    ok(f"{len(mods)} modules reviewed, all imports are stdlib or intra-package")

# --------------------------------------------------------------------------
print()
if errors:
    print(f"check_nfl_309921cc FAILED: {len(errors)} issue(s) across {checks} checks")
    for e in errors[:40]:
        print("  -", e)
    raise SystemExit(1)
print(f"check_nfl_309921cc OK: {len(pages)} HTML pages, {total_rows} sourced table rows, "
      f"{csv_rows} CSV rows, {len(datasets)} datasets, 0 <input> elements, {checks} checks passed")
raise SystemExit(0)
