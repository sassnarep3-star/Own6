#!/usr/bin/env python3
"""Strict offline verification, privacy, math, and source-link gate for SF 94122."""
from __future__ import annotations

import csv
import html.parser
import re
import sys
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_sf_94122  # noqa: E402

DATA_DIR = ROOT / "data" / "sf_94122"
DOCS_DIR = ROOT / "docs" / "sf-94122"
EXPECTED_PAGES = {
    "index.html",
    "units.html",
    "corporate-vs-individual.html",
    "notice-and-reasons.html",
    "tenant-scrutiny-and-fairness.html",
    "flagged.html",
}

OFFICIAL_HOSTS = {
    "www.sf.gov",
    "media.api.sf.gov",
    "leginfo.legislature.ca.gov",
    "oag.ca.gov",
    "calcivilrights.ca.gov",
    "codelibrary.amlegal.com",
    "www.justice.gov",
    "www.sec.gov",
    "www.census.gov",
    "www.huduser.gov",
    "github.com",
}

DEAD_URL_SUBSTRINGS = (
    "find-out-if-san-franciscos-rental-law-applies-you",
    "reports/tenant-rights-and-resources",
)

# Strict allowlist of non-personal 2-letter uppercase tokens permitted in deliverables.
ALLOWED_TWO_UPPER = {
    "AB", "AG", "CA", "CI", "DO", "FL", "FY", "ID",
    "IF", "OR", "OS", "PR", "RA", "SF", "TO", "UI",
}

SPACED_INITIALS_RE = re.compile(r"\b[A-Z]\.?\s+[A-Z]\.?\b")
TWO_UPPER_RE = re.compile(r"\b[A-Z]{2}\b")
MERGE_MARKER_RE = re.compile(r"^(?:<{7}(?:\s|$)|={7}$|>{7}(?:\s|$))", re.MULTILINE)


class DashboardHTMLParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.input_count = 0
        self.links: list[str] = []
        self.in_tbody = False
        self.in_row = False
        self.in_empty_cell = False
        self.empty_cell_text: list[str] = []
        self.row_links: list[str] = []
        self.row_badges: list[str] = []
        self.row_empty_cells = 0
        self.in_badge = False
        self.badge_buf: list[str] = []
        self.rows: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag == "h1":
            self.h1_count += 1
        elif tag == "input":
            self.input_count += 1
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key] or "")
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_links = []
            self.row_badges = []
            self.row_empty_cells = 0
        elif self.in_row:
            if tag == "a" and a.get("href"):
                self.row_links.append(a["href"] or "")
            elif tag == "td" and "empty-cell" in cls.split():
                self.in_empty_cell = True
                self.empty_cell_text = []
            elif tag == "span" and "badge" in cls.split():
                self.in_badge = True
                self.badge_buf = []

    def handle_data(self, data: str) -> None:
        if self.in_empty_cell:
            self.empty_cell_text.append(data)
        if self.in_badge:
            self.badge_buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_empty_cell:
            if "".join(self.empty_cell_text) == "":
                self.row_empty_cells += 1
            else:
                self.row_empty_cells = -999  # non-empty unverified cell!
            self.in_empty_cell = False
        elif tag == "span" and self.in_badge:
            self.row_badges.append("".join(self.badge_buf).strip())
            self.in_badge = False
        elif tag == "tr" and self.in_row:
            self.rows.append(
                {
                    "links": list(self.row_links),
                    "badges": list(self.row_badges),
                    "empty_cells": self.row_empty_cells,
                }
            )
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody = False


def check_privacy_text(label: str, text: str) -> list[str]:
    errs: list[str] = []
    for m in SPACED_INITIALS_RE.finditer(text):
        errs.append(f"{label}: prohibited spaced-initial pattern {m.group(0)!r}")
    for m in TWO_UPPER_RE.finditer(text):
        tok = m.group(0)
        if tok not in ALLOWED_TWO_UPPER:
            errs.append(f"{label}: unallowlisted 2-letter uppercase monogram {tok!r}")
    return errs


