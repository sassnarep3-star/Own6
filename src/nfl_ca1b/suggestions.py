"""Suggestions review queue.

The brief asks for a dedicated section where someone can review suggestions and
choose the best path BEFORE any change is implemented. So every suggestion is
published with what it costs, what it unblocks, and what it depends on — and
nothing is auto-implemented. Ranked by (unblocks x evidence strength) / effort.

An item is only ranked 'now' when it can be done without answering Q-01 (the
retrieval-terms question) and without a price archive.
"""
from __future__ import annotations

from typing import Dict, List

ROWS: List[Dict[str, object]] = [
    dict(sid="SG-01", title="Re-test the depth-chart route before spending anything on it",
         what="The historical plan was to read 32 club depth charts. The probe this session returned 404 for the path nfl.com/teams/<club>/depth-chart. Test one more club; if it 404s too, close route (a) and stop scheduling work against it.",
         unblocks="R-006, R-011, R-030, R-031 (depth of replacement, jersey-order rejection, depth source)", effort="1 read",
         dependency="none", blocking_question="", recommendation="do now",
         expected_benefit="Stops a whole workstream from being planned against a URL that does not exist."),
    dict(sid="SG-02", title="Publish the club abbreviation map as a first-class table",
         what="Packs store LA and LAR, AZ and ARI, for the same club. A one-page alias table (with the official spelling from the standings page) makes every cross-pack join exact.",
         unblocks="every cross-pack reconciliation, including this session's 971-value audit", effort="1 table, 0 reads",
         dependency="none", blocking_question="", recommendation="do now",
         expected_benefit="Removes the only class of false 'mismatch' found today (5 rows)."),
    dict(sid="SG-03", title="Make the week-10 inactives article the availability spine",
         what="The official inactives article is published once per game and never changes. It is the only page that states which named players did not dress. Capture it every week and join designations to it.",
         unblocks="R-029 (inactive lists), the designation calibration (Q-04), and any 'starters out' claim", effort="1 read per week",
         dependency="none", blocking_question="", recommendation="do now",
         expected_benefit="Turns 'suspected replacement' into 'confirmed inactive' with a dated source."),
    dict(sid="SG-04", title="Keep backtest scores off the leaderboard, permanently",
         what="The leaderboard currently has no ranks because nothing is settled. That is the correct state. Publish walk-forward scores on the backtest page, with the word backtest in the heading, and never let them appear in a rank column.",
         unblocks="R-009, R-035, R-036 (pre-registration, proper-score divisions, ranking with uncertainty)", effort="already implemented",
         dependency="none", blocking_question="", recommendation="keep",
         expected_benefit="Prevents the single most common way a project like this fools its owner."),
    dict(sid="SG-05", title="Get a price archive before any further origination work",
         what="Every market column, ROI, CLV and staking gate is blank because no official page publishes a price. Origination without a price tests nothing that can be traded.",
         unblocks="R-004, R-018, Q-02, Q-06, and the whole staking half of the leaderboard", effort="a licence or an archive contract",
         dependency="owner decision", blocking_question="Q-02", recommendation="owner decision",
         expected_benefit="Turns fair lines into residuals, and residuals into a testable edge."),
    dict(sid="SG-06", title="Answer the retrieval-terms question before automating anything",
         what="Scheduled capture (Wed/Thu/Fri injury snapshots, daily depth snapshots) is the brief's own requirement R-028, but the pages are the league's property. Get written permission or a licensed feed first; until then capture stays manual and dated.",
         unblocks="R-028, Q-01, and every 'automate capture' suggestion below", effort="one written answer",
         dependency="owner decision", blocking_question="Q-01", recommendation="owner decision",
         expected_benefit="Unblocks the only route to a real designation time-series."),
    dict(sid="SG-07", title="Automate the Wednesday-Thursday-Friday injury capture (after SG-06)",
         what="Three dated reads a week for the rest of the season would give about 60 reads by kickoff of week 18 — enough to measure how designations evolve, which is what makes the injury signal a surprise instead of a level.",
         unblocks="R-012, R-021, R-028, Q-04", effort="1 job + storage", dependency="SG-06",
         blocking_question="Q-01", recommendation="blocked",
         expected_benefit="Turns 2 dated reads into a series; the current gap is 2 of the ~40 reads a replay needs."),
    dict(sid="SG-08", title="Prefer play-time evidence over any depth chart",
         what="If a depth chart cannot be verified for all 32 clubs, snap counts are a measurable starter/backup split. Check whether an official snap-count table exists on any nfl.com game page before commissioning more chart parsing.",
         unblocks="R-011 (model depth from playing time, not jersey order), R-029", effort="1 probe per game page",
         dependency="none", blocking_question="", recommendation="do now",
         expected_benefit="Gives a quantitative starter proxy instead of a hand-read chart."),
    dict(sid="SG-09", title="Publish a weekly 'what changed' diff, not a new snapshot",
         what="The repo already stores two dated injury reads. Render the delta (added, removed, practice change, designation change) as the primary artifact and the level as a footnote.",
         unblocks="R-012 (surprise not level), the owner's weekly review", effort="already implemented",
         dependency="none", blocking_question="", recommendation="keep",
         expected_benefit="Makes the site readable week to week instead of being re-read from scratch."),
    dict(sid="SG-10", title="Never publish a club-level injury count without its denominator",
         what="A 'net injury count' is meaningless unless the report's own row count for that club is beside it. Publish both, and leave 'starters out' blank until a line-up source exists.",
         unblocks="R-013, R-039", effort="already implemented", dependency="none",
         blocking_question="", recommendation="keep",
         expected_benefit="Stops a blank from being read as zero."),
    dict(sid="SG-11", title="Score the model on totals before adding any new feature",
         what="The total equation is already fitted and publishes an expected total for every fixture. That is free out-of-sample evidence; collect it before adding inputs.",
         unblocks="Q-09, R-014", effort="already implemented", dependency="none",
         blocking_question="", recommendation="keep",
         expected_benefit="A second, independent test of the ratings with no new data cost."),
]


def rows() -> List[Dict[str, object]]:
    order = {"do now": 0, "keep": 1, "blocked": 2, "owner decision": 3}
    ranked = sorted(ROWS, key=lambda r: (order.get(str(r["recommendation"]), 9), str(r["sid"])))
    out = []
    for i, r in enumerate(ranked, start=1):
        out.append({**r, "queue_position": i})
    return out
