"""Synthetic offline Notes ledger and CLI lifecycle tests."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest import mock
import zlib

from line_backup_batch import notes
from line_backup_batch.daily import DailyError
from line_backup_batch.notes import (
    LOCAL_CHANGED,
    LOCAL_MISSING,
    PHOTO,
    VIDEO,
    NotesCollection,
    NotesError,
    NotesRecords,
)


ROOT = Path(__file__).resolve().parents[1]
PYTHON = '/usr/bin/python3'


def png(color=(255, 0, 0)):
    def chunk(name, data):
        return (struct.pack('>I', len(data)) + name + data +
                struct.pack('>I', zlib.crc32(name + data) & 0xffffffff))

    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * 2) * 2)) +
            chunk(b'IEND', b''))


def video_bytes(marker=0):
    return (b'ftypisom' + b'\x00' * 8 + bytes([marker]) * 64)


class NotesRecordsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix='notes-records-', dir=ROOT)
        self.base = Path(self.temporary.name).resolve()
        self.evidence = self.base / 'synthetic-evidence.txt'
        self.evidence.write_bytes(b'synthetic notes evidence')
        self.photo_root = self.base / 'photos'
        self.collection_path = self.base / 'records'
        self.collection = NotesCollection(str(self.collection_path))
        self.session = 'synthetic-session-1'
        self.active_patch = mock.patch.object(
            notes, '_write_active_hint', return_value=None)
        self.active_patch.start()
        self.records, self.summary = self.new_ledger(
            'synthetic-list-1', recovery_authorized=True)

    def tearDown(self):
        self.active_patch.stop()
        self.temporary.cleanup()

    def new_ledger(self, visual_key, *, recovery_authorized=False,
                   display_name='Synthetic Notes'):
        summary = self.collection.create(
            photo_root=str(self.photo_root),
            display_name=display_name,
            identity=notes.list_identity(visual_key=visual_key),
            binding_evidence=str(self.evidence),
            history_scope_evidence=str(self.evidence),
            recovery_authorized=recovery_authorized)
        records = NotesRecords(
            summary['records_root'], _allow_injected_verification=True)
        records.bind(session_id=self.session,
                     observation=str(self.evidence),
                     handoff=str(self.evidence))
        return records, summary

    def reopen(self, records):
        return NotesRecords(str(records.records),
                            _allow_injected_verification=True)

    def bind(self, records, session):
        return records.bind(session_id=session,
                            observation=str(self.evidence),
                            handoff=str(self.evidence))

    def observe_post(self, records, list_key, post_visual, media_identities,
                     *, session=None, no_media=False, media_count=None,
                     date='2026-10-31'):
        session = session or self.session
        post = notes.post_identity(visual_key=post_visual)
        post_key_value = notes.post_key(list_key, post)
        scan = records.scan(session_id=session, action='START',
                            evidence=str(self.evidence))
        records.page(
            session_id=session, scan_id=scan['scan_id'], page_index=0,
            posts=[dict(identity=post, date_summary=date)],
            top_reached=True, bottom_reached=True, overlap_keys=[],
            evidence=str(self.evidence))
        records.scan(session_id=session, action='FINISH',
                     scan_id=scan['scan_id'], evidence=str(self.evidence))
        count = 0 if no_media else (
            len(media_identities) if media_count is None else media_count)
        records.record_post(
            session_id=session, post_key_value=post_key_value,
            date_summary=date, media_count=count, text_sha256=None,
            evidence=str(self.evidence), no_media=no_media)
        if media_identities:
            records.record_media(
                session_id=session, post_key_value=post_key_value,
                items=[{'identity': identity} for identity in media_identities],
                missing=[], evidence=str(self.evidence))
        return post, post_key_value, scan

    def media_key(self, records, post_key_value, identity):
        return notes.media_key(records.list_data['list_key'],
                               post_key_value, identity)

    def download(self, records, media_key_value, filename, payload,
                 *, session=None, outcome='DOWNLOAD_FINISHED',
                 reconcile=None, verifier=None):
        session = session or self.session
        attempt = records.intent(session_id=session,
                                 media_key_value=media_key_value)
        staging = Path(attempt['destination'])
        (staging / filename).write_bytes(payload)
        records.outcome(session_id=session, attempt_id=attempt['attempt_id'],
                        outcome=outcome, evidence=str(self.evidence))
        if outcome == 'UNKNOWN' and reconcile is not None:
            records.reconcile(session_id=session,
                              attempt_id=attempt['attempt_id'],
                              result=reconcile, evidence=str(self.evidence))
        completion = records.verify(
            session_id=session, attempt_id=attempt['attempt_id'],
            verifier=verifier or self.pass_verifier,
            stability_interval=0)
        return attempt, completion

    @staticmethod
    def pass_verifier(path, row, identity):
        del path, identity
        return dict(verdict='PASS', sha256=row['sha256'])

    def event_bytes(self, records=None):
        records = records or self.records
        return {path.name: path.read_bytes()
                for path in (records.records / 'events').iterdir()}

    def run_cli(self, *args):
        env = dict(os.environ)
        env['PYTHONPATH'] = str(ROOT / 'src')
        return subprocess.run(
            [PYTHON, '-B', '-m', 'line_backup_batch.notes', *map(str, args)],
            cwd=str(ROOT), env=env, capture_output=True, text=True)

    def test_two_photos_one_video_lifecycle_and_new_session_skip(self):
        first_photo = notes.media_identity(kind=PHOTO, visual_key='photo-1')
        second_photo = notes.media_identity(kind=PHOTO, visual_key='photo-2')
        video = notes.media_identity(kind=VIDEO, visual_key='video-1')
        post, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-1',
            [first_photo, second_photo, video])
        keys = [self.media_key(self.records, post_key_value, identity)
                for identity in (first_photo, second_photo, video)]

        seen = []

        def verifier(path, row, identity):
            seen.append(identity['kind'])
            return dict(verdict='PASS', sha256=row['sha256'])

        first_attempt, first_completion = self.download(
            self.records, keys[0], 'one.png', png(), outcome='UNKNOWN',
            reconcile='DOWNLOAD_FINISHED', verifier=verifier)
        second_attempt, second_completion = self.download(
            self.records, keys[1], 'two.png', png((0, 255, 0)),
            verifier=verifier)
        video_attempt, video_completion = self.download(
            self.records, keys[2], 'three.mp4', video_bytes(3),
            verifier=verifier)

        self.assertEqual(seen, [PHOTO, PHOTO, VIDEO])
        self.assertEqual(first_attempt['status'], 'UNKNOWN')
        self.assertEqual(first_attempt['save_all_limit'], 1)
        self.assertEqual(first_attempt['save_all_count'], 0)
        self.assertEqual(first_completion['data']['media_key'], keys[0])
        self.assertEqual(second_completion['data']['media_key'], keys[1])
        self.assertEqual(video_completion['data']['media_key'], keys[2])

        post_directory = Path(video_completion['data']['destination'])
        self.assertEqual(
            sorted(path.name for path in post_directory.iterdir()),
            ['media_001.png', 'media_002.png', 'media_003.mp4'])
        reopened = self.reopen(self.records)
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 3)
        self.assertEqual(summary['local_counts']['VERIFIED_PRESENT'], 3)
        self.assertTrue(summary['all_known_media_complete'])
        self.assertEqual(
            [row['status'] for row in summary['media']],
            ['COMPLETED', 'COMPLETED', 'COMPLETED'])

        self.bind(reopened, 'synthetic-session-2')
        self.observe_post(
            reopened, self.summary['list_key'], 'post-1',
            [first_photo, second_photo, video], session='synthetic-session-2')
        with self.assertRaisesRegex(
                NotesError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            reopened.intent(
                session_id='synthetic-session-2', media_key_value=keys[0])
        self.assertEqual(summary['status_counts']['COMPLETED'], 3)

    def test_replay_second_outcome_and_second_save_all_are_refused(self):
        identity = notes.media_identity(kind=PHOTO, visual_key='single-photo')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-single', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        attempt = self.records.intent(
            session_id=self.session, media_key_value=key)
        before = self.event_bytes()
        with self.assertRaisesRegex(NotesError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.records.intent(session_id=self.session, media_key_value=key)
        self.assertEqual(self.event_bytes(), before)

        staging = Path(attempt['destination'])
        (staging / 'photo.png').write_bytes(png())
        self.records.outcome(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED', evidence=str(self.evidence))
        before = self.event_bytes()
        with self.assertRaisesRegex(NotesError, 'OUTCOME_ALREADY_RECORDED'):
            self.records.outcome(
                session_id=self.session, attempt_id=attempt['attempt_id'],
                outcome='NOT_SENT', evidence=str(self.evidence))
        with self.assertRaisesRegex(NotesError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.records.intent(session_id=self.session, media_key_value=key)
        self.assertEqual(self.event_bytes(), before)
        self.assertTrue(staging.is_dir())
        self.assertEqual(len(list(staging.iterdir())), 1)

    def test_unknown_is_blocked_until_reconcile(self):
        identity = notes.media_identity(kind=PHOTO, visual_key='unknown-photo')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-unknown', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        attempt = self.records.intent(
            session_id=self.session, media_key_value=key)
        self.records.outcome(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            outcome='UNKNOWN', evidence=str(self.evidence))
        before = self.event_bytes()
        with self.assertRaisesRegex(
                NotesError, 'KNOWN_DOWNLOAD_FINISH_REQUIRED'):
            self.records.verify(
                session_id=self.session, attempt_id=attempt['attempt_id'],
                verifier=self.pass_verifier, stability_interval=0)
        with self.assertRaisesRegex(NotesError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.records.intent(session_id=self.session, media_key_value=key)
        self.assertEqual(self.event_bytes(), before)

        self.records.reconcile(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            result='UNKNOWN', evidence=str(self.evidence))
        with self.assertRaisesRegex(
                NotesError, 'KNOWN_DOWNLOAD_FINISH_REQUIRED'):
            self.records.verify(
                session_id=self.session, attempt_id=attempt['attempt_id'],
                verifier=self.pass_verifier, stability_interval=0)
        with self.assertRaisesRegex(NotesError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.records.intent(session_id=self.session, media_key_value=key)

    def test_stopped_and_not_sent_recovery_use_new_empty_staging(self):
        identity = notes.media_identity(kind=PHOTO, visual_key='recover-photo')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-recovery', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        first = self.records.intent(
            session_id=self.session, media_key_value=key)
        self.records.outcome(
            session_id=self.session, attempt_id=first['attempt_id'],
            outcome='STOPPED', evidence=str(self.evidence))
        with self.assertRaisesRegex(NotesError, 'NOTES_RECOVERY_EVIDENCE_REQUIRED'):
            self.records.intent(session_id=self.session, media_key_value=key)
        second = self.records.intent(
            session_id=self.session, media_key_value=key,
            recovery_evidence=str(self.evidence))
        self.assertNotEqual(first['destination'], second['destination'])
        self.assertEqual(second['recovery_of'], first['attempt_id'])
        self.assertTrue(Path(first['destination']).is_dir())
        self.assertTrue(Path(second['destination']).is_dir())
        self.records.outcome(
            session_id=self.session, attempt_id=second['attempt_id'],
            outcome='NOT_SENT', evidence=str(self.evidence))
        third = self.records.intent(
            session_id=self.session, media_key_value=key,
            recovery_evidence=str(self.evidence))
        self.assertEqual(third['recovery_of'], second['attempt_id'])
        self.assertNotEqual(third['destination'], first['destination'])
        self.assertNotEqual(third['destination'], second['destination'])
        self.assertEqual(len(list(Path(first['destination']).iterdir())), 0)

    def test_naming_interruption_resumes_same_transaction(self):
        identity = notes.media_identity(kind=PHOTO, visual_key='naming-photo')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-naming', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        attempt = self.records.intent(
            session_id=self.session, media_key_value=key)
        staging = Path(attempt['destination'])
        (staging / 'naming.png').write_bytes(png())
        self.records.outcome(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED', evidence=str(self.evidence))
        with mock.patch.object(
                NotesRecords, '_execute_publish',
                side_effect=OSError('synthetic naming interruption')):
            with self.assertRaisesRegex(OSError, 'synthetic naming interruption'):
                self.records.verify(
                    session_id=self.session, attempt_id=attempt['attempt_id'],
                    verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(len(self.records._pending_publish_plans()), 1)
        reopened = self.reopen(self.records)
        resumed = reopened.resume()
        self.assertEqual(resumed['action'], 'PUBLISH_RESUMED')
        completion = resumed['completion']
        target = Path(completion['destination']) / completion['target_file']['name']
        self.assertTrue(target.is_file())
        self.assertFalse(staging.exists())
        self.assertEqual(reopened.summary()['status_counts']['COMPLETED'], 1)

    def test_cross_list_isolation_and_index_failures_fail_closed(self):
        second_records, second_summary = self.new_ledger(
            'synthetic-list-2', recovery_authorized=True,
            display_name='Second Notes')
        post_identity = notes.post_identity(visual_key='same-post')
        media_identity = notes.media_identity(kind=PHOTO, visual_key='same-media')
        first_post = notes.post_key(self.summary['list_key'], post_identity)
        second_post = notes.post_key(second_summary['list_key'], post_identity)
        self.assertNotEqual(first_post, second_post)
        self.assertNotEqual(
            notes.media_key(self.summary['list_key'], first_post, media_identity),
            notes.media_key(second_summary['list_key'], second_post,
                            media_identity))
        self.observe_post(self.records, self.summary['list_key'], 'same-post',
                          [media_identity])
        self.observe_post(second_records, second_summary['list_key'],
                          'same-post', [media_identity])
        foreign_key = notes.media_key(
            self.summary['list_key'], first_post, media_identity)
        with self.assertRaisesRegex(NotesError, 'MEDIA_NOT_OBSERVED'):
            second_records.intent(session_id=self.session,
                                  media_key_value=foreign_key)

        index_path = self.collection_path / 'index.json'
        original_index = index_path.read_bytes()
        index_path.write_bytes(b'{not-json')
        with self.assertRaisesRegex((NotesError, DailyError), 'INVALID_NOTES_INDEX'):
            self.collection.lists()
        index_path.write_bytes(original_index)

        second_root = Path(second_summary['records_root'])
        shutil.rmtree(second_root)
        with self.assertRaisesRegex(NotesError, 'REGISTERED_NOTES_RECORDS_MISSING'):
            self.collection.lists()

    def completed_ledger(self, label):
        records, summary = self.new_ledger(
            'synthetic-' + label, recovery_authorized=True,
            display_name='Ledger ' + label)
        identity = notes.media_identity(kind=PHOTO,
                                        visual_key='media-' + label)
        _, post_key_value, _ = self.observe_post(
            records, summary['list_key'], 'post-' + label, [identity])
        key = self.media_key(records, post_key_value, identity)
        _, completion = self.download(
            records, key, label + '.png', png())
        return records, summary, post_key_value, identity, completion

    def assert_completed_local_state(self, mutation, expected_local):
        records, summary, post_key_value, identity, completion = (
            self.completed_ledger(mutation))
        post_directory = Path(completion['data']['destination'])
        target = post_directory / completion['data']['target_file']['name']
        if mutation == 'missing':
            target.unlink()
        elif mutation == 'extra':
            (post_directory / 'unexpected.txt').write_bytes(b'extra')
        elif mutation == 'hash':
            target.write_bytes(png((0, 0, 255)))
        elif mutation == 'symlink':
            real = self.base / ('real-' + mutation + '.png')
            real.write_bytes(png((0, 255, 0)))
            target.unlink()
            target.symlink_to(real)
        reopened = self.reopen(records)
        result = reopened.summary()
        row = next(item for item in result['media']
                   if item['media_key'] == self.media_key(
                       reopened, post_key_value, identity))
        self.assertEqual(row['status'], 'COMPLETED')
        self.assertEqual(row['local_files'], expected_local)
        self.bind(reopened, 'new-session-' + mutation)
        self.observe_post(
            reopened, summary['list_key'], 'post-' + mutation, [identity],
            session='new-session-' + mutation)
        with self.assertRaises(NotesError) as raised:
            reopened.intent(session_id='new-session-' + mutation,
                            media_key_value=self.media_key(
                                reopened, post_key_value, identity))
        self.assertIn(raised.exception.args[0],
                      {'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD',
                       'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'})

    def test_partial_file_loss_extra_file_hash_drift_and_symlink_are_local_changed(self):
        for mutation in ('missing', 'extra', 'hash', 'symlink'):
            with self.subTest(mutation=mutation):
                self.assert_completed_local_state(mutation, LOCAL_CHANGED)

    def test_entire_completed_post_directory_missing_is_local_missing(self):
        records, summary, post_key_value, identity, completion = (
            self.completed_ledger('missing-dir'))
        post_directory = Path(completion['data']['destination'])
        shutil.rmtree(post_directory)
        reopened = self.reopen(records)
        result = reopened.summary()
        key = self.media_key(reopened, post_key_value, identity)
        row = next(item for item in result['media'] if item['media_key'] == key)
        self.assertEqual((row['status'], row['local_files']),
                         ('COMPLETED', LOCAL_MISSING))
        self.bind(reopened, 'new-session-missing-dir')
        self.observe_post(reopened, summary['list_key'], 'post-missing-dir',
                          [identity], session='new-session-missing-dir')
        with self.assertRaisesRegex(
                NotesError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            reopened.intent(session_id='new-session-missing-dir',
                            media_key_value=key)
        self.assertEqual(reopened.summary()['media'][0]['local_files'],
                         LOCAL_MISSING)

    def test_source_reorder_keeps_old_names_and_new_media_gets_next_number(self):
        first = notes.media_identity(kind=PHOTO, visual_key='reorder-photo-1')
        second = notes.media_identity(kind=VIDEO, visual_key='reorder-video-2')
        third = notes.media_identity(kind=PHOTO, visual_key='reorder-photo-3')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-reorder',
            [first, second])
        first_key = self.media_key(self.records, post_key_value, first)
        second_key = self.media_key(self.records, post_key_value, second)
        _, first_completion = self.download(
            self.records, first_key, 'first.png', png())
        _, second_completion = self.download(
            self.records, second_key, 'second.mp4', video_bytes(2))
        first_name = first_completion['data']['target_file']['name']
        second_name = second_completion['data']['target_file']['name']

        self.observe_post(
            self.records, self.summary['list_key'], 'post-reorder',
            [second, first, third])
        third_key = self.media_key(self.records, post_key_value, third)
        _, third_completion = self.download(
            self.records, third_key, 'third.png', png((0, 0, 255)))
        summary = self.reopen(self.records).summary()
        by_key = {row['media_key']: row for row in summary['media']}
        self.assertEqual(by_key[second_key]['source_order'], 0)
        self.assertEqual(by_key[first_key]['source_order'], 1)
        self.assertEqual(by_key[third_key]['source_order'], 2)
        self.assertEqual(
            first_completion['data']['target_file']['name'], first_name)
        self.assertEqual(
            second_completion['data']['target_file']['name'], second_name)
        self.assertEqual(third_completion['data']['target_file']['name'],
                         'media_003.png')

    def test_no_media_post_is_indexed_without_media_attempt(self):
        post, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-text', [],
            no_media=True)
        self.assertEqual(notes.post_key(self.summary['list_key'], post),
                         post_key_value)
        summary = self.summary_of(self.records)
        row = next(item for item in summary['posts']
                   if item['post_key'] == post_key_value)
        self.assertEqual(row['state'], 'NO_MEDIA')
        self.assertEqual(row['media'], [])
        self.assertEqual(summary['status_counts']['PENDING'], 0)
        self.assertTrue(summary['all_known_media_complete'])
        self.assertEqual(summary['dispatch_blockers'], [])

    def summary_of(self, records):
        return self.reopen(records).summary()

    def test_completion_manifest_readback_and_immutability(self):
        identity = notes.media_identity(kind=PHOTO,
                                        visual_key='immutable-photo')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-immutable', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        attempt, completion = self.download(
            self.records, key, 'immutable.png', png())
        reopened = self.reopen(self.records)
        reopened.summary()
        completion_event = next(
            event for event in reopened.events
            if event['kind'] == 'completion' and
            event['data']['media_key'] == key)
        verification_event = next(
            event for event in reopened.events
            if event['kind'] == 'verification' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        source = completion_event['data']['source_manifest']
        self.assertEqual(source, verification_event['data']['manifest'][0])
        target = (Path(completion_event['data']['destination']) /
                  completion_event['data']['target_file']['name'])
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),
                         source['sha256'])
        before = self.event_bytes(reopened)
        with self.assertRaisesRegex(NotesError, 'COMPLETION_IMMUTABLE'):
            reopened.verify(session_id=self.session,
                            attempt_id=attempt['attempt_id'],
                            verifier=self.pass_verifier,
                            stability_interval=0)
        with self.assertRaisesRegex(NotesError, 'OUTCOME_ALREADY_RECORDED'):
            reopened.outcome(session_id=self.session,
                             attempt_id=attempt['attempt_id'],
                             outcome='NOT_SENT', evidence=str(self.evidence))
        self.assertEqual(self.event_bytes(reopened), before)
        self.assertEqual(completion['data']['verification']['verifier'],
                         'INJECTED')

    def test_default_verify_rejects_injected_verifier(self):
        records, summary = self.new_ledger(
            'injected-default-verify', recovery_authorized=True)
        identity = notes.media_identity(
            kind=PHOTO, visual_key='injected-default-verify-media')
        _post, post_key_value, _scan = self.observe_post(
            records, summary['list_key'], 'injected-default-verify-post',
            [identity])
        key = self.media_key(records, post_key_value, identity)
        attempt = records.intent(session_id=self.session, media_key_value=key)
        staging = Path(attempt['destination'])
        (staging / 'synthetic.png').write_bytes(png())
        records.outcome(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED', evidence=str(self.evidence))
        before = self.event_bytes(records)

        production = NotesRecords(str(records.records))
        with self.assertRaisesRegex(
                NotesError, 'INJECTED_VERIFICATION_NOT_ALLOWED'):
            production.verify(
                session_id=self.session, attempt_id=attempt['attempt_id'],
                verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(self.event_bytes(records), before)

    def test_default_loader_rejects_injected_verification_event(self):
        records, _summary, _post_key_value, _identity, completion = (
            self.completed_ledger('injected-loader'))
        self.assertEqual(
            completion['data']['verification']['verifier'], 'INJECTED')

        allowed = self.reopen(records)
        self.assertEqual(allowed.summary()['status_counts']['COMPLETED'], 1)
        with self.assertRaisesRegex(
                NotesError, 'INJECTED_VERIFICATION_NOT_ALLOWED'):
            NotesRecords(str(records.records)).summary()
        refused = self.run_cli(
            'summary', '--records-root', records.records)
        self.assertEqual(refused.returncode, 4)
        payload = json.loads(refused.stdout)
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertEqual(payload['reason'], 'INJECTED_VERIFICATION_NOT_ALLOWED')
        self.assertFalse(payload['dispatch_authorized'])

    def test_cli_help_success_and_refusal_exit_codes(self):
        help_result = self.run_cli('--help')
        self.assertEqual(help_result.returncode, 0)
        self.assertIn('usage:', help_result.stdout)
        self.assertIn('intent', help_result.stdout)
        self.assertIn('exit 70', help_result.stdout)
        self.assertIn('INTERNAL_ERROR', help_result.stdout)

        identity = notes.media_identity(kind=PHOTO, visual_key='cli-photo')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'], 'post-cli', [identity])
        before = self.event_bytes()
        syntax = self.run_cli(
            'post', '--records-root', self.records.records,
            '--session-id', self.session, '--post-key', post_key_value,
            '--date-summary', 'synthetic', '--evidence', self.evidence)
        self.assertEqual(syntax.returncode, 2)
        self.assertEqual(self.event_bytes(), before)

        refused = self.run_cli(
            'intent', '--records-root', self.records.records,
            '--session-id', self.session, '--media-key', '0' * 64)
        self.assertEqual(refused.returncode, 4)
        payload = json.loads(refused.stdout)
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertEqual(payload['reason'], 'MEDIA_NOT_OBSERVED')
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(self.event_bytes(), before)

        listed = self.run_cli('lists', '--collection', self.collection_path)
        self.assertEqual(listed.returncode, 0)
        listed_payload = json.loads(listed.stdout)
        self.assertFalse(listed_payload['dispatch_authorized'])
        self.assertEqual(len(listed_payload['lists']), 1)

    def test_cli_unexpected_exception_is_internal_error(self):
        for raised in (KeyError('synthetic'), TypeError('synthetic'),
                       ValueError('synthetic'), OverflowError('synthetic')):
            with self.subTest(error_type=type(raised).__name__):
                output = io.StringIO()
                with mock.patch.object(
                        notes.NotesCollection, 'lists', side_effect=raised):
                    with mock.patch('sys.stdout', new=output):
                        exit_code = notes.main([
                            'lists', '--collection', str(self.collection_path)])
                self.assertEqual(exit_code, 70)
                payload = json.loads(output.getvalue())
                self.assertEqual(payload['status'], 'INTERNAL_ERROR')
                self.assertEqual(payload['reason'], 'UNEXPECTED_EXCEPTION')
                self.assertFalse(payload['dispatch_authorized'])
                self.assertNotIn('Traceback', output.getvalue())

    def test_cli_known_errors_remain_refused(self):
        for raised in (OSError('synthetic'), subprocess.SubprocessError('synthetic')):
            with self.subTest(error_type=type(raised).__name__):
                output = io.StringIO()
                with mock.patch.object(
                        notes.NotesCollection, 'lists', side_effect=raised):
                    with mock.patch('sys.stdout', new=output):
                        exit_code = notes.main([
                            'lists', '--collection', str(self.collection_path)])
                self.assertEqual(exit_code, 4)
                payload = json.loads(output.getvalue())
                self.assertEqual(payload['status'], 'REFUSED')
                self.assertFalse(payload['dispatch_authorized'])
                self.assertNotIn('Traceback', output.getvalue())


if __name__ == '__main__':
    unittest.main()
