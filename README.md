# Own6 — Originate Your Own NBA Lines
Research system for building your own NBA spread/total/win-prob, player-prop and correlated-parlay prices, with validation gates that remove luck (walk-forward, calibration, CLV, binomial + Bonferroni, bootstrap CI) and a leaderboard scored on the lower confidence bound of ROI.
- **Executive summary:** `EXECUTIVE_SUMMARY.md` · **Coordination board:** `COORDINATION.md`
- **Engine:** `src/own6/` (stdlib only) · **Tests:** `python3 -m pytest tests/ -q` (5 passing) · **Demo (synthetic only):** `examples/demo_synthetic.py`
- **Site:** `docs/` → GitHub Pages. Every table row links an official source; unconfirmed values are blank and listed on the Flagged for Review page.
- **Sources registry:** `data/sources.csv`. Research/analytics only — not betting advice.
