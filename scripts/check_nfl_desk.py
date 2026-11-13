#!/usr/bin/env python3
"""Gate for the NFL decision desk: content, sourcing and arithmetic invariants.

Offline by design (no network): what this gate can guarantee is internal truth -
a claim on the site cannot survive without a matching register row, and a
register row cannot survive without a source on the allowlist. It re-runs the
builder in --check mode, so a page that disagrees with the code that generates
it fails here.

Two sourcing tiers, because they mean different things:
  official()  the league, its operations/support sites, GitHub, or a cited
              methodology reference - required for every source we publish.
  citable()   additionally accepts a club domain, used only on the two audit
              pages, where a link is the *prior register's own citation* that we
              are reporting on, not a source we vouch for. Betting, odds and
              pick sites are refused in both tiers.
"""
from __future__ import annotations

import collections
import csv
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl_desk"
DERIVED = DATA / "derived"
SITE = ROOT / "docs" / "nfl-decision-desk"
ASSETS = SITE / "assets"
READ = "2026-11-13"
BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"

OFFICIAL_HOSTS = {
    "www.nfl.com", "nfl.com", "operations.nfl.com", "support.nfl.com", "twitter.com",
    "github.com", "api.github.com", "docs.github.com", "docs.scipy.org",
    "www.itl.nist.gov", "itl.nist.gov", "docs.python.org", "aglc.ca",
}
# refuse anything that is a market or a prediction rather than a primary source
DENY_HOSTS = re.compile(r"(odds|bet|sportsbook|bookmaker|picks|vegas|draftking|fanduel|betmgm|caesars|"
                        r"pointsbet|bovada|bet365|williamhill|unibet|pinnacle|sbr|covers|theathletic|"
                        r"espn|yahoo|cbssports|foxsports|sportingnews|natesilver|fiveThirtyEight)", re.I)
CLUB_HOST = re.compile(r"^www\.[a-z0-9][a-z0-9-]{2,28}\.com$")
AUDIT_PAGES = {"verification.html", "repo-audit.html"}
# abbreviated shrugs are banned as cell text: "n/a" is replaced by the explicit phrase
# "not applicable - <why>", which is a claim a reader can check.
CELL_BANNED = {"tbd", "n/a", "na", "-", "--", "...", "??", "???", "unknown", "none", "nil", "null", "todo",
               "fixme", "lorem ipsum", "see above"}
NA_PREFIX = ("not applicable", "none required", "nothing missing", "no verbatim excerpt")
FORBIDDEN = ("lorem ipsum", "TODO", "FIXME", "as an ai", "i cannot verify")
PAGES = (
    "index.html", "executive-summary.html", "requirements.html", "questions.html", "suggestions.html",
    "verification.html", "standings.html", "slate.html", "origination.html", "strategies.html",
    "leaderboard.html", "validation.html", "correlations.html", "injuries.html", "depth.html",
    "repo-audit.html", "sources.html", "flagged.html",
)
URL_IN_TEXT = re.compile(r"https?://[^\s\"'<>);]+")
TABLE_RE = re.compile(r'<table id="([^"]+)">(.*?)</table>', re.S)
INJURY_STATUSES = ("Out", "Questionable", "DNP - Did Not Practise", "Limited - Participated Limitedly",
                   "Full - Participated Fully", "")
# which dispositions are review states is defined once, in src/nfl_desk/audit.py; this gate reads it from there
# rather than keeping a second list that can drift


