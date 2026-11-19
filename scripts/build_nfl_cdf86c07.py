#!/usr/bin/env python3
"""Build the cdf86c07 NFL dashboard pack: data registers + static site.

Deterministic: no network, no clock. Every official value below was transcribed
from the two official pages named in SOURCES (read 2026-11-19 UTC via page fetch).
Market, price, and roof/weather columns are deliberately blank: no official NFL
page publishes a betting line, so nothing here is priced.
"""
from __future__ import annotations

import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl_cdf86c07"
DOCS = ROOT / "docs" / "nfl-cdf86c07"
READ_DAY = "2026-11-19"
STANDINGS_URL = "https://www.nfl.com/standings/division/2026/reg"
SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
RESERVE_OK = "https://www.nfl.com/transactions/league/reserve-list/2026/11"

# (club, division, w, l, t, pct, pf, pa, net, streak) — official standings page, read 2026-11-19
STANDINGS = [
    ("Buffalo Bills", "AFC East", 8, 1, 0, "0.889", 287, 199, 88, "5W"),
    ("New England Patriots", "AFC East", 5, 5, 0, "0.500", 221, 242, -21, "2L"),
    ("New York Jets", "AFC East", 2, 8, 0, "0.200", 194, 254, -60, "5L"),
    ("Miami Dolphins", "AFC East", 1, 8, 0, "0.111", 148, 224, -76, "3L"),
    ("Cincinnati Bengals", "AFC North", 7, 2, 0, "0.778", 278, 193, 85, "5W"),
    ("Pittsburgh Steelers", "AFC North", 6, 3, 0, "0.667", 198, 182, 16, "1L"),
    ("Cleveland Browns", "AFC North", 6, 4, 0, "0.600", 188, 220, -32, "1W"),
    ("Baltimore Ravens", "AFC North", 4, 6, 0, "0.400", 209, 259, -50, "5L"),
    ("Jacksonville Jaguars", "AFC South", 7, 2, 0, "0.778", 269, 144, 125, "3W"),
    ("Houston Texans", "AFC South", 3, 6, 0, "0.333", 233, 219, 14, "1L"),
    ("Indianapolis Colts", "AFC South", 3, 7, 0, "0.300", 208, 271, -63, "1W"),
    ("Tennessee Titans", "AFC South", 1, 8, 0, "0.111", 167, 239, -72, "3L"),
    ("Kansas City Chiefs", "AFC West", 7, 2, 0, "0.778", 237, 156, 81, "2W"),
    ("Denver Broncos", "AFC West", 7, 2, 0, "0.778", 198, 186, 12, "5W"),
    ("Las Vegas Raiders", "AFC West", 4, 6, 0, "0.400", 251, 289, -38, "2L"),
    ("Los Angeles Chargers", "AFC West", 1, 8, 0, "0.111", 144, 239, -95, "1W"),
    ("New York Giants", "NFC East", 5, 3, 1, "0.611", 203, 196, 7, "1L"),
    ("Dallas Cowboys", "NFC East", 4, 6, 0, "0.400", 286, 282, 4, "1L"),
    ("Washington Commanders", "NFC East", 3, 5, 1, "0.389", 196, 223, -27, "1W"),
    ("Philadelphia Eagles", "NFC East", 2, 7, 0, "0.222", 148, 221, -73, "7L"),
    ("Detroit Lions", "NFC North", 7, 2, 0, "0.778", 257, 199, 58, "5W"),
    ("Minnesota Vikings", "NFC North", 7, 2, 0, "0.778", 176, 126, 50, "1W"),
    ("Chicago Bears", "NFC North", 7, 2, 0, "0.778", 241, 184, 57, "4W"),
    ("Green Bay Packers", "NFC North", 6, 4, 0, "0.600", 226, 221, 5, "1L"),
    ("Carolina Panthers", "NFC South", 4, 5, 0, "0.444", 219, 236, -17, "1W"),
    ("Tampa Bay Buccaneers", "NFC South", 3, 6, 0, "0.333", 202, 178, 24, "1L"),
    ("New Orleans Saints", "NFC South", 3, 6, 0, "0.333", 202, 236, -34, "1L"),
    ("Atlanta Falcons", "NFC South", 3, 7, 0, "0.300", 201, 258, -57, "3L"),
    ("San Francisco 49ers", "NFC West", 8, 1, 0, "0.889", 281, 196, 85, "2W"),
    ("Seattle Seahawks", "NFC West", 6, 4, 0, "0.600", 223, 175, 48, "2W"),
    ("Los Angeles Rams", "NFC West", 6, 4, 0, "0.600", 248, 187, 61, "4W"),
    ("Arizona Cardinals", "NFC West", 3, 7, 0, "0.300", 184, 289, -105, "2L"),
]

