# NFL Decision Desk — Method

Companion to `NFL_DECISION_DESK_EXECUTIVE_SUMMARY.md`. The summary states what was found; this file states how
each number is produced, so that a reviewer can disagree with a step instead of having to trust a result.
Everything here is implemented in `src/nfl_desk/` and executed by `scripts/build_nfl_desk.py`.

## 1. Data model and provenance contract

Three layers, with a hard direction of flow:

```
data/nfl_desk/*.csv            input registers   what an official page said, one row per claim
  └─ raw/injury_report_week10_read.psv   verbatim transcription of the Week 10 injury report (pipe-separated)
data/nfl_desk/derived/*.csv    derived registers what the code computes from the inputs (regenerated, never edited)
docs/nfl-decision-desk/*.html  published views  rendered from the derived registers, byte-reproducible
```

Every register row carries `source_url` (the page read for *that row*) and `read_date`. Rows come in three
provenance states and no others:

| `verification_status` | meaning |
| --- | --- |
| `verified_direct_official_read` | transcribed from an official page in this session |
| `computed_from_verified_register` / `computed_from_official_read` | arithmetic on rows in the first category |
| `link_only_not_reverified` / `methodology_reference` | cited for shape or method; contributes no numeric input |

A blank cell is a value: it means *no confirmed value exists*, and it is always paired with a flag id on the
flagged register. `n/a` is not used, because "not applicable" and "not available" are different claims; where a
cell genuinely does not apply (a bye club's kickoff time) the cell says so in words, and the checker verifies
that any cell styled `.na` begins with an explicit reason.

## 2. Scoring registers

`standings_2026_thru_w10.csv` (32 clubs, through Week 10) and `standings_2025_final.csv` (32 clubs, final) hold
W-L-T, PF, PA, net, home/road splits, division and conference splits, streak, plus the printed PCT. In-range
assertions run on import:

* `sum(wins) == sum(losses)` and `sum(points_for) == sum(points_against)` — a league ledger must balance.
* `home_w+home_l+home_t + road_w+road_l+road_t == games_played` per club — the venue split cannot invent a game.
* `div ⊆ conf ⊆ overall` by wins and losses.
* `win_pct == (wins + 0.5·ties) / games_played` to three decimals, the convention the standings page prints
  (verified against the page's own legend and its two tied clubs in each season).

The last rule exists because of a real error: the first transcription computed PCT over wins and losses only,
which silently discards ties. Corrected values and the two confirming reads are recorded as `FL-24`, `S-13`
and `S-14`.

## 3. Line origination (`model.py`, `pricing.py`)

Given the verified registers, for a game with home club *h* and away club *a*:

```
base_home = 0.5 · (h.points_per_game + a.points_allowed_per_game)
base_away = 0.5 · (a.points_per_game + h.points_allowed_per_game)
expected_total  = base_home + base_away
expected_margin = base_home − base_away + home_field_points      # 0 here; 0 at a neutral site
points_home ~ Poisson(base_home + hfp/2),  points_away ~ Poisson(base_away − hfp/2)
P(margin = m) = Σ_k P_home(k + m) · P_away(k)                     # exact convolution, truncated at 80 pts, renormalised
P(home win)   = Σ_{m>0} P(m) + ½ · P(0)
```

Publishing the **exact margin distribution** rather than a normal approximation is not cosmetic: it is what
prices a tie. `P(m = 0)` is the push probability on a whole-number spread, and the same distribution yields the
mass at the key numbers 3 and 7 and the one-score window (1–8 points), all published per game. A model that
treats the margin as continuous misprices every push and every key number, which in the NFL is systematic
rather than rare.

Two assumptions are load-bearing, both labelled in-cell rather than hidden in a constant:

1. **Points are Poisson.** A distributional choice, standard for team scoring, and the reason totals are wide of
   a normal model's at the tails.
2. **Home-field advantage = 0 points** on this slate. Not a claim that home advantage is zero — a refusal to
   import a points value this register cannot measure (`MF-21` is blank for exactly that reason). Home clubs are
   67‑69‑1 this season, so the historical ~2.5 points would be an anachronism anyway.

Both are then *varied*: `sensitivity.csv` recomputes all 13 lines at 0.0 / 1.0 / 1.5 / 2.5 home points, and the
favoured side's stability across that grid is a gate result (`DG-12`), not a footnote. Totals are invariant to
the home assumption by construction, which the grid also demonstrates.

`pricing.py` converts between American and decimal odds and computes the break-even win rate (0.523810 at
−110, i.e. 11/21). It is used only for two things here: the break-even hurdle, and the *fair* American price at
each Fréchet bound. No market price is emitted anywhere, because there is no licensed quote to emit.

## 4. Correlation and combo dependence (`correlation.py`)

Club-level associations are measurable from the standings registers, so they are measured rather than asserted:
Pearson *r*, Spearman ρ (average ranks, ties shared), a 4,000-draw percentile bootstrap interval, and a
20,000-replicate permutation *p*-value. The permutation test is the primary inference because club ratings are
not an i.i.d. sample; the interval is reported so a reader can see a near-zero estimate that is *imprecise*
rather than one that is precise and small.

Measured results include the two that matter for pricing: offence versus same-club defence is weak with an
interval spanning zero (`CR-01`), and prior-season net rating carries over at r ≈ 0.50 with R² ≈ 0.25
(`CR-03`) — enough for a weak prior, not enough to price a line from.

The dependence a parlay actually needs (same-game residual correlation between a spread and a team total, or a
QB and a WR) cannot be computed without play-by-play and a joint outcome ledger. Those rows are blank and
flagged, and combos are priced by **Fréchet bounds**: for marginal probabilities *p₁*, *p₂*,

```
max(0, p₁ + p₂ − 1)  ≤  P(both)  ≤  min(p₁, p₂)
```

`frechet_bounds.csv` publishes the independence product alongside the fair price at the floor and at the
ceiling, plus the worst-case overcharge relative to the bounds. The independence figure is labelled as the null
it is (`DG-10` forbids using it as a price). Cross-game legs are treated the same way, since two legs from
different games share scoring environment, weather and slate timing.

## 5. Removing luck (`luck.py`)

Luck is removed by *measuring it*, in three steps:

1. Fit the Pythagorean exponent by grid search on each season's points for/against (2026: 3.370, R² 0.7488;
   2025: 3.045, R² 0.8485) and convert it to an expected-win vector.
2. Compare the residual spread in actual wins with the binomial noise floor implied by the same expectations
   (0.9862 vs 1.3616 wins in 2026; 1.3478 vs 1.9459 in 2025). The observed residual scatter is *smaller* than
   pure chance around the points-based expectation, which bounds any residual-skill signal at 8–10 games to
   roughly nothing. This is published as a measured null, not omitted.
3. Test persistence: 2025 wins-above-expectation against 2026 (r = −0.0077, p = 0.9675, R² = 0.0001). A team
   that got lucky last year is not lucky this year, so any "ride the fluke team" or "fade the unlucky team"
   strategy is refused at registration; strategies that need a luck-signal input are marked as requiring an
   input that does not exist.

Structural controls apply to every strategy regardless: expectation from points rather than record, push mass
priced explicitly, key-number mass published, no results-based feature in any input vector, and one frozen
family of twelve hypotheses with Holm–Bonferroni at α = 0.05 (the family size is fixed before any outcome is
scored, so *p*-hacking by enlarging the family is unavailable).

The sample arithmetic runs the other way too: `required_games_for_edge(edge, sigma)` inverts a two-sided 5% test
at 80% power, giving 125 settled games for a 1-point-per-game edge at margin SD 10 and 14 games at 3 points.
Since the per-game margin SD cannot be verified from a standings page, the answer is published as a grid over
σ ∈ {10, 11, 12, 13} rather than as a single number (`MF-20` stays blank).

## 6. Injuries and depth (`depth.py`)

The Week 10 report is transcribed verbatim to a PSVV (326 rows, all 28 clubs playing that week), then filtered
by a stated inclusion rule: every row designated Out or Questionable, plus every row where the player did not
practise. The excluded rows are not deleted — per-club coverage counts record them, and the checker recomputes
all counts from the raw read, asserts that practice-status counts partition the rows listed, and asserts that
the published subset is *exactly* what the inclusion rule selects.

Each club's players are grouped into unit groups by position (`OFFENCE_QB`, `OFFENCE_SKILL`, `OFFENCE_LINE`,
`DEFENCE_PASS_RUSH`, `DEFENCE_LINEBACKER`, `DEFENCE_SECONDARY`, `SPECIAL_TEAMS`), and each group is scored:

