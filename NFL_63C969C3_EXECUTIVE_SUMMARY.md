# NFL decision pack — session 63c969c3

**As of 2026-11-19 (UTC), Week 11 Thursday.** This pack adds a fresh official-source re-read of the standings, Week 11 and Week 12 schedules, Week 10 results, injury hub, transactions, TNF game centre, and NFL odds URL. The NFL readings corroborate the previous in-repository captures: 32 standings rows; 13 Week 11 games; 16 Week 12 games; 14 Week 10 finals; 253 injury player rows plus two markers; 25 November reserve-list records and 12 November trade rows. The three injury-hub reads (about 09:01Z, 11:07Z and this session's ~12:30Z transcription completion clock) show no observed row-level changes across 253 player keys. The artifact clocks are upper bounds/completion clocks, not NFL server timestamps; the transcription hashes do not authenticate the page response.

## Decision status
No originated lines, official market prices, result-derived performance, or validated correlations are published. The official NFL `/odds/` URL returned its 404 page. Fair lines, market lines, edges, probabilities, ROI/CLV and correlations remain blank; empty registers are intentional, not missing build output. No strategy is promoted. Singles remain the appropriate shadow starting point; parlays and prop combos are unqualified until joint probabilities and operator void/push rules are validated.

## High-value constraints / irregularities
- Injury hub lists Azeez Al-Shaair and Jaylon Carlies with blank game status while the November reserve list places both on Reserve/Injured. Presence on the injury hub does not prove eligibility.
- Jaylen Waddle appears on Denver's injury table but no November NFL trade row was found. Affiliation unresolved.
- Injury-page display names and player URL slugs disagree for Jacob Hummel/Jake Hummel and Dee Alford/Deaundre Ford.
- Standings H1 contains raw template tokens; body data reconciles to 149 W / 149 L / 2 T and PF=PA=6,923.
- IND@HOU game centre calls the stadium RELIANT STADIUM while schedule destination parameter says NRG Stadium. Preserve both verbatim; no resolution inferred.
- Week 12 venues not captured from every official game centre; leave blank until individually read.

## Blocking gates
Immutable scheduled multi-day injury/depth/inactive snapshots; official game-book starter and inactive evidence; official depth order for all 32 teams; official snap counts; 32-team roster/IR integration; market-data policy and authorized prices; verified results corpus; point-in-time train/validation/holdout; calibration/ablation evidence; prospective proper-score qualification and uncertainty; directly validated joint-probability evidence for combos. Existing preregistrations and prior leaderboard/control work remain in their source packs; this pack adds no performance claims.

See `docs/nfl-63c969c3/` for registers, questions, suggestions, sources, and flagged items. Every row in the registers links to a primary NFL page where the value is sourceable; unresolved or not-yet-captured data are blank and flagged.
