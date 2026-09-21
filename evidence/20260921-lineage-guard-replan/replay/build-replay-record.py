#!/usr/bin/env python3
"""Assemble the Rev27b offline replay record from the v7 selftest outputs.

Read-only over the selftest outputs; copies the key per-case guard outputs into
replay/out/ and writes replay-record.json. Deterministic (no timestamps).
"""
import hashlib
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(ROUND))
SELFTEST = os.path.join(REPO, "evidence", "20260916-route", "tools", "v7",
                        "selftest")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


with open(os.path.join(SELFTEST, "results.json"), "r", encoding="utf-8") as f:
    results = json.load(f)

by_name = {c["name"]: c for c in results["cases"]}

REPLAYS = [
    ("attempt-12-pre-click", "neg-attempt-12-pre-strict",
     "must REFUSE (expected: attempt-12 pre-click is the album list)"),
    ("attempt-12-post-click-strict", "neg-attempt-12-post-strict-ax-diff-form",
     "REFUSED under the strict contract: the saved same-round CU state is a diff "
     "form, not a full tree (evidence-shape gap; the surface itself is bridged below)"),
    ("attempt-12-post-click-bridged", "pos-attempt-12-post-bridged",
     "VERIFIED via the documented bridge: window screenshot byte-identical to the "
     "attempt-13 detail read, frame-post binds at MAD 2.259"),
    ("attempt-12-post-click-composite-bridged", "pos-attempt-12-composite-bridged",
     "VERIFIED + composite PASS (frozen attempt-12 verdict bound to frame-post)"),
    ("attempt-13-album-detail", "pos-attempt-13-detail-strict",
     "VERIFIED (same-round inventory/state/shot/frame)"),
    ("attempt-03-regression-with-frozen-verdict",
     "neg-attempt-03-regression-frozen-verdict",
     "must REFUSE even though the frozen verifier says ALBUM_OPEN_VERIFIED; "
     "composite must never PASS"),
    ("attempt-03-count57-no-detail", "neg-attempt-03-count57-no-detail",
     "must REFUSE (57 visible on the list surface, no detail window)"),
]

record = {
    "artifact": "Rev27b offline replay record (no GUI input, existing evidence only)",
    "source_results": {
        "path": "evidence/20260916-route/tools/v7/selftest/results.json",
        "sha256": sha256_file(os.path.join(SELFTEST, "results.json")),
        "guard_sha256": results["guard"]["sha256"],
    },
    "replays": [],
    "attempt_03_sweep": results["attempt_03_sweep"],
    "determinism": results["determinism"],
}

for label, case_name, expectation in REPLAYS:
    case = by_name[case_name]
    src = os.path.join(SELFTEST, "out", case_name + ".json")
    dst = os.path.join(OUT, label + ".json")
    shutil.copyfile(src, dst)
    record["replays"].append({
        "replay": label,
        "case": case_name,
        "expectation": expectation,
        "expected": case["expected"],
        "actual": case["actual"],
        "pass": case["pass"],
        "guard_output": {
            "path": "evidence/20260921-lineage-guard-replan/replay/out/" + label + ".json",
            "sha256": sha256_file(dst),
        },
    })

record["verdict"] = ("REPLAY_PASS" if all(r["pass"] for r in record["replays"])
                     and results["attempt_03_sweep"]["no_combo_verified"]
                     and results["determinism"]["repeat_byte_identical"]
                     else "REPLAY_FAIL")

with open(os.path.join(HERE, "replay-record.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False, indent=1) + "\n")
print(json.dumps({"verdict": record["verdict"],
                  "replays": [(r["replay"], r["actual"]["verdict"],
                               r["actual"]["exit_code"], r["actual"]["composite"])
                              for r in record["replays"]]}, ensure_ascii=False, indent=1))