```
deficiency = 3·Out + 2·DNP + 1·Limited                       # ordinal policy weights, printed beside every row
replacement_tier = f(n impaired)                             # 1 backup rep taken / 2nd-string start in play /
                                                               # 3rd-string involvement / 4th-string or depleted
cascading_cluster = yes when ≥2 players in the group are impaired
starter_dependent_unit = yes for QB room, O-line, pass rush, secondary
```

This replaces calibrated-looking multipliers with an explicitly ordinal screen: it ranks which groups are thinnest,
and it does not pretend to know how many points a replacement is worth. The report's `Injuries` column is blank
on most rows, so no effect size is estimable from this read (`FL-03`), and the depth chart's *order* is not in
the report at all, so "who is the second string" remains an open question (`Q-03`). Both facts are on the page
next to the score, not in a footnote.

## 7. Gates, strategies, leaderboard, rewards (`gates.py`, `leaderboard.py`)

Sixteen gates, in two families: **structural** (a strategy cannot be *specified* without satisfying them —
no market input, no results-based features, no independence pricing, push arithmetic present, assumptions varied)
and **evidence** (they can only be satisfied by data over time). States are `PASS`, `FAIL`, `BLOCKED`; a gate is
never promoted from `BLOCKED` to `PASS`, and every non-passing row states what was measured and the artefact that
unlocks it. States are recomputed at build time from the registers, so a gate cannot go stale in prose.

