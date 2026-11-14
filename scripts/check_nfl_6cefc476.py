#!/usr/bin/env python3
"""Line-by-line verification gate for the 6cefc476 pack.

Enforces, fail-closed:
  1.  Every data row carries an https source link to an official host.
  2.  A value cell is populated only when the row has a source; otherwise blank+flag.
  3.  Origination order: side (wave 1) -> total (wave 2) -> moneyline (wave 3).
  4.  model_fair_line, market_line and line_difference are separate columns;
      market/difference blank rows carry the price flag.
  5.  Price snapshots: every originated market has one open and one close row.
  6.  Results feed rows are verified with official game-page links.
  7.  Correlations publish n; measured rows carry coefficients, blocked rows blank.
  8.  Replacement depth publishes depth strings only with a depth-chart source.
  9.  Leaderboard keeps signal and staking separate; staking can never escalate.
 10.  A demotion gate with LIVE -> PAPER actions exists.
 11.  Site pages have zero input elements; every table row has an https link;
      internal links resolve.

Usage:  python3 scripts/check_nfl_6cefc476.py
"""
from __future__ import annotations

import csv
import html.parser
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl_6cefc476"
SITE = ROOT / "docs" / "nfl-6cefc476"

OFFICIAL_HOSTS = {
    "nfl.com", "www.nfl.com", "operations.nfl.com",
    "www.patriots.com", "patriots.com",
    "www.detroitlions.com", "detroitlions.com",
    "www.seahawks.com", "seahawks.com",
    "www.vikings.com", "vikings.com",
    "www.baltimoreravens.com", "baltimoreravens.com",
    "www.itl.nist.gov", "itl.nist.gov",
    "github.com", "api.github.com",
}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def official(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host in OFFICIAL_HOSTS or host.endswith(".nfl.com") or host.endswith(".patriots.com") \
        or host.endswith(".detroitlions.com") or host.endswith(".seahawks.com") \
        or host.endswith(".vikings.com") or host.endswith(".baltimoreravens.com")


def check_row_source(name: str, rows: list[dict], source_cols: list[str], value_cols: list[str]) -> None:
    for i, r in enumerate(rows, start=2):
        urls = [r.get(c, "").strip() for c in source_cols if r.get(c, "").strip()]
        if not urls:
            fail(f"{name}:{i}: row {r.get('market_id') or r.get('game_id') or r.get('correlation_id') or r.get('event_id') or r.get('q_id') or r.get('sug_id') or r.get('flag_id') or r.get('source_id') or r.get('rf_id') or r.get('strategy_id') or i} has no source link")
            continue
        for u in urls:
            if not u.startswith("https://"):
                fail(f"{name}:{i}: source link not https: {u}")
            elif not official(u):
                fail(f"{name}:{i}: source link not on an official host: {u}")
        populated = any((r.get(c) or "").strip() for c in value_cols)
        if populated and not urls:
            fail(f"{name}:{i}: populated values without a source link")


def main() -> int:
    # ---------- originated lines: order, columns, blanks -----------
    orig = load("originated_lines.csv")
    cols = list(orig[0])
    for col in ("model_fair_line", "market_line", "line_difference"):
        if col not in cols:
            fail(f"originated_lines.csv: missing required column {col}")
    by_market = {}
    for i, r in enumerate(orig, start=2):
        by_market.setdefault(r["game_id"], {})[r["market_type"]] = r
        if r["model_fair_line"].strip() == "":
            fail(f"originated_lines.csv:{i}: model_fair_line blank")
        if r["market_line"].strip() != "":
            fail(f"originated_lines.csv:{i}: market_line must stay blank without a licensed source")
        if r["line_difference"].strip() != "":
            fail(f"originated_lines.csv:{i}: line_difference must stay blank without a market line")
        if "N6F-04" not in r.get("flag_id", ""):
            fail(f"originated_lines.csv:{i}: blank market/difference rows must carry flag N6F-04")
    for gid, markets in by_market.items():
        for mt in ("side_spread", "total", "moneyline"):
            if mt not in markets:
                fail(f"originated_lines.csv: game {gid} missing market {mt}")
        if len(markets) == 3:
            o_side = int(markets["side_spread"]["origination_order"])
            o_tot = int(markets["total"]["origination_order"])
            o_ml = int(markets["moneyline"]["origination_order"])
            if not (o_side < o_tot < o_ml):
                fail(f"originated_lines.csv: game {gid} violates side->total->moneyline order")
            if markets["side_spread"]["origination_wave"] != "1" or \
               markets["total"]["origination_wave"] != "2" or \
               markets["moneyline"]["origination_wave"] != "3":
                fail(f"originated_lines.csv: game {gid} has wrong wave labels")
    waves = [int(r["origination_wave"]) for r in orig]
    if waves != sorted(waves):
        fail("originated_lines.csv: rows are not grouped in wave order (side wave, total wave, ML wave)")

    # ---------- price snapshots: open + close per market -----------
    prices = load("price_snapshots.csv")
    snap: dict[str, dict[str, dict]] = {}
    for i, r in enumerate(prices, start=2):
        snap.setdefault(r["market_id"], {})[r["snapshot_type"]] = r
        if r["snapshot_type"] == "open":
            if not r["our_number"].strip():
                fail(f"price_snapshots.csv:{i}: open snapshot missing our_number")
            if r["market_number"].strip():
                fail(f"price_snapshots.csv:{i}: market_number must stay blank without a licensed source")
        elif r["snapshot_type"] == "close":
            if r["verification_status"] not in {"pending_close", "computed_from_verified_inputs"}:
                fail(f"price_snapshots.csv:{i}: close row has unexpected status {r['verification_status']}")
        else:
            fail(f"price_snapshots.csv:{i}: unknown snapshot_type {r['snapshot_type']}")
    for r in orig:
        mid = r["market_id"]
        if mid not in snap:
            fail(f"price_snapshots.csv: market {mid} has no snapshot rows")
        else:
            if "open" not in snap[mid]:
                fail(f"price_snapshots.csv: market {mid} missing open snapshot")
            if "close" not in snap[mid]:
                fail(f"price_snapshots.csv: market {mid} missing close snapshot")

    # ---------- results feed ----------
    results = load("results_feed.csv")
    for i, r in enumerate(results, start=2):
        if r["verification_status"] != "verified_direct":
            fail(f"results_feed.csv:{i}: not verified_direct")
        if not r["source_url"].startswith("https://www.nfl.com/games/"):
            fail(f"results_feed.csv:{i}: expected official nfl.com game page link")
        if not r["away_score"].strip() or not r["home_score"].strip():
            fail(f"results_feed.csv:{i}: final score blank")

    # ---------- backtest ----------
    bt = load("backtest_grades.csv")
    for i, r in enumerate(bt, start=2):
        if "in-sample" not in r["in_sample_warning"] and "NOT a pre-kickoff" not in r["in_sample_warning"]:
            fail(f"backtest_grades.csv:{i}: missing retrospective warning")
        if r["status"] != "retrospective_derivation":
            fail(f"backtest_grades.csv:{i}: status must be retrospective_derivation")

    # ---------- correlations ----------
    corrs = load("correlations.csv")
    for i, r in enumerate(corrs, start=2):
        if not r["n"].strip():
            fail(f"correlations.csv:{i}: n must be published with every value")
        measured = r["status"].startswith("measured")
        if measured and not r["coefficient"].strip():
            fail(f"correlations.csv:{i}: measured row missing coefficient")
        if not measured and r["coefficient"].strip():
            fail(f"correlations.csv:{i}: blocked row must leave the coefficient blank")

    # ---------- replacement depth ----------
    depth = load("replacement_depth.csv")
    for i, r in enumerate(depth, start=2):
        has_depth = r["depth_of_replacement"].strip() != ""
        has_src = r["depth_source_url"].strip() != ""
        if has_depth and not has_src:
            fail(f"replacement_depth.csv:{i}: depth string published without a depth-chart source")
        if not has_depth and r["replacement_string"].strip():
            fail(f"replacement_depth.csv:{i}: replacement_string present but depth_of_replacement blank")
        if has_depth:
            if not official(r["depth_source_url"]) or not official(r["injury_source_url"]):
                fail(f"replacement_depth.csv:{i}: depth/injury source not official")
            if not r["injured_string"].strip():
                fail(f"replacement_depth.csv:{i}: depth published without the injured player's string")
        else:
            if "N6F-08" not in r["flag_id"] and "N6F-05" not in r["flag_id"] and "N6F-06" not in r["flag_id"] and "N6F-07" not in r["flag_id"]:
                fail(f"replacement_depth.csv:{i}: blank depth must carry a flag")

    # ---------- leaderboard ----------
    board = load("leaderboard.csv")
    for i, r in enumerate(board, start=2):
        if r["staking_can_escalate_signal"] != "no":
            fail(f"leaderboard.csv:{i}: staking_can_escalate_signal must be 'no'")
        for col in ("signal_cover_rate", "signal_status", "staking_roi", "staking_status"):
            if col not in r:
                fail(f"leaderboard.csv:{i}: missing separation column {col}")
        if r["staking_roi"].strip() and r["staking_status"].startswith("blocked"):
            fail(f"leaderboard.csv:{i}: blocked staking must leave ROI blank")
        if r["eligibility"] != "unqualified" and r["signal_status"] != "qualified":
            fail(f"leaderboard.csv:{i}: eligibility inconsistent with signal status")

    # ---------- gates ----------
    vg = load("validation_gates.csv")
    if len(vg) < 10:
        fail("validation_gates.csv: expected at least 10 gates")
    dg = load("demotion_gate.csv")
    if not any("LIVE -> PAPER" in r["action"] or "LIVE → PAPER" in r["action"] for r in dg):
        fail("demotion_gate.csv: no rule with a LIVE -> PAPER action")

    # ---------- questions / suggestions / flags / sources ----------
    for name, cols_val in (
        ("decision_questions.csv", ["question", "discovery_protocol"]),
        ("suggestions.csv", ["suggestion", "recommended_path"]),
        ("flagged.csv", ["item", "detail"]),
        ("sources.csv", ["title", "verbatim_excerpt"]),
        ("repo_findings.csv", ["finding", "evidence"]),
    ):
        rows = load(name)
        if not rows:
            fail(f"{name}: empty")
        check_row_source(name, rows, ["source_url", "url"],
                         cols_val if name != "sources.csv" else ["verbatim_excerpt"])
    for r in load("suggestions.csv"):
        if r["status"] != "pending_human_choice":
            fail(f"suggestions.csv: {r['sug_id']} must remain pending_human_choice")

    # ---------- site ----------
    class Page(html.parser.HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.links: list[str] = []
            self.forms = 0
            self.inputs = 0
            self.h1 = 0
            self.in_tbody = False
            self.in_row = False
            self.row_links: list[str] = []
            self.rows: list[list[str]] = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if attrs.get("href"):
                self.links.append(attrs["href"])
            if attrs.get("src"):
                self.links.append(attrs["src"])
            if tag in {"form"}:
                self.forms += 1
            if tag in {"input", "textarea", "select", "button"}:
                self.inputs += 1
            if tag == "h1":
                self.h1 += 1
            if tag == "tbody":
                self.in_tbody = True
            elif tag == "tr" and self.in_tbody:
                self.in_row = True
                self.row_links = []
            elif tag == "a" and self.in_row and attrs.get("href"):
                self.row_links.append(attrs["href"])

        def handle_endtag(self, tag):
            if tag == "tr" and self.in_row:
                self.rows.append(self.row_links)
                self.in_row = False
            elif tag == "tbody":
                self.in_tbody = False

    pages = sorted(SITE.glob("*.html"))
    if len(pages) < 14:
        fail(f"site: expected 14 pages, found {len(pages)}")
    for path in pages:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        p = Page()
        p.feed(text)
        if p.forms or p.inputs:
            fail(f"{rel}: input elements found ({p.forms} forms, {p.inputs} controls) — site must be zero-input")
        if p.h1 != 1:
            fail(f"{rel}: expected exactly one h1, found {p.h1}")
        for row_links in p.rows:
            if not any(urlparse(u).scheme == "https" for u in row_links):
                fail(f"{rel}: table body row without an https source link")
        for u in p.links:
            parsed = urlparse(u)
            if parsed.scheme in {"https", "mailto"}:
                continue
            if parsed.scheme or parsed.netloc or u.startswith("//"):
                fail(f"{rel}: insecure or unsupported link {u}")
                continue
            if not parsed.path:
                continue
            if parsed.path.startswith("/"):
                fail(f"{rel}: root-absolute link {u}")
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                fail(f"{rel}: broken internal link {u}")

    print(f"check_nfl_6cefc476: {len(errors)} issue(s) across data and site")
    for e in errors:
        print("FAIL", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
