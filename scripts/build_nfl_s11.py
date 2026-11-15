#!/usr/bin/env python3
"""Build the nfl_s11 pack: Week 10 injury transcription reconciliation, Week 11 venue table,
Flagged for Review and sources pages under docs/nfl-s11/.

Inputs (all in the repo):
  data/nfl_s11/injury_report_w10_transcription.psv   transcription of https://www.nfl.com/injuries/ (read 2026-11-15)
  data/nfl_d966f630/injury_report_rows.csv           repo pack d966f630 injury rows (read 2026-11-14)
  data/nfl_309921cc/week10_injuries.csv              repo pack 309921cc Week 10 rows
  data/nfl_s11/schedule_w11_venues.csv               Week 11 venues read from official game-centre pages
  data/nfl_s11/flagged.csv, data/nfl_s11/sources.csv hand-maintained registers

Outputs:
  data/nfl_s11/injury_reconciliation_w10.csv         every field-level and roster-level difference
  docs/nfl-s11/*.html                                static pages (no input controls)

No value is inferred. A blank cell stays blank and is labelled as blank.
"""
import csv
import html
import os
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S11 = os.path.join(ROOT, "data", "nfl_s11")
DOCS = os.path.join(ROOT, "docs", "nfl-s11")
PSV = os.path.join(S11, "injury_report_w10_transcription.psv")
D966 = os.path.join(ROOT, "data", "nfl_d966f630", "injury_report_rows.csv")
P309 = os.path.join(ROOT, "data", "nfl_309921cc", "week10_injuries.csv")
VENUES = os.path.join(S11, "schedule_w11_venues.csv")
FLAGGED = os.path.join(S11, "flagged.csv")
SOURCES = os.path.join(S11, "sources.csv")
RECON = os.path.join(S11, "injury_reconciliation_w10.csv")

INJURY_URL = "https://www.nfl.com/injuries/"
READ_DATE = "2026-11-15"
PSV_FIELDS = ["game_no", "day_time_et", "club", "player", "position", "injuries", "practice_status", "game_status"]


def read_transcription(path=PSV):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip()]
    header = lines[0].split("|")
    if header != PSV_FIELDS:
        raise ValueError(f"unexpected header {header}")
    rows = []
    for n, line in enumerate(lines[1:], start=2):
        parts = line.split("|")
        if len(parts) != len(PSV_FIELDS):
            raise ValueError(f"line {n} has {len(parts)} fields")
        rows.append(dict(zip(PSV_FIELDS, parts)))
    return rows


def club_norm(code):
    # Repo packs use LA for the Rams and the injury page prints LAR; page prints AZ, transcription uses ARI.
    return {"LA": "LAR", "AZ": "ARI"}.get(code, code)


def read_d966(path=D966):
    out = []
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out.append({
                "club": club_norm(r["club"]),
                "player": r["player"],
                "position": r["position"],
                "injuries": r["injury_text"],
                "practice_status": r["practice_status"],
                "game_status": r["game_status"],
            })
    return out


def read_309921(path=P309):
    out = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            out.append({
                "club": club_norm(r["team_abbr"]),
                "player": r["player"],
                "position": r["position"],
                "injuries": r["injury"],
                "practice_status": r["practice_status"],
                "game_status": r["game_status"],
            })
    return out


def keyed(rows):
    d = defaultdict(list)
    for r in rows:
        d[(r["club"], r["player"], r["position"])].append(r)
    return d


def reconcile(trans, repo):
    """Field-level differences between transcription and d966f630, plus roster-level gaps vs 309921cc."""
    issues = []
    tk, rk = keyed(trans), keyed(repo)
    for k in sorted(set(tk) | set(rk)):
        if k not in rk:
            issues.append(dict(kind="player_only_in_transcription", club=k[0], player=k[1], position=k[2],
                               field="row", page_value="present", repo_value="absent"))
            continue
        if k not in tk:
            issues.append(dict(kind="player_only_in_repo", club=k[0], player=k[1], position=k[2],
                               field="row", page_value="absent", repo_value="present"))
            continue
        t, r = tk[k][0], rk[k][0]
        for f in ("injuries", "practice_status", "game_status"):
            tv = (t[f] or "").strip()
            rv = (r[f] or "").strip()
            if tv != rv:
                issues.append(dict(kind="field_mismatch", club=k[0], player=k[1], position=k[2],
                                   field=f, page_value=tv, repo_value=rv))
    return issues


