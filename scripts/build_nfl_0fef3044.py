#!/usr/bin/env python3
"""Build the Week-11 official injury-hub capture pack (session 0fef3044).

Input : data/nfl_0fef3044/raw/injury_hub_week11_read_2026_11_19.txt  (verbatim transcription)
Output: data/nfl_0fef3044/*.csv  and  docs/nfl-0fef3044/*.html

No network access. Every output row is derived from the raw transcription, and every row
carries the official source URL it was read from. Blank official cells stay blank.
"""
from __future__ import annotations

import csv
import hashlib
import html
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data" / "nfl_0fef3044"
RAW = PACK / "raw" / "injury_hub_week11_read_2026_11_19.txt"
SLATE = ROOT / "data" / "nfl_0ce967db" / "week11_slate.csv"
DOCS = ROOT / "docs" / "nfl-0fef3044"
SOURCE_URL = "https://www.nfl.com/injuries/league/2026/reg11"
SLATE_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
SESSION = "0fef3044"
READ_UTC = "2026-11-19 after 12:09:34Z"
PLAYER_FIELDS = ["club", "player", "position", "injury", "practice_status", "game_status"]
EXPECTED_GAMES = 13
EXPECTED_CLUBS_ON_REPORT = 26
EXPECTED_BYE_CLUBS = {"ATL", "CLE", "GB", "LA", "NE", "SEA"}
GAME_STATUSES = ("Out", "Doubtful", "Questionable")
ALL_CLUBS = {
    "ATL", "AZ", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU",
    "IND", "JAX", "KC", "LAC", "LA", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT",
    "SEA", "SF", "TB", "TEN", "WAS",
}


class ParseError(ValueError):
    """Raised when the transcription does not match the expected layout (drift alarm)."""


def parse(text: str, source_url: str = SOURCE_URL) -> dict:
    games: list[dict] = []
    rows: list[dict] = []
    club_status: list[dict] = []
    game = None
    team = None
    for lineno, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.rstrip("\n")
        if not line or line.startswith(("VERBATIM", "Source URL", "Page title", "Read by", "Clock",
                                         "Hash", "Week-selector", "Field order", "Blank fields")):
            continue
        parts = line.split("|")
        kind = parts[0]
        if kind == "GAME":
            if len(parts) != 10:
                raise ParseError(f"line {lineno}: GAME header needs 10 fields, got {len(parts)}")
            _, day, kick, network, away, away_name, away_rec, home, home_name, home_rec = parts
            game = {
                "game_key": f"{away}@{home}", "date_et": day, "kickoff_et": kick,
                "network": network, "away": away, "home": home,
                "away_record": away_rec, "home_record": home_rec,
            }
            games.append(game)
            team = None
        elif kind == "TEAM":
            if game is None or len(parts) != 3:
                raise ParseError(f"line {lineno}: TEAM header outside a game or malformed")
            team = parts[1]
            if team not in (game["away"], game["home"]):
                raise ParseError(f"line {lineno}: TEAM {team} is not in game {game['game_key']}")
        elif kind == "NO INJURIES REPORTED" or (len(parts) == 2 and parts[1] == "NO INJURIES REPORTED"):
            club_status.append({"club": parts[0], "status": "No Injuries Reported",
                                "game_key": game["game_key"] if game else ""})
        else:
            if game is None or team is None:
                raise ParseError(f"line {lineno}: player row before any TEAM header")
            if len(parts) != 6:
                raise ParseError(f"line {lineno}: expected 6 fields, got {len(parts)}: {line!r}")
            club = parts[0]
            if club != team:
                raise ParseError(f"line {lineno}: row club {club} inside {team} block")
            if not parts[1].strip():
                raise ParseError(f"line {lineno}: blank player name")
            rows.append({
                "game_key": game["game_key"], "club": club, "player": parts[1].strip(),
                "position": parts[2].strip(), "injury": parts[3].strip(),
                "practice_status": parts[4].strip(), "game_status": parts[5].strip(),
            })
    return {"games": games, "rows": rows, "club_status": club_status, "source_url": source_url}


