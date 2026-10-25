#!/usr/bin/env python3
"""Run the real formal verify-only command and independently compare baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "tests" / "automation_verification"))
import harness as H  # noqa: E402


def digest(path: Path) -> dict:
    data = path.read_bytes() if path.exists() else b"<missing>"
    return {"path": str(path), "exists": path.exists(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run(argv: list[str], record_dir: Path) -> tuple[dict, dict | None]:
    record_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(WORKSPACE / "src")
    env["LC_ALL"] = "C"
    env["PATH"] = "/usr/bin:/bin"
    env["PYTHONHASHSEED"] = "0"
    (record_dir / "argv.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    process = subprocess.run(argv, cwd=WORKSPACE, env=env, capture_output=True, text=True, check=False)
    (record_dir / "stdout.log").write_text(process.stdout, encoding="utf-8")
    (record_dir / "stderr.log").write_text(process.stderr, encoding="utf-8")
    (record_dir / "exit-code").write_text(str(process.returncode) + "\n", encoding="utf-8")
    try:
        result = json.loads(process.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        result = None
    return {"argv": argv, "exit_code": process.returncode,
            "stdout": str(record_dir / "stdout.log"), "stderr": str(record_dir / "stderr.log"),
            "result": result}, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--baseline-pre", required=True)
    parser.add_argument("--baseline-post", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--group-key", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--expected-images", required=True, type=int)
    ns = parser.parse_args()
    project = ns.project_root.expanduser().resolve(strict=True)
    destination = ns.destination.expanduser().resolve(strict=True)
    config = project / "config/line_backup_config.json"
    state = project / "state/backup_state.json"
    run_log = project / "state/run_log.md"
    evidence = Path(ns.evidence_dir)
    evidence.mkdir(parents=True, exist_ok=True)
    verify_argv = ["/usr/bin/python3", "-m", "line_backup_acceptance", "verify-only",
                   "--project-root", str(project), "--config", str(config), "--state", str(state),
                   "--destination", str(destination), "--group-key", ns.group_key,
                   "--start-date", ns.start_date, "--end-date", ns.end_date,
                   "--expected-images", str(ns.expected_images), "--evidence-dir", str(evidence / "product")]
    verify_record, verify_result = run(verify_argv, evidence / "process")
    baseline_argv = ["/usr/bin/python3", str(WORKSPACE / "tests/authority_baseline.py"), "--config", str(config),
                     "--state", str(state), "--run-log", str(run_log), "--destination", str(destination),
                     "--output", str(ns.baseline_post)]
    baseline_record, _ = run(baseline_argv, evidence / "baseline-post-process")
    baseline_pre = Path(ns.baseline_pre)
    baseline_post = Path(ns.baseline_post)
    baseline_same = baseline_pre.is_file() and baseline_post.is_file() and baseline_pre.read_bytes() == baseline_post.read_bytes()
    expected = {"filesystem_status": "PASS", "registry_status": "FAIL", "source_status": "UNRESOLVED",
                "state_status": "LEGACY_PROVENANCE_LIMITED", "overall_status": "UNKNOWN",
                "failure_class": "INPUT_PROVENANCE_LIMITED", "artifact_readback": "PASS", "exit_code": 4}
    observed = {key: verify_result.get(key) if isinstance(verify_result, dict) else None for key in expected}
    summary = {"schema_version": 1, "verify": verify_record, "baseline_post": baseline_record,
               "expected": expected, "observed": observed, "baseline_delta": "UNCHANGED" if baseline_same else "WORSENED",
               "baseline_pre": digest(baseline_pre), "baseline_post_artifact": digest(baseline_post),
               "match": observed == expected and baseline_same and baseline_record["exit_code"] == 0}
    write_json(Path(ns.summary), summary)
    manifest = H.write_tree_manifest(evidence, exclude_extra=("readback-verification.json",))
    evidence_check = ["/usr/bin/python3", str(WORKSPACE / "tests/automation_verification" / "verify_evidence.py"),
                      "--root", str(evidence), "--output", str(evidence / "readback-verification.json")]
    readback = subprocess.run(evidence_check, cwd=str(WORKSPACE), env=os.environ.copy(), capture_output=True,
                              text=True, check=False)
    report = json.loads((evidence / "readback-verification.json").read_text(encoding="utf-8")) \
        if (evidence / "readback-verification.json").is_file() else {}
    print(json.dumps({"match": summary["match"], "baseline_delta": summary["baseline_delta"],
                      "verify_exit": verify_record["exit_code"], "verify_overall": observed.get("overall_status"),
                      "readback": report.get("verdict"),
                      "manifest_sha256": manifest["manifest_sha256"],
                      "readback_exit_code": readback.returncode}, sort_keys=True))
    return 0 if summary["match"] and report.get("verdict") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
