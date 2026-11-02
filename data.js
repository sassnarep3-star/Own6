window.OWN6 = {
  sources: {
    glossary: {label:'NBA Stats Glossary', url:'https://www.nba.com/stats/help/glossary'},
    glossaryArticle: {label:'NBA Inside the Game: Stat Glossary', url:'https://www.nba.com/news/inside-the-game-stat-glossary'}
  },
  metrics: [
    {category:'Player props', metric:'Points (PTS)', definition:'Number of points scored.', source:'glossary'},
    {category:'Player props', metric:'Rebounds (REB)', definition:'Rebounds collected on offense or defense.', source:'glossary'},
    {category:'Player props', metric:'Assists (AST)', definition:'Official NBA glossary entry; consult source for definition.', source:'glossary'},
    {category:'Player props', metric:'Assist-to-turnover ratio (AST/TO)', definition:'Assists compared with turnovers committed.', source:'glossary'},
    {category:'Player props', metric:'Expected field-goal percentage (xFG%)', definition:'Expected FG% given player-tracking details of each shot.', source:'glossaryArticle'},
    {category:'Player props', metric:'Field-goal percentage above expected (FG%+)', definition:'Difference between FG% and expected FG%.', source:'glossaryArticle'},
    {category:'Player props', metric:'Rebound chance percentage (REB Chance%)', definition:'Rebounds recovered compared with rebound chances.', source:'glossary'},
    {category:'Player props', metric:'Touches', definition:'Times a player or team touches and possesses the ball.', source:'glossary'},
    {category:'Player props', metric:'Time of possession', definition:'Minutes a player or team possesses the ball.', source:'glossary'},
    {category:'Player props', metric:'Drive points', definition:'Points on drives to the basket.', source:'glossary'},
    {category:'Player props', metric:'Catch-and-shoot points', definition:'Points on catch-and-shoot shots.', source:'glossary'},
    {category:'Team lines', metric:'Possessions / per-100 rates', definition:'Use NBA glossary definitions and the official NBA source for the chosen statistic; numerical values not supplied.', source:'glossary'},
    {category:'Market', metric:'Fair probability, market odds, vig, closing line', definition:'No official NBA source; requires timestamped, licensed market data. Not provided.', source:null}
  ],
  strategies: [
    {name:'Single: player volume distribution', market:'Points / rebounds / assists', signal:'Project minutes and opportunity first; model outcome distribution conditional on role and availability. Use xFG% as a shot-quality diagnostic, not a guarantee of future conversion.', evidence:'NBA definitions only; no tested effect or edge established.', gate:'All validation gates; no bet if data/availability uncertain.', source:'glossaryArticle'},
    {name:'Single: team scoring distribution', market:'Spread / total / moneyline', signal:'Estimate possession-level scoring and uncertainty; compare fair probability to executable, vig-adjusted market price.', evidence:'No verified prices or backtest in repository.', gate:'Time-ordered out-of-sample validation and market benchmark.', source:'glossary'},
    {name:'Parlay: joint outcome model', market:'Multi-leg combinations', signal:'Estimate joint probability directly or from a validated dependence model; never assume independence without evidence.', evidence:'No pairwise correlation observations available.', gate:'Joint calibration, sufficient paired samples, multiplicity correction, and price comparison.', source:null},
    {name:'Player-prop combo: shared game context', market:'Multiple player props', signal:'Model common minutes, pace, game state and usage drivers; estimate covariance from paired residuals, conditional on relevant context.', evidence:'Correlation value not measured; left blank.', gate:'Out-of-sample joint calibration and stability by season/role.', source:'glossary'}
  ]
};