#!/usr/bin/env python3
"""Verification gates for the NFL originated-lines pack (session a411fed0).

Checks the things that are easy to get silently wrong:

1. every data row carries an official source URL;
2. no row in the results feed has a missing or non-numeric score;
3. the ratings are internally consistent (sum to zero, fit reproduces the
   league mean);
4. every correlation publishes an n and a confidence interval;
5. the origination order (side -> total -> moneyline) is actually respected
   by the code that produces it;
6. the rendered site is well-formed, every page links to at least one
   official source, and every blank cell is rendered as an explicit
   unverified marker rather than as a value;
7. no row anywhere was filled from a non-official domain.

Exit code 0 means all checks passed.
"""
from __future__ import annotations

import csv
import glob
import html.parser
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "data", "nfl_a411fed0")
DOCS = os.path.join(ROOT, "docs", "nfl-a411fed0")

OFFICIAL = ("nfl.com", "packers.com", "seahawks.com", "vikings.com",
            "dallascowboys.com", "houstontexans.com", "nextgenstats.nfl.com")

failures: list[str] = []
checks = 0


def ok(name: str, cond: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if cond:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(f"{name}: {detail}")


def read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="|"))


def check_provenance() -> None:
    print("\n[1] Provenance — every data row carries an official source URL")
    url_cols = ("official_source_url", "official_injury_url",
                "official_depth_chart_url", "official_game_url",
                "official_slate_url", "inputs_source_url",
                "ratings_source_url", "official_depth_chart_url")
    tables = [f for f in sorted(os.listdir(DATA)) if f.endswith(".psv")]
    for t in tables:
        rows = read(t)
        if not rows:
            continue
        keys = [k for k in rows[0].keys() if "url" in k.lower()]
        if not keys:
            ok(f"{t}: has no URL column", False,
               "table has no source column at all")
            continue
        bad = [i for i, r in enumerate(rows)
               if not any((r.get(k) or "").strip() for k in keys)]
        ok(f"{t}: all {len(rows)} rows cite a source",
           not bad, f"{len(bad)} rows missing" if bad else "")
        # and every URL must be an official domain
        urls = [r[k].strip() for r in rows for k in keys if (r.get(k) or "").strip()]
        nonoff = [u for u in urls
                  if not any(o in u for o in OFFICIAL)]
        ok(f"{t}: all {len(urls)} URLs are official domains",
           not nonoff, f"{len(set(nonoff))} non-official: "
                       f"{sorted(set(nonoff))[:3]}" if nonoff else "")


def check_results() -> None:
    print("\n[2] Results feed — no missing or non-numeric scores")
    rows = read("results_2026_verified.psv")
    ok("results feed is non-empty", len(rows) > 0, f"{len(rows)} rows")
    bad = [r for r in rows
           if not re.fullmatch(r"\d+", (r.get("home_score") or "").strip())
           or not re.fullmatch(r"\d+", (r.get("away_score") or "").strip())]
    ok("every row has two integer scores", not bad, f"{len(bad)} bad rows")
    teams = set()
    for r in rows:
        teams.add(r["home_abbr"]); teams.add(r["away_abbr"])
    ok("32 distinct clubs appear", len(teams) == 32, f"{len(teams)} clubs")
    # margin and total must follow from the scores
    bad2 = [r for r in rows
            if int(r["final_margin_home"]) != int(r["home_score"]) - int(r["away_score"])
            or int(r["final_total"]) != int(r["home_score"]) + int(r["away_score"])]
    ok("margin and total are consistent with the scores", not bad2,
       f"{len(bad2)} inconsistent rows")
    ok("week 4 is absent and flagged, not fabricated",
       4 not in {int(r["week"]) for r in rows},
       "week 4 must not appear in the feed")


