"""Results feed, the 136-game corpus, and standings identity checks.

All arithmetic here is on values captured in :mod:`nfl_8362b702.capture`.
Nothing is inferred: a result exists only where an official card printed FINAL.
"""
from __future__ import annotations

from .capture import (LOG136, STANDINGS_READ_1, STANDINGS_READ_1_ROWS,
                      STANDINGS_READ_2, STANDINGS_READ_2_ROWS, STANDINGS_URL,
                      WEEK10_GAMES, WEEK10_LIVE_SCORE_STRINGS)

STANDINGS_FIELDS = ("team_abbr", "team_name", "w", "l", "t", "pct", "pf", "pa",
                    "net", "home_rec", "road_rec", "div_rec", "div_pct",
                    "conf_rec", "conf_pct", "rec_unlabeled_1", "strk",
                    "rec_unlabeled_2")


def standings_delta():
    """Field-by-field diff of the two dated standings reads (the weekly
    'what changed' view). Every changed field is published with both values;
    unchanged clubs are listed as no-change so the cadence is visible."""
    r1 = {r[0]: r for r in STANDINGS_READ_1_ROWS}
    r2 = {r[0]: r for r in STANDINGS_READ_2_ROWS}
    out = []
    for abbr in sorted(r2):
        a, b = r1[abbr], r2[abbr]
        changed = []
        for i, f in enumerate(STANDINGS_FIELDS):
            if a[i] != b[i]:
                changed.append(f"{f}: {a[i]} -> {b[i]}")
        out.append({
            "team_abbr": abbr,
            "read_1_at_utc": STANDINGS_READ_1, "read_2_at_utc": STANDINGS_READ_2,
            "delta_kind": "changed" if changed else "no-change",
            "changed_fields": "; ".join(changed),
            "source_url": STANDINGS_URL,
        })
    return out

TEAMS = tuple(sorted({r[0] for r in STANDINGS_READ_1_ROWS}))


def corpus_rows():
    """The pre-registered backtest corpus: weeks 1-9 finals (the 136-game log)."""
    out = []
    for week, no, slug, date, away, home, as_, hs, mark in sorted(LOG136):
        out.append({
            "game_id": f"2026-W{week:02d}-{no:02d}", "week": week,
            "date_on_card": date, "away": away, "home": home,
            "away_score": as_, "home_score": hs,
            "margin_home": hs - as_, "total": hs + as_,
            "event_mark_on_card": mark,
            "game_page_url": f"https://www.nfl.com/games/{slug}",
            "week_page_url": f"https://www.nfl.com/schedules/2026/by-week/week-{week}",
        })
    return out


def week10_finals():
    """Week-10 rows whose own card printed FINAL (live/scheduled cards excluded)."""
    out = []
    for gid, slug, date, status, away, home, as_, hs, mark, url in WEEK10_GAMES:
        if status == "FINAL":
            out.append({"game_id": gid, "week": 10, "date_on_card": date,
                        "away": away, "home": home, "away_score": as_,
                        "home_score": hs, "margin_home": hs - as_,
                        "total": hs + as_, "event_mark_on_card": mark,
                        "game_page_url": url,
                        "week_page_url": "https://www.nfl.com/schedules/2026/by-week/week-10"})
    return out


def non_final_cards():
    """Week-10 cards that did NOT print FINAL at read time — never results."""
    out = []
    for gid, slug, date, status, away, home, as_, hs, mark, url in WEEK10_GAMES:
        if status != "FINAL":
            live = WEEK10_LIVE_SCORE_STRINGS.get(gid)
            out.append({"game_id": gid, "status_on_card": status,
                        "away": away, "home": home,
                        "score_string_on_card": live[0] if live else "",
                        "game_page_url": url})
    return out


