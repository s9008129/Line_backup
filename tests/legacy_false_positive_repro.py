#!/usr/bin/env python3
"""Execute the preserved legacy verifier against isolated 56/58-image inputs."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
from pathlib import Path


WORK = Path(__file__).resolve().parents[1]
LEGACY = WORK / "evidence/20260915-verify-only-57/verify-only.sh"
BASE = Path("/private/tmp/line-backup-legacy-false-positive")
GROUP = "line:jp.naver.line.mac:旻謙允楨成長日記"
JPEGISH = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run_case(count: int) -> dict:
    root = BASE / str(count)
    if root.exists():
        shutil.rmtree(root)
    destination = root / "destination"
    (root / "config").mkdir(parents=True)
    (root / "state").mkdir()
    destination.mkdir()
    for index in range(count):
        (destination / f"image-{index:03d}.jpg").write_bytes(JPEGISH)
    write_json(root / "config/line_backup_config.json", {"schema_version": 2, "group_key": GROUP,
        "group_name": "fixture", "backup_root": str(root), "app_identifier": "jp.naver.line.mac",
        "max_albums_per_run": 1, "recovery_limit": 1, "poll_interval_seconds": 0,
        "stable_samples": 3, "max_wait_seconds": 15})
    write_json(root / "state/backup_state.json", {"schema_version": 2, "revision": 1,
        "current_run_id": None, "active_writer_id": None, "context_lock": None, "runs": [],
        "verified_albums": [{"group_key": GROUP, "fingerprint": {"start_date": "2024-05-13",
        "end_date": "2024-05-17", "expected_images": 57}, "destinations": [str(destination)]}]})
    (root / "state/run_log.md").write_text("legacy fixture\n", encoding="utf-8")
    script = root / "legacy-verify.sh"
    source = LEGACY.read_text(encoding="utf-8")
    source = source.replace('PROJECT_ROOT="/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state"', f'PROJECT_ROOT="{root}"')
    source = source.replace('DEST="/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57"', f'DEST="{destination}"')
    source = source.replace('OUT_DIR="${0:A:h}"', f'OUT_DIR="{root / "output"}"')
    script.write_text(source, encoding="utf-8")
    script.chmod(0o755)
    output = root / "output"
    output.mkdir()
    process = subprocess.run([str(script)], cwd=WORK, env=os.environ.copy(), capture_output=True, text=True, check=False)
    (output / "stdout.log").write_text(process.stdout, encoding="utf-8")
    (output / "stderr.log").write_text(process.stderr, encoding="utf-8")
    (output / "exit-code").write_text(str(process.returncode) + "\n", encoding="utf-8")
    actual_count = len([p for p in destination.iterdir() if p.is_file()])
    accepted = process.returncode == 0 and "FILESYSTEM_VERIFICATION=PASS" in process.stdout
    return {"count": count, "actual_image_files": actual_count, "legacy_exit": process.returncode,
            "legacy_claimed_pass": accepted, "argv": [str(script)], "stdout": str(output / "stdout.log"),
            "stderr": str(output / "stderr.log"), "exit_code": str(output / "exit-code")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    ns = parser.parse_args()
    if BASE.exists():
        shutil.rmtree(BASE)
    BASE.mkdir(parents=True)
    rows = [run_case(count) for count in (56, 58)]
    # The independent oracle is the fixture's actual filesystem count, not
    # the legacy output.  A reproduction succeeds only if the old process
    # accepts both wrong counts while the counts remain independently known.
    match = all(row["actual_image_files"] == row["count"] and row["legacy_claimed_pass"] for row in rows)
    summary = {"schema_version": 1, "legacy_script": str(LEGACY), "rows": rows,
               "independent_oracle": "old verifier accepted exact wrong counts 56 and 58",
               "reproduction_match": match}
    Path(ns.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.summary).write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reproduction_match": match, "counts": [r["actual_image_files"] for r in rows]}, sort_keys=True))
    return 0 if match else 1


if __name__ == "__main__":
    raise SystemExit(main())
