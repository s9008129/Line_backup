#!/usr/bin/env python3
"""Read-only snapshot of the formal authority files and destination."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import stat
from pathlib import Path


def digest(path: Path) -> dict:
    if not path.is_file():
        return {"path": str(path), "exists": False}
    data = path.read_bytes()
    return {"path": str(path), "exists": True, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def inventory(root: Path) -> dict:
    entries = []
    for entry in sorted(os.scandir(root), key=lambda e: e.name):
        st = entry.stat(follow_symlinks=False)
        item = {"relative_path": entry.name, "size": st.st_size, "mtime_ns": st.st_mtime_ns,
                "mode": stat.S_IFMT(st.st_mode), "type": "regular" if stat.S_ISREG(st.st_mode) else "other"}
        if stat.S_ISREG(st.st_mode):
            data = Path(entry.path).read_bytes()
            item["sha256"] = hashlib.sha256(data).hexdigest()
            item["mime"] = mimetypes.guess_type(entry.name)[0]
        entries.append(item)
    return {"root": str(root), "entries": entries, "regular_files": sum(e["type"] == "regular" for e in entries),
            "total_bytes": sum(e["size"] for e in entries)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--run-log", required=True)
    ap.add_argument("--destination", required=True)
    ap.add_argument("--output", required=True)
    ns = ap.parse_args()
    config = Path(ns.config)
    state = Path(ns.state)
    run_log = Path(ns.run_log)
    destination = Path(ns.destination)
    result = {"inputs": [digest(p) for p in (config, state, run_log)],
              "destination": inventory(destination)}
    out = Path(ns.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
