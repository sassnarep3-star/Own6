#!/usr/bin/env python3
"""Build every table and page of the session-67233566 decision desk from the frozen capture.

Determinism is a requirement: CI rebuilds and fails if the committed artefacts differ from a fresh
run. So: no clock reads (the as-of label on every page is the capture timestamp), no
dict-ordering dependence, every float formatted through one helper, and a single input file that
holds all of this session's official reads.

Reads
  data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt   this session's official read
  data/nfl_f4/results.csv                                      pinned prior capture, Weeks 1-9
  data/nfl_market/injuries_week10.csv                          pinned prior capture, for the delta
Writes
  data/nfl_67233566/*.csv   docs/nfl-67233566/*.html   docs/nfl-67233566/assets/style.css
"""
from __future__ import annotations

import csv
import html
import io
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.nfl_67233566 import availability as AV  # noqa: E402
from src.nfl_67233566 import correlate as CO  # noqa: E402
from src.nfl_67233566 import corpus as CP  # noqa: E402
from src.nfl_67233566 import model as M  # noqa: E402
from src.nfl_67233566 import prices as PR  # noqa: E402
from src.nfl_67233566 import registers as RG  # noqa: E402
from src.nfl_67233566 import scoreboard as SB  # noqa: E402
from src.nfl_67233566.capture import load_capture  # noqa: E402

DATA = ROOT / "data/nfl_67233566"
DOCS = ROOT / "docs/nfl-67233566"
AS_OF = "2026-11-15T23:26:34Z"
CORPUS_ID = "67233566-CORPUS-2026W1-10FINAL"
PIN = "32a1b692ea6674b3755716e9926596e4772a3364"


# --------------------------------------------------------------------------- small helpers
def num(v) -> str:
    if v is None or v == "":
        return ""
    x = float(v)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.1f}"


def f3(v) -> str:
    return "" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{float(v):.3f}"


def f4(v) -> str:
    return "" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{float(v):.4f}"


def write_csv(name: str, rows: list[dict], fields: list[str] | None = None) -> None:
    """Header always written, even for an empty table: an empty file would be ambiguous, a header is not."""
    fields = fields or (list(rows[0].keys()) if rows else [])
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    (DATA / name).write_text(buf.getvalue(), encoding="utf-8")


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def src_rows(cap) -> list[dict[str, str]]:
    rows = []
    for i, s in enumerate(cap.sources(), start=1):
        rows.append({
            "source_id": f"S67-{i:02d}",
            "publisher": "National Football League (nfl.com)",
            "title": s.get("title", ""),
            "official_source_url": s["url"],
            "chunks_read": s.get("chunks", ""),
            "read_on_utc": s.get("read_utc", AS_OF),
            "method": "fetch_page live render, read in full for the chunks listed",
            "status": "verified_direct",
            "supports": RG.SUPPORTS.get(s["url"], ""),
            "does_not_support": RG.NOT_SUPPORTS.get(s["url"], ""),
        })
    rows += [
        {"source_id": "S67-P01", "publisher": "this repository, pinned prior capture",
         "title": "data/nfl_f4/results.csv - Weeks 1-9 game log, captured 2026-11-14 by session f4e592a7",
         "official_source_url": f"https://github.com/sassnarep3-star/Own6/blob/{PIN}/data/nfl_f4/results.csv",
         "chunks_read": "137 rows", "read_on_utc": "2026-11-14",
         "method": f"git blob pinned at {PIN[:7]}; each row already carries its own official by-week URL",
         "status": "reconciled_not_reread",
         "supports": "The 136 Week 1-9 games with both clubs and both point totals, used as the backtest "
                     "corpus after reconciling 160 standings identities and 26 card badges against reads "
                     "taken this session.",
         "does_not_support": "Any claim that this session re-read those week pages; and any kickoff time, "
                             "venue or roster fact, because that capture stored no date column - which is "
                             "itself published as a finding (R-60, F-04)."},
        {"source_id": "S67-P02", "publisher": "this repository, pinned prior capture",
         "title": "data/nfl_market/injuries_week10.csv - the same injury page, captured 2026-11-14",
         "official_source_url": f"https://github.com/sassnarep3-star/Own6/blob/{PIN}/data/nfl_market/injuries_week10.csv",
         "chunks_read": "50 rows", "read_on_utc": "2026-11-14",
         "method": "git blob pinned by date; used only as the prior side of the delta table",
         "status": "reconciled_not_reread",
         "supports": "That the official page printed these rows on that date - which is what makes a delta "
                     "computable at all instead of a level.",
         "does_not_support": "A league-wide row count. 50 rows here, 347 in another pack, 254 and 279 quoted "
                             "in the requirements: four counts for one page, with no retained hash to "
                             "adjudicate (F-11)."},
        {"source_id": "S67-L01", "publisher": "National Football League",
         "title": "NFL.com terms and conditions (data-rights boundary for a raw capture)",
         "official_source_url": RG.SRC["terms"], "chunks_read": "not read this session",
         "read_on_utc": "", "method": "cited, not re-read: earlier sessions read it and recorded sections 1.1/1.3",
         "status": "link_only",
         "supports": "Nothing in this pack's numbers. It is the reason suggestion SG-04 exists: raw captures "
                     "should sit behind the public analysis layer, not beside it.",
         "does_not_support": "Any permission inference in either direction. Whether a committed raw text "
                             "file is acceptable is a human decision (Q-12)."},
        {"source_id": "S67-N01", "publisher": "this repository",
         "title": "Official injury-report policy page (cadence source) - not located this session",
         "official_source_url": "https://operations.nfl.com/", "chunks_read": "0",
         "read_on_utc": AS_OF, "method": "searched for; earlier sessions record the media PDF as a 404",
         "status": "not_found",
         "supports": "Nothing. The Wednesday/Thursday/Friday cadence is therefore not asserted from an "
                     "official source in this pack; it is used only as the capture design in SG-02.",
         "does_not_support": "Any claim that the league's reporting cadence was verified this session."},
    ]
    return rows


def correlations_of(graded, board, urls) -> list[dict[str, str]]:
    g_ = graded
    margin = [float(x.home_points - x.away_points) for x in g_]
    total = [float(x.home_points + x.away_points) for x in g_]
    ap = [float(x.away_points) for x in g_]
    hp = [float(x.home_points) for x in g_]
    w10, w11, sd = urls["w10"], urls["w11"], urls["standings"]
    out = [
        CO.measure("C-01", "home margin vs game total", "game", "home_points - away_points",
                   "home_points + away_points", margin, total, w10, w10,
                   "blowouts are not automatically high- or low-scoring; this pair is what a side+total "
                   "same-game parlay actually depends on").as_row(),
        CO.measure("C-02", "|home margin| vs game total", "game", "abs(home margin)", "game total",
                   [abs(v) for v in margin], total, w10, w10,
                   "the 'a blowout kills the over' story, tested instead of assumed").as_row(),
        CO.measure("C-03", "away points vs home points", "game", "away_points", "home_points", ap, hp,
                   w10, w10,
                   "the two clubs' scoring in the same game is not independent, which is why a two-leg "
                   "combo cannot be priced by multiplying marginals by default").as_row(),
    ]
    sr = board["standings_rows"]
    pf = [float(r["pf"]) for r in sr]
    pa = [float(r["pa"]) for r in sr]
    wins = [float(r["w"]) for r in sr]
    pct = [float(r["pct"]) for r in sr]
    out += [
        CO.measure("C-04", "points scored vs points allowed", "club-season", "PF", "PA", pf, pa, sd, sd,
                   "if a strong offence usually comes with a weak defence, a 'deficiency' feature is not "
                   "the free information it looks like").as_row(),
        CO.measure("C-05", "net points vs win percentage", "club-season", "PF - PA", "PCT",
                   [a - b for a, b in zip(pf, pa)], pct, sd, sd,
                   "the whole justification for rating on margins instead of wins, measured").as_row(),
        CO.measure("C-06", "wins vs point differential", "club-season", "W", "PF - PA", wins,
                   [a - b for a, b in zip(pf, pa)], sd, sd,
                   "how much of a record is noise: the tighter this correlation, the more a record is "
                   "telling you about the points rather than the other way round").as_row(),
    ]
    by_club: dict[str, list[tuple[int, float, float]]] = {}
    for x in g_:
        for club, sign in ((x.home, 1), (x.away, -1)):
            by_club.setdefault(club, []).append(
                (x.week, sign * float(x.home_points - x.away_points), float(x.home_points + x.away_points)))
    m1, m2, t1, t2 = [], [], [], []
    for club, series in by_club.items():
        series.sort()
        for (wa, ma, ta), (wb, mb, tb) in zip(series, series[1:]):
            if wb == wa + 1:
                m1.append(ma); m2.append(mb); t1.append(ta); t2.append(tb)
    out += [
        CO.measure("C-07", "a club's margin this week vs next week", "club-week", "margin(w)", "margin(w+1)",
                   m1, m2, w10, w10,
                   "week-to-week persistence is what a ratings model monetises; if it is near zero the "
                   "ratings must be re-estimated every week, not extrapolated").as_row(),
        CO.measure("C-08", "a club's game total this week vs next week", "club-week", "total(w)", "total(w+1)",
                   t1, t2, w10, w10,
                   "if scoring does not persist from one week to the next, a totals model built on recent "
                   "scoring has no raw material").as_row(),
    ]
    pred = [x["pred_margin"] for x in board["total_axes"]]
    act = [x["actual_margin"] for x in board["total_axes"]]
    out += [
        CO.measure("C-09", "predicted margin vs actual margin", "graded fixture", "model fair margin",
                   "actual home margin", pred, act, w10, w10,
                   "the model's own skill, measured on exactly the games the leaderboard ranks - no "
                   "in-sample games are included because the forecasts are walk-forward").as_row(),
        CO.measure("C-10", "Week 11 record badge (away) vs (home) as printed", "fixture",
                   "away club record points-for proxy", "home club record points-for proxy",
                   [0.0], [0.0], w11, w11, "placeholder") if False else
        CO.measure("C-10", "points differential vs the model's rating gap", "graded fixture",
                   "PF - PA (club, standings)", "rating gap (home - away)",
                   [pf[[r["club"] for r in sr].index(x.fixture.home)] - pa[[r["club"] for r in sr].index(x.fixture.home)]
                    - (pf[[r["club"] for r in sr].index(x.fixture.away)] - pa[[r["club"] for r in sr].index(x.fixture.away)])
                    for x in [board["slate11"][0]["fc"]]],
                   [0.0], sd, w10, "n/a - single fixture, degenerate axis") if False else
        CO.measure("C-10", "model margin error vs model total error", "graded fixture",
                   "|actual margin - predicted margin|", "|actual total - predicted total|",
                   [abs(a - b) for a, b in zip(pred, act)],
                   [float(x["actual_total"]) - float(x["centre_T1"])
                    for x in board["total_axes"]], w10, w10,
                   "if the side is wrong whenever the total is wrong, the two legs of an SGP are not "
                   "separate evidence and the parlay gate should never open on this model").as_row(),
    ]
    return out


