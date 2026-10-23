#!/usr/bin/env python3
"""E02: fixed binding, durable claim boundary, bounded child and no replay."""
from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import ExitStack

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
R = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
EPOCH = pathlib.Path(os.path.realpath(__file__)).parent.parent
SOURCE = EPOCH if (EPOCH / "checks/run_command.py").exists() else R
sys.path.insert(0, str(SOURCE / "tools"))
from evidence_io import mkdir_exclusive, publish_exclusive
from output_policy import OutputPolicy

spec = importlib.util.spec_from_file_location("ml07_runner_selftest", SOURCE / "checks/run_command.py")
RUNNER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RUNNER)


def fixture_rule(path: str):
    return {"rule_id": path, "exact_path": path, "exact_parent": path.rsplit("/", 1)[0],
            "producer": "checks/run_command.py", "allowed_phase": ["RUN_CHECK"], "entry_type": "REGULAR",
            "max_bytes": 1000000, "lifecycle": "CREATE_ONCE", "required_receipt": "NONE",
            "readback_requirement": "VERIFIED"}


class RunnerTests(unittest.TestCase):
    def test_directory_receipts_bind_to_their_own_family_freeze(self):
        with tempfile.TemporaryDirectory(dir=EPOCH / "tmp") as temp:
            root = pathlib.Path(temp)
            epoch = root / "epochs/e03"
            (epoch / "evidence").mkdir(parents=True)
            (epoch / "runtime").mkdir()
            evidence_source = {"task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence"}
            (epoch / "source-freeze.json").write_text(json.dumps(evidence_source))
            evidence_sha = hashlib.sha256((epoch / "source-freeze.json").read_bytes()).hexdigest()
            (epoch / "output-policy.json").write_text(json.dumps({
                "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence",
                "source_freeze_sha256": evidence_sha, "rules": [],
            }))
            production_source = {"task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "production"}
            (epoch / "production-source-freeze.json").write_text(json.dumps(production_source))
            production_sha = hashlib.sha256((epoch / "production-source-freeze.json").read_bytes()).hexdigest()
            (epoch / "production-output-policy.json").write_text(json.dumps({
                "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "production",
                "source_freeze_sha256": production_sha, "rules": [],
            }))
            early_dirs = [{"path": "epochs/e03", "identity_readback": True, "dev": 1, "ino": 2, "mode": 493, "uid": 501, "gid": 20}]
            late_dirs = [{"path": "epochs/e03/module-cache", "identity_readback": True, "dev": 1, "ino": 3, "mode": 493, "uid": 501, "gid": 20}]
            (epoch / "runtime/dependency-preparation-receipt.json").write_text(json.dumps({
                "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "producer": "tools/prepare_dependencies.py",
                "phase": "RUNTIME_PREPARE", "source_freeze_sha256": evidence_sha, "directories": early_dirs,
            }))
            (epoch / "evidence/materialization-receipt.json").write_text(json.dumps({
                "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "producer": "tools/prepare_epoch.py",
                "phase": "MATERIALIZE", "source_freeze_sha256": evidence_sha, "artifacts": [],
            }))
            (epoch / "production-freeze-receipt.json").write_text(json.dumps({
                "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "producer": "tools/prepare_production_family.py",
                "phase": "PRODUCTION_FREEZE", "source_freeze_sha256": production_sha, "directories": late_dirs,
            }))
            production_policy = OutputPolicy.load(epoch / "production-output-policy.json", root)
            with mock.patch.object(RUNNER, "ROOT", root), mock.patch.object(RUNNER, "EPOCH", epoch):
                refs = RUNNER._receipt_directory_refs(production_policy, "production")
                self.assertEqual(refs["epochs/e03"], early_dirs[0])
                self.assertEqual(refs["epochs/e03/module-cache"], late_dirs[0])
                bad_receipt = json.loads((epoch / "production-freeze-receipt.json").read_bytes())
                bad_receipt["source_freeze_sha256"] = evidence_sha
                (epoch / "production-freeze-receipt.json").write_text(json.dumps(bad_receipt))
                with self.assertRaisesRegex(RuntimeError, "DIRECTORY_RECEIPT_BINDING:production-freeze-receipt.json"):
                    RUNNER._receipt_directory_refs(production_policy, "production")

    def test_parent_refusal_before_claim_and_complete_directory_receipt_run(self):
        for omit_parent in (True, False):
            with self.subTest(omit_parent=omit_parent), tempfile.TemporaryDirectory(dir=EPOCH / "tmp") as temp:
                root = pathlib.Path(temp)
                (root / "epochs").mkdir()
                epoch = root / "epochs/e03"
                refs = [mkdir_exclusive(root, "epochs/e03")]
                (epoch / "runtime").mkdir()
                (epoch / "check-specs-freeze.json").write_text("{}\n")
                epoch_rel = "epochs/e03"
                refs.append(mkdir_exclusive(root, epoch_rel + "/evidence"))
                if not omit_parent:
                    refs.append(mkdir_exclusive(root, epoch_rel + "/evidence/checks"))
                    # A legal nested child changes parent timestamps before runner preflight.
                    (epoch / "evidence/checks/prior-child").mkdir()
                    (epoch / "evidence/checks/prior-child/marker").write_text("fixture\n")
                source_doc = {"task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence"}
                (epoch / "source-freeze.json").write_text(json.dumps(source_doc))
                source_sha = hashlib.sha256((epoch / "source-freeze.json").read_bytes()).hexdigest()
                (epoch / "output-policy.json").write_text(json.dumps({
                    "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence",
                    "source_freeze_sha256": source_sha, "rules": [],
                }))
                (epoch / "runtime/dependency-preparation-receipt.json").write_text(json.dumps({
                    "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "producer": "tools/prepare_dependencies.py",
                    "phase": "RUNTIME_PREPARE", "source_freeze_sha256": source_sha,
                    "directories": [refs[0]],
                }))
                (epoch / "evidence/materialization-receipt.json").write_text(json.dumps({
                    "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "producer": "tools/prepare_epoch.py",
                    "phase": "MATERIALIZE", "source_freeze_sha256": source_sha,
                    "artifacts": refs[1:],
                }))
                check_id = "E01-evidence-policy"
                base = f"{epoch_rel}/evidence/checks/{check_id}"
                paths = {suffix: base + "." + suffix for suffix in ("claim.json", "invocation.json", "stdout", "stderr", "receipt.json")}
                rules = [fixture_rule(p) for p in paths.values()]
                for rel in (epoch_rel, epoch_rel + "/evidence", epoch_rel + "/evidence/checks"):
                    rules.append({"rule_id": rel, "exact_path": rel, "exact_parent": rel.rsplit("/", 1)[0],
                                  "producer": "tools/prepare_epoch.py", "allowed_phase": ["MATERIALIZE"],
                                  "entry_type": "DIRECTORY", "max_bytes": 0, "lifecycle": "CREATE_ONCE",
                                  "required_receipt": "NONE", "readback_requirement": "IDENTITY"})
                policy = OutputPolicy({"task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence",
                                       "source_freeze_sha256": source_sha, "rules": rules}, root)
                check = {"argv": [sys.executable, "-c", "print('fixture-child')"], "timeout_seconds": 5, "stream_cap_bytes": 1000}
                def checked_preflight(_check_id):
                    RUNNER._verify_required_directories(policy, "evidence", paths)
                    return check, paths, {}, policy
                prior_cwd, prior_argv = pathlib.Path.cwd(), list(sys.argv)
                with ExitStack() as stack:
                    stack.enter_context(mock.patch.object(RUNNER, "ROOT", root))
                    stack.enter_context(mock.patch.object(RUNNER, "R", root))
                    stack.enter_context(mock.patch.object(RUNNER, "EPOCH", epoch))
                    stack.enter_context(mock.patch.object(RUNNER, "family_for", return_value="evidence"))
                    stack.enter_context(mock.patch.object(RUNNER, "preflight", side_effect=checked_preflight))
                    os.chdir(root)
                    sys.argv = [str(epoch / "checks/run_command.py"), check_id]
                    try:
                        if omit_parent:
                            with self.assertRaisesRegex(RuntimeError, "RUN_PARENT_MISSING:epochs/e03/evidence/checks"):
                                RUNNER.run(check_id)
                            self.assertFalse(any((root / p).exists() for p in paths.values()))
                        else:
                            result = RUNNER.run(check_id)
                            self.assertEqual(result["verdict"], "PASS")
                            self.assertTrue(result["outcome"]["reaped"])
                            self.assertEqual((root / paths["stdout"]).read_bytes(), b"fixture-child\n")
                            receipt = json.loads((root / paths["receipt.json"]).read_bytes())
                            self.assertEqual(receipt["verdict"], "PASS")
                            self.assertEqual(len(receipt["artifacts"]), 4)
                            self.assertTrue(all((root / p).is_file() for p in paths.values()))
                    finally:
                        os.chdir(prior_cwd)
                        sys.argv = prior_argv

    def test_fixed_preflight_rejects_identity_source_spec_index_and_collision(self):
        with tempfile.TemporaryDirectory(dir=EPOCH / "tmp") as temp:
            root = pathlib.Path(temp)
            epoch = root / "epochs/e01"
            (root / "epochs").mkdir()
            epoch_ref = mkdir_exclusive(root, "epochs/e01")
            checks_dir_ref = mkdir_exclusive(root, "epochs/e01/checks")
            evidence_ref = mkdir_exclusive(root, "epochs/e01/evidence")
            evidence_checks_ref = mkdir_exclusive(root, "epochs/e01/evidence/checks")
            (epoch / "runtime").mkdir()
            (root / "src").mkdir()
            (root / "src/code.py").write_bytes(b"fixed source\n")
            (root / "index").write_bytes(b"fixed index\n")
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            source_freeze = {"task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence", "source_hashes": {"src/code.py": digest(root / "src/code.py")}}
            (epoch / "source-freeze.json").write_text(json.dumps(source_freeze))
            runner_path = epoch / "checks/run_command.py"
            runner_path.write_bytes(b"fixture runner\n")
            check_id = "E01-evidence-policy"
            base = f"epochs/e01/evidence/checks/{check_id}"
            paths = [f"{base}.{suffix}" for suffix in ("claim.json", "invocation.json", "stdout", "stderr", "receipt.json")]
            source_sha = hashlib.sha256((epoch / "source-freeze.json").read_bytes()).hexdigest()
            directory_refs = [
                ("epochs/e01", epoch_ref), ("epochs/e01/checks", checks_dir_ref),
                ("epochs/e01/evidence", evidence_ref), ("epochs/e01/evidence/checks", evidence_checks_ref),
            ]
            directory_rules = [{"rule_id": rel, "exact_path": rel, "exact_parent": rel.rsplit("/", 1)[0],
                                "producer": "tools/prepare_epoch.py", "allowed_phase": ["MATERIALIZE"],
                                "entry_type": "DIRECTORY", "max_bytes": 0, "lifecycle": "CREATE_ONCE",
                                "required_receipt": "NONE", "readback_requirement": "IDENTITY"}
                               for rel, _ in directory_refs]
            policy = {"task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence", "source_freeze_sha256": source_sha, "rules": [*map(fixture_rule, paths), *directory_rules]}
            (epoch / "output-policy.json").write_text(json.dumps(policy))
            (epoch / "runtime/dependency-preparation-receipt.json").write_text(json.dumps({
                "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "producer": "tools/prepare_dependencies.py",
                "phase": "RUNTIME_PREPARE", "source_freeze_sha256": source_sha,
                "directories": [epoch_ref],
            }))
            (epoch / "evidence/materialization-receipt.json").write_text(json.dumps({
                "task_id": RUNNER.TASK_ID, "epoch": str(epoch), "producer": "tools/prepare_epoch.py",
                "phase": "MATERIALIZE", "source_freeze_sha256": source_sha,
                "artifacts": [ref for rel, ref in directory_refs if rel != "epochs/e01"],
            }))
            specs = {"task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence", "checks": [{"check_id": check_id, "family": "evidence", "argv": [sys.executable, "-c", "pass"], "timeout_seconds": 2, "stream_cap_bytes": 1000}]}
            (epoch / "check-specs.json").write_text(json.dumps(specs))
            freeze = {"task_id": RUNNER.TASK_ID, "epoch": str(epoch), "family": "evidence", "head": "fixture-head", "branch": "fixture-branch", "index_sha256": digest(root / "index"), "source_freeze_sha256": digest(epoch / "source-freeze.json"), "specs_sha256": digest(epoch / "check-specs.json"), "policy_sha256": digest(epoch / "output-policy.json"), "source_hashes": {"src/code.py": digest(root / "src/code.py")}, "executables": {str(pathlib.Path(sys.executable)): digest(pathlib.Path(sys.executable))}}
            (epoch / "check-specs-freeze.json").write_text(json.dumps(freeze))
            def git(*argv):
                values = {("git", "rev-parse", "HEAD"): b"fixture-head\n", ("git", "branch", "--show-current"): b"fixture-branch\n", ("git", "rev-parse", "--git-path", "index"): str(root / "index").encode() + b"\n", ("git", "diff", "--cached", "--name-only"): b""}
                return values[argv]
            prior_cwd, prior_argv = pathlib.Path.cwd(), list(sys.argv)
            with ExitStack() as stack:
                for name, value in (("ROOT", root), ("R", root), ("EPOCH", epoch)):
                    stack.enter_context(mock.patch.object(RUNNER, name, value))
                stack.enter_context(mock.patch.object(RUNNER, "command", side_effect=git))
                os.chdir(root)
                sys.argv = [str(runner_path), check_id]
                try:
                    self.assertEqual(RUNNER.preflight(check_id)[0]["check_id"], check_id)
                    freeze["source_hashes"] = {}
                    (epoch / "check-specs-freeze.json").write_text(json.dumps(freeze))
                    with self.assertRaisesRegex(RuntimeError, "FAMILY_SOURCE_MEMBERSHIP_DRIFT"):
                        RUNNER.preflight(check_id)
                    freeze["source_hashes"] = {"src/code.py": digest(root / "src/code.py")}
                    (epoch / "check-specs-freeze.json").write_text(json.dumps(freeze))
                    with self.assertRaisesRegex(RuntimeError, "UNKNOWN_CHECK_ID"):
                        RUNNER.preflight("UNKNOWN-CHECK")
                    with self.assertRaisesRegex(RuntimeError, "FAMILY_FREEZE_MISSING:production"):
                        RUNNER.preflight("N01-syntax-01")
                    specs["checks"][0]["family"] = "production"
                    (epoch / "check-specs.json").write_text(json.dumps(specs))
                    freeze["specs_sha256"] = digest(epoch / "check-specs.json")
                    (epoch / "check-specs-freeze.json").write_text(json.dumps(freeze))
                    with self.assertRaisesRegex(RuntimeError, "CHECK_FAMILY_MISSING_OR_MISMATCH:evidence"):
                        RUNNER.preflight(check_id)
                    specs["checks"][0]["family"] = "evidence"
                    (epoch / "check-specs.json").write_text(json.dumps(specs))
                    freeze["specs_sha256"] = digest(epoch / "check-specs.json")
                    (epoch / "check-specs-freeze.json").write_text(json.dumps(freeze))
                    os.chdir(epoch)
                    with self.assertRaisesRegex(RuntimeError, "WRONG_CWD_OR_RUNNER"):
                        RUNNER.preflight(check_id)
                    os.chdir(root)
                    with mock.patch.object(RUNNER, "command", side_effect=lambda *a: b"wrong\n" if a == ("git", "rev-parse", "HEAD") else git(*a)):
                        with self.assertRaisesRegex(RuntimeError, "GIT_HEAD_OR_BRANCH_DRIFT"):
                            RUNNER.preflight(check_id)
                    (root / "index").write_bytes(b"drifted index\n")
                    with self.assertRaisesRegex(RuntimeError, "GIT_INDEX_DRIFT"):
                        RUNNER.preflight(check_id)
                    (root / "index").write_bytes(b"fixed index\n")
                    (root / "src/code.py").write_bytes(b"source drift\n")
                    with self.assertRaisesRegex(RuntimeError, "SOURCE_DRIFT"):
                        RUNNER.preflight(check_id)
                    (root / "src/code.py").write_bytes(b"fixed source\n")
                    specs["checks"][0]["argv"] = [sys.executable, "-c", "print(1)"]
                    (epoch / "check-specs.json").write_text(json.dumps(specs))
                    with self.assertRaisesRegex(RuntimeError, "SPEC_OR_POLICY_DRIFT"):
                        RUNNER.preflight(check_id)
                    specs["checks"][0]["argv"] = [sys.executable, "-c", "pass"]
                    (epoch / "check-specs.json").write_text(json.dumps(specs))
                    (root / paths[0]).write_bytes(b"consumed claim\n")
                    with self.assertRaisesRegex(RuntimeError, "OUTPUT_COLLISION"):
                        RUNNER.preflight(check_id)
                finally:
                    os.chdir(prior_cwd)
                    sys.argv = prior_argv

    def test_real_child_timeout_cap_nonzero_and_reap(self):
        env = dict(os.environ)
        outcome, out, err = RUNNER.run_child([sys.executable, "-c", "import time;time.sleep(2)"], env, 1, 1024)
        self.assertEqual(outcome["stop_reason"], "TIMEOUT")
        self.assertTrue(outcome["reaped"])
        outcome, out, err = RUNNER.run_child([sys.executable, "-c", "import sys;sys.stdout.write('x'*5000)"], env, 3, 100)
        self.assertEqual(outcome["stop_reason"], "STDOUT_CAP")
        self.assertEqual(len(out), 100)
        self.assertTrue(outcome["reaped"])
        outcome, out, err = RUNNER.run_child([sys.executable, "-c", "raise SystemExit(9)"], env, 3, 1024)
        self.assertEqual(outcome["exit_code"], 9)
        self.assertTrue(outcome["reaped"])

    def test_claim_precedes_launch_and_failing_launch_consumes_id(self):
        with tempfile.TemporaryDirectory(dir=EPOCH / "tmp") as temp:
            root = pathlib.Path(temp)
            (root / "checks").mkdir()
            (root / "check-specs-freeze.json").write_text("{}\n")
            check_id = "fixture-one"
            paths = {suffix: f"checks/{check_id}.{suffix}" for suffix in ("claim.json", "invocation.json", "stdout", "stderr", "receipt.json")}
            policy = OutputPolicy({"task_id": RUNNER.TASK_ID, "epoch": str(root), "source_freeze_sha256": "fixture-sha", "rules": [fixture_rule(p) for p in paths.values()]}, root)
            check = {"argv": [sys.executable, "-c", "print('child')"], "timeout_seconds": 2, "stream_cap_bytes": 1000}
            def failed_launch(*args):
                self.assertTrue((root / paths["claim.json"]).exists())
                self.assertTrue((root / paths["invocation.json"]).exists())
                raise OSError("fixture launch failure")
            with mock.patch.object(RUNNER, "ROOT", root), mock.patch.object(RUNNER, "EPOCH", root), mock.patch.object(RUNNER, "family_for", return_value="evidence"), mock.patch.object(RUNNER, "preflight", return_value=(check, paths, {}, policy)), mock.patch.object(RUNNER, "run_child", side_effect=failed_launch):
                result = RUNNER.run(check_id)
                self.assertEqual(result["verdict"], "FAIL")
                self.assertIn("LAUNCH_OR_REAP_ERROR", result["outcome"]["stop_reason"])
                with self.assertRaisesRegex(RuntimeError, "CREATE_ONCE_CONFLICT"):
                    RUNNER.run(check_id)
            self.assertEqual(len(list((root / "checks").glob("fixture-one.*"))), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
