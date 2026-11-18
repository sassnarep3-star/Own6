#!/usr/bin/env python3
"""Verifier for the nfl_b2511a5c pack. Exit 0 only if every rule passes.

Rules
  1  every required file exists (including the re-fetch log)
  2  official reads: unique ids, host/class/gate flags consistent, raw SHA-256 matches, every excerpt is a
     substring of its raw capture, chunk counts well-formed, re-fetch log has one row per read
  3  Week 11 slate: 13 games, 26 playing clubs + 6 bye clubs = the 32 NFL clubs, each matchup line, time,
     network and record found in the raw schedule capture; venues only where a game centre was read, and then
     the venue tokens are found in that game centre's raw capture
  4  bye clubs: name and record found in the raw schedule capture
  5  claim checks: unique ids, allowed verdicts, live read ids exist, CONSISTENT rows cite a read, and the
     claims with a recomputable fact are recomputed from the raw captures
  6  club-site rows: every cell fragment found in its raw club capture; duplicate-name observations recounted
  7  flags, suggestions, questions and sources: unique ids, owner columns blank, status vocabulary, valid read ids
  8  pages: every table row carries an official nfl.com link; internal links resolve; no placeholder text
  9  determinism: the pages on disk equal a fresh build from the registers (no drift)
"""
from __future__ import annotations

import csv
import hashlib
import html
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(REPO, "data", "nfl_b2511a5c")
DOCS = os.path.join(REPO, "docs", "nfl-b2511a5c")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NFL_32 = {"ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX",
          "KC", "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
          "TEN", "WAS"}
NICK = {"IND": "COLTS", "HOU": "TEXANS", "MIA": "DOLPHINS", "BUF": "BILLS", "BAL": "RAVENS", "CAR": "PANTHERS",
        "NO": "SAINTS", "CHI": "BEARS", "TEN": "TITANS", "DAL": "COWBOYS", "TB": "BUCCANEERS", "DET": "LIONS",
        "ARI": "CARDINALS", "KC": "CHIEFS", "PIT": "STEELERS", "PHI": "EAGLES", "NYJ": "JETS", "LAC": "CHARGERS",
        "JAX": "JAGUARS", "NYG": "GIANTS", "LV": "RAIDERS", "DEN": "BRONCOS", "MIN": "VIKINGS", "SF": "49ERS",
        "CIN": "BENGALS", "WAS": "COMMANDERS"}
VENUE_TOKENS = {
    "Houston, TX - Reliant Stadium": ["HOUSTON, TX", "RELIANT STADIUM"],
    "Mexico City - Estadio Banorte": ["MEXICO CITY", "ESTADIO BANORTE"],
}
VERDICTS = ("CONSISTENT", "CONTRADICTED", "CONFLICT", "NOT CLEARED", "NOT RE-VERIFIED")
STATUSES = {"open", "awaiting_owner_choice"}
SEVERITY = {"high", "medium", "low"}
REQUIRED = [
    "README.md", "official_reads.csv", "week11_slate.csv", "week11_byes.csv", "claim_checks.csv",
    "club_depth_reads.csv", "flagged.csv", "pack_suggestions.csv", "pack_questions.csv", "sources.csv", "refetch_log.csv",
]
PAGES = ["index.html", "week11.html", "claims.html", "reads.html", "club-depth.html", "flagged.html",
         "suggestions.html", "questions.html", "sources.html"]

errors: list[str] = []


def fail(rule: str, msg: str) -> None:
    errors.append(f"[{rule}] {msg}")


