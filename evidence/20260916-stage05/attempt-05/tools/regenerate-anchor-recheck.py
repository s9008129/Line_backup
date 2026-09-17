#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot pre-commit correction of anchors/anchor-recheck.json (Stage-05 attempt-05).

Why this exists
---------------
The first generation of `anchors/anchor-recheck.json` (file SHA-256
`2189a10d69a24d30dbba641e83af523da01d0ec42b75f5987af79442de53fe2d`, 9,824 bytes,
never committed) recorded *incomplete* expectation values for four anchors:

  config       expected_sha256_prefix = "390cbdcf??"   (placeholder), expected_bytes present
  state        expected_bytes = null, expected_sha256_prefix = null
  run_log      expected_bytes = null, expected_sha256_prefix = null
  locator_tool expected_bytes = null

so those anchors reported `sha_match=false` (state/run_log/config) or asserted the
SHA only (locator_tool) even though every observed byte length and SHA-256 was
byte-identical to the durable record.  This tool re-observes all 18 anchors plus the
destination inventory and the §16.4 v1 contract table, fills every expectation from
the durable record, and rewrites the artifact with a `regeneration` provenance block
naming the prior file hash.  It is fail-closed: any observation that no longer equals
the first-pass value aborts the rewrite, and every expectation must be verifiable in
at least one named durable source before anything is written.

