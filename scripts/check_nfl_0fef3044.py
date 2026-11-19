#!/usr/bin/env python3
"""Check the 0fef3044 Week-11 injury capture pack: regenerate, compare, and verify links."""
from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_nfl_0fef3044 as b  # noqa: E402

FAILS: list[str] = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    print(("  ok   " if cond else "  FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def main() -> int:
    raw = b.RAW.read_bytes()
    parsed = b.parse(raw.decode("utf-8"))
    problems = b.validate(parsed)
    ok("transcription passes drift checks", not problems, "; ".join(problems))
    ok("13 game headers", len(parsed["games"]) == 13)
    ok("26 clubs on report (24 with rows + 2 clean)", len({r["club"] for r in parsed["rows"]}) == 24
       and len(parsed["club_status"]) == 2)
    absent = b.ALL_CLUBS - ({r["club"] for r in parsed["rows"]} | {c["club"] for c in parsed["club_status"]})
    ok("six absent clubs equal the schedule bye list", absent == b.EXPECTED_BYE_CLUBS, str(sorted(absent)))

    rows_csv = list(csv.DictReader((b.PACK / "injury_week11_rows.csv").open(encoding="utf-8")))
    ok("committed row CSV matches the transcription", len(rows_csv) == len(parsed["rows"]))
    ok("every row has an https official source_url",
       all(r["source_url"] == b.SOURCE_URL and r["source_url"].startswith("https://www.nfl.com/") for r in rows_csv))
    ok("every row has a player name and a practice status", all(r["player"] and r["practice_status"] for r in rows_csv))

    recon = b.reconcile(parsed)
    ok("every game pairing matches the official schedule read", all(r["matches_slate_pairing"] == "yes" for r in recon))
    ok("every kickoff matches the official schedule read", all(r["matches_slate_kickoff"] == "yes" for r in recon))

    cross = b.cross_read(parsed, raw.decode("utf-8"))[0]
    ok("row-for-row match with the independent 11:07Z same-day read (ade166a4)",
       cross["exact_row_matches"] == len(parsed["rows"]) == cross["other_read_player_rows"]
       and cross["only_in_this_read"] == 0 and cross["only_in_other_read"] == 0, str(cross))

    log = list(csv.DictReader((b.PACK / "capture_log.csv").open(encoding="utf-8")))
    ok("capture log hash equals the raw transcription hash",
       log[0]["raw_sha256_of_transcription"] == hashlib.sha256(raw).hexdigest())
    ok("capture log states official-bytes hash is unavailable", "not available" in log[0]["official_bytes_hash"])

    # Regenerate every committed output and compare byte-for-byte.
    before = {p: p.read_bytes() for p in b.PACK.glob("*.csv")}
    before.update({p: p.read_bytes() for p in b.DOCS.glob("*.html")})
    rc = b.main([])
    ok("build exits cleanly", rc == 0)
    after = {p: p.read_bytes() for p in b.PACK.glob("*.csv")}
    after.update({p: p.read_bytes() for p in b.DOCS.glob("*.html")})
    ok("regenerated outputs are byte-identical to committed ones", before == after)

    for name in ("index.html", "flagged.html"):
        text = (b.DOCS / name).read_text(encoding="utf-8")
        links = re.findall(r'href="([^"#]+)"', text)
        local = [l for l in links if not l.startswith(("http", "mailto"))]
        missing = [l for l in local if not (b.DOCS / l).exists()]
        ok(f"{name}: local links resolve", not missing, str(missing))
    idx = (b.DOCS / "index.html").read_text(encoding="utf-8")
    ok("index shows the row count", str(len(parsed["rows"])) in idx)
    ok("index carries the not-betting-advice notice", "Not betting advice" in idx)

    print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nall checks passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
