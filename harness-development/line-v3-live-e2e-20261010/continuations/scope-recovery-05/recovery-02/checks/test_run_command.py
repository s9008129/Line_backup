#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Fixture selftest for checks/run_command.py.

All fixture data is created under RUNROOT/fixtures/selftest-runner-<utc>/ and
removed only after a fully passing run (removal list is printed). The real
RUNROOT/evidence directory is never written: subprocess refusal cases and the
in-process fixture runs use fixture specs/evidence/tmp only, and the real
preflight case is asserted to add zero files. The frozen Node checks are never
launched here.

exit 0 and a JSON summary on stdout = PASS; any failed case = exit 1 and the
fixture tree is kept for inspection.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNROOT = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
FIXTURES = RUNROOT / "fixtures"
RUNCMD = RUNROOT / "checks/run_command.py"
EVIDENCE = RUNROOT / "evidence"
PYTHON = pathlib.Path(sys.executable)

RESULTS: list[dict] = []
FAILURES: list[str] = []


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def case(name: str, fn):
    started = time.monotonic()
    detail = {}
    ok = False
    error = None
    try:
        detail = fn() or {}
        ok = True
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}:{exc}"
    entry = {"name": name, "ok": ok, "elapsed_s": round(time.monotonic() - started, 3)}
    if error:
        entry["error"] = error
        FAILURES.append(name)
    if detail:
        entry.update(detail)
    RESULTS.append(entry)


def evidence_listing() -> list[str]:
    return sorted(entry.name for entry in os.scandir(EVIDENCE))


def fixture_spec(check_id: str, argv: list[str], *, timeout_seconds: int = 20,
                 limit: int = 1048576) -> dict:
    return {
        "kind": "FIXTURE_SPECS",
        "checks": [
            {
                "check_id": check_id,
                "launcher": "FIXTURE",
                "argv": [str(item) for item in argv],
                "requires": [],
                "product_attempt": False,
                "cwd": str(ROOT),
                "environment": {"FIXTURE_MARKER": "1"},
                "timeout_seconds": timeout_seconds,
                "stdout_limit_bytes": limit,
                "stderr_limit_bytes": limit,
                "evidence_stem": None,
                "source_hashes": {},
                "status": "FIXTURE",
                "automatic_retry": False,
            }
        ],
        "executables": [],
        "runner_allowed_check_ids": [check_id],
    }