Scope: reads anchors + destination inventory + product matcher code; writes only
`anchors/anchor-recheck.json`.  It never writes formal config/state/run_log, product
code, plan/handoff/execution, evidence from other attempts, or the 57 photos.
`manifest.json` is rewritten separately, after this tool succeeds.
"""

import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
ARTIFACT = REPO / "evidence/20260916-stage05/attempt-05/anchors/anchor-recheck.json"

# Durable-record expectations.  sha = full 64-hex recorded SHA-256; bytes = recorded
# byte length; sources = files that must literally contain the SHA (and, in at least
# one of them, the byte length) before any rewrite happens.
EXPECTATION_FIXES = {
    "config": {
        "sha": "390cbdcf36a88c9f134c0ecb29d39018ebadf42babfb7a264a741337499d3b3b",
        "bytes": 372,
        "sources": ["handoff.md", "evidence/20260916-baseline/attempt-02/baseline-pre.json"],
    },
    "state": {
        "sha": "e9313a563bf298d4b1e9ae243c5d3d404ad1333f69cb71b156e68589a8ec2f59",
        "bytes": 48146,
        "sources": ["handoff.md", "evidence/20260916-baseline/attempt-02/baseline-pre.json"],
    },
    "run_log": {
        "sha": "a62dd07d1df1a34fb91a11d6eec6ac8aae7146abf9eb7011b78b1d27914158bf",
        "bytes": 15950,
        "sources": ["handoff.md", "evidence/20260916-baseline/attempt-02/baseline-pre.json"],
    },
    "locator_tool": {
        "sha": "8c8b6fc704c09a476419492eef2cd999e472126312feff72093f2cfef715df9e",
        "bytes": 8943,
        "sources": ["evidence/20260916-route/attempt-03/pre-run-wait-observation-07.json",
                    "evidence/20260916-route/attempt-03/route-runbook.md"],
    },
}

APP_IDENTIFIER = "jp.naver.line.mac"
GROUP_STRING = "旻謙允禎成長日記"
FP = {"start_date": "2024-05-13", "end_date": "2024-05-17", "expected_images": 57}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(msg: str) -> "None":
    raise SystemExit("FAIL-CLOSED: " + msg)


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def main() -> int:
    prior_raw = ARTIFACT.read_bytes()
    doc = json.loads(prior_raw.decode("utf-8"))
    prior = {"sha256": sha256_bytes(prior_raw), "bytes": len(prior_raw)}

    # 1. Every expectation we apply must be present in its named durable sources.
    for name, fix in sorted(EXPECTATION_FIXES.items()):
        bytes_seen = False
        for rel in fix["sources"]:
            text = (REPO / rel).read_text(encoding="utf-8")
            if fix["sha"] not in text:
                fail(f"{fix['sha']} (expected {name}) not found in durable source {rel}")
            if (f'"bytes": {fix["bytes"]}' in text
                    or f"{fix['bytes']} bytes" in text
                    or f"{fix['bytes']:,} bytes" in text):
                bytes_seen = True
        if not bytes_seen:
            fail(f"recorded byte length for {name} not found in any durable source")

    # 2. Re-observe every anchor; abort if any first-pass observation changed.
    anchors = doc["anchors"]
    prior_anchor_sha = {n: e["expected_sha256_prefix"] for n, e in anchors.items()}
    prior_anchor_bytes = {n: e["expected_bytes"] for n, e in anchors.items()}
    prior_anchor_match = {n: e["sha_match"] for n, e in anchors.items()}
    for name, entry in sorted(anchors.items()):
        path = Path(entry["path"])
        if not path.is_file():
            fail(f"anchor {name} missing on disk: {path}")
        data = path.read_bytes()
        sha, nbytes = sha256_bytes(data), len(data)
        if nbytes != entry["bytes"] or sha != entry["sha256"]:
            fail(f"anchor {name} changed since first pass: "
                 f"{nbytes}/{sha} != {entry['bytes']}/{entry['sha256']}")
        expected_sha = entry["expected_sha256_prefix"]
        expected_bytes = entry["expected_bytes"]
        if name in EXPECTATION_FIXES:
            expected_sha = EXPECTATION_FIXES[name]["sha"]
            expected_bytes = EXPECTATION_FIXES[name]["bytes"]
            entry["expected_sha256_prefix"] = expected_sha
            entry["expected_bytes"] = expected_bytes
        if expected_sha is None or expected_bytes is None:
            fail(f"anchor {name} has no verifiable expectation source")
        entry["sha_match"] = bool(sha == expected_sha if len(expected_sha) == 64
                                  else sha.startswith(expected_sha))
        entry["bytes_match"] = bool(expected_bytes == nbytes)
        if not (entry["sha_match"] and entry["bytes_match"]):
            fail(f"anchor {name} does not match its recorded expectation")

    # 3. Destination inventory, re-observed from disk.
    #    Canonicalization of sorted_inventory_sha256 (recovered by reproducing the
    #    first pass): sha256 over "\n".join(f"{relative_path}\t{size}\t{sha256}" for
    #    entries sorted by relative_path) + trailing newline.
    dest = Path(doc["destination"]["path"])
    files = sorted(p for p in dest.rglob("*") if p.is_file())
    lines, total, zero = [], 0, 0
    for p in files:
        data = p.read_bytes()
        sha, nbytes = sha256_bytes(data), len(data)
        total += nbytes
        zero += 1 if nbytes == 0 else 0
        lines.append(f"{p.relative_to(dest).as_posix()}\t{nbytes}\t{sha}")
    observed = {
        "entry_count": len(files),
        "total_bytes": total,
        "zero_byte_files": zero,
        "sorted_inventory_sha256": sha256_bytes(("\n".join(lines) + "\n").encode("utf-8")),
    }
    for key, value in observed.items():
        if doc["destination"].get(key) != value:
            fail(f"destination {key} changed: {value} != {doc['destination'].get(key)}")

    # 4. Re-run the §16.4 v1 contract table against the frozen product matcher.
    sys.path.insert(0, str(REPO / "src"))
    from line_backup_acceptance.common import user_fact_v1_matches, _rehash_evidence_entries  # noqa: E402

    record_path = REPO / "evidence/20260916-user-fact/source-identity-user-fact.confirmed.v1.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    group_key = "line:" + APP_IDENTIFIER + ":" + GROUP_STRING
    album_label = FP["start_date"].replace("-", "/") + "～" + FP["end_date"][5:].replace("-", "/")
    part2 = record["answer"]["part_2"]
    conditions = {
        "answer_raw_nonempty": bool(str(record["answer"].get("raw", "")).strip()),
        "app_identifier": record.get("app_identifier") == APP_IDENTIFIER,
        "evidence_rehash": _rehash_evidence_entries(record.get("evidence")),
        "fingerprint_equal": record.get("fingerprint") == FP,
        "kind": record.get("kind") == "source_identity_user_fact",
        "merge_prohibited_true": record.get("merge_prohibited") is True,
        "part2_confirmed_album_equal": part2.get("confirmed_album") == album_label,
        "part2_confirmed_expected_images_equal": part2.get("confirmed_expected_images") == FP["expected_images"],
        "part2_confirmed_group_string_equal": part2.get("confirmed_group_string") == GROUP_STRING,
        "part2_confirms_same_source_true": part2.get("confirms_same_source") is True,
        "question_text_nonempty": bool(str(record["question"].get("text", "")).strip()),
        "raw_requested_group_join": "line:" + APP_IDENTIFIER + ":" + str(record.get("raw_requested_group")) == group_key,
        "record_version_is_1.0": record.get("record_version") == "1.0",
        "source_correspondence_result_CONFIRMED": record.get("source_correspondence_result") == "CONFIRMED",
        "status_CONFIRMED": record.get("status") == "CONFIRMED",
    }
    fixed = copy.deepcopy(record)
    fixed["answer"]["part_2"]["confirmed_album"] = album_label
    contract = {
        "album_label_expected_by_contract": album_label,
        "all_conditions_pass": all(conditions.values()),
        "conditions": conditions,
        "failed_conditions": sorted(k for k, v in conditions.items() if not v),
        "in_memory_single_field_correction_result": user_fact_v1_matches(
            fixed, app_identifier=APP_IDENTIFIER, group_key=group_key, fp=FP),
        "matcher_result": user_fact_v1_matches(record, app_identifier=APP_IDENTIFIER,
                                               group_key=group_key, fp=FP),
        "record_confirmed_album": part2.get("confirmed_album"),
    }
    prior_contract = doc["user_fact_v1_contract"]
    for key, value in contract.items():
        if prior_contract.get(key) != value:
            fail(f"§16.4 contract field {key} changed: {value} != {prior_contract.get(key)}")

    # 5. Rewrite with the corrected expectations and a provenance block.
    changes = {}
    for name, fix in EXPECTATION_FIXES.items():
        before = {"sha": prior_anchor_sha.get(name), "bytes": prior_anchor_bytes.get(name),
                  "match": prior_anchor_match.get(name)}
        changes[name] = {
            "expected_bytes": [before["bytes"], fix["bytes"]],
            "expected_sha256_prefix": [before["sha"], fix["sha"]],
            "sha_match": [before["match"], True],
        }
    doc["regeneration"] = {
        "anchor_field_changes": changes,
        "expectation_sources": sorted({rel for fix in EXPECTATION_FIXES.values()
                                       for rel in fix["sources"]}),
        "observed_values_unchanged": True,
        "prior_sha256": prior["sha256"],
        "prior_bytes": prior["bytes"],
        "reason": ("First generation recorded incomplete expectations for four anchors "
                   "(config placeholder '390cbdcf??'; state/run_log null; locator_tool bytes "
                   "null) and therefore reported sha_match=false for three anchors despite "
                   "byte-identical observations. Regenerated pre-commit (append-only applies to "
                   "committed history) with durable-record expectations; every observation "
                   "re-derived identical."),
        "regenerated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "regeneration_tool": "evidence/20260916-stage05/attempt-05/tools/regenerate-anchor-recheck.py",
    }
    if doc["checked_at_utc"] != "2026-09-17T05:29:42.726830Z":
        fail("first-pass checked_at_utc changed unexpectedly")
    dump(ARTIFACT, doc)

    new_raw = ARTIFACT.read_bytes()
    print(json.dumps({"all_anchors_match": all(a["sha_match"] and a["bytes_match"]
                                               for a in anchors.values()),
                      "anchors": len(anchors),
                      "contract_all_pass": contract["all_conditions_pass"],
                      "contract_failed": contract["failed_conditions"],
                      "destination_entries": observed["entry_count"],
                      "destination_total_bytes": observed["total_bytes"],
                      "new_bytes": len(new_raw),
                      "new_sha256": sha256_bytes(new_raw),
                      "prior_bytes": prior["bytes"],
                      "prior_sha256": prior["sha256"]},
                     indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
