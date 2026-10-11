#!/usr/bin/env python3
"""ML07 frozen, single-launch check runner. CLI accepts only a check ID."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import selectors
import signal
import subprocess
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
R = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
EPOCH = R / "epochs/e01"
TASK_ID = "TASK-20261010-line-v3-live-e2e"
SPECS = EPOCH / "check-specs.json"
FREEZE = EPOCH / "check-specs-freeze.json"
POLICY = EPOCH / "output-policy.json"
sys.path.insert(0, str(EPOCH / "tools"))
from evidence_io import publish_exclusive  # noqa: E402
from output_policy import OutputPolicy  # noqa: E402


def digest(path: pathlib.Path) -> tuple[int, str]:
    raw = path.read_bytes()
    return len(raw), hashlib.sha256(raw).hexdigest()


def command(*argv: str) -> bytes:
    return subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def ref(relative: str, data: bytes, cap: int, policy: OutputPolicy) -> dict:
    decision = policy.authorize_prewrite(path=relative, phase="RUN_CHECK", producer="checks/run_command.py", entry_type="REGULAR", byte_count=len(data), operation="CREATE", preexisting=(ROOT / relative).exists() or (ROOT / relative).is_symlink())
    if not decision.allowed:
        raise RuntimeError(f"OUTPUT_POLICY:{decision.code}:{relative}")
    return publish_exclusive(ROOT, relative, data, max_bytes=cap)


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def preflight(check_id: str) -> tuple[dict, dict, dict, OutputPolicy]:
    if pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != EPOCH / "checks/run_command.py":
        raise RuntimeError("WRONG_CWD_OR_RUNNER")
    specs = json.loads(SPECS.read_bytes())
    freeze = json.loads(FREEZE.read_bytes())
    policy = OutputPolicy.load(POLICY, ROOT)
    if specs.get("task_id") != TASK_ID or specs.get("epoch") != str(EPOCH) or freeze.get("task_id") != TASK_ID or freeze.get("epoch") != str(EPOCH):
        raise RuntimeError("SPEC_IDENTITY")
    if digest(SPECS)[1] != freeze.get("specs_sha256") or digest(POLICY)[1] != freeze.get("policy_sha256"):
        raise RuntimeError("SPEC_OR_POLICY_DRIFT")
    if digest(EPOCH / "source-freeze.json")[1] != policy.source_freeze_sha256 or freeze.get("source_freeze_sha256") != policy.source_freeze_sha256:
        raise RuntimeError("SOURCE_FREEZE_DRIFT")
    check = next((c for c in specs["checks"] if c["check_id"] == check_id), None)
    if check is None:
        raise RuntimeError("UNKNOWN_CHECK_ID")
    if command("git", "rev-parse", "HEAD").decode().strip() != freeze["head"] or command("git", "branch", "--show-current").decode().strip() != freeze["branch"]:
        raise RuntimeError("GIT_HEAD_OR_BRANCH_DRIFT")
    index_path = pathlib.Path(command("git", "rev-parse", "--git-path", "index").decode().strip())
    if not index_path.is_absolute():
        index_path = ROOT / index_path
    if digest(index_path)[1] != freeze["index_sha256"] or command("git", "diff", "--cached", "--name-only"):
        raise RuntimeError("GIT_INDEX_DRIFT")
    for rel, expected in freeze["source_hashes"].items():
        if digest(ROOT / rel)[1] != expected:
            raise RuntimeError(f"SOURCE_DRIFT:{rel}")
    for absolute, expected in freeze["executables"].items():
        if digest(pathlib.Path(absolute))[1] != expected:
            raise RuntimeError(f"EXECUTABLE_DRIFT:{absolute}")
    base = f"{EPOCH.relative_to(ROOT).as_posix()}/evidence/checks/{check_id}"
    paths = {suffix: f"{base}.{suffix}" for suffix in ("claim.json", "invocation.json", "stdout", "stderr", "receipt.json")}
    for suffix, rel in paths.items():
        if (ROOT / rel).exists() or (ROOT / rel).is_symlink():
            raise RuntimeError(f"OUTPUT_COLLISION:{suffix}")
        rule = policy.rule_for(rel)
        if not rule or rule["producer"] != "checks/run_command.py" or "RUN_CHECK" not in rule["allowed_phase"] or rule["lifecycle"] != "CREATE_ONCE":
            raise RuntimeError(f"OUTPUT_POLICY_MISSING:{rel}")
    return check, paths, freeze, policy


def child_environment() -> tuple[dict, dict]:
    env = dict(os.environ)
    controlled = {
        "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(EPOCH / "runtime/site-packages"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LINE_BACKUP_BATCH_TASK": str(R),
        "LINE_BACKUP_INSPECTION_TEST_ROOT": str(EPOCH / "fixtures"),
        "LINE_BACKUP_INSPECTION_FIXTURES": str(EPOCH / "fixtures/swift-inspection"),
        "TMPDIR": str(EPOCH / "tmp"), "TMP": str(EPOCH / "tmp"), "TEMP": str(EPOCH / "tmp"),
        "CLANG_MODULE_CACHE_PATH": str(EPOCH / "module-cache/clang"),
        "SWIFTPM_MODULECACHE_OVERRIDE": str(EPOCH / "module-cache/swift"),
    }
    diff = {k: {"previous_present": k in env, "effective": v} for k, v in controlled.items() if env.get(k) != v}
    env.update(controlled)
    return env, diff


def run_child(argv: list[str], env: dict, timeout: int, cap: int) -> tuple[dict, bytes, bytes]:
    started = time.monotonic()
    p = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, shell=False)
    selector = selectors.DefaultSelector()
    for stream, label in ((p.stdout, "stdout"), (p.stderr, "stderr")):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, label)
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    stop_reason = None
    try:
        while selector.get_map() or p.poll() is None:
            if time.monotonic() - started > timeout:
                stop_reason = "TIMEOUT"
                break
            for key, _ in selector.select(timeout=0.1):
                try:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buf = buffers[key.data]
                if len(buf) + len(chunk) > cap:
                    buf.extend(chunk[: max(0, cap - len(buf))])
                    stop_reason = f"{key.data.upper()}_CAP"
                    break
                buf.extend(chunk)
            if stop_reason:
                break
        if stop_reason:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        exit_code = p.wait(timeout=5)
    finally:
        selector.close()
        p.stdout.close(); p.stderr.close()
    return {"exit_code": exit_code, "stop_reason": stop_reason, "elapsed_ms": round((time.monotonic() - started) * 1000), "pid": p.pid, "reaped": True}, bytes(buffers["stdout"]), bytes(buffers["stderr"])


def run(check_id: str) -> dict:
    check, paths, freeze, policy = preflight(check_id)
    env, env_diff = child_environment()
    claim = {"format": "ML07_CHECK_CLAIM_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "check_id": check_id, "phase": "RUN_CHECK", "producer": "checks/run_command.py", "created_at_utc": utc(), "freeze_sha256": digest(FREEZE)[1], "source_freeze_sha256": policy.source_freeze_sha256, "argv": check["argv"]}
    claim_ref = ref(paths["claim.json"], encoded(claim), 1_000_000, policy)
    invocation = {"format": "ML07_CHECK_INVOCATION_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "check_id": check_id, "phase": "RUN_CHECK", "producer": "checks/run_command.py", "source_freeze_sha256": policy.source_freeze_sha256, "claim": claim_ref, "started_at_utc": utc(), "argv": check["argv"], "cwd": str(ROOT), "effective_env_diff": env_diff, "automatic_retry": False}
    invocation_ref = ref(paths["invocation.json"], encoded(invocation), 1_000_000, policy)
    try:
        outcome, stdout, stderr = run_child(check["argv"], env, check["timeout_seconds"], check["stream_cap_bytes"])
    except BaseException as exc:
        outcome = {"exit_code": None, "stop_reason": f"LAUNCH_OR_REAP_ERROR:{type(exc).__name__}:{exc}", "reaped": False}
        stdout = stderr = b""
    out_ref = ref(paths["stdout"], stdout, check["stream_cap_bytes"], policy)
    err_ref = ref(paths["stderr"], stderr, check["stream_cap_bytes"], policy)
    passed = outcome.get("exit_code") == 0 and outcome.get("reaped") is True and outcome.get("stop_reason") is None
    receipt = {"format": "ML07_CHECK_RECEIPT_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "check_id": check_id, "phase": "RUN_CHECK", "producer": "checks/run_command.py", "source_freeze_sha256": policy.source_freeze_sha256, "verdict": "PASS" if passed else "FAIL", "outcome": outcome, "claim": claim_ref, "invocation": invocation_ref, "artifacts": [claim_ref, invocation_ref, out_ref, err_ref], "completed_at_utc": utc()}
    receipt_ref = ref(paths["receipt.json"], encoded(receipt), 1_000_000, policy)
    return {"verdict": receipt["verdict"], "receipt": receipt_ref, "outcome": outcome}


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"verdict": "REFUSED", "reason": "ARGUMENTS"}))
        return 2
    try:
        result = run(sys.argv[1])
    except BaseException as exc:
        print(json.dumps({"verdict": "REFUSED", "reason": f"{type(exc).__name__}:{exc}"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