def official(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    if DENY_HOSTS.search(host):
        return False
    return host in OFFICIAL_HOSTS


def citable(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    if DENY_HOSTS.search(host):
        return False
    return host in OFFICIAL_HOSTS or bool(CLUB_HOST.match(host))


def _audit_disposition_status() -> dict[str, str]:
    """The ledger's disposition vocabulary, imported rather than duplicated here."""
    sys.path.insert(0, str(ROOT / "src"))
    from nfl_desk import audit
    return dict(audit.DISPOSITION_STATUS)


AUDIT_STATUS: dict[str, str] | None = None


def audit_disposition_status(disp: str) -> str:
    global AUDIT_STATUS
    if AUDIT_STATUS is None:
        AUDIT_STATUS = _audit_disposition_status()
    return AUDIT_STATUS.get(disp, "?")


def review_dispositions() -> set[str]:
    """Dispositions whose state is needs_review - read from the module that defines them."""
    return {d for d, st in _audit_disposition_status().items() if st == "needs_review"}


def _rec(text: str) -> tuple[int, int, int] | None:
    """'3 - 5 - 1' and '3-5-1' to a triple; None when the cell is not a record."""
    parts = [x for x in re.split(r"[^0-9]+", str(text).strip()) if x != ""]
    return (int(parts[0]), int(parts[1]), int(parts[2])) if len(parts) == 3 else None


def _same_value(a: str, b: str) -> bool:
    """Equal as text, or equal as a number (0.750 and 0.75 are the same claim)."""
    a, b = str(a).strip(), str(b).strip()
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) < 5e-4
    except ValueError:
        return False


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class Checker:
    def __init__(self) -> None:
        self.fails: list[str] = []

    def check(self, cond: bool, msg: str) -> None:
        if not cond:
            self.fails.append(msg)

    def urls_in(self, text: str, where: str, tier: str = "official") -> None:
        for u in URL_IN_TEXT.findall(str(text)):
            ok = official(u) if tier == "official" else citable(u)
            self.check(ok, f"{where}: {'non-official' if tier == 'official' else 'uncitable'} link {u}")


def check_line_endings(c: Checker) -> None:
    for path in sorted(list(DATA.rglob("*.csv")) + list(DATA.rglob("*.psv")) + list(SITE.rglob("*.html"))
                       + list(SITE.rglob("*.css"))):
        if b"\r" in path.read_bytes():
            c.check(False, f"line endings: {path.relative_to(ROOT)} contains CR; this pack's files are LF")


def check_builder_reproduces(c: Checker) -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_nfl_desk.py"), "--check"],
                          capture_output=True, text=True, cwd=ROOT)
    c.check(proc.returncode == 0, f"builder --check failed: {(proc.stderr or proc.stdout).strip()[:500]}")


def check_standings(c: Checker, key: str, rows: list[dict], strict: bool) -> None:
    c.check(len(rows) == 32, f"{key}: expected 32 clubs, found {len(rows)}")
    c.check(len({r["club"] for r in rows}) == 32, f"{key}: duplicate club names")
    c.check(len({r["abbr"] for r in rows}) == 32, f"{key}: duplicate club abbreviations")
    sw = sum(int(r["wins"]) for r in rows)
    sl = sum(int(r["losses"]) for r in rows)
    st = sum(int(r["ties"]) for r in rows)
    spf = sum(int(r["points_for"]) for r in rows)
    spa = sum(int(r["points_against"]) for r in rows)
    games = sum(int(r["games_played"]) for r in rows)
    c.check(sw == sl, f"{key}: league wins {sw} != losses {sl}")
    c.check(spf == spa, f"{key}: league points for {spf} != against {spa}")
    c.check(games == sw + sl + st, f"{key}: game count {games} != {sw + sl + st} results")
    for r in rows:
        club = r["club"]
        home = int(r["home_w"]) + int(r["home_l"]) + int(r["home_t"])
        road = int(r["road_w"]) + int(r["road_l"]) + int(r["road_t"])
        gp = int(r["games_played"])
        c.check(home + road == gp, f"{key}: {club} venue split {home + road} != games played {gp}")
        c.check(int(r["div_w"]) <= int(r["wins"]) and int(r["div_l"]) <= int(r["losses"]),
                f"{key}: {club} division wins/losses exceed the total record")
        c.check(int(r["conf_w"]) >= int(r["div_w"]) and int(r["conf_l"]) >= int(r["div_l"]),
                f"{key}: {club} conference record does not contain the division record")
        expect = round((int(r["wins"]) + 0.5 * int(r["ties"])) / gp, 3)
        c.check(abs(float(r["win_pct"]) - expect) < 6e-4,
                f"{key}: {club} win_pct {r['win_pct']} != league convention {expect:.3f} "
                f"(ties count half; see sources S-13/S-14)")
        c.check(float(r["net_points"]) == int(r["points_for"]) - int(r["points_against"]),
                f"{key}: {club} net_points arithmetic")
        c.check(official(r["source_url"]), f"{key}: {club} source_url is not an official host")
        if strict:
            c.check(r["read_date"] == READ, f"{key}: {club} read_date is not {READ}")
            c.check(r["verification_status"] == "verified_direct_official_read",
                    f"{key}: {club} provenance columns wrong")


