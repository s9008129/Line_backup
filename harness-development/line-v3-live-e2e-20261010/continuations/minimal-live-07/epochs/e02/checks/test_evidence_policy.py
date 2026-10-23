#!/usr/bin/env python3
"""E01: actual scanner, publisher, policy, and delayed subprocess fixtures."""
from __future__ import annotations

import importlib.util
import hashlib
import copy
import json
import os
import pathlib
import socket
import stat
import sys
import tempfile
import threading
import time
import unittest

R = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07")
EPOCH = pathlib.Path(os.path.realpath(__file__)).parent.parent
SOURCE = EPOCH if (EPOCH / "tools/evidence_io.py").exists() else R
sys.path.insert(0, str(SOURCE / "tools"))
sys.path.insert(0, str(pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src")))
from evidence_io import publish_exclusive
from output_policy import OutputPolicy
from transaction_chain import validate_ledger_chain, validate_state_chain


def module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


SCANNER = module(pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/tools/inventory.py"), "ml07_e01_scanner")
RUNNER = module(SOURCE / "checks/run_command.py", "ml07_e01_runner")
PAIR = module(SOURCE / "tools/inventory_pair.py", "ml07_e01_pair")


def rule(path: str, *, producer="fixture", phase="FIXTURE", lifecycle="CREATE_ONCE", required_receipt="NONE", registration_required=False, registration_path=None):
    return {"rule_id": path, "exact_path": path, "exact_parent": path.rsplit("/", 1)[0],
            "producer": producer, "allowed_phase": [phase], "entry_type": "REGULAR", "max_bytes": 100000,
            "lifecycle": lifecycle, "required_receipt": required_receipt, "readback_requirement": "VERIFIED",
            "registration_required": registration_required, "registration_path": registration_path}


class EvidencePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=EPOCH / "tmp")
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "evidence").mkdir()
        self.document = {"task_id": "fixture-task", "epoch": "fixture-epoch", "source_freeze_sha256": "source-freeze-fixture", "rules": [rule("evidence/out.json")]}
        self.policy = OutputPolicy(self.document, self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_exclusive_readback_collision_symlink_parent(self):
        rel = "evidence/out.json"
        self.assertTrue(self.policy.authorize_prewrite(path=rel, phase="FIXTURE", producer="fixture", entry_type="REGULAR", byte_count=3, operation="CREATE").allowed)
        first = publish_exclusive(self.root, rel, b"abc", max_bytes=100000)
        self.assertEqual(first["sha256"], __import__("hashlib").sha256(b"abc").hexdigest())
        self.assertTrue(self.policy.validate_observed(path=rel, phase="FIXTURE", producer="fixture", entry_type="REGULAR", byte_count=3, operation="CREATE", readback_ref=first).allowed)
        with self.assertRaises(FileExistsError):
            publish_exclusive(self.root, rel, b"replacement", max_bytes=100000)
        (self.root / "alias").symlink_to(self.root / "evidence", target_is_directory=True)
        with self.assertRaises(OSError):
            publish_exclusive(self.root, "alias/unsafe", b"x", max_bytes=100000)

    def test_exact_phase_producer_cap_and_unregistered_dynamic(self):
        args = dict(path="evidence/out.json", phase="FIXTURE", producer="fixture", entry_type="REGULAR", byte_count=1, operation="CREATE")
        self.assertEqual(self.policy.authorize_prewrite(**{**args, "phase": "LATE"}).code, "WRONG_PHASE_OR_PRODUCER")
        self.assertEqual(self.policy.authorize_prewrite(**{**args, "producer": "other"}).code, "WRONG_PHASE_OR_PRODUCER")
        self.assertEqual(self.policy.authorize_prewrite(**{**args, "byte_count": True}).code, "TYPE_OR_CAP")
        self.assertEqual(self.policy.authorize_prewrite(**{**args, "byte_count": 100001}).code, "TYPE_OR_CAP")
        self.assertEqual(self.policy.authorize_prewrite(**{**args, "path": "evidence/unlisted.json"}).code, "UNKNOWN_PATH")
        dynamic = {"rule_id": "dynamic", "path_template": "evidence/{kind}-{sequence:04d}.{extension}", "exact_parent": "evidence", "producer": "fixture", "allowed_phase": ["FIXTURE"], "entry_type": "REGULAR", "max_bytes": 100000, "lifecycle": "CREATE_ONCE", "required_receipt": "NONE", "readback_requirement": "VERIFIED", "allowed_kinds": ["raw-ax"], "sequence_min": 1, "sequence_max": 2, "extensions": {"raw-ax": "json"}, "registration_required": True, "registration_path": "evidence/{kind}-{sequence:04d}.registration.json"}
        self.policy = OutputPolicy({**self.document, "rules": [dynamic]}, self.root)
        self.assertEqual(self.policy.authorize_prewrite(path="evidence/raw-ax-0001.json", phase="FIXTURE", producer="fixture", entry_type="REGULAR", byte_count=1, operation="CREATE").code, "REGISTRATION_READBACK_FAILED")
        self.assertIsNone(self.policy.rule_for("evidence/raw-ax-0003.json"))
        self.assertIsNone(self.policy.rule_for("evidence/raw-ax-0001.png"))

    def test_real_scan_pair_delayed_stream_and_special_lstat_only(self):
        fifo = self.root / "evidence/special.fifo"
        os.mkfifo(fifo)
        child_result = []
        def launch():
            child_result.append(RUNNER.run_child([sys.executable, "-c", "import sys,time;sys.stdout.write('begin');sys.stdout.flush();time.sleep(.2);sys.stdout.write('end')"], dict(os.environ), 3, 1024))
        t = threading.Thread(target=launch)
        t.start()
        a = SCANNER.scan_tree(self.root, fifo_abs=fifo, allowlist_fifo=True, exclude_top_git=False, deadline_seconds=10)
        b = SCANNER.scan_tree(self.root, fifo_abs=fifo, allowlist_fifo=True, exclude_top_git=False, deadline_seconds=10)
        t.join(timeout=4)
        self.assertTrue(a.complete and b.complete and a.policy["ok"] and b.policy["ok"])
        self.assertEqual(a.records, b.records)
        self.assertEqual(child_result[0][1], b"beginend")
        self.assertEqual(child_result[0][0]["exit_code"], 0)
        self.assertFalse((self.root / "evidence/stdout").exists())
        sock = socket.socket(socket.AF_UNIX)
        try:
            old_cwd = pathlib.Path.cwd()
            os.chdir(self.root)
            try:
                sock.bind("evidence/unknown.socket")
            finally:
                os.chdir(old_cwd)
            opened = []
            original = SCANNER._open
            def spy(name, flags, dir_fd=None, mode=0o777):
                if name == "unknown.socket": opened.append((name, flags))
                return original(name, flags, dir_fd=dir_fd, mode=mode)
            SCANNER._open = spy
            try:
                unknown = SCANNER.scan_tree(self.root, fifo_abs=fifo, allowlist_fifo=True, exclude_top_git=False, deadline_seconds=10)
            finally:
                SCANNER._open = original
            self.assertFalse(unknown.policy["ok"])
            self.assertEqual(opened, [])
            self.assertTrue(any(r["path"] == "evidence/unknown.socket" for r in unknown.records))
        finally:
            sock.close()

    def test_partial_timeout_and_changed_pair_block(self):
        fifo = self.root / "evidence/special.fifo"
        os.mkfifo(fifo)
        complete = SCANNER.scan_tree(self.root, fifo_abs=fifo, allowlist_fifo=True, exclude_top_git=False, deadline_seconds=10)
        timeout = SCANNER.scan_tree(self.root, fifo_abs=fifo, allowlist_fifo=True, exclude_top_git=False, deadline_seconds=0)
        doc = lambda state: {"complete": state.complete, "policy": state.policy, "records": state.records}
        self.assertEqual(PAIR.pair_compare(doc(complete), doc(timeout))["verdict"], "BLOCKED")
        (self.root / "evidence/new.txt").write_text("changed")
        changed = SCANNER.scan_tree(self.root, fifo_abs=fifo, allowlist_fifo=True, exclude_top_git=False, deadline_seconds=10)
        self.assertEqual(PAIR.pair_compare(doc(complete), doc(changed))["verdict"], "BLOCKED")

    def test_known_fifo_anchor_normalization_checks_full_identity(self):
        path = PAIR.FIFO_REL
        old = [path, "S", 10, 20, stat.S_IFIFO | 0o644, 501, 20, 0, 100, 101, None]
        new = {"path": path, "kind": "FIFO", "content_read": False, "content_hash": None,
               "dev": 10, "ino": 20, "mode": 0o644, "uid": 501, "gid": 20,
               "size": 0, "mtime_ns": 100, "ctime_ns": 101}
        self.assertTrue(PAIR._anchor_identity_matches(path, old, new))
        for key, value in (("dev", 11), ("ino", 21), ("mode", 0o600), ("uid", 502),
                           ("gid", 21), ("size", 1), ("mtime_ns", 102), ("ctime_ns", 103),
                           ("kind", "OTHER_SPECIAL"), ("content_read", True)):
            with self.subTest(changed=key):
                changed = dict(new)
                changed[key] = value
                self.assertFalse(PAIR._anchor_identity_matches(path, old, changed))
        self.assertFalse(PAIR._anchor_identity_matches("evidence/other.fifo", old, new))
        # An old generic special entry is accepted only when its mode proves the
        # exact prior subtype; changing the anchor to a socket must fail closed.
        wrong_old_subtype = list(old)
        wrong_old_subtype[4] = stat.S_IFSOCK | 0o644
        self.assertFalse(PAIR._anchor_identity_matches(path, wrong_old_subtype, new))

    def test_anchor_identity_separates_stable_identity_from_lifecycle_metadata(self):
        path = "evidence/draft.json"
        old = [path, "F", 10, 20, stat.S_IFREG | 0o600, 501, 20, 3, 100, 101, "oldhash"]
        new = {"path": path, "kind": "REGULAR", "dev": 10, "ino": 20, "mode": 0o600,
               "uid": 501, "gid": 20, "size": 5, "mtime_ns": 102, "ctime_ns": 103,
               "sha256": "newhash"}
        self.assertTrue(PAIR._anchor_identity_matches(path, old, new))
        for key, value in (("ino", 21), ("mode", 0o644), ("uid", 502), ("gid", 21), ("kind", "DIRECTORY")):
            with self.subTest(changed=key):
                changed = dict(new); changed[key] = value
                self.assertFalse(PAIR._anchor_identity_matches(path, old, changed))
        symlink_old = ["evidence/link", "L", 10, 22, stat.S_IFLNK | 0o777, 501, 20, 4, 100, 101, "target-a"]
        symlink_new = {"path": "evidence/link", "kind": "SYMLINK", "dev": 10, "ino": 22,
                       "mode": 0o777, "uid": 501, "gid": 20, "size": 4, "mtime_ns": 100,
                       "ctime_ns": 101, "target": "target-a",
                       "sha256": hashlib.sha256(os.fsencode("target-a")).hexdigest()}
        self.assertTrue(PAIR._anchor_identity_matches("evidence/link", symlink_old, symlink_new))
        self.assertTrue(PAIR._symlink_target_matches(symlink_old[10], symlink_new))
        self.assertFalse(PAIR._symlink_target_matches(symlink_old[10], {**symlink_new, "target": "target-b"}))
        self.assertFalse(PAIR._symlink_target_matches(symlink_old[10], {**symlink_new, "sha256": "0" * 64}))

    def test_user_input_scan_mode_normalizes_only_type_bits(self):
        observed = {"fstat": {"mode": stat.S_IFREG | 0o600, "dev": 10, "ino": 20, "uid": 501, "gid": 20,
                              "size": 3, "mtime_ns": 100, "ctime_ns": 101, "sha256": "abc"}}
        record = {"path": PAIR.READ_ONLY_USER_INPUT, "kind": "REGULAR", "mode": 0o600, "dev": 10, "ino": 20,
                  "uid": 501, "gid": 20, "bytes": 3, "mtime_ns": 100, "ctime_ns": 101, "sha256": "abc",
                  "read_verified": True}
        self.assertTrue(PAIR._input_record_matches_annex(record, observed))
        for key, value in (("mode", 0o644), ("kind", "FIFO"), ("ino", 21)):
            with self.subTest(changed=key):
                changed = dict(record); changed[key] = value
                self.assertFalse(PAIR._input_record_matches_annex(changed, observed))

    def test_preservation_uses_only_readback_verified_e02_baseline(self):
        with tempfile.TemporaryDirectory(dir=EPOCH / "tmp") as temp:
            root = pathlib.Path(temp)
            old_root = PAIR.ROOT
            PAIR.ROOT = root
            try:
                base = root / PAIR.BASELINE_E02 / "evidence/inventory"
                base.mkdir(parents=True)
                check_dir = root / PAIR.BASELINE_E02 / "evidence/checks"
                check_dir.mkdir(parents=True)
                source_freeze_raw = PAIR.encoded({"family": "evidence"})
                (root / PAIR.BASELINE_E02 / "source-freeze.json").write_bytes(source_freeze_raw)
                (check_dir / "B01-baseline-pair.receipt.json").write_bytes(PAIR.encoded({"task_id": PAIR.TASK_ID, "epoch": str(root / PAIR.BASELINE_E02), "check_id": "B01-baseline-pair", "family": "evidence", "verdict": "PASS", "outcome": {"exit_code": 0, "reaped": True}}))
                scan_rel = PAIR.BASELINE_E02 + "/evidence/inventory/baseline-scan-01.json"
                compare_rel = PAIR.BASELINE_E02 + "/evidence/inventory/baseline-compare.json"
                scan = {"task_id": PAIR.TASK_ID, "epoch": str(root / PAIR.BASELINE_E02), "complete": True, "policy": {"ok": True}, "records": []}
                compare = {"verdict": "PASS"}
                scan_raw = PAIR.encoded(scan)
                compare_raw = PAIR.encoded(compare)
                (base / "baseline-scan-01.json").write_bytes(scan_raw)
                (base / "baseline-compare.json").write_bytes(compare_raw)
                receipt = {"task_id": PAIR.TASK_ID, "epoch": str(root / PAIR.BASELINE_E02), "producer": "tools/inventory_pair.py", "phase": "INVENTORY", "source_freeze_sha256": PAIR.sha(source_freeze_raw), "mode": "baseline", "verdict": "PASS", "artifacts": [
                    {"path": scan_rel, "bytes": len(scan_raw), "sha256": PAIR.sha(scan_raw)},
                    {"path": compare_rel, "bytes": len(compare_raw), "sha256": PAIR.sha(compare_raw)},
                ]}
                (base / "baseline-receipt.json").write_bytes(PAIR.encoded(receipt))
                result, problem = PAIR._verified_e02_baseline()
                self.assertIsNone(problem)
                self.assertEqual(result["records"], [])
                (base / "baseline-scan-01.json").write_bytes(PAIR.encoded({**scan, "complete": False}))
                _, problem = PAIR._verified_e02_baseline()
                self.assertEqual(problem, "BASELINE_E02_SCAN_REF_MISMATCH")
            finally:
                PAIR.ROOT = old_root

    def test_registration_claim_receipt_and_real_tail_readback(self):
        dynamic = {"rule_id": "dynamic", "path_template": "evidence/{kind}-{sequence:04d}.{extension}", "exact_parent": "evidence", "producer": "fixture", "allowed_phase": ["FIXTURE"], "entry_type": "REGULAR", "max_bytes": 100000, "lifecycle": "CREATE_ONCE", "required_receipt": "evidence/receipt.json", "required_claim": "evidence/claim.json", "readback_requirement": "VERIFIED", "allowed_kinds": ["raw-ax"], "sequence_min": 1, "sequence_max": 1, "extensions": {"raw-ax": "json"}, "registration_required": True, "registration_path": "evidence/registration.json"}
        self.policy = OutputPolicy({**self.document, "rules": [dynamic, rule("evidence/registration.json"), rule("evidence/claim.json"), rule("evidence/receipt.json")]}, self.root)
        path = "evidence/raw-ax-0001.json"
        registration = {"path": path, "producer": "fixture", "phase": "FIXTURE", "epoch": "fixture-epoch", "task_id": "fixture-task", "source_freeze_sha256": "source-freeze-fixture", "registered_at_ns": time.time_ns()}
        registration_ref = publish_exclusive(self.root, "evidence/registration.json", (json.dumps(registration)+"\n").encode(), max_bytes=100000)
        decision = self.policy.authorize_prewrite(path=path, phase="FIXTURE", producer="fixture", entry_type="REGULAR", byte_count=2, operation="CREATE", registration_ref=registration_ref)
        self.assertTrue(decision.allowed, decision)
        child, stdout, stderr = RUNNER.run_child([sys.executable, "-c", "print('{}')"], dict(os.environ), 3, 1000)
        self.assertTrue(child["reaped"])
        artifact_ref = publish_exclusive(self.root, path, stdout, max_bytes=100000)
        claim = {"task_id": "fixture-task", "epoch": "fixture-epoch", "producer": "fixture", "source_freeze_sha256": "source-freeze-fixture"}
        claim_ref = publish_exclusive(self.root, "evidence/claim.json", (json.dumps(claim)+"\n").encode(), max_bytes=100000)
        receipt = {"task_id": "fixture-task", "epoch": "fixture-epoch", "producer": "fixture", "phase": "FIXTURE", "source_freeze_sha256": "source-freeze-fixture", "claim": claim_ref, "artifacts": [artifact_ref]}
        receipt_ref = publish_exclusive(self.root, "evidence/receipt.json", (json.dumps(receipt)+"\n").encode(), max_bytes=100000)
        valid = self.policy.validate_observed(path=path, phase="FIXTURE", producer="fixture", entry_type="REGULAR", byte_count=len(stdout), operation="CREATE", registration_ref=registration_ref, receipt_ref=receipt_ref, readback_ref=artifact_ref)
        self.assertTrue(valid.allowed, valid)
        self.assertEqual(self.policy.validate_observed(path=path, phase="FIXTURE", producer="fixture", entry_type="REGULAR", byte_count=len(stdout), operation="CREATE", registration_ref=registration_ref, receipt_ref=None, readback_ref=artifact_ref).code, "RECEIPT_READBACK_FAILED")
        self.assertEqual(self.policy.validate_observed(path=path, phase="FIXTURE", producer="wrong", entry_type="REGULAR", byte_count=len(stdout), operation="CREATE", registration_ref=registration_ref, receipt_ref=receipt_ref, readback_ref=artifact_ref).code, "WRONG_PHASE_OR_PRODUCER")

    def test_canonical_transaction_requires_bound_receipt(self):
        (self.root / "state").mkdir()
        canonical = {**rule("state/backup_state.json", producer="line_backup_batch.Store", phase="CANONICAL", lifecycle="CANONICAL_TRANSACTION", required_receipt="evidence/state-summary.json"), "transaction_authority": "line_backup_batch.Store", "allowed_owners": ["minimal-live-07-g1"]}
        self.policy = OutputPolicy({**self.document, "rules": [canonical]}, self.root)
        data = b'{"revision":1}\n'
        before = self.policy.authorize_prewrite(path="state/backup_state.json", phase="CANONICAL", producer="line_backup_batch.Store", entry_type="REGULAR", byte_count=len(data), operation="CREATE")
        self.assertTrue(before.allowed, before)
        state_ref = publish_exclusive(self.root, "state/backup_state.json", data, max_bytes=100000)
        self.assertEqual(self.policy.validate_observed(path="state/backup_state.json", phase="CANONICAL", producer="line_backup_batch.Store", entry_type="REGULAR", byte_count=len(data), operation="CREATE", readback_ref=state_ref).code, "RECEIPT_READBACK_FAILED")
        receipt = {"task_id": "fixture-task", "epoch": "fixture-epoch", "producer": "line_backup_batch.Store", "phase": "CANONICAL", "source_freeze_sha256": "source-freeze-fixture", "canonical_writer": "line_backup_batch.Store", "owner": "minimal-live-07-g1", "run_id": "RUN-fixture", "path": "state/backup_state.json", "operation": "CREATE", "postimage_sha256": hashlib.sha256(data).hexdigest(), "artifacts": [state_ref]}
        receipt_ref = publish_exclusive(self.root, "evidence/state-summary.json", (json.dumps(receipt)+"\n").encode(), max_bytes=100000)
        after = self.policy.validate_observed(path="state/backup_state.json", phase="CANONICAL", producer="line_backup_batch.Store", entry_type="REGULAR", byte_count=len(data), operation="CREATE", receipt_ref=receipt_ref, readback_ref=state_ref)
        self.assertTrue(after.allowed, after)

    def test_exact_ledger_chain_and_missing_state_chain(self):
        before = {"version": "line-backup-gui-ledger-1", "task_id": "fixture-task", "cap": 1000, "entries": []}
        after = json.loads(json.dumps(before))
        after["entries"].append({"seq": 1, "id": "one", "kind": "scroll", "count": 1, "run_id": "run-one", "owner": "minimal-live-07-g1", "at": "2026-10-11T00:00:00Z", "state": "RESERVED", "outcome": None, "consumed_at": None})
        first_raw = (json.dumps(before, sort_keys=True)+"\n").encode()
        second_raw = (json.dumps(after, sort_keys=True)+"\n").encode()
        first = publish_exclusive(self.root, "evidence/ledger-before.json", first_raw, max_bytes=100000)
        second = publish_exclusive(self.root, "evidence/ledger-after.json", second_raw, max_bytes=100000)
        event = {"owner": "minimal-live-07-g1", "canonical_writer": "line_backup_batch.Store", "path": "harness-development/line-v3-live-e2e-20261010/gui-ledger.json", "operation": "reserve_gui", "before_ref": first, "after_ref": second, "before_sha256": first["sha256"], "after_sha256": second["sha256"]}
        self.assertEqual(validate_ledger_chain(first_raw, second_raw, [event], root=self.root), [])
        self.assertTrue(validate_ledger_chain(first_raw, second_raw, [{**event, "owner": "foreign"}], root=self.root))
        self.assertEqual(validate_state_chain(b"same", b"same", [], root=self.root), [])
        self.assertEqual(validate_state_chain(b"same", b"changed", [], root=self.root), ["STATE_CHANGED_WITHOUT_CHAIN"])

    def test_pinned_real_schema_dependency_and_format_rejections(self):
        import jsonschema
        import referencing
        import rpds
        import rfc3339_validator
        import six
        from jsonschema import Draft202012Validator, FormatChecker
        from line_backup_batch.schema import validate
        from line_backup_acceptance.common import validate_state_strict
        site = EPOCH / "runtime/site-packages"
        for mod in (jsonschema, referencing, rpds, rfc3339_validator, six):
            self.assertTrue(pathlib.Path(mod.__file__).is_relative_to(site), mod.__file__)
        extension = list((site / "rpds").glob("*.cpython-313-darwin.so"))
        self.assertEqual(len(extension), 1)
        self.assertEqual(hashlib.sha256(extension[0].read_bytes()).hexdigest(), next(r["sha256"] for r in json.loads((EPOCH / "runtime/dependency-install-observation.json").read_bytes())["installed_tree"] if r["path"] == extension[0].relative_to(site).as_posix()))
        schema = json.loads((pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_batch/state_v3.schema.json")).read_bytes())
        declared = set()
        def formats(node):
            if isinstance(node, dict):
                if "format" in node:
                    declared.add(node["format"])
                for value in node.values(): formats(value)
            elif isinstance(node, list):
                for value in node: formats(value)
        formats(schema)
        checker = FormatChecker()
        self.assertEqual(declared, {"date", "date-time"})
        self.assertTrue(declared <= set(checker.checkers))
        validator = Draft202012Validator(schema, format_checker=checker, registry=referencing.Registry(retrieve=lambda uri: (_ for _ in ()).throw(RuntimeError("EXTERNAL_SCHEMA_REFUSED"))))
        real_state = json.loads(pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/state/backup_state.json").read_bytes())
        self.assertEqual(list(validator.iter_errors(real_state)), [])
        validate(real_state)
        validate_state_strict(real_state)
        examples = [
            ({"format": "date"}, "2024-05-13", "2024-02-30"),
            ({"format": "date-time"}, "2026-10-11T03:00:00+00:00", "2026-10-11T03:00:00"),
        ]
        for fragment, accepted, rejected in examples:
            local = Draft202012Validator(fragment, format_checker=checker, registry=referencing.Registry())
            self.assertEqual(list(local.iter_errors(accepted)), [])
            self.assertTrue(list(local.iter_errors(rejected)))
        for mutation in (lambda d: d.update(revision=True), lambda d: d.update(schema_version="3"), lambda d: d.update(unexpected=True), lambda d: d["runs"][0]["fingerprint"].update(start_date="2024-02-30"), lambda d: d["runs"][0]["events"][0].update(at="2026-10-11T03:00:00")):
            bad = copy.deepcopy(real_state)
            mutation(bad)
            self.assertTrue(list(validator.iter_errors(bad)))
            with self.assertRaises(Exception):
                validate_state_strict(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