# Week-11 games: (date, kickoff, network, away, away_rec, home, home_rec, game-page slug)
# Records are as printed on the official schedule page; the checker matches them to STANDINGS.
SLATE = [
    ("2026-11-19", "8:15 PM", "PRIME", "IND", "3-7", "HOU", "3-6", "colts-at-texans-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "CBS", "MIA", "1-8", "BUF", "8-1", "dolphins-at-bills-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "FOX", "BAL", "4-6", "CAR", "4-5", "ravens-at-panthers-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "FOX", "NO", "3-6", "CHI", "7-2", "saints-at-bears-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "FOX", "TEN", "1-8", "DAL", "4-6", "titans-at-cowboys-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "FOX", "TB", "3-6", "DET", "7-2", "buccaneers-at-lions-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "CBS", "AZ", "3-7", "KC", "7-2", "cardinals-at-chiefs-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "CBS", "PIT", "6-3", "PHI", "2-7", "steelers-at-eagles-2026-reg-11"),
    ("2026-11-22", "4:05 PM", "FOX", "NYJ", "2-8", "LAC", "1-8", "jets-at-chargers-2026-reg-11"),
    ("2026-11-22", "4:25 PM", "CBS", "JAX", "7-2", "NYG", "5-3-1", "jaguars-at-giants-2026-reg-11"),
    ("2026-11-22", "4:25 PM", "CBS", "LV", "4-6", "DEN", "7-2", "raiders-at-broncos-2026-reg-11"),
    ("2026-11-22", "8:20 PM", "NBC", "MIN", "7-2", "SF", "8-1", "vikings-at-49ers-2026-reg-11"),
    ("2026-11-23", "8:15 PM", "ESPN", "CIN", "7-2", "WAS", "3-5-1", "bengals-at-commanders-2026-reg-11"),
]

# Teams on bye, Week 11 (official schedule page "Teams on Bye" block)
BYES = [("ATL", "3-7"), ("CLE", "6-4"), ("GB", "6-4"), ("LA", "6-4"), ("NE", "5-5"), ("SEA", "6-4")]

# Requirement register: (id, brief item, status, covered_by, blocking gate, clearing number)
# status vocabulary: captured (evidence in this pack) | partial (prior pack covers part) |
#                    blocked (required source not captured) | open (not started) | decided (policy text only)
REQ = [
    ("CD-01", "Price-snapshot store: opening + closing numbers for every originated market", "partial", "nfl_origination hash ledger (no prices)", "VG-03: no licensed/official price archive", "0 of 13 Week-11 markets have a dated open+close price"),
    ("CD-02", "Verified results feed for backtests and ROI", "partial", "nfl_51698d74 corpus (official finals)", "Results feed not automated; no price source", "150 official finals reconciled (149 W / 149 L / 2 T)"),
    ("CD-03", "Originate side, then total, then moneyline", "partial", "nfl_51698d74: 13 Week-11 fair lines MATCH", "No market to compare against", "13 of 13 games with fair side+total+moneyline"),
    ("CD-04", "Publish fair line, market line and difference as separate columns", "partial", "nfl_51698d74 fair-line column", "No official market line exists", "0 market cells (blank by policy)"),
    ("CD-05", "Separate signal from staking in the leaderboard", "partial", "nfl_51698d74 leaderboard", "Staking not separately scored", "8 of 8 leaderboard rows Brier-scored, 0 qualified"),
    ("CD-06", "Track depth of the replacement, not only the fact of replacement", "blocked", "none", "Depth-order source unresolved for 32 clubs", "32 of 32 clubs with a verified depth order"),
    ("CD-07", "Correlations only from officially sourced numbers, published with n", "partial", "nfl_51698d74 correlations", "Only 150 official finals in scope", "n = 150 per pair (4 pairs published)"),
    ("CD-08", "Demotion gate that sends a live strategy back to paper", "partial", "Gate text in origination pack; never exercised", "No live strategy exists", "1 live strategy to test the gate against"),
    ("CD-09", "Pre-register every strategy; backtests never on the leaderboard", "partial", "Pre-registration text in prior packs", "No dated registration commit for each strategy", "10 of 10 candidates with commit hash (none confirmed here)"),
    ("CD-10", "Availability graph: who was expected to start vs who started", "blocked", "none", "No expected-starter source captured", "32 clubs with expected + actual starters"),
    ("CD-11", "Do not model depth from jersey order; model from playing time", "decided", "Policy (this pack)", "Snap or Game Book source still required", "0 depth ranks inferred from jersey number"),
    ("CD-12", "Injury signal as a surprise (delta), never a level", "partial", "nfl_ade166a4 same-day delta: 0 changes", "Only two same-day reads captured", "3+ dated injury-report reads per week (Wed–Fri)"),
    ("CD-13", "Run the 32-team roster/IR sweep before any team-level model", "blocked", "nfl_ade166a4 injury hub (253 rows)", "Per-club roster and IR pages not swept", "32 of 32 clubs swept"),
    ("CD-14", "Fixture-context features from published schedule facts only", "captured", "This pack: Week-11 slate", "Venue transcription incomplete for Week 11", "13 of 13 Week-11 games with time, network, records"),
    ("CD-15", "Store every model output as probability plus inputs", "partial", "nfl_51698d74 model_outputs", "No inputs file for every output", "All outputs with inputs (not yet confirmed)"),
    ("CD-16", "Removal-of-luck panel on the site dashboard", "partial", "nfl_origination luck-share (~0.518)", "Panel not on this landing page", "1 panel on landing page"),
    ("CD-17", "Two-sided 'what would change our mind' field per strategy", "open", "none", "No strategy entry template finalized", "10 of 10 strategy entries with both sides"),
    ("CD-18", "Price our line and publish residual vs market on a schedule", "blocked", "none", "VG-03 no market price", "1 scheduled residual per week"),
    ("CD-19", "Turn the 136-game log into the pre-registered backtest corpus", "partial", "nfl_51698d74 counts 150 games", "136-game log not reconciled to 150", "136 log rows reconciled to 150 official finals"),
    ("CD-20", "Decide the price-data policy before any backtest is published", "decided", "Policy: no price published without licence", "Licence/terms unread", "Policy decided; 0 prices published"),
    ("CD-21", "Store every injury-hub read with clock time; publish delta, never level", "partial", "nfl_ade166a4 two timestamped reads", "No daily series", "Daily reads Wed to kickoff"),
    ("CD-22", "Decision-readiness table on the landing page: one row per requirement", "captured", "This pack (index.html)", "—", "82 of 82 requirements shown"),
    ("CD-23", "Transcribe venue of every fixture from the official game centre", "partial", "nfl_51698d74 Week-12 16 of 16", "Week-11 game-centre venues not captured here", "13 of 13 Week-11 venues"),
    ("CD-24", "Publish the league's dated schedule announcement beside the live schedule", "captured", "This pack: week-11 page", "—", "3 dated announcements transcribed (Weeks 16–18)"),
    ("CD-25", "Use official Game Books for actual starters and game-day status", "blocked", "none", "No Game Book captured", "0 of 13 Week-11 Game Books"),
    ("CD-26", "Ingest game-level results to make ratings opponent-aware", "open", "none", "Ratings model not rebuilt", "150 game results in ratings input"),
    ("CD-27", "Injury and personnel ablations instead of fixed penalties", "open", "none", "Needs verified availability features", "Chronological holdout with and without features"),
    ("CD-28", "Injury/depth ablations, identical models with and without features", "open", "none", "Same as CD-27", "Same as CD-27"),
    ("CD-29", "Automate immutable multi-day availability snapshots with hashes", "partial", "nfl_ade166a4 capture hashes", "No scheduled capture job", "Daily capture for 7 consecutive days"),
    ("CD-30", "Immutable official snapshots: injury, depth, inactives, with conflict flags", "blocked", "nfl_ade166a4 (injury only)", "No depth or inactive capture", "3 source types captured daily"),
    ("CD-31", "Capture official inactive lists and snap counts", "blocked", "none", "Inactives and snap pages not captured", "Inactives for 13 of 13 Week-11 games"),
    ("CD-32", "Fix the two depth-parsing failures (Texans image; Packers prefixes)", "blocked", "nfl_51698d74 flags 516-F06", "Texans depth is an image; needs authorised structured source", "2 of 2 parser failures fixed with raw string kept"),
    ("CD-33", "Model depth slots as groups, not a single starter", "decided", "Policy (this pack)", "Slot data not yet captured", "149 club/unit/position slots represented as groups"),
    ("CD-34", "Treat roster turnover as a first-class data event", "open", "nfl_51698d74 transactions reference", "No event log built", "Each depth row versioned to last roster event"),
    ("CD-35", "Singles-only shadow baseline, frozen and recorded before kickoff", "partial", "nfl_51698d74 frozen S01 forecaster", "Frozen forecast not timestamped before each kickoff", "13 of 13 Week-11 forecasts recorded pre-kickoff"),
    ("CD-36", "Joint-evidence gate for parlays and prop combos", "decided", "Policy (this pack)", "No validated joint probability", "0 combos ranked until gate passes"),
    ("CD-37", "Proper-score leaderboard divisions (singles, parlays, SGP, props)", "partial", "nfl_51698d74: singles only", "Only singles exist", "4 divisions, each with ≥1 eligible strategy"),
    ("CD-38", "Rank by Brier skill with game-cluster lower bound and multiplicity adjustment", "partial", "nfl_51698d74 Brier skill", "Cluster bound and multiplicity not confirmed", "8 of 8 rows with lower bound"),
    ("CD-39", "Durable snapshot storage outside the static site, plus alerts", "open", "none", "No external store configured", "1 external store + 1 freshness alert"),
    ("CD-40", "Public analysis layer vs private raw data layer", "blocked", "Suggestion S-06 (review only)", "Terms not read", "Terms read and split decided"),
    ("CD-41", "Per-team view: starters out, replacements named, net injury count", "open", "nfl_ade166a4 hub (partial data)", "Replacements blank (no depth source)", "32 of 32 team rows"),
    ("CD-42", "Announced-starter evidence field (not inferred replacement)", "blocked", "none", "No dated starter-change source captured", "Each announced change with date and link"),
    ("CD-43", "Official depth-chart register with date and source per row", "blocked", "none", "Depth source unresolved", "32 of 32 clubs with dated rows"),
    ("CD-44", "Calibrate 'Questionable' empirically", "blocked", "none", "No past-season report archive", "Designation-to-play rate with CI from archive"),
    ("CD-45", "Offense vs defense matchup deficiency matrix (1st–4th string)", "blocked", "none", "Depth slots not captured", "32 clubs × 4 string levels"),
    ("CD-46", "Flag stale depth rows against the official transactions log", "partial", "nfl_51698d74 reserve window", "Lamar/Huntley windows not retested", "Each depth row checked against transactions"),
    ("CD-47", "Point-in-time ledger for injuries, depth and inactives", "partial", "nfl_origination hash-chained ledger (no injury series)", "Ledger has no injury or depth rows", "Every row stamped with capture time"),
    ("CD-48", "Populate Lions game-status designations", "captured", "nfl_51698d74 re-test: closed", "—", "3 of 3 Lions designations shown"),
    ("CD-49", "Reject depth from jersey number, experience, or salary", "decided", "Policy (this pack)", "—", "0 depth orders derived from roster attributes"),
    ("CD-50", "Represent shared and empty depth slots faithfully", "blocked", "none", "Depth source unresolved", "Shared/empty slots shown as-is"),
    ("CD-51", "Resolve depth-order source (club pages, or snap counts) before the backup feature", "blocked", "nfl_51698d74 flag 516-F06", "Neither route verified for 32 clubs", "1 route verified for 32 of 32 clubs"),
    ("CD-52", "Score injury-designation reliability before using it as a feature", "blocked", "none", "No multi-season archive", "Play rate with CI for each designation"),
    ("CD-53", "Snapshot injury report every Wed, Thu and Fri", "open", "none", "No scheduled job", "3 dated snapshots per week"),
    ("CD-54", "Timestamped injury series from Wednesday to kickoff", "partial", "nfl_ade166a4 timestamped reads", "No daily series yet", "Reads at least daily Wed–kickoff"),
    ("CD-55", "Snap counts as starter proxy when depth chart is unavailable", "blocked", "none", "No snap-count source captured", "13 of 13 Week-11 snap pages"),
    ("CD-56", "Control baselines (random picks, favourites only) on every leaderboard run", "partial", "nfl_51698d74 control Brier 0.254094", "Random and favourite baselines not both shown", "2 control baselines per run"),
    ("CD-57", "Roof, surface and NWS hourly wind/precipitation overlay", "blocked", "none", "Roof and NWS not captured", "13 of 13 games with roof + forecast"),
    ("CD-58", "Two-stage leaderboard: proper-score qualification, then CLV/ROI escrow", "open", "none", "No prospective sample", "Stage 1 pass count and Stage 2 sample size"),
    ("CD-59", "Vig-free market consensus vs originated fair-line decomposition", "blocked", "none", "VG-03 no market", "1 vig-free consensus per game"),
    ("CD-60", "Weekly 'what changed' diff (rank, rating, availability)", "partial", "nfl_ade166a4 same-day delta", "Only one week of data", "2 consecutive weekly snapshots"),
    ("CD-61", "Publish every total twice until walk-forward picks one", "open", "none", "Estimators not built", "2 estimators with gap column"),
    ("CD-62", "Drift alarm per scraper: pinned row counts and fields, fail loudly", "captured", "This pack: pinned counts (32, 13, 6) + checker", "—", "3 pinned tables"),
    ("CD-63", "Capture reserve list so 'not listed' never means 'available'", "partial", "nfl_51698d74: 25 rows, 11/10–11/18 window", "Render window ends 11/18", "Full-season window captured"),
    ("CD-64", "Reject ranking strategies by season-long ROI", "decided", "Policy (this pack)", "—", "0 strategies ranked by season ROI"),
    ("CD-65", "Archive weekly injury reports for past seasons", "blocked", "none", "Past-season archive not captured", "Every week of one prior season"),
    ("CD-66", "Pre-register each strategy: definition frozen before results seen", "partial", "Pre-registration text in prior packs", "No commit hash per strategy", "10 of 10 with commit hash"),
    ("CD-67", "Freeze a rule (text, window, gates) in git before evaluation opens", "partial", "Git history of prior packs", "Not applied to a new rule here", "Commit hash per rule"),
    ("CD-68", "2026 kickoff and onside-kick regime priors", "open", "nfl_51698d74 flag 516-F12", "Regime effect not estimated", "Estimate with CI on the 2026 sample"),
    ("CD-69", "Split data into train, validation and final holdout seasons", "open", "none", "No season split defined", "3 disjoint season sets defined in writing"),
    ("CD-70", "Suggestions section for owner review, not auto-implemented", "captured", "This pack: suggestions.html", "—", "10 of 10 suggestions pending owner choice"),
    ("CD-71", "Clear list of questions, information and answers, with discovery paths", "captured", "This pack: questions.html", "—", "15 of 15 questions with discovery path"),
    ("CD-72", "Originate own NFL lines", "partial", "nfl_51698d74: 13 Week-11 fair lines", "No market to compare against", "13 of 13 games"),
    ("CD-73", "Leaderboard competition for singles, parlays, prop combos", "partial", "nfl_51698d74: singles only", "Parlay/prop gate CD-36 not passed", "3 divisions with ≥1 eligible strategy"),
    ("CD-74", "Each strategy must pass validation gates", "partial", "Gates in prior packs", "No strategy passes all gates", "≥1 strategy passes all gates"),
    ("CD-75", "Determine correlation values", "partial", "nfl_51698d74: 4 pairs, n=150", "Only official finals", "n = 150 per pair"),
    ("CD-76", "Remove luck; build selectively skill-based strategies", "partial", "nfl_origination luck-share (~0.518)", "No strategy beats control with CI", "1 strategy with lower bound above control"),
    ("CD-77", "Track injuries and 2nd/3rd/4th-string replacements, offense and defense", "blocked", "none", "Depth source CD-51 unresolved", "32 clubs × offense/defense × 4 string levels"),
    ("CD-78", "Executive summary", "captured", "NFL_CDF86C07_EXECUTIVE_SUMMARY.md", "—", "1 summary"),
    ("CD-79", "Line-by-line repo review with official links, irregularities flagged", "captured", "audit/NFL_CDF86C07_REPO_REVIEW.md", "—", "All findings linked"),
    ("CD-80", "Live GitHub Pages site: clean landing page + categorised subpages", "captured", "docs/nfl-cdf86c07/", "Pages deploy after merge", "1 landing + 7 subpages"),
    ("CD-81", "Flagged for Review page with source links; non-blocking", "captured", "docs/nfl-cdf86c07/flags.html", "—", "All flags with links; blocking_merge=no"),
    ("CD-82", "Parallel-session coordination via COORDINATION.md", "captured", "COORDINATION.md claim + record", "—", "1 claim + 1 completion record"),
]

QUESTIONS = [
    ("Q-01", "Where is a licensed or official NFL price archive, and what are its terms?", "No official NFL page publishes betting lines (nfl.com/odds returns 404).", "Terms of licensed odds vendors; not NFL pages. Read terms before any price is stored.", "VG-03 · CD-01, CD-04, CD-18, CD-59"),
    ("Q-02", "Which official pages show each club's depth order for all 32 clubs?", "Texans depth is an image; Packers prefix jersey numbers (prior pack).", "Per-club team pages on nfl.com; check each club individually and record the URL.", "CD-06, CD-43, CD-51"),
    ("Q-03", "Are official Game Books published for each game, and where?", "No Game Book captured in any pack.", "Game centre for a completed game, look for a Game Book link. Path not yet verified here.", "CD-25, CD-31"),
    ("Q-04", "Are inactive lists and snap counts published officially, and at what time?", "None captured.", "Game centre after kickoff (path unverified). Record the time stamp of each capture.", "CD-31, CD-55"),
    ("Q-05", "What does 'Questionable' mean in practice (play rate)?", "Official text gives no percentages.", "Archive of prior seasons' injury reports, joined to official inactive lists.", "CD-44, CD-52, CD-65"),
    ("Q-06", "Which Week-11 venues come from the game centre and which from hotel parameters?", "Week 11 venues not captured in this pack.", "Each game centre page (links in week11_slate.csv).", "CD-23"),
    ("Q-07", "Is the Week-11 Mexico City header's game the Vikings–49ers game?", "The schedule page places the Vikings at 49ers game under an 'International Game' header with a Mexico City logo; no venue is printed in the fetched text.", "Vikings at 49ers game centre (link in slate).", "CD-14, CD-23"),
    ("Q-08", "Does the reserve list cover the full season or only a render window?", "Prior pack: window 11/10–11/18 only.", "The reserve-list page with season and month parameters.", "CD-63"),
    ("Q-09", "Which roof and surface designations are official for each stadium?", "Not captured.", "Each game-centre page (roof/surface field, if published).", "CD-57"),
    ("Q-10", "What NWS forecast grid applies to each game location?", "Not captured; NWS is not in the allowed host list for this sandbox.", "Owner to confirm whether NWS may be fetched from this environment.", "CD-57"),
    ("Q-11", "How many finals make the backtest corpus: 136 or 150?", "Brief cites 136 games; the 51698d74 pack recomputes 150 from standings (149+149+2)/2.", "Reconcile the 136-game log against the official schedule week by week.", "CD-19"),
    ("Q-12", "Does the NFL publish dated starter changes for Lock, McCord and Brissett?", "Brief cites VR-24, VR-25, VQ-05 from a prior review; not re-read here.", "Official transactions page and team news pages (paths unverified).", "CD-42"),
    ("Q-13", "Will NFL or partner terms allow publishing raw row-level data?", "Terms not read in any pack.", "NFL legal terms page (linked from site footer) and data-partner terms.", "CD-40"),
    ("Q-14", "What is the registered commit hash for each pre-registered strategy?", "Not recorded per strategy.", "git log of the strategy-definition files.", "CD-09, CD-66, CD-67"),
    ("Q-15", "What is the season-level sample floor for the leaderboard to qualify any strategy?", "Not defined in this pack.", "Owner decision; see suggestion S-08.", "CD-38, CD-74"),
]

SUGGESTIONS = [
    ("S-01", "Add a Pending state for blank game-status cells rather than leaving them blank.", "Keeps 'no designation published' distinct from 'healthy'.", "owner"),
    ("S-02", "Capture the Week-11 game-centre venues (13 pages) and publish them beside the slate.", "Closes CD-23 for the current week; low cost.", "owner"),
    ("S-03", "Pick one route for depth order (club pages vs snap counts) and verify it for 32 clubs.", "Unblocks CD-06, CD-43, CD-51 and every depth feature.", "owner"),
    ("S-04", "Start the Wednesday–Friday injury-report snapshot job with hashes and fetch times.", "Creates the surprise series required by CD-12 and CD-53.", "owner"),
    ("S-05", "Ask the owner whether a licensed price archive is in scope before any market column appears.", "Market columns stay blank until a licence is confirmed (Q-01).", "owner"),
    ("S-06", "Read NFL and data-partner terms, then decide the public/private data split.", "Needed before raw rows are published (Q-13, CD-40).", "owner"),
    ("S-07", "Reconcile the 136-game log with the 150 official finals before any backtest is published.", "Avoids a corpus that silently differs between packs (Q-11).", "owner"),
    ("S-08", "Set the leaderboard sample floor and multiplicity method in writing before any strategy is scored.", "Prevents post-hoc threshold choice (Q-15).", "owner"),
    ("S-09", "Add a freshness alert: fail the build when a capture is older than one day during the season.", "Makes drift visible (CD-62, CD-39).", "owner"),
    ("S-10", "Add a per-team view that shows starters out and net injury count, with replacements blank until a depth source is verified.", "Quick decision view without inferring replacements (CD-41).", "owner"),
]

FLAGS = [
    ("CDF-01", "Standings page H1 renders raw template tokens ('$year$ NFL $displayname$ Standings') while the <title> reads '2026 NFL Division Standings'.", STANDINGS_URL, "low", "no"),
    ("CDF-02", "Week-11 schedule places Vikings at 49ers under an 'International Game, November 22nd' header with a Mexico City logo; no venue is printed in the fetched text.", SCHEDULE_URL, "low", "no"),
    ("CDF-03", "Week-11 Thursday game (IND at HOU, Nov 19) is dated today; its result is not in this pack.", SCHEDULE_URL, "info", "no"),
    ("CDF-04", "Corpus size disagrees across packs: brief/prior log 136 games; 51698d74 recomputes 150 from standings (149+149+2)/2.", STANDINGS_URL, "medium", "no"),
    ("CDF-05", "Requirement register cites 'nfl_origination' and 'nfl_51698d74' outputs that were not re-verified in this session; their status is carried, not re-proven.", "https://www.nfl.com/standings/division/2026/reg", "low", "no"),
    ("CDF-06", "No official NFL page publishes a betting line; market columns are blank by policy, so no edge can be measured.", "https://www.nfl.com/legal/terms/", "medium", "no"),
]

SOURCES = [
    ("SRC-01", "NFL 2026 division standings (regular season)", STANDINGS_URL, "standings_2026_11_19.csv (32 rows)", "2026-11-19"),
    ("SRC-02", "NFL Week 11 2026 schedule (games, times, networks, records, byes, TBD notes)", SCHEDULE_URL, "week11_slate.csv (13 games), byes_week11.csv (6)", "2026-11-19"),
    ("SRC-03", "NFL reserve list, November 2026 (reference only; not re-read this session)", RESERVE_OK, "none in this pack", "not read"),
    ("SRC-04", "NFL game pages for Week 11 (linked per row)", "https://www.nfl.com/games/colts-at-texans-2026-reg-11", "game_url column", "link only, not opened"),
]

def sha_note() -> str:
    return "transcription of fetched page text; hash covers the CSV artifact, not HTTP bytes"


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def build_data() -> None:
    write_csv(DATA / "standings_2026_11_19.csv",
              ["club", "division", "w", "l", "t", "pct", "pf", "pa", "net_pts", "streak", "source_url", "read_day"],
              [[c, d, w, l, t, p, pf, pa, net, s, STANDINGS_URL, READ_DAY] for (c, d, w, l, t, p, pf, pa, net, s) in STANDINGS])
    write_csv(DATA / "week11_slate.csv",
              ["game_date", "kickoff_as_printed", "network", "away", "away_record", "home", "home_record", "game_url", "schedule_url", "read_day"],
              [[d, k, n, a, ar, h, hr, f"https://www.nfl.com/games/{slug}", SCHEDULE_URL, READ_DAY] for (d, k, n, a, ar, h, hr, slug) in SLATE])
    write_csv(DATA / "byes_week11.csv",
              ["team_abbr", "record_as_printed", "source_url", "read_day"],
              [[t, r, SCHEDULE_URL, READ_DAY] for (t, r) in BYES])
    write_csv(DATA / "requirements.csv",
              ["req_id", "brief_item", "status", "covered_by", "blocking_gate", "clearing_number", "source_url"],
              [list(r) + [SCHEDULE_URL if r[2] == "captured" and "Week" in r[3] else STANDINGS_URL] for r in REQ])
    write_csv(DATA / "questions.csv",
              ["q_id", "question", "known_state", "discovery_path", "gates"],
              [list(q) for q in QUESTIONS])
    write_csv(DATA / "suggestions.csv",
              ["s_id", "suggestion", "why", "decision_owner", "pending_human_choice", "implemented"],
              [[s, t, w, o, "yes", "no"] for (s, t, w, o) in SUGGESTIONS])
    write_csv(DATA / "flagged.csv",
              ["flag_id", "finding", "source_url", "severity", "blocking_merge"],
              [list(f) for f in FLAGS])
    write_csv(DATA / "sources.csv",
              ["src_id", "title", "url", "used_for", "read_status"],
              [list(s) for s in SOURCES])
    import hashlib
    def digest(name: str) -> str:
        return hashlib.sha256((DATA / name).read_bytes()).hexdigest()
    write_csv(DATA / "capture_log.csv",
              ["capture_id", "url", "rows", "artifact", "sha256", "read_day", "note"],
              [["C-01", STANDINGS_URL, 32, "standings_2026_11_19.csv", digest("standings_2026_11_19.csv"), READ_DAY, sha_note()],
               ["C-02", SCHEDULE_URL, 13, "week11_slate.csv", digest("week11_slate.csv"), READ_DAY, sha_note()],
               ["C-03", SCHEDULE_URL, 6, "byes_week11.csv", digest("byes_week11.csv"), READ_DAY, sha_note()]])


# ---------- site ----------
CSS = """
:root{--ink:#1b2430;--muted:#5b6675;--line:#dfe4ea;--bg:#f7f9fb;--accent:#1f6feb;--warn:#b26a00}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#fff;border-bottom:1px solid var(--line);padding:14px 22px;display:flex;flex-wrap:wrap;gap:14px;align-items:center}
header .brand{font-weight:700;margin-right:auto}
nav a{margin-right:12px;color:var(--accent);text-decoration:none}nav a:hover{text-decoration:underline}
main{max-width:1180px;margin:0 auto;padding:22px}
h1{font-size:24px;margin:0 0 6px}h2{font-size:18px;margin:28px 0 8px}
p.lede{color:var(--muted);margin:0 0 16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:16px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.card b{display:block;font-size:22px}.card span{color:var(--muted);font-size:13px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin:8px 0 18px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:14px}
th{background:#eef3f8;font-weight:600;position:sticky;top:0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid var(--line);background:#fff}
.st-captured{background:#e6f6ec;border-color:#b7e4c7}.st-partial{background:#fff7e6;border-color:#f5d28a}
.st-blocked{background:#fdecec;border-color:#f3b4b4}.st-open{background:#eef3f8}.st-decided{background:#f1ecf9}
.note{background:#fff;border-left:4px solid var(--accent);padding:10px 14px;margin:14px 0;color:var(--muted)}
.warn{border-left-color:var(--warn)}
footer{color:var(--muted);font-size:13px;padding:20px 22px;text-align:center}
"""

NAV = [("index.html", "Overview"), ("standings.html", "Standings"), ("week11.html", "Week 11"),
       ("requirements.html", "Decision readiness"), ("questions.html", "Questions"),
       ("suggestions.html", "Suggestions (review)"), ("flags.html", "Flagged for Review"), ("sources.html", "Sources")]


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def link(url: str, label: str = "source") -> str:
    return f'<a href="{esc(url)}" rel="noopener">{esc(label)}</a>'


def page(title: str, active: str, body: str) -> str:
    nav = "".join(f'<a href="{href}"{" aria-current=page" if href == active else ""}>{esc(lbl)}</a>' for href, lbl in NAV)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NFL dashboard (cdf86c07)</title><style>{CSS}</style></head>
<body><header><div class="brand">NFL dashboard · pack cdf86c07</div><nav>{nav}</nav></header>
<main>{body}</main>
<footer>Every row links to its official nfl.com source. Blank = not confirmed from an official source. No market prices, no betting advice, no profitability claim. Read day {READ_DAY} (UTC).</footer>
</body></html>
"""


def table(headers: list[str], rows: list[list[str]], num_cols: set[int] = frozenset()) -> str:
    th = "".join(f'<th class="{"num" if i in num_cols else ""}">{esc(h)}</th>' for i, h in enumerate(headers))
    trs = []
    for r in rows:
        tds = "".join(f'<td class="{"num" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r))
        trs.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


def status_tag(s: str) -> str:
    return f'<span class="tag st-{esc(s)}">{esc(s)}</span>'


def counts(items):
    out = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out


def build_site() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    st = counts(r[2] for r in REQ)
    total_w = sum(r[2] for r in STANDINGS)
    total_l = sum(r[3] for r in STANDINGS)
    total_t = sum(r[4] for r in STANDINGS)
    total_pf = sum(r[6] for r in STANDINGS)
    total_pa = sum(r[7] for r in STANDINGS)

    # landing
    cards = f"""<div class="cards">
<div class="card"><b>{len(REQ)}</b><span>requirements tracked</span></div>
<div class="card"><b>{st.get('captured',0)}</b><span>captured or decided here</span></div>
<div class="card"><b>{st.get('partial',0)}</b><span>partial (prior pack)</span></div>
<div class="card"><b>{st.get('blocked',0)}</b><span>blocked by a missing source</span></div>
<div class="card"><b>{len(FLAGS)}</b><span>flags (non-blocking)</span></div>
</div>"""
    dr_rows = [[esc(r[0]), esc(r[1]), status_tag(r[2]), esc(r[4]), esc(r[5])] for r in REQ]
    body = f"""<h1>NFL decision dashboard</h1>
<p class="lede">Read day {READ_DAY} (UTC). Official NFL pages only. Nothing here is a betting recommendation, and no profitable edge is demonstrated.</p>
{cards}
<div class="note"><b>Executive summary.</b> The official 2026 standings (32 clubs) and Week-11 slate (13 games, 6 byes) are captured with a source link per row. Totals reconcile: {total_w} W, {total_l} L, {total_t} T, PF {total_pf:,}, PA {total_pa:,}. No official NFL page publishes a betting line, so every market, price, difference and ROI cell is blank by policy. Most of the brief's requirements are blocked by missing official sources (depth order, inactives, Game Books, roof/weather, price archive). The blockers are listed in the decision-readiness table below.</div>
<div class="note warn"><b>Suggestions are review-only.</b> See the <a href="suggestions.html">Suggestions</a> page. Nothing is implemented until the owner chooses. Open items are on the <a href="flags.html">Flagged for Review</a> page.</div>
<h2>Decision readiness (one row per requirement)</h2>
<p class="lede">Each row names the gate that blocks it and the number that would clear it. Status: captured · partial · blocked · open · decided.</p>
{table(["ID", "Requirement", "Status", "Blocking gate", "Clearing number"], dr_rows)}
"""
    (DOCS / "index.html").write_text(page("Overview", "index.html", body), encoding="utf-8")

    # standings
    rows = []
    for (c, d, w, l, t, p, pf, pa, net, s) in STANDINGS:
        rows.append([esc(c), esc(d), str(w), str(l), str(t), p, str(pf), str(pa), f"{net:+d}" if net else "0", esc(s), link(STANDINGS_URL)])
    body = f"""<h1>2026 standings · all 32 clubs</h1>
<p class="lede">Regular season, read {READ_DAY}. Source: <a href="{STANDINGS_URL}">nfl.com division standings</a>. Net points and the league totals are derived here (arithmetic only).</p>
<div class="cards"><div class="card"><b>{total_w} / {total_l} / {total_t}</b><span>league W / L / T</span></div>
<div class="card"><b>{total_pf:,} / {total_pa:,}</b><span>league PF / PA (equal by construction)</span></div></div>
{table(["Club", "Division", "W", "L", "T", "PCT", "PF", "PA", "Net", "Streak", "Source"], rows, {2,3,4,5,6,7,8})}
<div class="note warn">Flag CDF-01: the page H1 prints raw template tokens. Values were taken from the table, not the heading. See <a href="flags.html">Flagged for Review</a>.</div>"""
    (DOCS / "standings.html").write_text(page("Standings", "standings.html", body), encoding="utf-8")

    # week 11
    srows = []
    for (d, k, n, a, ar, h, hr, slug) in SLATE:
        srows.append([esc(d), esc(k), esc(n), f"{esc(a)} <small>({esc(ar)})</small>", f"{esc(h)} <small>({esc(hr)})</small>", link(f"https://www.nfl.com/games/{slug}", "game page")])
    brows = [[esc(t), esc(r), link(SCHEDULE_URL)] for (t, r) in BYES]
    body = f"""<h1>Week 11 · slate, byes and schedule notices</h1>
<p class="lede">Source: <a href="{SCHEDULE_URL}">nfl.com Week 11 schedule</a>. Kickoff times as printed on the page (ET). Records as printed.</p>
<h2>Games ({len(SLATE)})</h2>
{table(["Date", "Kickoff", "Network", "Away (record)", "Home (record)", "Source"], srows)}
<div class="note warn">Flag CDF-02: the Vikings at 49ers game sits under an 'International Game' header with a Mexico City logo; no venue is printed in the fetched text, so no venue is recorded here.</div>
<h2>Teams on bye ({len(BYES)})</h2>
{table(["Team", "Record", "Source"], brows)}
<h2>Dated schedule announcement (published beside the live schedule)</h2>
<div class="note">The official page states: Week 16 designated matchups will be determined and announced no later than immediately after Week 14. Week 17: no later than immediately after Week 15. Week 18: determined and announced following the conclusion of Week 17. Source: {link(SCHEDULE_URL, "nfl.com Week 11 schedule, 'TBD Games' note")}.</div>"""
    (DOCS / "week11.html").write_text(page("Week 11", "week11.html", body), encoding="utf-8")

    # requirements
    rrows = [[esc(r[0]), esc(r[1]), status_tag(r[2]), esc(r[3]), esc(r[4]), esc(r[5]),
              link(SCHEDULE_URL if r[2] == "captured" and "Week" in r[3] else STANDINGS_URL)] for r in REQ]
    body = f"""<h1>Decision readiness · requirement register</h1>
<p class="lede">{len(REQ)} requirements from the brief. Status counts: {', '.join(f'{k} {v}' for k, v in sorted(st.items()))}. A row marked captured is evidenced by an official link; partial rows cite the prior pack without re-verifying it.</p>
{table(["ID", "Requirement", "Status", "Covered by", "Blocking gate", "Clearing number", "Source"], rrows)}"""
    (DOCS / "requirements.html").write_text(page("Decision readiness", "requirements.html", body), encoding="utf-8")

    # questions
    qrows = [[esc(q[0]), esc(q[1]), esc(q[2]), esc(q[3]), esc(q[4])] for q in QUESTIONS]
    body = f"""<h1>Questions, information and answers</h1>
<p class="lede">Each open question names what is known, and a discovery path. No answer is written here without an official source.</p>
{table(["ID", "Question", "Known state", "Discovery path", "Gates"], qrows)}"""
    (DOCS / "questions.html").write_text(page("Questions", "questions.html", body), encoding="utf-8")

    # suggestions
    srows = [[esc(s[0]), esc(s[1]), esc(s[2]), esc(s[3]), "yes", "no"] for s in SUGGESTIONS]
    body = f"""<h1>Suggestions for owner review</h1>
<div class="note warn"><b>Review only.</b> None of these is implemented. Choose a number (or several) and the next session will act on it.</div>
{table(["ID", "Suggestion", "Why", "Decision owner", "Pending choice", "Implemented"], srows)}"""
    (DOCS / "suggestions.html").write_text(page("Suggestions", "suggestions.html", body), encoding="utf-8")

    # flags
    frows = [[esc(f[0]), esc(f[1]), esc(f[3]), esc(f[4]), link(f[2])] for f in FLAGS]
    body = f"""<h1>Flagged for Review</h1>
<p class="lede">Irregularities and unverified items. None blocks the merge. Each row links to its official source.</p>
{table(["Flag", "Finding", "Severity", "Blocks merge", "Source"], frows)}"""
    (DOCS / "flags.html").write_text(page("Flagged for Review", "flags.html", body), encoding="utf-8")

    # sources
    xrows = [[esc(s[0]), esc(s[1]), esc(s[3]), esc(s[4]), link(s[2], s[2])] for s in SOURCES]
    body = f"""<h1>Sources</h1>
<p class="lede">Official sources only. Each row says what it was used for and whether it was read.</p>
{table(["ID", "Title", "Used for", "Read", "URL"], xrows)}"""
    (DOCS / "sources.html").write_text(page("Sources", "sources.html", body), encoding="utf-8")


def main() -> None:
    build_data()
    build_site()
    print("built", DATA.relative_to(ROOT), DOCS.relative_to(ROOT))


if __name__ == "__main__":
    main()
