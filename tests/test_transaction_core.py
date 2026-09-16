"""Ownership-protocol-compliant core probes for the transaction authority boundary.

Rev15 §15.5: the literal /private/tmp/line-backup-acceptance-case-01..25 roots are owned by
tests/acceptance_case_driver.py (its ownership marker is authoritative).  This unit test
therefore creates only its own private temp root, removes nothing shared, and asserts the
authority boundary itself: a refused authority preflight performs no state read and leaves no
lock file behind.  The happy-path revision protocol is covered end-to-end by the acceptance
case driver (Case 01 and the rest of the 25-case matrix) through the real CLI.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"


class TransactionCoreTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "line_backup_acceptance", *args],
                              cwd=WORKSPACE,
                              env={**os.environ, "PYTHONPATH": str(WORKSPACE / "src")},
                              capture_output=True, text=True)

    def test_test_mode_refuses_non_literal_root_without_state_read(self):
        with tempfile.TemporaryDirectory(prefix="line-backup-core-") as tmp:
            root = Path(tmp)
            state = root / "state" / "backup_state.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"schema_version": 2, "revision": 0, "current_run_id": None,
                                         "active_writer_id": None, "context_lock": None,
                                         "runs": [], "verified_albums": []}), encoding="utf-8")
            before = state.read_bytes()
            evidence = root / "evidence"
            p = self.run_cli("transaction", "prepare", "--project-root", str(root), "--state", str(state),
                             "--evidence-dir", str(evidence), "--test-mode", "--run-id", "RUN",
                             "--owner-id", "OWNER", "--group-key", GROUP, "--start-date", "2024-05-13",
                             "--end-date", "2024-05-17", "--expected-images", "57",
                             "--destination", str(root / "destination"))
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertEqual(json.loads((evidence / "result.json").read_text(encoding="utf-8"))["failure_class"],
                             "INVALID_AUTHORITY")
            self.assertEqual(state.read_bytes(), before)
            self.assertFalse((root / "state" / ".line-backup-state.lock").exists())

    def test_production_authority_mismatch_happens_without_state_read(self):
        with tempfile.TemporaryDirectory(prefix="line-backup-core-") as tmp:
            root = Path(tmp)
            (root / "state").mkdir(parents=True)
            foreign_state = root / "other-state.json"
            foreign_state.write_text("{}\n", encoding="utf-8")
            evidence = root / "evidence"
            p = self.run_cli("transaction", "prepare", "--project-root", str(root), "--state", str(foreign_state),
                             "--evidence-dir", str(evidence), "--run-id", "RUN", "--owner-id", "OWNER")
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertEqual(json.loads((evidence / "result.json").read_text(encoding="utf-8"))["failure_class"],
                             "INVALID_AUTHORITY")
            self.assertEqual(foreign_state.read_text(encoding="utf-8"), "{}\n")
            self.assertFalse((root / "state" / ".line-backup-state.lock").exists())


if __name__ == "__main__":
    unittest.main()
