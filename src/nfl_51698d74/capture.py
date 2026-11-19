"""Capture helpers for session 51698d74 (nfl_51698d74 pack).

Honesty rules encoded here (mirrors data/nfl_0ce967db/capture_log.csv convention):
  * Every artifact written by this pack is a TRANSCRIPTION of page text that the
    session read through its page-fetch tool. It is not raw HTTP response bytes.
  * The sha256 in capture_log.csv therefore covers the transcription artifact
    ONLY. It cannot prove what the page said at read time — only that the
    artifact has not changed since it was written.
  * read_on_utc is the artifact-write clock, an UPPER BOUND on when the page was
    read (the fetch happened earlier in the same session window on the stated
    date). Each log row states this in its note.
  * Five raw files carry data lines confirmed identical to the prior-session
    (a67ddef8) transcription by row-by-row comparison against this session's
    fresh read; their headers state this. The Week-12 venue and reserve-list
    artifacts are new transcriptions from this session's reads.
"""
from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timezone

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACK = os.path.join(REPO, "data", "nfl_51698d74")
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
    """Write a transcription artifact under data/nfl_51698d74/raw/ and return
    (absolute_path, sha256)."""
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path, sha256_file(path)


def append_capture_log(rows: list[dict]) -> str:
    """Append rows to capture_log.csv (creating it with LOG_FIELDS if absent)."""
    os.makedirs(PACK, exist_ok=True)
    exists = os.path.exists(LOG)
    with open(LOG, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS, extrasaction="ignore")
        if not exists:
            w.writeheader()
        for r in rows:
            r.setdefault("artifact_sha_covers", SHA_COVERS)
            r.setdefault("access_method", "page-fetch tool (agent session), in-session read")
            w.writerow(r)
    return LOG


def verify_capture_log() -> list[str]:
    """Return a list of problems: rows whose artifact is missing or whose stored
    sha256 no longer matches the artifact bytes."""
    problems: list[str] = []
    if not os.path.exists(LOG):
        return ["capture_log.csv missing"]
    with open(LOG, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rel = row.get("artifact_path", "")
            path = os.path.join(REPO, rel) if rel else ""
            if not rel or not os.path.exists(path):
                problems.append(f"{row.get('read_id')}: artifact missing: {rel!r}")
                continue
            actual = sha256_file(path)
            if actual != row.get("artifact_sha256", ""):
                problems.append(
                    f"{row.get('read_id')}: sha256 mismatch for {rel} "
                    f"(stored {row.get('artifact_sha256','')[:16]}…, actual {actual[:16]}…)"
                )
    return problems
