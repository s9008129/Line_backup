"""Read-only replay of canonical state/GUI-ledger transition evidence.

Every transition carries exact before/after bytes and a bounded operation. A
missing intermediate receipt never collapses into an end-state-only PASS.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

from output_policy import _read_anchored

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
OWNERS = {"minimal-live-07-g1", "minimal-live-07-g2"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_ref(root: pathlib.Path, ref: dict) -> bytes:
    if not isinstance(ref, dict) or set(("path", "bytes", "sha256")) - set(ref):
        raise ValueError("INCOMPLETE_REF")
    path = ref["path"]
    if not isinstance(path, str) or path.startswith("/") or any(part in ("", ".", "..") for part in path.split("/")):
        raise ValueError("INVALID_REF_PATH")
    raw, _ = _read_anchored(root, path, 16 * 1024 * 1024)
    if len(raw) != ref["bytes"] or sha(raw) != ref["sha256"]:
        raise ValueError("REF_BYTES")
    return raw


def validate_state_chain(initial: bytes, final: bytes, chain: list[dict], *, root: pathlib.Path = ROOT) -> list[str]:
    from line_backup_batch.store import TRANSITION_FIELDS, changed_keys, validate_nested_delta
    from line_backup_acceptance.common import validate_state_strict
    problems: list[str] = []
    current = initial
    if not chain and initial != final:
        return ["STATE_CHANGED_WITHOUT_CHAIN"]
    for index, event in enumerate(chain):
        try:
            if event.get("owner") not in OWNERS or event.get("canonical_writer") != "line_backup_batch.Store" or event.get("path") != "state/backup_state.json":
                raise ValueError("STATE_WRITER_OR_OWNER")
            operation = event["operation"]
            if operation not in TRANSITION_FIELDS or operation == "migrate":
                raise ValueError("STATE_OPERATION")
            before_raw = read_ref(root, event["before_ref"])
            after_raw = read_ref(root, event["after_ref"])
            if before_raw != current:
                raise ValueError("STATE_CHAIN_GAP")
            before, after = json.loads(before_raw), json.loads(after_raw)
            if type(before.get("revision")) is not int or type(after.get("revision")) is not int or after["revision"] != before["revision"] + 1:
                raise ValueError("STATE_REVISION_CAS")
            if changed_keys(before, after) - {"revision"} > TRANSITION_FIELDS[operation]:
                raise ValueError("STATE_TOP_LEVEL_SCOPE")
            validate_nested_delta(before, after, operation)
            validate_state_strict(after)
            if event.get("before_sha256") != sha(before_raw) or event.get("after_sha256") != sha(after_raw) or event.get("before_revision") != before["revision"] or event.get("after_revision") != after["revision"]:
                raise ValueError("STATE_RECEIPT_PREPOST")
            if operation in ("prepare", "calibrate", "intent", "dispatch", "finalize", "stop") and event.get("run_id") != after.get("current_run_id"):
                raise ValueError("STATE_RUN_BINDING")
            current = after_raw
        except Exception as exc:
            problems.append(f"STATE_TRANSITION_{index}:{type(exc).__name__}:{exc}")
            break
    if current != final:
        problems.append("STATE_FINAL_HASH_MISMATCH")
    return problems


def validate_ledger_chain(initial: bytes, final: bytes, chain: list[dict], *, root: pathlib.Path = ROOT) -> list[str]:
    problems: list[str] = []
    current = initial
    if not chain and initial != final:
        return ["LEDGER_CHANGED_WITHOUT_CHAIN"]
    for index, event in enumerate(chain):
        try:
            if event.get("owner") not in OWNERS or event.get("canonical_writer") != "line_backup_batch.Store" or event.get("path") != "harness-development/line-v3-live-e2e-20261010/gui-ledger.json":
                raise ValueError("LEDGER_WRITER_OR_OWNER")
            before_raw = read_ref(root, event["before_ref"])
            after_raw = read_ref(root, event["after_ref"])
            if before_raw != current:
                raise ValueError("LEDGER_CHAIN_GAP")
            before, after = json.loads(before_raw), json.loads(after_raw)
            if set(before) != {"version", "task_id", "cap", "entries"} or set(after) != set(before) or any(before[k] != after[k] for k in ("version", "task_id", "cap")) or after["cap"] != 1000:
                raise ValueError("LEDGER_SCHEMA_OR_CAP")
            old, new = before["entries"], after["entries"]
            if not isinstance(old, list) or not isinstance(new, list):
                raise ValueError("LEDGER_ENTRIES")
            if event.get("operation") == "reserve_gui":
                if len(new) != len(old)+1 or new[:-1] != old or new[-1].get("seq") != len(new) or new[-1].get("state") != "RESERVED" or new[-1].get("owner") != event["owner"] or type(new[-1].get("count")) is not int or new[-1]["count"] < 1:
                    raise ValueError("LEDGER_RESERVE_DELTA")
            elif event.get("operation") == "consume_gui":
                if len(new) != len(old):
                    raise ValueError("LEDGER_CONSUME_LENGTH")
                changed = [j for j, (a, b) in enumerate(zip(old, new)) if a != b]
                if len(changed) != 1:
                    raise ValueError("LEDGER_CONSUME_COUNT")
                j = changed[0]; a, b = old[j], new[j]
                if a.get("state") != "RESERVED" or b.get("state") != "CONSUMED" or a.get("owner") != event["owner"] or {k:v for k,v in a.items() if k not in ("state", "outcome", "consumed_at")} != {k:v for k,v in b.items() if k not in ("state", "outcome", "consumed_at")}:
                    raise ValueError("LEDGER_CONSUME_DELTA")
            else:
                raise ValueError("LEDGER_OPERATION")
            if sum(e["count"] for e in new) > after["cap"]:
                raise ValueError("LEDGER_QUOTA")
            if event.get("before_sha256") != sha(before_raw) or event.get("after_sha256") != sha(after_raw):
                raise ValueError("LEDGER_RECEIPT_PREPOST")
            current = after_raw
        except Exception as exc:
            problems.append(f"LEDGER_TRANSITION_{index}:{type(exc).__name__}:{exc}")
            break
    if current != final:
        problems.append("LEDGER_FINAL_HASH_MISMATCH")
    return problems
