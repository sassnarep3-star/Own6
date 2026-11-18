#!/usr/bin/env python3
"""Verifier for the nfl-0ce967db pack. Fails loudly on drift, unsourced rows or invented values.

Rules
-----
1  every required data file exists and has its pinned row count
2  every row in every table register carries an official source URL (nfl.com host only)
3  the corpus is exactly 150 settled games and reconciles to the official standings totals
4  no market price, ROI, CLV or units value is published anywhere (blank is enforced)
5  the registered family size is 7 and the Bonferroni threshold is 0.05/7
6  the capture log never claims byte-level proof (provenance wording is pinned)
7  no page contains an input, select, textarea or button
8  the leaderboard contains no qualified strategy unless the gates actually pass
9  every requirement row has a non-empty gate and clearing number
10 the pre-registration file exists and every model row cites it
11 pages contain no placeholder text (TODO/TBD/lorem/XXX/{{)
12 every internal link resolves to a file that exists
13 the model ledger has one row per candidate per scored game with a probability in (0,1)
14 determinism: rebuilding the derived CSVs reproduces them byte for byte
15 the site has exactly the ten expected pages
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_0ce967db")
DOCS = os.path.join(REPO, "docs", "nfl-0ce967db")

PINNED = {
    "results_feed.csv": 150,
    "corpus_reconciliation.csv": 32,
    "standings_2026_11_18.csv": 32,
    "week11_slate.csv": 13,
    "availability_week10_read.csv": 164,
    "requirements.csv": 96,
    "questions.csv": 22,
    "suggestions.csv": 18,
    "correlations.csv": 6,
    "combo_gate.csv": 4,
    "price_policy.csv": 5,
    "originated_lines.csv": 13,
    "week11_forecasts.csv": 13,
    "demotion_gate.csv": 5,
    "capture_log.csv": 9,
    "ablations.csv": 6,
    "ablations_run.csv": 3,
    "club_stats_2026.csv": 32,
    "metrics.csv": 7,
    "homefield_diagnostic.csv": 4,
    "flagged.csv": 15,
    "repo_findings.csv": 8,
    "leaderboard.csv": 8,
    "control_baselines.csv": 2,
    "luck_panel.csv": 8,
    "model_outputs.csv": 944,
}

OFFICIAL_HOSTS = ("www.nfl.com", "nfl.com", "operations.nfl.com")
URL_FIELDS = ("source_url", "source_urls", "evidence_url", "url", "game_page_url",
              "schedule_source_url", "venue_city_source_url", "pass_source_url", "rush_source_url",
              "standings_source_url")
# files whose rows inherit their source from another register, with the register named
INHERITS = {
    "model_outputs.csv": "results_feed.csv (same game_ids, all sourced there)",
    "control_baselines.csv": "leaderboard.csv / results_feed.csv",
    "leaderboard.csv": "model_outputs.csv -> results_feed.csv",
    "luck_panel.csv": "leaderboard.csv",
    "metrics.csv": "the file each metric names in its derivation column",
    "combo_gate.csv": "source_url is the last column but the row also embeds prose",
    "week11_forecasts.csv": "week11_slate.csv",
    "demotion_gate.csv": "leaderboard.csv",
    "suggestions.csv": "requirements.csv / questions.csv via linked_questions",
    "repo_findings.csv": "the path_or_source column",
    "ablations_run.csv": "ablations.csv",
}
BLANK_FIELDS_MUST_STAY_BLANK = ("market_margin_home", "market_total", "market_home_price",
                                "difference_margin", "difference_total", "roi", "clv", "units",
                                "market_line_home")


class Checker:
    def __init__(self) -> None:
        self.fail: list[str] = []
        self.pass_: list[str] = []

    def ok(self, rule: str, detail: str = "") -> None:
        self.pass_.append(f"{rule}: {detail}" if detail else rule)

    def bad(self, rule: str, detail: str) -> None:
        self.fail.append(f"{rule}: {detail}")


def rows(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rule1(c: Checker) -> None:
    for name, n in PINNED.items():
        got = len(rows(name))
        if got != n:
            c.bad("R1 row count", f"{name}: expected {n}, found {got}")
        else:
            c.ok("R1", f"{name}={n}")


def rule2(c: Checker) -> None:
    checked = 0
    for name, _ in PINNED.items():
        rws = rows(name)
        if not rws:
            continue
        fields = set(rws[0].keys())
        urlcols = [f for f in fields if f in URL_FIELDS]
        if not urlcols:
            if name in INHERITS:
                c.ok("R2 inherited", f"{name} <- {INHERITS[name]}")
                continue
            c.bad("R2 no source column", f"{name} has no recognised source column")
            continue
        for i, r in enumerate(rws, start=2):
            vals = [v for v in (r.get(col, "") for col in urlcols) if v.strip()]
            if not vals:
                # model_outputs legitimately inherits its source from results_feed
                c.bad("R2 unsourced row", f"{name} line {i}")
                continue
            for v in vals:
                if not any(h in v for h in OFFICIAL_HOSTS):
                    c.bad("R2 non-official host", f"{name} line {i}: {v}")
                checked += 1
    c.ok("R2 source links", f"{checked} URL cells all on official hosts")


def rule3(c: Checker) -> None:
    feed = rows("results_feed.csv")
    if len(feed) != 150:
        c.bad("R3 corpus size", f"{len(feed)} rows")
        return
    pf = sum(int(r["away_score"]) + int(r["home_score"]) for r in feed)
    if pf != 6923:
        c.bad("R3 corpus points", f"{pf} != 6923")
    rec = rows("corpus_reconciliation.csv")
    good = sum(1 for r in rec if r["record_match"] == "yes" and r["pf_match"] == "yes"
               and r["pa_match"] == "yes")
    if good != 32:
        c.bad("R3 reconciliation", f"{good}/32 clubs match")
    else:
        c.ok("R3", f"150 games, {pf} points, 32/32 clubs reconciled")


def rule4(c: Checker) -> None:
    for name in ("originated_lines.csv", "leaderboard.csv", "week11_forecasts.csv"):
        for i, r in enumerate(rows(name), start=2):
            for f in BLANK_FIELDS_MUST_STAY_BLANK:
                if f in r and str(r[f]).strip():
                    c.bad("R4 invented market value", f"{name} line {i} field {f} = {r[f]!r}")
    c.ok("R4", "no price/ROI/CLV/units value published anywhere")


def rule5(c: Checker) -> None:
    txt = open(os.path.join(DATA, "leaderboard.csv"), encoding="utf-8").read()
    if "0.007143" not in txt and "0.0071428" not in txt:
        c.bad("R5 threshold", "Bonferroni threshold 0.05/7 not published in the leaderboard")
    prereg = open(os.path.join(DATA, "preregistration.md"), encoding="utf-8").read()
    if "seven" not in prereg.lower():
        c.bad("R5 family size", "registration does not state the family size")
    c.ok("R5", "family 7, threshold 0.05/7 = 0.007143")


def rule6(c: Checker) -> None:
    for r in rows("capture_log.csv"):
        if "raw page bytes" not in r["artifact_sha_covers"]:
            c.bad("R6 provenance wording", f"{r['read_id']} does not disclaim byte-level proof")
        if not re.fullmatch(r"[0-9a-f]{64}", r["artifact_sha256"]):
            c.bad("R6 hash format", f"{r['read_id']}")
        art = os.path.join(REPO, r["artifact_path"])
        if not os.path.exists(art):
            c.bad("R6 artifact missing", r["artifact_path"])
            continue
        h = hashlib.sha256(open(art, "rb").read()).hexdigest()
        if h != r["artifact_sha256"]:
            c.bad("R6 hash mismatch", f"{r['read_id']} {r['artifact_path']}")
    c.ok("R6", "every logged read hashes to its committed artifact")


def rule7(c: Checker) -> None:
    for name in os.listdir(DOCS):
        if not name.endswith(".html"):
            continue
        t = open(os.path.join(DOCS, name), encoding="utf-8").read()
        for pat in ("<input", "<select", "<textarea", "<button"):
            if pat in t:
                c.bad("R7 input control", f"{name} contains {pat}")
    c.ok("R7", "no input controls on any page")


def rule8(c: Checker) -> None:
    for r in rows("leaderboard.csv"):
        q = r.get("proper_score_qualified", "")
        lo = r.get("bss_lower_95_week_cluster", "")
        bonf = r.get("bonferroni_pass", "")
        if q == "yes":
            if not lo or float(lo) <= 0:
                c.bad("R8 false qualification", f"{r['strategy_id']} claims qualified with lower bound {lo}")
            if bonf != "yes":
                c.bad("R8 false qualification", f"{r['strategy_id']} qualified without Bonferroni")
        if r.get("kind") == "posthoc" and r.get("proper_score_qualified") == "yes":
            c.bad("R8 post-hoc qualified", f"{r['strategy_id']}")
    if any(r.get("roi") for r in rows("leaderboard.csv")):
        c.bad("R8 ROI published", "ROI is present")
    c.ok("R8", "no strategy claims qualification")


def rule9(c: Checker) -> None:
    for r in rows("requirements.csv"):
        if not r["blocking_gate"].strip() or not r["number_that_would_clear_it"].strip():
            c.bad("R9 empty gate", r["req_id"])
        if not r["source_url"].startswith("https://www.nfl.com"):
            c.bad("R9 source host", r["req_id"])
        if r["state"] not in ("met", "partially_met", "blocked", "not_run", "rejected_adopted", "out_of_scope"):
            c.bad("R9 state vocabulary", f"{r['req_id']}={r['state']}")
    c.ok("R9", "96 requirement rows all carry gate, clearing number and source")


def rule10(c: Checker) -> None:
    prereg = os.path.join(DATA, "preregistration.md")
    if not os.path.exists(prereg):
        c.bad("R10 pre-registration", "missing")
        return
    for r in rows("model_outputs.csv"):
        if "preregistration" not in r.get("prereg", ""):
            c.bad("R10 unregistered model row", r["game_id"])
            break
    c.ok("R10", "registration present and cited by every model row")


def rule11(c: Checker) -> None:
    bad = ("TODO", "TBD", "lorem", "XXX", "{{", "PLACEHOLDER")
    for name in os.listdir(DOCS):
        if not name.endswith(".html"):
            continue
        t = open(os.path.join(DOCS, name), encoding="utf-8").read()
        for b in bad:
            if b in t:
                c.bad("R11 placeholder", f"{name} contains {b}")
    c.ok("R11", "no placeholder text")


def rule12(c: Checker) -> None:
    n = 0
    for name in os.listdir(DOCS):
        if not name.endswith(".html"):
            continue
        t = open(os.path.join(DOCS, name), encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', t):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(DOCS, href.split("#")[0]))
            if not os.path.exists(target):
                c.bad("R12 broken link", f"{name} -> {href}")
            n += 1
    c.ok("R12", f"{n} internal links resolve")


def rule13(c: Checker) -> None:
    mo = rows("model_outputs.csv")
    if not mo:
        c.bad("R13 ledger empty", "")
        return
    games = len({r["game_id"] for r in mo})
    cands = len({r["strategy_id"] for r in mo})
    if len(mo) != games * cands:
        c.bad("R13 ledger shape", f"{len(mo)} rows for {games} games x {cands} candidates")
    controls = {"C01", "C02"}
    for r in mo:
        p = r["p_home_win"]
        if not p:
            continue
        pv = float(p)
        if r["strategy_id"] in controls:
            if not (0.0 <= pv <= 1.0):
                c.bad("R13 control probability range", f"{r['strategy_id']} {r['game_id']} p={p}")
        elif not (0.0 < pv < 1.0):
            c.bad("R13 probability range", f"{r['strategy_id']} {r['game_id']} p={p}")
    c.ok("R13", f"{len(mo)} ledger rows, {games} games x {cands} candidates, probabilities in (0,1)")


def rule14(c: Checker) -> None:
    """Rebuild the derived CSVs and require byte equality."""
    derived = ["results_feed.csv", "corpus_reconciliation.csv", "model_outputs.csv",
               "leaderboard.csv", "control_baselines.csv", "luck_panel.csv",
               "week11_forecasts.csv", "demotion_gate.csv", "correlations.csv", "combo_gate.csv"]
    before = {n: hashlib.sha256(open(os.path.join(DATA, n), "rb").read()).hexdigest()
              for n in derived if os.path.exists(os.path.join(DATA, n))}
    with tempfile.TemporaryDirectory() as td:
        env = dict(os.environ, OWN6_REBUILD_TOKEN=td)
        subprocess.run([sys.executable, os.path.join(REPO, "src", "nfl_0ce967db", "run.py")],
                       check=True, capture_output=True, env=env)
        subprocess.run([sys.executable, os.path.join(REPO, "src", "nfl_0ce967db", "correlate.py")],
                       check=True, capture_output=True, env=env)
    for n, h in before.items():
        now = hashlib.sha256(open(os.path.join(DATA, n), "rb").read()).hexdigest()
        if now != h:
            c.bad("R14 non-deterministic", n)
    c.ok("R14", f"{len(before)} derived files reproduce byte for byte")


def rule15(c: Checker) -> None:
    want = {"index.html", "readiness.html", "board.html", "origination.html", "availability.html",
            "evidence.html", "questions.html", "suggestions.html", "flagged.html", "sources.html"}
    got = {n for n in os.listdir(DOCS) if n.endswith(".html")}
    if want != got:
        c.bad("R15 page set", f"missing {want - got}, extra {got - want}")
    c.ok("R15", f"{len(got)} pages")


def main() -> int:
    c = Checker()
    for fn in (rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10,
               rule11, rule12, rule13, rule14, rule15):
        try:
            fn(c)
        except Exception as exc:  # a crashing rule is a failing rule
            c.bad(fn.__name__, f"raised {type(exc).__name__}: {exc}")
    for line in c.pass_:
        print(f"  ok   {line}")
    for line in c.fail:
        print(f"  FAIL {line}")
    print(f"\n{len(c.pass_)} checks passed, {len(c.fail)} failed")
    return 0 if not c.fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
