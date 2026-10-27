"""Synthetic accounting plus real macOS ImageIO; no LINE or GUI input."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import uuid
import zlib
from unittest import mock

from line_backup_batch.daily import (DailyRecords, DailyError, NORMALIZED_HISTORY_SCHEMA, MEMORY_SCHEMA,
                                     NAMING_SCHEMA, album_key, allocate_component, digest, encoded,
                                     planned_photo_names, reference, safe_component, verify_directory)
from line_backup_batch.daily import strict_json


def png(color=(255, 0, 0)):
    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) + \
        chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * 2) * 2)) + chunk(b'IEND', b'')


class DailyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Foundation normalizes /private/var to /var while pathlib resolves in
        # the other direction. The unchanged decoder intentionally rejects that
        # alias; use a real fixture directory in this checkout instead.
        cls.fixtures = tempfile.TemporaryDirectory(prefix='.line-daily-tests-',
                                                   dir=Path(__file__).resolve().parents[1])
        cls.tools = tempfile.TemporaryDirectory(prefix='decoder-', dir=cls.fixtures.name)
        cls.decoder = Path(cls.tools.name).resolve() / 'image_decode'
        cls.source = Path(__file__).resolve().parents[1] / 'src/line_backup_batch/image_decode.swift'
        # The installed CLT default SDK is newer than its compiler. Select the
        # installed matching SDK explicitly; do not change the system selection.
        sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
        sdk_args = ['-sdk', str(sdk)] if sdk.exists() else []
        result = subprocess.run(['xcrun', 'swiftc', *sdk_args, str(cls.source), '-o', str(cls.decoder)],
                                capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        cls.decoder_sha = hashlib.sha256(cls.decoder.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.tools.cleanup()
        cls.fixtures.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='case-', dir=self.fixtures.name)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'backup'
        self.root.mkdir()
        self.counter = 0
        self.store = DailyRecords(self.root)
        self.group = self.store.initialize(binding_evidence=self.evidence('synthetic foreground'),
                                          history_scope_evidence=self.evidence('synthetic history scope'))
        self.session = 'synthetic-session'
        self.bind()
        self.cards = [dict(start_date='2026-01-01', end_date='2026-01-02', expected_images=2,
                           visual_key='synthetic-cover-' + str(n)) for n in range(4)]
        self.store.history(session_id=self.session, scope_evidence=self.evidence('no historical albums in fixture'), entries=[])
        self.store.start_scan(session_id=self.session)

    def tearDown(self):
        self.temp.cleanup()

    def evidence(self, value):
        self.counter += 1
        path = self.base / ('evidence-%d.txt' % self.counter)
        path.write_text(json.dumps(value), encoding='utf-8')
        return str(path)

    def bind(self, group=None, session=None, store=None):
        return (store or self.store).bind(session_id=session or self.session,
            local_group_id=(group or self.group)['local_group_id'],
            observation=self.evidence('synthetic fresh AX/screenshot'), handoff=self.evidence('synthetic handoff'))

    def page(self, cards, top=False, bottom=False, offset=0, unresolved=0):
        screenshot = self.evidence('synthetic fresh screenshot')
        ax = self.evidence('synthetic AX')
        with self.store.locked():
            pages = self.store.pages()
        boundary = None
        if top or bottom:
            boundary = self.evidence(dict(edge='top' if top else 'bottom', session_id=self.session,
                edge_key=album_key(cards[0] if top else cards[-1]), before_offset=offset, after_offset=offset,
                before_screenshot=pages[-1]['evidence']['screenshot'] if pages else reference(screenshot),
                after_screenshot=reference(screenshot), input_receipt=reference(self.evidence('synthetic scroll returned'))))
        return self.store.page(session_id=self.session, cards=cards, screenshot=screenshot, ax=ax,
            top_confirmed=top, bottom_stationary=bottom, boundary_evidence=boundary,
            scroll_evidence=None if top else self.evidence('synthetic down scroll'), unresolved=unresolved)

    def detail(self, card):
        return self.store.detail(session_id=self.session, identity=card,
                                 evidence=self.evidence('synthetic matching detail'))

    def intent(self, card, recovery=None):
        with self.store.locked():
            group_names = self.store.matching('group-name')
            album_names = [row for row in self.store.matching('album-name')
                           if row['album_key'] == album_key(card)]
        if not group_names:
            self.store.capture_group_name(session_id=self.session, name='Synthetic Group',
                source=self.evidence('synthetic group name for regression'))
        if not album_names:
            self.store.capture_album_name(session_id=self.session, identity=card,
                name='Album %s' % card['visual_key'],
                source=self.evidence('synthetic album name for regression'))
        self.detail(card)
        return self.store.intent(session_id=self.session, identity=card, recovery_authorization=recovery)

    def legacy_intent(self, card):
        self.detail(card)
        with self.store.locked():
            key = album_key(card)
            attempt_id = uuid.uuid4().hex
            album_root = self.root / 'albums'
            album_root.mkdir(exist_ok=True)
            destination = album_root / attempt_id
            destination.mkdir()
            return self.store.append('intent', dict(album_key=key, identity=card,
                attempt_id=attempt_id, session_id=self.session, destination=str(destination),
                recovery_of=None, recovery_authorization=None, naming=None,
                save_all_retry_allowed=False, dispatch_authorized=False))

    def finished(self, attempt):
        self.store.outcome(session_id=self.session, attempt_id=attempt['attempt_id'],
                           outcome='DOWNLOAD_FINISHED', evidence=self.evidence('synthetic download finished'))

    def complete(self, attempt):
        return self.store.complete(session_id=self.session, attempt_id=attempt['attempt_id'],
                                   decoder=str(self.decoder), decoder_sha256=self.decoder_sha)

    def test_identity_needs_visual_disambiguator_not_name_ocr(self):
        self.assertNotEqual(album_key(self.cards[0]), album_key(self.cards[1]))
        invalid = dict(self.cards[0], visual_key='')
        with self.assertRaisesRegex(DailyError, 'VISUAL_IDENTITY_REQUIRED'):
            album_key(invalid)
        self.assertNotIn('group_name', self.group)
        self.assertNotIn('GROUP_NAME', self.group)

    def test_new_intent_requires_captured_names_and_never_falls_back_to_legacy_layout(self):
        self.page(self.cards[:1], top=True)
        self.store.detail(session_id=self.session, identity=self.cards[0], evidence=self.evidence('detail'))
        with self.assertRaisesRegex(DailyError, 'GROUP_AND_ALBUM_NAMES_REQUIRED'):
            self.store.intent(session_id=self.session, identity=self.cards[0])
        self.store.capture_group_name(session_id=self.session, name='Group',
            source=self.evidence('synthetic group OCR'))
        with self.assertRaisesRegex(DailyError, 'GROUP_AND_ALBUM_NAMES_REQUIRED'):
            self.store.intent(session_id=self.session, identity=self.cards[0])
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Album',
            source=self.evidence('synthetic album OCR'))
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        self.assertEqual(Path(attempt['destination']), self.root / 'Group' / 'Album')
        self.assertFalse((self.root / 'albums' / attempt['attempt_id']).exists())

    def test_destination_group_and_session_bindings_are_separate(self):
        other = self.base / 'other-group'
        other.mkdir()
        store = DailyRecords(other)
        group = store.initialize(binding_evidence=self.evidence('other foreground'),
                                 history_scope_evidence=self.evidence('other history'))
        self.assertNotEqual(group['local_group_id'], self.group['local_group_id'])
        with self.assertRaisesRegex(DailyError, 'WRONG_LOCAL_GROUP'):
            self.bind(group=self.group, store=store)
        with self.assertRaisesRegex(DailyError, 'FRESH_FOREGROUND_BINDING_REQUIRED'):
            self.store.start_scan(session_id='another session')
        with self.assertRaisesRegex(DailyError, 'RECORDS_ALREADY_EXIST'):
            self.store.initialize(binding_evidence=self.evidence('x'), history_scope_evidence=self.evidence('y'))

    def test_imported_history_never_crosses_group_even_for_identical_cards(self):
        other = self.base / 'history-group'
        other.mkdir()
        store = DailyRecords(other)
        group = store.initialize(binding_evidence=self.evidence('new foreground'),
                                 history_scope_evidence=self.evidence('new scope'))
        self.bind(group=group, store=store)
        with self.assertRaisesRegex(DailyError, 'CROSS_GROUP_HISTORY_REFUSED'):
            store.history(session_id=self.session, scope_evidence=self.evidence('mapping'), entries=[dict(
                identity=self.cards[0], status='COMPLETED', local_group_id=self.group['local_group_id'],
                source=self.evidence('old completed'))])

    def test_unsupported_history_is_protected_unknown_and_cannot_make_daily_pass(self):
        root = self.base / 'legacy-group'
        root.mkdir()
        store = DailyRecords(root)
        group = store.initialize(binding_evidence=self.evidence('new foreground'),
                                 history_scope_evidence=self.evidence('old history scope'))
        store.bind(session_id=self.session, local_group_id=group['local_group_id'],
                   observation=self.evidence('fresh observation'), handoff=self.evidence('handoff'))
        store.history(session_id=self.session, scope_evidence=self.evidence('mapping'), entries=[dict(
            identity=self.cards[0], local_group_id=group['local_group_id'], status='COMPLETED',
            source=self.evidence('not a normalized completion record'))])
        store.start_scan(session_id=self.session)
        self._page_for(store, self.cards[:1], group, top=True)
        self._page_for(store, self.cards[:1], group, bottom=True)
        report = store.summary()
        self.assertEqual(report['PROTECTED_HISTORY'], 1)
        self.assertEqual(report['ALL_ELIGIBLE_ALBUMS_BACKED_UP'], 'INCOMPLETE')
        self.assertEqual(report['sensor_verified'], False)
        self.assertEqual(report['real_line_e2e'], 'NOT_TESTED')
        store.detail(session_id=self.session, identity=self.cards[0], evidence=self.evidence('detail'))
        with self.assertRaisesRegex(DailyError, 'PROTECTED_NO_REDOWNLOAD'):
            store.intent(session_id=self.session, identity=self.cards[0])

    def _page_for(self, store, cards, group, top=False, bottom=False):
        screenshot = self.evidence('fresh screenshot')
        ax = self.evidence('fresh AX')
        with store.locked():
            pages = store.pages()
        boundary = None
        if top or bottom:
            boundary = self.evidence(dict(edge='top' if top else 'bottom', session_id=self.session,
                edge_key=album_key(cards[0] if top else cards[-1]), before_offset=0, after_offset=0,
                before_screenshot=pages[-1]['evidence']['screenshot'] if pages else reference(screenshot),
                after_screenshot=reference(screenshot), input_receipt=reference(self.evidence('scroll'))))
        return store.page(session_id=self.session, cards=cards, screenshot=screenshot, ax=ax,
            top_confirmed=top, bottom_stationary=bottom, boundary_evidence=boundary,
            scroll_evidence=None if top else self.evidence('down scroll'))

    def test_normalized_history_requires_matching_group_identity_and_photo_proof(self):
        root = self.base / 'normalized-group'
        root.mkdir()
        store = DailyRecords(root)
        group = store.initialize(binding_evidence=self.evidence('new foreground'),
                                 history_scope_evidence=self.evidence('history scope'))
        store.bind(session_id=self.session, local_group_id=group['local_group_id'],
                   observation=self.evidence('fresh observation'), handoff=self.evidence('handoff'))
        identity = self.cards[0]
        manifest = [{'name': '1.jpg', 'size': 10, 'sha256': 'a' * 64},
                    {'name': '2.jpg', 'size': 20, 'sha256': 'b' * 64}]
        manifest_sha = digest(encoded(manifest))
        manifest_path = self.base / 'manifest.json'
        manifest_path.write_bytes(encoded({'manifest': manifest, 'manifest_sha256': manifest_sha}))
        imageio_path = self.base / 'imageio.json'
        imageio_path.write_bytes(encoded({'verdict': 'PASS', 'readOnly': True, 'expected': 2,
            'actualEntries': 2, 'entries': [dict(name=row['name'], decoded=True, sha256=row['sha256'])
                                             for row in manifest]}))
        source_path = self.base / 'normalized-history.json'
        source_path.write_bytes(encoded({'schema': NORMALIZED_HISTORY_SCHEMA,
            'local_group_id': group['local_group_id'], 'identity': identity,
            'album_key': album_key(identity), 'status': 'COMPLETED',
            'photo_verification': {'expected_images': 2, 'manifest_sha256': manifest_sha,
                'manifest_evidence': reference(manifest_path),
                'imageio_evidence': reference(imageio_path)}}))
        store.history(session_id=self.session, scope_evidence=self.evidence('mapping'), entries=[dict(
            identity=identity, local_group_id=group['local_group_id'], status='COMPLETED',
            source=str(source_path))])
        self.assertEqual(store.status_map()[album_key(identity)], 'COMPLETED')
        for path in (manifest_path, imageio_path, source_path):
            path.unlink()
        reopened = DailyRecords(root)
        memory = reopened.memory()
        self.assertEqual(memory['albums'][0]['status'], 'COMPLETED')
        self.assertEqual(memory['history'][0]['photo_verification']['manifest']['manifest'], manifest)

    def legacy_claim(self, card=None):
        card = card or self.cards[0]
        return dict(id='synthetic-existing-photos', local_group_id=None,
            identity_hint={k: card[k] for k in ('start_date', 'end_date', 'expected_images')},
            status='PROTECTED_HISTORY', recorded_status='UNMAPPED_LOCAL_PHOTOS',
            reason='Synthetic local photos without reliable list binding')

    def import_memory(self, entries=None):
        return self.store.import_memory(local_group_id=self.group['local_group_id'],
            legacy_albums=entries or [], coverage='SYNTHETIC_LOCAL_FACTS_ONLY', provenance=[])

    def test_legacy_candidates_protect_without_assigning_group_or_blocking_other_dates(self):
        unrelated = dict(self.cards[1], start_date='2026-02-01', end_date='2026-02-02')
        self.import_memory([self.legacy_claim()])
        self.page([self.cards[0], unrelated], top=True)
        self.page([self.cards[0], unrelated], bottom=True)
        self.assertEqual(self.store.summary()['PROTECTED_HISTORY'], 1)
        with self.assertRaisesRegex(DailyError, 'PROTECTED_NO_REDOWNLOAD'):
            self.intent(self.cards[0])
        self.assertTrue(self.intent(unrelated)['attempt_id'])
        reopened = DailyRecords(self.root).memory()
        self.assertIsNone(reopened['legacy_albums'][0]['local_group_id'])
        self.assertEqual(reopened['legacy_albums'][0]['recorded_status'], 'UNMAPPED_LOCAL_PHOTOS')

    def test_memory_cannot_override_actual_completion_or_unknown_dispatch(self):
        self.page(self.cards[:1], top=True)
        self.page(self.cards[:1], bottom=True)
        attempt = self.intent(self.cards[0])
        self.import_memory([self.legacy_claim()])
        self.assertEqual(self.store.memory()['albums'][0]['status'], 'UNKNOWN')
        with self.assertRaisesRegex(DailyError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.intent(self.cards[0])
        for n in (1, 2):
            (Path(attempt['destination']) / ('%d.png' % n)).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        self.assertEqual(DailyRecords(self.root).summary()['COMPLETED'], 1)

    def test_memory_import_rejects_cross_group_completion_claims_and_second_import(self):
        before = len(list((self.store.records / 'events').iterdir()))
        with self.assertRaisesRegex(DailyError, 'WRONG_LOCAL_GROUP'):
            self.store.import_memory(local_group_id='wrong', legacy_albums=[], coverage='scope', provenance=[])
        for claim, error in ((dict(self.legacy_claim(), local_group_id='other'), 'CROSS_GROUP_HISTORY_REFUSED'),
                             (dict(self.legacy_claim(), status='COMPLETED'), 'LEGACY_CLAIM_CANNOT_COMPLETE')):
            with self.assertRaisesRegex(DailyError, error):
                self.import_memory([claim])
        self.assertEqual(len(list((self.store.records / 'events').iterdir())), before)
        self.import_memory()
        with self.assertRaisesRegex(DailyError, 'MEMORY_ALREADY_IMPORTED'):
            self.import_memory()

    def test_memory_reads_only_active_records_not_import_sources(self):
        from unittest.mock import patch
        from line_backup_batch import daily
        self.import_memory([self.legacy_claim()])
        original = daily.read_file
        def local_only(path):
            self.assertTrue(Path(path).is_relative_to(self.store.records), str(path))
            return original(path)
        with patch.object(daily, 'read_file', side_effect=local_only):
            memory = DailyRecords(self.root).memory()
            self.assertEqual(memory['schema'], MEMORY_SCHEMA)
            self.assertEqual(DailyRecords(self.root).summary()['total'], 0)

    def test_external_roots_and_evidence_are_not_runtime_inputs(self):
        with tempfile.TemporaryDirectory(prefix='line-external-input-') as name:
            outside = Path(name).resolve()
            with self.assertRaisesRegex(DailyError, 'PROJECT_LOCAL_ROOT_REQUIRED'):
                DailyRecords(outside)
            source = outside / 'old-data.json'
            source.write_text('{}')
            with self.assertRaisesRegex(DailyError, 'PROJECT_LOCAL_EVIDENCE_REQUIRED'):
                reference(source)
            project = Path(__file__).resolve().parents[1]
            run = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily',
                'summary', '--root', str(self.root), '--input', str(source)],
                env=dict(os.environ, PYTHONPATH=str(project / 'src')), capture_output=True, text=True)
            self.assertEqual(run.returncode, 4)
            self.assertEqual(json.loads(run.stdout)['reason'], 'PROJECT_LOCAL_EVIDENCE_REQUIRED')

    def test_legacy_event_migration_preserves_unknown_and_downgrades_missing_proof(self):
        # The fixture emulates the old immutable event format without modifying
        # any real event. The missing source must become a recorded barrier.
        old_source = reference(self.evidence('synthetic old source'))
        with self.store.locked():
            self.store.append('history', dict(scope_evidence=old_source, entries=[dict(
                album_key=album_key(self.cards[0]), identity=self.cards[0], status='COMPLETED',
                declared_status='COMPLETED', source=old_source), dict(
                album_key=album_key(self.cards[1]), identity=self.cards[1], status='UNKNOWN',
                declared_status='UNKNOWN', source=old_source)]))
        Path(old_source['path']).unlink()
        with self.assertRaisesRegex(DailyError, 'MEMORY_MIGRATION_REQUIRED'):
            self.store.memory()
        self.import_memory()
        memory = DailyRecords(self.root).memory()
        statuses = {a['album_key']: a['status'] for a in memory['albums']}
        self.assertEqual(statuses[album_key(self.cards[0])], 'PROTECTED_HISTORY')
        self.assertEqual(statuses[album_key(self.cards[1])], 'UNKNOWN')
        self.page(self.cards[:2], top=True)
        with self.assertRaisesRegex(DailyError, 'PROTECTED_NO_REDOWNLOAD'):
            self.intent(self.cards[0])
        with self.assertRaisesRegex(DailyError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.intent(self.cards[1])

    def test_imported_exclusion_is_self_contained_and_never_dispatches(self):
        root = self.base / 'excluded-group'
        root.mkdir()
        store = DailyRecords(root)
        group = store.initialize(binding_evidence=self.evidence('binding'), history_scope_evidence=self.evidence('scope'))
        self.bind(group=group, store=store)
        identity = self.cards[0]
        owner = self.evidence('synthetic owner exclusion')
        exclusion = self.evidence(dict(schema='line-backup-exclusion/v1', local_group_id=group['local_group_id'],
            identity=identity, album_key=album_key(identity), decision='EXCLUDE_ALBUM', owner_source=reference(owner)))
        source = self.evidence(dict(schema=NORMALIZED_HISTORY_SCHEMA, local_group_id=group['local_group_id'],
            identity=identity, album_key=album_key(identity), status='EXCLUDED', exclusion_evidence=reference(exclusion)))
        store.history(session_id=self.session, scope_evidence=self.evidence('scope'), entries=[dict(
            identity=identity, local_group_id=group['local_group_id'], status='EXCLUDED', source=source)])
        for filename in (source, exclusion, owner):
            Path(filename).unlink()
        store.start_scan(session_id=self.session)
        self._page_for(store, [identity], group, top=True)
        self._page_for(store, [identity], group, bottom=True)
        self.assertEqual(DailyRecords(root).summary()['EXCLUDED'], 1)
        store.detail(session_id=self.session, identity=identity, evidence=self.evidence('detail'))
        with self.assertRaisesRegex(DailyError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            store.intent(session_id=self.session, identity=identity)

    def test_memory_event_binding_and_schema_corruption_fail_closed(self):
        self.import_memory([self.legacy_claim()])
        path = sorted((self.store.records / 'events').glob('*.json'))[-1]
        raw = path.read_bytes()
        event = json.loads(raw)
        event['data']['schema'] = 'unsupported'
        path.write_bytes(encoded(event))
        with self.assertRaisesRegex(DailyError, 'MEMORY_DIGEST_CHANGED'):
            DailyRecords(self.root).memory()
        event = json.loads(raw)
        event['data']['legacy_albums'] = []
        path.write_bytes(encoded(event))
        with self.assertRaisesRegex(DailyError, 'MEMORY_DIGEST_CHANGED'):
            DailyRecords(self.root).memory()
        path.write_bytes(raw)
        event = json.loads(raw)
        event['local_group_id'] = 'wrong'
        path.write_bytes(encoded(event))
        with self.assertRaisesRegex(DailyError, 'EVENT_BINDING_CHANGED'):
            DailyRecords(self.root).memory()
        path.write_bytes(raw)
        path.unlink()
        with self.assertRaisesRegex(DailyError, 'MEMORY_ANCHOR_SET_CHANGED'):
            DailyRecords(self.root).memory()

    def test_source_with_wrong_normalized_group_is_protected_not_completed(self):
        root = self.base / 'mismatched-normalized-group'
        root.mkdir()
        store = DailyRecords(root)
        group = store.initialize(binding_evidence=self.evidence('new foreground'),
                                 history_scope_evidence=self.evidence('history scope'))
        store.bind(session_id=self.session, local_group_id=group['local_group_id'],
                   observation=self.evidence('fresh observation'), handoff=self.evidence('handoff'))
        source = self.evidence({'schema': NORMALIZED_HISTORY_SCHEMA,
            'local_group_id': 'different-group', 'identity': self.cards[0],
            'album_key': album_key(self.cards[0]), 'status': 'COMPLETED'})
        store.history(session_id=self.session, scope_evidence=self.evidence('mapping'), entries=[dict(
            identity=self.cards[0], local_group_id=group['local_group_id'], status='COMPLETED', source=source)])
        self.assertEqual(store.status_map()[album_key(self.cards[0])], 'PROTECTED_HISTORY')

    def test_full_ordered_overlap_deduplicates_cards_but_does_not_imply_completion(self):
        self.page(self.cards[:3], top=True)
        self.page(self.cards[1:])
        self.page(self.cards[1:], bottom=True, offset=100)
        report = self.store.summary()
        self.assertEqual(report['total'], 4)
        self.assertEqual(report['list_coverage'], 'OBSERVED')
        self.assertEqual(report['INCOMPLETE'], 4)
        self.assertEqual(report['ALL_ELIGIBLE_ALBUMS_BACKED_UP'], 'INCOMPLETE')

    def test_no_top_no_overlap_reorder_and_ambiguous_same_page_are_refused(self):
        with self.assertRaisesRegex(DailyError, 'TOP_BOUNDARY_REQUIRED'):
            self.page(self.cards[:2])
        with self.assertRaisesRegex(DailyError, 'AMBIGUOUS_SAME_PAGE_CARDS'):
            self.page([self.cards[0], self.cards[0]], top=True)
        self.page(self.cards[:2], top=True)
        with self.assertRaisesRegex(DailyError, 'LIST_OVERLAP_GAP'):
            self.page(self.cards[2:])
        with self.assertRaisesRegex(DailyError, 'LIST_REORDER_OR_LOOP'):
            self.page([self.cards[1], self.cards[0], self.cards[2]])

    def test_same_cards_alone_cannot_establish_bottom(self):
        self.page(self.cards[:2], top=True)
        with self.assertRaisesRegex(DailyError, 'NO_MOVEMENT_IS_NOT_A_NEW_PAGE'):
            self.page(self.cards[:2])
        with self.assertRaisesRegex(DailyError, 'BOTTOM_NOT_STATIONARY'):
            self.page(self.cards[1:3], bottom=True)
        screenshot = self.evidence('fresh screenshot')
        boundary = self.evidence(dict(edge='bottom', session_id=self.session,
            edge_key=album_key(self.cards[1]), before_offset=100, after_offset=101))
        with self.assertRaisesRegex(DailyError, 'BOUNDARY_MOVEMENT_OBSERVED'):
            self.store.page(session_id=self.session, cards=self.cards[:2], screenshot=screenshot,
                ax=self.evidence('ax'), bottom_stationary=True, boundary_evidence=boundary,
                scroll_evidence=self.evidence('scroll'))

    def test_unresolved_cards_and_missing_prior_scan_cards_prevent_completeness(self):
        self.page(self.cards[:3], top=True, unresolved=1)
        self.page(self.cards[:3], bottom=True)
        self.assertEqual(self.store.summary()['UNKNOWN'], 1)
        self.store.start_scan(session_id=self.session)
        self.page(self.cards[:2], top=True)
        self.page(self.cards[:2], bottom=True)
        self.assertEqual(self.store.summary()['UNKNOWN'], 1)

    def test_new_session_requires_new_scan_not_old_cursor_or_coordinates(self):
        self.page(self.cards[:2], top=True)
        self.bind(session='next-session')
        with self.assertRaisesRegex(DailyError, 'NEW_SCAN_REQUIRED_AFTER_HANDOFF'):
            self.store.page(session_id='next-session', cards=self.cards[:2], screenshot=self.evidence('s'),
                            ax=self.evidence('ax'), top_confirmed=True)

    def test_durable_unknown_survives_fresh_process_object_and_blocks_every_album(self):
        self.page(self.cards[:2], top=True)
        attempt = self.intent(self.cards[0])
        reopened = DailyRecords(self.root)
        self.assertEqual(reopened.summary()['UNKNOWN'], 1)
        self.assertFalse(attempt['dispatch_authorized'])
        with self.assertRaisesRegex(DailyError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.intent(self.cards[0], self.evidence('cannot override unknown'))
        with self.assertRaisesRegex(DailyError, 'PENDING_OTHER_ALBUM_NO_DISPATCH'):
            self.intent(self.cards[1])
        destination = Path(attempt['destination'])
        self.assertEqual(destination.parent.parent, self.root)
        self.assertTrue(destination.is_dir())

    def test_explicit_unknown_outcome_cannot_be_rewritten_as_stopped_or_not_sent(self):
        self.page(self.cards[:2], top=True)
        attempt = self.intent(self.cards[0])
        self.store.outcome(session_id=self.session, attempt_id=attempt['attempt_id'], outcome='UNKNOWN',
                           evidence=self.evidence('dispatch result unknown'))
        for outcome in ('STOPPED', 'NOT_SENT'):
            with self.assertRaisesRegex(DailyError, 'OUTCOME_ALREADY_KNOWN'):
                self.store.outcome(session_id=self.session, attempt_id=attempt['attempt_id'], outcome=outcome,
                                   evidence=self.evidence('claimed resolution'))
        with self.assertRaisesRegex(DailyError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.intent(self.cards[0], self.evidence({'decision': 'AUTHORIZE_ALBUM_RECOVERY'}))

    def test_album_recovery_preserves_partial_files_and_requires_specific_authorization(self):
        self.page(self.cards[:2], top=True)
        attempt = self.intent(self.cards[0])
        partial = Path(attempt['destination']) / 'partial.png'
        partial.write_bytes(png())
        original = partial.read_bytes()
        self.store.outcome(session_id=self.session, attempt_id=attempt['attempt_id'], outcome='STOPPED',
                           evidence=self.evidence('synthetic old download confirmed terminated'))
        with self.assertRaisesRegex(DailyError, 'ALBUM_RECOVERY_AUTHORIZATION_REQUIRED'):
            self.intent(self.cards[0])
        with self.assertRaisesRegex(DailyError, 'RECOVERY_AUTHORIZATION_SCOPE_MISMATCH'):
            self.intent(self.cards[0], self.evidence(dict(decision='AUTHORIZE_ALBUM_RECOVERY',
                local_group_id='wrong-group', album_key=album_key(self.cards[0]))))
        approval = self.evidence(dict(decision='AUTHORIZE_ALBUM_RECOVERY',
            local_group_id=self.group['local_group_id'], album_key=album_key(self.cards[0]),
            previous_attempt_id=attempt['attempt_id'], preserve_existing=True,
            owner_source=reference(self.evidence('synthetic album-specific Owner authorization'))))
        recovered = self.intent(self.cards[0], approval)
        self.assertNotEqual(attempt['destination'], recovered['destination'])
        self.assertEqual(recovered['recovery_of'], attempt['attempt_id'])
        self.assertEqual(list(Path(recovered['destination']).iterdir()), [])
        self.assertEqual(partial.read_bytes(), original)
        with self.assertRaisesRegex(DailyError, 'ONLY_LATEST_ATTEMPT_CAN_CHANGE'):
            self.store.outcome(session_id=self.session, attempt_id=attempt['attempt_id'],
                               outcome='NOT_SENT', evidence=self.evidence('late stale result'))

    def test_real_imageio_duplicate_content_allowed_and_completed_never_redownloaded(self):
        self.page(self.cards[:1], top=True)
        self.page(self.cards[:1], bottom=True)
        attempt = self.intent(self.cards[0])
        for n in (1, 2):
            (Path(attempt['destination']) / ('%d.png' % n)).write_bytes(png())
        self.finished(attempt)
        completed = self.complete(attempt)
        self.assertEqual(completed['proof']['imageio']['verdict'], 'PASS')
        self.assertEqual(len({r['sha256'] for r in completed['proof']['manifest']}), 1)
        report = self.store.summary()
        self.assertEqual(report['ALL_ELIGIBLE_ALBUMS_BACKED_UP'], 'PASS')
        self.assertFalse(report['formal_auto_verified'])
        self.assertEqual(report['evidence_role'], 'AGENT_ATTESTED_OBSERVATIONS')
        self.assertFalse(report['sensor_verified'])
        self.assertEqual(report['real_line_e2e'], 'NOT_TESTED')
        self.assertEqual(report['pass_scope'], 'AGENT_ATTESTED_ACCOUNTING_ONLY')
        with self.assertRaisesRegex(DailyError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            self.intent(self.cards[0])
        with self.assertRaisesRegex(DailyError, 'COMPLETION_IMMUTABLE'):
            self.complete(attempt)
        (Path(attempt['destination']) / completed['proof']['manifest'][0]['name']).unlink()
        with self.assertRaisesRegex(DailyError, 'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD'):
            self.intent(self.cards[0])

    def test_count_mismatch_corrupt_content_and_decoder_drift_never_complete(self):
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        root = Path(attempt['destination'])
        (root / '1.png').write_bytes(png())
        self.finished(attempt)
        with self.assertRaisesRegex(DailyError, 'DOWNLOAD_COUNT_MISMATCH'):
            self.complete(attempt)
        (root / '2.png').write_bytes(png()[:30])
        with self.assertRaisesRegex(DailyError, 'IMAGEIO_DECODE_FAILED'):
            self.complete(attempt)
        with self.assertRaisesRegex(DailyError, 'DECODER_DRIFT'):
            verify_directory(str(root), 2, str(self.decoder), '0' * 64)
        self.assertEqual(self.store.summary()['INCOMPLETE'], 1)

    def test_symlink_destination_evidence_and_download_refused(self):
        alias = self.base / 'alias'
        alias.symlink_to(self.root)
        with self.assertRaisesRegex(DailyError, 'CANONICAL_DIRECTORY_REQUIRED'):
            DailyRecords(alias)
        file = self.evidence('evidence')
        link = self.base / 'link'
        link.symlink_to(file)
        with self.assertRaisesRegex(DailyError, 'EVIDENCE_SYMLINK_REFUSED'):
            reference(link)
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        (Path(attempt['destination']) / '1.png').symlink_to(file)
        self.finished(attempt)
        with self.assertRaisesRegex(DailyError, 'DOWNLOAD_NOT_REGULAR'):
            self.complete(attempt)

    def test_strict_json_rejects_ambiguous_or_invalid_records(self):
        for raw in (b'{"status":"UNKNOWN","status":"COMPLETED"}',
                    b'{"nested":{"x":1,"x":2}}', b'NaN', b'Infinity',
                    b'-Infinity', b'"\xff"', b'{', b'[' * 2000):
            with self.subTest(raw=raw[:60]), self.assertRaisesRegex(DailyError, '^INVALID_INPUT$'):
                strict_json(raw, 'INVALID_INPUT')
        self.assertEqual(strict_json(b'{"status":"UNKNOWN","n":1}', 'INVALID_INPUT'),
                         {'status': 'UNKNOWN', 'n': 1})

    def test_retired_commands_refuse_before_accessing_destination(self):
        project = Path(__file__).resolve().parents[1]
        env = dict(os.environ, PYTHONPATH=str(project / 'src'))
        missing = self.base / 'must-not-be-created'
        for module, args, expected in (
                ('line_backup_batch', ['begin', '--root', str(missing)], 64),
                ('line_backup_batch.daily', ['authorization-request', '--root', str(missing)], 2)):
            run = subprocess.run(['/usr/bin/python3', '-B', '-m', module, *args],
                                 env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, expected, run.stderr)
            self.assertFalse(missing.exists())

    def test_malformed_cli_input_is_refused_without_writing_records(self):
        project = Path(__file__).resolve().parents[1]
        malformed = self.base / 'input.json'
        malformed.write_bytes(b'{"session_id":"one","session_id":"two"}')
        before = {p.name: p.read_bytes() for p in (self.root / 'backup-records/events').iterdir()}
        run = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily',
                              'scan', '--root', str(self.root), '--input', str(malformed)],
                             env=dict(os.environ, PYTHONPATH=str(project / 'src')),
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 4, run.stderr)
        refused = json.loads(run.stdout)
        self.assertEqual(refused['reason'], 'INVALID_INPUT')
        self.assertFalse(refused['dispatch_authorized'])
        self.assertEqual({p.name: p.read_bytes() for p in (self.root / 'backup-records/events').iterdir()}, before)

    def test_direct_naming_and_correction_cli_needs_no_hand_edited_json(self):
        project = Path(__file__).resolve().parents[1]
        env = dict(os.environ, PYTHONPATH=str(project / 'src'))

        def run_cli(*args):
            result = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily', *args],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            return json.loads(result.stdout)

        help_run = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily', '--help'],
                                  env=env, capture_output=True, text=True)
        self.assertEqual(help_run.returncode, 0, help_run.stderr)
        for operation in ('capture-group-name', 'capture-album-name', 'correct-group-name',
                          'correct-album-name', 'resume-naming'):
            self.assertIn(operation, help_run.stdout)

        self.page(self.cards[:1], top=True)
        group = run_cli('capture-group-name', '--root', str(self.root), '--session-id', self.session,
                        '--name', 'Fans/Group', '--source', self.evidence('synthetic CLI group name'))['result']
        album = run_cli('capture-album-name', '--root', str(self.root), '--session-id', self.session,
                        '--album-key', album_key(self.cards[0]), '--name', 'Trip',
                        '--source', self.evidence('synthetic CLI album name'))['result']
        self.assertEqual((group['path_name'], album['path_name']), ('Fans Group', 'Trip'))
        self.detail(self.cards[0])
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)

        corrected = run_cli('correct-album-name', '--root', str(self.root),
                            '--album-key', album_key(self.cards[0]), '--name', 'Journey',
                            '--source', self.evidence('synthetic CLI album correction'),
                            '--decoder', str(self.decoder), '--decoder-sha256', self.decoder_sha)
        self.assertFalse(corrected['dispatch_authorized'])
        self.assertTrue((self.root / 'Fans Group' / 'Journey').is_dir())
        group_corrected = run_cli('correct-group-name', '--root', str(self.root),
                                  '--name', 'Renamed Fans', '--source', self.evidence('synthetic CLI group correction'),
                                  '--decoder', str(self.decoder), '--decoder-sha256', self.decoder_sha)
        self.assertFalse(group_corrected['dispatch_authorized'])
        self.assertTrue((self.root / 'Renamed Fans' / 'Journey').is_dir())
        resumed = run_cli('resume-naming', '--root', str(self.root), '--decoder', str(self.decoder),
                          '--decoder-sha256', self.decoder_sha)
        self.assertEqual(resumed['result']['status'], 'NOTHING_TO_RESUME')
        self.assertFalse(resumed['dispatch_authorized'])

    def test_direct_intent_outcome_and_verify_close_no_json_flow(self):
        project = Path(__file__).resolve().parents[1]
        env = dict(os.environ, PYTHONPATH=str(project / 'src'))

        def run_cli(*args):
            result = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily', *args],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            return json.loads(result.stdout)

        self.page(self.cards[:1], top=True)
        run_cli('capture-group-name', '--root', str(self.root), '--session-id', self.session,
                '--name', 'Direct Group', '--source', self.evidence('synthetic CLI group name'))
        run_cli('capture-album-name', '--root', str(self.root), '--session-id', self.session,
                '--album-key', album_key(self.cards[0]), '--name', 'Direct Album',
                '--source', self.evidence('synthetic CLI album name'))
        self.detail(self.cards[0])
        intent_run = run_cli('intent', '--root', str(self.root), '--session-id', self.session,
                             '--album-key', album_key(self.cards[0]))
        attempt = intent_run['result']
        self.assertFalse(intent_run['dispatch_authorized'])
        self.assertFalse(attempt['dispatch_authorized'])
        self.assertFalse(attempt['save_all_retry_allowed'])
        destination = Path(attempt['destination'])
        self.assertEqual(destination, self.root / 'Direct Group' / 'Direct Album')
        (destination / '2.png').write_bytes(png((0, 255, 0)))
        (destination / '1.png').write_bytes(png())

        outcome_run = run_cli('outcome', '--root', str(self.root), '--session-id', self.session,
                              '--attempt-id', attempt['attempt_id'], '--outcome', 'DOWNLOAD_FINISHED',
                              '--evidence', self.evidence('synthetic CLI download finished'))
        self.assertFalse(outcome_run['dispatch_authorized'])
        verified = run_cli('verify', '--root', str(self.root), '--session-id', self.session,
                           '--attempt-id', attempt['attempt_id'], '--decoder', str(self.decoder),
                           '--decoder-sha256', self.decoder_sha)
        self.assertFalse(verified['dispatch_authorized'])
        self.assertEqual([row['name'] for row in verified['result']['proof']['manifest']],
                         ['Direct Album_001.png', 'Direct Album_002.png'])
        self.assertFalse((self.root / 'albums').exists())
        with self.store.locked():
            self.assertEqual(len(self.store.matching('name-transaction')), 1)
            self.assertEqual(len(self.store.matching('completion')), 1)

    def test_direct_cli_command_help_and_exclusive_input_contract(self):
        project = Path(__file__).resolve().parents[1]
        env = dict(os.environ, PYTHONPATH=str(project / 'src'))
        help_expectations = {
            'intent': ('--album-key', '--session-id'),
            'outcome': ('--attempt-id', '--outcome', '--evidence'),
            'verify': ('--attempt-id', '--decoder-sha256'),
            'capture-album-name': ('--album-key', '--name', '--source'),
            'correct-group-name': ('--name', '--source', '--decoder-sha256'),
            'resume-naming': ('--decoder', '--decoder-sha256'),
        }
        for operation, expected in help_expectations.items():
            with self.subTest(operation=operation):
                result = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily',
                                         operation, '--help'], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                for option in ('--root', *expected):
                    self.assertIn(option, result.stdout)
                self.assertIn('cannot be combined with --input', result.stdout)
        mixed = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily',
                                'intent', '--root', str(self.root), '--input', str(self.base / 'legacy.json'),
                                '--session-id', self.session, '--album-key', album_key(self.cards[0])],
                               env=env, capture_output=True, text=True)
        self.assertEqual(mixed.returncode, 2, mixed.stderr)
        self.assertIn('--input cannot be combined with direct arguments', mixed.stderr)
        unrelated = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily',
                                    'resume-naming', '--root', str(self.root), '--name', 'ignored'],
                                   env=env, capture_output=True, text=True)
        self.assertEqual(unrelated.returncode, 2, unrelated.stderr)
        self.assertIn('unexpected arguments for resume-naming: --name', unrelated.stderr)
        missing = subprocess.run(['/usr/bin/python3', '-B', '-m', 'line_backup_batch.daily',
                                  'outcome', '--root', str(self.root), '--session-id', self.session,
                                  '--attempt-id', 'synthetic', '--outcome', 'DOWNLOAD_FINISHED'],
                                 env=env, capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2, missing.stderr)
        self.assertIn('missing arguments for outcome: --evidence', missing.stderr)

    def test_torn_event_or_changed_evidence_blocks_without_resetting_history(self):
        self.page(self.cards[:1], top=True)
        events = self.root / 'backup-records/events'
        before = {p.name: p.read_bytes() for p in events.iterdir()}
        pending = events / '.pending-interrupted'
        pending.write_bytes(b'{')
        with self.assertRaisesRegex(DailyError, 'EVENT_SEQUENCE_OR_PENDING_WRITE'):
            self.store.summary()
        self.assertEqual({p.name: p.read_bytes() for p in events.iterdir() if p != pending}, before)

    def test_named_backup_preserves_identity_sorts_originals_and_avoids_name_collisions(self):
        sorted_card = dict(self.cards[0], expected_images=3, visual_key='synthetic-sorted-files')
        colliding_card = dict(self.cards[1], expected_images=1, visual_key='synthetic-colliding-name')
        self.page([sorted_card, colliding_card], top=True)
        group = self.store.capture_group_name(session_id=self.session, name='Fans/Group',
            source=self.evidence('synthetic OCR group name'))
        first = self.store.capture_album_name(session_id=self.session, identity=sorted_card,
            name='Trip', source=self.evidence('synthetic OCR album name one'))
        second = self.store.capture_album_name(session_id=self.session, identity=colliding_card,
            name='trip', source=self.evidence('synthetic OCR album name two'))
        self.assertNotEqual(album_key(sorted_card), album_key(colliding_card))
        self.assertEqual(group['path_name'], 'Fans Group')
        self.assertEqual(first['path_name'], 'Trip')
        self.assertEqual(second['path_name'], 'trip (2)')
        self.detail(sorted_card)
        attempt = self.store.intent(session_id=self.session, identity=sorted_card)
        sources = {'10.JPG': png(), '2.jpeg': png() + b'second', '1.png': png() + b'third'}
        self.assertEqual(Path(attempt['destination']), self.root / 'Fans Group' / 'Trip')
        for name, content in sources.items():
            (Path(attempt['destination']) / name).write_bytes(content)
        self.finished(attempt)
        completed = self.complete(attempt)
        self.assertEqual([row['name'] for row in completed['proof']['manifest']],
                         ['Trip_001.png', 'Trip_002.JPG', 'Trip_003.jpeg'])
        mapping = {row['source_name']: row['target_name'] for row in completed['naming']['rows']}
        for source_name, content in sources.items():
            self.assertEqual((Path(attempt['destination']) / mapping[source_name]).read_bytes(), content)
        memory = DailyRecords(self.root).memory()
        self.assertEqual(memory['group']['display_name'], 'Fans/Group')
        self.assertEqual(memory['group']['path_name'], 'Fans Group')
        album = next(row for row in memory['albums'] if row['album_key'] == album_key(sorted_card))
        self.assertEqual(album['display_name'], 'Trip')
        self.assertEqual(album['current_destination'], str(self.root / 'Fans Group' / 'Trip'))
        self.assertEqual(album['status'], 'COMPLETED')
        self.assertNotIn('trip', album_key(sorted_card))

    def test_safe_components_unicode_case_collisions_and_photo_width(self):
        self.assertEqual(safe_component('  ..Hidden/A\\B\x00C  '), 'Hidden A B C')
        self.assertEqual(safe_component('A\u0308'), 'Ä')
        self.assertLessEqual(len(safe_component('x' * 500).encode('utf-8')), 180)
        for value in ('', '   ', '.', '..', './'):
            with self.subTest(value=value), self.assertRaisesRegex(DailyError, 'NAME_REQUIRES_USER_INPUT'):
                safe_component(value)
        parent = self.base / 'safe-components'
        parent.mkdir()
        (parent / 'Trip').mkdir()
        self.assertEqual(allocate_component(parent, 'trip'), 'trip (2)')
        self.assertEqual(allocate_component(parent, 'Café', taken=['Cafe\u0301']), 'Café (2)')
        names = ['original-%04d.png' % number for number in range(1000)]
        plan = planned_photo_names('Trip', names)
        self.assertEqual(plan[0]['target_name'], 'Trip_0001.png')
        self.assertTrue(all(len(Path(row['target_name']).stem.split('_')[-1]) == 4 for row in plan))

    def test_album_and_group_corrections_reverify_and_project_new_paths(self):
        self.page(self.cards[:2], top=True)
        self.store.capture_group_name(session_id=self.session, name='Friends',
            source=self.evidence('synthetic group OCR'))
        for card, name in ((self.cards[0], 'Trip'), (self.cards[1], 'trip')):
            self.store.capture_album_name(session_id=self.session, identity=card,
                name=name, source=self.evidence('synthetic album OCR ' + name))
        completed = []
        for card, names in ((self.cards[0], ('b.png', 'a.jpg')), (self.cards[1], ('d.png', 'c.jpg'))):
            self.detail(card)
            attempt = self.store.intent(session_id=self.session, identity=card)
            for name in names:
                (Path(attempt['destination']) / name).write_bytes(png())
            self.finished(attempt)
            completed.append(self.complete(attempt))
        group_path = self.root / 'Friends'
        self.assertTrue((group_path / 'Trip').is_dir())
        corrected = self.store.correct_album_name(album_key=album_key(self.cards[1]), name='Journey',
            source=self.evidence('synthetic Owner album correction'),
            decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        self.assertFalse((group_path / 'trip (2)').exists())
        self.assertTrue((group_path / 'Journey').is_dir())
        self.assertEqual([row['name'] for row in corrected['correction']['albums'][0]['proof']['manifest']],
                         ['Journey_001.jpg', 'Journey_002.png'])
        self.assertEqual(self.store.status_map()[album_key(self.cards[1])], 'COMPLETED')
        grouped = self.store.correct_group_name(name='Friends/Archive',
            source=self.evidence('synthetic Owner group correction'),
            decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        new_group = self.root / 'Friends Archive'
        self.assertFalse(group_path.exists())
        self.assertTrue((new_group / 'Trip').is_dir())
        self.assertTrue((new_group / 'Journey').is_dir())
        self.assertEqual(len(grouped['correction']['albums']), 2)
        self.assertEqual(set(self.store.status_map()[album_key(card)] for card in self.cards[:2]),
                         {'COMPLETED'})
        memory = DailyRecords(self.root).memory()
        self.assertEqual(memory['group']['path_name'], 'Friends Archive')
        self.assertEqual({row['current_destination'] for row in memory['albums'][:2]},
                         {str(new_group / 'Trip'), str(new_group / 'Journey')})

    def test_initial_naming_resumes_after_interruption_without_second_transaction(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        self.store.capture_group_name(session_id=self.session, name='Trip Group',
            source=self.evidence('synthetic group OCR'))
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Trip',
            source=self.evidence('synthetic album OCR'))
        self.detail(self.cards[0])
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        for name in ('2.png', '1.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        original_rename = daily_module.exclusive_rename
        interrupted_once = {'value': False}
        def interrupted(source, target):
            if (not interrupted_once['value'] and Path(target).name.startswith('.line-naming-') and
                    Path(target).name.endswith('.tmp')):
                interrupted_once['value'] = True
                raise OSError('synthetic naming interruption')
            return original_rename(source, target)
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.complete(attempt)
        resumed = DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
                                                        decoder_sha256=self.decoder_sha)
        self.assertEqual([row['name'] for row in resumed['proof']['manifest']],
                         ['Trip_001.png', 'Trip_002.png'])
        with self.store.locked():
            transactions = self.store.matching('name-transaction')
            completions = self.store.matching('completion')
        self.assertEqual(len(transactions), 1)
        self.assertEqual(len(completions), 1)
        self.assertEqual(DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
            decoder_sha256=self.decoder_sha)['status'], 'NOTHING_TO_RESUME')

    def test_initial_naming_reconciles_file_rename_completed_before_progress(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        self.store.capture_group_name(session_id=self.session, name='Trip Group',
            source=self.evidence('synthetic group OCR'))
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Trip',
            source=self.evidence('synthetic album OCR'))
        self.detail(self.cards[0])
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        for name in ('2.png', '1.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        original_rename = daily_module.exclusive_rename
        interrupted_once = {'value': False}
        def interrupted(source, target):
            result = original_rename(source, target)
            if (not interrupted_once['value'] and Path(target).name.startswith('.line-naming-') and
                    Path(target).name.endswith('.tmp')):
                interrupted_once['value'] = True
                raise OSError('synthetic naming progress interruption')
            return result
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.complete(attempt)
        resumed = DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
            decoder_sha256=self.decoder_sha)
        self.assertEqual([row['name'] for row in resumed['proof']['manifest']],
                         ['Trip_001.png', 'Trip_002.png'])
        with self.store.locked():
            self.assertEqual(len(self.store.matching('name-transaction')), 1)
            self.assertEqual(len(self.store.matching('completion')), 1)
        self.assertEqual(DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
            decoder_sha256=self.decoder_sha)['status'], 'NOTHING_TO_RESUME')

    def test_pending_album_correction_is_protected_then_resumes(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        self.store.capture_group_name(session_id=self.session, name='Trip Group',
            source=self.evidence('synthetic group OCR'))
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Trip',
            source=self.evidence('synthetic album OCR'))
        self.detail(self.cards[0])
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        original_rename = daily_module.exclusive_rename
        interrupted_once = {'value': False}
        def interrupted(source, target):
            if (not interrupted_once['value'] and Path(target).name.startswith('.line-naming-') and
                    Path(target).name.endswith('.tmp')):
                interrupted_once['value'] = True
                raise OSError('synthetic correction interruption')
            return original_rename(source, target)
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.store.correct_album_name(album_key=album_key(self.cards[0]), name='Renamed',
                    source=self.evidence('synthetic Owner correction'),
                    decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        self.assertEqual(DailyRecords(self.root).status_map()[album_key(self.cards[0])],
                         'PROTECTED_HISTORY')
        corrected = DailyRecords(self.root).correct_album_name(album_key=album_key(self.cards[0]),
            name='Renamed', source=self.evidence('retry source is not used for stored plan'),
            decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        self.assertTrue((self.root / 'Trip Group' / 'Renamed').is_dir())
        self.assertEqual([row['name'] for row in corrected['correction']['albums'][0]['proof']['manifest']],
                         ['Renamed_001.png', 'Renamed_002.png'])
        self.assertEqual(DailyRecords(self.root).status_map()[album_key(self.cards[0])], 'COMPLETED')

    def test_album_correction_reconciles_file_rename_completed_before_progress(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        self.store.capture_group_name(session_id=self.session, name='Trip Group',
            source=self.evidence('synthetic group OCR'))
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Trip',
            source=self.evidence('synthetic album OCR'))
        self.detail(self.cards[0])
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        original_rename = daily_module.exclusive_rename
        interrupted_once = {'value': False}
        def interrupted(source, target):
            result = original_rename(source, target)
            if (not interrupted_once['value'] and Path(target).name.startswith('.line-naming-') and
                    Path(target).name.endswith('.tmp')):
                interrupted_once['value'] = True
                raise OSError('synthetic correction progress interruption')
            return result
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.store.correct_album_name(album_key=album_key(self.cards[0]), name='Renamed',
                    source=self.evidence('synthetic Owner correction'),
                    decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        corrected = DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
            decoder_sha256=self.decoder_sha)
        self.assertTrue((self.root / 'Trip Group' / 'Renamed').is_dir())
        self.assertEqual([row['name'] for row in corrected['correction']['albums'][0]['proof']['manifest']],
                         ['Renamed_001.png', 'Renamed_002.png'])
        with self.store.locked():
            self.assertEqual(len(self.store.matching('name-correction-plan')), 1)
            self.assertEqual(len(self.store.matching('album-name')), 2)
            self.assertEqual(len(self.store.matching('completion')), 1)
        self.assertEqual(DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
            decoder_sha256=self.decoder_sha)['status'], 'NOTHING_TO_RESUME')

    def test_group_correction_refuses_an_incomplete_named_child(self):
        self.page(self.cards[:2], top=True)
        first = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(first['destination']) / name).write_bytes(png())
        self.finished(first)
        self.complete(first)
        self.intent(self.cards[1])
        with self.assertRaisesRegex(DailyError, 'FOREIGN_OR_INCOMPLETE_GROUP_CONTENT'):
            self.store.correct_group_name(name='Renamed Group',
                source=self.evidence('synthetic Owner group correction'),
                decoder=str(self.decoder), decoder_sha256=self.decoder_sha)

    def test_case_only_album_correction_uses_safe_rename_chain(self):
        self.page(self.cards[:1], top=True)
        self.store.capture_group_name(session_id=self.session, name='Case Group',
            source=self.evidence('synthetic group OCR'))
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Trip',
            source=self.evidence('synthetic album OCR'))
        self.detail(self.cards[0])
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        corrected = self.store.correct_album_name(album_key=album_key(self.cards[0]), name='trip',
            source=self.evidence('synthetic case-only Owner correction'),
            decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        self.assertTrue((self.root / 'Case Group' / 'trip').is_dir())
        self.assertEqual([row['name'] for row in corrected['correction']['albums'][0]['proof']['manifest']],
                         ['trip_001.png', 'trip_002.png'])

    def test_initial_naming_metadata_drift_after_transaction_is_refused(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        original_rename = daily_module.exclusive_rename
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=OSError('synthetic stop')):
            with self.assertRaises(OSError):
                self.complete(attempt)
        source = Path(attempt['destination']) / '1.png'
        info = source.stat()
        os.utime(source, ns=(info.st_atime_ns, info.st_mtime_ns + 1_000_000_000))
        with self.assertRaisesRegex(DailyError, 'NAMING_FILE_CHANGED'):
            DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
                                                   decoder_sha256=self.decoder_sha)
        self.assertTrue(source.exists())
        self.assertEqual(len(self.store.matching('completion')), 0)
        self.assertIs(original_rename, daily_module.exclusive_rename)

    def test_resume_naming_recovers_finished_before_transaction(self):
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        resumed = DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
                                                        decoder_sha256=self.decoder_sha)
        self.assertEqual([row['name'] for row in resumed['proof']['manifest']],
                         ['Album synthetic-cover-0_001.png', 'Album synthetic-cover-0_002.png'])
        with self.store.locked():
            self.assertEqual(len(self.store.matching('name-transaction')), 1)
            self.assertEqual(len(self.store.matching('completion')), 1)

    def test_resume_naming_revalidates_finished_evidence(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=OSError('synthetic stop')):
            with self.assertRaises(OSError):
                self.complete(attempt)
        with self.store.locked():
            evidence = Path(self.store.matching('outcome')[-1]['evidence']['path'])
        evidence.write_text('tampered synthetic outcome', encoding='utf-8')
        with self.assertRaisesRegex(DailyError, 'EVIDENCE_DRIFT'):
            DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
                                                   decoder_sha256=self.decoder_sha)
        self.assertEqual(len(self.store.matching('completion')), 0)

    def test_resume_naming_refuses_unknown_outcome(self):
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        self.store.outcome(session_id=self.session, attempt_id=attempt['attempt_id'],
                           outcome='UNKNOWN', evidence=self.evidence('synthetic unknown outcome'))
        with self.assertRaisesRegex(DailyError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
                                                   decoder_sha256=self.decoder_sha)

    def test_resume_naming_refuses_stopped_outcome(self):
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        self.store.outcome(session_id=self.session, attempt_id=attempt['attempt_id'],
                           outcome='STOPPED', evidence=self.evidence('synthetic stopped outcome'))
        with self.assertRaisesRegex(DailyError, 'NO_DOWNLOAD_FINISHED_TO_RESUME'):
            DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
                                                   decoder_sha256=self.decoder_sha)

    def test_resume_naming_refuses_intent_without_outcome(self):
        self.page(self.cards[:1], top=True)
        self.intent(self.cards[0])
        with self.assertRaisesRegex(DailyError, 'KNOWN_DOWNLOAD_FINISH_REQUIRED'):
            DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
                                                   decoder_sha256=self.decoder_sha)

    def test_complete_refuses_duplicate_while_correction_is_pending(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=OSError('synthetic stop')):
            with self.assertRaises(OSError):
                self.store.correct_album_name(album_key=album_key(self.cards[0]), name='Renamed',
                    source=self.evidence('synthetic Owner correction'),
                    decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        with self.assertRaisesRegex(DailyError, 'PENDING_NAMING_TRANSACTION'):
            self.complete(attempt)
        self.assertEqual(len(self.store.matching('completion')), 1)

    def test_group_correction_rechecks_content_before_rename(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        self.store.capture_group_name(session_id=self.session, name='Trip Group',
            source=self.evidence('synthetic group OCR'))
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Trip',
            source=self.evidence('synthetic album OCR'))
        self.detail(self.cards[0])
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=OSError('synthetic stop')):
            with self.assertRaises(OSError):
                self.store.correct_group_name(name='Renamed Group',
                    source=self.evidence('synthetic Owner group correction'),
                    decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        image = next((self.root / 'Trip Group' / 'Trip').glob('*.png'))
        image.write_bytes(png((0, 255, 0)))
        with self.assertRaisesRegex(DailyError, 'CORRECTION_CONTENT_CHANGED'):
            DailyRecords(self.root).correct_group_name(name='Renamed Group',
                source=self.evidence('unused stored correction source'),
                decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        self.assertTrue((self.root / 'Trip Group' / 'Trip').is_dir())
        self.assertEqual(DailyRecords(self.root).status_map()[album_key(self.cards[0])],
                         'PROTECTED_HISTORY')

    def test_album_correction_rechecks_content_after_plan_before_rename(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        self.store.capture_group_name(session_id=self.session, name='Trip Group',
            source=self.evidence('synthetic group OCR'))
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Trip',
            source=self.evidence('synthetic album OCR'))
        self.detail(self.cards[0])
        attempt = self.store.intent(session_id=self.session, identity=self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=OSError('synthetic stop')):
            with self.assertRaises(OSError):
                self.store.correct_album_name(album_key=album_key(self.cards[0]), name='Renamed',
                    source=self.evidence('synthetic Owner album correction'),
                    decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        album_path = self.root / 'Trip Group' / 'Trip'
        image = next(album_path.glob('*.png'))
        changed = png((0, 255, 0))
        image.write_bytes(changed)
        with self.assertRaisesRegex(DailyError, 'CORRECTION_CONTENT_CHANGED'):
            DailyRecords(self.root).resume_naming(decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        self.assertTrue(album_path.is_dir())
        self.assertEqual(image.read_bytes(), changed)
        self.assertEqual(DailyRecords(self.root).status_map()[album_key(self.cards[0])],
                         'PROTECTED_HISTORY')
        with self.store.locked():
            self.assertEqual(len(self.store.matching('album-name')), 1)

    def test_group_correction_rejects_swapped_child_directories(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:2], top=True)
        self.store.capture_group_name(session_id=self.session, name='Two Albums',
            source=self.evidence('synthetic group OCR'))
        for card, name, color in ((self.cards[0], 'Alpha', (255, 0, 0)),
                                  (self.cards[1], 'Beta', (0, 255, 0))):
            self.store.capture_album_name(session_id=self.session, identity=card, name=name,
                source=self.evidence('synthetic album OCR ' + name))
            self.detail(card)
            attempt = self.store.intent(session_id=self.session, identity=card)
            (Path(attempt['destination']) / '1.png').write_bytes(png(color))
            (Path(attempt['destination']) / '2.png').write_bytes(png((0, 0, 255)))
            self.finished(attempt)
            self.complete(attempt)
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=OSError('synthetic stop')):
            with self.assertRaises(OSError):
                self.store.correct_group_name(name='Two Albums Renamed',
                    source=self.evidence('synthetic Owner group correction'),
                    decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        group = self.root / 'Two Albums'
        hold = self.base / 'synthetic-swap-hold'
        (group / 'Alpha').rename(hold)
        (group / 'Beta').rename(group / 'Alpha')
        hold.rename(group / 'Beta')
        with self.assertRaisesRegex(DailyError, 'CORRECTION_DIRECTORY_CHANGED'):
            DailyRecords(self.root).correct_group_name(name='Two Albums Renamed',
                source=self.evidence('unused stored correction source'),
                decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        self.assertTrue(group.is_dir())

    def test_group_correction_resumes_after_directory_temp_rename(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        original_rename = daily_module.exclusive_rename
        def interrupted(source, target):
            if Path(target).name == 'Renamed Group':
                raise OSError('synthetic group directory interruption')
            return original_rename(source, target)
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.store.correct_group_name(name='Renamed Group',
                    source=self.evidence('synthetic Owner group correction'),
                    decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        with self.store.locked():
            plan = self.store.matching('name-correction-plan')[-1]
        self.assertFalse((self.root / 'Synthetic Group').exists())
        self.assertTrue((self.root / plan['temp_group_path_name']).is_dir())
        corrected = DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
            decoder_sha256=self.decoder_sha)
        self.assertTrue((self.root / 'Renamed Group' / attempt['naming']['album_path_name']).is_dir())
        self.assertEqual(len(corrected['correction']['albums']), 1)
        with self.store.locked():
            self.assertEqual(len(self.store.matching('group-name')), 2)

    def test_group_correction_reconciles_rename_completed_before_progress(self):
        from line_backup_batch import daily as daily_module
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        original_rename = daily_module.exclusive_rename
        def interrupted(source, target):
            result = original_rename(source, target)
            if Path(target).name == 'Renamed Group':
                raise OSError('synthetic interruption after directory rename')
            return result
        with mock.patch.object(daily_module, 'exclusive_rename', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.store.correct_group_name(name='Renamed Group',
                    source=self.evidence('synthetic Owner group correction'),
                    decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        self.assertFalse((self.root / 'Synthetic Group').exists())
        self.assertTrue((self.root / 'Renamed Group' / attempt['naming']['album_path_name']).is_dir())
        with self.store.locked():
            plan = self.store.matching('name-correction-plan')[-1]
            progress = self.store.matching('name-progress')
        self.assertFalse(any(row.get('action') == 'TEMP_TO_DIRECTORY' for row in progress))
        corrected = DailyRecords(self.root).resume_naming(decoder=str(self.decoder),
            decoder_sha256=self.decoder_sha)
        self.assertEqual(len(corrected['correction']['albums']), 1)
        with self.store.locked():
            actions = [row.get('action') for row in self.store.matching('name-progress')
                       if row.get('transaction_id') == plan['transaction_id']]
            self.assertEqual(actions.count('DIRECTORY_TO_TEMP'), 1)
            self.assertEqual(actions.count('TEMP_TO_DIRECTORY'), 1)
            self.assertEqual(len(self.store.matching('group-name')), 2)

    def test_album_and_group_corrections_refuse_legacy_unknown_outside_group(self):
        self.page(self.cards[:2], top=True)
        first = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(first['destination']) / name).write_bytes(png())
        self.finished(first)
        self.complete(first)
        self.legacy_intent(self.cards[1])
        with self.assertRaisesRegex(DailyError, 'UNSUPPORTED_OLDER_FORMAT_CORRECTION'):
            self.store.correct_group_name(name='Changed Group',
                source=self.evidence('synthetic Owner group correction'),
                decoder=str(self.decoder), decoder_sha256=self.decoder_sha)
        with self.assertRaisesRegex(DailyError, 'UNSUPPORTED_OLDER_FORMAT_CORRECTION'):
            self.store.correct_album_name(album_key=album_key(self.cards[0]), name='Changed Album',
                source=self.evidence('synthetic Owner album correction'),
                decoder=str(self.decoder), decoder_sha256=self.decoder_sha)

    def test_album_correction_refuses_foreign_group_entry(self):
        self.page(self.cards[:1], top=True)
        attempt = self.intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        group = Path(attempt['destination']).parent
        (group / 'foreign').mkdir()
        with self.assertRaisesRegex(DailyError, 'FOREIGN_OR_INCOMPLETE_GROUP_CONTENT'):
            self.store.correct_album_name(album_key=album_key(self.cards[0]), name='Renamed',
                source=self.evidence('synthetic Owner album correction'),
                decoder=str(self.decoder), decoder_sha256=self.decoder_sha)

    def test_sanitized_names_and_symlink_destination_targets_are_not_followed(self):
        self.page(self.cards[:1], top=True)
        group = self.store.capture_group_name(session_id=self.session, name='../Group',
            source=self.evidence('synthetic traversal group name'))
        album = self.store.capture_album_name(session_id=self.session, identity=self.cards[0],
            name='A/B/../Album', source=self.evidence('synthetic traversal album name'))
        self.assertEqual((group['path_name'], album['path_name']), ('Group', 'A B .. Album'))
        outside = self.base / 'outside'
        outside.mkdir()
        (self.root / 'Group' / 'A B .. Album').symlink_to(outside)
        self.detail(self.cards[0])
        with self.assertRaisesRegex(DailyError, 'TARGET_ALREADY_EXISTS'):
            self.store.intent(session_id=self.session, identity=self.cards[0])
        self.assertEqual(list(outside.iterdir()), [])

    def test_corrections_refuse_legacy_format_and_foreign_group_content(self):
        self.page(self.cards[:1], top=True)
        attempt = self.legacy_intent(self.cards[0])
        for name in ('1.png', '2.png'):
            (Path(attempt['destination']) / name).write_bytes(png())
        self.finished(attempt)
        self.complete(attempt)
        self.store.capture_group_name(session_id=self.session, name='Legacy Group',
            source=self.evidence('synthetic OCR after legacy completion'))
        self.store.capture_album_name(session_id=self.session, identity=self.cards[0], name='Legacy Album',
            source=self.evidence('synthetic album OCR after legacy completion'))
        with self.assertRaisesRegex(DailyError, 'UNSUPPORTED_OLDER_FORMAT_CORRECTION'):
            self.store.correct_album_name(album_key=album_key(self.cards[0]), name='Changed',
                source=self.evidence('synthetic Owner correction'),
                decoder=str(self.decoder), decoder_sha256=self.decoder_sha)

        other = dict(self.cards[1], expected_images=1, visual_key='synthetic-new-format-child')
        self.store.start_scan(session_id=self.session)
        self.page([self.cards[0], other], top=True)
        self.store.capture_album_name(session_id=self.session, identity=other, name='Child',
            source=self.evidence('synthetic second album OCR'))
        self.detail(other)
        named_attempt = self.store.intent(session_id=self.session, identity=other)
        (Path(named_attempt['destination']) / 'one.png').write_bytes(png())
        self.finished(named_attempt)
        self.complete(named_attempt)
        group_path = self.root / 'Legacy Group'
        (group_path / 'foreign').mkdir()
        with self.assertRaisesRegex(DailyError, 'FOREIGN_OR_INCOMPLETE_GROUP_CONTENT'):
            self.store.correct_group_name(name='Changed Group',
                source=self.evidence('synthetic Owner group correction'),
                decoder=str(self.decoder), decoder_sha256=self.decoder_sha)


if __name__ == '__main__':
    unittest.main()