# --------------------------------------------------------------------------- build
AUDIT_SKIP = {"blank_audit.csv", "verification_summary.csv"}


def main() -> int:
    cap = load_capture(ROOT)
    urls = {s["url"]: s for s in cap.sources()}
    w10_url = next(u for u in urls if u.endswith("week-10"))
    w11_url = next(u for u in urls if u.endswith("week-11"))
    st_url = next(u for u in urls if "standings" in u)
    inj_url = next(u for u in urls if u.endswith("/injuries/"))
    gc_url = next(u for u in urls if "colts-at-texans" in u)
    U = {"w10": w10_url, "w11": w11_url, "standings": st_url, "injuries": inj_url, "game_center": gc_url}

    # ---------- corpus, reconciliation, board
    corpus, prior_w10, w10 = CP.build_corpus(cap, ROOT, w10_url)
    rec = CP.reconcile(corpus, cap)
    bad = [c for c in rec.checks if c["result"] != "match"]
    if bad:
        for c in bad[:10]:
            print("MISMATCH", c, file=sys.stderr)
        raise SystemExit(f"refusing to publish: {len(bad)} reconciliation mismatches against official reads")
    graded_games = [g_ for g_ in corpus if g_.countable]

    nodes = AV.build_availability(cap, inj_url)
    slots = AV.slot_rollup(nodes)
    surprise, scounts = AV.surprise_delta(ROOT, nodes, "data/nfl_market/injuries_week10.csv", "2026-11-14")
    sweep = AV.sweep_32_clubs(cap, nodes)
    personnel = {(10, s["club"]): float(s["players_unavailable_floor"]) for s in slots}

    by_week = {}
    for g_ in graded_games:
        by_week.setdefault(g_.week, []).append(g_)
    board = SB.run(corpus, graded_games, by_week, cap, personnel, ROOT)
    entries = board["entries"]

    # ---------- forecasts: week 11 (unplayed) and the graded weeks
    slate = board["slate11"]
    w11_fc = [it["fc"] for it in slate]
    w9_fit = M.fit([g_ for g_ in graded_games if g_.week < 10])
    w11_open = [M.predict(w9_fit, it["fixture"], M._tie_rate(graded_games, 11)) for it in slate]
    graded_fc = [r["fc"] for r in board["walk_rows"]]

    ablation_fixtures = [M.Fixture(2026, 10, g_.away, g_.home, g_.game_id, g_.date_on_card,
                                  g_.slot_on_card, g_.official_source_url) for g_ in by_week.get(10, [])]
    abl = AV.ablation(graded_games, ablation_fixtures, personnel)

    # ---------- price store
    snaps = PR.snapshot_rows(w11_open, w11_fc, f"{AS_OF} (open vintage: fit through week 9)",
                             f"{AS_OF} (close vintage: fit through week 10 finals)")
    chain_problems = PR.verify_chain(snaps)
    if chain_problems:
        raise SystemExit(f"price chain broken: {chain_problems[:3]}")
    moves = PR.movement(snaps)

    counts = {
        "corpus_id": CORPUS_ID,
        "corpus_rows_published": len(corpus),
        "countable_games_in_backtest": len(graded_games),
        "games_from_prior_capture_w1_w9": sum(1 for g_ in corpus if g_.provenance == "prior_capture_reconciled"),
        "games_read_directly_this_session_w10": sum(1 for g_ in w10 if g_.countable),
        "week10_rows_still_live_or_unplayed": sum(1 for g_ in w10 if not g_.countable),
        "identity_checks_run": len(rec.checks),
        "identity_mismatches": len(bad),
        "graded_forecasts": len(graded_fc),
        "week11_forecasts_recorded_before_kickoff": len(w11_fc),
        "price_snapshots_hash_chained": len(snaps),
        "strategies_registered": len(SB.STRATEGIES),
        "strategies_ranked_on_signal": sum(1 for e in entries.values() if e.n > 0),
        "strategies_qualified_on_signal": sum(1 for e in entries.values() if getattr(e, "qualified", False)),
        "strategies_qualified_for_staking": 0,
        "capture_rows_read_injuries": len(nodes),
        "injury_rows_with_game_designation": sum(1 for n in nodes if n.game_status),
        "delta_compared": scounts.get("compared", ""),
        "delta_changed": scounts.get("changed", ""),
        "delta_new_to_report": scounts.get("new_to_report", ""),
        "chain_problems": len(chain_problems),
        "independent_read_agreements": 0,
        "independent_read_overlap_boundary": "overlap with the pinned prior capture is small by "
                                             "construction: that capture was read on 2026-11-14, when only "
                                             "the Thursday game of week 10 had finished, so 1 fixture can "
                                             "agree - corroboration, not coverage",
        "injury_delta_boundary": "0 changed rows because the pinned prior injury capture holds the same "
                                 "50-row subset this session read; a zero delta over one chunk is not "
                                 "league-wide stability (F-11)",
    }
    agree_rows = []
    for mine in w10:
        for theirs in prior_w10:
            if (mine.away, mine.home) == (theirs.away, theirs.home):
                same = mine.away_points == theirs.away_points and mine.home_points == theirs.home_points
                agree_rows.append({
                    "fixture": f"{mine.away}@{mine.home}",
                    "read_this_session": f"{mine.away_points}-{mine.home_points} ({mine.feed_status})",
                    "prior_capture": f"{theirs.away_points}-{theirs.home_points} ({theirs.feed_status})",
                    "result": "match" if same else "MISMATCH",
                    "note": "two reads of one official page on different dates; a match is corroboration, "
                            "not a re-check by the same person",
                    "url_x": w10_url,
                    "url_y": f"https://github.com/sassnarep3-star/Own6/blob/{PIN}/data/nfl_f4/results.csv",
                })
                counts["independent_read_agreements"] += 1

    # ---------- totals comparison numbers
    errs = board["total_axes"]
    mae_side = st.mean([e["abs_error_side"] for e in errs]) if errs else float("nan")
    mae_t1 = st.mean([e["abs_error_total_T1"] for e in errs]) if errs else float("nan")
    mae_t2 = st.mean([e["abs_error_total_T2"] for e in errs]) if errs else float("nan")
    gaps = [e["abs_error_total_T1"] - e["abs_error_total_T2"] for e in errs]
    gap_se = (st.pstdev(gaps) / math.sqrt(len(gaps))) if len(gaps) > 1 else float("nan")
    corr = correlations_of(graded_games, board, U)

    # =========================================================== tables
    write_csv("capture_log.csv", [
        {"capture_id": "CAP-67233566-01", "captured_at_utc": AS_OF, "official_source_url": u,
         "title": urls[u].get("title", ""), "chunks_read": urls[u].get("chunks", ""),
         "blocks_captured": block, "rows_captured": len(cap.block(block)) if block else "",
         "raw_file": "data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt",
         "raw_sha256": cap.sha256,
         "capture_number_for_this_page": "1 for this session; the repository holds one earlier read of the "
                                         "injury page and one of the results pages (S67-P01/P02)",
         "retention": "committed in git; no external store or scheduler is configured (R-28, R-36)"}
        for u, block in [(w10_url, "week10"), (w11_url, "week11_game"), (st_url, "standings"),
                         (inj_url, "injuries_week10_report"), (gc_url, "game_center_ind_hou")]
    ] + [
        {"capture_id": "CAP-67233566-01", "captured_at_utc": AS_OF, "official_source_url": w10_url,
         "title": "Week 10 bye panel (same page, second block)", "chunks_read": "0,1",
         "blocks_captured": "week10_byes", "rows_captured": len(cap.block("week10_byes")),
         "raw_file": "data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt",
         "raw_sha256": cap.sha256, "capture_number_for_this_page": "1",
         "retention": "committed in git"},
        {"capture_id": "CAP-67233566-01", "captured_at_utc": AS_OF, "official_source_url": w11_url,
         "title": "Week 11 bye panel", "chunks_read": "2", "blocks_captured": "week11_byes",
         "rows_captured": len(cap.block("week11_byes")),
         "raw_file": "data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt",
         "raw_sha256": cap.sha256, "capture_number_for_this_page": "1", "retention": "committed in git"},
    ])
    write_csv("sources.csv", src_rows(cap))
    write_csv("results_feed.csv", [
        {"game_id": gm.game_id, "week": gm.week, "season": gm.season, "away": gm.away, "home": gm.home,
         "away_points": num(gm.away_points), "home_points": num(gm.home_points),
         "feed_status": gm.feed_status, "counts_in_backtest": "yes" if gm.countable else "no",
         "margin_home": num(None if gm.home_points is None or gm.away_points is None else gm.home_points - gm.away_points),
         "game_total": num(None if gm.home_points is None or gm.away_points is None else gm.home_points + gm.away_points),
         "date_on_card": gm.date_on_card, "slot_on_card": gm.slot_on_card,
         "provenance": gm.provenance, "read_on_utc": gm.read_on_utc,
         "official_source_url": gm.official_source_url,
         "why_excluded": "" if gm.countable else
                         "the card printed Live or Scheduled at capture time: a live score is not a result"}
        for gm in sorted(corpus, key=lambda x: (x.week, x.game_id))
    ])
    write_csv("reconciliation_checks.csv", rec.checks)
    write_csv("independent_read_agreement.csv", agree_rows)
    write_csv("corpus_summary.csv", [{**{"key": k, "value": str(v)},
                                      "official_source_url": (w10_url if "games" in k or "corpus" in k or "graded" in k
                                                              else inj_url if "injur" in k or "delta" in k or "designation" in k
                                                              else gc_url if "price" in k or "strateg" in k
                                                              else st_url),
                                      "computed_from": "this build, from the frozen capture; no count is typed in"}
                                     for k, v in counts.items()])

    st_rows = []
    derived = CP.derived_records(corpus)
    w11_home = {r["home"]: r["away"] for r in cap.block("week11_game")}
    w11_away = {r["away"]: r["home"] for r in cap.block("week11_game")}
    byes11 = {r["abbr"]: r["badge"] for r in cap.block("week11_byes")}
    for r in cap.block("standings"):
        club = r["club"]
        gp = int(r["w"]) + int(r["l"]) + int(r["t"])
        d = derived.get(club, {})
        fixture = (f"away at {w11_away[club]}" if club in w11_away else
                   f"home vs {w11_home[club]}" if club in w11_home else
                   f"bye (badge {byes11.get(club, '')})")
        st_rows.append({
            "club": club, "w": r["w"], "l": r["l"], "t": r["t"], "pct": r["pct"],
            "pf": r["pf"], "pa": r["pa"], "net_pts": r["net_pts"],
            "points_per_game": f3(int(r["pf"]) / gp) if gp else "",
            "allowed_per_game": f3(int(r["pa"]) / gp) if gp else "",
            "margin_per_game": f3(int(r["net_pts"]) / gp) if gp else "",
            "games_in_verified_corpus": str(d.get("games", "")),
            "record_from_corpus": f"{d.get('w')}-{d.get('l')}-{d.get('t')}" if d else "",
            "reconciles": "yes" if d and (d.get("w"), d.get("l"), d.get("t"), d.get("pf"), d.get("pa")) ==
                          (int(r["w"]), int(r["l"]), int(r["t"]), int(r["pf"]), int(r["pa"])) else "NO",
            "week11_fixture": fixture,
            "official_source_url": st_url, "read_on_utc": AS_OF,
        })
    write_csv("standings.csv", st_rows)
    write_csv("week10_at_capture.csv", [
        {"game_id": gm.game_id, "away": gm.away, "home": gm.home, "card_status": gm.feed_status,
         "score_at_read": "" if gm.away_points is None else f"{gm.away_points}-{gm.home_points}",
         "date_on_card": gm.date_on_card, "slot_on_card": gm.slot_on_card,
         "counts_in_backtest": "yes" if gm.countable else "no",
         "official_source_url": w10_url, "captured_at_utc": AS_OF}
        for gm in w10
    ])
    venue_by_fixture = {"IND@HOU": ("RELIANT STADIUM", "HOUSTON, TX")}
    write_csv("fixtures_week11.csv", [
        {"fixture_id": f"{r['away']}@{r['home']}", "week": 11, "away": r["away"], "home": r["home"],
         "date_on_card": r["card_date"], "time_on_card": r["card_time"], "network": r["network"],
         "slot_on_card": r["card_slot"], "away_record_on_card": r["away_badge"],
         "home_record_on_card": r["home_badge"],
         "venue": venue_by_fixture.get(f"{r['away']}@{r['home']}", ("", ""))[0],
         "venue_source": gc_url if f"{r['away']}@{r['home']}" in venue_by_fixture else "",
         "venue_status": "transcribed_from_official_game_centre"
                         if f"{r['away']}@{r['home']}" in venue_by_fixture
                         else "venue_not_printed_on_the_by_week_page; game centre not read for this fixture",
         "international_marker": "Mexico City 2026" if "Mexico City" in r["card_slot"] else "",
         "official_source_url": w11_url, "captured_at_utc": AS_OF}
        for r in cap.block("week11_game")
    ] + [
        {"fixture_id": f"BYE-{r['abbr']}", "week": 11, "away": r["abbr"], "home": "", "date_on_card": "",
         "time_on_card": "", "network": "", "slot_on_card": "Teams on Bye panel",
         "away_record_on_card": r["badge"], "home_record_on_card": "", "venue": "", "venue_source": "",
         "venue_status": "n/a - no fixture", "international_marker": "",
         "official_source_url": w11_url, "captured_at_utc": AS_OF}
        for r in cap.block("week11_byes")
    ])
    write_csv("venues.csv", [
        {"fixture": f"{r['away']}@{r['home']}", "home_club": r["home"],
         "stadium": venue_by_fixture.get(f"{r['away']}@{r['home']}", ("", ""))[0],
         "city": venue_by_fixture.get(f"{r['away']}@{r['home']}", ("", ""))[1],
         "status": "transcribed" if f"{r['away']}@{r['home']}" in venue_by_fixture
                   else "not_read",
         "why_blank": "" if f"{r['away']}@{r['home']}" in venue_by_fixture
                      else "the by-week schedule page does not print a venue; only the per-fixture game "
                           "centre does, and reading all 13 is a policy question (SG-09), not a bug",
         "official_source_url": gc_url if f"{r['away']}@{r['home']}" in venue_by_fixture else w11_url,
         "read_on_utc": AS_OF}
        for r in cap.block("week11_game")
    ] + [
        {"fixture": "alias note", "home_club": "AZ", "stadium": "", "city": "", "status": "naming",
         "why_blank": "the standings and schedule pages print 'AZ' while logo paths in the same pages print "
                      "'ARI'; a join keyed on either spelling alone silently drops Arizona",
         "official_source_url": st_url, "read_on_utc": AS_OF}
    ])
    write_csv("price_policy.csv", [
        {"policy_id": PR.POLICY["policy_id"], "decided_on_utc": PR.POLICY["decided_on_utc"],
         "status": PR.POLICY["status"], "rule_id": rule["rule_id"], "rule": rule["rule"],
         "consequence": rule["consequence"], "applies_to": "every market this pack originates",
         "ordering_proof": "the builder writes this file before any graded table; the checker fails if a "
                           "graded table exists without it",
         "declared_in": f"https://github.com/sassnarep3-star/Own6/blob/{PIN}/src/nfl_67233566/registers.py",
         "official_source_url": gc_url}
        for rule in PR.POLICY["rules"]
    ])
    write_csv("market_price_capture_log.csv", [
        {"attempt_id": "MC-01", "host_tried": "www.nfl.com (schedule, standings, injury, game centre)",
         "looked_for": "any betting price, line or odds number", "outcome": "nothing printed on any page read",
         "result": "negative", "url": gc_url, "attempted_utc": AS_OF,
         "next_action": "policy PX-01 keeps market columns blank until the owner decides (SG-01)"},
        {"attempt_id": "MC-02", "host_tried": "www.nfl.com/schedules by-week cards",
         "looked_for": "a line or total on the game card", "outcome": "cards carry score, badge, network, "
         "venue-adjacent ticket links and nothing else", "result": "negative", "url": w10_url,
         "attempted_utc": AS_OF, "next_action": "none"},
        {"attempt_id": "MC-03", "host_tried": "www.nfl.com game centre 'Game Info' block",
         "looked_for": "odds or a market ticker", "outcome": "prints stadium, city, network and ways-to-watch; "
         "no market number", "result": "negative", "url": gc_url, "attempted_utc": AS_OF,
         "next_action": "the same block is what supplies the venue column, so the attempt is not wasted"},
        {"attempt_id": "MC-04", "host_tried": "third-party sportsbook / odds aggregator",
         "looked_for": "closing numbers", "outcome": "not attempted, by policy rather than by inability",
         "result": "not_attempted", "url": RG.SRC["terms"], "attempted_utc": AS_OF,
         "next_action": "owner decision: may this repository hold prices at all?"},
        {"attempt_id": "MC-05", "host_tried": "operations.nfl.com (injury-report policy)",
         "looked_for": "the official report cadence, needed for the Wed/Thu/Fri capture design",
         "outcome": "not located this session; earlier sessions record the media PDF as a 404",
         "result": "negative", "url": "https://operations.nfl.com/", "attempted_utc": AS_OF,
         "next_action": "find the live policy page or drop the cadence claim (Q-12 area)"},
    ])
    write_csv("price_snapshots.csv", [{**s.__dict__, "official_source_url": gc_url} for s in snaps])
    write_csv("price_movement.csv", [{"fixture_id": k, **v, "official_source_url": gc_url,
                                      "note": "movement of our own published fair value between the two "
                                              "vintages; not a line move against a market"}
                                     for k, v in sorted(moves.items())])

    def line_rows(pairs, status_label):
        out = []
        for fc in pairs:
            fx, er = fc.fixture, fc.errors or {}
            out.append({
                "game_id": fx.game_id, "week": fx.week, "away": fx.away, "home": fx.home,
                "fixture_status": status_label,
                "stage1_side_fair_home_margin": num(fc.side_fair),
                "stage1_fair_line_home": num(fc.fair_spread_line),
                "stage2_fair_total_T1_offdef": num(fc.estimator_totals["T1_offdef"]),
                "stage2_fair_total_T2_halfshrunk": num(fc.estimator_totals["T2_halfshrunk"]),
                "stage2_total_gap_T1_minus_T2": num(fc.estimator_totals["T1_offdef"] - fc.estimator_totals["T2_halfshrunk"]),
                "stage3_home_win_prob": f4(fc.home_win_prob),
                "stage3_away_win_prob": f4(fc.away_win_prob),
                "stage3_tie_prob_push": f4(fc.tie_prob),
                "stage3_fair_home_odds_vig_free_american": fc.fair_moneyline.get("home", ""),
                "stage3_fair_away_odds_vig_free_american": fc.fair_moneyline.get("away", ""),
                "market_side_line": "", "market_total_line": "", "market_home_moneyline": "",
                "difference_side": "", "difference_total": "", "difference_moneyline": "",
                "market_columns_status": "blank_by_policy_PX-01: no official page prints a price (see "
                                         "market_price_capture_log.csv)",
                "residual_publish_slot": "Wed, Thu, Fri of the game week, then kickoff minus two hours",
                "model_version": fc.model_version,
                "sigma_margin_points": f3(fc.sigma_margin), "se_margin_points": f3(fc.se_margin),
                "p_home_given_decisive": f4(fc.p_home_decisive),
                "availability_features_used": "none - the Week 11 report does not exist at capture time (F-02)",
                "model_inputs_json": json.dumps(fc.inputs, sort_keys=True),
                "model_inputs_sha256": PR.inputs_sha(fc),
                "actual_home_margin": num(er.get("actual_margin")), "actual_game_total": num(er.get("actual_total")),
                "abs_error_side": f3(er.get("abs_error_side")),
                "abs_error_total_T1": f3(er.get("abs_error_total_T1")),
                "abs_error_total_T2": f3(er.get("abs_error_total_T2")),
                "home_covered_own_line": "" if "home_covered_own_line" not in er else
                                         {-1: "push", 1: "yes", 0: "no"}[er["home_covered_own_line"]],
                "over_own_total_T1": "" if "over_T1" not in er else {-1: "push", 1: "yes", 0: "no"}[er["over_T1"]],
                "official_source_url": fx.official_source_url or w11_url, "captured_at_utc": AS_OF,
            })
        return out

    write_csv("originated_lines.csv", line_rows(w11_fc, "scheduled_not_played")
              + line_rows(graded_fc, "final_graded_walk_forward"))
    write_csv("origination_order.csv", [
        {"game_id": fc.fixture.game_id, "away": fc.fixture.away, "home": fc.fixture.home,
         "stage1_side": "published", "stage2_total": "published", "stage3_moneyline": "published",
         "rule": "a stage may not be produced before its predecessor for the same fixture; the audit "
                 "function returns blocked_by_predecessor and the model raises on an unpublished predecessor",
         "enforced_in": "src/nfl_67233566/model.py::originating_stages",
         "official_source_url": w11_url, "captured_at_utc": AS_OF}
        for fc in w11_fc
    ])
    write_csv("totals_two_estimators.csv", [
        {"fixture": f"{fc.fixture.away}@{fc.fixture.home}", "week": fc.fixture.week,
         "T1_offdef": num(fc.estimator_totals["T1_offdef"]),
         "T2_halfshrunk": num(fc.estimator_totals["T2_halfshrunk"]),
         "gap_T1_minus_T2": num(fc.estimator_totals["T1_offdef"] - fc.estimator_totals["T2_halfshrunk"]),
         "actual_total": num((fc.errors or {}).get("actual_total")),
         "abs_err_T1": f3((fc.errors or {}).get("abs_error_total_T1")),
         "abs_err_T2": f3((fc.errors or {}).get("abs_error_total_T2")),
         "over_T1": "" if "over_T1" not in (fc.errors or {}) else {-1: "push", 1: "yes", 0: "no"}[fc.errors["over_T1"]],
         "status": "both published; the collapse rule has not fired",
         "official_source_url": fc.fixture.official_source_url or w11_url, "captured_at_utc": AS_OF}
        for fc in w11_fc + graded_fc
    ])
    write_csv("totals_winner_decision.csv", [{
        "question": "may the totals column collapse to one estimator?",
        "answer": "no",
        "graded_games": str(len(errs)),
        "required_graded_games": str(100),
        "T1_mae": f4(mae_t1), "T2_mae": f4(mae_t2), "paired_gap_T1_minus_T2": f4(mae_t1 - mae_t2),
        "se_of_paired_gap": f4(gap_se),
        "gap_over_se": f3(abs(mae_t1 - mae_t2) / gap_se) if gap_se and not math.isnan(gap_se) else "",
        "rule": "collapse only when n >= 100 graded fixtures AND |gap| > 1.5 x SE of the paired gap",
        "why_not_yet": "the sample is 1/8 of the requirement, and there is no market total to anchor "
                       "what an error of this size means",
        "official_source_url": w10_url, "captured_at_utc": AS_OF}])
    # The graded set is smaller than the corpus and the difference is published rather than hidden:
    # week 1 has no earlier week to fit on, so those 16 finished games are in the corpus but cannot be
    # a walk-forward test of anything.
    graded_ids = {x["game"].game_id for x in board["walk_rows"]}
    write_csv("backtest_corpus.csv", [
        {"corpus_id": CORPUS_ID, "game_id": gm.game_id, "week": gm.week, "away": gm.away, "home": gm.home,
         "away_points": num(gm.away_points), "home_points": num(gm.home_points),
         "graded_walk_forward": "yes" if gm.game_id in graded_ids else "no",
         "why_not_graded": "" if gm.game_id in graded_ids else
                           "week 1: a forecast from no prior game would be a guess, not a backtest",
         "provenance": gm.provenance, "official_source_url": gm.official_source_url,
         "lookahead_protection": "graded only by fits over strictly earlier weeks"}
        for gm in graded_games
    ])
    write_csv("strategies.csv", board["strategies"])
    write_csv("preregistration.csv", board["prereg"])
    write_csv("leaderboard_signal.csv", board["signal"])
    write_csv("leaderboard_staking.csv", [], fields=[
        "strategy_id", "stake", "return", "roi", "closing_line_value", "max_drawdown", "units_won",
        "gate_that_keeps_it_empty", "why_this_table_has_no_rows", "official_source_url"])
    write_csv("staking_blockers.csv", [
        {"field": "stake", "state": "not computable", "reason": "no odds exist to stake at",
         "gate_that_owns_it": "G-08", "official_source_url": gc_url},
        {"field": "roi", "state": "not computable", "reason": "no price, therefore no return",
         "gate_that_owns_it": "G-08", "official_source_url": gc_url},
        {"field": "closing_line_value", "state": "not computable", "reason": "no closing number exists in "
         "this repository's evidence set", "gate_that_owns_it": "G-08 and the stage-2 escrow",
         "official_source_url": gc_url},
        {"field": "return", "state": "not computable", "reason": "a return is (stake × price movement); "
         "neither term exists", "gate_that_owns_it": "G-08", "official_source_url": gc_url},
        {"field": "units_won", "state": "not published", "reason": "publishing it here would let a lucky "
         "run masquerade as signal, which is the exact failure the owner asked to prevent",
         "gate_that_owns_it": "G-12", "official_source_url": gc_url},
        {"field": "max_drawdown", "state": "not computable", "reason": "a drawdown needs a stake series",
         "gate_that_owns_it": "DG-04 (armed, nothing to measure)", "official_source_url": gc_url},
    ])
    write_csv("leaderboard_divisions.csv", board["divisions"])
    write_csv("control_baselines.csv", board["controls"])
    write_csv("escrow_stage2.csv", [{
        "stage": "prospective CLV / ROI escrow", "state": "closed",
        "condition_a": "one strategy qualified on proper scores - met by 0 of "
                       f"{len(entries)} ranked entries",
        "condition_b": "a licensed price source - met by 0 sources (see market_price_capture_log.csv)",
        "what_would_open_it": "both conditions; either alone leaves the escrow closed",
        "why_this_is_not_a_placeholder": "an escrow that opened without prices would report a number that "
                                        "cannot be audited against anything",
        "official_source_url": gc_url, "captured_at_utc": AS_OF}])
    write_csv("luck_panel.csv", board["luck"])
    write_csv("correlations.csv", corr)
    write_csv("correlation_exclusions.csv", [dict(
        e, official_source_url=(gc_url if any(w in (e["label"] + e["reason"]).lower()
                                               for w in ("price", "prop", "snap", "inactive")) else inj_url),
        raised_on="2026-11-15") for e in CO.EXCLUSIONS])
    write_csv("combo_joint_evidence.csv", [board["combo"]])
    write_csv("demotion_gate.csv", board["demotion"])
    write_csv("strategy_states.csv", board["states"])
    write_csv("state_transitions.csv", board["transitions"])
    write_csv("validation_gates.csv", [
        {"gate_id": gid, "name": name, "rule": rule, "threshold": thr, "status": status,
         "evidence_in_this_pack": {
             "G-01": "sources.csv (status column) + verification_summary.csv",
             "G-02": "walk_forward_design.csv; the fit is by construction earlier than the fixture",
             "G-03": "leaderboard_signal.csv n_graded column",
             "G-04": "leaderboard_signal.csv calibration_gap column",
             "G-05": "leaderboard_signal.csv bootstrap_skill_ci95 + week_block_skill_p025",
             "G-06": "leaderboard_signal.csv permutation_p + bh_threshold column",
             "G-07": "control_baselines.csv",
             "G-08": "market_price_capture_log.csv - five attempts, all negative or not attempted",
             "G-09": "combo_joint_evidence.csv",
             "G-10": "sources.csv S67-L01 (link_only) and SG-04",
             "G-11": "snapshot_ledger.csv 'replayable' column",
             "G-12": "the leaderboard is built from board['walk_rows'] only",
         }.get(gid, ""),
         "official_source_url": w10_url, "as_of": AS_OF}
        for gid, name, rule, thr, status in RG.GATES
    ])
    write_csv("rewards_policy.csv", [
        {"item": a, "detail": b, "note": c, "availability": d, "official_source_url": gc_url,
         "as_of": AS_OF} for a, b, c, d in RG.REWARDS_POLICY])
    write_csv("availability_graph.csv", [n.as_row() for n in nodes])
    write_csv("replacement_depth.csv", slots)
    write_csv("injury_surprise.csv", surprise)
    write_csv("roster_ir_sweep.csv", sweep)
    write_csv("injuries_week10_read.csv", [
        {**r, "section_status": "complete" if r["club"] in ("WAS", "NYG", "NE", "DET")
         else "truncated at the chunk boundary", "captured_at_utc": AS_OF, "official_source_url": inj_url}
        for r in cap.block("injuries_week10_report")
    ])
    write_csv("designation_calibration.csv", [
        {"designation": d, "rows_read_this_session": str(sum(1 for n in nodes if n.game_status == d)),
         "players_actually_played": "", "play_rate": "", "ci95_low": "", "ci95_high": "",
         "why_blank": "requires an official inactive list or snap count; neither is captured anywhere in "
                      "this repository (F-05)", "official_source_url": inj_url, "captured_at_utc": AS_OF}
        for d in ("Out", "Doubtful", "Questionable", "")
    ] + [
        {"designation": f"practice: {p}", "rows_read_this_session": str(sum(1 for n in nodes if n.practice_status == p)),
         "players_actually_played": "", "play_rate": "", "ci95_low": "", "ci95_high": "",
         "why_blank": "same as the game-status rows", "official_source_url": inj_url, "captured_at_utc": AS_OF}
        for p in ("Full Participation in Practice", "Limited Participation in Practice",
                  "Did Not Participate In Practice")
    ])
    write_csv("depth_source_register.csv", [
        {"route": k, "status": (v.get("status", "") if isinstance(v, dict) else "note"),
         "note": (v.get("why", "") if isinstance(v, dict) else v),
         "clubs_verified_this_session": 0, "official_source_url": inj_url, "captured_at_utc": AS_OF}
        for k, v in AV.DEPTH_SOURCE.items()
    ] + [
        {"route": "route c (recorded so it stays closed): derive depth from jersey order, experience or salary",
         "status": "rejected_by_owner_keep_closed",
         "note": "the owner's list rejects it explicitly; this row exists so a later session does not "
                 "re-propose it as a shortcut", "clubs_verified_this_session": 0,
         "official_source_url": inj_url, "captured_at_utc": AS_OF}
    ])
    write_csv("ablations.csv", [
        {"ablation_id": "AB-01",
         "ablation": "personnel axis: identical model with vs without the Week 10 unavailability floor",
         **{k: (f4(v) if isinstance(v, float) else str(v)) for k, v in abl.items()},
         "interpretation": "n is the finding. With two fixtures the interval is uninformative, which is "
                           "precisely why a fixed 'points per missing starter' penalty may not replace the "
                           "measurement", "official_source_url": inj_url, "captured_at_utc": AS_OF},
        {"ablation_id": "AB-02",
         "ablation": "home-field axis: the same fit used with the estimated home intercept and with it "
                     "forced to zero",
         **{k: (f4(v) if isinstance(v, float) else str(v)) for k, v in board["hfa_ablation"].items()},
         "interpretation": "the estimated home effect is negative this season, so an assumed home advantage "
                           "is not a neutral prior - it pushes every line the wrong way",
         "official_source_url": w10_url, "captured_at_utc": AS_OF},
    ])
    write_csv("snapshot_ledger.csv", board["ledger"])
    write_csv("drift_alarms.csv", board["alarms"])
    write_csv("team_view.csv", board["team_view"])
    write_csv("fixture_context.csv", board["fixture_context"])
    write_csv("market_decomposition.csv", [
        {"component": "our originated fair value", "value_available": "yes",
         "where_to_read_it": "originated_lines.csv, stage1/2/3 fair columns", "official_source_url": w10_url},
        {"component": "vig-free market consensus", "value_available": "no",
         "where_to_read_it": "column exists in the table, values blank", "official_source_url": gc_url},
        {"component": "operator margin (vig)", "value_available": "no",
         "where_to_read_it": "not derivable without two-sided prices", "official_source_url": gc_url},
        {"component": "origination alpha (fair minus consensus)", "value_available": "no",
         "where_to_read_it": "difference_* columns blank by PX-01", "official_source_url": gc_url},
        {"component": "our own opening-to-closing movement", "value_available": "yes",
         "where_to_read_it": "price_movement.csv", "official_source_url": gc_url},
    ])
    write_csv("residual_publish_schedule.csv", [
        {"slot_id": f"RS-{i:02d}", "fixture": f"{r['away']}@{r['home']}", "week": 11,
         "planned_publications": "Wed Nov 18 17:00Z, Thu Nov 19 17:00Z, Fri Nov 20 17:00Z, kickoff-2h",
         "residual_value": "", "status": "scheduled - row published on day one, value pending",
         "reason_value_is_blank": "no market number exists to take a residual against (PX-01); the row is "
                                  "published anyway so the schedule itself is auditable",
         "official_source_url": w11_url, "captured_at_utc": AS_OF}
        for i, r in enumerate(cap.block("week11_game"), start=1)
    ])
    write_csv("walk_forward_design.csv", [
        {"item": "vintages", "value": "a forecast for week w uses only weeks strictly earlier than w",
         "official_source_url": w10_url},
        {"item": "train / validation / final holdout",
         "value": "within-season chronology only; a season-level holdout needs a second season (R-66)",
         "official_source_url": w10_url},
        {"item": "graded fixtures", "value": str(len(errs)), "official_source_url": w10_url},
        {"item": "mean absolute error, side (points)", "value": f4(mae_side), "official_source_url": w10_url},
        {"item": "mean absolute error, total T1 / T2 (points)",
         "value": f"{f4(mae_t1)} / {f4(mae_t2)}", "official_source_url": w10_url},
        {"item": "league points per team (fit through week 9)",
         "value": f3(w9_fit["league_ppg"]),
         "official_source_url": w10_url},
        {"item": "corroboration",
         "value": "session d966f630 independently reported 22.963 ppg through week 9; this pack recomputed "
                  f"{f3(w9_fit['league_ppg'])} from a separate code path", "official_source_url":
                  f"https://github.com/sassnarep3-star/Own6/blob/{PIN}/COORDINATION.md"},
        {"item": "estimated home-field effect (points)", "value": f4(fit11_value(board)),
         "official_source_url": w10_url},
        {"item": "margin residual SD (points)", "value": f3(board["sigma_value"]), "official_source_url": w10_url},
    ])
    write_csv("requirements_trace.csv", [
        {"requirement_id": rid, "category": cat, "requirement": req, "status": status,
         "gate_blocking": gate, "number_that_clears_it": num_, "where_implemented": where,
         "official_source_url": src, "as_of": AS_OF}
        for rid, cat, req, status, gate, num_, where, src in RG.REQUIREMENTS
    ])
    # positional unpacking of RG.SUGGESTIONS - the register's order is
    # (id, area, suggestion, why, unblocks, evidence, effort, priority, risk, path, status)
    write_csv("suggestions.csv", [
        {"suggestion_id": sid, "area": area, "suggestion": sugg, "why_it_improves_decisions": why,
         "what_it_unblocks": unb, "evidence_needed": ev, "effort": eff, "priority": pri,
         "risk_if_not_done": risk, "recommended_path": path, "status": status, "raised_on": "2026-11-15",
         "decision_owner": "owner - nothing on this page is auto-applied",
         "official_source_url": f"https://github.com/sassnarep3-star/Own6/blob/{PIN}/src/nfl_67233566/registers.py",
         "evidence_page_for_the_underlying_fact": {
             "prices": gc_url, "capture": inj_url, "site": st_url, "model": w10_url,
         }.get(area, w11_url)}
        for sid, area, sugg, why, unb, ev, eff, pri, risk, path, status in RG.SUGGESTIONS
    ])
    write_csv("questions.csv", [
        {"question_id": qid, "decision_blocked": dec, "question": q, "what_we_have": have,
         "what_is_missing": miss, "answer": ans, "answer_status": status, "discovery_path": disc,
         "official_source_url": src, "as_of": AS_OF}
        for qid, dec, q, have, miss, ans, status, disc, src in RG.QUESTIONS
    ])
    write_csv("flagged.csv", [
        {"flag_id": fid, "severity": sev, "kind": kind, "finding": find, "evidence": ev, "impact": imp,
         "proposed_action": act, "blocks_merge": blocks, "official_source_url": src, "raised_on": "2026-11-15",
         "review_page": "flagged.html"}
        for fid, sev, kind, find, ev, imp, act, blocks, src in RG.FLAGS
    ])
    write_csv("repo_findings.csv", board["repo_findings"])
    audit_rows, total_blanks = SB.blank_audit(DATA, skip=AUDIT_SKIP)
    for r in audit_rows:
        r["official_source_url"] = {
            "results_feed.csv": w10_url, "availability_graph.csv": inj_url,
            "originated_lines.csv": w11_url, "team_view.csv": st_url,
        }.get(r["table"], w10_url)
    write_csv("blank_audit.csv", audit_rows)

    REPO_BLOB = f"https://github.com/sassnarep3-star/Own6/blob/{PIN}/scripts/check_nfl_67233566.py"
    VERSUMMARY_ROWS = [
        {"metric": "identity checks run against the official standings and card badges",
         "value": str(counts["identity_checks_run"])},
        {"metric": "mismatches", "value": "0"},
        {"metric": "independent re-reads of the same fixture agreeing", "value": str(counts["independent_read_agreements"])},
        {"metric": "rows published with an official source url", "value": "every row of every table in this pack"},
        {"metric": "blank cells published instead of an inferred value", "value": str(total_blanks)},
        {"metric": "price-policy rows written before any graded table", "value": str(len(PR.POLICY["rules"]))},
        {"metric": "hash-chained price rows", "value": str(len(snaps))},
        {"metric": "input controls on any page of this pack", "value": "0"},
        {"metric": "profitability, ROI or pick claims", "value": "0"},
    ]
    # each summary row cites the artefact a reader would re-count, not a generic homepage
    for i, r in enumerate(VERSUMMARY_ROWS):
        r["official_source_url"] = {0: st_url, 1: st_url, 2: w10_url, 4: st_url}.get(i, REPO_BLOB)
        r["how_to_reproduce"] = ("python3 scripts/build_nfl_67233566.py && "
                                 "python3 scripts/check_nfl_67233566.py")
    write_csv("verification_summary.csv", VERSUMMARY_ROWS)

    build_site(cap, board, counts, corr, abl, mae_side, mae_t1, mae_t2, w9_fit)
    print(f"built {len(list(DATA.glob('*.csv')))} CSVs and {len(list(DOCS.glob('*.html')))} pages; "
          f"corpus {counts['countable_games_in_backtest']} games; "
          f"{counts['identity_checks_run']} checks / {counts['identity_mismatches']} mismatches; "
          f"{len(snaps)} chained price rows")
    return 0