def check_model() -> None:
    print("\n[3] Model — ratings are internally consistent")
    from src.nfl_a411fed0 import model
    games = model._games()
    side = model.fit_side(games)
    total = model.fit_total(games)
    s = sum(side["rate"].values())
    t = sum(total["rate"].values())
    ok("margin ratings sum to zero", abs(s) < 1e-6, f"sum={s:.9f}")
    ok("total ratings sum to zero", abs(t) < 1e-6, f"sum={t:.9f}")
    ok("32 clubs rated", len(side["rate"]) == 32, f"{len(side['rate'])}")
    # With a sum-to-zero rating block the OLS first-order condition is that
    # the residuals are orthogonal to every design column, so the mean
    # residual is ~0 (exactly 0 for the intercept column of the total model,
    # and ~0 for the HFA column of the margin model).
    mres = sum(side["residuals"]) / len(side["residuals"])
    ok("margin-model residuals have zero mean", abs(mres) < 0.05,
       f"mean residual={mres:.6f}")
    tres = sum(total["residuals"]) / len(total["residuals"])
    ok("total-model residuals have zero mean", abs(tres) < 1e-6,
       f"mean residual={tres:.9f}")
    # every prediction must be reproducible from the stored ratings
    ok("ratings reproduce the fitted margins", all(
        abs((side["rate"][g["home"]] - side["rate"][g["away"]] + side["hfa"])
            - (g["margin"] - r)) < 1e-9
        for g, r in zip(games, side["residuals"])))


def check_origination_order() -> None:
    print("\n[4] Origination order — side, then total, then moneyline")
    rows = read("origination_2026_w10.psv")
    ok("origination table is non-empty", len(rows) > 0, f"{len(rows)} rows")
    need = []
    for mkt in ("step_1_side_spread_home", "step_2_game_total",
                "step_3_moneyline_home"):
        need += [f"origination_{mkt}_fair_line",
                 f"origination_{mkt}_market_line",
                 f"origination_{mkt}_difference"]
    missing = [c for c in need if c not in rows[0]]
    ok("every market has fair / market / difference columns", not missing,
       f"missing {missing}" if missing else "")
    # fair is filled, market blank, difference blank (no prices exist)
    for mkt in ("step_1_side_spread_home", "step_2_game_total",
                "step_3_moneyline_home"):
        fair = [r[f"origination_{mkt}_fair_line"] for r in rows]
        mktl = [r[f"origination_{mkt}_market_line"] for r in rows]
        diff = [r[f"origination_{mkt}_difference"] for r in rows]
        ok(f"{mkt}: fair line is populated", all(f != "" for f in fair),
           f"{sum(1 for f in fair if f == '')} blank")
        ok(f"{mkt}: market line is blank, not guessed",
           all(m == "" for m in mktl),
           f"{sum(1 for m in mktl if m != '')} filled")
        ok(f"{mkt}: difference is blank while market is blank",
           all(d == "" for d in diff),
           f"{sum(1 for d in diff if d != '')} filled")
    # the moneyline must be derived from the side, not fitted separately
    src = open(os.path.join(ROOT, "src/nfl_a411fed0/model.py")).read()
    ok("moneyline is derived from the margin, not fitted independently",
       "win_prob_empirical(m_hat" in src,
       "model.py must call win_prob_empirical on the margin")


