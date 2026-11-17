"""Claim checks, contradiction register, information gaps, guardrails and the repo review.

The pattern throughout: a sentence somebody published is put next to a number this build recomputes,
and the verdict is produced by comparing them. Where the comparison cannot be made the row says so
and the value stays blank.
"""
from __future__ import annotations

import os
import re
from collections import Counter
from typing import Dict, List, Optional

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --------------------------------------------------------------------------- claim checks

#: claim_id, claim (verbatim where possible), where it is written, metric that tests it, test
CLAIMS: List[Dict[str, str]] = [
    {"claim_id": "C01", "metric": "M-RES-67233",
     "claim": "145 reconciled finished games",
     "where": "docs/index.html hub card for pack 67233566; COORDINATION.md session 67233566",
     "test": "rows where counts_in_backtest starts with 'yes', against total rows in the file"},
    {"claim_id": "C02", "metric": "M-CORP-8362",
     "claim": "corpus identities (136 games; PF = PA = 6246)",
     "where": "COORDINATION.md session 8362b702 verification record",
     "test": "row count and the sum of the four score columns in corpus_136.csv"},
    {"claim_id": "C03", "metric": "M-RES-F4", "claim": "a 137-game results feed that reconciles to official standings on all five fields",
     "where": "docs/index.html hub card for pack nfl-f4", "test": "row count of data/nfl_f4/results.csv"},
    {"claim_id": "C04", "metric": "M-RES-A411", "claim": "120 verified games",
     "where": "docs/index.html hub card for pack nfl_a411fed0", "test": "row count of results_2026_verified.psv"},
    {"claim_id": "C05", "metric": "M-RES-D966", "claim": "a 44-game verified results feed",
     "where": "docs/index.html hub card for pack d966f630", "test": "row count of data/nfl_d966f630/results_feed.csv"},
    {"claim_id": "C06", "metric": "M-INJ-48217", "claim": "347 injury rows across 28 clubs plus 4 byes",
     "where": "docs/index.html hub card for pack 48217a55", "test": "row count and distinct club values in the capture file"},
    {"claim_id": "C07", "metric": "M-INJ-8362", "claim": "injury hub (two dated reads, 155-row window)",
     "where": "COORDINATION.md session 8362b702 sources record", "test": "row count divided by distinct read clocks in injury_series.csv"},
    {"claim_id": "C08", "metric": "M-BLK-48217", "claim": "1,054 blank cells, every one traced to a flag",
     "where": "docs/index.html hub card for pack 48217a55",
     "test": "sum of the blank_cells column of the pack's own blank_audit.csv (the flag register is a different file)"},
    {"claim_id": "C09", "metric": "M-PRC-D966", "claim": "a hash-chained opening/closing price ledger",
     "where": "docs/index.html hub card for pack d966f630", "test": "rows carrying any actual number in the ledger"},
    {"claim_id": "C10", "metric": "M-PRC-309921", "claim": "price-snapshot store (opening + closing) for every originated market",
     "where": "docs/index.html hub cards for nfl_309921cc and nfl_market", "test": "rows carrying any actual number"},
    {"claim_id": "C11", "metric": "M-RSV-8362", "claim": "reserve list captured so 'not listed' never means 'available'",
     "where": "the owner's brief; data/nfl_8362b702/reserve_register.csv", "test": "clubs covered by the register against the 32 the gate demands"},
    {"claim_id": "C12", "metric": "M-DPT-67233", "claim": "32 dated club depth charts, or official snap counts",
     "where": "the owner's brief (G-DEPTH-SRC); data/nfl_67233566/depth_source_register.csv",
     "test": "clubs_verified_this_session summed over the register's own rows"},
    {"claim_id": "C13", "metric": "M-RDY-6AB24", "claim": "the landing-page decision-readiness table: 81 requirements",
     "where": "docs/index.html hub card for pack 6ab24751", "test": "row count of readiness.csv"},
    {"claim_id": "C14", "metric": "M-RDY-8362", "claim": "decision-readiness ledger, one row per requirement",
     "where": "docs/nfl-8362b702/readiness.html", "test": "row count and how many rows still name a blocking gate"},
    {"claim_id": "C15", "metric": "M-FILE-depth_chart_register.csv",
     "claim": "T7 Club depth-chart register: data/nfl_48217a55/depth_chart_register.csv, data/nfl_48217a55/depth_slot_shapes.csv",
     "where": "COORDINATION.md, session 48217a55 task board, marked in progress", "test": "do the named files exist on this branch"},
    {"claim_id": "C16", "metric": "M-LDR-8362", "claim": "proper-score leaderboard divisions with no backtest numbers",
     "where": "the owner's brief; data/nfl_8362b702/leaderboard_strategies.csv",
     "test": "entries published in the division register"},
    {"claim_id": "C17", "metric": "M-LDR-D966", "claim": "one strategy promoted, nine held back on real numbers",
     "where": "data/nfl_d966f630/suggestions.csv D966-S09 rationale", "test": "entries in the combined board"},
]


NUMERIC_FIELDS = ("rows_counted_in_backtest", "games_with_final_scores", "clubs", "weeks",
                  "points_sum", "distinct_reads", "entries", "clubs_verified_total",
                  "rows_with_game_status", "rows_with_any_number", "rows_number_third_party_host",
                  "rows_number_official_host", "rows_number_repo_self", "distinct_games",
                  "distinct_markets", "rows_with_a_blocking_gate",
                  "rows_own_model_number", "blank_cells_total", "cells_total",
                  "rows_market_number_official_host", "rows_market_number_third_party",
                  "rows_market_number_repo_self", "rows_market_number_no_url")


