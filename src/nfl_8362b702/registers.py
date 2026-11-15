"""Flagged register, source register, questions, suggestions, price policy."""
from __future__ import annotations

from .capture import (CAPTURE_ATTEMPTS, GB_ROSTER_URL, INJURY_URL,
                      STANDINGS_URL, TB_DET_GAME_URL, WEEK10_SCHED_URL,
                      WEEK11_SCHED_URL)

SOURCES = [
    ("SRC-01", "NFL.com league standings 2026 (REG)", STANDINGS_URL,
     "2026-11-15T23:26:00Z", "32 club rows; W-L-T/PCT/PF/PA/NET/HOME/ROAD/DIV/CONF/STRK read verbatim"),
    ("SRC-02", "NFL.com weekly schedule weeks 1-9 (the 136-game log)",
     "https://www.nfl.com/schedules/2026/by-week/week-{1..9}", "2026-11-15T23:45:00Z",
     "136 FINAL cards with scores; only cards printing FINAL are results"),
    ("SRC-03", "NFL.com weekly schedule week 10", WEEK10_SCHED_URL, "2026-11-15T23:35:00Z",
     "14 cards: 9 FINAL, 3 live (score strings kept but never results), 2 scheduled"),
    ("SRC-04", "NFL.com weekly schedule week 11", WEEK11_SCHED_URL, "2026-11-15T23:28:00Z",
     "13 fixtures + 6-club bye panel; card dates/kickoffs/networks verbatim"),
    ("SRC-05", "NFL.com official injury report hub (WEEK 10)", INJURY_URL, "2026-11-15T23:58:00Z",
     "155 player rows across 13 club tables (chunks 0-2), every column verbatim"),
    ("SRC-06", "NFL.com Green Bay Packers roster page", GB_ROSTER_URL, "2026-11-16T00:02:00Z",
     "41 non-ACT rows with the page's own status codes; no legend published"),
    ("SRC-07", "NFL.com game centre TB at DET (week 11)", TB_DET_GAME_URL, "2026-11-15T23:27:00Z",
     "Game Info block: Stadium FORD FIELD, Location DETROIT, MI"),
    ("SRC-08", "NFL.com Terms and Conditions", "https://www.nfl.com/legal/terms/",
     "carried read (sibling packs 2026-11-13/14)", "§1.3 limits use to individual non-commercial "
     "informational purposes and prohibits systematic retrieval to build a database without consent"),
]

