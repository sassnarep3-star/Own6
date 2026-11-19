"""Capture helpers for session ade166a4 (nfl_ade166a4 pack).

Honesty rules encoded here (mirrors data/nfl_a67ddef8/capture_log.csv convention):
  * Every artifact written by this pack is a TRANSCRIPTION of page text that the
    session read through its page-fetch tool. It is not raw HTTP response bytes.
  * The sha256 in capture_log.csv therefore covers the transcription artifact
    ONLY. It cannot prove what the page said at read time — only that the
    artifact has not changed since it was written.
  * read_on_utc is the artifact-write clock, an UPPER BOUND on when the page was
    read (the fetch happened earlier in the same session window on the stated
    date). Each log row states this in its note.
  * This pack is a SECOND same-day read pair for the Week 11 injury hub: the
    first read is data/nfl_a67ddef8/raw/injuries_reg11_2026-11-19.md (~09:01Z),
    the second is data/nfl_ade166a4/raw/injuries_reg11_2026-11-19_b.md (~11:07Z).
"""
from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timezone

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACK = os.path.join(REPO, "data", "nfl_ade166a4")
RAW = os.path.join(PACK, "raw")
LOG = os.path.join(PACK, "capture_log.csv")

LOG_FIELDS = [
    "read_id", "source_url", "page_title_as_read", "what_was_read",
    "read_on_utc", "access_method", "artifact_path", "artifact_sha256",
    "artifact_sha_covers", "status", "note",
]

SHA_COVERS = (
    "sha256 covers the bytes of the transcription artifact named in "
    "artifact_path only; it cannot prove what the page said at read time"
)

NOTE = (
    "in-session page read on 2026-11-19 (UTC); read_on_utc is the artifact-write "
    "clock, an upper bound on the fetch time; sha256 covers the transcription "
    "artifact only and cannot prove what the page said"
)


def utc_now() -> str:
    """UTC clock, second precision, Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_raw(name: str, text: str) -> tuple[str, str]:
    """Write a transcription artifact under data/nfl_ade166a4/raw/ and return
    (absolute_path, sha256)."""
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path, sha256_file(path)


def append_capture_log(rows: list[dict]) -> str:
    """Write capture_log.csv from rows that carry artifact_path; fills the hash
    by hashing the artifact bytes at write time."""
    os.makedirs(PACK, exist_ok=True)
    out_rows = []
    for row in rows:
        path = row["artifact_path"]
        full = os.path.join(REPO, path)
        rec = dict(row)
        rec["artifact_sha256"] = sha256_file(full)
        rec["artifact_sha_covers"] = SHA_COVERS
        rec["status"] = "verified-2026-11-19"
        rec["note"] = NOTE
        out_rows.append(rec)
    path = LOG
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS, lineterminator="\r\n")
        w.writeheader()
        w.writerows(out_rows)
    return path