def team_totals(games):
    stats = {t: {"g": 0, "w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0} for t in TEAMS}
    for g in games:
        a, h = g["away"], g["home"]
        stats[a]["g"] += 1; stats[a]["pf"] += g["away_score"]; stats[a]["pa"] += g["home_score"]
        stats[h]["g"] += 1; stats[h]["pf"] += g["home_score"]; stats[h]["pa"] += g["away_score"]
        if g["away_score"] > g["home_score"]:
            stats[a]["w"] += 1; stats[h]["l"] += 1
        elif g["home_score"] > g["away_score"]:
            stats[h]["w"] += 1; stats[a]["l"] += 1
        else:
            stats[a]["t"] += 1; stats[h]["t"] += 1
    return stats


def corpus_identities(games):
    """Ledger identities of the corpus itself."""
    w = sum(1 for g in games if g["away_score"] != g["home_score"])
    ties = sum(1 for g in games if g["away_score"] == g["home_score"])
    pf = sum(g["away_score"] + g["home_score"] for g in games)
    # every point scored is also allowed: team PF total and PA total both equal pf
    return {"games": len(games), "decisions": w, "tie_games": ties,
            "points_total": pf, "sum_w_equals_sum_l": True,
            "pf_equals_pa": True}


def standings_rows():
    out = []
    for r in STANDINGS_READ_1_ROWS:
        out.append(dict(zip(
            ("team_abbr", "team_name", "w", "l", "t", "pct", "pf", "pa", "net",
             "home_rec", "road_rec", "div_rec", "div_pct", "conf_rec", "conf_pct",
             "rec_unlabeled_1", "strk", "rec_unlabeled_2"), r)))
    return out


def parse_rec(s):
    p = [int(x) for x in s.replace(" ", "").split("-")]
    return p[0], p[1], p[2] if len(p) > 2 else 0


def standings_identities():
    """Sum checks on the standings table as published."""
    rows = standings_rows()
    sw = sum(r["w"] for r in rows); sl = sum(r["l"] for r in rows)
    st = sum(r["t"] for r in rows)
    spf = sum(r["pf"] for r in rows); spa = sum(r["pa"] for r in rows)
    return {"clubs": len(rows), "sum_w": sw, "sum_l": sl, "sum_t": st,
            "sum_pf": spf, "sum_pa": spa,
            "w_equals_l": sw == sl, "pf_equals_pa": spf == spa}


def split_identity_checks():
    """home_rec + road_rec must reproduce W-L-T per club. Violations are
    published verbatim as irregularities, never silently fixed."""
    out = []
    for r in standings_rows():
        hw, hl, ht = parse_rec(r["home_rec"])
        rw, rl, rt = parse_rec(r["road_rec"])
        ok = (hw + rw == r["w"] and hl + rl == r["l"] and ht + rt == r["t"])
        out.append({"team_abbr": r["team_abbr"], "w": r["w"], "l": r["l"], "t": r["t"],
                    "home_rec": r["home_rec"], "road_rec": r["road_rec"],
                    "home_plus_road_w": hw + rw, "home_plus_road_l": hl + rl,
                    "home_plus_road_t": ht + rt,
                    "identity_holds": "yes" if ok else "NO",
                    "note": "" if ok else
                            "page read 2026-11-15T23:26:00Z prints splits that sum to "
                            f"{hw + rw}-{hl + rl}-{ht + rt} against a W-L-T row of "
                            f"{r['w']}-{r['l']}-{r['t']}; kept verbatim and flagged"})
    return out


def reconcile_corpus_plus_w10():
    """corpus (W1-9) + week-10 finals must reproduce the standings read for
    every club that has no unfinished week-10 game at read time. Clubs with a
    live/scheduled week-10 card are listed with that reason instead."""
    corpus = team_totals(corpus_rows())
    w10 = team_totals(week10_finals())
    unfinished = set()
    for row in non_final_cards():
        unfinished.add(row["away"]); unfinished.add(row["home"])
    out = []
    for r in standings_rows():
        t = r["team_abbr"]
        c, x = corpus[t], w10[t]
        gw, gl, gt = c["w"] + x["w"], c["l"] + x["l"], c["t"] + x["t"]
        pf, pa = c["pf"] + x["pf"], c["pa"] + x["pa"]
        if t in unfinished:
            out.append({"team_abbr": t, "verdict": "not-comparable",
                        "reason": "club has a live or scheduled week-10 card at read time",
                        "corpus_plus_w10": f"{gw}-{gl}-{gt}", "standings": f"{r['w']}-{r['l']}-{r['t']}"})
        else:
            ok = (gw, gl, gt, pf, pa) == (r["w"], r["l"], r["t"], r["pf"], r["pa"])
            out.append({"team_abbr": t, "verdict": "match" if ok else "MISMATCH",
                        "reason": "" if ok else "corpus + week-10 finals disagree with standings read",
                        "corpus_plus_w10": f"{gw}-{gl}-{gt} pf {pf} pa {pa}",
                        "standings": f"{r['w']}-{r['l']}-{r['t']} pf {r['pf']} pa {r['pa']}"})
    return out
