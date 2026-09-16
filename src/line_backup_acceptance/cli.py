from __future__ import annotations

import argparse
import json
from pathlib import Path

from .authority import validate_transaction, validate_verify
from .common import AcceptanceError, atomic_write_json, emit
from . import status, transaction, verifier


def _common(parser):
    parser.add_argument("--project-root")
    parser.add_argument("--config")
    parser.add_argument("--run-log")
    parser.add_argument("--state")
    parser.add_argument("--evidence-dir")
    parser.add_argument("--test-mode", action="store_true")
    parser.add_argument("--pause-at")
    parser.add_argument("--barrier-file")
    parser.add_argument("--storage-fault", choices=["WRITE_BEFORE_REPLACE", "READBACK_UNCERTAIN_AFTER_REPLACE"])


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="line_backup_acceptance")
    sub = ap.add_subparsers(dest="command")
    verify = sub.add_parser("verify-only")
    _common(verify)
    verify.add_argument("--destination")
    verify.add_argument("--group-key")
    verify.add_argument("--start-date")
    verify.add_argument("--end-date")
    verify.add_argument("--expected-images", type=int)
    verify.add_argument("--run-id")
    tx = sub.add_parser("transaction")
    txsub = tx.add_subparsers(dest="operation")
    for op in ("prepare", "resume", "commit", "finalize", "duplicate-check"):
        p = txsub.add_parser(op)
        _common(p)
        p.add_argument("--run-id")
        p.add_argument("--expected-revision", type=int)
        p.add_argument("--expected-owner-id")
        p.add_argument("--owner-id")
        p.add_argument("--group-key")
        p.add_argument("--start-date")
        p.add_argument("--end-date")
        p.add_argument("--expected-images", type=int)
        p.add_argument("--destination")
        p.add_argument("--dispatcher")
        p.add_argument("--dispatch-counter")
        p.add_argument("--verification-json")
        p.add_argument("--source-evidence")
        p.add_argument("--outcome", choices=["VERIFIED", "SAFE_ABORT"])
        p.add_argument("--dispatcher-outcome", choices=["RETURNED", "UNKNOWN"], default="RETURNED")
        p.add_argument("--crash-after-dispatch", action="store_true")
        p.add_argument("--no-dispatch", action="store_true")
        p.add_argument("--storage-fault-slot", choices=["intent", "dispatch"])
    st = sub.add_parser("status")
    stsub = st.add_subparsers(dest="operation")
    ev = stsub.add_parser("evaluate")
    ev.add_argument("--input")
    ev.add_argument("--output")
    return ap


def _error(ns, exc: AcceptanceError) -> int:
    evidence = getattr(ns, "evidence_dir", None)
    if evidence:
        try:
            result = verifier.write_error(Path(evidence), exc)
        except Exception as write_exc:
            result = {"schema_version": 1, "overall_status": "UNKNOWN", "failure_class": exc.code,
                      "error": exc.message, "artifact_error": str(write_exc), "exit_code": exc.exit_code}
    else:
        result = {"schema_version": 1, "overall_status": "UNKNOWN", "failure_class": exc.code,
                  "error": exc.message, "exit_code": exc.exit_code}
    emit(result)
    return exc.exit_code


def main(argv=None) -> int:
    ap = parser()
    ns = ap.parse_args(argv)
    try:
        if ns.command == "verify-only":
            result, code = verifier.inspect(ns)
            emit(result)
            return code
        if ns.command == "transaction":
            if ns.operation not in {"prepare", "resume", "commit", "finalize", "duplicate-check"}:
                raise AcceptanceError("INVALID_INPUT", "transaction operation is required", 2)
            validate_transaction(ns)
            # Rev15 §15.1 fixed order: (1) authority validation, (2) adapter-flag semantic
            # rejection, (3) operation logic.  resume owns its own adapter-flag rejection
            # (INVALID_INPUT, after authority and before any state read); every other operation
            # refuses test-only fault flags without --test-mode here.
            if ns.operation != "resume" and not ns.test_mode and (
                    ns.pause_at or ns.barrier_file or ns.storage_fault or ns.storage_fault_slot
                    or ns.crash_after_dispatch or ns.dispatcher_outcome not in (None, "RETURNED")):
                raise AcceptanceError("INVALID_AUTHORITY", "test-only adapter flags require --test-mode", 2)
            fn = {"prepare": transaction.prepare, "resume": transaction.resume, "commit": transaction.commit,
                  "finalize": transaction.finalize, "duplicate-check": transaction.duplicate_check}[ns.operation]
            result, code = fn(ns)
            emit(result)
            return code
        if ns.command == "status" and ns.operation == "evaluate":
            result, code = status.run(ns)
            emit(result)
            return code
        raise AcceptanceError("INVALID_INPUT", "a command and operation are required", 2)
    except AcceptanceError as exc:
        return _error(ns, exc)
    except (TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        return _error(ns, AcceptanceError("INTERNAL_ERROR", str(exc), 1))
