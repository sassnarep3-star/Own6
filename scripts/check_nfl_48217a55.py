#!/usr/bin/env python3
"""Verify the nfl-48217a55 pack.

Every rule below is a statement a reviewer can check by hand. The rules exist because this
pack's whole claim is that its tables are what the official pages said, that nothing was
invented, and that every blank is accounted for. If a rule cannot be checked by hand from
the cited page, it should not be here.

Exit code is non-zero if any rule fails, so this is the drift alarm (gate G12): wire it
into CI and a silent parser drift fails the build.

Usage
-----
    python3 scripts/check_nfl_48217a55.py
"""

from __future__ import annotations

import csv
import html.parser
import os
import re
import sys
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_48217a55 import OFFICIAL_HOSTS  # noqa: E402
from nfl_48217a55 import advice as A     # noqa: E402
from nfl_48217a55 import capture as C    # noqa: E402
from nfl_48217a55 import correlate as X  # noqa: E402
from nfl_48217a55 import flags as FL     # noqa: E402
from nfl_48217a55 import gates as G      # noqa: E402
from nfl_48217a55 import injuries as IN  # noqa: E402
from nfl_48217a55 import model as M      # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_48217a55")
DOCS = os.path.join(REPO, "docs", "nfl-48217a55")

PASS, FAIL = 0, 0
MESSAGES = []


def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
        MESSAGES.append(f"FAIL  {label}: {detail}")


def rule(n, label, ok, detail=""):
    check(f"rule {n} ({label})", ok, detail)


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def must_exist(names):
    for n in names:
        check(f"table {n} exists", os.path.exists(os.path.join(DATA, n)))


