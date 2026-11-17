"""Recompute what the repo actually contains, so no claim on the board is taken on trust.

Every metric here is read out of a file in this repository at build time. A claim that a pack made
in prose is checked against the metric, and the verdict is computed — never typed. If a file is
missing, the metric records ``missing`` and the row that needed it stays blank, per the pack's
evidence rule.
"""
from __future__ import annotations

import csv
import os
import re
from urllib.parse import urlparse
from collections import Counter
from typing import Dict, List, Optional, Tuple

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: metric_id -> (pack, relative file, what to count)
SPECS: List[Tuple[str, str, str, Dict[str, str]]] = [
    ("M-RES-309921", "nfl_309921cc", "data/nfl_309921cc/results_feed.csv", "results"),
    ("M-RES-48217", "nfl_48217a55", "data/nfl_48217a55/results_feed.csv", "results"),
    ("M-RES-67233", "nfl_67233566", "data/nfl_67233566/results_feed.csv", "results"),
    ("M-RES-6CEFC", "nfl_6cefc476", "data/nfl_6cefc476/results_feed.csv", "results"),
    ("M-RES-D966", "nfl_d966f630", "data/nfl_d966f630/results_feed.csv", "results"),
    ("M-CORP-8362", "nfl_8362b702", "data/nfl_8362b702/corpus_136.csv", "results"),
    ("M-RES-8362", "nfl_8362b702", "data/nfl_8362b702/results_week10.csv", "results"),
    ("M-RES-F4", "nfl_f4", "data/nfl_f4/results.csv", "results"),
    ("M-RES-MKT", "nfl_market", "data/nfl_market/results.csv", "results"),
    ("M-RES-A411", "nfl_a411fed0", "data/nfl_a411fed0/results_2026_verified.psv", "results"),
    ("M-FIN-E5E38", "nfl_e5e38f9e", "data/nfl_e5e38f9e/official_w10_finals.csv", "results"),
    ("M-INJ-48217", "nfl_48217a55", "data/nfl_48217a55/injury_report_2026_11_15.csv", "injury"),
    ("M-INJ-D966", "nfl_d966f630", "data/nfl_d966f630/injury_report_rows.csv", "injury"),
    ("M-INJ-67233", "nfl_67233566", "data/nfl_67233566/injuries_week10_read.csv", "injury"),
    ("M-INJ-8362", "nfl_8362b702", "data/nfl_8362b702/injury_series.csv", "injury"),
    ("M-INJ-309921", "nfl_309921cc", "data/nfl_309921cc/week10_injuries.csv", "injury"),
    ("M-INJ-WK", "nfl_wk", "data/nfl_wk/injuries_week10.csv", "injury"),
    ("M-PRC-309921", "nfl_309921cc", "data/nfl_309921cc/price_snapshots.csv", "price"),
    ("M-PRC-67233", "nfl_67233566", "data/nfl_67233566/price_snapshots.csv", "price"),
    ("M-PRC-6CEFC", "nfl_6cefc476", "data/nfl_6cefc476/price_snapshots.csv", "price"),
    ("M-PRC-8362", "nfl_8362b702", "data/nfl_8362b702/price_policy.csv", "price"),
    ("M-PRC-D966", "nfl_d966f630", "data/nfl_d966f630/price_snapshots_open_close.csv", "price"),
    ("M-PRC-F4", "nfl_f4", "data/nfl_f4/price_snapshots.csv", "price"),
    ("M-PRC-A411", "nfl_a411fed0", "data/nfl_a411fed0/price_snapshot_coverage.psv", "count"),
    ("M-DPT-D966", "nfl_d966f630", "data/nfl_d966f630/club_depth_rollup.csv", "depth"),
    ("M-DPT-309921", "nfl_309921cc", "data/nfl_309921cc/depth_charts.csv", "depth"),
    ("M-DPT-F4", "nfl_f4", "data/nfl_f4/depth_chart_verified.csv", "depth"),
    ("M-DPT-67233", "nfl_67233566", "data/nfl_67233566/depth_source_register.csv", "depth_register"),
    ("M-RSV-48217", "nfl_48217a55", "data/nfl_48217a55/reserve_list.csv", "reserve"),
    ("M-RSV-8362", "nfl_8362b702", "data/nfl_8362b702/reserve_register.csv", "reserve"),
    ("M-RDY-6AB24", "nfl_6ab24751", "data/nfl_6ab24751/readiness.csv", "readiness"),
    ("M-RDY-8362", "nfl_8362b702", "data/nfl_8362b702/readiness.csv", "readiness"),
    ("M-RDY-67233", "nfl_67233566", "data/nfl_67233566/requirements_trace.csv", "readiness"),
    ("M-RDY-48217", "nfl_48217a55", "data/nfl_48217a55/requirements_decision_readiness.csv", "readiness"),
    ("M-LDR-8362", "nfl_8362b702", "data/nfl_8362b702/leaderboard_strategies.csv", "leaderboard"),
    ("M-LDR-D966", "nfl_d966f630", "data/nfl_d966f630/leaderboard_combined.csv", "leaderboard"),
    ("M-FLG-48217", "nfl_48217a55", "data/nfl_48217a55/flagged.csv", "count"),
    ("M-BLK-48217", "nfl_48217a55", "data/nfl_48217a55/blank_audit.csv", "blanks"),
    ("M-FLG-8362", "nfl_8362b702", "data/nfl_8362b702/flagged.csv", "count"),
    ("M-FLG-67233", "nfl_67233566", "data/nfl_67233566/flagged.csv", "count"),
]

