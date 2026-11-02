"""Focused tests for Notes v2 evidence bundles and legacy compatibility."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
import uuid

from line_backup_batch import notes, notes_evidence
from line_backup_batch.daily import digest, encoded
from line_backup_batch.notes import NotesCollection, NotesError, NotesRecords


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TASKS = ROOT / '.local' / 'line-backup' / 'tasks'
FIXTURE_ROOT = ROOT / 'tests' / 'fixtures' / 'notes_v1'


class NotesEvidenceTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='.line-notes-evidence-', dir=str(PRIVATE_TASKS))
        self.base = Path(self.temporary.name).resolve()
        self.packs = self.base / 'packs'
        self.packs.mkdir()
        self.statement = self.base / 'statement.txt'
        self.statement.write_bytes(b'synthetic statement\n')
        self.screenshot = self.base / 'screenshot.bin'
        self.screenshot.write_bytes(b'synthetic screenshot bytes')
        self.stdout = self.base / 'stdout.bin'
        self.stdout.write_bytes(b'')
        self.stderr = self.base / 'stderr.bin'
        self.stderr.write_bytes(b'')
        self.context = dict(list_key='a' * 64, scan_id='scan-a')

    def tearDown(self):
        self.temporary.cleanup()

    def make_bundle(self, *, context=None, assets=None):
        return notes_evidence.create_bundle(
            statement=str(self.statement),
            assets=(assets if assets is not None else [
                ('screenshot', str(self.screenshot)),
                ('command_stdout', str(self.stdout)),
                ('command_stderr', str(self.stderr)),
            ]),
            context=(self.context if context is None else context),
            output_dir=str(self.packs / uuid.uuid4().hex))

    def make_records_evidence(self):
        records = self.base / ('records-' + uuid.uuid4().hex)
        (records / 'evidence').mkdir(parents=True)
        return records

    def write_outer(self, raw, *, records=None):
        records = records or self.make_records_evidence()
        sha256 = digest(raw)
        path = records / 'evidence' / sha256
        path.write_bytes(raw)
        return dict(path=str(path), bytes=len(raw), sha256=sha256)

    def test_v2_reopens_after_sources_move_and_keeps_parent_bytes(self):
        created = self.make_bundle()
        records = self.make_records_evidence()
        context = notes_evidence.normalize_context(self.context)
        ref = notes_evidence.preserve_bundle(
            records, created['bundle_path'], context)
        self.assertEqual(set(ref), {'path', 'bytes', 'sha256'})
        self.assertEqual(Path(ref['path']).parent, records / 'evidence')
        self.assertEqual(Path(ref['path']).name, ref['sha256'])
        saved_parent = Path(ref['path']).read_bytes()
        self.assertEqual(saved_parent, Path(created['bundle_path']).read_bytes())

        self.statement.unlink()
        self.screenshot.unlink()
        self.stdout.unlink()
        self.stderr.unlink()
        loaded = notes_evidence.load_saved_evidence(
            records / 'evidence', ref, context)
        self.assertEqual(loaded['classification'], 'REFERENCE_VERIFIED')
        self.assertEqual(loaded['data']['schema'], notes_evidence.SCHEMA)
        self.assertEqual(loaded['data']['context'], context)

    def test_empty_parent_is_rejected_but_family_text_remains_legacy(self):
        records = self.make_records_evidence()
        with self.assertRaisesRegex(
                notes_evidence.NotesEvidenceError, 'EMPTY_EVIDENCE'):
            notes_evidence.load_saved_evidence(
                records / 'evidence', self.write_outer(b'', records=records),
                self.context)

        for marker in (
                b'legacy log mentions line-notes-evidence/v2\n',
                b'{"note":"line-notes-evidence/v2"}'):
            with self.subTest(marker=marker):
                records = self.make_records_evidence()
                outer = self.write_outer(marker, records=records)
                loaded = notes_evidence.load_saved_evidence(
                    records / 'evidence', outer, self.context)
                self.assertEqual(loaded['classification'], 'LEGACY_OPAQUE')
                self.assertEqual(loaded['outer_ref'], outer)

    def test_required_roles_nonempty_and_command_streams_may_be_empty(self):
        created = self.make_bundle()
        inspected = notes_evidence.inspect_source_bundle(
            created['bundle_path'], self.context)
        refs = {ref['role']: ref for ref in [
            inspected['data']['statement_ref'], *inspected['data']['assets']]}
        self.assertGreater(refs['statement']['bytes'], 0)
        self.assertGreater(refs['screenshot']['bytes'], 0)
        self.assertEqual(refs['command_stdout']['bytes'], 0)
        self.assertEqual(refs['command_stderr']['bytes'], 0)

        self.statement.write_bytes(b'')
        with self.assertRaisesRegex(
                notes_evidence.NotesEvidenceError, 'EMPTY_EVIDENCE'):
            notes_evidence.create_bundle(
                statement=str(self.statement), assets=[],
                context=self.context,
                output_dir=str(self.packs / uuid.uuid4().hex))

        self.statement.write_bytes(b'synthetic statement\n')
        self.screenshot.write_bytes(b'')
        with self.assertRaisesRegex(
                notes_evidence.NotesEvidenceError, 'EMPTY_EVIDENCE'):
            notes_evidence.create_bundle(
                statement=str(self.statement),
                assets=[('screenshot', str(self.screenshot))],
                context=self.context,
                output_dir=str(self.packs / uuid.uuid4().hex))

    def test_parent_child_tamper_symlink_missing_and_escape_are_rejected(self):
        cases = ('missing_parent', 'missing_child', 'child_drift',
                 'child_symlink', 'outer_escape')
        for case in cases:
            with self.subTest(case=case):
                created = self.make_bundle()
                records = self.make_records_evidence()
                context = notes_evidence.normalize_context(self.context)
                ref = notes_evidence.preserve_bundle(
                    records, created['bundle_path'], context)
                data = json.loads(Path(ref['path']).read_bytes())
                child = records / 'evidence' / data['statement_ref']['sha256']
                if case == 'missing_parent':
                    Path(ref['path']).unlink()
                    code = 'EVIDENCE_DRIFT'
                elif case == 'missing_child':
                    child.unlink()
                    code = 'EVIDENCE_CHILD_MISSING'
                elif case == 'child_drift':
                    child.write_bytes(b'tampered')
                    code = 'EVIDENCE_CHILD_DRIFT'
                elif case == 'child_symlink':
                    child.unlink()
                    child.symlink_to(self.statement)
                    code = 'EVIDENCE_CHILD_MISSING'
                else:
                    outside = self.base / 'outside-evidence'
                    outside.write_bytes(b'outside')
                    ref = dict(path=str(outside), bytes=7,
                               sha256=digest(b'outside'))
                    code = 'EVIDENCE_BINDING_CHANGED'
                with self.assertRaisesRegex(
                        notes_evidence.NotesEvidenceError, code):
                    notes_evidence.load_saved_evidence(
                        records / 'evidence', ref, context)

    def test_duplicate_json_version_and_context_are_rejected(self):
        records = self.make_records_evidence()
        duplicate = (
            b'{"schema":"line-notes-evidence/v2",'
            b'"schema":"line-notes-evidence/v2","context":{}}')
        with self.assertRaisesRegex(notes_evidence.NotesEvidenceError,
                                    'INVALID_EVIDENCE_BUNDLE'):
            notes_evidence.load_saved_evidence(
                records / 'evidence',
                self.write_outer(duplicate, records=records), self.context)

        created = self.make_bundle()
        for schema, code in (
                ('line-notes-evidence/v9', 'UNSUPPORTED_EVIDENCE_SCHEMA'),):
            data = json.loads(Path(created['bundle_path']).read_bytes())
            data['schema'] = schema
            raw = encoded(data)
            target = self.packs / uuid.uuid4().hex
            target.mkdir()
            (target / 'bundle.json').write_bytes(raw)
            for ref in [data['statement_ref'], *data['assets']]:
                (target / ref['sha256']).write_bytes(
                    Path(ref['source_path']).read_bytes())
            with self.assertRaisesRegex(notes_evidence.NotesEvidenceError,
                                        code):
                notes_evidence.inspect_source_bundle(
                    target / 'bundle.json', self.context)

        with self.assertRaisesRegex(notes_evidence.NotesEvidenceError,
                                    'EVIDENCE_CONTEXT_MISMATCH'):
            notes_evidence.inspect_source_bundle(
                created['bundle_path'], dict(list_key='b' * 64))

    def test_source_symlink_and_non_private_output_are_rejected(self):
        linked = self.base / 'statement-link.txt'
        linked.symlink_to(self.statement)
        with self.assertRaisesRegex(notes_evidence.NotesEvidenceError,
                                    'EVIDENCE_SYMLINK_REFUSED'):
            notes_evidence.create_bundle(
                statement=str(linked), assets=[], context=self.context,
                output_dir=str(self.packs / uuid.uuid4().hex))

        existing = self.packs / uuid.uuid4().hex
        existing.mkdir()
        with self.assertRaisesRegex(notes_evidence.NotesEvidenceError,
                                    'EVIDENCE_OUTPUT_DIRECTORY_EXISTS'):
            notes_evidence.create_bundle(
                statement=str(self.statement), assets=[], context=self.context,
                output_dir=str(existing))

        with tempfile.TemporaryDirectory(prefix='notes-evidence-outside-') as outside:
            outside = Path(outside).resolve()
            with self.assertRaisesRegex(notes_evidence.NotesEvidenceError,
                                        'PROJECT_PRIVATE_EVIDENCE_REQUIRED'):
                notes_evidence.create_bundle(
                    statement=str(self.statement), assets=[],
                    context=self.context,
                    output_dir=str(outside / uuid.uuid4().hex))

    def test_relative_paths_missing_parent_and_hard_link_are_rejected(self):
        output = self.packs / uuid.uuid4().hex
        cases = (
            ('relative_statement', 'statement.txt', [], output,
             'PROJECT_LOCAL_EVIDENCE_REQUIRED'),
            ('relative_asset', str(self.statement),
             [('screenshot', 'screenshot.bin')], output,
             'PROJECT_LOCAL_EVIDENCE_REQUIRED'),
            ('relative_output', str(self.statement), [],
             '.local/line-backup/tasks/synthetic-evidence',
             'NEW_EVIDENCE_DIRECTORY_REQUIRED'),
            ('missing_parent', str(self.statement), [],
             self.packs / uuid.uuid4().hex / 'bundle',
             'EVIDENCE_OUTPUT_PARENT_REQUIRED'),
        )
        for name, statement, assets, output_dir, code in cases:
            with self.subTest(case=name):
                with self.assertRaisesRegex(notes_evidence.NotesEvidenceError,
                                            code):
                    notes_evidence.create_bundle(
                        statement=statement, assets=assets,
                        context=self.context, output_dir=str(output_dir))
                if name != 'relative_output':
                    self.assertFalse(Path(output_dir).exists())

        hard_link = self.base / 'statement-hard-link.txt'
        os.link(str(self.statement), str(hard_link))
        with self.assertRaisesRegex(notes_evidence.NotesEvidenceError,
                                    'EVIDENCE_SOURCE_CHANGED'):
            notes_evidence.create_bundle(
                statement=str(hard_link), assets=[], context=self.context,
                output_dir=str(self.packs / uuid.uuid4().hex))

    def test_init_context_mismatch_has_no_collection_or_photo_side_effects(self):
        collection_path = self.base / 'wrong-context-collection'
        photo_root = self.base / 'wrong-context-photos'
        identity = notes.list_identity(visual_key='expected-context')
        wrong_context = dict(list_key='b' * 64)
        wrong_bundle = self.make_bundle(
            context=wrong_context)['bundle_path']

        with self.assertRaisesRegex(NotesError, 'EVIDENCE_CONTEXT_MISMATCH'):
            NotesCollection(str(collection_path)).create(
                photo_root=str(photo_root), display_name='Synthetic',
                identity=identity, binding_evidence=wrong_bundle,
                history_scope_evidence=wrong_bundle)

        self.assertFalse(collection_path.exists())
        self.assertFalse(photo_root.exists())

    def test_init_rejects_invalid_bundle_before_collection_or_photo_side_effects(self):
        collection_path = self.base / 'collection'
        photo_root = self.base / 'photos'
        identity = notes.list_identity(visual_key='evidence-preflight')
        with self.assertRaisesRegex(NotesError, 'EVIDENCE_BUNDLE_REQUIRED'):
            NotesCollection(str(collection_path)).create(
                photo_root=str(photo_root), display_name='Synthetic',
                identity=identity,
                binding_evidence=str(self.statement),
                history_scope_evidence=str(self.statement))
        self.assertFalse(collection_path.exists())
        self.assertFalse(photo_root.exists())

    def test_init_rejects_bundle_changed_after_preflight_without_event(self):
        collection_path = self.base / 'collection'
        identity = notes.list_identity(visual_key='preflight-race')
        context = dict(list_key=notes.list_key(identity))
        original = self.make_bundle(context=context)
        alternate_statement = self.base / 'alternate-statement.txt'
        alternate_statement.write_bytes(b'alternate synthetic statement\n')
        replacement = notes_evidence.create_bundle(
            statement=str(alternate_statement),
            assets=[('screenshot', str(self.screenshot))],
            context=context,
            output_dir=str(self.packs / uuid.uuid4().hex))
        original_fn = notes._preflight_evidence
        changed = []

        def preflight_then_change(source, expected_context=None):
            inspected = original_fn(source, expected_context)
            if not changed:
                target = Path(source)
                replacement_data = json.loads(
                    Path(replacement['bundle_path']).read_bytes())
                for ref in [replacement_data['statement_ref'],
                            *replacement_data['assets']]:
                    child = target.parent / ref['sha256']
                    child.write_bytes(Path(ref['source_path']).read_bytes())
                target.write_bytes(Path(replacement['bundle_path']).read_bytes())
                changed.append(True)
            return inspected

        with mock.patch.object(notes, '_preflight_evidence',
                               side_effect=preflight_then_change):
            with self.assertRaisesRegex(
                    NotesError, 'EVIDENCE_SOURCE_CHANGED'):
                NotesCollection(str(collection_path)).create(
                    photo_root=str(self.base / 'photos'),
                    display_name='Synthetic',
                    identity=identity,
                    binding_evidence=original['bundle_path'],
                    history_scope_evidence=original['bundle_path'])

        records_dirs = list(collection_path.glob('*/events'))
        self.assertEqual(len(records_dirs), 1)
        self.assertEqual(list(records_dirs[0].iterdir()), [])

    def test_preserve_failure_keeps_interrupted_blobs_and_no_event(self):
        collection_path = self.base / 'collection'
        identity = notes.list_identity(visual_key='interrupted-blobs')
        context = dict(list_key=notes.list_key(identity))
        valid = notes_evidence.create_bundle(
            statement=str(self.statement),
            assets=[('screenshot', str(self.screenshot))],
            context=context,
            output_dir=str(self.packs / uuid.uuid4().hex))['bundle_path']
        original = notes_evidence._write_or_verify
        calls = []

        def fail_parent(path, raw):
            calls.append(Path(path).name)
            if len(calls) == 3:
                raise notes_evidence.NotesEvidenceError('EVIDENCE_WRITE_FAILED')
            return original(path, raw)

        with mock.patch.object(notes_evidence, '_write_or_verify',
                               side_effect=fail_parent):
            with self.assertRaisesRegex(NotesError, 'EVIDENCE_WRITE_FAILED'):
                NotesCollection(str(collection_path)).create(
                    photo_root=str(self.base / 'photos'),
                    display_name='Synthetic',
                    identity=identity,
                    binding_evidence=valid,
                    history_scope_evidence=valid)

        records_dirs = list(collection_path.glob('*/events'))
        self.assertEqual(len(records_dirs), 1)
        self.assertEqual(list(records_dirs[0].iterdir()), [])
        evidence_dir = records_dirs[0].parent / 'evidence'
        self.assertEqual(len(list(evidence_dir.iterdir())), 2)
        self.assertFalse((evidence_dir / 'bundle.json').exists())

    def test_published_blob_is_retained_when_post_link_sync_fails(self):
        records = self.make_records_evidence()
        raw = b'published before directory sync failed'
        target = records / 'evidence' / digest(raw)
        with mock.patch.object(notes_evidence, 'sync_dir',
                               side_effect=OSError('synthetic sync failure')):
            with self.assertRaisesRegex(
                    notes_evidence.NotesEvidenceError, 'EVIDENCE_WRITE_FAILED'):
                notes_evidence._write_new(target, raw)
        self.assertEqual(target.read_bytes(), raw)
        self.assertEqual(list(target.parent.glob('.pending-*')), [])
        notes_evidence._write_or_verify(target, raw)

    def test_evidence_pack_cli_returns_exact_outer_ref(self):
        output = self.packs / uuid.uuid4().hex
        result = notes.main([
            'evidence-pack', '--statement', str(self.statement),
            '--asset', 'screenshot', str(self.screenshot),
            '--list-key', self.context['list_key'],
            '--scan-id', self.context['scan_id'],
            '--output-dir', str(output),
        ])
        self.assertEqual(result, 0)


class NotesV1CompatibilityTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='.line-notes-v1-', dir=str(PRIVATE_TASKS))
        self.base = Path(self.temporary.name).resolve()
        self.metadata = json.loads((FIXTURE_ROOT / 'fixture.json').read_bytes())
        self.placeholder = self.metadata['root_placeholder']
        self.collection = self.base / 'collection'
        shutil.copytree(FIXTURE_ROOT / 'collection_template', self.collection)
        for path in self.collection.rglob('*.json'):
            raw = path.read_bytes()
            path.write_bytes(raw.replace(self.placeholder.encode(),
                                         str(self.base).encode()))
        self.records = (self.collection /
                        self.metadata['local_list_id'])
        self._repair_legacy_chain()

    def tearDown(self):
        self.temporary.cleanup()

    def _repair_legacy_chain(self):
        events = sorted((self.records / 'events').iterdir())
        previous = None
        for path in events:
            event = json.loads(path.read_bytes())
            event['previous_sha256'] = previous
            raw = encoded(event)
            path.write_bytes(raw)
            previous = digest(raw)

        store_path = self.records / 'store.json'
        store = json.loads(store_path.read_bytes())
        store['records_root'] = str(self.records)
        store['created_event_sha256'] = digest(events[0].read_bytes())
        store['list_json_sha256'] = digest(
            (self.records / 'list.json').read_bytes())
        store_path.write_bytes(encoded(store))

        index_path = self.collection / 'index.json'
        index = json.loads(index_path.read_bytes())
        index['lists'][self.metadata['local_list_id']].update(
            records_root=str(self.records),
            store_sha256=digest(store_path.read_bytes()))
        index_path.write_bytes(encoded(index))

        created = json.loads(events[0].read_bytes())['data']
        paths = [Path(created['photo_root']), Path(created['list_directory'])]
        for path in events:
            event = json.loads(path.read_bytes())
            if event['kind'] == 'intent':
                paths.append(Path(event['data']['destination']))
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)

    def portable(self, value):
        if isinstance(value, str):
            return value.replace(self.placeholder, str(self.base))
        if isinstance(value, list):
            return [self.portable(item) for item in value]
        if isinstance(value, dict):
            return {key: self.portable(item) for key, item in value.items()}
        return value

    def assert_projection_subset(self, actual, expected, path='projection'):
        if isinstance(expected, dict):
            self.assertIsInstance(actual, dict, path)
            self.assertLessEqual(set(expected), set(actual), path)
            for key, value in expected.items():
                self.assert_projection_subset(actual[key], value,
                                              path + '.' + key)
        elif isinstance(expected, list):
            self.assertIsInstance(actual, list, path)
            self.assertEqual(len(actual), len(expected), path)
            for index, (actual_row, expected_row) in enumerate(
                    zip(actual, expected)):
                self.assert_projection_subset(
                    actual_row, expected_row, '%s[%d]' % (path, index))
        else:
            self.assertEqual(actual, expected, path)

    def test_frozen_v1_projection_and_bytes_do_not_upgrade(self):
        events = sorted((self.records / 'events').iterdir())
        self.assertEqual(
            [json.loads(path.read_bytes())['kind'] for path in events],
            self.metadata['event_kinds'])
        before = {path.name: path.read_bytes() for path in events}

        records = NotesRecords(str(self.records))
        summary = records.summary()
        memory = records.memory()
        with mock.patch.object(notes, '_read_active_hint', return_value=None):
            lists = NotesCollection(str(self.collection)).lists()

        golden = self.portable(json.loads(
            (FIXTURE_ROOT / 'golden.json').read_bytes()))
        self.assert_projection_subset(summary, golden['summary'], 'summary')
        self.assert_projection_subset(memory, golden['memory'], 'memory')
        self.assert_projection_subset(
            lists['lists'][0], golden['summary'], 'lists[0]')
        self.assertEqual(memory, summary)
        self.assertEqual(summary['evidence_corrections'], [])
        for row in summary['media']:
            self.assertEqual(row['effective_kind'], row['kind'])
            self.assertIsNone(row['kind_correction_ref'])
            self.assertEqual(row['source_availability'], 'UNKNOWN')
        self.assertEqual(
            {path.name: path.read_bytes() for path in events}, before)

        audit = records.evidence_audit()
        self.assertTrue(audit['integrity_ok'])
        self.assertTrue(audit['business_projection_omitted'])
        self.assertTrue(audit['references'])
        for row in audit['references']:
            self.assertEqual(row['classification'], 'LEGACY_OPAQUE')
            self.assertEqual(row['reference_check'],
                             'REFERENCE_CHECK_NOT_AVAILABLE')
            self.assertTrue(row['integrity_ok'])

        evidence_ref = json.loads(events[0].read_bytes())['data'][
            'binding_evidence']
        loaded = notes_evidence.load_saved_evidence(
            self.records / 'evidence', evidence_ref)
        self.assertEqual(loaded['classification'], 'LEGACY_OPAQUE')
        self.assertEqual(loaded['outer_ref'], evidence_ref)

    def test_new_writer_rejects_frozen_opaque_evidence_without_side_effects(self):
        collection = self.base / 'new-collection'
        photo_root = self.base / 'new-photos'
        evidence = json.loads(
            (self.records / 'events' / '00000001.json').read_bytes()
        )['data']['binding_evidence']['path']
        with self.assertRaisesRegex(NotesError, 'EVIDENCE_BUNDLE_REQUIRED'):
            NotesCollection(str(collection)).create(
                photo_root=str(photo_root), display_name='Synthetic New',
                identity=notes.list_identity(visual_key='new-v1-rejected'),
                binding_evidence=evidence,
                history_scope_evidence=evidence)
        self.assertFalse(collection.exists())
        self.assertFalse(photo_root.exists())


if __name__ == '__main__':
    unittest.main()
