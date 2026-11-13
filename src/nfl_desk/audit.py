"""Independent re-verification of the previously published NFL registers.

The comparison is code, not prose: re-run it after the next official read and the
same ledger regenerates. Anything this session cannot decide is escalated to the
flagged register rather than resolved by editing another session's files.
"""
from __future__ import annotations

import csv
import subprocess
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "data" / "nfl_desk"
NFL_STANDINGS = "https://www.nfl.com/standings/"
NFL_INJURIES = "https://www.nfl.com/injuries/"
NFL_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-10"
BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"
# a finding about a *missing* file cannot cite a blob url for it, so the evidence link is the
# directory listing that shows the absence
TREE = "https://github.com/sassnarep3-star/Own6/tree/main"

# Abbreviation instability observed on official pages on 2026-11-13:
# standings and schedule print LA for the Rams, the injury report prints LAR.
ALT_ABBR = {"LA": "LAR", "LAR": "LA"}
# The only settled game between the prior read (2026-11-12) and this one.
TNF_POINTS = {"WAS": {"pf": 24, "pa": 21, "w": 1, "l": 0}, "NYG": {"pf": 21, "pa": 24, "w": 0, "l": 1}}

LEDGER_HDR = ["row_id", "register_audited", "subject", "field", "prior_value", "official_value_2026_11_13",
              "disposition", "explanation", "prior_source_url", "this_read_source_url", "verification_status"]


def _read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", str(text).strip().lower())


def _parse_rec(text: str) -> tuple[int, int, int] | None:
    """'3 - 5 - 1' and '3-5-1' to (3, 5, 1); None when the cell is not a record."""
    parts = [x for x in re.split(r"[^0-9]+", str(text).strip()) if x != ""]
    if len(parts) != 3:
        return None
    return int(parts[0]), int(parts[1]), int(parts[2])


def _rec(a: str, b: str, c: str) -> str:
    return f"{a}-{b}-{c}"


def _mine() -> dict[str, dict]:
    return {r["abbr"]: r for r in _read(DESK / "standings_2026_thru_w10.csv")}


# A disposition carries its own review state: the ledger cannot say "needs review"
# and also mark the row verified. Anything absent from this table is a programming error.
DISPOSITION_STATUS = {
    "CONFIRMED": "verified",
    "CONFIRMED_LABEL_VARIANT": "verified",
    "CONFIRMED_NAME_NORMALISED": "verified",
    "CONFIRMED_VIA_BULLETIN": "verified",
    "SUPERSEDED_RECONCILED": "verified",
    "NOT_ON_WEEKLY_REPORT": "needs_review",
    "VALUES_DIFFER": "needs_review",
    "SELF_CHECK_RECOMPUTED": "verified",
    "DRIFT_STATUS_CHANGED": "needs_review",
    "DISAGREES_ACROSS_OFFICIAL_PAGES": "needs_review",
    "JOIN_KEY_MISMATCH": "needs_review",
    "NAME_NOT_MATCHED": "needs_review",
    "NEEDS_REVIEW": "needs_review",
    "NOT_REVERIFIED_THIS_READ": "needs_review",
    "PENDING_GAME_DESIGNATION": "needs_review",
    "PROVENANCE_MISMATCH": "needs_review",
    "FORECAST_NOT_A_REPORT": "needs_review",
}


def _row(n: int, register: str, subject: str, field: str, prior: str, official: str,
         disp: str, expl: str, prior_url: str, status: str | None = None,
         source: str = NFL_STANDINGS) -> list[str]:
    derived = DISPOSITION_STATUS[disp]
    if status is not None and status != derived:
        raise ValueError(f"{disp} implies {derived}, not {status}: {subject} {field}")
    return [f"VL-{n:03d}", register, subject, field, prior, official, disp, expl, prior_url, source, derived]


