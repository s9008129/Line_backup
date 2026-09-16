#!/usr/bin/env python3
"""W-WAVE-RUN — run the whole Phase-2 repair wave in both orders over disjoint durable roots.

Order `driver-first` (ownership-last): R1 -> R2 -> R3 -> R4 -> R5 -> R6-status -> R7 -> R6-ownership.
Order `ownership-first`:               R6-ownership -> R1 -> R2 -> R3 -> R4 -> R5 -> R6-status -> R7.

Every driver runs the real operator CLI as real subprocesses and writes its own evidence
directory with an append-only SHA-256/bytes manifest. The wave then writes the order-level
observation and a tree manifest excluding only `manifest.json` and its own derived read-back
report, and runs `verify_evidence.py` as an independent read-back over the order root, whose
report lands in the same durable root. Durable roots only: `/private/tmp` is working space,
never evidence storage.

Append-only: an attempt/order root that already contains content is refused; a re-run goes to a
new attempt root. Drivers share the product's literal case-root namespace, so the two orders run
sequentially, never in parallel.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as H  # noqa: E402

DRIVER_ID = "wave-run-all"
TASK_ID = H.TASK_ID
DEFAULT_ATTEMPT = H.WORK / "evidence/20260916-auto-verification/attempt-02"
DRAFT_DIR = Path("/private/tmp/line-backup-acceptance-wave")
PYCACHE = "/private/tmp/line-backup-acceptance-pycache"

R1 = ("phase2-r1", "run_phase2_r1_crash_window.py", "SAFE_NO_SECOND_DISPATCH_AFTER_CRASH_WINDOW")
R2 = ("phase2-r2", "run_phase2_r2_loaded_intent.py", "SAFE_FRESH_PROCESS_NEVER_DISPATCHES")
R3 = ("phase2-r3", "run_phase2_r3_preconditions.py", "SAFE_R3_PRECONDITION_REFUSALS")
R4 = ("phase2-r4", "run_phase2_r4_finalize_trust.py", "SAFE_R4_REFUSALS_AND_CLOSED_LOOP")
R5 = ("phase2-r5", "run_phase2_r5_verifier_gaps.py", "SAFE_R5_AXIS_AND_READ_ERROR_CONTRACT")
R6_STATUS = ("phase2-r6-status", "run_phase2_r6_status_selfcert.py",
             "SAFE_R6_STATUS_SCENARIO_LABELLED_NON_ACCEPTANCE")
R6_OWNERSHIP = ("phase2-r6-ownership", "run_phase2_r6_harness_ownership.py", "NO_DELETION_OBSERVED")
R7 = ("phase2-r7", "run_phase2_r7_integration.py", "SAFE_R7_LOOP_CLOSED_AND_DUPLICATE_REFUSED")

ORDERS = {
    "driver-first": [R1, R2, R3, R4, R5, R6_STATUS, R7, R6_OWNERSHIP],
    "ownership-first": [R6_OWNERSHIP, R1, R2, R3, R4, R5, R6_STATUS, R7],
}


def driver_env() -> dict:
    env = os.environ.copy()
    env.update({"PYTHONPATH": str(H.SRC), "LC_ALL": "C", "PATH": "/usr/bin:/bin",
                "PYTHONHASHSEED": "0", "PYTHONPYCACHEPREFIX": PYCACHE})
    return env


def env_fingerprint(env: dict) -> dict:
    return {"PYTHONPATH": env.get("PYTHONPATH"), "LC_ALL": env.get("LC_ALL"), "PATH": env.get("PATH"),
            "PYTHONHASHSEED": env.get("PYTHONHASHSEED"), "PYTHONPYCACHEPREFIX": env.get("PYTHONPYCACHEPREFIX")}


def run_one(driver_dir: str, script: str, safe_verdict: str, order_root: Path, timeout: float) -> dict:
    ev_dir = order_root / driver_dir
    argv = ["/usr/bin/python3", str(H.WORK / "tests/automation_verification" / script),
            "--evidence-dir", str(ev_dir)]
    env = driver_env()
    record_dir = order_root / "driver-records" / driver_dir
    record_dir.mkdir(parents=True, exist_ok=True)
    H.write_json(record_dir / "argv.json", {"argv": argv, "cwd": str(H.WORK),
                                            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                            "env_fingerprint": env_fingerprint(env), "secrets_removed": True})
    try:
        proc = subprocess.run(argv, cwd=str(H.WORK), env=env, capture_output=True, text=True, check=False,
                              timeout=timeout)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\n<wave timeout after {timeout}s>\n"
        code = -1000
    (record_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    (record_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    (record_dir / "exit-code").write_text(f"{code}\n", encoding="utf-8")
    verdict = None
    observation = ev_dir / "observation.json"
    if observation.is_file():
        try:
            verdict = json.loads(observation.read_text(encoding="utf-8")).get("verdict")
        except Exception as exc:  # noqa: BLE001 - recorded, never raised
            verdict = f"UNREADABLE_OBSERVATION: {exc}"
    safe = (code == 0) and (verdict == safe_verdict)
    return {"driver": driver_dir, "script": script, "argv": argv, "exit_code": code, "verdict": verdict,
            "expected_safe_verdict": safe_verdict, "safe": safe,
            "stdout_tail": stdout.strip().splitlines()[-1] if stdout.strip() else "",
            "stderr_tail": stderr.strip().splitlines()[-1] if stderr.strip() else "",
            "observation": str(observation) if observation.is_file() else None,
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def readback_argv(order_root: Path, output: Path) -> list[str]:
    return ["/usr/bin/python3", str(H.WORK / "tests/automation_verification/verify_evidence.py"),
            "--root", str(order_root), "--output", str(output)]


def run_order(name: str, attempt_root: Path, timeout: float) -> dict:
    order_root = attempt_root / f"order-{name}"
    if order_root.exists() and any(order_root.iterdir()):
        raise SystemExit(f"refusing: order root {order_root} is not empty (append-only evidence)")
    order_root.mkdir(parents=True, exist_ok=True)
    drivers = []
    for driver_dir, script, safe_verdict in ORDERS[name]:
        ev_dir = order_root / driver_dir
        if ev_dir.exists() and any(ev_dir.iterdir()):
            raise SystemExit(f"refusing: driver evidence dir {ev_dir} is not empty (append-only evidence)")
        drivers.append(run_one(driver_dir, script, safe_verdict, order_root, timeout))
    all_safe = all(row["safe"] for row in drivers)

    # Draft read-back (before the order observation exists) into /private/tmp working space:
    # this gives the observation real read-back numbers without churning the durable root.
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    draft_report = DRAFT_DIR / f"{name}-readback-draft.json"
    draft_argv = readback_argv(order_root, draft_report)
    H.write_json(order_root / "driver-records" / "verify-evidence-draft-argv.json",
                 {"argv": draft_argv, "cwd": str(H.WORK), "secrets_removed": True})
    draft = subprocess.run(draft_argv, cwd=str(H.WORK), env=driver_env(), capture_output=True, text=True,
                           check=False, timeout=1800)
    draft_data = json.loads(draft_report.read_text(encoding="utf-8")) if draft_report.is_file() else {}

    observation = {
        "driver": DRIVER_ID, "task_id": TASK_ID, "order": name,
        "order_meaning": ("ownership-last: R1-R7 and the status rows run first, then the ownership probe"
                          if name == "driver-first" else
                          "ownership-first: the ownership probe observes every shared root before any driver runs"),
        "claim": "the whole wave (R1-R7, the 25 acceptance cases, the status rows and the ownership probe) "
                 "runs safely in both orders over disjoint durable roots and every manifest stays readable",
        "attempt_root": str(attempt_root), "order_root": str(order_root),
        "argv": sys.argv, "cwd": str(H.WORK), "interpreter": sys.version,
        "env_fingerprint": env_fingerprint(driver_env()),
        "shared_case_root_note": "both orders use the product's literal /private/tmp case-root namespace; "
                                 "they run sequentially, never in parallel",
        "drivers": drivers, "all_drivers_safe": all_safe,
        "readback": {
            "tool": "tests/automation_verification/verify_evidence.py",
            "final_report": str(order_root / "readback-verification.json"),
            "final_report_note": "the in-tree report is the final pass, run after this observation and the order "
                                 "manifest were frozen; its exit code is recorded in run-all-summary.json",
            "draft_argv": draft_argv, "draft_report": str(draft_report), "draft_exit_code": draft.returncode,
            "draft_counts": {k: draft_data.get(k) for k in ("manifests", "supplements", "artifacts_checked")},
            "draft_problems": (draft_data.get("problems") or [])[:5],
            "draft_uncovered_files": (draft_data.get("uncovered_files") or [])[:5],
        },
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    H.write_json(order_root / "order-observation.json", observation)
    order_manifest = H.write_tree_manifest(order_root, exclude_extra=("readback-verification.json",))

    # Final read-back: the durable report over the frozen order tree.
    final_report = order_root / "readback-verification.json"
    final_argv = readback_argv(order_root, final_report)
    final = subprocess.run(final_argv, cwd=str(H.WORK), env=driver_env(), capture_output=True, text=True,
                           check=False, timeout=1800)
    final_data = json.loads(final_report.read_text(encoding="utf-8")) if final_report.is_file() else {}
    order_safe = all_safe and final.returncode == 0 and final_data.get("verdict") == "PASS"
    return {"order": name, "order_root": str(order_root), "order_safe": order_safe,
            "all_drivers_safe": all_safe, "drivers": drivers,
            "order_manifest": {"files": order_manifest["files"], "total_bytes": order_manifest["total_bytes"],
                               "manifest_sha256": order_manifest["manifest_sha256"]},
            "final_readback": {"argv": final_argv, "exit_code": final.returncode,
                               "verdict": final_data.get("verdict"),
                               "counts": {k: final_data.get(k)
                                          for k in ("manifests", "supplements", "artifacts_checked")},
                               "problems": (final_data.get("problems") or [])[:5],
                               "uncovered_files": (final_data.get("uncovered_files") or [])[:5]},
            "observation": str(order_root / "order-observation.json")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--attempt-root", default=str(DEFAULT_ATTEMPT))
    ap.add_argument("--orders", default="driver-first,ownership-first")
    ap.add_argument("--timeout", type=float, default=5400.0)
    ns = ap.parse_args()
    attempt_root = Path(ns.attempt_root)
    if attempt_root.exists() and (attempt_root / "run-all-summary.json").exists():
        raise SystemExit(f"refusing: {attempt_root / 'run-all-summary.json'} already exists (append-only evidence); "
                         "use a new attempt root or archive the previous summary explicitly")
    attempt_root.mkdir(parents=True, exist_ok=True)
    results = []
    for name in ns.orders.split(","):
        name = name.strip()
        if name not in ORDERS:
            raise SystemExit(f"unknown order {name!r}; choose from {sorted(ORDERS)}")
        print(json.dumps({"running_order": name, "order_root": str(attempt_root / f'order-{name}')},
                         ensure_ascii=False), flush=True)
        results.append(run_order(name, attempt_root, ns.timeout))
    summary = {"driver": DRIVER_ID, "task_id": TASK_ID, "attempt_root": str(attempt_root),
               "argv": sys.argv, "cwd": str(H.WORK), "interpreter": sys.version,
               "host": {"platform": platform.platform(), "python": sys.version.split()[0]},
               "orders": results, "all_orders_safe": all(r["order_safe"] for r in results),
               "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    meta = H.write_json(attempt_root / "run-all-summary.json", summary)
    print(json.dumps({"all_orders_safe": summary["all_orders_safe"],
                      "orders": {r["order"]: {"order_safe": r["order_safe"],
                                              "readback": r["final_readback"]["verdict"],
                                              "drivers": {d["driver"]: d["verdict"] for d in r["drivers"]}}
                                 for r in results},
                      "summary": {"path": meta["path"], "sha256": meta["sha256"], "bytes": meta["bytes"]}},
                     ensure_ascii=False))
    return 0 if summary["all_orders_safe"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
