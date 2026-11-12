# NFL Labs — Executive Summary (2026-11-12, session `arena/efebf74f-own6`)

**Decision:** Publish the NFL research framework, requirements inventory, decision-readiness ledger, suggestions review section, line-origination hypotheses, injury/depth-deficiency model, and verification registry as **design and method only**. **Do not publish a current NFL line, correlation estimate, profitable strategy, or reward winner.** No authorized NFL gambling-use data feed is configured, and no candidate has passed the ten validation gates. Luck cannot be eliminated; the protocol reduces false discoveries. Nothing here is betting advice.

**This summary is verified line-by-line.** Every row-level claim in the linked tables carries an official `https` source; unverified empirical values are blank and flagged. Manual review links are provided. See `data/nfl/sources.csv` for the full registry and `audit/NFL_AUDIT.md` for the line-by-line check.

## What is delivered (additive, does not replace NBA/rental work)

- **Live NFL dashboard:** `docs/nfl/index.html` → live at https://sassnarep3-star.github.io/Own6/nfl/ (legacy `main:/docs` Pages builder). Clean, simple, dashboard-style landing with category cards and status chips. Build: `python3 scripts/build_nfl.py` · Check: `python3 scripts/check_nfl.py`.
- **Requirements inventory:** `data/nfl/requirements.csv` (R01–R18) organized by Governance / Site & UX / NFL Analytics / Executive / Verification. Each requirement is traceable to a file and a flag.
- **Decision framework:** `data/nfl/decision_questions.csv` (Q01–Q10) listing the question that must be answered, what we have, what we lack, current answer status (blank/unverified/open), and how missing information can be discovered without hallucination.
- **Suggestions review section:** `data/nfl/suggestions.csv` (S01–S12) + `docs/nfl/suggestions.html` — a dedicated, reviewable table of high-impact site/decision improvements. Every suggestion is `needs review` and explicitly `not implemented` until the owner selects a path.
- **Line-origination pack:** `data/nfl/origin_strategies.csv` (N01–N10: 3 singles, 3 player props, 2 prop combos, 2 parlays, 1 meta CLV) + `research/NFL_SIGNALS.md`. Each strategy is a frozen hypothesis with its own-line method, correlation pair, and gate set. ROI/CLV are blank.
- **Validation & luck control:** `data/nfl/validation_gates.csv` (G01–G10) + `research/NFL_VALIDATION.md` — rights/provenance → chronology → sample/precision → calibration → ROI → comparable CLV → multiplicity → dependence → ledger. Leaderboard (`data/nfl/leaderboard.csv`) ranks only **all-gate qualifiers** by the lower bound of slate-clustered holdout ROI; rewards are non-monetary research priority only. Current state: empty.
- **Injury & depth-deficiency tracking:** `data/nfl/injury_tracking.csv` + `data/nfl/depth_model.csv` + `research/NFL_INJURY_DEPTH.md` + `docs/nfl/injuries.html` + `docs/nfl/depth.html`. The system is designed to ingest the timestamped official injury report (Practice / Game Status / Inactive at 90 min), map each position's 1st/2nd/3rd/4th-string depth, and compute a per-unit deficiency score (e.g., `1 − starter_snaps/expected`). Until a licensed depth feed is captured, all deficiency values remain blank and flagged.
- **Sources & flagged items:** `data/nfl/sources.csv` (S-NFL-01 … S-NFL-24) and `data/nfl/flagged.csv` (F-NFL-01 … F-NFL-12) with severity, remediation, and official links. Every published page renders them.

## Key findings (verified status, not profitability)