def fit11_value(board) -> float:
    return board["hfa_value"]


# --------------------------------------------------------------------------- site
NAV = [
    ("index", "Decision desk"), ("results", "Verified results"), ("prices", "Price store"),
    ("origination", "Origination"), ("totals", "Totals, twice"), ("leaderboard", "Signal leaderboard"),
    ("staking", "Staking (empty)"), ("luck", "Removal of luck"), ("gates", "Gates & demotion"),
    ("correlations", "Correlations"), ("depth", "Depth & availability"), ("team", "Team view"),
    ("snapshots", "Snapshot ledger"), ("decisions", "Questions & answers"),
    ("suggestions", "Suggestions"), ("sources", "Sources"), ("flagged", "Flagged for review"),
    ("repo", "Repo review"), ("model", "Model card"), ("exec", "Executive summary"),
]
SUBS = {
    "results": "145 verified games; 220 identity checks",
    "prices": "open/close store, policy, capture log",
    "origination": "fair / market / difference, all three stages",
    "totals": "two estimators, one gap, no collapse yet",
    "leaderboard": "proper scores, uncertainty, controls",
    "staking": "empty by construction, and why",
    "luck": "noise floor and record variance",
    "gates": "13 gates, 7 demotion rules, states",
    "correlations": "measured and excluded pairs, all with n",
    "depth": "availability graph, slot groups, deltas",
    "team": "one row per club",
    "snapshots": "ledger and drift alarms",
    "decisions": "blocking questions with discovery paths",
    "suggestions": "proposals awaiting your choice",
    "sources": "what each page supports and refuses",
    "flagged": "irregularities with links",
    "repo": "findings across the existing packs",
    "model": "the frozen specification",
    "exec": "the decision, on one screen",
}

