# Own6 — NBA line-origination research

Verified NBA data → line-origination model → gated strategy leaderboard → published dashboard.

**Start here:** [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) · **Site:** [docs/index.html](docs/index.html)

| Area | Entry points |
|---|---|
| Data (every row sourced) | [data/](data/) — standings, ratings, 92 results, 15-game market lines, props, flags |
| Research | [research/strategies.md](research/strategies.md) · [research/validation.md](research/validation.md) · [research/correlation.md](research/correlation.md) |
| Verification | `python3 scripts/verify_data.py` → [verification/](verification/) |
| Model | `python3 scripts/model.py` → walk-forward backtest + tonight's Own6 lines |
| Site build / link check | `python3 scripts/build_site.py` · `python3 scripts/linkcheck.py` |
| Coordination | [COORDINATION.md](COORDINATION.md) |

Research/paper only — no real wagers. Official sources: NBA.com (standings, ratings, results),
ESPN (schedule, DraftKings lines feed, player logs) with per-row links in every CSV.
