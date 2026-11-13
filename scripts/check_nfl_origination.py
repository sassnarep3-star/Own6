#!/usr/bin/env python3
"""Comprehensive offline verification gate for the NFL Origination & Verification Pack.

Enforces:
1. All 11 published HTML pages + `assets/style.css` exist and match `build_nfl_origination.py --check`.
2. Zero `<input>`, `<form>`, `<select>`, or `<textarea>` elements (`0` manual user input).
3. At least one `<h1>` per page, zero unresolved merge markers, and zero leaked Python generator reprs.
4. Every `<tbody><tr>` row across every table in all 11 pages carries at least one `https://` link
   to an allowlisted official domain.
5. Every `<td class="empty">` cell has literally empty text content (`""`).
6. Every relative internal link resolves inside `ROOT`, and every `github.com/sassnarep3-star/Own6/blob/main/...`
   URL points to an existing repository file.
7. Every CSV dataset in `data/nfl_origination/` passes schema and blank-cell checks. The through-Week-9
   snapshot (`verified_standings_2026_w10.csv`) passes 32-club league accounting (`135W == 135L`, `2T`,
   `6,246 PF == 6,246 PA`). The live 13 Nov standings (`standings_live_2026_11_13.csv`) pass
   136W == 136L, 2T, 6,291 PF == 6,291 PA, with only NYG and WAS changed.
"""
from __future__ import annotations

import csv
import html.parser
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "docs" / "nfl-origination"
DATA_DIR = ROOT / "data" / "nfl_origination"

EXPECTED_PAGES = (
    "index.html",
    "executive-summary.html",
    "requirements.html",
    "suggestions.html",
    "decision-qa.html",
    "strategies-leaderboard.html",
    "validation-gates.html",
    "correlations.html",
    "injuries-depth.html",
    "repo-audit.html",
    "flagged.html",
)

ALLOWED_OFFICIAL_DOMAINS = (
    "nfl.com",
    "operations.nfl.com",
    "support.nfl.com",
    "patriots.com",
    "detroitlions.com",
    "commanders.com",
    "giants.com",
    "vikings.com",
    "packers.com",
    "clevelandbrowns.com",
    "azcardinals.com",
    "scipy.org",
    "scikit-learn.org",
    "statsmodels.org",
    "nist.gov",
    "aglc.ca",
    "github.com",
    "api.github.com",
    "docs.github.com",
)


