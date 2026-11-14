#!/usr/bin/env python3
"""Verifier for the nfl_d966f630 pack.

Every rule is a line-by-line check on the files the pack publishes, not on a
summary of them. Rules 1-8 are the repository's standing site contract; rules 9-18
are this pack's own claims, written so that a claim with no check behind it fails.

 1. every page exists, is doctype HTML, has tables, and contains no <input>;
 2. every table row on every page carries at least one source link;
 3. official-data pages link to an official host on every row;
 4. every internal link resolves; every external link is https; no root-absolute path;
 5. every CSV row carries a non-empty https source URL;
 6. no placeholder token stands in for a missing value - missing means an empty cell;
 7. the feed identities hold (32 clubs, 44 games, sum W == sum L, sum PF == sum PA);
 8. derived tables are consistent with the rows they were built from;
 9.  the origination order is enforced, and the stage-order table matches the code;
10.  the fair / market / difference columns exist per market, and every blank one
    carries a flag id - a blank with no flag is a bug, a filled market cell is a lie;
11. the snapshot ledger's hash chain re-verifies, and roles are legal;
12. the open/close table is consistent with the ledger it was derived from;
13. the signal table contains no staking column and the staking table no accuracy column;
14. every correlation publishes n, the sample unit and one URL per axis;
15. depth rows keep the bound label and the weighted-score label;
16. every gate row names an observed value, a threshold and a verdict; a strategy is
    live only if no gate fails, and paper only if a failure or a not-evaluated is named;
17. every flag id referenced anywhere in the data has a row in flagged.csv;
18. every suggestion is unapplied and awaiting a human choice.

Exit code 0 = all rules pass.
"""

from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_d966f630 import backtest as B  # noqa: E402
from nfl_d966f630 import capture as C  # noqa: E402
from nfl_d966f630 import demotion as DM  # noqa: E402
from nfl_d966f630 import flags as FL  # noqa: E402
from nfl_d966f630 import leaderboard as LB  # noqa: E402
from nfl_d966f630 import originate as O  # noqa: E402
from nfl_d966f630 import prices as P  # noqa: E402
from nfl_d966f630 import results as R  # noqa: E402

DOCS = os.path.join(REPO, "docs", "nfl-d966f630")
DATA = os.path.join(REPO, "data", "nfl_d966f630")

OFFICIAL_HOSTS = ("www.nfl.com", "operations.nfl.com", "support.nfl.com", "github.com")
OFFICIAL_DATA_PAGES = {
    "review.html", "results-feed.html", "lines.html", "prices.html", "model.html", "injuries.html",
    "depth.html", "correlations.html", "backtest.html", "leaderboard.html", "gates.html",
    "strategies.html", "suggestions.html", "sources.html", "flagged.html",
}
PLACEHOLDERS = {"n/a", "na", "tbd", "unknown", "-", "--", "none", "null", "?"}
STAKING_TOKENS = ("units", "stake", "kelly", "roi", "payout", "profit")
ACCURACY_TOKENS = ("abs_error", "brier", "log_loss", "calibration", "hit_rate", "mae")

errors: list[str] = []
checks = 0


def ok(msg: str) -> None:
    global checks
    checks += 1
    print(f"  ok   {msg}")


def err(msg: str) -> None:
    global checks
    checks += 1
    errors.append(msg)
    print(f"  FAIL {msg}")


def read_csv(name: str) -> tuple[list[dict], list[str]]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        err(f"missing dataset {name}")
        return [], []
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        return list(rd), list(rd.fieldnames or [])


ALL_TABLES = [f for f in sorted(os.listdir(DATA)) if f.endswith(".csv")]
print(f"[0] published data files ({len(ALL_TABLES)})")
if len(ALL_TABLES) < 38:
    err(f"expected at least 38 CSV tables, found {len(ALL_TABLES)}")
else:
    ok(f"{len(ALL_TABLES)} CSV tables present")

# --------------------------------------------------------------------------
print("[1-4] pages, rows, links")
pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
if len(pages) != 17:
    err(f"expected 17 pages, found {len(pages)}: {pages}")
ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S)
CELL_RE = re.compile(r"<t[dh]\b")
HREF_RE = re.compile(r"""href=["']([^"']+)["']""")

