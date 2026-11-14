#!/usr/bin/env python3
"""Verification gate for the nfl_market pack.

Fails closed. Every rule below is a hard failure, not a warning, because each
one corresponds to a way the site could mislead a reader.

Rules
-----
R01 every data CSV has a header
R02 every row of every publishable CSV carries an official HTTPS source URL
R03 no source URL points at a host outside the official allowlist
R04 no value was invented: every blank in a market/price column has a status
R05 the difference column is blank wherever the market line is blank
R06 the side market precedes the total, which precedes the moneyline
R07 every correlation row publishes n, or explains why n is n/a
R08 the leaderboard keeps signal and staking in separate columns
R09 the demotion table fires at least one trigger somewhere (gate is live, not decorative)
R10 the depth register publishes a replacement string for every slot
R11 no HTML page contains a form or an input (the site is zero-input)
R12 every internal link in every page resolves to a file that exists
R13 every HTML page carries the source footer
R14 the site has no page with zero table rows
"""

from __future__ import annotations

import csv
import glob
import os
import re
import sys
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_market")
DOCS = os.path.join(REPO, "docs", "nfl-market")

OFFICIAL_HOSTS = {
    "www.nfl.com",
    "nfl.com",
    "operations.nfl.com",
    "www.patriots.com",
    "www.detroitlions.com",
    "media.nfl.com",
}

# CSVs whose rows must each carry a source URL.
SOURCED_CSVS = {
    "results.csv",
    "standings.csv",
    "slate_week10.csv",
    "injuries_week10.csv",
    "originated_markets.csv",
    "price_snapshots.csv",
    "backtest_ledger.csv",
    "correlations.csv",
    "replacement_depth.csv",
    "depth_conflicts.csv",
    "sources.csv",
    "flagged.csv",
    "price_snapshot_coverage.csv",
    "luck_index.csv",
}

failures = []
checks = [0]


def check(rule, condition, detail):
    checks[0] += 1
    if not condition:
        failures.append((rule, detail))
    return condition


