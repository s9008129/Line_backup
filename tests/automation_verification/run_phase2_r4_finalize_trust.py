#!/usr/bin/env python3
"""Phase 2 / R4 — `transaction finalize` must validate its verification evidence, and the
transaction -> verify-only loop must close on real files.

CLAIM (Rev14, reproduced pre-fix in attempt-01)  finalize() trusted any --verification-json:
       arbitrary JSON (PASS/57, FAIL/0, {}, another run's result) produced a VERIFIED registry
       entry, and the entry could never satisfy the verifier's source requirement, so the loop
       never closed.
ENTRY  Real CLI `transaction prepare` + `verify-only --test-mode` + `commit` + `finalize` in the
       test-mode fixture root /private/tmp/line-backup-acceptance-case-06; the dispatcher adapter
       replaces only external I/O and writes the 57 fixture images itself.
ORACLE Persisted state after every commit (revision, run fields, registry entry), the real
       destination inventory, the genuine verify-only chains (result.json + manifest.json), the
       verbatim verify-only stdout/exit over the closed state, and state hashes.
DECIDE Post-fix (this run): every fabricated / malformed / foreign / tampered payload must be
       refused (INVALID_VERIFICATION_EVIDENCE or VERIFICATION_RUN_MISMATCH, exit 4, no registry
       write), and the honest loop prepare -> verify -> commit -> finalize -> verify must reach
       overall PASS with source CONFIRMED.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures as F  # noqa: E402
import harness as H  # noqa: E402

DRIVER_ID = "phase2-r4-finalize-trust"
GROUP = F.GROUP
FP57 = F.FP57
START, END, COUNT = FP57["start_date"], FP57["end_date"], FP57["expected_images"]
CASE_ROOT = Path("/private/tmp/line-backup-acceptance-case-06")
ATTEMPT_01 = H.WORK / "evidence/20260916-auto-verification/attempt-01/phase2-r4"
PRE_FIX = {
    "verdict": "REPRODUCED_FINALIZE_TRUSTS_JSON",
    "observation": ("finalize committed VERIFIED from arbitrary JSON (PASS/57, FAIL/0, {}, another run's JSON); the "
                    "entry carried no source_authority and the transaction -> verify-only loop never reached PASS"),
    "evidence": str(ATTEMPT_01 / "observation.json"),
}

DOWNLOADER = '''#!/usr/bin/env python3
import argparse, json, os, struct, time, zlib
p = argparse.ArgumentParser(); p.add_argument('--counter'); p.add_argument('--outcome')
p.add_argument('--crash-after-dispatch', action='store_true')
n = p.parse_args()
with open(n.counter, 'a', encoding='utf-8') as fh:
    fh.write(json.dumps({{'outcome': n.outcome, 'pid': os.getpid(), 'at': time.time()}}) + '\\n')
dest = {dest!r}
files = {files!r}
os.makedirs(dest, exist_ok=True)
def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
raw = b''.join(b'\\x00' + bytes((10, 20, 30) * 8) for _ in range(8))
png = (b'\\x89PNG\\r\\n\\x1a\\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 8, 8, 8, 2, 0, 0, 0))
       + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
for i in range(files):
    with open(os.path.join(dest, f'image-{{i:03d}}.png'), 'wb') as fh:
        fh.write(png)
raise SystemExit(1 if n.crash_after_dispatch else 0)
'''


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return H.sha256_file(Path(path))


def write_downloader(path: Path, destination: Path, files: int) -> Path:
    path.write_text(DOWNLOADER.format(dest=str(destination), files=files), encoding="utf-8")
    path.chmod(0o755)
    return path


def base(paths: dict, operation: str, *extra: str) -> list[str]:
    return ["transaction", operation, "--project-root", str(paths["case_root"]), "--config", str(paths["config"]),
            "--run-log", str(paths["run_log"]), "--state", str(paths["state"]), "--test-mode", *extra]


def verify_args(paths: dict, evidence_dir: Path, *, run_id: str | None) -> list[str]:
    args = ["verify-only", "--project-root", str(paths["case_root"]), "--config", str(paths["config"]),
            "--state", str(paths["state"]), "--test-mode", "--destination", str(paths["destination"]),
            "--group-key", GROUP, "--start-date", START, "--end-date", END, "--expected-images", str(COUNT),
            "--evidence-dir", str(evidence_dir)]
    if run_id:
        args += ["--run-id", run_id]
    return args


def build_closed_loop_fixture(root: Path, ev: Path) -> dict:
    H.ensure_owned_root(root, DRIVER_ID)
    H.reset_owned_content(root)
    paths = F.write_canonical_root(root, F.fresh_state(), destination_name="backups/album-a")
    paths["source_evidence"] = F.source_evidence_record(root, name="source-evidence.json")["path"]
    paths["counter"] = root / "dispatch-counter.jsonl"
    paths["counter"].touch()
    paths["dispatcher"] = write_downloader(root / "downloader-adapter.py", Path(paths["destination"]), COUNT)
    return paths


def refutation_fixture(root: Path) -> dict:
    """A separate canonical case root content for the finalize negatives (completed dispatch)."""
    H.reset_owned_content(root)
    destination = root / "backups" / "album-refusals"
    destination.mkdir(parents=True)
    state = F.fresh_state(revision=2)
    run = F.completed_dispatch_run("RUN-R4-R", "WRITER-R4-R", str(destination))
    state["runs"] = [run]
    state["current_run_id"] = "RUN-R4-R"
    state["active_writer_id"] = "WRITER-R4-R"
    paths = F.write_canonical_root(root, state, destination_name="backups/album-refusals",
                                   config_extra={"backup_root": str(root / "backups")})
    paths["source_evidence"] = F.source_evidence_record(root, name="source-evidence.json")["path"]
    return paths


def finalize_args(paths: dict, run_id: str, owner: str, revision: int, verification: Path) -> list[str]:
    return base(paths, "finalize", "--run-id", run_id, "--expected-revision", str(revision),
                "--expected-owner-id", owner, "--outcome", "VERIFIED",
                "--verification-json", str(verification), "--evidence-dir", str(Path(paths["case_root"]) / "evidence" / "finalize"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case-root", default=str(CASE_ROOT))
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root, ev = Path(ns.case_root), Path(ns.evidence_dir)
    if case_root.resolve() != CASE_ROOT.resolve():
        print(json.dumps({"verdict": "INCONCLUSIVE_SETUP_FAILED",
                          "reason": f"R4 is bound to its literal case root {CASE_ROOT}"}, ensure_ascii=False))
        return 1
    ev.mkdir(parents=True, exist_ok=True)

    record = {"driver": DRIVER_ID,
              "claim": ("pre-fix: finalize trusted any JSON and the loop never closed; post-fix: fabricated/malformed/"
                        "foreign/tampered evidence is refused and the honest loop reaches overall PASS"),
              "entry": "real CLI prepare -> verify-only -> commit -> finalize -> verify-only (test-mode case-06)",
              "oracle": ("persisted state after every commit + real destination inventory + genuine verify chains + "
                         "verify-only result/exit + pre/post state hashes"),
              "pre_fix": PRE_FIX, "case_root": str(case_root), "program_hashes": H.program_hashes()}
    checks: dict[str, bool] = {}

    # ---------------- closed loop ----------------
    paths = build_closed_loop_fixture(case_root, ev)
    prepare = H.run_product(ev / "closed-loop" / "01-prepare",
                            base(paths, "prepare", "--run-id", "RUN-R4", "--owner-id", "WRITER-R4",
                                 "--group-key", GROUP, "--start-date", START, "--end-date", END,
                                 "--expected-images", str(COUNT), "--destination", str(paths["destination"]),
                                 "--source-evidence", str(paths["source_evidence"]),
                                 "--dispatcher", str(paths["dispatcher"]), "--dispatch-counter", str(paths["counter"]),
                                 "--dispatcher-outcome", "RETURNED",
                                 "--evidence-dir", str(case_root / "evidence" / "prepare")), timeout=120)
    p_result = prepare["result"] or {}
    dest_files = sorted(p.name for p in Path(paths["destination"]).iterdir())
    record["closed_loop"] = {"prepare": {"exit_code": prepare["exit_code"], "result": p_result,
                                         "counter_lines": len(H.counter_entries(paths["counter"])),
                                         "destination_files": len(dest_files)},
                             "argv": prepare["argv"]}
    checks["prepare.prepared"] = p_result.get("result") == "PREPARED" and prepare["exit_code"] == 0
    checks["prepare.dispatch"] = p_result.get("dispatch_performed") is True
    checks["prepare.destination-57"] = len(dest_files) == COUNT
    checks["prepare.counter-1"] = len(H.counter_entries(paths["counter"])) == 1

    verify1_dir = case_root / "evidence" / "verify-1"
    verify1 = H.run_product(ev / "closed-loop" / "02-verify-1", verify_args(paths, verify1_dir, run_id="RUN-R4"),
                            timeout=120)
    v1 = verify1["result"] or {}
    record["closed_loop"]["verify_1"] = {"exit_code": verify1["exit_code"],
                                         "filesystem": v1.get("filesystem_status"),
                                         "registry": v1.get("registry_status"),
                                         "source": v1.get("source_status"),
                                         "overall": v1.get("overall_status")}
    checks["verify1.filesystem-pass"] = v1.get("filesystem_status") == "PASS"
    checks["verify1.consistent-axes"] = ((v1.get("registry_status"), v1.get("source_status")) != ("PASS", "CONFIRMED"))

    commit = H.run_product(ev / "closed-loop" / "03-commit",
                           base(paths, "commit", "--run-id", "RUN-R4", "--expected-revision", "2",
                                "--expected-owner-id", "WRITER-R4",
                                "--verification-json", str(verify1_dir / "result.json"),
                                "--evidence-dir", str(case_root / "evidence" / "commit")), timeout=120)
    record["closed_loop"]["commit"] = {"exit_code": commit["exit_code"], "result": commit["result"]}
    checks["commit.committed"] = (commit["result"] or {}).get("result") == "COMMITTED_VERIFICATION" \
                                 and commit["exit_code"] == 0

    finalize = H.run_product(ev / "closed-loop" / "04-finalize",
                             finalize_args(paths, "RUN-R4", "WRITER-R4", 3, verify1_dir / "result.json"),
                             timeout=120)
    record["closed_loop"]["finalize"] = {"exit_code": finalize["exit_code"], "result": finalize["result"]}
    state = read_json(paths["state"])
    entry = (state.get("verified_albums") or [None])[0]
    record["closed_loop"]["registry_entry"] = entry
    checks["finalize.finalized"] = (finalize["result"] or {}).get("result") == "FINALIZED" and finalize["exit_code"] == 0
    checks["finalize.entry-bound"] = bool(entry) and entry.get("verified_run_id") == "RUN-R4"

    verify2_dir = case_root / "evidence" / "verify-2"
    verify2 = H.run_product(ev / "closed-loop" / "05-verify-2", verify_args(paths, verify2_dir, run_id="RUN-R4"),
                            timeout=120)
    v2 = verify2["result"] or {}
    record["closed_loop"]["verify_2"] = {"exit_code": verify2["exit_code"],
                                         "axes": {k: v2.get(k) for k in ("filesystem_status", "registry_status",
                                                                         "source_status", "state_status",
                                                                         "overall_status")}}
    checks["verify2.exit0"] = verify2["exit_code"] == 0
    checks["verify2.overall-pass"] = v2.get("overall_status") == "PASS"
    checks["verify2.registry-pass"] = v2.get("registry_status") == "PASS"
    checks["verify2.source-confirmed"] = v2.get("source_status") == "CONFIRMED"
    checks["verify2.state-exact"] = v2.get("state_status") == "EXACT"

    # ---------------- finalize refusals ----------------
    # Preserve the genuine verify-1 chain outside the case root *before* the refusal fixture resets it;
    # the payloads handed to the product must live inside the case root (test-mode authority).
    import shutil as _sh
    preserved_chain = ev / "refusals" / "inputs" / "genuine-chain"
    if preserved_chain.exists():
        _sh.rmtree(preserved_chain)
    _sh.copytree(verify1_dir, preserved_chain)

    rpaths = refutation_fixture(case_root)
    r_state_path = Path(rpaths["state"])
    pre_sha = sha(r_state_path)
    chain_dir = case_root / "evidence" / "genuine-chain"
    chain_dir.parent.mkdir(parents=True, exist_ok=True)
    _sh.copytree(preserved_chain, chain_dir)

    refusal_inputs = case_root / "evidence" / "refusals"
    refusal_inputs.mkdir(parents=True, exist_ok=True)
    fabricated = refusal_inputs / "fabricated-result.json"
    H.write_json(fabricated, {"schema_version": 1, "mode": "verify_only", "run_id": "RUN-R4-R",
                              "group_key": GROUP, "fingerprint": dict(FP57),
                              "destination": str(rpaths["destination"]), "filesystem_status": "PASS",
                              "recognized_images": COUNT, "expected_images": COUNT,
                              "overall_status": "PASS", "exit_code": 0})
    fail_claim = refusal_inputs / "fail-claim.json"
    H.write_json(fail_claim, {"schema_version": 1, "overall_status": "FAIL", "recognized_images": 0})
    empty_claim = refusal_inputs / "empty.json"
    H.write_json(empty_claim, {})

    rows = [
        ("a-fabricated", fabricated, 4, "INVALID_VERIFICATION_EVIDENCE"),
        ("b1-fail-claim", fail_claim, 4, "INVALID_VERIFICATION_EVIDENCE"),
        ("b2-empty", empty_claim, 4, "INVALID_VERIFICATION_EVIDENCE"),
        ("c-foreign-run-chain", chain_dir / "result.json", 4, "VERIFICATION_RUN_MISMATCH"),
    ]
    refusal_rows = {}
    for name, payload_path, expect_exit, expect_class in rows:
        rec = H.run_product(ev / "refusals" / name,
                            finalize_args(rpaths, "RUN-R4-R", "WRITER-R4-R", 2, Path(payload_path)), timeout=120)
        result = rec["result"] or {}
        state_after = sha(r_state_path)
        state_data = read_json(r_state_path)
        refusal_rows[name] = {"exit_code": rec["exit_code"], "result": result,
                              "state_unchanged": state_after == pre_sha,
                              "registry_entries": len(state_data.get("verified_albums") or []),
                              "argv": rec["argv"]}
        checks[f"{name}.refused"] = rec["exit_code"] == expect_exit and result.get("result") == expect_class
        checks[f"{name}.no-write"] = state_after == pre_sha and not (state_data.get("verified_albums") or [])

    # tampered genuine chain: change result.json bytes after its manifest was written
    tampered_dir = case_root / "evidence" / "tampered-chain"
    if tampered_dir.exists():
        _sh.rmtree(tampered_dir)
    _sh.copytree(chain_dir, tampered_dir)
    tampered_target = tampered_dir / "result.json"
    tampered_target.write_bytes(tampered_target.read_bytes() + b"\n")
    rec = H.run_product(ev / "refusals" / "b3-tampered-chain",
                        finalize_args(rpaths, "RUN-R4-R", "WRITER-R4-R", 2, tampered_dir / "result.json"), timeout=120)
    result = rec["result"] or {}
    state_after = sha(r_state_path)
    refusal_rows["b3-tampered-chain"] = {"exit_code": rec["exit_code"], "result": result,
                                         "state_unchanged": state_after == pre_sha,
                                         "registry_entries": len(read_json(r_state_path).get("verified_albums") or [])}
    checks["b3-tampered-chain.refused"] = rec["exit_code"] in (2, 4) and result.get("result") in {
        "INVALID_VERIFICATION_EVIDENCE", "INVALID_INPUT"}
    checks["b3-tampered-chain.no-write"] = state_after == pre_sha
    record["refusals"] = refusal_rows

    record["checks"] = checks
    record["verdict"] = "SAFE_R4_REFUSALS_AND_CLOSED_LOOP" if all(checks.values()) else "REGRESSION_OR_UNEXPECTED"
    H.write_json(ev / "observation.json", record)
    H.durable_copy_tree(case_root, ev / "case-root-durable")
    H.write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "failed": [k for k, v in checks.items() if not v],
                      "verify_2": record["closed_loop"]["verify_2"]["axes"]}, ensure_ascii=False))
    return 0 if record["verdict"] == "SAFE_R4_REFUSALS_AND_CLOSED_LOOP" else 1


if __name__ == "__main__":
    raise SystemExit(main())