def validate(parsed: dict) -> list[str]:
    """Drift alarm: returns a list of failures. Empty list means the pack is consistent."""
    problems: list[str] = []
    games = parsed["games"]
    rows = parsed["rows"]
    if len(games) != EXPECTED_GAMES:
        problems.append(f"expected {EXPECTED_GAMES} game headers, found {len(games)}")
    clubs_seen = {r["club"] for r in rows} | {c["club"] for c in parsed["club_status"]}
    if len(clubs_seen) != EXPECTED_CLUBS_ON_REPORT:
        problems.append(f"expected {EXPECTED_CLUBS_ON_REPORT} clubs on report, found {len(clubs_seen)}")
    missing = ALL_CLUBS - clubs_seen
    if missing != EXPECTED_BYE_CLUBS:
        problems.append(f"clubs absent from report {sorted(missing)} differ from expected bye list")
    for r in rows:
        for f in ("club", "player", "practice_status"):
            if not r[f]:
                problems.append(f"required field {f} blank for {r['player']!r}")
        if r["game_status"] and r["game_status"] not in GAME_STATUSES:
            problems.append(f"unexpected game status {r['game_status']!r} for {r['player']!r}")
    keys = [(r["club"], r["player"]) for r in rows]
    dupes = [k for k, n in Counter(keys).items() if n > 1]
    if dupes:
        problems.append(f"duplicate club/player rows: {dupes}")
    return problems


def load_slate() -> dict:
    out = {}
    with SLATE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out[f"{r['away']}@{r['home']}"] = r
    return out


def reconcile(parsed: dict) -> list[dict]:
    slate = load_slate()
    result = []
    for g in parsed["games"]:
        s = slate.get(g["game_key"])
        slate_kick = s["kickoff_et"].replace(" ", "") if s else ""
        report_kick = g["kickoff_et"].replace(" PM", "PM").replace(" AM", "AM").replace(" ET", "")
        result.append({
            "game_key": g["game_key"],
            "report_kickoff": g["kickoff_et"],
            "slate_game_id": s["game_id"] if s else "",
            "slate_kickoff": s["kickoff_et"] if s else "",
            "slate_network": s["network"] if s else "",
            "report_network": g["network"],
            "matches_slate_pairing": "yes" if s else "no",
            "matches_slate_kickoff": "yes" if s and slate_kick == report_kick.replace(" ", "") else "no",
            "source_url": SOURCE_URL,
            "slate_source_url": SLATE_URL,
        })
    return result


OTHER_READ = ROOT / "data" / "nfl_ade166a4" / "injuries_reg11_b.csv"


def cross_read(parsed: dict, raw_text: str) -> list[dict]:
    """Compare every player row with the independent 11:07Z same-day read in data/nfl_ade166a4."""
    nick = {}
    for line in raw_text.splitlines():
        if line.startswith("GAME|"):
            f = line.split("|")
            nick[f[5]] = f[4]
            nick[f[8]] = f[7]
    mine = Counter((r["club"], r["player"], r["position"], r["injury"], r["practice_status"], r["game_status"])
                   for r in parsed["rows"])
    other = Counter()
    other_placeholder = 0
    with OTHER_READ.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["player"].strip().startswith("(no injuries reported"):
                other_placeholder += 1
                continue
            other[(nick.get(r["team"], "?"), r["player"], r["position"], r["injury"],
                   r["practice_status"], r["game_status"])] += 1
    exact = sum((mine & other).values())
    return [{
        "compared_read": "data/nfl_ade166a4/injuries_reg11_b.csv (read 2026-11-19T11:06:58Z-11:12:05Z)",
        "this_read_player_rows": sum(mine.values()),
        "other_read_player_rows": sum(other.values()),
        "exact_row_matches": exact,
        "only_in_this_read": sum((mine - other).values()),
        "only_in_other_read": sum((other - mine).values()),
        "other_read_placeholder_rows": other_placeholder,
        "unmapped_club_rows_in_other_read": other.get(("?", "", "", "", "", ""), 0),
        "source_url": SOURCE_URL,
    }]


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def club_summary(parsed: dict) -> list[dict]:
    by_club: "OrderedDict[str, Counter]" = OrderedDict()
    for r in parsed["rows"]:
        c = by_club.setdefault(r["club"], Counter())
        c["rows"] += 1
        c[f"game:{r['game_status'] or 'blank'}"] += 1
        c[f"practice:{r['practice_status'] or 'blank'}"] += 1
    out = []
    for club in sorted(by_club):
        c = by_club[club]
        out.append({
            "club": club,
            "rows": c["rows"],
            "game_out": c["game:Out"],
            "game_doubtful": c["game:Doubtful"],
            "game_questionable": c["game:Questionable"],
            "game_blank": c["game:blank"],
            "practice_dnp": c["practice:Did Not Participate In Practice"],
            "practice_lp": c["practice:Limited Participation in Practice"],
            "practice_fp": c["practice:Full Participation in Practice"],
            "source_url": SOURCE_URL,
        })
    return out


