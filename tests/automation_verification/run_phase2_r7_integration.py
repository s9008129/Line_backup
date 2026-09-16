#!/usr/bin/env python3
"""Phase 2 / R7 — the claimed end-to-end flow does not close.

CLAIM  The product claims a reusable transaction workflow, but no real path connects a
       source adapter (GUI/observation) and a download adapter to the transaction engine
       and then to verify-only: after a genuine new transaction -> finalization, the
       registry entry that finalize creates can never satisfy the verifier's source
       requirement, so the repeat/verify loop reports NOT_ACHIEVED. Additionally the
       post-finalization duplicate gate can be bypassed by choosing a new destination.
ENTRY  Real CLI: duplicate-check -> prepare -> resume (adapter only replaces external I/O
       and owns the side-effect counter) -> commit -> finalize -> duplicate-check ->
       prepare-to-second-destination -> verify-only.
ORACLE Persisted state/registry, real destination files, independent counter, verify-only
       stdout/exit. The adapter never writes VERIFIED and never decides UNKNOWN.
DECIDE Non-closing loop or duplicate bypass -> the reusable-automation CORE item is unmet;
       the integration contract (source evidence, registry provenance, duplicate gate)
       must be fixed before any production dispatch.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import GROUP, make_png
from harness import (counter_entries, durable_copy_tree, program_hashes, read_json, run_product, write_json,
                     write_tree_manifest)

CASE_ROOT = Path("/private/tmp/line-backup-acceptance-case-09")
VERIFIER_ROOT = Path("/private/tmp/line-backup-acceptance-verifier/r7")
DEST = CASE_ROOT / "backups" / "album-integration"
DEST2 = CASE_ROOT / "backups" / "album-integration-second"
START, END, COUNT = "2024-05-13", "2024-05-17", 57


def downloader_script(path: Path, destination: Path, counter: Path, files: int) -> Path:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import argparse, json, time, zlib, struct\n"
        "p = argparse.ArgumentParser(); p.add_argument('--counter'); p.add_argument('--outcome')\n"
        "p.add_argument('--crash-after-dispatch', action='store_true')\n"
        "n = p.parse_args()\n"
        "with open(n.counter, 'a', encoding='utf-8') as fh:\n"
        "    fh.write(json.dumps({'outcome': n.outcome, 'at': time.time()}) + '\\n')\n"
        f"dest = {str(destination)!r}\n"
        f"files = {files}\n"
        "import os\n"
        "os.makedirs(dest, exist_ok=True)\n"
        "def chunk(kind, data):\n"
        "    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)\n"
        "raw = b''.join(b'\\x00' + bytes((10, 20, 30) * 8) for _ in range(8))\n"
        "png = b'\\x89PNG\\r\\n\\x1a\\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 8, 8, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')\n"
        "for i in range(files):\n"
        "    with open(os.path.join(dest, f'image-{i:03d}.png'), 'wb') as fh:\n"
        "        fh.write(png)\n"
        "raise SystemExit(1 if n.crash_after_dispatch else 0)\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-root", default=str(CASE_ROOT))
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root = Path(ns.case_root)
    ev = Path(ns.evidence_dir)
    ev.mkdir(parents=True, exist_ok=True)
    if case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True)
    DEST.mkdir(parents=True)
    DEST2.mkdir(parents=True)
    counter = case_root / "counter.jsonl"
    counter.touch()
    dispatcher = downloader_script(case_root / "downloader-adapter.py", DEST, counter, COUNT)
    state_path = case_root / "state.json"
    write_json(state_path, {"schema_version": 2, "revision": 0, "current_run_id": None, "active_writer_id": None,
                            "context_lock": None, "runs": [], "verified_albums": []})
    write_json(case_root / "verification-adapter.json", {"filesystem_status": "PASS", "regular_files": COUNT,
                                                         "recognized_images": COUNT, "zero_byte_files": 0,
                                                         "produced_by": "download-adapter inventory (external I/O replacement)"})

    common = ["--project-root", str(case_root), "--state", str(state_path), "--test-mode"]
    record = {"claim": "end-to-end transaction -> finalize -> verify-only loop and duplicate gate",
              "entry": "real CLI transaction/verify-only; adapter replaces only external I/O",
              "oracle": "persisted state/registry + destination files + counter + verify-only result",
              "program_hashes": program_hashes(), "case_root": str(case_root)}

    first_dup = run_product(ev / "01-duplicate-check", ["transaction", "duplicate-check", *common,
                                                        "--group-key", GROUP, "--start-date", START, "--end-date", END,
                                                        "--expected-images", str(COUNT), "--destination", str(DEST),
                                                        "--evidence-dir", str(case_root / "evidence" / "dup1")])
    record["duplicate_check_first"] = first_dup["result"]

    prepare = run_product(ev / "02-prepare", ["transaction", "prepare", *common, "--run-id", "RUN-R7",
                                              "--owner-id", "WRITER-R7", "--group-key", GROUP, "--start-date", START,
                                              "--end-date", END, "--expected-images", str(COUNT),
                                              "--destination", str(DEST), "--evidence-dir",
                                              str(case_root / "evidence" / "prepare")])
    record["prepare"] = prepare["result"]

    resume = run_product(ev / "03-resume-dispatch", ["transaction", "resume", *common, "--run-id", "RUN-R7",
                                                     "--expected-revision", "1", "--expected-owner-id", "WRITER-R7",
                                                     "--dispatcher", str(dispatcher), "--dispatch-counter", str(counter),
                                                     "--evidence-dir", str(case_root / "evidence" / "resume")])
    files_after_download = sorted(p.name for p in DEST.iterdir())
    record["resume"] = resume["result"]
    record["downloaded_files"] = len(files_after_download)
    record["side_effect_counter"] = len(counter_entries(counter))

    commit = run_product(ev / "04-commit", ["transaction", "commit", *common, "--run-id", "RUN-R7",
                                            "--expected-revision", "2", "--expected-owner-id", "WRITER-R7",
                                            "--verification-json", str(case_root / "verification-adapter.json"),
                                            "--evidence-dir", str(case_root / "evidence" / "commit")])
    record["commit"] = commit["result"]

    finalize = run_product(ev / "05-finalize", ["transaction", "finalize", *common, "--run-id", "RUN-R7",
                                                "--expected-revision", "3", "--expected-owner-id", "WRITER-R7",
                                                "--verification-json", str(case_root / "verification-adapter.json"),
                                                "--outcome", "VERIFIED", "--evidence-dir",
                                                str(case_root / "evidence" / "finalize")])
    record["finalize"] = finalize["result"]
    state_after_finalize = read_json(state_path)
    write_json(ev / "state-after-finalize.json", state_after_finalize)
    entry = (state_after_finalize.get("verified_albums") or [None])[0]
    record["registry_entry"] = {k: entry.get(k) for k in ("group_key", "verified_run_id", "destinations", "source_kind",
                                                          "source_authority", "evidence")} if entry else None

    second_dup = run_product(ev / "06-duplicate-check-terminal", ["transaction", "duplicate-check", *common,
                                                                  "--group-key", GROUP, "--start-date", START,
                                                                  "--end-date", END, "--expected-images", str(COUNT),
                                                                  "--destination", str(DEST),
                                                                  "--evidence-dir", str(case_root / "evidence" / "dup2")])
    record["duplicate_check_after_terminal"] = second_dup["result"]

    # verify-only closure over the same state/registry/destination (verifier fixture root)
    if VERIFIER_ROOT.exists():
        shutil.rmtree(VERIFIER_ROOT)
    (VERIFIER_ROOT / "config").mkdir(parents=True)
    (VERIFIER_ROOT / "state").mkdir(parents=True)
    write_json(VERIFIER_ROOT / "config" / "line_backup_config.json", {
        "schema_version": 2, "group_key": GROUP, "group_name": GROUP.rsplit(":", 1)[-1],
        "backup_root": str(case_root / "backups"), "app_identifier": "jp.naver.line.mac", "max_albums_per_run": 1,
        "recovery_limit": 1, "poll_interval_seconds": 5, "stable_samples": 3, "max_wait_seconds": 600})
    shutil.copyfile(state_path, VERIFIER_ROOT / "state" / "backup_state.json")
    (VERIFIER_ROOT / "state" / "run_log.md").write_text("fixture run log\n", encoding="utf-8")
    verify = run_product(ev / "07-verify-only", ["verify-only", "--project-root", str(VERIFIER_ROOT),
                                                 "--config", str(VERIFIER_ROOT / "config" / "line_backup_config.json"),
                                                 "--state", str(VERIFIER_ROOT / "state" / "backup_state.json"),
                                                 "--run-log", str(VERIFIER_ROOT / "state" / "run_log.md"),
                                                 "--destination", str(DEST), "--group-key", GROUP,
                                                 "--start-date", START, "--end-date", END,
                                                 "--expected-images", str(COUNT),
                                                 "--evidence-dir", str(case_root / "evidence" / "verify"),
                                                 "--test-mode"])
    record["verify_only_after_finalize"] = verify["result"]

    # duplicate bypass probe: same fingerprint, second (empty) destination
    prepare2 = run_product(ev / "08-prepare-second-destination", ["transaction", "prepare", *common,
                                                                  "--run-id", "RUN-R7-B", "--owner-id", "WRITER-R7B",
                                                                  "--group-key", GROUP, "--start-date", START,
                                                                  "--end-date", END, "--expected-images", str(COUNT),
                                                                  "--destination", str(DEST2), "--evidence-dir",
                                                                  str(case_root / "evidence" / "prepare2")])
    record["prepare_second_destination"] = prepare2["result"]

    verify_result = verify["result"] or {}
    closed = (verify_result.get("overall_status") == "PASS" and verify_result.get("source_status") == "CONFIRMED")
    bypass = (prepare2["result"] or {}).get("result") == "PREPARED"
    record["verdict"] = ("REPRODUCED_NON_CLOSING_LOOP" if not closed else "LOOP_CLOSED") + \
                        ("_AND_DUPLICATE_BYPASS" if bypass else "")
    record["integration_closed"] = closed
    record["duplicate_bypass_after_terminal"] = bypass
    write_json(ev / "observation.json", record)
    durable_copy_tree(VERIFIER_ROOT, ev / "verifier-root-durable")
    durable_copy_tree(case_root, ev / "case-root-durable")
    write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "verify_overall": verify_result.get("overall_status"),
                      "verify_registry": verify_result.get("registry_status"),
                      "verify_source": verify_result.get("source_status"),
                      "second_prepare": (prepare2["result"] or {}).get("result")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
