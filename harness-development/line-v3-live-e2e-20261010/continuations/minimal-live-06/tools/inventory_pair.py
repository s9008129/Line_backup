#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Minimal-live-06 paired, no-follow workspace inventory.

The scan core is imported read-only from recovery-02. Both full scans and the
comparison stay in memory; this process publishes its four exact outputs only
after the pair has been checked. The known FIFO is lstat-only through the
reused scanner. This tool never opens or reads a special file.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import stat
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06"
RUN = ROOT / RUNREL
EVIDENCE = RUN / "evidence" / "inventory"
POLICY = RUN / "output-policy-frozen.json"
SCANNER = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/tools/inventory.py"
FIFO_REL = "evidence/20260916-auto-verification/attempt-01/archive-phase1/private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo"
FIFO = ROOT / FIFO_REL
DEADLINE_SECONDS = 1200
CHUNK = 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_scanner():
    spec = importlib.util.spec_from_file_location("recovery02_inventory_readonly", SCANNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("SCANNER_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def secure_path(path: pathlib.Path) -> None:
    if not path.is_absolute() or not path.resolve().is_relative_to(ROOT):
        raise RuntimeError(f"PATH_OUTSIDE_ROOT:{path}")
    current = pathlib.Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        st = current.lstat()
        if stat.S_ISLNK(st.st_mode):
            raise RuntimeError(f"SYMLINK_ANCESTOR:{current}")


def write_exclusive(path: pathlib.Path, data: bytes) -> dict:
    secure_path(path.parent)
    if not path.parent.is_dir():
        raise RuntimeError(f"PARENT_MISSING:{path.parent}")
    dfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dfd)
        try:
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("SHORT_WRITE")
                view = view[written:]
            os.fsync(fd)
            before = os.fstat(fd)
        finally:
            os.close(fd)
        rfd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dfd)
        try:
            chunks = []
            while True:
                part = os.read(rfd, CHUNK)
                if not part:
                    break
                chunks.append(part)
            after = os.fstat(rfd)
        finally:
            os.close(rfd)
    finally:
        os.close(dfd)
    actual = b"".join(chunks)
    if actual != data or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        raise RuntimeError(f"READBACK_OR_IDENTITY_MISMATCH:{path}")
    return {"path": path.relative_to(ROOT).as_posix(), "absolute_path": str(path), "bytes": len(data), "sha256": sha(data), "exclusive": True, "readback_verified": True}


def scan_once(scanner, slot: int) -> dict:
    start_utc = utc()
    start_mono = time.monotonic()
    state = scanner.scan_tree(ROOT, fifo_abs=FIFO, allowlist_fifo=True, exclude_top_git=True, deadline_seconds=DEADLINE_SECONDS)
    end_mono = time.monotonic()
    return {
        "format": "MINIMAL_LIVE_06_INVENTORY_V1",
        "slot": slot,
        "root": str(ROOT),
        "started_at_utc": start_utc,
        "ended_at_utc": utc(),
        "elapsed_ms": int((end_mono - start_mono) * 1000),
        "complete": state.complete,
        "timeout": state.timeout,
        "errors": state.errors,
        "policy": state.policy,
        "counts": {"total": len(state.records), "directories": sum(r.get("kind") == "DIRECTORY" for r in state.records), "regular": sum(r.get("kind") == "REGULAR" for r in state.records), "symlinks": sum(r.get("kind") == "SYMLINK" for r in state.records), "fifos": sum(r.get("kind") == "FIFO" for r in state.records)},
        "records": state.records,
    }


def compare_pair(first: dict, second: dict) -> dict:
    if not first.get("complete") or not second.get("complete"):
        return {"verdict": "BLOCKED", "reason": "PARTIAL_OR_TIMED_OUT_SCAN", "added": [], "removed": [], "changed": []}
    if not (first.get("policy", {}).get("ok") and second.get("policy", {}).get("ok")):
        return {"verdict": "BLOCKED", "reason": "SPECIAL_OBJECT_OR_FIFO_POLICY", "added": [], "removed": [], "changed": []}
    a = {r["path"]: r for r in first["records"]}
    b = {r["path"]: r for r in second["records"]}
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    changed = sorted(p for p in (set(a) & set(b)) if a[p] != b[p])
    verdict = "PASS" if not added and not removed and not changed else "BLOCKED"
    return {"verdict": verdict, "reason": "IDENTICAL_COMPLETE_PAIR" if verdict == "PASS" else "WORKSPACE_CHANGED_DURING_PAIR", "added": added, "removed": removed, "changed": changed, "counts": {"added": len(added), "removed": len(removed), "changed": len(changed)}}