Twelve strategies are preregistered, each with a frozen hypothesis, required versus available versus missing
inputs, and its luck controls. Readiness is the fraction of required inputs that are verified and on disk —
rankable today, and deliberately not a quality signal. Performance is holdout ROI on a frozen snapshot set,
same-line closing value, Brier against de-vigged market probabilities, and a composite skill score; all four are
blank, and all twelve entries sit at `TIER-0`. The four-tier reward ladder and its total-order tie-break
(evidence gates, then readiness, then strategy id) are published before anyone competes, which is the only
version of a reward competition that cannot be reverse-engineered from results.

## 8. Verification ledger (`audit.py`)

The audit compares the prior registers field by field against this read, with one row per (subject, field) and a
disposition from a closed vocabulary. Each disposition determines its own review state, so a row cannot say
"needs review" while being marked verified:

| disposition | state |
| --- | --- |
| `CONFIRMED` | verified — the strings match (or match as numbers, e.g. 0.750 vs 0.75) |
| `CONFIRMED_LABEL_VARIANT` | verified — same claim, different notation (`PM ET` vs `PM EST`, `true` vs `yes`, a compound status cell) |
| `CONFIRMED_NAME_NORMALISED` | verified — matches once Jr./Sr./II/III are normalised |
| `CONFIRMED_VIA_BULLETIN` | verified — an IR or season-ending move that a weekly participation report never prints |
| `SUPERSEDED_RECONCILED` | verified — the prior value was right at its own timestamp; the difference equals the one settled game between the reads |
| `SELF_CHECK_RECOMPUTED` | verified — an invariant of this pack's own registers |
| `DRIFT_STATUS_CHANGED`, `DISAGREES_ACROSS_OFFICIAL_PAGES`, `FORECAST_NOT_A_REPORT`, `JOIN_KEY_MISMATCH`, `NAME_NOT_MATCHED`, `NOT_REVERIFIED_THIS_READ`, `PENDING_GAME_DESIGNATION`, `PROVENANCE_MISMATCH`, `VALUES_DIFFER` | needs review |

