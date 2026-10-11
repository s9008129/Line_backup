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
import stat
import subprocess
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
R = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
EPOCH = pathlib.Path(os.path.realpath(__file__)).parent.parent
TASK_ID = "TASK-20261010-line-v3-live-e2e"
FAMILY_IDS = {
    "evidence": {"E01-evidence-policy", "E02-runner-selftest", "B01-baseline-pair", "B02-preservation-pair"},
    "production": {"N01-syntax-01", "N01-syntax-02", "N01-syntax-03", "N01-syntax-04", "N01-syntax-05", "N01-syntax-06", "N01-syntax-07", "N02-tests", "P01-batch", "P02-binding", "P03-transaction", "P04-v2", "S01-build", "S02-tests"},
}


def family_for(check_id: str) -> str:
    matches = [family for family, ids in FAMILY_IDS.items() if check_id in ids]
    if len(matches) != 1:
        raise RuntimeError("UNKNOWN_CHECK_ID")
    return matches[0]
sys.path.insert(0, str(EPOCH / "tools"))
from evidence_io import publish_exclusive  # noqa: E402
from output_policy import OutputPolicy  # noqa: E402


def digest(path: pathlib.Path) -> tuple[int, str]:
    raw = path.read_bytes()
    return len(raw), hashlib.sha256(raw).hexdigest()


def command(*argv: str) -> bytes:
    if argv and argv[0] == "git":
        argv = ("git", "--no-optional-locks", *argv[1:])
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
    if pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != EPOCH / "checks/run_command.py" or EPOCH.parent != R / "epochs" or EPOCH.name not in ("e01", "e02", "e03"):
        raise RuntimeError("WRONG_CWD_OR_RUNNER")
    family = family_for(check_id)
    names = ("check-specs.json", "check-specs-freeze.json", "output-policy.json", "source-freeze.json") if family == "evidence" else ("production-check-specs.json", "production-check-specs-freeze.json", "production-output-policy.json", "production-source-freeze.json")
    SPECS, FREEZE, POLICY, SOURCE_FREEZE = (EPOCH / name for name in names)
    if not all(path.is_file() and not path.is_symlink() for path in (SPECS, FREEZE, POLICY, SOURCE_FREEZE)):
        raise RuntimeError("FAMILY_FREEZE_MISSING:" + family)
    specs = json.loads(SPECS.read_bytes())
    freeze = json.loads(FREEZE.read_bytes())
    source_freeze = json.loads(SOURCE_FREEZE.read_bytes())
    policy = OutputPolicy.load(POLICY, ROOT)
    if specs.get("family") != family or freeze.get("family") != family or policy.document.get("family") != family:
        raise RuntimeError("FAMILY_BINDING_MISMATCH:" + family)
    if source_freeze.get("family") != family or source_freeze.get("task_id") != TASK_ID or source_freeze.get("epoch") != str(EPOCH):
        raise RuntimeError("SOURCE_FAMILY_IDENTITY:" + family)
    if specs.get("task_id") != TASK_ID or specs.get("epoch") != str(EPOCH) or freeze.get("task_id") != TASK_ID or freeze.get("epoch") != str(EPOCH):
        raise RuntimeError("SPEC_IDENTITY")
    if digest(SPECS)[1] != freeze.get("specs_sha256") or digest(POLICY)[1] != freeze.get("policy_sha256"):
        raise RuntimeError("SPEC_OR_POLICY_DRIFT")
    if source_freeze.get("source_hashes") != freeze.get("source_hashes"):
        raise RuntimeError("FAMILY_SOURCE_MEMBERSHIP_DRIFT")
    if digest(SOURCE_FREEZE)[1] != policy.source_freeze_sha256 or freeze.get("source_freeze_sha256") != policy.source_freeze_sha256:
        raise RuntimeError("SOURCE_FREEZE_DRIFT")
    check = next((c for c in specs["checks"] if c["check_id"] == check_id), None)
    if check is None or check.get("family") != family:
        raise RuntimeError("CHECK_FAMILY_MISSING_OR_MISMATCH:" + family)
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
    _verify_required_directories(policy, family, paths)
    return check, paths, freeze, policy