def compare_baseline_to_pair(baseline: dict, first: dict, second: dict, policy: dict) -> dict:
    pair = compare_pair(first, second)
    if pair["verdict"] != "PASS":
        return {**pair, "baseline_comparison": "BLOCKED"}
    base = {r["path"]: r for r in baseline.get("records", [])}
    now = {r["path"]: r for r in second["records"]}
    added = sorted(set(now) - set(base))
    removed = sorted(set(base) - set(now))
    changed = sorted(p for p in set(base) & set(now) if base[p] != now[p])
    allowed_rel = set(policy.get("fixed_files", []))
    allowed = {f"{RUNREL}/{p}" for p in allowed_rel}
    allowed.update(policy.get("dynamic_registered_paths", []))
    unexplained_added = sorted(p for p in added if p not in allowed)
    verdict = "PASS" if not removed and not changed and not unexplained_added else "BLOCKED"
    return {"verdict": verdict, "reason": "EXACT_POLICY_DELTA" if verdict == "PASS" else "PRESERVATION_DELTA_REQUIRES_REVIEW", "added": added, "removed": removed, "changed": changed, "unexplained_added": unexplained_added, "counts": {"added": len(added), "removed": len(removed), "changed": len(changed)}}


def expected_paths(mode: str) -> list[pathlib.Path]:
    stem = "baseline" if mode == "baseline" else "preservation"
    return [EVIDENCE / f"{stem}-scan-01.json", EVIDENCE / f"{stem}-scan-02.json", EVIDENCE / f"{stem}-compare.json", EVIDENCE / f"{stem}-receipt.json"]


def publish_pair(mode: str, first: dict, second: dict, comparison: dict, scanner_hash: str) -> dict:
    now = utc()
    paths = expected_paths(mode)
    docs = [first, second, comparison]
    refs = []
    for path, doc in zip(paths[:3], docs, strict=True):
        raw = (json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        refs.append(write_exclusive(path, raw))
    receipt = {
        "format": "MINIMAL_LIVE_06_INVENTORY_PAIR_RECEIPT_V1", "task_id": "TASK-20261010-line-v3-live-e2e", "run_rel": RUNREL,
        "mode": mode, "verdict": comparison.get("verdict", "BLOCKED"), "created_at_utc": now,
        "scanner_source": {"path": str(SCANNER), "sha256": scanner_hash}, "fifo_policy": {"path": FIFO_REL, "content_read": False, "content_hash": None},
        "scans": refs[:2], "comparison": refs[2], "outputs": refs, "native_harness_validation": "NOT_RUN"
    }
    receipt_raw = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    refs.append(write_exclusive(paths[3], receipt_raw))
    return {**receipt, "receipt_ref": refs[3]}


def main(argv: list[str]) -> int:
    if pathlib.Path.cwd() != ROOT or len(argv) != 2 or argv[1] not in ("baseline", "preservation"):
        print(json.dumps({"status": "REFUSED", "errors": ["WRONG_CWD_OR_ARGUMENTS"]}))
        return 2
    invoked = pathlib.Path(os.path.realpath(argv[0]))
    if invoked != RUN / "tools" / "inventory_pair.py":
        print(json.dumps({"status": "REFUSED", "errors": [f"WRONG_SCRIPT:{invoked}"]}))
        return 2
    mode = argv[1]
    paths = expected_paths(mode)
    if any(os.path.lexists(p) for p in paths):
        print(json.dumps({"status": "REFUSED", "errors": ["OUTPUT_COLLISION"]}))
        return 2
    policy = json.loads(POLICY.read_bytes())
    scanner_hash = hashlib.sha256(SCANNER.read_bytes()).hexdigest()
    scanner = load_scanner()
    # No workspace invocation/stream/output is published between scan 1 and 2.
    first = scan_once(scanner, 1)
    second = scan_once(scanner, 2)
    if mode == "baseline":
        comparison = compare_pair(first, second)
    else:
        baseline_path = EVIDENCE / "baseline-scan-01.json"
        if not baseline_path.is_file() or baseline_path.is_symlink():
            comparison = {"verdict": "BLOCKED", "reason": "BASELINE_MISSING", "added": [], "removed": [], "changed": []}
        else:
            baseline = json.loads(baseline_path.read_bytes())
            comparison = compare_baseline_to_pair(baseline, first, second, policy)
    receipt = publish_pair(mode, first, second, comparison, scanner_hash)
    print(json.dumps({"status": receipt["verdict"], "mode": mode, "counts": second["counts"], "comparison": receipt["comparison"], "receipt": receipt["receipt_ref"]}, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
