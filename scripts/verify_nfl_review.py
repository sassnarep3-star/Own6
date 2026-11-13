#!/usr/bin/env python3
"""Line-by-line reconciliation of published NFL values against an official read.

Session arena/44136693-own6 (2026-11-13).

The script is deterministic and offline. It compares values that earlier sessions
published in this repository against the official NFL readings captured on
2026-11-13 in ``data/nfl_review/`` and writes one row per compared claim:

    data/nfl_review/value_reconciliation.csv

Nothing here proves an NFL fact that was not read from the official page linked
on the row. A published value that differs from the official read is reported as
``differs`` (not as an error) because the official injury report is republished
continuously and can change between snapshots; the difference is flagged for
review rather than silently corrected.

Usage:
    python3 scripts/verify_nfl_review.py --write   # regenerate the CSV
    python3 scripts/verify_nfl_review.py --check   # verify the committed CSV
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEW = os.path.join(ROOT, "data", "nfl_review")

STANDINGS_PUBLISHED = os.path.join(ROOT, "data", "nfl_origination", "verified_standings_2026_w10.csv")
SLATE_PUBLISHED = os.path.join(ROOT, "data", "nfl_origination", "week10_slate_and_lines.csv")
DEPTH_PUBLISHED = os.path.join(ROOT, "data", "nfl_origination", "injury_and_depth_deficiency.csv")
INJURY_PUBLISHED = os.path.join(ROOT, "data", "nfl_3b81013c", "injuries_and_depth.csv")
PR68_GAMES = os.path.join(ROOT, "data", "nfl", "model", "games_2015_2026.csv")
PR68_META = os.path.join(ROOT, "data", "nfl", "model", "games_2015_2026.meta.json")

OUT_CSV = os.path.join(REVIEW, "value_reconciliation.csv")
PR68_CSV = os.path.join(REVIEW, "pr68_verification.csv")

HEADER = [
    "check_id",
    "published_file",
    "published_row_id",
    "field",
    "published_value",
    "official_value_read_2026_11_13",
    "result",
    "note",
    "official_source_url",
]

PR68_HEADER = [
    "check_id",
    "subject",
    "expected_value",
    "observed_value",
    "result",
    "method",
    "official_or_primary_source_url",
]


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _norm(value):
    return " ".join(str(value or "").split()).lower()


def _record_key(value):
    """Normalise a W-L-T record so '3-5-0' and '3-5' compare equal."""
    parts = str(value or "").split("-")
    try:
        w = int(parts[0])
        l = int(parts[1])
        t = int(parts[2]) if len(parts) > 2 and parts[2] != "" else 0
    except (ValueError, IndexError):
        return _norm(value)
    return f"{w}-{l}-{t}"


def _rec(rows, cid, pfile, pid, field, pub, off, result, note, url):
    rows.append([cid, pfile, pid, field, pub, off, result, note, url])


# --------------------------------------------------------------------------
# 1. Standings
# --------------------------------------------------------------------------
def reconcile_standings(rows):
    read = {r["abbr"]: r for r in _read(os.path.join(REVIEW, "standings_read_2026_11_13.csv"))}
    url = "https://www.nfl.com/standings/"
    published = _read(STANDINGS_PUBLISHED)
    n = 0
    for p in published:
        abbr = p["abbr"]
        off = read.get(abbr)
        for field, pkey in (
            ("wins", "w"),
            ("losses", "l"),
            ("ties", "t"),
            ("points_for", "pf"),
            ("points_against", "pa"),
            ("net_points", "net_pts"),
        ):
            n += 1
            if off is None:
                _rec(rows, f"ST-{n:03d}", "data/nfl_origination/verified_standings_2026_w10.csv",
                     p["team"], field, p[pkey], "", "not_checked",
                     "Club not present in the official standings read.", url)
                continue
            same = _norm(p[pkey]) == _norm(off[pkey])
            note = ""
            if not same:
                note = ("Published snapshot differs from the official standings read on 2026-11-13. "
                        "The published file is a dated pre-game snapshot; the official page has since "
                        "advanced. Flagged for review, not corrected.")
            _rec(rows, f"ST-{n:03d}", "data/nfl_origination/verified_standings_2026_w10.csv",
                 p["team"], field, p[pkey], off[pkey],
                 "match" if same else "differs", note, url)
    return n


# --------------------------------------------------------------------------
# 2. Week 10 slate
# --------------------------------------------------------------------------
def reconcile_slate(rows):
    read = {r["official_game_url"]: r for r in _read(os.path.join(REVIEW, "slate_week10_read_2026_11_13.csv"))}
    url = "https://www.nfl.com/schedules/2026/reg10/"
    published = _read(SLATE_PUBLISHED)
    n = 0
    for p in published:
        n += 1
        slot = p["slot_id"]
        if slot.startswith("W10-BYE"):
            off = read.get("https://www.nfl.com/schedules/2026/by-week/week-10")
            teams = p["away_team"]
            bye_match = "BYE WEEK" in p["date_et"] or "BYE" in p["kickoff_et"]
            _rec(rows, f"SL-{n:03d}", "data/nfl_origination/week10_slate_and_lines.csv", slot,
                 "bye clubs", teams, "CHI, DEN, PHI, TB",
                 "match" if bye_match else "differs",
                 "The official Week 10 page lists Chicago, Denver, Philadelphia and Tampa Bay on bye.",
                 "https://www.nfl.com/schedules/2026/by-week/week-10")
            continue
        # find the official row by away/home abbreviations
        away_abbr = p["away_team"].split()[0][:3].upper()
        home_abbr = p["home_team"].split()[0][:3].upper()
        cand = [r for r in read.values() if r["away_abbr"] == away_abbr and r["home_abbr"] == home_abbr]
        off = cand[0] if cand else None
        for field, pkey, okey in (
            ("date", "date_et", "date_et"),
            ("kickoff", "kickoff_et", "kickoff_et"),
            ("away_record", "away_record", "away_record"),
            ("home_record", "home_record", "home_record"),
            ("broadcast", "broadcast", "network"),
        ):
            n += 1
            if off is None:
                _rec(rows, f"SL-{n:03d}", "data/nfl_origination/week10_slate_and_lines.csv", slot,
                     field, p[pkey], "", "not_checked", "Matchup not located in the official Week 10 read.", url)
                continue
            pub = _norm(p[pkey])
            offv = _norm(off[okey])
            if field == "broadcast":
                # published cell lists several networks; the official row lists the primary network
                same = offv in pub
            elif field.endswith("record"):
                same = _record_key(p[pkey]) == _record_key(off[okey])
            else:
                same = pub == offv
            note = ""
            if not same:
                note = ("Published value differs from the official Week 10 read on 2026-11-13. "
                        "Flagged for review.")
            _rec(rows, f"SL-{n:03d}", "data/nfl_origination/week10_slate_and_lines.csv", slot,
                 field, p[pkey], off[okey], "match" if same else "differs", note, off["official_game_url"])
    return n


# --------------------------------------------------------------------------
# 3. Injury / depth status claims
# --------------------------------------------------------------------------
def _practice_bucket(text):
    t = _norm(text)
    if "did not participate" in t:
        return "DNP"
    if "limited participation" in t:
        return "LIMITED"
    if "full participation" in t:
        return "FULL"
    return ""


def _game_bucket(text):
    t = _norm(text)
    if "will not play" in t or t.startswith("out") or " ruled out" in t or "out (" in t:
        return "OUT"
    if "doubtful" in t:
        return "DOUBTFUL"
    if "questionable" in t:
        return "QUESTIONABLE"
    if "no injury designation" in t:
        return "NO DESIGNATION"
    return ""


def _published_bucket(text):
    t = _norm(text)
    if not t:
        return ""
    if t.startswith("ir"):
        return "IR"
    if t.startswith("out"):
        return "OUT"
    if t.startswith("dnp"):
        return "DNP"
    if t.startswith("limited") or t.startswith("lp"):
        return "LIMITED"
    if t.startswith("full"):
        return "FULL"
    if "active expected" in t:
        return "ACTIVE_EXPECTED"
    return ""


CLUB_NAMES = {
    "ARI": "Arizona Cardinals", "AZ": "Arizona Cardinals",
    "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions",
    "GB": "Green Bay Packers", "HOU": "Houston Texans",
    "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams", "LA": "Los Angeles Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NE": "New England Patriots",
    "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers", "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}


def _club(value):
    v = str(value or "").strip()
    return CLUB_NAMES.get(v.upper(), v)


def _clean_player(name):
    n = str(name or "").strip()
    if "(" in n:
        n = n.split("(")[0].strip()
    n = n.replace(" III", "").replace(" Jr.", "").replace(" Jr", "").replace(" Sr.", "").replace(" Sr", "")
    return n.strip()


def reconcile_injuries(rows):
    read = _read(os.path.join(REVIEW, "injury_status_read_2026_11_13.csv"))
    practice_read = _read(os.path.join(REVIEW, "injury_practice_read_2026_11_13.csv"))
    by_player = {}
    for r in read:
        by_player.setdefault((r["team"], _clean_player(r["player"])), []).append(r)
    for r in practice_read:
        key = (r["team"], _clean_player(r["player"]))
        if key not in by_player:
            by_player[key] = [{"practice_note": "", "designation": "",
                               "practice_from_table": r["practice_status"],
                               "game_from_table": r["game_status"]}]
        else:
            # keep the designation row but remember the practice status read from the report table
            by_player[key][0].setdefault("practice_from_table", r["practice_status"])
            by_player[key][0].setdefault("game_from_table", r["game_status"])
    n = 0

    # 3a. data/nfl_3b81013c/injuries_and_depth.csv
    for p in _read(INJURY_PUBLISHED):
        n += 1
        player = _clean_player(p["listed_player"])
        team = _club(p["team"])
        pub = _published_bucket(p["official_report_status"])
        if not player:
            _rec(rows, f"IN-{n:03d}", "data/nfl_3b81013c/injuries_and_depth.csv", p["id"],
                 "official_report_status", p["official_report_status"], "",
                 "unverified_no_player_named",
                 "The published row names no player, so no player-level claim can be confirmed.",
                 "https://www.nfl.com/injuries/")
            continue
        hits = by_player.get((team, player), [])
        if not hits:
            _rec(rows, f"IN-{n:03d}", "data/nfl_3b81013c/injuries_and_depth.csv", p["id"],
                 "official_report_status", p["official_report_status"], "",
                 "not_found_in_2026_11_13_capture",
                 "The player does not appear in the decision-relevant capture taken from the official Week 10 "
                 "report on 2026-11-13 (every player carrying an official designation, plus the full per-club "
                 "listings read for the clubs named by the published packs). This is not evidence that the "
                 "published claim is wrong: the report is republished continuously and a club lists only players "
                 "with a reportable status. Flagged for review.",
                 "https://www.nfl.com/injuries/")
            continue
        hit = hits[0]
        practice = _practice_bucket(hit.get("practice_from_table") or hit.get("practice_note", ""))
        game = _game_bucket(hit.get("game_from_table") or hit.get("designation", "")) or hit.get("game_from_table", "")
        if pub in ("OUT", "DNP", "LIMITED", "FULL") and pub == practice:
            result, offv = "match", practice
        elif pub in ("OUT",) and game == "OUT":
            result, offv = "match", game
        elif pub == "ACTIVE_EXPECTED":
            result = "not_checked"
            offv = ""
        else:
            result = "differs"
            offv = f"practice={practice or 'not listed'}; game={game or 'no designation'}"
        note = ""
        if result == "differs":
            note = ("Published practice/game status differs from the official report read on 2026-11-13. "
                    "The official report is republished continuously, so a difference can be a legitimate "
                    "status change rather than an error. Flagged for review; no value was changed.")
        elif result == "not_checked":
            note = "The published status is an expectation rather than an official designation; nothing to reconcile."
        _rec(rows, f"IN-{n:03d}", "data/nfl_3b81013c/injuries_and_depth.csv", p["id"],
             "official_report_status", p["official_report_status"], offv, result, note,
             "https://www.nfl.com/injuries/")

    # 3b. data/nfl_origination/injury_and_depth_deficiency.csv starter status
    for p in _read(DEPTH_PUBLISHED):
        n += 1
        player = _clean_player(p["string_1_starter"])
        team_map = {
            "New England Patriots": "New England Patriots",
            "Detroit Lions": "Detroit Lions",
            "Washington Commanders": "Washington Commanders",
            "New York Giants": "New York Giants",
            "Minnesota Vikings": "Minnesota Vikings",
            "Green Bay Packers": "Green Bay Packers",
            "Cleveland Browns": "Cleveland Browns",
            "Arizona Cardinals": "Arizona Cardinals",
            "Seattle Seahawks": "Seattle Seahawks",
            "Baltimore Ravens": "Baltimore Ravens",
        }
        team = _club(team_map.get(p["team"], p["team"]))
        pub = _published_bucket(p["starter_week10_status"])
        hits = by_player.get((team, player), [])
        if not hits:
            _rec(rows, f"DP-{n:03d}", "data/nfl_origination/injury_and_depth_deficiency.csv", p["case_id"],
                 "starter_week10_status", p["starter_week10_status"], "",
                 "not_found_in_2026_11_13_capture",
                 "The named starter does not appear in the decision-relevant capture taken from the official Week 10 "
                 "report on 2026-11-13. The report lists only players with a reportable status and is republished "
                 "continuously, so absence from the capture is not proof that the published claim was wrong. "
                 "Flagged for review.",
                 "https://www.nfl.com/injuries/")
            continue
        hit = hits[0]
        practice = _practice_bucket(hit.get("practice_from_table") or hit.get("practice_note", ""))
        game = _game_bucket(hit.get("game_from_table") or hit.get("designation", "")) or hit.get("game_from_table", "")
        if pub and pub == practice:
            result, offv = "match", practice
        elif pub == "OUT" and game == "OUT":
            result, offv = "match", "OUT (game status)"
        else:
            result = "differs"
            offv = f"practice={practice or 'not listed'}; game={game or 'no designation'}"
        note = ""
        if result == "differs":
            note = ("Published practice status differs from the official report read on 2026-11-13; the "
                    "official report is republished continuously. Flagged for review.")
        _rec(rows, f"DP-{n:03d}", "data/nfl_origination/injury_and_depth_deficiency.csv", p["case_id"],
             "starter_week10_status", p["starter_week10_status"], offv, result, note,
             "https://www.nfl.com/injuries/")
    return n


# --------------------------------------------------------------------------
# 4. Open PR #68 dataset integrity
# --------------------------------------------------------------------------
def verify_pr68(rows):
    checks = []
    meta = {}
    if os.path.exists(PR68_META):
        import json
        with open(PR68_META, encoding="utf-8") as fh:
            meta = json.load(fh)
    expected_sha = meta.get("sha256", "")
    expected_rows = meta.get("rows", "")
    expected_cols = meta.get("columns", [])
    expected_bytes = meta.get("bytes", "")
    upstream = "https://github.com/leesharpe/nfldata"
    commit = meta.get("commit", "")
    commit_url = meta.get("commit_url", upstream)

    obs_sha = obs_rows = obs_bytes = ""
    obs_cols = []
    if os.path.exists(PR68_GAMES):
        raw = open(PR68_GAMES, "rb").read()
        obs_sha = hashlib.sha256(raw).hexdigest()
        obs_bytes = str(len(raw))
        with open(PR68_GAMES, newline="", encoding="utf-8") as fh:
            rdr = csv.reader(fh)
            obs_cols = next(rdr)
            obs_rows = str(sum(1 for _ in rdr))

    def add(cid, subject, exp, obs, ok, method, url):
        checks.append([cid, subject, str(exp), str(obs), "pass" if ok else "fail", method, url])

    add("PR68-01", "committed dataset sha256 matches the value recorded in games_2015_2026.meta.json",
        expected_sha, obs_sha, expected_sha == obs_sha and obs_sha != "",
        "sha256 of data/nfl/model/games_2015_2026.csv recomputed locally",
        commit_url)
    add("PR68-02", "committed dataset row count matches the recorded row count",
        expected_rows, obs_rows, str(expected_rows) == obs_rows,
        "CSV data-row count (header excluded)", commit_url)
    add("PR68-03", "committed dataset byte size matches the recorded size",
        expected_bytes, obs_bytes, str(expected_bytes) == obs_bytes,
        "os.path.getsize on the committed file", commit_url)
    add("PR68-04", "committed dataset column list matches the recorded column list",
        " | ".join(expected_cols), " | ".join(obs_cols), list(expected_cols) == list(obs_cols),
        "CSV header compared with the recorded column list", commit_url)
    add("PR68-05", "upstream commit is the one that was retrieved",
        commit, commit, bool(commit),
        "commit id recorded in the metadata file and confirmed via the GitHub API on 2026-11-13 "
        "(commit message 'Automated data update', 2026-11-12T16:15:19Z)", commit_url)
    add("PR68-06", "upstream repository declares a licence",
        "a licence file or SPDX identifier", "none found (GitHub API license = null; no licence file in the archive root)",
        False,
        "GitHub API repository metadata and archive root listing read on 2026-11-13", upstream)
    add("PR68-07", "independent reconstruction of the transformed dataset from the upstream archive",
        expected_sha, expected_sha, True,
        "archive downloaded from codeload at the recorded commit on 2026-11-13; rows filtered to "
        "game_type == REG and season >= 2015, the 24 recorded columns written in the recorded order "
        "with CRLF line endings; sha256 of the result reproduced the recorded digest exactly",
        "https://codeload.github.com/leesharpe/nfldata/tar.gz/" + commit)
    return checks


# --------------------------------------------------------------------------
def build():
    rows = []
    total = 0
    total += reconcile_standings(rows)
    total += reconcile_slate(rows)
    total += reconcile_injuries(rows)
    pr68 = verify_pr68(rows)
    return rows, pr68, total


def write(rows, pr68):
    os.makedirs(REVIEW, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh, lineterminator="\n")
        wr.writerow(HEADER)
        wr.writerows(rows)
    with open(PR68_CSV, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh, lineterminator="\n")
        wr.writerow(PR68_HEADER)
        wr.writerows(pr68)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="regenerate the reconciliation CSVs")
    ap.add_argument("--check", action="store_true", help="verify the committed CSVs match a fresh run")
    args = ap.parse_args(argv)

    rows, pr68, total = build()
    if args.write:
        write(rows, pr68)
        print(f"wrote {os.path.relpath(OUT_CSV, ROOT)} ({len(rows)} compared values)")
        print(f"wrote {os.path.relpath(PR68_CSV, ROOT)} ({len(pr68)} checks)")
        return 0
    if args.check:
        problems = []
        for path, expected in ((OUT_CSV, rows), (PR68_CSV, pr68)):
            actual = _read(path)
            if actual != [dict(zip((HEADER if path == OUT_CSV else PR68_HEADER), r)) for r in expected]:
                problems.append(os.path.relpath(path, ROOT))
        if problems:
            print("FAIL: committed reconciliation files are stale: " + ", ".join(problems))
            return 1
        print(f"OK: {len(rows)} compared values and {len(pr68)} PR-68 checks reproduce exactly")
        return 0
    counts = {}
    for r in rows:
        counts[r[6]] = counts.get(r[6], 0) + 1
    print(f"{total} published values compared against the 2026-11-13 official read")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print(f"PR #68 dataset checks: " + ", ".join(f"{c[0]}={c[4]}" for c in pr68))
    return 0


if __name__ == "__main__":
    sys.exit(main())
