#!/usr/bin/env python3
"""Phase 2 / R6 (second half) — test-ownership isolation: drivers delete shared case roots.

CLAIM  `tests/authority_negative_driver.py` (setup_case_roots) and
       `tests/test_transaction_core.py` (setup/teardown) delete the shared
       /private/tmp/line-backup-acceptance-case-01..12 roots, destroying other tests'
       evidence (historically: case-12 disappeared). Re-running drivers in any order
       is therefore destructive and non-repeatable.
ENTRY  The real driver scripts, run as subprocesses, exactly as a test runner would.
ORACLE Marker files placed in the roots before the run + surviving durable copies.
DECIDE Markers destroyed -> harness ownership is not isolated; drivers must own their
       roots and must never delete another case's evidence.
NOTE   This script MUST run last: it destroys /private/tmp/line-backup-acceptance-case-01..12.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import WORK, program_hashes, write_json, write_tree_manifest

ROOTS = [Path(f"/private/tmp/line-backup-acceptance-case-{i:02d}") for i in range(1, 13)]
MARKER = "phase2-r6-ownership-marker.txt"


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    ev = Path(ns.evidence_dir)
    ev.mkdir(parents=True, exist_ok=True)

    for root in ROOTS:
        root.mkdir(parents=True, exist_ok=True)
        (root / MARKER).write_text(f"owned by phase2-r6 probe: {root}\n", encoding="utf-8")
    before = {str(r): (r / MARKER).exists() for r in ROOTS}

    record = {"claim": "drivers delete shared case roots (cross-test contamination)",
              "entry": "python3 tests/authority_negative_driver.py / tests/test_transaction_core.py",
              "oracle": "marker files in /private/tmp/line-backup-acceptance-case-01..12",
              "program_hashes": program_hashes()}
    import subprocess
    (ev / "driver-output").mkdir(parents=True, exist_ok=True)
    run = subprocess.run(["/usr/bin/python3", str(WORK / "tests/authority_negative_driver.py"),
                          "--summary", str(ev / "driver-output" / "summary.json")],
                         cwd=WORK, capture_output=True, text=True, check=False, timeout=600)
    (ev / "driver-stdout.log").write_text(run.stdout, encoding="utf-8")
    (ev / "driver-stderr.log").write_text(run.stderr, encoding="utf-8")
    (ev / "driver-exit-code").write_text(f"{run.returncode}\n", encoding="utf-8")
    after = {str(r): (r / MARKER).exists() for r in ROOTS}
    destroyed = sorted(k for k in before if before[k] and not after.get(k))

    unit = subprocess.run(["/usr/bin/python3", "-m", "unittest", "-v", "tests.test_transaction_core"],
                          cwd=WORK, capture_output=True, text=True, check=False, timeout=600)
    (ev / "unit-stdout.log").write_text(unit.stdout, encoding="utf-8")
    (ev / "unit-stderr.log").write_text(unit.stderr, encoding="utf-8")
    (ev / "unit-exit-code").write_text(f"{unit.returncode}\n", encoding="utf-8")
    after_unit = {str(r): (r / MARKER).exists() for r in ROOTS}
    destroyed_by_unit = sorted(k for k in before if before[k] and not after_unit.get(k))

    record["markers_before"] = before
    record["markers_after_authority_driver"] = after
    record["markers_after_unit_test"] = after_unit
    record["destroyed_by_authority_driver"] = destroyed
    record["destroyed_by_unit_test"] = destroyed_by_unit
    record["driver_exit_code"] = run.returncode
    record["unit_exit_code"] = unit.returncode
    record["verdict"] = ("REPRODUCED_CROSS_TEST_DELETION" if (destroyed or destroyed_by_unit)
                         else "NO_DELETION_OBSERVED")
    write_json(ev / "observation.json", record)
    write_tree_manifest(ev)
    print({"verdict": record["verdict"], "destroyed_by_driver": destroyed, "destroyed_by_unit": destroyed_by_unit})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