# ---------------------------------------------------------------------------
class RowLinks(html.parser.HTMLParser):
    """Collect, per table row, the external links and whether the table is internal."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []          # list of dicts: {internal: bool, rows: [ [links] ]}
        self._cur = None
        self._row = None
        self._in_td = False
        self._in_thead = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._cur = {"internal": bool(a.get("data-internal")),
                         "reason": a.get("data-internal", ""), "rows": []}
            self.tables.append(self._cur)
        elif tag == "thead":
            self._in_thead = True
        elif tag == "tr" and self._cur is not None:
            # header rows carry no data, so they carry no source link either
            self._row = None if self._in_thead else []
        elif tag == "td" and self._row is not None:
            self._in_td = True
        elif tag == "a" and self._row is not None:
            href = a.get("href", "")
            if href.startswith("http"):
                self._row.append(href)
        elif tag in ("input", "select", "textarea", "form", "button"):
            self._row = self._row if self._row is not None else []
            self._row.append("__INPUT__")

    def handle_endtag(self, tag):
        if tag == "td":
            self._in_td = False
        elif tag == "thead":
            self._in_thead = False
        elif tag == "tr" and self._cur is not None and self._row is not None:
            self._cur["rows"].append(self._row)
            self._row = None
        elif tag == "table":
            self._cur = None


def main() -> int:
    # ---------------------------------------------------------------- rule 1
    expected_tables = [
        "sources.csv", "injury_report_2026_11_15.csv", "injury_club_rollup.csv",
        "depth_of_replacement.csv", "announced_starters.csv", "roster_events.csv",
        "reserve_list.csv", "trades.csv", "week10_slate.csv", "week10_live_scores.csv",
        "results_feed.csv", "standings_as_rendered.csv", "standings_point_in_time.csv",
        "standings_reconstruction.csv", "standings_verification.csv", "integrity_checks.csv",
        "team_ratings_naive.csv", "luck_panel.csv", "week9_inactives.csv", "venues.csv",
        "depth_route_probe.csv", "correlations.csv", "correlation_exclusions.csv",
        "designation_calibration.csv", "price_capture_attempts.csv",
        "originated_lines_schema.csv", "strategy_registry.csv", "validation_gates.csv",
        "leaderboard.csv", "reward_tiers.csv", "requirements_decision_readiness.csv",
        "questions.csv", "suggestions.csv", "repo_findings.csv", "flagged.csv",
        "blank_audit.csv",
    ]
    must_exist(expected_tables)
    rule(1, "all 36 tables present",
         all(os.path.exists(os.path.join(DATA, n)) for n in expected_tables),
         "missing: " + ",".join(n for n in expected_tables
                                if not os.path.exists(os.path.join(DATA, n))))

    # ---------------------------------------------------------------- rule 2
    rep = read("injury_report_2026_11_15.csv") or []
    clubs = sorted({r["club"] for r in rep})
    all32 = set(C.CLUB_ABBR_ALIASES.values()) | {
        c for c, *_ in C.STANDINGS_RENDER}
    rule(2, "injury report covers 347 rows",
         len(rep) == 347, f"found {len(rep)}")
    rule(2, "clubs on the report plus bye clubs make 32",
         len(clubs) + len(C.BYE_CLUBS_WEEK10) == 32,
         f"{len(clubs)} on report + {len(C.BYE_CLUBS_WEEK10)} byes")
    rule(2, "no club appears both on the report and on bye",
         not (set(clubs) & set(C.BYE_CLUBS_WEEK10)),
         str(set(clubs) & set(C.BYE_CLUBS_WEEK10)))
    rule(2, "every club code is a known NFL club",
         set(clubs) <= all32, str(set(clubs) - all32))

    # ---------------------------------------------------------------- rule 3
    bad_practice = {r["practice_status"] for r in rep} - set(IN.PRACTICE_STATUSES)
    rule(3, "practice status is one of the three official values",
         not bad_practice, str(bad_practice))
    bad_game = {r["game_status"] for r in rep} - set(IN.DESIGNATIONS) - {""}
    rule(3, "game status is official or genuinely blank",
         not bad_game, str(bad_game))
    rule(3, "a blank game status is never published as a clearance",
         all(r["game_status"] != "Available" for r in rep))

    # ---------------------------------------------------------------- rule 4
    roll = read("injury_club_rollup.csv") or []
    rule(4, "club rollup sums to the report",
         sum(int(r["rows_on_report"]) for r in roll) == len(rep),
         f"{sum(int(r['rows_on_report']) for r in roll)} vs {len(rep)}")
    rule(4, "rollup Out count matches the report",
         sum(int(r["out"]) for r in roll)
         == sum(1 for r in rep if r["game_status"] == "Out"))
    rule(4, "rollup has one row per club on the report",
         len(roll) == len(clubs), f"{len(roll)} vs {len(clubs)}")

    # ---------------------------------------------------------------- rule 5
    pit = read("standings_point_in_time.csv") or []
    rule(5, "reconstructed table has 32 clubs", len(pit) == 32, str(len(pit)))
    pf = sum(int(r["pf"]) for r in pit)
    pa = sum(int(r["pa"]) for r in pit)
    rule(5, "league points for equals points against", pf == pa, f"{pf} vs {pa}")
    rule(5, "wins equal losses",
         sum(int(r["w"]) for r in pit) == sum(int(r["l"]) for r in pit))
    games = sum(int(r["games"]) for r in pit) // 2
    rule(5, "completed games through Week 9 is 136", games == 136, str(games))
    rule(5, "no club has a negative games played",
         all(int(r["games"]) > 0 for r in pit))

    # ---------------------------------------------------------------- rule 6
    recon = read("standings_reconstruction.csv") or []
    bad = []
    for r in recon:
        rw, rl, rt = (int(x) for x in r["rendered_record"].split("-"))
        sw, sl, st = (int(x) for x in r["reconstructed_record"].split("-"))
        sub = int(r["week10_games_subtracted"])
        if (rw - sw) + (rl - sl) + (rt - st) != sub:
            bad.append(r["club"])
        if int(r["rendered_pf"]) - int(r["subtracted_pf"]) != int(r["reconstructed_pf"]):
            bad.append(r["club"] + ":pf")
        if int(r["rendered_pa"]) - int(r["subtracted_pa"]) != int(r["reconstructed_pa"]):
            bad.append(r["club"] + ":pa")
    rule(6, "reconstruction arithmetic holds for every club", not bad, str(bad[:5]))

    # ---------------------------------------------------------------- rule 7
    ver = read("standings_verification.csv") or []
    nmatch = sum(1 for v in ver if v["match"] == "yes")
    rule(7, "reconstruction matches the official pregame page 10/10",
         nmatch == 10 and len(ver) == 10, f"{nmatch}/{len(ver)}")

    # ---------------------------------------------------------------- rule 8
    cors = read("correlations.csv") or []
    rule(8, "every correlation publishes n", all(c["n"] for c in cors))
    rule(8, "every correlation has n >= 3", all(int(c["n"]) >= 3 for c in cors))
    rule(8, "estimate lies inside its interval",
         all(float(c["ci_low"]) <= float(c["estimate"]) <= float(c["ci_high"])
             for c in cors))
    rule(8, "every correlation names a method", all(c["method"] for c in cors))
    rule(8, "both axes of every correlation cite an official https page",
         all(c["x_source_url"].startswith("https://") and c["y_source_url"].startswith("https://")
             and urlparse(c["x_source_url"]).hostname in OFFICIAL_HOSTS
             and urlparse(c["y_source_url"]).hostname in OFFICIAL_HOSTS for c in cors))
    excl = read("correlation_exclusions.csv") or []
    rule(8, "every excluded candidate says why and what would clear it",
         all(e["why_not"] and e["what_would_clear_it"] for e in excl))

    # ---------------------------------------------------------------- rule 9
    cal = read("designation_calibration.csv") or []
    rule(9, "no designation is marked usable as a feature",
         all(r["usable_as_feature"] == "no" for r in cal))
    rule(9, "every calibration row carries the selection warning",
         all(r["selection_warning"] for r in cal))

    # --------------------------------------------------------------- rule 10
    reqs = read("requirements_decision_readiness.csv") or []
    ids = [r["requirement_id"] for r in reqs]
    rule(10, "requirement ids are unique", len(ids) == len(set(ids)))
    rule(10, "every requirement has text and a published-state note",
         all(r["requirement"] and r["what_is_published"] for r in reqs))
    vocab = {A.CLEARED, A.PARTIAL, A.BLOCKED, A.REJECTED, A.NEEDS_REVIEW}
    rule(10, "status is in the published vocabulary",
         all(r["status"] in vocab for r in reqs),
         str({r["status"] for r in reqs} - vocab))
    rule(10, "every blocked or partial requirement names the number that clears it",
         all(r["clearing_number"] for r in reqs if r["status"] in (A.BLOCKED, A.PARTIAL)),
         str([r["requirement_id"] for r in reqs
              if r["status"] in (A.BLOCKED, A.PARTIAL) and not r["clearing_number"]]))
    rule(10, "every requirement row names its evidence file",
         all(r["evidence_file"] for r in reqs))

    # --------------------------------------------------------------- rule 11
    audit = read("blank_audit.csv") or []
    untraced = [a["table"] for a in audit
                if int(a["blank_cells"]) > 0 and not a["flag_ids"]
                and a["table"] not in FL.EXPECTED_BLANKS]
    rule(11, "every blank cell is traced to a flag or an expected-blank reason",
         not untraced, str(untraced))
    rule(11, "blank audit covers every published table",
         len(audit) == len(expected_tables),
         f"{len(audit)} vs {len(expected_tables)}")

    # --------------------------------------------------------------- rule 12
    flags = read("flagged.csv") or []
    fids = [f["flag_id"] for f in flags]
    rule(12, "flag ids are unique", len(fids) == len(set(fids)))
    rule(12, "flag severity is from the published set",
         all(f["severity"] in {"high", "medium", "low"} for f in flags))
    rule(12, "every flag says what would fill the gap",
         all(f["what_would_fill_it"] for f in flags))

    # --------------------------------------------------------------- rule 13
    schema = read("originated_lines_schema.csv") or []
    rule(13, "no market line is ever filled in",
         all(r["market_line"] == "" for r in schema))
    rule(13, "no difference column is ever filled in",
         all(r["difference"] == "" for r in schema))
    rule(13, "every blank market cell carries the price flag",
         all(r["flag_id"] == "48217-F01" for r in schema))
    rule(13, "origination order is side=1, total=2, moneyline=3",
         all({"side": "1", "total": "2", "moneyline": "3"}[r["market"]]
             == r["origination_stage"] for r in schema))

    # --------------------------------------------------------------- rule 14
    lb = read("leaderboard.csv") or []
    rule(14, "no strategy is ranked in any division",
         all(int(r["ranked_strategies"]) == 0 for r in lb))
    rule(14, "no strategy is qualified in any division",
         all(int(r["qualified_strategies"]) == 0 for r in lb))
    rule(14, "all five divisions are present", len(lb) == 5, str(len(lb)))
    tiers = read("reward_tiers.csv") or []
    rule(14, "no reward tier is monetary", all(t["monetary"] == "none" for t in tiers))

    # --------------------------------------------------------------- rule 15
    strat = read("strategy_registry.csv") or []
    rule(15, "every strategy is pre-registered",
         all("frozen" in s["pre_registration"].lower() for s in strat))
    candidates = [s for s in strat if s["family"] != "control"]
    rule(15, "every candidate strategy has a two-sided change-our-mind rule",
         all("Promote" in s["what_would_change_our_mind"]
             and "Demote" in s["what_would_change_our_mind"] for s in candidates),
         str([s["strategy_id"] for s in candidates
              if not ("Promote" in s["what_would_change_our_mind"]
                      and "Demote" in s["what_would_change_our_mind"])]))
    rule(15, "control strategies are marked as never promotable",
         all("never promoted" in s["what_would_change_our_mind"].lower()
             for s in strat if s["family"] == "control"))
    rule(15, "no strategy is qualified",
         all(s["qualified"] == "no" for s in strat))
    rule(15, "backtest numbers are forbidden on the leaderboard",
         all(s["backtest_on_leaderboard"] == "forbidden" for s in strat))
    controls = [s for s in strat if s["family"] == "control"]
    rule(15, "two control baselines are registered", len(controls) == 2, str(len(controls)))
    rule(15, "no combo strategy has an opened window",
         all(s["evaluation_window"].lower().startswith("not opened")
             for s in strat if s["family"] in ("parlay", "same-game parlay", "prop combo")))

    # --------------------------------------------------------------- rule 16
    pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
    rule(16, "all 18 pages exist", len(pages) == 18, str(len(pages)))

    broken, bad_host, no_src, inputs = [], [], [], []
    for name in pages:
        path = os.path.join(DOCS, name)
        text = open(path, encoding="utf-8").read()
        p = RowLinks()
        p.feed(text)
        for t in p.tables:
            for i, links in enumerate(t["rows"], start=1):
                if "__INPUT__" in links:
                    inputs.append(f"{name} table row {i}")
                ext = [l for l in links if l != "__INPUT__"]
                for l in ext:
                    host = urlparse(l).hostname or ""
                    if not l.startswith("https://") or host not in OFFICIAL_HOSTS:
                        bad_host.append(f"{name}: {l}")
                if not ext and not t["internal"]:
                    no_src.append(f"{name} table row {i}")
        for href in re.findall(r'href="([^"#][^"]*)"', text):
            if href.startswith("http"):
                continue
            target = os.path.join(DOCS, href.split("#")[0])
            if not os.path.exists(target):
                broken.append(f"{name} -> {href}")

    rule(16, "no internal link is broken", not broken, "; ".join(broken[:5]))
    rule(16, "every external link is https on an official host",
         not bad_host, "; ".join(sorted(set(bad_host))[:5]))
    rule(16, "every data row carries an official source link",
         not no_src, "; ".join(no_src[:5]))
    rule(16, "no page contains an input control", not inputs, "; ".join(inputs[:5]))

    # --------------------------------------------------------------- rule 17
    banned = ["guaranteed profit", "risk-free", "sure thing", "beat the book",
              "winning system", "expected profit of"]
    hits = []
    for name in pages:
        text = open(os.path.join(DOCS, name), encoding="utf-8").read().lower()
        for b in banned:
            if b in text:
                hits.append(f"{name}: {b}")
    rule(17, "no profitability claim anywhere", not hits, "; ".join(hits))

    live = read("week10_live_scores.csv") or []
    rule(17, "in-progress games are excluded from the results feed",
         all(r["in_results_feed"] == "no" for r in live))
    feed = read("results_feed.csv") or []
    rule(17, "the results feed holds finals only",
         all(r["status"] == "FINAL" for r in feed))

    # --------------------------------------------------------------- rule 18
    dep = read("depth_of_replacement.csv") or []
    rule(18, "no replacement is named from the injury report",
         all(r["replacement_named"] == "" for r in dep))
    ann = read("announced_starters.csv") or []
    rule(18, "every announced starter cites the page that names them",
         all(r["source_url"].startswith("https://") for r in ann))
    probe = read("depth_route_probe.csv") or []
    rule(18, "no depth order is published from the 404 route",
         all(r["depth_order_published"] == "" for r in probe))
    rule(18, "the 404 result is recorded, not hidden",
         any("404" in r["http_result"] for r in probe))

    # --------------------------------------------------------------- rule 19
    res = read("reserve_list.csv") or []
    rule(19, "reserve-list rows carry an interpretation, so absence is never read as health",
         all(r["interpretation"] for r in res))
    rule(19, "the reserve list is not empty",
         len(res) == len(C.RESERVE_LIST_NOV_2026), str(len(res)))
    w9 = read("week9_inactives.csv") or []
    rule(19, "inactive rows are club-attributed and venue-tagged",
         all(r["club"] and r["venue"] for r in w9))

    # --------------------------------------------------------------- rule 20
    gates = read("validation_gates.csv") or []
    rule(20, "every gate names the number that clears it",
         all(g["threshold"] for g in gates))
    rule(20, "every gate records what is observed now", all(g["observed"] for g in gates))
    rule(20, "every gate carries a source link",
         all(g["source_url"].startswith("https://") for g in gates))
    rule(20, "gate status is pass or fail",
         all(g["status"] in {"pass", "fail"} for g in gates))

    # --------------------------------------------------------------- rule 21
    qs = read("questions.csv") or []
    rule(21, "every question names the decision it blocks and a discovery path",
         all(q["decision_blocked"] and q["discovery_path"] for q in qs))
    rule(21, "every question says what we have and what is missing",
         all(q["what_we_have"] and q["what_is_missing"] for q in qs))
    sugs = read("suggestions.csv") or []
    rule(21, "every suggestion offers options and a cost of doing nothing",
         all(s["options"] and s["cost_of_doing_nothing"] for s in sugs))

    # --------------------------------------------------------------- rule 22
    srcs = read("sources.csv") or []
    rule(22, "every source has a URL and a read time",
         all(s["url"].startswith("https://") and s["read_at_utc"] for s in srcs))
    rule(22, "every source is on an official host",
         all(urlparse(s["url"]).hostname in OFFICIAL_HOSTS for s in srcs),
         str({urlparse(s["url"]).hostname for s in srcs} - set(OFFICIAL_HOSTS)))
    rule(22, "every source records the chunk range read",
         all(s["chunks_read"] for s in srcs))

    # --------------------------------------------------------------- rule 23
    rf = read("repo_findings.csv") or []
    rule(23, "every repo finding records how it was checked",
         all(r["how_it_was_checked"] for r in rf))
    rule(23, "every repo finding has a status", all(r["status"] for r in rf))
    rule(23, "every repo finding links its source",
         all(r["source_url"].startswith("http") for r in rf))

    # ------------------------------------------------------------------
    print(f"nfl-48217a55 pack: {PASS + FAIL} checks run, {FAIL} failure(s)")
    for m in MESSAGES:
        print(m)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