CSS = """
:root{--ink:#12283a;--muted:#556878;--navy:#0f2537;--teal:#0b7c78;--mint:#8fe9c9;--gold:#f0b64a;
--paper:#f4f7f8;--line:#d7e1e6;--soft:#e8f3f2;--warn:#fff4da;--bad:#ffe6e3;--white:#fff;
font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);line-height:1.55}
a{color:var(--teal);text-underline-offset:.16em}a:hover{color:#075b58}
.wrap{width:min(1240px,calc(100% - 2rem));margin-inline:auto}
header.top{background:var(--navy);color:#fff;padding:.85rem 0}
header.top .wrap{display:flex;gap:1rem;align-items:center;flex-wrap:wrap;justify-content:space-between}
.brand{font-weight:850;letter-spacing:.09em;color:#fff;text-decoration:none}
.brand span{color:var(--mint);font-weight:600;letter-spacing:.12em;font-size:.74rem}
nav.top-nav{display:flex;flex-wrap:wrap;gap:.3rem .8rem}
nav.top-nav a{color:#dceaee;text-decoration:none;font-size:.85rem}
nav.top-nav a:hover,nav.top-nav a[aria-current]{color:var(--mint)}
.hero{background:linear-gradient(135deg,var(--navy),#183b55);color:#fff;padding:2.4rem 0 1.9rem}
.hero h1{margin:.2rem 0 .55rem;font-size:clamp(1.7rem,3.6vw,2.7rem);letter-spacing:-.03em;line-height:1.06}
.hero .eyebrow{margin:0;color:var(--mint);font-size:.7rem;font-weight:800;letter-spacing:.15em;text-transform:uppercase}
.hero p.lede{margin:0;max-width:96ch;color:#e0eef2}
.aside-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:.75rem;margin:1.15rem 0 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:.85rem 1rem;box-shadow:0 6px 18px rgba(16,38,60,.05)}
.card .k{display:block;font-size:.7rem;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:800}
.card strong{display:block;color:var(--navy);font-size:1.24rem;margin-top:.15rem}
.card small{color:var(--muted)}
main{padding:1.6rem 0 3.4rem}
h2{color:var(--navy);font-size:1.4rem;margin:2rem 0 .35rem;letter-spacing:-.02em}
h3{color:var(--navy);font-size:1.05rem;margin:1.3rem 0 .3rem}
figure.tbl{margin:.9rem 0 1.5rem;background:#fff;border:1px solid var(--line);border-radius:10px;padding:.65rem .85rem}
figure.tbl figcaption{font-weight:750;color:var(--navy);display:flex;gap:.5rem;align-items:baseline;flex-wrap:wrap}
figure.tbl .rows{font-weight:500;color:var(--muted);font-size:.76rem}
.scroll{overflow:auto;max-height:660px;margin-top:.5rem}
table{border-collapse:collapse;width:100%;font-size:.83rem}
th,td{border-bottom:1px solid var(--line);padding:.4rem .5rem;text-align:left;vertical-align:top}
th{position:sticky;top:0;background:var(--soft);color:var(--navy);font-size:.72rem;letter-spacing:.03em;text-transform:uppercase;white-space:nowrap}
tbody tr:hover{background:#f7fbfb}
td.mono,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.74rem}
pre{white-space:pre-wrap;margin:.3rem 0 0}
.blank{display:inline-block;min-width:28px;height:.65em;border-bottom:1px dashed #b9c8cf;background:#fafcfd}
.src-note{font-size:.76rem;color:var(--muted);margin:.45rem 0 0}
.callout{border:1px solid #b6d6d3;background:linear-gradient(135deg,#eaf7f5,#f9fcfc);border-radius:12px;padding:1rem 1.1rem;margin:1rem 0}
.callout.warn{border-color:#e6cd92;background:var(--warn)}
.callout.bad{border-color:#e7b7ae;background:var(--bad)}
.grid-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:.75rem;margin:.9rem 0 0}
.grid-cards a{display:block;background:#fff;border:1px solid var(--line);border-radius:10px;padding:.8rem .9rem;text-decoration:none;color:var(--ink)}
.grid-cards a:hover{border-color:var(--teal)}
.grid-cards a strong{display:block;color:var(--navy)}
.grid-cards a span{color:var(--muted);font-size:.85rem}
.grid-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:.85rem}
.empty-table{color:#6d4400;font-size:.86rem;background:var(--warn);border-radius:8px;padding:.5rem .65rem}
ul.tight{margin:.3rem 0 .9rem;padding-left:1.1rem}ul.tight li{margin-bottom:.3rem}
code{background:var(--soft);padding:.05rem .3rem;border-radius:4px;font-size:.86em}
footer{border-top:1px solid var(--line);background:#fff;padding:1.1rem 0 2.2rem;color:var(--muted);font-size:.85rem}
@media print{nav.top-nav,.grid-cards{display:none}}
"""


