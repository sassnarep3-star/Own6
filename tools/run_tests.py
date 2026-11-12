#!/usr/bin/env python3
"""Run the repository's pytest-style unit tests without needing pytest installed.

The sandbox has no pytest (PEP 668 blocks a system pip install), so this stdlib
runner imports tests/test_engine.py and calls every test_* function. It is used by
.github/workflows/verify.yml and by the integration verification pass.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# This runner exists so tests still run where pytest/numpy/scipy are unavailable.
# Test modules that declare a third-party requirement are owned by a runner that
# installs it (see .github/workflows/nfl-lab-ci.yml for tests/test_nfl_lab.py).
NEEDS_THIRD_PARTY = {"test_nfl_lab.py"}


def main() -> int:
    test_files = sorted(p for p in (ROOT / "tests").glob("test_*.py")
                        if p.name not in NEEDS_THIRD_PARTY)
    if not test_files:
        print("FAIL: no test files found", file=sys.stderr)
        return 1
    passed = failed = 0
    for path in test_files:
        spec = importlib.util.spec_from_file_location(f"own6_test_{path.stem}", path)
        if spec is None or spec.loader is None:
            print(f"FAIL: cannot import {path.name}", file=sys.stderr)
            failed += 1
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001 - report every failure
            print(f"FAIL: import {path.name}: {exc}", file=sys.stderr)
            traceback.print_exc()
            failed += 1
            continue
        for name in sorted(n for n in dir(module) if n.startswith("test_")):
            fn = getattr(module, name)
            if not callable(fn):
                continue
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL {path.name}::{name}: {type(exc).__name__}: {exc}")
                traceback.print_exc()
                failed += 1
            else:
                print(f"PASS {path.name}::{name}")
                passed += 1
    for skipped in sorted(NEEDS_THIRD_PARTY):
        if (ROOT / "tests" / skipped).exists():
            print(f"SKIP {skipped}: requires numpy/scipy/pytest; covered by the NFL lab workflow")
    total = passed + failed
    print(f"RESULT: {passed}/{total} tests passed")
    return 0 if failed == 0 and total > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
