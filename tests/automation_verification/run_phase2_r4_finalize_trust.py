#!/usr/bin/env python3
"""Phase 2 / R4 — `transaction finalize` trusts any JSON claim of VERIFIED.

CLAIM  finalize() reads `--verification-json`, persists its content unchanged and, for
       `--outcome VERIFIED`, appends a `verified_albums` entry without checking the
       source of the JSON, its content, or whether it belongs to this run/group. The
       entry it writes carries no `source_authority`, so the transaction -> verify-only
       loop can never reach overall PASS even when the destination afterwards really
       contains exactly the claimed files.
ENTRY  Real CLI: `transaction prepare` + `transaction finalize` in the test-mode fixture
       root /private/tmp/line-backup-acceptance-case-06, then `verify-only --test-mode`
       over a byte-identical copy of the post-(a) state in the verifier fixture root
       /private/tmp/line-backup-acceptance-verifier/r4 (canonical config/state children).
ORACLE Persisted state after every commit (revision, run fields, registry entry),
       destination inventory at finalize time (0 files) versus the fabricated claim
       (PASS/57), the verbatim verify-only stdout/exit over the same state, and the
       r4 state hash before/after verify-only (verify must not mutate state).
DECIDE Fabricated / self-contradictory / foreign JSON producing VERIFIED entries, and a
       verify-only result that cannot confirm the finalize-made entry from real files,
       mean registry writes are not evidence-backed: finalize must validate the
       verification source and run identity before the registry addition can commit.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import GROUP, make_png
from harness import (durable_copy_tree, program_hashes, read_json, run_product, sha256_file, write_json,
                     write_tree_manifest)

CASE_ROOT = Path("/private/tmp/line-backup-acceptance-case-06")
VERIFIER_ROOT = Path("/private/tmp/line-backup-acceptance-verifier/r4")
BACKUP_ROOT = CASE_ROOT / "backups"
ALBUM_A = BACKUP_ROOT / "album-a"
ALBUM_B = BACKUP_ROOT / "album-b"
ALBUM_C = BACKUP_ROOT / "album-c"
ALBUM_D = BACKUP_ROOT / "album-d"
START, END, COUNT = "2024-05-13", "2024-05-17", 57
FP57 = {"start_date": START, "end_date": END, "expected_images": COUNT}
GROUP_B = "line:jp.naver.line.mac:測試相簿-FAIL-宣稱"
GROUP_C = "line:jp.naver.line.mac:測試相簿-空JSON"
GROUP_D = "line:jp.naver.line.mac:測試相簿-別run"
FP_B = {"start_date": "2024-06-01", "end_date": "2024-06-02", "expected_images": 3}
FP_C = {"start_date": "2024-07-01", "end_date": "2024-07-02", "expected_images": 1}
FP_D = {"start_date": "2024-08-01", "end_date": "2024-08-02", "expected_images": 2}


def find_run(state: dict, run_id: str) -> dict | None:
    return next((r for r in state.get("runs", []) if isinstance(r, dict) and r.get("run_id") == run_id), None)


def find_entry(state: dict, run_id: str) -> dict | None:
    return next((e for e in state.get("verified_albums", []) if isinstance(e, dict) and e.get("verified_run_id") == run_id), None)


def local_hashes() -> dict:
    here = Path(__file__).resolve().parent
    out = {}
    for name in ("harness.py", "fixtures.py", Path(__file__).name):
        item = here / name
        out[name] = {"bytes": item.stat().st_size, "sha256": sha256_file(item)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case-root", default=str(CASE_ROOT))
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root = Path(ns.case_root)
    ev = Path(ns.evidence_dir)
    if case_root != CASE_ROOT:
        print(json.dumps({"error": "R4 reproduction is bound to its assigned case root", "case_root": str(case_root)}))
        return 2
    ev.mkdir(parents=True, exist_ok=True)

    for root in (CASE_ROOT, VERIFIER_ROOT):
        if root.exists():
            shutil.rmtree(root)
    BACKUP_ROOT.mkdir(parents=True)
    ALBUM_A.mkdir()
    state_path = case_root / "state.json"
    state0 = {"schema_version": 2, "revision": 0, "current_run_id": None, "active_writer_id": None,
              "context_lock": None, "runs": [], "verified_albums": []}
    write_json(state_path, state0)
    write_json(ev / "pre-state.json", state0)

    record: dict = {
        "claim": "transaction finalize trusts any --verification-json and writes a VERIFIED registry entry "
                 "without source/content/run-association validation; the entry can never satisfy the verifier's "
                 "source requirement, so the transaction -> verify-only loop never closes",
        "entry": "real CLI transaction prepare/finalize (test-mode case-06) + verify-only --test-mode (verifier/r4)",
        "oracle": "persisted state after each commit; registry entry fields; destination inventory at finalize time "
                  "vs fabricated claim; verbatim verify-only stdout/exit; r4 state hash before/after verify-only",
        "decision": "fabricated/contradictory/foreign JSON producing VERIFIED entries, and verify-only being unable "
                    "to confirm the finalize-made entry from real files, mean finalize must validate the verification "
                    "source and run identity before the registry addition can commit",
        "program_hashes": {**program_hashes(), **local_hashes()},
        "case_root": str(CASE_ROOT),
        "verifier_root": str(VERIFIER_ROOT),
        "subcases": {},
        "observations": [],
    }

    def tx(step: str, operation: str, extra: list[str]) -> dict:
        before = read_json(state_path)
        rec = run_product(ev / step, ["transaction", operation, "--project-root", str(CASE_ROOT),
                                      "--state", str(state_path), "--test-mode",
                                      "--evidence-dir", str(CASE_ROOT / "evidence" / step), *extra], timeout=120)
        after = read_json(state_path)
        write_json(ev / f"state-{step}.json", after)
        rec["revision_before"], rec["revision_after"] = before.get("revision"), after.get("revision")
        rec["result_code"] = (rec.get("result") or {}).get("result")
        return rec

    def prepare(step: str, run_id: str, owner: str, group: str, fp: dict, dest: Path) -> dict:
        return tx(step, "prepare", ["--run-id", run_id, "--owner-id", owner, "--group-key", group,
                                    "--start-date", fp["start_date"], "--end-date", fp["end_date"],
                                    "--expected-images", str(fp["expected_images"]), "--destination", str(dest)])

    def finalize(step: str, run_id: str, owner: str, verification: Path) -> dict:
        revision = read_json(state_path)["revision"]
        return tx(step, "finalize", ["--run-id", run_id, "--expected-revision", str(revision),
                                     "--expected-owner-id", owner, "--verification-json", str(verification),
                                     "--outcome", "VERIFIED"])

    # ---------------- (a) fabricated PASS/57 JSON on a non-terminal run ----------------
    fake_a = {"schema_version": 1, "mode": "verify_only", "run_id": "RUN-R4A", "group_key": GROUP,
              "fingerprint": FP57, "destination": str(ALBUM_A), "filesystem_status": "PASS",
              "regular_files": 57, "recognized_images": 57, "zero_byte_files": 0,
              "produced_by": "fabricated fixture; no filesystem scan was performed"}
    verification_a = case_root / "verification-a.json"
    write_json(verification_a, fake_a)
    prep_a = prepare("a-prepare", "RUN-R4A", "WRITER-R4A", GROUP, FP57, ALBUM_A)
    dest_files_at_finalize = sorted(p.name for p in ALBUM_A.iterdir())
    fin_a = finalize("a-finalize", "RUN-R4A", "WRITER-R4A", verification_a)
    shutil.copyfile(state_path, ev / "state-after-a.json")
    state_a = read_json(state_path)
    run_a = find_run(state_a, "RUN-R4A")
    entry_a = find_entry(state_a, "RUN-R4A")
    record["subcases"]["a_fabricated_pass_json_non_terminal_run"] = {
        "input_verification_json": {"path": str(verification_a), "content": fake_a},
        "run_before_finalize": {"run_id": "RUN-R4A", "phase": "SAVE_ALL_INTENT_COMMITTED",
                                "terminal_before": False, "verification_before": None},
        "destination_files_at_finalize_time": {"count": len(dest_files_at_finalize), "names": dest_files_at_finalize,
                                               "note": "the fabricated JSON claims PASS/57 regular files while the "
                                                       "destination was empty and was never scanned by the product"},
        "prepare": {k: prep_a[k] for k in ("exit_code", "result", "revision_before", "revision_after", "record_dir")},
        "finalize": {k: fin_a[k] for k in ("exit_code", "result", "revision_before", "revision_after", "record_dir")},
        "persisted_state_after_a": state_a,
        "persisted_state_after_a_sha256": sha256_file(ev / "state-after-a.json"),
        "registry_entry_written": entry_a,
        "registry_entry_keys": sorted(entry_a.keys()) if entry_a else None,
        "entry_has_source_authority": ("source_authority" in entry_a) if entry_a else None,
        "run_a_after_finalize": {k: (run_a or {}).get(k) for k in ("workflow_outcome", "phase", "contract_revision",
                                                                   "observed_title", "source_provenance")},
        "ownership_after_finalize": {"current_run_id": state_a.get("current_run_id"),
                                     "active_writer_id": state_a.get("active_writer_id"),
                                     "context_lock": state_a.get("context_lock")},
    }

    # ---------------- (b1) JSON content itself claims FAIL ----------------
    fake_b1 = {"schema_version": 1, "mode": "verify_only", "run_id": "RUN-R4B", "group_key": GROUP_B,
               "fingerprint": FP_B, "destination": str(ALBUM_B), "filesystem_status": "FAIL",
               "regular_files": 0, "recognized_images": 0, "zero_byte_files": 12, "failure_class": "INPUT_NEGATIVE",
               "produced_by": "fabricated fixture whose content claims total failure"}
    verification_b1 = case_root / "verification-b1-fail-claim.json"
    write_json(verification_b1, fake_b1)
    prep_b1 = prepare("b1-prepare", "RUN-R4B", "WRITER-R4B", GROUP_B, FP_B, ALBUM_B)
    fin_b1 = finalize("b1-finalize", "RUN-R4B", "WRITER-R4B", verification_b1)
    state_b1 = read_json(state_path)
    run_b1 = find_run(state_b1, "RUN-R4B")
    entry_b1 = find_entry(state_b1, "RUN-R4B")
    record["subcases"]["b1_content_claims_fail"] = {
        "input_verification_json": {"path": str(verification_b1), "content": fake_b1},
        "prepare": {k: prep_b1[k] for k in ("exit_code", "result", "revision_before", "revision_after", "record_dir")},
        "finalize": {k: fin_b1[k] for k in ("exit_code", "result", "revision_before", "revision_after", "record_dir")},
        "run_b1_stored_verification": (run_b1 or {}).get("verification"),
        "run_b1_workflow_outcome": (run_b1 or {}).get("workflow_outcome"),
        "registry_entry_written": entry_b1,
        "contradiction": "the stored verification evidence says FAIL / 0 recognized images / 12 zero-byte files, yet "
                         "the run was finalized VERIFIED and a verified_albums entry was added (content never inspected)",
    }

    # ---------------- (b2) completely empty JSON ----------------
    verification_b2 = case_root / "verification-b2-empty.json"
    write_json(verification_b2, {})
    prep_b2 = prepare("b2-prepare", "RUN-R4C", "WRITER-R4C", GROUP_C, FP_C, ALBUM_C)
    fin_b2 = finalize("b2-finalize", "RUN-R4C", "WRITER-R4C", verification_b2)
    state_b2 = read_json(state_path)
    run_b2 = find_run(state_b2, "RUN-R4C")
    entry_b2 = find_entry(state_b2, "RUN-R4C")
    record["subcases"]["b2_empty_json"] = {
        "input_verification_json": {"path": str(verification_b2), "content": {}},
        "prepare": {k: prep_b2[k] for k in ("exit_code", "result", "revision_before", "revision_after", "record_dir")},
        "finalize": {k: fin_b2[k] for k in ("exit_code", "result", "revision_before", "revision_after", "record_dir")},
        "run_b2_stored_verification": (run_b2 or {}).get("verification"),
        "run_b2_workflow_outcome": (run_b2 or {}).get("workflow_outcome"),
        "registry_entry_written": entry_b2,
        "contradiction": "an empty JSON object {} was accepted as terminal verification evidence and produced a "
                         "VERIFIED registry entry",
    }

    # ---------------- (c) JSON belonging to another run / another group ----------------
    prep_c = prepare("c-prepare", "RUN-R4D", "WRITER-R4D", GROUP_D, FP_D, ALBUM_D)
    fin_c = finalize("c-finalize", "RUN-R4D", "WRITER-R4D", verification_a)
    state_c = read_json(state_path)
    run_d = find_run(state_c, "RUN-R4D")
    entry_d = find_entry(state_c, "RUN-R4D")
    stored_d = (run_d or {}).get("verification") or {}
    record["subcases"]["c_foreign_run_group_json"] = {
        "foreign_verification_json": {"path": str(verification_a), "content": fake_a,
                                      "belongs_to": {"run_id": "RUN-R4A", "group_key": GROUP,
                                                     "destination": str(ALBUM_A)}},
        "target_run": {"run_id": "RUN-R4D", "group_key": GROUP_D, "destination": str(ALBUM_D)},
        "prepare": {k: prep_c[k] for k in ("exit_code", "result", "revision_before", "revision_after", "record_dir")},
        "finalize": {k: fin_c[k] for k in ("exit_code", "result", "revision_before", "revision_after", "record_dir")},
        "run_d_stored_verification": stored_d,
        "stored_verification_run_id": stored_d.get("run_id"),
        "stored_verification_group_key": stored_d.get("group_key"),
        "run_group_key": (run_d or {}).get("group_key"),
        "run_workflow_outcome": (run_d or {}).get("workflow_outcome"),
        "registry_entry_written": entry_d,
        "cross_run_accepted": (stored_d.get("run_id") not in (None, "RUN-R4D")
                               and (run_d or {}).get("workflow_outcome") == "VERIFIED"),
    }

    # ---------------- (d) integration closed loop: verify-only over the same state ----------------
    (VERIFIER_ROOT / "config").mkdir(parents=True)
    (VERIFIER_ROOT / "state").mkdir(parents=True)
    config_path = VERIFIER_ROOT / "config" / "line_backup_config.json"
    config = {"schema_version": 2, "group_key": GROUP, "group_name": GROUP.rsplit(":", 1)[-1],
              "backup_root": str(BACKUP_ROOT), "app_identifier": "jp.naver.line.mac", "max_albums_per_run": 1,
              "recovery_limit": 1, "poll_interval_seconds": 5, "stable_samples": 3, "max_wait_seconds": 600}
    write_json(config_path, config)
    (VERIFIER_ROOT / "state" / "run_log.md").write_text("fixture run log (non-gating projection)\n", encoding="utf-8")
    state_copy = VERIFIER_ROOT / "state" / "backup_state.json"
    shutil.copyfile(ev / "state-after-a.json", state_copy)
    state_copy_sha_before = sha256_file(state_copy)
    pngs = [make_png(ALBUM_A / f"image-{index:03d}.png", size=8) for index in range(COUNT)]
    probe = subprocess.run(["/usr/bin/file", "--mime-type", "-b", "--", str(pngs[0])], capture_output=True, text=True,
                           check=False)
    verify = run_product(ev / "d-verify-only", ["verify-only", "--project-root", str(VERIFIER_ROOT),
                                                "--config", str(config_path), "--state", str(state_copy),
                                                "--run-log", str(VERIFIER_ROOT / "state" / "run_log.md"),
                                                "--destination", str(ALBUM_A), "--group-key", GROUP,
                                                "--start-date", START, "--end-date", END,
                                                "--expected-images", str(COUNT),
                                                "--evidence-dir", str(VERIFIER_ROOT / "evidence" / "verify-only"),
                                                "--test-mode"], timeout=120)
    state_copy_sha_after = sha256_file(state_copy)
    vres = verify.get("result") or {}
    vfs = vres.get("filesystem") or {}
    record["subcases"]["d_verify_only_closed_loop"] = {
        "fixture_root": str(VERIFIER_ROOT),
        "config": {"path": str(config_path), "content": config, "sha256": sha256_file(config_path)},
        "state_copy": {"path": str(state_copy), "sha256_before": state_copy_sha_before,
                       "sha256_after": state_copy_sha_after,
                       "bytes_identical_to_persisted_state_after_a": state_copy_sha_before == sha256_file(ev / "state-after-a.json"),
                       "field_rewrites": "NONE - the verified destination is literally state.run.destination "
                                         "(album-a) as persisted by the transaction CLI; only backup_root is a "
                                         "verifier-side config value, so no state field was adapted"},
        "destination": {"path": str(ALBUM_A), "files": len(pngs),
                        "total_bytes": sum(p.stat().st_size for p in pngs),
                        "sample_file_probe": {"argv": ["/usr/bin/file", "--mime-type", "-b", "--", str(pngs[0])],
                                              "exit_code": probe.returncode, "stdout": probe.stdout.strip()}},
        "verify_only": {"exit_code": verify["exit_code"], "result": vres, "record_dir": verify["record_dir"]},
        "observed_statuses": {k: vres.get(k) for k in ("filesystem_status", "registry_status", "source_status",
                                                       "state_status", "overall_status", "failure_class")},
        "filesystem_summary": {"regular_files": vfs.get("regular_files"), "recognized_images": vfs.get("recognized_images"),
                               "total_bytes": vfs.get("total_bytes"), "error_codes": vfs.get("error_codes")},
        "expected_statuses_from_task": {"allowed": ["registry FAIL or source UNRESOLVED"],
                                        "observed": "recorded as-is; no expectation was rewritten"},
        "registry_entry_used_by_verify_only": entry_a,
        "verify_only_mutated_state": state_copy_sha_after != state_copy_sha_before,
    }

    # ---------------- verdicts ----------------
    a_reproduced = (fin_a["result_code"] == "FINALIZED" and entry_a is not None
                    and entry_a.get("source_kind") == "filesystem_verification"
                    and "source_authority" not in entry_a)
    b1_reproduced = (fin_b1["result_code"] == "FINALIZED" and (run_b1 or {}).get("workflow_outcome") == "VERIFIED"
                     and entry_b1 is not None)
    b2_reproduced = (fin_b2["result_code"] == "FINALIZED" and (run_b2 or {}).get("workflow_outcome") == "VERIFIED"
                     and entry_b2 is not None)
    c_reproduced = (fin_c["result_code"] == "FINALIZED"
                    and record["subcases"]["c_foreign_run_group_json"]["cross_run_accepted"] and entry_d is not None)
    d_source_confirmed = vres.get("source_status") == "CONFIRMED"
    d_reproduced = (not d_source_confirmed) and vres.get("overall_status") != "PASS"
    subcase_verdicts = {
        "a": "REPRODUCED_FAKE_JSON_FINALIZED" if a_reproduced else "NOT_REPRODUCED",
        "b1": "REPRODUCED_FAIL_CLAIM_STILL_VERIFIED" if b1_reproduced else "NOT_REPRODUCED",
        "b2": "REPRODUCED_EMPTY_JSON_STILL_VERIFIED" if b2_reproduced else "NOT_REPRODUCED",
        "c": "REPRODUCED_CROSS_RUN_JSON_ACCEPTED" if c_reproduced else "NOT_REPRODUCED",
        "d": "REPRODUCED_FINALIZE_ENTRY_NOT_SOURCE_CONFIRMED" if d_reproduced else "NOT_REPRODUCED",
    }
    all_reproduced = a_reproduced and b1_reproduced and b2_reproduced and c_reproduced and d_reproduced
    any_reproduced = any([a_reproduced, b1_reproduced, b2_reproduced, c_reproduced, d_reproduced])
    record["subcase_verdicts"] = subcase_verdicts
    record["verdict"] = "R4_REPRODUCED" if all_reproduced else ("R4_PARTIALLY_REPRODUCED" if any_reproduced else "R4_NOT_REPRODUCED")
    record["integrated_entry_cannot_reach_source_confirmed"] = not d_source_confirmed
    record["rationale"] = ("finalize() writes only schema keys (group_key, fingerprint, verified_run_id, destinations, "
                           "source_kind, evidence); the verifier requires entry.source_authority == "
                           "'authoritative_exact_join' for source CONFIRMED, which the product never writes and the "
                           "registry schema (additionalProperties=false) does not even allow, so the verified_albums "
                           "entry produced by finalize can never close the verify-only loop")

    durable_case = durable_copy_tree(CASE_ROOT, ev / "case-root-durable")
    durable_verifier = durable_copy_tree(VERIFIER_ROOT, ev / "verifier-root-durable")
    record["durable_copies"] = {
        "case_root_durable": {"path": str(ev / "case-root-durable"), "files": durable_case["files"],
                              "total_bytes": durable_case["total_bytes"], "manifest_sha256": durable_case["manifest_sha256"]},
        "verifier_root_durable": {"path": str(ev / "verifier-root-durable"), "files": durable_verifier["files"],
                                  "total_bytes": durable_verifier["total_bytes"],
                                  "manifest_sha256": durable_verifier["manifest_sha256"]},
    }
    write_json(ev / "observation.json", record)
    write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "subcase_verdicts": subcase_verdicts,
                      "observed": record["subcases"]["d_verify_only_closed_loop"]["observed_statuses"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