#: paths named on the coordination task board that a later session should find on main
BOARD_ARTIFACTS: List[Tuple[str, str]] = [
    ("nfl_48217a55", "data/nfl_48217a55/depth_chart_register.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/depth_slot_shapes.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/results_feed.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/standings_2026_w9.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/schedule_week10.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/bye_clubs_week10.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/strategies.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/validation_gates.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/injury_report_2026_11_15.csv"),
    ("nfl_48217a55", "data/nfl_48217a55/reserve_list.csv"),
    ("nfl_8362b702", "data/nfl_8362b702/corpus_136.csv"),
    ("nfl_8362b702", "data/nfl_8362b702/luck_panel_records.csv"),
    ("nfl_8362b702", "data/nfl_8362b702/control_baselines.csv"),
    ("nfl_8362b702", "data/nfl_8362b702/availability_nodes.csv"),
    ("nfl_8362b702", "data/nfl_8362b702/scraper_contracts.csv"),
]

#: the three game-status cells the owner's brief says were published blank
LIONS_ROWS = ("Kerby Joseph", "Cade Mays", "D.J. Reed")

# --------------------------------------------------------------------------- helpers


def load(rel: str) -> Optional[List[Dict[str, str]]]:
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return None
    delim = "|" if rel.endswith(".psv") else ","
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()}
                for r in csv.DictReader(fh, delimiter=delim)]


def _cols(rows: List[Dict[str, str]], *needles: str) -> List[str]:
    if not rows:
        return []
    return [c for c in rows[0] if any(n in c.lower() for n in needles)]


def _numeric_present(v: str) -> bool:
    """True when a cell holds a number, including signed American-odds style values (+105, -1.0)."""
    s = v.replace("-", "").replace("+", "").replace(".", "").strip()
    return bool(s) and s.isdigit()


# --------------------------------------------------------------------------- metric bodies


