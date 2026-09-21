#!/usr/bin/env python3
"""Deterministic SHA-256 freeze manifest for the v6 replan wave artifacts.

Covers: v6 sources + selftest harness + Phase A/B/E documents + replay/geometry/
negative artifacts + selftest results. Excludes __pycache__ and this manifest.
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
REPLAN = os.path.join(ROOT, "evidence/20260921-replan-v6")

TREES = [
    os.path.join(ROOT, "evidence/20260916-route/tools/v6"),
    REPLAN,
]
SKIP_DIRS = {"__pycache__"}
SKIP_FILES = {"artifact-freeze.json"}
SELF = os.path.abspath(__file__)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


entries = []
for tree in TREES:
    for dirpath, dirnames, filenames in os.walk(tree):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            if os.path.abspath(path) == SELF:
                continue
            rel = os.path.relpath(path, ROOT)
            if rel in SKIP_FILES:
                continue
            entries.append({"path": rel, "bytes": os.path.getsize(path),
                            "sha256": sha256(path)})

entries.sort(key=lambda e: e["path"])
manifest = {
    "schema": "v6-replan-freeze/1",
    "note": "SHA-256 of every v6 replan artifact frozen before the Phase F reviews. "
            "This manifest does not include its own hash; it is recorded in the commit "
            "message and in the review artifacts.",
    "artifact_count": len(entries),
    "artifacts": entries,
}
out = os.path.join(REPLAN, "attempt-01", "artifact-freeze.json")
with open(out, "w", encoding="utf-8") as f:
    f.write(json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
print("written", out, "artifacts:", len(entries))
