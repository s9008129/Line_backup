#!/usr/bin/env python3
"""Mechanically derive RUNROOT/evidence/planned-additions.json.

--initial: pre_baseline_additions = baseline-01 RUNREL records minus prewrite v2 records.
           Exclusive (O_EXCL) create; must run after inventory-baseline-02 exists.
--final:   post_baseline_additions = preservation-02 RUNREL records minus baseline-01
           RUNREL records; post_preservation_tail_writes = the frozen 7-file list.
           In-place rewrite (readback verified); must run after preservation-02 and
           before compare-preservation.
"""
import hashlib
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
RUNROOT = ROOT / RUNREL
EVIDENCE = RUNROOT / "evidence"
B1 = EVIDENCE / "inventory-baseline-01.json"
P2 = EVIDENCE / "inventory-preservation-02.json"
PREWRITE = EVIDENCE / "bootstrap-prewrite-runroot-v2.json"
OUT = EVIDENCE / "planned-additions.json"
SCRIPT_REL = f"{RUNREL}/tmp/make_planned_additions.py"

TAIL = [
    f"{RUNREL}/evidence/compare-preservation.json",
    f"{RUNREL}/evidence/preservation-recovery-02.json",
    f"{RUNREL}/E2E測試報告.md",
    f"{RUNREL}/progress.md",
    f"{RUNREL}/evidence/attempt-ledger-recovery-02.json",
    f"{RUNREL}/evidence/report-manifest.json",
    f"{RUNREL}/evidence/implementation-result.json",
]


def load(path):
    return json.loads(path.read_bytes())


def runrel_paths(doc, key="records"):
    found = set()
    for rec in doc.get(key) or []:
        path = str(rec.get("path", ""))
        if path == RUNREL or path.startswith(RUNREL + "/"):
            found.add(path)
    return found


def script_sha():
    return hashlib.sha256((ROOT / SCRIPT_REL).read_bytes()).hexdigest()


def base_doc():
    return {
        "format": "RECOVERY_02_PLANNED_ADDITIONS_V1",
        "task_id": "TASK-20261011-line-baseline-recovery-02",
        "run_rel": RUNREL,
        "generator": {"path": SCRIPT_REL, "sha256": script_sha()},
    }


def main(argv):
    if len(argv) != 2 or argv[1] not in ("--initial", "--final"):
        raise SystemExit("usage: make_planned_additions.py --initial|--final")
    mode = argv[1]
    b1_paths = runrel_paths(load(B1))
    prewrite = load(PREWRITE)
    prewrite_paths = {str(r.get("path", "")) for r in prewrite.get("prewrite_runroot_records") or []}
    pre = sorted(b1_paths - prewrite_paths)
    if mode == "--initial":
        doc = base_doc()
        doc["pre_baseline_additions"] = pre
        doc["post_baseline_additions"] = []
        doc["post_preservation_tail_writes"] = TAIL
        doc["created_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        doc["initial_stats"] = {
            "pre_baseline_additions": len(pre),
            "baseline01_runrel_records": len(b1_paths),
            "prewrite_runroot_records": len(prewrite_paths),
            "baseline01_sha256": hashlib.sha256(B1.read_bytes()).hexdigest(),
        }
        data = (json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        if OUT.read_bytes() != data:
            raise SystemExit("READBACK_MISMATCH:" + str(OUT))
        print(json.dumps({"status": "OK", "mode": "initial", "pre_baseline_additions": len(pre),
                          "output_bytes": len(data), "output_sha256": hashlib.sha256(data).hexdigest()}, sort_keys=True))
        return 0
    p2_paths = runrel_paths(load(P2))
    post = sorted(p2_paths - b1_paths)
    existing = load(OUT)
    if sorted(existing.get("pre_baseline_additions") or []) != pre:
        raise SystemExit("PRE_BASELINE_ADDITIONS_DRIFT")
    doc = base_doc()
    doc["pre_baseline_additions"] = pre
    doc["post_baseline_additions"] = post
    doc["post_preservation_tail_writes"] = TAIL
    doc["finalized_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    doc["final_stats"] = {
        "post_baseline_additions": len(post),
        "preservation02_runrel_records": len(p2_paths),
        "preservation02_sha256": hashlib.sha256(P2.read_bytes()).hexdigest(),
    }
    data = (json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with open(OUT, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if OUT.read_bytes() != data:
        raise SystemExit("READBACK_MISMATCH:" + str(OUT))
    print(json.dumps({"status": "OK", "mode": "final", "post_baseline_additions": len(post),
                      "tail_writes": len(TAIL), "output_bytes": len(data),
                      "output_sha256": hashlib.sha256(data).hexdigest()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
