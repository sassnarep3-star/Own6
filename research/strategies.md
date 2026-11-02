# Signal-generation strategies — NBA line origination (2026-27)

Session `325834c9` · branch `arena/325834c9-own6` · data cut 2026-11-02 (92 games, 15-game slate).

All strategies are **pre-registered** below before their results were examined. Every status is
computed from official-source data only ([sources](#sources)). Everything is research/paper only —
no real wagers. Statuses: `TRACKING` (gates not yet met, collecting evidence),
`NOT DEPLOYED` (failed a gate or sample too small), `VALIDATED` (all gates met; none yet).

## Leaderboard (rewards)

Rewards are **paper units** (research bankroll), paid monthly to the top-ranked strategies:

| Rank | Reward |
|---|---|
| 1st | +20 units and top placement on the site leaderboard |
| 2nd | +10 units |
| 3rd | +5 units |

Ranking score = 2 × (gates fully passed) − (gates failed); untested gates count as neither
(partial passes — e.g. G2 at n=82 — do not count). Starting bankroll 100 units; no allocation
>1 unit/night while a strategy is `TRACKING`; `VALIDATED` strategies may be allocated up to
5 units/night. Rank = score (ties broken by status tier TRACKING > NOT DEPLOYED).

| ID | Strategy | Category | Gates passed (of 6) | Failed / unmet | Status | Score |
|---|---|---|---|---|---|---|
| S-6 | Cross-game 2-leg parlay | Parlays | G3, G4 | G1, G2 untested | TRACKING | 4 |
| S-1 | Rating-margin singles (model spread vs market) | Single bets | G3, G4 | G1 failed (CI crosses 0); G2/G6 partial (n=82) | TRACKING | 3 |
| S-3 | Rest-adjusted (B2B/fatigue) | Single bets | G3, G4 | G2 failed (own-sample null) | NOT DEPLOYED | 3 |
| S-4 | Player-prop single (points) | Player props | G4 | G1, G2 untested | TRACKING | 2 |
| S-5 | Same-game teammate points combo | Player-prop combos | G4 | G3 partial (n=6); G6 unmet | NOT DEPLOYED | 2 |
| S-7 | Open→close line-move signal | Single bets | G4 | G1, G2, G5 untested | TRACKING | 2 |
| S-2 | Model totals vs market total | Single bets | G4 | G2 failed (MAE ≈ baseline) | NOT DEPLOYED | 1 |

S-6's lead reflects measured correlation structure + protocol compliance only — its legs inherit
S-1's failed G1, so it receives no paper allocation until S-1 is validated.

## Strategy specifications

### S-1 Rating-margin singles — `TRACKING` (G2 pass, G1 fail)
- Signal: Own6 model v0.1 (`scripts/model.py`): shrunk venue-adjusted strength (k=8),
  expanding HCA (init 2.5), expanding margin σ (init 12.0); win prob = Φ(margin/σ).
- Bet rule (paper): model favourite when |edge| = P(model fav) − de-vigged market P ≥ 0.03, else pass.
- 2026-11-02 slate: 13/15 model favourites agree with DraftKings; two disagreements
  (WSH@ORL — model WSH +2.3; POR@DEN — model POR +2.3) are recorded as paper leans.
- Gate G1 result: mean log-loss improvement vs expanding home-win baseline = 0.0312,
  95% bootstrap CI [−0.013, 0.073] → **not significant → not validated**.

### S-2 Model totals — `NOT DEPLOYED`
- Signal: (PF_h + PA_a)/2 + (PF_a + PA_h)/2 from shrunk prior scoring means (k=4).
- Result: MAE 16.45 pts vs expanding-mean baseline MAE 16.80 (n=82) — edge +0.35 pts (tie);
  bias +1.10 (slight over-prediction). No deployable edge.

### S-3 Rest-adjusted singles — `NOT DEPLOYED`
- Hypothesis: back-to-backs depress margins (literature: −1.2 to −2.3 pts vs rested,
  see [validation.md](validation.md) citations).
- Own 2026-27 sample: B2B/1-day teams 66-65 (50.4%) vs 2+ days 12-11 (52.2%);
  rest-differential vs home margin r = −0.016 (n=76) → **no usable signal in-sample**;
  consistent with a small true effect below this sample's resolution. Not deployed.

### S-4 Player-prop single (points) — `TRACKING`
- Example (verified lines, event 401909907): Donovan Mitchell line 22.5 (open 23.5),
  official October average 22.7 (ESPN gamelog / NBA.com game leaders). Lean: over by 0.2
  before vig → below the 0.03-equivalent edge threshold → paper lean only, no bet.
- Shai Gilgeous-Alexander line 30.5 (open 29.5): official season PPG **not collected** →
  projection left blank and flagged (no inference rule).

### S-5 Same-game teammate points combo — `NOT DEPLOYED`
- Pair: Mitchell (CLE) + Allen (CLE), 2026-27, r = −0.422 (n=6) — usage-sharing direction,
  but n≪ 60 required. Joint-probability pricing with correlation; not deployable.

### S-6 Cross-game 2-leg parlay — `TRACKING`
- Framework: joint = p₁·p₂ adjusted for measured cross-game correlation
  r = 0.105 (n=357 same-date game-margin pairs) — weak positive dependence, not zero.
- Legs come from S-1, which is not validated → parlays cannot outrank their legs;
  no paper allocation until S-1 clears G1.

### S-7 Open→close line-move signal — `TRACKING`
- All 15 games of the 2026-11-02 slate captured with **open and current** DraftKings lines
  ([data/market_lines_2026-11-02.csv](../data/market_lines_2026-11-02.csv)).
  Largest moves: DET −4.5→−6.5, ATL −7.5→−10.5, SA −15.5→−16.5, MIA@LAL total 239.5→236.5.
  Settlement pending tonight → G5 (CLV) tracking begins here.

## Sources
- NBA.com standings / advanced stats / game cards: https://www.nba.com/standings · https://www.nba.com/stats/teams/advanced · per-game URLs in [data files](../data/)
- ESPN schedule + ESPN core odds feed (DraftKings lines, DraftKings is an NBA co-official sports betting partner — https://pr.nba.com/draftkings-and-fanduel-become-co-official-sports-betting-partners-of-the-nba/): https://www.espn.com/nba/schedule/_/date/20261102 · https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/401909907/competitions/401909907/odds
- ESPN player gamelogs: https://www.espn.com/nba/player/gamelog/_/id/3908809
