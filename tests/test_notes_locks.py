"""Precise Notes flock contention and exit classification tests."""
import contextlib
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import uuid

from line_backup_batch import notes, notes_evidence


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TASKS = ROOT / '.local' / 'line-backup' / 'tasks'
PYTHON = '/usr/bin/python3'


class NotesLockTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='notes-locks-', dir=str(PRIVATE_TASKS))
        self.base = Path(self.temporary.name).resolve()
        self.active_path = self.base / 'active-notes-task.json'
        self.cli_support = self.base / 'cli-support'
        self.cli_support.mkdir()
        (self.cli_support / 'sitecustomize.py').write_text(
            'import pathlib\n'
            'from line_backup_batch import notes\n'
            'notes._active_task_path = lambda: pathlib.Path(%r)\n'
            'notes._read_active_hint = lambda: None\n'
            'notes._write_active_hint = lambda *args, **kwargs: None\n'
            % str(self.active_path), encoding='utf-8')
        self.statement = self.base / 'statement.txt'
        self.statement.write_bytes(b'synthetic lock statement\n')
        self.screenshot = self.base / 'screenshot.txt'
        self.screenshot.write_bytes(b'synthetic lock screenshot')
        self.packs = self.base / 'evidence-packs'
        self.packs.mkdir()
        self.photo_root = self.base / 'photos'
        self.collection_path = self.base / 'collection'
        self.identity = notes.list_identity(visual_key='lock-test-list')
        self.list_key_value = notes.list_key(self.identity)
        evidence = self.bundle(list_key=self.list_key_value)
        self.collection = notes.NotesCollection(str(self.collection_path))
        self.patches = [
            mock.patch.object(notes, '_active_task_path',
                              return_value=self.active_path),
            mock.patch.object(notes, '_read_active_hint', return_value=None),
            mock.patch.object(notes, '_write_active_hint', return_value=None),
        ]
        for patch in self.patches:
            patch.start()
        self.summary = self.collection.create(
            photo_root=str(self.photo_root), display_name='Synthetic Locks',
            identity=self.identity, binding_evidence=evidence,
            history_scope_evidence=evidence)
        self.records = notes.NotesRecords(self.summary['records_root'])
        self.records.bind(
            session_id='synthetic-lock-session',
            observation=self.bundle(list_key=self.list_key_value),
            handoff=self.bundle(list_key=self.list_key_value))

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.temporary.cleanup()

    def bundle(self, **context):
        return notes_evidence.create_bundle(
            statement=str(self.statement),
            assets=[('screenshot', str(self.screenshot))],
            context=context,
            output_dir=str(self.packs / uuid.uuid4().hex))['bundle_path']

    def run_main(self, *args):
        output = io.StringIO()
        with mock.patch('sys.stdout', new=output):
            code = notes.main([str(value) for value in args])
        return code, json.loads(output.getvalue())

    def run_cli(self, *args):
        environment = dict(os.environ)
        environment['PYTHONPATH'] = os.pathsep.join(
            (str(self.cli_support), str(ROOT / 'src')))
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        completed = subprocess.run(
            [PYTHON, '-B', '-m', 'line_backup_batch.notes',
             *(str(value) for value in args)],
            cwd=str(ROOT), env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            check=False)
        return completed.returncode, completed.stdout, completed.stderr

    def run_cli_json(self, *args):
        code, stdout, stderr = self.run_cli(*args)
        self.assertTrue(stdout.strip(), stderr)
        return code, json.loads(stdout)

    @contextlib.contextmanager
    def hold_lock(self, path):
        script = (
            'import fcntl, os, sys\n'
            'fd = os.open(sys.argv[1], os.O_RDWR)\n'
            'fcntl.flock(fd, fcntl.LOCK_EX)\n'
            'print("READY", flush=True)\n'
            'sys.stdin.readline()\n'
        )
        process = subprocess.Popen(
            [PYTHON, '-B', '-c', script, str(path)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        failure = None
        try:
            ready = process.stdout.readline()
            if ready != 'READY\n':
                failure = AssertionError(
                    'lock holder failed: ' + process.stderr.read())
            else:
                yield
        finally:
            if process.poll() is None:
                process.stdin.write('release\n')
                process.stdin.flush()
                process.stdin.close()
                process.wait(timeout=5)
            if process.returncode not in (0, None):
                failure = AssertionError(
                    'lock holder exited %s: %s' %
                    (process.returncode, process.stderr.read()))
            process.stdout.close()
            process.stderr.close()
            if failure is not None:
                raise failure

    def assert_lock_busy(self, payload, scope, retry_safe):
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertEqual(payload['reason'], 'NOTES_LOCK_BUSY')
        self.assertEqual(payload['scope'], scope)
        self.assertEqual(payload['retry_safe'], retry_safe)
        self.assertFalse(payload['dispatch_authorized'])

    def test_collection_lock_is_precise_for_reads_and_mutations(self):
        locked_path = self.collection_path / '.lock'
        new_identity = notes.list_identity(visual_key='lock-test-new-list')
        new_evidence = self.bundle(list_key=notes.list_key(new_identity))
        new_photo_root = self.base / 'new-photos'
        new_photo_root.mkdir()
        with self.hold_lock(locked_path):
            code, payload = self.run_main(
                'lists', '--collection', self.collection_path)
            self.assertEqual(code, 4)
            self.assert_lock_busy(payload, 'collection', True)

            code, payload = self.run_main(
                'init', '--collection', self.collection_path,
                '--photo-root', new_photo_root, '--name', 'Synthetic New',
                '--visual-key', 'lock-test-new-list',
                '--binding-evidence', new_evidence,
                '--history-scope-evidence', new_evidence)
            self.assertEqual(code, 4)
            self.assert_lock_busy(payload, 'collection', False)

        code, payload = self.run_main(
            'lists', '--collection', self.collection_path)
        self.assertEqual(code, 0)
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(len(payload['lists']), 1)

    def test_real_cli_readonly_commands_are_lock_busy_then_succeed(self):
        with self.hold_lock(self.collection_path / '.lock'):
            code, payload = self.run_cli_json(
                'lists', '--collection', self.collection_path)
            self.assertEqual(code, 4)
            self.assert_lock_busy(payload, 'collection', True)

        code, payload = self.run_cli_json(
            'lists', '--collection', self.collection_path)
        self.assertEqual(code, 0)
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(len(payload['lists']), 1)

        with self.hold_lock(self.records.records / '.lock'):
            code, payload = self.run_cli_json(
                'summary', '--records-root', self.records.records)
            self.assertEqual(code, 4)
            self.assert_lock_busy(payload, 'records', True)

            output = io.StringIO()
            with mock.patch('sys.stdout', new=output):
                code = notes.main([
                    'reattest', 'preview', '--records-root',
                    str(self.records.records), '--session-id',
                    'synthetic-lock-session'])
            self.assertEqual(code, 4)
            self.assert_lock_busy(json.loads(output.getvalue()),
                                  'records', True)

        code, payload = self.run_cli_json(
            'summary', '--records-root', self.records.records)
        self.assertEqual(code, 0)
        self.assertEqual(payload['list_key'], self.list_key_value)
        self.assertFalse(payload['dispatch_authorized'])
        self.assertFalse(self.active_path.exists())

    def test_records_lock_is_precise_for_reads_and_resume(self):
        locked_path = self.records.records / '.lock'
        with self.hold_lock(locked_path):
            for command in ('memory', 'summary', 'evidence-audit'):
                with self.subTest(command=command):
                    code, payload = self.run_main(
                        command, '--records-root', self.records.records)
                    self.assertEqual(code, 4)
                    self.assert_lock_busy(payload, 'records', True)

            code, payload = self.run_main(
                'resume', '--records-root', self.records.records)
            self.assertEqual(code, 4)
            self.assert_lock_busy(payload, 'records', False)

        code, payload = self.run_main(
            'summary', '--records-root', self.records.records)
        self.assertEqual(code, 0)
        self.assertEqual(payload['list_key'], self.list_key_value)
        self.assertFalse(payload['dispatch_authorized'])

    def test_non_flock_eagain_is_not_marked_retry_safe(self):
        error = OSError(errno.EAGAIN, 'synthetic non-flock eagain')
        with mock.patch.object(notes, '_open_lock', side_effect=error):
            code, payload = self.run_main(
                'lists', '--collection', self.collection_path)
        self.assertEqual(code, 4)
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertNotEqual(payload['reason'], 'NOTES_LOCK_BUSY')
        self.assertNotIn('retry_safe', payload)
        self.assertFalse(payload['dispatch_authorized'])

    def test_flock_contention_errnos_map_to_exact_lock_busy(self):
        for error_number in (errno.EAGAIN, errno.EWOULDBLOCK):
            with self.subTest(error_number=error_number):
                error = OSError(error_number, 'synthetic flock contention')
                with mock.patch.object(notes.fcntl, 'flock',
                                       side_effect=error):
                    code, payload = self.run_main(
                        'lists', '--collection', self.collection_path)
                self.assertEqual(code, 4)
                self.assert_lock_busy(payload, 'collection', True)

    def test_flock_other_oserror_is_not_lock_busy(self):
        error = OSError(errno.EIO, 'synthetic flock failure')
        with mock.patch.object(notes.fcntl, 'flock', side_effect=error):
            code, payload = self.run_main(
                'lists', '--collection', self.collection_path)
        self.assertEqual(code, 4)
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertEqual(payload['reason'], str(error))
        self.assertNotIn('retry_safe', payload)
        self.assertFalse(payload['dispatch_authorized'])

    def test_internal_error_is_not_marked_retry_safe(self):
        with mock.patch.object(notes.NotesCollection, 'lists',
                               side_effect=KeyError('synthetic')):
            code, payload = self.run_main(
                'lists', '--collection', self.collection_path)
        self.assertEqual(code, 70)
        self.assertEqual(payload['status'], 'INTERNAL_ERROR')
        self.assertEqual(payload['reason'], 'UNEXPECTED_EXCEPTION')
        self.assertNotIn('retry_safe', payload)
        self.assertFalse(payload['dispatch_authorized'])


if __name__ == '__main__':
    unittest.main()
