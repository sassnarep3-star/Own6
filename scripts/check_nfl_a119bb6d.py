#!/usr/bin/env python3
"""Fail-closed checks for the a119bb6d pack and its published pages.

Every check is a boolean assertion with a name, so a failure names the thing
that broke. Exit code is 0 only if all checks pass; there is no warning tier,
because a warning tier is where unverified numbers go to be published.

Run: python3 scripts/check_nfl_a119bb6d.py
"""

from __future__ import annotations

import csv
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "data", "nfl_a119bb6d")
PARSED = os.path.join(DATA, "parsed")
DOCS = os.path.join(ROOT, "docs", "nfl-a119bb6d")

FAILS: list[str] = []
CHECKS = [0]

OFFICIAL_HOSTS = ("nfl.com", "static.www.nfl.com")


def load(name: str, folder: str = DATA):
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS[0] += 1
    if not condition:
        FAILS.append(f"{name}: {detail}")


def main() -> int:
    games = load("game_books.csv", PARSED)
    lineups = load("gamebook_lineups.csv", PARSED)
    participation = load("gamebook_participation.csv", PARSED)
    injuries = load("injury_report.csv", PARSED)
    inactives = load("inactives.csv", PARSED)
    availability = load("availability_graph.csv")
    calibration = load("designation_calibration.csv")
    problems = load("capture_problems.csv")
    capture_log = load("capture_log.csv", os.path.join(DATA, "_capture"))

    # ---- the capture actually happened -----------------------------------
    check("capture ran", bool(games), "no game books were parsed")
    check(
        "every game book has a hash",
        all(re.fullmatch(r"[0-9a-f]{64}", g.get("gamebook_sha256", "")) for g in games),
        "a game book row has no valid SHA-256",
    )
    check(
        "every game book has an official URL",
        all(
            "nfl.com" in g.get("gamebook_url", "") and "nfl.com" in g.get("game_url", "")
            for g in games
        ),
        "a game book row has no official league URL",
    )
    check(
        "every game book row names both clubs",
        all(g.get("away_team") and g.get("home_team") for g in games),
        "a game book row has a blank club name",
    )
    check(
        "every game book row has a final score",
        all(g.get("away_score") and g.get("home_score") for g in games),
        "a game book row has no score",
    )
    check(
        "every game book row has a venue",
        all(g.get("stadium") for g in games),
        "a game book row has no stadium",
    )

    # ---- the lineups are complete ----------------------------------------
    per_game: dict[str, list[dict]] = {}
    for row in lineups:
        per_game.setdefault(row["game_slug"], []).append(row)
    check(
        "every game book yields 44 starters",
        all(len(v) == 44 for v in per_game.values()) and bool(per_game),
        "a game has a starter count other than 44",
    )
    check(
        "each game has 11 starters per side per unit",
        all(
            len([r for r in v if r["side"] == side and r["unit"] == unit]) == 11
            for v in per_game.values()
            for side in ("away", "home")
            for unit in ("offense", "defense")
        ),
        "a game has an unbalanced starting eleven",
    )
    check(
        "every starter has a position, a jersey and a name",
        all(r.get("position") and r.get("jersey") and r.get("player") for r in lineups),
        "a starter row has a blank field",
    )
    check(
        "every starter row names an official source",
        all("nfl.com" in r.get("source_url", "") for r in lineups),
        "a starter row has no official source",
    )

    # ---- participation ----------------------------------------------------
    roles = {r["role"] for r in participation}
    check(
        "participation records the three official roles",
        {"substitute", "did_not_play", "not_active"} <= roles,
        f"roles seen: {sorted(roles)}",
    )
    check(
        "every participation row names an official source",
        all("nfl.com" in r.get("source_url", "") for r in participation),
        "a participation row has no official source",
    )

    # ---- the availability graph ------------------------------------------
    check("availability graph is not empty", bool(availability), "no rows")
    check(
        "every availability row has an actual starter",
        all(r.get("actual_player") for r in availability),
        "an availability row has no actual starter",
    )
    check(
        "every availability row names an official source",
        all("nfl.com" in r.get("source_url", "") for r in availability),
        "an availability row has no official source",
    )
    check(
        "a replacement always carries a depth lower bound",
        all(
            r.get("replacement_string_lower_bound") != ""
            for r in availability
            if r.get("change_type") == "replaced"
        ),
        "a replacement has no depth lower bound",
    )
    check(
        "a depth lower bound is never below one",
        all(
            int(r["replacement_string_lower_bound"]) >= 1
            for r in availability
            if r.get("replacement_string_lower_bound")
        ),
        "a depth lower bound is below one",
    )
    check(
        "the depth lower bound equals the unavailable count plus one",
        all(
            int(r["replacement_string_lower_bound"]) == int(r["unavailable_ahead"]) + 1
            for r in availability
            if r.get("replacement_string_lower_bound") and r.get("unavailable_ahead")
        ),
        "the depth lower bound and the unavailable count disagree",
    )
    check(
        "no availability row infers a depth from a list order",
        all(
            "jersey" not in (r.get("note") or "").lower()
            or "not" in (r.get("note") or "").lower()
            for r in availability
        ),
        "an availability row claims a jersey-order depth",
    )

    # ---- the calibration ---------------------------------------------------
    check("calibration is not empty", bool(calibration), "no rows")
    for row in calibration:
        n = int(row["n"])
        check(
            f"calibration row '{row['designation']}' has n",
            n > 0,
            "n is zero",
        )
        rate = float(row["play_rate"])
        low = float(row["play_rate_ci95_low"])
        high = float(row["play_rate_ci95_high"])
        check(
            f"calibration row '{row['designation']}' interval contains the rate",
            low <= rate <= high,
            f"{low} <= {rate} <= {high} fails",
        )
        check(
            f"calibration row '{row['designation']}' interval is inside [0,1]",
            0.0 <= low <= 1.0 and 0.0 <= high <= 1.0,
            "interval outside [0,1]",
        )
        check(
            f"calibration row '{row['designation']}' counts add up",
            n == int(row["n_started"]) + int(row["n_played_off_bench"])
            + int(row["n_did_not_play"]) + int(row["n_inactive"])
            + int(row["n_not_in_game_book"]),
            "the outcome counts do not sum to n",
        )
        check(
            f"calibration row '{row['designation']}' names an official source",
            "nfl.com" in row.get("source_url", ""),
            "no official source",
        )

    # ---- the injury report rows ------------------------------------------
    check(
        "every injury row names an official source",
        all("nfl.com" in r.get("source_url", "") for r in injuries),
        "an injury row has no official source",
    )
    check(
        "every injury row has a club and a player",
        all(r.get("club") and r.get("player") for r in injuries),
        "an injury row has a blank club or player",
    )
    check(
        "every inactive row names an official source",
        all("nfl.com" in r.get("source_url", "") for r in inactives),
        "an inactive row has no official source",
    )

    # ---- the capture ledger ------------------------------------------------
    check("the capture ledger is not empty", bool(capture_log), "no rows")
    check(
        "every successful read has a hash and a clock time",
        all(
            re.fullmatch(r"[0-9a-f]{64}", r.get("sha256", ""))
            and r.get("fetched_at_utc")
            for r in capture_log
            if r.get("http_status") == "200"
        ),
        "a successful read has no hash or no clock time",
    )
    check(
        "every read is on an official host",
        all(
            any(host in r.get("url", "") for host in OFFICIAL_HOSTS)
            for r in capture_log
        ),
        "a read is not on an official NFL host",
    )

    # ---- the published pages ------------------------------------------------
    pages = [
        "index.html", "game-books.html", "availability.html", "calibration.html",
        "snapshots.html", "requirements.html", "flagged.html", "sources.html",
    ]
    for name in pages:
        path = os.path.join(DOCS, name)
        check(f"page {name} exists", os.path.exists(path), "missing")
    for name in pages:
        path = os.path.join(DOCS, name)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith("http"):
                check(
                    f"page {name} links to an official host",
                    any(host in href for host in OFFICIAL_HOSTS),
                    f"non-official link {href}",
                )
            elif not href.startswith("#"):
                target = os.path.join(DOCS, href)
                check(
                    f"page {name} link {href} resolves",
                    os.path.exists(target),
                    "broken internal link",
                )
    flagged_page = ""
    flagged_path = os.path.join(DOCS, "flagged.html")
    if os.path.exists(flagged_path):
        flagged_page = open(flagged_path, encoding="utf-8").read()
    for problem in problems:
        check(
            "every capture problem is published on the flagged page",
            problem["problem"][:60] in flagged_page,
            f"not published: {problem['problem'][:60]}",
        )

    # ---- the build is deterministic ------------------------------------------
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "build_nfl_a119bb6d.py")],
        capture_output=True,
        text=True,
    )
    check("the build runs", proc.returncode == 0, proc.stderr[-400:])
    diff = subprocess.run(
        ["git", "diff", "--name-only", "--", "data/nfl_a119bb6d", "docs/nfl-a119bb6d"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    check(
        "the build is a pure function of the committed data",
        diff.stdout.strip() == "",
        f"rebuild changed: {diff.stdout.strip()[:300]}",
    )

    print(f"{CHECKS[0] - len(FAILS)}/{CHECKS[0]} checks passed")
    for failure in FAILS:
        print(f"FAIL {failure}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
