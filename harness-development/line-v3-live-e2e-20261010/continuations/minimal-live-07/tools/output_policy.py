"""Single ML07 output authorization and inventory-delta evaluator.

The policy is frozen as JSON before formal checks. Callers pass a requested
write or observed delta; neither a filename alone nor an observed manifest
can grant a path. Receipt and registration references are read from disk.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import stat
from dataclasses import dataclass

from evidence_io import normalized_relative, open_anchored_directory


REQUIRED = {
    "rule_id", "exact_parent", "producer", "allowed_phase",
    "entry_type", "max_bytes", "lifecycle", "required_receipt",
    "readback_requirement",
}
LIFECYCLES = {"CREATE_ONCE", "DRAFT_BEFORE_FREEZE", "CANONICAL_TRANSACTION", "PRODUCER_SCRATCH"}
TYPES = {"REGULAR", "DIRECTORY", "SYMLINK"}


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str
    rule_id: str | None = None


def _read_anchored(root: pathlib.Path, rel: str, cap: int) -> tuple[bytes, os.stat_result]:
    parts = normalized_relative(rel)
    fd = open_anchored_directory(root)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
        try:
            before = os.fstat(leaf)
            if not stat.S_ISREG(before.st_mode) or before.st_size > cap:
                raise RuntimeError("REF_TYPE_OR_SIZE")
            chunks, size = [], 0
            while True:
                b = os.read(leaf, min(1024 * 1024, cap - size + 1))
                if not b:
                    break
                size += len(b)
                if size > cap:
                    raise RuntimeError("REF_CAP")
                chunks.append(b)
            after = os.fstat(leaf)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise RuntimeError("REF_RACE")
            return b"".join(chunks), after
        finally:
            os.close(leaf)
    finally:
        os.close(fd)


def _verified_doc(root: pathlib.Path, ref: dict, cap: int = 1024 * 1024) -> tuple[dict, os.stat_result]:
    if not isinstance(ref, dict) or set(("path", "bytes", "sha256")) - set(ref):
        raise ValueError("REF_INCOMPLETE")
    raw, st = _read_anchored(root, ref["path"], cap)
    if len(raw) != ref["bytes"] or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
        raise ValueError("REF_READBACK_MISMATCH")
    return json.loads(raw), st


class OutputPolicy:
    def __init__(self, document: dict, root: pathlib.Path):
        self.document = document
        self.root = root
        self.epoch = document.get("epoch")
        self.task_id = document.get("task_id")
        self.source_freeze_sha256 = document.get("source_freeze_sha256")
        self.rules = document.get("rules")
        if not isinstance(self.rules, list) or not self.epoch or not self.task_id:
            raise ValueError("POLICY_IDENTITY_OR_RULES_MISSING")
        ids, paths = set(), set()
        for rule in self.rules:
            if not isinstance(rule, dict) or REQUIRED - rule.keys():
                raise ValueError("INCOMPLETE_RULE")
            pathname = rule.get("exact_path") or rule.get("path_template")
            if not pathname or bool(rule.get("exact_path")) == bool(rule.get("path_template")):
                raise ValueError("EXACT_OR_RESTRICTED_TEMPLATE_REQUIRED")
            if rule["rule_id"] in ids or pathname in paths:
                raise ValueError("DUPLICATE_RULE_OR_PATH")
            ids.add(rule["rule_id"]); paths.add(pathname)
            parts = normalized_relative(pathname)
            if "/".join(parts[:-1]) != rule["exact_parent"]:
                raise ValueError("PARENT_MISMATCH")
            if rule.get("path_template"):
                if not rule.get("allowed_kinds") or not isinstance(rule.get("sequence_min"), int) or not isinstance(rule.get("sequence_max"), int) or rule["sequence_min"] < 1 or rule["sequence_max"] > 5000 or rule["sequence_min"] > rule["sequence_max"]:
                    raise ValueError("UNBOUNDED_TEMPLATE")
                if "{kind}" not in pathname or "{sequence:04d}" not in pathname:
                    raise ValueError("UNSUPPORTED_TEMPLATE")
                if "{extension}" in pathname and not isinstance(rule.get("extensions"), dict):
                    raise ValueError("MISSING_EXTENSION_MAP")
            if rule["lifecycle"] not in LIFECYCLES or rule["entry_type"] not in TYPES:
                raise ValueError("INVALID_LIFECYCLE_OR_TYPE")
            if type(rule["max_bytes"]) is not int or rule["max_bytes"] < 0:
                raise ValueError("INVALID_CAP")
            if not isinstance(rule["allowed_phase"], list) or not rule["allowed_phase"]:
                raise ValueError("MISSING_PHASE")
            if rule["readback_requirement"] not in ("VERIFIED", "IDENTITY"):
                raise ValueError("INVALID_READBACK_REQUIREMENT")
            if rule["lifecycle"] == "CANONICAL_TRANSACTION" and (not rule.get("transaction_authority") or rule["required_receipt"] == "NONE"):
                raise ValueError("TRANSACTION_RULE_INCOMPLETE")
            if rule["lifecycle"] == "PRODUCER_SCRATCH" and (not rule.get("scratch_lifetime") or not rule.get("scratch_root") or not pathname.startswith(rule["scratch_root"] + "/")):
                raise ValueError("SCRATCH_RULE_INCOMPLETE")

    @classmethod
    def load(cls, path: pathlib.Path, root: pathlib.Path) -> "OutputPolicy":
        return cls(json.loads(path.read_bytes()), root)

    def rule_for(self, rel: str) -> dict | None:
        normalized_relative(rel)
        for rule in self.rules:
            if rule.get("exact_path") == rel:
                return rule
            template = rule.get("path_template")
            if not template:
                continue
            pattern = re.escape(template).replace(re.escape("{kind}"), r"(?P<kind>[a-z0-9-]+)").replace(re.escape("{sequence:04d}"), r"(?P<sequence>[0-9]{4})").replace(re.escape("{extension}"), r"(?P<extension>[a-z0-9]+)")
            match = re.fullmatch(pattern, rel)
            if not match:
                continue
            fields = match.groupdict()
            kind, sequence = fields["kind"], int(fields["sequence"])
            if kind not in rule["allowed_kinds"] or not rule["sequence_min"] <= sequence <= rule["sequence_max"]:
                continue
            extension = fields.get("extension")
            if extension is not None and rule["extensions"].get(kind) != extension:
                continue
            result = dict(rule)
            result["exact_path"] = rel
            result["kind"] = kind
            result["sequence"] = sequence
            if extension is not None:
                result["extension"] = extension
            for key in ("required_receipt", "registration_path"):
                if isinstance(result.get(key), str) and "{" in result[key]:
                    result[key] = result[key].format(kind=kind, sequence=sequence, extension=extension)
            return result
        return None

    def _base_decision(
        self, *, path: str, phase: str, producer: str, entry_type: str,
        byte_count: int, operation: str, preexisting: bool,
    ) -> tuple[Decision, dict | None]:
        rule = self.rule_for(path)
        if rule is None:
            return Decision(False, "UNKNOWN_PATH"), None
        rid = rule["rule_id"]
        if phase not in rule["allowed_phase"] or producer != rule["producer"]:
            return Decision(False, "WRONG_PHASE_OR_PRODUCER", rid), rule
        if entry_type != rule["entry_type"] or type(byte_count) is not int or byte_count < 0 or byte_count > rule["max_bytes"]:
            return Decision(False, "TYPE_OR_CAP", rid), rule
        lifecycle = rule["lifecycle"]
        if lifecycle == "CREATE_ONCE" and (preexisting or operation != "CREATE"):
            return Decision(False, "CREATE_ONCE_CONFLICT", rid), rule
        if lifecycle == "DRAFT_BEFORE_FREEZE" and phase == "FROZEN":
            return Decision(False, "DRAFT_FROZEN", rid), rule
        if lifecycle == "CANONICAL_TRANSACTION" and operation not in ("CREATE", "MODIFY"):
            return Decision(False, "TRANSACTION_OPERATION", rid), rule
        if lifecycle == "PRODUCER_SCRATCH" and operation not in ("CREATE", "MODIFY", "DELETE"):
            return Decision(False, "SCRATCH_OPERATION", rid), rule
        if lifecycle == "PRODUCER_SCRATCH" and not path.startswith(rule["scratch_root"] + "/"):
            return Decision(False, "SCRATCH_ROOT", rid), rule
        return Decision(True, "BASE_AUTHORIZED", rid), rule

    def _registration(self, rule: dict, *, path: str, phase: str, producer: str, operation: str, registration_ref: dict | None, readback_ref: dict | None) -> Decision:
        rid = rule["rule_id"]
        if rule.get("registration_required"):
            try:
                doc, reg_st = _verified_doc(self.root, registration_ref)
            except (OSError, ValueError, RuntimeError, TypeError, KeyError, json.JSONDecodeError):
                return Decision(False, "REGISTRATION_READBACK_FAILED", rid)
            if registration_ref["path"] != rule.get("registration_path"):
                return Decision(False, "REGISTRATION_PATH", rid)
            if any((doc.get("path") != path, doc.get("producer") != producer,
                    doc.get("phase") != phase, doc.get("epoch") != self.epoch,
                    doc.get("task_id") != self.task_id,
                    doc.get("source_freeze_sha256") != self.source_freeze_sha256)):
                return Decision(False, "REGISTRATION_BINDING", rid)
            if operation != "CREATE" and rule["lifecycle"] != "CANONICAL_TRANSACTION":
                return Decision(False, "REGISTERED_NONCREATE", rid)
            if readback_ref and doc.get("registered_at_ns", 0) > readback_ref.get("created_at_ns", -1):
                return Decision(False, "REGISTRATION_AFTER_ARTIFACT", rid)
            if readback_ref and reg_st.st_ctime_ns > readback_ref.get("created_at_ns", -1):
                return Decision(False, "REGISTRATION_FILE_AFTER_ARTIFACT", rid)
        return Decision(True, "REGISTERED", rid)

    def authorize_prewrite(self, *, path: str, phase: str, producer: str, entry_type: str,
                           byte_count: int, operation: str, preexisting: bool = False,
                           registration_ref: dict | None = None) -> Decision:
        base, rule = self._base_decision(path=path, phase=phase, producer=producer, entry_type=entry_type, byte_count=byte_count, operation=operation, preexisting=preexisting)
        if not base.allowed:
            return base
        registered = self._registration(rule, path=path, phase=phase, producer=producer, operation=operation, registration_ref=registration_ref, readback_ref=None)
        if not registered.allowed:
            return registered
        return Decision(True, "PREWRITE_AUTHORIZED", rule["rule_id"])

    def validate_observed(self, *, path: str, phase: str, producer: str, entry_type: str,
                          byte_count: int, operation: str, preexisting: bool = False,
                          registration_ref: dict | None = None, receipt_ref: dict | None = None,
                          readback_ref: dict | None = None) -> Decision:
        base, rule = self._base_decision(path=path, phase=phase, producer=producer, entry_type=entry_type, byte_count=byte_count, operation=operation, preexisting=preexisting)
        if not base.allowed:
            return base
        registered = self._registration(rule, path=path, phase=phase, producer=producer, operation=operation, registration_ref=registration_ref, readback_ref=readback_ref)
        if not registered.allowed:
            return registered
        rid = rule["rule_id"]
        required = rule["required_receipt"]
        if required != "NONE":
            try:
                receipt, _ = _verified_doc(self.root, receipt_ref)
            except (OSError, ValueError, RuntimeError, TypeError, KeyError, json.JSONDecodeError):
                return Decision(False, "RECEIPT_READBACK_FAILED", rid)
            if receipt_ref["path"] != required or receipt.get("epoch") != self.epoch or receipt.get("task_id") != self.task_id or receipt.get("producer") != producer or receipt.get("phase") != phase or receipt.get("source_freeze_sha256") != self.source_freeze_sha256:
                return Decision(False, "RECEIPT_BINDING", rid)
            if rule["lifecycle"] == "CANONICAL_TRANSACTION":
                if (receipt.get("canonical_writer") != rule["transaction_authority"] or receipt.get("path") != path or receipt.get("operation") != operation or not receipt.get("run_id") or receipt.get("owner") not in rule.get("allowed_owners", []) or (operation == "MODIFY" and not receipt.get("preimage_sha256")) or (readback_ref and receipt.get("postimage_sha256") != readback_ref.get("sha256"))):
                    return Decision(False, "TRANSACTION_RECEIPT_BINDING", rid)
            claim_path = rule.get("required_claim")
            if claim_path:
                try:
                    claim_ref = receipt.get("claim")
                    claim, _ = _verified_doc(self.root, claim_ref)
                except (OSError, ValueError, RuntimeError, TypeError, KeyError, json.JSONDecodeError):
                    return Decision(False, "CLAIM_READBACK_FAILED", rid)
                if claim_ref["path"] != claim_path or claim.get("task_id") != self.task_id or claim.get("epoch") != self.epoch or claim.get("producer") != producer or claim.get("source_freeze_sha256") != self.source_freeze_sha256:
                    return Decision(False, "CLAIM_BINDING", rid)
            artifacts = receipt.get("artifacts") or []
            if not any(a.get("path") == path and a.get("bytes") == byte_count and (not readback_ref or a.get("sha256") == readback_ref.get("sha256")) for a in artifacts if isinstance(a, dict)):
                return Decision(False, "RECEIPT_ARTIFACT_MISSING", rid)
        if rule["readback_requirement"] == "VERIFIED":
            if not readback_ref or readback_ref.get("path") != path or readback_ref.get("bytes") != byte_count or readback_ref.get("readback_verified") is not True:
                return Decision(False, "READBACK_REQUIRED", rid)
            try:
                raw, st = _read_anchored(self.root, path, rule["max_bytes"])
            except (OSError, ValueError, RuntimeError):
                return Decision(False, "ARTIFACT_READBACK_FAILED", rid)
            if hashlib.sha256(raw).hexdigest() != readback_ref.get("sha256") or len(raw) != byte_count:
                return Decision(False, "ARTIFACT_BYTES_MISMATCH", rid)
            if readback_ref.get("dev") not in (None, st.st_dev) or readback_ref.get("ino") not in (None, st.st_ino):
                return Decision(False, "ARTIFACT_IDENTITY_MISMATCH", rid)
            if rule.get("check_id") and path.endswith(".json"):
                try:
                    checked = json.loads(raw)
                except (ValueError, TypeError):
                    return Decision(False, "CHECK_DOCUMENT_INVALID", rid)
                if checked.get("task_id") != self.task_id or checked.get("epoch") != self.epoch or checked.get("check_id") != rule["check_id"] or checked.get("producer") != producer or checked.get("phase") != phase or checked.get("source_freeze_sha256") != self.source_freeze_sha256:
                    return Decision(False, "CHECK_DOCUMENT_BINDING", rid)
        elif rule["readback_requirement"] == "IDENTITY":
            if not readback_ref or readback_ref.get("path") != path:
                return Decision(False, "IDENTITY_READBACK_REQUIRED", rid)
            try:
                parts = normalized_relative(path)
                parent = open_anchored_directory(self.root)
                try:
                    for part in parts[:-1]:
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                        os.close(parent)
                        parent = child
                    observed = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
                finally:
                    os.close(parent)
            except (OSError, ValueError, RuntimeError):
                return Decision(False, "IDENTITY_READBACK_FAILED", rid)
            if not stat.S_ISDIR(observed.st_mode) or observed.st_dev != readback_ref.get("dev") or observed.st_ino != readback_ref.get("ino"):
                return Decision(False, "IDENTITY_READBACK_MISMATCH", rid)
        return Decision(True, "AUTHORIZED", rid)
