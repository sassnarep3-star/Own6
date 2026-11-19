"""Parser for the official NFL Game Book.

The Game Book is the league's own document for a completed game. This module
turns the layout-preserving text of that document into structured facts and
nothing else: every field it returns was read off the page, and every field it
cannot find comes back empty so the caller can leave the cell blank rather
than guess.

The document layout that matters (and nothing else is assumed):

* a header line with the date, the match-up and the start time,
* a venue line, a roof/surface line and a game-day weather line,
* the officials block,
* a ``Lineups`` table with four columns -- visitor offense, visitor defense,
  home offense, home defense,
* three two-column blocks -- ``Substitutions``, ``Did Not Play`` and
  ``Not Active`` -- visitor column first, home column second,
* the score lines and the paid attendance.

Column boundaries are found from the *data* rather than from the header: the
gap between two adjacent columns is the run of spaces that separates them, and
the same boundary appears on every row of the block. The modal end position of
those runs is therefore the column start. No character offset is hard-coded, so
a document that lays its columns out differently still parses.
"""

from __future__ import annotations

import re
from collections import Counter

#: ``POS 12 A.Name`` -- the name may carry a second capitalised word
#: ("A.St. Brown") and a title prefix ("Dr.Jones").
PLAYER_RE = re.compile(
    r"(?P<pos>[A-Z0-9]{1,3})\s+(?P<jersey>\d{1,2})\s+"
    r"(?P<name>(?:[A-Z][A-Za-z'\-]*\.\s*){1,2}[A-Za-z][A-Za-z'\-]*)"
)

DATE_RE = re.compile(r"Date:\s*(?P<date>[A-Za-z]+,\s*\d{1,2}/\d{1,2}/\d{4})")
MATCHUP_RE = re.compile(
    r"Date:\s*[A-Za-z]+,\s*\d{1,2}/\d{1,2}/\d{4}\s+(?P<away>.+?)\s+at\s+"
    r"(?P<home>.+?)\s+Start Time:"
)
START_RE = re.compile(r"Start Time:\s*(?P<time>.+?)\s*$")
VENUE_RE = re.compile(
    r"^\s*at\s+(?P<stadium>.+?),\s*(?P<city>[^,]+(?:,\s*[A-Z]{2})?)\s*$"
)
ROOF_RE = re.compile(
    r"(?P<status>Retractable Roof\s*-\s*(?:Open|Closed)|Open Stadium|Closed Stadium)"
    r"(?:\s*-\s*|\s+on\s+)?\s*(?P<surface>.*)$"
)
WEATHER_RE = re.compile(
    r"Game Weather:\s*(?P<sky>.*?)\s+Temp:\s*(?P<temp_f>-?\d+)\s*.?\s*F\s*"
    r"\((?P<temp_c>-?\d+\.?\d*)\s*.?\s*C\)\s*Humidity:\s*(?P<humidity>\d+)%,\s*"
    r"Wind:\s*(?P<wind>[A-Z]{1,3}\s+\d+\s*mph)"
)
WIND_CHILL_RE = re.compile(r"Wind Chill:\s*(?P<chill>-?\d+)")
ATTENDANCE_RE = re.compile(r"Paid Attendance:\s*(?P<attendance>[\d,]+)")
SCORE_RE = re.compile(
    r"^(?P<side>VISITOR|HOME):\s*(?P<club>.+?)\s+(?P<q1>\d+)\s+(?P<q2>\d+)\s+"
    r"(?P<q3>\d+)\s+(?P<q4>\d+)\s+(?P<ot>\d+)\s+(?P<total>\d+)\s*$"
)
OFFICIAL_RE = re.compile(
    r"(?P<role>Referee|Umpire|Down Judge|Side Judge|Field Judge|Back Judge|"
    r"Replay Official|Line Judge):\s*(?P<name>[A-Za-z'\.\,\- ]+?)\s*\((?P<num>\d+)\)"
)
GAP_RE = re.compile(r" {8,}")


def _cluster(positions: list[int], tolerance: int = 2) -> list[int]:
    """Group near-identical positions and return the cluster centres."""
    clusters: list[list[int]] = []
    for pos in sorted(positions):
        for cluster in clusters:
            if abs(cluster[-1] - pos) <= tolerance:
                cluster.append(pos)
                break
        else:
            clusters.append([pos])
    scored = sorted(
        ((len(c), int(round(sum(c) / len(c)))) for c in clusters),
        key=lambda item: (-item[0], item[1]),
    )
    return [centre for _count, centre in scored]


