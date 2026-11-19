"""The sixteen decision themes this board sorts every suggestion and question into.

Each theme is a *decision the owner can actually take*, not a topic. The text in this file is the
compiler's synthesis of the cited rows in ``data/**/suggestions*.csv`` and ``data/**/questions*.csv``
— the page labels it as such, and every row keeps the file and id of the source rows it summarises.
Nothing here asserts a fact about the world; the facts live in ``reads.py``.
"""
from __future__ import annotations

from typing import Dict, List

#: theme definitions. ``keywords`` are used only as the fallback classifier; ``overrides`` (below)
#: is the authoritative hand-checked assignment for rows whose wording the keywords cannot place.
THEMES: List[Dict[str, str]] = [
    {
        "theme_id": "T01",
        "name": "Rights ceiling on NFL-sourced numbers",
        "decision_question": "What may this project store and republish at all — one manual read per page, a scheduled capture, or a licensed feed?",
        "options": "A. Keep the current rule (one manual read per source per session, derived numbers published, raw rows kept in the repo) and write it down as policy. | B. Ask NFL Enterprises in writing for a stated permission, keep everything behind that answer meanwhile. | C. Licence a commercial data feed and drop the scraping question entirely.",
        "evidence_to_choose": "A written position (permission, refusal, or silence) from NFL Enterprises, or the terms text quoted with the exact clause this project relies on.",
        "why_now": "Every other gate that says 'ask first' points back here: the Wed/Thu/Fri cadence, the private raw store, and any scheduled capture all change shape depending on the answer.",
        "keywords": "rights|licen|licence|terms|consent|commercial|scrap|permission|provenance gate|publication ceiling",
        "brief_items": "Decide the price-data policy before any backtest is published; Split the site into a public analysis layer and a private data layer",
    },
    {
        "theme_id": "T02",
        "name": "Where opening and closing numbers come from",
        "decision_question": "Do we buy a price archive, do we go on without one, or do we publish a residual against a source we are allowed to name?",
        "options": "A. License one market-price source (even a small one) and treat every price column as an ingest, not a rewrite. | B. Freeze the pricing half of the roadmap, say so on the landing page, and rank on Brier/log-loss against the results feed only. | C. Use the site's own originated line as the reference and publish movement of our own number only.",
        "evidence_to_choose": "A quote from a price vendor with retention, timestamp granularity and settlement terms, or a written decision that the pricing half is closed.",
        "why_now": "Five separate packs recorded the same blocked store. Until this is chosen, CLV, ROI, vig decomposition and the closing-line half of every gate stay structurally blank.",
        "keywords": "price|odds|closing|opening line|clv|vig|market line|snapshot of the line|book",
        "brief_items": "Add a price-snapshot store that records opening and closing numbers; Publish the model's fair line, the market line, and the difference; Price a line ourselves and publish the residual against the market",
    },
    {
        "theme_id": "T03",
        "name": "Capture cadence and immutability",
        "decision_question": "How often do we capture, who runs the job, and where do immutable captures live?",
        "options": "A. Three reads a week (Wed, Thu, Fri) into a store outside the static site, each with a hash and a clock. | B. Two reads a week (Wed, Fri), the Friday one before the final line move. | C. Daily reads from Wednesday to kickoff, only for the fixtures we originate.",
        "evidence_to_choose": "A scheduler that survives outside GitHub Pages (a runner with a writable store), plus one demonstrated capture of the same page at two clock times showing the delta.",
        "why_now": "The report page this session read was still on Week 10 the day after Week 10 ended, and the game centre for a Week 11 fixture said the club reports were 'not available at this time' — the cadence has to be scheduled to catch the transitions that matter.",
        "keywords": "cadence|schedule|daily|wednesday|thursday|friday|snapshot|immutable|hash|timestamp|fetch time|clock",
        "brief_items": "Snapshot the nfl.com injury report every Wed, Thu and Fri; Treat the injury report as a timestamped series; Build immutable official availability snapshots; Store every injury-hub read with its clock time; Automate immutable multi-day availability snapshots; Add durable snapshot storage and alerts",
    },
    {
        "theme_id": "T04",
        "name": "Public analysis layer vs private data layer",
        "decision_question": "Which artefacts stay on the published site and which move to a private store?",
        "options": "A. Public site keeps derived indices, ratios and links to the official page; raw row-level captures move to a private store and the site publishes their hashes. | B. Leave everything in the repo and add a data-rights notice per table. | C. Publish nothing but the summary panel and give the owner the CSVs directly.",
        "evidence_to_choose": "The owner's answer to T01, plus one named private destination (bucket or branch) with retention defined.",
        "why_now": "Row-level injury and roster data is already public in this repo. Whether that is intended is a decision, not an accident that should keep compounding.",
        "keywords": "private|public site|row-level|republish|data layer|bucket|retention|storage",
        "brief_items": "Split the site into a public analysis layer and a private data layer; Capture stale depth rows ...; Add durable snapshot storage and alerts",
    },
    {
        "theme_id": "T05",
        "name": "The depth-order source for all 32 clubs",
        "decision_question": "Which source defines depth order — club depth pages, official snap counts, or neither?",
        "options": "A. Route (a): verify the club-hosted depth page club by club, store the raw string, keep the 'Unofficial' label and the page date on every row. | B. Route (b): derive the split from playing time / snap counts once a source that publishes them is verified. | C. Neither: keep depth as an evidence register (who was listed where) and refuse to score deficiency at all.",
        "evidence_to_choose": "A per-club register with 32 dated rows for route (a), or one official per-game snap-count table for route (b). A count below 32 with no route (b) source means the deficiency feature stays unbuilt.",
        "why_now": "This session read the Packers chart (labelled 'Unofficial, Nov. 10, 2026', jersey numbers prefixed, three WR rows and a safety listed in two rows) and the nfl.com roster page links straight to the club depth chart; the Texans chart was not at the conventional club path at all. Route (a) is real and partial, and it is exactly as unreliable as the brief says.",
        "keywords": "depth|starter|string|snap|replacement|backup|slot|jersey|inactive|lineup|48|47|playing time",
        "brief_items": "Model depth slots as groups, not a single starter; Do not model depth from jersey order; Resolve the depth-order source before building the backup-deficiency feature; Fix the two depth-parsing failures; Use snap counts as the starter proxy; Represent shared and empty depth slots faithfully; Add an official depth-chart register",
    },
    {
        "theme_id": "T06",
        "name": "Availability, reserve list and roster turnover",
        "decision_question": "How do we record that a player is off the report because he is on a reserve list, not because he is healthy?",
        "options": "A. Capture every club roster page (status code column) on the same cadence as the report and join on it before calling anyone 'available'. | B. Capture the league transactions hub instead — one page, dated, all clubs. | C. Both, with the roster page as the authority and the transaction page as the alarm.",
        "evidence_to_choose": "A dated register of status codes per club (ACT/RES/RSR/TRC/…) with the legend transcribed, and one worked example where 'not listed' is explained by the reserve list.",
        "why_now": "This session closed one such example: Malik Willis is absent from the Week 10 report because nfl.com's own Dolphins roster lists him 'QB • RES' and the league's article says the Dolphins placed him on injured reserve — but the register in the repo attributes him to Green Bay, which is the wrong club for the question.",
        "keywords": "injur|reserve|ir |injured list|roster|transaction|trade|release|sign|elevat|practice squad|availability|absent",
        "brief_items": "Capture the reserve list so 'not listed' never means 'available'; Run the 32-team roster/IR sweep; Treat roster turnover as a first-class data event; Build the availability graph as a first-class dataset",
    },
    {
        "theme_id": "T07",
        "name": "Corpus, results feed and settlement conventions",
        "decision_question": "Which game log is canonical, how far back does it go, and what happens on a push?",
        "options": "A. Declare one corpus id (season + through-week), publish its boundary on every table, and backfill Weeks 1-9 and prior seasons into it. | B. Keep per-pack corpora and publish a crosswalk instead. | C. Freeze the current corpus and only ever extend forward.",
        "evidence_to_choose": "One file that is named as canonical, with per-week counts that reconcile to the official standings, and a written settlement rule for ties and voids.",
        "why_now": "Four different game counts are in circulation across packs, each internally consistent but each answering a different question — that is precisely how a backtest becomes unfalsifiable.",
        "keywords": "corpus|backfill|results feed|settled|settlement|push|tie|void|standings|reconcil|weeks 1|final score|log",
        "brief_items": "Turn the 136-game log into the pre-registered backtest corpus; Ingest game-level results to make the ratings opponent-aware; Transcribe the venue of every fixture",
    },
    {
        "theme_id": "T08",
        "name": "Model disclosure and the second total estimator",
        "decision_question": "Which estimators are published, and does the model say what it left out?",
        "options": "A. Publish both total estimators with the gap column until a walk-forward comparison picks one; state the home-field term and its interval everywhere it matters. | B. Publish one estimator and its residual only. | C. Add shrinkage/opponent adjustment first, then decide.",
        "evidence_to_choose": "A walk-forward comparison with n and a coverage check (both intervals within five points of the nominal 80 per cent before any winner is declared), from the corpus agreed in T07.",
        "why_now": "Packs already disagree about whether the model uses home field at all; a fair line that does not disclose its omissions looks more precise than it is.",
        "keywords": "model|estimator|total|home field|hfa|shrink|rating|opponent|distribution|key number|calibrat|residual",
        "brief_items": "Publish every model total twice until one wins; Store every model output as a probability plus its inputs; Add a fixture-context feature set; Ingest game-level results to make the ratings opponent-aware",
    },
    {
        "theme_id": "T09",
        "name": "Designation reliability: play rates, not folklore",
        "decision_question": "Does 'Questionable' mean anything yet, and do we use the label as a feature?",
        "options": "A. Score the designation-to-play join first (several seasons of reports against inactive lists), publish play rate with intervals, only then decide whether the label becomes a feature. | B. Use designations only for the surprise signal (change since last read) and never as a level. | C. Drop the label from the model and keep it on the page.",
        "evidence_to_choose": "An archive of past-season reports joined to past-season inactive lists, with a measured play rate and confidence interval per designation.",
        "why_now": "The official report publishes no percentages; a single pregame read is not evidence of a rate. One pack counted 11 designation/outcome pairs, which is a starting point, not a calibration.",
        "keywords": "designation|questionable|doubtful|out |dnp|limited|full participation|practice|play rate|probab|surprise|delta",
        "brief_items": "Calibrate what 'Questionable' means empirically; Score injury-designation reliability before using it as a feature; Make the injury signal a surprise, never a level; Store every injury-hub read with its clock time",
    },
    {
        "theme_id": "T10",
        "name": "Leaderboard governance: promotion, demotion, rewards",
        "decision_question": "What does the board rank, when may a strategy go live, and what is the prize?",
        "options": "A. Rank on benchmark-relative proper scores with a game-clustered lower bound; staking results never move a rank; promotion needs a prospective window and demotion is a mechanical gate run before publication. | B. Add CLV to the rank once prices exist (T02) and keep proper scores as the qualification stage. | C. Two boards: a qualified board and a clearly labelled provisional one, never sorted together.",
        "evidence_to_choose": "The reward currency fixed before any result (non-monetary unless the owner says otherwise), a named promotion/demotion owner, and one demotion-gate run wired into CI rather than written by hand.",
        "why_now": "Every pack currently publishes an empty board with different eligibility text; the moment one board goes live the rules must already be frozen.",
        "keywords": "leaderboard|promot|demot|reward|eligib|rank|board|paper|live strategy|staking|division|escrow",
        "brief_items": "Separate 'signal' from 'staking' in the leaderboard; Define a demotion gate that sends a live strategy back to paper; Use proper-score leaderboard divisions; Add a control baseline to every leaderboard run; Rank with proper scores and uncertainty",
    },
    {
        "theme_id": "T11",
        "name": "Statistical honesty: pre-registration, uncertainty, multiplicity",
        "decision_question": "What must a number carry before the site may print it?",
        "options": "A. Every gate threshold committed to git before the evaluation window opens (commit hash = registration), every published statistic with n and an interval, and a power calculation beside each gate. | B. Add bootstrap intervals and a multiplicity adjustment once n is large enough. | C. Publish point estimates with a plain 'no interval available' label where none exists.",
        "evidence_to_choose": "The pre-registration commit hashes for the strategy set, plus a published power calculation for the smallest effect worth detecting on the corpus from T07.",
        "why_now": "A rule chosen after seeing the data is a licence to find skill in noise; the site already promises a 100-forecast floor in one pack and a 200-event floor in another, and neither is derived from a power calculation.",
        "keywords": "power|interval|confidence|bootstrap|pre-registr|prereg|multiplicit|uncertain|significance|p-hack|frozen|holdout",
        "brief_items": "Pre-register every strategy; Freeze a rule before it sees data; Split data into train, validation and final holdout seasons; Compute correlations only from officially sourced numbers and publish n",
    },
    {
        "theme_id": "T12",
        "name": "Site information architecture and review workflow",
        "decision_question": "One canonical site with an owner decision log, or many per-session dashboards?",
        "options": "A. Declare one canonical pack, link the others as archive, put the decision-readiness table and this suggestions board on the landing page, and give every suggestion row an empty 'your decision' column. | B. Keep per-pack dashboards and add a shared nav strip plus a crosswalk page. | C. Merge everything into one pack and delete the rest.",
        "evidence_to_choose": "The owner's choice of canonical pack, and one confirmation that a decision recorded on the board is honoured by the next session (a named artefact per decision).",
        "why_now": "Sixteen suggestion registers and ten question registers with different schemas already exist; the review cost of that is what this page is paying down.",
        "keywords": "site|page|nav|navigation|dashboard|landing|layout|table|ui|accessib|mobile|glossar|archiv|canonic|crosswalk|diff report|what changed",
        "brief_items": "Put a decision-readiness table on the landing page; Publish a weekly 'what changed' diff; Make suggestions on how to improve the site",
    },
    {
        "theme_id": "T13",
        "name": "Tooling: drift alarms, link probes, build determinism",
        "decision_question": "What fails the build when the source changes shape?",
        "options": "A. Pin every parser to expected row counts and required fields and fail loudly; add a nightly HEAD probe of every cited URL; keep the rebuild-and-diff check in CI. | B. Only probe on demand, keep the row-count alarms. | C. Add alerting to the capture store as well (freshness and schema change).",
        "evidence_to_choose": "One demonstrated failure: a parser that breaks on a removed field in a test fixture and a build that goes red because of it.",
        "why_now": "Blank cells are currently indistinguishable from absent data unless a contract catches it; that is the failure mode the brief calls out for the Texans and Packers depth pages.",
        "keywords": "drift|alarm|alert|monitor|checker|probe|ci|build|determin|hash check|broken link|regression|contract|fail",
        "brief_items": "Add a drift alarm to every scraper; Add durable snapshot storage and alerts",
    },
    {
        "theme_id": "T14",
        "name": "Coordination, ownership and merge process",
        "decision_question": "How do parallel sessions stop duplicating and contradicting each other?",
        "options": "A. Split COORDINATION.md into a live task board plus an append-only archive; feature branches never regenerate shared inventories; every board row carries an artefact path that a checker proves exists. | B. Keep one file and add a staleness alarm (a row claiming 'in progress' with no commit in 60 minutes is reported). | C. Name an integration session for each publishing round.",
        "evidence_to_choose": "A green checker that proves every path named on the board exists on main, plus one board row closed with its artefact hash.",
        "why_now": "This session's own audit found board rows that name files which are not in the repository, and tasks still marked 'in progress' for a pack that has already merged.",
        "keywords": "coordination|board|session|merge|conflict|claim|scope|handoff|ownership|integration|duplicate|dedup",
        "brief_items": "Parallel sessions coordinate in COORDINATION.md; Shared outputs change only in the integration session",
    },
    {
        "theme_id": "T15",
        "name": "Fixture context: venue, roof, weather, rest, internationals",
        "decision_question": "Which published schedule facts become features, and from what source?",
        "options": "A. Transcribe venue and stadium from each game centre's Game Info block, keep roof/surface blank until an official register is found, and take weather from the public government forecast service keyed by stadium coordinates. | B. Skip weather entirely; keep venue and rest/bye only. | C. Add the international-slate adjustments (travel, kickoff hour) as an explicit flag, not a number.",
        "evidence_to_choose": "A venue row for every fixture we originate (this session read one: 'RELIANT STADIUM', 'HOUSTON, TX' on the Colts-Texans game centre), an official roof/surface designation per stadium, and a stadium coordinate table.",
        "why_now": "Totals and passing volume are the markets most exposed to a roof and a wind reading, and a 9:30 a.m. ET kickoff in Munich is already in the Week 10 slate.",
        "keywords": "venue|stadium|roof|surface|turf|weather|wind|nws|noaa|forecast|rest|bye|kickoff|munich|frankfurt|london|madrid|international|travel",
        "brief_items": "Add a fixture-context feature set built only from published schedule facts; Stadium Roof/Surface & NWS overlay; Transcribe the venue of every fixture; Publish the league's dated schedule announcement",
    },
    {
        "theme_id": "T16",
        "name": "Combos: parlays, SGP and player props",
        "decision_question": "What may a combo be ranked on, and what stays refused?",
        "options": "A. Keep the joint-evidence gate: no combo is ranked until a directly validated joint probability and the operator's void/push rules both exist. | B. Publish copula-based combo pricing as a research artefact only, clearly not tradeable. | C. Ingest official per-player game statistics first so prop legs can settle at all.",
        "evidence_to_choose": "Paired residual samples for the specific leg pairs (n stated), one operator rule document per combo shape, and a per-player official stat source.",
        "why_now": "Multiplying marginal probabilities is invalid under dependence; without a joint estimate the combo family is arithmetic, not a signal.",
        "keywords": "parlay|combo|sgp|prop|joint|dependen|correlat|copula|leg|multip",
        "brief_items": "Keep parlays and prop combos behind a joint-evidence gate; Compute correlations only from officially sourced numbers; Originate the side first, then the total, then the moneyline",
    },
]