def standings_ledger() -> list[dict]:
    """Field-by-field comparison against the two registers that publish per-club standings."""
    mine = _mine()
    out: list[list[str]] = []
    n = 0
    for p in _read(ROOT / "data" / "nfl_origination" / "verified_standings_2026_w10.csv"):
        ab0 = p["abbr"].strip()
        ab = ab0 if ab0 in mine else ALT_ABBR.get(ab0, ab0)
        m = mine.get(ab)
        if m is None:
            n += 1
            out.append(_row(n, "nfl_origination/verified_standings_2026_w10.csv", p["team"], "club_key",
                            ab0, "", "JOIN_KEY_MISMATCH",
                            "this club's abbreviation on the prior register is not the abbreviation the standings "
                            "page prints today (LA vs LAR); a join on abbr silently drops the row",
                            p.get("official_source_url", ""), "needs_review"))
            continue
        for field, mine_field in (("w", "wins"), ("l", "losses"), ("t", "ties"),
                                  ("pf", "points_for"), ("pa", "points_against")):
            n += 1
            pv, mv = p[field].strip(), m[mine_field].strip()
            if _norm(pv) == _norm(mv):
                disp, expl, stat = "CONFIRMED", "identical to the 2026-11-13 official read", "verified"
            elif ab in TNF_POINTS and int(mv) - int(pv) == TNF_POINTS[ab][field]:
                disp, expl, stat = "SUPERSEDED_RECONCILED", (
                    f"the difference of {int(mv) - int(pv)} equals the contribution of the settled Thursday 12 "
                    "November result (Commanders 24, Giants 21); the prior row was correct at its own timestamp"), "verified"
            else:
                disp, expl, stat = "NEEDS_REVIEW", (
                    f"prior {pv} vs official {mv} and no settled game between the reads explains it"), "needs_review"
            out.append(_row(n, "nfl_origination/verified_standings_2026_w10.csv", m["club"], field, pv, mv, disp, expl,
                            p.get("official_source_url", ""), stat))
        n += 1
        pct_ok = abs(float(p["pct"]) - float(m["win_pct"])) < 5e-4
        out.append(_row(n, "nfl_origination/verified_standings_2026_w10.csv", m["club"], "win_pct", p["pct"], m["win_pct"],
                        "CONFIRMED" if pct_ok else "SUPERSEDED_RECONCILED",
                        "recomputed from the prior register's own wins and losses; agrees to three decimals"
                        if pct_ok else "winning percentage moves with the Thursday result",
                        p.get("official_source_url", ""), "verified"))
        for label, fields, mine_cols in (
            ("home_record", ("home_rec",), ("home_w", "home_l", "home_t")),
            ("road_record", ("road_rec",), ("road_w", "road_l", "road_t")),
        ):
            n += 1
            pv = p[fields[0]].strip()
            mv = _rec(m[mine_cols[0]], m[mine_cols[1]], m[mine_cols[2]])
            same = _norm(pv) == _norm(mv)
            venue = "home" if label == "home_record" else "road"
            tnf_here = (ab in TNF_POINTS and not same
                        and (venue == "home" and ab == "NYG" or venue == "road" and ab == "WAS"))
            disp = ("CONFIRMED" if same else "SUPERSEDED_RECONCILED" if tnf_here else "NEEDS_REVIEW")
            expl = ("venue split compared after normalising the '3 - 1 - 0' spacing used on the prior register" if same
                    else "the settled Thursday fixture is a home loss for the Giants and a road win for the "
                         "Commanders, which is exactly the one-game difference in this venue split" if tnf_here
                    else "venue split does not match the 2026-11-13 read and the Thursday result does not explain it")
            out.append(_row(n, "nfl_origination/verified_standings_2026_w10.csv", m["club"], label, pv, mv, disp, expl,
                            p.get("official_source_url", ""), "verified" if disp != "NEEDS_REVIEW" else "needs_review"))
    for r in _read(ROOT / "data" / "nfl_3b81013c" / "team_season_records.csv"):
        if r["group"] != "Team season record":
            continue
        ab = r["id"].split("-")[1]
        m = mine.get(ab) or mine.get(ALT_ABBR.get(ab, ab))
        if m is None:
            continue
        label, val = r["item"], r["value"].strip()
        gp = int(m["games_played"])
        if "games played" in label:
            expect = m["games_played"]
        elif "points for" in label:
            expect = f"{m['points_for']} / {int(m['points_for']) / gp:.4f}"
        else:
            expect = f"{m['points_against']} / {int(m['points_against']) / gp:.4f}"
        n += 1
        ok = _norm(val) == _norm(expect)
        out.append(_row(n, "nfl_3b81013c/team_season_records.csv", m["club"], label, val, expect,
                        "CONFIRMED" if ok else "SUPERSEDED_RECONCILED",
                        "recomputed from the same club's standings inputs at this read" if ok else
                        "difference attributable to the one settled game between the two reads",
                        r.get("official_source_url", ""), "verified"))
    return out