def main() -> int:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fixture_root = FIXTURES / f"selftest-runner-{stamp}-{os.getpid()}"
    fixture_root.mkdir(parents=True, exist_ok=False)
    fx_evidence = fixture_root / "evidence"
    fx_tmp = fixture_root / "tmp"
    fx_evidence.mkdir()
    fx_tmp.mkdir()
    (fixture_root / "cwd").mkdir()
    run_command = load_module("recovery02_run_command", RUNCMD)

    def preflight_ok():
        before = evidence_listing()
        problems = run_command.validate_location(str(RUNCMD))
        assert not problems, problems
        specs, freeze, expected, spec_problems = run_command.verify_specs_and_freeze()
        assert not spec_problems, spec_problems
        runtimes, runtime_problems = run_command.verify_runtime(specs)
        assert not runtime_problems, runtime_problems
        report = run_command.preflight_report(specs=specs, freeze=freeze, expected=expected, runtimes=runtimes)
        assert report["status"] == "PREFLIGHT_OK", report
        assert report["writes"] == 0 and report["child_started"] is False
        assert evidence_listing() == before, "preflight must add no evidence files"
        assert sorted(report["allowed_check_ids"]) == ["node-adapter-syntax-02", "node-adapter-tests-01"]
        return {"runner_sha256": report["runner"]["sha256"], "allowed": report["allowed_check_ids"]}

    case("preflight_no_writes_ok", preflight_ok)

    def subprocess_refusal(argv: list[str], cwd: pathlib.Path):
        proc = subprocess.run(
            [str(PYTHON), "-B", str(argv[0]), *argv[1:]],
            cwd=str(cwd), capture_output=True, timeout=60, shell=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(fx_tmp), "TMP": str(fx_tmp), "TEMP": str(fx_tmp)},
        )
        text = proc.stdout.decode("utf-8", "replace")
        try:
            doc = json.loads(text)
        except Exception:  # noqa: BLE001
            doc = None
        return proc.returncode, doc, text

    def misplaced_copy_refused():
        copy_dir = fixture_root / "misplaced"
        copy_dir.mkdir()
        copy_path = copy_dir / "run_command.py"
        copy_path.write_bytes(RUNCMD.read_bytes())
        code, doc, text = subprocess_refusal([copy_path, "--preflight"], ROOT)
        assert code == 2, (code, text)
        assert doc and any("WRONG_LOCATION" in err for err in doc.get("errors", [])), doc
        return {"refusal": doc.get("errors")}

    case("misplaced_copy_refused", misplaced_copy_refused)

    def ancestor_symlink_refused():
        link = fixture_root / "linked-checks"
        os.symlink(RUNROOT / "checks", link)
        code, doc, text = subprocess_refusal([link / "run_command.py", "--preflight"], ROOT)
        assert code == 2, (code, text)
        assert doc and any("SYMLINK_ANCESTOR" in err for err in doc.get("errors", [])), doc
        return {"refusal": doc.get("errors")}

    case("ancestor_symlink_refused", ancestor_symlink_refused)

    def unknown_check_id_refused():
        code, doc, text = subprocess_refusal([RUNCMD, "bogus-check-01", "--", "/bin/echo", "hi"], ROOT)
        assert code == 2, (code, text)
        assert doc and any("UNKNOWN_CHECK_ID" in err for err in doc.get("errors", [])), doc
        return {"refusal": doc.get("errors")}

    case("unknown_check_id_refused", unknown_check_id_refused)

    def argv_not_frozen_refused():
        before = evidence_listing()
        code, doc, text = subprocess_refusal([RUNCMD, "node-adapter-syntax-02", "--", "/bin/echo", "hi"], ROOT)
        assert code == 2, (code, text)
        assert doc and any("ARGV_NOT_FROZEN" in err for err in doc.get("errors", [])), doc
        assert evidence_listing() == before, "refusal must not create evidence files"
        return {"refusal": doc.get("errors")}

    case("argv_not_frozen_refused", argv_not_frozen_refused)

    marker = fixture_root / "launched.marker"
    spec = fixture_spec(
        "fixture-existing-id",
        [str(PYTHON), "-B", "-c", f"open({str(marker)!r}, 'w').write('launched')"],
    )
    stem = fx_evidence / "fixture-existing-id"
    pathlib.Path(f"{stem}.receipt.json").write_bytes(b"{}")

    def existing_id_refused():
        exit_code, doc = run_command.run_check(
            "fixture-existing-id", spec["checks"][0]["argv"], specs=spec, expected={},
            runtimes={}, evidence_dir=fx_evidence, tmp_dir=fx_tmp, child_cwd=ROOT,
        )
        assert exit_code == 2, doc
        assert any("ID_COLLISION" in err for err in doc.get("errors", [])), doc
        assert not marker.exists(), "child must not launch when the ID already exists"
        return {"refusal": doc.get("errors")}

    case("existing_id_refused", existing_id_refused)
    pathlib.Path(f"{stem}.receipt.json").unlink()

    ok_spec = fixture_spec(
        "fixture-ok",
        [str(PYTHON), "-B", "-c", "import sys;print('stdout-line');print('stderr-line', file=sys.stderr)"],
    )

    def ok_run_receipt_and_readback():
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code, doc = run_command.run_check(
                "fixture-ok", ok_spec["checks"][0]["argv"], specs=ok_spec, expected={},
                runtimes={}, evidence_dir=fx_evidence, tmp_dir=fx_tmp, child_cwd=ROOT,
            )
        assert exit_code == 0, doc
        assert doc["status"] == "PASS" and doc["exit_code"] == 0 and doc["timeout"] is False
        assert doc["cwd"] == str(ROOT)
        stdout_path = pathlib.Path(doc["stdout"]["absolute_path"])
        stderr_path = pathlib.Path(doc["stderr"]["absolute_path"])
        assert stdout_path.read_bytes() == b"stdout-line\n"
        assert stderr_path.read_bytes() == b"stderr-line\n"
        assert doc["stdout"]["readback_verified"] is True and doc["stderr"]["readback_verified"] is True
        assert doc["stdout"]["sha256"] == sha256_file(stdout_path)
        receipt_path = pathlib.Path(f"{fx_evidence / 'fixture-ok'}.receipt.json")
        assert receipt_path.exists() and json.loads(receipt_path.read_bytes())["status"] == "PASS"
        return {"stdout_sha256": doc["stdout"]["sha256"]}

    case("ok_run_receipt_and_readback", ok_run_receipt_and_readback)

    def second_run_same_id_refused():
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code, doc = run_command.run_check(
                "fixture-ok", ok_spec["checks"][0]["argv"], specs=ok_spec, expected={},
                runtimes={}, evidence_dir=fx_evidence, tmp_dir=fx_tmp, child_cwd=ROOT,
            )
        assert exit_code == 2, doc
        assert any("ID_COLLISION" in err for err in doc.get("errors", [])), doc
        return {"refusal": doc.get("errors")}

    case("second_run_same_id_refused", second_run_same_id_refused)

    exit_spec = fixture_spec("fixture-exit3", [str(PYTHON), "-B", "-c", "import sys;sys.exit(3)"])

    def nonzero_exit_fails():
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code, doc = run_command.run_check(
                "fixture-exit3", exit_spec["checks"][0]["argv"], specs=exit_spec, expected={},
                runtimes={}, evidence_dir=fx_evidence, tmp_dir=fx_tmp, child_cwd=ROOT,
            )
        assert exit_code == 1, doc
        assert doc["status"] == "FAIL" and doc["exit_code"] == 3 and doc["timeout"] is False
        return {"exit_code": doc["exit_code"]}

    case("nonzero_exit_fails", nonzero_exit_fails)

    pid_file = fixture_root / "grandchild.pid"
    timeout_spec = fixture_spec(
        "fixture-timeout",
        [str(PYTHON), "-B", "-c",
         "import subprocess,sys,time\n"
         f"p=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(60)'])\n"
         f"open({str(pid_file)!r},'w').write(str(p.pid))\n"
         "time.sleep(60)\n"],
        timeout_seconds=2,
    )

    def timeout_kills_process_group():
        started = time.monotonic()
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code, doc = run_command.run_check(
                "fixture-timeout", timeout_spec["checks"][0]["argv"], specs=timeout_spec, expected={},
                runtimes={}, evidence_dir=fx_evidence, tmp_dir=fx_tmp, child_cwd=ROOT,
            )
        elapsed = time.monotonic() - started
        assert exit_code == 1, doc
        assert doc["timeout"] is True and doc["status"] == "FAIL", doc
        assert elapsed < 20, elapsed
        assert doc["cleanup"]["process_group_killed"] is True and doc["cleanup"]["reaped"] is True, doc["cleanup"]
        deadline = time.monotonic() + 5
        dead = False
        while time.monotonic() < deadline:
            if not pid_file.exists():
                time.sleep(0.1)
                continue
            pid = int(pid_file.read_text() or "0")
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                dead = True
                break
            time.sleep(0.2)
        assert dead, "grandchild process must be gone after process-group kill"
        return {"elapsed_s": round(elapsed, 3)}

    case("timeout_kills_process_group", timeout_kills_process_group)

    flood_spec = fixture_spec(
        "fixture-stream-limit",
        [str(PYTHON), "-B", "-c", "print('x'*3000000)"],
        limit=100000,
    )

    def stream_limit_enforced():
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code, doc = run_command.run_check(
                "fixture-stream-limit", flood_spec["checks"][0]["argv"], specs=flood_spec, expected={},
                runtimes={}, evidence_dir=fx_evidence, tmp_dir=fx_tmp, child_cwd=ROOT,
            )
        assert exit_code == 1, doc
        assert doc["stream_limit_exceeded"] is True and doc["status"] == "FAIL", doc
        assert doc["stdout"]["bytes"] == 100000, doc["stdout"]
        assert any("STREAM_LIMIT_EXCEEDED" in note for note in doc["notes"]), doc["notes"]
        return {"stdout_bytes": doc["stdout"]["bytes"]}

    case("stream_limit_enforced", stream_limit_enforced)

    cwd_spec = fixture_spec("fixture-cwd", [str(PYTHON), "-B", "-c", "import os;print(os.getcwd())"])

    def caller_cwd_fixed_child_cwd():
        old = pathlib.Path.cwd()
        os.chdir(fixture_root / "cwd")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code, doc = run_command.run_check(
                    "fixture-cwd", cwd_spec["checks"][0]["argv"], specs=cwd_spec, expected={},
                    runtimes={}, evidence_dir=fx_evidence, tmp_dir=fx_tmp, child_cwd=ROOT,
                )
        finally:
            os.chdir(old)
        assert exit_code == 0, doc
        assert pathlib.Path(doc["stdout"]["absolute_path"]).read_bytes() == (str(ROOT) + "\n").encode()
        assert doc["cwd"] == str(ROOT)
        return {"child_cwd": doc["cwd"]}

    case("caller_cwd_fixed_child_cwd", caller_cwd_fixed_child_cwd)

    removed: dict = {"attempted": False, "paths": []}
    passed = not FAILURES
    if passed:
        removed = {"attempted": True, "paths": [str(fixture_root.relative_to(ROOT))]}
        shutil.rmtree(fixture_root)
    summary = {
        "pass": passed,
        "cases": RESULTS,
        "failed": FAILURES,
        "run_command_sha256": sha256_file(RUNCMD),
        "fixture_root": str(fixture_root.relative_to(ROOT)),
        "removed": removed,
        "native_harness_validation": "NOT_RUN",
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