def load(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def raw_text(path: str) -> str:
    with open(os.path.join(REPO, path), encoding="utf-8") as f:
        return f.read()


def rule1() -> None:
    for name in REQUIRED:
        if not os.path.isfile(os.path.join(DATA, name)):
            fail("1", f"missing data/nfl_b2511a5c/{name}")
    for name in PAGES:
        if not os.path.isfile(os.path.join(DOCS, name)):
            fail("1", f"missing docs/nfl-b2511a5c/{name}")


def rule2(reads: list[dict]) -> dict[str, dict]:
    ids = [r["read_id"] for r in reads]
    if len(ids) != len(set(ids)):
        fail("2", "duplicate read_id")
    if len(reads) != 13:
        fail("2", f"expected 13 official reads, found {len(reads)}")
    read = {r["read_id"]: r for r in reads}
    for r in reads:
        host = re.match(r"https://([^/]+)/", r["url"])
        if not host or host.group(1) != r["host"]:
            fail("2", f"{r['read_id']}: url host does not match host column")
        if r["host"] == "www.nfl.com":
            if r["source_class"] != "official_nfl" or r["release_gate_host"] != "yes":
                fail("2", f"{r['read_id']}: nfl.com read must be official_nfl with release_gate_host=yes")
        else:
            if r["source_class"] != "official_club" or r["release_gate_host"] != "no":
                fail("2", f"{r['read_id']}: club read must be official_club with release_gate_host=no")
        m = re.fullmatch(r"(\d+) of (\d+)", r["chunks_read"])
        if not m or int(m.group(1)) > int(m.group(2)) or int(m.group(1)) < 1:
            fail("2", f"{r['read_id']}: malformed chunks_read {r['chunks_read']!r}")
        path = os.path.join(REPO, r["raw_file"])
        if not os.path.isfile(path):
            fail("2", f"{r['read_id']}: raw capture missing")
            continue
        with open(path, "rb") as f:
            raw = f.read()
        if hashlib.sha256(raw).hexdigest() != r["raw_sha256"]:
            fail("2", f"{r['read_id']}: raw SHA-256 mismatch")
        text = raw.decode("utf-8")
        for piece in [p.strip() for p in r["expect"].split(" || ")]:
            if piece not in text:
                fail("2", f"{r['read_id']}: excerpt not found in raw capture: {piece[:60]!r}")
    # re-fetch log: one row per read; every row names its result
    log = load("refetch_log.csv")
    logged = {r["read_id"]: r for r in log}
    if set(logged) != set(read):
        fail("2", "refetch_log.csv must have exactly one row per official read")
    for rid, r in logged.items():
        if not (r["refetch_result"].startswith("MATCH") or r["refetch_result"] == "NOT RE-FETCHED"):
            fail("2", f"{rid}: refetch_result not in vocabulary: {r['refetch_result']!r}")
        if rid in read and r["url"] != read[rid]["url"]:
            fail("2", f"{rid}: refetch url differs from official_reads url")
    return read


def rule3(read: dict[str, dict], slate: list[dict], byes: list[dict]) -> None:
    if len(slate) != 13:
        fail("3", f"expected 13 Week 11 games, found {len(slate)}")
    if len({s["matchup"] for s in slate}) != len(slate):
        fail("3", "duplicate matchup")
    playing = [s["away"] for s in slate] + [s["home"] for s in slate]
    bye = [b["club"] for b in byes]
    if len(set(playing)) != len(playing):
        fail("3", "a club plays twice")
    if set(playing) & set(bye):
        fail("3", "a club is both playing and on bye")
    if set(playing) | set(bye) != NFL_32 or len(set(playing) | set(bye)) != 32:
        fail("3", "playing + bye clubs do not cover the 32 NFL clubs exactly once")
    sched = raw_text(read["R03"]["raw_file"])
    lines = sched.splitlines()
    for s in slate:
        line = [ln for ln in lines if ln.startswith(s["matchup"] + ", ")]
        if not line:
            fail("3", f"game {s['game_no']} {s['matchup']!r}: matchup line not in R03 raw")
            continue
        if s["time_et"] not in line[0] or s["network"] not in line[0]:
            fail("3", f"game {s['game_no']}: time/network not on the R03 matchup line")
        for ab in (s["away"], s["home"]):
            rec = s["away_record"] if ab == s["away"] else s["home_record"]
            if f"{NICK[ab]} {rec}" not in sched:
                fail("3", f"game {s['game_no']}: {NICK[ab]} {rec} not in R03 raw")
        if s["venue_status"] == "read":
            tokens = VENUE_TOKENS.get(s["venue"])
            if tokens is None or not s["venue_read_id"]:
                fail("3", f"game {s['game_no']}: venue read but no token map or read id")
                continue
            gc = raw_text(read[s["venue_read_id"]]["raw_file"])
            for tok in tokens:
                if tok not in gc:
                    fail("3", f"game {s['game_no']}: venue token {tok!r} not in {s['venue_read_id']} raw")
        elif s["venue"] or s["venue_read_id"]:
            fail("3", f"game {s['game_no']}: venue filled while status is not read")
    for b in byes:
        needle = f"{b['club']} {b['club_name']} {b['record']}"
        if needle not in sched:
            fail("4", f"bye {b['club']}: {needle!r} not in R03 raw")
    if len(byes) != 6:
        fail("4", f"expected 6 bye clubs, found {len(byes)}")


def rule5(read: dict[str, dict], claims: list[dict]) -> None:
    ids = [c["claim_id"] for c in claims]
    if len(ids) != len(set(ids)) or len(claims) != 14:
        fail("5", "claim ids not unique or count is not 14")
    for c in claims:
        if not c["verdict"].startswith(VERDICTS):
            fail("5", f"{c['claim_id']}: verdict not in vocabulary: {c['verdict']!r}")
        for rid in [x for x in c["live_read_ids"].split("|") if x]:
            if rid not in read:
                fail("5", f"{c['claim_id']}: unknown read id {rid}")
        if c["verdict"].startswith("CONSISTENT") and not c["live_read_ids"]:
            fail("5", f"{c['claim_id']}: CONSISTENT without a read")
    by = {c["claim_id"]: c for c in claims}
    # recomputed facts from the raw captures
    r1 = raw_text(read["R01"]["raw_file"])
    for name in ("Kerby Joseph", "Cade Mays", "D.J. Reed"):
        row = [ln for ln in r1.splitlines() if ln.startswith(f"| {name} |")]
        if not row or not row[0].endswith("| Out |"):
            fail("5", f"CC01 recompute: {name} is not Out in R01 raw")
    r11 = raw_text(read["R11"]["raw_file"])
    qb = [ln for ln in r11.splitlines() if ln.startswith("| QB |")]
    if not qb or "Jackson" in qb[0] or "Huntley" in qb[0]:
        fail("5", "CC04 recompute: QB row of R11 unexpectedly names Jackson or Huntley")
    if by.get("CC04", {}).get("verdict", "").startswith("CONTRADICTED") is False:
        fail("5", "CC04 must be CONTRADICTED (QB row recomputed without Jackson or Huntley)")
    r10 = raw_text(read["R10"]["raw_file"])
    if not re.search(r"^\| QB \| \d+ Jordan Love", r10, re.M):
        fail("5", "CC05 recompute: Packers QB row lacks a jersey-number prefix")
    if "Unofficial, Nov. 10, 2026" not in r10:
        fail("5", "CC06 recompute: Packers unofficial label not found")
    if "404 - Flag on the Play." not in raw_text(read["R02"]["raw_file"]):
        fail("5", "CC07 recompute: R02 is not a 404 body")
    if "MEXICO CITY" not in raw_text(read["R05"]["raw_file"]):
        fail("5", "CC09 recompute: R05 venue missing")
    if "HOUSTON, TX" not in raw_text(read["R04"]["raw_file"]):
        fail("5", "CC11 recompute: R04 venue missing")
    if by.get("CC13", {}).get("verdict", "").startswith("NOT RE-VERIFIED") is False:
        fail("5", "CC13 must stay NOT RE-VERIFIED until all 8 chunks are read")


def rule6(read: dict[str, dict], club: list[dict]) -> None:
    for c in club:
        r = read.get(c["read_id"])
        if not r or r["host"] == "www.nfl.com":
            fail("6", f"club row {c['row']} must cite a club read")
            continue
        text = raw_text(r["raw_file"])
        for frag in [x.strip() for x in c["cells"].split("|")]:
            if frag and frag != "(empty)" and frag not in text:
                fail("6", f"{c['read_id']} {c['row']}: fragment not in raw capture: {frag!r}")
    r10 = raw_text(read["R10"]["raw_file"])
    r11 = raw_text(read["R11"]["raw_file"])
    if r10.count("Kitan Oladapo") != 2:
        fail("6", "recount: Kitan Oladapo should appear twice in R10")
    if r11.count("Ryan Neuzil") != 2:
        fail("6", "recount: Ryan Neuzil should appear twice in R11")


def unique_ids(rule: str, rows: list[dict], key: str) -> None:
    ids = [r[key] for r in rows]
    if len(ids) != len(set(ids)):
        fail(rule, f"duplicate {key}")


def rule7(read: dict[str, dict], flags: list[dict], sugg: list[dict], qs: list[dict], sources: list[dict]) -> None:
    unique_ids("7", flags, "flag_id")
    for f in flags:
        if f["severity"] not in SEVERITY:
            fail("7", f"{f['flag_id']}: bad severity")
        if f["status"] not in {"open", "closed"}:
            fail("7", f"{f['flag_id']}: bad status")
        for rid in [x for x in f["evidence_read_ids"].split("|") if x]:
            if rid not in read:
                fail("7", f"{f['flag_id']}: unknown read {rid}")
    unique_ids("7", sugg, "suggestion_id")
    for s in sugg:
        if s["owner_choice"]:
            fail("7", f"{s['suggestion_id']}: owner_choice must stay blank")
        if s["status"] not in STATUSES:
            fail("7", f"{s['suggestion_id']}: bad status {s['status']!r}")
    unique_ids("7", qs, "q_id")
    for q in qs:
        for rid in [x for x in q["read_ids"].split("|") if x]:
            if rid not in read:
                fail("7", f"{q['q_id']}: unknown read {rid}")
    unique_ids("7", sources, "source_id")
    for s in sources:
        host = re.match(r"https://([^/]+)/", s["url"])
        if not host or host.group(1) != s["host"]:
            fail("7", f"{s['source_id']}: url/host mismatch")


TR = re.compile(r"<tr>(.*?)</tr>", re.S)


def rule8() -> None:
    for name in PAGES:
        path = os.path.join(DOCS, name)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        for body in TR.findall(text):
            if "<td>" in body and "https://www.nfl.com/" not in body:
                fail("8", f"{name}: table row without an official nfl.com link")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(path), href.split("#")[0]))
            if not os.path.exists(target):
                fail("8", f"{name}: broken internal link {href}")
        for bad in ("TODO", "None<", ">nan<", "<generator"):
            if bad in text:
                fail("8", f"{name}: placeholder text {bad!r}")


def rule9() -> None:
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import build_nfl_b2511a5c as B  # noqa: E402

    fresh = B.build()
    for name, text in fresh.items():
        path = os.path.join(DOCS, name)
        if not os.path.isfile(path):
            continue
        if open(path, encoding="utf-8").read() != text:
            fail("9", f"{name} differs from a fresh build; rerun scripts/build_nfl_b2511a5c.py")


def main() -> int:
    rule1()
    if errors:
        return report()
    reads = load("official_reads.csv")
    read = rule2(reads)
    rule3(read, load("week11_slate.csv"), load("week11_byes.csv"))
    rule5(read, load("claim_checks.csv"))
    rule6(read, load("club_depth_reads.csv"))
    rule7(read, load("flagged.csv"), load("pack_suggestions.csv"), load("pack_questions.csv"), load("sources.csv"))
    rule8()
    rule9()
    return report()


def report() -> int:
    for e in errors:
        print("FAIL", e)
    if errors:
        print(f"check_nfl_b2511a5c: {len(errors)} problem(s)")
        return 1
    print("check_nfl_b2511a5c: all rules pass (1-9)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
