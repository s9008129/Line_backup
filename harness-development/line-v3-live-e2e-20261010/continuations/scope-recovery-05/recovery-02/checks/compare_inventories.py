#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Recovery-02 fixed-input inventory comparisons.

Modes (all inputs/outputs fixed; no arbitrary paths):
  baseline-consistency : inventory-baseline-01 vs -02
  bootstrap-delta      : bootstrap-prewrite-runroot-v2 prewrite records vs
                         inventory-baseline-01, restricted to RUNREL
  historical           : scope-recovery-05/.local/preexisting-files.json vs
                         inventory-baseline-01 (projected to fields the old
                         manifest really has; uncovered paths are coverage gaps)
  preservation         : inventory-preservation-01 vs -02 consistency and
                         inventory-baseline-01 vs inventory-preservation-02 delta

Rules:
- a comparison is BLOCKED if either inventory is incomplete, timed out, or
  policy-blocked; no delta conclusion may be drawn from a partial scan
- added/removed/changed paths must be inside the explicitly allowed sets
- directory content identity = mode/dev/ino/uid/gid + the entry list: entry
  changes are tolerated only when exactly explained by direct-child
  additions/removals, and directory mtime/ctime/size/nlink drift (e.g. approved
  fixture create/delete cycles) is never compared or treated as a change
- projection mode compares only fields present in both records

Writes exactly one exclusive output: RUNROOT/evidence/compare-<mode>.json
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
RUNROOT = ROOT / RUNREL
EVIDENCE = RUNROOT / "evidence"

INV_B1 = EVIDENCE / "inventory-baseline-01.json"
INV_B2 = EVIDENCE / "inventory-baseline-02.json"
INV_P1 = EVIDENCE / "inventory-preservation-01.json"
INV_P2 = EVIDENCE / "inventory-preservation-02.json"
PREWRITE = EVIDENCE / "bootstrap-prewrite-runroot-v2.json"
PLANNED = EVIDENCE / "planned-additions.json"
HISTORIC = (
    ROOT
    / "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/.local/preexisting-files.json"
)
HISTORIC_SHA = "b115df6ea55e3a985e98651018e742769b02e6f7854989e68f8d7214680832f2"

