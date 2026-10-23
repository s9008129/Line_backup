#!/usr/bin/env python3
"""Write check-specs-freeze.json with write-time hashes, then verify equality.

The expected bindings are computed by importing the frozen checks/run_command.py
itself (build_expected_bindings) so there is no reimplementation drift, then the
freshly written freeze is re-verified with run_command.verify_specs_and_freeze().
Exclusive create; refuses on collision. Readback verified.
"""
import hashlib
import importlib.util
import json
import os
import pathlib
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
RUNROOT = ROOT / RUNREL
FREEZE = RUNROOT / "check-specs-freeze.json"
SCRIPT_REL = f"{RUNREL}/tmp/write_freeze.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("r02_run_command", RUNROOT / "checks/run_command.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    runner = load_runner()
    expected = runner.build_expected_bindings(runner.load_json(runner.CHECK_SPECS))
    if not all(expected.values()):
        raise SystemExit("EMPTY_BINDING_IN_EXPECTED")
    freeze = {
        "format": "RECOVERY_02_CHECK_SPECS_FREEZE_V1",
        "task_id": "TASK-20261011-line-baseline-recovery-02",
        "run_rel": RUNREL,
        "self_reference": {"excluded_relative_path": f"{RUNREL}/check-specs-freeze.json"},
        "resolved_source_hashes": dict(sorted(expected.items())),
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generator": {"path": SCRIPT_REL, "sha256": hashlib.sha256((ROOT / SCRIPT_REL).read_bytes()).hexdigest()},
        "native_harness_validation": "NOT_RUN",
    }
    data = (json.dumps(freeze, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if os.path.lexists(FREEZE):
        raise SystemExit(f"ID_COLLISION:{FREEZE}")
    fd = os.open(FREEZE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    if FREEZE.read_bytes() != data:
        raise SystemExit("READBACK_MISMATCH")
    _specs, _freeze, expected2, problems = runner.verify_specs_and_freeze()
    if problems or expected2 != expected:
        raise SystemExit(f"FREEZE_VERIFY_FAILED:{problems}")
    print(json.dumps({
        "status": "OK",
        "freeze_path": str(FREEZE),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "keys": len(expected),
        "problems": problems,
    }, ensure_ascii=True, sort_keys=True))
    for rel, digest in sorted(expected.items()):
        print(rel, digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
