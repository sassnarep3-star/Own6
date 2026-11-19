"""Derive the d6a947cb registers from the repo's existing ledgers and raw captures.

Everything written here is computed from files on disk:
  * requirements.csv  <- data/nfl_0ce967db/requirements.csv (96 owner bullets, carried states)
  * ledger_comparison.csv <- the four existing requirement ledgers (state counts)
  * capture_log.csv   <- sha256 + byte count of each raw excerpt in data/nfl_d6a947cb/raw/

Re-running this module must reproduce the same files byte-for-byte (see tests).
"""
from __future__ import annotations

import csv
import hashlib
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "nfl_d6a947cb"
LEDGER = ROOT / "data" / "nfl_0ce967db" / "requirements.csv"

# Official NFL URLs whose text was read on 2026-11-19 (UTC batch clock, see capture_log.csv).
READ_TODAY = {
    "https://www.nfl.com/injuries/": "2026-11-19T12:08Z (chunk 0 of 7 only)",
    "https://www.nfl.com/legal/terms/": "2026-11-19T12:09Z (chunk 0 of 9 only; s.1.3)",
    "https://www.nfl.com/schedules/": "2026-11-19T12:09Z (chunk 0 of 3 only)",
    "https://www.nfl.com/injuries/league/2026/reg10": "2026-11-19T12:10Z (chunk 0 of 8 only)",
    "https://www.nfl.com/games/colts-at-texans-2026-reg-11": "2026-11-19T12:11Z (chunk 0 of 3 only)",
    "https://operations.nfl.com/gameday/nfl-schedule/": "2026-11-19T12:10Z",
    "https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf": "2026-11-19T12:10Z",
}

# Duplicate bullets in the owner brief (same requirement restated). Map dupe -> canonical id.
DUPLICATES = {
    "R89": "R15", "R90": "R04", "R91": "R16", "R92": "R17",
    "R93": "R09", "R94": "R10", "R95": "R51", "R96": "R62",
}

# Category per canonical requirement (assigned here, by reading each bullet).
CATEGORY = {}
for rid in ["R01", "R02", "R18", "R19", "R20", "R26", "R57", "R65", "R67"]:
    CATEGORY[rid] = "Data, prices & results"
for rid in ["R10", "R12", "R21", "R23", "R24", "R28", "R44", "R45", "R46", "R50", "R51",
            "R52", "R53", "R61", "R63", "R39", "R41"]:
    CATEGORY[rid] = "Injuries & availability"
for rid in ["R06", "R11", "R13", "R25", "R29", "R30", "R31", "R38", "R40", "R42", "R43",
            "R47", "R48", "R49", "R77"]:
    CATEGORY[rid] = "Depth charts & roster"
for rid in ["R03", "R04", "R14", "R15", "R22", "R27", "R32", "R55", "R59", "R60", "R71", "R73"]:
    CATEGORY[rid] = "Models & origination"
for rid in ["R05", "R07", "R08", "R09", "R16", "R17", "R33", "R34", "R35", "R54", "R56", "R58",
            "R62", "R64", "R66", "R72", "R74", "R75", "R76"]:
    CATEGORY[rid] = "Leaderboard & validation"
for rid in ["R36", "R37", "R68", "R69", "R70", "R78", "R79", "R80", "R81", "R82", "R83",
            "R84", "R85", "R86", "R87", "R88"]:
    CATEGORY[rid] = "Site, governance & publication"

