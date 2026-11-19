"""Capture log: hashes of the raw transcripts and the official-source probe.

Honest limit, stated on the site as well: the sha256 here is taken over the
*transcription* committed in ``data/nfl_d713b52f/raw/``. The fetch tool used in
this session does not expose the response bytes, so the hash proves the
transcript has not changed since it was written — it does not prove the remote
page served those bytes. Every row also carries the URL and the UTC read clock.
"""
from __future__ import annotations

import csv
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(REPO, "data", "nfl_d713b52f")
RAW = os.path.join(DATA, "raw")

READ_AT = "2026-11-19T11:10:00Z"

# file, source_url, kind, what it is used for
CAPTURES = [
    ("cap01_schedules_w11.txt", "https://www.nfl.com/schedules/", "schedule",
     "Week 11 slate rows used for the fixture-context captures (game date, kickoff ET, network, clubs, records)"),
    ("cap02_standings.txt", "https://www.nfl.com/standings/", "standings",
     "All 32 clubs: W-L-T, PCT, PF, PA, NET. Used for the arithmetic audit and for the Week 11 strength inputs."),
    ("cap03_injuries_reg11_ind_hou.txt", "https://www.nfl.com/injuries/", "injury_report",
     "Week 11 report, Thursday IND@HOU block: 26 player rows across 2 clubs with practice and game status"),
    ("cap04_injuries_reg10_header.txt", "https://www.nfl.com/injuries/league/2026/reg10", "injury_report",
     "Header only: the Week 10 page renders a Week 11 <title> while its body heading says WEEK 10"),
    ("cap05_gb_lac_bal.txt",
     "https://static.www.nfl.com/image/upload/v1794916121/gamecenter/ab78ad5a-4feb-11f1-abca-2c54536568a9.pdf",
     "game_book",
     "LAC@BAL official Game Book: lineups, substitutions, did-not-play, not-active, playtime, weather, roof/surface, referee"),
    ("cap06_gb_hou_cle.txt",
     "https://static.www.nfl.com/image/upload/v1794829724/gamecenter/ab583279-4feb-11f1-abca-2c54536568a9.pdf",
     "game_book",
     "HOU@CLE official Game Book: lineups, not-active, playtime. The only Week 10 game whose report carries game designations for both clubs."),
    ("cap07_gb_ne_det.txt",
     "https://static.www.nfl.com/image/upload/v1794829721/gamecenter/ab582c2f-4feb-11f1-abca-2c54536568a9.pdf",
     "game_book",
     "NE@DET official Game Book: lineups, not-active, playtime. Settles the three inherited blank Lions designations and the game-centre venue name."),
    ("cap08_gb_was_nyg.txt",
     "https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf",
     "game_book",
     "WAS@NYG official Game Book: lineups, not-active, playtime. Settles the two Commanders designations."),
    ("cap09_injuries_reg10_clubs.txt", "https://www.nfl.com/injuries/league/2026/reg10", "injury_report",
     "Week 10 report, the four clubs joined to the four books: NE, DET, HOU, CLE, WAS, NYG, LAC"),
    ("cap10_stats_index.txt", "https://www.nfl.com/stats/player-stats/", "probe",
     "The complete official player-stats category list (11 categories, no snap counts) plus the 404 on the snap-counts URL"),
    ("cap11_games_lac_bal_centre.txt", "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10", "game_centre",
     "Game centre: score, week, the Game Book link, and the Game Info venue block"),
]

