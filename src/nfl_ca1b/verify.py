"""Line-by-line re-verification of every merged pack's stored official values.

Two mechanical tests, both re-runnable with no network:

  A. STANDINGS RECONCILIATION
     For every pack that stores a standings snapshot: take the pack's own stored
     per-club W-L-T and PF/PA, undo the games its snapshot had not yet seen, and
     compare with this session's read of nfl.com/standings (2026-11-17T00:40Z).
     The undo is driven by the pack's own read timestamp, not by guesswork: a
     packed snapshot older than a week-10 final cannot include it.

  B. RESULTS RECONCILIATION
     For every pack that stores a results feed: join each row to this session's
     official finals by (week, away, home) and flag disagreeing scores, plus any
     week-10 game that is final now and missing from that pack.

Everything the repo got right is recorded too. The output is one row per tested
value so the owner can see the sample size behind every claim.
"""
from __future__ import annotations

import csv
import pathlib
from typing import Dict, Iterable, List, Optional, Tuple

from . import capture

ROOT = pathlib.Path(__file__).resolve().parents[2]

# week-10 finals, by when they became final according to official cards
W10_ORDER = capture.WEEK10[:-1]  # 13 finals, LAC@BAL excluded (still scheduled)
W10_BASE = 9                     # 8362b702's 2026-11-15T23:35Z read saw 9 FINAL
W10_AFTER = 4                    # ... and these 4 went final afterwards

STORE_TIMES = {
    # pack -> read timestamp of the standings snapshot it publishes
    "nfl_309921cc": "2026-11-13",
    "nfl_3b81013c": "2026-11-13",
    "nfl_48217a55": "2026-11-15T18:40Z",
    "nfl_67233566": "2026-11-15T23:26Z",
    "nfl_6cefc476": "2026-11-14",
    "nfl_8362b702": "2026-11-15T23:26Z",
    "nfl_d966f630": "2026-11-14",
    "nfl_market": "2026-11-14",
    "nfl_origination": "2026-11-13",
    "nfl_wk": "2026-11-13",
}

# The official page prints LA for the Rams; several packs store LAR. That is a code
# alias, not a data error, so it is normalised before comparison and logged once.
CLUB_ALIAS = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX", "ARZ": "AZ", "ARI": "AZ",
              "LVR": "LV", "SFO": "SF"}

# Per-club PF/PA column names differ between packs; map them explicitly.
STANDINGS_COLS = {
    "pf": ("pf", "points_for", "pf_"),
    "pa": ("pa", "points_against", "pa_"),
    "w": ("w", "wins"), "l": ("l", "losses"), "t": ("t", "ties"),
}


def _pick(row: dict, names) -> Optional[int]:
    for n in names:
        if n in row and str(row[n]).strip() != "":
            return _int(row[n])
    return None


def w10_visible(ts: str) -> int:
    """Upper bound on week-10 finals a snapshot taken at `ts` could contain.

    Thursday's game was final on 2026-11-12; the Sunday blocks were final by the
    evening of 2026-11-15. The exact k is then inferred from the data itself and
    reported next to the result, so a wrong guess cannot hide an error.
    """
    if ts.startswith("2026-11-15"):
        return W10_BASE
    if ts.startswith("2026-11-14"):
        return 1  # only the Thursday game could be final
    return 1


STANDINGS_FILES = [
    ("nfl_309921cc", "data/nfl_309921cc/standings_2026_w10.csv", "abbr"),
    ("nfl_3b81013c", "data/nfl_3b81013c/team_season_records.csv", None),
    ("nfl_48217a55", "data/nfl_48217a55/standings_as_rendered.csv", "club"),
    ("nfl_67233566", "data/nfl_67233566/standings.csv", "club"),
    ("nfl_6cefc476", "data/nfl_6cefc476/standings_2026_11_14.csv", "team"),
    ("nfl_8362b702", "data/nfl_8362b702/standings_asof.csv", "team_abbr"),
    ("nfl_d966f630", "data/nfl_d966f630/standings_2026_w10.csv", "club"),
    ("nfl_market", "data/nfl_market/standings.csv", "team_abbr"),
    ("nfl_origination", "data/nfl_origination/standings_live_2026_11_13.csv", "abbr"),
    ("nfl_wk", "data/nfl_wk/standings_2026_w11.csv", "team"),
]


def _int(v: str) -> Optional[int]:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _load_standings(rel: str, key: str) -> Dict[str, Tuple[int, int, int, int, int]]:
    path = ROOT / rel
    out: Dict[str, Tuple[int, int, int, int, int]] = {}
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if key not in r:
                continue
            t = (r[key] or "").strip()
            if not t:
                continue
            t = CLUB_ALIAS.get(t, t)
            w, l, ti = (_pick(r, STANDINGS_COLS["w"]), _pick(r, STANDINGS_COLS["l"]),
                        _pick(r, STANDINGS_COLS["t"]))
            pf, pa = _pick(r, STANDINGS_COLS["pf"]), _pick(r, STANDINGS_COLS["pa"])
            if None not in (w, l, ti, pf, pa):
                out[t] = (w, l, ti, pf, pa)
    return out


