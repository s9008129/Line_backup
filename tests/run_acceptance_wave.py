#!/usr/bin/env python3
"""Acceptance wave (Stage-04 evidence) — the real operator CLI through every acceptance driver.

Runs, into one fresh append-only durable root (default `evidence/20260916-acceptance/attempt-03`):

  transactions/case-NN/            cases 01..25: durable copy of the literal case root (its own
                                   manifest.json sits at the copy root so every entry resolves)
  transactions/case-NN/records/    per-case driver record (argv, stdout, stderr, exit-code, result,
                                   pre/post state, dispatch counter)
  verifier/  + verifier-fixture-rows.json + verifier-summary.json     (40-row verifier matrix)
  status/    + status-rows.json + status-summary.json                 (19-row status contract)
  authority/ + authority-summary.json                                 (11 authority negatives)
  legacy-false-positive-summary.json                                  (preserved legacy process, 56/58)

The attempt tree ends with a tree manifest and an independent read-back report
(`verify_evidence.py`). `/private/tmp` is working space only; the runner's own workspace root
carries the §15.5 ownership marker and is rebuilt through `ensure_owned_root`/`reset_owned_content`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

TESTS = Path(__file__).resolve().parent
WORK = TESTS.parent
sys.path.insert(0, str(WORK / "tests" / "automation_verification"))
import harness as H  # noqa: E402

DRIVER_ID = "acceptance-wave-runner"
TASK_ID = H.TASK_ID
DEFAULT_ATTEMPT = WORK / "evidence/20260916-acceptance/attempt-03"
WORKSPACE = Path("/private/tmp/line-backup-acceptance-acceptance-wave")
PYCACHE = "/private/tmp/line-backup-acceptance-pycache"
CASES = [f"{index:02d}" for index in range(1, 26)]


def driver_env() -> dict:
    env = os.environ.copy()
    env.update({"PYTHONPATH": str(WORK / "src"), "LC_ALL": "C", "PATH": "/usr/bin:/bin",
                "PYTHONHASHSEED": "0", "PYTHONPYCACHEPREFIX": PYCACHE})
    return env


def run_driver(label: str, argv: list[str], record_dir: Path, timeout: float) -> dict:
    record_dir.mkdir(parents=True, exist_ok=True)
    H.write_json(record_dir / "argv.json", {"argv": argv, "cwd": str(WORK), "secrets_removed": True})
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        proc = subprocess.run(argv, cwd=str(WORK), env=driver_env(), capture_output=True, text=True, check=False,
                              timeout=timeout)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\n<timeout after {timeout}s>\n"
        code = -1000
    (record_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    (record_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    (record_dir / "exit-code").write_text(f"{code}\n", encoding="utf-8")
    return {"label": label, "argv": argv, "exit_code": code, "started_at": started,
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "stdout_tail": stdout.strip().splitlines()[-1] if stdout.strip() else "",
            "stderr_tail": stderr.strip().splitlines()[-1] if stderr.strip() else ""}


def run_case(case_id: str, attempt_root: Path, timeout: float) -> dict:
    case_root = Path(f"/private/tmp/line-backup-acceptance-case-{case_id}")
    dest = attempt_root / "transactions" / f"case-{case_id}"
    stash = WORKSPACE / "stash" / f"case-{case_id}"
    stash.mkdir(parents=True, exist_ok=True)
    argv = ["/usr/bin/python3", str(TESTS / "acceptance_case_driver.py"), "--case-id", case_id,
            "--case-root", str(case_root),
            "--pre-state", str(stash / "pre-state.json"), "--state", str(case_root / "state" / "backup_state.json"),
            "--post-state", str(stash / "post-state.json"), "--counter", str(stash / "counter.jsonl"),
            "--result", str(stash / "result.json"), "--manifest", str(stash / "manifest.json"),
            "--stdout", str(stash / "stdout.log"), "--stderr", str(stash / "stderr.log"),
            "--exit-code", str(stash / "exit-code"), "--evidence-dir", str(stash / "driver-evidence")]
    row = run_driver(f"case-{case_id}", argv, stash / "driver-record", timeout)
    result = H.read_json(stash / "result.json") if (stash / "result.json").is_file() else {}
    manifest_identity = None
    if (stash / "manifest.json").is_file() and (case_root / "manifest.json").is_file():
        stash_sha = H.sha256_file(stash / "manifest.json")
        root_sha = H.sha256_file(case_root / "manifest.json")
        manifest_identity = {"stash_sha256": stash_sha, "case_root_sha256": root_sha,
                             "identical": stash_sha == root_sha,
                             "note": "the case manifest is written by the driver at the end of the run; the "
                                     "durable copy replaces its manifest.json with the harness tree manifest"}
    H.durable_copy_tree(case_root, dest)
    records = dest / "records"
    records.mkdir(exist_ok=True)
    for name in ("pre-state.json", "post-state.json", "counter.jsonl", "result.json",
                 "stdout.log", "stderr.log", "exit-code"):
        src = stash / name
        if src.is_file():
            (records / name).write_bytes(src.read_bytes())
    if (stash / "manifest.json").is_file():
        (records / "product-manifest-copy.json").write_bytes((stash / "manifest.json").read_bytes())
    row.update({"case_id": case_id, "case_root": str(case_root), "durable_copy": str(dest),
                "independent_oracle_match": result.get("independent_oracle_match"),
                "failed_checks": result.get("failed_checks"),
                "manifest_identity": manifest_identity,
                "product_manifest_copy": str(records / "product-manifest-copy.json"),
                "product_manifest_note": "raw artifact; its entries are relative to the case root, which the "
                                         "durable copy mirrors byte-for-byte",
                "stash_note": "the stash lives in working space; the durable copy carries the same bytes"})
    row["safe"] = row["exit_code"] == 0 and result.get("independent_oracle_match") is True \
        and (manifest_identity is None or manifest_identity["identical"])
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--attempt-root", default=str(DEFAULT_ATTEMPT))
    ap.add_argument("--timeout", type=float, default=1800.0)
    ns = ap.parse_args()
    attempt_root = Path(ns.attempt_root)
    if attempt_root.exists() and any(attempt_root.iterdir()):
        raise SystemExit(f"refusing: attempt root {attempt_root} is not empty (append-only evidence)")
    attempt_root.mkdir(parents=True, exist_ok=True)
    H.ensure_owned_root(WORKSPACE, DRIVER_ID)
    H.reset_owned_content(WORKSPACE)

    case_rows = [run_case(case_id, attempt_root, ns.timeout) for case_id in CASES]
    cases_safe = all(row["safe"] for row in case_rows)

    drivers: dict[str, dict] = {}
    records_root = attempt_root / "driver-records"
    rows_file = attempt_root / "verifier-fixture-rows.json"
    drivers["verifier_emit_rows"] = run_driver(
        "verifier-emit-rows",
        ["/usr/bin/python3", str(TESTS / "verifier_fixture_driver.py"), "--emit-manifest", str(rows_file)],
        records_root / "verifier-emit-rows", ns.timeout)
    drivers["verifier"] = run_driver(
        "verifier",
        ["/usr/bin/python3", str(TESTS / "verifier_fixture_driver.py"), "--manifest", str(rows_file),
         "--evidence-dir", str(attempt_root / "verifier"), "--summary", str(attempt_root / "verifier-summary.json")],
        records_root / "verifier", ns.timeout)
    drivers["status"] = run_driver(
        "status",
        ["/usr/bin/python3", str(TESTS / "status_fixture_driver.py"),
         "--manifest", str(attempt_root / "status-rows.json"), "--evidence-dir", str(attempt_root / "status"),
         "--summary", str(attempt_root / "status-summary.json")],
        records_root / "status", ns.timeout)
    drivers["authority"] = run_driver(
        "authority",
        ["/usr/bin/python3", str(TESTS / "authority_negative_driver.py"),
         "--summary", str(attempt_root / "authority-summary.json"), "--evidence-dir", str(attempt_root / "authority")],
        records_root / "authority", ns.timeout)
    drivers["legacy"] = run_driver(
        "legacy",
        ["/usr/bin/python3", str(TESTS / "legacy_false_positive_repro.py"),
         "--summary", str(attempt_root / "legacy-false-positive-summary.json")],
        records_root / "legacy", ns.timeout)

    summaries = {}
    for key, path in (("verifier", attempt_root / "verifier-summary.json"),
                      ("status", attempt_root / "status-summary.json"),
                      ("authority", attempt_root / "authority-summary.json"),
                      ("legacy", attempt_root / "legacy-false-positive-summary.json")):
        if path.is_file():
            data = H.read_json(path)
            field = {"verifier": "all_match", "status": "all_match",
                     "authority": "all_match", "legacy": "reproduction_match"}[key]
            summaries[key] = {"path": str(path), "bytes": path.stat().st_size, "sha256": H.sha256_file(path),
                              field: data.get(field)}
    drivers_safe = all(row["exit_code"] == 0 for row in drivers.values()) and \
        all(value.get(field) is True for value, field in
            zip(summaries.values(), ("all_match", "all_match", "all_match", "reproduction_match"))) and \
        len(summaries) == 4

    observation = {
        "driver": DRIVER_ID, "task_id": TASK_ID, "attempt_root": str(attempt_root),
        "argv": sys.argv, "cwd": str(WORK), "interpreter": sys.version,
        "env_fingerprint": {"PYTHONPATH": str(WORK / "src"), "LC_ALL": "C", "PATH": "/usr/bin:/bin",
                            "PYTHONHASHSEED": "0", "PYTHONPYCACHEPREFIX": PYCACHE},
        "claim": "the fixed product passes the 25 acceptance cases, the 40-row verifier matrix, the 19-row "
                 "status contract, the 11 authority negatives and the preserved legacy false-positive "
                 "reproduction through the real operator CLI",
        "workspace_root": {"path": str(WORKSPACE), "owned": True,
                           "note": "/private/tmp is working space; durable copies live under the attempt root"},
        "cases": case_rows, "cases_safe": cases_safe, "drivers": drivers,
        "summaries": summaries, "drivers_safe": drivers_safe,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    H.write_json(attempt_root / "acceptance-observation.json", observation)
    manifest = H.write_tree_manifest(attempt_root, exclude_extra=("readback-verification.json",))
    readback_argv = ["/usr/bin/python3", str(WORK / "tests" / "automation_verification" / "verify_evidence.py"),
                     "--root", str(attempt_root), "--output", str(attempt_root / "readback-verification.json")]
    rb = subprocess.run(readback_argv, cwd=str(WORK), env=driver_env(), capture_output=True, text=True, check=False,
                        timeout=1800)
    report = H.read_json(attempt_root / "readback-verification.json") if \
        (attempt_root / "readback-verification.json").is_file() else {}
    all_safe = cases_safe and drivers_safe and rb.returncode == 0 and report.get("verdict") == "PASS"
    print(json.dumps({"attempt_root": str(attempt_root), "all_safe": all_safe,
                      "cases_safe": cases_safe, "cases_failed": [r["case_id"] for r in case_rows if not r["safe"]],
                      "drivers": {k: {"exit_code": v["exit_code"], "stdout_tail": v["stdout_tail"]}
                                  for k, v in drivers.items()},
                      "summaries": summaries,
                      "readback": {"verdict": report.get("verdict"), "manifests": report.get("manifests"),
                                   "artifacts_checked": report.get("artifacts_checked"),
                                   "problems": len(report.get("problems") or []),
                                   "uncovered_files": len(report.get("uncovered_files") or [])},
                      "manifest": {"files": manifest["files"], "total_bytes": manifest["total_bytes"],
                                   "manifest_sha256": manifest["manifest_sha256"]}}, ensure_ascii=False))
    return 0 if all_safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