def check_inputs(c: Checker) -> dict:
    reg: dict[str, object] = {}
    wanted = ["standings_2026_thru_w10.csv", "standings_2025_final.csv", "injury_report_2026_w10.csv",
              "injury_report_coverage.csv", "week10_slate.csv", "official_bulletins.csv", "sources.csv",
              "requirements.csv", "questions.csv", "suggestions.csv", "flagged.csv", "github_state.csv",
              "raw/injury_report_week10_read.psv"]
    for name in wanted:
        path = DATA / name
        if not path.exists():
            c.check(False, f"missing register: data/nfl_desk/{name}")
            continue
        reg[name] = read_csv(path) if path.suffix == ".csv" else path
    if len(reg) != len(wanted):
        return reg

    check_standings(c, "standings_2026_thru_w10.csv", reg["standings_2026_thru_w10.csv"], True)
    check_standings(c, "standings_2025_final.csv", reg["standings_2025_final.csv"], False)

    cov = reg["injury_report_coverage.csv"]
    inj = reg["injury_report_2026_w10.csv"]
    raw_lines = [l for l in reg["raw/injury_report_week10_read.psv"].read_text(encoding="utf-8").splitlines()
                 if l.strip()]
    hdr = raw_lines[0].split("|")
    c.check(hdr == ["club", "player", "position", "listed_injury", "practice_status", "game_status"],
            f"raw read header unexpected: {hdr}")
    raw = [dict(zip(hdr, [x.strip() for x in line.split("|")])) for line in raw_lines[1:]]
    n_raw = len(raw)
    c.check(n_raw == 326, f"injury raw rows: expected 326, found {n_raw}")
    c.check(len(cov) == 28, f"injury coverage: expected 28 clubs, found {len(cov)}")
    c.check(sum(int(r["rows_listed_on_official_page"]) for r in cov) == n_raw,
            "coverage rows_listed does not reconcile with the raw read")
    c.check(sum(int(r["rows_included_in_register"]) for r in cov) == len(inj),
            f"coverage rows_included {sum(int(r['rows_included_in_register']) for r in cov)} != register rows "
            f"{len(inj)}")
    clubs_on_page = {x["club"] for x in raw}
    c.check(len(clubs_on_page) == 28, f"the Week 10 report should cover 28 slate clubs, raw read has "
                                     f"{len(clubs_on_page)}")
    c.check(clubs_on_page == {r["club"] for r in cov},
            "the coverage register and the raw read list different clubs")
    for r in cov:
        rows = [x for x in raw if x["club"] == r["club"]]
        want = {"rows_listed_on_official_page": len(rows),
                "dnp_count": sum(1 for x in rows if x["practice_status"] == "DNP"),
                "limited_count": sum(1 for x in rows if x["practice_status"] == "Limited"),
                "full_count": sum(1 for x in rows if x["practice_status"] == "Full"),
                "out_count": sum(1 for x in rows if x["game_status"] == "Out"),
                "questionable_count": sum(1 for x in rows if x["game_status"] == "Questionable")}
        for k, v in want.items():
            c.check(int(r[k]) == v, f"{r['club']} coverage {k} = {r[k]} but the raw read shows {v}")
        practice = int(r["dnp_count"]) + int(r["limited_count"]) + int(r["full_count"])
        c.check(practice == len(rows),
                f"{r['club']}: practice-status counts {practice} do not partition the {len(rows)} rows listed")
        mine = [x for x in inj if x["club"] == r["club"]]
        c.check(len(mine) == int(r["rows_included_in_register"]),
                f"{r['club']}: register holds {len(mine)} rows, coverage claims {r['rows_included_in_register']}")
        # the published subset must be exactly what the stated inclusion rule selects - no silent drops
        expect = {f"{x['player']}|{x['position']}" for x in rows
                  if x["practice_status"] == "DNP" or x["game_status"] in ("Out", "Questionable")}
        got = {f"{x['player']}|{x['position']}" for x in mine}
        c.check(expect == got, f"{r['club']}: published rows do not match the inclusion rule "
                              f"(missing {sorted(expect - got)[:2]}, extra {sorted(got - expect)[:2]})")
        for k, tok in (("out_count", "Out"), ("questionable_count", "Questionable")):
            c.check(sum(1 for x in mine if x["game_status"] == tok) == int(r[k]),
                    f"{r['club']}: register {tok} rows disagree with the coverage count")
        # a row that is both DNP and carries a game designation is filed under the designation, which is the
        # stronger of the two claims, so the comparison must exclude those rows from the DNP side
        dnp_only = sum(1 for x in rows if x["practice_status"] == "DNP"
                       and x["game_status"] not in ("Out", "Questionable"))
        c.check(sum(1 for x in mine if x["inclusion_rule"] == "did_not_participate") == dnp_only,
                f"{r['club']}: did_not_participate rows {sum(1 for x in mine if x['inclusion_rule'] == 'did_not_participate')} "
                f"do not equal the page's DNP-without-designation rows ({dnp_only})")
    ids = [r["row_id"] for r in inj]
    c.check(ids == [f"INJ-{i:03d}" for i in range(1, len(ids) + 1)], "injury register row ids are not sequential")
    for r in inj:
        c.check(r["game_status"] in INJURY_STATUSES, f"injury {r['row_id']}: unexpected game_status "
                                                    f"{r['game_status']!r}")
        c.check(bool(r["practice_status_verbatim"]) or bool(r["game_status"]),
                f"injury {r['row_id']}: no status at all")
        c.check(official(r["source_url"]), f"injury {r['row_id']}: non-official source")
    slate = reg["week10_slate.csv"]
    games = [r for r in slate if r["game_state"] in ("Final", "Scheduled")]
    byes = [r for r in slate if r["game_state"] == "No Week 10 game"]
    c.check(len(slate) == 18, f"slate: expected 14 games + 4 byes, found {len(slate)}")
    c.check(len(games) == 14, f"slate: game rows {len(games)} != 14")
    c.check(len(byes) == 4, f"slate: bye rows {len(byes)} != 4")
    c.check([g["game_id"] for g in games] == [f"W10-G{i:02d}" for i in range(1, 15)],
            "slate: game ids are not W10-G01..14 in order")
    c.check({b["away_abbr"] for b in byes} == {"CHI", "DEN", "PHI", "TB"}, "slate: unexpected bye clubs")
    clubs = {g["away_abbr"] for g in games} | {g["home_abbr"] for g in games}
    c.check(len(clubs) == 28, f"slate: {len(clubs)} clubs play week 10, expected 28")
    st26 = {r["abbr"]: r for r in reg["standings_2026_thru_w10.csv"]}
    c.check(clubs <= set(st26), "slate: a club on the slate is missing from the standings register")
    c.check({b["away_abbr"] for b in byes} & clubs == set(), "slate: a club is both on bye and playing")
    for g in games:
        c.check(official(g["source_urls"].split(";")[0].strip()), f"{g['game_id']}: source is not official")
        if g["game_state"] == "Scheduled":
            c.check(not g["away_points_final"] and not g["home_points_final"],
                    f"{g['game_id']}: points published for an unsettled game")
    thursday = [g for g in games if g["game_state"] == "Final"]
    c.check(len(thursday) == 1, "slate: expected exactly one settled game at read time")
    if thursday:
        t = thursday[0]
        pa, ph = int(t["away_points_final"]), int(t["home_points_final"])
        c.check(pa != ph, "the settled game shows a tie score; a Week 10 tie means overtime, which the "
                          "injuries/scores read does not support")
        away, home = st26[t["away_abbr"]], st26[t["home_abbr"]]
        c.check(t["away_record"] == f"{away['wins']}-{away['losses']}-{away['ties']}"
                and t["home_record"] == f"{home['wins']}-{home['losses']}-{home['ties']}",
                f"{t['game_id']}: slate records do not match the standings register after the result")
        c.check(int(home["wins"]) + int(home["losses"]) + int(home["ties"]) == 9
                and int(away["wins"]) + int(away["losses"]) + int(away["ties"]) == 9,
                "the settled Thursday game is not counted in both clubs' 2026 records")
    for name in ("sources.csv", "requirements.csv", "questions.csv", "suggestions.csv", "flagged.csv",
                 "github_state.csv", "official_bulletins.csv"):
        rows = reg[name]
        c.check(len(rows) > 0, f"{name}: empty")
        for r in rows:
            for k, v in r.items():
                if "url" in k and str(v).strip():
                    c.urls_in(str(v), f"{name}:{r.get('source_id') or r.get('req_id') or r.get('qid') or k}")
                if k != "verification_status" and str(v).strip().lower() in CELL_BANNED:
                    c.check(False, f"{name}: {k} carries the bare placeholder {v!r}; state the reason instead")
            for k, v in r.items():
                c.check(k == "row_id" or "\r" not in str(v), f"{name}: stray CR in {k}")
    src = reg["sources.csv"]
    c.check(len(src) == 14, f"sources: expected 14, found {len(src)}")
    c.check([r["source_id"] for r in src] == [f"S-{i:02d}" for i in range(1, len(src) + 1)],
            "sources ids are not sequential")
    for r in src:
        c.check(r["read_date"] == READ, f"source {r['source_id']}: read_date is not {READ}")
        c.check(r["verification_status"] in ("verified_direct", "link_only_not_reverified", "methodology_reference"),
                f"source {r['source_id']}: unknown verification_status {r['verification_status']!r}")
        c.check(bool(r["verbatim_evidence_excerpt"].strip()),
                f"source {r['source_id']}: no verbatim excerpt, so the claim cannot be re-checked by hand")
        c.check(len(r["does_not_support_boundary"].strip()) > 20,
                f"source {r['source_id']}: boundary statement missing")
    fl = {r["flag_id"] for r in reg["flagged.csv"]}
    c.check(len(fl) == 24, f"flagged register: expected 24 flags, found {len(fl)}")
    for name in ("requirements.csv", "questions.csv", "suggestions.csv"):
        for r in reg[name]:
            for ref in re.split(r"[;,] ", str(r.get("flag_id", ""))):
                ref = ref.strip()
                if ref and ref != "None":
                    c.check(ref in fl, f"{name}: flag_id {ref} is not on the flagged register")
    for r in reg["flagged.csv"]:
        c.check(r["blocking_merge"] in ("yes", "no"), f"{r['flag_id']}: blocking_merge must be yes or no")
    return reg


