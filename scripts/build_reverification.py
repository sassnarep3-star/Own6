#!/usr/bin/env python3
"""Build and check the line-by-line reverification page.

Source of record: data/line_reverification_2026-11-03.csv
Output:           docs/reverification/index.html

Every row must carry an official https source URL (host allow-list), the date
the official page was read, a short quoted evidence string for any result that
claims a reading, and an owner action for anything that is not "verified".
Rows whose result is "not_checked" carry no read date and no evidence: they
are published as unverified, not as facts.

Usage:
  python3 scripts/build_reverification.py          # write the page
  python3 scripts/build_reverification.py --check  # validate + up-to-date check
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import pathlib
import re
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "line_reverification_2026-11-03.csv"
OUT_PATH = ROOT / "docs" / "reverification" / "index.html"
REPO_BLOB_PREFIX = "https://github.com/sassnarep3-star/Own6/blob/main/"

COLUMNS = [
    "id", "area", "claim_location", "claim_as_published",
    "official_source_url", "official_source_read_on", "official_evidence",
    "result", "action",
]
RESULTS = {
    "verified": "Verified: the official text supports the claim.",
    "mismatch": "Mismatch: the official text contradicts or does not contain the published claim.",
    "unverified": "Unverified: no official text found; value stays blank.",
    "flagged": "Flagged: a rule or as-of issue needs owner action; facts were checked.",
    "carried_forward": "Carried forward: read on an earlier date; not re-read today.",
    "not_checked": "Not checked: published as a limitation, not as a fact.",
}
# Results that assert something was read from an official page.
READ_REQUIRED = {"verified", "mismatch", "unverified", "flagged", "carried_forward"}
# Hosts that may be cited. nba.com and law.go.kr are the official publishers of the
# text checked; github.com / api.github.com are the repo's own official records;
# sassnarep3-star.github.io is the project's live Pages site (subject of R06 only).
ALLOWED_HOSTS = {"www.nba.com", "www.law.go.kr", "github.com", "api.github.com", "sassnarep3-star.github.io"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RESULT_CSS = {
    "verified": "#86efac", "mismatch": "#fca5a5", "unverified": "#fcd34d",
    "flagged": "#fdba74", "carried_forward": "#93c5fd", "not_checked": "#cbd5e1",
}


class ValidationError(Exception):
    pass


def load_rows(path: pathlib.Path = CSV_PATH) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != COLUMNS:
            raise ValidationError(f"columns must be exactly {COLUMNS}, got {reader.fieldnames}")
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def validate_row(row: dict[str, str], repo_root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    rid = row.get("id", "?")
    if not re.fullmatch(r"[LNRS]\d{2}", rid):
        errors.append(f"{rid}: id must look like L01/N01/R01")
    if row["result"] not in RESULTS:
        errors.append(f"{rid}: unknown result '{row['result']}'")
    for col in ("area", "claim_location", "claim_as_published", "official_source_url"):
        if not row[col]:
            errors.append(f"{rid}: empty {col}")
    url = row["official_source_url"]
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_HOSTS:
        errors.append(f"{rid}: source must be https on an allowed official host, got {url!r}")
    if url.startswith(REPO_BLOB_PREFIX):
        rel = url[len(REPO_BLOB_PREFIX):].split("#", 1)[0]
        if not (repo_root / rel).exists():
            errors.append(f"{rid}: repo file does not exist: {rel}")
    read_on = row["official_source_read_on"]
    if row["result"] in READ_REQUIRED:
        if not ISO_DATE.match(read_on):
            errors.append(f"{rid}: result '{row['result']}' needs an ISO read date")
        else:
            try:
                dt.date.fromisoformat(read_on)
            except ValueError:
                errors.append(f"{rid}: invalid read date {read_on}")
        if not row["official_evidence"]:
            errors.append(f"{rid}: result '{row['result']}' needs quoted official_evidence")
    if row["result"] == "not_checked":
        if read_on:
            errors.append(f"{rid}: not_checked must not carry a read date")
        if row["official_evidence"]:
            errors.append(f"{rid}: not_checked must not carry evidence")
    if row["result"] != "verified" and not row["action"]:
        errors.append(f"{rid}: non-verified row needs an action")
    return errors


def validate_all(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for row in rows:
        rid = row.get("id", "")
        if rid in seen:
            errors.append(f"{rid}: duplicate id")
        seen.add(rid)
        errors.extend(validate_row(row))
    if not rows:
        errors.append("no rows")
    return errors


def render(rows: list[dict[str, str]]) -> str:
    counts = {k: 0 for k in RESULTS}
    for r in rows:
        counts[r["result"]] += 1
    e = html.escape

    def badge(result: str) -> str:
        return f'<span class="badge" style="--c:{RESULT_CSS[result]}">{e(result.replace("_", " "))}</span>'

    cards = "".join(
        f'<div class="card"><span class="num">{counts[k]}</span><span class="lbl">{e(k.replace("_", " "))}</span>'
        f'<span class="desc">{e(RESULTS[k])}</span></div>'
        for k in RESULTS
    )
    flagged = [r for r in rows if r["result"] != "verified"]
    flag_items = "".join(
        f'<li><a href="#{e(r["id"])}"><strong>{e(r["id"])}</strong></a> {e(r["area"])}: '
        f'{e(r["claim_as_published"])} <em>({e(r["result"].replace("_", " "))})</em></li>'
        for r in flagged
    )
    body_rows = []
    for r in rows:
        ev = e(r["official_evidence"]) or '<span class="empty">not confirmed</span>'
        body_rows.append(
            f'<tr id="{e(r["id"])}">'
            f'<td><strong>{e(r["id"])}</strong></td>'
            f'<td>{e(r["area"])}</td>'
            f'<td>{e(r["claim_location"])}</td>'
            f'<td>{e(r["claim_as_published"])}</td>'
            f'<td><a href="{e(r["official_source_url"])}" rel="noopener">official source ↗</a></td>'
            f'<td>{e(r["official_source_read_on"]) or "—"}</td>'
            f'<td class="ev">{ev}</td>'
            f'<td>{badge(r["result"])}</td>'
            f'<td>{e(r["action"])}</td>'
            "</tr>"
        )
    table = "\n".join(body_rows)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Line-by-line reverification of Own6 legal, NBA-policy and site claims against official sources, with flagged items for review.">
<title>Line-by-line reverification · Own6</title>
<link rel="stylesheet" href="../assets/style.css">
<style>
  .rv main{{max-width:1240px;margin:0 auto;padding:28px 22px 60px}}
  .rv h1{{font-size:30px;margin:6px 0 10px}}
  .rv .lead{{color:var(--mut);max-width:900px}}
  .rv .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:22px 0}}
  .rv .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:4px}}
  .rv .card .num{{font-size:26px;font-weight:700}}
  .rv .card .lbl{{text-transform:capitalize;font-weight:600}}
  .rv .card .desc{{color:var(--mut);font-size:12px}}
  .rv .callout{{border-left:4px solid #fba94b;background:var(--card);padding:12px 16px;border-radius:8px;margin:18px 0}}
  .rv table{{width:100%;border-collapse:collapse;font-size:13px}}
  .rv th,.rv td{{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
  .rv th{{position:sticky;top:0;background:#0e1426;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}}
  .rv td.ev{{max-width:380px}}
  .rv .badge{{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:700;color:#0b1220;background:var(--c);text-transform:capitalize;white-space:nowrap}}
  .rv .empty{{color:#fca5a5}}
  .rv a{{color:#93c5fd}}
  .rv footer{{color:var(--mut);font-size:12px;margin-top:24px}}
</style>
</head>
<body class="landing rv">
<nav aria-label="Primary navigation"><a class="brand" href="../index.html">OWN6 <span> / RESEARCH LAB</span></a><a href="../hub/index.html">Data hub</a><a href="../verified/index.html">Verified archive</a><a href="../lab/flagged.html">Flagged for Review</a><a href="#table">Full table</a></nav>
<main>
<p class="eyebrow">CHECKED 2026-11-03 · OFFICIAL SOURCES ONLY · NO BETTING ADVICE</p>
<h1>Line-by-line reverification</h1>
<p class="lead">Each row compares one published claim (legal text, NBA policy, repo fact or site value) with the official page it cites. A row is <strong>verified</strong> only when the official text read on the date shown supports it. Anything else is marked and listed under Flagged for Review. Blank means not confirmed, not zero. This is not legal advice: Korean counsel review remains open (flag F01).</p>

<section class="cards" aria-label="Result counts">{cards}</section>

<section class="callout" aria-labelledby="findings">
<h2 id="findings">Key findings (snapshot 2026-11-03)</h2>
<ul>
<li><strong>Korean statute:</strong> 15 of 16 statute rows (L01–L15) match the official 국민체육진흥법 text read today, including the Art. 26 prohibitions and the Art. 47–49 penalties. Art. 54 corporate liability is limited to Art. 47 item 2 (L16, needs a correction). Later-effective versions of some articles exist (L17).</li>
<li><strong>NBA terms:</strong> the §1 reuse/linking limit and the §9 Stats limits (non-commercial use only; no use in connection with any gambling, including legal gambling) are quoted verbatim (N01–N03). Legal review of linking and reuse stays open.</li>
<li><strong>NBA partner list:</strong> the official July 9, 2026 list does not include Brazil, but the repo's policy data does (N06, mismatch). The Oct. 26, 2026 release confirms the integrity framework and the Kalshi/Polymarket partnerships (N04), but does not list the prop restrictions reported by the press (N08–N12). Those stay unverified.</li>
<li><strong>Site consistency:</strong> two validation-gate sets share IDs G1–G8 and G01–G10 with different meanings (R03). The landing page's counts (6 candidates, 10 gates, 0 qualified) match the code and data (R01–R02).</li>
<li><strong>Source-link coverage:</strong> 31 table rows on the verified pages still lack an official link (R04). Those files belong to other sessions, so they are logged as requests, not edited here.</li>
<li><strong>Game results:</strong> 2 of 92 rows were checked against official NBA game pages and match (R07–R08). The other 90 were not re-read today (R09), so the results are not claimed as fully verified.</li>
</ul>
</section>

<section class="callout" aria-labelledby="flags">
<h2 id="flags">Flagged for Review</h2>
<p>These items do not block publication. Each row shows the official source and the action requested.</p>
<ul>{flag_items}</ul>
</section>

<section id="table" aria-labelledby="full">
<h2 id="full">All {len(rows)} rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>ID</th><th>Area</th><th>Where it appears</th><th>Claim as published</th><th>Official source</th><th>Read on</th><th>Official evidence (quoted)</th><th>Result</th><th>Action</th></tr></thead>
<tbody>
{table}
</tbody>
</table></div>
</section>

<footer>
Generated by <code>scripts/build_reverification.py</code> from <a href="{REPO_BLOB_PREFIX}data/line_reverification_2026-11-03.csv">data/line_reverification_2026-11-03.csv</a>. Coordination record: <a href="{REPO_BLOB_PREFIX}COORDINATION.md">COORDINATION.md</a>. Repo-internal facts are linked to the GitHub file they describe. Quoted Korean text is the official wording; English labels are the compiler's summaries and are not official translations.
</footer>
</main>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    rows = load_rows()
    errors = validate_all(rows)
    if errors:
        for err in errors:
            print(f"ERROR {err}", file=sys.stderr)
        return 1
    page = render(rows)
    if check_only:
        if not OUT_PATH.exists() or OUT_PATH.read_text(encoding="utf-8") != page:
            print(f"STALE {OUT_PATH.relative_to(ROOT)}: run python3 scripts/build_reverification.py", file=sys.stderr)
            return 1
        print(f"OK: {len(rows)} rows valid; {OUT_PATH.relative_to(ROOT)} is up to date")
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"WROTE {OUT_PATH.relative_to(ROOT)} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