def roster_gap_309921(trans, p309):
    """Player-level gaps between the transcription and pack 309921cc (326 rows)."""
    tk, pk = keyed(trans), keyed(p309)
    gaps = []
    for k in sorted(set(tk) | set(pk)):
        if k not in pk:
            gaps.append(dict(kind="missing_in_309921cc", club=k[0], player=k[1], position=k[2],
                             field="row", page_value="present", repo_value="absent"))
        elif k not in tk:
            gaps.append(dict(kind="extra_in_309921cc", club=k[0], player=k[1], position=k[2],
                             field="row", page_value="absent", repo_value="present"))
    return gaps


def write_reconciliation(issues, gaps):
    fields = ["issue_id", "kind", "club", "player", "position", "field", "page_value_transcribed",
              "repo_value", "source_url", "read_date", "status"]
    rows = []
    for i, x in enumerate(issues, start=1):
        if x["kind"] == "field_mismatch":
            status = "page value used; repo value differs from live page; needs correction in source pack"
        else:
            status = "roster-level difference; flagged, not resolved"
        rows.append(dict(issue_id=f"RC-{i:03d}", kind=x["kind"], club=x["club"], player=x["player"],
                         position=x["position"], field=x["field"], page_value_transcribed=x["page_value"],
                         repo_value=x["repo_value"], source_url=INJURY_URL, read_date=READ_DATE, status=status))
    base = len(rows)
    for j, x in enumerate(gaps, start=1):
        rows.append(dict(issue_id=f"RC-{base + j:03d}", kind=x["kind"], club=x["club"], player=x["player"],
                         position=x["position"], field=x["field"], page_value_transcribed=x["page_value"],
                         repo_value=x["repo_value"], source_url=INJURY_URL, read_date=READ_DATE,
                         status="roster-level difference between packs; flagged, not resolved"))
    with open(RECON, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return rows


def read_csv(path):
    """Read a register; every row must have exactly the header's number of fields."""
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    width = len(reader.fieldnames or [])
    for n, r in enumerate(rows, start=2):
        if None in r or any(v is None for v in r.values()) or len(r) != width:
            raise ValueError(f"{os.path.basename(path)} line {n}: expected {width} fields")
    return rows


GITHUB_BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"


def source_href(url):
    """Repo references are published as GitHub blob links (the gate rejects bare relative or repo: links)."""
    if url.startswith("repo:"):
        return GITHUB_BLOB + url[len("repo:"):]
    return url


PAGE_CSS = """body{font-family:system-ui,sans-serif;margin:24px;line-height:1.45;color:#111}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border:1px solid #ccc;padding:4px 6px;text-align:left;vertical-align:top}
th{background:#f2f2f2}nav a{margin-right:12px}.note{color:#444;font-size:13px}"""


def page(title, body):
    nav = ('<nav><a href="index.html">Home</a><a href="injuries-w10.html">Week 10 injuries</a>'
           '<a href="reconciliation-w10.html">Reconciliation</a><a href="venues-w11.html">Week 11 venues</a>'
           '<a href="flagged.html">Flagged for Review</a><a href="sources.html">Sources</a></nav>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)} | Own6 NFL S11</title><style>{PAGE_CSS}</style></head>'
            f'<body>{nav}<h1>{html.escape(title)}</h1>{body}</body></html>\n')


def link(url, text=None):
    text = text or url
    return f'<a href="{html.escape(url)}" rel="noopener">{html.escape(text)}</a>'


def table(headers, rows_html):
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows_html)}</tbody></table>"


def cell(v):
    v = "" if v is None else str(v)
    return f"<td>{html.escape(v) if v else '<span class=note>blank</span>'}</td>"


def build_injuries(trans):
    head = ["Game", "Day / time (ET)", "Club", "Player", "Pos", "Injuries", "Practice status", "Game status", "Source"]
    body = []
    for r in trans:
        body.append("<tr>" + cell(r["game_no"]) + cell(r["day_time_et"]) + cell(r["club"]) + cell(r["player"])
                    + cell(r["position"]) + cell(r["injuries"]) + cell(r["practice_status"]) + cell(r["game_status"])
                    + f"<td>{link(INJURY_URL, 'nfl.com/injuries')}</td></tr>")
    intro = (f"<p>{len(trans)} rows, 14 games, 28 clubs, transcribed from the official NFL Week 10 injury report "
             f"read {READ_DATE}. A blank game status means the page printed no game status for that player; "
             f"it does not mean the player is healthy. The page has no published timestamp; the read date is ours.</p>")
    return page("Week 10 injury report (transcription)", intro + table(head, body))


