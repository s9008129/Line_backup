"""Synthetic accounting plus real macOS ImageIO; no LINE or GUI input."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

from line_backup_batch.daily import (DailyRecords, DailyError, NORMALIZED_HISTORY_SCHEMA,
                                     album_key, digest, encoded, reference, verify_directory)


def png():
    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) + \
        chunk(b'IDAT', zlib.compress((b'\0' + b'\xff\0\0' * 2) * 2)) + chunk(b'IEND', b'')


class DailyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Foundation normalizes /private/var to /var while pathlib resolves in
        # the other direction. The unchanged decoder intentionally rejects that
        # alias; use a real fixture directory in this checkout instead.
        cls.fixtures = tempfile.TemporaryDirectory(prefix='.line-daily-tests-',
                                                   dir=Path(__file__).resolve().parents[1])
        cls.tools = tempfile.TemporaryDirectory(prefix='line-daily-decoder-')
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
        self.detail(card)
        return self.store.intent(session_id=self.session, identity=card, recovery_authorization=recovery)

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
        manifest_path.write_bytes(encoded({'manifest': manifest, 'manifest_sha256': '0' * 64}))
        self.assertEqual(store.status_map()[album_key(identity)], 'PROTECTED_HISTORY')

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
        self.assertEqual(len(list((self.root / 'albums').iterdir())), 1)

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
        (Path(attempt['destination']) / '1.png').unlink()
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
        with self.assertRaises(OSError):
            self.complete(attempt)

    def test_cross_group_authorization_request_cannot_create_consent_review_or_grant(self):
        self.page(self.cards[:1], top=True)
        request = self.store.authorization_request(session_id=self.session, identity=self.cards[0],
                                                    owner_request=self.evidence('synthetic Owner request'))
        self.assertEqual(request['status'], 'BLOCKED_NEW_GROUP_ISSUER_REQUIRES_REVIEW')
        self.assertFalse(request['dispatch_authorized'])
        self.assertIsNone(request['external_implementation_review'])
        self.assertIsNone(request['runtime_grant'])
        self.assertFalse(request['native_authorize_is_issuer'])
        self.assertFalse((self.root / 'albums').exists())

    def test_torn_event_or_changed_evidence_blocks_without_resetting_history(self):
        self.page(self.cards[:1], top=True)
        events = self.root / 'backup-records/events'
        before = {p.name: p.read_bytes() for p in events.iterdir()}
        pending = events / '.pending-interrupted'
        pending.write_bytes(b'{')
        with self.assertRaisesRegex(DailyError, 'EVENT_SEQUENCE_OR_PENDING_WRITE'):
            self.store.summary()
        self.assertEqual({p.name: p.read_bytes() for p in events.iterdir() if p != pending}, before)


if __name__ == '__main__':
    unittest.main()
