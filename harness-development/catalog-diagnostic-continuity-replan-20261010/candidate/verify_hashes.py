#!/usr/bin/env python3
# verify_hashes.py -- recompute the frozen candidate hash from the candidate
# files and compare it to the recorded frozen value. Read-only.
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
FROZEN_FILES = ["catalog_diagnostic.py", "offline_vision.swift", "profiles.json",
                "run_offline_once.py", "test_catalog_diagnostic.py"]

def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()

files = {name: sha(os.path.join(HERE, name)) for name in FROZEN_FILES}
computed = hashlib.sha256(json.dumps({k: v for k, v in sorted(files.items())},
                                     separators=(",", ":")).encode()).hexdigest()
recorded = json.load(open(os.path.join(TASK, "offline-validation", "candidate-manifest.json")))["candidate_hash"]
binding = json.load(open(os.path.join(TASK, "offline-validation", "binding.json")))["candidate_hash"]
print(json.dumps({"computed": computed, "recorded": recorded, "binding": binding,
                  "match": computed == recorded == binding,
                  "files": files}, indent=1, sort_keys=True))
sys.exit(0 if computed == recorded == binding else 1)
