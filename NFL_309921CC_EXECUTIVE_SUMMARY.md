# NFL 309921CC — Executive Summary

**Session:** `arena/309921cc-own6` · **Capture date:** 2026-11-13 (UTC) · **Live site:** `docs/nfl-309921cc/`
**Scope:** all 32 clubs, NFL Week 10 of the 2026 season · **Rebuild:** `python3 scripts/build_nfl_309921cc.py`
**Verifier:** `python3 scripts/check_nfl_309921cc.py` · **Tests:** `python3 -m unittest discover -s tests -p "test_nfl_309921cc.py"`

---

## 1. One-sentence summary

The framework, the league-level statistics that can be computed from official data, and the
verified Week 10 picture are real and published; every betting-performance number is blank, is
flagged, and will stay blank until licensed data exists — because a fabricated benchmark is the
easiest way to mistake luck for skill.

## 2. What we did

| Deliverable | Where | Size |
|---|---|---|
| Verified official capture (11 pages read directly) | `data/nfl_309921cc/sources.csv` | 11 sources, each with a verbatim excerpt and a stated boundary |
| 2026 standings, all 32 clubs | `data/nfl_309921cc/standings_2026_w10.csv` | 32 rows |
| Week 10 slate, byes and the one final result | `week10_slate.csv`, `week10_byes.csv` | 14 games, 4 byes |
| Official Week 10 injury report | `week10_injuries.csv`, `week10_injury_load.csv` | 326 rows + 28-club load table |
| Club depth charts (1st → 4th string, offense and defense) | `depth_charts.csv` | 45 position slots, 2 clubs |
| Starter-versus-backup deficiency map | `depth_deficiency.csv`, `depth_unlisted_designations.csv` | 45 + 4 rows |
| Decision ledger (knowns, unknowns, how to discover) | `decision_ledger.csv` | 16 questions |
| Site-improvement suggestions (review only) | `suggestions.csv` | 14 suggestions, all `pending_human_choice` |
| Strategy catalog (singles, parlays, prop combos) | `strategies.csv` | 10 preregistered, 0 qualified |
| Validation gates | `validation_gates.csv` | 12 gates: 4 open, 8 blocked |
| **Measured** correlations and luck index | `correlations.csv`, `luck_index.csv` | 8 correlations + 32-row luck decomposition |
| Originated fair spread and total | `originated_lines.csv` | 13 scheduled games modelled |
| Leaderboard and rewards | `leaderboard_tiers.csv`, `leaderboard_entries.csv` | 4 tiers, 10 entries, 0 rewards awarded |
| Repository review | `repo_findings.csv` | 15 verified irregularities |
| Flagged for review | `flagged.csv` | 17 blank or unresolved items |
| Zero-input dashboard | `docs/nfl-309921cc/` | 16 pages, 695 sourced table rows, 0 `<input>` elements |

## 3. Verified numbers (read from official pages, not modelled)

- **Standings identities hold exactly:** sum(W) = sum(L) = 136, sum(T) = 2, sum(PF) = sum(PA) = 6,291.
  Every non-tie game yields exactly one win and one loss, and every point scored is a point allowed.
  8 divisions of 4 clubs, 32 unique abbreviations.
- **League scoring rate:** 22.9599 points per team-game, i.e. **45.9197 points per game** across both teams.
- **Week 10:** 14 games, 28 clubs, 4 byes (CHI 7-2, DEN 7-2, PHI 2-7, TB 3-6).
- **One game already final at capture:** Commanders 24, Giants 21, Thursday 12 November.
- **Injury report:** 326 rows across the 28 clubs playing this week; 25 rows carry an
  Out/Questionable designation. The other Game Status cells were still blank because the report
  is populated progressively through the week.

## 4. Measured statistics (computed here from the verified standings)

Unlike the other NFL packs in this repository, these values are **measured**, not blank, because
they can be computed from official data alone. They describe the league; they are not betting edges.

| ID | Relationship | Method | r | p (two-sided) | 95% CI |
|---|---|---|---|---|---|
| NFL3-COR-01 | Points for per game ~ win % | Pearson | 0.6984 | 8.8e-06 | 0.4622 to 0.8420 |
| NFL3-COR-02 | Points against per game ~ win % | Pearson | −0.6636 | 3.5e-05 | −0.8221 to −0.4097 |
| NFL3-COR-03 | Net points per game ~ win % | Pearson | 0.8781 | 4.1e-11 | 0.7630 to 0.9392 |
| NFL3-COR-04 | Points for per game ~ points against per game | Pearson | −0.2041 | 0.2626 | −0.5160 to 0.1557 |
| NFL3-COR-05 | Net points per game ~ win % | Spearman | 0.8658 | 1.6e-10 | 0.7407 to 0.9329 |
| NFL3-COR-06 | Home win % ~ overall win % | Pearson | 0.8863 | 1.5e-11 | 0.7781 to 0.9434 |
| NFL3-COR-07 | Division win % ~ overall win % | Pearson | 0.3084 | 0.0859 | −0.0451 to 0.5933 |
| NFL3-COR-08 | Points for per game ~ net points per game | Pearson | 0.8019 | 3.4e-08 | 0.6291 to 0.8992 |

Two of the eight are **not** distinguishable from zero at the 5% level — COR-04 and COR-07. That
result is published as it came out; it is not suppressed.

**Luck decomposition.** Regressing win percentage on net points per game across the 32 official
rows: intercept 0.4990, slope 0.033574 per net point per game (SE 0.003341, t = 10.0498, df = 30,
p = 4.1e-11), R² = 0.7710, residual SD 0.1165 win percentage. The residual is the part of a club's
record its scoring does not explain. The largest positive residuals (won more than scoring implies)
are Denver (+0.234) and Cleveland (+0.187); the largest negative are Tampa Bay (−0.255) and
Jacksonville (−0.202). Gate G10 applies the same estimator to a strategy, but on slate-clustered
data, and requires the interval to exclude zero before any reward.

