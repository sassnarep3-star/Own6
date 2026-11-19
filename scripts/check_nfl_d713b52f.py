#!/usr/bin/env python3
"""Verifier for the nfl_d713b52f pack. Fails loudly on drift, unsourced rows or invented values.

Rules
-----
 1  every required data file exists and has its pinned row count
 2  every data row carries a non-empty field it must carry (per-file, below)
 3  every URL in the data is https and on an official host (nfl.com or its static host)
     or is an explicit, reviewed exception recorded in ALLOWED_EXTERNAL
 4  capture-log sha256 values match the raw files (capture.verify_capture_log)
 5  no page contains input, select, textarea or button
 6  no page contains placeholder text (TODO / TBD / lorem / XXX / {{)
 7  every internal link resolves to a file that exists
 8  every published dollar/ROI/CLV/units cell is empty (the price policy)
 9  every requirement row has a gate and a clearing number
10  every suggestion row is pending and has an empty decision
11  every flag row is non-blocking and carries an official link
12  standings arithmetic holds: 32 clubs, sum(PF) == sum(PA), sum(W) == sum(L)
13  the designation join reproduces its own counts from its rows
14  snap capacity: every club's transcribed player-snaps <= unit snaps * 11
15  model: every row carries a probability, an input hash, and a positive prior count
16  determinism: rebuilding the data and the site reproduces them byte for byte
17  the site has exactly the seven expected pages and the four model state facts are true
18  the Week 11 market and residual columns are empty and say why
19  every playtime row carries the publisher's 'Unofficial' label
20  no page states a win rate, ROI or profit as an outcome
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
DATA = os.path.join(REPO, "data", "nfl_d713b52f")
DOCS = os.path.join(REPO, "docs", "nfl-d713b52f")
sys.path.insert(0, os.path.join(REPO, "src"))

PINNED = {
    "capture_log.csv": 11,
    "source_probe.csv": 6,
    "standings.csv": 32,
    "fixtures.csv": 4,
    "starters.csv": 176,
    "playtime.csv": 121,
    "snap_sum.csv": 8,
    "game_status.csv": 79,
    "designation_join.csv": 79,
    "replacement.csv": 54,
    "snap_gap.csv": 16,
    "not_active.csv": 50,
    "club_view.csv": 8,
    "fixture_features.csv": 8,
    "model_outputs.csv": 134,
    "unscored.csv": 16,
    "backtest_summary.csv": 1,
    "implementation_comparison.csv": 1,
    "luck_panel.csv": 1,
    "week11_forecasts.csv": 3,
    "strategies.csv": 4,
    "recompute.csv": 38,
    "recompute_summary.csv": 1,
    "requirements.csv": 86,
    "gates.csv": 39,
    "questions.csv": 18,
    "suggestions.csv": 12,
    "flagged.csv": 12,
    "sources.csv": 15,
    "diff.csv": 33,
}

EXPECTED_PAGES = ["index.html", "evidence.html", "model.html", "availability.html",
                  "questions.html", "suggestions.html", "flagged.html"]

OFFICIAL_HOSTS = {"www.nfl.com", "static.www.nfl.com"}

# URLs that appear in data as text but are not sources for a value. Each needs a reason.
ALLOWED_EXTERNAL = {}


class Fail(Exception):
    pass


def rows(name):
    with open(os.path.join(DATA, name), newline="") as fh:
        return list(csv.DictReader(fh))


def rule1_and_2(errors):
    for name, n in PINNED.items():
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            errors.append(f"rule1: {name} missing")
            continue
        got = len(rows(name))
        if got != n:
            errors.append(f"rule1: {name} has {got} rows, pinned at {n}")
    must = {
        "standings.csv": ["club", "w", "l", "pf", "pa", "source_url"],
        "fixtures.csv": ["game_id", "venue_game_book", "source_url"],
        "starters.csv": ["game_id", "club", "player_as_printed", "source_url"],
        "not_active.csv": ["game_id", "club", "player_as_printed", "source_url"],
        "playtime.csv": ["club", "player_as_printed", "snaps", "source_url", "publisher_label"],
        "designation_join.csv": ["game_id", "club", "player", "game_status", "report_url", "book_url"],
        "snap_gap.csv": ["player", "consistent", "report_url", "book_url"],
        "replacement.csv": ["player", "designation", "book_url"],
        "model_outputs.csv": ["game_id", "p_home_win", "inputs_sha256", "inputs_json"],
        "requirements.csv": ["rid", "gate", "clears_it", "status"],
        "suggestions.csv": ["sid", "status"],
        "flagged.csv": ["fid", "source_url", "blocks_merge"],
        "capture_log.csv": ["raw_file", "source_url", "sha256", "read_at_utc"],
        "sources.csv": ["url", "host", "read_at_utc"],
        "week11_forecasts.csv": ["game_id", "p_home_win", "state", "price_note"],
        "questions.csv": ["qid", "question", "need", "discovery"],
        "gates.csv": ["gate", "clears", "state"],
    }
    for name, cols in must.items():
        for r in rows(name):
            for c in cols:
                if str(r.get(c, "")).strip() == "":
                    errors.append(f"rule2: {name} row {r.get('rid') or r.get('fid') or r.get('sid') or r.get('game_id') or '?'} is missing {c}")
                    break


def rule3(errors):
    url_re = re.compile(r"https?://[^\s,;\"'<>]+")
    for name in os.listdir(DATA):
        if not name.endswith(".csv"):
            continue
        for i, r in enumerate(rows(name), start=2):
            for key, val in r.items():
                if not val:
                    continue
                for url in url_re.findall(val):
                    host = url.split("/")[2]
                    if host in OFFICIAL_HOSTS:
                        continue
                    if host in ALLOWED_EXTERNAL:
                        continue
                    errors.append(f"rule3: {name} line {i} field {key} cites a non-official host {host}")


def rule4(errors):
    from nfl_d713b52f import capture
    ok, problems = capture.verify_capture_log()
    for p in problems:
        errors.append(f"rule4: {p}")


def page_text(name):
    with open(os.path.join(DOCS, name)) as fh:
        return fh.read()


def rule5_6(errors):
    for name in EXPECTED_PAGES:
        text = page_text(name).lower()
        for tag in ("<input", "<select", "<textarea", "<button"):
            if tag in text:
                errors.append(f"rule5: {name} contains {tag}")
        for bad in ("todo", "tbd", "lorem", "xxx", "{{"):
            if bad in text:
                errors.append(f"rule6: {name} contains placeholder {bad!r}")


def rule7(errors):
    link_re = re.compile(r'href="([^"#]+)"')
    for name in EXPECTED_PAGES:
        text = page_text(name)
        for href in link_re.findall(text):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(DOCS, href))
            if not os.path.exists(target):
                errors.append(f"rule7: {name} links to missing {href}")


def rule8(errors):
    banned = re.compile(r"\b(roi|clv|units|profit|bankroll|stake)\b", re.I)
    for name in ("week11_forecasts.csv", "strategies.csv", "backtest_summary.csv", "leaderboard.csv"):
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            continue
        for r in rows(name):
            for key, val in r.items():
                if re.search(r"(roi|clv|units|profit|stake|market)", key, re.I) and str(val).strip():
                    errors.append(f"rule8: {name} publishes a price/staking value in {key}: {val!r}")
    # A page may name a staking term freely; what it may not do is attach a number to one.
    absence = re.compile(r"blank|absent|empty|no price|by policy|cannot|no official page|not computed|"
                         r"drop roi|roi and clv|no official", re.I)
    for name in EXPECTED_PAGES:
        text = page_text(name)
        for m in banned.finditer(text):
            # the term must be adjacent to a number to count as a claim about it
            adj = text[max(0, m.start() - 22): m.end() + 22]
            window = text[max(0, m.start() - 120): m.end() + 60]
            if re.search(r"[-+]?\d[\d.,]*\s?%?", adj) and not absence.search(window):
                errors.append(f"rule8: {name} attaches a number to a staking term: …{window.strip()[-120:]}…")
                break


def rule9(errors):
    for r in rows("requirements.csv"):
        if not r["gate"].strip() or not r["clears_it"].strip():
            errors.append(f"rule9: {r['rid']} lacks a gate or a clearing number")
        if r["status"] not in ("done", "partial", "blocked"):
            errors.append(f"rule9: {r['rid']} has unknown status {r['status']}")


def rule10(errors):
    for r in rows("suggestions.csv"):
        if r["status"] != "pending_human_choice":
            errors.append(f"rule10: {r['sid']} status is {r['status']}")
        if r["decision"].strip():
            errors.append(f"rule10: {r['sid']} already carries a decision")


def rule11(errors):
    for r in rows("flagged.csv"):
        if r["blocks_merge"] != "no":
            errors.append(f"rule11: {r['fid']} claims to block the merge")
        if not r["source_url"].startswith("https://"):
            errors.append(f"rule11: {r['fid']} lacks an official link")


def rule12(errors):
    st = rows("standings.csv")
    if len(st) != 32:
        errors.append("rule12: not 32 clubs")
    pf = sum(int(r["pf"]) for r in st)
    pa = sum(int(r["pa"]) for r in st)
    if pf != pa:
        errors.append(f"rule12: sum(PF)={pf} != sum(PA)={pa}")
    w = sum(int(r["w"]) for r in st)
    l = sum(int(r["l"]) for r in st)
    if w != l:
        errors.append(f"rule12: sum(W)={w} != sum(L)={l}")
    for r in st:
        if int(r["pf"]) - int(r["pa"]) != int(r["net_pts"]):
            errors.append(f"rule12: {r['club']} net points does not equal PF-PA")


def rule13(errors):
    j = rows("designation_join.csv")
    out = [r for r in j if r["game_status"] == "Out"]
    q = [r for r in j if r["game_status"] == "Questionable"]
    consistent = [r for r in out if r["not_active"].startswith("yes")]
    if len(out) != 16:
        errors.append(f"rule13: {len(out)} Out rows, expected 16")
    if len(consistent) != 12:
        errors.append(f"rule13: {len(consistent)} Out rows on the inactive list, expected 12")
    if len(q) != 25:
        errors.append(f"rule13: {len(q)} Questionable rows, expected 25")
    gap = rows("snap_gap.csv")
    if len(gap) != len(out):
        errors.append(f"rule13: snap_gap has {len(gap)} rows for {len(out)} Out designations")
    # every club's counts must equal the rows behind them
    for c in rows("club_view.csv"):
        mine = [r for r in j if r["club"] == c["club"] and r["game_id"] == c["game_id"]]
        if int(c["declared_out"]) != len([r for r in mine if r["game_status"] == "Out"]):
            errors.append(f"rule13: {c['club']} declared_out does not match its rows")


def rule14(errors):
    for s in rows("snap_sum.csv"):
        if int(s["player_snaps_transcribed"]) > int(s["capacity_player_snaps"]):
            errors.append(f"rule14: {s['club']} transcribed player-snaps exceed the 11-player capacity")
        if s["within_capacity"] != "yes":
            errors.append(f"rule14: {s['club']} marked outside capacity")


def rule15b(errors):
    """The luck panel must not be degenerate, and its published identity must close."""
    lp = rows("luck_panel.csv")[0]
    if lp["bins_used"] == lp["n"]:
        errors.append("rule15b: one game per bin — the decomposition is degenerate and must not be quoted")
    if float(lp["identity_residual"]) > 1e-9:
        errors.append(f"rule15b: the Murphy identity does not close ({lp['identity_residual']})")
    if abs(float(lp["brier"]) - float(lp["brier_binned"])) > 0.02:
        errors.append("rule15b: binning moved the Brier score by more than 0.02; the bins are too coarse")


def rule15(errors):
    for r in rows("model_outputs.csv"):
        p = float(r["p_home_win"])
        if not (0.0 <= p <= 1.0):
            errors.append(f"rule15: {r['game_id']} probability {p} outside [0,1]")
        if len(r["inputs_sha256"]) != 64:
            errors.append(f"rule15: {r['game_id']} input hash is not 64 hex chars")
        payload = r["inputs_json"]
        if hashlib.sha256(payload.encode()).hexdigest() != r["inputs_sha256"]:
            errors.append(f"rule15: {r['game_id']} input hash does not match its payload")
        if int(r["n_home_prior"]) < 1 or int(r["n_away_prior"]) < 1:
            errors.append(f"rule15: {r['game_id']} scored with a club having no prior game")
    bt = rows("backtest_summary.csv")[0]
    if float(bt["bss_lo_week_cluster"]) > 0:
        errors.append("rule15: the lower bound is positive; the site's 'nothing is promoted' claim is now false and must be updated")


def rule16(errors):
    """Rebuild my own trees and compare bytes; never leave a foreign file modified.

    The build scripts here only write ``data/nfl_d713b52f`` and ``docs/nfl-d713b52f``. Later
    packs' builders enumerate *this* pack's registers, so running this verifier can make a
    neighbouring pack's generated files stale on disk. The verifier therefore snapshots the
    git status of everything outside its own scope and restores any file that changed,
    rather than trusting the builders to stay in their lane.
    """
    import subprocess as sp
    def dirty_outside():
        out = sp.run(["git", "status", "--porcelain", "--", "data", "docs"],
                     cwd=REPO, capture_output=True, text=True).stdout
        keep = []
        for line in out.splitlines():
            path = line[3:].strip().strip('"')
            if path.startswith(("data/nfl_d713b52f/", "docs/nfl-d713b52f/")):
                continue
            keep.append(path)
        return keep
    foreign_before = set(dirty_outside())
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        # rebuild data into the real tree, but compare against a saved copy first
        saved = {}
        for name in PINNED:
            with open(os.path.join(DATA, name), "rb") as fh:
                saved[name] = fh.read()
        saved_docs = {}
        for name in EXPECTED_PAGES:
            with open(os.path.join(DOCS, name), "rb") as fh:
                saved_docs[name] = fh.read()
        subprocess.check_call([sys.executable, os.path.join(REPO, "scripts", "build_nfl_d713b52f_data.py")],
                              stdout=subprocess.DEVNULL, env=env)
        subprocess.check_call([sys.executable, os.path.join(REPO, "scripts", "build_nfl_d713b52f.py")],
                              stdout=subprocess.DEVNULL, env=env)
        for name in PINNED:
            with open(os.path.join(DATA, name), "rb") as fh:
                if fh.read() != saved[name]:
                    errors.append(f"rule16: {name} is not reproducible byte for byte")
        for name in EXPECTED_PAGES:
            with open(os.path.join(DOCS, name), "rb") as fh:
                if fh.read() != saved_docs[name]:
                    errors.append(f"rule16: {name} is not reproducible byte for byte")
        del tmp
    foreign_after = set(dirty_outside()) - foreign_before
    if foreign_after:
        sp.run(["git", "checkout", "HEAD", "--"] + sorted(foreign_after), cwd=REPO, check=False)
        print(f"   note: restored {len(foreign_after)} file(s) outside this pack's scope: "
              f"{sorted(foreign_after)[:3]}")


def rule17(errors):
    for name in EXPECTED_PAGES:
        if not os.path.exists(os.path.join(DOCS, name)):
            errors.append(f"rule17: {name} missing")
    bt = rows("backtest_summary.csv")[0]
    if bt["state"] != "paper":
        errors.append("rule17: the model is not in paper state")
    for s in rows("strategies.csv"):
        if s["state"] == "live":
            errors.append("rule17: a strategy claims live state with no prospective sample")
        if int(s["prospective_n"]) != 0:
            errors.append("rule17: a strategy claims a prospective sample that cannot exist yet")


def rule18(errors):
    for r in rows("week11_forecasts.csv"):
        for col in ("market_side", "market_total", "market_moneyline", "residual_side",
                    "residual_total", "residual_moneyline"):
            if r[col].strip():
                errors.append(f"rule18: {r['game_id']} publishes {col} without a price source")
        if "by policy" not in r["price_note"]:
            errors.append(f"rule18: {r['game_id']} does not state the price policy")


def rule19(errors):
    for r in rows("playtime.csv"):
        if r["publisher_label"] != "Unofficial":
            errors.append(f"rule19: {r['club']} {r['player_as_printed']} is not labelled Unofficial")


def rule20(errors):
    """No page may present a win rate or return as an achieved outcome."""
    for name in EXPECTED_PAGES:
        text = page_text(name)
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s?%", text):
            ctx = text[max(0, m.start() - 90): m.end() + 40].lower()
            if re.search(r"(win rate|return|profit)", ctx) and "not" not in ctx and "no " not in ctx:
                errors.append(f"rule20: {name} states a percentage as an outcome: …{ctx.strip()[:100]}…")


def main():
    errors = []
    rule1_and_2(errors)
    rule3(errors)
    rule4(errors)
    rule5_6(errors)
    rule7(errors)
    rule8(errors)
    rule9(errors)
    rule10(errors)
    rule11(errors)
    rule12(errors)
    rule13(errors)
    rule14(errors)
    rule15(errors)
    rule15b(errors)
    rule17(errors)
    rule18(errors)
    rule19(errors)
    rule20(errors)
    rule16(errors)   # last: it rewrites the tree

    if errors:
        print(f"FAIL — {len(errors)} problem(s)")
        for e in errors[:80]:
            print("  ", e)
        if len(errors) > 80:
            print(f"   … and {len(errors) - 80} more")
        sys.exit(1)
    print(f"OK — 21 rules, {sum(PINNED.values()):,} pinned data rows, {len(EXPECTED_PAGES)} pages")


if __name__ == "__main__":
    main()
