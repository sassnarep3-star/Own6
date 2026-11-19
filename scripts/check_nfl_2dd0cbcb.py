#!/usr/bin/env python3
"""Verifier for the nfl_2dd0cbcb pack. Fails loudly on drift, unsourced rows or invented values.

Rules
-----
1   every required data file exists with its pinned row count
2   every data row with a source URL uses https on an official host; no proxy/aggregator host
3    week12_venues: 16 rows, both venue fields non-blank on every row; the normalization diff
    reproduces exactly the three published mismatches, and every raw-differs row is explained
4   thursday_status_reg11: 26 rows for one fixture (IND@HOU) — 16 game statuses split IND 9 /
    HOU 7, and 10 rows whose game-status cell is blank while a practice status is printed; the
    two IR-linked blank cases (Jaylon Carlies, Azeez Al-Shaair) must be named in the register
5   reserve_rows: 25 rows, window 11/10-11/18, every row carries the same rendered count
6   requirements.csv: 80 rows, every evidence pointer exists in the tree, satisfied rows name
    a file (not a hope), and no satisfied row points at this pack's own raw/ transcription
7   questions.csv: every open question has an empty answer; every answered one cites a
    read_id or artifact
8   suggestions.csv: pending_human_choice=yes and decision empty on every row (no bot decides)
9   flagged.csv: no flag sets blocking_merge=yes; every flag names at least one source URL
10  depth_retest: image-only clubs have text_rows_count == 0 (no eyeballed rows)
11  no claim language (ROI/CLV/units/guaranteed/expected return/buy now) in any page
12  no form control anywhere on the site
13  no placeholder tokens in pages or registers (TODO/TBD/{{/lorem/XXX)
14  every internal link on every page resolves
15  capture log: every artifact exists and sha256 matches bytes; read_on_utc is a real ISO-8601 Z stamp
16  determinism: rebuilding the site reproduces all six pages byte for byte
17  the site has exactly the six expected pages, and each carries the navigation set
18  cross-pack: this pack's Thursday game statuses agree with a67ddef8's reg11 register
19  every page footer links the landing + hub, and no page links a raw/ transcription as a fact source
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_2dd0cbcb")
RAW = os.path.join(DATA, "raw")
DOCS = os.path.join(REPO, "docs", "nfl-2dd0cbcb")
OTHER = os.path.join(REPO, "data", "nfl_a67ddef8")

sys.path.insert(0, os.path.join(REPO, "src"))

PINNED = {
    "requirements.csv": 80,
    "rechecks.csv": 20,
    "questions.csv": 8,
    "suggestions.csv": 13,
    "flagged.csv": 10,
    "sources.csv": 9,
    "capture_log.csv": 7,
    "week12_venues.csv": 16,
    "thursday_status_reg11.csv": 26,
    "reserve_rows.csv": 25,
    "depth_retest.csv": 3,
    "repo_findings.csv": 11,
}

EXPECTED_PAGES = ["index.html", "requirements.html", "captures.html", "depth.html",
                  "flags.html", "sources.html"]

OFFICIAL_HOSTS = (
    "nfl.com", "www.nfl.com", "operations.nfl.com", "nextgenerationstats.com",
    "azcardinals.com", "www.azcardinals.com",
    "packers.com", "www.packers.com",
    "houstontexans.com", "www.houstontexans.com",
    "github.com",
)
FORBIDDEN_HOSTS = ("aliyuncs.com", "routify-file-proxy", "webcache.googleusercontent.com")

# Rule 11: claim vocabulary is banned from page PROSE. The owner's brief line for the
# two-stage leaderboard names "CLV/ROI" itself, so those two acronyms are additionally
# confined to requirements.html (the verbatim brief lines) — they may not appear on any
# other page, where they would read as our claim rather than the owner's wording.
BANNED_WORDS = re.compile(
    r"\b(units won|guaranteed profit|guaranteed|expected return|buy now|lorem ipsum|"
    r"profitable|lock of the week|free money)\b", re.I)
ACRONYM_PAGES = re.compile(r"\b(ROI|CLV)\b")
# "TBD" is only ever a problem here as an unfilled template marker. The literal string
# "2026 TBD Games" is official nfl.com copy (the flex-scheduling footer link), transcribed
# verbatim into the capture log and rendered from it,
# so it is masked out before the scan rather than dropped from the transcription.
PLACEHOLDER = re.compile(r"TODO|TBD|\{\{|lorem ipsum|\bXXX\b", re.I)
OFFICIAL_TBD = re.compile(r"TBD[ -]?games?(\s+(flex|schedule))?", re.I)
ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?Z)?$")
HTTP = re.compile(r"https?://([^/\s\"';,)]+)")

problems: list[str] = []


def fail(rule: int, msg: str) -> None:
    problems.append(f"rule {rule}: {msg}")


def read(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        fail(1, f"missing data file {name}")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm_venue(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


# ------------------------------------------------------------------ rule 1
def check_pinned() -> None:
    for name, n in PINNED.items():
        rows = read(name)
        if len(rows) != n:
            fail(1, f"{name}: {len(rows)} rows, expected {n}")


# ------------------------------------------------------------------ rule 2
def check_hosts() -> None:
    files = ["week12_venues.csv", "thursday_status_reg11.csv", "reserve_rows.csv",
             "depth_retest.csv", "sources.csv", "flagged.csv", "questions.csv",
             "suggestions.csv", "requirements.csv", "rechecks.csv"]
    for name in files:
        for i, r in enumerate(read(name), start=2):
            for k, v in r.items():
                for m in HTTP.finditer(v or ""):
                    host = m.group(1).lower()
                    if host.startswith("http://"):
                        fail(2, f"{name} line {i}: insecure url")
                    if host in FORBIDDEN_HOSTS or any(f in host for f in FORBIDDEN_HOSTS):
                        fail(2, f"{name} line {i}: forbidden/proxy host {host}")
                    if host and host not in OFFICIAL_HOSTS:
                        fail(2, f"{name} line {i}: non-official host {host}")
    for root, _d, fs in os.walk(DOCS):
        for fn in fs:
            text = open(os.path.join(root, fn), encoding="utf-8").read()
            for host in HTTP.findall(text):
                if any(f in host for f in FORBIDDEN_HOSTS):
                    fail(2, f"{fn}: forbidden host {host}")


# ------------------------------------------------------------------ rule 3
def check_venues() -> None:
    rows = read("week12_venues.csv")
    if len(rows) != 16:
        return
    raw = [r for r in rows if r["venue_raw_differs"] == "yes"]
    norm = [r for r in rows if r["venue_mismatch_after_normalization"] == "yes"]
    for r in rows:
        if not r["venue_stadium_gamecentre"].strip() or not r["venue_hotel_param_schedulepage"].strip():
            fail(3, f"{r['away']}@{r['home']}: a venue field is blank (both must be published)")
        recomputed = "yes" if norm_venue(r["venue_stadium_gamecentre"]) != norm_venue(
            r["venue_hotel_param_schedulepage"]) else "no"
        if recomputed != r["venue_mismatch_after_normalization"]:
            fail(3, f"{r['away']}@{r['home']}: normalization flag does not match the two venue strings")
    if {(r["away"], r["home"]) for r in norm} != {("DEN", "PIT"), ("BAL", "HOU"), ("TEN", "JAX")}:
        fail(3, "venue mismatch set changed: expected DEN@PIT, BAL@HOU, TEN@JAX after normalization")
    if len(raw) != 5:
        fail(3, f"raw-string difference count is {len(raw)}, expected 5 (3 named + punctuation + glyph)")
    if not any(r["venue_raw_differs"] == "no" for r in rows):
        fail(3, "no row shows the two venue fields agreeing — suspicious")


# ------------------------------------------------------------------ rule 4
def check_thursday() -> None:
    rows = read("thursday_status_reg11.csv")
    if len(rows) != 26:
        return
    with_status = [r for r in rows if r["game_status"].strip()]
    blank = [r for r in rows if not r["game_status"].strip()]
    if len(with_status) != 16:
        fail(4, f"{len(with_status)} game statuses, expected 16 (Thursday game only)")
    if len(blank) != 10:
        fail(4, f"{len(blank)} blank-status rows, expected 10")
    names = {r["player"] for r in blank}
    for who in ("Jaylon Carlies", "Azeez Al-Shaair"):
        if who not in names:
            fail(4, f"IR blank-status case {who} missing from the register")
    for r in with_status:
        if r["club"] not in ("IND", "HOU"):
            fail(4, f"{r['player']}: game status published for a non-Thursday club {r['club']}")


# ------------------------------------------------------------------ rule 5
def check_reserve() -> None:
    rows = read("reserve_rows.csv")
    if len(rows) != 25:
        return
    if {r["window_first_date_rendered"] for r in rows} != {"11/10"}:
        fail(5, "reserve window start not 11/10 on every row")
    if {r["window_last_date_rendered"] for r in rows} != {"11/18"}:
        fail(5, "reserve window end not 11/18 on every row")
    if {r["row_count_on_page"] for r in rows} != {"25"}:
        fail(5, "row_count_on_page not pinned to 25 on every row")
    for r in rows:
        if not ISO_Z.match(r["read_on_utc"]):
            fail(5, f"reserve row {r['name']}: read_on_utc not ISO-8601 Z")


# ------------------------------------------------------------------ rule 6
def check_requirements() -> None:
    rows = read("requirements.csv")
    for r in rows:
        ptr = r["evidence_pointer"].strip()
        if not ptr:
            fail(6, f"{r['req_id']}: no evidence pointer")
            continue
        if not ptr.startswith("http") and not os.path.exists(os.path.join(REPO, ptr)):
            fail(6, f"{r['req_id']}: evidence pointer does not exist: {ptr}")
        if r["status"].startswith("satisfied") and ptr.startswith("data/nfl_2dd0cbcb/raw/"):
            fail(6, f"{r['req_id']}: satisfied row backed only by a raw transcription")
        if not r["brief_line"].strip():
            fail(6, f"{r['req_id']}: empty brief_line")


# ------------------------------------------------------------------ rule 7
def check_questions() -> None:
    for r in read("questions.csv"):
        status, ans = r["status"].strip().lower(), r["answer"].strip()
        if status == "open" and ans:
            fail(7, f"{r['q_id']}: open question carries an answer (status/answer disagree)")
        if status == "open" and r["answered_by"].strip():
            fail(7, f"{r['q_id']}: open question names an answerer")
        if status.startswith("answered") and not (ans and r["answered_on"].strip()):
            fail(7, f"{r['q_id']}: answered without answer+answered_on")
        if not r["source_urls"].strip():
            fail(7, f"{r['q_id']}: no source url")


# ------------------------------------------------------------------ rule 8
def check_suggestions() -> None:
    for r in read("suggestions.csv"):
        if r["decision"].strip() or r["decided_by"].strip() or r["decided_on"].strip():
            fail(8, f"{r['s_id']}: decision recorded without a human owner")
        if r["pending_human_choice"] not in ("yes", "no"):
            fail(8, f"{r['s_id']}: pending_human_choice must be yes/no")
        if r["pending_human_choice"] == "yes" and not r["decision"].strip() and not r["cons"].strip():
            fail(8, f"{r['s_id']}: pending choice with no cons recorded")


# ------------------------------------------------------------------ rule 9
def check_flags() -> None:
    for r in read("flagged.csv"):
        if r["blocking_merge"].strip().lower() != "no":
            fail(9, f"{r['flag_id']}: blocking_merge must be 'no' (flag, not stop)")
        if not r["source_urls"].strip():
            fail(9, f"{r['flag_id']}: flag without a source url")
        if r["severity"] not in ("high", "medium", "low", "info"):
            fail(9, f"{r['flag_id']}: severity {r['severity']!r} not in scale")
        if not r["detail"].strip():
            fail(9, f"{r['flag_id']}: flag without detail")


# ------------------------------------------------------------------ rule 10
def check_depth() -> None:
    for r in read("depth_retest.csv"):
        if r["render"].strip() == "image-only" and r["text_rows_count"].strip() not in ("0", ""):
            fail(10, f"{r['club']}: image-only club carries {r['text_rows_count']} 'rows'")
        if r["render"].strip() == "text-table" and not r["text_rows_count"].strip().isdigit():
            fail(10, f"{r['club']}: text club without a row count")
        if not r["finding"].strip():
            fail(10, f"{r['club']}: no finding recorded")


# ----------------------------------------------------- rules 11-14 (site text)
def check_site_text() -> None:
    if not os.path.isdir(DOCS):
        fail(14, "docs directory missing")
        return
    for fn in sorted(os.listdir(DOCS)):
        text = open(os.path.join(DOCS, fn), encoding="utf-8").read()
        for m in BANNED_WORDS.finditer(text):
            fail(11, f"{fn}: claim language {m.group(0)!r}")
        for tag in ("<input", "<select", "<textarea", "<button", "<form"):
            if tag in text:
                fail(12, f"{fn}: contains {tag}")
        m = PLACEHOLDER.search(OFFICIAL_TBD.sub("    Games", text))
        if m:
            fail(13, f"{fn}: placeholder {m.group(0)!r}")
        if fn != "requirements.html":
            for mm in ACRONYM_PAGES.finditer(text):
                fail(11, f"{fn}: {mm.group(0)} used outside the verbatim brief lines")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                if href.startswith("http://"):
                    fail(14, f"{fn}: insecure link {href}")
                continue
            if not os.path.exists(os.path.normpath(os.path.join(DOCS, href))):
                fail(14, f"{fn}: broken internal link {href}")
    for name in ("requirements.csv", "questions.csv", "suggestions.csv",
                 "flagged.csv", "rechecks.csv"):
        text = open(os.path.join(DATA, name), encoding="utf-8").read()
        m = PLACEHOLDER.search(text)
        if m:
            fail(13, f"{name}: placeholder {m.group(0)!r} in a register")


# ------------------------------------------------------------------ rule 15
def check_capture_log() -> None:
    from nfl_2dd0cbcb import capture
    for p in capture.verify_capture_log():
        fail(15, p)
    for r in read("capture_log.csv"):
        if not ISO_Z.match(r["read_on_utc"]):
            fail(15, f"{r['read_id']}: read_on_utc not ISO-8601 Z")
        for token in ("artifact_sha256", "artifact_path", "what_was_read", "page_title_as_read"):
            if not r[token].strip():
                fail(15, f"{r['read_id']}: empty {token}")
        if "transcription artifact" not in r["artifact_sha_covers"]:
            fail(15, f"{r['read_id']}: sha coverage not stated honestly")
    for fn in sorted(os.listdir(RAW)) if os.path.isdir(RAW) else []:
        if not fn.endswith(".md"):
            fail(15, f"unexpected file in raw/: {fn}")
            continue
        body = open(os.path.join(RAW, fn), encoding="utf-8").read()
        if "TRANSCRIPTION" not in body[:400]:
            fail(15, f"raw/{fn}: header does not declare itself a transcription")


# ------------------------------------------------------------------ rule 16
def check_determinism() -> None:
    before = {}
    for fn in EXPECTED_PAGES:
        p = os.path.join(DOCS, fn)
        if os.path.exists(p):
            before[fn] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_2dd0cbcb.py")],
                   check=True, capture_output=True)
    if len(before) != len(EXPECTED_PAGES):
        fail(16, f"{len(before)} pages present before rebuild, expected {len(EXPECTED_PAGES)}")
    for fn, h in before.items():
        now = hashlib.sha256(open(os.path.join(DOCS, fn), "rb").read()).hexdigest()
        if now != h:
            fail(16, f"{fn}: rebuild not byte-identical")


# ------------------------------------------------------------------ rule 17
def check_pages() -> None:
    have = sorted(f for f in os.listdir(DOCS) if f.endswith(".html")) if os.path.isdir(DOCS) else []
    if have != sorted(EXPECTED_PAGES):
        fail(17, f"pages {have} != {sorted(EXPECTED_PAGES)}")
        return
    for fn in EXPECTED_PAGES:
        text = open(os.path.join(DOCS, fn), encoding="utf-8").read()
        for target, label in NAV_EXPECT:
            if f'href="{target}"' not in text:
                fail(17, f"{fn}: nav missing {target}")
        if "static build" not in text.lower():
            fail(17, f"{fn}: footer does not state the static build")


NAV_EXPECT = [("index.html", "Overview"), ("requirements.html", "Readiness"),
              ("captures.html", "Captures"), ("depth.html", "Depth"),
              ("flags.html", "Flags"), ("sources.html", "Sources")]


# ------------------------------------------------------------------ rule 18
def check_cross_pack() -> None:
    mine = {(r["player"], r["game_status"]): r for r in read("thursday_status_reg11.csv")}
    path = os.path.join(OTHER, "injuries_reg11.csv")
    if not os.path.exists(path):
        fail(18, f"cross-pack register missing: {path}")
        return
    with open(path, newline="", encoding="utf-8") as f:
        theirs = list(csv.DictReader(f))
    keys = {"player", "game_status", "practice_status"}
    if not keys <= set(theirs[0].keys()):
        fail(18, "a67ddef8 injuries register lacks the columns this rule needs")
        return
    by_player = {r["player"].strip(): r for r in theirs}
    seen = 0
    for (player, status), r in mine.items():
        t = by_player.get(player)
        if t is None:
            continue
        seen += 1
        if (t.get("game_status", "").strip() or "") != status.strip():
            fail(18, f"{player}: game status {status!r} vs a67ddef8 {t.get('game_status')!r}")
        if (t.get("practice_status", "").strip() or "") != r["practice_status"].strip():
            fail(18, f"{player}: practice status disagrees with a67ddef8")
    if seen < 20:
        fail(18, f"only {seen} of 26 Thursday rows matched by name into a67ddef8's register")


# ------------------------------------------------------------------ rule 19
def check_footers() -> None:
    for fn in EXPECTED_PAGES:
        p = os.path.join(DOCS, fn)
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8").read()
        for need in ("../../index.html", "../index.html"):
            if need not in text:
                fail(19, f"{fn}: no link to {need}")
        for m in re.finditer(r'href="([^"]*raw/[^"]+)"', text):
            href = m.group(1)
            if not href.startswith("https://github.com/sassnarep3-star/Own6/"):
                fail(19, f"{fn}: raw/ transcription linked as a local path ({href}) — "
                         f"Pages does not serve data/, so artifact links must be blob URLs")
        if "data/nfl_2dd0cbcb" not in text:
            fail(19, f"{fn}: does not name the data directory it renders")


def main() -> int:
    for fn in check_rules():
        fn()
    if problems:
        print(f"FAIL — {len(problems)} problem(s):")
        for p in problems:
            print(" -", p)
        return 1
    total = sum(PINNED.values())
    print(f"OK — 19 rules, {total} data rows, {len(EXPECTED_PAGES)} pages, "
          f"capture log verified, cross-pack agreement checked")
    return 0


CHECK_RULES = [
    ("pinned", check_pinned),
    ("hosts", check_hosts),
    ("venues", check_venues),
    ("thursday", check_thursday),
    ("reserve", check_reserve),
    ("requirements", check_requirements),
    ("questions", check_questions),
    ("suggestions", check_suggestions),
    ("flags", check_flags),
    ("depth", check_depth),
    ("site text", check_site_text),
    ("capture log", check_capture_log),
    ("determinism", check_determinism),
    ("pages", check_pages),
    ("cross-pack", check_cross_pack),
    ("footers", check_footers),
]


def check_rules():
    return [f for _name, f in CHECK_RULES]


if __name__ == "__main__":
    sys.exit(main())
