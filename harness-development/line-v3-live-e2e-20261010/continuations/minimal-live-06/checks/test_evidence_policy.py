#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""E01 one-shot fixture check for paired scan and output publication rules."""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import socket
import stat
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06"
RUN = ROOT / RUNREL
FIX = RUN / "tmp" / "evidence-policy-selftest"
SCAN_PATH = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/tools/inventory.py"
PAIR_PATH = RUN / "tools" / "inventory_pair.py"
CASES = []
FAILURES = []


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def case(name, fn):
    start = time.monotonic()
    try:
        detail = fn() or {}
        CASES.append({"name": name, "status": "PASS", "elapsed_ms": int((time.monotonic()-start)*1000), "detail": detail})
    except Exception as exc:  # preserve exact failure as a check finding
        FAILURES.append(name)
        CASES.append({"name": name, "status": "FAIL", "elapsed_ms": int((time.monotonic()-start)*1000), "error": f"{type(exc).__name__}:{exc}"})


def records(path="root/file", digest="a", mtime=10):
    return [{"path": path, "kind": "REGULAR", "bytes": 3, "sha256": digest, "mtime_ns": mtime}]


def main():
    if pathlib.Path.cwd() != ROOT or not FIX.is_dir() or FIX.is_symlink():
        print(json.dumps({"status":"FAIL","reason":"FIXED_ROOT_OR_FIXTURE_ROOT_INVALID"}))
        return 1
    scanner = load("r06_inventory_scanner", SCAN_PATH)
    pair = load("r06_inventory_pair", PAIR_PATH)
    fixture = FIX / f"e01-{os.getpid()}"
    fixture.mkdir(mode=0o700, exist_ok=False)
    root_stat = fixture.lstat()

    def stable_pair_stays_in_memory():
        published=[]
        scans=0
        def scan_stub(_scanner, slot):
            nonlocal scans
            scans += 1
            assert published == [], "publication happened before both scans completed"
            return {"slot":slot,"complete":True,"timeout":False,"errors":[],"policy":{"ok":True},"records":records()}
        first=scan_stub(scanner,1)
        second=scan_stub(scanner,2)
        comparison=pair.compare_pair(first,second)
        published.append("after-compare")
        assert scans==2 and comparison["verdict"]=="PASS"
        return {"scans":scans,"verdict":comparison["verdict"]}

    case("two_scans_then_compare_before_publication", stable_pair_stays_in_memory)

    def partial_never_becomes_empty_baseline():
        incomplete={"complete":False,"timeout":True,"policy":{"ok":False},"records":[]}
        complete={"complete":True,"timeout":False,"policy":{"ok":True},"records":records()}
        result=pair.compare_pair(incomplete,complete)
        assert result["verdict"]=="BLOCKED" and result["reason"]=="PARTIAL_OR_TIMED_OUT_SCAN"
        return result

    case("partial_scan_is_blocked_not_missing_paths", partial_never_becomes_empty_baseline)

    def changed_pair_is_blocked():
        result=pair.compare_pair({"complete":True,"policy":{"ok":True},"records":records()}, {"complete":True,"policy":{"ok":True},"records":records(digest="b")})
        assert result["verdict"]=="BLOCKED" and result["counts"]["changed"]==1
        return result["counts"]

    case("race_or_content_change_blocks_pair", changed_pair_is_blocked)

    def directory_or_record_metadata_is_compared():
        a={"complete":True,"policy":{"ok":True},"records":[{"path":"d","kind":"DIRECTORY","entries":["x"],"mtime_ns":1}]}
        b={"complete":True,"policy":{"ok":True},"records":[{"path":"d","kind":"DIRECTORY","entries":["x"],"mtime_ns":2}]}
        result=pair.compare_pair(a,b)
        assert result["verdict"]=="BLOCKED" and result["changed"]==["d"]
        return {"changed":result["changed"]}

    case("directory_metadata_delta_is_not_ignored", directory_or_record_metadata_is_compared)

    def fifo_is_only_lstat():
        tree=fixture/"fifo-tree"; tree.mkdir()
        fifo=tree/"known.fifo"; os.mkfifo(fifo,0o600)
        opened=[]; original=scanner._open
        def spy(name, flags, dir_fd=None, mode=0o777):
            if pathlib.Path(str(name)).name=="known.fifo": opened.append(str(name))
            return original(name,flags,dir_fd=dir_fd,mode=mode)
        scanner._open=spy
        try:
            state=scanner.scan_tree(tree,fifo_abs=fifo,allowlist_fifo=True,exclude_top_git=False)
        finally:
            scanner._open=original
        found=[r for r in state.records if r["path"]=="known.fifo"]
        assert not opened and len(found)==1 and found[0]["kind"]=="FIFO"
        assert found[0]["content_read"] is False and found[0]["content_hash"] is None
        return {"opened_fifo":False,"kind":found[0]["kind"]}

    case("known_fifo_is_lstat_only", fifo_is_only_lstat)

    def unknown_special_blocks_without_open():
        tree=fixture/"special-tree"; tree.mkdir()
        sock=socket.socket(socket.AF_UNIX); path=tree/"unknown.sock"; sock.bind(str(path))
        try:
            state=scanner.scan_tree(tree,fifo_abs=fixture/"not-present.fifo",allowlist_fifo=False,exclude_top_git=False)
        finally:
            sock.close()
        assert any(v["code"]=="UNEXPECTED_SPECIAL_OBJECT" for v in state.policy_violations)
        return {"violation_codes":sorted(v["code"] for v in state.policy_violations)}

    case("unknown_special_object_is_metadata_only_blocker", unknown_special_blocks_without_open)

    def exclusive_publication_and_collision():
        path=fixture/"output.json"; payload=b"{\"ok\":true}\n"
        first=pair.write_exclusive(path,payload)
        assert path.read_bytes()==payload and first["readback_verified"]
        try:
            pair.write_exclusive(path,b"replacement")
        except FileExistsError:
            pass
        else:
            raise AssertionError("existing output was overwritten")
        assert path.read_bytes()==payload
        return {"sha256":first["sha256"],"collision_preserved":True}

    case("exclusive_output_readback_and_collision_preservation", exclusive_publication_and_collision)

    def symlink_parent_is_rejected():
        target=fixture/"target"; target.mkdir()
        link=fixture/"linked-parent"; os.symlink(target,link)
        try:
            pair.write_exclusive(link/"x.json",b"x")
        except (RuntimeError,OSError):
            pass
        else:
            raise AssertionError("symlink parent accepted")
        assert not (target/"x.json").exists()
        return {"target_unchanged":True}

    case("symlink_output_parent_refused", symlink_parent_is_rejected)

    def planned_and_observed_are_separate():
        policy=json.loads((RUN/"output-policy-frozen.json").read_bytes())
        assert "fixed_files" in policy and "dynamic_artifacts" in policy
        assert policy.get("dynamic_registered_paths") is None
        return {"fixed_paths":len(policy["fixed_files"]),"dynamic_registration_required":policy["dynamic_artifacts"]["registration_before_write"]}

    case("fixed_policy_and_dynamic_registration_are_distinct", planned_and_observed_are_separate)

    if not FAILURES:
        st=fixture.lstat()
        if (st.st_dev,st.st_ino)!=(root_stat.st_dev,root_stat.st_ino) or stat.S_ISLNK(st.st_mode):
            print(json.dumps({"status":"FAIL","reason":"FIXTURE_IDENTITY_CHANGED","cases":CASES},ensure_ascii=False))
            return 1
        shutil.rmtree(fixture)
    result={"format":"E01_EVIDENCE_POLICY_SELFTEST_V1","status":"PASS" if not FAILURES else "FAIL","case_count":len(CASES),"passed":len(CASES)-len(FAILURES),"failed":FAILURES,"cases":CASES,"fixture_retained":bool(FAILURES)}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0 if not FAILURES else 1


if __name__=="__main__":
    raise SystemExit(main())