def child_environment(family: str) -> tuple[dict, dict]:
    env = dict(os.environ)
    controlled = {
        "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(EPOCH / "runtime/site-packages"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LINE_BACKUP_BATCH_TASK": str(R),
        "TMPDIR": str(EPOCH / "tmp"), "TMP": str(EPOCH / "tmp"), "TEMP": str(EPOCH / "tmp"),
    }
    if family == "production":
        controlled.update({
            "LINE_BACKUP_INSPECTION_TEST_ROOT": str(EPOCH / "fixtures"),
            "LINE_BACKUP_INSPECTION_FIXTURES": str(EPOCH / "fixtures/swift-inspection"),
            "CLANG_MODULE_CACHE_PATH": str(EPOCH / "module-cache/clang"),
            "SWIFTPM_MODULECACHE_OVERRIDE": str(EPOCH / "module-cache/swift"),
        })
    diff = {k: {"previous_present": k in env, "effective": v} for k, v in controlled.items() if env.get(k) != v}
    env.update(controlled)
    return env, diff


def _receipt_directory_refs(policy: OutputPolicy, family: str) -> dict[str, dict]:
    """Collect directory identities only from frozen, exact producer receipts."""
    evidence_source_path = EPOCH / "source-freeze.json"
    evidence_policy_path = EPOCH / "output-policy.json"
    if not all(p.is_file() and not p.is_symlink() for p in (evidence_source_path, evidence_policy_path)):
        raise RuntimeError("EVIDENCE_FREEZE_MISSING")
    evidence_source = json.loads(evidence_source_path.read_bytes())
    evidence_policy = OutputPolicy.load(evidence_policy_path, ROOT)
    evidence_sha = digest(evidence_source_path)[1]
    if (evidence_source.get("family") != "evidence" or evidence_source.get("task_id") != TASK_ID
            or evidence_source.get("epoch") != str(EPOCH) or evidence_policy.document.get("family") != "evidence"
            or evidence_policy.source_freeze_sha256 != evidence_sha):
        raise RuntimeError("EVIDENCE_FREEZE_BINDING")
    if family == "evidence":
        if policy.source_freeze_sha256 != evidence_sha:
            raise RuntimeError("EVIDENCE_POLICY_FREEZE_BINDING")
        production_sha = None
    else:
        production_source_path = EPOCH / "production-source-freeze.json"
        if not production_source_path.is_file() or production_source_path.is_symlink():
            raise RuntimeError("PRODUCTION_FREEZE_MISSING")
        production_source = json.loads(production_source_path.read_bytes())
        production_sha = digest(production_source_path)[1]
        if (production_source.get("family") != "production" or production_source.get("task_id") != TASK_ID
                or production_source.get("epoch") != str(EPOCH) or policy.document.get("family") != "production"
                or policy.source_freeze_sha256 != production_sha):
            raise RuntimeError("PRODUCTION_FREEZE_BINDING")
    paths = [
        (EPOCH / "runtime/dependency-preparation-receipt.json", "tools/prepare_dependencies.py", "RUNTIME_PREPARE", "directories", evidence_sha),
        (EPOCH / "evidence/materialization-receipt.json", "tools/prepare_epoch.py", "MATERIALIZE", "artifacts", evidence_sha),
    ]
    if family == "production":
        paths.append((EPOCH / "production-freeze-receipt.json", "tools/prepare_production_family.py", "PRODUCTION_FREEZE", "directories", production_sha))
    refs: dict[str, dict] = {}
    for receipt_path, producer, phase, field, expected_source_sha in paths:
        if not receipt_path.is_file() or receipt_path.is_symlink():
            raise RuntimeError("DIRECTORY_RECEIPT_MISSING:" + receipt_path.name)
        doc = json.loads(receipt_path.read_bytes())
        if (doc.get("task_id") != TASK_ID or doc.get("epoch") != str(EPOCH)
                or doc.get("producer") != producer or doc.get("phase") != phase
                or doc.get("source_freeze_sha256") != expected_source_sha):
            raise RuntimeError("DIRECTORY_RECEIPT_BINDING:" + receipt_path.name)
        for item in doc.get(field, []):
            if isinstance(item, dict) and item.get("identity_readback") is True and isinstance(item.get("path"), str):
                if item["path"] in refs:
                    raise RuntimeError("DIRECTORY_RECEIPT_DUPLICATE:" + item["path"])
                refs[item["path"]] = item
    return refs


