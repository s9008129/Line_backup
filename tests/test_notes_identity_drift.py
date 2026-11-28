"""Synthetic filesystem epochs and crash recovery; never opens LINE or real data."""
from collections import Counter
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
import unittest
from unittest import mock

from line_backup_batch import notes
import test_notes_download_only as download_fixtures
import test_notes_media_verify as media_fixtures
import test_notes_restart as restart_fixtures


class StatView:
    """Change one observed stat field without changing any fixture file."""

    def __init__(self, original, **overrides):
        self.original = original
        self.overrides = overrides

    def __getattr__(self, name):
        return self.overrides.get(name, getattr(self.original, name))


@contextmanager
def device_epoch(offset=1000003):
    """Observe one consistent old device epoch, then return to the real one.

    All three stat surfaces agree during an epoch. The actual filesystem,
    immutable event bytes, inodes, content and timestamps remain unchanged.
    """
    def shifted(original):
        def observe(*args, **kwargs):
            result = original(*args, **kwargs)
            return StatView(result, st_dev=result.st_dev + offset)
        return observe

    # Python 3.9 pathlib caches stat functions in its accessor. Explicitly
    # include Path's surface so one simulated epoch never mixes two devices.
    with mock.patch.object(os, 'stat', side_effect=shifted(os.stat)), \
            mock.patch.object(os, 'lstat', side_effect=shifted(os.lstat)), \
            mock.patch.object(os, 'fstat', side_effect=shifted(os.fstat)), \
            mock.patch.object(Path, 'stat', lambda path, **kw: os.stat(path, **kw)), \
            mock.patch.object(Path, 'lstat', lambda path: os.lstat(path)):
        yield