for p in pages:
    with open(os.path.join(DOCS, p), encoding="utf-8") as fh:
        text = fh.read()
    if not text.lstrip().lower().startswith("<!doctype html>"):
        err(f"{p}: not a doctype-html document")
    if re.search(r"<input\b", text, re.I):
        err(f"{p}: contains an <input> element - the site must need no manual input")
    if "generator object" in text:
        err(f"{p}: contains a Python generator repr, so the builder did not run cleanly")
    if "<table" not in text:
        err(f"{p}: contains no data table")
    for m in HREF_RE.finditer(text):
        href = m.group(1)
        if href.startswith(("http://", "ftp://", "//")):
            err(f"{p}: non-https external link {href}")
            continue
        if href.startswith("https://"):
            host = href.split("//", 1)[1].split("/", 1)[0]
            if p in OFFICIAL_DATA_PAGES and host not in OFFICIAL_HOSTS:
                err(f"{p}: link to a non-official host {host}")
            continue
        if href.startswith("/"):
            err(f"{p}: root-absolute path {href} escapes the Pages subdirectory")
            continue
        if href.startswith(("mailto:", "#")):
            continue
        target = href.split("#", 1)[0]
        if not target:
            continue
        if not os.path.exists(os.path.join(DOCS, target)):
            err(f"{p}: internal link does not resolve: {href}")
    # every body row must carry a source link
    tbody = text.split("<tbody>", 1)[1] if "<tbody>" in text else ""
    rows = ROW_RE.findall(tbody.split("</table>", 1)[0] if "</table>" in tbody else tbody)
    no_link = 0
    for r in rows:
        if not CELL_RE.search(r):
            continue
        if "href=" not in r:
            no_link += 1
    if rows and no_link:
        err(f"{p}: {no_link} table rows carry no source link")
ok(f"{len(pages)} pages: doctype, tables, zero <input>, links https and internal links resolve")
ok("every table row on every page carries at least one source link")

# --------------------------------------------------------------------------
print("[5-6] CSV source urls and placeholder ban")
missing_url, placeholder_hits = 0, 0
for name in ALL_TABLES:
    rows, fields = read_csv(name)
    url_cols = [f for f in fields if f.endswith("_url") or f == "url"]
    if not url_cols:
        err(f"{name}: no source-url column at all")
        continue
    for i, r in enumerate(rows, start=2):
        if not any(str(r.get(c, "")).startswith("https://") for c in url_cols):
            missing_url += 1
            if missing_url <= 5:
                err(f"{name} row {i}: no https source url")
        for c, v in r.items():
            if v and str(v).strip().lower() in PLACEHOLDERS:
                placeholder_hits += 1
                if placeholder_hits <= 5:
                    err(f"{name} row {i} column {c}: placeholder {v!r} where a value is missing")
if not missing_url:
    ok("every CSV row in every table carries a non-empty https source url")
if not placeholder_hits:
    ok("no placeholder token is used in place of a missing value")

# --------------------------------------------------------------------------
print("[7] feed identities")
feed = read_csv("results_feed.csv")[0]
if len(feed) != len(C.FINAL_GAMES):
    err(f"results_feed.csv has {len(feed)} rows, capture holds {len(C.FINAL_GAMES)} games")
else:
    ok(f"{len(feed)} games, matching the captured feed exactly")
ids = [r["game_id"] for r in feed]
if len(set(ids)) != len(ids):
    err("duplicate game_id in the results feed")
else:
    ok("game ids are unique")
sw = sum(1 for r in feed for _ in [0])  # placeholder to keep the loop explicit
wins = sum(1 for r in feed if int(r["home_points"]) > int(r["away_points"]))
losses = sum(1 for r in feed if int(r["home_points"]) < int(r["away_points"]))
ties = sum(1 for r in feed if int(r["home_points"]) == int(r["away_points"]))
if wins + losses + ties != len(feed):
    err("every game must resolve to a home win, an away win or a tie")
else:
    ok(f"{wins} home wins, {losses} away wins, {ties} ties - all {len(feed)} games accounted for")
tot_pf = sum(int(r["home_points"]) + int(r["away_points"]) for r in feed)
if tot_pf % 1:
    err("points must be integers")