def column_boundaries(lines: list[str], expected: int) -> list[int]:
    """Return the start offsets of the columns in a block of lines.

    ``expected`` is the number of columns the block has. The boundary of a
    column is the end of the run of spaces that separates it from the previous
    one; the modal such position across the block is the column start.
    """
    ends: list[int] = []
    for line in lines:
        for match in GAP_RE.finditer(line):
            ends.append(match.end())
    if not ends:
        return []
    centres = _cluster(ends)
    return sorted(centres[:expected])


def _split_cells(line: str, boundaries: list[int]) -> list[str]:
    """Split ``line`` at the given column start offsets."""
    cells = []
    previous = 0
    for start in boundaries:
        cells.append(line[previous:start].strip())
        previous = start
    cells.append(line[previous:].strip())
    return cells


def _clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


def parse_game_book(text: str, *, source_url: str = "", gamebook_sha256: str = "") -> dict:
    """Parse one Game Book's layout text.

    Returns a dictionary with the header facts, the lineups, the participation
    lists and a ``problems`` list. Every problem names a field that could not
    be read, so the caller can leave it blank and say why.
    """
    lines = text.splitlines()
    result: dict = {
        "source_url": source_url,
        "gamebook_sha256": gamebook_sha256,
        "date_et": "",
        "away_team": "",
        "home_team": "",
        "start_time": "",
        "stadium": "",
        "city": "",
        "roof_status": "",
        "surface": "",
        "weather_sky": "",
        "temp_f": "",
        "temp_c": "",
        "humidity_pct": "",
        "wind": "",
        "wind_chill": "",
        "attendance": "",
        "away_score": "",
        "home_score": "",
        "away_q1": "", "away_q2": "", "away_q3": "", "away_q4": "", "away_ot": "",
        "home_q1": "", "home_q2": "", "home_q3": "", "home_q4": "", "home_ot": "",
        "officials": [],
        "lineups": [],
        "substitutions": [],
        "did_not_play": [],
        "not_active": [],
        "problems": [],
    }
    problems = result["problems"]

    # ---- header -----------------------------------------------------------
    for raw in lines[:40]:
        line = raw.rstrip()
        if not line.strip():
            continue
        m = DATE_RE.search(line)
        if m and not result["date_et"]:
            result["date_et"] = m.group("date")
            mt = MATCHUP_RE.search(line)
            if mt:
                result["away_team"] = mt.group("away").strip()
                result["home_team"] = mt.group("home").strip()
            mtime = START_RE.search(line)
            if mtime:
                result["start_time"] = mtime.group("time").strip()
            continue
        mv = VENUE_RE.match(line)
        if mv and not result["stadium"]:
            result["stadium"] = mv.group("stadium").strip()
            result["city"] = mv.group("city").strip()
            continue
        mw = WEATHER_RE.search(line)
        if mw:
            result["weather_sky"] = mw.group("sky").strip()
            result["temp_f"] = mw.group("temp_f")
            result["temp_c"] = mw.group("temp_c")
            result["humidity_pct"] = mw.group("humidity")
            result["wind"] = mw.group("wind").strip()
            continue
        mc = WIND_CHILL_RE.search(line)
        if mc and not result["wind_chill"]:
            result["wind_chill"] = mc.group("chill")
        if "Roof" in line or re.search(r"\bStadium\s+on\b", line):
            mroof = ROOF_RE.search(line.strip())
            if mroof:
                result["roof_status"] = mroof.group("status").strip()
                surface = re.sub(r"\s+Wind Chill.*$", "", mroof.group("surface")).strip()
                result["surface"] = surface
                continue
        if mc:
            continue
        for mo in OFFICIAL_RE.finditer(line):
            result["officials"].append(
                {
                    "role": mo.group("role"),
                    "name": mo.group("name").strip(),
                    "number": mo.group("num"),
                }
            )

    if not result["away_team"] or not result["home_team"]:
        problems.append("matchup not read from the header line")
    if not result["stadium"]:
        problems.append("venue not read from the header block")
    if not result["roof_status"]:
        problems.append("roof/surface designation not found")
    if not result["weather_sky"]:
        problems.append("game-day weather not found")
    if not result["officials"]:
        problems.append("officials block not found")

    # ---- score and attendance --------------------------------------------
    for raw in lines:
        line = raw.strip()
        ms = SCORE_RE.match(line)
        if ms:
            side = ms.group("side")
            prefix = "away" if side == "VISITOR" else "home"
            for q in ("q1", "q2", "q3", "q4", "ot"):
                result[f"{prefix}_{q}"] = ms.group(q)
            result[f"{prefix}_score"] = ms.group("total")
            continue
        ma = ATTENDANCE_RE.search(line)
        if ma and not result["attendance"]:
            result["attendance"] = ma.group("attendance").replace(",", "")

    if not result["away_score"] or not result["home_score"]:
        problems.append("final score not read")

    # ---- lineups ----------------------------------------------------------
    header_idx = None
    for i, raw in enumerate(lines):
        if raw.strip() == "Lineups":
            header_idx = i
            break
    if header_idx is None:
        problems.append("'Lineups' block not found")
    else:
        rows: list[str] = []
        for raw in lines[header_idx + 1:]:
            stripped = raw.strip()
            if not stripped:
                if rows:
                    break
                continue
            if stripped.startswith("Substitutions"):
                break
            if "Offense" in stripped and "Defense" in stripped:
                continue
            # A real lineups row carries four players. The club-name row above
            # the table carries no jersey number and is skipped.
            if not PLAYER_RE.search(stripped):
                if rows:
                    break
                continue
            rows.append(raw)
            if len(rows) == 11:
                break
        if len(rows) < 11:
            problems.append(f"only {len(rows)} lineups rows read (11 expected)")
        boundaries = column_boundaries(rows, expected=3)
        for raw in rows[:11]:
            # The four cells of a row are the four player entries it holds.
            # Reading them with the entry pattern rather than with fixed
            # character offsets keeps the parse correct even when the
            # document's columns are not perfectly aligned.
            matches = list(PLAYER_RE.finditer(raw))
            if len(matches) != 4:
                problems.append(
                    f"lineups row holds {len(matches)} player entries (4 expected)"
                )
                continue
            for cell_index, m in enumerate(matches):
                side = "away" if cell_index < 2 else "home"
                unit = "offense" if cell_index % 2 == 0 else "defense"
                result["lineups"].append(
                    {
                        "side": side,
                        "unit": unit,
                        "position": m.group("pos"),
                        "jersey": m.group("jersey"),
                        "player": _clean_name(m.group("name")),
                    }
                )
        if len(result["lineups"]) != 44:
            problems.append(f"{len(result['lineups'])} starters read (44 expected)")

    # ---- two-column participation blocks ----------------------------------
    for label, key in (
        ("Substitutions", "substitutions"),
        ("Did Not Play", "did_not_play"),
        ("Not Active", "not_active"),
    ):
        block = _two_column_block(lines, label)
        if block is None:
            problems.append(f"'{label}' block not found")
            continue
        away_text, home_text = block
        result[key] = _parse_entry_list(away_text, "away")
        result[key].extend(_parse_entry_list(home_text, "home"))

    return result


