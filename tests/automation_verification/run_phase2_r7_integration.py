#!/usr/bin/env python3
"""Phase 2 / R7 (post-fix) — the reusable transaction path closes end-to-end and the duplicate gate holds.

CLAIM (Rev14, reproduced pre-fix in attempt-01)  No real path connected prepare/resume/commit/finalize
       to verify-only: after a genuine fixture transaction and a VERIFIED finalization, verify-only still
       reported source UNRESOLVED / overall NOT_ACHIEVED, and a second `prepare` for the same
       fingerprint at a new destination returned PREPARED (duplicate bypass).

ENTRY  Real CLI on the literal canonical case root /private/tmp/line-backup-acceptance-case-09:
       duplicate-check -> prepare (dispatcher adapter replaces only external I/O, owns the side-effect
       counter and writes the 57 fixture images itself) -> verify-only (verify-1 chain) -> commit ->
       finalize VERIFIED -> verify-only run 2 -> duplicate-check (terminal) -> terminal resume ->
       prepare to a second, empty destination.

ORACLE Persisted state/registry (revision, run fields, registry entry), the real destination inventory,
       the independent counter file, the genuine verify-only chains (result.json + manifest.json), and an
       external re-hash of the exported binding reference (the driver re-reads the artifact itself).

DECIDE Post-fix safe verdict: the loop closes (verify-2 = Filesystem PASS / Registry PASS / Source
       CONFIRMED / State EXACT / Overall PASS, exit 0); terminal duplicate-check returns SKIP_DUPLICATE
       and terminal resume returns SKIP_TERMINAL with zero extra dispatch; the same-fingerprint
       different-destination prepare is refused (CONFLICT_DUPLICATE_FINGERPRINT, exit 4, no state write).
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures as F  # noqa: E402
import harness as H  # noqa: E402

DRIVER_ID = "phase2-r7-integration"
GROUP = F.GROUP
FP57 = F.FP57
START, END, COUNT = FP57["start_date"], FP57["end_date"], FP57["expected_images"]
CASE_ROOT = Path("/private/tmp/line-backup-acceptance-case-09")
ATTEMPT_01 = H.WORK / "evidence/20260916-auto-verification/attempt-01/phase2-r7"
PRE_FIX = {
    "verdict": "REPRODUCED_NON_CLOSING_LOOP_AND_DUPLICATE_BYPASS",
    "observation": ("prepare -> resume (1 side effect) -> commit -> finalize VERIFIED; verify-only then reported "
                    "source UNRESOLVED / overall NOT_ACHIEVED, and a second prepare for the same fingerprint at a "
                    "new destination returned PREPARED"),
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


def base(paths: dict, operation: str, *extra: str) -> list[str]:
    return ["transaction", operation, "--project-root", str(paths["case_root"]), "--config", str(paths["config"]),
            "--run-log", str(paths["run_log"]), "--state", str(paths["state"]), "--test-mode", *extra]


def dup_args(paths: dict, destination: str, evidence: Path) -> list[str]:
    return ["transaction", "duplicate-check", "--project-root", str(paths["case_root"]), "--config",
            str(paths["config"]), "--run-log", str(paths["run_log"]), "--state", str(paths["state"]),
            "--test-mode", "--group-key", GROUP, "--start-date", START, "--end-date", END,
            "--expected-images", str(COUNT), "--destination", destination, "--evidence-dir", str(evidence)]


def verify_args(paths: dict, destination: str, evidence_dir: Path, *, run_id: str) -> list[str]:
    return ["verify-only", "--project-root", str(paths["case_root"]), "--config", str(paths["config"]),
            "--state", str(paths["state"]), "--test-mode", "--destination", destination, "--group-key", GROUP,
            "--start-date", START, "--end-date", END, "--expected-images", str(COUNT),
            "--evidence-dir", str(evidence_dir), "--run-id", run_id]


def external_rehash_expectation(paths: dict, entry: dict | None) -> dict:
    """Independently re-read and re-hash the binding artifact the registry entry exports."""
    reference = (entry or {}).get("evidence")
    row: dict = {"reference": reference, "parses": False, "resolved": None, "sha256_matches": False,
                 "anchors_match": False, "external_rehash_ok": False}
    if not isinstance(reference, str):
        return row
    head, sep, rest = reference.partition(":")
    relpath, sep2, sha256 = rest.rpartition(":")
    row["kind"] = head
    if not sep or not sep2 or "/" in relpath or not relpath or len(sha256) != 64:
        return row
    row["parses"] = True
    resolved = Path(paths["case_root"]) / relpath
    row["resolved"] = str(resolved)
    if not resolved.is_file():
        return row
    data = resolved.read_bytes()
    row["sha256_matches"] = hashlib.sha256(data).hexdigest() == sha256 and (entry or {}).get("source_kind") is not None
    try:
        record = json.loads(data.decode("utf-8"))
        row["anchors_match"] = (record.get("app_identifier") == "jp.naver.line.mac"
                                and record.get("group_key") == (entry or {}).get("group_key")
                                and record.get("fingerprint") == (entry or {}).get("fingerprint"))
    except Exception:
        row["anchors_match"] = False
    row["external_rehash_ok"] = bool(row["sha256_matches"] and row["anchors_match"])
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case-root", default=str(CASE_ROOT))
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root, ev = Path(ns.case_root), Path(ns.evidence_dir)
    if case_root.resolve() != CASE_ROOT.resolve():
        print(json.dumps({"verdict": "INCONCLUSIVE_SETUP_FAILED",
                          "reason": f"R7 is bound to its literal case root {CASE_ROOT}"}, ensure_ascii=False))
        return 1
    if ev.exists() and any(ev.iterdir()):
        raise SystemExit(f"refusing: evidence dir {ev} is not empty (append-only evidence)")
    ev.mkdir(parents=True, exist_ok=True)

    H.ensure_owned_root(case_root, DRIVER_ID)
    H.reset_owned_content(case_root)
    paths = F.write_canonical_root(case_root, F.fresh_state(), destination_name="backups/album-integration")
    dest2 = case_root / "backups" / "album-integration-second"
    dest2.mkdir(parents=True, exist_ok=True)
    counter = case_root / "dispatch-counter.jsonl"
    counter.touch()
    adapter = case_root / "downloader-adapter.py"
    adapter.write_text(DOWNLOADER.format(dest=str(paths["destination"]), files=COUNT), encoding="utf-8")
    adapter.chmod(0o755)
    source_evidence = F.source_evidence_record(case_root, name="source-evidence.json")["path"]

    record = {"driver": DRIVER_ID,
              "claim": "post-fix: the transaction -> finalize -> verify-only loop closes and the duplicate gate refuses bypass",
              "entry": "real CLI duplicate-check -> prepare -> verify-1 -> commit -> finalize -> verify-2 -> "
                       "duplicate-check -> terminal resume -> second-destination prepare",
              "oracle": "state/registry + destination inventory + independent counter + genuine verify chains + "
                        "external re-hash of the exported binding",
              "pre_fix": PRE_FIX, "case_root": str(case_root), "program_hashes": H.program_hashes()}
    checks: dict[str, bool] = {}

    dup1 = H.run_product(ev / "01-duplicate-check", dup_args(paths, paths["destination"], case_root / "evidence" / "dup1"))
    checks["dup1.not-duplicate"] = (dup1["result"] or {}).get("result") == "NOT_DUPLICATE" and dup1["exit_code"] == 0
    record["duplicate_check_before"] = {"exit_code": dup1["exit_code"], "result": dup1["result"], "argv": dup1["argv"]}

    prepare = H.run_product(ev / "02-prepare",
                            base(paths, "prepare", "--run-id", "RUN-R7", "--owner-id", "WRITER-R7",
                                 "--group-key", GROUP, "--start-date", START, "--end-date", END,
                                 "--expected-images", str(COUNT), "--destination", str(paths["destination"]),
                                 "--source-evidence", str(source_evidence), "--dispatcher", str(adapter),
                                 "--dispatch-counter", str(counter), "--dispatcher-outcome", "RETURNED",
                                 "--evidence-dir", str(case_root / "evidence" / "prepare")), timeout=120)
    p_result = prepare["result"] or {}
    destination_files = sorted(p.name for p in Path(paths["destination"]).iterdir())
    record["prepare"] = {"exit_code": prepare["exit_code"], "result": p_result,
                         "counter_lines": len(H.counter_entries(counter)),
                         "destination_files": len(destination_files), "argv": prepare["argv"]}
    checks["prepare.prepared"] = p_result.get("result") == "PREPARED" and prepare["exit_code"] == 0
    checks["prepare.dispatch-once"] = p_result.get("dispatch_performed") is True and len(H.counter_entries(counter)) == 1
    checks["prepare.destination-57"] = len(destination_files) == COUNT

    verify1_dir = case_root / "evidence" / "verify-1"
    verify1 = H.run_product(ev / "03-verify-1", verify_args(paths, paths["destination"], verify1_dir, run_id="RUN-R7"),
                            timeout=120)
    v1 = verify1["result"] or {}
    record["verify_1"] = {"exit_code": verify1["exit_code"],
                          "axes": {k: v1.get(k) for k in ("filesystem_status", "registry_status", "source_status",
                                                          "state_status", "overall_status", "failure_class")}}
    checks["verify1.filesystem-pass"] = v1.get("filesystem_status") == "PASS"
    checks["verify1.not-yet-confirmed"] = (v1.get("registry_status"), v1.get("source_status")) != ("PASS", "CONFIRMED")

    commit = H.run_product(ev / "04-commit",
                           base(paths, "commit", "--run-id", "RUN-R7", "--expected-revision", "2",
                                "--expected-owner-id", "WRITER-R7",
                                "--verification-json", str(verify1_dir / "result.json"),
                                "--evidence-dir", str(case_root / "evidence" / "commit")), timeout=120)
    checks["commit.committed"] = (commit["result"] or {}).get("result") == "COMMITTED_VERIFICATION" and commit["exit_code"] == 0
    record["commit"] = {"exit_code": commit["exit_code"], "result": commit["result"]}

    finalize = H.run_product(ev / "05-finalize",
                             base(paths, "finalize", "--run-id", "RUN-R7", "--expected-revision", "3",
                                  "--expected-owner-id", "WRITER-R7", "--outcome", "VERIFIED",
                                  "--verification-json", str(verify1_dir / "result.json"),
                                  "--evidence-dir", str(case_root / "evidence" / "finalize")), timeout=120)
    checks["finalize.finalized"] = (finalize["result"] or {}).get("result") == "FINALIZED" and finalize["exit_code"] == 0
    state_after_finalize = read_json(paths["state"])
    entry = (state_after_finalize.get("verified_albums") or [None])[0]
    rehash = external_rehash_expectation(paths, entry)
    record["finalize"] = {"exit_code": finalize["exit_code"], "result": finalize["result"],
                          "registry_entry": {k: (entry or {}).get(k) for k in
                                             ("group_key", "verified_run_id", "destinations", "source_kind", "evidence")},
                          "external_rehash": rehash}
    checks["finalize.entry-bound"] = bool(entry) and entry.get("verified_run_id") == "RUN-R7"
    checks["finalize.binding-rehashed-externally"] = rehash["external_rehash_ok"] is True

    verify2_dir = case_root / "evidence" / "verify-2"
    verify2 = H.run_product(ev / "06-verify-2", verify_args(paths, paths["destination"], verify2_dir, run_id="RUN-R7"),
                            timeout=120)
    v2 = verify2["result"] or {}
    record["verify_2"] = {"exit_code": verify2["exit_code"],
                          "axes": {k: v2.get(k) for k in ("filesystem_status", "registry_status", "source_status",
                                                          "state_status", "overall_status", "failure_class")}}
    checks["verify2.exit0"] = verify2["exit_code"] == 0
    checks["verify2.overall-pass"] = v2.get("overall_status") == "PASS"
    checks["verify2.registry-pass"] = v2.get("registry_status") == "PASS"
    checks["verify2.source-confirmed"] = v2.get("source_status") == "CONFIRMED"
    checks["verify2.state-exact"] = v2.get("state_status") == "EXACT"

    counter_before_dups = len(H.counter_entries(counter))
    dup2 = H.run_product(ev / "07-duplicate-check-terminal",
                         dup_args(paths, paths["destination"], case_root / "evidence" / "dup2"))
    checks["dup2.skip-duplicate"] = (dup2["result"] or {}).get("result") == "SKIP_DUPLICATE" and dup2["exit_code"] == 0
    record["duplicate_check_after"] = {"exit_code": dup2["exit_code"], "result": dup2["result"]}

    resume = H.run_product(ev / "08-resume-terminal",
                           base(paths, "resume", "--run-id", "RUN-R7", "--expected-revision",
                                str(read_json(paths["state"]).get("revision")),
                                "--expected-owner-id", "WRITER-R7", "--no-dispatch",
                                "--evidence-dir", str(case_root / "evidence" / "resume")), timeout=120)
    checks["resume.skip-terminal"] = (resume["result"] or {}).get("result") == "SKIP_TERMINAL" and resume["exit_code"] == 0
    record["terminal_resume"] = {"exit_code": resume["exit_code"], "result": resume["result"]}

    state_before_second = sha(paths["state"])
    prepare2 = H.run_product(ev / "09-prepare-second-destination",
                             base(paths, "prepare", "--run-id", "RUN-R7-B", "--owner-id", "WRITER-R7B",
                                  "--group-key", GROUP, "--start-date", START, "--end-date", END,
                                  "--expected-images", str(COUNT), "--destination", str(dest2),
                                  "--source-evidence", str(source_evidence), "--dispatcher", str(adapter),
                                  "--dispatch-counter", str(counter), "--dispatcher-outcome", "RETURNED",
                                  "--evidence-dir", str(case_root / "evidence" / "prepare2")), timeout=120)
    state_after_second = sha(paths["state"])
    p2 = prepare2["result"] or {}
    record["prepare_second_destination"] = {"exit_code": prepare2["exit_code"], "result": p2,
                                            "state_unchanged": state_before_second == state_after_second,
                                            "counter_lines": len(H.counter_entries(counter)),
                                            "argv": prepare2["argv"]}
    checks["prepare2.refused"] = p2.get("result") == "CONFLICT_DUPLICATE_FINGERPRINT" and prepare2["exit_code"] == 4
    checks["prepare2.no-state-write"] = state_before_second == state_after_second
    checks["prepare2.no-extra-dispatch"] = len(H.counter_entries(counter)) == counter_before_dups == 1

    record["checks"] = checks
    record["verdict"] = "SAFE_R7_LOOP_CLOSED_AND_DUPLICATE_REFUSED" if all(checks.values()) else "REGRESSION_OR_UNEXPECTED"
    H.write_json(ev / "observation.json", record)
    H.durable_copy_tree(case_root, ev / "case-root-durable")
    H.write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "failed": [k for k, v in checks.items() if not v],
                      "verify_2": record["verify_2"]["axes"],
                      "second_prepare": p2.get("result")}, ensure_ascii=False))
    return 0 if record["verdict"] == "SAFE_R7_LOOP_CLOSED_AND_DUPLICATE_REFUSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
