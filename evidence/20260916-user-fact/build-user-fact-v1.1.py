#!/usr/bin/env python3
"""Stage-04 §19.1: deterministic, fail-closed construction of the corrected user-fact record v1.1.

Reads the frozen v1 record, applies exactly one string-leaf correction
(answer.part_2.confirmed_album: long form -> canonical short label, U+FF5E kept),
asserts the expected size and SHA-256 BEFORE writing, and refuses to write on any
mismatch. The v1 record and the gate artifact are never modified.

Usage: build_v1_1.py [--dry-run] [--out PATH]   (default OUT = the repo path in the plan)
"""
import argparse
import hashlib
import json
import os
import sys

V1 = "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260916-user-fact/source-identity-user-fact.confirmed.v1.json"
DEFAULT_OUT = "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260916-user-fact/source-identity-user-fact.confirmed.v1.1.json"
V1_SHA = "2cd7eccdb99da5dc"  # prefix only; full SHA asserted below
V1_SHA_FULL = None
OLD = '"confirmed_album": "2024/05/13～2024/05/17"'
NEW = '"confirmed_album": "2024/05/13～05/17"'
EXPECT_BYTES = 1741
EXPECT_SHA = "a8c1055137d14026f7ecbc15b4f06ee540b56114af3276b081a0be72d195c263"
GATE = "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260916-user-fact/human-gate-answer-20260917.json"
GATE_BYTES = 1438
GATE_SHA = "03ffff57d50a5f97e596749dfa6bbde50b5ab50253c1f34469cc896e89ef57f7"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def fail(msg):
    print("FAIL_CLOSED: " + msg, file=sys.stderr)
    raise SystemExit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    raw = open(V1, "rb").read()
    v1_sha = sha256_bytes(raw)
    text = raw.decode("utf-8")

    if text.count(OLD) != 1:
        fail(f"v1 must contain the long-form confirmed_album leaf exactly once (found {text.count(OLD)})")
    v1_obj = json.loads(text)
    out_text = text.replace(OLD, NEW)
    out_raw = out_text.encode("utf-8")

    # ---- pre-write assertions on the candidate bytes ----
    if len(out_raw) != EXPECT_BYTES:
        fail(f"candidate bytes {len(out_raw)} != expected {EXPECT_BYTES}")
    cand_sha = sha256_bytes(out_raw)
    if cand_sha != EXPECT_SHA:
        fail(f"candidate sha256 {cand_sha} != expected {EXPECT_SHA}")

    out_obj = json.loads(out_text)
    if set(out_obj) != set(v1_obj):
        fail("key set changed at top level")
    if set(out_obj["answer"]) != set(v1_obj["answer"]) or set(out_obj["answer"]["part_2"]) != set(v1_obj["answer"]["part_2"]):
        fail("key set changed below answer")
    if out_obj["record_version"] != "1.0":
        fail("record_version changed")
    for path in (("kind",), ("status",), ("source_correspondence_result",), ("merge_prohibited",),
                 ("app_identifier",), ("raw_requested_group",), ("raw_persisted_group",),
                 ("supplied_by",), ("recorded_at_local",), ("answer", "raw"),
                 ("answer", "part_2", "text"), ("question", "text")):
        a, b = v1_obj, out_obj
        for key in path:
            a, b = a[key], b[key]
        if a != b:
            fail(f"unexpected change at {'.'.join(path)}")
    if out_obj["fingerprint"] != v1_obj["fingerprint"] or out_obj["evidence"] != v1_obj["evidence"]:
        fail("fingerprint or evidence changed")
    if out_obj["answer"]["part_2"]["confirmed_album"] != "2024/05/13～05/17":
        fail("confirmed_album is not the canonical short label")
    if "～" not in out_obj["answer"]["part_2"]["confirmed_album"] or "\uff5e" not in out_obj["answer"]["part_2"]["confirmed_album"]:
        fail("U+FF5E not preserved")
    # line diff: exactly one changed line
    diff_lines = [(i, a, b) for i, (a, b) in enumerate(zip(text.splitlines(), out_text.splitlines())) if a != b]
    if len(diff_lines) != 1:
        fail(f"expected exactly one changed line, got {len(diff_lines)}")

    ev = out_obj["evidence"][0]
    ev_raw = open(ev["path"], "rb").read()
    if len(ev_raw) != ev["bytes"] or sha256_bytes(ev_raw) != ev["sha256"]:
        fail("evidence entry does not re-hash to its recorded bytes/sha256")
    gate_raw = open(GATE, "rb").read()
    if len(gate_raw) != GATE_BYTES or sha256_bytes(gate_raw) != GATE_SHA:
        fail("gate artifact bytes/sha differ from the frozen expectation")

    report = {
        "v1_path": V1, "v1_bytes": len(raw), "v1_sha256": v1_sha,
        "out_path": args.out, "out_bytes": len(out_raw), "out_sha256": cand_sha,
        "single_changed_line": {"line_no_1based": diff_lines[0][0] + 1,
                                "old": diff_lines[0][1], "new": diff_lines[0][2]},
        "gate_bytes": len(gate_raw), "gate_sha256": sha256_bytes(gate_raw),
        "evidence_rehash_ok": True, "dry_run": args.dry_run,
    }
    print(json.dumps(report, ensure_ascii=False, indent=1))

    if args.dry_run:
        return 0
    if os.path.exists(args.out):
        fail(f"refusing to overwrite existing {args.out}")
    with open(args.out, "wb") as f:
        f.write(out_raw)
    written = open(args.out, "rb").read()
    if sha256_bytes(written) != EXPECT_SHA or len(written) != EXPECT_BYTES:
        fail("post-write re-read mismatch")
    print("WROTE " + args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