def _two_column_block(lines: list[str], label: str) -> tuple[str, str] | None:
    """Return the (visitor, home) text of a two-column block.

    Each row of the block is split at the run of spaces that separates the two
    columns, so the split does not depend on where the columns happen to sit.
    A row that starts with a wide indent carries only the home column.
    """
    header_idx = None
    for i, raw in enumerate(lines):
        if raw.strip().startswith(label):
            header_idx = i
            break
    if header_idx is None:
        return None
    body: list[str] = []
    for raw in lines[header_idx + 1:]:
        stripped = raw.strip()
        if not stripped:
            if body:
                break
            continue
        if re.match(
            r"^(Field Goals|Scoring Plays|Final Individual|Time:|Paid Attendance|"
            r"National Football League)",
            stripped,
        ):
            break
        body.append(raw)
    if not body:
        return ("", "")
    left_parts: list[str] = []
    right_parts: list[str] = []
    for raw in body:
        indent = len(raw) - len(raw.lstrip())
        gaps = list(GAP_RE.finditer(raw))
        if indent >= 8 and not gaps:
            right_parts.append(raw.strip())
            left_parts.append("")
            continue
        if not gaps:
            left_parts.append(raw.strip())
            right_parts.append("")
            continue
        widest = max(gaps, key=lambda m: (m.end() - m.start(), m.start()))
        left_parts.append(raw[: widest.start()].strip())
        right_parts.append(raw[widest.end():].strip())
    return (" ".join(p for p in left_parts if p), " ".join(p for p in right_parts if p))


def _parse_entry_list(text: str, side: str) -> list[dict]:
    """Parse a comma-separated list of ``POS NUM Name`` entries."""
    entries: list[dict] = []
    if not text.strip():
        return entries
    flat = re.sub(r"\s+", " ", text).strip()
    for chunk in flat.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = PLAYER_RE.match(chunk)
        if not m:
            continue
        entries.append(
            {
                "side": side,
                "position": m.group("pos"),
                "jersey": m.group("jersey"),
                "player": _clean_name(m.group("name")),
            }
        )
    return entries
