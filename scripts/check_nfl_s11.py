#!/usr/bin/env python3
"""Drift alarm and line-by-line checker for the nfl_s11 pack.

Pinned facts (from the live nfl.com Week 10 injury page read 2026-11-15, 8 chunks):
  347 injury rows, 14 games, 28 clubs; 14 players with 28 field-level mismatches vs d966f630;
  21 roster-level gaps vs 309921cc (326 rows); 13 Week 11 venues; 14 flagged items.
Exit code 0 = all checks pass; 1 = at least one check failed (printed).
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import build_nfl_s11 as b  # noqa: E402

ALLOWED_HOSTS = {"www.nfl.com", "nfl.com", "github.com"}
PINNED = {"injury_rows": 347, "games": 14, "clubs": 28, "field_mismatch_players": 14,
          "field_mismatch_fields": 28, "roster_gaps": 21, "venues": 13, "flags": 14}


def check_injuries(errors):
    trans = b.read_transcription()
    if len(trans) != PINNED["injury_rows"]:
        errors.append(f"injury rows {len(trans)} != {PINNED['injury_rows']}")
    games = {r["game_no"] for r in trans}
    if len(games) != PINNED["games"]:
        errors.append(f"games {len(games)} != {PINNED['games']}")
    clubs = {r["club"] for r in trans}
    if len(clubs) != PINNED["clubs"]:
        errors.append(f"clubs {len(clubs)} != {PINNED['clubs']}")
    for r in trans:
        for f in b.PSV_FIELDS:
            if f not in r:
                errors.append(f"missing field {f}")
        if not r["player"].strip() or not r["club"].strip():
            errors.append(f"blank player/club in game {r['game_no']}")
    return trans


def check_reconciliation(errors, trans):
    repo = b.read_d966()
    p309 = b.read_309921()
    issues = b.reconcile(trans, repo)
    gaps = b.roster_gap_309921(trans, p309)
    players = {(x["club"], x["player"]) for x in issues if x["kind"] == "field_mismatch"}
    if len(players) != PINNED["field_mismatch_players"]:
        errors.append(f"field-mismatch players {len(players)} != {PINNED['field_mismatch_players']}")
    fields = [x for x in issues if x["kind"] == "field_mismatch"]
    if len(fields) != PINNED["field_mismatch_fields"]:
        errors.append(f"field-mismatch fields {len(fields)} != {PINNED['field_mismatch_fields']}")
    if len(gaps) != PINNED["roster_gaps"]:
        errors.append(f"roster gaps {len(gaps)} != {PINNED['roster_gaps']}")
    if any(g["kind"] != "missing_in_309921cc" for g in gaps):
        errors.append("roster gaps include rows present only in 309921cc; reconcile before publishing")
    # The published reconciliation CSV must match the recomputed one.
    with open(b.RECON, encoding="utf-8", newline="") as fh:
        published = list(csv.DictReader(fh))
    if len(published) != len(issues) + len(gaps):
        errors.append(f"reconciliation CSV rows {len(published)} != {len(issues) + len(gaps)}; rerun build")
    tk = b.keyed(trans)
    for x in fields:
        t = tk[(x["club"], x["player"], x["position"])][0]
        if (t[x["field"]] or "").strip() != x["page_value"]:
            errors.append(f"transcription drift for {x['player']} {x['field']}")
    return issues, gaps


def check_venues(errors):
    rows = b.read_csv(b.VENUES)
    if len(rows) != PINNED["venues"]:
        errors.append(f"venues {len(rows)} != {PINNED['venues']}")
    ids = [r["game_id"] for r in rows]
    if len(set(ids)) != len(ids):
        errors.append("duplicate venue game_id")
    for r in rows:
        if not r["venue_stadium"].strip():
            errors.append(f"blank venue for {r['game_id']}")
        if not r["venue_source_url"].startswith("https://www.nfl.com/games/"):
            errors.append(f"venue source not a game-centre URL for {r['game_id']}")
    return rows


def check_flags_sources(errors):
    try:
        flags = b.read_csv(b.FLAGGED)
        b.read_csv(b.SOURCES)
        b.read_csv(b.VENUES)
    except ValueError as exc:
        errors.append(str(exc))
        return
    if len(flags) != PINNED["flags"]:
        errors.append(f"flags {len(flags)} != {PINNED['flags']}")
    for f in flags:
        if not f["detail"].strip():
            errors.append(f"flag {f['flag_id']} has no detail")
    for s in b.read_csv(b.SOURCES):
        url = s["url"]
        if url.startswith("repo:"):
            url = b.source_href(url)
        host = re.match(r"https://([^/]+)/", url)
        if not host or host.group(1) not in ALLOWED_HOSTS:
            errors.append(f"source {s['source_id']} host not allowed: {url}")


def check_html(errors):
    if not os.path.isdir(b.DOCS):
        errors.append("docs/nfl-s11 missing; run scripts/build_nfl_s11.py")
        return
    for name in sorted(os.listdir(b.DOCS)):
        if not name.endswith(".html"):
            continue
        text = open(os.path.join(b.DOCS, name), encoding="utf-8").read()
        if "<input" in text.lower():
            errors.append(f"{name} contains an input control")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith("https://"):
                host = re.match(r"https://([^/]+)/", href).group(1)
                if host not in ALLOWED_HOSTS:
                    errors.append(f"{name} links to disallowed host {host}")
        if name == "injuries-w10.html":
            tbody = text.split("<tbody>")[1].split("</tbody>")[0]
            rows = tbody.count("<tr>")
            links = len(re.findall(r'<a href="https://www\.nfl\.com/injuries/"', tbody))
            if rows != PINNED["injury_rows"] or links != rows:
                errors.append(f"injuries page rows={rows} links={links}; each row needs one nfl.com link")
        if name == "venues-w11.html":
            tbody = text.split("<tbody>")[1].split("</tbody>")[0]
            rows = tbody.count("<tr>")
            links = len(re.findall(r'<a href="https://www\.nfl\.com/games/', tbody))
            if rows != PINNED["venues"] or links != rows:
                errors.append(f"venues page rows={rows} links={links}")


def main():
    errors = []
    trans = check_injuries(errors)
    check_reconciliation(errors, trans)
    check_venues(errors)
    check_flags_sources(errors)
    check_html(errors)
    if errors:
        for e in errors:
            print("FAIL", e)
        return 1
    print("nfl_s11 checks: OK "
          f"({PINNED['injury_rows']} injury rows, {PINNED['venues']} venues, {PINNED['flags']} flags)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
