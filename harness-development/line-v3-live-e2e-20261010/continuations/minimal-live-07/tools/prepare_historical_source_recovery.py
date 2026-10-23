#!/usr/bin/env python3
"""Recover two exact E01 source bytes from the user-provided transcript annex.

This publishes an immutable archive only. It never restores or executes the
historical producer files.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import stat
import sys

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
R = ROOT / RUNREL
ARCHIVE = f"{RUNREL}/evidence/historical-source-recovery-01"
TRANSCRIPT = "codex-session-01a12976-2554-7ed0-8d4c-356688f674ee.md"
TRANSCRIPT_SHA = "5cd0f697d6b6eac0bd7c6ffa284397980b08113aab2cd480435735f2e2028210"
EXPECTED = {
    "tools/prepare_dependencies.py": {
        "start_line": 4552, "end_line": 4728, "line_count": 177, "bytes": 11895,
        "sha256": "bab2ab28c4641b76448e804dffc447d76d91de74e2eb9a55479c4ad3212a12a3",
        "source_header_line": 4551, "extraction": "cat -n numbered lines; strip 9 spaces + sequential line number + four display separator spaces; blank numbered lines have no payload",
    },
    "tools/prepare_epoch.py": {
        "start_line": 3894, "end_line": 4061, "line_count": 168, "bytes": 17156,
        "sha256": "2cab971d7e21fe2f3b11c45b85925ca8eccd543e3c9d7ef0e211d7e193cac1ce",
        "source_header_line": 3893, "extraction": "cat output; remove exactly four display-indentation spaces from each source line",
    },
}


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_bytes(lines: list[str], relative: str) -> bytes:
    spec = EXPECTED[relative]
    block = lines[spec["start_line"] - 1:spec["end_line"]]
    if len(block) != spec["line_count"]:
        raise RuntimeError("TRANSCRIPT_SOURCE_LINE_COUNT:" + relative)
    if relative.endswith("prepare_epoch.py"):
        if any(not line.startswith("    ") for line in block):
            raise RuntimeError("TRANSCRIPT_DISPLAY_INDENT:" + relative)
        raw = "".join(line[4:] for line in block).encode()
    else:
        out: list[bytes] = []
        for ordinal, line in enumerate(block, 1):
            if line.endswith("\n"):
                body, ending = line[:-1], b"\n"
            else:
                body, ending = line, b""
            field = body[:10]
            payload = body[10:]
            number = field.strip()
            if (len(field) != 10 or not number.isdigit() or int(number) != ordinal
                    or (payload and not payload.startswith("    "))):
                raise RuntimeError("TRANSCRIPT_NUMBERED_LINE:" + relative + ":" + str(ordinal))
            out.append((payload[4:] if payload else "").encode() + ending)
        raw = b"".join(out)
    if len(raw) != spec["bytes"] or sha(raw) != spec["sha256"]:
        raise RuntimeError("RECOVERED_SOURCE_HASH_MISMATCH:" + relative)
    return raw


def fstat(path: pathlib.Path) -> dict:
    st = path.lstat()
    return {"path": path.relative_to(ROOT).as_posix(), "dev": st.st_dev, "ino": st.st_ino,
            "mode": st.st_mode, "uid": st.st_uid, "gid": st.st_gid, "size": st.st_size,
            "mtime_ns": st.st_mtime_ns, "ctime_ns": st.st_ctime_ns,
            "actual_type": "REGULAR" if stat.S_ISREG(st.st_mode) else "OTHER"}


def main() -> int:
    if pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != R / "tools/prepare_historical_source_recovery.py" or len(sys.argv) != 1:
        raise RuntimeError("LOCATION_OR_ARGUMENTS")
    annex_path = R / "evidence/read-only-user-input-01.json"
    annex_receipt_path = R / "evidence/read-only-user-input-01.receipt.json"
    annex_raw = annex_path.read_bytes()
    annex_receipt_raw = annex_receipt_path.read_bytes()
    annex = json.loads(annex_raw)
    annex_receipt = json.loads(annex_receipt_raw)
    transcript = base64.b64decode(annex["source_base64"], validate=True)
    if (sha(transcript) != TRANSCRIPT_SHA or annex["source_fstat"].get("sha256") != TRANSCRIPT_SHA
            or annex["user_reference"] != TRANSCRIPT or annex["authority"] != "READ_ONLY_USER_INPUT"
            or annex.get("source_producer") is not None or annex.get("source_write_authority") is not None
            or annex_receipt.get("annex", {}).get("sha256") != sha(annex_raw)
            or annex_receipt.get("annex", {}).get("bytes") != len(annex_raw)
            or annex_receipt.get("readback_verified") is not True):
        raise RuntimeError("TRANSCRIPT_ANNEX_BINDING")
    lines = transcript.decode("utf-8").splitlines(keepends=True)
    recovered = {rel: source_bytes(lines, rel) for rel in EXPECTED}

    e01 = R / "epochs/e01"
    freeze_raw = (e01 / "source-freeze.json").read_bytes()
    freeze = json.loads(freeze_raw)
    if sha(freeze_raw) != "de309ab1d7516c9bc81c01b0ce7b1e2d33ee1b0c96556e85eae62bb2660e840b":
        raise RuntimeError("E01_SOURCE_FREEZE_HASH")
    historical = []
    for rel, raw in recovered.items():
        expected_hash = EXPECTED[rel]["sha256"]
        if freeze.get("source_hashes", {}).get(f"{RUNREL}/{rel}") != expected_hash:
            raise RuntimeError("RECOVERY_NOT_MATCHING_E01_FREEZE:" + rel)
        old_path = R / rel
        current = fstat(old_path)
        historical.append({"source_path": f"{RUNREL}/{rel}", "e01_frozen_sha256": expected_hash,
                           "recovered_sha256": sha(raw), "recovered_bytes": len(raw),
                           "transcript_line_range_inclusive": [EXPECTED[rel]["start_line"], EXPECTED[rel]["end_line"]],
                           "transcript_source_header_line": EXPECTED[rel]["source_header_line"],
                           "transcript_extraction": EXPECTED[rel]["extraction"],
                           "current_old_path_readback": {**current, "sha256": sha(old_path.read_bytes()) if current["actual_type"] == "REGULAR" else None},
                           "historical_old_path_metadata": "UNKNOWN_WHEN_NOT_RECORDED",
                           "restored_or_executed": False})

    sys.path.insert(0, str(R / "tools"))
    from evidence_io import mkdir_exclusive, publish_exclusive
    directory = mkdir_exclusive(ROOT, ARCHIVE, mode=0o700)
    source_refs = []
    for rel, raw in recovered.items():
        name = pathlib.PurePosixPath(rel).name
        source_refs.append({"source_path": f"{RUNREL}/{rel}",
                            "archive": publish_exclusive(ROOT, f"{ARCHIVE}/{name}", raw, max_bytes=2_000_000)})
    observed = dt.datetime.now(dt.timezone.utc).isoformat()
    manifest = {"format": "ML07_HISTORICAL_SOURCE_RECOVERY_MANIFEST_V1",
                "task_id": "TASK-20261010-line-v3-live-e2e", "publisher": "context_history",
                "decision_owner": "root_planner", "source_authority": "READ_ONLY_USER_INPUT",
                "source_producer": None, "source_write_authority": None,
                "transcript": {"user_reference": TRANSCRIPT, "absolute_path": str(ROOT / TRANSCRIPT),
                               "annex_path": f"{RUNREL}/evidence/read-only-user-input-01.json",
                               "annex_sha256": sha(annex_raw), "annex_receipt_path": f"{RUNREL}/evidence/read-only-user-input-01.receipt.json",
                               "annex_receipt_sha256": sha(annex_receipt_raw), "source_bytes": len(transcript),
                               "source_sha256": sha(transcript)},
                "e01_source_freeze": {"path": f"{RUNREL}/epochs/e01/source-freeze.json", "sha256": sha(freeze_raw)},
                "recovered_sources": historical, "archive_directory": directory,
                "observed_at_utc": observed, "old_e01_artifacts_modified": False}
    manifest_raw = encoded(manifest)
    manifest_ref = publish_exclusive(ROOT, f"{ARCHIVE}/recovery-manifest.json", manifest_raw, max_bytes=1_000_000)
    receipt = {"format": "ML07_HISTORICAL_SOURCE_RECOVERY_RECEIPT_V1",
               "task_id": "TASK-20261010-line-v3-live-e2e", "publisher": "context_history",
               "decision_owner": "root_planner", "producer": "tools/prepare_historical_source_recovery.py",
               "manifest": manifest_ref, "sources": source_refs,
               "readback_verified": True, "observed_at_utc": observed,
               "historical_metadata_restored": False, "historical_tools_executed": False}
    receipt_raw = encoded(receipt)
    receipt_ref = publish_exclusive(ROOT, f"{ARCHIVE}/recovery-receipt.json", receipt_raw, max_bytes=1_000_000)
    print(json.dumps({"archive_directory": directory, "sources": source_refs,
                      "manifest": manifest_ref, "receipt": receipt_ref}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