Reconciliations are computed, not asserted: a Thursday record difference is only `SUPERSEDED_RECONCILED` when the
delta is exactly one win for the winner or one loss for the loser, and a venue split is compared after
normalising the `'3 - 1 - 0'` spacing the prior register uses. Where two official pages disagree with each other
(the broadcast carrier lists), the desk records the disagreement rather than picking a winner, because nothing
in either page says which is authoritative.

## 9. Publishing discipline

`build_nfl_desk.py` renders 18 pages from the derived registers; `--check` compares against what is committed
and fails on any byte of difference, which is what makes the site auditable rather than hand-written.
`check_nfl_desk.py` then enforces the content contract: every table row carries an allowlisted source link,
`.empty` cells are literally empty and `.na` cells state a reason, header and cell counts match, row counts in
captions match the tbody, no page contains a form control or a script, relative links resolve, blob links point
at files that exist in the repository, and the derived numbers re-derive.

Two source tiers, because they mean different things. `official()` accepts the league, its operations and
support sites, GitHub, and cited methodology references, and is required for every value this pack publishes.
`citable()` additionally accepts a club domain and is used *only* on the two audit pages, where a link is
another pack's own citation being reported rather than a source this pack endorses. Betting, odds and pick
sites are refused in both tiers, so a market number could not sneak in through a source URL.

## 10. Known limits of the method

* A single read per page is a snapshot of one moment; that is the entire content of `DG-04` and it is not fixable
  by prose.
* Poisson points understate the influence of overtime decisions, red-zone usage and pace; both tails are visible
  in the model's regulation-tie mass (0.0484) against the observed tied-game rate (0.0073), which the desk
  publishes as a calibration gap (`FL-16`) instead of adjusting a constant to hide it.
* Season-long scoring rates ignore schedule strength and quarter-level usage; they are a rating, not a
  projection with an opponent-quality term, and no such term is available without play-by-play.
* Correlations here are club-season associations across 32 clubs. They constrain priors; they do not price a
  game.
* Depth scores are ordinal screens over one week's designations, on a page that is revised Wednesday to Friday.

## 11. File map

| path | contents |
| --- | --- |
| `data/nfl_desk/*.csv` | input registers: standings (2 seasons), slate, injury report + coverage, bulletins, sources, requirements, questions, suggestions, flagged, GitHub state |
| `data/nfl_desk/raw/injury_report_week10_read.psv` | verbatim transcription of the Week 10 report, 326 rows |
| `data/nfl_desk/derived/*.csv` | 12 registers regenerated on every build |
| `src/nfl_desk/league.py` | club loading, league facts, rounding convention |
| `src/nfl_desk/model.py` | Poisson convolution, key numbers, push and win probabilities |
| `src/nfl_desk/pricing.py` | American/decimal conversion, break-even, de-vig |
| `src/nfl_desk/correlation.py` | Pearson, Spearman, bootstrap interval, permutation test, Fréchet bounds |
| `src/nfl_desk/luck.py` | Pythagorean fit, residual versus binomial noise, persistence, sample arithmetic |
| `src/nfl_desk/depth.py` | unit grouping, deficiency scoring, cluster alerts |
| `src/nfl_desk/gates.py` | gate definitions, state recomputation, Holm–Bonferroni |
| `src/nfl_desk/leaderboard.py` | strategy registry, readiness ranking, reward tiers |
| `src/nfl_desk/audit.py` | field-by-field verification ledger and repo integrity checks |
| `src/nfl_desk/derive.py` | the single source of truth for every published computed number |
| `scripts/build_nfl_desk.py` | registers → pages, byte-reproducible |
| `scripts/check_nfl_desk.py` | content, sourcing and invariant gate |
| `tests/test_nfl_desk.py` | stdlib unit tests, including the pricing and PCT conventions this pack got wrong once |
