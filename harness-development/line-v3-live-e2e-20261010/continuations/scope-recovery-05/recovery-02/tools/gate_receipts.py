#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Recovery-02 gate receipts (fixed inputs, exclusive outputs).

Subcommands and outputs (RUNROOT/evidence):
  g-baseline    -> g-baseline-recovery-02.json
  g-runner      -> g-runner.json
  g-adapter     -> g-adapter-offline.json
  g-preservation-> preservation-recovery-02.json

Every subcommand re-reads the frozen artifacts, verifies them against the
recorded expectations, runs two independent read-only git observations, and
emits one exclusive JSON receipt with per-check results. PASS requires every
check to hold; otherwise the receipt records FAIL and exits 1. A receipt is
never rewritten (ID collision refuses before any side effect).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
RUNROOT = ROOT / RUNREL
EVIDENCE = RUNROOT / "evidence"
CON = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations"

FORMAT = "RECOVERY_02_GATE_RECEIPT_V1"
TASK_ID = "TASK-20261011-line-baseline-recovery-02"
TOOL_REL = f"{RUNREL}/tools/gate_receipts.py"
DRY_RUN = False

# frozen identity expectations (bootstrap anchor + check-specs + prior receipts)
EXP = {
    "head": "6dbd45679ebf54a2c27faf1c8212b475c4b87f7a",
    "branch": "v43-ab/codex-rev28",
    "index_sha256": "13fe8bd0c329367fbbc6a24439a0cf27635c4e30c6193c17b1b940980351cb83",
    "index_bytes": 5080170,
    "python_sha256": "34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804",
    "node_sha256": "1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040",
    "adapter_sha256": "bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2",
    "test_sha256": "0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd",
    "state_sha256": "455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6",
    "config_sha256": "5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362",
    "ledger_sha256": "92bab0cf122871b42f3db62af956289b62fbf4e279219766a8850b61f20e135f",
    "plan_sha256": "6604529c8e9bf06aa59eeb4a0c92358a0b0e7218335d6cd568e8cd4d96bb71bc",
    "handoff_md_sha256": "fa076f677c547abe690f6b0be5d1d996c85110bc89cd5634c4f023022a72c3c5",
    "contract_sha256": "057145c121290465b8c4970ed85f30ad860be91013336c301f46ea77c1c6f45a",
    "prewrite_v2_sha256": "4e067bac795173164d11361029c09d4f4a17890d07f3c90cbfbc2428c45f96ce",
    "prewrite_v1_bytes": 41083592,
    "historic_sha256": "b115df6ea55e3a985e98651018e742769b02e6f7854989e68f8d7214680832f2",
    "historic_status_sha256": "67f7855774654f9f32f635fba5dbc80262b1e72fc950d32df00360a39fa40f04",
    "fifo_ino": 124270681,
    "fifo_mode": 0o644,
    "fifo_size": 0,
    "backup_rel_prefix": "backups/",
    "backup_regular_count": 239,
}
INCIDENTS = {
    f"{CON}/evidence/node-adapter-syntax-01.invocation.json": ("e6af579520a315edb79877c4fb7fb6ecab8066cd9f1c4c9fccd396d296bc9e3e", 303),
    f"{CON}/evidence/node-adapter-syntax-01.receipt.json": ("e1d16b370f6f7c9d7d6275e8afd21fe77946dececef290ebc64a740914637719", 678),
    f"{CON}/evidence/node-adapter-syntax-01.stdout": ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 0),
    f"{CON}/evidence/node-adapter-syntax-01.stderr": ("8948d951d254f345d8f1ce65686618a314622897641a6a037058ed782bff1fa4", 318),
}
OLD_FAIL = {
    f"{CON}/scope-recovery-05/evidence/g-baseline.json": ("b8837c5dc8aadccf46e24c25d768ed57fa4dde7e7644e5938448b90e67ef464d", 142531),
    f"{CON}/scope-recovery-05/evidence/g-baseline-failure-detail.json": ("c0ce0019b68df53f72e2b0e6ab2c0e0ac151df2c3dd8e6619c7289ed38a6a005", 1680),
}
PRODUCT = {
    "adapter": f"{ROOT}/scripts/line_backup_cua_adapter.mjs",
    "test": f"{ROOT}/tests/test_cua_adapter.mjs",
    "state": f"{ROOT}/state/backup_state.json",
    "config": f"{ROOT}/config/line_backup_config.json",
    "ledger": f"{ROOT}/harness-development/line-v3-live-e2e-20261010/gui-ledger.json",
    "python": "/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13",
    "node": "/opt/homebrew/Cellar/node/26.7.0/bin/node",
}
PYTHON = PRODUCT["python"]
OUTPUTS = {
    "g-baseline": EVIDENCE / "g-baseline-recovery-02.json",
    "g-runner": EVIDENCE / "g-runner.json",
    "g-adapter": EVIDENCE / "g-adapter-offline.json",
    "g-preservation": EVIDENCE / "preservation-recovery-02.json",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> tuple[int, str]:
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


def ref_of(path) -> dict:
    path = pathlib.Path(path)
    size, digest = sha256_file(path)
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = None
    return {"path": rel, "absolute_path": str(path), "bytes": size, "sha256": digest}


def load_json(path):
    return json.loads(pathlib.Path(path).read_bytes())


def write_exclusive(path: pathlib.Path, data: bytes) -> dict:
    dir_fd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        wfd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(wfd, view):]
            os.fsync(wfd)
        finally:
            os.close(wfd)
        rfd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
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
        raise RuntimeError(f"WRITE_READBACK_MISMATCH:{path}")
    return {"path": path.relative_to(ROOT).as_posix(), "absolute_path": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def git_observation() -> dict:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["LC_ALL"] = "C"

    def run(*args: str) -> bytes:
        proc = subprocess.run(["git", *args], cwd=str(ROOT), env=env, capture_output=True, timeout=60, shell=False)
        if proc.returncode != 0:
            raise RuntimeError(f"GIT_FAILED:{args}:{proc.returncode}:{proc.stderr[:200]!r}")
        return proc.stdout

    status_z = run("status", "--porcelain=v1", "-z", "--untracked-files=all")
    return {
        "head": run("rev-parse", "HEAD").decode().strip(),
        "branch": run("branch", "--show-current").decode().strip(),
        "staged": run("diff", "--cached", "--name-only").decode(),
        "status_z_sha256": sha256_bytes(status_z),
        "status_z_bytes": len(status_z),
        "ls_files_stage_sha256": sha256_bytes(run("ls-files", "--stage")),
        "index_sha256": sha256_file(ROOT / ".git/index")[1],
        "index_bytes": sha256_file(ROOT / ".git/index")[0],
    }


class Receipt:
    def __init__(self, gate_id: str):
        self.gate_id = gate_id
        self.checks: list[dict] = []
        self.refs: dict = {}

    def check(self, name: str, ok: bool, **detail) -> bool:
        entry = {"name": name, "ok": bool(ok)}
        entry.update({k: v for k, v in detail.items() if v is not None})
        self.checks.append(entry)
        return bool(ok)

    def expect_ref(self, name: str, path, expected_sha: str, expected_bytes=None) -> bool:
        got = ref_of(path)
        self.refs[name] = got
        ok = got["sha256"] == expected_sha
        if expected_bytes is not None:
            ok = ok and got["bytes"] == expected_bytes
        return self.check(f"{name}_hash", ok, expected_sha256=expected_sha, actual_sha256=got["sha256"], bytes=got["bytes"])

    @property
    def failures(self) -> list[str]:
        return [c["name"] for c in self.checks if not c["ok"]]

    def emit(self) -> int:
        status = "PASS" if not self.failures else "FAIL"
        doc = {
            "format": FORMAT,
            "kind": "RECOVERY_02_GATE_RECEIPT",
            "task_id": TASK_ID,
            "gate_id": self.gate_id,
            "status": status,
            "failures": self.failures,
            "checks": self.checks,
            "refs": self.refs,
            "tool": {"path": TOOL_REL, "sha256": sha256_file(ROOT / TOOL_REL)[1]},
            "native_harness_validation": "NOT_RUN",
            "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "created_monotonic_ns": time.monotonic_ns(),
        }
        data = (json.dumps(doc, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")
        out = OUTPUTS[self.gate_id]
        if DRY_RUN:
            print(json.dumps({"gate_id": self.gate_id, "status": status, "dry_run": True, "checks": len(self.checks), "failures": self.failures, "planned_output": str(out)}, ensure_ascii=True, sort_keys=True))
            return 0 if status == "PASS" else 1
        if os.path.lexists(out):
            print(json.dumps({"status": "REFUSED", "errors": [f"ID_COLLISION:{out}"]}))
            return 2
        ref = write_exclusive(out, data)
        print(json.dumps({"gate_id": self.gate_id, "status": status, "checks": len(self.checks), "failures": self.failures, "output": ref}, ensure_ascii=True, sort_keys=True))
        return 0 if status == "PASS" else 1


def inventory_summary(path, *, expect_tool_sha: str | None) -> tuple[dict, dict, dict]:
    ref = ref_of(path)
    doc = load_json(path)
    policy = doc.get("policy") or {}
    summary = {
        "complete": doc.get("complete"),
        "timeout": doc.get("timeout"),
        "errors": len(doc.get("errors") or []),
        "policy_ok": policy.get("ok"),
        "policy_violations": len(policy.get("violations") or []),
        "fifo_found": policy.get("fifo_found"),
        "fifo_observation": policy.get("fifo_observation"),
        "counts": doc.get("counts"),
        "tool": doc.get("tool"),
        "started_at_utc": doc.get("started_at_utc"),
        "ended_at_utc": doc.get("ended_at_utc"),
        "elapsed_ms": doc.get("elapsed_ms"),
    }
    records = doc.get("records") or []
    backups = [r for r in records if str(r.get("path", "")).startswith(EXP["backup_rel_prefix"]) and r.get("kind") == "REGULAR"]
    fifo_records = [r for r in records if r.get("kind") == "FIFO"]
    specials = [r for r in records if r.get("kind") == "OTHER_SPECIAL"]
    extra = {
        "backup_records": len(backups),
        "backup_all_regular_verified": all(r.get("kind") == "REGULAR" and r.get("read_verified") is True and len(str(r.get("sha256", ""))) == 64 for r in backups),
        "backup_total_files": sum(1 for r in backups if r.get("kind") == "REGULAR"),
        "fifo_record_count": len(fifo_records),
        "fifo_content_read": any(r.get("content_read") for r in fifo_records),
        "other_special_count": len(specials),
        "total_records": len(records),
    }
    if expect_tool_sha is not None:
        summary["tool_sha_matches"] = (doc.get("tool") or {}).get("sha256") == expect_tool_sha
    del doc
    return ref, summary, extra


def check_inventory(receipt: Receipt, name: str, path, *, expect_tool_sha: str | None, expect_fifo: bool = True) -> dict:
    ref, summary, extra = inventory_summary(path, expect_tool_sha=expect_tool_sha)
    receipt.refs[name] = ref
    ok = (
        summary["complete"] is True
        and summary["timeout"] is False
        and summary["errors"] == 0
        and summary["policy_ok"] is True
        and summary["policy_violations"] == 0
        and extra["other_special_count"] == 0
        and extra["total_records"] > 100000
        and (expect_tool_sha is None or summary.get("tool_sha_matches") is True)
    )
    if expect_fifo:
        fifo = summary["fifo_observation"] or {}
        ok = ok and summary["fifo_found"] is True and extra["fifo_record_count"] == 1 and extra["fifo_content_read"] is False
        ok = ok and fifo.get("ino") == EXP["fifo_ino"] and fifo.get("mode") == EXP["fifo_mode"] and fifo.get("size") == EXP["fifo_size"]
    receipt.check(f"{name}_usable", ok, detail=summary, extra=extra)
    return summary


def host_receipt_ok(receipt: Receipt, check_id: str, *, expect_empty_stdout: bool = False) -> dict | None:
    stem = EVIDENCE / check_id
    receipt_path = pathlib.Path(f"{stem}.receipt.json")
    if not receipt_path.exists():
        receipt.check(f"{check_id}_receipt_present", False, detail=f"missing {receipt_path}")
        return None
    got = load_json(receipt_path)
    receipt.refs[f"{check_id}.receipt"] = ref_of(receipt_path)
    stdout_ref = ref_of(f"{stem}.stdout")
    stderr_ref = ref_of(f"{stem}.stderr")
    receipt.refs[f"{check_id}.stdout"] = stdout_ref
    receipt.refs[f"{check_id}.stderr"] = stderr_ref
    exit_ok = got.get("exit_code") == 0 and got.get("timeout") is not True
    stdout_ok = not expect_empty_stdout or stdout_ref["bytes"] == 0
    stderr_ok = stderr_ref["bytes"] == 0
    receipt.check(f"{check_id}_exit", exit_ok, detail=got.get("exit_code"), stdout_bytes=stdout_ref["bytes"], stderr_bytes=stderr_ref["bytes"])
    receipt.check(f"{check_id}_streams", stdout_ok and stderr_ok)
    return got


def host_json_stdout(check_id: str) -> dict | None:
    stem = EVIDENCE / check_id
    try:
        return json.loads(pathlib.Path(f"{stem}.stdout").read_bytes())
    except Exception:
        return None


def g_baseline() -> int:
    receipt = Receipt("g-baseline")
    receipt.expect_ref("plan", RUNROOT / "plan.md", EXP["plan_sha256"])
    receipt.expect_ref("handoff_md", RUNROOT / "handoff.md", EXP["handoff_md_sha256"])
    receipt.expect_ref("plan_contract", RUNROOT / "plan-contract.json", EXP["contract_sha256"], 2811)
    receipt.expect_ref("handoff_json", RUNROOT / "handoff.json", EXP["contract_sha256"], 2811)
    receipt.expect_ref("bootstrap_v2", EVIDENCE / "bootstrap-prewrite-runroot-v2.json", EXP["prewrite_v2_sha256"])
    receipt.expect_ref("historic_manifest", CON / "scope-recovery-05/.local/preexisting-files.json", EXP["historic_sha256"])
    receipt.expect_ref("historic_status", CON / "scope-recovery-05/.local/preexisting-status.z", EXP["historic_status_sha256"])
    for path, (sha, size) in {**INCIDENTS, **OLD_FAIL}.items():
        receipt.expect_ref("incident_" + pathlib.Path(path).name, path, sha, size)

    tool_sha = sha256_file(RUNROOT / "tools/inventory.py")[1]
    compare_sha = sha256_file(RUNROOT / "checks/compare_inventories.py")[1]
    selftest = host_receipt_ok(receipt, "baseline-selftest-02")
    stdout_doc = host_json_stdout("baseline-selftest-02")
    if stdout_doc is not None:
        cases = stdout_doc.get("cases") or []
        receipt.check(
            "selftest_pass",
            stdout_doc.get("pass") is True and len(cases) == 9 and all(c.get("ok") for c in cases),
            cases=len(cases), failed=[c.get("name") for c in cases if not c.get("ok")],
        )
        receipt.check("selftest_tool_binding", stdout_doc.get("tool_sha256") == tool_sha and stdout_doc.get("compare_sha256") == compare_sha,
                      tool_sha256=stdout_doc.get("tool_sha256"), compare_sha256=stdout_doc.get("compare_sha256"))
        receipt.check("selftest_cleanup", (stdout_doc.get("removed") or {}).get("attempted") is True)
    else:
        receipt.check("selftest_pass", False, detail="stdout not JSON")

    check_inventory(receipt, "inventory-baseline-01", EVIDENCE / "inventory-baseline-01.json", expect_tool_sha=tool_sha)
    check_inventory(receipt, "inventory-baseline-02", EVIDENCE / "inventory-baseline-02.json", expect_tool_sha=tool_sha)
    for mode in ("baseline-consistency", "bootstrap-delta", "historical"):
        path = EVIDENCE / f"compare-{mode}.json"
        if not path.exists():
            receipt.check(f"compare-{mode}", False, detail="missing")
            continue
        doc = load_json(path)
        receipt.refs[f"compare-{mode}"] = ref_of(path)
        receipt.check(f"compare-{mode}", doc.get("status") == "PASS",
                      failures=len(doc.get("failures") or []), blocked_reasons=len(doc.get("blocked_reasons") or []),
                      note=doc.get("note"))

    obs1 = git_observation()
    obs2 = git_observation()
    receipt.refs["git_observation_1"] = obs1
    receipt.refs["git_observation_2"] = obs2
    receipt.check("git_two_observations_equal", obs1 == obs2)
    receipt.check("git_head", obs1["head"] == EXP["head"], actual=obs1["head"])
    receipt.check("git_branch", obs1["branch"] == EXP["branch"], actual=obs1["branch"])
    receipt.check("git_staged_empty", obs1["staged"] == "", actual_bytes=len(obs1["staged"]))
    receipt.check("git_index", obs1["index_sha256"] == EXP["index_sha256"] and obs1["index_bytes"] == EXP["index_bytes"],
                  actual=obs1["index_sha256"], bytes=obs1["index_bytes"])

    receipt.expect_ref("adapter", PRODUCT["adapter"], EXP["adapter_sha256"])
    receipt.expect_ref("test", PRODUCT["test"], EXP["test_sha256"])
    receipt.expect_ref("state", PRODUCT["state"], EXP["state_sha256"])
    receipt.expect_ref("config", PRODUCT["config"], EXP["config_sha256"])
    receipt.expect_ref("ledger", PRODUCT["ledger"], EXP["ledger_sha256"])
    receipt.expect_ref("python", PRODUCT["python"], EXP["python_sha256"])
    receipt.expect_ref("node", PRODUCT["node"], EXP["node_sha256"])

    _, b1_summary, b1_extra = inventory_summary(EVIDENCE / "inventory-baseline-01.json", expect_tool_sha=tool_sha)
    receipt.check("backups_hashed_in_inventory",
                  b1_extra["backup_records"] == EXP["backup_regular_count"] and b1_extra["backup_all_regular_verified"],
                  backup_records=b1_extra["backup_records"], all_regular_verified=b1_extra["backup_all_regular_verified"])

    ok, reasons = _contract_ok()
    receipt.check("contract_matches_frozen_contract", ok, reasons=reasons)
    return receipt.emit()


def _contract_ok() -> tuple[bool, list[str]]:
    try:
        contract = load_json(RUNROOT / "plan-contract.json")
    except Exception as exc:  # noqa: BLE001
        return False, [f"CONTRACT_UNREADABLE:{exc}"]
    reasons = []
    if contract.get("task_id") != TASK_ID:
        reasons.append("TASK_ID_MISMATCH")
    if contract.get("allowed_paths") != [RUNREL]:
        reasons.append("ALLOWED_PATHS_MISMATCH")
    if (contract.get("workflow_policy") or {}).get("max_parallel_writers") != 0:
        reasons.append("WRITER_POLICY_MISMATCH")
    gates = {g.get("gate_id"): g for g in contract.get("gate_specs") or []}
    if set(gates) != {"G_BASELINE", "G_RUNNER", "G_ADAPTER_OFFLINE", "G_PRESERVE", "G_REPORT"}:
        reasons.append("GATE_SET_MISMATCH")
    return (not reasons), reasons


def g_runner() -> int:
    receipt = Receipt("g-runner")
    baseline_receipt = EVIDENCE / "g-baseline-recovery-02.json"
    if baseline_receipt.exists():
        doc = load_json(baseline_receipt)
        receipt.refs["g-baseline-recovery-02"] = ref_of(baseline_receipt)
        receipt.check("g_baseline_pass", doc.get("status") == "PASS")
    else:
        receipt.check("g_baseline_pass", False, detail="missing receipt")
    for name, path in {
        "run_command.py": RUNROOT / "checks/run_command.py",
        "test_run_command.py": RUNROOT / "checks/test_run_command.py",
        "check-specs.json": RUNROOT / "check-specs.json",
        "check-specs-freeze.json": RUNROOT / "check-specs-freeze.json",
    }.items():
        if path.exists():
            receipt.refs[name] = ref_of(path)
        else:
            receipt.check(f"{name}_present", False, detail="missing")

    freeze_ok = False
    if (RUNROOT / "check-specs-freeze.json").exists():
        freeze = load_json(RUNROOT / "check-specs-freeze.json")
        receipt.refs["freeze"] = ref_of(RUNROOT / "check-specs-freeze.json")
        resolved = freeze.get("resolved_source_hashes") or {}
        missing = [rel for rel, sha in resolved.items() if not sha]
        mismatched = []
        for rel, sha in resolved.items():
            if not sha:
                continue
            path = ROOT / rel
            if not path.exists() or sha256_file(path)[1] != sha:
                mismatched.append(rel)
        freeze_ok = not missing and not mismatched
        receipt.check("freeze_all_sources_resolved", freeze_ok, missing=missing, mismatched=mismatched)
        receipt.check("freeze_adapter_test",
                      resolved.get("scripts/line_backup_cua_adapter.mjs") == EXP["adapter_sha256"]
                      and resolved.get("tests/test_cua_adapter.mjs") == EXP["test_sha256"])
    else:
        receipt.check("freeze_all_sources_resolved", False, detail="freeze file missing")

    preflight = host_receipt_ok(receipt, "runner-preflight-01")
    preflight_doc = host_json_stdout("runner-preflight-01")
    if preflight_doc is not None:
        receipt.check("preflight_report", preflight_doc.get("status") == "PREFLIGHT_OK", status=preflight_doc.get("status"))
        node_evidence_absent = not any(
            (EVIDENCE / f"{stem}{suffix}").exists()
            for stem in ("node-adapter-syntax-02", "node-adapter-tests-01")
            for suffix in (".json", ".receipt.json", ".stdout", ".stderr")
        )
        receipt.check("preflight_before_node_launch", node_evidence_absent)
    selftest = host_receipt_ok(receipt, "runner-selftest-01")
    selftest_doc = host_json_stdout("runner-selftest-01")
    if selftest_doc is not None:
        cases = selftest_doc.get("cases") or []
        receipt.check("runner_selftest_pass", selftest_doc.get("pass") is True and cases and all(c.get("ok") for c in cases),
                      cases=len(cases), failed=[c.get("name") for c in cases if not c.get("ok")])
        receipt.check("runner_selftest_binding",
                      selftest_doc.get("run_command_sha256") == sha256_file(RUNROOT / "checks/run_command.py")[1])
    return receipt.emit()


def g_adapter() -> int:
    receipt = Receipt("g-adapter")
    for gate in ("g-baseline-recovery-02.json", "g-runner.json"):
        path = EVIDENCE / gate
        if path.exists():
            doc = load_json(path)
            receipt.refs[gate] = ref_of(path)
            receipt.check(f"{gate}_pass", doc.get("status") == "PASS")
        else:
            receipt.check(f"{gate}_pass", False, detail="missing receipt")
    for check_id in ("node-adapter-syntax-02", "node-adapter-tests-01"):
        stem = EVIDENCE / check_id
        if not pathlib.Path(f"{stem}.receipt.json").exists():
            receipt.check(f"{check_id}_present", False, detail="missing receipt")
            continue
        doc = load_json(pathlib.Path(f"{stem}.receipt.json"))
        receipt.refs[f"{check_id}.receipt"] = ref_of(pathlib.Path(f"{stem}.receipt.json"))
        stdout_ref = ref_of(pathlib.Path(f"{stem}.stdout"))
        stderr_ref = ref_of(pathlib.Path(f"{stem}.stderr"))
        receipt.refs[f"{check_id}.stdout"] = stdout_ref
        receipt.refs[f"{check_id}.stderr"] = stderr_ref
        receipt.check(f"{check_id}_exit", doc.get("exit_code") == 0 and doc.get("timeout") is not True and doc.get("status") == "PASS",
                      exit_code=doc.get("exit_code"), timeout=doc.get("timeout"), status=doc.get("status"))
        receipt.check(f"{check_id}_stderr_empty", stderr_ref["bytes"] == 0)
        receipt.check(f"{check_id}_adapter_hash",
                      (doc.get("product_hashes") or {}).get("adapter_sha256") == EXP["adapter_sha256"]
                      and (doc.get("product_hashes") or {}).get("test_sha256") == EXP["test_sha256"],
                      product_hashes=doc.get("product_hashes"))
        if check_id == "node-adapter-syntax-02":
            receipt.check("syntax_stdout_empty", stdout_ref["bytes"] == 0)
        else:
            text = pathlib.Path(f"{stem}.stdout").read_bytes().decode("utf-8", "replace")
            receipt.check("tests_reported_pass", ("fail 0" in text) or ("# fail 0" in text) or ("not ok" not in text),
                          stdout_bytes=stdout_ref["bytes"])
    receipt.expect_ref("adapter_now", PRODUCT["adapter"], EXP["adapter_sha256"])
    receipt.expect_ref("test_now", PRODUCT["test"], EXP["test_sha256"])
    receipt.expect_ref("state_now", PRODUCT["state"], EXP["state_sha256"])
    receipt.expect_ref("config_now", PRODUCT["config"], EXP["config_sha256"])
    receipt.expect_ref("ledger_now", PRODUCT["ledger"], EXP["ledger_sha256"])
    return receipt.emit()


def g_preservation() -> int:
    receipt = Receipt("g-preservation")
    for gate in ("g-baseline-recovery-02.json", "g-runner.json", "g-adapter-offline.json"):
        path = EVIDENCE / gate
        if path.exists():
            receipt.refs[gate] = ref_of(path)
            receipt.check(f"{gate}_pass", load_json(path).get("status") == "PASS")
        else:
            receipt.check(f"{gate}_pass", False, detail="missing receipt")
    check_inventory(receipt, "inventory-preservation-01", EVIDENCE / "inventory-preservation-01.json", expect_tool_sha=sha256_file(RUNROOT / "tools/inventory.py")[1])
    check_inventory(receipt, "inventory-preservation-02", EVIDENCE / "inventory-preservation-02.json", expect_tool_sha=sha256_file(RUNROOT / "tools/inventory.py")[1])
    compare_path = EVIDENCE / "compare-preservation.json"
    if compare_path.exists():
        doc = load_json(compare_path)
        receipt.refs["compare-preservation"] = ref_of(compare_path)
        receipt.check("compare_preservation", doc.get("status") == "PASS", failures=len(doc.get("failures") or []))
    else:
        receipt.check("compare_preservation", False, detail="missing")
    obs1 = git_observation()
    obs2 = git_observation()
    receipt.refs["git_observation_1"] = obs1
    receipt.refs["git_observation_2"] = obs2
    receipt.check("git_two_observations_equal", obs1 == obs2)
    receipt.check("git_head", obs1["head"] == EXP["head"], actual=obs1["head"])
    receipt.check("git_index", obs1["index_sha256"] == EXP["index_sha256"] and obs1["index_bytes"] == EXP["index_bytes"])
    for name, key in (("adapter", "adapter"), ("test", "test"), ("state", "state"), ("config", "config"), ("ledger", "ledger")):
        receipt.expect_ref(f"{name}_final", PRODUCT[key], EXP[f"{key}_sha256"])
    for name, (sha, size) in {**INCIDENTS, **OLD_FAIL}.items():
        receipt.expect_ref("incident_final_" + pathlib.Path(name).name, name, sha, size)
    _, p2_summary, p2_extra = inventory_summary(EVIDENCE / "inventory-preservation-02.json", expect_tool_sha=sha256_file(RUNROOT / "tools/inventory.py")[1])
    receipt.check("backups_final", p2_extra["backup_records"] == EXP["backup_regular_count"] and p2_extra["backup_all_regular_verified"],
                  backup_records=p2_extra["backup_records"])
    planned = load_json(EVIDENCE / "planned-additions.json")
    tail = set(planned.get("post_preservation_tail_writes") or [])
    p2_doc = load_json(EVIDENCE / "inventory-preservation-02.json")
    p2_paths = {str(r.get("path")) for r in (p2_doc.get("records") or [])}
    receipt.refs["planned-additions"] = ref_of(EVIDENCE / "planned-additions.json")
    written = sorted(p for p in tail if (ROOT / p).exists())
    receipt.check("tail_writes_declared", bool(tail) and all(p.startswith(RUNREL + "/") for p in tail), tail=sorted(tail), written_so_far=written)
    receipt.check("tail_writes_after_preservation_scan", all(p not in p2_paths for p in tail), tail_not_in_p2=sorted(p for p in tail if p not in p2_paths))
    return receipt.emit()


def main(argv: list[str]) -> int:
    global DRY_RUN
    args = list(argv[1:])
    if args and args[0] == "--dry-run":
        DRY_RUN = True
        args = args[1:]
    if len(args) != 1 or args[0] not in OUTPUTS:
        raise SystemExit("usage: gate_receipts.py [--dry-run] g-baseline|g-runner|g-adapter|g-preservation")
    if pathlib.Path.cwd() != ROOT:
        print(json.dumps({"status": "REFUSED", "errors": [f"WRONG_CWD:{pathlib.Path.cwd()}"]}))
        return 2
    if pathlib.Path(os.path.realpath(sys.argv[0])) != RUNROOT / "tools/gate_receipts.py":
        print(json.dumps({"status": "REFUSED", "errors": [f"WRONG_SCRIPT:{os.path.realpath(sys.argv[0])}"]}))
        return 2
    return {"g-baseline": g_baseline, "g-runner": g_runner, "g-adapter": g_adapter, "g-preservation": g_preservation}[args[0]]()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