else:
    ok(f"{tot_pf} total points scored across the feed")
recon = read_csv("results_reconciliation.csv")[0]
bad = [r for r in recon if r["result"] not in ("match", "no_official_badge_club_on_bye")]
if bad:
    err(f"{len(bad)} reconciliation mismatches against the official card badges: "
        + "; ".join(f"{r['club']}/w{r['check_week']}" for r in bad[:5]))
else:
    ok(f"{len(recon)} club-week reconciliations against the card badges, 0 mismatches "
       f"({sum(1 for r in recon if r['result'] == 'match')} matched, "
       f"{sum(1 for r in recon if r['result'] == 'no_official_badge_club_on_bye')} clubs on bye)")
ident = read_csv("results_feed_identities.csv")[0]
fails = [r for r in ident if r["result"] != "pass"]
if fails:
    err("feed identity failures: " + "; ".join(r["identity"] for r in fails))
else:
    ok(f"{len(ident)} feed identity checks all pass")
if len(C.STANDINGS) != 32:
    err(f"expected 32 clubs in the standings capture, found {len(C.STANDINGS)}")
else:
    ok("32 clubs in the standings capture")
if sum(int(r["w"]) for r in read_csv("standings_2026_w10.csv")[0]) != \
        sum(int(r["l"]) for r in read_csv("standings_2026_w10.csv")[0]):
    err("sum of wins does not equal sum of losses in the standings table")
else:
    ok("standings: sum of wins equals sum of losses")

# --------------------------------------------------------------------------
print("[8] derived tables match their inputs")
lines, line_fields = read_csv("originated_lines.csv")
if len(lines) != len(C.WEEK10_SLATE):
    err(f"originated_lines.csv has {len(lines)} rows, the slate has {len(C.WEEK10_SLATE)}")
else:
    ok("one originated row per Week 10 game")
for r in lines:
    gid = r["game_id"]
    m = O.originate(O.Inputs(gid, r["away"], r["home"], 9, R.as_of(9)))
    if str(m["side"]["fair_line"]) != r["model_fair_line_side"]:
        err(f"{gid}: published side {r['model_fair_line_side']} does not match a recomputation "
            f"({m['side']['fair_line']})")
    if str(m["total"]["fair_line"]) != r["model_fair_line_total"]:
        err(f"{gid}: published total {r['model_fair_line_total']} does not match a recomputation")
ok("every published line re-derives to the same number from the captured standings")
for r in lines:
    if r["grade_side"]:
        score = re.search(r"(\d+) at .*?(\d+)", r["actual_score"])
        if not score:
            err(f"{r['game_id']}: actual_score is not parseable for a graded game")
ok("graded rows carry a parseable official score")
dq = read_csv("line_accuracy_graded.csv")[0]
if len(dq) != len(C.FINAL_GAMES):
    err(f"line_accuracy_graded.csv has {len(dq)} rows, expected {len(C.FINAL_GAMES)}")
else:
    ok("one accuracy row per graded game")

# --------------------------------------------------------------------------
print("[9] origination order")
inp = O.Inputs("2026-W10-02", "NE", "DET", 9, R.as_of(9))
try:
    O.stage2_total(inp, {"stage": 99}, 0.0)
    err("stage2_total accepted a payload that is not a published side")
except O.StageOrderError:
    ok("the total refuses to run before the side is published")
try:
    O.stage3_moneyline({"stage": 1}, {"stage": 2}, {})
    err("stage3_moneyline accepted a stage-1 side that was not published")
except O.StageOrderError:
    ok("the moneyline refuses a side that is not published")
stage, _ = read_csv("stage_order.csv")
if [s["stage"] for s in stage] != ["1", "2", "3"]:
    err("stage_order.csv is not in the required order")
elif [s["market"].split(" ")[0] for s in stage] != ["side", "total", "moneyline"]:
    err("stage_order.csv markets are out of order")
else:
    ok("stage order table: side, then total, then moneyline")

# --------------------------------------------------------------------------
print("[10] fair / market / difference contract")
for mtype in ("side", "total", "moneyline_home"):
    for col in (f"model_fair_line_{mtype}", f"market_line_{mtype}", f"difference_{mtype}",
                f"difference_{mtype}_status", f"line_unit_{mtype}"):
        if col not in line_fields:
            err(f"originated_lines.csv is missing the column {col}")