def measure(kind: str, rows: List[Dict[str, str]]) -> Dict[str, str]:
    out = {"rows": str(len(rows))}
    if not rows:
        return out
    if kind == "results":
        weeks = _cols(rows, "week")
        if weeks:
            vals = {r.get(weeks[0], "") for r in rows if r.get(weeks[0], "")}
            out["weeks"] = str(len(vals))
            out["week_range"] = f"{min(vals)}–{max(vals)}" if vals else ""
        score_cols = _cols(rows, "score", "points")
        if score_cols:
            out["games_with_final_scores"] = str(sum(
                1 for r in rows if all(_numeric_present(r.get(c, "")) for c in score_cols[:2])))
        flag = [c for c in rows[0] if "counts_in_backtest" in c]
        if flag:
            yes = sum(1 for r in rows if r.get(flag[0], "").lower().startswith("y"))
            out["rows_counted_in_backtest"] = str(yes)
            out["rows_excluded"] = str(len(rows) - yes)
        pts = [c for c in score_cols if "away" in c or "home" in c]
        if len(pts) >= 2:
            tot = 0
            for r in rows:
                for c in pts:
                    if _numeric_present(r.get(c, "")):
                        tot += int(float(r[c]))
            out["points_sum"] = str(tot)
    elif kind == "injury":
        clubs = _cols(rows, "club", "team")
        if clubs:
            out["clubs"] = str(len({r.get(clubs[0], "") for r in rows if r.get(clubs[0], "")}))
        gs = [c for c in rows[0] if "game_status" in c]
        if gs:
            out["rows_with_game_status"] = str(sum(1 for r in rows if r.get(gs[0], "")))
            out["game_status_blank"] = str(sum(1 for r in rows if not r.get(gs[0], "")))
            counts = Counter(r[gs[0]] for r in rows if r.get(gs[0], ""))
            out["status_mix"] = "; ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        clock = [c for c in rows[0] if "read" in c and ("utc" in c or "at" in c)]
        if clock:
            out["distinct_reads"] = str(len({r.get(clock[0], "") for r in rows if r.get(clock[0], "")}))
    elif kind == "price":
        # A number in a price file means nothing until we know whose number it is and what URL it
        # cites. Own-model columns (our_number, fair_*, originated_*) are this project's arithmetic;
        # market columns (market_number, price_*, opening/closing_number) are paired with the URL the
        # row gives for that field, and classified by host: league / third-party / this repository.
        cols = list(rows[0])
        own = [c for c in cols if re.search(r"(our_|fair_|model_|originated|own_)", c.lower())
               and re.search(r"(number|line|price|prob)", c.lower())]
        market = [c for c in cols if c not in own
                  and re.search(r"(opening|closing|market_number|price|line|american|decimal)", c.lower())
                  and not re.search(r"(url|status|note|class|role|published|timestamp|snapshot_id|flag|count|basis|coverage"
                                    r"|movement|delta|diff|_gap|implied|prob|^with_|_with_)", c.lower())]
        derived = [c for c in cols if c not in own + market
                   and re.search(r"(movement|delta|diff|_gap|implied|prob)", c.lower())
                   and not re.search(r"(url|status|note|class|role|flag)", c.lower())]
        urlcols = [c for c in cols if "url" in c.lower()]  # noqa: F841

        def paired_url(row: Dict[str, str], col: str) -> str:
            stem = re.match(r"(opening|closing)", col.lower())
            if stem:
                cand = f"{stem.group(1)}_source_url"
                if cand in row:
                    return row[cand]
            # deliberately not falling back to official_source_url: that column names the fixture's
            # official page, not the source of the number, and treating it as the number's source
            # would turn our own reconstruction into an "official" price.
            for pref in ("second_source_url", "market_source_url", "source_url"):
                if row.get(pref, "").startswith("http"):
                    return row[pref]
            return ""

        def host_of(u: str) -> str:
            return urlparse(u).netloc.lower() if u.startswith("http") else ""

        counts = {"own": 0, "market_official": 0, "market_third_party": 0,
                  "market_repo_self": 0, "market_no_url": 0}
        for r in rows:
            if any(_numeric_present(r.get(c, "")) for c in own):
                counts["own"] += 1
            for c in market:
                # counted per cell, not per row: the same row can hold our own reconstruction in one
                # column and a number whose cited page is an official one in another, and taking the
                # first hit only would understate exactly the case worth seeing
                if _numeric_present(r.get(c, "")):
                    h = host_of(paired_url(r, c))
                    if "nfl.com" in h and "github" not in h:
                        counts["market_official"] += 1
                    elif "github.com" in h:
                        counts["market_repo_self"] += 1
                    elif not h:
                        counts["market_no_url"] += 1
                    else:
                        counts["market_third_party"] += 1
        withnum = sum(1 for r in rows if any(_numeric_present(r.get(c, "")) for c in own + market))
        out["number_columns"] = ";".join(own + market)
        out["own_number_columns"] = ";".join(own)
        out["market_number_columns"] = ";".join(market)
        out["derived_number_columns"] = ";".join(derived)
        out["rows_derived_number_only"] = str(sum(
            1 for r in rows if any(_numeric_present(r.get(c, "")) for c in derived)
            and not any(_numeric_present(r.get(c, "")) for c in own + market)))
        out["counting_unit"] = ("market buckets count number CELLS (a row can carry our number in one column "
                              "and a sourced number in another); rows_with_any_number counts rows")
        out["rows_with_any_number"] = str(withnum)
        out["rows_fully_blank_numbers"] = str(len(rows) - withnum)
        out["rows_own_model_number"] = str(counts["own"])
        out["rows_market_number_official_host"] = str(counts["market_official"])
        out["rows_market_number_third_party"] = str(counts["market_third_party"])
        out["rows_market_number_repo_self"] = str(counts["market_repo_self"])
        out["rows_market_number_no_url"] = str(counts["market_no_url"])
        # kept for the claim checks: numbers whose *cited* source is an official page
        out["rows_number_official_host"] = str(counts["market_official"])
        out["rows_number_third_party_host"] = str(counts["market_third_party"])
        out["rows_number_repo_self"] = str(counts["market_repo_self"])

        for col, key in (("game_key", "distinct_games"), ("game_id", "distinct_games"),
                         ("market", "distinct_markets"), ("market_type", "distinct_markets")):
            if col in rows[0]:
                out[key] = str(len({r.get(col, "") for r in rows if r.get(col, "")}))
        prov = [c for c in rows[0] if "provider" in c.lower()]
        if prov:
            vals = sorted({r.get(prov[0], "") for r in rows if r.get(prov[0], "")})
            out["providers"] = " | ".join(v[:60] for v in vals[:3])
        st = [c for c in rows[0] if c.lower() == "status"]
        if st:
            out["status_mix"] = "; ".join(f"{k}={v}" for k, v in
                                          sorted(Counter(r.get(st[0], "") or "(blank)" for r in rows).items()))
    elif kind in ("depth", "reserve"):
        clubs = _cols(rows, "club", "team")
        if clubs:
            out["clubs"] = str(len({r.get(clubs[0], "") for r in rows if r.get(clubs[0], "")}))
    elif kind == "depth_register":
        vals = _cols(rows, "clubs_verified")
        if vals:
            out["clubs_verified_total"] = str(sum(int(r[vals[0]]) for r in rows
                                                  if r.get(vals[0], "").isdigit()))
    elif kind == "readiness":
        st = [c for c in rows[0] if c.lower() == "status"]
        if st:
            counts = Counter(r.get(st[0], "") or "(blank)" for r in rows)
            out["status_mix"] = "; ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        blocked = [c for c in rows[0] if "gate" in c.lower()]
        if blocked:
            out["rows_with_a_blocking_gate"] = str(sum(
                1 for r in rows if r.get(blocked[0], "") and r.get(blocked[0], "").lower()
                not in ("none", "n/a", "closed", "complete", "delivered")))
    elif kind == "blanks":
        bc = [c for c in rows[0] if c.lower() in ("blank_cells", "blank_count", "blanks")]
        if bc:
            out["blank_cells_total"] = str(sum(int(r[bc[0]]) for r in rows if r.get(bc[0], "").isdigit()))
        cells = [c for c in rows[0] if c.lower() == "cells"]
        if cells:
            out["cells_total"] = str(sum(int(r[cells[0]]) for r in rows if r.get(cells[0], "").isdigit()))
    elif kind == "leaderboard":
        out["entries"] = str(len(rows))
    return out


