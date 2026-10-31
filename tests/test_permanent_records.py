"""Synthetic permanent-memory lifecycle checks; no LINE or private photo input."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import test_daily_records as helpers
from line_backup_batch.daily import DailyRecords, DailyError, album_key
from line_backup_batch import daily as daily_module
from line_backup_batch import record_store


class PermanentRecordsTests(unittest.TestCase):
    # Reuse fixture operations, not the legacy test class or its 73 test cases.
    setUpClass = classmethod(helpers.DailyTests.setUpClass.__func__)
    tearDownClass = classmethod(helpers.DailyTests.tearDownClass.__func__)
    evidence = helpers.DailyTests.evidence
    bind = helpers.DailyTests.bind
    page = helpers.DailyTests.page
    detail = helpers.DailyTests.detail
    intent = helpers.DailyTests.intent
    finished = helpers.DailyTests.finished
    complete = helpers.DailyTests.complete

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='permanent-', dir=self.fixtures.name)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'photos'
        self.root.mkdir()
        self.collection = self.base / 'backup-records'
        self.counter = 0
        self.session = 'synthetic-permanent-session'
        self.cards = [dict(start_date='2026-01-01', end_date='2026-01-02', expected_images=2,
                           visual_key='synthetic-permanent-cover-' + str(n)) for n in range(2)]
        self.group = record_store.create_group(self.root, self.init_data(), self.collection)
        self.records_root = Path(self.group['records_root'])
        self.store = DailyRecords(records_root=self.records_root)
        self.bind()
        self.store.history(session_id=self.session, scope_evidence=self.evidence('synthetic empty history'), entries=[])
        self.store.start_scan(session_id=self.session)

    def tearDown(self):
        self.temp.cleanup()

    def init_data(self):
        return dict(binding_evidence=self.evidence('synthetic foreground'),
                    history_scope_evidence=self.evidence('synthetic history scope'), layout='FLAT_V1')

    def test_evidence_directory_symlink_refused_before_writing(self):
        evidence = self.records_root / 'evidence'
        preserved = self.base / 'preserved-evidence'
        evidence.rename(preserved)
        foreign = self.base / 'foreign'
        foreign.mkdir()
        evidence.symlink_to(foreign)
        with self.assertRaises((DailyError, OSError)):
            self.store.bind(session_id='synthetic-symlink-refusal',
                local_group_id=self.group['local_group_id'],
                observation=self.evidence('fresh observation'), handoff=self.evidence('fresh handoff'))
        self.assertEqual(list(foreign.iterdir()), [])

    def test_finder_metadata_does_not_hide_registered_history(self):
        (self.collection / '.DS_Store').write_bytes(b'synthetic Finder metadata')
        result = record_store.groups(self.collection)
        self.assertEqual([r['local_group_id'] for r in result['groups']], [self.group['local_group_id']])

    def test_pristine_collection_is_read_only_empty_but_known_missing_history_refuses(self):
        collection = self.base / 'missing-store'
        self.assertEqual(record_store.groups(collection)['groups'], [])
        self.assertFalse(collection.exists())
        active = self.base / '.local/line-backup/active-task.json'
        active.parent.mkdir(parents=True)
        active.write_text(json.dumps({'records_root': str(collection / self.group['local_group_id'])}))
        with mock.patch.object(record_store, 'CORE_ROOT', self.base):
            with self.assertRaisesRegex(DailyError, 'KNOWN_RECORDS_MISSING_NO_EMPTY_HISTORY'):
                record_store.groups(collection)
            with self.assertRaisesRegex(DailyError, 'KNOWN_RECORDS_MISSING_NO_EMPTY_HISTORY'):
                record_store.create_group(self.root, self.init_data(), collection)
        self.assertFalse(collection.exists())

    def seed_completed(self):
        self.page(self.cards, top=True)
        self.page(self.cards, bottom=True)
        attempt = self.intent(self.cards[0])
        for n in (1, 2):
            (Path(attempt['destination']) / ('%d.png' % n)).write_bytes(helpers.png())
        self.finished(attempt)
        completion = self.complete(attempt)
        return attempt, completion

    def event_bytes(self):
        return {p.name: p.read_bytes() for p in (self.records_root / 'events').iterdir()}

    def first_album(self, store=None):
        return next(row for row in (store or self.store).memory()['albums']
                    if row['album_key'] == album_key(self.cards[0]))

    def run_cli(self, *args, expected=0):
        completed = subprocess.run(
            ['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily', *map(str, args)],
            cwd=daily_module.CORE_ROOT, env=dict(os.environ, PYTHONPATH='src'),
            capture_output=True, text=True)
        self.assertEqual(completed.returncode, expected, completed.stderr + completed.stdout)
        self.assertNotIn('Traceback', completed.stderr + completed.stdout)
        result = json.loads(completed.stdout)
        self.assertFalse(result['dispatch_authorized'])
        if expected == 4:
            self.assertEqual(result['status'], 'REFUSED')
        return result

    def test_cli_init_reads_groups_and_destination_without_legacy_root(self):
        photo_root = self.base / 'cli-photos'
        photo_root.mkdir()
        collection = self.base / 'cli-records'
        source = self.evidence(self.init_data())
        initialized = self.run_cli('init', '--root', photo_root, '--records-root', collection,
                                   '--input', source)['result']
        records = Path(initialized['records_root'])
        self.assertEqual(records.parent, collection)
        self.assertFalse((photo_root / 'backup-records').exists())
        memory = self.run_cli('memory', '--records-root', records)['result']
        self.assertEqual(memory['local_group_id'], initialized['local_group_id'])
        self.run_cli('summary', '--records-root', records)
        registered = self.run_cli('groups', '--records-root', collection)['result']['groups']
        self.assertEqual([row['local_group_id'] for row in registered], [initialized['local_group_id']])
        binding = self.evidence(dict(session_id='cli-session',
            local_group_id=initialized['local_group_id'],
            observation=self.evidence('synthetic cli observation'),
            handoff=self.evidence('synthetic cli handoff')))
        self.run_cli('bind', '--records-root', records, '--input', binding)
        shutil.rmtree(photo_root)
        self.run_cli('memory', '--records-root', records)
        self.run_cli('summary', '--records-root', records)
        new_root = self.base / 'cli-next-photos'
        new_root.mkdir()
        result = self.run_cli('destination', '--records-root', records, '--root', new_root,
            '--session-id', 'cli-session', '--source', self.evidence('synthetic new cli destination'))['result']
        self.assertEqual(result['destination'], str(new_root))
        refused = self.run_cli('destination', '--records-root', records, '--root', new_root,
            '--session-id', 'wrong-session', '--source', self.evidence('synthetic invalid binding'), expected=4)
        self.assertIn('FRESH_FOREGROUND_BINDING_REQUIRED', refused['reason'])

    def test_new_group_header_tampering_is_refused_by_api_and_module_cli(self):
        header = self.records_root / 'group.json'
        original = header.read_bytes()
        changed = json.loads(original)
        changed['destination_inode'] += 1
        header.write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaisesRegex(DailyError, 'MIGRATED_RECORD_CHANGED'):
            self.store.memory()
        refused = self.run_cli('memory', '--records-root', self.records_root, expected=4)
        self.assertIn('MIGRATED_RECORD_CHANGED', refused['reason'])
        header.write_bytes(original)

    def test_pending_initial_naming_stays_blocked_after_photo_root_removal(self):
        self.page(self.cards, top=True)
        attempt = self.intent(self.cards[0])
        for n in (1, 2):
            (Path(attempt['destination']) / ('%d.png' % n)).write_bytes(helpers.png())
        self.finished(attempt)
        with mock.patch.object(daily_module, 'exclusive_rename',
                               side_effect=OSError('synthetic first naming rename interruption')):
            with self.assertRaisesRegex(OSError, 'synthetic first naming rename interruption'):
                self.complete(attempt)
        with self.store.locked():
            self.assertEqual(len(self.store._pending_initial_transactions()), 1)
        shutil.rmtree(self.root)
        reopened = DailyRecords(records_root=self.records_root)
        self.assertNotEqual(self.first_album(reopened)['status'], 'COMPLETED')
        self.bind(session='naming-recovery-session', store=reopened)
        new_root = self.base / 'after-interrupted-naming'
        new_root.mkdir()
        before = self.event_bytes()
        with self.assertRaisesRegex(DailyError, 'PENDING_NAMING_TRANSACTION'):
            reopened.destination(root=new_root, session_id='naming-recovery-session',
                                 source=self.evidence('synthetic new naming destination'))
        self.assertEqual(self.event_bytes(), before)

    def test_real_imageio_completed_survives_album_and_entire_photo_root_removal(self):
        attempt, completion = self.seed_completed()
        self.assertEqual(completion['proof']['imageio']['verdict'], 'PASS')
        self.assertEqual(self.first_album()['local_files'], 'VERIFIED_PRESENT')
        immutable = self.event_bytes()
        shutil.rmtree(attempt['destination'])
        reopened = DailyRecords(records_root=self.records_root)
        album = self.first_album(reopened)
        self.assertEqual(reopened.memory()['schema'], 'line-backup-memory/v2')
        self.assertEqual((album['status'], album['local_files']), ('COMPLETED', 'LOCAL_MISSING'))
        with self.assertRaisesRegex(DailyError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            reopened.intent(session_id=self.session, identity=self.cards[0])
        shutil.rmtree(self.root)
        self.assertEqual(self.first_album(DailyRecords(records_root=self.records_root))['status'], 'COMPLETED')
        self.assertEqual(self.event_bytes(), immutable)
        self.assertFalse(reopened.memory()['external_copy_verified'])

    def test_new_destination_only_accepts_new_album_and_keeps_historical_path(self):
        attempt, _ = self.seed_completed()
        original = attempt['destination']
        shutil.rmtree(self.root)
        self.root.mkdir()
        self.bind(session='synthetic-new-session')
        self.session = 'synthetic-new-session'
        self.store.destination(root=self.root, session_id=self.session,
                               source=self.evidence('synthetic new empty destination approval'))
        self.store.start_scan(session_id=self.session)
        self.page(self.cards, top=True)
        self.page(self.cards, bottom=True)
        with self.assertRaisesRegex(DailyError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            self.store.intent(session_id=self.session, identity=self.cards[0])
        new_attempt = self.intent(self.cards[1])
        self.assertTrue(Path(new_attempt['destination']).is_relative_to(self.root))
        self.assertEqual(self.first_album()['current_destination'], original)
        self.assertEqual(self.first_album()['local_files'], 'LOCAL_MISSING')

    def test_recreated_root_requires_explicit_new_destination_binding(self):
        self.seed_completed()
        self.root.rename(self.base / 'retired-photos')
        self.root.mkdir()
        before = self.event_bytes()
        with self.assertRaisesRegex(DailyError, 'DESTINATION_BINDING_CHANGED'):
            self.store.intent(session_id=self.session, identity=self.cards[1])
        self.assertEqual(before, self.event_bytes())

    def test_partial_file_loss_keeps_completed_but_blocks_new_dispatch(self):
        attempt, completion = self.seed_completed()
        (Path(attempt['destination']) / completion['proof']['manifest'][0]['name']).unlink()
        self.assertEqual((self.first_album()['status'], self.first_album()['local_files']),
                         ('COMPLETED', 'LOCAL_CHANGED'))
        before = self.event_bytes()
        with self.assertRaisesRegex(DailyError, 'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD'):
            self.store.intent(session_id=self.session, identity=self.cards[1])
        self.assertEqual(self.event_bytes(), before)

    def test_symlink_album_is_changed_not_missing_and_cannot_unlock_dispatch(self):
        attempt, _ = self.seed_completed()
        destination = Path(attempt['destination'])
        saved = self.base / 'symlink-target'
        destination.rename(saved)
        destination.symlink_to(saved, target_is_directory=True)
        self.assertEqual(self.first_album()['local_files'], 'LOCAL_CHANGED')
        with self.assertRaisesRegex(DailyError, 'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD'):
            self.store.intent(session_id=self.session, identity=self.cards[1])

    def test_unknown_attempt_survives_deleted_photos_and_cannot_rebind_or_replay(self):
        self.page(self.cards, top=True)
        self.intent(self.cards[0])
        shutil.rmtree(self.root)
        self.assertEqual(self.first_album()['status'], 'UNKNOWN')
        self.root.mkdir()
        self.bind(session='synthetic-new-session')
        before = self.event_bytes()
        with self.assertRaisesRegex(DailyError, 'UNRESOLVED_ATTEMPT|PENDING_NAMING'):
            self.store.destination(root=self.root, session_id='synthetic-new-session',
                                   source=self.evidence('synthetic new destination'))
        self.assertEqual(self.event_bytes(), before)

    def test_same_album_identity_does_not_merge_across_registered_groups(self):
        self.seed_completed()
        other_root = self.base / 'other-photos'
        other_root.mkdir()
        other = record_store.create_group(other_root, self.init_data(), self.collection)
        other_store = DailyRecords(records_root=other['records_root'])
        self.bind(group=other, session='synthetic-other-group', store=other_store)
        other_store.history(session_id='synthetic-other-group',
                            scope_evidence=self.evidence('other empty history'), entries=[])
        other_store.start_scan(session_id='synthetic-other-group')
        original_store, original_session = self.store, self.session
        try:
            self.store, self.session = other_store, 'synthetic-other-group'
            self.page(self.cards, top=True)
        finally:
            self.store, self.session = original_store, original_session
        groups = record_store.groups(self.collection)['groups']
        statuses = {row['local_group_id']: row['albums'][0]['status'] for row in groups}
        self.assertEqual(statuses[self.group['local_group_id']], 'COMPLETED')
        self.assertEqual(statuses[other['local_group_id']], 'INCOMPLETE')

    def test_missing_or_corrupt_catalog_never_initializes_empty_history(self):
        path = self.collection / 'index.json'
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(DailyError, 'RECORD_INDEX_MISSING'):
            self.store.memory()
        path.write_bytes(b'{bad json')
        with self.assertRaisesRegex(DailyError, 'INVALID_RECORD_INDEX'):
            record_store.groups(self.collection)
        path.write_bytes(original)
        self.assertEqual(self.store.memory()['local_group_id'], self.group['local_group_id'])

    def legacy_source(self):
        root = self.base / 'legacy-photos'
        root.mkdir()
        source = DailyRecords(root)
        group = source.initialize(**self.init_data())
        source.bind(session_id='legacy-session', local_group_id=group['local_group_id'],
                    observation=self.evidence('legacy observation'), handoff=self.evidence('legacy handoff'))
        source.history(session_id='legacy-session', scope_evidence=self.evidence('legacy no history'), entries=[])
        return root, source, group

    def test_migration_preserves_raw_history_and_is_idempotent_without_double_writers(self):
        root, source, group = self.legacy_source()
        raw = {str(p.relative_to(source.records)): p.read_bytes()
               for p in source.records.rglob('*.json')}
        migrated = record_store.migrate(root, self.collection)
        migrated_root = Path(migrated['records_root'])
        for relative, content in raw.items():
            self.assertEqual((source.records / relative).read_bytes(), content)
            self.assertEqual((migrated_root / relative).read_bytes(), content)
        with self.assertRaisesRegex(DailyError, 'LEGACY_RECORDS_READ_ONLY'):
            DailyRecords(root)
        self.assertEqual(DailyRecords(records_root=migrated_root).memory()['local_group_id'],
                         group['local_group_id'])
        replay = record_store.migrate(root, self.collection)
        self.assertEqual(replay['records_root'], migrated['records_root'])
        self.assertEqual(len(record_store.groups(self.collection)['groups']), 2)

    def test_migration_resumes_after_redirect_before_catalog_publish(self):
        root, source, group = self.legacy_source()
        real_register = record_store.register
        with mock.patch.object(record_store, 'register', side_effect=OSError('synthetic publish interruption')):
            with self.assertRaisesRegex(OSError, 'synthetic publish interruption'):
                record_store.migrate(root, self.collection)
        self.assertTrue((source.records / 'record-store.json').exists())
        with self.assertRaisesRegex(DailyError, 'LEGACY_RECORDS_READ_ONLY'):
            DailyRecords(root)
        with mock.patch.object(record_store, 'register', wraps=real_register):
            result = record_store.migrate(root, self.collection)
        self.assertEqual(DailyRecords(records_root=result['records_root']).memory()['local_group_id'],
                         group['local_group_id'])
        self.assertEqual(len(record_store.groups(self.collection)['groups']), 2)

    def test_migrated_completion_survives_removal_of_original_photos_and_evidence(self):
        root, source, group = self.legacy_source()
        original_context = self.root, self.store, self.group, self.session
        try:
            self.root, self.store, self.group, self.session = root, source, group, 'legacy-session'
            source.start_scan(session_id=self.session)
            _, completion = self.seed_completed()
        finally:
            self.root, self.store, self.group, self.session = original_context
        result = record_store.migrate(root, self.collection)
        shutil.rmtree(root)
        # Every original helper evidence file is expendable after migration;
        # the current and migrated stores must use their permanent copies.
        for evidence in self.base.glob('evidence-*.txt'):
            evidence.unlink()
        reopened = DailyRecords(records_root=result['records_root'])
        album = self.first_album(reopened)
        self.assertEqual((album['status'], album['local_files']), ('COMPLETED', 'LOCAL_MISSING'))
        self.assertEqual(album['completions'][0]['proof'], completion['proof'])

    def test_first_migration_resumes_before_first_index_publication(self):
        root, _, group = self.legacy_source()
        empty_collection = self.base / 'first-migration-records'
        with mock.patch.object(record_store, 'register', side_effect=OSError('synthetic first publish interruption')):
            with self.assertRaisesRegex(OSError, 'synthetic first publish interruption'):
                record_store.migrate(root, empty_collection)
        result = record_store.migrate(root, empty_collection)
        self.assertEqual(DailyRecords(records_root=result['records_root']).memory()['local_group_id'],
                         group['local_group_id'])
        self.assertEqual(len(record_store.groups(empty_collection)['groups']), 1)


if __name__ == '__main__':
    unittest.main()