def _verify_required_directories(policy: OutputPolicy, family: str, output_paths: dict[str, str]) -> None:
    for rel in output_paths.values():
        parent = (ROOT / rel).parent
        current = ROOT
        for part in parent.relative_to(ROOT).parts:
            current = current / part
            try:
                st = current.lstat()
            except OSError as exc:
                raise RuntimeError("RUN_PARENT_MISSING:" + current.relative_to(ROOT).as_posix()) from exc
            if current.is_symlink() or not stat.S_ISDIR(st.st_mode):
                raise RuntimeError("RUN_PARENT_NOT_DIRECTORY:" + current.relative_to(ROOT).as_posix())
    refs = _receipt_directory_refs(policy, family)
    required: set[str] = set()
    epoch_rel = EPOCH.relative_to(ROOT).as_posix()
    for rel in output_paths.values():
        parts = rel.split("/")
        for index in range(1, len(parts)):
            parent = "/".join(parts[:index])
            if parent.startswith(epoch_rel + "/") or parent == epoch_rel:
                rule = policy.rule_for(parent)
                if rule and rule.get("entry_type") == "DIRECTORY":
                    required.add(parent)
    if family == "production":
        required.update(epoch_rel + "/" + name for name in
                        ("module-cache", "module-cache/clang", "module-cache/swift", "fixtures", "fixtures/swift-inspection"))
    for rel in sorted(required):
        expected = refs.get(rel)
        if not expected:
            raise RuntimeError("RUN_PARENT_RECEIPT_MISSING:" + rel)
        path = ROOT / rel
        try:
            st = path.lstat()
        except OSError as exc:
            raise RuntimeError("RUN_PARENT_MISSING:" + rel) from exc
        if (path.is_symlink() or not stat.S_ISDIR(st.st_mode)
                or st.st_dev != expected.get("dev") or st.st_ino != expected.get("ino")
                or stat.S_IMODE(st.st_mode) != expected.get("mode") or st.st_uid != expected.get("uid")
                or st.st_gid != expected.get("gid")):
            raise RuntimeError("RUN_PARENT_IDENTITY_MISMATCH:" + rel)


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
    family = family_for(check_id)
    freeze_path = EPOCH / ("check-specs-freeze.json" if family == "evidence" else "production-check-specs-freeze.json")
    env, env_diff = child_environment(family)
    claim = {"format": "ML07_CHECK_CLAIM_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "check_id": check_id, "family": family, "phase": "RUN_CHECK", "producer": "checks/run_command.py", "created_at_utc": utc(), "freeze_sha256": digest(freeze_path)[1], "source_freeze_sha256": policy.source_freeze_sha256, "argv": check["argv"]}
    claim_ref = ref(paths["claim.json"], encoded(claim), 1_000_000, policy)
    invocation = {"format": "ML07_CHECK_INVOCATION_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "check_id": check_id, "family": family, "phase": "RUN_CHECK", "producer": "checks/run_command.py", "source_freeze_sha256": policy.source_freeze_sha256, "claim": claim_ref, "started_at_utc": utc(), "argv": check["argv"], "cwd": str(ROOT), "effective_env_diff": env_diff, "automatic_retry": False}
    invocation_ref = ref(paths["invocation.json"], encoded(invocation), 1_000_000, policy)
    try:
        outcome, stdout, stderr = run_child(check["argv"], env, check["timeout_seconds"], check["stream_cap_bytes"])
    except BaseException as exc:
        outcome = {"exit_code": None, "stop_reason": f"LAUNCH_OR_REAP_ERROR:{type(exc).__name__}:{exc}", "reaped": False}
        stdout = stderr = b""
    out_ref = ref(paths["stdout"], stdout, check["stream_cap_bytes"], policy)
    err_ref = ref(paths["stderr"], stderr, check["stream_cap_bytes"], policy)
    passed = outcome.get("exit_code") == 0 and outcome.get("reaped") is True and outcome.get("stop_reason") is None
    receipt = {"format": "ML07_CHECK_RECEIPT_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "check_id": check_id, "family": family, "phase": "RUN_CHECK", "producer": "checks/run_command.py", "source_freeze_sha256": policy.source_freeze_sha256, "verdict": "PASS" if passed else "FAIL", "outcome": outcome, "claim": claim_ref, "invocation": invocation_ref, "artifacts": [claim_ref, invocation_ref, out_ref, err_ref], "completed_at_utc": utc()}
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