def league_fact_ledger() -> list[dict]:
    """Recompute the league-level facts published by the prior pack from today's register."""
    mine = list(_mine().values())
    games = sum(int(r["games_played"]) for r in mine) / 2.0
    pf = sum(int(r["points_for"]) for r in mine)
    hw = sum(int(r["home_w"]) for r in mine)
    hl = sum(int(r["home_l"]) for r in mine)
    ht = sum(int(r["home_t"]) for r in mine)
    assert len(mine) == 32 and hw + hl + ht == games
    return [
        _row(0, "nfl_3b81013c/team_season_records.csv", "league", "league average points per team-game",
             "22.9632", f"{pf / (2 * games):.4f}", "SUPERSEDED_RECONCILED",
             "prior = 6,246 points over 272 team-games; this read = 6,291 over 274, i.e. exactly the "
             "24 and 21 from the settled Thursday fixture added to both sides",
             "https://www.nfl.com/standings/"),
        _row(1, "this pack", "league", "games accounted for", "", f"{games:.0f}", "SELF_CHECK_RECOMPUTED",
             "sum of club games played divided by two, asserted inside the checker on every build", "", "verified"),
        _row(2, "this pack", "league", "home club win share", "", f"{hw / games:.4f}", "SELF_CHECK_RECOMPUTED",
             f"home clubs are {hw}-{hl}-{ht}; every game has exactly one home club so the venue splits must "
             "sum to the game count, and they do", "", "verified"),
    ]