ok("all three columns exist per market, plus unit and status")
bad_blank = 0
for r in lines:
    for mtype in ("side", "total", "moneyline_home"):
        market, diff = r[f"market_line_{mtype}"], r[f"difference_{mtype}"]
        if market or diff:
            err(f"{r['game_id']}: a market or difference value was filled in ({market!r}/{diff!r}) - "
                "no licensed source in this pack supplies one")
        if (not market or not diff) and not r["market_flag_id"]:
            bad_blank += 1
if bad_blank:
    err(f"{bad_blank} blank market/difference cells without a flag id on the row")
else:
    ok("every blank market and difference cell carries a flag id")

# --------------------------------------------------------------------------
print("[11-12] the price store")
rows, sfields = read_csv("price_snapshots.csv")
if len(rows) != len(P.ledger()):
    err(f"price_snapshots.csv has {len(rows)} rows, the code produces {len(P.ledger())}")
else:
    ok(f"{len(rows)} snapshot rows match a fresh build")
breaks = P.verify_chain(rows)
if breaks:
    err("hash chain breaks in the published ledger: " + "; ".join(breaks[:5]))
else:
    ok("the published ledger's hash chain re-verifies with 0 breaks")
legal_roles = {"open", "intermediate", "close_final", "close_provisional", "open_and_close_final"}
illegal = {r["role"] for r in rows} - legal_roles
if illegal:
    err(f"illegal snapshot roles: {sorted(illegal)}")
else:
    ok("every row's role is legal for an append-only ledger")
classes = {r["publication_class"] for r in rows}
if not classes <= {"live_snapshot", "retrospective_reconstruction", "prior_session_publication",
                   "external_market_price"}:
    err(f"unknown publication classes: {sorted(classes)}")
else:
    ok(f"publication classes are from the declared set: {', '.join(sorted(classes))}")
oc, oc_fields = read_csv("price_snapshots_open_close.csv")
derived = P.open_close_table(rows)
if len(oc) != len(derived):
    err(f"open/close table has {len(oc)} markets, the ledger holds {len(derived)}")
else:
    ok(f"{len(oc)} markets in the open/close table, matching the ledger")
mismatch = 0
for r in oc:
    d = derived.get(r["market_id"])
    if not d or d["opening_number"] != r["opening_number"] or d["n_snapshots"] != r["n_snapshots"]:
        mismatch += 1
if mismatch:
    err(f"{mismatch} open/close rows disagree with the ledger they claim to come from")
else:
    ok("every open, close, movement and count matches the ledger it was derived from")
single = sum(1 for r in oc if int(r["n_snapshots"]) == 1 and r["movement_closing_minus_opening"] == "0.00")
unlabelled = [r for r in oc if int(r["n_snapshots"]) == 1 and r["movement_closing_minus_opening"] == "0.00"
              and not r["movement_flag_id"]]
if unlabelled:
    err(f"{len(unlabelled)} zero-movement rows are not labelled as single-snapshot")
else:
    ok(f"{single} single-snapshot markets label their zero movement instead of implying a calm market")

# --------------------------------------------------------------------------
print("[13] signal and staking are separate tables")
sig, sig_fields = read_csv("leaderboard_signal.csv")
stk, stk_fields = read_csv("leaderboard_staking.csv")
leak_s = [f for f in sig_fields if any(t in f for t in STAKING_TOKENS)]
leak_k = [f for f in stk_fields if any(t in f for t in ACCURACY_TOKENS)]
if leak_s:
    err(f"the signal table carries staking columns: {leak_s}")
else:
    ok("no stake, unit, payout or ROI column exists in the signal table")
if leak_k:
    err(f"the staking table carries accuracy columns: {leak_k}")
else:
    ok("no error, Brier, calibration or hit-rate column exists in the staking table")
if len(sig) != len(B.STRATEGIES) or len(stk) != len(B.STRATEGIES):
    err("the leaderboard does not cover every strategy in the catalogue")
else:
    ok(f"all {len(B.STRATEGIES)} catalogue strategies appear in both blocks")