def compute() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for mid, pack, rel, kind in SPECS:
        rows = load(rel)
        row = {"metric_id": mid, "pack": pack, "file": rel, "kind": kind,
               "exists": "yes" if rows is not None else "no"}
        if rows is None:
            row["note"] = "file not present on this branch — nothing counted, nothing inferred"
        else:
            row.update(measure(kind, rows))
            row["note"] = ""
        out.append(row)
    for pack, rel in BOARD_ARTIFACTS:
        here = os.path.exists(os.path.join(REPO, rel))
        out.append({"metric_id": f"M-FILE-{os.path.basename(rel)}", "pack": pack, "file": rel,
                    "kind": "file_exists", "exists": "yes" if here else "no",
                    "rows": "", "note": ("path named on the coordination task board, and present"
                                         if here else "path named on the coordination task board; "
                                         "the file is not in the tree, so it holds no number and is "
                                         "reported as a contradiction rather than measured")})
    return out


def lions_cells() -> List[Dict[str, str]]:
    """What the capture file actually holds for the three rows the owner says were blank."""
    rows = load("data/nfl_48217a55/injury_report_2026_11_15.csv") or []
    out = []
    for name in LIONS_ROWS:
        hits = [r for r in rows if r.get("player", "").strip() == name]
        if hits:
            h = hits[0]
            out.append({"player": name, "found_in_capture": "yes", "club": h.get("club", ""),
                        "practice_status_in_file": h.get("practice_status", ""),
                        "game_status_in_file": h.get("game_status", ""),
                        "read_at_utc_in_file": h.get("read_at_utc", "")})
        else:
            out.append({"player": name, "found_in_capture": "no", "club": "",
                        "practice_status_in_file": "", "game_status_in_file": "",
                        "read_at_utc_in_file": ""})
    return out


def corpus_table() -> List[Dict[str, str]]:
    """Every pack's own game count, side by side — the number the leaderboard needs fixed."""
    table = []
    for mid, pack, rel, kind in SPECS:
        if kind != "results":
            continue
        rows = load(rel)
        entry = {"metric_id": mid, "pack": pack, "file": rel, "rows": "", "weeks": "",
                 "games_with_final_scores": "", "rows_counted_in_backtest": "", "status": "missing"}
        if rows is not None:
            m = measure("results", rows)
            entry.update({k: m.get(k, "") for k in entry if k in m})
            entry["status"] = "present"
        table.append(entry)
    table.sort(key=lambda e: e["file"])
    return table