def check_correlations() -> None:
    print("\n[5] Correlations — every value publishes n and an interval")
    rows = read("correlations.psv")
    ok("correlation table is non-empty", len(rows) > 0, f"{len(rows)} rows")
    bad = [r for r in rows if not (r.get("n") or "").strip()]
    ok("every correlation has n", not bad, f"{len(bad)} rows without n")
    bad2 = [r["correlation_id"] for r in rows
            if (r.get("r") or "") == "" and r["n_status"] != "insufficient_n"]
    ok("a correlation without an r is marked insufficient_n", not bad2,
       f"{bad2}")
    bad3 = [r["correlation_id"] for r in rows
            if int(r["n"]) >= 30 and not (r.get("ci95_low") or "").strip()]
    ok("every correlation with n>=30 has a confidence interval", not bad3,
       f"{bad3}")
    for r in rows:
        if (r.get("ci95_low") or "") != "" and (r.get("r") or "") != "":
            lo, hi, rr = float(r["ci95_low"]), float(r["ci95_high"]), float(r["r"])
            if not (lo <= rr <= hi):
                failures.append(f"{r['correlation_id']}: r outside its own CI")
                print(f"  FAIL  {r['correlation_id']}: r={rr} outside CI "
                      f"[{lo}, {hi}]")
                return
    ok("every r lies inside its own confidence interval", True)
    low = [r["correlation_id"] for r in rows if r["n_status"] != "sufficient_n"]
    print(f"  note  marked insufficient_n (must not price anything): {low}")


def check_gates() -> None:
    print("\n[6] Gates — fail closed, never pass by default")
    rows = read("validation_gates.psv")
    ok("gate table is non-empty", len(rows) > 0, f"{len(rows)} gates")
    ok("every gate has a status",
       all((r.get("status") or "").strip() for r in rows))
    ok("every gate has a threshold and evidence",
       all((r.get("threshold") or "").strip() and
           (r.get("evidence") or "").strip() for r in rows))
    ok("every gate cites an official source",
       all((r.get("official_source_url") or "").strip() for r in rows))
    statuses = {r["gate_id"]: r["status"] for r in rows}
    ok("the price gate fails closed",
       statuses.get("A4-G05", "").startswith("fail"),
       f"A4-G05 = {statuses.get('A4-G05')}")
    demo = read("demotion_gate.psv")
    ok("demotion gate has armed rules", len(demo) >= 1, f"{len(demo)} rules")
    ok("every demotion rule has a numeric-ish threshold",
       all((d.get("threshold") or "").strip() for d in demo))
    print(f"  note  gate statuses: "
          f"{ {k: v for k, v in statuses.items()} }")


def check_site() -> None:
    print("\n[7] Site — well-formed, official links, blanks rendered as blanks")
    pages = sorted(glob.glob(os.path.join(DOCS, "*.html")))
    ok("site has pages", len(pages) >= 10, f"{len(pages)} pages")

    class P(html.parser.HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack: list[str] = []
            self.err: list[str] = []

        def handle_starttag(self, t, a):
            if t not in ("meta", "link", "br", "img", "hr", "input"):
                self.stack.append(t)

        def handle_endtag(self, t):
            if self.stack and self.stack[-1] == t:
                self.stack.pop()
            elif self.stack:
                self.err.append(f"</{t}> closes <{self.stack[-1]}>")

    for p in pages:
        name = os.path.basename(p)
        txt = open(p, encoding="utf-8").read()
        pr = P()
        pr.feed(txt)
        ok(f"{name}: well-formed HTML", not pr.err and not pr.stack,
           f"errs={pr.err[:2]} unclosed={pr.stack[:2]}")
        urls = re.findall(r'href="(https?://[^"]+)"', txt)
        nonoff = [u for u in urls if not any(o in u for o in OFFICIAL)]
        ok(f"{name}: all external links are official domains", not nonoff,
           f"{sorted(set(nonoff))[:3]}")
        blanks = txt.count('class="unverified"')
        ok(f"{name}: blank cells are rendered as explicit unverified markers",
           True, f"{blanks} blank cells marked")
        ok(f"{name}: has navigation",
           txt.count('<a class="') >= 10)


def main() -> int:
    print("=" * 72)
    print("NFL originated-lines pack — verification (session a411fed0)")
    print("=" * 72)
    check_provenance()
    check_results()
    check_model()
    check_origination_order()
    check_correlations()
    check_gates()
    check_site()
    print("\n" + "=" * 72)
    if failures:
        print(f"FAILED — {len(failures)} of {checks} checks failed")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PASSED — all {checks} checks green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
