# NFL Own-Line Market Desk — Executive Summary

**Session:** `arena/33ee4854-own6` · **Capture date:** 2026-11-14 (UTC) · **Base commit:** `36c6f84`
**Live site:** https://sassnarep3-star.github.io/Own6/docs/nfl-market/
**Data pack:** `data/nfl_market/` (21 CSVs) · **Code:** `src/nfl_market/` · **Gates:** `scripts/check_nfl_market.py` (971 checks)

---

## 1. The one paragraph

This pack originates its own NFL numbers, keeps a full opening/closing price-snapshot store for
every market it originates, grades itself against a verified results feed, and reports **signal
quality and staking outcome as two separate scores** so a lucky staking run cannot disguise a
broken signal. It is built to fail closed, and on this data it does fail closed: **no strategy is
live, none may be, and the originated side model went 28–44.** The single most important finding is
negative and structural — **the NFL publishes no odds or line page**, so there is no official market
line, no difference column, and no measurable edge. Every column that depends on a price ships
blank with an explicit status rather than a guess.

## 2. What was asked for, what exists, and what it cannot do

| Requirement | Status | Artefact | Honest limit |
|---|---|---|---|
| Price-snapshot store: opening **and** closing numbers for every originated market | Built, row-complete | `price_snapshots.csv` (216 rows), `docs/nfl-market/snapshots.html` | Every price cell is blank. `https://www.nfl.com/odds/` is the NFL 404 page. |
| Verified results feed so backtests and ROI can be computed *at all* | Done | `results.csv` (137 games), one official week-URL per row | Scores only — no box scores, no drive data, no player stats. |
| Originate **side → total → moneyline** | Done | `originated_markets.csv` (42 rows, `origination_order` 1/2/3) | Moneyline inherits every error of the side; it is last for that reason. |
| Fair line, market line, difference as **separate columns** | Done | `originated_markets.csv` | Market line and difference blank by rule, not by omission. |
| Separate **signal** from **staking** on the leaderboard | Done | `leaderboard.csv`, `docs/nfl-market/leaderboard.html` | Ranked on signal only; a `divergence_flag` names every disagreement. |
| Track the **depth of the replacement**, not the fact of one | Done for 2 clubs | `replacement_depth.csv` (45 slots) | Only NE and DET depth charts were captured; 30 clubs are absent, not guessed. |
| Correlations only from officially sourced numbers, **with n** | Done | `correlations.csv` (8 rows) | 3 requested correlations are **refused**, not estimated. |
| **Demotion gate** that sends a live strategy back to paper | Done | `demotion_gate.csv`, `docs/nfl-market/demotion.html` | Not yet exercised by a live strategy, because none is live. |
| Suggestions section to review before implementing | Done, nothing applied | `suggestions.csv` (8 option sets, all `pending_human_choice`) | Every row awaits an owner decision. |
| Questions / knowns / unknowns / discovery protocol | Done | `decision_ledger.csv` (12 questions) | 5 need an owner choice; 7 need data or time. |

## 3. The findings that change a decision

1. **There is no official price.** NFL.com serves a 404 at `/odds/`. Therefore the market-line and
   difference columns cannot be filled without breaking the project's own official-source rule. This
   is flag `NM-F01` and decision `DQ-01`. **It gates every other market conclusion.**
2. **The side model is worse than a coin flip.** Walking forward over weeks 5–9 it went **28–44**
   (hit rate 0.3889, one-sided p vs a fair coin 0.978). This is published on the front page, not
   buried. It is flag `NM-F02` and decision `DQ-05`.
3. **ROI is now computable and the results are weak.** Singles: total 39–33 (ROI +0.034 at a declared
   flat −110), moneyline 44–27 (no ROI — no price exists), side 28–44 (ROI −0.258). Parlays are worse
   than independence predicts, because same-game legs are **negatively** correlated (`r = −0.181`,
   `n = 72`).
4. **The leaderboard can now catch the failure it was built to catch.** `single_total` ranks with a
   *positive* staking score but a *weak* signal score, and the table flags exactly that:
   `positive_staking_masks_weak_signal`. That is the mechanism requested, working on real data.
5. **Everything is in-sample.** No forward sample exists, so gate G09 is closed and **6 of 10 gates
   are closed**. A backtest is not a track record.
6. **Depth is measured as a distance, not a flag.** Of 45 captured depth slots, 4 starters are ruled
   Out. The deepest replacement forced is 2nd string. The NE running-back room is the sharpest case:
   Stevenson (Q) 1st, Henderson (**Out**) 2nd, so if Stevenson is scratched the club goes to **3rd
   string Corey Kiner**. Six depth-chart players are ruled Out by the official injury report — the
   exact rows a line should move on.

## 4. How the verification works

Every published number is one of three things, and the site labels which:

- **Transcribed** from an official NFL-family page read on 2026-11-14 — listed with its URL in
  `sources.csv` (9 sources) and linked per row.
- **Computed** from those transcriptions by `src/nfl_market` — reproducible by re-running
  `scripts/build_nfl_market.py`.
- **Blank** — an explicit, published refusal with a status string. Never an inference.

`scripts/check_nfl_market.py` enforces this with 971 machine checks: every row carries an official
HTTPS source, no URL points outside the official host allowlist, every blank price has a status,
the difference column is blank exactly where the market line is blank, the origination order is
side→total→moneyline, every correlation publishes `n` or a refusal, signal and staking never merge
into one column, the demotion gate actually fires, the site has zero form controls, and every
internal link resolves. 34 regression tests lock the same invariants, including a reconciliation
that the standings' points-for/against equals the sum over the captured games.

## 5. What a reader should do with this

In this order:

1. **Read `flagged.html`** — 11 items, each with the source link needed to review it.
2. **Read `decision-ledger.html`** — 12 questions split into what we know, what we do not, and how to
   find out. Five need an owner choice.
3. **Decide S-08 first** (is a licensed price feed ever acceptable?). Nothing else about measuring an
   edge can move until that is answered.
4. **Then S-01** (is the side model fixable or dead?) and **S-03** (lock the forward-bet definition
   before any forward bet is recorded).
5. **Do not bet anything.** No strategy is live, no edge has been measured, and the site says so.

## 6. Repository irregularities flagged (not fixed here)

Recorded in `repo_findings.csv` and published at `repo-review.html`:

- Five NFL packs already coexist (`data/nfl`, `nfl_3b81013c`, `nfl_origination`, `nfl_wk`,
  `nfl_309921cc`) with **overlapping subject matter and different numbers for the same Week 10
  games**. A reader cannot tell which is current. This pack is namespaced `nfl_market` and linked
  from the root index, but the duplication itself is unresolved.
- Three separate CSVs describe the same Week 10 slate. Only this pack's rows were re-verified today.
- Five PRs were open at claim time; merging them later would put contradictory tables on one site.
- The assurance/coverage inventories were **not** regenerated by this session.

## 7. Cross-session coordination

Claimed in `COORDINATION.md` under session `arena/33ee4854-own6` (tasks M0–M15) and pushed **before**
any data work. All file paths are disjoint from every prior and concurrent NFL scope: this session
owns only `data/nfl_market/`, `docs/nfl-market/`, `src/nfl_market/`, `research/nfl_market/`, three
`scripts/`, one `tests/` file and one workflow. Shared files (`docs/index.html`, `README.md`,
`COORDINATION.md`) received **additive** insertions only.

**Platform note:** the brief specifies `session-<id>/<task>` branches. Arena fixes this session to
`arena/33ee4854-own6` and forbids creating or switching branches, so scopes are kept non-overlapping
by file path instead. Logged as a deviation in `COORDINATION.md`.