PRICE_FILES = [
    ("nfl_309921cc", "data/nfl_309921cc/price_snapshots.csv"),
    ("nfl_67233566", "data/nfl_67233566/price_snapshots.csv"),
    ("nfl_6cefc476", "data/nfl_6cefc476/price_snapshots.csv"),
    ("nfl_8362b702", "data/nfl_8362b702/price_policy.csv"),
    ("nfl_d966f630", "data/nfl_d966f630/price_snapshots_open_close.csv"),
    ("nfl_f4", "data/nfl_f4/price_snapshots.csv"),
]


def price_semantics() -> List[Dict[str, str]]:
    """What each pack's price file says a "number" is, in its own words.

    Counted per populated cell, from each file's own columns, with one rule that matters: if the column
    name declares ownership (``our_number``, ``fair_line``, ``model_*``) the cell is ours whatever URL sits
    beside it; otherwise the host of the URL paired with that column decides the class — official page,
    third-party carrier, or a file inside this repository. A number in a column called ``closing_number``
    whose paired URL is an nfl.com schedule page is reported as an official-cited cell, because that is
    the pairing a later reader would quote (see CF-10 in the audit).
    """
    out: List[Dict[str, str]] = []
    for pack, rel in PRICE_FILES:
        rows = load(rel)
        entry = {"pack": pack, "file": rel, "status": "missing", "number_columns": "",
                 "populated_cells": "", "cells_own_labelled": "", "cells_official_cited": "",
                 "cells_third_party_market": "", "cells_repo_reconstruction": "", "cells_no_url": "",
                 "cited_hosts": "", "own_labels": "", "games_covered": "", "note": ""}
        if not rows:
            entry["note"] = "file absent or empty on this branch — nothing counted, nothing inferred"
            out.append(entry)
            continue

        def paired(row: Dict[str, str], col: str) -> str:
            for cand in (f"{col}_source_url", f"{col.split('_')[0]}_source_url",
                         "source_url", "second_source_url"):
                if row.get(cand, "").startswith("http"):
                    return row[cand]
            return ""

        cols = [c for c in rows[0]
                if re.search(r"(number|price|line|american|decimal)", c.lower())
                and not re.search(r"(url|status|note|class|role|flag|count|basis|coverage|snapshot_id"
                                  r"|movement|delta|diff|implied|prob|second)", c.lower())]
        own_cols = [c for c in cols if re.search(r"(our_|fair_|model_|originated|own_)", c.lower())]
        hosts: Counter = Counter()
        pop, labels = [], []
        cls = {"own": 0, "official": 0, "third": 0, "repo": 0, "none": 0}
        for c in cols:
            n = 0
            for r in rows:
                if not _numeric_present(r.get(c, "")):
                    continue
                n += 1
                paired_url = "" if c in own_cols else paired(r, c)
                host = urlparse(paired_url).netloc.lower() if paired_url else ""
                hosts[host or ("(ours, labelled)" if c in own_cols else "(none)")] += 1
                if c in own_cols:
                    cls["own"] += 1
                elif not host:
                    cls["none"] += 1
                elif "github.com" in host:
                    cls["repo"] += 1
                elif "nfl.com" in host:
                    cls["official"] += 1
                else:
                    cls["third"] += 1
            pop.append(f"{c}={n}")
        for c in rows[0]:
            if re.search(r"(role|class)$", c.lower()):
                mix = Counter(r.get(c, "") for r in rows if r.get(c, ""))
                labels.append(f"{c}: " + ", ".join(f"{k}×{v}" for k, v in mix.most_common(3)))
        games: Counter = Counter()
        for c in rows[0]:
            if c.lower() in ("game_key", "game_id"):
                games.update(r.get(c, "") for r in rows if r.get(c, ""))
        entry.update({
            "status": "present",
            "number_columns": ";".join(cols) or "no number column in this file",
            "populated_cells": "; ".join(pop) if pop else "no populated number cell",
            "cells_own_labelled": str(cls["own"]),
            "cells_official_cited": str(cls["official"]),
            "cells_third_party_market": str(cls["third"]),
            "cells_repo_reconstruction": str(cls["repo"]),
            "cells_no_url": str(cls["none"]),
            "cited_hosts": "; ".join(f"{k}={v}" for k, v in hosts.most_common(4)) or "no url cited",
            "own_labels": " | ".join(labels) or "none given",
            "games_covered": str(len(games)) if games else "",
            "note": ("own-labelled columns are the pack's own word for its model number; 'official-cited' means a "
                     "number sits in a market-sounding column with an official page URL beside it, which is the "
                     "pairing CF-10 questions, not proof that the page published the number"),
        })
        out.append(entry)
    return out