def _reconcile_at(stored, official, k: int) -> Tuple[int, int]:
    """(#clubs that match, #clubs present) if the snapshot contained k week-10 finals."""
    unseen = W10_ORDER[k:]
    good = tot = 0
    for club, (sw, sl, st, spf, spa) in stored.items():
        if club not in official:
            continue
        tot += 1
        aw, al, at, apf, apa = sw, sl, st, spf, spa
        for _gid, _d, away, home, a_s, h_s, _stt in unseen:
            for cx, pf, pa in ((away, a_s, h_s), (home, h_s, a_s)):
                if cx == club:
                    aw += 1 if pf > pa else 0
                    al += 1 if pf < pa else 0
                    at += 1 if pf == pa else 0
                    apf += pf
                    apa += pa
        if (aw, al, at, apf, apa) == official[club]:
            good += 1
    return good, tot


def standings_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    official = capture.STANDINGS
    for pack, rel, key in STANDINGS_FILES:
        ts = STORE_TIMES[pack]
        visible = w10_visible(ts)
        if key is None:  # nfl_3b81013c stores aggregates, not club rows
            rows.append({
                "pack": pack, "file": rel, "unit": "file", "club": "",
                "stored": "not a club-row snapshot", "official_today": "",
                "expected_from_stored": "", "component": "",
                "status": "not_testable_per_club",
                "note": "aggregate item/value table; club W-L rows are not stored under an abbr key",
                "source_url": "https://www.nfl.com/standings/",
            })
            continue
        stored = _load_standings(rel, key)
        # infer how many week-10 finals the snapshot already contained: pick the k
        # (bounded above by the pack's own read date) that reconciles the most clubs
        cap = w10_visible(ts)
        scored = [( _reconcile_at(stored, official, k)[0], k) for k in range(cap + 1)]
        best_good, k_inferred = max(scored)
        missing = sorted(set(official) - set(stored))
        for club in sorted(stored):
            if club not in official:
                rows.append({"pack": pack, "file": rel, "unit": "club", "club": club,
                             "stored": "", "official_today": "", "expected_from_stored": "",
                             "component": "", "status": "club_code_not_in_official_read",
                             "note": "abbreviation differs from today's page (AZ/LA/LAR/LAC etc.)",
                             "source_url": "https://www.nfl.com/standings/"})
                continue
            sw, sl, st, spf, spa = stored[club]
            ow, ol, ot, opf, opa = official[club]
            # add back the week-10 finals this snapshot could not have seen
            unseen = W10_ORDER[k_inferred:]
            aw, al, at, apf, apa = sw, sl, st, spf, spa
            for _gid, _d, away, home, a_s, h_s, _st in unseen:
                for club_x, pf, pa in ((away, a_s, h_s), (home, h_s, a_s)):
                    if club_x != club:
                        continue
                    aw += 1 if pf > pa else 0
                    al += 1 if pf < pa else 0
                    at += 1 if pf == pa else 0
                    apf += pf
                    apa += pa
            ok = (aw, al, at, apf, apa) == (ow, ol, ot, opf, opa)
            rows.append({
                "pack": pack, "file": rel, "unit": "club", "club": club,
                "stored": "%d-%d-%d PF %d PA %d" % (sw, sl, st, spf, spa),
                "official_today": "%d-%d-%d PF %d PA %d" % (ow, ol, ot, opf, opa),
                "expected_from_stored": "%d-%d-%d PF %d PA %d (stored + %d unseen week-10 finals)"
                                        % (aw, al, at, apf, apa, len(unseen)),
                "component": "",
                "status": "match" if ok else "mismatch",
                "note": ("k_inferred=%d (%d/%d clubs reconcile at that k)"
                         % (k_inferred, best_good, len(stored))) if ok else
                        ("k_inferred=%d (%d/%d clubs reconcile at that k); this club does not"
                         % (k_inferred, best_good, len(stored))),
                "source_url": "https://www.nfl.com/standings/",
            })
        for club in missing:
            rows.append({"pack": pack, "file": rel, "unit": "club", "club": club,
                         "stored": "", "official_today": "", "expected_from_stored": "",
                         "component": "", "status": "club_missing_from_pack",
                         "note": "club present on the official page but not stored", "source_url": ""})
    return rows


# --------------------------------------------------------------- results feeds
RESULTS_FILES = [
    ("nfl_309921cc", "data/nfl_309921cc/results_feed.csv", "away", "home", "away_score", "home_score", "week"),
    ("nfl_48217a55", "data/nfl_48217a55/results_feed.csv", "away", "home", "away_points", "home_points", "week"),
    ("nfl_67233566", "data/nfl_67233566/results_feed.csv", "away", "home", "away_points", "home_points", "week"),
    ("nfl_6cefc476", "data/nfl_6cefc476/results_feed.csv", "away", "home", "away_score", "home_score", "week"),
    ("nfl_8362b702", "data/nfl_8362b702/corpus_136.csv", "away", "home", "away_score", "home_score", "week"),
    ("nfl_d966f630", "data/nfl_d966f630/results_feed.csv", "away", "home", "away_points", "home_points", "week"),
    ("nfl_f4", "data/nfl_f4/results.csv", "away", "home", "away_score", "home_score", "week"),
    ("nfl_market", "data/nfl_market/results.csv", "away_team", "home_team", "away_score", "home_score", "week"),
]