def build_recon(rows):
    head = ["ID", "Kind", "Club", "Player", "Field", "Page (transcribed)", "Repo d966f630", "Status", "Source"]
    body = []
    for r in rows:
        body.append("<tr>" + cell(r["issue_id"]) + cell(r["kind"]) + cell(r["club"]) + cell(r["player"])
                    + cell(r["field"]) + cell(r["page_value_transcribed"]) + cell(r["repo_value"])
                    + cell(r["status"]) + f"<td>{link(INJURY_URL, 'nfl.com/injuries')}</td></tr>")
    intro = ("<p>Field-level and roster-level differences between the live-page transcription and the repo packs. "
             "Page values are used. Repo values are shown exactly as stored; they are not corrected here.</p>")
    return page("Week 10 reconciliation", intro + table(head, body))


def build_venues(venues):
    head = ["Game", "Day", "Date (2026)", "Time (ET)", "Network", "Away", "Home", "Venue", "City", "State", "Source"]
    body = []
    for v in venues:
        body.append("<tr>" + cell(v["game_id"]) + cell(v["day"]) + cell(v["date_2026"]) + cell(v["time_et"])
                    + cell(v["network_as_rendered"]) + cell(v["away_club"]) + cell(v["home_club"])
                    + cell(v["venue_stadium"]) + cell(v["venue_city"]) + cell(v["venue_state"])
                    + f"<td>{link(v['venue_source_url'], 'game centre')}</td></tr>")
    intro = ("<p>Venue of each Week 11 fixture from the official game-centre Game Info. Times and networks are "
             "as rendered on the official schedule page; no bye or record values are published here.</p>")
    return page("Week 11 venues", intro + table(head, body))


def build_flagged(flags):
    head = ["ID", "Item", "Detail", "Source", "Blocks publish?"]
    body = []
    for f in flags:
        body.append("<tr>" + cell(f["flag_id"]) + cell(f["item"]) + cell(f["detail"])
                    + (f"<td>{link(f['source_url'])}</td>" if f["source_url"] else "<td><span class=note>blank</span></td>")
                    + cell(f["blocks_publish"]) + "</tr>")
    return page("Flagged for Review", table(head, body))


def build_sources(srcs):
    head = ["ID", "Source", "Used for", "Read date", "Result"]
    body = []
    for s in srcs:
        body.append("<tr>" + cell(s["source_id"]) + f"<td>{link(source_href(s['url']), s['url'])}</td>" + cell(s["used_for"])
                    + cell(s["read_date"]) + cell(s["result"]) + "</tr>")
    return page("Sources", table(head, body))


def build_index(counts):
    body = ("<p>Week 10 injury report transcription, reconciliation, Week 11 venue table, flagged items and sources. "
            "Every row links to the official nfl.com page it was read from. Blank cells are unverified or absent, "
            "never inferred.</p><ul>"
            f"<li>Week 10 injury rows: {counts['injury']} (14 games, 28 clubs)</li>"
            f"<li>Reconciliation items: {counts['recon']} (field-level and roster-level)</li>"
            f"<li>Week 11 venues read: {counts['venues']} of 13</li>"
            f"<li>Flagged for Review items: {counts['flags']}</li></ul>"
            "<p>No betting, stake, pick or profitability content on these pages.</p>")
    return page("NFL S11 — Week 10 injuries and Week 11 venues", body)


def main():
    trans = read_transcription()
    repo = read_d966()
    p309 = read_309921()
    issues = reconcile(trans, repo)
    gaps = roster_gap_309921(trans, p309)
    recon = write_reconciliation(issues, gaps)
    venues = read_csv(VENUES)
    flags = read_csv(FLAGGED)
    srcs = read_csv(SOURCES)
    os.makedirs(DOCS, exist_ok=True)
    out = {
        "index.html": build_index({"injury": len(trans), "recon": len(recon), "venues": len(venues), "flags": len(flags)}),
        "injuries-w10.html": build_injuries(trans),
        "reconciliation-w10.html": build_recon(recon),
        "venues-w11.html": build_venues(venues),
        "flagged.html": build_flagged(flags),
        "sources.html": build_sources(srcs),
    }
    for name, content in out.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as fh:
            fh.write(content)
    print(f"injury rows={len(trans)} field_mismatches={len(issues)} roster_gaps={len(gaps)} venues={len(venues)} flags={len(flags)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
