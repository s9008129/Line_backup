"""Offline integrity tests for reveal evidence in existing Notes v2 bundles."""
import json
import shutil
import tempfile
import unittest
from unittest import mock
import uuid
from pathlib import Path

from line_backup_batch import notes, notes_evidence
from line_backup_batch.daily import digest
from line_backup_batch.notes import NotesCollection, NotesError, NotesRecords


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TASKS = ROOT / '.local' / 'line-backup' / 'tasks'


class NotesRevealEvidenceTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='.line-notes-reveal-', dir=str(PRIVATE_TASKS))
        self.addCleanup(self.temporary.cleanup)
        self.outer = Path(self.temporary.name).resolve()
        self.base = self.outer / 'fixture'
        self.base.mkdir()
        self.sentinel_path = self.outer / 'active-fallback.json'
        self.sentinel_bytes = json.dumps(
            dict(schema='line-notes-active-task/v1',
                 records_root=str(self.base / 'fallback-records'),
                 local_list_id='synthetic-fallback-list',
                 session_id='synthetic-fallback-session',
                 updated_at='synthetic-sentinel'),
            sort_keys=True, separators=(',', ':')).encode('utf-8')
        self.sentinel_path.write_bytes(self.sentinel_bytes)
        self.addCleanup(self._assert_locator_cleanup_boundary)
        self.addCleanup(self._cleanup_fixture)
        self.active_path = self.base / 'active-notes-task.json'
        self.active_path_patch = mock.patch.object(
            notes, '_active_task_path', return_value=self.sentinel_path)
        self.active_path_mock = self.active_path_patch.start()
        self.addCleanup(self.active_path_patch.stop)
        self.active_path_mock.return_value = self.active_path
        self.assertEqual(notes._active_task_path(), self.active_path)
        self.asset_dir = self.base / 'assets'
        self.asset_dir.mkdir()
        self.pack_dir = self.base / 'packs'
        self.pack_dir.mkdir()
        self.statement_bytes = b'reveal statement\n'
        self.visible_statement_bytes = b'TOOLBAR_VISIBLE\n'
        self.transient_statement_bytes = b'REVEAL_TRANSIENT\n'
        self.before_bytes = b'before screenshot\n'
        self.after_bytes = b'after screenshot\n'
        self.ax_bytes = b'viewer AX bytes\n'
        self.input_receipt_bytes = b'{"result":"synthetic"}\n'
        self.visible_timeline_bytes = (
            b'{"capture_wait_semantics":"UNKNOWN","state":"TOOLBAR_VISIBLE"}\n')
        self.transient_timeline_bytes = (
            b'{"capture_wait_semantics":"UNKNOWN",'
            b'"state":"REVEAL_TRANSIENT"}\n')
        self.statement = self.write_asset(
            'statement.txt', self.statement_bytes)
        self.visible_statement = self.write_asset(
            'visible-statement.txt', self.visible_statement_bytes)
        self.transient_statement = self.write_asset(
            'transient-statement.txt', self.transient_statement_bytes)
        self.before = self.write_asset('before.bin', self.before_bytes)
        self.after = self.write_asset('after.bin', self.after_bytes)
        self.ax = self.write_asset('viewer.ax', self.ax_bytes)
        self.input_receipt = self.write_asset(
            'input-receipt.json', self.input_receipt_bytes)
        self.visible_timeline = self.write_asset(
            'visible-timeline.json', self.visible_timeline_bytes)
        self.transient_timeline = self.write_asset(
            'transient-timeline.json', self.transient_timeline_bytes)

        self.identity = notes.list_identity(visual_key='reveal-list')
        self.list_key = notes.list_key(self.identity)
        self.collection = NotesCollection(str(self.base / 'collection'))
        init_bundle = self.bundle(list_key=self.list_key)['bundle_path']
        self.summary = self.collection.create(
            photo_root=str(self.base / 'photos'),
            display_name='Synthetic Reveal List',
            identity=self.identity,
            binding_evidence=init_bundle,
            history_scope_evidence=init_bundle)
        self.records = NotesRecords(self.summary['records_root'])
        self.session = 'synthetic-reveal-session'
        self.records.bind(
            session_id=self.session,
            observation=self.bundle(list_key=self.list_key)['bundle_path'],
            handoff=self.bundle(list_key=self.list_key)['bundle_path'])

        self.post_identity = notes.post_identity(visual_key='reveal-post')
        self.post_key = notes.post_key(self.list_key, self.post_identity)
        self.media_identity = notes.media_identity(
            kind=notes.UNCLASSIFIED, visual_key='reveal-media')
        self.media_key = notes.media_key(
            self.list_key, self.post_key, self.media_identity)
        self.scan = self.records.scan(
            session_id=self.session, action='START',
            evidence=self.bundle(list_key=self.list_key)['bundle_path'])
        self.scan_id = self.scan['scan_id']
        self.scan_context = dict(list_key=self.list_key, scan_id=self.scan_id)

    def write_asset(self, name, raw):
        path = self.asset_dir / name
        path.write_bytes(raw)
        return path

    @staticmethod
    def _remove_fixture_path(path):
        shutil.rmtree(path, ignore_errors=True)

    def _cleanup_fixture(self):
        self._remove_fixture_path(self.base)

    def _assert_locator_cleanup_boundary(self):
        self.assertFalse(self.base.exists(), 'inner fixture was not removed')
        self.assertEqual(self.sentinel_path.read_bytes(), self.sentinel_bytes)

    def bundle(self, *, assets=None, statement=None, **context):
        return notes_evidence.create_bundle(
            statement=str(self.statement if statement is None else statement),
            assets=(assets if assets is not None else [
                ('screenshot', str(self.before))]),
            context=context,
            output_dir=str(self.pack_dir / uuid.uuid4().hex))

    def prepare_post(self, *, evidence=None):
        self.records.page(
            session_id=self.session, scan_id=self.scan_id, page_index=0,
            posts=[dict(identity=self.post_identity,
                        date_summary='synthetic date')],
            top_reached=True, bottom_reached=True, overlap_keys=[],
            evidence=self.bundle(**self.scan_context)['bundle_path'])
        self.records.scan(
            session_id=self.session, action='FINISH', scan_id=self.scan_id,
            evidence=self.bundle(**self.scan_context)['bundle_path'])
        post_evidence = (
            evidence if evidence is not None else
            self.bundle(
                list_key=self.list_key, post_key=self.post_key,
                scan_id=self.scan_id)['bundle_path'])
        self.records.record_post(
            session_id=self.session, post_key_value=self.post_key,
            date_summary='synthetic date', media_count=1, text_sha256=None,
            evidence=post_evidence, scan_id=self.scan_id)

    def assert_saved_bundle(self, outer_ref, expected_context,
                            statement_raw, expected_assets):
        loaded = notes_evidence.load_saved_evidence(
            self.records.records / 'evidence', outer_ref, expected_context)
        self.assertEqual(loaded['classification'], 'REFERENCE_VERIFIED')
        self.assertEqual(loaded['data']['context'], expected_context)
        statement_ref = loaded['data']['statement_ref']
        self.assertEqual(statement_ref['role'], 'statement')
        self.assertEqual(statement_ref['bytes'], len(statement_raw))
        self.assertEqual(statement_ref['sha256'], digest(statement_raw))
        self.assertEqual(
            [ref['role'] for ref in loaded['data']['assets']],
            [role for role, _ in expected_assets])
        for ref, (role, raw) in zip(
                loaded['data']['assets'], expected_assets):
            self.assertEqual(ref['role'], role)
            self.assertEqual(ref['bytes'], len(raw))
            self.assertEqual(ref['sha256'], digest(raw))
        audit = notes_evidence.audit_saved_evidence(
            self.records.records / 'evidence', outer_ref, expected_context)
        self.assertTrue(audit['integrity_ok'])
        self.assertEqual(audit['reference_check'], 'VERIFIED')
        return loaded

    def test_visible_and_transient_bytes_survive_events_and_missing_sources(self):
        post_context = dict(
            list_key=self.list_key, post_key=self.post_key,
            scan_id=self.scan_id)
        visible_assets = [
            ('screenshot', str(self.before)),
            ('ax', str(self.ax)),
            ('observation', str(self.visible_timeline)),
        ]
        visible_bundle = self.bundle(
            assets=visible_assets, statement=self.visible_statement,
            **post_context)['bundle_path']
        self.prepare_post(evidence=visible_bundle)

        media_context = dict(
            list_key=self.list_key, post_key=self.post_key,
            scan_id=self.scan_id)
        wrong_post = notes.post_identity(visual_key='other-post')
        wrong_bundle = self.bundle(
            list_key=self.list_key,
            post_key=notes.post_key(self.list_key, wrong_post),
            scan_id=self.scan_id)['bundle_path']
        with self.assertRaisesRegex(NotesError, 'EVIDENCE_CONTEXT_MISMATCH'):
            self.records.record_media(
                session_id=self.session, post_key_value=self.post_key,
                items=[{'identity': self.media_identity}], missing=[],
                evidence=wrong_bundle, scan_id=self.scan_id)
        self.assertFalse(any(
            event['kind'] == 'media' for event in self.records.events))

        transient_assets = [
            ('screenshot', str(self.before)),
            ('ax', str(self.ax)),
            ('input_receipt', str(self.input_receipt)),
            ('screenshot', str(self.after)),
            ('ax', str(self.ax)),
            ('observation', str(self.transient_timeline)),
        ]
        reveal_bundle = self.bundle(
            assets=transient_assets, statement=self.transient_statement,
            **media_context)['bundle_path']
        self.records.record_media(
            session_id=self.session, post_key_value=self.post_key,
            items=[{'identity': self.media_identity}], missing=[],
            evidence=reveal_bundle, scan_id=self.scan_id)
        post_event = next(
            event for event in self.records.events if event['kind'] == 'post')
        media_event = next(
            event for event in self.records.events if event['kind'] == 'media')
        expected_post_context = notes_evidence.normalize_context(post_context)
        expected_media_context = notes_evidence.normalize_context(media_context)

        for path in (self.statement, self.visible_statement,
                     self.transient_statement, self.before, self.after,
                     self.ax, self.input_receipt, self.visible_timeline,
                     self.transient_timeline):
            path.unlink()
        self.assertFalse(any(path.exists() for path in (
            self.statement, self.visible_statement, self.transient_statement,
            self.before, self.after, self.ax, self.input_receipt,
            self.visible_timeline, self.transient_timeline)))

        self.assert_saved_bundle(
            post_event['data']['evidence'], expected_post_context,
            self.visible_statement_bytes,
            [('screenshot', self.before_bytes),
             ('ax', self.ax_bytes),
             ('observation', self.visible_timeline_bytes)])
        loaded_media = self.assert_saved_bundle(
            media_event['data']['evidence'], expected_media_context,
            self.transient_statement_bytes,
            [('screenshot', self.before_bytes),
             ('ax', self.ax_bytes),
             ('input_receipt', self.input_receipt_bytes),
             ('screenshot', self.after_bytes),
             ('ax', self.ax_bytes),
             ('observation', self.transient_timeline_bytes)])
        ax_refs = [
            ref for ref in loaded_media['data']['assets']
            if ref['role'] == 'ax']
        self.assertEqual(len(ax_refs), 2)
        self.assertEqual(ax_refs[0]['sha256'], ax_refs[1]['sha256'])
        self.assertNotEqual(digest(self.before_bytes), digest(self.after_bytes))
        self.assertEqual(
            json.loads(self.active_path.read_text(encoding='utf-8'))['session_id'],
            self.session)

        summary = self.records.summary()
        self.assertEqual(summary['status_counts']['PENDING'], 1)
        self.assertEqual(summary['media'][0]['status'], 'PENDING')
        self.assertEqual(summary['unresolved_attempts'], [])
        self.assertFalse(summary['all_known_media_complete'])
        self.assertFalse(any(
            event['kind'] in ('intent', 'outcome')
            for event in self.records.events))

        child = next(
            ref for ref in loaded_media['data']['assets']
            if ref['role'] == 'screenshot')
        child_path = self.records.records / 'evidence' / child['sha256']
        child_path.write_bytes(b'tampered synthetic screenshot\n')
        with self.assertRaisesRegex(
                notes_evidence.NotesEvidenceError, 'EVIDENCE_CHILD_DRIFT'):
            notes_evidence.load_saved_evidence(
                self.records.records / 'evidence',
                media_event['data']['evidence'], expected_media_context)
        audit = notes_evidence.audit_saved_evidence(
            self.records.records / 'evidence',
            media_event['data']['evidence'], expected_media_context)
        self.assertFalse(audit['integrity_ok'])
        self.assertEqual(audit['reference_check'], 'REFERENCE_CHECK_NOT_AVAILABLE')
        self.assertTrue(any(
            child['status'] == 'DRIFT' and
            child['error'] == 'EVIDENCE_CHILD_DRIFT'
            for child in audit['child_assets']))


if __name__ == '__main__':
    unittest.main()