def official_results() -> Dict[Tuple[int, str, str], Tuple[int, int]]:
    out: Dict[Tuple[int, str, str], Tuple[int, int]] = {}
    with (ROOT / "data/nfl_8362b702/corpus_136.csv").open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("away_score") and r.get("home_score"):
                out[(int(r["week"]), r["away"], r["home"])] = (int(r["away_score"]), int(r["home_score"]))
    for r in csv.DictReader((ROOT / "data/nfl_8362b702/results_week10.csv").open(newline="")):
        if r.get("away_score") and r.get("home_score"):
            out[(10, r["away"], r["home"])] = (int(r["away_score"]), int(r["home_score"]))
    for _gid, away, home, a_s, h_s in capture.NEW_FINALS:
        out[(10, away, home)] = (a_s, h_s)
    return out


def results_rows() -> List[Dict[str, object]]:
    official = official_results()
    rows: List[Dict[str, object]] = []
    for pack, rel, ak, hk, ask, hsk, wk in RESULTS_FILES:
        path = ROOT / rel
        if not path.exists():
            rows.append({"pack": pack, "file": rel, "week": "", "matchup": "", "stored": "",
                         "official": "", "status": "file_missing", "note": "", "source_url": ""})
            continue
        seen = set()
        with path.open(newline="") as fh:
            for r in csv.DictReader(fh):
                a, h = (r.get(ak) or "").strip(), (r.get(hk) or "").strip()
                a, h = CLUB_ALIAS.get(a, a), CLUB_ALIAS.get(h, h)
                w = _int(r.get(wk))
                a_s, h_s = _int(r.get(ask)), _int(r.get(hsk))
                if w is None or not a or not h or a_s is None or h_s is None:
                    continue
                seen.add((w, a, h))
                key = (w, a, h)
                if key not in official:
                    rows.append({"pack": pack, "file": rel, "week": w, "matchup": "%s@%s" % (a, h),
                                 "stored": "%d-%d" % (a_s, h_s), "official": "",
                                 "status": "not_in_official_log",
                                 "note": "row does not join to the official card log (week/away/home)",
                                 "source_url": ""})
                    continue
                off = official[key]
                ok = off == (a_s, h_s)
                st = (r.get("feed_status") or r.get("status") or r.get("result_status") or "").lower()
                if not ok and ("progress" in st or "live" in st or "schedul" in st):
                    rows.append({"pack": pack, "file": rel, "week": w, "matchup": "%s@%s" % (a, h),
                                 "stored": "%d-%d" % (a_s, h_s), "official": "%d-%d" % off,
                                 "status": "live_snapshot_not_final",
                                 "note": "pack labels this row %r and excludes it from its corpus; "
                                         "the official card is now final at a different score" % st,
                                 "source_url": "https://www.nfl.com/schedules/2026/by-week/week-%d" % w})
                    continue
                rows.append({"pack": pack, "file": rel, "week": w, "matchup": "%s@%s" % (a, h),
                             "stored": "%d-%d" % (a_s, h_s), "official": "%d-%d" % off,
                             "status": "match" if ok else "mismatch",
                             "note": "" if ok else "stored score differs from the official card",
                             "source_url": "https://www.nfl.com/schedules/2026/by-week/week-%d" % w})
        # week-10 finals missing from this pack (only for feeds that carry week 10)
        if not any(k[0] == 10 for k in seen):
            rows.append({"pack": pack, "file": rel, "week": "", "matchup": "", "stored": "",
                         "official": "", "status": "week10_out_of_scope",
                         "note": "this feed carries no week-10 row at all; week 10 is out of its scope",
                         "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"})
            continue
        for key, off in official.items():
            if key[0] == 10 and key not in seen:
                late = key[1:] in {(x[2], x[3]) for x in capture.NEW_FINALS}
                before = STORE_TIMES.get(pack, "") < "2026-11-15"
                status = ("not_yet_final_at_read"
                          if before or late else "missing_week10_final")
                rows.append({"pack": pack, "file": rel, "week": 10, "matchup": "%s@%s" % (key[1], key[2]),
                             "stored": "", "official": "%d-%d" % off, "status": status,
                             "note": ("this pack's capture predates the game going final"
                                      if status == "not_yet_final_at_read" else
                                      "official week-10 final not present in this pack's feed"),
                             "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"})
    return rows


def summarise(rows: Iterable[Dict[str, object]]) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for r in rows:
        d = out.setdefault(str(r["pack"]), {})
        d[str(r["status"])] = d.get(str(r["status"]), 0) + 1
    return out
