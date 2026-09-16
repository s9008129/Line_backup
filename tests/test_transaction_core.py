import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"


class TransactionCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path("/private/tmp/line-backup-acceptance-case-12")
        if self.tmp.exists(): shutil.rmtree(self.tmp)
        self.root = self.tmp
        self.root.mkdir()
        self.state = {"schema_version": 2, "revision": 0, "current_run_id": None, "active_writer_id": None,
                      "context_lock": None, "runs": [], "verified_albums": []}
        (self.root / "state.json").write_text(json.dumps(self.state), encoding="utf-8")
        (self.root / "destination").mkdir()
        (self.root / "evidence").mkdir()

    def tearDown(self):
        if self.tmp.exists(): shutil.rmtree(self.tmp)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "line_backup_acceptance", *args], cwd=Path(__file__).parents[1], env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}, capture_output=True, text=True)

    def test_prepare_creates_one_owned_revision(self):
        p = self.run_cli("transaction", "prepare", "--project-root", str(self.root), "--state", str(self.root / "state.json"), "--evidence-dir", str(self.root / "evidence"), "--test-mode", "--run-id", "RUN", "--owner-id", "OWNER", "--group-key", GROUP, "--start-date", "2024-05-13", "--end-date", "2024-05-17", "--expected-images", "57", "--destination", str(self.root / "destination"))
        self.assertEqual(p.returncode, 0, p.stderr)
        state = json.loads((self.root / "state.json").read_text())
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["active_writer_id"], "OWNER")
        self.assertFalse(state["runs"][0]["intent"]["save_all_retry_allowed"])

    def test_authority_mismatch_happens_without_state_read(self):
        other = Path("/private/tmp/line-backup-acceptance-case-11"); other.mkdir(parents=True, exist_ok=True)
        ev = self.root / "evidence-authority"
        p = self.run_cli("transaction", "prepare", "--project-root", str(self.root), "--state", str(other / "state.json"), "--evidence-dir", str(ev), "--test-mode", "--run-id", "RUN", "--owner-id", "OWNER")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads((ev / "result.json").read_text())["failure_class"], "INVALID_AUTHORITY")
        self.assertFalse((self.root / ".line-backup-state.lock").exists())


if __name__ == "__main__": unittest.main()
