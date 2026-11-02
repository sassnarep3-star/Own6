# Coordination board

Session: `arena/3b057a2c-own6` (the repository branch is fixed by Arena; no separate session branch can be used).

| Task | Status | Owner | Files |
|---|---|---|---|
| NBA strategy research, validation framework, executive summary, and dashboard/site integration | done | arena/3b057a2c-own6 | COORDINATION.md, README.md, docs/**, index.html, assets/**, .github/workflows/** |

## Task notes / audit log
- Initial repository review: only a six-byte README (`# Own6`) existed; no app, source data, tests, or coordination board was present. No other task claim was found.
- Scope claimed by this session. The Arena-managed branch must remain `arena/3b057a2c-own6`; it is not possible to use a separate `session-...` branch here. This session integrated all available work because no other session/task claim was present.
- Official source checks performed on 2026-11-02: [NBA Stats overview](https://www.nba.com/stats/overview) confirms the NBA's official player/team statistics presentation; [NBA Stats glossary](https://www.nba.com/stats/help/glossary) provides official stat definitions; [NBA Official 2026-27 injury report](https://official.nba.com/nba-injury-report-2026-27-season/) confirms season-specific team reporting requirements and updates. The 2025-26 official injury-report page is also linked where season-specific policy is noted.
- Source limitation: NBA sources do not verify book-specific betting odds, settlement, strategy profit, predictive edge, correlation coefficients, or leaderboard rewards. Those remain blank/unverified and are published on `docs/flagged.html`.
- Verification: checked all HTML files and local hyperlinks using Python's HTMLParser; 7 pages checked, no broken local file links. Added GitHub Actions Pages workflow with the same local-link validation plus static artifact deployment. External provider availability and eventual GitHub Pages account settings/deployment must be checked in GitHub Actions/Pages after merge.
- Methodology, model ideas, gating principles and leaderboard controls are explicitly presented as proposed research design, not official NBA facts or empirically validated results. No luck-removal or guaranteed-profit claim is made.
- PR/merge/Pages deployment result: pending; this branch's workflow deploys on main after integration. Record final PR and deploy status here if GitHub permits.
