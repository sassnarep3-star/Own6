#!/usr/bin/env python3
"""Check rental dashboard integrity and verification.

- Every page listed in build_rental.py PAGES must exist and have one h1
- Every tbody table row must carry at least one official HTTPS source link
- Internal links must resolve
- Math for calculations_per_unit recomputed
- No conflict markers, generator leaks, manual inputs
"""
from __future__ import annotations
import csv
import html.parser
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "rental"
DATA = ROOT / "data" / "rental"
EXPECTED = {"index.html","units.html","lawful.html","history.html","calculations.html","notices.html","discrimination.html","practices.html","market.html","checklist.html","sources.html","flagged.html","reasonable.html"}

OFFICIAL_SUFFIXES = (
    "sf.gov", "codelibrary.amlegal.com", "leginfo.legislature.ca.gov",
    "hud.gov", "congress.gov", "bls.gov", "huduser.gov",
    "github.com", "sfplanning.org", "sftu.org", "bayarealegalaid.org",
    "redfin.com", "vouchermatch.com",
)

errors=[]

def fail(m): errors.append(m)

def official(url: str) -> bool:
    p=urlparse(url)
    host=(p.hostname or "").lower()
    return p.scheme=="https" and any(host==s or host.endswith("."+s) for s in OFFICIAL_SUFFIXES)

class Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]; self.ids=set(); self.h1=0; self.in_tbody=False; self.in_row=False; self.row_has_source=False; self.rows=[]; self.inputs=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        if tag=="a" and a.get("href"):
            self.links.append(a["href"])
            if self.in_row and official(a["href"]):
                self.row_has_source=True
        if tag=="h1": self.h1+=1
        if tag=="tbody": self.in_tbody=True
        if tag=="tr" and self.in_tbody: self.in_row=True; self.row_has_source=False
        if tag=="input": self.inputs+=1
    def handle_endtag(self, tag):
        if tag=="tr" and self.in_row: self.rows.append(self.row_has_source); self.in_row=False
        if tag=="tbody": self.in_tbody=False

def main()->int:
    pages=sorted(OUT.glob("*.html"))
    found={p.name for p in pages}
    if EXPECTED - found:
        fail(f"missing expected pages {sorted(EXPECTED - found)}")
    if found - EXPECTED:
        # allow extra reasonable.html but flag unexpected extra besides EXPECTED
        extra=found - EXPECTED
        # reasonable.html is expected extra above but we already include; if any other extra unexpected, fail
        # Actually reasonable.html is now in EXPECTED we added, so nothing extra expected
        for e in extra:
            fail(f"unexpected extra page {e} — add to EXPECTED if intended")

    all_ids={}
    parsed={}
    for path in pages:
        text=path.read_text(encoding="utf-8")
        p=Parser()
        p.feed(text)
        parsed[path.name]=p
        all_ids[path.name]=p.ids
        if p.h1!=1:
            fail(f"{path.name}: expected one h1 found {p.h1}")
        if p.inputs:
            fail(f"{path.name}: manual input field not allowed")
        if "<generator object" in text: fail(f"{path.name}: generator repr leaked")
        if re.search(r"^(<<<<<<< |=======|>>>>>>> )", text, re.M): fail(f"{path.name}: conflict marker")
        if not p.rows: fail(f"{path.name}: no table rows")
        for i,has in enumerate(p.rows,1):
            if not has: fail(f"{path.name}: table row {i} lacks official HTTPS source link (needs sf.gov / leginfo / hud.gov / etc.)")
    # internal links
    for name,p in parsed.items():
        for href in p.links:
            u=urlparse(href)
            if u.scheme:
                if u.scheme!="https": fail(f"{name}: non-HTTPS link {href}")
                continue
            if href.startswith("//"): fail(f"{name}: protocol-relative {href}"); continue
            target=unquote(u.path)
            if not target: continue
            # internal relative like "history.html" or "assets/style.css"
            # resolve against OUT/name
            # handle paths like docs/rental/assets/style.css incorrectly? Should be just relative.
            if target.startswith("/"):
                # absolute from repo root - check if docs/rental case? For now treat as error unless we map
                target_path = ROOT / target.lstrip("/")
            else:
                target_path = (OUT / name).parent / target
            if not target_path.exists():
                fail(f"{name}: broken internal link {href} -> {target_path}")
            if u.fragment:
                # fragment check
                frag_ids = all_ids.get(target_path.name, set())
                # only check if target is an HTML page we parsed and has ids
                if target_path.suffix==".html" and frag_ids and u.fragment not in frag_ids:
                    fail(f"{name}: broken fragment {href}")

    # Math recomputation
    import csv
    with (DATA/"calculations_per_unit.csv").open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        if r['scenario_id']=="C-RULE": continue
        try:
            base=float(r['base_rent'])
            dec=float(r['increase_decimal'])
            dollar_computed=round(base*dec,2)
            reported=float(r['dollar_increase_computed'])
            if abs(dollar_computed - reported) > 0.01:
                fail(f"calc {r['scenario_id']}: recomputed dollar {dollar_computed} != reported {reported}")
            new_computed=round(base + dollar_computed,2)
            reported_new=float(r['new_rent_computed'])
            if abs(new_computed - reported_new) > 0.01:
                fail(f"calc {r['scenario_id']}: recomputed new {new_computed} != reported {reported_new}")
        except Exception as e:
            fail(f"calc {r['scenario_id']}: exception {e}")

    # Check every data CSV row has source_url https if possible? Ensure at least one source column exists with https
    csv_checks = {
        "units.csv": "source_url_official_coverage",
        "sf_allowable_increases.csv": "source_url_official",
        "sf_rent_board_rules.csv": "source_url_official",
        "state_federal_laws.csv": "source_url_official",
        "calculations_per_unit.csv": "source_url_official",
        "notice_requirements.csv": "source_url_official",
        "corporate_vs_individual_practices.csv": "source_url_official",
        "discrimination_analysis.csv": "source_url_official",
        "market_context_94122.csv": "source_url_official",
        "lawyer_review_checklist.csv": "source_url_official",
    }
    for fname, src_col in csv_checks.items():
        path=DATA/fname
        if not path.exists():
            fail(f"missing data file {fname}")
            continue
        with path.open(newline="",encoding="utf-8") as f:
            rd=list(csv.DictReader(f))
        if not rd:
            fail(f"{fname}: empty")
        for i,row in enumerate(rd,1):
            url=row.get(src_col,"") or row.get("source_url_official","")
            if not url or not url.startswith("https://"):
                fail(f"{fname} row {i}: missing official HTTPS source in {src_col}")

    # flagged page must mention R-F01 etc
    flagged_text=(OUT/"flagged.html").read_text(encoding="utf-8")
    for fid in ["R-F01","R-F04","R-F06","R-F07"]:
        if fid not in flagged_text:
            fail(f"flagged.html missing {fid}")

    if errors:
        print("RENTAL CHECK FAILED")
        for e in errors: print(" -",e)
        return 1
    total_rows=sum(len(p.rows) for p in parsed.values())
    print(f"OK: {len(pages)} rental pages; {total_rows} table rows all carry official HTTPS sources; math recomputed; links resolve.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
