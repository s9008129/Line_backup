#!/usr/bin/env python3
"""Literal authority-negative subprocess matrix with a read-only oracle (Rev15 §15.4 / Rev17/Rev18).

Eleven rows: six test-only parser/canonical-path negatives on the allowlisted case
roots (case-01…case-10) and five production-mode negatives against
/private/tmp/line-backup-acceptance-authority/production-root.  Every row must
return INVALID_AUTHORITY, exit 2, before any config/state/lock read or mutation.

Ownership (Rev15 §15.5): the driver creates only its own literal root
/private/tmp/line-backup-acceptance-authority (marker before any fixture content),
never removes or overwrites a root lacking its marker, and removes nothing by
default.  The case roots are foreign, read-only fixture paths pinned by the plan;
the driver hashes only the state/config/run-log/lock/counter/dispatcher paths it
references and never writes into them itself (the product only ever writes the
pinned evidence subdirectories, which is the point of the rows).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR / "automation_verification"))

import harness as H  # noqa: E402

BASE = Path("/private/tmp/line-backup-acceptance-authority")
DRIVER_ID = "authority-negative-driver"
GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"
CASE = lambda index: Path(f"/private/tmp/line-backup-acceptance-case-{index:02d}")  # noqa: E731
PY = "/usr/bin/python3"
TXN = [PY, "-m", "line_backup_acceptance", "transaction"]
EXPECTED = {"failure_class": "INVALID_AUTHORITY", "exit_code": 2, "artifact_readback": "PASS_WITH_NO_STATE_WRITE"}


def case_paths(root: Path) -> list:
    """The fixture-state paths the plan names for the oracle (never the bulk tree)."""
    return [root / "config" / "line_backup_config.json", root / "state" / "backup_state.json",
            root / "state" / "run_log.md", root / ".line-backup-state.lock", root / "counter.jsonl",
            root / "dispatcher.py"]


def rows() -> list:
    c = CASE
    test_rows = [
        ("auth-prepare", TXN + ["prepare", "--project-root", str(c(1)),
                                "--config", str(c(2) / "config" / "line_backup_config.json"),
                                "--run-log", str(c(2) / "state" / "run_log.md"),
                                "--state", str(c(2) / "state" / "backup_state.json"),
                                "--run-id", "AUTH-PREPARE", "--owner-id", "AUTH-WRITER", "--group-key", GROUP,
                                "--start-date", "2024-05-13", "--end-date", "2024-05-17", "--expected-images", "57",
                                "--destination", str(c(1) / "destination"),
                                "--evidence-dir", str(c(1) / "evidence" / "authority-prepare"),
                                "--test-mode"],
         [c(1), c(2)], []),
        ("auth-resume", TXN + ["resume", "--project-root", str(c(3)),
                               "--config", str(c(4) / "config" / "line_backup_config.json"),
                               "--run-log", str(c(4) / "state" / "run_log.md"),
                               "--state", str(c(4) / "state" / "backup_state.json"),
                               "--run-id", "AUTH-RESUME", "--expected-revision", "1",
                               "--expected-owner-id", "AUTH-WRITER",
                               "--dispatcher", str(c(3) / "dispatcher.py"),
                               "--dispatch-counter", str(c(3) / "counter.jsonl"),
                               "--evidence-dir", str(c(3) / "evidence" / "authority-resume"),
                               "--no-dispatch", "--test-mode"],
         [c(3), c(4)], [c(3) / "counter.jsonl"]),
        ("auth-commit", TXN + ["commit", "--project-root", str(c(5)),
                               "--config", str(c(6) / "config" / "line_backup_config.json"),
                               "--run-log", str(c(6) / "state" / "run_log.md"),
                               "--state", str(c(6) / "state" / "backup_state.json"),
                               "--run-id", "AUTH-COMMIT", "--expected-revision", "1",
                               "--expected-owner-id", "AUTH-WRITER",
                               "--verification-json", str(c(5) / "verification.json"),
                               "--evidence-dir", str(c(5) / "evidence" / "authority-commit"),
                               "--test-mode"],
         [c(5), c(6)], []),
        ("auth-finalize", TXN + ["finalize", "--project-root", str(c(7)),
                                 "--config", str(c(8) / "config" / "line_backup_config.json"),
                                 "--run-log", str(c(8) / "state" / "run_log.md"),
                                 "--state", str(c(8) / "state" / "backup_state.json"),
                                 "--run-id", "AUTH-FINALIZE", "--expected-revision", "1",
                                 "--expected-owner-id", "AUTH-WRITER", "--outcome", "SAFE_ABORT",
                                 "--verification-json", str(c(7) / "verification.json"),
                                 "--evidence-dir", str(c(7) / "evidence" / "authority-finalize"),
                                 "--test-mode"],
         [c(7), c(8)], []),
        ("auth-duplicate", TXN + ["duplicate-check", "--project-root", str(c(9)),
                                  "--config", str(c(10) / "config" / "line_backup_config.json"),
                                  "--run-log", str(c(10) / "state" / "run_log.md"),
                                  "--state", str(c(10) / "state" / "backup_state.json"),
                                  "--group-key", GROUP, "--start-date", "2024-05-13", "--end-date", "2024-05-17",
                                  "--expected-images", "57", "--destination", str(c(9) / "destination"),
                                  "--evidence-dir", str(c(9) / "evidence" / "authority-duplicate"),
                                  "--test-mode"],
         [c(9), c(10)], []),
        ("auth-no-root", TXN + ["resume",
                                "--state", str(c(1) / "state" / "backup_state.json"),
                                "--run-id", "AUTH-NO-ROOT", "--expected-revision", "1",
                                "--expected-owner-id", "AUTH-WRITER",
                                "--dispatcher", str(c(1) / "dispatcher.py"),
                                "--dispatch-counter", str(c(1) / "counter.jsonl"),
                                "--evidence-dir", str(c(1) / "evidence" / "authority-no-root"),
                                "--no-dispatch", "--test-mode"],
         [c(1)], [c(1) / "counter.jsonl"]),
    ]
    production = BASE / "production-root"
    alternate = BASE / "alternate"
    prod_rows = [
        ("prod-missing-config", TXN + ["prepare", "--project-root", str(production),
                                       "--run-log", str(production / "state" / "run_log.md"),
                                       "--state", str(production / "state" / "backup_state.json"),
                                       "--run-id", "AUTH-PROD-PREPARE", "--owner-id", "AUTH-PROD-WRITER",
                                       "--group-key", GROUP, "--start-date", "2024-05-13", "--end-date", "2024-05-17",
                                       "--expected-images", "57", "--destination", str(production / "destination"),
                                       "--evidence-dir", str(BASE / "evidence" / "prod-prepare")],
         [production, alternate], []),
        ("prod-alternate-config", TXN + ["resume", "--project-root", str(production),
                                         "--config", str(alternate / "config" / "line_backup_config.json"),
                                         "--run-log", str(production / "state" / "run_log.md"),
                                         "--state", str(production / "state" / "backup_state.json"),
                                         "--run-id", "AUTH-PROD-RESUME", "--expected-revision", "1",
                                         "--expected-owner-id", "AUTH-PROD-WRITER",
                                         "--dispatcher", str(BASE / "dispatcher.py"),
                                         "--dispatch-counter", str(BASE / "counter.jsonl"),
                                         "--evidence-dir", str(BASE / "evidence" / "prod-resume"), "--no-dispatch"],
         [production, alternate], [BASE / "counter.jsonl"]),
        ("prod-alternate-run-log", TXN + ["commit", "--project-root", str(production),
                                          "--config", str(production / "config" / "line_backup_config.json"),
                                          "--run-log", str(alternate / "state" / "run_log.md"),
                                          "--state", str(production / "state" / "backup_state.json"),
                                          "--run-id", "AUTH-PROD-COMMIT", "--expected-revision", "1",
                                          "--expected-owner-id", "AUTH-PROD-WRITER",
                                          "--verification-json", str(production / "verification.json"),
                                          "--evidence-dir", str(BASE / "evidence" / "prod-commit")],
         [production, alternate], []),
        ("prod-alternate-state", TXN + ["finalize", "--project-root", str(production),
                                        "--config", str(production / "config" / "line_backup_config.json"),
                                        "--run-log", str(production / "state" / "run_log.md"),
                                        "--state", str(alternate / "state" / "backup_state.json"),
                                        "--run-id", "AUTH-PROD-FINALIZE", "--expected-revision", "1",
                                        "--expected-owner-id", "AUTH-PROD-WRITER", "--outcome", "SAFE_ABORT",
                                        "--verification-json", str(production / "verification.json"),
                                        "--evidence-dir", str(BASE / "evidence" / "prod-finalize")],
         [production, alternate], []),
        ("prod-outside-destination", TXN + ["duplicate-check", "--project-root", str(production),
                                            "--config", str(production / "config" / "line_backup_config.json"),
                                            "--run-log", str(production / "state" / "run_log.md"),
                                            "--state", str(production / "state" / "backup_state.json"),
                                            "--group-key", GROUP, "--start-date", "2024-05-13",
                                            "--end-date", "2024-05-17", "--expected-images", "57",
                                            "--destination", str(BASE / "outside-destination"),
                                            "--evidence-dir", str(BASE / "evidence" / "prod-duplicate")],
         [production, alternate], []),
    ]
    return [{"label": label, "argv": argv, "mode": "test",
             "touched": sorted({str(path) for root in roots for path in case_paths(root)}),
             "counters": [str(path) for path in counters]}
            for label, argv, roots, counters in test_rows] + [
        {"label": label, "argv": argv, "mode": "production",
         "touched": sorted({str(path) for root in roots for path in _production_paths(root)}),
         "counters": [str(path) for path in counters]}
        for label, argv, roots, counters in prod_rows]


def _production_paths(root: Path) -> list:
    return case_paths(root) + [root / "verification.json", BASE / "outside-destination",
                               BASE / "dispatcher.py"]


def snapshot(paths: list) -> dict:
    return {path: H.sha256_file(Path(path)) if Path(path).is_file() else None for path in paths}


def counter_lines(path: str) -> int:
    target = Path(path)
    if not target.is_file():
        return 0
    return len([line for line in target.read_text(encoding="utf-8").splitlines() if line.strip()])


def chain_ok(evidence: Path) -> bool:
    result_path, manifest_path = evidence / "result.json", evidence / "manifest.json"
    if not (result_path.is_file() and manifest_path.is_file()):
        return False
    data = result_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    names = {item["path"] for item in manifest.get("artifacts") or []}
    return (manifest.get("result_sha256") == H.sha256_bytes(data)
            and manifest.get("result_bytes") == len(data)
            and "result.json" in names and "manifest.json" not in names)


def build_fixtures() -> dict:
    """Create only this driver's own literal root and the production fixture inside it."""
    owned = H.ensure_owned_root(BASE, DRIVER_ID)
    H.reset_owned_content(BASE)
    production, alternate = BASE / "production-root", BASE / "alternate"
    backup = production / "backup"
    destination = backup / "destination"
    destination.mkdir(parents=True)
    (production / "config").mkdir()
    (production / "state").mkdir()
    config = {"schema_version": 2, "group_key": GROUP, "group_name": "authority production fixture",
              "backup_root": str(backup), "app_identifier": "jp.naver.line.mac",
              "max_albums_per_run": 50, "recovery_limit": 1, "poll_interval_seconds": 5,
              "stable_samples": 3, "max_wait_seconds": 60}
    state = {"schema_version": 2, "revision": 1, "current_run_id": None, "active_writer_id": None,
             "context_lock": None, "runs": [], "verified_albums": []}
    H.write_json(production / "config" / "line_backup_config.json", config)
    H.write_json(production / "state" / "backup_state.json", state)
    (production / "state" / "run_log.md").write_text("authority production fixture run log\n", encoding="utf-8")
    (alternate / "config").mkdir(parents=True)
    (alternate / "state").mkdir()
    H.write_json(alternate / "config" / "line_backup_config.json", config)
    H.write_json(alternate / "state" / "backup_state.json", state)
    (alternate / "state" / "run_log.md").write_text("alternate run log\n", encoding="utf-8")
    (BASE / "dispatcher.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (BASE / "counter.jsonl").touch()
    return owned


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--evidence-dir")
    ap.add_argument("--clean-owned", action="store_true")
    ns = ap.parse_args()

    build_fixtures()
    env = {"LC_ALL": "C", "LANG": "C", "PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0",
           "PYTHONPATH": str(REPO / "src")}
    results = []
    for row in rows():
        label = row["label"]
        evidence = Path(row["argv"][row["argv"].index("--evidence-dir") + 1])
        before = snapshot(row["touched"])
        counters_before = {path: counter_lines(path) for path in row["counters"]}
        process = subprocess.run(row["argv"], cwd=REPO, env=env, capture_output=True, text=True, check=False)
        after = snapshot(row["touched"])
        counters_after = {path: counter_lines(path) for path in row["counters"]}
        try:
            product = json.loads(process.stdout.strip().splitlines()[-1])
        except (IndexError, ValueError, json.JSONDecodeError):
            product = {}
        observed = {key: product.get(key) for key in EXPECTED}
        checks = {
            "exit_2": process.returncode == 2,
            "invalid_authority": observed["failure_class"] == "INVALID_AUTHORITY",
            "no_state_write": before == after,
            "no_new_counter_lines": all(counters_after[path] == counters_before.get(path, 0)
                                        for path in row["counters"]) if row["counters"] else True,
            "result_artifact_readback": observed["artifact_readback"] == "PASS_WITH_NO_STATE_WRITE",
            "evidence_chain_readback": chain_ok(evidence),
        }
        record = {"label": label, "mode": row["mode"], "argv": row["argv"], "exit_code": process.returncode,
                  "expected": dict(EXPECTED), "observed": observed, "checks": checks,
                  "before": before, "after": after, "counters_before": counters_before,
                  "counters_after": counters_after,
                  "match": bool(process.returncode == 2 and observed == EXPECTED and all(checks.values()))}
        results.append(record)

    summary = {"schema_version": 1, "driver_id": DRIVER_ID, "task_id": H.TASK_ID,
               "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "program_hashes": H.program_hashes(), "rows": results,
               "all_match": all(record["match"] for record in results)}
    if ns.evidence_dir:
        evidence_dir = Path(ns.evidence_dir)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        H.write_json(evidence_dir / "summary.json", summary)
        H.write_tree_manifest(evidence_dir)
    cleanup = None
    if ns.clean_owned:
        cleanup = H.clean_owned_root(BASE, DRIVER_ID)
        summary["cleanup"] = cleanup
        H.write_json(Path(ns.summary), summary)
    else:
        H.write_json(Path(ns.summary), summary)
    print(json.dumps({"all_match": summary["all_match"],
                      "failed": [r["label"] for r in results if not r["match"]], "cleanup": cleanup},
                     ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