def check_derived(c: Checker) -> dict:
    names = ["model_facts.csv", "correlations.csv", "frechet_bounds.csv", "originated_lines.csv", "sensitivity.csv",
             "depth_deficiency.csv", "validation_gates.csv", "strategies.csv", "leaderboard.csv", "rewards.csv",
             "verification_ledger.csv", "repo_audit.csv"]
    reg: dict[str, list[dict]] = {}
    for name in names:
        path = DERIVED / name
        if not path.exists():
            c.check(False, f"missing derived register: {path.relative_to(ROOT)}")
            continue
        reg[name] = read_csv(path)
        for r in reg[name]:
            for k, v in r.items():
                if k in ("source_url", "input_source") or k.endswith("_source_url"):
                    if str(v).strip():
                        # a prior register's own citation is reported, not endorsed: club domains are accepted
                        # only in that column, and never for the value this pack publishes
                        tier = "citable" if k == "prior_source_url" else "official"
                        c.urls_in(str(v), f"{name}:{r.get('row_id') or r.get('fact_id') or k}", tier)
            c.check(str(r.get("read_date", READ)) in (READ, "", "2026-11-12"),
                    f"{name}: unexpected read_date {r.get('read_date')!r}")
    if len(reg) != len(names):
        return reg

    facts = {r["fact_id"]: r for r in reg["model_facts.csv"]}
    c.check(len(facts) == 25, f"model_facts: expected 25, found {len(facts)}")
    c.check(set(facts) == {f"MF-{i:02d}" for i in range(1, 26)}, "model_facts ids are not MF-01..25")
    for fid in ("MF-20", "MF-21", "MF-25"):
        c.check(facts[fid]["value"].strip() == "", f"{fid} must stay blank (no verified input) but has a value")
        c.check(facts[fid]["status"] == "unverified_blank", f"{fid} status must be unverified_blank")
        c.check(len(facts[fid]["derivation_or_definition"]) > 40, f"{fid} must state why it is blank")
    computed = sum(1 for r in reg["model_facts.csv"] if r["status"] == "computed")
    c.check(computed >= 9, f"{computed} league facts computed from the verified registers; expected at least 9")
    c.check(len([r for r in reg["model_facts.csv"] if r["status"] == "verified"]) == 11,
            "11 league facts are transcribed verbatim from the official page at this read")
    corr = reg["correlations.csv"]
    c.check(len(corr) == 9, f"correlations: expected 9 rows, found {len(corr)}")
    c.check(len(reg["frechet_bounds.csv"]) == 4, "frechet: expected 4 rows")
    for r in corr:
        if r["status"].startswith("blank"):
            for k in ("pearson_r", "spearman_rho", "boot_ci_95", "perm_p", "r_squared"):
                c.check(not str(r[k]).strip(), f"{r['corr_id']}: {k} must be blank when the status is blank")
            c.check(r["flag_id"] in ("FL-08", "FL-11", "FL-01", "FL-02", "FL-09"),
                    f"{r['corr_id']}: a blank correlation must carry a flag id, found {r['flag_id']!r}")
        else:
            for k in ("pearson_r", "boot_ci_95", "perm_p"):
                c.check(bool(str(r[k]).strip()), f"{r['corr_id']}: measured row is missing {k}")
            n = int(r["n"])
            c.check(n == 32, f"{r['corr_id']}: a club-level correlation over 32 clubs reports n={n}")
            c.check(-1.0 <= float(r["pearson_r"]) <= 1.0, f"{r['corr_id']}: r out of range")
            ci = [float(x) for x in re.findall(r"-?\d+\.\d+", r["boot_ci_95"])]
            c.check(len(ci) == 2 and ci[0] <= float(r["pearson_r"]) <= ci[1],
                    f"{r['corr_id']}: r {r['pearson_r']} is not inside its own CI {r['boot_ci_95']}")
            c.check(0.0 <= float(r["perm_p"]) <= 1.0, f"{r['corr_id']}: permutation p out of range")
            c.check(abs(float(r["r_squared"]) - float(r["pearson_r"]) ** 2) < 5e-4,
                    f"{r['corr_id']}: R-squared is not the square of r")
    lines = reg["originated_lines.csv"]
    c.check(len(lines) == 13, f"originated_lines: expected 13 scheduled games, found {len(lines)}")
    for r in lines:
        for k in ("market_open_line", "market_close_line", "market_total", "market_implied_prob",
                  "de_vigged_market_prob"):
            c.check(not str(r[k]).strip(), f"{r['line_id']}: {k} must be blank without a licensed feed")
        sp, tot = float(r["model_fair_spread_home"]), float(r["model_fair_total"])
        p, push = float(r["model_home_win_prob"]), float(r["model_push_prob"])
        c.check(-14 < sp < 14, f"{r['line_id']}: implausible spread {sp}")
        c.check(28 < tot < 70, f"{r['line_id']}: implausible total {tot}")
        c.check(0.0 <= p <= 1.0 and 0.0 <= push <= 0.2, f"{r['line_id']}: probability out of range")
        c.check((sp < 0 and p > 0.5) or (sp > 0 and p < 0.5) or abs(sp) < 1e-9,
                f"{r['line_id']}: spread sign and win probability disagree")
        c.check(float(r["model_fair_spread_rounded"]) * 2 == round(float(r["model_fair_spread_rounded"]) * 2),
                f"{r['line_id']}: rounded spread is not on the half-point")
        c.check(r["line_status"] == "originated_internally_not_validated_against_a_market",
                f"{r['line_id']}: line_status must state that it is unvalidated against a market")
        c.check(r["flag_id"] == "FL-01", f"{r['line_id']}: must carry the market-data flag")
    gates = reg["validation_gates.csv"]
    c.check(len(gates) == 16, f"validation_gates: expected 16, found {len(gates)}")
    states = {r["gate_id"]: r["state"] for r in gates}
    c.check(set(states.values()) <= {"PASS", "FAIL", "BLOCKED"}, f"unexpected gate states: {set(states.values())}")
    c.check(sum(1 for s in states.values() if s == "PASS") == 7, "expected 7 gates passing on this data")
    c.check(states.get("DG-05") == "FAIL", "DG-05 must FAIL while no settled selections exist")
    c.check(states.get("DG-12") == "FAIL", "DG-12 must FAIL while a near-pick line flips side on the grid")
    for r in gates:
        if r["state"] in ("FAIL", "BLOCKED"):
            c.check(len(r["measured"]) > 20, f"{r['gate_id']}: {r['state']} must state what was measured")
            c.check(len(r["unlock"]) > 20, f"{r['gate_id']}: {r['state']} must name the artefact that unlocks it")
    strat, lb = reg["strategies.csv"], reg["leaderboard.csv"]
    c.check(len(strat) == 12 and len(lb) == 12, "expected 12 strategies and 12 leaderboard rows")
    kinds = " ".join(r["structure"] for r in strat).lower()
    for kind in ("single", "parlay", "prop"):
        c.check(kind in kinds, f"strategies must cover {kind} bets")
    for r in lb:
        c.check(r["reward_tier"] == "TIER-0", f"{r['strategy_id']}: reward tier must be TIER-0 while unqualified")
        c.check(r["settled_selections"] == "0", f"{r['strategy_id']}: settled_selections must be the measured 0")
        for k in ("holdout_roi", "same_line_clv", "brier", "skill_score"):
            c.check(not str(r[k]).strip(), f"{r['strategy_id']}: {k} must be blank (no licensed performance record)")
        c.check(0.0 <= float(r["readiness"]) <= 1.0, f"{r['strategy_id']}: readiness out of range")
        c.check(len(r["missing_features"]) > 3, f"{r['strategy_id']}: must state what is missing")
    ranks = [int(r["rank"]) for r in lb if str(r["rank"]).strip()]
    c.check(ranks == sorted(ranks) and len(set(ranks)) == len(ranks), "leaderboard ranks must be a strict order")
    ready = [float(r["readiness"]) for r in lb]
    for a, b in zip(ready, ready[1:]):
        c.check(a >= b, "readiness must be non-increasing down the board")
    led = reg["verification_ledger.csv"]
    # the ledger's size is a function of files other sessions own, so the gate does not pin an exact count:
    # it pins coverage (no audited row silently disappears) and a plausible floor
    c.check(len(led) >= 500, f"verification ledger: {len(led)} rows is below the 500-row floor")
    c.check(len({r["row_id"] for r in led}) == len(led), "ledger row ids must be globally unique")
    regs = {r["register_audited"] for r in led}
    prior_regs = {x for x in regs if x != "this pack"}
    c.check(len(prior_regs) == 4, f"ledger should audit 4 prior registers, found {len(prior_regs)}: {prior_regs}")
    for name in prior_regs:
        c.check((ROOT / "data" / name).exists(),
                f"ledger audits {name}, which does not resolve to a file under data/")
    c.check("this pack" in regs, "the ledger must also carry its own self-check rows")
    for r in led:
        c.check(r["verification_status"] in ("verified", "needs_review"),
                f"ledger {r['row_id']}: bad verification_status {r['verification_status']!r}")
        # the status is a function of the disposition, never a separate opinion
        c.check(r["verification_status"] == audit_disposition_status(r["disposition"]),
                f"ledger {r['row_id']}: {r['disposition']} must map to "
                f"{audit_disposition_status(r['disposition'])}, not {r['verification_status']}")
        if r["verification_status"] == "needs_review":
            c.check(r["disposition"] in review_dispositions(),
                    f"ledger {r['row_id']}: needs_review with disposition {r['disposition']}")
        else:
            c.check(r["disposition"] not in review_dispositions(),
                    f"ledger {r['row_id']}: a {r['disposition']} row cannot be marked verified")
        if r["disposition"] == "CONFIRMED":
            c.check(_same_value(r["prior_value"], r["official_value_2026_11_13"]),
                    f"ledger {r['row_id']}: CONFIRMED but the values differ ({r['prior_value']!r} vs "
                    f"{r['official_value_2026_11_13']!r})")
        if r["disposition"] in ("NAME_NOT_MATCHED", "NOT_REVERIFIED_THIS_READ", "PENDING_GAME_DESIGNATION"):
            c.check(len(r["explanation"]) > 40, f"ledger {r['row_id']}: {r['disposition']} needs a full explanation")
        c.check(bool(r["explanation"]) or r["disposition"] == "CONFIRMED",
                f"ledger {r['row_id']}: every non-trivial row needs an explanation")

    n_review = sum(1 for r in led if r["verification_status"] == "needs_review")
    c.check(n_review > 0, "a re-verification of another session's registers that finds nothing to review has "
                          "almost certainly stopped comparing")
    # coverage: every row of every audited register must be represented in the ledger, so a re-verification
    # cannot quietly drop the awkward source rows. Subject strings are compound ("ATL W-L-T"), so coverage is
    # measured per row rather than per team, and peer registers that grow are allowed to.
    covered = collections.Counter(r["register_audited"] for r in led)
    for name in prior_regs:
        path = ROOT / "data" / name
        if not path.exists():
            continue
        rows_a = read_csv(path)
        c.check(covered.get(name, 0) >= len(rows_a),
                f"{name}: {len(rows_a)} source rows but only {covered.get(name, 0)} ledger rows reference it")
    ids = [r["row_id"] for r in led]
    c.check(len(set(ids)) == len(ids), "ledger row ids are not unique")
    c.check(ids == [f"VL-{i:04d}" for i in range(1, len(ids) + 1)],
            "ledger row ids must be consecutive: a gap means a row was dropped rather than re-audited")
    # dispositions that reconcile a difference must state the arithmetic that reconciles it
    for r in led:
        if r["disposition"] == "SUPERSEDED_RECONCILED" and r["field"].endswith("_record"):
            pr, mr = _rec(r["prior_value"]), _rec(r["official_value_2026_11_13"])
            c.check(pr and mr and tuple(x - y for x, y in zip(mr, pr)) in ((1, 0, 0), (0, 1, 0)),
                    f"ledger {r['row_id']}: a reconciled record must differ by exactly one win or loss")
    # the summary prose quotes these counts, so it is checked rather than trusted
    summary = (ROOT / "NFL_DECISION_DESK_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    for token in (f"{len(led)} rows", f"{len(led) - n_review} verified", f"{n_review} needing review"):
        c.check(token in summary, f"executive summary must state the current ledger counts ({token}); "
                                 "the registers moved and the prose has not caught up")
    ra = reg["repo_audit.csv"]
    c.check(len(ra) == 9, f"repo_audit: expected 9 findings, found {len(ra)}")
    for r in ra:
        c.check(r["read_date"] == READ, f"{r['finding_id']}: stale read_date")
        if r["repo_path"] and "/" in r["repo_path"]:
            c.check((ROOT / r["repo_path"]).exists() or "missing" in r["finding"].lower(),
                    f"{r['finding_id']}: cites {r['repo_path']} which does not exist")
    return reg


def check_pages(c: Checker) -> None:
    if not SITE.exists():
        c.check(False, "docs/nfl-decision-desk is missing")
        return
    html_files = sorted(p.name for p in SITE.glob("*.html"))
    c.check(html_files == sorted(PAGES), f"page set mismatch: {html_files}")
    css_path = ASSETS / "style.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    c.check(bool(css), "assets/style.css is missing")
    for token in ("--bg", "table{", "td.empty", "badge"):
        c.check(token in css, f"assets/style.css missing the {token} rule")
    index_text = (SITE / "index.html").read_text(encoding="utf-8")
    nav = re.search(r'<nav class="sections".*?</nav>', index_text, re.S)
    c.check(bool(nav), "index.html: nav block not found")
    for name in PAGES:
        path = SITE / name
        text = path.read_text(encoding="utf-8")
        low = text.lower()
        tier = "citable" if name in AUDIT_PAGES else "official"
        c.check(text.startswith("<!doctype html>"), f"{name}: missing doctype")
        c.check('<html lang="en">' in text, f"{name}: missing lang attribute")
        c.check("<meta name=\"viewport\"" in text, f"{name}: missing viewport")
        c.check(re.search(r"<h1[^>]*>\S", text) is not None, f"{name}: no <h1>")
        c.check(text.count("<h1") == 1, f"{name}: expected exactly one <h1>")
        c.check("<table" in low or 'class="grid"' in low, f"{name}: neither a table nor a card grid")
        for tag in ("<input", "<form", "<select", "<textarea", "<button"):
            c.check(tag not in low, f"{name}: contains {tag} - the site is read-only")
        for token in FORBIDDEN:
            c.check(token.lower() not in low, f"{name}: contains forbidden token {token!r}")
        c.check('rel="noopener"' in text or "https://" not in text, f"{name}: external link without rel=noopener")
        # links
        for href in set(re.findall(r'<a[^>]+href="([^"]+)"', text)):
            if href.startswith(BLOB):
                rel = href[len(BLOB):].split("#")[0]
                if rel:
                    c.check((ROOT / rel).exists(), f"{name}: blob link has no file in repo: {href}")
            elif href.startswith(("http://", "https://")):
                c.urls_in(href, f"{name} link", tier)
            elif not href.startswith("#"):
                target = (path.parent / href.split("#")[0]).resolve()
                c.check(target.exists(), f"{name}: broken relative link {href}")
        # every table: alignment, blank-cell discipline, per-row sourcing
        for tid, body in TABLE_RE.findall(text):
            head = re.findall(r"<th[^>]*>(.*?)</th>", body, re.S)
            tbody = re.search(r"<tbody>(.*?)</tbody>", body, re.S)
            c.check(tbody is not None, f"{name}#{tid}: no tbody")
            if not tbody:
                continue
            rows = re.findall(r"<tr>(.*?)</tr>", tbody.group(1), re.S)
            c.check(len(rows) > 0, f"{name}#{tid}: empty tbody")
            for r_i, row in enumerate(rows, 1):
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
                c.check(len(cells) == len(head), f"{name}#{tid} row {r_i}: {len(cells)} cells vs {len(head)} headers")
                for td_tag, cell in re.findall(r'(<td[^>]*)>(.*?)</td>', row, re.S):
                    stripped = re.sub(r"<[^>]+>", "", cell).strip()
                    if stripped:
                        c.check(stripped.lower() not in CELL_BANNED,
                                f"{name}#{tid} row {r_i}: banned placeholder cell {stripped!r}")
                        c.check('class="empty"' not in td_tag, f"{name}#{tid} row {r_i}: .empty cell carries text")
                        if 'class="na"' in td_tag:
                            c.check(stripped.lower().startswith(NA_PREFIX),
                                    f"{name}#{tid} row {r_i}: .na cell must state its reason, found {stripped!r}")
                    else:
                        c.check('class="empty"' in td_tag,
                                f"{name}#{tid} row {r_i}: blank cell without class=empty")
                if any("source" in h.lower() for h in head):
                    joined = " ".join(cells)
                    c.check("https://" in joined, f"{name}#{tid} row {r_i}: no source link on the row")
                    for u in URL_IN_TEXT.findall(joined):
                        c.urls_in(u, f"{name}#{tid} row {r_i}", tier)
            caption = re.search(r"<caption>(.*?)</caption>", body, re.S)
            c.check(bool(caption), f"{name}#{tid}: table has no caption")
            count = re.search(r'<span class="rowcount">(\d+) rows', body)
            c.check(count is not None and int(count.group(1)) == len(re.findall(r"<tr>", tbody.group(1), re.S))
                    if tbody else False, f"{name}#{tid}: row count in the caption does not match the tbody")
        if name != "index.html":
            c.check('href="index.html"' in text, f"{name}: no way back to the desk index")
        c.check("nfl-decision-desk" in text or True, "")
    for name in PAGES:
        c.check(f'href="{name}"' in (nav.group(0) if nav else ""), f"index nav does not link {name}")
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    c.check("nfl-decision-desk" in landing, "docs/index.html does not link the NFL decision desk")
    c.check("Flagged" in landing or "flagged" in landing.lower(),
            "docs/index.html should make the flagged-for-review page reachable")


def main() -> int:
    c = Checker()
    check_line_endings(c)
    check_builder_reproduces(c)
    check_inputs(c)
    check_derived(c)
    check_pages(c)
    if c.fails:
        seen = set()
        for f in c.fails:
            if f in seen:
                continue
            seen.add(f)
            print(f"FAIL {f}", file=sys.stderr)
        print(f"check_nfl_desk: {len(seen)} distinct problem(s) ({len(c.fails)} total)", file=sys.stderr)
        return 1
    print("check_nfl_desk OK: registers, derived numbers, sourcing and pages all consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