class NotesIdentityDriftTests(unittest.TestCase):
    def setUp(self):
        # Composition avoids discovering the fixture TestCase's tests twice.
        self.flow = download_fixtures.DownloadOnlyTests()
        self.flow.setUp()
        self.addCleanup(self.flow.doCleanups)

    def completed(self, label):
        ledger, attempt, _ = self.flow.attempt(
            label, kind=notes.PHOTO, content=media_fixtures.png())
        completion = self.flow.check(ledger, attempt)
        target = (Path(completion['data']['destination']) /
                  completion['data']['target_file']['name'])
        return ledger, completion, target

    def assert_events_preserved(self, before, records):
        after = self.flow.helper.event_bytes(records)
        for name, raw in before.items():
            self.assertEqual(after[name], raw, name)

    def test_completion_device_epoch_does_not_change_summary_or_restart(self):
        with device_epoch():
            ledger, completion, target = self.completed('epoch-completed')
        self.assertNotEqual(completion['data']['target_file']['device'],
                            target.stat().st_dev)
        before = self.flow.helper.event_bytes(ledger.records)
        records = self.flow.helper.reopen(ledger)
        summary = records.summary()
        self.assertEqual(summary['local_counts']['VERIFIED_PRESENT'], 1)
        self.assertEqual(summary['local_counts']['LOCAL_CHANGED'], 0)
        self.assertTrue(summary['all_known_media_complete'])
        self.assertNotIn('COMPLETED_FILES_CHANGED', summary['dispatch_blockers'])
        self.assertEqual(records.restart_preview()['status'], 'NO_RESTART_REQUIRED')
        self.assertEqual(self.flow.helper.event_bytes(records), before)

    def test_completed_metadata_and_directory_replacement_keep_content_usable(self):
        for mode in ('inode', 'mtime', 'ctime', 'directory'):
            with self.subTest(mode=mode):
                ledger, completion, target = self.completed('metadata-' + mode)
                before = self.flow.helper.event_bytes(ledger.records)
                original = target.read_bytes()
                if mode == 'inode':
                    replacement = target.with_name('replacement.tmp')
                    replacement.write_bytes(original)
                    os.replace(replacement, target)
                    self.assertNotEqual(target.stat().st_ino,
                                        completion['data']['target_file']['inode'])
                elif mode == 'mtime':
                    info = target.stat()
                    os.utime(target, ns=(info.st_atime_ns,
                                         info.st_mtime_ns + 1000000000))
                elif mode == 'ctime':
                    target.chmod(0o400)
                    self.assertNotEqual(target.stat().st_ctime_ns,
                                        completion['data']['target_file']['ctime_ns'])
                else:
                    directory = target.parent
                    replacement = self.flow.helper.base / 'replacement-directory'
                    original_directory = self.flow.helper.base / 'old-directory'
                    shutil.copytree(directory, replacement)
                    directory.rename(original_directory)
                    replacement.rename(directory)
                    self.assertNotEqual(directory.stat().st_ino,
                                        completion['data']['target_directory']['inode'])
                records = self.flow.helper.reopen(ledger)
                self.assertEqual(records.summary()['local_counts']['VERIFIED_PRESENT'], 1)
                self.assertEqual(target.read_bytes(), original)
                self.assertEqual(self.flow.helper.event_bytes(records), before)

    def test_publish_resumes_original_transaction_across_device_epoch_at_each_progress(self):
        for state in ('plan-only', 'DIRECTORY_READY', 'FILE_LINKED', 'SOURCE_REMOVED'):
            with self.subTest(state=state):
                with device_epoch():
                    ledger, first, attempt, source, target = \
                        self.flow.pending_second_media('epoch-publish-' + state)
                    if state != 'plan-only':
                        append_progress = notes.NotesRecords._append_progress

                        def interrupt(records, transaction, action, details):
                            result = append_progress(records, transaction, action, details)
                            if action == state:
                                raise OSError('synthetic durable progress interruption')
                            return result

                        with mock.patch.object(notes.NotesRecords, '_append_progress', interrupt):
                            with self.assertRaisesRegex(OSError, 'durable progress interruption'):
                                ledger.records.resume()
                first_target = (Path(first['data']['destination']) /
                                first['data']['target_file']['name'])
                first_identity = self.flow.local_file_identity(first_target)
                before = self.flow.helper.event_bytes(ledger.records)
                before_counts = Counter(event['kind'] for event in ledger.records.events)
                expected_hash = ledger.records._pending_publish_plans()[0]['data']['source']['sha256']
                records = self.flow.helper.reopen(ledger)
                self.assertEqual(records.summary()['local_counts']['LOCAL_CHANGED'], 0)
                resumed = records.resume()
                self.assertEqual(resumed['action'], 'PUBLISH_RESUMED')
                self.assertEqual(resumed['completion']['attempt_id'], attempt['attempt_id'])
                after_counts = Counter(event['kind'] for event in records.events)
                for kind in ('intent', 'outcome', 'verification', 'publish-plan',
                             'restart-confirm', 'restart-copy-plan', 'restart-activation'):
                    self.assertEqual(after_counts[kind], before_counts[kind], kind)
                self.assertEqual(after_counts['completion'], before_counts['completion'] + 1)
                self.assertFalse(source.exists())
                self.assertEqual(target.stat().st_nlink, 1)
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), expected_hash)
                self.assertEqual(self.flow.local_file_identity(first_target), first_identity)
                self.assertFalse((records.current_list_directory / 'versions').exists())
                self.assert_events_preserved(before, records)
                reopened = self.flow.helper.reopen(ledger)
                self.assertEqual(reopened.summary()['local_counts']['VERIFIED_PRESENT'], 2)
                self.assertEqual(reopened.restart_preview()['status'], 'NO_RESTART_REQUIRED')
                settled = self.flow.helper.event_bytes(reopened)
                self.assertEqual(reopened.resume()['action'], 'NO_NAMING_TRANSACTION')
                self.assertEqual(self.flow.helper.event_bytes(reopened), settled)

    def test_verification_before_plan_resumes_after_device_epoch_without_new_verification(self):
        with device_epoch():
            ledger, attempt, _ = self.flow.attempt(
                'epoch-verified', content=media_fixtures.png())
            with mock.patch.object(notes.NotesRecords, '_append_publish_plan',
                                   side_effect=OSError('synthetic before plan')):
                with self.assertRaisesRegex(OSError, 'before plan'):
                    self.flow.check(ledger, attempt)
        before = self.flow.helper.event_bytes(ledger.records)
        records = self.flow.helper.reopen(ledger)
        result = records.download_check(session_id=ledger.session,
                                       attempt_id=attempt['attempt_id'], stability_interval=0)
        self.assertEqual(result['kind'], 'completion')
        self.assertEqual(sum(event['kind'] == 'verification' for event in records.events), 1)
        self.assertEqual(sum(event['kind'] == 'intent' for event in records.events), 1)
        self.assert_events_preserved(before, records)
        self.assertEqual(self.flow.helper.reopen(ledger).summary()['local_counts']['VERIFIED_PRESENT'], 1)

    def test_restart_copy_plan_uses_current_source_but_preserves_historical_reference(self):
        restart = restart_fixtures.NotesRestartTests()
        restart.setUp()
        self.addCleanup(restart.tearDown)
        with device_epoch():
            context = restart.one_media_restart_context('epoch-copy-plan')
            attempt = restart.restart_download(
                restart.records, context['key'], 'fresh.png', media_fixtures.png(),
                context['preview']['restart_id'])
            with mock.patch.object(notes.media_verify, 'copy_exclusive',
                                   side_effect=OSError('synthetic before copy')):
                with self.assertRaisesRegex(OSError, 'before copy'):
                    restart.records.download_check(session_id=restart.session,
                                                   attempt_id=attempt['attempt_id'], stability_interval=0)
        plan = next(event for event in restart.records.events if event['kind'] == 'restart-copy-plan')
        before = restart.event_files()
        source_path = Path(attempt['destination']) / 'fresh.png'
        self.assertNotEqual(plan['data']['source']['device'], source_path.stat().st_dev)
        result = restart.records.restart_resume(session_id=restart.session,
                                                download_only=True, stability_interval=0)
        self.assertEqual(result['action'], 'RESTART_ACTIVATED')
        candidate = next(event for event in restart.records.events if event['kind'] == 'restart-candidate')
        self.assertEqual(candidate['data']['source'], plan['data']['source'])
        self.assertNotEqual(candidate['data']['candidate']['inode'], source_path.stat().st_ino)
        self.assertEqual(sum(event['kind'] == 'restart-copy-plan' for event in restart.records.events), 1)
        self.assertEqual(sum(event['kind'] == 'intent' for event in restart.records.events), 2)
        for name, raw in before.items():
            self.assertEqual(restart.event_files()[name], raw)
        reopened = restart.reopen(restart.records)
        self.assertEqual(reopened.summary()['local_counts']['VERIFIED_PRESENT'], 1)
        self.assertEqual(reopened.restart_resume(session_id=restart.session,
                                                download_only=True)['action'], 'ALREADY_ACTIVATED')

    def test_real_completed_damage_blocks_publish_even_when_device_epoch_is_benign(self):
        for mode in ('hash', 'size', 'missing', 'extra', 'symlink', 'hardlink'):
            with self.subTest(mode=mode):
                with device_epoch():
                    ledger, completion, _, source, _ = self.flow.pending_second_media('damage-' + mode)
                target = Path(completion['data']['destination']) / completion['data']['target_file']['name']
                original_source = source.read_bytes()
                if mode == 'hash':
                    raw = target.read_bytes()
                    target.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
                elif mode == 'size':
                    target.write_bytes(target.read_bytes() + b'changed')
                elif mode == 'missing':
                    target.unlink()
                elif mode == 'extra':
                    (target.parent / 'unexpected.bin').write_bytes(b'extra')
                elif mode == 'symlink':
                    original = target.with_name('original-outside')
                    original = self.flow.helper.base / original.name
                    target.rename(original)
                    target.symlink_to(original)
                else:
                    os.link(target, self.flow.helper.base / 'external-hardlink')
                records = self.flow.helper.reopen(ledger)
                before = self.flow.helper.event_bytes(records)
                self.assertEqual(records.summary()['local_counts']['LOCAL_CHANGED'], 1)
                with self.assertRaisesRegex(notes.NotesError, 'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD'):
                    records.resume()
                self.assertEqual(source.read_bytes(), original_source)
                self.assertEqual(self.flow.helper.event_bytes(records), before)

    def test_whole_completed_directory_missing_retains_completion(self):
        ledger, _, target = self.completed('whole-missing')
        target.parent.rename(self.flow.helper.base / 'removed-completed-directory')
        before = self.flow.helper.event_bytes(ledger.records)
        records = self.flow.helper.reopen(ledger)
        summary = records.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(summary['local_counts']['LOCAL_MISSING'], 1)
        self.assertEqual(self.flow.helper.event_bytes(records), before)

    def test_pending_source_inode_replacement_is_still_refused(self):
        with device_epoch():
            ledger, _, _, source, target = self.flow.pending_second_media('source-inode')
        replacement = source.with_name('replacement.tmp')
        replacement.write_bytes(source.read_bytes())
        os.replace(replacement, source)
        records = self.flow.helper.reopen(ledger)
        with self.assertRaisesRegex(notes.NotesError, 'PUBLISH_SOURCE_CHANGED'):
            records.resume()
        self.assertTrue(source.exists())
        self.assertFalse(target.exists())
        self.assertEqual(sum(event['kind'] == 'completion' for event in records.events), 1)

    def test_same_operation_cross_device_hardlink_is_still_refused(self):
        ledger, _, _, source, target = self.flow.pending_second_media('live-cross-device')
        original_stat = os.stat
        original_lstat = os.lstat

        def cross_device(path, *args, **kwargs):
            info = original_stat(path, *args, **kwargs)
            return (StatView(info, st_dev=info.st_dev + 1)
                    if Path(path) == target.parent else info)

        def cross_device_lstat(path, *args, **kwargs):
            info = original_lstat(path, *args, **kwargs)
            return (StatView(info, st_dev=info.st_dev + 1)
                    if Path(path) == target.parent else info)

        with mock.patch.object(os, 'stat', side_effect=cross_device), \
                mock.patch.object(os, 'lstat', side_effect=cross_device_lstat), \
                mock.patch.object(Path, 'stat', lambda path, **kw: os.stat(path, **kw)):
            with self.assertRaisesRegex(notes.NotesError, 'CROSS_DEVICE_PUBLISH_UNAVAILABLE'):
                ledger.records.resume()
        self.assertTrue(source.exists())
        self.assertFalse(target.exists())

    def test_unknown_and_no_outcome_are_not_unlocked_by_device_epoch(self):
        for outcome in (None, 'UNKNOWN'):
            with self.subTest(outcome=outcome):
                with device_epoch():
                    ledger, attempt, source = self.flow.attempt(
                        'epoch-outcome-' + str(outcome), outcome=outcome,
                        content=media_fixtures.png())
                records = self.flow.helper.reopen(ledger)
                before = self.flow.helper.event_bytes(records)
                with self.assertRaisesRegex(notes.NotesError, 'KNOWN_DOWNLOAD_FINISH_REQUIRED'):
                    records.download_check(session_id=ledger.session,
                                           attempt_id=attempt['attempt_id'], stability_interval=0)
                with self.assertRaisesRegex(notes.NotesError, 'UNRESOLVED_ATTEMPT_BLOCKS_CHANGE'):
                    records._assert_no_unknown_attempts()
                self.assertTrue(source.exists())
                self.assertEqual(self.flow.helper.event_bytes(records), before)

    def test_mutation_during_read_still_refuses_completion(self):
        ledger, completion, target = self.completed('read-race')
        inode = target.stat().st_ino
        original_fstat = os.fstat
        for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'):
            with self.subTest(field=field):
                reads = 0

                def changing(fd):
                    nonlocal reads
                    result = original_fstat(fd)
                    if result.st_ino == inode:
                        reads += 1
                        if reads == 2:
                            return StatView(result, **{field: getattr(result, field) + 1})
                    return result

                with mock.patch.object(os, 'fstat', side_effect=changing):
                    availability = ledger.records._completion_availability()
                self.assertEqual(availability[completion['data']['media_key']], notes.LOCAL_CHANGED)


if __name__ == '__main__':
    unittest.main()
