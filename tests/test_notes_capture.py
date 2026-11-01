"""Focused tests for the one-shot Notes CLI capture wrapper."""
import datetime
import io
import json
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import uuid

from line_backup_batch import notes_capture


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TASKS = ROOT / '.local' / 'line-backup' / 'tasks'


class NotesCaptureTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='notes-capture-', dir=str(PRIVATE_TASKS))
        self.base = Path(self.temporary.name).resolve()
        self.output = self.base / 'captures'
        self.output.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def completed(code, stdout=b'', stderr=b''):
        return subprocess.CompletedProcess([], code, stdout, stderr)

    def receipt_data(self, result, name):
        return json.loads((Path(result['receipt_dir']) / name).read_bytes())

    @staticmethod
    def reference(path):
        raw = Path(path).read_bytes()
        return dict(path=str(path), bytes=len(raw),
                    sha256=hashlib.sha256(raw).hexdigest())

    def test_request_precedes_one_child_and_each_capture_uses_new_receipt(self):
        calls = []
        seen = set()

        def run_child(command, cwd, env):
            receipts = set(self.output.glob('notes-capture-*'))
            new = receipts - seen
            self.assertEqual(len(new), 1)
            receipt = new.pop()
            seen.update(receipts)
            request = json.loads((receipt / 'request.json').read_bytes())
            self.assertEqual(request['child_args'], ['--help'])
            self.assertFalse((receipt / 'complete.json').exists())
            calls.append((command, cwd, env))
            return self.completed(0, b'out-' + str(len(calls)).encode(), b'')

        with mock.patch.object(notes_capture, '_run_child',
                               side_effect=run_child):
            first = notes_capture.capture(str(self.output), ['--help'])
            second = notes_capture.capture(str(self.output), ['--help'])

        self.assertEqual(len(calls), 2)
        self.assertNotEqual(first['receipt_dir'], second['receipt_dir'])
        for result, stdout in ((first, b'out-1'), (second, b'out-2')):
            complete = self.receipt_data(result, 'complete.json')
            self.assertEqual(complete['status'], 'COMPLETE')
            self.assertEqual(complete['dispatch_authorized'], False)
            for key in ('request', 'stdout', 'stderr', 'result'):
                ref = complete[key]
                raw = Path(ref['path']).read_bytes()
                self.assertEqual(len(raw), ref['bytes'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),
                                 ref['sha256'])
            self.assertEqual(
                Path(complete['stdout']['path']).read_bytes(), stdout)
            self.assertEqual(
                Path(complete['stderr']['path']).read_bytes(), b'')

    def test_refusal_then_success_keeps_both_receipts(self):
        with mock.patch.object(
                notes_capture, '_run_child',
                side_effect=[self.completed(4, b'blocked'),
                             self.completed(0, b'ok')]):
            refused = notes_capture.capture(str(self.output), ['--help'])
            succeeded = notes_capture.capture(str(self.output), ['--help'])

        self.assertEqual(refused['child_exit'], 4)
        self.assertEqual(succeeded['child_exit'], 0)
        self.assertNotEqual(refused['receipt_dir'], succeeded['receipt_dir'])
        self.assertEqual(
            Path(self.receipt_data(refused, 'complete.json')['stdout']['path'])
            .read_bytes(), b'blocked')
        self.assertEqual(
            Path(self.receipt_data(succeeded, 'complete.json')['stdout']['path'])
            .read_bytes(), b'ok')

    def test_real_fixed_child_help_records_execution_contract_and_succeeds(self):
        result = notes_capture.capture(str(self.output), ['--help'])
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['child_exit'], 0)
        complete = self.receipt_data(result, 'complete.json')
        request = self.receipt_data(result, 'request.json')
        child_result = self.receipt_data(result, 'result.json')
        receipt = Path(result['receipt_dir'])
        executable = Path(notes_capture.sys.executable).resolve(strict=True)
        module = Path(notes_capture.notes.__file__).resolve(strict=True)

        self.assertEqual(
            request['child_command'],
            [str(executable), '-B', '-m', 'line_backup_batch.notes',
             '--help'])
        self.assertEqual(request['cwd'], str(ROOT.resolve()))
        self.assertEqual(request['pythonpath'], str(ROOT / 'src'))
        self.assertEqual(request['receipt_id'], receipt.name)
        self.assertEqual(request['program'], dict(
            python_executable=str(executable),
            python_executable_sha256=hashlib.sha256(
                executable.read_bytes()).hexdigest(),
            notes_module_path=str(module),
            notes_module_sha256=hashlib.sha256(module.read_bytes()).hexdigest(),
            python_version=notes_capture.sys.version,
        ))
        for payload in (request, child_result, complete):
            self.assertEqual(payload['schema'], notes_capture.SCHEMA)
            self.assertFalse(payload['dispatch_authorized'])
            for field in ('recorded_at', 'started_at', 'finished_at'):
                if field in payload:
                    parsed = datetime.datetime.fromisoformat(payload[field])
                    self.assertEqual(parsed.utcoffset(),
                                     datetime.timedelta(0))
            if 'clock_source' in payload:
                self.assertEqual(
                    payload['clock_source'],
                    'python:datetime.datetime.now(datetime.timezone.utc)')
        self.assertLessEqual(
            datetime.datetime.fromisoformat(complete['started_at']),
            datetime.datetime.fromisoformat(complete['finished_at']))
        self.assertEqual(child_result['started_at'], complete['started_at'])
        self.assertEqual(child_result['finished_at'], complete['finished_at'])
        self.assertEqual(child_result['child_exit'], 0)
        self.assertEqual(child_result['outer_exit'], 0)
        self.assertEqual(complete['program'], request['program'])
        self.assertEqual(complete['request'],
                         self.reference(receipt / 'request.json'))
        self.assertEqual(complete['result'],
                         self.reference(receipt / 'result.json'))
        self.assertEqual(complete['stdout'],
                         self.reference(receipt / 'stdout.bin'))
        self.assertEqual(complete['stderr'],
                         self.reference(receipt / 'stderr.bin'))
        self.assertIn(b'usage:', Path(complete['stdout']['path']).read_bytes())
        self.assertEqual(Path(complete['stderr']['path']).read_bytes(), b'')

    def test_child_exits_70_and_signal_are_preserved_exactly(self):
        cases = (
            (0, b'zero', b'', 0, None, 0),
            (2, b'usage', b'', 2, None, 2),
            (4, b'refused', b'', 4, None, 4),
            (70, b'internal', b'', 70, None, 70),
            (-15, b'', b'signal', None, 15, 143),
        )
        for code, stdout, stderr, child_exit, signal, outer in cases:
            with self.subTest(child_exit=child_exit, signal=signal):
                output = io.StringIO()
                with mock.patch.object(
                        notes_capture, '_run_child',
                        return_value=self.completed(code, stdout, stderr)):
                    with mock.patch('sys.stdout', new=output):
                        exit_code = notes_capture.main([
                            '--output-root', str(self.output), '--', '--help'])
                self.assertEqual(exit_code, outer)
                payload = json.loads(output.getvalue())
                self.assertEqual(payload['child_exit'], child_exit)
                self.assertEqual(payload['signal'], signal)
                self.assertEqual(payload['outer_exit'], outer)
                complete = self.receipt_data(payload, 'complete.json')
                result = self.receipt_data(payload, 'result.json')
                self.assertEqual(complete['child_exit'], child_exit)
                self.assertEqual(complete['signal'], signal)
                self.assertEqual(complete['outer_exit'], outer)
                self.assertEqual(result['child_exit'], child_exit)
                self.assertEqual(result['signal'], signal)
                self.assertEqual(
                    Path(complete['stdout']['path']).read_bytes(), stdout)
                self.assertEqual(
                    Path(complete['stderr']['path']).read_bytes(), stderr)

    def test_child_zero_then_post_child_persistence_failure_is_wrapper_70(self):
        cases = (
            ('result.json', 'RESULT', False, False, False),
            ('stdout.bin', 'STDOUT', True, False, False),
            ('stderr.bin', 'STDERR', True, True, False),
            ('complete.json', 'COMPLETE', True, True, True),
        )
        for name, phase, result_exists, stdout_exists, stderr_exists in cases:
            with self.subTest(name=name):
                output_root = self.output / name.replace('.', '-')
                output_root.mkdir()
                calls = []
                original_write = notes_capture._write_new

                def fail_target(path, raw, target=name):
                    if Path(path).name == target:
                        raise notes_capture.CaptureError(
                            'CAPTURE_WRITE_FAILED')
                    return original_write(path, raw)

                output = io.StringIO()
                with mock.patch.object(
                        notes_capture, '_run_child',
                        side_effect=lambda *args: (
                            calls.append(True) or
                            self.completed(0, b'ok', b''))):
                    with mock.patch.object(
                            notes_capture, '_write_new',
                            side_effect=fail_target):
                        with mock.patch('sys.stdout', new=output):
                            exit_code = notes_capture.main([
                                '--output-root', str(output_root), '--',
                                '--help'])

                self.assertEqual(exit_code, 70)
                self.assertEqual(len(calls), 1)
                payload = json.loads(output.getvalue())
                self.assertEqual(payload['status'], 'INTERNAL_ERROR')
                self.assertEqual(payload['reason'], 'CAPTURE_INCOMPLETE')
                self.assertEqual(payload['capture_code'],
                                 'CAPTURE_PERSISTENCE_FAILED')
                self.assertEqual(payload['child_exit'], 0)
                receipt = Path(payload['receipt_dir'])
                self.assertTrue((receipt / 'request.json').is_file())
                self.assertEqual((receipt / 'result.json').exists(),
                                 result_exists)
                self.assertEqual((receipt / 'stdout.bin').exists(),
                                 stdout_exists)
                self.assertEqual((receipt / 'stderr.bin').exists(),
                                 stderr_exists)
                self.assertFalse((receipt / 'complete.json').exists())
                incomplete = json.loads(
                    (receipt / 'incomplete.json').read_bytes())
                self.assertEqual(incomplete['status'], 'INCOMPLETE')
                self.assertEqual(incomplete['phase'], phase)
                self.assertEqual(incomplete['child_exit'], 0)

    def test_child_launch_failure_is_wrapper_70_without_retry(self):
        calls = []

        def fail_launch(*args):
            calls.append(args)
            raise OSError('synthetic launch failure')

        output = io.StringIO()
        with mock.patch.object(notes_capture, '_run_child',
                               side_effect=fail_launch):
            with mock.patch('sys.stdout', new=output):
                exit_code = notes_capture.main([
                    '--output-root', str(self.output), '--', '--help'])

        self.assertEqual(exit_code, 70)
        self.assertEqual(len(calls), 1)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload['status'], 'INTERNAL_ERROR')
        self.assertEqual(payload['reason'], 'CAPTURE_INCOMPLETE')
        self.assertEqual(payload['capture_code'],
                         'CAPTURE_CHILD_LAUNCH_FAILED')
        self.assertNotIn('child_exit', payload)
        receipt = Path(payload['receipt_dir'])
        self.assertTrue((receipt / 'request.json').is_file())
        self.assertFalse((receipt / 'complete.json').exists())
        child_result = json.loads((receipt / 'result.json').read_bytes())
        self.assertEqual(child_result['status'], 'CHILD_LAUNCH_FAILED')
        self.assertIsNone(child_result['child_exit'])
        self.assertIsNone(child_result['signal'])
        incomplete = json.loads((receipt / 'incomplete.json').read_bytes())
        self.assertEqual(incomplete['status'], 'INCOMPLETE')
        self.assertEqual(incomplete['phase'], 'CHILD_LAUNCH')

    def test_program_drift_after_child_is_incomplete_without_reexecution(self):
        identity = notes_capture._program_identity()
        changed = dict(identity, python_version=identity['python_version'] + ' drift')
        calls = []
        with mock.patch.object(
                notes_capture, '_program_identity',
                side_effect=[identity, changed]):
            with mock.patch.object(
                    notes_capture, '_run_child',
                    side_effect=lambda *args: (
                        calls.append(True) or
                        self.completed(0, b'ok', b''))):
                with mock.patch('sys.stdout', new=io.StringIO()) as output:
                    exit_code = notes_capture.main([
                        '--output-root', str(self.output), '--', '--help'])

                payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 70)
        self.assertEqual(len(calls), 1)
        self.assertEqual(payload['status'], 'INTERNAL_ERROR')
        self.assertEqual(payload['reason'], 'CAPTURE_INCOMPLETE')
        self.assertEqual(payload['capture_code'], 'CAPTURE_PROGRAM_CHANGED')
        self.assertEqual(payload['child_exit'], 0)
        receipt = Path(payload['receipt_dir'])
        self.assertTrue((receipt / 'request.json').is_file())
        self.assertTrue((receipt / 'result.json').is_file())
        self.assertTrue((receipt / 'stdout.bin').is_file())
        self.assertTrue((receipt / 'stderr.bin').is_file())
        self.assertFalse((receipt / 'complete.json').exists())
        incomplete = json.loads((receipt / 'incomplete.json').read_bytes())
        self.assertEqual(incomplete['status'], 'INCOMPLETE')
        self.assertEqual(incomplete['phase'], 'PROGRAM_CHANGED')
        self.assertEqual(incomplete['child_exit'], 0)

    def test_receipt_and_request_name_collisions_are_rejected_before_child(self):
        fixed_hex = uuid.uuid4().hex

        class FixedUUID:
            hex = fixed_hex

        (self.output / ('notes-capture-' + fixed_hex)).mkdir()
        with mock.patch.object(notes_capture.uuid, 'uuid4',
                               return_value=FixedUUID()):
            with mock.patch.object(notes_capture, '_run_child') as child:
                with self.assertRaisesRegex(
                        notes_capture.CaptureError, 'CAPTURE_RECEIPT_COLLISION'):
                    notes_capture.capture(str(self.output), ['--help'])
                child.assert_not_called()

        def collision(parent):
            target = parent / 'notes-capture-file-collision'
            target.mkdir()
            (target / 'request.json').write_bytes(b'existing receipt')
            return target.resolve(strict=True)

        with mock.patch.object(notes_capture, '_new_receipt',
                               side_effect=collision):
            with mock.patch.object(notes_capture, '_run_child') as child:
                with self.assertRaises(notes_capture.CaptureError) as raised:
                    notes_capture.capture(str(self.output), ['--help'])
                child.assert_not_called()
        self.assertEqual(raised.exception.code, 'CAPTURE_PERSISTENCE_FAILED')

    def test_unsafe_output_roots_are_rejected_before_child(self):
        real = self.base / 'real-output'
        real.mkdir()
        linked = self.base / 'linked-output'
        linked.symlink_to(real, target_is_directory=True)
        with mock.patch.object(notes_capture, '_run_child') as child:
            with self.assertRaisesRegex(
                    notes_capture.CaptureError, 'CAPTURE_OUTPUT_ROOT_REQUIRED'):
                notes_capture.capture(str(linked), ['--help'])
            child.assert_not_called()

        with tempfile.TemporaryDirectory(
                prefix='notes-capture-outside-') as outside:
            outside = Path(outside).resolve()
            with mock.patch.object(notes_capture, '_run_child') as child:
                with self.assertRaisesRegex(
                        notes_capture.CaptureError,
                        'PROJECT_PRIVATE_CAPTURE_REQUIRED'):
                    notes_capture.capture(outside, ['--help'])
                child.assert_not_called()

    def test_receipt_symlink_is_rejected_before_child(self):
        real = self.base / 'real-receipt'
        real.mkdir()
        linked = self.base / 'linked-receipt'
        linked.symlink_to(real, target_is_directory=True)
        with mock.patch.object(notes_capture, '_new_receipt',
                               return_value=linked):
            with mock.patch.object(notes_capture, '_run_child') as child:
                with self.assertRaisesRegex(
                        notes_capture.CaptureError, 'CAPTURE_RECEIPT_CHANGED'):
                    notes_capture.capture(str(self.output), ['--help'])
                child.assert_not_called()


if __name__ == '__main__':
    unittest.main()
