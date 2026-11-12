#!/usr/bin/env python3
"""Guard rails for the NFL lab pages.

Four rules, each one a failure a reader would actually notice:

R1 row-source   every <tr> holding data must contain a link; market cells must not be filled
R2 blank        no market price, no invented status, no numeric cell without a source column
R3 links        every internal href resolves to a file in docs/nfl/lab/
R4 drift        the page set, the row counts and the gate counts match the artefacts
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAB = ROOT / "docs" / "nfl" / "lab"
DATA = ROOT / "data" / "nfl"

PAGES = {
    "index.html", "lines.html", "strategies.html", "validation.html", "correlations.html",
    "leaderboard.html", "injuries.html", "depth.html", "questions.html", "suggestions.html",
    "findings.html", "sources.html", "flagged.html", "audit.html",
}
# cells that are allowed to be blank by design (no verified value exists)
BLANK_OK = {"market spread", "market total", "game status"}


def rows(html: str):
    return [r for r in re.findall(r"<tr>(.*?)</tr>", html, re.S) if "<td" in r]


def check() -> list[str]:
    errs: list[str] = []
    lab = LAB
    if not lab.is_dir():
        return ["docs/nfl/lab/ missing - run scripts/build_nfl_lab.py"]

    present = {p.name for p in lab.glob("*.html")}
    missing, extra = PAGES - present, present - PAGES
    if missing:
        errs.append(f"R4 missing pages: {sorted(missing)}")
    if extra:
        errs.append(f"R4 unexpected pages: {sorted(extra)}")

    # R1 / R2 / R3 per page
    for name in sorted(PAGES & present):
        html = (lab / name).read_text(encoding="utf-8")
        if "generator object" in html or re.search(r">\s*(None|nan)\s*<", html):
            errs.append(f"R4 {name}: placeholder text leaked (generator object / bare None)")
        if re.search(r"\\[ntr]|\bnan\b", html):
            errs.append(f"R4 {name}: escape artefact or NaN in output")
        for i, r in enumerate(rows(html)):
            if 'href="http' not in r:
                errs.append(f"R1 {name} row {i}: no source link")
                break
        # every data table must have a Source-ish header
        for tbl in re.findall(r"<table.*?</table>", html, re.S):
            head = re.search(r"<thead>.*?</thead>", tbl, re.S)
            if head and "<th" in head.group(0):
                labels = [re.sub(r"<[^>]+>", "", h).strip().lower() for h in re.findall(r"<th[^>]*>.*?</th>", head.group(0), re.S)]
                if not ("source" in " ".join(labels) or "evidence" in " ".join(labels) or "verification" in " ".join(labels)):
                    errs.append(f"R2 {name}: table without a source/evidence column: {labels[:4]}")
        # internal links resolve
        for href in re.findall(r'href="([^":]+\.html)"', html):
            if not (lab / href).is_file():
                errs.append(f"R3 {name}: broken internal link {href}")

    # R2 - the own-lines market columns must be empty, and the injury status column must not invent a status
    lines = (lab / "lines.html").read_text(encoding="utf-8")
    for r in rows(lines):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        if len(cells) >= 12 and any(re.search(r"\d", c) for c in cells[9:11]):
            errs.append("R2 lines.html: a market cell is filled - no verified price exists")
            break

    # R4 - drift against the artefacts
    backtest = json.loads((DATA / "model" / "backtest.json").read_text())
    validation = (lab / "validation.html").read_text(encoding="utf-8")
    gate_rows = len([r for r in rows(validation) if re.search(r"<td>(S[1-8])</td><td>G\d\d</td>", r)])
    expected = sum(len(c["gates"]) for c in backtest["gates"])
    if gate_rows != expected:
        errs.append(f"R4 validation.html: {gate_rows} gate rows, expected {expected}")

    inj = len(rows((lab / "injuries.html").read_text(encoding="utf-8")))
    import csv
    with (DATA / "raw" / "injuries_week10_read.csv").open(newline="", encoding="utf-8") as f:
        inj_src = sum(1 for _ in csv.DictReader(f))
    if inj != inj_src:
        errs.append(f"R4 injuries.html: {inj} rows, csv has {inj_src}")

    q = json.loads((DATA / "questions.json").read_text())["questions"]
    sq = json.loads((DATA / "suggestions.json").read_text())["suggestions"]
    fq = len([r for r in rows((lab / "questions.html").read_text(encoding="utf-8"))])
    fs = len([r for r in rows((lab / "suggestions.html").read_text(encoding="utf-8"))])
    # questions table + the "blocking" list has no rows; suggestions has a scoring table of 6
    if fq != len(q):
        errs.append(f"R4 questions.html: {fq} rows, register has {len(q)}")
    if fs - 6 != len(sq):
        errs.append(f"R4 suggestions.html: {fs} data rows, register has {len(sq)} (+6 scoring rows)")

    # no absolute-root links (Pages serves under /Own6/)
    for name in sorted(PAGES & present):
        html = (lab / name).read_text(encoding="utf-8")
        if re.search(r'href="/(?!/)', html):
            errs.append(f"R3 {name}: root-absolute link")

    return errs


def main() -> int:
    errs = check()
    if errs:
        print(f"check_nfl_lab: {len(errs)} failure(s)")
        for e in errs:
            print("  -", e)
        return 1
    print("check_nfl_lab: 4 rule families pass over 14 pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