## 5. Originated lines

Thirteen scheduled games carry our own fair spread and total, computed only from verified
points-for and points-against per game. One game was already final and is deliberately **not**
modelled.

- Model mean total **46.3785** vs the league's own **45.9197** points per game → difference
  **+0.4588** points. That difference is the model's self-consistency check.
- Model mean absolute home spread: **3.7808** points.
- Declared parameters, not fitted: home-field advantage 0.00 points, shrinkage 1.00 (flag NFL3-F06).
- **No moneyline probability is published.** Converting a point margin into a win probability needs
  a victory-margin distribution, and no official page in this pack supplies one (flag NFL3-F08).
- **No market spread, market total or closing-line value is published** (flag NFL3-F10).

## 6. Injury and depth-deficiency tracking

Both offense and defense are tracked the same way. Club depth charts give 1st-to-4th string
ordering; the official injury report gives Out/Questionable designations; the two are joined so
that the **active string** (the shallowest listed string not ruled Out) and the **next available
backup** are resolved for every position slot.

Findings where the deficiency score is above zero:

| Club | Unit | Slot | 1st string | Active | Next available | Score |
|---|---|---|---|---|---|---|
| NE | Offense | WR | A.J. Brown (Questionable) | 1st | 2nd — Efton Chism III | 0.35 |
| NE | Offense | **LG** | Ben Brown (**Out**) | 2nd — Walter Rouse (**Questionable**) | **none listed** | **0.85** |
| NE | Offense | RB | Rhamondre Stevenson (Questionable) | 1st | **3rd** — Corey Kiner (2nd string Henderson **Out**) | 0.35 |
| NE | Defense | CB | Carlton Davis III (**Out**) | 2nd — Channing Canada | none listed | 0.65 |
| DET | Offense | C | Cade Mays (**Out**) | 2nd — Juice Scruggs | none listed | 0.65 |
| DET | Defense | CB | D.J. Reed (**Out**) | 2nd — Rock Ya-Sin | 3rd — Khalil Dorsey | 0.65 |

Two caveats are carried on every row: both clubs label their own chart **unofficial**, and the
deficiency weights are **proposed, not observed** (flags NFL3-F04 and NFL3-F07). Four designated
players do not appear on their own club's chart at all — Reggie Gilliam (NE), Greg Van Roten (NE),
Kerby Joseph (DET, ruled Out) and Kevin Byard (NE), whose chart entry reads "Kevin Byard III". The
name prefix match is reported as a candidate only; this pack does not assert the two names are the
same person.

## 7. Suggestions (review only — nothing has been implemented)

Fourteen suggestions are published, each with the current repository state, the decision problem it
solves, two or three option paths, a recommended path, prerequisites, effort and reversibility.
Every one is `pending_human_choice`. The highest-impact ones:

- **NFL3-SUG-12** — put the rights question first, before any further numeric capture.
- **NFL3-SUG-03** — repoint the 71 citations of a URL that now returns a 404.
- **NFL3-SUG-02** — name one canonical NFL pack and mark the others as archived provenance.
- **NFL3-SUG-13** — make the source checker probe HTTP status, not just link shape.

## 8. Repository review — irregularities found

Fifteen findings, each with evidence and a link. The four that change what should happen next:

1. **NFL3-RF-14 (High) — rights.** NFL.com Terms §1.3 permits individual non-commercial
   informational use and prohibits systematic retrieval to compile a database without express prior
   written consent. This repository is, by construction, a compiled database of official tables.
   The question applies to the whole repository, not to one pack, and is unanswered.
2. **NFL3-RF-03 (High) — a dead source URL cited 71 times.** `https://www.nfl.com/official-nfl-rules/`
   returned the official NFL 404 page on 2026-11-13. It is cited by 20+ files, including live
   published pages under `docs/nfl/`.
3. **NFL3-RF-08 (High) — the standings lag a completed game.** The Thursday result is published as
   final, but the standings table still shows both clubs with pre-game records.
4. **NFL3-RF-13 (High) — checkers validate link shape, not liveness.** No existing checker fetches
   the external URL, which is how 71 dead citations reached publication.

5. **NFL3-RF-15 (Medium) — the shared coverage tool has no NFL publisher.** `scripts/source_coverage.py`
   declares a publisher allowlist that contains no NFL or NFL-club domain, so rebuilding the coverage
   artifacts classifies 655 of this pack's 693 NFL-sourced rows as `secondary_reference_only`. The
   label is a policy gap in the shared tool, not missing evidence in this pack.

Also logged: the NBA-only root redirect, four competing NFL packs, the subscription-terms page
cited as the general terms, an unreadable injury-policy PDF, proposed thresholds published in value
columns, standings columns the page's own legend does not define, team-stats tables that rendered
without readable headers, two open PRs editing the same generated inventories, and a ~194 KB
coordination file whose live task board is buried.

## 9. What is deliberately blank

Market prices, closing lines, closing-line value, moneyline probabilities, every measured
dependence between two betting legs, and every strategy performance statistic. The ledger holds
**0 graded selections**, so **0 of 10 strategies qualify** and **no leaderboard reward has been
awarded**. Rewards are non-monetary by design: research standing and publication priority only.

## 10. Limits

Statistical validation reduces uncertainty; it does not remove luck. The correlations and the luck
index describe the 2026 season through Week 9 as published on 2026-11-13; they are not forecasts and
not betting edges. Content is published for individual non-commercial informational review under the
[NFL.com Terms and Conditions](https://www.nfl.com/legal/terms/). No wager, no picks service, no
profitability claim, and no monetary reward.
