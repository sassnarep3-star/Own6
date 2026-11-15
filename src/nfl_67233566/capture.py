"""Frozen official capture for session 67233566 (read 2026-11-15T23:26:34Z).

Everything published by this pack is derived from ONE file:
``data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt``.  This module parses it.
There is no network access here and no value is invented: an empty field stays empty,
because on the official page an empty cell means "not printed", not "zero".

Block grammar
-------------
``#block <name> <field>|<field>|...`` header, then one record per line, ``|``-separated.
``#source``, ``#capture``, ``#note`` and ``#prior_capture`` lines are metadata records that
keep their raw text so the source register and the capture log can be rebuilt from them.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

CAPTURE_RELPATH = "data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt"

_BLOCK = re.compile(r"^#(?P<name>[A-Za-z0-9_]+)\s+(?P<fields>[A-Za-z0-9_|]+)\s*$")


@dataclass
class Capture:
    """Parsed capture. ``rows`` maps block name -> list of dicts (empty string = not printed)."""

    rows: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    meta: dict[str, list[str]] = field(default_factory=dict)
    text: str = ""
    sha256: str = ""

    def block(self, name: str) -> list[dict[str, str]]:
        return self.rows[name]

    def sources(self) -> list[dict[str, str]]:
        """``#source url=... chunks=... title=... read_utc=...`` metadata lines."""
        out: list[dict[str, str]] = []
        for line in self.meta.get("source", []):
            parts = re.findall(r'(\w+)=("[^"]*"|\S+)', line)
            rec = {k: v.strip('"') for k, v in parts}
            out.append(rec)
        return out


def parse_capture(text: str) -> Capture:
    cap = Capture(text=text, sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())
    fields: list[str] | None = None
    name = ""
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("#"):
            body = line[1:]
            m = _BLOCK.match(line)
            if m and "|" in m.group("fields"):
                name = m.group("name")
                fields = [f.strip() for f in m.group("fields").split("|")]
                cap.rows.setdefault(name, [])
                cap.meta.setdefault(name, [])
                continue
            key = body.split(" ", 1)[0].split("=", 1)[0].strip()
            fields = None
            name = key
            cap.meta.setdefault(key, []).append(body)
            continue
        if not line.strip():
            continue
        if fields is None or not name:
            continue
        values = [v.strip() for v in line.split("|")]
        if len(values) < len(fields):
            raise ValueError(f"short record in block {name!r}: {line!r}")
        if len(values) > len(fields):
            raise ValueError(f"long record in block {name!r}: {line!r}")
        cap.rows[name].append(dict(zip(fields, values)))
    return cap


def load_capture(root: Path | None = None) -> Capture:
    root = root or Path(__file__).resolve().parents[2]
    path = root / CAPTURE_RELPATH
    return parse_capture(path.read_text(encoding="utf-8"))


def as_float(value: str) -> float | None:
    return None if value == "" else float(value)


def as_int(value: str) -> int | None:
    return None if value == "" else int(value)


def badge_to_record(badge: str) -> tuple[int, int, int] | None:
    """``'3-5-1'`` -> ``(3, 5, 1)``. Returns None for an empty badge."""
    if not badge:
        return None
    parts = badge.split("-")
    if len(parts) == 2:  # the by-week cards print "8-1" when no tie exists, "3-5-1" otherwise
        parts = parts + ["0"]
    if len(parts) != 3:
        raise ValueError(f"malformed badge {badge!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])