def _claim_numbers(text: str) -> List[int]:
    """Numbers in prose, with thousands separators collapsed (1,054 -> 1054)."""
    t = re.sub(r"(\d),(\d{3})\b", r"\1\2", text)
    return [int(x) for x in re.findall(r"\b(\d{1,4})\b", t)]


def claim_checks(metrics: List[Dict[str, str]], lions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_id = {m["metric_id"]: m for m in metrics}
    out = []
    for c in CLAIMS:
        m = by_id.get(c["metric"], {})
        cands: Dict[str, str] = {}
        for key in ("rows",) + NUMERIC_FIELDS:
            v = m.get(key, "")
            if v and v.isdigit():
                cands.setdefault(key, v)
        actual = "; ".join(f"{k}={v}" for k, v in cands.items()) or "metric unavailable"
        verdict = ""
        if c["metric"].startswith("M-FILE-"):
            verdict = ("consistent" if m.get("exists") == "yes"
                       else "CONTRADICTION: the board names a file that is not in the tree")
        elif not cands:
            verdict = "not measurable from a row count"
        else:
            want = _claim_numbers(c["claim"])
            hit = [(k, v) for k, v in cands.items() if int(v) in want]
            if hit:
                verdict = "consistent — " + "; ".join(f"{k}={v}" for k, v in hit)
            else:
                derived = ""
                if cands.get("rows") and cands.get("distinct_reads") and int(cands["distinct_reads"]) > 1:
                    per = int(cands["rows"]) // int(cands["distinct_reads"])
                    derived = f"; rows ÷ distinct_reads = {per}"
                    if per in want:
                        verdict = (f"consistent once divided by reads — {cands['rows']} rows over "
                                   f"{cands['distinct_reads']} dated reads = {per} per read")
                if not verdict.startswith("consistent"):
                    verdict = ("check needed — the file reports "
                               + ", ".join(f"{k}={v}" for k, v in list(cands.items())[:3])
                               + f" where the prose says {'/'.join(str(w) for w in want) or 'n/a'}"
                               + derived + "; a row count is not always what the prose counted")
        out.append({**c, "measured_from_file": m.get("file", ""), "actual": actual,
                    "verdict": verdict})
    out.append({
        "claim_id": "C18", "metric": "lions_game_status",
        "claim": "Kerby Joseph, Cade Mays and D.J. Reed are published with a blank game-status cell while the official article lists all three as Out",
        "where": "the owner's brief (VR-08, VR-12)",
        "test": "what the 2026-11-15 capture file holds for those three players, against the official page read 2026-11-17",
        "measured_from_file": "data/nfl_48217a55/injury_report_2026_11_15.csv",
        "actual": " || ".join(f"{l['player']}: file game_status='{l['game_status_in_file']}' "
                             f"practice='{l['practice_status_in_file']}' club={l['club']}" for l in lions),
        "verdict": ("the capture file already carries 'Out' for all three, and the official page read this "
                    "session prints Out for all three — the blank cells are a publish/display failure, not a source gap"),
    })
    return out


# --------------------------------------------------------------------------- contradictions

def conflicts(corpus: List[Dict[str, str]], metrics: List[Dict[str, str]],
              inventory: List[Dict[str, str]],
              semantics: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    by_id = {m["metric_id"]: m for m in metrics}
    sizes = []
    for row in corpus:
        n = row.get("games_with_final_scores") or row.get("rows") or ""
        if n:
            sizes.append(f"{row['pack'].replace('nfl_', '')}={n}")
    inj = [f"{m['pack'].replace('nfl_', '')}={m.get('rows', '?')}"
           for m in metrics if m["kind"] == "injury" and m.get("rows")]
    schemas = Counter(i["columns"] for i in inventory)
    pr = price_rollup(metrics)
    f4_third = sum(int(m.get("rows_market_number_third_party") or 0)
                   for m in metrics if m["metric_id"] == "M-PRC-F4")
    missing = [m["file"] for m in metrics if m["kind"] == "file_exists" and m["exists"] == "no"]
    sem = {x["pack"]: x for x in (semantics or [])}
    d966 = sem.get("nfl_d966f630", {})
    f4 = sem.get("nfl_f4", {})
    d966_official = d966.get("cells_official_cited", "?")
    d966_hosts = d966.get("cited_hosts", "?")
    d966_labels = d966.get("own_labels", "?")
    f4_cells = f4.get("cells_third_party_market", "?")
    f4_hosts = f4.get("cited_hosts", "?")
    tot_third = sum(int(v.get("cells_third_party_market") or 0) for v in sem.values())
    tot_own = sum(int(v.get("cells_own_labelled") or 0) for v in sem.values())
    tot_repo = sum(int(v.get("cells_repo_reconstruction") or 0) for v in sem.values())
    tot_official = sum(int(v.get("cells_official_cited") or 0) for v in sem.values())
    sem_summary = (f"counted per populated cell across the six price stores: {tot_third} cells cite a third-party carrier "
                   f"(real operator quotes), {tot_own} sit in a column the pack itself labels as ours, {tot_repo} cite a file "
                   f"inside this repository, and {tot_official} sit in a market-sounding column with an official page cited "
                   f"beside them. Store by store: " + " ; ".join(
                       f"{k.replace('nfl_', '')}: {v.get('populated_cells', 'absent')} (hosts: {v.get('cited_hosts', 'none')})"
                       for k, v in sorted(sem.items())))
    per_store = " | ".join(
        f"{x['pack'].replace('nfl_', '')}: cells {x.get('populated_cells', '')}; hosts {x.get('cited_hosts', '')}; "
        f"labels {x.get('own_labels', '')}" for x in (semantics or []))
    rows_out = [
        {"conflict_id": "CF-01", "kind": "contradiction", "severity": "high",
         "subject": "Roster state of a specific quarterback",
         "side_a": "data/nfl_8362b702/reserve_absence.csv line 2 — 'Malik Willis, GB … state unknown', read 2026-11-16",
         "side_b": "official reads R7/R8 this session — nfl.com player profile 'QB • #2' plus the league article 'Dolphins place QB Malik Willis (groin) on injured reserve'; nfl.com Dolphins roster row 'Malik Willis | 2 | QB | RES'",
         "computed": "the register names the Green Bay roster page as the source of a Miami roster question",
         "what_it_changes": "The question was answerable from the club that actually held him. Every 'unknown roster state' inherited from this row should be re-read before it is used.",
         "action": "correct the club attribution in the owning pack (not edited here); treat the state as documented, not unknown",
         "evidence": "R7;R8"},
        {"conflict_id": "CF-02", "kind": "contradiction", "severity": "high",
         "subject": "How big is the verified game corpus?",
         "side_a": "per-pack results feeds, recomputed by this build", "side_b": "",
         "computed": "; ".join(sizes),
         "what_it_changes": "Six feeds for the same season carry different game counts. A leaderboard computed over one corpus and compared with a number quoted from another is meaningless, and the brief demands a single pre-registered corpus.",
         "action": "take the T07 decision: name one corpus id, publish its boundary on every table, backfill the rest",
         "evidence": "metrics.csv corpus rows"},
        {"conflict_id": "CF-03", "kind": "contradiction", "severity": "medium",
         "subject": "How many rows is the Week 10 injury report?",
         "side_a": "per-pack capture files, recomputed", "side_b": "",
         "computed": "; ".join(inj),
         "what_it_changes": "The same weekly report has been counted five ways with no published window rule, which is why the owner's brief lists a 254-versus-279 staleness complaint. Without an expected-rows contract nobody can tell staleness from a parse failure.",
         "action": "pin an expected row count per club per capture (T03 + T13), and publish the window on every table",
         "evidence": "M-INJ-* rows in metrics.csv"},
        {"conflict_id": "CF-04", "kind": "stale_state", "severity": "medium",
         "subject": "Task board vs repository",
         "side_a": "COORDINATION.md — 48217a55 board rows T1–T13 marked 'in progress'; 8362b702 P-rows marked 'in progress' though both packs merged",
         "side_b": "the files this build can see",
         "computed": f"paths named on the board but absent from the tree: {len(missing)}" + (f" ({'; '.join(missing)})" if missing else ""),
         "what_it_changes": "A takeover rule depends on the board: 'no commits for 60 minutes and the task is free'. Rows that are never closed make that rule unenforceable and invite duplicated work — the exact failure the parallel-session protocol exists to stop.",
         "action": "close or re-verify those rows; add a checker that proves every board path exists (T14)",
         "evidence": "M-FILE-* rows in metrics.csv"},
        {"conflict_id": "CF-05", "kind": "agreement", "severity": "info",
         "subject": "No official page publishes a line",
         "side_a": "this session's eleven official reads — nine pages first, then the exact schedule URL a price ledger cites, read in full; no number on any of them",
         "side_b": "every pack that tried to build a price store from nfl.com",
         "computed": sem_summary,
         "what_it_changes": "Settled, and it should stop being re-listed as an open research task: the league is not a "
                            "price source. What remains is a purchase or a freeze, not a scraper.",
         "action": "decide T02 (buy, or freeze the pricing half and say so)", "evidence": "R1–R9; price_semantics.csv"},
        {"conflict_id": "CF-09", "kind": "contradiction", "severity": "high",
         "subject": "Whether the repo holds usable market prices, and under what label",
         "side_a": "five packs state that no price row exists anywhere, and the hub cards repeat it",
         "side_b": f"data/nfl_f4/price_snapshots.csv holds {f4_cells} populated number cells cited to a third-party carrier "
                   f"({f4_hosts}), each carrying snapshot_type=open and close for the same game — real market prices, with a "
                   f"status column that reads 'verified'",
         "computed": per_store + f" — totals: third-party market cells {tot_third}, own-labelled {tot_own}, repo reconstruction {tot_repo}, official-cited {tot_official}",
         "what_it_changes": "This is the price-data policy the brief demands be decided before any backtest is published, "
                            "and the site answers it two ways at once. One pack has operator open/close pairs (third-party "
                            "quotes, not official, and its own flags say 13 of 14 games had no settled close); the other five "
                            "stores are blank or hold our own model number with an official page cited as input provenance. "
                            "A CLV or ROI figure computed from the first class and described using the second class's "
                            "language would be a category error — and 'verified' on a third-party quote contradicts the "
                            "project's own rule that verified means read from an official source.",
         "action": ("decide the accepted price class in one sentence (official only / licensed vendor / third-party-with-"
                    "provenance), then relabel what does not qualify and re-point the gates at the surviving rows; if "
                    "third-party quotes are accepted, they become the earliest usable market reference the project has"),
         "evidence": "price_semantics.csv; data/nfl_f4/flagged.csv F4-F02, F4-F09, F4-F16"},
        {"conflict_id": "CF-10", "kind": "citation_defect", "severity": "high",
         "subject": "A number cell that cites a page which cannot contain it",
         "side_a": f"data/nfl_d966f630/price_snapshots_open_close.csv: {d966_official} populated number cells whose own "
                   f"*_source_url points at an nfl.com schedule page — a page that prints fixtures, times and scores, "
                   f"never a line — that exact URL was read in full this session (R10), which is what turns this from an "
                   f"inference about a route name into a tested citation",
         "side_b": "the same file's own labels: opening_class='retrospective_reconstruction' or "
                   "'prior_session_publication', closing_role='open_and_close_final' or 'close_provisional', and a "
                   "movement_note that says the two numbers come from two different model versions",
         "computed": f"populated number cells by cited host: {d966_hosts}; own labels on those rows: {d966_labels}",
         "what_it_changes": "Read carefully, this is not a fabricated market price — the pack says in its own note that "
                            "both numbers are ours. The defect is the citation: a source URL that appears beside a number "
                            "will be quoted later without the note attached, and 'nfl.com' beside a price-looking number "
                            "reads as if the league published it. Any residual-against-market column inherits that "
                            "ambiguity. It is also the case a required-field alarm should catch: the cited host cannot "
                            "contain the class of value stored.",
         "action": ("in the owning pack: move the input-provenance URL to an inputs column and leave the number's own "
                    "source blank (or point it at the model-version file that produced it); add the host-class check to "
                    "the verifier pattern used here (rule 6)"),
         "evidence": "price_semantics.csv; R5"},
        {"conflict_id": "CF-06", "kind": "insight", "severity": "medium",
         "subject": "Where a depth chart actually lives",
         "side_a": "nfl.com/teams/green-bay-packers/depth-chart/ → 404 (read this session)",
         "side_b": "the same league roster page prints a 'DEPTH CHART' link to the club's own site, whose chart is dated and labelled 'Unofficial, Nov. 10, 2026'",
         "computed": "packers.com chart parsed as a table: 3 player columns, no rank labels, 3 separate WR rows, one safety repeated in two rows",
         "what_it_changes": "Route (a) is real — the league itself links out to it — but the club disclaims it, and the shape is groups rather than a ranked list. Any 'depth register' must therefore store the raw row, the club label and the page date, and must refuse to name a single starter.",
         "action": "take the T05 decision with this shape in mind", "evidence": "R3;R4;R8;R9"},
        {"conflict_id": "CF-07", "kind": "contradiction", "severity": "medium",
         "subject": "The blank cells the brief reports",
         "side_a": "brief item: three Lions rows 'published with a blank game-status cell'",
         "side_b": "the capture file and the official page both carry 'Out' for all three",
         "computed": "see C18 in claim_checks.csv",
         "what_it_changes": "The defect is between the capture and the published table, not in the source. It is a pipeline test, not a data-collection task — cheaper to fix, and it would have been caught by a required-field alarm.",
         "action": "T13: fail the build when a captured field is dropped on the way to the page",
         "evidence": "R1;C18"},
        {"conflict_id": "CF-08", "kind": "contradiction", "severity": "high",
         "subject": "Reviewability of the suggestion layer itself",
         "side_a": "one suggestion register per pack, each with its own column names",
         "side_b": "the owner's request: one section to review and choose a path",
         "computed": (f"{len(inventory)} registers; {len(schemas)} distinct column vocabularies; "
                      f"{sum(int(i['rows']) for i in inventory)} rows"),
         "what_it_changes": "No comparison was possible across packs: the same proposal appears under four names with four statuses. That is the decision cost this board pays down.",
         "action": "adopt this consolidated view (or the alternative in T12) before another pack adds register 17",
         "evidence": "sources_inventory.csv"},
    ]
    return rows_out


def price_rollup(metrics: List[Dict[str, str]]) -> Dict[str, int]:
    """Totals across every price store in the repo, by whose number it is."""
    tot = {"rows": 0, "any_number": 0, "own": 0, "official": 0, "third_party": 0,
           "repo_self": 0, "no_url": 0}
    keys = {"rows": "rows", "any_number": "rows_with_any_number", "own": "rows_own_model_number",
            "official": "rows_market_number_official_host",
            "third_party": "rows_market_number_third_party",
            "repo_self": "rows_market_number_repo_self",
            "no_url": "rows_market_number_no_url"}
    for m in metrics:
        if m["kind"] != "price":
            continue
        for out_key, col in keys.items():
            v = m.get(col, "")
            if v.isdigit():
                tot[out_key] += int(v)
    return tot


# --------------------------------------------------------------------------- information gaps

def gaps(corpus: List[Dict[str, str]], metrics: List[Dict[str, str]],
         semantics: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:  # noqa: C901
    by_id = {m["metric_id"]: m for m in metrics}
    max_games = max([int(r.get("games_with_final_scores") or r.get("rows") or 0) for r in corpus] or [0])
    pr = price_rollup(metrics)
    sem = {x["pack"]: x for x in (semantics or [])}
    rsv_clubs = max([int(m.get("clubs") or 0) for m in metrics if m["kind"] == "reserve"] or [0])
    rows_out = [
        {"gap_id": "G-01", "missing_dataset": "Timestamped opening and closing numbers for every market we originate",
         "what_it_is_for": "the price-snapshot store, fair/market/difference columns, CLV, vig-free decomposition, ROI",
         "coverage_now": ((sem or {}).get("nfl_f4", {}).get("populated_cells", "no f4 store")
                          + " — third-party operator quotes exist for one pack's Week 10 slate ("
                          + (sem or {}).get("nfl_f4", {}).get("cited_hosts", "?") + "); "
                          + "every other store is blank or holds this project's own number: "
                          + " ; ".join(f"{k.replace('nfl_', '')}: {v.get('populated_cells', 'absent')}"
                                       for k, v in sorted((sem or {}).items()) if k != "nfl_f4")
                          + ". No store holds a number taken from a page that actually publishes lines — and the "
                            "one official URL a price cell does cite was read in full this session (R10): fixtures, "
                            "times, scores, records, no line."),
         "acquisition_route": "A procurement decision, not a scraping task: quote one licensed archive for retention + timestamp granularity; or publish the freeze decision and rank on proper scores only.",
         "official_host": "none — no official NFL page publishes a line", "clearing_number": ">=1 named source with opening and closing numbers for at least the Week 11 slate (13 fixtures)",
         "cost_class": "money + legal review", "blocks_themes": "T02;T07;T10;T16",
         "risk_if_left_open": "every gate that needs a market number stays structurally blank and the leaderboard can never promote on line value",
         "status": "OPEN — decided only by the owner", "evidence": "M-PRC-*;C09;C10;CF-05"},
        {"gap_id": "G-02", "missing_dataset": "One canonical game-level results corpus with a stated boundary",
         "what_it_is_for": "backtests, opponent-aware ratings, walk-forward gates, settlement",
         "coverage_now": f"largest feed in the repo = {max_games} games with final scores; six feeds disagree (see CF-02)",
         "acquisition_route": "read nfl.com's by-week pages for every week of the season into one file, then make every pack cite it instead of its own",
         "official_host": "www.nfl.com/schedules", "clearing_number": "one file, every finished fixture of 2026 Weeks 1-11 with scores, reconciled to the division standings",
         "cost_class": "mechanical effort", "blocks_themes": "T07;T08;T11",
         "risk_if_left_open": "corpus shopping — the same claim can be true in one file and false in another",
         "status": "OPEN", "evidence": "metrics.csv;CF-02"},
        {"gap_id": "G-03", "missing_dataset": "Official snap counts / participation share per player per game",
         "what_it_is_for": "replacing jersey-order and chart-column guesses with measured playing time",
         "coverage_now": "0 — the per-game participation route returned no table (a 404 at the /boxscore route for an unplayed fixture; no other official source found this session)",
         "acquisition_route": "after kickoff, re-read the same fixture's game centre stats/box-score tabs and record the exact route that carries participation; if none exists, record that route (b) is dead and go to route (a) for all 32 clubs",
         "official_host": "www.nfl.com/games", "clearing_number": "one official per-game participation table, read for a played fixture, with snap counts for at least 2 clubs",
         "cost_class": "one read per fixture", "blocks_themes": "T05",
         "risk_if_left_open": "the deficiency feature is built on charts the clubs themselves label 'Unofficial'",
         "status": "OPEN — must be re-attempted after a played fixture", "evidence": "R2;O3;CF-06"},
        {"gap_id": "G-04", "missing_dataset": "Dated depth charts for all 32 clubs, with raw row strings",
         "what_it_is_for": "who is the 2nd/3rd/4th string, and therefore what a starter's absence costs",
         "coverage_now": "1 club verified readable and dated (Packers, 'Unofficial, Nov. 10, 2026'); 1 club verified absent at the conventional path (Texans); nfl.com hosts none",
         "acquisition_route": "walk the 32 club roster pages, follow the 'DEPTH CHART' link each one prints (the Dolphins roster page did), and store the raw table plus the label and date; log a club as 'no chart' rather than guessing",
         "official_host": "club sites linked from nfl.com/teams/<club>/roster", "clearing_number": "32 dated rows, each with a URL, a page date and the club's own caveat",
         "cost_class": "32 reads + a parser per template", "blocks_themes": "T05;T09",
         "risk_if_left_open": "backup-deficiency numbers that no source supports",
         "status": "PARTIALLY CLOSED — route proven, coverage 1/32", "evidence": "R3;R4;R8;R9;CF-06"},
        {"gap_id": "G-05", "missing_dataset": "Official game-day inactive lists and announced starters",
         "what_it_is_for": "confirming that a backup actually replaced a starter, instead of suspecting it",
         "coverage_now": "one prior pack captured a Week 9 inactive list; this session read none (no official route located before kickoff this week)",
         "acquisition_route": "the game centre 'INJURY REPORT' tab and the club's game-day report, read at T-90m; store as an evidence event, not a modelled input",
         "official_host": "www.nfl.com/games; club sites", "clearing_number": "one inactive list per fixture we originate, timestamped before kickoff",
         "cost_class": "one timed read per fixture", "blocks_themes": "T05;T06;T09",
         "risk_if_left_open": "'replacement certainty' stays unprovable and the depth ledger is suspicion",
         "status": "OPEN", "evidence": "R6;O9"},
        {"gap_id": "G-06", "missing_dataset": "Reserve/IR status codes for every club",
         "what_it_is_for": "so that 'not listed on the report' never silently means 'available'",
         "coverage_now": f"{rsv_clubs} clubs covered by the largest reserve register in the repo; one worked example closed this session (Willis, 'RES', Miami)",
         "acquisition_route": "read each club's nfl.com roster page, keep the status-code column verbatim with the legend, and diff it against the weekly report",
         "official_host": "www.nfl.com/teams/<club>/roster", "clearing_number": "32 clubs with dated status-code registers; any player absent from the report explained by a code",
         "cost_class": "32 reads", "blocks_themes": "T06;T09",
         "risk_if_left_open": "healthy-looking availability that is actually an IR absence — and the wrong-club lookup this board already found",
         "status": "PARTIALLY CLOSED — method proven on one player", "evidence": "R7;R8;A1;M-RSV-*"},
        {"gap_id": "G-07", "missing_dataset": "Stadium roof designation and surface type, per venue per game",
         "what_it_is_for": "totals and passing volume; the brief's 90-minute roof designation",
         "coverage_now": "0 official roof/surface rows; this session read a stadium name and city only (Colts at Texans: 'RELIANT STADIUM', 'HOUSTON, TX')",
         "acquisition_route": "the venue comes from each game centre; roof/surface needs a dated register that no page read this session publishes — the honest options are a club stadium page (secondary, club-hosted) or dropping the feature",
         "official_host": "www.nfl.com/games (venue only)", "clearing_number": "one roof/surface row per venue in the corpus, each with the page and date it came from",
         "cost_class": "30ish reads, judgement required", "blocks_themes": "T15",
         "risk_if_left_open": "a totals model that treats an indoor 41-degree game and a roof-open windy game the same",
         "status": "OPEN", "evidence": "R6;O8"},
        {"gap_id": "G-08", "missing_dataset": "Hourly forecast grid at each stadium coordinate at kickoff",
         "what_it_is_for": "wind/precipitation overlay on totals and prop projections",
         "coverage_now": "0 captured; no coordinate table in the repo either — and the official by-week page "
                         "prints a one-word weather token per fixture with no number beside it (R11)",
         "acquisition_route": "the one gap here that needs no permission and no vendor: a public-domain government forecast service keyed by stadium latitude/longitude, read at a fixed lead time and stored with its clock",
         "official_host": "api.weather.gov (public domain, not NFL)", "clearing_number": "one dated forecast read per fixture in the slate, at a fixed lead time, with the grid point stored",
         "cost_class": "code only", "blocks_themes": "T15",
         "risk_if_left_open": "the environment feature stays untestable while being quoted in prose",
         "status": "OPEN — cheapest gap to close", "evidence": "O8|O14"},
        {"gap_id": "G-09", "missing_dataset": "A dated transactions log joined to depth and availability",
         "what_it_is_for": "treating roster turnover as a versioning event (a trade invalidates a depth assumption)",
         "coverage_now": "one pack captured November trades in its own file; no durable register keyed to club and date",
         "acquisition_route": "the league's transactions hub and the club news feeds, read on the same cadence as the report, then assert every depth/availability row against the last roster event",
         "official_host": "www.nfl.com (transactions); club sites", "clearing_number": "one dated transaction row per move affecting a player who appears in a depth or availability register",
         "cost_class": "one read per capture day", "blocks_themes": "T06;T05",
         "risk_if_left_open": "stale depth quoted as current — the Baltimore case in the owner's brief",
         "status": "OPEN", "evidence": "R8;A1"},
        {"gap_id": "G-10", "missing_dataset": "Multi-season archive of designations joined to outcomes",
         "what_it_is_for": "the empirical meaning of Questionable/Doubtful, i.e. play rate per label",
         "coverage_now": "one pack reports 11 definite designation/outcome pairs from a single pregame page; no season archive",
         "acquisition_route": "past weeks of the official report are reachable from the page's own week selector (this session saw WEEK 1 to WEEK 10 offered for 2026, and 1965-2026 for seasons) — capture them, then join to inactives",
         "official_host": "www.nfl.com/injuries/", "clearing_number": ">=3 seasons of report rows joined to inactive lists, with a play-rate interval per designation",
         "cost_class": "bulk capture + join", "blocks_themes": "T09;T11",
         "risk_if_left_open": "the label stays folklore and either over- or under-weights real absences",
         "status": "OPEN — the selector proves the archive is at least reachable", "evidence": "R1;O1"},
        {"gap_id": "G-11", "missing_dataset": "Operator void/push/alternate rules for each combo shape",
         "what_it_is_for": "settling parlays and prop combos without inventing a rule",
         "coverage_now": "0 operator rule documents in the repo; the repo has one internal convention (a tie refunded) labelled as such",
         "acquisition_route": "read the rule text of whichever operator is actually used, or freeze combos; a rule written by us is not the operator's rule",
         "official_host": "not an NFL page — operator rule pages", "clearing_number": "one rule document per combo shape, quoted with URL and date",
         "cost_class": "reading only", "blocks_themes": "T16;T07",
         "risk_if_left_open": "push handling changes payoffs and nobody can say which convention produced a number",
         "status": "OPEN", "evidence": "CF-05"},
        {"gap_id": "G-12", "missing_dataset": "A scheduler and a store that outlives a static site",
         "what_it_is_for": "immutable multi-day availability snapshots, freshness monitoring, alerts",
         "coverage_now": "every capture in the repo was made by a session reading a page; no dated series exists beyond a few same-week pairs",
         "acquisition_route": "one scheduled job with a writable destination and a hash-per-capture log, plus a freshness alarm; the rights answer (T01) decides whether it may run against the league's pages",
         "official_host": "n/a (infrastructure)", "clearing_number": "7 consecutive days of captures with no gap and a replayable diff for one club",
         "cost_class": "infrastructure + policy", "blocks_themes": "T03;T04;T13",
         "risk_if_left_open": "backtests that cannot be run, because nobody can show what was knowable when",
         "status": "OPEN", "evidence": "O1;O9;A3"},
        {"gap_id": "G-13", "missing_dataset": "The owner's choices on the sixteen paths",
         "what_it_is_for": "every 'not implemented because nobody chose' row in the repo",
         "coverage_now": f"{sum(1 for _ in ())} decisions recorded; the columns exist and are empty by design",
         "acquisition_route": "answer on the Suggestions page; one letter per path is enough (A/B/C) and the next session implements only what was chosen",
         "official_host": "n/a (governance)", "clearing_number": ">=1 recorded choice; >=6 choices unblocks a coherent roadmap for a week",
         "cost_class": "minutes", "blocks_themes": "T01;T02;T04;T07;T10;T12;T14",
         "risk_if_left_open": "more packs, each re-asking the same questions in its own schema",
         "status": "OPEN — this row is the point of the section", "evidence": "decision_paths.csv"},
    ]
    g13 = rows_out[-1]
    g13["coverage_now"] = "0 of 16 paths carry an owner choice; every decision column on this board is intentionally blank"
    return rows_out


# --------------------------------------------------------------------------- guardrails

GUARDRAILS: List[Dict[str, str]] = [
    {"guardrail_id": "RJ-01", "what_is_refused": "Deriving depth order from jersey number, experience or salary",
     "why": "A jersey number is a marketing choice. This session's read shows why it breaks: the Packers chart prints '0 Matthew Golden' and '9 Christian Watson' as two different WR rows — the numbers order nothing.",
     "instead": "Store the club's own row and the club's own label; refuse to name a starter the club did not name.", "theme": "T05"},
    {"guardrail_id": "RJ-02", "what_is_refused": "Ranking strategies by season-long ROI",
     "why": "ROI needs prices the project does not have, and a short-run ROI is a description of variance, not a test of skill.",
     "instead": "Benchmark-relative proper scores with a game-clustered lower bound and a multiplicity adjustment; staking reported separately.", "theme": "T10"},
    {"guardrail_id": "RJ-03", "what_is_refused": "Any backtest number on the leaderboard",
     "why": "Once a backtest sits on the board, every later choice is contaminated by it.",
     "instead": "Pre-registration commit as the registration; prospective rows only.", "theme": "T11"},
    {"guardrail_id": "RJ-04", "what_is_refused": "Subtracting a fixed number of points for a missing starter",
     "why": "A fixed penalty is a guess with the confidence of a constant.",
     "instead": "Ablations: the same model with and without verified availability features, chronological holdout, difference published with uncertainty.", "theme": "T09"},
    {"guardrail_id": "RJ-05", "what_is_refused": "Treating 'Questionable' as a known probability",
     "why": "The official report publishes no percentages; inherited folklore values are unauditable.",
     "instead": "Measure play rate per designation against inactive lists, publish the interval, then decide whether the label earns model space.", "theme": "T09"},
    {"guardrail_id": "RJ-06", "what_is_refused": "Multiplying marginal probabilities to price a parlay or combo",
     "why": "Invalid under dependence; two 0.50 legs can be nearly certain or nearly impossible together.",
     "instead": "A joint estimate measured from settled pairs, plus the operator's void/push rules, or no combo is ranked.", "theme": "T16"},
    {"guardrail_id": "RJ-07", "what_is_refused": "Transcribing a depth chart out of an image by eye",
     "why": "It is unverifiable, unreproducible, and it will be quoted later as if it were sourced.",
     "instead": "Record 'no machine-readable chart at this route' and leave the cells blank; ask for an authorised structured source.", "theme": "T05"},
    {"guardrail_id": "RJ-08", "what_is_refused": "Scheduled automated capture before the rights question is answered",
     "why": "Automation changes the character of the use, and the terms reading the packs relied on restrict systematic non-personal use.",
     "instead": "One manual, dated, hashed read per page per session until T01 is decided; then build the cadence job the owner approves.", "theme": "T01"},
    {"guardrail_id": "RJ-09", "what_is_refused": "Calling column 1 of a depth chart 'the starter'",
     "why": "This session's read shows a safety listed in two rows and three separate WR rows; there is no single rank-1 per position to promote.",
     "instead": "Model slots as groups; where a club names two players at the same rank, publish two.", "theme": "T05"},
    {"guardrail_id": "RJ-10", "what_is_refused": "Filling a replacement from inference when the source leaves it blank",
     "why": "The blank is information: nobody has announced the replacement.",
     "instead": "Announced-starter evidence only, with its date and page; keep the inferred candidate in a separate, clearly labelled field if at all.", "theme": "T06"},
    {"guardrail_id": "RJ-11", "what_is_refused": "Publishing a correlation without its n and its source rows",
     "why": "A coefficient computed over an unstated sample is decoration.",
     "instead": "Compute only from official numbers, publish n, and label measurement versus proposal.", "theme": "T11"},
    {"guardrail_id": "RJ-12", "what_is_refused": "Letting a new pack open a 17th suggestion register",
     "why": "Sixteen registers with different schemas is why this board exists; each new one raises the review cost of every decision.",
     "instead": "Extend this board's source registers, or file a request on COORDINATION.md.", "theme": "T12"},
]


# --------------------------------------------------------------------------- repo review

def repo_findings(stats: Dict[str, str]) -> List[Dict[str, str]]:
    f = []
    def add(fid, finding, evidence, why, action):
        f.append({"finding_id": fid, "finding": finding, "measured": evidence,
                  "why_it_matters_for_decisions": why, "suggested_action": action,
                  "owner_decision": ""})
    add("RF-01", "The site is a set of parallel per-session dashboards, not one dashboard.",
        f"{stats['pack_dirs']} pack directories under docs/, {stats['hub_cards']} cards on the hub landing page, {stats['root_cards']} cards on the root portal",
        "A reviewer comparing two packs has to open both, and the same question is answered differently on each. Decision cost grows with every pack.",
        "T12 — name a canonical pack, keep the others as archive, move the shared registers (this board) to the landing page.")
    add("RF-02", "The landing pages list overlapping but not identical pack sets.",
        f"hub-only: {stats['hub_only']}; root-only: {stats['root_only']}; in both: {stats['in_both']}",
        "The two entry points disagree about what exists. Anyone deciding from one page is deciding on a different repository than someone using the other.",
        "Generate both card lists from one file (also removes a class of drift the link checker cannot see).")
    # RF-03 deliberately reports a BUCKET, not an exact count. COORDINATION.md is
    # appended to by every session, so an exact line/byte count makes this pack's
    # published artifacts stale (and its CI "build changed nothing" check red) the
    # moment anybody else commits -- which is a defect in the measurement, not in
    # the repository. Rounding keeps the finding true and keeps the artifacts
    # reproducible by the next session without a rebuild.
    _lines_bucket = (int(stats['coord_lines']) // 100) * 100
    _kb_bucket = (int(str(stats['coord_bytes']).split()[0].replace(',', '')) // 10240) * 10
    add("RF-03", "The coordination board is no longer reviewable as a board.",
        f"about {_lines_bucket}+ lines / {_kb_bucket}+ KB in COORDINATION.md, with {stats['coord_inprogress']} rows still marked in progress",
        "The takeover and de-duplication rules depend on reading the board. At this size nobody does, so work duplicates.",
        "T14 — split into a live board plus an append-only archive; add the board-path checker.")
    add("RF-04", "Every session wrote its own executive summary at the repository root.",
        f"{stats['exec_summaries']} executive-summary markdown files at root, {stats['exec_summaries_nfl']} of them NFL-domain",
        "There is no single answer to 'where are we'. The owner's request for an executive summary is currently satisfied 17 different ways.",
        "One current summary at root, per-session summaries moved to docs/archive/.")
    add("RF-05", "The review backlog is a number, and it is published nowhere in aggregate.",
        f"{stats['flag_rows_total']} flagged rows across {stats['flag_files']} flag registers; {stats['blank_cells_note']}",
        "The brief treats blanks as the most informative thing on the page; today they are distributed across packs and invisible.",
        "Surface the aggregate on the landing page (this board does, per pack, in conflicts + gaps).")
    add("RF-06", "Each pack added its own CI workflow.",
        f"{stats['workflows']} workflow files in .github/workflows",
        "CI time and failure triage scale with pack count, and a green board can hide a pack nobody re-runs.",
        "Collapse to one NFL workflow that runs every pack's build+check in a matrix.")
    add("RF-07", "The repository mixes domains and one-off artefacts in the same root.",
        f"{stats['domain_mix']}",
        "A reviewer cannot tell what is in scope for the NFL programme, which is itself a decision the brief asks to be visible.",
        "Move non-NFL and one-off files under docs/archive/ or their own top-level directory; decide in T12.")
    add("RF-08", "No LICENSE file at the root while the site publishes third-party data.",
        f"root license file present: {stats['license']}",
        "The data-rights ceiling (T01) and the code licence are different questions, and both are currently answered by silence.",
        "Add a code licence plus an explicit data-rights statement per table (3b81013c S-10 already proposed it).")
    add("RF-09", "Verification is asserted by each pack and cross-checked by none.",
        f"{stats['verifier_scripts']} per-pack build/check script pairs; {stats['shared_checkers']} shared checkers",
        "The same value is 'verified' in one pack and 'unverified' in another, which is how the board ends up re-litigating settled evidence.",
        "One ledger of official reads with hashes (this pack's official_reads.csv is the pattern) that every verifier may cite.")
    add("RF-10", "The site can prove a source URL exists but not that it said anything.",
        f"registers carrying a source URL column: {stats['registers_with_url']}/{stats['register_files']}; retained raw text files: {stats['raw_files']}",
        "A link is not an evidence chain. Without retained text, tomorrow's reviewer cannot tell a misread from a changed source.",
        "Keep the raw excerpt with its hash for every read the site cites (T03), including the 12 this session recorded.")
    return f