- **Rights blocker (F-NFL-01).** [NFL Terms](https://www.nfl.com/terms/) restrict reuse; no authorized gambling-use license is on file. The [official injury-report policy PDF](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf) and public [league injury page](https://www.nfl.com/injuries/league/2024/reg17) describe *reporting obligations*, not a data license. All market prices therefore stay blank. [NFL standings](https://www.nfl.com/standings/) and the [schedule](https://www.nfl.com/schedule/) are official reference pages for table identity, not performance evidence.
- **Ledger is empty by design (G04, F-NFL-06).** With zero authorized observations, gate sample floors (≥200 holdout bets, ≥60 slate clusters) cannot be met. The leaderboard is therefore empty, exactly as the [NIST confidence-limit guidance](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) and [Bonferroni](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm) logic demand.
- **Injury data is timestamped, not static.** The policy states Practice Reports are “updated on a continual basis” and every reportable injury — causing missed games, missed practices, or limited participation — must be listed even if the player takes all reps. [2017 policy PDF](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf). A single snapshot without hashes is insufficient; see `data/nfl/injury_tracking.csv`.
- **Depth deficiency is design-only until depth-feed licensed.** The model defines per-unit deficiency (OL, DL, secondary, QB, WR, RB, TE, K) and flags 2nd/3rd/4th-string starts, but without an official depth chart feed, all scores are blank (F-NFL-04). See `data/nfl/depth_model.csv`.
- **Correlations are blank until measured.** Same-game home vs away points, margin vs total, cross-game slate effects, QB-WR stacks, RB carry splits, OL-vs-QB efficiency, secondary-vs-WR production, and pressure interactions are all hypothesized, not measured (F-NFL-05). Method: training-only paired residuals, retain zeros, slate-clustered CI, joint sample required — per [SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) and [bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html). No `r` value is published.
- **No fabricated odds or payouts.** American ↔ implied conversion follows [DraftKings odds formulas](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB); parlay payout is multiplicative but that is **not** a joint-probability model ([parlay calculator](https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator)); spread pushes void ([spread rules](https://sportsbook.draftkings.com/help/how-to-bet-spread)); totals are defined per [over/under](https://sportsbook.draftkings.com/help/how-to-bet-over-under). No current price is stored.

## Decision-readiness snapshot (questions / informations / answers)

| Area | Have | Missing | Status |
|---|---|---|---|
| Rights & licensed feed | Terms text, policy PDF, landing pages | Written gambling-use license, API spec, hashes | **Blank — do not decide to publish prices** |
| Injury & depth | Policy fields + design model | Dated PDFs + depth-chart snapshots + hashes | **Blank — do not price depth** |
| Line origination | Methodology (pace×efficiency, shrunk rates, copula) | Licensed stat feed + fitted coefficients | **Method only** |
| Signals & leaderboard | Frozen hypotheses N01–N10 + gate charter | Holdout ≥200 bets / 60 slates, CLV archive | **Empty — rank none** |
| Correlations | Pair list + training-only method | Residual ledger + joint samples + CIs | **Blank** |

Full ledger: `data/nfl/decision_questions.csv` → `docs/nfl/questions.html`. Each missing-info row includes a concrete discovery suggestion (e.g., “request Sportradar/Genius quote and record license ID before scraping”).

## Suggestions — how to improve decision making (review-only)

Twelve reviewable proposals (S01–S12) sit in `docs/nfl/suggestions.html`. Highlights: (1) requirements traceability table, (2) decision-readiness chips on every page, (3) per-unit deficiency badges, (4) own-line calculator showing **formulas not prices**, (5) correlation explorer with clustered CIs, (6) validation-gate progress board, (7) leaderboard rewards charter, (8) sticky Flagged link, (9) source-coverage counter, (10) weekly ingestion design (no scraping), (11) quantitative depth deficiency score, (12) parlay-safety explainer. All are labeled proposal-only; none are implemented until the owner chooses a path in `COORDINATION.md`.

## What remains unverified (published on Flagged for Review)

F-NFL-01 rights/feed · F-NFL-02 market prices · F-NFL-03 live injury snapshots · F-NFL-04 depth scores · F-NFL-05 correlations · F-NFL-06 leaderboard/ROI · F-NFL-07 CLV · F-NFL-08 parlay joint probs · F-NFL-09 prop settlement · F-NFL-10 suggestion auto-apply · F-NFL-11 cross-sport provenance · F-NFL-12 stale live labels. These block empirical qualification, **not** publication of the research framework.

## Reproduce

```sh
python -m pip install -r requirements-empirical.txt
python3 scripts/build_nfl.py
python3 scripts/check_nfl.py
python3 tools/release_gate.py
python -m pytest -q tests  # existing NBA/lab gates still pass; NFL pack adds no fabricated-data assertions
```

Artifacts are committed. The empty ledger deterministically reports `no qualifier`; fixtures stay in `tests/` and never enter published tables.

## No betting advice

Analytics research only. No wagers, stakes, picks, payouts, or profitability claims. Luck can be reduced by preregistration, proper scoring, clustered uncertainty, and multiplicity control — it cannot be eliminated. For problem gambling in Alberta (Calgary), verified 2026-11-03 on the official AGLC site: AGLC Self-Exclusion Program **1-844-468-8034** ([aglc.ca](https://aglc.ca/gaming/common-gaming-questions)), Alberta Health Services Addiction Helpline **1-866-332-2322**.

---

## Line-by-line verification note

This summary was written from files that themselves passed `scripts/check_nfl.py`: every CSV has an official `https` URL per row; every HTML table row carries an `official source` link; blanks carry the `— unverified / blank` badge. See `audit/NFL_AUDIT.md` for the per-file row count and the link-check result.