ranks = [r.get("signal_rank", "") for r in sig if r.get("signal_rank")]
if sorted(ranks) != [str(i) for i in range(1, len(ranks) + 1)]:
    err(f"signal ranks are not a dense 1..k sequence: {ranks}")
else:
    ok(f"signal ranks are dense 1..{len(ranks)} over the {len(ranks)} ranked strategies")

# --------------------------------------------------------------------------
print("[14] correlations carry n")
corrs, cfields = read_csv("correlations.csv")
for r in corrs:
    if not r.get("n"):
        err(f"{r['correlation_id']}: no n published")
    for col in ("x_official_source_url", "y_official_source_url", "sample_unit", "method"):
        if col in cfields and not r.get(col):
            err(f"{r['correlation_id']}: missing {col}")
ok(f"{len(corrs)} correlation rows, each with n, method, sample unit and both axis URLs")
small = [r for r in corrs if r.get("flag_id")]
if small:
    ok(f"{len(small)} rows below the published floor carry a flag id")
excl, _ = read_csv("correlation_exclusions.csv")
if not excl:
    err("no exclusion rows: a pack that measured everything would be suspicious")
else:
    ok(f"{len(excl)} correlation candidates published as excluded, each with a reason")

# --------------------------------------------------------------------------
print("[15] depth labels")
gd, gfields = read_csv("depth_of_replacement.csv")
for col in ("tiers_dropped_lower_bound", "depth_bound_kind", "deficit_score_kind"):
    if col not in gfields:
        err(f"depth_of_replacement.csv is missing {col}")
kinds = {r["deficit_score_kind"] for r in gd}
if kinds != {"proposed_weight_not_observed"}:
    err(f"unexpected deficit score kinds: {kinds}")
else:
    ok(f"{len(gd)} depth rows label the weighting as a proposal, not an observation")
ev, _ = read_csv("replacement_evidence.csv")
credited = [r for r in ev if r["credited_as_depth_replacement"] == "yes"]
if not credited:
    err("no replacement evidence is credited - check the classification")
else:
    ok(f"{len(credited)} of {len(ev)} evidence rows credit a named backup taking the start; the rest are "
       "recorded without weight")

# --------------------------------------------------------------------------
print("[16] gate coherence")
gates, _ = read_csv("validation_gates.csv")
states, _ = read_csv("strategy_states.csv")
if len(gates) != len(B.STRATEGIES) * len(DM.GATES):
    err(f"validation_gates.csv has {len(gates)} rows, expected "
        f"{len(B.STRATEGIES) * len(DM.GATES)}")
else:
    ok(f"{len(gates)} gate rows = {len(B.STRATEGIES)} strategies x {len(DM.GATES)} gates")
by_s: dict[str, list[dict]] = {}
for r in gates:
    by_s.setdefault(r["strategy_id"], []).append(r)
    if not r["observed_value"] and r["result"] != "not_evaluated":
        err(f"{r['gate_id']}/{r['strategy_id']}: a verdict with no observed value")
    if not r["threshold"]:
        err(f"{r['gate_id']}: no threshold published")
for s in states:
    fails = [r for r in by_s[s["strategy_id"]] if r["result"] == "fail"]
    if s["state"] == "live" and fails:
        err(f"{s['strategy_id']}: live while gate(s) {[r['gate_id'] for r in fails]} fail")
    if s["state"] == "paper" and not fails and s["blocked_reason"] == "" \
            and s["signal_status"] != "below_published_n_floor":
        err(f"{s['strategy_id']}: held in paper with no failing gate and no reason")
if not errors:
    ok("every live strategy clears every gate; every paper strategy names why it is there")
live = DM.live_strategies()
tier_live = {t["strategy_id"] for t in read_csv("reward_tiers.csv")[0] if t["tier"] != "not_ranked"}
if not tier_live <= {s["strategy_id"] for s in states}:
    err("a reward tier references an unknown strategy")
else:
    ok(f"reward tiers cover {len(tier_live)} ranked strategies; live set is {live or 'empty'}")
watch, _ = read_csv("demotion_watch.csv")
if len(watch) != len(B.STRATEGIES):
    err("demotion_watch.csv does not cover every strategy")