def capture_log(raw_bytes: bytes, parsed: dict) -> list[dict]:
    return [{
        "capture_id": f"{SESSION}-W11-01",
        "source_url": SOURCE_URL,
        "read_utc": READ_UTC,
        "week": 11,
        "games": len(parsed["games"]),
        "player_rows": len(parsed["rows"]),
        "clubs_with_rows_or_clean_status": len({r["club"] for r in parsed["rows"]} | {c["club"] for c in parsed["club_status"]}),
        "raw_file": str(RAW.relative_to(ROOT)),
        "raw_sha256_of_transcription": hashlib.sha256(raw_bytes).hexdigest(),
        "official_bytes_hash": "not available (no shell route to nfl.com; fetch tool returns extracted text)",
        "delta_vs_prior_week11_read": "none: first Week-11 read in this repository",
    }]


def flags(parsed: dict, recon: list[dict]) -> list[dict]:
    rows = parsed["rows"]
    return [
        {"flag_id": f"{SESSION.upper()[:4]}-F01", "severity": "medium",
         "topic": "roster-affiliation (carry-forward)",
         "observation": "Jaylen Waddle is listed under DEN (Broncos) on the Week 11 report and is not listed under MIA. "
                        "This is the same observation as open flag ADE-F01. The read here is independent and matches it.",
         "status": "open", "source_url": SOURCE_URL,
         "related": "ADE-F01 (data/nfl_ade166a4/flagged.csv)"},
        {"flag_id": f"{SESSION.upper()[:4]}-F02", "severity": "low", "topic": "absent clubs",
         "observation": "Six clubs (ATL, CLE, GB, LA, NE, SEA) have no table on the Week 11 report. "
                        "The schedule read in data/nfl_0ce967db lists the same six as on bye. "
                        "The injury page itself does not print a bye label, so the bye status is confirmed only by the schedule page.",
         "status": "reconciled to schedule read; not independently re-read", "source_url": SLATE_URL,
         "related": "data/nfl_0ce967db/raw/week11_slate_read_2026_11_18.txt"},
        {"flag_id": f"{SESSION.upper()[:4]}-F03", "severity": "medium", "topic": "Detroit game status blank",
         "observation": "Kerby Joseph (S), Cade Mays (C) and D.J. Reed (CB) appear on the Week 11 report with a blank Game Status. "
                        "The Week 10 read in data/nfl_0ce967db listed all three as Out. Those are different weeks, so the Week 10 "
                        "value is not carried forward. A blank game status is left blank here and is not treated as Out or Available.",
         "status": "open", "source_url": SOURCE_URL, "related": "VR-08/VR-12 (data/nfl_0ce967db/flagged.csv)"},
        {"flag_id": f"{SESSION.upper()[:4]}-F04", "severity": "medium", "topic": "capture precision",
         "observation": "The fetch tool returns no per-request timestamp and no raw HTML bytes. The read time is recorded as "
                        "'after 12:09:34Z' and the file hash covers this transcription only, not official bytes.",
         "status": "limitation (recorded)", "source_url": SOURCE_URL, "related": ""},
        {"flag_id": f"{SESSION.upper()[:4]}-F05", "severity": "low", "topic": "name transcription",
         "observation": "Two names differ between the displayed name and the profile link slug on the page: Jacob Hummel (slug jake-hummel) "
                        "and Dee Alford (slug deaundre-ford). The displayed name is used; the slug is not used as a source.",
         "status": "recorded", "source_url": SOURCE_URL, "related": ""},
    ]


def count_designations(parsed: dict) -> Counter:
    c = Counter()
    for r in parsed["rows"]:
        c[r["game_status"] or "(blank)"] += 1
    return c


def html_escape(v) -> str:
    return html.escape(str(v), quote=True)


CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1d2330;background:#f7f8fa;line-height:1.45}
header{background:#14213d;color:#fff;padding:18px 24px}
header a{color:#ffd166}
main{max-width:1200px;margin:0 auto;padding:18px 24px 48px}
h1{font-size:1.5rem;margin:0 0 4px}h2{font-size:1.15rem;margin:26px 0 8px}
.note{background:#fff;border-left:4px solid #3a86ff;padding:10px 14px;margin:12px 0;border-radius:4px}
.warn{border-left-color:#e63946}
.tiles{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.tile{background:#fff;border-radius:6px;padding:10px 14px;min-width:150px;box-shadow:0 1px 2px #0001}
.tile b{display:block;font-size:1.3rem}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.88rem}
th,td{border-bottom:1px solid #e3e6ec;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#eef1f6;position:sticky;top:0}
input#f{padding:7px 10px;width:320px;max-width:100%;margin:6px 0;border:1px solid #bbb;border-radius:4px}
nav a{margin-right:14px}
.wrap{overflow-x:auto}
"""


def page(title: str, body: str, active: str) -> str:
    nav = [("index.html", "Week 11 report"), ("flagged.html", "Flagged for Review"),
           ("../index.html", "Repository home")]
    links = " ".join(f'<a href="{href}">{label}</a>' for href, label in nav)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_escape(title)} · Own6 NFL</title>
<style>{CSS}</style></head>
<body>
<header><div><strong>Own6 · NFL official injury-hub capture</strong> &nbsp;|&nbsp; session {SESSION}</div>
<nav style="margin-top:8px">{links}</nav></header>
<main>
{body}
</main></body></html>
"""


def render(parsed: dict, recon: list[dict], summary: list[dict], flag_rows: list[dict], log: list[dict]) -> dict[str, str]:
    rows = parsed["rows"]
    desig = count_designations(parsed)
    tiles = "".join(
        f'<div class="tile"><b>{v}</b>{html_escape(k)}</div>' for k, v in [
            ("games on report", len(parsed["games"])),
            ("clubs with rows or 'No Injuries Reported'", log[0]["clubs_with_rows_or_clean_status"]),
            ("player rows", len(rows)),
            ("Out (game status)", desig.get("Out", 0)),
            ("Doubtful", desig.get("Doubtful", 0)),
            ("Questionable", desig.get("Questionable", 0)),
            ("blank game status", desig.get("(blank)", 0)),
        ])
    body_rows = []
    for r in rows:
        body_rows.append(
            "<tr>" + "".join(f"<td>{html_escape(r[k]) or '&nbsp;'}</td>" for k in
                             ["game_key", "club", "player", "position", "injury", "practice_status", "game_status"])
            + f'<td><a href="{SOURCE_URL}">NFL.com injury report</a></td></tr>')
    for c in parsed["club_status"]:
        body_rows.append(
            f"<tr><td>{html_escape(c['game_key'])}</td><td>{html_escape(c['club'])}</td><td colspan='5'><em>"
            f"{html_escape(c['status'])}</em></td>"
            f'<td><a href="{SOURCE_URL}">NFL.com injury report</a></td></tr>')
    rows_html = "".join(body_rows)
    summary_html = "".join(
        f"<tr><td>{s['club']}</td><td>{s['rows']}</td><td>{s['game_out']}</td><td>{s['game_doubtful']}</td>"
        f"<td>{s['game_questionable']}</td><td>{s['game_blank']}</td><td>{s['practice_dnp']}</td>"
        f"<td>{s['practice_lp']}</td><td>{s['practice_fp']}</td><td><a href='{SOURCE_URL}'>NFL.com</a></td></tr>"
        for s in summary)
    recon_html = "".join(
        f"<tr><td>{r['game_key']}</td><td>{html_escape(r['report_kickoff'])}</td><td>{html_escape(r['slate_kickoff'])}</td>"
        f"<td>{html_escape(r['report_network'])}</td><td>{html_escape(r['slate_network'])}</td>"
        f"<td>{r['matches_slate_pairing']}</td><td>{r['matches_slate_kickoff']}</td>"
        f"<td><a href='{SLATE_URL}'>NFL.com schedule</a></td></tr>" for r in recon)
    index_body = f"""
<h1>Week 11 official injury report — dated capture</h1>
<p>First dated read of the Week 11 page in this repository. Values are copied from
<a href="{SOURCE_URL}">{SOURCE_URL}</a> as displayed. Blank cells are blank on the official page and are
<strong>not</strong> filled in. No delta is published yet because no earlier Week 11 read exists here.</p>
<div class="tiles">{tiles}</div>
<div class="note warn"><strong>Not betting advice.</strong> Designations are shown as published. Nothing on this page is a
probability, pick, price or edge. Capture limits (no official bytes, approximate clock) are on the
<a href="flagged.html">Flagged for Review</a> page.</div>

<h2>Club summary (player rows only)</h2>
<div class="wrap"><table><thead><tr><th>Club</th><th>Rows</th><th>Out</th><th>Doubtful</th><th>Questionable</th>
<th>Game status blank</th><th>DNP</th><th>LP</th><th>FP</th><th>Source</th></tr></thead><tbody>
{summary_html}
</tbody></table></div>

<h2>Game reconciliation against the official Week 11 schedule read</h2>
<div class="wrap"><table><thead><tr><th>Game</th><th>Report kickoff</th><th>Schedule kickoff</th><th>Report network</th><th>Schedule network</th><th>Pairing matches schedule</th><th>Kickoff matches schedule</th><th>Source</th></tr></thead><tbody>
{recon_html}
</tbody></table></div>

<h2>All player rows (as read)</h2>
<p>Filter: <input id="f" placeholder="type a club, player, injury or status" oninput="flt()"></p>
<div class="wrap"><table id="t"><thead><tr><th>Game</th><th>Club</th><th>Player</th><th>Pos</th><th>Injury</th><th>Practice</th><th>Game status</th><th>Source</th></tr></thead><tbody>
{rows_html}
</tbody></table></div>
<script>
function flt(){{var q=document.getElementById('f').value.toLowerCase();
document.querySelectorAll('#t tbody tr').forEach(function(r){{r.style.display=r.textContent.toLowerCase().indexOf(q)>-1?'':'none';}});}}
</script>
"""
    flag_html = "".join(
        f"<tr><td>{html_escape(f['flag_id'])}</td><td>{html_escape(f['severity'])}</td><td>{html_escape(f['topic'])}</td>"
        f"<td>{html_escape(f['observation'])}</td><td>{html_escape(f['status'])}</td>"
        f"<td><a href='{f['source_url']}'>source</a></td><td>{html_escape(f['related'])}</td></tr>" for f in flag_rows)
    flagged_body = f"""
<h1>Flagged for Review</h1>
<p>Items below are published with their source links and remain open until the owner decides. They do not block anything.</p>
<div class="wrap"><table><thead><tr><th>ID</th><th>Severity</th><th>Topic</th><th>Observation</th><th>Status</th><th>Source</th><th>Related</th></tr></thead>
<tbody>{flag_html}</tbody></table></div>
"""
    return {"index.html": page("Week 11 injury capture", index_body, "index"),
            "flagged.html": page("Flagged for Review", flagged_body, "flagged")}


def main(argv: list[str]) -> int:
    raw_bytes = RAW.read_bytes()
    parsed = parse(raw_bytes.decode("utf-8"))
    problems = validate(parsed)
    if problems:
        for p in problems:
            print("DRIFT:", p, file=sys.stderr)
        return 1
    recon = reconcile(parsed)
    summary = club_summary(parsed)
    log = capture_log(raw_bytes, parsed)
    flag_rows = flags(parsed, recon)
    cross = cross_read(parsed, raw_bytes.decode("utf-8"))

    PACK.mkdir(parents=True, exist_ok=True)
    write_csv(PACK / "injury_week11_rows.csv",
              ["game_key", "club", "player", "position", "injury", "practice_status", "game_status", "source_url"],
              [{**r, "source_url": SOURCE_URL} for r in parsed["rows"]])
    write_csv(PACK / "club_status_week11.csv", ["game_key", "club", "status", "source_url"],
              [{**c, "source_url": SOURCE_URL} for c in parsed["club_status"]])
    write_csv(PACK / "club_summary_week11.csv",
              ["club", "rows", "game_out", "game_doubtful", "game_questionable", "game_blank",
               "practice_dnp", "practice_lp", "practice_fp", "source_url"], summary)
    write_csv(PACK / "slate_reconciliation.csv",
              ["game_key", "report_kickoff", "slate_game_id", "slate_kickoff", "slate_network", "report_network",
               "matches_slate_pairing", "matches_slate_kickoff", "source_url", "slate_source_url"], recon)
    write_csv(PACK / "capture_log.csv", list(log[0].keys()), log)
    write_csv(PACK / "cross_read_check.csv", list(cross[0].keys()), cross)
    write_csv(PACK / "flags.csv", ["flag_id", "severity", "topic", "observation", "status", "source_url", "related"], flag_rows)

    DOCS.mkdir(parents=True, exist_ok=True)
    for name, text in render(parsed, recon, summary, flag_rows, log).items():
        (DOCS / name).write_text(text, encoding="utf-8")
    print(f"ok: {len(parsed['games'])} games, {len(parsed['rows'])} player rows, "
          f"{len(parsed['club_status'])} clean-status clubs, {len(flag_rows)} flags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
