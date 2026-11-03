# Independent evidence and release review — 2026-11-03

## Executive decision

The existing [live dashboard](https://sassnarep3-star.github.io/Own6/docs/) is a research prototype, **not a validated betting system**. Its empirical ledger has no authorized observations; it displays no qualified leaderboard entries or empirical correlation coefficients. It does not automatically originate actionable current lines. The design proposes singles, props and parlays, but no skill or profitability is established. Statistical testing can reduce the risk of mistaking noise for skill; it cannot remove luck.

## What this session checked

| Check | Result | Evidence and limit |
|---|---|---|
| NBA metric definitions | Official glossary retrieved; it defines metrics, not predictive edge. | [NBA Stats glossary](https://www.nba.com/stats/help/glossary) |
| Rights boundary | NBA terms §9 state NBA Statistics may not be used in connection with gambling, including legal gambling; §1 imposes public reuse restrictions. Whether a particular proposed use or separate licensed feed is permitted requires rights review. | [NBA Terms of Use](https://www.nba.com/termsofuse#nba-statistics) |
| Deployment configuration and state | GitHub Pages API reported `main:/` and build `f2877f3e4d5fd1ca736f1c66ff3a03b439b4f3b5` built; the live landing and lab flags pages rendered when fetched. This is not a test of every external link. | [Pages API](https://api.github.com/repos/sassnarep3-star/Own6/pages/builds/latest); [GitHub publishing documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) |
| Local tests | 34 pytest tests passed after installing `requirements-empirical.txt` and pytest in an isolated environment. Release gate, lab checker, report checker and integration audit passed. | Repository commands, not external fact verification. |
| Row-source compliance | `python tools/check_site.py` reports 31 advisory rows without official source links under `docs/verified/`; the [lab flags page](https://sassnarep3-star.github.io/Own6/docs/lab/flagged.html) discloses this. The every-row requirement is not met. A link alone would not establish correctness. | [NBA glossary](https://www.nba.com/stats/help/glossary) provides definitions, not universal row verification. |
| Conflicting repository descriptions | README says no historical data or sportsbook quotes are included but also describes historical results and secondary-source lines; files include historical data and market lines. Their inclusion and evidence status need reconciliation, not blanket verification. | [NBA schedule](https://www.nba.com/schedule); [NBA terms](https://www.nba.com/termsofuse) |

## Remaining limitations

This was not an independent line-by-line review of every repository row. Existing integration checks recompute values and check link structure, not source content, data rights, live availability or executable prices. Historical prototype metrics and third-party odds must not be confused with the empty authorized lab's results. The current design is no-input to browse, but an operational, legally authorized automated feed is not configured. The separate open integration work by other sessions was not modified or represented as complete here.

For a defensible leaderboard, first establish permitted data and timestamped, executable market quotes; preserve pregame forecasts and settlement rules; evaluate time-ordered holdouts, calibration, costs, correlated bets and uncertainty; adjust for strategy selection and multiple tests; and award only preregistered qualifiers. Treat all numeric estimates as unverified until their underlying observations, calculation and provenance are independently checked.