def run_checks(root: Path = ROOT) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    data_dir = root / "data" / "sf_94122"
    docs_dir = root / "docs" / "sf-94122"

    # 1. Deterministic builder match when checking the real repo root
    if root.resolve() == ROOT.resolve():
        expected_outputs = build_sf_94122.generate_all()
        for name, expected in expected_outputs.items():
            target = docs_dir / name
            if not target.exists() or target.read_text(encoding="utf-8") != expected:
                errors.append(f"docs/sf-94122/{name}: out of sync with build_sf_94122.py")

    # 2. CSV data checks & math recomputation
    csv_files = sorted(data_dir.glob("*.csv"))
    if len(csv_files) < 8:
        errors.append(f"Expected >=8 CSV files in data/sf_94122, found {len(csv_files)}")

    total_csv_rows = 0
    for csv_path in csv_files:
        raw = csv_path.read_text(encoding="utf-8")
        if MERGE_MARKER_RE.search(raw):
            errors.append(f"{csv_path.name}: merge conflict marker")
        errors.extend(check_privacy_text(f"data/sf_94122/{csv_path.name}", raw))
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
                errors.append(f"{csv_path.name}: duplicate or missing CSV headers")
                continue
            for idx, row in enumerate(reader, 2):
                total_csv_rows += 1
                st = row.get("verification_status", "")
                val = row.get("verified_value", "")
                url = row.get("official_source_url", "")
                if st not in {"verified", "unverified"}:
                    errors.append(f"{csv_path.name}:{idx}: invalid verification_status={st!r}")
                if st == "unverified" and val != "":
                    errors.append(f"{csv_path.name}:{idx}: unverified row has non-blank verified_value={val!r}")
                if st == "verified" and val.strip() == "":
                    errors.append(f"{csv_path.name}:{idx}: verified row has blank verified_value")
                parsed = urlparse(url)
                if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
                    errors.append(f"{csv_path.name}:{idx}: non-official or non-HTTPS source {url!r}")
                if any(dead in url for dead in DEAD_URL_SUBSTRINGS):
                    errors.append(f"{csv_path.name}:{idx}: dead HTTP-404 URL {url!r}")

    # Verify exact Decimal math on scenarios CSV
    scen_path = data_dir / "unit_increase_scenarios.csv"
    if scen_path.exists():
        with scen_path.open(newline="", encoding="utf-8") as fh:
            scen_rows = list(csv.DictReader(fh))
        expected_pairs = {
            "S-04": (Decimal("3995.00"), Decimal("1.6"), Decimal("63.92"), Decimal("4058.92")),
            "S-05": (Decimal("3995.00"), Decimal("1.6"), Decimal("63.92"), Decimal("4058.92")),
            "S-06": (Decimal("3995.00"), Decimal("3.0"), Decimal("119.85"), Decimal("4114.85")),
            "S-08": (Decimal("3150.00"), Decimal("1.6"), Decimal("50.40"), Decimal("3200.40")),
            "S-09": (Decimal("3150.00"), Decimal("5.0"), Decimal("157.50"), Decimal("3307.50")),
            "S-10": (Decimal("3150.00"), Decimal("10.0"), Decimal("315.00"), Decimal("3465.00")),
            "S-11": (Decimal("3150.00"), Decimal("13.1"), Decimal("412.65"), Decimal("3562.65")),
        }
        seen = {r["id"]: r for r in scen_rows}
        for sid, (ebase, epct, einc, enew) in expected_pairs.items():
            if sid not in seen:
                errors.append(f"unit_increase_scenarios.csv: missing scenario {sid}")
                continue
            r = seen[sid]
            inc = (Decimal(r["base_rent_usd"]) * Decimal(r["rate_pct"].rstrip("%"))) / Decimal("100")
            if Decimal(r["base_rent_usd"]) != ebase or Decimal(r["rate_pct"].rstrip("%")) != epct or inc != einc or Decimal(r["monthly_increase_usd"]) != einc or Decimal(r["new_monthly_rent_usd"]) != enew:
                errors.append(f"unit_increase_scenarios.csv:{sid}: math mismatch")

    # 3. HTML page checks
    html_pages = sorted(docs_dir.glob("*.html"))
    if {p.name for p in html_pages} != EXPECTED_PAGES:
        errors.append(f"Expected HTML pages {sorted(EXPECTED_PAGES)}, found {[p.name for p in html_pages]}")
    if not (docs_dir / "styles.css").is_file():
        errors.append("docs/sf-94122/styles.css missing")

    total_html_rows = 0
    for page in html_pages:
        text = page.read_text(encoding="utf-8")
        rel = f"docs/sf-94122/{page.name}"
        if MERGE_MARKER_RE.search(text):
            errors.append(f"{rel}: merge conflict marker")
        if "<generator object" in text or "Math.erf(" in text:
            errors.append(f"{rel}: forbidden generator/JS construct")
        errors.extend(check_privacy_text(rel, text))

        p = DashboardHTMLParser()
        p.feed(text)
        if p.h1_count != 1:
            errors.append(f"{rel}: expected 1 <h1>, found {p.h1_count}")
        if p.input_count != 0:
            errors.append(f"{rel}: <input> elements not allowed ({p.input_count})")
        if not p.rows:
            errors.append(f"{rel}: no <tbody><tr> data rows found")

        for link in p.links:
            if any(dead in link for dead in DEAD_URL_SUBSTRINGS):
                errors.append(f"{rel}: active link uses HTTP-404 URL {link}")
            u = urlparse(link)
            if u.scheme:
                if u.scheme != "https" or u.hostname not in OFFICIAL_HOSTS:
                    errors.append(f"{rel}: external link not on verified HTTPS official host: {link}")
            else:
                if link.startswith(("//", "/")):
                    errors.append(f"{rel}: non-relative link {link}")
                    continue
                target_path = unquote(u.path)
                if target_path and not (page.parent / target_path).resolve().is_file():
                    errors.append(f"{rel}: broken relative link {link}")

        for idx, rinfo in enumerate(p.rows, 1):
            total_html_rows += 1
            official_row_links = [
                lnk for lnk in rinfo["links"]
                if urlparse(lnk).scheme == "https" and urlparse(lnk).hostname in OFFICIAL_HOSTS
            ]
            if not official_row_links:
                errors.append(f"{rel}: table row {idx} lacks an official HTTPS source link")
            if "unverified" in rinfo["badges"] and rinfo["empty_cells"] <= 0:
                errors.append(f"{rel}: unverified table row {idx} does not leave its value cell blank")

    # 4. Markdown deliverables privacy & dead-URL scan
    for md_rel in ("research/SF_94122_EXECUTIVE_SUMMARY.md", "audit/SF_94122_REPO_AND_SOURCE_AUDIT.md"):
        md_path = root / md_rel
        if not md_path.is_file():
            errors.append(f"{md_rel}: missing required report")
            continue
        md_text = md_path.read_text(encoding="utf-8")
        if MERGE_MARKER_RE.search(md_text):
            errors.append(f"{md_rel}: merge conflict marker")
        errors.extend(check_privacy_text(md_rel, md_text))
        for m in re.finditer(r"\[[^\]]+\]\((https?://[^)]+)\)", md_text):
            murl = m.group(1)
            if any(dead in murl for dead in DEAD_URL_SUBSTRINGS):
                errors.append(f"{md_rel}: markdown link points to HTTP-404 URL {murl}")

    # Confirm anonymized placeholders appear in baseline CSV
    base_txt = (data_dir / "property_units_baseline.csv").read_text(encoding="utf-8") if (data_dir / "property_units_baseline.csv").exists() else ""
    for placeholder in ("Tenant 1A", "Tenant 1B", "Tenant 1C", "Tenant 1D", "Tenant 2A", "Tenant 2B"):
        if placeholder not in base_txt:
            errors.append(f"property_units_baseline.csv: missing anonymized placeholder {placeholder}")

    stats = {
        "csv_files": len(csv_files),
        "csv_rows": total_csv_rows,
        "html_pages": len(html_pages),
        "html_rows": total_html_rows,
    }
    return errors, stats


def main() -> int:
    errors, stats = run_checks(ROOT)
    if errors:
        print(f"SF 94122 CHECK FAILED ({len(errors)} error(s)):")
        for err in errors:
            print(f" - {err}")
        return 1
    print(
        f"SF 94122 OK: {stats['html_pages']} HTML pages ({stats['html_rows']} sourced rows), "
        f"{stats['csv_files']} CSV files ({stats['csv_rows']} rows), zero PII/initials, "
        f"blank unverified cells, and exact Decimal math verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