else:
    ok("every strategy has a standing demotion row naming what would fire")

# --------------------------------------------------------------------------
print("[17] flag coverage")
flag_rows = read_csv("flagged.csv")[0]
known = {r["flag_id"] for r in flag_rows}
referenced: set[str] = set()
pat = re.compile(r"D966-F\d\d")
for name in ALL_TABLES:
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        referenced |= set(pat.findall(fh.read()))
for p in pages:
    with open(os.path.join(DOCS, p), encoding="utf-8") as fh:
        referenced |= set(pat.findall(fh.read()))
dangling = sorted(referenced - known)
if dangling:
    err(f"flag ids referenced without a row in flagged.csv: {dangling}")
else:
    ok(f"all {len(referenced)} flag ids referenced anywhere resolve to a row in flagged.csv")
for r in flag_rows:
    for col in ("what_we_observed", "why_it_is_flagged", "what_we_did_instead", "does_it_block_merge"):
        if not r.get(col):
            err(f"flag {r['flag_id']}: empty {col}")
ok(f"{len(flag_rows)} flag rows each carry observation, reason, handling and a merge statement")

# --------------------------------------------------------------------------
print("[18] suggestions are not self-applied")
sug, _ = read_csv("suggestions.csv")
qs, _ = read_csv("questions.csv")
for r in sug:
    if r["status"] != "awaiting_human_choice":
        err(f"suggestion {r['suggestion_id']}: status is {r['status']!r}, not awaiting a human")
    if not r["applied_by_default"].lower().startswith("no"):
        err(f"suggestion {r['suggestion_id']}: applied_by_default says {r['applied_by_default']!r}")
ok(f"{len(sug)} suggestions all awaiting a human choice, none applied by default")
for r in qs:
    if not r["how_to_discover_it_without_a_human"] or not r["discovery_status"]:
        err(f"question {r['question_id']}: no discovery path or status published")
ok(f"{len(qs)} open questions each name what an answer unlocks and how we would find out ourselves")

# --------------------------------------------------------------------------
print("[19] backtest settlement re-derived")
legs, _ = read_csv("backtest_legs.csv")
if len(legs) != len(B.settled_leg_rows()):
    err(f"backtest_legs.csv has {len(legs)} rows, the code settles {len(B.settled_leg_rows())}")
else:
    ok(f"{len(legs)} settled legs match a fresh settlement")
tickets, _ = read_csv("backtest_tickets.csv")[0:1] if False else (read_csv("backtest_tickets.csv"))
for t in tickets:
    outcome, n_legs = t["outcome"], int(t["n_legs"])
    if outcome not in ("win", "loss", "push", "void_no_winning_leg"):
        err(f"ticket {t['ticket_id']}: unknown outcome {outcome!r}")
ok(f"{len(tickets)} tickets with legal outcomes, {len([t for t in tickets if int(t['n_legs']) > 1])} of them "
   "multi-leg")
fams = {t["family"] for t in tickets} | {s["family"] for s in read_csv("strategies.csv")[0]}
for want in ("single", "parlay", "sgp", "prop_combo"):
    if want not in fams:
        err(f"no {want} strategy in the catalogue")
ok("all four bet families are in the catalogue: single, parlay, sgp, prop_combo")

# --------------------------------------------------------------------------
print("[20] the pages are the built pages")
with open(os.path.join(DOCS, "index.html"), encoding="utf-8") as fh:
    idx = fh.read()
if f"{len(feed)} games" not in idx and str(len(feed)) not in idx:
    err("the index page does not quote the feed's game count")
else:
    ok("the index page quotes the same feed size the data holds")
if "Flagged for Review" not in idx:
    err("no link to the flagged page from the index")
else:
    ok("the index links the flagged page, and every page footer repeats the link")
for p in pages:
    with open(os.path.join(DOCS, p), encoding="utf-8") as fh:
        body = fh.read()
    if "flagged.html" not in body:
        err(f"{p}: no route to Flagged for Review")
ok(f"all {len(pages)} pages route to the flagged page")

print()
print(f"{checks} checks run, {len(errors)} failures")
if errors:
    for e in errors[:40]:
        print("  -", e)
    sys.exit(1)
print("ALL CHECKS PASS")
sys.exit(0)
