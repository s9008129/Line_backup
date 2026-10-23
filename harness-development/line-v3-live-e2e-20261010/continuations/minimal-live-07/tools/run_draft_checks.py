#!/usr/bin/env python3
"""Run the editable R sources against the already pinned e01 Python namespace."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
R = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
E01 = R / "epochs/e01"


def load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("IMPORT_SPEC:" + str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if pathlib.Path.cwd() != ROOT or pathlib.Path(sys.executable).name != "python3.13":
        raise RuntimeError("FIXED_ROOT_AND_PYTHON_313_REQUIRED")
    env = __import__("os").environ
    expected_pythonpath = str(ROOT / "src") + ":" + str(E01 / "runtime/site-packages")
    if env.get("PYTHONPATH") != expected_pythonpath or env.get("PYTHONNOUSERSITE") != "1" or env.get("PYTHONDONTWRITEBYTECODE") != "1":
        raise RuntimeError("FIXED_DRAFT_ENV_REQUIRED")
    evidence_tests = load("ml07_draft_evidence_tests", R / "checks/test_evidence_policy.py")
    runner_tests = load("ml07_draft_runner_tests", R / "checks/test_run_command.py")
    evidence_tests.EPOCH = E01
    evidence_tests.PAIR.EPOCH = E01
    runner_tests.EPOCH = E01
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(evidence_tests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(runner_tests))
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    doc = {
        "format": "ML07_DRAFT_SOURCE_TEST_RESULT_V1",
        "formal_id": None,
        "verdict": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "output": output.getvalue(),
        "sources": {p.relative_to(ROOT).as_posix(): digest(p) for p in (
            R / "tools/evidence_io.py", R / "tools/output_policy.py", R / "tools/transaction_chain.py",
            R / "tools/inventory_pair.py", R / "checks/run_command.py", R / "checks/test_evidence_policy.py",
            R / "checks/test_run_command.py", R / "tools/run_draft_checks.py")},
        "python": {"path": sys.executable, "sha256": digest(pathlib.Path(sys.executable))},
        "fixture_root": str(E01 / "tmp"),
        "formal_claim_created": False,
    }
    print(json.dumps(doc, ensure_ascii=False, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