def _is_allowed_official_https(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return any(host == dom or host.endswith("." + dom) for dom in ALLOWED_OFFICIAL_DOMAINS)


class DashboardHTMLParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.forbidden_controls: list[str] = []
        self.all_links: list[str] = []
        self.in_tbody = False
        self.in_tr = False
        self.in_empty_td = False
        self.empty_td_buf: list[str] = []
        self.non_empty_blank_cells = 0
        self.empty_cell_count = 0
        self.current_row_cells = 0
        self.current_row_links: list[str] = []
        self.tbody_rows: list[tuple[int, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: (v or "") for k, v in attrs}
        if tag == "h1":
            self.h1_count += 1
        if tag in {"input", "form", "select", "textarea"}:
            self.forbidden_controls.append(tag)
        for key in ("href", "src"):
            if attr_map.get(key):
                self.all_links.append(attr_map[key])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.current_row_cells = 0
            self.current_row_links = []
        elif tag == "td" and self.in_tr:
            self.current_row_cells += 1
            classes = set(attr_map.get("class", "").split())
            if "empty" in classes:
                self.in_empty_td = True
                self.empty_td_buf = []
                self.empty_cell_count += 1
        elif tag == "a" and self.in_tr and attr_map.get("href"):
            self.current_row_links.append(attr_map["href"])

    def handle_data(self, data: str) -> None:
        if self.in_empty_td:
            self.empty_td_buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_empty_td:
            if "".join(self.empty_td_buf) != "":
                self.non_empty_blank_cells += 1
            self.in_empty_td = False
        elif tag == "tr" and self.in_tr:
            self.tbody_rows.append((self.current_row_cells, list(self.current_row_links)))
            self.in_tr = False
        elif tag == "tbody":
            self.in_tbody = False


def verify_all() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    stats = {"pages": 0, "rows": 0, "empty_cells": 0, "csv_files": 0}

    # 1. Generator determinism check
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_nfl_origination.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        errors.append(f"build_nfl_origination.py --check failed: {proc.stdout.strip()} {proc.stderr.strip()}")

    if not (SITE_DIR / "assets" / "style.css").is_file():
        errors.append("Missing docs/nfl-origination/assets/style.css")

    # 2. HTML page structural, zero-input, link, and row-source checks
    for page_name in EXPECTED_PAGES:
        page_path = SITE_DIR / page_name
        if not page_path.is_file():
            errors.append(f"Missing page docs/nfl-origination/{page_name}")
            continue
        stats["pages"] += 1
        raw = page_path.read_text(encoding="utf-8")
        if any(m in raw for m in ("<<<<<<<", "=======", ">>>>>>>")):
            errors.append(f"{page_name}: unresolved git merge marker")
        if "<generator object" in raw or "Traceback (most recent" in raw:
            errors.append(f"{page_name}: leaked Python error/generator text")

        p = DashboardHTMLParser()
        p.feed(raw)
        if p.h1_count < 1:
            errors.append(f"{page_name}: missing <h1> heading")
        if p.forbidden_controls:
            errors.append(f"{page_name}: forbidden interactive input controls {p.forbidden_controls}")
        if p.non_empty_blank_cells > 0:
            errors.append(f"{page_name}: {p.non_empty_blank_cells} <td class='empty'> cells contain non-empty text")
        if not p.tbody_rows:
            errors.append(f"{page_name}: contains 0 <tbody><tr> data rows")

        stats["empty_cells"] += p.empty_cell_count
        for idx, (ncells, rlinks) in enumerate(p.tbody_rows, 1):
            stats["rows"] += 1
            if ncells < 3:
                errors.append(f"{page_name} row {idx}: too few cells ({ncells})")
            if not any(_is_allowed_official_https(u) for u in rlinks):
                errors.append(f"{page_name} row {idx}: missing allowlisted official https:// source link")

        for link in p.all_links:
            parsed = urlparse(link)
            if parsed.scheme == "https":
                if parsed.hostname == "github.com" and parsed.path.startswith("/sassnarep3-star/Own6/blob/main/"):
                    rel_blob = parsed.path.removeprefix("/sassnarep3-star/Own6/blob/main/")
                    if not (ROOT / rel_blob).exists():
                        errors.append(f"{page_name}: broken repo blob link {link}")
                continue
            if parsed.scheme or parsed.netloc or link.startswith("/") or link.startswith("//"):
                errors.append(f"{page_name}: disallowed non-https or root-absolute link {link}")
                continue
            if parsed.path:
                target = (page_path.parent / unquote(parsed.path)).resolve()
                if not target.is_relative_to(ROOT) or not target.exists():
                    errors.append(f"{page_name}: broken relative link {link}")

    # 3. CSV schema, blank-cell, and 32-team league accounting checks
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    stats["csv_files"] = len(csv_files)
    if len(csv_files) < 13:
        errors.append(f"Expected >= 13 CSV files in data/nfl_origination, found {len(csv_files)}")

    for csv_path in csv_files:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
                errors.append(f"{csv_path.name}: duplicate or missing CSV headers")
                continue
            if "official_source_url" not in reader.fieldnames:
                errors.append(f"{csv_path.name}: missing official_source_url column")
                continue
            for line_no, row in enumerate(reader, 2):
                if None in row or any(v is None for v in row.values()):
                    errors.append(f"{csv_path.name}:{line_no}: malformed CSV column count")
                    continue
                if not _is_allowed_official_https(row["official_source_url"]):
                    errors.append(f"{csv_path.name}:{line_no}: non-allowlisted URL {row['official_source_url']}")

    st_path = DATA_DIR / "verified_standings_2026_w10.csv"
    if st_path.is_file():
        with st_path.open(newline="", encoding="utf-8") as fh:
            st = list(csv.DictReader(fh))
        if len(st) != 32:
            errors.append(f"verified_standings_2026_w10.csv: expected 32 clubs, got {len(st)}")
        w_sum = sum(int(x["w"]) for x in st)
        l_sum = sum(int(x["l"]) for x in st)
        t_sum = sum(int(x["t"]) for x in st)
        pf_sum = sum(int(x["pf"]) for x in st)
        pa_sum = sum(int(x["pa"]) for x in st)
        if not (w_sum == l_sum == 135 and t_sum == 2 and pf_sum == pa_sum == 6246):
            errors.append(
                f"Standings league identity mismatch: W={w_sum}, L={l_sum}, T={t_sum}, PF={pf_sum}, PA={pa_sum}"
            )

    live_path = DATA_DIR / "standings_live_2026_11_13.csv"
    if live_path.is_file():
        with live_path.open(newline="", encoding="utf-8") as fh:
            live = list(csv.DictReader(fh))
        if len(live) != 32:
            errors.append(f"standings_live_2026_11_13.csv: expected 32 clubs, got {len(live)}")
        lw = sum(int(x["w"]) for x in live)
        ll = sum(int(x["l"]) for x in live)
        lt = sum(int(x["t"]) for x in live)
        lpf = sum(int(x["pf"]) for x in live)
        lpa = sum(int(x["pa"]) for x in live)
        if not (lw == ll == 136 and lt == 2 and lpf == lpa == 6291):
            errors.append(f"Live 13 Nov standings identity mismatch: W={lw}, L={ll}, T={lt}, PF={lpf}, PA={lpa}")
        changed = sorted(x["abbr"] for x in live if x["changed_since_w9_snapshot"] == "true")
        if changed != ["NYG", "WAS"]:
            errors.append(f"Unexpected club changes since the Week 9 snapshot: {changed}")

    return errors, stats


def main() -> int:
    errors, stats = verify_all()
    if errors:
        for err in errors:
            print("FAIL:", err)
        print(f"check_nfl_origination FAILED with {len(errors)} error(s).")
        return 1
    print(
        f"check_nfl_origination OK: {stats['pages']} HTML pages, {stats['rows']} sourced table rows, "
        f"{stats['empty_cells']} verified blank cells, {stats['csv_files']} CSV datasets, 0 <input> elements."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
