"""Synthetic offline tests for Notes restart batches and version activation."""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest import mock
import uuid
import zlib

from line_backup_batch import media_verify, notes, notes_evidence
from line_backup_batch.daily import digest, encoded
from line_backup_batch.media_verify import MediaVerificationError
from line_backup_batch.notes import (
    LOCAL_VERIFIED,
    PHOTO,
    VIDEO,
    NotesCollection,
    NotesError,
    NotesRecords,
)


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TASKS = ROOT / '.local' / 'line-backup' / 'tasks'


def png(color=(255, 0, 0)):
    def chunk(name, data):
        return (struct.pack('>I', len(data)) + name + data +
                struct.pack('>I', zlib.crc32(name + data) & 0xffffffff))

    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * 2) * 2)) +
            chunk(b'IEND', b''))


def video_bytes(marker=0):
    return b'ftypisom' + b'\0' * 8 + bytes([marker]) * 64


class NotesRestartTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='notes-restart-', dir=PRIVATE_TASKS)
        self.base = Path(self.temporary.name).resolve()
        self.evidence_source = self.base / 'synthetic-evidence.txt'
        self.evidence_source.write_bytes(b'synthetic notes restart evidence')
        self.screenshot = self.base / 'synthetic-screenshot.txt'
        self.screenshot.write_bytes(b'synthetic notes restart screenshot')
        self.evidence_packs = self.base / 'evidence-packs'
        self.evidence_packs.mkdir()
        self.photo_root = self.base / 'photos'
        self.collection_path = self.base / 'records'
        self.collection = NotesCollection(str(self.collection_path))
        self.session = 'synthetic-restart-session-1'
        self.active_patch = mock.patch.object(
            notes, '_write_active_hint', return_value=None)
        self.active_patch.start()
        self.records, self.summary = self.new_ledger('synthetic-restart-list')

    def tearDown(self):
        self.active_patch.stop()
        self.temporary.cleanup()

    def make_evidence(self, **context):
        output = self.evidence_packs / uuid.uuid4().hex
        return notes_evidence.create_bundle(
            statement=str(self.evidence_source),
            assets=[('screenshot', str(self.screenshot))],
            context=context, output_dir=str(output))['bundle_path']

    def new_ledger(self, visual_key):
        identity = notes.list_identity(visual_key=visual_key)
        list_key_value = notes.list_key(identity)
        evidence = self.make_evidence(list_key=list_key_value)
        summary = self.collection.create(
            photo_root=str(self.photo_root),
            display_name='Synthetic Restart Notes',
            identity=identity,
            binding_evidence=evidence,
            history_scope_evidence=evidence,
            recovery_authorized=True)
        records = NotesRecords(
            summary['records_root'], _allow_injected_verification=True)
        records.bind(
            session_id=self.session,
            observation=self.make_evidence(
                list_key=summary['list_key']),
            handoff=self.make_evidence(list_key=summary['list_key']))
        return records, summary

    def reopen(self, records):
        return NotesRecords(
            str(records.records), _allow_injected_verification=True)

    def bind(self, records, session):
        return records.bind(
            session_id=session,
            observation=self.make_evidence(
                list_key=records.list_data['list_key']),
            handoff=self.make_evidence(
                list_key=records.list_data['list_key']))

    def scan_posts(self, records, posts, *, session=None, recovery=False):
        session = session or self.session
        list_key_value = records.list_data['list_key']
        scan = records.scan(
            session_id=session, action='START',
            evidence=self.make_evidence(list_key=list_key_value),
            recovery=recovery)
        page_rows = []
        for post in posts:
            page_rows.append(dict(identity=post['identity'],
                                  date_summary=post['date']))
        scan_evidence = self.make_evidence(
            list_key=list_key_value, scan_id=scan['scan_id'])
        records.page(
            session_id=session, scan_id=scan['scan_id'], page_index=0,
            posts=page_rows, top_reached=True, bottom_reached=True,
            overlap_keys=[], evidence=scan_evidence)
        records.scan(
            session_id=session, action='FINISH', scan_id=scan['scan_id'],
            evidence=scan_evidence)
        result = {}
        for post in posts:
            post_key_value = notes.post_key(list_key_value, post['identity'])
            post_evidence = self.make_evidence(
                list_key=list_key_value, post_key=post_key_value,
                scan_id=scan['scan_id'])
            records.record_post(
                session_id=session, post_key_value=post_key_value,
                date_summary=post['date'],
                media_count=len(post['media']) + len(post.get('missing', [])),
                text_sha256=None, evidence=post_evidence,
                no_media=not post['media'] and not post.get('missing'))
            if post['media'] or post.get('missing'):
                records.record_media(
                    session_id=session, post_key_value=post_key_value,
                    items=[dict(identity=identity)
                           for identity in post['media']],
                    missing=post.get('missing', []), evidence=post_evidence)
            result[post['name']] = (post_key_value, scan)
        return result

    def media_key(self, post_key_value, identity):
        return notes.media_key(
            self.records.list_data['list_key'], post_key_value, identity)

    def attempt_evidence(self, records, attempt):
        return self.make_evidence(
            list_key=records.list_data['list_key'],
            post_key=attempt['post_key'], media_key=attempt['media_key'],
            attempt_id=attempt['attempt_id'], scan_id=attempt['scan_id'])

    def confirm_restart(self, records, preview, *, session=None):
        session = session or self.session
        return records.restart_confirm(
            session_id=session, preview=preview,
            evidence=self.make_evidence(
                list_key=records.list_data['list_key'],
                scan_id=preview['scope']['scan_id']))

    def scan_after_confirm(self, records, posts, *, session=None):
        return self.scan_posts(records, posts, session=session, recovery=True)

    def finish_restart_attempt(self, records, attempt, name, payload):
        path = Path(attempt['destination']) / name
        path.write_bytes(payload)
        records.outcome(
            session_id=self.session,
            attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=self.attempt_evidence(records, attempt))
        return path

    @staticmethod
    def pass_verifier(path, row, identity):
        del path, identity
        return dict(verdict='PASS', sha256=row['sha256'])

    def download(self, records, key, name, payload, *, session=None,
                 outcome='DOWNLOAD_FINISHED', verifier=None):
        session = session or self.session
        attempt = records.intent(
            session_id=session, media_key_value=key)
        (Path(attempt['destination']) / name).write_bytes(payload)
        evidence = self.attempt_evidence(records, attempt)
        records.outcome(
            session_id=session, attempt_id=attempt['attempt_id'],
            outcome=outcome, evidence=evidence)
        completion = None
        if outcome == 'DOWNLOAD_FINISHED':
            completion = records.verify(
                session_id=session, attempt_id=attempt['attempt_id'],
                verifier=verifier or self.pass_verifier,
                stability_interval=0)
        return attempt, completion

    def restart_download(self, records, key, name, payload, restart_id,
                         *, session=None):
        session = session or self.session
        attempt = records.intent(
            session_id=session, media_key_value=key,
            restart_id=restart_id)
        (Path(attempt['destination']) / name).write_bytes(payload)
        evidence = self.attempt_evidence(records, attempt)
        records.outcome(
            session_id=session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED', evidence=evidence)
        return attempt

    def event_files(self, records=None):
        records = records or self.records
        return {path.name: path.read_bytes()
                for path in (records.records / 'events').iterdir()}

    def read_events(self, records):
        return [json.loads(path.read_text(encoding='utf-8'))
                for path in sorted((records.records / 'events').iterdir())]

    def rewrite_events(self, records, events):
        previous = None
        for index, event in enumerate(events, 1):
            event['sequence'] = index
            event['previous_sha256'] = previous
            raw = encoded(event)
            notes._atomic_replace_json(
                records.records / 'events' / ('%08d.json' % index), event)
            previous = digest(raw)

    def one_media_restart_context(self, label, kind=PHOTO, confirm=True):
        photo = notes.media_identity(
            kind=kind, visual_key=label + '-photo')
        post_identity = notes.post_identity(visual_key=label + '-post')
        observed = self.scan_posts(
            self.records,
            [dict(name='post', identity=post_identity, date='2026-11-03',
                  media=[photo])])
        post_key_value, initial_scan = observed['post']
        key = self.media_key(post_key_value, photo)
        old = self.records.intent(
            session_id=self.session, media_key_value=key)
        old_raw = Path(old['destination']) / (
            'old.png' if kind == PHOTO else 'old.mp4')
        old_raw.write_bytes(png((10, 20, 30)))
        self.records.outcome(
            session_id=self.session, attempt_id=old['attempt_id'],
            outcome='UNKNOWN',
            evidence=self.attempt_evidence(self.records, old))
        preview = self.records.restart_preview()
        self.assertEqual(preview['status'], 'RESTART_REQUIRED')
        if confirm:
            self.confirm_restart(self.records, preview)
            self.scan_after_confirm(
                self.records,
                [dict(name='post', identity=post_identity, date='2026-11-03',
                      media=[photo])])
        return dict(key=key, photo=photo, post_identity=post_identity,
                    initial_scan=initial_scan, old=old, old_raw=old_raw,
                    preview=preview)

    def test_restart_unknown_and_no_outcome_attempts_can_be_superseded(self):
        photo = notes.media_identity(
            kind=PHOTO, visual_key='restart-c07-photo')
        post_identity = notes.post_identity(visual_key='restart-c07-post')
        observed = self.scan_posts(
            self.records,
            [dict(name='post', identity=post_identity, date='2026-11-03',
                  media=[photo])])
        post_key_value, _ = observed['post']
        key = self.media_key(post_key_value, photo)

        old = self.records.intent(
            session_id=self.session, media_key_value=key)
        old_raw = Path(old['destination']) / 'old.png'
        old_raw.write_bytes(png((10, 20, 30)))
        self.records.outcome(
            session_id=self.session, attempt_id=old['attempt_id'],
            outcome='UNKNOWN',
            evidence=self.attempt_evidence(self.records, old))
        old_bytes = self.event_files()

        preview = self.records.restart_preview()
        self.assertEqual(preview['status'], 'RESTART_REQUIRED')
        self.confirm_restart(self.records, preview)
        self.scan_after_confirm(
            self.records,
            [dict(name='post', identity=post_identity, date='2026-11-03',
                  media=[photo])])

        first = self.records.intent(
            session_id=self.session, media_key_value=key,
            restart_id=preview['restart_id'])
        first_raw = Path(first['destination']) / 'first.png'
        first_raw.write_bytes(png((40, 50, 60)))
        first_intent_sequence = max(
            event['sequence'] for event in self.records.events
            if event['kind'] == 'intent' and
            event['data']['attempt_id'] == first['attempt_id'])

        second = self.records.intent(
            session_id=self.session, media_key_value=key,
            restart_id=preview['restart_id'])
        self.assertNotEqual(first['attempt_id'], second['attempt_id'])
        self.assertEqual(second['prior_attempt']['sequence'],
                         first_intent_sequence)
        self.assertEqual(
            self.records.events[first['prior_attempt']['sequence'] - 1][
                'data']['attempt_id'], old['attempt_id'])
        self.assertEqual(first_raw.read_bytes(), png((40, 50, 60)))
        self.assertEqual(old_raw.read_bytes(), png((10, 20, 30)))
        for name, raw in old_bytes.items():
            self.assertEqual(self.event_files()[name], raw)

        self.records.outcome(
            session_id=self.session, attempt_id=second['attempt_id'],
            outcome='UNKNOWN',
            evidence=self.attempt_evidence(self.records, second))
        second_intent_sequence = max(
            event['sequence'] for event in self.records.events
            if event['kind'] == 'intent' and
            event['data']['attempt_id'] == second['attempt_id'])
        third = self.records.intent(
            session_id=self.session, media_key_value=key,
            restart_id=preview['restart_id'])
        self.assertNotEqual(second['attempt_id'], third['attempt_id'])
        self.assertEqual(third['prior_attempt']['sequence'],
                         second_intent_sequence)
        self.assertEqual(first_raw.read_bytes(), png((40, 50, 60)))
        self.assertEqual(old_raw.read_bytes(), png((10, 20, 30)))
        self.assertFalse(any(
            event['kind'] == 'reconcile' and
            event['data'].get('attempt_id') in (first['attempt_id'],
                                                second['attempt_id'])
            for event in self.records.events))

    def test_restart_replay_rejects_v3_prior_attempt_drift(self):
        context = self.one_media_restart_context('restart-si-n01')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((41, 42, 43)),
            context['preview']['restart_id'])
        events = self.read_events(self.records)
        intent = next(
            event for event in events if event['kind'] == 'intent' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        self.assertIsNotNone(intent['data']['prior_attempt'])
        intent['data']['prior_attempt'] = None
        self.rewrite_events(self.records, events)

        with self.assertRaisesRegex(
                NotesError, 'RESTART_PRIOR_ATTEMPT_CHANGED'):
            self.reopen(self.records).summary()

    def test_interrupted_recovery_scan_and_new_session_are_bound_to_new_attempt(self):
        context = self.one_media_restart_context('restart-c06')
        old_scan_id = context['old']['scan_id']
        new_session = 'synthetic-restart-session-2'
        self.bind(self.records, new_session)
        evidence = self.make_evidence(
            list_key=self.records.list_data['list_key'])
        started = self.records.scan(
            session_id=new_session, action='START', recovery=True,
            evidence=evidence)
        self.records.page(
            session_id=new_session, scan_id=started['scan_id'],
            page_index=0,
            posts=[dict(identity=context['post_identity'],
                        date_summary='2026-11-03')],
            top_reached=True, bottom_reached=True, overlap_keys=[],
            evidence=self.make_evidence(
                list_key=self.records.list_data['list_key'],
                scan_id=started['scan_id']))
        self.records.scan(
            session_id=new_session, action='INTERRUPT',
            scan_id=started['scan_id'], reason='synthetic foreground loss',
            evidence=self.make_evidence(
                list_key=self.records.list_data['list_key'],
                scan_id=started['scan_id']))
        reopened = self.reopen(self.records)
        reopened.summary()
        latest, scans = reopened._open_scan()
        self.assertEqual(latest, started['scan_id'])
        self.assertIsNone(scans[started['scan_id']]['complete'])
        self.assertEqual(scans[started['scan_id']]['interrupted'][
                             'data']['action'], 'INTERRUPTED')
        self.assertNotEqual(latest, old_scan_id)

        self.scan_posts(
            reopened,
            [dict(name='post', identity=context['post_identity'],
                  date='2026-11-03', media=[context['photo']])],
            session=new_session, recovery=True)
        recovery = reopened.intent(
            session_id=new_session, media_key_value=context['key'],
            restart_id=context['preview']['restart_id'])
        self.assertNotEqual(recovery['scan_id'], old_scan_id)
        self.assertEqual(reopened.list_data['list_key'],
                         self.records.list_data['list_key'])
        self.assertEqual(
            reopened._attempt_projection()['attempts'][
                context['old']['attempt_id']]['scan_id'], old_scan_id)

    def test_copy_failure_does_not_publish_a_candidate_or_activate(self):
        context = self.one_media_restart_context('restart-c08-copy')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((70, 80, 90)),
            context['preview']['restart_id'])
        before = self.event_files()
        with mock.patch.object(
                media_verify, '_copy_exclusive',
                side_effect=MediaVerificationError(
                    'SYNTHETIC_COPY_FAILED', {'stage': 'copy'})):
            with self.assertRaisesRegex(NotesError,
                                        'SYNTHETIC_COPY_FAILED'):
                self.records.verify(
                    session_id=self.session,
                    attempt_id=attempt['attempt_id'],
                    verifier=self.pass_verifier, stability_interval=0)
        after_failure = self.event_files()
        self.assertEqual(len(set(after_failure) - set(before)), 1)
        self.assertFalse(any(
            event['kind'] == 'restart-candidate'
            for event in self.records.events))
        self.assertFalse(any(
            event['kind'] == 'restart-activation'
            for event in self.records.events))
        self.assertEqual(len([
            event for event in self.records.events
            if event['kind'] == 'restart-copy-plan']), 1)
        with mock.patch.object(
                media_verify, '_copy_exclusive',
                wraps=media_verify._copy_exclusive):
            candidate = self.records.verify(
                session_id=self.session, attempt_id=attempt['attempt_id'],
                verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(len([
            event for event in self.records.events
            if event['kind'] == 'restart-copy-plan']), 1)
        self.assertEqual(candidate['status'], 'CANDIDATE_VERIFIED')
        self.assertNotEqual(
            (candidate['candidate']['device'],
             candidate['candidate']['inode']),
            (candidate['source']['device'], candidate['source']['inode']))
        activated = self.records.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')

    def test_activation_reply_loss_is_read_back_without_duplicate(self):
        context = self.one_media_restart_context('restart-c08-activation')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((91, 92, 93)),
            context['preview']['restart_id'])
        self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)

        original = NotesRecords.append
        raised = []

        def append_then_lose_reply(records, kind, data):
            result = original(records, kind, data)
            if kind == 'restart-activation' and not raised:
                raised.append(result)
                raise OSError('synthetic activation reply lost')
            return result

        with mock.patch.object(NotesRecords, 'append', append_then_lose_reply):
            with self.assertRaisesRegex(OSError,
                                        'synthetic activation reply lost'):
                self.records.restart_resume(
                    session_id=self.session, verifier=self.pass_verifier,
                    stability_interval=0)
        self.assertEqual(len(raised), 1)
        reopened = self.reopen(self.records)
        replay = reopened.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(replay['action'], 'ALREADY_ACTIVATED')
        self.assertEqual(
            sum(event['kind'] == 'restart-activation'
                for event in reopened.events), 1)
        summary = reopened.summary()
        self.assertFalse(summary['restart_batch_open'])
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(
            len([row for row in summary['media']
                 if row.get('active_restart_id') ==
                 context['preview']['restart_id']]), 1)

    def test_candidate_reply_loss_is_read_back_without_duplicate(self):
        context = self.one_media_restart_context('restart-c08-candidate')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((94, 95, 96)),
            context['preview']['restart_id'])
        original = NotesRecords.append
        raised = []

        def append_then_lose_reply(records, kind, data):
            result = original(records, kind, data)
            if kind == 'restart-candidate' and not raised:
                raised.append(result)
                raise OSError('synthetic candidate reply lost')
            return result

        with mock.patch.object(NotesRecords, 'append', append_then_lose_reply):
            with self.assertRaisesRegex(OSError,
                                        'synthetic candidate reply lost'):
                self.records.verify(
                    session_id=self.session, attempt_id=attempt['attempt_id'],
                    verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(len(raised), 1)
        reopened = self.reopen(self.records)
        replay = reopened.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        self.assertTrue(replay['replayed'])
        self.assertEqual(
            sum(event['kind'] == 'restart-candidate'
                for event in reopened.events), 1)
        activated = reopened.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)

    def test_restart_vertical_path_isolated_candidate_and_reopen(self):
        photo = notes.media_identity(
            kind=PHOTO, visual_key='restart-a-photo')
        video = notes.media_identity(
            kind=VIDEO, visual_key='restart-a-video')
        unknown_photo = notes.media_identity(
            kind=PHOTO, visual_key='restart-b-unknown')
        post_a_identity = notes.post_identity(visual_key='restart-post-a')
        post_b_identity = notes.post_identity(visual_key='restart-post-b')
        observed = self.scan_posts(
            self.records,
            [dict(name='a', identity=post_a_identity, date='2026-11-01',
                  media=[photo, video]),
             dict(name='b', identity=post_b_identity, date='2026-11-02',
                  media=[unknown_photo])])
        post_a, _ = observed['a']
        post_b, _ = observed['b']
        keys = {
            'photo': self.media_key(post_a, photo),
            'video': self.media_key(post_a, video),
            'unknown': self.media_key(post_b, unknown_photo),
        }

        photo_attempt, photo_completion = self.download(
            self.records, keys['photo'], 'old-a.png', png())
        video_attempt, video_completion = self.download(
            self.records, keys['video'], 'old-a.mp4', video_bytes(1))
        old_directory = Path(photo_completion['data']['destination'])
        old_photo_path = old_directory / photo_completion['data']['target_file']['name']
        old_video_path = old_directory / video_completion['data']['target_file']['name']
        old_photo_hash = hashlib.sha256(old_photo_path.read_bytes()).hexdigest()
        old_video_hash = hashlib.sha256(old_video_path.read_bytes()).hexdigest()

        unknown_attempt = self.records.intent(
            session_id=self.session, media_key_value=keys['unknown'])
        old_raw = Path(unknown_attempt['destination']) / 'old-unknown.png'
        old_raw.write_bytes(png((0, 0, 255)))
        self.records.outcome(
            session_id=self.session,
            attempt_id=unknown_attempt['attempt_id'],
            outcome='UNKNOWN',
            evidence=self.attempt_evidence(self.records, unknown_attempt))
        (old_directory / 'unexpected-history.txt').write_bytes(
            b'makes the old completed directory LOCAL_CHANGED')

        preview = self.records.restart_preview()
        self.assertEqual(preview['status'], 'RESTART_REQUIRED')
        self.assertEqual(
            {post['post_key'] for post in preview['scope']['posts']},
            {post_a, post_b})
        scope_keys = {
            row['media_key']
            for post in preview['scope']['posts']
            for row in post['media']}
        self.assertEqual(scope_keys, set(keys.values()))
        before_confirm = self.event_files()
        with self.assertRaisesRegex(
                NotesError, 'RESTART_CONFIRMATION_REQUIRED'):
            self.records.intent(
                session_id=self.session, media_key_value=keys['photo'],
                restart_id=preview['restart_id'])
        forged = dict(preview, scope_digest='0' * 64)
        with self.assertRaisesRegex(NotesError, 'RESTART_PREVIEW_CHANGED'):
            self.records.restart_confirm(
                session_id=self.session, preview=forged,
                evidence=self.make_evidence(
                    list_key=self.summary['list_key'],
                    scan_id=preview['scope']['scan_id']))
        self.assertEqual(self.event_files(), before_confirm)

        confirm = self.records.restart_confirm(
            session_id=self.session, preview=preview,
            evidence=self.make_evidence(
                list_key=self.summary['list_key'],
                scan_id=preview['scope']['scan_id']))
        self.assertEqual(confirm['status'], 'CONFIRMED')
        replay = self.records.restart_confirm(
            session_id=self.session, preview=preview,
            evidence=self.make_evidence(
                list_key=self.summary['list_key'],
                scan_id=preview['scope']['scan_id']))
        self.assertTrue(replay['replayed'])
        open_summary = self.records.summary()
        self.assertTrue(open_summary['restart_batch_open'])
        self.assertIn('RESTART_BATCH_OPEN', open_summary['dispatch_blockers'])
        self.assertFalse(open_summary['all_known_media_complete'])

        self.scan_posts(
            self.records,
            [dict(name='a', identity=post_a_identity, date='2026-11-01',
                  media=[photo, video]),
             dict(name='b', identity=post_b_identity, date='2026-11-02',
                  media=[unknown_photo])],
            recovery=True)
        attempts = {
            'photo': self.restart_download(
                self.records, keys['photo'], 'retry-a.png', png((0, 255, 0)),
                preview['restart_id']),
            'video': self.restart_download(
                self.records, keys['video'], 'retry-a.mp4', video_bytes(2),
                preview['restart_id']),
            'unknown': self.restart_download(
                self.records, keys['unknown'], 'retry-b.png',
                png((0, 255, 255)), preview['restart_id']),
        }
        with old_raw.open('r+b') as late_fd:
            candidates = {}
            for key in (keys['photo'], keys['video'], keys['unknown']):
                candidate = self.records.verify(
                    session_id=self.session,
                    attempt_id=attempts[
                        next(name for name, value in keys.items()
                             if value == key)]['attempt_id'],
                    verifier=self.pass_verifier,
                    stability_interval=0)
                candidates[key] = candidate
                self.assertEqual(candidate['status'], 'CANDIDATE_VERIFIED')
                before_summary = self.records.summary()
                self.assertTrue(before_summary['restart_batch_open'])
                self.assertFalse(before_summary['all_known_media_complete'])

            late_fd.seek(0)
            late_fd.write(b'late writer changed the old raw file')
            late_fd.flush()
            os.fsync(late_fd.fileno())

        old_candidate = candidates[keys['unknown']]
        candidate_path = Path(old_candidate['candidate']['path'])
        self.assertEqual(
            hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            old_candidate['candidate']['sha256'])

        resumed = self.records.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(resumed['action'], 'RESTART_ACTIVATED')
        self.assertEqual(
            resumed['activation']['restart_id'],
            preview['restart_id'])

        reopened = self.reopen(self.records)
        final = reopened.summary()
        self.assertFalse(final['restart_batch_open'])
        self.assertNotIn('RESTART_BATCH_OPEN', final['dispatch_blockers'])
        self.assertTrue(final['all_known_media_complete'])
        self.assertEqual(final['status_counts']['COMPLETED'], 3)
        self.assertEqual(final['local_counts'][LOCAL_VERIFIED], 3)
        active_rows = [
            row for row in final['media']
            if row.get('active_restart_id') == preview['restart_id']]
        self.assertEqual({row['media_key'] for row in active_rows},
                         set(keys.values()))
        self.assertEqual(len({row['active_candidate_ref']['sequence']
                              for row in active_rows}), 3)

        after_events = self.event_files(reopened)
        for name, raw in before_confirm.items():
            self.assertEqual(after_events[name], raw)
        self.assertEqual(
            hashlib.sha256(old_photo_path.read_bytes()).hexdigest(),
            old_photo_hash)
        self.assertEqual(
            hashlib.sha256(old_video_path.read_bytes()).hexdigest(),
            old_video_hash)
        self.assertEqual(
            hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            old_candidate['candidate']['sha256'])
        self.assertEqual(
            reopened.restart_preview()['status'], 'NO_RESTART_REQUIRED')
        replay_completions, _ = reopened._completion_projection()
        replay_attempts = reopened._attempt_projection()
        for old_attempt, key in ((photo_attempt, keys['photo']),
                                 (video_attempt, keys['video'])):
            reopen_verification = reopened._verification_for_attempt(
                old_attempt['attempt_id'])
            self.assertIsNotNone(reopen_verification)
            self.assertEqual(replay_completions[key]['data']['attempt_id'],
                             old_attempt['attempt_id'])
        self.assertEqual(
            reopened._attempt_result(unknown_attempt['attempt_id'],
                                     replay_attempts), 'UNKNOWN')

    def test_unconfirmed_forged_and_wrong_confirmations_append_nothing(self):
        photo = notes.media_identity(
            kind=PHOTO, visual_key='restart-c01-photo')
        post_identity = notes.post_identity(visual_key='restart-c01-post')
        observed = self.scan_posts(
            self.records,
            [dict(name='post', identity=post_identity, date='2026-11-06',
                  media=[photo])])
        post_key_value, _ = observed['post']
        key = self.media_key(post_key_value, photo)
        old = self.records.intent(
            session_id=self.session, media_key_value=key)
        (Path(old['destination']) / 'old.png').write_bytes(png((1, 2, 3)))
        self.records.outcome(
            session_id=self.session, attempt_id=old['attempt_id'],
            outcome='UNKNOWN',
            evidence=self.attempt_evidence(self.records, old))
        preview = self.records.restart_preview()
        self.assertEqual(preview['status'], 'RESTART_REQUIRED')
        before = self.event_files()

        with self.assertRaisesRegex(NotesError,
                                    'RESTART_CONFIRMATION_REQUIRED'):
            self.records.intent(
                session_id=self.session, media_key_value=key,
                restart_id=preview['restart_id'])
        self.assertEqual(self.event_files(), before)

        forged = copy.deepcopy(preview)
        forged['scope']['posts'][0]['media'][0]['identity'][
            'visual_key'] = 'forged-identity'
        with self.assertRaisesRegex(NotesError, 'RESTART_PREVIEW_CHANGED'):
            self.records.restart_confirm(
                session_id=self.session, preview=forged,
                evidence=self.make_evidence(
                    list_key=self.records.list_data['list_key'],
                    scan_id=preview['scope']['scan_id']))
        self.assertEqual(self.event_files(), before)

        with self.assertRaisesRegex(
                NotesError, 'FRESH_FOREGROUND_BINDING_REQUIRED'):
            self.records.restart_confirm(
                session_id='synthetic-unbound-session', preview=preview,
                evidence=self.make_evidence(
                    list_key=self.records.list_data['list_key'],
                    scan_id=preview['scope']['scan_id']))
        self.assertEqual(self.event_files(), before)

        other_list = notes.list_key(
            notes.list_identity(visual_key='synthetic-other-list'))
        with self.assertRaisesRegex(NotesError,
                                    'EVIDENCE_CONTEXT_MISMATCH'):
            self.records.restart_confirm(
                session_id=self.session, preview=preview,
                evidence=self.make_evidence(
                    list_key=other_list,
                    scan_id=preview['scope']['scan_id']))
        self.assertEqual(self.event_files(), before)
        self.assertFalse(any(
            event['kind'] in ('restart-confirm', 'restart-activation')
            for event in self.records.events))

    def test_confirm_rejects_scan_drift_and_cross_list_preview(self):
        context = self.one_media_restart_context(
            'restart-c01-drift', confirm=False)
        preview = context['preview']
        self.scan_posts(
            self.records,
            [dict(name='post', identity=context['post_identity'],
                  date='2026-11-03', media=[context['photo']])],
            recovery=True)
        before = self.event_files()
        with self.assertRaisesRegex(NotesError,
                                    'RESTART_EXPECTED_TIP_CHANGED'):
            self.confirm_restart(self.records, preview)
        self.assertEqual(self.event_files(), before)

        other_records, _other_summary = self.new_ledger(
            'synthetic-cross-list')
        other_before = self.event_files(other_records)
        with self.assertRaisesRegex(NotesError,
                                    'RESTART_EXPECTED_TIP_CHANGED'):
            other_records.restart_confirm(
                session_id=self.session, preview=preview,
                evidence=self.make_evidence(
                    list_key=other_records.list_data['list_key']))
        self.assertEqual(self.event_files(other_records), other_before)
        self.assertFalse(any(
            event['kind'] == 'restart-confirm'
            for event in other_records.events))

    def test_confirmed_pending_publish_is_suppressed_not_republished(self):
        photo = notes.media_identity(
            kind=PHOTO, visual_key='restart-c06-photo')
        post_identity = notes.post_identity(visual_key='restart-c06-post')
        observed = self.scan_posts(
            self.records,
            [dict(name='post', identity=post_identity, date='2026-11-05',
                  media=[photo])])
        post_key_value, _ = observed['post']
        key = self.media_key(post_key_value, photo)
        old = self.records.intent(
            session_id=self.session, media_key_value=key)
        raw = Path(old['destination']) / 'old.png'
        raw.write_bytes(png((5, 6, 7)))
        self.records.outcome(
            session_id=self.session, attempt_id=old['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=self.attempt_evidence(self.records, old))
        with mock.patch.object(
                NotesRecords, '_execute_publish',
                side_effect=OSError('synthetic publish crash')):
            with self.assertRaisesRegex(OSError, 'synthetic publish crash'):
                self.records.verify(
                    session_id=self.session,
                    attempt_id=old['attempt_id'],
                    verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(len(self.records._pending_publish_plans()), 1)
        self.assertEqual(len([
            event for event in self.records.events
            if event['kind'] == 'verification' and
            event['data']['attempt_id'] == old['attempt_id']]), 1)

        preview = self.records.restart_preview()
        self.assertEqual(preview['status'], 'RESTART_REQUIRED')
        scoped = next(
            row for post in preview['scope']['posts']
            for row in post['media'] if row['media_key'] == key)
        self.assertIsNotNone(scoped['prior_pending_plan'])
        self.confirm_restart(self.records, preview)
        self.scan_after_confirm(
            self.records,
            [dict(name='post', identity=post_identity, date='2026-11-05',
                  media=[photo])])
        before = self.event_files()
        self.assertEqual(self.records._pending_publish_plans(), [])
        resumed = self.records.resume()
        self.assertEqual(resumed['action'], 'NO_NAMING_TRANSACTION')
        self.assertEqual(self.event_files(), before)
        with self.assertRaisesRegex(NotesError,
                                    'RESTART_SUPERSEDED_ATTEMPT'):
            self.records.verify(
                session_id=self.session, attempt_id=old['attempt_id'],
                verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(self.event_files(), before)
        self.assertFalse(any(
            event['kind'] == 'completion'
            for event in self.records.events))

        attempt = self.restart_download(
            self.records, key, 'new.png', png((8, 9, 10)),
            preview['restart_id'])
        candidate = self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(candidate['status'], 'CANDIDATE_VERIFIED')
        activated = self.records.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')
        reopened = self.reopen(self.records)
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertFalse(summary['restart_batch_open'])
        after = self.event_files(reopened)
        for name, content in before.items():
            self.assertEqual(after[name], content)

    def test_candidate_drift_is_replaced_by_new_unique_copy(self):
        context = self.one_media_restart_context('restart-c08-drift')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((20, 30, 40)),
            context['preview']['restart_id'])
        first = self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        first_path = Path(first['candidate']['path'])
        first_path.write_bytes(first_path.read_bytes() + b'drift')
        self.assertEqual(
            self.records._candidate_file_availability(first['candidate']),
            notes.LOCAL_CHANGED)

        second = self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        self.assertFalse(second['replayed'])
        second_path = Path(second['candidate']['path'])
        self.assertNotEqual(second_path, first_path)
        self.assertTrue(first_path.exists())
        self.assertEqual(
            hashlib.sha256(second_path.read_bytes()).hexdigest(),
            second['candidate']['sha256'])
        self.assertEqual(len([
            event for event in self.records.events
            if event['kind'] == 'restart-copy-plan']), 2)
        self.assertEqual(len([
            event for event in self.records.events
            if event['kind'] == 'restart-candidate']), 2)

        activated = self.records.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')
        summary = self.records.summary()
        active = [
            row for row in summary['media']
            if row.get('active_restart_id') ==
            context['preview']['restart_id']]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]['active_candidate_ref']['sequence'],
                         second['candidate_ref']['sequence'])

    def test_complete_copy_without_manifest_is_not_adopted(self):
        context = self.one_media_restart_context('restart-c08-manifest')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((60, 70, 80)),
            context['preview']['restart_id'])
        original = media_verify._copy_exclusive

        def copy_then_fail(source, target, expected):
            original(source, target, expected)
            raise MediaVerificationError(
                'SYNTHETIC_FSYNC_FAILED', {'stage': 'fsync'})

        with mock.patch.object(
                media_verify, '_copy_exclusive', side_effect=copy_then_fail):
            with self.assertRaisesRegex(NotesError,
                                        'SYNTHETIC_FSYNC_FAILED'):
                self.records.verify(
                    session_id=self.session,
                    attempt_id=attempt['attempt_id'],
                    verifier=self.pass_verifier, stability_interval=0)
        plans = [
            event for event in self.records.events
            if event['kind'] == 'restart-copy-plan']
        self.assertEqual(len(plans), 1)
        self.assertFalse(any(
            event['kind'] == 'restart-candidate'
            for event in self.records.events))
        first_path = (Path(plans[0]['data']['target_directory']) /
                      plans[0]['data']['target_name'])
        self.assertTrue(first_path.exists())
        first_bytes = first_path.read_bytes()

        candidate = self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(len([
            event for event in self.records.events
            if event['kind'] == 'restart-copy-plan']), 2)
        second_path = Path(candidate['candidate']['path'])
        self.assertNotEqual(second_path, first_path)
        self.assertEqual(first_path.read_bytes(), first_bytes)
        self.assertEqual(
            hashlib.sha256(second_path.read_bytes()).hexdigest(),
            hashlib.sha256(png((60, 70, 80))).hexdigest())
        activated = self.records.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')
        self.assertEqual(
            activated['activation']['candidates'][0]['candidate']['path'],
            str(second_path))

    def test_source_change_before_isolation_is_rejected(self):
        context = self.one_media_restart_context('restart-c09-source')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((9, 9, 9)),
            context['preview']['restart_id'])
        original = media_verify._copy_exclusive

        def change_then_copy(source, target, expected):
            with open(source, 'ab') as stream:
                stream.write(b'late-write')
            return original(source, target, expected)

        with mock.patch.object(
                media_verify, '_copy_exclusive', side_effect=change_then_copy):
            with self.assertRaisesRegex(
                    NotesError, 'MEDIA_CHANGED_DURING_ISOLATION'):
                self.records.verify(
                    session_id=self.session,
                    attempt_id=attempt['attempt_id'],
                    verifier=self.pass_verifier, stability_interval=0)
        self.assertFalse(any(
            event['kind'] == 'restart-candidate'
            for event in self.records.events))
        self.assertFalse(any(
            event['kind'] == 'restart-activation'
            for event in self.records.events))

    def test_old_raw_path_recreated_after_candidate_does_not_change_candidate(self):
        context = self.one_media_restart_context('restart-c09-recreate')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((44, 55, 66)),
            context['preview']['restart_id'])
        candidate = self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        candidate_path = Path(candidate['candidate']['path'])
        candidate_hash = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        candidate_info = os.stat(str(candidate_path), follow_symlinks=False)

        context['old_raw'].unlink()
        context['old_raw'].write_bytes(png((99, 98, 97)))
        self.assertEqual(
            hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            candidate_hash)
        after = os.stat(str(candidate_path), follow_symlinks=False)
        self.assertEqual((after.st_dev, after.st_ino),
                         (candidate_info.st_dev, candidate_info.st_ino))
        activated = self.records.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')
        summary = self.records.summary()
        active = [
            row for row in summary['media']
            if row.get('active_restart_id') ==
            context['preview']['restart_id']]
        self.assertEqual(len(active), 1)
        self.assertEqual(
            hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            candidate_hash)

    def test_new_media_after_activation_publishes_into_active_version(self):
        context = self.one_media_restart_context('restart-prn03')
        attempt = self.restart_download(
            self.records, context['key'], 'new.png', png((11, 22, 33)),
            context['preview']['restart_id'])
        candidate = self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        activated = self.records.restart_resume(
            session_id=self.session, verifier=self.pass_verifier,
            stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')
        active_directory = Path(candidate['candidate']['path']).parent

        new_photo = notes.media_identity(
            kind=PHOTO, visual_key='restart-prn03-new-photo')
        self.scan_posts(
            self.records,
            [dict(name='post', identity=context['post_identity'],
                  date='2026-11-03',
                  media=[context['photo'], new_photo])],
            recovery=True)
        post_key_value = notes.post_key(
            self.records.list_data['list_key'], context['post_identity'])
        new_key = self.media_key(post_key_value, new_photo)
        _new_attempt, completion = self.download(
            self.records, new_key, 'next.png', png((77, 88, 99)))
        self.assertEqual(completion['data']['destination'],
                         str(active_directory))
        self.assertEqual(completion['data']['target_file']['name'],
                         'media_002.png')
        summary = self.records.summary()
        row = next(item for item in summary['media']
                   if item['media_key'] == new_key)
        self.assertEqual(row['status'], 'COMPLETED')
        self.assertEqual(row['local_files'], LOCAL_VERIFIED)

    def test_no_outcome_pre_restart_attempt_is_superseded_without_fake_stop(self):
        photo = notes.media_identity(
            kind=PHOTO, visual_key='restart-c02-photo')
        post_identity = notes.post_identity(visual_key='restart-c02-post')
        observed = self.scan_posts(
            self.records,
            [dict(name='post', identity=post_identity, date='2026-11-07',
                  media=[photo])])
        post_key_value, _ = observed['post']
        key = self.media_key(post_key_value, photo)
        old = self.records.intent(
            session_id=self.session, media_key_value=key)
        old_raw = Path(old['destination']) / 'old.png'
        old_raw.write_bytes(png((12, 13, 14)))
        self.assertFalse(any(
            event['kind'] == 'outcome' and
            event['data']['attempt_id'] == old['attempt_id']
            for event in self.records.events))
        preview = self.records.restart_preview()
        self.assertEqual(preview['status'], 'RESTART_REQUIRED')
        self.confirm_restart(self.records, preview)
        self.scan_after_confirm(
            self.records,
            [dict(name='post', identity=post_identity, date='2026-11-07',
                  media=[photo])])
        attempt = self.restart_download(
            self.records, key, 'new.png', png((15, 16, 17)),
            preview['restart_id'])
        intent_event = next(
            event for event in self.records.events
            if event['kind'] == 'intent' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        self.assertEqual(intent_event['data']['prior_attempt']['sequence'],
                         next(event['sequence'] for event in self.records.events
                              if event['kind'] == 'intent' and
                              event['data']['attempt_id'] ==
                              old['attempt_id']))
        self.assertEqual(old_raw.read_bytes(), png((12, 13, 14)))
        self.assertFalse(any(
            event['kind'] == 'outcome' and
            event['data']['attempt_id'] == old['attempt_id']
            for event in self.records.events))

    def image_decoder(self):
        root = tempfile.TemporaryDirectory(
            prefix='decoder-', dir=str(self.base))
        self.addCleanup(root.cleanup)
        decoder = Path(root.name) / 'image_decode'
        source = ROOT / 'src' / 'line_backup_batch' / 'image_decode.swift'
        try:
            result = subprocess.run(
                ['xcrun', '--sdk', 'macosx', 'swiftc', str(source),
                 '-o', str(decoder)],
                capture_output=True, text=True)
        except OSError as exc:
            self.skipTest('Swift compiler unavailable: {}'.format(exc))
        if result.returncode:
            self.skipTest('Swift decoder cannot be built: {}'.format(
                result.stderr[:500]))
        return decoder

    def pinned_video_payload(self):
        if not (media_verify.FFMPEG_PATH.is_file() and
                media_verify.FFPROBE_PATH.is_file()):
            self.skipTest('pinned Homebrew ffmpeg/ffprobe pair unavailable')
        try:
            media_verify.inspect_video_tools()
        except MediaVerificationError as exc:
            self.skipTest('pinned video tools unavailable: {}'.format(exc))
        target = self.base / 'synthetic.mp4'
        result = subprocess.run(
            [str(media_verify.FFMPEG_PATH), '-nostdin', '-hide_banner',
             '-loglevel', 'error', '-f', 'lavfi',
             '-i', 'color=c=red:s=64x64:d=1:r=10',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
             '-movflags', '+faststart', str(target)],
            capture_output=True)
        if result.returncode:
            self.skipTest('ffmpeg fixture generation failed: {}'.format(
                result.stderr.decode('utf-8', 'replace')[:500]))
        return target.read_bytes()

    def test_real_synthetic_photo_candidate_decodes_and_activates(self):
        context = self.one_media_restart_context('restart-real-photo')
        decoder = self.image_decoder()
        payload = png((30, 60, 90))
        attempt = self.restart_download(
            self.records, context['key'], 'real.png', payload,
            context['preview']['restart_id'])
        candidate = self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            decoder=str(decoder),
            decoder_sha256=hashlib.sha256(decoder.read_bytes()).hexdigest(),
            stability_interval=0)
        self.assertEqual(candidate['verification']['verifier'], 'IMAGEIO')
        self.assertEqual(candidate['verification']['returncode'], 0)
        self.assertEqual(candidate['candidate']['sha256'],
                         hashlib.sha256(payload).hexdigest())
        activated = self.records.restart_resume(
            session_id=self.session, stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')
        reopened = self.reopen(self.records)
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertFalse(summary['restart_batch_open'])

    def test_real_synthetic_video_candidate_decodes_and_activates(self):
        context = self.one_media_restart_context(
            'restart-real-video', kind=VIDEO)
        payload = self.pinned_video_payload()
        attempt = self.restart_download(
            self.records, context['key'], 'real.mp4', payload,
            context['preview']['restart_id'])
        candidate = self.records.verify(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            stability_interval=0)
        self.assertEqual(candidate['verification']['verifier'],
                         'FFMPEG_NULL_DECODE')
        self.assertGreaterEqual(
            candidate['verification']['all_audio_video_streams_decoded'], 1)
        self.assertTrue(all(
            row['coverage']['duration_covered']
            for row in candidate['verification']['decoded_streams']))
        activated = self.records.restart_resume(
            session_id=self.session, stability_interval=0)
        self.assertEqual(activated['action'], 'RESTART_ACTIVATED')
        reopened = self.reopen(self.records)
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertFalse(summary['restart_batch_open'])



if __name__ == '__main__':
    unittest.main()
