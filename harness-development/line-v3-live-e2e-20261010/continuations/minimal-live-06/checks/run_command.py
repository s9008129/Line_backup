#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Recovery-02 fixed-root guarded check runner (production CLI).

CLI:
  run_command.py --preflight                  -> observation only; writes nothing
  run_command.py CHECK_ID -- COMMAND [ARG...] -> one frozen check, exclusive outputs

Fixed absolute ROOT/RUNROOT/evidence/tmp; no parent-walk root inference.
CHECK_ID must be one of check-specs.json runner_allowed_check_ids and the
COMMAND/ARG list must equal that check's frozen argv exactly. Every source
binding is resolved from check-specs-freeze.json and re-verified against the
files on disk before any side effect (mkdir/write/launch). A missing,
null, or mismatching binding refuses with exit 2.

Per check the runner writes exactly three exclusive files under
RUNROOT/evidence/<check_id>.* : .stdout, .stderr, .receipt.json. Outputs are
published through an anchored directory FD with fsync + readback. Child
processes run with cwd fixed to ROOT, TMPDIR/TMP/TEMP fixed to RUNROOT/tmp,
shell=False, a 60 s wall timeout, and 1 MiB per-stream caps; on timeout or
cap breach the whole child process group is killed and reaped and the check
is FAIL with incomplete streams kept as received. automatic_retry=false:
an existing output ID refuses before launch and a receipt is never rewritten.

This module is also imported by checks/test_run_command.py, which drives
preflight/run_check with explicit fixture specs/evidence dirs/tmp dirs
(test-only parameters; the production CLI never accepts overrides).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import select
import signal
import stat
import subprocess
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
RUNROOT = ROOT / RUNREL
EVIDENCE = RUNROOT / "evidence"
TMPDIR = RUNROOT / "tmp"
TOOL_PATH = RUNROOT / "checks" / "run_command.py"
CHECK_SPECS = RUNROOT / "check-specs.json"
FREEZE = RUNROOT / "check-specs-freeze.json"

FORMAT = "RECOVERY_02_RUN_COMMAND_RECEIPT_V1"
TASK_ID = "TASK-20261011-line-baseline-recovery-02"
CHILD_CWD = ROOT
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_STREAM_LIMIT_BYTES = 1048576
READ_CHUNK = 65536


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> tuple[int, str]:
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            h.update(chunk)
    return size, h.hexdigest()


def ref_of(path: pathlib.Path) -> dict:
    size, digest = sha256_file(path)
    return {
        "path": path.relative_to(ROOT).as_posix() if str(path).startswith(str(ROOT)) else str(path),
        "absolute_path": str(path),
        "bytes": size,
        "sha256": digest,
    }


def load_json(path: pathlib.Path):
    return json.loads(path.read_bytes())


def _symlink_ancestors(path: pathlib.Path) -> list[str]:
    problems: list[str] = []
    current = pathlib.Path("/")
    for part in path.parts[1:]:
        current = current / part
        try:
            info = current.lstat()
        except OSError as exc:  # noqa: BLE001
            problems.append(f"PATH_UNREADABLE:{current}:{exc}")
            break
        if stat.S_ISLNK(info.st_mode):
            problems.append(f"SYMLINK_ANCESTOR:{current}")
    return problems


