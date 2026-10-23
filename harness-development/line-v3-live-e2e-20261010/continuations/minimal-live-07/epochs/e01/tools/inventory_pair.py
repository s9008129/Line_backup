#!/usr/bin/env python3
"""ML07 complete paired inventory with prewrite-anchor reconciliation."""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import stat
import subprocess
import sys
import time
import zlib

from evidence_io import publish_exclusive
from output_policy import OutputPolicy
from transaction_chain import validate_ledger_chain, validate_state_chain

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
R = ROOT / RUNREL
EPOCH = R / "epochs/e01"
SCANNER = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/tools/inventory.py"
FIFO_REL = "evidence/20260916-auto-verification/attempt-01/archive-phase1/private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo"
TASK_ID = "TASK-20261010-line-v3-live-e2e"
CAP = 128 * 1024 * 1024
PRODUCT_PATHS = {
    "scripts/line_backup_cua_adapter.mjs", "src/line_backup_batch/cli.py",
    "src/line_backup_batch/observations.py", "src/line_backup_batch/store.py",
    "rev28/Sources/rev28ctl/main.swift",
    "rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift",
    "rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift",
    "rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift",
    "rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift",
}
STATE = "state/backup_state.json"
LEDGER = "harness-development/line-v3-live-e2e-20261010/gui-ledger.json"
BACKUP = "backups/旻謙允禎成長日記"


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def command(*argv: str) -> bytes:
    return subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def scanner_module():
    spec = importlib.util.spec_from_file_location("ml07_frozen_readonly_scanner", SCANNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("SCANNER_IMPORT")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scan_once(scanner, slot: int) -> dict:
    start = time.monotonic()
    state = scanner.scan_tree(ROOT, fifo_abs=ROOT / FIFO_REL, allowlist_fifo=True, exclude_top_git=True, deadline_seconds=1200)
    return {"format": "ML07_INVENTORY_SCAN_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "slot": slot,
            "captured_at_utc": utc(), "elapsed_seconds": time.monotonic()-start,
            "complete": state.complete, "timeout": state.timeout, "errors": state.errors,
            "policy": state.policy, "records": state.records,
            "counts": {"total": len(state.records), "regular": sum(r.get("kind") == "REGULAR" for r in state.records)}}


def pair_compare(a: dict, b: dict) -> dict:
    if not a["complete"] or not b["complete"] or not a["policy"]["ok"] or not b["policy"]["ok"]:
        return {"verdict": "BLOCKED", "reason": "PARTIAL_TIMEOUT_OR_SPECIAL_POLICY", "added": [], "removed": [], "changed": []}
    first = {x["path"]: x for x in a["records"]}
    second = {x["path"]: x for x in b["records"]}
    added = sorted(second.keys()-first.keys()); removed = sorted(first.keys()-second.keys())
    changed = sorted(p for p in first.keys() & second.keys() if first[p] != second[p])
    return {"verdict": "PASS" if not (added or removed or changed) else "BLOCKED", "reason": "IDENTICAL_COMPLETE_PAIR" if not (added or removed or changed) else "WORKSPACE_CHANGED_DURING_PAIR", "added": added, "removed": removed, "changed": changed}


def _kind(rec: dict) -> str:
    return {"D": "DIRECTORY", "F": "REGULAR", "L": "SYMLINK", "S": "SPECIAL"}.get(rec[1], "SPECIAL")


def _children(paths: set[str], directory: str) -> set[str]:
    prefix = directory + "/" if directory else ""
    return {p[len(prefix):].split("/", 1)[0] for p in paths if p.startswith(prefix) and p != directory}


def _authorized_bootstrap_delta(policy: OutputPolicy, before: dict, after: dict, path: str, operation: str, *, product: bool = False) -> tuple[bool, str]:
    rule = policy.rule_for(path)
    if not rule:
        return False, "UNKNOWN_BOOTSTRAP_PATH"
    if not path.startswith(RUNREL + "/") and not (product and path in PRODUCT_PATHS):
        return False, "BOOTSTRAP_OUTSIDE_R"
    if rule["lifecycle"] not in ("CREATE_ONCE", "DRAFT_BEFORE_FREEZE", "PRODUCER_SCRATCH"):
        return False, "BOOTSTRAP_LIFECYCLE"
    expected = after or before
    kind = _kind(expected) if isinstance(expected, list) else expected.get("kind")
    if kind != rule["entry_type"]:
        return False, "BOOTSTRAP_TYPE"
    if operation == "MODIFY" and rule["lifecycle"] != "DRAFT_BEFORE_FREEZE":
        return False, "BOOTSTRAP_MODIFY_NON_DRAFT"
    phase = rule["allowed_phase"][0]
    def disk_ref(rel: str | None) -> dict | None:
        if not rel:
            return None
        p = ROOT / rel
        if not p.is_file() or p.is_symlink():
            return None
        raw = p.read_bytes()
        return {"path": rel, "bytes": len(raw), "sha256": sha(raw)}
    registration = disk_ref(rule.get("registration_path"))
    receipt = disk_ref(rule["required_receipt"] if rule["required_receipt"] != "NONE" else None)
    readback = None
    if kind == "REGULAR":
        readback = {"path": path, "bytes": expected["size"], "sha256": expected["sha256"],
                    "dev": expected["dev"], "ino": expected["ino"],
                    "created_at_ns": expected["ctime_ns"], "readback_verified": True}
    elif kind == "DIRECTORY":
        readback = {"path": path, "dev": expected["dev"], "ino": expected["ino"]}
    decision = policy.validate_observed(path=path, phase=phase, producer=rule["producer"],
                                        entry_type=kind, byte_count=expected["size"] if kind == "REGULAR" else 0,
                                        operation=operation, preexisting=(operation != "CREATE"),
                                        registration_ref=registration, receipt_ref=receipt,
                                        readback_ref=readback)
    return decision.allowed, decision.code


def _fresh_git(anchor: dict) -> list[str]:
    problems = []
    if command("git", "rev-parse", "HEAD").decode().strip() != anchor["head"]:
        problems.append("HEAD_CHANGED")
    if command("git", "branch", "--show-current").decode().strip() != anchor["branch"]:
        problems.append("BRANCH_CHANGED")
    idx = pathlib.Path(anchor["index"]["path"])
    if sha(idx.read_bytes()) != anchor["index"]["sha256"]:
        problems.append("INDEX_CHANGED")
    if sha(command("git", "diff", "--binary", "--no-ext-diff")) != anchor["tracked_diff"]["sha256"]:
        problems.append("TRACKED_DIFF_CHANGED")
    if sha(command("git", "diff", "--cached", "--binary", "--no-ext-diff")) != anchor["cached_diff"]["sha256"]:
        problems.append("CACHED_DIFF_CHANGED")
    return problems


def _protected(anchor: dict) -> list[str]:
    problems = []
    for item in anchor["protected"]:
        p = ROOT / item["path"]
        if p.exists() != item["exists"]:
            problems.append("PROTECTED_EXISTENCE:" + item["path"])
            continue
        if item["exists"] and item.get("sha256") and (not p.is_file() or p.is_symlink() or sha(p.read_bytes()) != item["sha256"]):
            problems.append("PROTECTED_CONTENT:" + item["path"])
    return problems


def baseline_compare(first: dict, second: dict, policy: OutputPolicy) -> dict:
    pair = pair_compare(first, second)
    if pair["verdict"] != "PASS":
        return {**pair, "anchor_reconciliation": "BLOCKED"}
    anchor = json.loads((R / "evidence/bootstrap-anchors.json").read_bytes())
    namespace = json.loads((R / "evidence/namespace-pair-prewrite.json").read_bytes())
    if not namespace["equal"] or namespace["scan_1_errors"] or namespace["scan_2_errors"]:
        return {"verdict": "BLOCKED", "reason": "NAMESPACE_ANCHOR_INCOMPLETE"}
    raw = zlib.decompress(base64.b64decode(namespace["records_zlib_base64"]))
    if sha(raw) != namespace["records_sha256"] or len(raw) != namespace["records_bytes"]:
        return {"verdict": "BLOCKED", "reason": "NAMESPACE_ANCHOR_HASH"}
    old = {r[0]: r for r in json.loads(raw)}
    now = {r["path"]: r for r in second["records"]}
    problems = _fresh_git(anchor) + _protected(anchor)
    previous = json.loads((ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06/prewrite-anchors.json").read_bytes())
    for item in previous["anchor_1"]["protected_files"]:
        if item.get("sha256") and sha((ROOT / item["path"]).read_bytes()) != item["sha256"]:
            problems.append("HISTORICAL_PROTECTED:" + item["path"])
    added = sorted(now.keys()-old.keys()); removed = sorted(old.keys()-now.keys())
    changed = []
    if removed:
        problems.append("REMOVED_PATHS")
    for p in added:
        ok, reason = _authorized_bootstrap_delta(policy, {}, now[p], p, "CREATE")
        if not ok: problems.append(f"ADDED:{p}:{reason}")
    for p in sorted(old.keys() & now.keys()):
        o, n = old[p], now[p]
        kind = _kind(o)
        if kind != n["kind"] or o[2:4] != [n["dev"], n["ino"]] or stat.S_IMODE(o[4]) != n["mode"] or o[5:7] != [n["uid"], n["gid"]]:
            problems.append("IDENTITY_OR_MODE:" + p); continue
        if kind == "DIRECTORY":
            if o[7:10] != [n["size"], n["mtime_ns"], n["ctime_ns"]]:
                if _children(set(old), p) == _children(set(now), p):
                    problems.append("DIRECTORY_METADATA_WITHOUT_CHILD_DELTA:" + p)
                else:
                    changed.append(p)
        elif o[7:10] != [n["size"], n["mtime_ns"], n["ctime_ns"]]:
            ok, reason = _authorized_bootstrap_delta(policy, o, n, p, "MODIFY")
            if not ok: problems.append(f"CHANGED:{p}:{reason}")
            else: changed.append(p)
    # Exact known early bootstrap publications have readback fingerprints.
    bootstrap = json.loads((R / "evidence/bootstrap-publications.json").read_bytes())
    for item in bootstrap["entries"]:
        if item["lifecycle"] == "DRAFT_BEFORE_FREEZE":
            continue
        p = ROOT / item["path"]
        if not p.is_file() or p.is_symlink() or sha(p.read_bytes()) != item["sha256"]:
            problems.append("BOOTSTRAP_PUBLICATION_DRIFT:" + item["path"])
    return {"verdict": "PASS" if not problems else "BLOCKED", "reason": "ANCHOR_BOOTSTRAP_GIT_PROTECTED_RECONCILED" if not problems else "ANCHOR_OR_BOOTSTRAP_MISMATCH", "added": added, "removed": removed, "changed": changed, "problems": problems[:200], "problem_count": len(problems), "namespace_record_count": len(old), "pair_record_count": len(now)}


def _canonical_preimage() -> dict[str, bytes]:
    data = json.loads((R / "evidence/canonical-preimage.json").read_bytes())
    result = {}
    for entry in data["entries"]:
        raw = base64.b64decode(entry["base64"], validate=True)
        if len(raw) != entry["bytes"] or sha(raw) != entry["sha256"]:
            raise ValueError("CANONICAL_PREIMAGE_HASH")
        result[entry["path"]] = raw
    return result


def _transaction_chain() -> dict:
    path = EPOCH / "evidence/transactions/chain.json"
    if not path.exists():
        return {"state": [], "ledger": []}
    data = json.loads(path.read_bytes())
    if data.get("task_id") != TASK_ID or data.get("epoch") != str(EPOCH) or set(data) != {"task_id", "epoch", "state", "ledger"}:
        raise ValueError("TRANSACTION_CHAIN_IDENTITY")
    return data


def _registered_destinations(baseline_paths: set[str]) -> tuple[list[str], list[str]]:
    registry = EPOCH / "evidence/transactions/destinations.json"
    if not registry.exists():
        return [], []
    data = json.loads(registry.read_bytes())
    problems = []
    if data.get("task_id") != TASK_ID or data.get("epoch") != str(EPOCH):
        problems.append("DESTINATION_REGISTRY_IDENTITY")
    dests = data.get("destinations")
    if not isinstance(dests, list) or len(dests) > 2:
        return [], problems + ["DESTINATION_COUNT"]
    paths = []
    for item in dests:
        path = item.get("path")
        if not isinstance(path, str) or not path.startswith(BACKUP + "/") or path in baseline_paths or item.get("owner") not in ("minimal-live-07-g1", "minimal-live-07-g2") or item.get("registered_empty") is not True or not item.get("registration_ref"):
            problems.append("DESTINATION_REGISTRATION")
        else:
            paths.append(path)
    if len(paths) != len(set(paths)):
        problems.append("DESTINATION_DUPLICATE")
    return paths, problems


def preservation_compare(first: dict, second: dict, policy: OutputPolicy) -> dict:
    pair = pair_compare(first, second)
    if pair["verdict"] != "PASS":
        return {**pair, "baseline_comparison": "BLOCKED"}
    baseline_path = EPOCH / "evidence/inventory/baseline-scan-01.json"
    baseline = json.loads(baseline_path.read_bytes())
    if not baseline.get("complete") or not baseline.get("policy", {}).get("ok"):
        return {"verdict": "BLOCKED", "reason": "BASELINE_SCAN_INCOMPLETE"}
    old = {r["path"]: r for r in baseline["records"]}
    now = {r["path"]: r for r in second["records"]}
    added = sorted(now.keys()-old.keys()); removed = sorted(old.keys()-now.keys())
    changed = sorted(p for p in old.keys() & now.keys() if old[p] != now[p])
    problems = []
    if removed:
        problems.append("REMOVED_PATHS")
    destinations, destination_problems = _registered_destinations(set(old))
    problems.extend(destination_problems)
    for p in added:
        if p.startswith(RUNREL + "/"):
            ok, reason = _authorized_bootstrap_delta(policy, {}, now[p], p, "CREATE")
            if not ok: problems.append(f"ARTIFACT:{p}:{reason}")
        elif any(p == dest or p.startswith(dest + "/") for dest in destinations):
            if now[p]["kind"] not in ("DIRECTORY", "REGULAR") or (now[p]["kind"] == "REGULAR" and now[p]["size"] == 0):
                problems.append("NATIVE_DESTINATION_TYPE_OR_ZERO:" + p)
        else:
            problems.append("UNAUTHORIZED_ADDITION:" + p)
    for p in changed:
        a,b=old[p],now[p]
        if a["kind"] != b["kind"] or (a["dev"],a["ino"],a["mode"],a["uid"],a["gid"]) != (b["dev"],b["ino"],b["mode"],b["uid"],b["gid"]) and b["kind"] == "DIRECTORY":
            problems.append("IDENTITY_OR_MODE:" + p);continue
        if b["kind"] == "DIRECTORY":
            if _children(set(old),p) == _children(set(now),p):
                problems.append("DIRECTORY_METADATA_WITHOUT_CHILD_DELTA:" + p)
        elif p in (STATE, LEDGER):
            pass
        elif p in PRODUCT_PATHS or p.startswith(RUNREL + "/"):
            ok, reason = _authorized_bootstrap_delta(policy, a, b, p, "MODIFY", product=(p in PRODUCT_PATHS))
            if not ok: problems.append(f"CHANGED:{p}:{reason}")
        else:
            problems.append("UNAUTHORIZED_CHANGE:" + p)
    for p in old:
        if p.startswith(BACKUP + "/") and p in now and old[p]["kind"] != "DIRECTORY" and old[p] != now[p]:
            problems.append("ORIGINAL_BACKUP_CHANGED:" + p)
    try:
        pre = _canonical_preimage()
        chain = _transaction_chain()
        for p, validator, key in ((STATE, validate_state_chain, "state"), (LEDGER, validate_ledger_chain, "ledger")):
            if old[p]["sha256"] != sha(pre[p]):
                problems.append("BASELINE_CANONICAL_PREIMAGE:" + p)
            final = (ROOT / p).read_bytes()
            if sha(final) != now[p]["sha256"]:
                problems.append("POST_CANONICAL_HASH:" + p)
            problems.extend(validator(pre[p], final, chain[key], root=ROOT))
    except Exception as exc:
        problems.append(f"TRANSACTION_CHAIN_READ:{type(exc).__name__}:{exc}")
    return {"verdict": "PASS" if not problems else "BLOCKED", "reason": "AUTHORIZED_DELTA_AND_CANONICAL_CHAIN" if not problems else "PRESERVATION_DELTA_REQUIRES_REVIEW", "added": added, "removed": removed, "changed": changed, "problems": problems[:200], "problem_count": len(problems)}


def publish(mode: str, first: dict, second: dict, comparison: dict, policy: OutputPolicy) -> dict:
    base = f"{EPOCH.relative_to(ROOT).as_posix()}/evidence/inventory/{mode}"
    refs = []
    for suffix, doc in (("scan-01.json", first), ("scan-02.json", second), ("compare.json", comparison)):
        rel = f"{base}-{suffix}"; raw = encoded(doc)
        decision = policy.authorize_prewrite(path=rel, phase="INVENTORY", producer="tools/inventory_pair.py", entry_type="REGULAR", byte_count=len(raw), operation="CREATE", preexisting=(ROOT / rel).exists())
        if not decision.allowed: raise RuntimeError(f"POLICY:{decision.code}:{rel}")
        refs.append(publish_exclusive(ROOT, rel, raw, max_bytes=CAP))
    receipt = {"format": "ML07_INVENTORY_PAIR_RECEIPT_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "phase": "INVENTORY", "producer": "tools/inventory_pair.py", "source_freeze_sha256": policy.source_freeze_sha256, "mode": mode, "verdict": comparison["verdict"], "artifacts": refs, "published_at_utc": utc(), "scanner": {"path": str(SCANNER), "sha256": sha(SCANNER.read_bytes())}, "fifo": {"path": FIFO_REL, "content_opened": False}}
    rel = f"{base}-receipt.json"; raw = encoded(receipt)
    decision = policy.authorize_prewrite(path=rel, phase="INVENTORY", producer="tools/inventory_pair.py", entry_type="REGULAR", byte_count=len(raw), operation="CREATE", preexisting=(ROOT / rel).exists())
    if not decision.allowed: raise RuntimeError(f"POLICY:{decision.code}:{rel}")
    receipt_ref = publish_exclusive(ROOT, rel, raw, max_bytes=1_000_000)
    return {"verdict": comparison["verdict"], "receipt": receipt_ref, "counts": second["counts"]}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("baseline", "preservation") or pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != EPOCH / "tools/inventory_pair.py":
        print(json.dumps({"verdict": "REFUSED", "reason": "LOCATION_OR_ARGUMENTS"})); return 2
    mode = sys.argv[1]
    policy = OutputPolicy.load(EPOCH / "output-policy.json", ROOT)
    scanner = scanner_module()
    first = scan_once(scanner, 1)
    second = scan_once(scanner, 2)
    comparison = baseline_compare(first, second, policy) if mode == "baseline" else preservation_compare(first, second, policy)
    result = publish(mode, first, second, comparison, policy)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