FLAGGED = [
    ("FLAG-01", "high", "standings page internal inconsistency",
     "MIN home splits 3-1-0 + road splits 4-2-0 sum to 7-3-0 while the W-L-T row and PCT "
     "print 7-2-0 (.778 = 7/9). All 32 clubs were checked; only MIN fails the identity.",
     "home_rec/road_rec kept verbatim, identity check published, nothing rewritten",
     "re-read the standings page after week 10 completes and ask the league which cells are stale",
     STANDINGS_URL),
    ("FLAG-02", "high", "rights boundary",
     "NFL.com Terms §1.3 (carried verified read) limits use to individual non-commercial "
     "informational purposes and prohibits systematic retrieval to compile a database without "
     "express prior written consent.",
     "every value is a single manual read with its clock; no automated harvester runs in CI; "
     "capture attempts logged with outcomes",
     "obtain written consent or a licence before any scheduled automation (G-SCHED) or "
     "commercial use; see questions.csv Q-01",
     "https://www.nfl.com/legal/terms/"),
    ("FLAG-03", "high", "roster state unknown (not listed ≠ available)",
     "Malik Willis appears nowhere on the GB roster page read 2026-11-16T00:02Z — no row with "
     "any status code, and no IR row. A sibling pack recorded him on injured reserve on "
     "2026-11-13/14. His current state is unknown at this read.",
     "absence published as its own row with interpretation 'unknown'",
     "check the club's official transactions page or a dated league transaction wire",
     GB_ROSTER_URL),
    ("FLAG-04", "medium", "name/slug conflict on one official row",
     "GB roster row prints display name 'Zach Bako-Bewele' with player URL slug 'zach-tom' "
     "(50 | G | RES). The row names two different people.",
     "kept verbatim as both strings; not reconciled or corrected",
     "report to the site publisher; do not merge identities without a second official source",
     GB_ROSTER_URL),
    ("FLAG-05", "medium", "week-1 card date vs window header",
     "The week-1 page's SNF header reads 'Sunday Night Football, September 9th' while the game "
     "card's date line reads 'Wednesday, September 9th'. The card string is kept verbatim.",
     "date_on_card kept exactly as printed; both strings published",
     "re-read the week-1 page; ask the publisher which is authoritative",
     "https://www.nfl.com/schedules/2026/by-week/week-1"),
    ("FLAG-06", "high", "no official market prices exist",
     "No official NFL page publishes opening or closing betting numbers. Every market/price/"
     "CLV/ROI-dependent cell in this pack is blank by rule, not by omission.",
     "price_policy.csv records the policy; G-PRICE fails closed",
     "licence a timestamped price archive (opening + closing) before any price-dependent number",
     "https://www.nfl.com/legal/terms/"),
    ("FLAG-07", "high", "official Game Books not reachable",
     "Actual starters and game-day inactives live in NFL Game Books; no game book was reachable "
     "this session (no official PDF URL discovered from an official page).",
     "every actual_start/replacement_named cell blank and gated at G-GAMEBOOK",
     "locate the official game-book URL pattern (from an official page) and parse 32 books",
     TB_DET_GAME_URL),
    ("FLAG-08", "low", "week-scoped injury URL 404",
     "https://www.nfl.com/injuries/2026/week-11 returns 404; the hub renders the current week "
     "with a WEEK 1..WEEK 10 selector. Logged as a capture attempt, not retried blindly.",
     "attempt logged in capture_attempts.csv with outcome",
     "use the hub + week selector when week-11 designations publish (Wed of game week)",
     "https://www.nfl.com/injuries/2026/week-11"),
    ("FLAG-09", "medium", "roster status codes have no legend",
     "The roster page prints ACT/CUT/DEV/PUP/RES/RSR/TRC/TRD/TRT with no legend. Codes are "
     "published verbatim and are not expanded to invented meanings.",
     "codes kept as-is; RES/PUP/RSR treated as 'reserve section' only in the structural sense "
     "labelled on the page",
     "ask the publisher for a legend before any code becomes a feature",
     GB_ROSTER_URL),
    ("FLAG-10", "high", "week-11 forecasts are personnel-blind",
     "The hub still renders WEEK 10 at read time; no week-11 designations exist yet. The "
     "week-11 forecasts therefore use no personnel inputs at all — recorded in each output row.",
     "model outputs record 'neutral_site' and roster inputs only; no injury feature exists",
     "re-run personnel ablations after G-SWEEP closes and week-11 designations publish",
     INJURY_URL),
    ("FLAG-11", "medium", "'resting player' rows carry game-status Out",
     "JAX rows (Jessie Bates, Jordan Davis) print injury text 'Not injury related - resting "
     "player' with game status 'Out'. A designation mixes rest and injury; calibration studies "
     "must split these before any label becomes a feature.",
     "rows captured verbatim with their injury text",
     "G-CAL: split rest vs injury before scoring designation reliability",
     INJURY_URL),
    ("FLAG-12", "low", "standings read straddles live week-10 games",
     "At 2026-11-15T23:26Z the standings excluded the three live cards (LA-AZ, SEA-LV, SF-DAL) "
     "and the scheduled SNF/MNF games. Team game counts therefore range 8-10.",
     "read_at published per row; reconciliation marks those clubs 'not-comparable'",
     "take standings read B after MNF (2026-11-17) for a clean week-10 close",
     STANDINGS_URL),
]

QUESTIONS = [
    ("Q-01", "rights", "May this project store and republish NFL-sourced numbers at all?",
     "NFL.com Terms §1.3 read by sibling packs 2026-11-13/14 (individual non-commercial use only)",
     "written consent/licence naming this use", "BLOCKED",
     "send a written request to NFL Enterprises describing the exact use; record the reply verbatim",
     "https://www.nfl.com/legal/terms/"),
    ("Q-02", "prices", "Where can timestamped opening and closing numbers be licensed?",
     "nothing official; no price row exists in the repo", "a licensed odds archive with timestamps",
     "BLOCKED", "request quotes from licensed odds providers; compare archive retention + settlement terms",
     "https://www.nfl.com/legal/terms/"),
    ("Q-03", "game books", "What is the official URL pattern for NFL Game Books?",
     "the game centre page shows overview/stats only", "a game-book link discovered from an official page",
     "OPEN", "read the game centre's tabs and Football Operations pages for a game-book link",
     TB_DET_GAME_URL),
    ("Q-04", "snap counts", "Does an official snap-count table exist and where?",
     "nothing read this session", "one official snap table per game", "OPEN",
     "check the game centre stats tab and Football Operations publications", TB_DET_GAME_URL),
    ("Q-05", "roster", "What happened to Malik Willis between 2026-11-13 and 2026-11-15?",
     "prior pack recorded IR; my read shows no roster row at all", "a dated transactions record",
     "OPEN", "read the club's official transactions/news page; capture it with a date",
     GB_ROSTER_URL),
    ("Q-06", "depth", "Which verified source defines depth order for all 32 clubs?",
     "club charts are undated and partly images (Texans)", "32 dated structured charts OR official snaps",
     "OPEN", "resolve route (a) club-by-club or route (b) snap counts before any deficiency feature",
     "https://www.nfl.com/teams/green-bay-packers/roster/"),
    ("Q-07", "weather", "Is there an official roof/surface register and an NWS grid per venue?",
     "venue names captured (game centre)", "1 official roof/surface source + NWS point reads",
     "OPEN", "read stadium pages for roof/surface; use api.weather.gov grids keyed by venue lat/lon",
     TB_DET_GAME_URL),
]