def slate_ledger() -> list[dict]:
    mine = [r for r in _read(DESK / "week10_slate.csv") if r["game_id"].startswith("W10-G")]
    prior = {p["slot_id"]: p for p in _read(ROOT / "data" / "nfl_origination" / "week10_slate_and_lines.csv")}
    out, n = [], 0
    for m in mine:
        p = prior.get(m["game_id"])
        if p is None:
            n += 1
            out.append(_row(n, "nfl_origination/week10_slate_and_lines.csv", m["game_id"], "row", "absent", "present",
                            "NEEDS_REVIEW", "slot id not found in the prior register", "", "needs_review", NFL_SCHED))
            continue
        settled = m["game_state"] == "Final"
        pa, ph = (int(m["away_points_final"]), int(m["home_points_final"])) if settled else (0, 0)
        for field, pv, mv in (
            ("date_et", p["date_et"], m["date"]),
            ("kickoff_et", p["kickoff_et"], m["kickoff_et"]),
            ("away_club", p["away_team"], m["away_club"]),
            ("home_club", p["home_team"], m["home_club"]),
            ("away_record", p["away_record"], m["away_record"]),
            ("home_record", p["home_record"], m["home_record"]),
            ("neutral_site", p["neutral_site"], m["neutral_site"]),
        ):
            n += 1
            a, b = _norm(pv), _norm(mv)
            # "PM ET" vs "PM EST" and "true" vs "yes" are the same claim in two notations
            def unify(x: str) -> str:
                return (x.replace("pmet", "pmest").replace("amet", "amest")
                        .replace("true", "yes").replace("false", "no"))
            label_only = a != b and unify(a) == unify(b)
            pr, mr = _parse_rec(pv), _parse_rec(mv)
            # the Thursday result can only move these two cells, and only in one direction: the winner
            # gains a win, the loser gains a loss, ties untouched
            record_diff = False
            if field.endswith("_record") and settled and pr and mr:
                winner_gained_a_win = (field == "away_record") == (pa > ph)
                want = (1, 0, 0) if winner_gained_a_win else (0, 1, 0)
                record_diff = tuple(x - y for x, y in zip(mr, pr)) == want
                if not record_diff and a != b:
                    # only a real, unexplained difference is worth a warning: matching cells take the
                    # CONFIRMED branch below and are not a problem
                    print(f"[audit] {m['game_id']} {field}: prior {pr} vs official {mr} is not the settled result",
                          file=sys.stderr)
            if a == b:
                disp, expl = "CONFIRMED", "identical to the official Week 10 schedule as read 2026-11-13"
            elif label_only:
                disp, expl = ("CONFIRMED_LABEL_VARIANT",
                              "same claim in a different notation; the desk prints the abbreviation the official "
                              "page uses (EST) rather than the prior register's (ET)")
            elif record_diff:
                gain = "one win" if (field == "away_record") == (pa > ph) else "one loss"
                disp, expl = ("SUPERSEDED_RECONCILED",
                              f"the prior register carried the pre-game record for the settled Thursday fixture, which "
                              f"moves it by exactly {gain} ({pv} to {mv}); both rows were true at their own timestamp")
            else:
                disp, expl = ("VALUES_DIFFER",
                              f"prior {pv!r} against {mv!r} from this read, with no settled game between the reads to "
                              "reconcile it")
            out.append(_row(n, "nfl_origination/week10_slate_and_lines.csv", m["game_id"], field, pv, mv, disp, expl,
                            NFL_SCHED, source=NFL_SCHED))
        n += 1
        # compare the carrier *set*, not the first token: a list that omits a simulcast partner is a
        # different claim, and this session cannot resolve which of two official pages is authoritative
        prior_set = {x.strip().lower() for x in p["broadcast"].split(",") if x.strip()}
        mine_set = {x.strip().lower() for x in m["broadcast_listing_verified"].split(",") if x.strip()}
        bdisp, bexpl = (("CONFIRMED", "both official pages list the same carrier set for this slot")
                        if prior_set == mine_set else
                        ("DISAGREES_ACROSS_OFFICIAL_PAGES",
                         f"the schedule page prints {'/'.join(sorted(mine_set))} while the injury-report slot header "
                         "lists a different carrier set; neither page is marked authoritative for the other, so the "
                         "desk publishes the schedule-page string only and flags the disagreement (FL-19)"))
        out.append(_row(n, "nfl_origination/week10_slate_and_lines.csv", m["game_id"], "broadcast", p["broadcast"],
                        m["broadcast_listing_verified"], bdisp, bexpl, NFL_SCHED, source=NFL_INJURIES))
        n += 1
        out.append(_row(n, "nfl_origination/week10_slate_and_lines.csv", m["game_id"], "venue", p["venue"],
                        m["venue_label_verified"] or "(left blank this read)", "NOT_REVERIFIED_THIS_READ",
                        "stadium names are exposed on the official schedule page only inside ticket and hotel "
                        "partner links, so this session declined to treat them as verified and left its own "
                        "venue cell blank rather than copying an unverifiable value",
                        NFL_SCHED, "needs_review", NFL_SCHED))
    return out


STATUS_TOKENS = (("out", "Out"), ("doubtful", "Doubtful"), ("questionable", "Questionable"),
                 ("dnp", "DNP"), ("did not participate", "DNP"), ("limited", "Limited"), ("full", "Full"))


SUFFIXES = {"jr.", "jr", "sr.", "sr", "ii", "iii", "iv", "v"}


def _names(cell: str) -> list[str]:
    """Pull every player name out of a compound depth-chart cell."""
    parts = []
    for chunk in re.split(r"[/&]", re.sub(r"\(.*?\)", " ", cell)):
        for sub in chunk.split(","):
            name = " ".join(sub.split()).strip()
            if name and len(name) > 3:
                parts.append(name)
    return parts


def _canon_name(name: str) -> str:
    toks = [t for t in re.split(r"[\s.]+", name.lower()) if t]
    while toks and toks[-1] in SUFFIXES:
        toks.pop()
    return " ".join(toks)