# The source probe: a dated yes/no for each route the brief depends on.
# The answer is the text read, not an inference.
PROBE = [
    dict(probe_id="P1",
         question="Does an official NFL page publish player snap counts?",
         answer="no as a league table; yes as a per-game table inside the official Game Book PDF",
         evidence="https://www.nfl.com/stats/player-stats/ lists 11 categories and no snap-count category; "
                  "https://www.nfl.com/stats/player-stats/category/snap-counts/2026/reg/all returns 404 - Flag on the Play. "
                  "The official Game Book publishes a 'Playtime Percentage' table per game.",
         raw="cap10_stats_index.txt; cap05_gb_lac_bal.txt",
         caveat="the Game Book captions that table '(Unofficial)'. It therefore cannot serve the brief's "
                "'only from officially sourced numbers' rule as a certified count; it can serve as an "
                "NFL-published, dated, per-game participation measure that is labelled unofficial by its own publisher.",
         official="partial",
         status="open"),
    dict(probe_id="P2",
         question="Does an official NFL page publish per-game inactive lists?",
         answer="yes: the official Game Book prints a 'Not Active' block for both clubs",
         evidence="'Not Active' block read in all four Game Books captured here; 6 players per club.",
         raw="cap05_gb_lac_bal.txt, cap06_gb_hou_cle.txt, cap07_gb_ne_det.txt, cap08_gb_was_nyg.txt",
         caveat="the book is published after the game; it is a settlement record, not a pre-kickoff feed. "
                "For pre-kickoff certainty the 90-minute inactive list would be needed, and no official page "
                "for that list was located in this session.",
         official="yes",
         status="open"),
    dict(probe_id="P3",
         question="Does the official Game Book name the actual starters?",
         answer="yes: a 'Lineups' block lists the 11 offensive and 11 defensive starters per club",
         evidence="Lineups block read in all four books; 22 starters per club per game.",
         raw="cap05..cap08",
         caveat="the block is the book's own naming of who started; it is not a depth chart and does not "
                "carry a depth rank.",
         official="yes",
         status="open"),
    dict(probe_id="P4",
         question="Does an official page publish a 2026 snap-count leaderboard?",
         answer="no",
         evidence="snap-counts URL 404; the stats index enumerates its categories and snap counts is not one.",
         raw="cap10_stats_index.txt",
         caveat="absence on the index is not proof the data does not exist somewhere on nfl.com; only that this "
                "session did not find an official 2026 snap-count leaderboard.",
         official="n/a",
         status="open"),
    dict(probe_id="P5",
         question="Does the official Week 10 injury report carry a game designation for both clubs in every game?",
         answer="no",
         evidence="In the four games joined here, exactly 11 of 12 club blocks carry at least one non-empty "
                  "Game Status cell; the Giants block carries none (11 rows, all blank).",
         raw="cap09_injuries_reg10_clubs.txt",
         caveat="only four games were read for this probe, so the finding is scoped to them.",
         official="yes",
         status="open"),
    dict(probe_id="P6",
         question="Does the official Game Book publish stadium roof and surface?",
         answer="yes, as a text line: 'Open Stadium on Natural Grass' / 'Open Stadium on Field Turf'",
         evidence="read in all four books.",
         raw="cap05..cap08",
         caveat="the roof is the design, not the state at kickoff. Three of four books also carry measured "
                "game-day weather (temperature, humidity, wind, wind chill).",
         official="yes",
         status="open"),
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def capture_rows():
    rows = []
    for name, url, kind, used_for in CAPTURES:
        path = os.path.join(RAW, name)
        rows.append(dict(
            capture_id=os.path.splitext(name)[0],
            raw_file=f"data/nfl_d713b52f/raw/{name}",
            source_url=url,
            kind=kind,
            read_at_utc=READ_AT,
            sha256=sha256_file(path),
            bytes=str(os.path.getsize(path)),
            used_for=used_for,
            hash_scope="sha256 of the committed transcription, not of the remote response bytes",
        ))
    return rows


def verify_capture_log(log_path=None) -> tuple[bool, list[str]]:
    """Recompute every hash. Returns (ok, messages)."""
    log_path = log_path or os.path.join(DATA, "capture_log.csv")
    problems = []
    if not os.path.exists(log_path):
        return False, [f"missing {log_path}"]
    with open(log_path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    seen = set()
    for row in rows:
        name = os.path.basename(row["raw_file"])
        seen.add(name)
        path = os.path.join(RAW, name)
        if not os.path.exists(path):
            problems.append(f"{name}: raw file missing")
            continue
        actual = sha256_file(path)
        if actual != row["sha256"]:
            problems.append(f"{name}: sha256 mismatch (log {row['sha256'][:12]}, file {actual[:12]})")
    for name, _, _, _ in CAPTURES:
        if name not in seen:
            problems.append(f"{name}: present in CAPTURES but not in the log")
    if len(rows) != len(CAPTURES):
        problems.append(f"log has {len(rows)} rows, expected {len(CAPTURES)}")
    return (not problems), problems