#: Rows whose wording the keyword classifier cannot place, checked by hand against the source file.
#: Key is ``pack|kind|local_id``. Anything not listed here falls back to the classifier.
OVERRIDES: Dict[str, str] = {
    "nfl|suggestions|S01": "T12",
    "nfl|suggestions|S02": "T12",
    "nfl|suggestions|S03": "T05",
    "nfl_origination|suggestions|SUG-01": "T12",
    "nfl_origination|suggestions|SUG-02": "T12",
    "nfl_origination|suggestions|SUG-03": "T12",
    "nfl_origination|suggestions|SUG-09": "T13",
    "nfl_origination|suggestions|SUG-10": "T14",
    "nfl_origination|suggestions|SUG-12": "T06",
    "nfl_origination|suggestions|SUG-13": "T11",
    "nfl_b72e2687|suggestions|B72-S06": "T11",
    "nfl_b72e2687|suggestions|B72-S10": "T11",
    "nfl_origination|suggestions|SUG-14": "T07",
    "nfl_309921cc|suggestions|NFL3-SUG-01": "T12",
    "nfl_309921cc|suggestions|NFL3-SUG-02": "T12",
    "nfl_309921cc|suggestions|NFL3-SUG-03": "T13",
    "nfl_309921cc|suggestions|NFL3-SUG-04": "T12",
    "nfl_309921cc|suggestions|NFL3-SUG-09": "T14",
    "nfl_309921cc|suggestions|NFL3-SUG-10": "T14",
    "nfl_309921cc|suggestions|NFL3-SUG-11": "T12",
    "nfl_309921cc|suggestions|NFL3-SUG-14": "T10",
    "nfl_3b81013c|suggestions|S-01": "T12",
    "nfl_3b81013c|suggestions|S-06": "T11",
    "nfl_3b81013c|suggestions|S-08": "T12",
    "nfl_3b81013c|suggestions|S-10": "T01",
    "nfl_3b81013c|suggestions|S-11": "T12",
    "nfl_3b81013c|suggestions|S-12": "T13",
    "nfl_48217a55|suggestions|SUG-07": "T11",
    "nfl_48217a55|suggestions|SUG-09": "T12",
    "nfl_48217a55|suggestions|SUG-10": "T13",
    "nfl_48217a55|suggestions|SUG-12": "T10",
    "nfl_48217a55|suggestions|SUG-15": "T12",
    "nfl_48217a55|suggestions|SUG-16": "T07",
    "nfl_67233566|suggestions|SG-12": "T14",
    "nfl_6cefc476|suggestions|N6CF-S06": "T10",
    "nfl_6cefc476|suggestions|N6CF-S08": "T12",
    "nfl_6cefc476|suggestions|N6CF-S09": "T11",
    "nfl_6cefc476|suggestions|N6CF-S11": "T10",
    "nfl_6cefc476|suggestions|N6CF-S12": "T01",
    "nfl_8362b702|suggestions|SG-03": "T08",
    "nfl_8362b702|suggestions|SG-06": "T12",
    "nfl_a411fed0|suggestions|A10-S01": "T02",
    "nfl_a411fed0|suggestions|A10-S04": "T08",
    "nfl_a411fed0|suggestions|A10-S05": "T10",
    "nfl_a411fed0|suggestions|A10-S09": "T11",
    "nfl_a411fed0|suggestions|A10-S10": "T16",
    "nfl_a411fed0|suggestions|A10-S11": "T10",
    "nfl_a411fed0|suggestions|A10-S12": "T14",
    "nfl_d966f630|suggestions|D966-S03": "T07",
    "nfl_d966f630|suggestions|D966-S06": "T02",
    "nfl_d966f630|suggestions|D966-S07": "T05",
    "nfl_d966f630|suggestions|D966-S09": "T10",
    "nfl_d966f630|suggestions|D966-S10": "T10",
    "nfl_e5e38f9e|suggestions|E5-S02": "T10",
    "nfl_e5e38f9e|suggestions|E5-S04": "T12",
    "nfl_e5e38f9e|suggestions|E5-S08": "T11",
    "nfl_e5e38f9e|suggestions|E5-S10": "T10",
    "nfl_f4|suggestions|S05": "T08",
    "nfl_f4|suggestions|S06": "T15",
    "nfl_f4|suggestions|S08": "T10",
    "nfl_f4|suggestions|S09": "T13",
    "nfl_f4|suggestions|S10": "T12",
    "nfl_market|suggestions|S-01": "T08",
    "nfl_market|suggestions|S-02": "T10",
    "nfl_market|suggestions|S-03": "T11",
    "nfl_market|suggestions|S-06": "T01",
    "nfl_market|suggestions|S-07": "T12",
    "nfl_wk|suggestions|SG-04": "T12",
    "nfl_wk|suggestions|SG-12": "T13",
    "nfl_wk|suggestions|SG-13": "T07",
    "nfl_wk|suggestions|SG-14": "T12",
    "nfl_wk|suggestions|SG-15": "T12",
    "nfl_wk|suggestions|SG-16": "T12",
    "nfl_wk|suggestions|SG-17": "T12",
    "nfl_wk|suggestions|SG-18": "T13",
    "nfl_wk|suggestions|SG-19": "T14",
    "nfl|questions|Q08": "T11",
    "nfl_3b81013c|questions|Q-04": "T08",
    "nfl_6cefc476|questions|N6CF-Q13": "T02",
    "nfl_e5e38f9e|questions|Q-E5-14": "T14",
    "nfl_wk|questions|Q-16": "T07",
    "nfl_wk|questions|Q-19": "T01",
    # Rows from session b72e2687 whose wording the keyword fallback cannot place. Hand-checked
    # 2026-11-19 by d713b52f: S06 publishes the removal-of-luck panel (statistical honesty), S10
    # pre-registers a baseline before it sees data (same theme). Assignment only — no text edited.
}

THEME_IDS = [t["theme_id"] for t in THEMES]
BY_ID = {t["theme_id"]: t for t in THEMES}


def classify(pack: str, kind: str, local_id: str, haystack: str) -> str:
    """Return the theme id for one register row.

    Overrides win; otherwise the theme with the most keyword hits wins; ``T00`` means the
    classifier could not place the row and a human must (the verifier fails on any T00).
    """
    key = f"{pack}|{kind}|{local_id}"
    if key in OVERRIDES:
        return OVERRIDES[key]
    text = haystack.lower()
    best, best_hits = "T00", 0
    for theme in THEMES:
        hits = 0
        for kw in theme["keywords"].split("|"):
            kw = kw.strip().lower()
            if kw and kw in text:
                hits += 1
        if hits > best_hits:
            best, best_hits = theme["theme_id"], hits
    return best


def theme_names() -> Dict[str, str]:
    return {t["theme_id"]: t["name"] for t in THEMES}