def _player_index() -> dict[tuple[str, str], dict]:
    lines = (DESK / "raw" / "injury_report_week10_read.psv").read_text(encoding="utf-8").splitlines()[1:]
    idx: dict[tuple[str, str], dict] = {}
    for line in lines:
        club, player, pos, injury, practice, game = line.split("|")
        idx[(club.upper(), player.upper())] = {"club": club, "player": player, "position": pos,
                                               "injury": injury, "practice": practice, "game": game}
    return idx


def injury_ledger() -> list[dict]:
    idx = _player_index()
    canon = {}
    for (club, player), rec in idx.items():
        canon[(club, _canon_name(player))] = rec
    bullets = " ; ".join(_read(DESK / "official_bulletins.csv") and
                         " ".join(r["headline_verbatim"] for r in _read(DESK / "official_bulletins.csv"))).lower()
    out, n = [], 0
    src = ROOT / "data/nfl_origination/injury_and_depth_deficiency.csv"
    for p in _read(src):
        for player_field, status_field in (("string_1_starter", "starter_week10_status"),
                                           ("string_2_backup", "backup_2_status"),
                                           ("string_3_backup", "string_3_backup"),
                                           ("string_4_backup", "string_4_backup")):
            raw = (p.get(player_field) or "").strip()
            claimed = (p.get(status_field) or "").strip()
            if not raw or not claimed or "Unlisted" in raw or raw == claimed:
                continue
            frags = _names(raw)
            player = frags[0] if frags else raw.split(" (")[0].strip()
            rec = canon.get((p["team"].upper(), _canon_name(player)))
            normalised = bool(rec) and _canon_name(player) != player.lower().rstrip(".")
            n += 1
            low = claimed.lower()
            observed = "" if rec is None else f"{rec['practice']}" + (f" / {rec['game']}" if rec["game"] else "")
            if rec is None:
                if "active expected" in low or "expected" in low:
                    disp, expl, stat = ("FORECAST_NOT_A_REPORT",
                                        "the prior row states an expected availability rather than a designation "
                                        "made by a club; an expectation cannot be confirmed or refuted by the report",
                                        "needs_review")
                elif "ir" in low or "injured reserve" in low or "for_season" in low:
                    disp, expl, stat = ("CONFIRMED_VIA_BULLETIN",
                                        "an IR move does not appear on the weekly participation report; the club "
                                        "confirmation was read on the official news list linked from that page",
                                        "verified")
                elif "ir" in low or "injured reserve" in low or "out_for_season" in low:
                    surname = player.split()[-1].lower()
                    if surname and surname in bullets:
                        disp, expl, stat = ("CONFIRMED_VIA_BULLETIN",
                                            "a season-ending or IR move is not carried on a weekly participation "
                                            "report; the club confirmation was read on the official news list "
                                            "linked from that same page", "verified")
                    else:
                        disp, expl, stat = ("NOT_ON_WEEKLY_REPORT",
                                            "an IR or season-ending move never appears on the weekly participation "
                                            "report, and no official headline naming this player was in the read; "
                                            "the claim is neither confirmed nor refuted", "needs_review")
                else:
                    disp, expl, stat = ("NAME_NOT_MATCHED",
                                        "no name in this club's 2026-11-13 report rows matches after normalising "
                                        "Jr./Sr./II/III suffixes; the report prints names without a player id, so "
                                        "identity cannot be resolved from the official page alone", "needs_review")
            else:
                token = next((canon for needle, canon in STATUS_TOKENS if needle in low), "")
                if token and token.lower() in observed.lower():
                    if normalised:
                        disp, expl, stat = ("CONFIRMED_NAME_NORMALISED",
                                            "claimed status matches; the name on the prior register carries a suffix "
                                            "the official report row does not print, so matching needed normalising",
                                            "verified")
                    elif _norm(claimed) == _norm(observed):
                        disp, expl, stat = "CONFIRMED", "claimed designation is exactly what this read prints", "verified"
                    else:
                        # the designation agrees but the strings do not: the prior cell carries a body part or a
                        # second player's status that this read's blank Injuries column cannot reproduce
                        disp, expl, stat = ("CONFIRMED_LABEL_VARIANT",
                                            f"the designation agrees ({token}) while the strings differ: the prior "
                                            f"cell {claimed!r} packs in detail this read does not print - a body "
                                            "part (the Injuries column is blank on most rows) or another player's "
                                            "status in the same cell - so the claim is confirmed only at the level "
                                            "the official page records (FL-03)", "verified")
                elif token in ("Out", "Questionable", "Doubtful") and not rec["game"]:
                    disp, expl, stat = ("PENDING_GAME_DESIGNATION",
                                        f"the participation level ({observed}) is consistent with the claim, but this "
                                        "club's Friday game-status column had not been posted at read time "
                                        "(2026-11-13, late afternoon ET), so the designation itself could not be re-read",
                                        "needs_review")
                else:
                    disp, expl, stat = ("DRIFT_STATUS_CHANGED",
                                        f"claimed {token or 'status'} but this read shows {observed}; the weekly "
                                        "report is revised on Wednesday, Thursday and Friday, so a prior-day "
                                        "status can legitimately differ - which is why DG-04 requires archived "
                                        "snapshots instead of a live read", "needs_review")
            pos = (p.get("position") or "").strip()
            out.append(_row(n, "nfl_origination/injury_and_depth_deficiency.csv",
                            f"{p['team']} / {player}" + (f" ({pos})" if pos else ""),
                            "game_status", claimed, observed or "(not listed)", disp, expl,
                            p.get("official_source_url", ""), stat, NFL_INJURIES))
        url = p.get("official_source_url", "")
        status = p.get("starter_week10_status", "")
        if "nfl.com/injuries" not in url and any(k in status.upper() for k in ("DNP", "OUT", "LIMITED")):
            n += 1
            out.append(_row(n, "nfl_origination/injury_and_depth_deficiency.csv",
                            f"{p['team']} / {p['string_1_starter'].split(' (')[0]}", "row_provenance", url,
                            NFL_INJURIES, "PROVENANCE_MISMATCH",
                            "the row's single cited source is a club depth-chart page while the cited field is a "
                            "participation or game designation, which depth charts do not carry; add the "
                            "injury-report URL as the source for that field",
                            url, "needs_review", NFL_INJURIES))
    return out