SUGGESTIONS = [
    ("SG-01", "site", "Put the decision-readiness table on the root landing page beside the pack cards",
     "the brief asks for one row per requirement with gate + number at the landing page",
     "high", "low", "an integration-session edit to docs/index.html (shared file)",
     "awaiting_choice", "not_implemented"),
    ("SG-02", "data", "Close G-SWEEP first: capture 32 club roster/IR pages before any team-level model",
     "every deficiency feature is blocked on it; the sweep is cheap relative to its payoff",
     "high", "medium", "32 fetches + the rights question Q-01", "awaiting_choice", "not_implemented"),
    ("SG-03", "method", "Publish the second total estimator and keep both visible until walk-forward decides",
     "the brief demands two totals with a gap column; one estimator hides its own fragility",
     "medium", "medium", "needs a second model + n >= 32 settled games", "awaiting_choice", "not_implemented"),
    ("SG-04", "process", "Make the capture schedule Wed/Thu/Fri only after Q-01 is answered in writing",
     "automated retrieval collides with Terms §1.3 without consent; the brief forbids manual input",
     "high", "high", "licence/consent first", "awaiting_choice", "not_implemented"),
    ("SG-05", "data", "Add a transactions-log capture so roster turnover becomes machine-visible",
     "the Willis disappearance shows roster state is not durable between reads",
     "medium", "medium", "needs an official transactions source (Q-05)", "awaiting_choice", "not_implemented"),
    ("SG-06", "site", "Add the what-changed diff page to the weekly cadence once read B reads are scheduled",
     "two reads in one session prove the mechanism; a weekly cadence proves the habit",
     "medium", "low", "depends on SG-04", "awaiting_choice", "not_implemented"),
]

PRICE_POLICY = [
    ("P-01", "No backtest or forecast number in this pack is price-dependent; none is published.",
     "active"),
    ("P-02", "Opening/closing price columns may exist as schema, but stay empty until a licensed, "
             "timestamped feed is attached; empty never means zero.", "active"),
    ("P-03", "No settlement, ROI, CLV or payout figure may be published without both price rows "
             "(open AND close) and an official final.", "active"),
    ("P-04", "If a price source appears later, it must carry: market id, timestamp with zone, "
             "source name, and an immutable row id, or it is rejected.", "active"),
]


def sources_rows():
    return [{"source_id": a, "title": b, "url": c, "read_on_utc": d, "what_was_read": e}
            for a, b, c, d, e in SOURCES]


def flagged_rows():
    return [{"flag_id": a, "severity": b, "category": c, "issue": d,
             "what_was_done": e, "remediation": f, "source_url": g}
            for a, b, c, d, e, f, g in FLAGGED]


def questions_rows():
    return [{"question_id": a, "topic": b, "question": c, "what_we_have": d,
             "what_we_lack": e, "status": f, "discovery_route": g, "source_url": h}
            for a, b, c, d, e, f, g, h in QUESTIONS]


def suggestions_rows():
    return [{"suggestion_id": a, "area": b, "suggestion": c, "reasoning": d,
             "priority": e, "effort": f, "cost_or_risk": g,
             "state": h, "implementation": i}
            for a, b, c, d, e, f, g, h, i in SUGGESTIONS]


def price_policy_rows():
    return [{"policy_id": a, "rule": b, "state": c} for a, b, c in PRICE_POLICY]


def attempt_rows():
    return [{"read_at_utc": t, "url": u, "intent": i, "outcome": o, "note": n}
            for t, u, i, o, n in CAPTURE_ATTEMPTS]
