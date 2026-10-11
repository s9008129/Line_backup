#!/usr/bin/env python3
"""Record the present identity of the exact historical E01 cache directory."""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import stat
import sys

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
R = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
REL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/epochs/e01/tmp/pip-cache"


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main() -> int:
    if pathlib.Path.cwd() != ROOT:
        raise RuntimeError("WRONG_ROOT")
    target = ROOT / REL
    st = os.lstat(target)
    if not stat.S_ISDIR(st.st_mode) or target.is_symlink() or sorted(os.listdir(target)):
        raise RuntimeError("E01_PIPCACHE_NOT_EMPTY_DIRECTORY")
    observed = {"path": REL, "dev": st.st_dev, "ino": st.st_ino, "actual_type": "DIRECTORY",
                "mode": st.st_mode, "uid": st.st_uid, "gid": st.st_gid, "size": st.st_size,
                "mtime_ns": st.st_mtime_ns, "ctime_ns": st.st_ctime_ns, "children": [],
                "observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "historical_inode_or_readback": "UNKNOWN"}
    sys.path.insert(0, str(R / "tools"))
    from evidence_io import publish_exclusive
    manifest_path = f"{R.relative_to(ROOT).as_posix()}/evidence/e01-pip-cache-current-readback-01.json"
    raw = encoded({"format": "ML07_E01_PIPCACHE_CURRENT_READBACK_V1", "task_id": "TASK-20261010-line-v3-live-e2e", "observation": observed})
    manifest_ref = publish_exclusive(ROOT, manifest_path, raw, max_bytes=1_000_000)
    receipt = {"format": "ML07_E01_PIPCACHE_READBACK_RECEIPT_V1", "task_id": "TASK-20261010-line-v3-live-e2e",
               "producer": "tools/prepare_e01_pipcache_readback.py", "phase": "BOOTSTRAP",
               "observation": observed, "artifact": manifest_ref, "readback_verified": True}
    receipt_raw = encoded(receipt)
    receipt_ref = publish_exclusive(ROOT, f"{R.relative_to(ROOT).as_posix()}/evidence/e01-pip-cache-current-readback-01.receipt.json", receipt_raw, max_bytes=1_000_000)
    print(json.dumps({"artifact": manifest_ref, "receipt": receipt_ref}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