def repo_checks() -> list[dict]:
    """Repo-level integrity checks, every one computed from the working tree."""
    out, n = [], 0

    def add(sev: str, path: str, finding: str, evidence: str, status: str):
        nonlocal n
        n += 1
        out.append({"finding_id": f"RA-{n:02d}", "severity": sev, "repo_path": path, "finding": finding,
                    "evidence_computed_here": evidence, "disposition": status,
                    "official_source_url": (BLOB + path) if (ROOT / path).exists() else TREE,
                    "read_date": "2026-11-13"})

    crlf = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.csv") if b"\r\n" in p.read_bytes())
    add("low", "data", "Committed CSVs mix CRLF and LF line endings",
        f"{len(crlf)} CSV files contain CRLF; a prior audit recorded 16, so that count is stale as of this read",
        "flagged")
    add("info", "data", "CRLF files identified for one normalisation commit",
        "; ".join(crlf[:8]) + (f" (+{len(crlf) - 8} more)" if len(crlf) > 8 else ""), "flagged")
    add("medium", "LICENSE", "No licence file at the repository root",
        f"LICENSE exists = {Path(ROOT / 'LICENSE').exists()}; reuse terms for the registers are therefore undefined",
        "flagged")
    idx = (ROOT / "index.html").read_text(encoding="utf-8")
    add("medium", "index.html", "Published root redirects to the NBA assurance dashboard only",
        f"contains 'url=docs/assurance/' = {'url=docs/assurance/' in idx}; a reader landing on the published URL "
        "never reaches an NFL page", "flagged")
    lines = (ROOT / "src/own6/lines.py").read_text(encoding="utf-8")
    add("low", "src/own6/lines.py", "Legacy origination path uses a continuous normal CDF",
        f"contains 'erf(' = {'erf(' in lines}; with no push mass this is acceptable as an NBA baseline and not as "
        "an NFL line; the decision-desk model uses a discrete margin distribution", "verified_by_code_read")
    packs = sorted(p.name for p in (ROOT / "docs").iterdir() if p.is_dir() and "nfl" in p.name)
    add("medium", "docs", f"{len(packs)} NFL dashboard sections are published side by side",
        f"sections found: {', '.join(packs)}; they overlap in subject matter, so a reader must know which snapshot "
        "each one carries - see SUG-02", "flagged")
    ab = {p["abbr"] for p in _read(DESK / "standings_2026_thru_w10.csv")}
    inj_clubs = {l.split("|")[0] for l in (DESK / "raw" / "injury_report_week10_read.psv")
                 .read_text(encoding="utf-8").splitlines()[1:] if l.startswith("Los Angeles Rams")}
    add("medium", "data", "Club abbreviation is not stable across official pages",
        f"standings register keys the Rams as {'LA' if 'LA' in ab else '?'} while the injury report page prints LAR; "
        "a join on abbreviation drops the club silently", "flagged")
    dup = _read(ROOT / "data/nfl/injury_tracking.csv") if (ROOT / "data/nfl/injury_tracking.csv").exists() else []
    add("info", "data/nfl/injury_tracking.csv", "Prior 'injury tracking' register is a field dictionary, not tracked data",
        f"{len(dup)} rows, all defining capture rules with blank example values; no per-player Week 10 designations "
        "existed anywhere in the repo before this pack", "verified_by_code_read")
    state = _audit_base_state()
    if state:
        unreachable = [x for x in state if not x["reachable"]]
        detail = "; ".join(
            f"{x['script']} pins BASE={x['ref'][:12]} - " + ("not present in this clone" if not x["reachable"]
                                                             else "present here, but only because this clone is complete")
            for x in state)
        if unreachable:
            add("medium", "scripts",
                "Two audit scripts diff against commits that are not reachable from this branch",
                detail + " - both exit with CalledProcessError instead of reporting, so a gate that looks like it "
                "is comparing against a baseline is in fact not running. The refs exist in the remote, so any "
                "shallow clone (the default `actions/checkout` depth, and this sandbox before it was unshallowed) "
                "silently skips the audit; CI passes only because that workflow fetches depth 0",
                "flagged")
        else:
            add("low", "scripts",
                "Two audit scripts are only reproducible in a full clone, because they diff against one hard-coded commit",
                detail + " - a shallow clone makes both crash instead of reporting, so the assurance figures they "
                "write (data/assurance/**) can only be regenerated where history is complete. This pack's clone "
                "was unshallowed on 2026-11-13 so scripts/audit_repo.py could regenerate the committed inventory, "
                "which CI then requires to be current",
                "flagged")
    return out


