"""Read-only dynamic destination polling and full image decode."""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
TASK = Path(__file__).resolve().parents[2]
OPERATOR_PATH = TASK / "candidate/v2/operator.py"
spec = importlib.util.spec_from_file_location("task_operator", OPERATOR_PATH)
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)
from line_backup_acceptance.verifier import _classify_filesystem, _inventory, _inventory_key


def write_new(directory: Path, name: str, value):
    with (directory / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--run-authority", type=Path, required=True)
    args = parser.parse_args()
    operator.require(args.run_authority.is_relative_to(TASK), "run authority outside task")
    authority = operator.authorize(args.run_authority, args.project_root)
    op = operator.Operator(operator.ROOT, authority["config_sha256"], authority["run_id"],
                           authority["owner_id"], authority["fingerprint"],
                           authority["target_evidence"], authority["target_evidence_sha256"])
    op.evidence.mkdir(parents=True, exist_ok=True)

    reader = operator.ProjectReader(str(operator.ROOT))
    try:
        cfg, state, _, _, _ = op.load(reader)
    finally:
        reader.close()
    run = op.run(state)
    operator.require(state["active_writer_id"] == op.owner_id and state["current_run_id"] == op.run_id
                     and run["workflow_outcome"] == "IN_PROGRESS", "no current writer")
    operator.require(run["phase"] in {"DOWNLOAD_STARTED", "VERIFYING"}
                     and run["intent_state"] == "TRIGGER_CONFIRMED", "not in download observation phase")
    dispatch = run["dispatch_evidence"]
    operator.require(dispatch["save_all_click_count"] == 1 and dispatch["save_all_invocation_attempted"] is True
                     and dispatch["folder_chooser_appeared"] is True, "dispatch/chooser not proved")
    destination = Path(run["destination"])
    operator.no_symlink(destination)
    expected_destination = Path(cfg["backup_root"]) / cfg["group_name"] / (
        f"{op.fp['start_date']}_{op.fp['end_date']}_{op.fp['expected_images']}張")
    operator.require(destination == expected_destination, "destination authority mismatch")

    deadline = time.monotonic() + cfg["max_wait_seconds"]
    stable = []
    samples = []
    while True:
        operator.no_symlink(destination)
        sample = _inventory(destination, False)
        sample["monotonic_seconds"] = time.monotonic()
        samples.append(sample)
        write_new(op.evidence, f"inventory-{len(samples):03}.json", sample)
        print(json.dumps({"sample": len(samples), "images": sample["recognized_images"],
                          "entries": len(sample["entries"]), "bytes": sample["total_bytes"]}), flush=True)
        if stable and (_inventory_key(stable[-1]) != _inventory_key(sample)
                       or stable[-1]["total_bytes"] != sample["total_bytes"]):
            stable = []
        stable.append(sample)
        if len(stable) >= cfg["stable_samples"]:
            tail = stable[-cfg["stable_samples"]:]
            verdict, _ = _classify_filesystem(tail, op.fp["expected_images"])
            if verdict == "PASS":
                break
        if time.monotonic() >= deadline:
            write_new(op.evidence, "verification-incomplete.json", {
                "outcome": "INCOMPLETE_OR_STILL_DOWNLOADING", "last_inventory": sample,
                "samples": len(samples), "retry_save_all": False})
            raise RuntimeError("verification deadline; no repeat Save All")
        time.sleep(cfg["poll_interval_seconds"])

    operator.require(all(b["monotonic_seconds"] - a["monotonic_seconds"] >= cfg["poll_interval_seconds"]
                         for a, b in zip(tail, tail[1:])), "stable intervals not fulfilled")
    decoder = TASK / "candidate/v2/bin/image-decode"
    operator.no_symlink(decoder)
    decoded = subprocess.run([str(decoder), str(destination), str(op.fp["expected_images"])],
                             capture_output=True, timeout=180)
    (op.evidence / "image-decode.stdout.json").write_bytes(decoded.stdout)
    (op.evidence / "image-decode.stderr.log").write_bytes(decoded.stderr)
    result = json.loads(decoded.stdout)
    operator.require(decoded.returncode == 0 and result["verdict"] == "PASS" and not decoded.stderr,
                     "full decode failed")
    operator.require(len(result["entries"]) == op.fp["expected_images"]
                     and all(entry["decoded"] is True for entry in result["entries"]), "decode count")

    operator.no_symlink(destination)
    last = _inventory(destination, False)
    operator.require(_inventory_key(last) == _inventory_key(tail[-1])
                     and last["total_bytes"] == tail[-1]["total_bytes"], "inventory changed during decode")
    verification = {
        "observed_at": operator.utc_now(), "outcome": "PASS", "regular_files": last["regular_files"],
        "image_files": last["recognized_images"], "subdirectories": [], "total_bytes": last["total_bytes"],
        "extensions": dict(collections.Counter(Path(entry["relative_path"]).suffix for entry in last["entries"])),
        "metadata_files": [], "zero_byte_files": [], "partial_temp_files": [], "unrecognized_files": [],
        "other_entries": [], "stable_samples": cfg["stable_samples"], "inventory": last["entries"],
        "evidence": f"Actual inventories were stable at {cfg['poll_interval_seconds']}-second intervals; all "
                    f"{op.fp['expected_images']} images decoded with ImageIO/RGB draw; post-decode inventory unchanged."
    }
    hashes = [entry["sha256"] for entry in last["entries"]]
    write_new(op.evidence, "filesystem-verification.json", verification)
    write_new(op.evidence, "verification-receipt.json", {
        "verdict": "PASS", "verification": verification,
        "decoder_sha256": operator.sha(decoder.read_bytes()), "decoder_exit_code": decoded.returncode,
        "decoder_stdout_sha256": operator.sha((op.evidence / "image-decode.stdout.json").read_bytes()),
        "stable_interval_seconds": cfg["poll_interval_seconds"],
        "stable_sample_count": cfg["stable_samples"], "sample_count": len(samples),
        "actual_content_multiset_sha256": operator.sha("\n".join(sorted(hashes)).encode()),
        "distinct_content_hashes": len(set(hashes)),
        "duplicate_content_hash_observation": len(hashes) - len(set(hashes)),
        "backup_files_modified_by_verifier": False
    })
    print(json.dumps({"verdict": "PASS", "images": verification["image_files"],
                      "total_bytes": verification["total_bytes"],
                      "fully_decoded": len(result["entries"])}), flush=True)


if __name__ == "__main__":
    main()
