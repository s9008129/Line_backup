"""Bounded root-issue coordination. Trusted parent transport, no model launcher.

The invoker is a coordinator capability that actually calls the platform. A role
cannot obtain write authority by claiming that a reviewer recommended a fix.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path
from typing import Callable

from .contracts import ContractError, path_is_within_scope, safe_relative_path, read_stable_beneath
from .budgets import validate_compact_state


class EscalationError(RuntimeError):
    pass


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise EscalationError(f"{label} requires nonempty text")
    return value


def validate_high_review_analysis(analysis, contract_sha256):
    """Apply the shared structural and semantic rules for a reviewer return.

    JSON Schema validation remains pinned to the originating run's bundle;
    this pure check is shared by that endpoint and the durable IssueLedger
    boundary so their route, text, and path decisions cannot drift.
    Extra fields stay accepted. In particular, ``dependencies`` is only
    interpreted by ``authorize`` for a continuation route.
    """
    if not isinstance(analysis, dict):
        raise EscalationError("high-review analysis must be an object")
    required = ("contract_sha256", "facts", "inferences", "unknowns", "evidence",
                "confidence", "route", "permitted_action", "success_criterion",
                "stop_condition", "allowed_paths")
    missing = [key for key in required if key not in analysis]
    if missing:
        raise EscalationError("analysis lacks " + ", ".join(missing))
    digest = analysis["contract_sha256"]
    if (not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest) or
        digest != contract_sha256):
        raise EscalationError("analysis is not bound to the frozen issue contract")
    for key in ("facts", "inferences", "unknowns", "evidence"):
        if not isinstance(analysis[key], list):
            raise EscalationError(f"analysis {key} must be a list")
    if not analysis["facts"] or not analysis["evidence"]:
        raise EscalationError("analysis requires observed facts and evidence references")
    route = analysis["route"]
    if not isinstance(route, str) or route not in {
        "IMPLEMENTER_FIX", "TARGETED_DIAGNOSTIC", "PLANNER_REPLAN", "EXTERNAL_BLOCKER"
    }:
        raise EscalationError("unsupported high-review route")
    if analysis.get("request_another_review"):
        raise EscalationError("recursive review is forbidden")
    if not isinstance(analysis["allowed_paths"], list):
        raise EscalationError("analysis allowed_paths must be a list")
    for path in analysis["allowed_paths"]:
        try:
            safe_relative_path(path)
        except (ContractError, TypeError) as exc:
            raise EscalationError("analysis allowed_paths contains an unsafe path") from exc
    for key in ("confidence", "permitted_action", "success_criterion", "stop_condition"):
        _text(analysis[key], key)
    return route


class IssueLedger:
    """One review and one continuation per explicit root condition across tasks.

    Callers must hold the controller task lock for task routing mutations. This
    ledger serializes root conditions additionally; it never acquires task locks.
    Records are immutable events; small projections are replaceable summaries.
    """
    def __init__(self, root: Path):
        self.root = Path(root)

    @contextlib.contextmanager
    def _lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".lock").open("a+b") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def _path(self, issue_id):
        if not isinstance(issue_id, str) or not re.fullmatch(r"[a-f0-9]{64}", issue_id):
            raise EscalationError("invalid root issue ID")
        return self.root / issue_id

    def _load(self, issue_id):
        try:
            directory = self._path(issue_id)
            item = json.loads((directory / "state.json").read_text())
            previous = None
            records = sorted(directory.glob("[0-9]*-*.json"))
            for seq, path in enumerate(records, 1):
                raw = path.read_bytes(); record = json.loads(raw)
                if record.get("sequence") != seq or record.get("previous_sha256") != previous:
                    raise EscalationError("issue event integrity mismatch; stop and reconcile")
                previous = hashlib.sha256(raw).hexdigest()
            if len(records) != item.get("sequence") or previous != item.get("event_sha256"):
                raise EscalationError("issue projection interrupted or changed; stop and reconcile")
            projected = {key: value for key, value in item.items() if key != "event_sha256"}
            if not records or record.get("projection") != projected:
                raise EscalationError("issue projection does not match durable transition")
            return item
        except (OSError, ValueError) as exc:
            raise EscalationError("issue unavailable; stop and reconcile") from exc

    def _event(self, item, event, detail):
        directory = self._path(item["issue_id"])
        directory.mkdir(exist_ok=True)
        seq = item.get("sequence", 0) + 1
        record = {"sequence": seq, "event": event, "time_ns": time.time_ns(),
                  "previous_sha256": item.get("event_sha256"), "detail": detail,
                  "projection": {**{k: v for k, v in item.items() if k != "event_sha256"}, "sequence": seq}}
        raw = json.dumps(record, ensure_ascii=False, sort_keys=True).encode() + b"\n"
        projected = {**item, "sequence":seq, "event_sha256":hashlib.sha256(raw).hexdigest()}
        state_raw = validate_compact_state(projected)
        path = directory / f"{seq:06d}-{event}.json"
        # An interrupted event before projection update is ambiguous: never
        # overwrite/replay it as a second dispatch. Require explicit reconciliation.
        with path.open("xb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        item.update(projected)
        fd, temp = tempfile.mkstemp(dir=directory, prefix="state-")
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(state_raw)
                stream.flush(); os.fsync(stream.fileno())
            os.replace(temp, directory / "state.json")
        finally:
            Path(temp).unlink(missing_ok=True)

    def open(self, packet):
        required = {"task_id", "run_id", "source_sha256", "goal", "failed_condition", "capability_boundary",
                    "contract_sha256", "facts", "hypotheses", "attempts", "last_learning",
                    "impact", "question", "owner", "success_criterion", "stop_condition"}
        if not isinstance(packet, dict) or not required.issubset(packet):
            raise EscalationError("issue packet lacks required facts/decision/stop fields")
        for field in required - {"facts", "hypotheses", "attempts"}:
            _text(packet[field], field)
        for field in ("facts", "hypotheses", "attempts"):
            if not isinstance(packet[field], list):
                raise EscalationError(f"{field} must be a list")
        if not packet["facts"]:
            raise EscalationError("issue needs observed facts; hypotheses alone are insufficient")
        if not all(re.fullmatch(r"[a-f0-9]{64}", packet[k]) for k in ("contract_sha256", "source_sha256")):
            raise EscalationError("issue requires a frozen contract SHA256")
        # Hypothesis names, model, task and observed error text do not reset identity.
        issue_id = packet.get("lineage_issue_id") or _digest({key: packet[key].strip()
            for key in ("goal", "failed_condition", "capability_boundary")})
        directory = self._path(issue_id)
        with self._lock():
            if (directory / "state.json").exists():
                item = self._load(issue_id)
                item["tasks"][packet["task_id"]] = packet["contract_sha256"]
                # Reopening a resolved condition requires explicit human judgment;
                # no silent budget reset from another task or renamed hypothesis.
                if item["state"] == "RESOLVED":
                    item["state"] = "WAIT_HUMAN"
                self._event(item, "ISSUE_LINKED", packet)
            else:
                item = {"issue_id": issue_id, "tasks": {packet["task_id"]: packet["contract_sha256"]},
                        "state": "STOPPED", "reviews": 0, "continuations": 0,
                        "packet": packet, "sequence": 0}
                self._event(item, "ISSUE_OPENED_STOPPED", packet)
        return issue_id

    def status(self, issue_id):
        with self._lock():
            return self._load(issue_id)

    def pending_for_task(self, task_id):
        with self._lock():
            summaries = []
            for path in self.root.iterdir():
                if not path.is_dir() or not re.fullmatch(r"[a-f0-9]{64}", path.name):
                    continue
                item = self._load(path.name)
                if task_id in item["tasks"] and item["state"] != "RESOLVED":
                    summaries.append({"issue_id": item["issue_id"], "state": item["state"],
                        "consumed_run_id": item.get("continuation_run_id"),
                        "permission": item.get("permission")})
            return summaries

    def claim(self, issue_id):
        with self._lock():
            item = self._load(issue_id)
            if item["state"] != "STOPPED" or item["reviews"]:
                raise EscalationError("automatic review already claimed or human intervention required")
            token = uuid.uuid4().hex
            item.update(state="REVIEW_CLAIMED", reviews=1, token=token)
            self._event(item, "DISPATCH_CLAIMED", {"token": token})
            return {"action": "REQUEST_HIGH_REVIEW", "issue_id": issue_id, "token": token,
                    "role": "HIGH_REASONING_REVIEWER", "packet": item["packet"],
                    "nested_review_allowed": False}

    def _bound(self, item, token):
        if item.get("token") != token:
            raise EscalationError("dispatch token mismatch")

    def _unresolved_sharing(self, item):
        """Other unresolved roots that share at least one task with this issue."""
        shared = []
        for path in self.root.iterdir():
            if not path.is_dir() or not re.fullmatch(r"[a-f0-9]{64}", path.name) or path.name == item["issue_id"]:
                continue
            other = self._load(path.name)
            if other["state"] != "RESOLVED" and set(other["tasks"]) & set(item["tasks"]):
                shared.append(other)
        return shared

    def _transport(self, item, record):
        for key in ("task_id", "run_id", "contract_sha256", "source_sha256"):
            if record.get(key) != item["packet"][key]:
                raise EscalationError(f"platform transport binding mismatch: {key}")
        if record.get("source") != "TRUSTED_OPERATOR":
            raise EscalationError("only trusted coordinator can import platform transport")
        safe_relative_path(item["packet"]["task_id"])
        try:
            raw, _ = read_stable_beneath(self.root.parent / item["packet"]["task_id"], record["raw_path"])
            if not raw or hashlib.sha256(raw).hexdigest() != record["raw_sha256"]:
                raise EscalationError("raw platform response missing or changed")
        except (ContractError, OSError, KeyError, TypeError) as exc:
            raise EscalationError("actual raw platform record is required") from exc

    def invoked(self, issue_id, token, receipt):
        with self._lock():
            item = self._load(issue_id); self._bound(item, token)
            if item["state"] != "REVIEW_CLAIMED":
                raise EscalationError("review is not eligible for invocation")
            for key in ("platform", "agent_id", "requested_model", "actual_model", "effort"):
                _text(receipt.get(key), key)
            if receipt.get("issue_id") != issue_id or receipt.get("token") != token:
                raise EscalationError("actual invocation binding mismatch")
            self._transport(item, receipt)
            item.update(state="REVIEW_INVOKED", invocation=receipt)
            self._event(item, "DISPATCH_INVOKED", receipt)

    def fail_dispatch(self, issue_id, token, reason):
        with self._lock():
            item = self._load(issue_id); self._bound(item, token)
            if item["state"] not in {"REVIEW_CLAIMED", "REVIEW_INVOKED"}:
                raise EscalationError("dispatch is already terminal")
            item["state"] = "WAIT_HUMAN"
            self._event(item, "DISPATCH_FAILED", {"reason": _text(reason, "reason")})

    def returned(self, issue_id, token, analysis, completion):
        with self._lock():
            item = self._load(issue_id); self._bound(item, token)
            if item["state"] != "REVIEW_INVOKED":
                raise EscalationError("no actual review invocation to complete")
            if (completion.get("issue_id") != issue_id or completion.get("token") != token or
                completion.get("agent_id") != item["invocation"]["agent_id"] or
                completion.get("platform") != item["invocation"]["platform"] or
                completion.get("platform_session_id") != item["invocation"].get("platform_session_id") or
                completion.get("status") != "completed" or
                completion.get("analysis_sha256") != _digest(analysis) or
                completion.get("process_exit") is not None):
                raise EscalationError("native completion/analysis binding mismatch")
            self._transport(item, completion)
            route = validate_high_review_analysis(analysis, item["packet"]["contract_sha256"])
            item.update(state="ANALYSIS_RETURNED" if route in {"IMPLEMENTER_FIX", "TARGETED_DIAGNOSTIC"}
                        else "WAIT_HUMAN", analysis=analysis, completion=completion)
            self._event(item, "ANALYSIS_RETURNED", {"analysis": analysis, "completion": completion})

    def authorize(self, issue_id, *, contract_sha256, allowed_paths):
        with self._lock():
            item = self._load(issue_id)
            if item["state"] != "ANALYSIS_RETURNED" or item["continuations"]:
                raise EscalationError("no unused bounded continuation")
            if contract_sha256 not in item["tasks"].values():
                raise EscalationError("continuation contract differs from issue binding")
            if contract_sha256 != item["analysis"]["contract_sha256"]:
                raise EscalationError("analysis cannot authorize a different contract")
            permitted = item["analysis"]["allowed_paths"]
            for path in permitted:
                if not any(path_is_within_scope(path, scope) for scope in allowed_paths):
                    raise EscalationError("review action exceeds frozen allowed paths; replan required")
            dependencies = item["analysis"].get("dependencies")
            if dependencies is None:
                dependencies = {}
            if not isinstance(dependencies, dict):
                raise EscalationError("review dependency judgments must be an object")
            other_ids = {other["issue_id"] for other in self._unresolved_sharing(item)
                         if other["issue_id"] != item["issue_id"]}
            if set(dependencies) != other_ids:
                raise EscalationError("review must freeze explicit dependency judgments for other unresolved roots")
            for value in dependencies.values():
                if value not in {"INDEPENDENT", "PREREQUISITE_SATISFIED", "PREREQUISITE_BLOCKED", "UNKNOWN"}:
                    raise EscalationError("unsupported dependency judgment")
            permission = {"issue_id": issue_id, "contract_sha256": contract_sha256, "allowed_paths": permitted,
                          "dependencies": dependencies, "action": item["analysis"]["permitted_action"],
                          "success_criterion": item["analysis"]["success_criterion"],
                          "stop_condition": item["analysis"]["stop_condition"]}
            item.update(state="CONTINUATION_AUTHORIZED", permission=permission)
            self._event(item, "CONTINUATION_AUTHORIZED", permission)
            return permission

    def guard_task(self, task_id, stage, contract_sha256, allowed_paths, *, run_id=None, selected_issue_id=None):
        with self._lock():
            affected = [self._load(p.name) for p in self.root.iterdir()
                        if p.is_dir() and re.fullmatch(r"[a-f0-9]{64}", p.name)]
            affected = [i for i in affected if task_id in i["tasks"] and i["state"] not in {"RESOLVED"}]
            # Review/inspection can run only through dispatch; stage allocation
            # cannot bypass STOP by switching role, task, or replan name.
            # Exactly one unresolved root for this task is unambiguous and may
            # be selected implicitly; competing roots keep failing closed until
            # an explicit selection is supplied.
            if affected and selected_issue_id is None and len(affected) == 1:
                selected_issue_id = affected[0]["issue_id"]
            if affected and (not selected_issue_id or selected_issue_id not in {i["issue_id"] for i in affected}):
                raise EscalationError("explicit unresolved issue selection is required")
            item = next((i for i in affected if i["issue_id"] == selected_issue_id), None)
            if item:
                if stage != "IMPLEMENT" or item["state"] != "CONTINUATION_AUTHORIZED":
                    raise EscalationError("selected issue is not authorized for continuation")
                other_ids = {i["issue_id"] for i in affected if i["issue_id"] != selected_issue_id}
                judged = item["permission"].get("dependencies", {})
                if set(judged) != other_ids or any(v not in {"INDEPENDENT", "PREREQUISITE_SATISFIED"} for v in judged.values()):
                    raise EscalationError("other unresolved roots lack dependency-safe judgments")
            for item in affected:
                if item["issue_id"] != selected_issue_id:
                    continue
                if item["permission"]["contract_sha256"] != contract_sha256:
                    raise EscalationError("continuation contract mismatch")
                if not run_id:
                    raise EscalationError("continuation requires exact allocated run identity")
                for path in item["permission"]["allowed_paths"]:
                    if not any(path_is_within_scope(path, p) for p in allowed_paths):
                        raise EscalationError("continuation exceeds current frozen run paths")
            if affected:
                item = next(i for i in affected if i["issue_id"] == selected_issue_id)
                item.update(state="CONTINUATION_CONSUMED", continuations=1,
                            continuation_task_id=task_id, continuation_run_id=run_id)
                self._event(item, "CONTINUATION_CONSUMED", {"task_id": task_id, "run_id": run_id})
                return item["permission"]
            return None

    def finish_task_run(self, task_id, accepted, *, run_id=None, evidence=None):
        with self._lock():
            for path in list(self.root.iterdir()):
                if not path.is_dir() or not re.fullmatch(r"[a-f0-9]{64}", path.name):
                    continue
                item = self._load(path.name)
                if item.get("continuation_task_id") == task_id and item["state"] == "CONTINUATION_CONSUMED":
                    if not run_id or run_id != item.get("continuation_run_id"):
                        raise EscalationError("continuation completion run mismatch")
                    proven = (accepted and isinstance(evidence, dict) and
                              evidence.get("condition") == item["permission"]["success_criterion"] and
                              isinstance(evidence.get("verified_files"), list) and bool(evidence["verified_files"]))
                    if proven:
                        try:
                            safe_relative_path(task_id)
                            for descriptor in evidence["verified_files"]:
                                raw, _ = read_stable_beneath(self.root.parent / task_id, descriptor["path"])
                                if not raw or len(raw) != descriptor["bytes"] or hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
                                    proven = False
                        except (ContractError, OSError, KeyError, TypeError):
                            proven = False
                    route = (item.get("analysis") or {}).get("route")
                    if proven and route == "TARGETED_DIAGNOSTIC":
                        item["state"] = "DIAGNOSTIC_COMPLETE_WAIT_HUMAN"
                    else:
                        item["state"] = "RESOLVED" if proven else "WAIT_HUMAN"
                    self._event(item, item["state"], {"task_id": task_id, "run_id": run_id,
                                "accepted": bool(proven), "evidence": evidence})

    def dispatch(self, issue_id, invoker: Callable):
        """Coordinator actively invokes once; uncertain/failed calls never retry."""
        request = self.claim(issue_id)
        try:
            receipt, analysis, completion = invoker(request)
            self.invoked(issue_id, request["token"], receipt)
            self.returned(issue_id, request["token"], analysis, completion)
        except Exception as exc:
            # Keep the real exception category/text, never infer account quota.
            current = self.status(issue_id)
            if current["state"] in {"REVIEW_CLAIMED", "REVIEW_INVOKED"}:
                self.fail_dispatch(issue_id, request["token"], f"{type(exc).__name__}: {exc}")
            raise EscalationError("high review failed/unknown; WAIT_HUMAN") from exc
        return self.status(issue_id)
