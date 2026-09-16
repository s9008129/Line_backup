#!/usr/bin/env python3
"""Literal authority-negative subprocess matrix with read-only oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


BASE = Path("/private/tmp/line-backup-acceptance-authority")
CASES = [Path(f"/private/tmp/line-backup-acceptance-case-{i:02d}") for i in range(1, 13)]
GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> dict:
    data = path.read_bytes() if path.exists() and path.is_file() else b"<missing>"
    return {"exists": path.exists(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def state_digest(root: Path) -> dict:
    paths = [root / "state.json", root / "config" / "line_backup_config.json", root / "state" / "backup_state.json",
             root / "state" / "run_log.md", root / ".line-backup-state.lock", root / "counter.jsonl"]
    return {str(path): digest(path) for path in paths}


def env_for() -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    env["LC_ALL"] = "C"
    env["PATH"] = "/usr/bin:/bin"
    env["PYTHONHASHSEED"] = "0"
    return env


def run(argv: list[str], record: Path) -> dict:
    record.mkdir(parents=True, exist_ok=True)
    (record / "argv.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    p = subprocess.run(argv, cwd=Path(__file__).resolve().parents[1], env=env_for(), capture_output=True, text=True, check=False)
    (record / "stdout.log").write_text(p.stdout, encoding="utf-8")
    (record / "stderr.log").write_text(p.stderr, encoding="utf-8")
    (record / "exit-code").write_text(str(p.returncode) + "\n", encoding="utf-8")
    try:
        result = json.loads(p.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        result = None
    return {"argv": argv, "exit_code": p.returncode, "result": result,
            "stdout": str(record / "stdout.log"), "stderr": str(record / "stderr.log")}


def setup_case_roots() -> None:
    for root in CASES:
        if root.exists():
            shutil.rmtree(root)
        (root / "evidence").mkdir(parents=True)
        write_json(root / "state.json", {"schema_version": 2, "revision": 0, "current_run_id": None,
                                          "active_writer_id": None, "context_lock": None, "runs": [],
                                          "verified_albums": []})
        (root / "dispatcher.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        (root / "dispatcher.py").chmod(0o755)
        (root / "counter.jsonl").touch()


def setup_production() -> tuple[Path, Path]:
    root = BASE / "production-root"
    alternate = BASE / "alternate"
    for item in (root, alternate):
        if item.exists():
            shutil.rmtree(item)
    backup = root / "backup"
    destination = backup / "destination"
    destination.mkdir(parents=True)
    (root / "config").mkdir()
    (root / "state").mkdir()
    config = {"schema_version": 2, "group_key": GROUP, "group_name": "fixture",
              "backup_root": str(backup), "app_identifier": "jp.naver.line.mac",
              "max_albums_per_run": 1, "recovery_limit": 1, "poll_interval_seconds": 5,
              "stable_samples": 3, "max_wait_seconds": 15}
    write_json(root / "config" / "line_backup_config.json", config)
    write_json(root / "state" / "backup_state.json", {"schema_version": 2, "revision": 0,
                                                         "current_run_id": None, "active_writer_id": None,
                                                         "context_lock": None, "runs": [], "verified_albums": []})
    (root / "state" / "run_log.md").write_text("production fixture run log\n", encoding="utf-8")
    (alternate / "config").mkdir(parents=True)
    (alternate / "state").mkdir()
    write_json(alternate / "config" / "line_backup_config.json", config)
    write_json(alternate / "state" / "backup_state.json", {"tamper": True})
    (alternate / "state" / "run_log.md").write_text("alternate\n", encoding="utf-8")
    return root, alternate


def tx_prefix(root: Path, evidence: Path, *, operation: str, test: bool = False) -> list[str]:
    value = ["/usr/bin/python3", "-m", "line_backup_acceptance", "transaction"]
    value.append(operation)
    if test:
        value.extend(["--project-root", str(root), "--state", str(root / "state.json"),
                      "--evidence-dir", str(evidence), "--test-mode"])
    else:
        value.extend(["--project-root", str(root), "--evidence-dir", str(evidence)])
    return value


def expected(result: dict | None, code: int) -> bool:
    return (code == 2 and isinstance(result, dict) and result.get("failure_class") == "INVALID_AUTHORITY"
            and result.get("artifact_readback") == "PASS_WITH_NO_STATE_WRITE")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(BASE / "summary.json"))
    ns = parser.parse_args()
    if BASE.exists():
        shutil.rmtree(BASE)
    BASE.mkdir(parents=True)
    setup_case_roots()
    production, alternate = setup_production()
    results = []

    test_rows = [
        ("test-state-mismatch", tx_prefix(CASES[0], CASES[0] / "evidence" / "authority-state", operation="prepare", test=True)
         + ["--state", str(CASES[1] / "state.json"), "--run-id", "AUTH-PREPARE", "--owner-id", "AUTH-WRITER",
            "--group-key", GROUP, "--start-date", "2024-05-13", "--end-date", "2024-05-17", "--expected-images", "57",
            "--destination", str(CASES[0] / "destination")]),
        ("test-state-mismatch-resume", tx_prefix(CASES[2], CASES[2] / "evidence" / "authority-resume", operation="resume", test=True)
         + ["--state", str(CASES[3] / "state.json"), "--run-id", "AUTH-RESUME", "--expected-revision", "1",
            "--expected-owner-id", "AUTH-WRITER", "--dispatcher", str(CASES[2] / "dispatcher.py"),
            "--dispatch-counter", str(CASES[2] / "counter.jsonl"), "--no-dispatch"]),
        ("test-state-mismatch-commit", tx_prefix(CASES[4], CASES[4] / "evidence" / "authority-commit", operation="commit", test=True)
         + ["--state", str(CASES[5] / "state.json"), "--run-id", "AUTH-COMMIT", "--expected-revision", "1",
            "--expected-owner-id", "AUTH-WRITER", "--verification-json", str(CASES[4] / "verification.json")]),
        ("test-state-mismatch-finalize", tx_prefix(CASES[6], CASES[6] / "evidence" / "authority-finalize", operation="finalize", test=True)
         + ["--state", str(CASES[7] / "state.json"), "--run-id", "AUTH-FINALIZE", "--expected-revision", "1",
            "--expected-owner-id", "AUTH-WRITER", "--outcome", "SAFE_ABORT", "--verification-json", str(CASES[6] / "verification.json")]),
        ("test-state-mismatch-duplicate", tx_prefix(CASES[8], CASES[8] / "evidence" / "authority-duplicate", operation="duplicate-check", test=True)
         + ["--state", str(CASES[9] / "state.json"), "--group-key", GROUP, "--start-date", "2024-05-13",
            "--end-date", "2024-05-17", "--expected-images", "57", "--destination", str(CASES[8] / "destination")]),
        ("test-missing-root", ["/usr/bin/python3", "-m", "line_backup_acceptance", "transaction", "resume",
                               "--state", str(CASES[0] / "state.json"), "--run-id", "AUTH-NO-ROOT", "--expected-revision", "1",
                               "--expected-owner-id", "AUTH-WRITER", "--dispatcher", str(CASES[0] / "dispatcher.py"),
                               "--dispatch-counter", str(CASES[0] / "counter.jsonl"), "--evidence-dir",
                               str(CASES[0] / "evidence" / "authority-no-root"), "--no-dispatch", "--test-mode"]),
    ]
    for label, argv in test_rows:
        touched = {str(path): state_digest(path) for path in {Path(argv[argv.index("--project-root") + 1]) if "--project-root" in argv else CASES[0], CASES[0], CASES[1], CASES[2], CASES[3], CASES[4], CASES[5], CASES[6], CASES[7], CASES[8], CASES[9]}}
        record = run(argv, BASE / "records" / label)
        untouched = {path: state_digest(Path(path)) for path in touched}
        ok = expected(record["result"], record["exit_code"]) and touched == untouched
        results.append({"label": label, "process": record, "before": touched, "after": untouched, "match": ok})

    production_rows = [
        ("prod-missing-config", tx_prefix(production, BASE / "evidence" / "prod-prepare", operation="prepare")
         + ["--run-log", str(production / "state" / "run_log.md"), "--state", str(production / "state" / "backup_state.json"),
            "--run-id", "AUTH-PROD-PREPARE", "--owner-id", "AUTH-PROD-WRITER", "--group-key", GROUP,
            "--start-date", "2024-05-13", "--end-date", "2024-05-17", "--expected-images", "57",
            "--destination", str(production / "destination")]),
        ("prod-alternate-config", tx_prefix(production, BASE / "evidence" / "prod-resume", operation="resume")
         + ["--config", str(alternate / "config" / "line_backup_config.json"), "--run-log", str(production / "state" / "run_log.md"),
            "--state", str(production / "state" / "backup_state.json"), "--run-id", "AUTH-PROD-RESUME", "--expected-revision", "1",
            "--expected-owner-id", "AUTH-PROD-WRITER", "--dispatcher", str(BASE / "dispatcher.py"), "--dispatch-counter", str(BASE / "counter.jsonl"), "--no-dispatch"]),
        ("prod-alternate-run-log", tx_prefix(production, BASE / "evidence" / "prod-commit", operation="commit")
         + ["--config", str(production / "config" / "line_backup_config.json"), "--run-log", str(alternate / "state" / "run_log.md"),
            "--state", str(production / "state" / "backup_state.json"), "--run-id", "AUTH-PROD-COMMIT", "--expected-revision", "1",
            "--expected-owner-id", "AUTH-PROD-WRITER", "--verification-json", str(production / "verification.json")]),
        ("prod-alternate-state", tx_prefix(production, BASE / "evidence" / "prod-finalize", operation="finalize")
         + ["--config", str(production / "config" / "line_backup_config.json"), "--run-log", str(production / "state" / "run_log.md"),
            "--state", str(alternate / "state" / "backup_state.json"), "--run-id", "AUTH-PROD-FINALIZE", "--expected-revision", "1",
            "--expected-owner-id", "AUTH-PROD-WRITER", "--outcome", "SAFE_ABORT", "--verification-json", str(production / "verification.json")]),
        ("prod-outside-destination", tx_prefix(production, BASE / "evidence" / "prod-duplicate", operation="duplicate-check")
         + ["--config", str(production / "config" / "line_backup_config.json"), "--run-log", str(production / "state" / "run_log.md"),
            "--state", str(production / "state" / "backup_state.json"), "--group-key", GROUP, "--start-date", "2024-05-13",
            "--end-date", "2024-05-17", "--expected-images", "57", "--destination", str(BASE / "outside-destination")]),
    ]
    for label, argv in production_rows:
        touched_paths = [production, alternate, BASE / "outside-destination"]
        before = {str(path): state_digest(path) for path in touched_paths}
        record = run(argv, BASE / "records" / label)
        after = {str(path): state_digest(path) for path in touched_paths}
        ok = expected(record["result"], record["exit_code"]) and before == after
        results.append({"label": label, "process": record, "before": before, "after": after, "match": ok})

    summary = {"schema_version": 1, "rows": results, "all_match": all(row["match"] for row in results)}
    write_json(Path(ns.summary), summary)
    print(json.dumps({"all_match": summary["all_match"], "failed": [r["label"] for r in results if not r["match"]]}, sort_keys=True))
    return 0 if summary["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