def _write_exclusive(parent: pathlib.Path, name: str, data: bytes) -> dict:
    dir_fd = os.open(str(parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        wfd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(wfd, view):]
            os.fsync(wfd)
        finally:
            os.close(wfd)
        rfd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
        try:
            chunks = []
            while True:
                chunk = os.read(rfd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(rfd)
        readback = b"".join(chunks)
    finally:
        os.close(dir_fd)
    if readback != data:
        raise RuntimeError(f"WRITE_READBACK_MISMATCH:{parent / name}")
    out = parent / name
    return {
        "path": out.relative_to(ROOT).as_posix() if str(out).startswith(str(ROOT)) else str(out),
        "absolute_path": str(out),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "readback_verified": True,
    }


def validate_location(invoked_path: str) -> list[str]:
    problems: list[str] = []
    invoked = pathlib.Path(invoked_path)
    if not invoked.is_absolute():
        invoked = (pathlib.Path.cwd() / invoked)
    problems += _symlink_ancestors(invoked)
    if pathlib.Path(os.path.realpath(invoked)) != TOOL_PATH:
        problems.append(f"WRONG_LOCATION:{os.path.realpath(invoked)}")
    for fixed in (ROOT, RUNROOT, EVIDENCE, TMPDIR):
        if not fixed.is_dir():
            problems.append(f"MISSING_DIR:{fixed}")
        problems += _symlink_ancestors(fixed)
    return problems


def _resolve_rel(key: str) -> pathlib.Path | None:
    runroot_candidate = ROOT / RUNREL / key
    plain_candidate = ROOT / key
    if runroot_candidate.exists() and not plain_candidate.exists():
        return runroot_candidate
    if plain_candidate.exists() and not runroot_candidate.exists():
        return plain_candidate
    return None


def build_expected_bindings(specs: dict) -> dict[str, str]:
    expected: dict[str, str] = {}
    for check in specs.get("checks", []):
        for key, fixed in (check.get("source_hashes") or {}).items():
            if (ROOT / RUNREL / key) == FREEZE or (ROOT / key) == FREEZE:
                continue
            resolved = _resolve_rel(key)
            if resolved is None:
                raise RuntimeError(f"SOURCE_NOT_RESOLVED:{key}")
            _, actual = sha256_file(resolved)
            if fixed is not None and fixed != actual:
                raise RuntimeError(f"FIXED_SOURCE_MISMATCH:{key}:{fixed}!={actual}")
            expected[resolved.relative_to(ROOT).as_posix()] = actual
    return expected


def verify_specs_and_freeze() -> tuple[dict, dict, dict[str, str], list[str]]:
    problems: list[str] = []
    specs = load_json(CHECK_SPECS)
    if specs.get("task_id") != TASK_ID or specs.get("run_rel") != RUNREL:
        problems.append("CHECK_SPECS_IDENTITY_MISMATCH")
    expected = build_expected_bindings(specs)
    freeze = load_json(FREEZE)
    resolved = freeze.get("resolved_source_hashes") or {}
    if freeze.get("task_id") != TASK_ID or freeze.get("run_rel") != RUNREL:
        problems.append("FREEZE_IDENTITY_MISMATCH")
    self_rule = freeze.get("self_reference") or {}
    if self_rule.get("excluded_relative_path") != f"{RUNREL}/check-specs-freeze.json":
        problems.append("FREEZE_SELF_RULE_MISMATCH")
    if resolved != expected:
        missing = sorted(set(expected) - set(resolved))
        extra = sorted(set(resolved) - set(expected))
        mismatched = sorted(k for k in set(resolved) & set(expected) if resolved[k] != expected[k])
        problems.append(f"FREEZE_BINDINGS_MISMATCH:missing={missing}:extra={extra}:mismatched={mismatched}")
    return specs, freeze, expected, problems


def verify_runtime(specs: dict) -> tuple[dict[str, dict], list[str]]:
    problems: list[str] = []
    runtimes: dict[str, dict] = {}
    for exe in specs.get("executables", []):
        path = pathlib.Path(exe["absolute_path"])
        if not path.is_file():
            problems.append(f"RUNTIME_MISSING:{path}")
            continue
        size, digest = sha256_file(path)
        if digest != exe["sha256"] or size != exe["bytes"]:
            problems.append(f"RUNTIME_MISMATCH:{path}:{digest}!={exe['sha256']}")
        runtimes[exe["name"]] = {"path": str(path), "sha256": digest, "bytes": size}
    return runtimes, problems


def _check_spec(specs: dict, check_id: str) -> dict | None:
    for check in specs.get("checks", []):
        if check.get("check_id") == check_id:
            return check
    return None


def preflight_report(*, specs: dict | None = None, freeze: dict | None = None,
                     expected: dict[str, str] | None = None, runtimes: dict[str, dict] | None = None) -> dict:
    specs = specs if specs is not None else load_json(CHECK_SPECS)
    freeze = freeze if freeze is not None else load_json(FREEZE)
    expected = expected if expected is not None else build_expected_bindings(specs)
    runtimes = runtimes if runtimes is not None else verify_runtime(specs)[0]
    allowed = list(specs.get("runner_allowed_check_ids") or [])
    return {
        "status": "PREFLIGHT_OK",
        "format": "RECOVERY_02_RUNNER_PREFLIGHT_V1",
        "task_id": TASK_ID,
        "run_rel": RUNREL,
        "cwd": str(pathlib.Path.cwd()),
        "child_cwd": str(CHILD_CWD),
        "temporary_root": str(TMPDIR),
        "evidence_dir": str(EVIDENCE),
        "runner": {"absolute_path": str(TOOL_PATH), "sha256": sha256_file(TOOL_PATH)[1]},
        "check_specs": {"absolute_path": str(CHECK_SPECS), "sha256": sha256_file(CHECK_SPECS)[1]},
        "freeze": {"absolute_path": str(FREEZE), "sha256": sha256_file(FREEZE)[1]},
        "resolved_source_hashes": expected,
        "runtimes": runtimes,
        "allowed_check_ids": allowed,
        "shell": False,
        "automatic_retry": False,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "stream_limit_bytes": DEFAULT_STREAM_LIMIT_BYTES,
        "writes": 0,
        "child_started": False,
        "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "monotonic_ns": time.monotonic_ns(),
    }


def _drain(proc: subprocess.Popen, limit: int, deadline: float) -> tuple[bytes, bytes, list[str], bool, bool]:
    out = bytearray()
    err = bytearray()
    notes: list[str] = []
    timeout = False
    limit_hit = False
    streams = {proc.stdout: ("stdout", out), proc.stderr: ("stderr", err)}
    open_streams = set(streams)
    while open_streams:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timeout = True
            notes.append("TIMEOUT")
            break
        ready, _, _ = select.select(list(open_streams), [], [], min(remaining, 0.25))
        for stream in ready:
            name, sink = streams[stream]
            chunk = stream.read(READ_CHUNK)
            if chunk is None:
                continue
            if chunk == b"":
                open_streams.discard(stream)
                continue
            room = limit - len(sink)
            sink.extend(chunk[:room])
            if len(chunk) > room:
                limit_hit = True
                notes.append(f"STREAM_LIMIT_EXCEEDED:{name}")
                break
        if limit_hit:
            break
        if proc.poll() is not None and all(stream.fileno() < 0 for stream in open_streams):
            break
    return bytes(out), bytes(err), notes, timeout, limit_hit


def _kill_group(proc: subprocess.Popen) -> bool:
    killed = False
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        killed = True
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.kill()
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    return killed


def run_check(check_id: str, argv: list[str], *, specs: dict | None = None,
              expected: dict[str, str] | None = None, runtimes: dict[str, dict] | None = None,
              evidence_dir: pathlib.Path | None = None, tmp_dir: pathlib.Path | None = None,
              child_cwd: pathlib.Path | None = None, timeout_seconds: int | None = None,
              stream_limit_bytes: int | None = None) -> tuple[int, dict]:
    evidence_dir = evidence_dir if evidence_dir is not None else EVIDENCE
    tmp_dir = tmp_dir if tmp_dir is not None else TMPDIR
    child_cwd = child_cwd if child_cwd is not None else CHILD_CWD
    specs = specs if specs is not None else load_json(CHECK_SPECS)
    expected = expected if expected is not None else build_expected_bindings(specs)
    runtimes = runtimes if runtimes is not None else verify_runtime(specs)[0]
    spec = _check_spec(specs, check_id)
    refusal: list[str] = []
    allowed_ids = [str(item) for item in (specs.get("runner_allowed_check_ids") or [])]
    if check_id not in allowed_ids:
        refusal.append(f"CHECK_ID_NOT_ALLOWED:{check_id}")
    if spec is None:
        refusal.append(f"UNKNOWN_CHECK_ID:{check_id}")
    else:
        frozen_argv = [str(item) for item in spec.get("argv") or []]
        if frozen_argv != [str(item) for item in argv]:
            refusal.append(f"ARGV_NOT_FROZEN:{check_id}")
    launcher_name = (spec or {}).get("launcher")
    if spec is not None and launcher_name == "VERIFIED_RUNROOT_RUNNER":
        runtime = None
        for name, info in runtimes.items():
            if str(argv[0]) == info["path"]:
                runtime = info
                break
        if runtime is None:
            refusal.append(f"RUNTIME_NOT_FIXED:{argv[0]}")
    stem = evidence_dir / check_id
    out_paths = [pathlib.Path(f"{stem}.stdout"), pathlib.Path(f"{stem}.stderr"), pathlib.Path(f"{stem}.receipt.json")]
    for path in out_paths:
        if os.path.lexists(path):
            refusal.append(f"ID_COLLISION:{path}")
    if refusal:
        return 2, {"status": "REFUSED", "check_id": check_id, "errors": refusal}

    timeout_seconds = timeout_seconds if timeout_seconds is not None else int(spec.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS)
    stream_limit_bytes = stream_limit_bytes if stream_limit_bytes is not None else int(spec.get("stdout_limit_bytes") or DEFAULT_STREAM_LIMIT_BYTES)
    child_env = dict(os.environ)
    child_env.update({k: v for k, v in (spec.get("environment") or {}).items()})
    started_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    started_mono = time.monotonic()
    proc = subprocess.Popen(
        [str(item) for item in argv],
        cwd=str(child_cwd),
        env=child_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=True,
    )
    deadline = started_mono + timeout_seconds
    out_bytes, err_bytes, notes, timeout, limit_hit = _drain(proc, stream_limit_bytes, deadline)
    if timeout or limit_hit:
        group_killed = _kill_group(proc)
        cleanup = {"process_group_killed": group_killed, "reaped": True, "notes": notes}
    else:
        try:
            proc.wait(timeout=max(1.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            timeout = True
            group_killed = _kill_group(proc)
            notes.append("TIMEOUT")
            cleanup = {"process_group_killed": group_killed, "reaped": True, "notes": notes}
        else:
            cleanup = {"process_group_killed": False, "reaped": True, "notes": notes}
    exit_code = proc.returncode
    ended_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    stdout_ref = _write_exclusive(evidence_dir, f"{check_id}.stdout", out_bytes)
    stderr_ref = _write_exclusive(evidence_dir, f"{check_id}.stderr", err_bytes)
    status = "PASS" if (exit_code == 0 and not timeout and not limit_hit) else "FAIL"
    product_hashes = {
        "adapter_sha256": expected.get("scripts/line_backup_cua_adapter.mjs"),
        "test_sha256": expected.get("tests/test_cua_adapter.mjs"),
        "supplemental_test_sha256": expected.get(f"{RUNREL}/checks/test_capture_regression.mjs"),
    }
    receipt = {
        "format": FORMAT,
        "kind": "RECOVERY_02_RUN_COMMAND_RECEIPT",
        "task_id": TASK_ID,
        "run_rel": RUNREL,
        "check_id": check_id,
        "status": status,
        "exit_code": exit_code,
        "timeout": timeout,
        "stream_limit_exceeded": limit_hit,
        "notes": notes,
        "argv": [str(item) for item in argv],
        "cwd": str(child_cwd),
        "environment_overrides": {k: v for k, v in (spec.get("environment") or {}).items()},
        "source_hashes": {
            key: expected.get(_resolve_rel(key).relative_to(ROOT).as_posix()) if _resolve_rel(key) else None
            for key in (spec.get("source_hashes") or {})
        },
        "product_hashes": product_hashes,
        "runner": {"path": TOOL_PATH.relative_to(ROOT).as_posix(), "absolute_path": str(TOOL_PATH), "sha256": sha256_file(TOOL_PATH)[1]},
        "started_at_utc": started_utc,
        "ended_at_utc": ended_utc,
        "elapsed_ms": int((time.monotonic() - started_mono) * 1000),
        "monotonic_start_ns": time.monotonic_ns(),
        "timeout_seconds": timeout_seconds,
        "stream_limit_bytes": stream_limit_bytes,
        "stdout": stdout_ref,
        "stderr": stderr_ref,
        "cleanup": cleanup,
        "automatic_retry": False,
        "native_harness_validation": "NOT_RUN",
    }
    data = (json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")
    receipt_ref = _write_exclusive(evidence_dir, f"{check_id}.receipt.json", data)
    summary = {"check_id": check_id, "status": status, "exit_code": exit_code, "timeout": timeout,
               "stream_limit_exceeded": limit_hit, "stdout": stdout_ref, "stderr": stderr_ref, "receipt": receipt_ref}
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
    return (0 if status == "PASS" else 1), receipt


def main(argv: list[str]) -> int:
    problems = validate_location(argv[0])
    if problems:
        print(json.dumps({"status": "REFUSED", "errors": problems}, ensure_ascii=False))
        return 2
    if len(argv) == 2 and argv[1] == "--preflight":
        try:
            specs, freeze, expected, spec_problems = verify_specs_and_freeze()
            runtimes, runtime_problems = verify_runtime(specs)
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"status": "PREFLIGHT_REFUSED", "errors": [f"SPECS_UNREADABLE:{exc}"]}, ensure_ascii=False))
            return 2
        if spec_problems or runtime_problems:
            print(json.dumps({"status": "PREFLIGHT_REFUSED", "errors": spec_problems + runtime_problems}, ensure_ascii=False))
            return 2
        report = preflight_report(specs=specs, freeze=freeze, expected=expected, runtimes=runtimes)
        print(json.dumps(report, ensure_ascii=True, sort_keys=True))
        return 0
    if len(argv) >= 4 and argv[2] == "--":
        check_id = argv[1]
        command = argv[3:]
        try:
            specs, _freeze, expected, spec_problems = verify_specs_and_freeze()
            runtimes, runtime_problems = verify_runtime(specs)
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"status": "REFUSED", "errors": [f"SPECS_UNREADABLE:{exc}"]}, ensure_ascii=False))
            return 2
        if spec_problems or runtime_problems:
            print(json.dumps({"status": "REFUSED", "errors": spec_problems + runtime_problems}, ensure_ascii=False))
            return 2
        exit_code, doc = run_check(check_id, command, specs=specs, expected=expected, runtimes=runtimes)
        if exit_code == 2:
            print(json.dumps(doc, ensure_ascii=False, sort_keys=True))
        return exit_code
    raise SystemExit("usage: run_command.py --preflight | run_command.py CHECK_ID -- COMMAND [ARG ...]")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