# Per-row re-check results from this session. Only rows listed here differ from the carried state.
# Each entry: (d6a_status, basis, flag_ids)
RECHECK = {
    "R01": ("blocked", "Re-read 2026-11-19: nfl.com Terms s.1.3 prohibits systematic retrieval to compile a database absent express written consent. The price-archive policy cannot rely on this page as permission. Legal review needed (see RF-06).", "RF-06"),
    "R20": ("needs_review", "Carried 'met' rests on a policy text that does not address s.1.3 of the NFL.com Terms (re-read today). Policy re-opened, not confirmed.", "RF-06"),
    "R22": ("met", "Carried 'met' pointed at a sub-page (docs/nfl-0ce967db). This pack's landing page now carries the one-row-per-requirement table with gate and clearing number.", ""),
    "R23": ("partially_met", "Re-read 2026-11-19: venue for 1 of 13 Week 11 games (Colts at Texans = 'Reliant Stadium', Houston TX, Game Center). Schedule page hotel link names 'NRG Stadium' for the same game. Naming conflict flagged. 12 venues still unread.", "RF-07"),
    "R29": ("needs_decision", "Carried 'out_of_scope' contradicts the owner brief, which asks for both parser failures to be fixed. Texans image needs an authorized structured source; Packers number-stripping needs no source. Decision needed.", "RF-08"),
    "R45": ("met", "Re-read 2026-11-19: Week 10 official report (nfl.com/injuries/league/2026/reg10) shows Kerby Joseph, Cade Mays and D.J. Reed each 'Out' in the Game Status column. The blank-cell defect does not reproduce today.", "RF-05"),
    "R63": ("blocked", "Re-read 2026-11-19: /injuries/league/2026/reg10 resolves, so past weekly pages are reachable. No archive exists yet and the legal basis is open (RF-06).", "RF-06"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def host(url: str) -> str:
    return url.split("/")[2] if "//" in url else ""


def build_requirements() -> list[dict]:
    rows = list(csv.DictReader(LEDGER.open(newline="", encoding="utf-8")))
    out = []
    for r in rows:
        rid = r["req_id"]
        dup = DUPLICATES.get(rid, "")
        status, basis, flags = RECHECK.get(rid, (r["state"], "Carried from nfl_0ce967db (not re-checked this session)." , ""))
        if rid in RECHECK and status == r["state"]:
            basis = "Carried state confirmed this session. " + basis
        url = r["source_url"]
        read = READ_TODAY.get(url, "")
        out.append(OrderedDict([
            ("req_id", rid),
            ("category", CATEGORY.get(dup or rid, "UNCATEGORIZED")),
            ("owner_requirement", r["owner_requirement"]),
            ("duplicate_of", dup),
            ("carried_state", r["state"]),
            ("d6a_status", status),
            ("d6a_basis", basis),
            ("blocking_gate", r["blocking_gate"]),
            ("number_that_would_clear_it", r["number_that_would_clear_it"]),
            ("source_url", url),
            ("source_host", host(url)),
            ("source_read_today_utc", read),
            ("flag_ids", flags),
            ("carried_from", "data/nfl_0ce967db/requirements.csv (" + rid + ")"),
        ]))
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def discover_ledgers() -> list[tuple[str, str]]:
    """Every requirements.csv in the data tree except this pack's own register."""
    found = []
    for p in sorted((ROOT / "data").rglob("requirements.csv")):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("data/nfl_d6a947cb/"):
            continue
        header = p.open(newline="", encoding="utf-8").readline()
        cols = [c.strip() for c in next(csv.reader([header]))]
        col = next((c for c in ("state", "status") if c in cols), "")
        found.append((rel, col))
    return found


def build_ledger_comparison() -> list[dict]:
    out = []
    for rel, col in discover_ledgers():
        rows = list(csv.DictReader((ROOT / rel).open(newline="", encoding="utf-8")))
        counts = Counter((r.get(col) or "").strip() or "(blank)" for r in rows) if col else Counter()
        out.append(OrderedDict([
            ("ledger", rel),
            ("rows", str(len(rows))),
            ("status_column", col or "NONE (no state/status column)"),
            ("status_counts", "; ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "n/a"),
            ("distinct_status_values", str(len(counts))),
        ]))
    return out


def build_capture_log() -> list[dict]:
    out = []
    raw = DATA / "raw"
    for p in sorted(raw.glob("*.txt")):
        out.append(OrderedDict([
            ("file", p.relative_to(ROOT).as_posix()),
            ("sha256", sha256(p)),
            ("bytes", str(p.stat().st_size)),
            ("captured_by", "d6a947cb (manual excerpt of tool output; hash covers this excerpt file, not the live page)"),
        ]))
    return out


def main() -> None:
    write_csv(DATA / "requirements.csv", build_requirements())
    write_csv(DATA / "ledger_comparison.csv", build_ledger_comparison())
    write_csv(DATA / "capture_log.csv", build_capture_log())
    print("ok")


if __name__ == "__main__":
    main()
