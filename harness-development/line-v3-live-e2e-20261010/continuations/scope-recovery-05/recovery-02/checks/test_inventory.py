#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Fixture selftest for tools/inventory.py and checks/compare_inventories.py.

All fixture data is created under RUNROOT/fixtures/selftest-<utc>/ and removed
only after a fully passing run (removal list is printed). The real workspace is
never scanned and the real allowlisted FIFO is never touched. Fixture FIFOs are
used only here.

exit 0 and a JSON summary on stdout = PASS; any failed case = exit 1 and the
fixture tree is kept for inspection.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import stat
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNROOT = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
FIXTURES = RUNROOT / "fixtures"
TOOL_PATH = RUNROOT / "tools" / "inventory.py"
COMPARE_PATH = RUNROOT / "checks" / "compare_inventories.py"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_file(path: pathlib.Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def make_regular(path: str, size: int) -> dict:
    record = {
        "path": path,
        "kind": "REGULAR",
        "mode": 420,
        "dev": 1,
        "ino": 2,
        "nlink": 1,
        "uid": 501,
        "gid": 20,
        "size": size,
        "mtime_ns": 111,
        "ctime_ns": 222,
        "bytes": size,
        "sha256": "a" * 64,
    }
    return record


def make_dir(path: str, entries: list[str], mtime: int = 111) -> dict:
    return {
        "path": path,
        "kind": "DIRECTORY",
        "mode": 493,
        "dev": 1,
        "ino": 3,
        "nlink": 2 + len(entries),
        "uid": 501,
        "gid": 20,
        "size": 64,
        "mtime_ns": mtime,
        "ctime_ns": mtime,
        "entries": sorted(entries),
        "sha256": sha(json.dumps(sorted(entries), ensure_ascii=False).encode("utf-8")),
    }


def make_doc(records: list[dict], *, complete: bool = True, timeout: bool = False, policy_ok: bool = True, mode: str = "test", slot: str = "01") -> dict:
    return {
        "format": "RECOVERY_02_INVENTORY_V1",
        "mode": mode,
        "slot": slot,
        "complete": complete,
        "timeout": timeout,
        "policy": {"ok": policy_ok, "violations": [], "fifo_found": policy_ok, "fifo_observation": {} if policy_ok else None},
        "counts": {"total": len(records)},
        "records": records,
    }


def run_cases(inventory, compare):
    cases = []

    def case(name, fn):
        started = time.time()
        try:
            detail = fn()
            cases.append({"name": name, "ok": True, "detail": detail if detail is not None else {}, "seconds": round(time.time() - started, 3)})
        except Exception as exc:  # noqa: BLE001 - selftest reports any failure
            cases.append({"name": name, "ok": False, "error": f"{type(exc).__name__}:{exc}", "seconds": round(time.time() - started, 3)})

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    fixture_root = FIXTURES / f"selftest-{stamp}-{os.getpid()}"

    def froot(*parts: str) -> pathlib.Path:
        return fixture_root.joinpath(*parts)

    fixture_root.mkdir(parents=True, exist_ok=False)
    deleted = {"attempted": False, "paths": []}

    # ------------------------------------------------------------------ basic
    def basic_tree():
        base = froot("basic")
        f1 = (b"hello\n" * 64)
        top = bytes(range(256))
        write_file(base / "d1" / "f1.txt", f1)
        write_file(base / "d1" / ".hidden", b"h")
        write_file(base / "d1" / "d2" / "deep.bin", b"deep")
        (base / "d1" / "empty").mkdir(parents=True)
        write_file(base / "top.bin", top)
        write_file(base / "repo" / ".git" / "config", b"[core]\n")
        write_file(base / "repo" / "README", b"x")
        os.symlink("d1/f1.txt", base / "link_rel")
        os.symlink("no/such/target", base / "link_dangling")
        os.symlink(str(ROOT), base / "outside_symlink")
        state = inventory.scan_tree(base, fifo_abs=pathlib.Path("/nonexistent-fifo"), allowlist_fifo=False, exclude_top_git=False)
        assert state.errors == [], state.errors
        assert state.policy_violations == [], state.policy_violations
        by = {r["path"]: r for r in state.records}
        expected = {
            "d1", "d1/f1.txt", "d1/.hidden", "d1/d2", "d1/d2/deep.bin", "d1/empty",
            "top.bin", "repo", "repo/.git", "repo/.git/config", "repo/README",
            "link_rel", "link_dangling", "outside_symlink",
        }
        assert set(by) == expected, sorted(set(by) ^ expected)
        assert by["d1/f1.txt"]["sha256"] == sha(f1) and by["d1/f1.txt"]["bytes"] == len(f1)
        assert by["top.bin"]["sha256"] == sha(top)
        assert by["d1/.hidden"]["kind"] == "REGULAR"
        assert by["d1/empty"]["kind"] == "DIRECTORY" and by["d1/empty"]["entries"] == []
        assert by["d1"]["entries"] == sorted(by["d1"]["entries"]), "entries must be sorted"
        assert by["repo/.git"]["kind"] == "DIRECTORY", "nested .git must be included in fixture scans"
        assert by["link_rel"]["kind"] == "SYMLINK" and by["link_rel"]["target"] == "d1/f1.txt"
        assert by["link_rel"]["sha256"] == sha(os.fsencode("d1/f1.txt"))
        assert by["link_dangling"]["kind"] == "SYMLINK"
        assert not any(p.startswith("outside_symlink/") for p in by), "symlink must not be followed"
        assert "content_read" not in by["top.bin"] or by["top.bin"]["content_read"] is not False
        return {"records": len(state.records)}

    case("basic_tree", basic_tree)

    # ------------------------------------------------------------------- fifo
    def fifo_case():
        base = froot("fifo")
        (base / "fifo").mkdir(parents=True)
        fifo_path = base / "fifo" / "f"
        os.mkfifo(fifo_path, 0o644)
        os.symlink("f", base / "fifo" / "link_to_fifo")
        opened = []
        real_open = inventory._open

        def spy_open(name, flags, dir_fd=None, mode=0o777):
            opened.append((name, flags, dir_fd))
            return real_open(name, flags, dir_fd=dir_fd, mode=mode) if dir_fd is not None else real_open(name, flags, mode)

        inventory._open = spy_open
        try:
            state = inventory.scan_tree(base, fifo_abs=fifo_path, allowlist_fifo=True, exclude_top_git=False)
        finally:
            inventory._open = real_open
        assert state.fifo_found is True and state.policy_violations == [], state.policy_violations
        by = {r["path"]: r for r in state.records}
        rec = by["fifo/f"]
        assert rec["kind"] == "FIFO", rec["kind"]
        assert rec["content_read"] is False and rec["content_hash"] is None
        assert "bytes" not in rec and "sha256" not in rec, "FIFO with size 0 must not be treated as empty regular"
        assert rec["size"] == 0 and rec["mode"] == 0o644
        assert by["fifo/link_to_fifo"]["kind"] == "SYMLINK"
        assert not any(entry[0] == "f" for entry in opened), "fixture FIFO must never be opened"
        # without allowlist the same FIFO must block policy, still never opened
        opened.clear()
        inventory._open = spy_open
        try:
            state2 = inventory.scan_tree(base, fifo_abs=fifo_path, allowlist_fifo=False, exclude_top_git=False)
        finally:
            inventory._open = real_open
        assert state2.policy["ok"] is False
        assert any(v["code"] == "UNEXPECTED_SPECIAL_OBJECT" for v in state2.policy_violations), state2.policy_violations
        assert not any(entry[0] == "f" for entry in opened), "unapproved FIFO must never be opened"
        return {"fifo_dev": rec["dev"], "fifo_ino": rec["ino"]}

    case("fifo_lstat_only", fifo_case)

    # -------------------------------------------------------------- unreadable
    def unreadable_case():
        base = froot("unreadable")
        write_file(base / "secret.bin", b"secret")
        write_file(base / "ok.bin", b"fine")
        os.chmod(base / "secret.bin", 0o000)
        try:
            state = inventory.scan_tree(base, fifo_abs=pathlib.Path("/nonexistent-fifo"), allowlist_fifo=False, exclude_top_git=False)
        finally:
            os.chmod(base / "secret.bin", 0o644)
        codes = [e["code"] for e in state.errors]
        assert "UNREADABLE_PATH" in codes, codes
        assert state.complete is False
        by = {r["path"]: r for r in state.records}
        assert "ok.bin" in by, "partial records must be kept"
        assert "secret.bin" not in by or by["secret.bin"]["kind"] != "REGULAR"
        return {"error_codes": codes}

    case("unreadable_partial", unreadable_case)

    # --------------------------------------------------- read mismatch (bytes)
    def read_mismatch_case():
        base = froot("read_mismatch")
        write_file(base / "a.bin", b"0123456789")
        real_read = inventory._read_fd_bytes
        inventory._read_fd_bytes = lambda fd: (0, sha(b""))
        try:
            state = inventory.scan_tree(base, fifo_abs=pathlib.Path("/nonexistent-fifo"), allowlist_fifo=False, exclude_top_git=False)
        finally:
            inventory._read_fd_bytes = real_read
        codes = [e["code"] for e in state.errors]
        assert "FILE_CHANGED_DURING_READ" in codes, codes
        assert state.complete is False
        return {"error_codes": codes}

    case("read_mismatch_partial", read_mismatch_case)

    # ---------------------------------------------------- signature drift
    def sig_drift_case():
        base = froot("sig_drift")
        write_file(base / "b.bin", b"data")
        real_sig = inventory._sig
        counts: dict[int, int] = {}

        def patched(st):
            base_sig = real_sig(st)
            seen = counts.get(st.st_ino, 0) + 1
            counts[st.st_ino] = seen
            if seen == 2 and st.st_size == 4:
                return (base_sig[0], base_sig[1], base_sig[2], base_sig[3], base_sig[4] + 1, base_sig[5])
            return base_sig

        inventory._sig = patched
        try:
            state = inventory.scan_tree(base, fifo_abs=pathlib.Path("/nonexistent-fifo"), allowlist_fifo=False, exclude_top_git=False)
        finally:
            inventory._sig = real_sig
        codes = [e["code"] for e in state.errors]
        assert "FILE_CHANGED_DURING_READ" in codes, codes
        assert state.complete is False
        return {"error_codes": codes}

    case("sig_drift_partial", sig_drift_case)

    # ---------------------------------------------------------------- timeout
    def timeout_case():
        base = froot("timeout")
        for index in range(40):
            write_file(base / f"f{index:02d}.bin", b"x")
        state = inventory.scan_tree(base, fifo_abs=pathlib.Path("/nonexistent-fifo"), allowlist_fifo=False, exclude_top_git=False, deadline_seconds=0.0)
        codes = [e["code"] for e in state.errors]
        assert state.timeout is True and "INVENTORY_TIMEOUT" in codes, codes
        assert state.complete is False
        assert len(state.records) < 40, "timeout must keep partial records only"
        return {"records": len(state.records)}

    case("timeout_partial", timeout_case)

    # ------------------------------------------------------------ normalize
    def normalize_case():
        ok = inventory._norm_rel("a/b/c")
        assert ok == "a/b/c"
        bad = []
        for value in ("", "/a", "a/", "a//b", "a/./b", "a/../b"):
            try:
                inventory._norm_rel(value)
            except ValueError:
                bad.append(value)
        assert len(bad) == 6, bad
        assert inventory._sane_name("x") and not inventory._sane_name("..") and not inventory._sane_name("a/b")
        return {"rejected": bad}

    case("normalization", normalize_case)

    # ------------------------------------------------------------ duplicate
    def duplicate_case():
        state = inventory.ScanState(deadline_seconds=1.0)
        state.add({"path": "a", "kind": "REGULAR"})
        state.add({"path": "a", "kind": "REGULAR"})
        codes = [e["code"] for e in state.errors]
        assert "DUPLICATE_PATH" in codes, codes
        assert len(state.records) == 1
        return {"error_codes": codes}

    case("duplicate_path", duplicate_case)

    # -------------------------------------------------- compare unit tests
    def compare_case():
        rec = make_regular("x.bin", 3)
        base_doc = make_doc([rec])
        assert compare.compare_docs(base_doc, make_doc([dict(rec)]), label="same")["status"] == "PASS"
        blocked = compare.compare_docs(make_doc([rec], complete=False), make_doc([rec]), label="blocked")
        assert blocked["status"] == "BLOCKED", blocked
        extra = dict(rec, path="y.bin")
        added = compare.compare_docs(base_doc, make_doc([dict(rec), extra]), label="added")
        assert added["status"] == "FAIL" and any(f["code"] == "ADDED_NOT_ALLOWED" for f in added["failures"])
        allowed = compare.compare_docs(base_doc, make_doc([dict(rec), extra]), label="allowed", allowed_additions={"y.bin"})
        assert allowed["status"] == "PASS", allowed["failures"]
        removed = compare.compare_docs(make_doc([dict(rec), extra]), base_doc, label="removed")
        assert removed["status"] == "FAIL" and any(f["code"] == "REMOVED_NOT_ALLOWED" for f in removed["failures"])
        changed = compare.compare_docs(base_doc, make_doc([dict(rec, sha256="b" * 64)]), label="changed")
        assert changed["status"] == "FAIL" and any(f["code"] == "FIELD_MISMATCH" for f in changed["failures"])
        # directory entry delta explained by direct-child addition
        d_old = make_dir("d", ["a.bin"], mtime=100)
        d_new = make_dir("d", ["a.bin", "b.bin"], mtime=999)
        explained = compare.compare_docs(
            make_doc([make_regular("d/a.bin", 1), d_old]),
            make_doc([make_regular("d/a.bin", 1), make_regular("d/b.bin", 1), d_new]),
            label="dir-explained",
            allowed_additions={"d/b.bin"},
        )
        assert explained["status"] == "PASS", explained["failures"]
        unexplained = compare.compare_docs(
            make_doc([make_regular("d/a.bin", 1), d_old]),
            make_doc([make_regular("d/a.bin", 1), make_regular("d/b.bin", 1), d_new]),
            label="dir-unexplained",
        )
        assert unexplained["status"] == "FAIL"
        assert any(f["code"] in {"UNEXPLAINED_ENTRY_DELTA", "ADDED_NOT_ALLOWED"} for f in unexplained["failures"])
        # projection: old record carries only a subset of fields
        projectible_old = {"path": "p.bin", "kind": "REGULAR", "mode": 420, "sha256": "a" * 64, "bytes": 3}
        projectible_new = dict(rec, path="p.bin")
        projected = compare.compare_docs(make_doc([projectible_old]), make_doc([projectible_new]), label="projection", projection=True)
        assert projected["status"] == "PASS", projected["failures"]
        drift = compare.compare_docs(make_doc([dict(projectible_old, sha256="c" * 64)]), make_doc([projectible_new]), label="projection-drift", projection=True)
        assert drift["status"] == "FAIL"
        return {"checked": 9}

    case("compare_units", compare_case)

    summary = {
        "kind": "RECOVERY_02_BASELINE_SELFTEST",
        "task_id": "TASK-20261011-line-baseline-recovery-02",
        "fixture_root": str(fixture_root),
        "cases": cases,
        "pass": all(c["ok"] for c in cases),
        "tool_sha256": sha(TOOL_PATH.read_bytes()),
        "compare_sha256": sha(COMPARE_PATH.read_bytes()),
        "python": sys.executable,
        "python_version": sys.version,
        "removed": deleted,
    }
    if summary["pass"]:
        deleted["attempted"] = True
        removed_paths = [str(p.relative_to(ROOT)) for p in sorted(fixture_root.rglob("*"), key=lambda p: len(str(p)), reverse=True)]
        shutil.rmtree(fixture_root)
        assert not fixture_root.exists()
        deleted["paths"] = removed_paths + [str(fixture_root.relative_to(ROOT))]
        summary["removed"] = deleted
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["pass"] else 1


def main() -> int:
    if pathlib.Path.cwd() != ROOT:
        print(json.dumps({"status": "REFUSED", "errors": [f"WRONG_CWD:{pathlib.Path.cwd()}"]}))
        return 2
    if pathlib.Path(os.path.realpath(__file__)) != RUNROOT / "checks/test_inventory.py":
        print(json.dumps({"status": "REFUSED", "errors": [f"WRONG_SCRIPT:{os.path.realpath(__file__)}"]}))
        return 2
    FIXTURES.mkdir(parents=True, exist_ok=True)
    inventory = load_module("recovery02_inventory", TOOL_PATH)
    compare = load_module("recovery02_compare", COMPARE_PATH)
    return run_cases(inventory, compare)


if __name__ == "__main__":
    raise SystemExit(main())
