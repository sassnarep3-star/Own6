#!/usr/bin/env python3
"""Scheduled capture of the official NFL injury report (session 79fd4958).

What it does, once per run:
  1. Fetches the official page (default https://www.nfl.com/injuries/, which
     resolves to the current week) and keeps the RAW response bytes.
  2. Writes the raw bytes to data/nfl_capture/raw/ (git-ignored: raw NFL page
     bytes are kept out of the public repository until the terms are read).
     The raw bytes are uploaded by the workflow as a private artifact.
  3. Computes sha256 over the raw bytes and the UTC clock of the fetch.
  4. Checks the page for drift: title, week label, the exact injury-table
     header, minimum table and player-row counts, and row shape. Any failure
     is written to the index and the process exits 1 (loud failure).
  5. Appends ONE row to data/nfl_capture/index.csv. The index holds derived
     metadata only (time, URL, byte count, sha256, counts, status). It never
     holds player-level text. Existing rows are never rewritten.

Standard library only, so the scheduled workflow needs no install step.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_URL = "https://www.nfl.com/injuries/"
DEFAULT_RAW_DIR = os.path.join(REPO, "data", "nfl_capture", "raw")
DEFAULT_INDEX = os.path.join(REPO, "data", "nfl_capture", "index.csv")

REQUIRED_HEADER = ["Player", "Position", "Injuries", "Practice Status", "Game Status"]
MIN_INJURY_TABLES = 8
MIN_PLAYER_ROWS = 100
USER_AGENT = (
    "Mozilla/5.0 (compatible; Own6-official-capture/1.0; "
    "+https://github.com/sassnarep3-star/Own6)"
)

INDEX_FIELDS = [
    "capture_utc", "requested_url", "final_url", "http_status", "bytes",
    "sha256", "raw_file", "page_title", "week_label", "injury_tables",
    "player_rows", "blank_game_status_rows", "changed_vs_previous",
    "status", "failure_reason",
]

WEEK_RE = re.compile(r"Week\s+\d{1,2}\s+of\s+the\s+\d{4}\s+Season", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm(text: str) -> str:
    return " ".join(text.split())


class _TableParser(HTMLParser):
    """Collects every <table> as a list of rows, each row a list of cell texts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.tables: list[list[list[str]]] = []
        self._tables: list[list[list[str]]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):  # noqa: D401 - HTMLParser API
        if tag == "title":
            self._in_title = True
        elif tag == "table":
            self._tables.append([])
        elif tag == "tr" and self._tables:
            if self._row is not None:
                self._tables[-1].append(self._row)
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(_norm("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._tables:
            self._tables[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._tables:
            if self._row is not None:
                self._tables[-1].append(self._row)
                self._row = None
            self.tables.append(self._tables.pop())

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._cell is not None:
            self._cell.append(data)


def evaluate(body: bytes, http_status: int, min_tables: int = MIN_INJURY_TABLES,
             min_rows: int = MIN_PLAYER_ROWS) -> dict:
    """Pure function: parse raw bytes and return derived metadata plus drift reasons."""
    parser = _TableParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    parser.close()
    title = _norm(parser.title)
    reasons: list[str] = []

    if http_status != 200:
        reasons.append(f"http_status={http_status}")
    if "injury report" not in title.lower():
        reasons.append("title_missing_injury_report")
    week_match = WEEK_RE.search(title)
    week_label = week_match.group(0) if week_match else ""
    if not week_label:
        reasons.append("week_label_missing")

    injury_tables = [t for t in parser.tables if t and t[0] == REQUIRED_HEADER]
    near_misses = [
        t for t in parser.tables
        if t and "Player" in t[0] and "Practice Status" in t[0] and t[0] != REQUIRED_HEADER
    ]
    if near_misses:
        reasons.append(f"header_drift_tables={len(near_misses)}")
    if len(injury_tables) < min_tables:
        reasons.append(f"injury_tables={len(injury_tables)}<min{min_tables}")

    player_rows = 0
    blank_game = 0
    bad_shape = 0
    for table in injury_tables:
        for row in table[1:]:
            if len(row) != len(REQUIRED_HEADER):
                bad_shape += 1
                continue
            player_rows += 1
            if row[4] == "":
                blank_game += 1
    if bad_shape:
        reasons.append(f"row_shape_drift_rows={bad_shape}")
    if player_rows < min_rows:
        reasons.append(f"player_rows={player_rows}<min{min_rows}")

    return {
        "page_title": title,
        "week_label": week_label,
        "injury_tables": len(injury_tables),
        "player_rows": player_rows,
        "blank_game_status_rows": blank_game,
        "status": "ok" if not reasons else "fail",
        "failure_reason": ";".join(reasons),
    }


def fetch(url: str, attempts: int = 3, timeout: int = 60) -> tuple[int, str, bytes]:
    """GET the page. Returns (http_status, final_url, raw_bytes). Retries transient errors."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "text/html"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.geturl(), resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read() if exc.fp else b""
            if exc.code < 500 or attempt == attempts:
                return exc.code, url, body
            last_error = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
        time.sleep(5 * attempt)
    raise RuntimeError(f"fetch failed after {attempts} attempts: {last_error!r}")


def _last_sha(index_path: str) -> str:
    if not os.path.exists(index_path):
        return ""
    last = ""
    with open(index_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("sha256"):
                last = row["sha256"]
    return last


def _append_row(index_path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    new_file = not os.path.exists(index_path) or os.path.getsize(index_path) == 0
    with open(index_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=INDEX_FIELDS, lineterminator="\n")
        if new_file:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in INDEX_FIELDS})


def capture(url: str, raw_dir: str, index_path: str, fetch_fn=fetch,
            clock=utc_now, min_tables: int = MIN_INJURY_TABLES,
            min_rows: int = MIN_PLAYER_ROWS) -> tuple[int, dict]:
    """Run one capture. Returns (exit_code, index_row). Always appends one index row."""
    ts = clock()
    row = {"capture_utc": ts, "requested_url": url}
    previous_sha = _last_sha(index_path)
    try:
        http_status, final_url, body = fetch_fn(url)
    except Exception as exc:  # network failure is a loud, recorded failure
        row.update({"status": "fail", "failure_reason": f"fetch_error:{type(exc).__name__}",
                    "changed_vs_previous": "unknown"})
        _append_row(index_path, row)
        return 1, row

    row.update({"final_url": final_url, "http_status": http_status, "bytes": len(body)})
    if not body:
        row.update({"status": "fail", "failure_reason": f"empty_body;http_status={http_status}",
                    "changed_vs_previous": "unknown"})
        _append_row(index_path, row)
        return 1, row

    sha = hashlib.sha256(body).hexdigest()
    os.makedirs(raw_dir, exist_ok=True)
    raw_name = f"{ts.replace(':', '').replace('-', '')}_{sha[:12]}.html"
    with open(os.path.join(raw_dir, raw_name), "wb") as fh:
        fh.write(body)

    ev = evaluate(body, http_status, min_tables=min_tables, min_rows=min_rows)
    if not previous_sha:
        changed = "first"
    else:
        changed = "no" if previous_sha == sha else "yes"
    row.update(ev)
    row.update({"sha256": sha, "raw_file": raw_name, "changed_vs_previous": changed})
    _append_row(index_path, row)
    return (0 if ev["status"] == "ok" else 1), row


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--raw-dir", default=DEFAULT_RAW_DIR)
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--min-tables", type=int, default=MIN_INJURY_TABLES)
    ap.add_argument("--min-rows", type=int, default=MIN_PLAYER_ROWS)
    args = ap.parse_args(argv)
    code, row = capture(args.url, args.raw_dir, args.index,
                        min_tables=args.min_tables, min_rows=args.min_rows)
    # Print metadata only (no player-level text) for the job log.
    summary = {k: row.get(k, "") for k in INDEX_FIELDS}
    print("capture result:", summary, file=sys.stdout)
    if code != 0:
        print(f"::error::official injury capture FAILED: {row.get('failure_reason', '')}")
    return code


if __name__ == "__main__":
    sys.exit(main())