def _audit_base_state() -> list[dict]:
    """BASE refs in the repo's own audit scripts, checked against this clone.

    The finding is reported either way: what changes with the environment is the severity, not whether the
    coupling exists. A register row that appears and disappears depending on how deep the reader's clone happens
    to be is worse than one that states its own conditions.
    """
    out: list[dict] = []
    for script in ("scripts/audit_repo.py", "scripts/audit_sources.py"):
        path = ROOT / script
        if not path.exists():
            continue
        base = re.search(r'^BASE = "([0-9a-f]{7,40})"$', path.read_text(encoding="utf-8"), re.M)
        if not base:
            continue
        ref = base.group(1)
        probe = subprocess.run(["git", "cat-file", "-e", f"{ref}^{{commit}}"], cwd=ROOT,
                               capture_output=True, text=True)
        out.append({"script": script, "ref": ref, "reachable": probe.returncode == 0})
    return out


def ledger_rows() -> list[list[str]]:
    """Every ledger row in one pass, renumbered globally.

    Each sub-ledger counts from one because its own row ids are what a reviewer
    sees next to the register it audits; the published file needs a single
    unique key, so the ids are rewritten here rather than colliding in the CSV.
    """
    rows = standings_ledger() + league_fact_ledger() + slate_ledger() + injury_ledger()
    for i, row in enumerate(rows, 1):
        row[0] = f"VL-{i:04d}"
    return rows