FORMAT = "RECOVERY_02_COMPARE_V1"
MODES = ("baseline-consistency", "bootstrap-delta", "historical", "preservation")
SELF_OUTPUTS = {
    f"{RUNREL}/evidence/inventory-baseline-01.json",
    f"{RUNREL}/evidence/inventory-baseline-02.json",
    f"{RUNREL}/evidence/inventory-preservation-01.json",
    f"{RUNREL}/evidence/inventory-preservation-02.json",
}
# Directory identity/content fields that are compared on every path. Directory
# mtime/ctime/size/nlink track entry churn and are intentionally excluded.
_DIR_FIELDS = ("mode", "dev", "ino", "uid", "gid")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ref_of(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "absolute_path": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def _write_exclusive(path: pathlib.Path, data: bytes) -> dict:
    fd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        wfd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(wfd, view):]
            os.fsync(wfd)
        finally:
            os.close(wfd)
        rfd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            chunks = []
            while True:
                chunk = os.read(rfd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(rfd)
        readback = b"".join(chunks)
    finally:
        os.close(fd)
    if readback != data:
        raise RuntimeError(f"WRITE_READBACK_MISMATCH:{path}")
    return {"path": path.relative_to(ROOT).as_posix(), "absolute_path": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def usable(doc: dict) -> tuple[bool, list[str]]:
    reasons = []
    if doc.get("complete") is not True:
        reasons.append("INVENTORY_NOT_COMPLETE")
    if doc.get("timeout") is True:
        reasons.append("INVENTORY_TIMEOUT")
    if not (doc.get("policy") or {}).get("ok"):
        reasons.append("INVENTORY_POLICY_BLOCKED")
    return (not reasons), reasons


def index_records(records: list[dict]) -> dict[str, dict]:
    by: dict[str, dict] = {}
    for record in records:
        path = record.get("path")
        if path in by:
            raise ValueError(f"DUPLICATE_RECORD:{path}")
        by[path] = record
    return by


def _kind(record: dict) -> str:
    return record.get("kind", "UNKNOWN")


def compare_docs(
    base: dict,
    post: dict,
    *,
    label: str,
    allowed_additions: set[str] = frozenset(),
    allowed_removals: set[str] = frozenset(),
    projection: bool = False,
    domain_prefix: str | None = None,
) -> dict:
    base_ok, base_reasons = usable(base)
    post_ok, post_reasons = usable(post)
    result: dict = {
        "label": label,
        "status": "BLOCKED",
        "blocked_reasons": [],
        "failures": [],
        "added": [],
        "removed": [],
        "changed": [],
        "directory_explained": [],
    }
    if not base_ok:
        result["blocked_reasons"] += [f"base:{reason}" for reason in base_reasons]
    if not post_ok:
        result["blocked_reasons"] += [f"post:{reason}" for reason in post_reasons]
    if result["blocked_reasons"]:
        return result

    old = index_records(base.get("records", []))
    new = index_records(post.get("records", []))
    if domain_prefix:
        old = {p: r for p, r in old.items() if p == domain_prefix or p.startswith(domain_prefix + "/")}
        new = {p: r for p, r in new.items() if p == domain_prefix or p.startswith(domain_prefix + "/")}

    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    result["added"] = added
    result["removed"] = removed
    for path in added:
        if path not in allowed_additions:
            result["failures"].append({"code": "ADDED_NOT_ALLOWED", "path": path})
    for path in removed:
        if path not in allowed_removals:
            result["failures"].append({"code": "REMOVED_NOT_ALLOWED", "path": path})

    added_set, removed_set = set(added), set(removed)
    for path in sorted(set(old) & set(new)):
        old_rec, new_rec = old[path], new[path]
        if _kind(old_rec) != _kind(new_rec):
            result["failures"].append({"code": "KIND_CHANGED", "path": path, "old": _kind(old_rec), "new": _kind(new_rec)})
            continue
        kind = _kind(old_rec)
        if kind == "DIRECTORY":
            if not (projection and "entries" not in old_rec):
                old_entries, new_entries = set(old_rec.get("entries", [])), set(new_rec.get("entries", []))
                if old_entries != new_entries:
                    expected = {
                        p.rsplit("/", 1)[1]
                        for p in (added_set | removed_set)
                        if p.rsplit("/", 1)[0] == path
                    }
                    if (old_entries ^ new_entries) == expected and (old_entries ^ new_entries):
                        for key in _DIR_FIELDS:
                            if key in old_rec and key in new_rec and old_rec[key] != new_rec[key]:
                                result["failures"].append({"code": "DIR_FIELD_MISMATCH", "path": path, "field": key})
                        result["directory_explained"].append({"path": path, "entries_delta": sorted(old_entries ^ new_entries)})
                        continue
                    result["failures"].append(
                        {"code": "UNEXPLAINED_ENTRY_DELTA", "path": path, "old": sorted(old_entries), "new": sorted(new_entries)}
                    )
                    continue
            fields = [k for k in _DIR_FIELDS if k in old_rec and k in new_rec]
        else:
            fields = [k for k in old_rec.keys() if k in new_rec and k != "path"]
        mismatch_fields = [k for k in fields if old_rec.get(k) != new_rec.get(k)]
        if mismatch_fields:
            result["changed"].append({"path": path, "fields": mismatch_fields, "old": {k: old_rec.get(k) for k in mismatch_fields}, "new": {k: new_rec.get(k) for k in mismatch_fields}})
            for key in mismatch_fields:
                result["failures"].append({"code": "FIELD_MISMATCH", "path": path, "field": key})
    if not result["failures"]:
        result["status"] = "PASS"
    else:
        result["status"] = "FAIL"
    return result


def load_json(path: pathlib.Path) -> dict | list:
    return json.loads(path.read_bytes())


def _emit(mode: str, doc: dict) -> int:
    out = EVIDENCE / f"compare-{mode}.json"
    if os.path.lexists(out):
        print(json.dumps({"status": "REFUSED", "errors": [f"ID_COLLISION:{out}"]}))
        return 2
    doc = dict(doc)
    doc["created_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    doc["format"] = FORMAT
    data = (json.dumps(doc, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")
    ref = _write_exclusive(out, data)
    doc["output"] = ref
    print(json.dumps({"mode": mode, "status": doc.get("status"), "failures": len(doc.get("failures", [])), "blocked_reasons": len(doc.get("blocked_reasons", [])), "output": ref}, ensure_ascii=True, sort_keys=True))
    return 0 if doc.get("status") == "PASS" else 1


def mode_baseline_consistency() -> int:
    b1, b2 = load_json(INV_B1), load_json(INV_B2)
    cmp_result = compare_docs(b1, b2, label="baseline-consistency", allowed_additions=set(SELF_OUTPUTS))
    doc = {
        "mode": "baseline-consistency",
        "status": cmp_result["status"],
        "inputs": {"inventory-01": ref_of(INV_B1), "inventory-02": ref_of(INV_B2)},
        "blocked_reasons": cmp_result["blocked_reasons"],
        "failures": cmp_result["failures"],
        "added": cmp_result["added"],
        "removed": cmp_result["removed"],
        "changed": cmp_result["changed"],
        "directory_explained": cmp_result["directory_explained"],
        "counts": {"inventory-01": b1.get("counts"), "inventory-02": b2.get("counts")},
    }
    return _emit("baseline-consistency", doc)


def mode_bootstrap_delta() -> int:
    prewrite = load_json(PREWRITE)
    b1 = load_json(INV_B1)
    planned = load_json(PLANNED)
    allowed = set(planned.get("pre_baseline_additions", []))
    old = {"records": prewrite.get("prewrite_runroot_records", []), "complete": True, "timeout": False, "policy": {"ok": True}}
    cmp_result = compare_docs(old, b1, label="bootstrap-delta", allowed_additions=allowed, projection=True, domain_prefix=RUNREL)
    missing_planned = sorted(p for p in allowed if p not in {r["path"] for r in b1.get("records", [])})
    failures = list(cmp_result["failures"])
    if missing_planned:
        failures.append({"code": "PLANNED_ADDITION_MISSING", "paths": missing_planned})
    doc = {
        "mode": "bootstrap-delta",
        "status": "BLOCKED" if cmp_result["status"] == "BLOCKED" else ("PASS" if not failures else "FAIL"),
        "inputs": {"prewrite": ref_of(PREWRITE), "inventory-01": ref_of(INV_B1), "planned-additions": ref_of(PLANNED)},
        "blocked_reasons": cmp_result["blocked_reasons"],
        "failures": failures,
        "added": cmp_result["added"],
        "removed": cmp_result["removed"],
        "changed": cmp_result["changed"],
        "directory_explained": cmp_result["directory_explained"],
        "domain_prefix": RUNREL,
    }
    return _emit("bootstrap-delta", doc)


def mode_historical() -> int:
    historic_ref = ref_of(HISTORIC)
    if historic_ref["sha256"] != HISTORIC_SHA:
        doc = {
            "mode": "historical",
            "status": "FAIL",
            "inputs": {"historic": historic_ref},
            "failures": [{"code": "HISTORIC_MANIFEST_HASH_MISMATCH", "expected": HISTORIC_SHA, "actual": historic_ref["sha256"]}],
            "blocked_reasons": [],
        }
        return _emit("historical", doc)
    historic = load_json(HISTORIC)
    b1 = load_json(INV_B1)
    b1_ok, b1_reasons = usable(b1)
    if not b1_ok:
        return _emit("historical", {"mode": "historical", "status": "BLOCKED", "blocked_reasons": b1_reasons, "inputs": {"inventory-01": ref_of(INV_B1), "historic": historic_ref}})
    old_index = {r["path"]: r for r in historic}
    new_index = index_records(b1.get("records", []))
    new_index = {p: r for p, r in new_index.items() if p != RUNREL and not p.startswith(RUNREL + "/")}
    failures = []
    missing = sorted(set(old_index) - set(new_index))
    for path in missing:
        failures.append({"code": "HISTORICAL_PATH_MISSING", "path": path})
    changed = []
    entry_extensions = []
    for path in sorted(set(old_index) & set(new_index)):
        old_rec, new_rec = old_index[path], new_index[path]
        if old_rec.get("kind") != new_rec.get("kind"):
            failures.append({"code": "HISTORICAL_KIND_CHANGED", "path": path, "old": old_rec.get("kind"), "new": new_rec.get("kind")})
            continue
        if old_rec.get("kind") == "DIRECTORY":
            old_entries, new_entries = set(old_rec.get("entries", [])), set(new_rec.get("entries", []))
            lost = old_entries - new_entries
            if lost:
                failures.append({"code": "HISTORICAL_DIR_ENTRY_LOST", "path": path, "entries": sorted(lost)})
            extra = new_entries - old_entries
            for name in sorted(extra):
                child = f"{path}/{name}"
                if child in old_index:
                    failures.append({"code": "HISTORICAL_DIR_ENTRY_UNEXPECTED", "path": path, "entry": name})
                else:
                    entry_extensions.append(child)
                    failures.append({"code": "HISTORICAL_DIR_ENTRY_EXTENSION", "path": path, "entry": name})
            if old_rec.get("mode") != new_rec.get("mode"):
                failures.append({"code": "HISTORICAL_DIR_MODE_MISMATCH", "path": path})
            continue
        for key in ("sha256", "mode"):
            if key in old_rec and old_rec.get(key) != new_rec.get(key):
                failures.append({"code": "HISTORICAL_FIELD_MISMATCH", "path": path, "field": key})
        if old_rec.get("kind") == "REGULAR" and "bytes" in old_rec and old_rec.get("bytes") != new_rec.get("bytes"):
            failures.append({"code": "HISTORICAL_FIELD_MISMATCH", "path": path, "field": "bytes"})
        if old_rec.get("kind") == "SYMLINK" and old_rec.get("target") != new_rec.get("target"):
            failures.append({"code": "HISTORICAL_FIELD_MISMATCH", "path": path, "field": "target"})
    coverage_gaps = {"REGULAR": [], "SYMLINK": [], "DIRECTORY": [], "FIFO": [], "OTHER_SPECIAL": []}
    for path, rec in new_index.items():
        if path in old_index:
            continue
        coverage_gaps.setdefault(rec.get("kind", "OTHER"), []).append(path)
    runroot_gap = sorted(p for p in coverage_gaps.get("REGULAR", []) + coverage_gaps.get("DIRECTORY", []) if p == RUNREL or p.startswith(RUNREL + "/"))
    coverage_summary = {k: {"count": len(v), "sample": v[:20]} for k, v in coverage_gaps.items() if v}
    doc = {
        "mode": "historical",
        "status": "PASS" if not failures else "FAIL",
        "inputs": {"inventory-01": ref_of(INV_B1), "historic": historic_ref},
        "blocked_reasons": [],
        "failures": failures,
        "missing_count": len(missing),
        "changed_count": len(changed),
        "changed": changed,
        "directory_entry_extensions_count": len(entry_extensions),
        "directory_entry_extensions_sample": entry_extensions[:20],
        "coverage_gap_counts": {k: len(v) for k, v in coverage_gaps.items() if v},
        "coverage_gaps": coverage_summary,
        "runroot_coverage_gap_present": bool(runroot_gap),
        "historic_record_count": len(historic),
        "current_external_record_count": len(new_index),
        "note": "uncovered paths are HISTORICAL_COVERAGE_GAP, never attestations; covered fields (regular sha256/bytes/mode, symlink target/sha256/mode, directory entries/mode subset rule) must match",
    }
    return _emit("historical", doc)


def mode_preservation() -> int:
    b1, p1, p2 = load_json(INV_B1), load_json(INV_P1), load_json(INV_P2)
    planned = load_json(PLANNED)
    post_allowed = set(planned.get("post_baseline_additions", []))
    tail = set(planned.get("post_preservation_tail_writes", []))
    consistency = compare_docs(p1, p2, label="preservation-consistency", allowed_additions=set(SELF_OUTPUTS))
    delta = compare_docs(b1, p2, label="baseline->preservation-02", allowed_additions=post_allowed | set(SELF_OUTPUTS))
    p2_paths = {r["path"] for r in p2.get("records", [])}
    missing_planned = sorted(p for p in post_allowed if p not in p2_paths)
    premature_tail = sorted(p for p in tail if p in p2_paths)
    failures = list(delta["failures"]) + list(consistency["failures"])
    if missing_planned:
        failures.append({"code": "PLANNED_POST_ADDITION_MISSING", "paths": missing_planned})
    if premature_tail:
        failures.append({"code": "TAIL_WRITE_PRESENT_BEFORE_PRESERVATION_SCAN", "paths": premature_tail})
    status = "BLOCKED" if (consistency["status"] == "BLOCKED" or delta["status"] == "BLOCKED") else ("PASS" if not failures else "FAIL")
    doc = {
        "mode": "preservation",
        "status": status,
        "inputs": {"inventory-baseline-01": ref_of(INV_B1), "inventory-preservation-01": ref_of(INV_P1), "inventory-preservation-02": ref_of(INV_P2), "planned-additions": ref_of(PLANNED)},
        "blocked_reasons": consistency["blocked_reasons"] + delta["blocked_reasons"],
        "consistency": {k: consistency[k] for k in ("status", "failures", "added", "removed", "changed", "directory_explained")},
        "delta": {k: delta[k] for k in ("status", "failures", "added", "removed", "changed", "directory_explained")},
        "failures": failures,
        "consistency_failures": consistency["failures"],
        "post_baseline_additions_expected": sorted(post_allowed),
        "tail_writes_declared": sorted(tail),
    }
    return _emit("preservation", doc)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in MODES:
        print(json.dumps({"status": "REFUSED", "errors": ["usage: compare_inventories.py baseline-consistency|bootstrap-delta|historical|preservation"]}))
        return 2
    if pathlib.Path.cwd() != ROOT:
        print(json.dumps({"status": "REFUSED", "errors": [f"WRONG_CWD:{pathlib.Path.cwd()}"]}))
        return 2
    mode = argv[1]
    if mode == "baseline-consistency":
        return mode_baseline_consistency()
    if mode == "bootstrap-delta":
        return mode_bootstrap_delta()
    if mode == "historical":
        return mode_historical()
    return mode_preservation()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
