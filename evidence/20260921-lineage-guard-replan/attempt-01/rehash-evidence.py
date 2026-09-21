#!/usr/bin/env python3
"""Read-only re-hash of the three lineage-bearing attempt directories.

Verifies, without modifying anything:
  1. every file listed in attempt-12 / attempt-13 `artifact_sha256` maps,
  2. every file listed in attempt-03's run-ledger `evidence_manifest` and
     `evidence_manifest_dirs`,
  3. a full sha256 inventory of the three attempt directories (excluding
     .DS_Store / __pycache__ / *.pyc), reporting files not covered by the
     recorded manifests.

Deterministic: same tree => identical output JSON (sorted keys, no timestamps).
"""
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ATT = {
    "attempt-12": "evidence/20260916-route/attempt-12",
    "attempt-13": "evidence/20260916-route/attempt-13",
    "attempt-03": "evidence/20260921-rev27-save-all/attempt-03",
}
SKIP_NAMES = {".DS_Store"}
SKIP_DIRS = {"__pycache__"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(rel):
    out = {}
    base = os.path.join(ROOT, rel)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name in SKIP_NAMES or name.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, name)
            relpath = os.path.relpath(full, ROOT)
            out[relpath] = sha256_file(full)
    return out


def load(path):
    with open(os.path.join(ROOT, path), "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(paths, base_rel):
    return {k if k.startswith("evidence/") else base_rel + "/" + k: v
            for k, v in paths.items()}


def verify(paths, inventory, base_rel):
    missing, mismatch, verified = [], [], 0
    for key, expected in sorted(paths.items()):
        relpath = key if key.startswith("evidence/") else base_rel + "/" + key
        actual = inventory.get(relpath)
        if actual is None:
            missing.append(key)
        elif actual != expected:
            mismatch.append({"path": relpath, "recorded": expected, "now": actual})
        else:
            verified += 1
    return {"entries": len(paths), "verified": verified, "missing": missing,
            "mismatch": mismatch}


result = {
    "artifact": "lineage-guard replan: read-only evidence re-hash (attempt-01)",
    "method": "sha256 of every file; recorded manifests re-verified against disk",
    "attempts": {},
}

for label, rel in ATT.items():
    inventory = walk(rel)
    entry = {
        "dir": rel,
        "files_on_disk": len(inventory),
        "bytes_on_disk": sum(os.path.getsize(os.path.join(ROOT, p)) for p in inventory),
    }
    if label in ("attempt-12", "attempt-13"):
        scope = load(os.path.join(rel, "99-scope-status.json"))
        recorded = scope.get("artifact_sha256", {})
        entry["recorded_manifest_source"] = rel + "/99-scope-status.json::artifact_sha256"
        entry["recorded_verification"] = verify(recorded, inventory, rel)
        entry["files_not_in_recorded_manifest"] = sorted(
            set(inventory) - set(normalize(recorded, rel)))
    else:
        ledger = load(os.path.join(rel, "run-ledger.json"))
        flat = dict(ledger.get("evidence_manifest", {}))
        for sub, mapping in ledger.get("evidence_manifest_dirs", {}).items():
            for name, sha in mapping.items():
                flat[sub + "/" + name] = sha
        entry["recorded_manifest_source"] = rel + "/run-ledger.json::evidence_manifest(+dirs)"
        entry["recorded_verification"] = verify(flat, inventory, rel)
        entry["files_not_in_recorded_manifest"] = sorted(set(inventory) - set(normalize(flat, rel)))
    result["attempts"][label] = entry

result["verdict"] = "ALL_RECORDED_HASHES_MATCH" if all(
    not e["recorded_verification"]["missing"] and not e["recorded_verification"]["mismatch"]
    for e in result["attempts"].values()) else "HASH_MISMATCH_FOUND"

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence-rehash.json")
payload = json.dumps(result, ensure_ascii=False, indent=1, sort_keys=False)
with open(out, "w", encoding="utf-8") as f:
    f.write(payload + "\n")
print(payload)
sys.exit(0 if result["verdict"] == "ALL_RECORDED_HASHES_MATCH" else 1)