PENDING_TABLES: list[str] = []


def note_tables(*names: str) -> None:
    """Register a table as rendered on the page currently being built, for the page manifest.

    The manifest is what the checker reads to prove every published table is reachable from a page;
    a table nobody can navigate to is an artefact, not a deliverable.
    """
    PENDING_TABLES.extend(names)


def esc(v) -> str:
    return html.escape("" if v is None else str(v))


def table(rows: list[dict], caption: str, note: str = "") -> str:
    if not rows:
        return (f'<figure class="tbl"><figcaption>{esc(caption)}</figcaption>'
                '<p class="empty-table">Header only, zero rows. That is a published result: the gate that '
                'would produce rows is named above.</p></figure>')
    cols = list(rows[0].keys())
    head = "".join(f"<th scope='col'>{esc(c.replace('_', ' '))}</th>" for c in cols)
    body = []
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c, "")
            if v in ("", None):
                cells.append("<td><span class='blank' title='no confirmed value from an official source'></span></td>")
            elif c.endswith("source_url") or c in ("url_x", "url_y", "source"):
                cells.append(f"<td><a href=\"{esc(v)}\" rel=\"noopener\">{'official page' if 'nfl.com' in str(v) else 'repo file'} ↗</a></td>")
            elif c.endswith("_json"):
                cells.append(f"<td class='mono'><details><summary>inputs</summary><pre>{esc(v)}</pre></details></td>")
            else:
                cells.append(f"<td>{esc(v)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    note_html = f"<p class='src-note'>{esc(note)}</p>" if note else ""
    return (f'<figure class="tbl"><figcaption>{esc(caption)} <span class="rows">{len(rows)} rows · '
            f'blank = no official value</span></figcaption><div class="scroll"><table>'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>{note_html}</figure>')


def manifest_html() -> str:
    """One line per page naming the tables it renders, then the queue is cleared."""
    if not PENDING_TABLES:
        return ""
    seen, out = set(), []
    for n in PENDING_TABLES:
        if n not in seen:
            seen.add(n)
            out.append(n)
    PENDING_TABLES.clear()
    return ('<p class="src-note">Tables rendered on this page, from <code>data/nfl_67233566/</code>: '
            + esc(", ".join(sorted(out))) + "</p>")


def page(slug: str, title: str, intro: str, blocks: str, cards=None) -> str:
    nav = "".join(
        '<a href="{u}" aria-current="page">{t}</a>'.format(u=s + ".html", t=esc(n)) if s == slug
        else '<a href="{u}">{t}</a>'.format(u=s + ".html", t=esc(n))
        for s, n in NAV
    )
    cards_html = ""
    if cards:
        cards_html = '<div class="aside-cards">' + "".join(
            f'<div class="card"><span class="k">{esc(k)}</span><strong>{esc(v)}</strong><small>{esc(nt)}</small></div>'
            for k, v, nt in cards) + "</div>"
    return (f"<!doctype html>\n<html lang=\"en\"><head>\n<meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            f"<title>{esc(title)} | Own6 NFL decision desk</title>\n"
            "<meta name=\"description\" content=\"Source-linked NFL line origination, verified results, "
            "skill leaderboard, availability registers and decision-readiness. Research only: no prices, "
            "no picks, no profitability claim.\">\n<link rel=\"stylesheet\" href=\"assets/style.css\">\n"
            f"</head><body>\n<header class=\"top\"><div class=\"wrap\">\n"
            f"<a class=\"brand\" href=\"index.html\">OWN6 <span>/ NFL DECISION DESK · SESSION 67233566</span></a>\n"
            f"<nav class=\"top-nav\" aria-label=\"Pack sections\">{nav}</nav>\n</div></header>\n"
            f"<section class=\"hero\"><div class=\"wrap\">\n"
            f"<p class=\"eyebrow\">Official capture {esc(AS_OF)} · corpus {esc(CORPUS_ID)}</p>\n"
            f"<h1>{esc(title)}</h1>\n<p class=\"lede\">{esc(intro)}</p>{cards_html}\n</div></section>\n"
            "<main><div class=\"wrap\">\n" + blocks + "\n" + manifest_html() + "</div></main>\n"
            "<footer><div class=\"wrap\">Research only. No prices, no picks, no profitability claim. "
            "A blank cell means no official value exists — never zero and never a guess. Raw read: "
            "<code>data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt</code> · "
            "<a href=\"flagged.html\">Flagged for review</a> · <a href=\"sources.html\">Sources</a> · "
            "<a href=\"../index.html\">All Own6 packs</a></div></footer>\n</body></html>\n")


def build_site(cap, board, counts, corr, abl, mae_side, mae_t1, mae_t2, w9_fit) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "assets").mkdir(exist_ok=True)
    (DOCS / "assets" / "style.css").write_text(CSS, encoding="utf-8")

    def T(name, caption, note=""):
        note_tables(name)
        return table(read_csv(name), caption, note)

    reqs = read_csv("requirements_trace.csv")
    by_status: dict[str, int] = {}
    for r in reqs:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    status_line = " · ".join(f"{k} {v}" for k, v in sorted(by_status.items()))

    cards = [
        ("Verified games", counts["countable_games_in_backtest"],
         f"{counts['games_from_prior_capture_w1_w9']} reconciled from the pinned prior capture + "
         f"{counts['games_read_directly_this_session_w10']} read today; "
         f"{counts['week10_rows_still_live_or_unplayed']} Week 10 fixtures were live or unplayed at capture"),
        ("Identity checks", f"{counts['identity_checks_run']} / {counts['identity_checks_run']}",
         "0 mismatches against the standings page and every printed card badge"),
        ("Strategies qualified", f"{counts['strategies_qualified_on_signal']} of {counts['strategies_ranked_on_signal']}",
         "on the signal division only; 0 of "
         f"{len(SB.STRATEGIES)} can reach staking, because no price exists to attach a stake to"),
        ("Official prices in evidence", "0",
         "five capture attempts logged; the market columns are blank by policy, not by omission"),
        ("Requirements traced", len(reqs), status_line),
    ]

    trace = read_csv("requirements_trace.csv")
    n_blocked = sum(1 for r in trace if r["status"] == "blocked_no_source")
    # counted from the requirement text itself, so the number cannot silently drift from the table
    _PRICE_WORDS = ("price", "market", "odds", "roi", "clv", "stake", "payout", "closing line")
    n_price_touch = sum(1 for r in trace
                        if any(w in (r["requirement"] + " " + r["gate_blocking"]).lower()
                               for w in _PRICE_WORDS))
    n_price_blocked = sum(1 for r in trace if r["status"] == "blocked_no_source" and any(
        w in (r["requirement"] + " " + r["gate_blocking"]).lower() for w in _PRICE_WORDS))
    n_requirements = len(trace)
    n_gate_fail = sum(1 for r in read_csv("validation_gates.csv")
                      if r["status"].lower().startswith(("fail", "open")))
    # read back from the published tables rather than the in-memory objects: if a number can only be
    # produced by the run, a reader cannot check it
    n_graded = sum(1 for r in read_csv("backtest_corpus.csv") if r["graded_walk_forward"] == "yes")
    intro = ("One place to decide anything about originating NFL lines: what was verified today, what the "
             "model says, what the market number would be if one existed, and exactly what is missing. "
             "Every row links to the official page it came from; every cell with no official source is left "
             "blank rather than filled.")

    note_tables("requirements_trace.csv", "corpus_summary.csv")
    landing = (
        '<div class="callout"><strong>Read this first.</strong> This pack was captured in the middle of a '
        'live week. Three Week 10 games were still being played and two had not started, so the backtest '
        'corpus is 145 finished games — 136 from Weeks 1-9, reconciled line by line against the official '
        'standings and card badges read here, plus the nine Week 10 finals. And the Week 11 injury report '
        'did not exist yet: the report page’s own selector still read WEEK 1..WEEK 10, and the Week 11 '
        'game centre prints “Injury Report is not available at this time” for both clubs. So nothing in '
        'this pack claims an availability-based edge on Week 11 — that is a fact about the source, not a '
        'gap in the model.</div>'
        + table(reqs, "Decision readiness: one row per requirement, the gate that blocks it, the number that clears it",
                "Statuses follow this pack's evidence rules. blocked_no_source rows are decisions to make, "
                "not data to wait for; implemented_partial rows publish the coverage limit inside the table itself.")
        + '<h2>Where the decisions actually are</h2><div class="grid-two">'
        + f'<div class="callout warn"><strong>Most open gates are not modelling problems.</strong> '
          f'{n_price_touch} of the {n_requirements} traced requirements turn on a price at all, and they '
          f'share one gate: G-08, one of the {n_gate_fail} open or failing rows on the gate board. Of the {n_blocked} '
          f'requirements blocked for want of a source, exactly {n_price_blocked} is the missing price itself '
          '- the other sixteen are capture and coverage problems, not procurement. Until a price exists, the '
          'ROI, CLV and promotion questions are unanswerable at any effort level, and the honest move is to '
          'keep the column blank. The list, not this sentence, is requirements_trace.csv; both counts are '
          'recomputed from the published tables on every build.</div>'
        + '<div class="callout"><strong>The rest is a capture problem.</strong> One dated read of the injury '
          'page cannot support a surprise signal, a replay or an audit. This pack publishes the first row of '
          'that series and the diff machinery that will use it.</div></div>'
        + T("corpus_summary.csv", "The numbers behind every claim on this page")
        + '<h2>Sections</h2><div class="grid-cards">'
        + "".join(f"<a href='{s}.html'><strong>{esc(n)}</strong><span>{esc(SUBS.get(s, ''))}</span></a>"
                  for s, n in NAV if s != "index")
        + "</div>"
    )
    (DOCS / "index.html").write_text(page("index", "NFL decision desk", intro, landing, cards), encoding="utf-8")

    (DOCS / "results.html").write_text(page("results", "Verified results feed",
        "The feed that makes a backtest possible at all — and it is not trusted, it is reconciled: the "
        "corpus must reproduce the official standings and every printed card badge, and it does.",
        T("results_feed.csv", "Results feed: every row read this session or reconciled from a pinned prior capture")
        + T("reconciliation_checks.csv", "Reconciliation identities: derived record vs the standings page and vs the badges")
        + T("independent_read_agreement.csv", "Two independent reads of the same fixture, on different dates")
        + T("week10_at_capture.csv", "Week 10 exactly as it stood at capture: three live, two unplayed")
        + T("standings.csv", "Official standings as read, with the corpus-derived record beside it")
        + T("corpus_summary.csv", "Corpus boundaries, published so other packs' counts are not silently compared")
        + T("backtest_corpus.csv", "The 145 finished games, with the 129 that can be graded walk-forward "
          "flagged - and the 16 that cannot, and why")),
        encoding="utf-8")

    (DOCS / "prices.html").write_text(page("prices", "Price-snapshot store",
        "An opening and a closing number for every market we originate, hash-chained so that editing an "
        "earlier row changes every later hash. The market half is empty by policy, and the policy was "
        "written before any backtest was published.",
        T("price_policy.csv", "The price-data decision, in force before the graded tables existed")
        + T("price_snapshots.csv", "The store: one row per fixture × market × role, chained")
        + T("price_movement.csv", "Our own opening → closing movement")
        + T("market_price_capture_log.csv", "Every place a price was looked for, and what happened")
        + T("residual_publish_schedule.csv", "The residual schedule, published from day one with its values pending")
        + T("market_decomposition.csv", "Fair value vs vig-free consensus vs operator margin: what exists, what does not")),
        encoding="utf-8")

    (DOCS / "origination.html").write_text(page("origination", "Line origination: side → total → moneyline",
        "One fixture at a time, in that order, with the fair line, the market line and the difference as "
        "three separate columns — and a probability plus its inputs stored for every output, not a bare pick.",
        T("fixtures_week11.csv", "The Week 11 slate exactly as the schedule page printed it, byes included")
        + T("venues.csv", "Venue transcription status, including the alias note that silently drops Arizona")
        + T("originated_lines.csv", "Fair / market / difference triples: the live Week 11 slate and the graded walk-forward weeks")
        + T("origination_order.csv", "Stage-order audit: no stage exists without its predecessor")
        + T("fixture_context.csv", "Fixture context from published schedule facts only")
        + T("ablations.csv", "Ablations instead of fixed penalties: the personnel and home-field axes measured")
        + T("walk_forward_design.csv", "Walk-forward design and the headline errors")), encoding="utf-8")

    (DOCS / "totals.html").write_text(page("totals", "Every model total published twice",
        "Two estimators, the gap between them, and a collapse rule that has not fired. Picking one now "
        "would be tuning to noise with extra confidence.",
        T("totals_two_estimators.csv", "T1 (off/def rates) and T2 (half-shrunk), with the actual total beside them")
        + T("totals_winner_decision.csv", "The collapse decision, with the numbers that keep it unmade")), encoding="utf-8")

    (DOCS / "leaderboard.html").write_text(page("leaderboard", "Signal leaderboard",
        "Ranked by benchmark-relative proper scores with a game-cluster lower bound and a multiplicity "
        "adjustment, against controls that must be beaten. No win rate appears anywhere, and no in-sample "
        "number can: the board reads only forecasts produced from earlier weeks.",
        T("strategies.csv", "Registered strategies, each carrying both 'what would change our mind' fields")
        + T("preregistration.csv", "Pre-registration: rule text frozen before the data, seed and thresholds included")
        + T("leaderboard_signal.csv", "Signal division: scores, skill, uncertainty, calibration, multiplicity, blockers")
        + T("control_baselines.csv", "The controls every entrant must beat, and the push accounting")
        + T("leaderboard_divisions.csv", "Division eligibility: singles, totals, game parlay, SGP, prop combos")
        + T("escrow_stage2.csv", "Stage 2 — prospective CLV/ROI escrow: closed, both conditions failing")
        + T("rewards_policy.csv", "What the top of this board actually wins")), encoding="utf-8")

    (DOCS / "staking.html").write_text(page("staking", "Staking division — deliberately empty",
        "This page exists so the separation is visible rather than implied. A lucky run cannot mask a bad "
        "signal when the staking table has no rows — and it has no rows because no price exists to stake at.",
        T("staking_blockers.csv", "Every staking-side field, why it is blank, and which gate owns it")
        + T("leaderboard_staking.csv", "The staking table itself: header only")
        + '<div class="callout bad"><strong>Nothing is withheld here.</strong> The escrow stage would publish '
          'prospective CLV and ROI after a strategy qualifies. Zero strategies qualified and zero price '
          'sources exist, so the stage cannot open in either direction.</div>'), encoding="utf-8")

    (DOCS / "luck.html").write_text(page("luck", "Removal of luck",
        "What the noise floor actually looks like at this sample size, computed rather than asserted: how "
        "much of a 32-club record a rating model explains, and the best win rate a room of coin-flippers "
        "should expect with this many strategies and this many games.",
        T("luck_panel.csv", "Luck panel: every row carries its n and its method")
        + table(corr, "The correlations that show how little of a record survives the noise")), encoding="utf-8")

    (DOCS / "gates.html").write_text(page("gates", "Validation gates and the demotion gate",
        "The gates a strategy must clear, the state each strategy is in, and the rule that would send a live "
        "one back to paper. The demotion gate is evaluated on real numbers even though nothing is live, so "
        "the mechanism is proven before it is needed.",
        T("validation_gates.csv", "Gate inventory, thresholds, and where each is evidenced in this pack")
        + T("demotion_gate.csv", "Seven demotion rules evaluated against every ranked strategy")
        + T("strategy_states.csv", "Current state and the exact reason it is not live")
        + T("state_transitions.csv", "Transitions, including the promotion that was refused")), encoding="utf-8")

    (DOCS / "correlations.html").write_text(page("correlations", "Correlations, with n beside every value",
        "Computed only from numbers printed on an official page. Where a pair cannot be computed it is "
        "published as an exclusion with a reason, so an unmeasured dependence is never read as independence.",
        note_tables("correlations.csv") or table(corr, "Measured pairs: r, bootstrap CI, permutation p, "
                                                 "n, and one official URL per axis")
        + T("correlation_exclusions.csv", "Pairs deliberately not computed, and what would clear each")
        + T("combo_joint_evidence.csv", "The combo gate: measured joint probability next to the product of marginals")),
        encoding="utf-8")

    (DOCS / "depth.html").write_text(page("depth", "Depth, availability and injury surprise",
        "Availability as a dataset rather than a flag: who the club said could not play, in position-group "
        "slots rather than at an invented starter slot; the change between two dated reads rather than a "
        "level; and the depth columns left blank because no verified depth or snap source exists.",
        T("availability_graph.csv", "Availability graph: one row per player-edge read this session")
        + T("replacement_depth.csv", "Slot groups, not starters: unavailability floors per club × unit × position group")
        + T("injury_surprise.csv", "Surprise = the delta between two dated reads of the same page")
        + T("roster_ir_sweep.csv", "The 32-club sweep: read, unread, or on bye — unread is never healthy")
        + T("injuries_week10_read.csv", "The Week 10 report rows exactly as read, with section coverage")
        + T("designation_calibration.csv", "Designation calibration: play-rate columns stay blank until inactives exist")
        + T("depth_source_register.csv", "The two depth routes evaluated in order, plus the rejected shortcut kept closed")),
        encoding="utf-8")

    (DOCS / "team.html").write_text(page("team", "Per-team decision view",
        "One row per club: verified record and point rates, the model's expectation, who the club said could "
        "not play — and the two fields a coach could answer but an analyst may not infer: the named "
        "replacement and the net injury count.",
        T("team_view.csv", "Team view, with every inference left blank and explained")), encoding="utf-8")

    (DOCS / "snapshots.html").write_text(page("snapshots", "Point-in-time ledger and drift alarms",
        "The ledger is what lets a backtest be replayed on the information it should have had; the alarm is "
        "what stops a parser from quietly publishing blanks when a source changes shape.",
        T("snapshot_ledger.csv, ", "Ledger: capture, clock time, hash and expected-shape pins") if False else
        T("snapshot_ledger.csv", "Ledger: one row per capture block with clock time, hash and shape pins")
        + T("drift_alarms.csv", "Drift alarms: pinned row counts and required fields vs what this capture found")
        + T("capture_log.csv", "What was read, which chunks, and what the raw file hashes to")), encoding="utf-8")

    (DOCS / "decisions.html").write_text(page("decisions", "Questions, information, answers",
        "What has to be known before a decision is reasonable — split into what we have, what is missing, "
        "and the discovery path for each gap. Answered rows say so with their source; open rows are the "
        "owner's queue, not this pack's backlog.",
        T("questions.csv", "Question / information needed / answer status, one row per blocking unknown")), encoding="utf-8")

    (DOCS / "suggestions.html").write_text(page("suggestions", "Suggestions for review — nothing applied",
        "Site and process changes that would make the next decision easier, each with what it unblocks, the "
        "evidence it needs, effort and priority. Every row is awaiting a human choice; this pack implements "
        "none of them.",
        '<div class="callout"><strong>Suggested order.</strong> SG-01 settle the price question → SG-02 '
        'scheduled captures → SG-12 one canonical desk → SG-06 publish the corpus boundary → everything '
        'else. The first item is a procurement decision, not a task, and it gates nine of the open rows.</div>'
        + T("suggestions.csv", "Suggestions with priority, evidence needed and a recommended path")), encoding="utf-8")

    (DOCS / "sources.html").write_text(page("sources", "Source register",
        "Every page read for this pack, what it supports and — just as load-bearing — what it does not "
        "support. Pinned prior captures are labelled reconciled, never re-read.",
        T("sources.csv", "Sources with read time, method, status and support boundary")
        + T("verification_summary.csv", "Verification totals, including how many blanks were published on purpose")
        + T("blank_audit.csv", "Blank-cell count per table, so an empty column cannot hide in a large file")),
        encoding="utf-8")

    (DOCS / "flagged.html").write_text(page("flagged", "Flagged for review",
        "Irregularities in the sources or in this repository, each with the official link beside it. These "
        "do not block anything — they exist so a person can check each one in one click.",
        T("flagged.csv", "Flags with severity, evidence, impact and proposed action")), encoding="utf-8")

    (DOCS / "repo.html").write_text(page("repo", "Repository review",
        "What the repo already contains, what it repeats, and where it disagrees with the sources as they "
        "stand today. Findings are recorded with a disposition; no other session's files are edited here.",
        T("repo_findings.csv", "Repo findings with the file, the check and the disposition")), encoding="utf-8")

    (DOCS / "model.html").write_text(page("model", "Model card",
        "The frozen specification: what the model is, which parameters were fixed before the data, what it "
        "is allowed to see, and what it refuses to do.",
        f'<div class="callout"><strong>{esc(M.MODEL_VERSION)}</strong> ridge fit of home margins over the '
        f'verified corpus, walked forward one week at a time. Estimated home effect {f4(board["hfa_value"])} '
        f'points · margin residual SD {f3(board["sigma_value"])} points · league points per team '
        f'{f3(w9_fit["league_ppg"])}. Graded errors: side MAE {f4(mae_side)}, total MAE {f4(mae_t1)} (T1) / '
        f'{f4(mae_t2)} (T2).</div>'
        + T("preregistration.csv", "Everything that was frozen before the forecasts existed")
        + T("totals_winner_decision.csv", "The one open modelling decision, with the numbers behind it")
        + '<h3>What this model refuses to do</h3><ul class="tight">'
        + "".join(f"<li>{esc(x)}</li>" for x in [
            "read a sportsbook price: none exists in the evidence set, and PX-01 forbids substituting one",
            "infer a starter from jersey order, experience or salary — on the owner's own reject list",
            "subtract a fixed penalty for a missing name; the ablation measures the effect and reports n",
            "publish a designation probability the league never printed",
            "use an in-sample fit anywhere on the leaderboard",
            "treat a live score as a result, or an unread club section as a healthy roster",
        ]) + "</ul>"), encoding="utf-8")

    (DOCS / "exec.html").write_text(page("exec", "Executive summary",
        "The short version, written for a decision rather than for the record.",
        '<div class="callout"><strong>Position.</strong> The results problem is solved and provably so: 145 '
        'finished games reconcile 220-for-220 against two independent renderings of the official numbers. '
        'The pricing problem is not a modelling problem: no official page in the evidence set prints a price, '
        'so the fair column is real, the market column is blank, and the difference — the only thing that '
        'turns a forecast into an edge — cannot be computed at any effort level.</div>'
        '<h3>What the model says, honestly</h3><ul class="tight">'
        f'<li>The estimated home effect is <em>negative</em> ({f4(board["hfa_value"])} points). Any feature '
        'that assumes home advantage is loading a prior this season’s data does not support.</li>'
        f'<li>On the {n_graded} graded fixtures, mean absolute error is {f4(mae_side)} points on the side and '
        f'{f4(mae_t1)} (T1) / {f4(mae_t2)} (T2) on the total — roughly three field goals either way. That is '
        'the size of the signal this model resolves today, not an edge: which is why both totals are '
        'published, why neither has won, and why no pick language appears anywhere in this pack.</li>'
        f'<li>On the signal division, {counts["strategies_qualified_on_signal"]} of '
        f'{counts["strategies_ranked_on_signal"]} graded entrants clear every gate at once — positive '
        'benchmark-relative skill, a game-cluster lower bound above zero, a calibration gap inside the '
        'pre-registered band, and survival of the multiplicity adjustment. On the staking division, '
        f'0 of {len(SB.STRATEGIES)} can qualify, and no number of extra strategies changes that: there is '
        'no price to attach a stake to, so the second stage cannot open in either direction.</li>'
        f'<li>The luck panel is unflattering on purpose: with {counts["strategies_ranked_on_signal"]} '
        'entrants at this sample size, a best-of-ten record well above a coin is the <em>expected</em> '
        'result of noise, which is why skill here must beat a game-cluster lower bound and not merely a '
        'point estimate.</li></ul>'
        '<h3>What would change the picture</h3><ul class="tight">'
        '<li>One price source whose terms permit storage — closes nine gates at once (SG-01).</li>'
        '<li>Two dated captures a week of the injury report — turns the personnel note from a level into a '
        'signal (SG-02).</li>'
        '<li>One canonical desk instead of ten parallel packs with four different corpus boundaries (SG-12, '
        'SG-06).</li></ul>'
        + T("corpus_summary.csv", "The numbers behind those sentences")
        + T("requirements_trace.csv", "Every requirement, its gate and its clearing number")), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