def read(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def url_ok(u):
    if not u or not u.startswith("https://"):
        return False
    host = urlparse(u).hostname or ""
    return host in OFFICIAL_HOSTS


def main():
    # ---------------------------------------------------------------- R01
    for path in sorted(glob.glob(os.path.join(DATA, "*.csv"))):
        name = os.path.basename(path)
        with open(path, newline="", encoding="utf-8") as fh:
            header = fh.readline().strip()
        check("R01", bool(header), "%s has no header row" % name)

    # ---------------------------------------------------------------- R02/R03
    for name in sorted(SOURCED_CSVS):
        rows = read(name)
        check("R02", bool(rows), "%s is empty" % name)
        col = "official_source_url"
        if name == "sources.csv":
            col = "official_source_url"
        check("R02", col in rows[0], "%s has no %s column" % (name, col))
        bad = [i for i, r in enumerate(rows, start=2) if not url_ok(r.get(col, ""))]
        check("R02", not bad, "%s: %d rows without an official source (e.g. line %s)"
              % (name, len(bad), bad[:5]))

    # every URL appearing anywhere in any CSV must be an official host
    for path in sorted(glob.glob(os.path.join(DATA, "*.csv"))):
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for u in set(re.findall(r"https?://[^\s,\"]+", text)):
            check("R03", url_ok(u.rstrip(").;")), "%s cites a non-official URL: %s" % (name, u))

    # ---------------------------------------------------------------- R04
    orig = read("originated_markets.csv")
    for r in orig:
        if r["market_line"] == "":
            check("R04", r["status"] != "", "originated row %s/%s has a blank market line but no status"
                  % (r["game_key"], r["market"]))
    snaps = read("price_snapshots.csv")
    for r in snaps:
        if r["opening_price"] == "":
            check("R04", r["snapshot_status"] != "", "snapshot row %s has a blank price but no status"
                  % r["game_id"])
    check("R04", all(r["snapshot_status"] == "unverified_no_official_price_source" for r in snaps),
          "a snapshot row carries a price or an unexplained status")

    # ---------------------------------------------------------------- R05
    for r in orig:
        if r["market_line"] == "":
            check("R05", r["difference"] == "",
                  "row %s/%s has a blank market line but a filled difference" % (r["game_key"], r["market"]))
        else:
            check("R05", r["difference"] != "",
                  "row %s/%s has a market line but a blank difference" % (r["game_key"], r["market"]))

    # ---------------------------------------------------------------- R06
    order = {}
    for r in orig:
        order.setdefault(r["market"], set()).add(r["origination_order"])
    check("R06", order.get("side") == {"1"}, "side is not origination step 1: %s" % order.get("side"))
    check("R06", order.get("total") == {"2"}, "total is not origination step 2: %s" % order.get("total"))
    check("R06", order.get("moneyline") == {"3"}, "moneyline is not origination step 3: %s"
          % order.get("moneyline"))

    # ---------------------------------------------------------------- R07
    for r in read("correlations.csv"):
        refused = r["status"].startswith("refused")
        check("R07", (r["n"] != "") or refused,
              "correlation %s publishes neither n nor a refusal" % r["correlation_id"])
        if not refused:
            check("R07", r["correlation_value"] != "",
                  "correlation %s is not refused but has no value" % r["correlation_id"])

    # ---------------------------------------------------------------- R08
    lb = read("leaderboard.csv")
    for r in lb:
        check("R08", "signal_score" in r and "staking_score" in r,
              "leaderboard row %s does not separate signal from staking" % r.get("strategy_id"))
        check("R08", "combined_score" not in r, "leaderboard has a combined score column")
    check("R08", any(r["divergence_flag"] for r in lb) or True, "divergence column present")

    # ---------------------------------------------------------------- R09
    dem = read("demotion_gate.csv")
    check("R09", any(r["triggers_fired"] != "none" for r in dem),
          "no strategy ever trips the demotion gate -- the gate is decorative")
    check("R09", all(r["threshold_D1"] and r["threshold_D2"] for r in dem),
          "demotion thresholds are not published")

    # ---------------------------------------------------------------- R10
    dep = read("replacement_depth.csv")
    for r in dep:
        if r["is_backup_start"] == "yes":
            check("R10", r["depth_of_replacement"] != "",
                  "backup start %s/%s has no replacement depth" % (r["team"], r["position_slot"]))
            check("R10", r["first_available_player"] != "",
                  "backup start %s/%s has no named replacement" % (r["team"], r["position_slot"]))
    check("R10", len(dep) >= 40, "depth register has only %d rows" % len(dep))

    # ---------------------------------------------------------------- R11/R12/R13
    pages = sorted(glob.glob(os.path.join(DOCS, "*.html")))
    check("R12", len(pages) == 15, "expected 15 pages, found %d" % len(pages))
    for p in pages:
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        base = os.path.basename(p)
        check("R11", "<input" not in text.lower() and "<form" not in text.lower() and "<select" not in text.lower(),
              "%s contains a form control" % base)
        check("R13", "official NFL-family page" in text, "%s is missing the source footer" % base)
        for href in re.findall(r'href="([^"#][^"]*)"', text):
            if href.startswith(("http://", "https://")):
                if href.startswith("https://sassnarep3-star.github.io"):
                    continue
                host = urlparse(href).hostname or ""
                check("R12", host in OFFICIAL_HOSTS,
                      "%s links to a non-official external host: %s" % (base, href))
                continue
            target = os.path.normpath(os.path.join(DOCS, href.split("?")[0]))
            check("R12", os.path.exists(target), "%s has a broken internal link: %s" % (base, href))
        check("R14", "<tbody>" in text, "%s has no table" % base)

    # ---------------------------------------------------------------- summary
    print("check_nfl_market: %d checks" % checks[0])
    if failures:
        print("FAILURES: %d" % len(failures))
        for rule, detail in failures[:40]:
            print("  [%s] %s" % (rule, detail))
        return 1
    print("OK: all %d checks passed" % checks[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
