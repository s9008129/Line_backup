#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import fcntl
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import line_backup_agent_resume as resume


def write_lock_record(root: Path, record: dict) -> None:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    lock = root / ".session.lock"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, resume.canonical_json(record) + b"\n")
        os.fsync(fd)
        fcntl.fcntl(fd, fcntl.F_FULLFSYNC, 0)
    finally:
        os.close(fd)


class StrictJsonTests(unittest.TestCase):
    def test_duplicate_key_is_rejected(self) -> None:
        with self.assertRaises(resume.InputError) as caught:
            resume.strict_json_loads(b'{"a":1,"a":2}')
        self.assertEqual(caught.exception.code, "DUPLICATE_JSON_KEY")

    def test_non_finite_number_is_rejected(self) -> None:
        with self.assertRaises(resume.InputError) as caught:
            resume.strict_json_loads(b'{"value":NaN}')
        self.assertEqual(caught.exception.code, "NON_FINITE_JSON")

    def test_nul_and_size_are_rejected(self) -> None:
        with self.assertRaises(resume.InputError):
            resume.strict_json_loads(b'{"a":1}\x00')
        with self.assertRaises(resume.InputError):
            resume.strict_json_loads(b" " * (resume.MAX_LINE_BYTES + 1))


class IdentityAndSyncTests(unittest.TestCase):
    def test_real_process_and_boot_identity(self) -> None:
        observed = resume.current_process_identity()
        self.assertEqual(observed["pid"], os.getpid())
        self.assertTrue(observed["started_at"])
        self.assertEqual(resume.process_identity(os.getpid()), observed)
        self.assertTrue(resume.boot_identity())
        self.assertIsNone(resume.process_identity(999_999_999))

    def test_sync_probe_uses_real_primitives_and_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            result = resume.sync_probe(root)
            self.assertTrue(result["file_fsync"])
            self.assertTrue(result["fullfsync"])
            self.assertTrue(result["directory_fsync"])
            self.assertTrue(result["readback"])
            self.assertRegex(result["probe_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(list(root.glob(".sync-probe-*")), [])
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)

    def test_pinned_swift_sources_are_byte_identical(self) -> None:
        expected = {
            "image_decode.swift": "238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b",
            "modern_ocr.swift": "19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861",
        }
        for name, digest in expected.items():
            actual = hashlib.sha256((REPO_ROOT / "scripts" / "agent_resume" / name).read_bytes()).hexdigest()
            self.assertEqual(actual, digest)


class SessionRootTests(unittest.TestCase):
    def _record(self, host: dict, pending_input: bool = False) -> dict:
        return {
            "schema_version": 1,
            "state": "active",
            "session_id": "session-test",
            "task_id": "AGENT-RESUME-P0-20261022",
            "boot_id": resume.boot_identity(),
            "controller": {"pid": 999_999_998, "started_at": "not-running"},
            "host": host,
            "pending_input": pending_input,
            "started_at_utc": resume.utc_now(),
        }

    def test_global_writer_lock_and_clean_close(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            try:
                identity = resume.process_identity(host.pid)
                self.assertIsNotNone(identity)
                first = resume.SessionRoot(root)
                first.acquire()
                first.activate(self._record(identity))
                second = resume.SessionRoot(root)
                with self.assertRaises(resume.WriterBusy) as caught:
                    second.acquire()
                self.assertEqual(caught.exception.code, "WRITER_BUSY")
                first.close_clean()
                third = resume.SessionRoot(root)
                third.acquire()
                third.activate(self._record(identity))
                third.close_clean()
                record = json.loads((root / ".session.lock").read_text(encoding="utf-8"))
                self.assertEqual(record["state"], "closed")
                self.assertEqual(stat.S_IMODE((root / ".session.lock").stat().st_mode), 0o600)
            finally:
                host.terminate()
                host.wait(timeout=5)

    def test_live_old_host_blocks_takeover_until_it_exits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            identity = resume.process_identity(host.pid)
            self.assertIsNotNone(identity)
            first = resume.SessionRoot(root)
            first.acquire()
            first.activate(self._record(identity))
            first.release_without_close()
            blocked = resume.SessionRoot(root)
            with self.assertRaises(resume.SafetyBlock) as caught:
                blocked.acquire()
            self.assertEqual(caught.exception.code, "OLD_HOST_ALIVE")
            host.terminate()
            host.wait(timeout=5)
            time.sleep(0.1)
            takeover = resume.SessionRoot(root)
            takeover.acquire()
            takeover.activate(self._record(resume.current_process_identity()))
            takeover.close_clean()

    def test_pending_input_blocks_takeover_even_after_host_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            record = self._record({"pid": 999_999_999, "started_at": "not-running"}, pending_input=True)
            write_lock_record(root, record)
            blocked = resume.SessionRoot(root)
            with self.assertRaises(resume.SafetyBlock) as caught:
                blocked.acquire()
            self.assertEqual(caught.exception.code, "PENDING_INPUT_UNRESOLVED")

    def test_corrupt_or_non_private_owner_record_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            write_lock_record(root, {"schema_version": 1, "state": "active"})
            (root / ".session.lock").write_bytes(b'{"schema_version":1,"state":"active","state":"closed"}\n')
            blocked = resume.SessionRoot(root)
            with self.assertRaises(resume.SafetyBlock) as caught:
                blocked.acquire()
            self.assertEqual(caught.exception.code, "SESSION_OWNER_RECORD_INVALID")


class SessionEofTests(unittest.TestCase):
    def test_eof_after_hello_is_unclean_and_leaves_takeover_barrier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            task_id = "AGENT-RESUME-M0-EOF"
            host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            process = None
            try:
                host_identity = resume.process_identity(host.pid)
                self.assertIsNotNone(host_identity)
                server_code = (
                    "import sys\n"
                    "from pathlib import Path\n"
                    "sys.path.insert(0, sys.argv[1])\n"
                    "import line_backup_agent_resume as resume\n"
                    "raise SystemExit(resume.SessionServer(sys.argv[2], Path(sys.argv[3])).run())\n"
                )
                process = subprocess.Popen(
                    [sys.executable, "-B", "-c", server_code, str(REPO_ROOT / "scripts"), task_id, str(root)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                request = {
                    "version": 1,
                    "request_id": "eof-hello",
                    "session_id": "eof-session",
                    "task_id": task_id,
                    "expected_generation": 0,
                    "operation": "hello",
                    "data": {"host": host_identity, "boot_id": resume.boot_identity()},
                }
                process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
                process.stdin.flush()
                response = json.loads(process.stdout.readline())
                self.assertTrue(response["ok"])
                process.stdin.close()
                self.assertEqual(process.wait(timeout=5), resume.EXIT_SAFETY_BLOCK)

                blocked = resume.SessionRoot(root)
                with self.assertRaises(resume.SafetyBlock) as caught:
                    blocked.acquire()
                self.assertEqual(caught.exception.code, "OLD_HOST_ALIVE")
            finally:
                if process is not None and process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                if process is not None:
                    for stream in (process.stdin, process.stdout, process.stderr):
                        if stream is not None:
                            stream.close()
                host.terminate()
                host.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
