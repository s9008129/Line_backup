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
import uuid
import zlib

from line_backup_batch import notes, notes_evidence
from line_backup_batch.daily import DailyError
from line_backup_batch.notes import (
    LOCAL_CHANGED,
    LOCAL_MISSING,
    LOCAL_VERIFIED,
    PHOTO,
    VIDEO,
    NotesCollection,
    NotesError,
    NotesRecords,
)


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TASKS = ROOT / '.local' / 'line-backup' / 'tasks'
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
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='notes-records-', dir=PRIVATE_TASKS)
        self.base = Path(self.temporary.name).resolve()
        self.evidence = self.base / 'synthetic-evidence.txt'
        self.evidence.write_bytes(b'synthetic notes evidence')
        self.screenshot = self.base / 'synthetic-screenshot.txt'
        self.screenshot.write_bytes(b'synthetic screenshot evidence')
        self.evidence_packs = self.base / 'evidence-packs'
        self.evidence_packs.mkdir()
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

    def make_evidence(self, **context):
        output = self.evidence_packs / uuid.uuid4().hex
        return notes_evidence.create_bundle(
            statement=str(self.evidence),
            assets=[('screenshot', str(self.screenshot))],
            context=context, output_dir=str(output))['bundle_path']

    def new_ledger(self, visual_key, *, recovery_authorized=False,
                   display_name='Synthetic Notes', context_id=None):
        identity = notes.list_identity(visual_key=visual_key,
                                       context_id=context_id)
        list_key_value = notes.list_key(identity)
        evidence = self.make_evidence(list_key=list_key_value)
        summary = self.collection.create(
            photo_root=str(self.photo_root),
            display_name=display_name,
            identity=identity,
            binding_evidence=evidence,
            history_scope_evidence=evidence,
            recovery_authorized=recovery_authorized)
        records = NotesRecords(
            summary['records_root'], _allow_injected_verification=True)
        records.bind(session_id=self.session,
                     observation=self.make_evidence(
                         list_key=summary['list_key']),
                     handoff=self.make_evidence(
                         list_key=summary['list_key']))
        return records, summary

    def reopen(self, records):
        return NotesRecords(str(records.records),
                            _allow_injected_verification=True)

    def bind(self, records, session):
        return records.bind(session_id=session,
                            observation=self.make_evidence(
                                list_key=records.list_data['list_key']),
                            handoff=self.make_evidence(
                                list_key=records.list_data['list_key']))

    def observe_post(self, records, list_key, post_visual, media_identities,
                     *, session=None, no_media=False, media_count=None,
                     date='2026-10-31'):
        session = session or self.session
        post = notes.post_identity(visual_key=post_visual)
        post_key_value = notes.post_key(list_key, post)
        scan = records.scan(session_id=session, action='START',
                            evidence=self.make_evidence(list_key=list_key))
        scan_evidence = self.make_evidence(
            list_key=list_key, scan_id=scan['scan_id'])
        records.page(
            session_id=session, scan_id=scan['scan_id'], page_index=0,
            posts=[dict(identity=post, date_summary=date)],
            top_reached=True, bottom_reached=True, overlap_keys=[],
            evidence=scan_evidence)
        records.scan(session_id=session, action='FINISH',
                     scan_id=scan['scan_id'], evidence=scan_evidence)
        count = 0 if no_media else (
            len(media_identities) if media_count is None else media_count)
        post_evidence = self.make_evidence(
            list_key=list_key, post_key=post_key_value,
            scan_id=scan['scan_id'])
        records.record_post(
            session_id=session, post_key_value=post_key_value,
            date_summary=date, media_count=count, text_sha256=None,
            evidence=post_evidence, no_media=no_media)
        if media_identities:
            records.record_media(
                session_id=session, post_key_value=post_key_value,
                items=[{'identity': identity} for identity in media_identities],
                missing=[], evidence=post_evidence)
        return post, post_key_value, scan

    def media_key(self, records, post_key_value, identity):
        return notes.media_key(records.list_data['list_key'],
                               post_key_value, identity)

    def attempt_evidence(self, records, attempt):
        return self.make_evidence(
            list_key=records.list_data['list_key'],
            post_key=attempt['post_key'], media_key=attempt['media_key'],
            attempt_id=attempt['attempt_id'], scan_id=attempt['scan_id'])

    def download(self, records, media_key_value, filename, payload,
                 *, session=None, outcome='DOWNLOAD_FINISHED',
                 reconcile=None, verifier=None):
        session = session or self.session
        attempt = records.intent(session_id=session,
                                 media_key_value=media_key_value)
        staging = Path(attempt['destination'])
        (staging / filename).write_bytes(payload)
        evidence = self.attempt_evidence(records, attempt)
        records.outcome(session_id=session, attempt_id=attempt['attempt_id'],
                        outcome=outcome, evidence=evidence)
        if outcome == 'UNKNOWN' and reconcile is not None:
            records.reconcile(session_id=session,
                              attempt_id=attempt['attempt_id'],
                              result=reconcile, evidence=evidence)
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

    def test_bind_omitted_context_inherits_saved_context(self):
        records, _summary = self.new_ledger(
            'context-bind', context_id='saved-context')
        before = self.event_bytes(records)
        with self.assertRaisesRegex(NotesError, 'WRONG_NOTES_CONTEXT'):
            records.bind(
                session_id='wrong-context-session',
                observation=self.make_evidence(
                    list_key=records.list_data['list_key']),
                handoff=self.make_evidence(
                    list_key=records.list_data['list_key']),
                context_id='different-context')
        self.assertEqual(self.event_bytes(records), before)

        binding = self.bind(records, 'omitted-context-session')
        self.assertEqual(binding['context_id'], 'saved-context')
        explicit = records.bind(
            session_id='explicit-context-session',
            observation=self.make_evidence(
                list_key=records.list_data['list_key']),
            handoff=self.make_evidence(
                list_key=records.list_data['list_key']),
            context_id='saved-context')
        self.assertEqual(explicit['context_id'], 'saved-context')
        events = [json.loads(path.read_text())
                  for path in sorted((records.records / 'events').iterdir())]
        self.assertEqual(events[-1]['data']['context_id'], 'saved-context')

        cli_records, _ = self.new_ledger(
            'context-bind-cli', context_id='saved-cli-context')
        args = ('bind', '--records-root', cli_records.records,
                '--session-id', 'cli-fresh-session',
                '--observation', self.make_evidence(
                    list_key=cli_records.list_data['list_key']),
                '--handoff', self.make_evidence(
                    list_key=cli_records.list_data['list_key']))
        before = self.event_bytes(cli_records)
        rejected = self.run_cli(*args, '--context-id', 'wrong-cli-context')
        self.assertEqual(rejected.returncode, 4)
        self.assertEqual(self.event_bytes(cli_records), before)
        accepted = self.run_cli(*args, '--context-id', 'saved-cli-context')
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        result = json.loads(accepted.stdout)
        self.assertEqual(result['context_id'], 'saved-cli-context')

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
            outcome='DOWNLOAD_FINISHED',
            evidence=self.attempt_evidence(self.records, attempt))
        before = self.event_bytes()
        with self.assertRaisesRegex(NotesError, 'OUTCOME_ALREADY_RECORDED'):
            self.records.outcome(
                session_id=self.session, attempt_id=attempt['attempt_id'],
                outcome='NOT_SENT',
                evidence=self.attempt_evidence(self.records, attempt))
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
            outcome='UNKNOWN',
            evidence=self.attempt_evidence(self.records, attempt))
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
            result='UNKNOWN',
            evidence=self.attempt_evidence(self.records, attempt))
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
            outcome='STOPPED',
            evidence=self.attempt_evidence(self.records, first))
        with self.assertRaisesRegex(NotesError, 'NOTES_RECOVERY_EVIDENCE_REQUIRED'):
            self.records.intent(session_id=self.session, media_key_value=key)
        second = self.records.intent(
            session_id=self.session, media_key_value=key,
            recovery_evidence=self.attempt_evidence(self.records, first))
        self.assertNotEqual(first['destination'], second['destination'])
        self.assertEqual(second['recovery_of'], first['attempt_id'])
        self.assertTrue(Path(first['destination']).is_dir())
        self.assertTrue(Path(second['destination']).is_dir())
        self.records.outcome(
            session_id=self.session, attempt_id=second['attempt_id'],
            outcome='NOT_SENT',
            evidence=self.attempt_evidence(self.records, second))
        third = self.records.intent(
            session_id=self.session, media_key_value=key,
            recovery_evidence=self.attempt_evidence(self.records, second))
        self.assertEqual(third['recovery_of'], second['attempt_id'])
        self.assertNotEqual(third['destination'], first['destination'])
        self.assertNotEqual(third['destination'], second['destination'])
        self.assertEqual(len(list(Path(first['destination']).iterdir())), 0)

    def test_new_intent_staging_allows_environment_attachment(self):
        identity = notes.media_identity(
            kind=PHOTO, visual_key='intent-environment')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'],
            'post-intent-environment', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        original = notes._new_unique_directory

        def create_staging(parent, prefix):
            staging = original(parent, prefix)
            (staging / '.DS_Store').write_bytes(
                b'synthetic new-intent environment')
            return staging

        before = self.event_bytes()
        with mock.patch.object(
                notes, '_new_unique_directory', side_effect=create_staging):
            attempt = self.records.intent(
                session_id=self.session, media_key_value=key)
        staging = Path(attempt['destination'])
        self.assertEqual([path.name for path in staging.iterdir()],
                         ['.DS_Store'])
        self.assertEqual(
            (staging / '.DS_Store').read_bytes(),
            b'synthetic new-intent environment')
        self.assertEqual(attempt['status'], 'UNKNOWN')
        self.assertFalse(attempt['dispatch_authorized'])
        self.assertEqual(self.records._validate_staging(attempt), staging)
        intent_events = [event for event in self.records.events
                         if event['kind'] == 'intent']
        self.assertEqual(len(intent_events), 1)
        self.assertEqual(intent_events[0]['data']['destination'], str(staging))
        after = self.event_bytes()
        self.assertEqual(len(after), len(before) + 1)
        self.assertLessEqual(set(before), set(after))

    def test_new_intent_staging_refuses_non_environment_entries(self):
        identity = notes.media_identity(
            kind=PHOTO, visual_key='intent-invalid-environment')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'],
            'post-intent-invalid-environment', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        original = notes._new_unique_directory

        for entry_type in (
                'unknown-file', 'other-dotfile', 'unknown-directory',
                'environment-symlink', 'environment-directory',
                'environment-hardlink', 'extra-media'):
            with self.subTest(entry_type=entry_type):
                hardlink_target = self.base / (
                    'intent-hardlink-target-' + entry_type)

                def create_staging(parent, prefix):
                    staging = original(parent, prefix)
                    environment = staging / '.DS_Store'
                    if entry_type == 'unknown-file':
                        (staging / 'unexpected.bin').write_bytes(b'unexpected')
                    elif entry_type == 'other-dotfile':
                        (staging / '.AppleDouble').write_bytes(b'other dotfile')
                    elif entry_type == 'unknown-directory':
                        (staging / 'unexpected-directory').mkdir()
                    elif entry_type == 'environment-symlink':
                        hardlink_target.write_bytes(b'link target')
                        environment.symlink_to(hardlink_target)
                    elif entry_type == 'environment-directory':
                        environment.mkdir()
                    elif entry_type == 'environment-hardlink':
                        hardlink_target.write_bytes(b'hardlink target')
                        os.link(hardlink_target, environment)
                    else:
                        environment.write_bytes(b'environment bytes')
                        (staging / 'unexpected.mp4').write_bytes(b'extra video')
                    return staging

                before = self.event_bytes()
                with mock.patch.object(
                        notes, '_new_unique_directory',
                        side_effect=create_staging):
                    with self.assertRaisesRegex(
                            NotesError, 'EMPTY_STAGING_REQUIRED'):
                        self.records.intent(
                            session_id=self.session, media_key_value=key)
                self.assertEqual(self.event_bytes(), before)

    def test_environment_attachment_survives_inventory_publish_and_cleanup(self):
        first_identity = notes.media_identity(
            kind=PHOTO, visual_key='publish-environment-first')
        second_identity = notes.media_identity(
            kind=PHOTO, visual_key='publish-environment-second')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'],
            'post-publish-environment', [first_identity, second_identity])
        first_key = self.media_key(
            self.records, post_key_value, first_identity)
        second_key = self.media_key(
            self.records, post_key_value, second_identity)
        _first_attempt, first_completion = self.download(
            self.records, first_key, 'first.png', png())
        post_directory = Path(first_completion['data']['destination'])
        first_target = post_directory / first_completion['data']['target_file']['name']
        first_bytes = first_target.read_bytes()
        first_info = first_target.stat()
        target_environment = post_directory / '.DS_Store'
        target_environment.write_bytes(b'target environment bytes')

        original = notes._new_unique_directory

        def create_staging(parent, prefix):
            staging = original(parent, prefix)
            (staging / '.DS_Store').write_bytes(b'staging environment 0')
            return staging

        with mock.patch.object(
                notes, '_new_unique_directory', side_effect=create_staging):
            attempt = self.records.intent(
                session_id=self.session, media_key_value=second_key)
        staging = Path(attempt['destination'])
        staging_environment = staging / '.DS_Store'
        (staging / 'second.png').write_bytes(png((0, 255, 0)))
        self.records.outcome(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=self.attempt_evidence(self.records, attempt))

        original_inventory = notes._inventory_row
        samples = []

        def changing_inventory(path):
            row = original_inventory(path)
            if Path(path).name != '.DS_Store':
                samples.append(row)
                staging_environment.write_bytes(
                    ('staging environment %d' % len(samples)).encode('ascii'))
            return row

        with mock.patch.object(
                notes, '_inventory_row', side_effect=changing_inventory):
            completion = self.records.verify(
                session_id=self.session, attempt_id=attempt['attempt_id'],
                verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(len(samples), 4)
        self.assertEqual(completion['data']['media_key'], second_key)
        self.assertEqual(completion['data']['source_manifest']['name'],
                         'second.png')
        verification = next(
            event for event in self.records.events
            if event['kind'] == 'verification' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        self.assertEqual(verification['data']['manifest'],
                         [completion['data']['source_manifest']])
        self.assertEqual(staging_environment.read_bytes(),
                         b'staging environment 4')
        self.assertEqual([path.name for path in staging.iterdir()],
                         ['.DS_Store'])
        self.assertEqual(target_environment.read_bytes(),
                         b'target environment bytes')
        self.assertEqual(
            sorted(path.name for path in post_directory.iterdir()),
            ['.DS_Store', 'media_001.png', 'media_002.png'])
        self.assertEqual(first_target.read_bytes(), first_bytes)
        self.assertEqual(first_target.stat().st_ino, first_info.st_ino)
        self.assertFalse(any(
            b'.DS_Store' in raw for raw in self.event_bytes().values()))
        self.assertEqual(self.records._pending_publish_plans(), [])

        reopened = self.reopen(self.records)
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 2)
        self.assertEqual(summary['local_counts'][LOCAL_VERIFIED], 2)
        self.assertTrue(summary['all_known_media_complete'])
        self.assertEqual(summary['dispatch_blockers'], [])
        self.assertEqual(reopened.resume()['action'], 'NO_NAMING_TRANSACTION')
        self.assertEqual(reopened.resume()['pending'], [])
        self.assertEqual(sum(
            event['kind'] == 'outcome' and
            event['data']['attempt_id'] == attempt['attempt_id']
            for event in reopened.events), 1)
        self.assertEqual(sum(
            event['kind'] == 'completion' and
            event['data']['media_key'] == second_key
            for event in reopened.events), 1)

        staging_environment.unlink()
        self.assertEqual(self.reopen(self.records).summary()['local_counts'][
            LOCAL_VERIFIED], 2)
        self.assertTrue(staging.is_dir())
        self.assertEqual(list(staging.iterdir()), [])

    def test_publish_rejects_extra_video_and_target_collision(self):
        for mutation, error in (
                ('extra-video', 'POST_DIRECTORY_UNEXPECTED_CONTENT'),
                ('target-collision', 'TARGET_ALREADY_EXISTS')):
            with self.subTest(mutation=mutation):
                records, summary = self.new_ledger(
                    'publish-negative-' + mutation,
                    recovery_authorized=True)
                first_identity = notes.media_identity(
                    kind=PHOTO, visual_key=mutation + '-first')
                second_identity = notes.media_identity(
                    kind=PHOTO, visual_key=mutation + '-second')
                _, post_key_value, _ = self.observe_post(
                    records, summary['list_key'],
                    'post-' + mutation, [first_identity, second_identity])
                second_key = self.media_key(
                    records, post_key_value, second_identity)
                post_directory, existed = \
                    records._post_directory_for_publish(post_key_value)
                self.assertFalse(existed)
                post_directory.mkdir(parents=True)
                environment = post_directory / '.DS_Store'
                environment.write_bytes(b'post environment bytes')
                if mutation == 'extra-video':
                    protected = post_directory / 'unexpected.mp4'
                    protected.write_bytes(b'protected extra video')

                attempt = records.intent(
                    session_id=self.session, media_key_value=second_key)
                (Path(attempt['destination']) / 'first.png').write_bytes(
                    png((0, 0, 255)))
                records.outcome(
                    session_id=self.session,
                    attempt_id=attempt['attempt_id'],
                    outcome='DOWNLOAD_FINISHED',
                    evidence=self.attempt_evidence(records, attempt))

                if mutation == 'extra-video':
                    with self.assertRaisesRegex(NotesError, error):
                        records.verify(
                            session_id=self.session,
                            attempt_id=attempt['attempt_id'],
                            verifier=self.pass_verifier,
                            stability_interval=0)
                else:
                    original_publish_directory = \
                        records._post_directory_for_publish
                    collision_written = []

                    def publish_directory_with_collision(
                            post_key, original=original_publish_directory):
                        result = original(post_key)
                        protected = post_directory / 'media_001.png'
                        protected.write_bytes(b'protected collision bytes')
                        collision_written.append(protected)
                        return result

                    with mock.patch.object(
                            records, '_post_directory_for_publish',
                            side_effect=publish_directory_with_collision):
                        with self.assertRaisesRegex(NotesError, error):
                            records.verify(
                                session_id=self.session,
                                attempt_id=attempt['attempt_id'],
                                verifier=self.pass_verifier,
                                stability_interval=0)
                    self.assertEqual(len(collision_written), 1)
                    protected = collision_written[0]

                self.assertEqual(environment.read_bytes(),
                                 b'post environment bytes')
                if mutation == 'extra-video':
                    self.assertEqual(protected.read_bytes(),
                                     b'protected extra video')
                else:
                    self.assertEqual(protected.read_bytes(),
                                     b'protected collision bytes')
                self.assertFalse(any(
                    event['kind'] == 'completion' and
                    event['data']['media_key'] == second_key
                    for event in records.events))
                self.assertFalse(any(
                    event['kind'] == 'publish-plan' and
                    event['data']['attempt_id'] == attempt['attempt_id']
                    for event in records.events))
                self.assertFalse(any(
                    b'.DS_Store' in raw for raw in self.event_bytes(records).values()))

    def test_inventory_environment_filter_does_not_mask_unknown_entries(self):
        for mutation, error in (
                ('unknown-file', 'DOWNLOAD_COUNT_MISMATCH'),
                ('other-dotfile', 'UNEXPECTED_DOWNLOAD_ENTRY'),
                ('unknown-directory', 'UNEXPECTED_DOWNLOAD_ENTRY'),
                ('environment-symlink', 'UNEXPECTED_DOWNLOAD_ENTRY'),
                ('environment-directory', 'UNEXPECTED_DOWNLOAD_ENTRY'),
                ('environment-hardlink', 'UNEXPECTED_DOWNLOAD_ENTRY'),
                ('extra-video', 'DOWNLOAD_COUNT_MISMATCH')):
            with self.subTest(mutation=mutation):
                records, summary = self.new_ledger(
                    'inventory-negative-' + mutation,
                    recovery_authorized=True)
                identity = notes.media_identity(
                    kind=PHOTO, visual_key=mutation + '-media')
                _, post_key_value, _ = self.observe_post(
                    records, summary['list_key'], 'post-' + mutation,
                    [identity])
                key = self.media_key(records, post_key_value, identity)
                attempt = records.intent(
                    session_id=self.session, media_key_value=key)
                staging = Path(attempt['destination'])
                (staging / 'first.png').write_bytes(png((1, 2, 3)))
                environment = staging / '.DS_Store'
                if mutation == 'unknown-file':
                    environment.write_bytes(b'environment bytes')
                    protected = staging / 'unexpected.bin'
                    protected.write_bytes(b'protected unknown file')
                elif mutation == 'other-dotfile':
                    environment.write_bytes(b'environment bytes')
                    protected = staging / '.AppleDouble'
                    protected.write_bytes(b'protected other dotfile')
                elif mutation == 'unknown-directory':
                    environment.write_bytes(b'environment bytes')
                    protected = staging / 'unexpected-directory'
                    protected.mkdir()
                elif mutation == 'environment-symlink':
                    protected = self.base / 'inventory-environment-target'
                    protected.write_bytes(b'protected symlink target')
                    environment.symlink_to(protected)
                elif mutation == 'environment-directory':
                    environment.mkdir()
                    protected = environment
                elif mutation == 'environment-hardlink':
                    protected = self.base / 'inventory-hardlink-target'
                    protected.write_bytes(b'protected hardlink target')
                    os.link(protected, environment)
                else:
                    environment.write_bytes(b'environment bytes')
                    protected = staging / 'unexpected.mp4'
                    protected.write_bytes(b'protected extra video')

                records.outcome(
                    session_id=self.session, attempt_id=attempt['attempt_id'],
                    outcome='DOWNLOAD_FINISHED',
                    evidence=self.attempt_evidence(records, attempt))
                before = self.event_bytes(records)
                with self.assertRaisesRegex(NotesError, error):
                    records.verify(
                        session_id=self.session,
                        attempt_id=attempt['attempt_id'],
                        verifier=self.pass_verifier,
                        stability_interval=0)
                self.assertEqual(self.event_bytes(records), before)
                self.assertFalse(any(
                    event['kind'] in ('verification', 'completion')
                    for event in records.events
                    if event['data'].get('attempt_id') == attempt['attempt_id']))

    def test_inventory_environment_filter_does_not_mask_real_media_drift(self):
        identity = notes.media_identity(
            kind=PHOTO, visual_key='inventory-media-drift')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'],
            'post-inventory-media-drift', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        attempt = self.records.intent(
            session_id=self.session, media_key_value=key)
        staging = Path(attempt['destination'])
        source = staging / 'first.png'
        original_bytes = png((1, 2, 3))
        changed_bytes = png((3, 2, 1))
        source.write_bytes(original_bytes)
        environment = staging / '.DS_Store'
        environment.write_bytes(b'protected inventory environment')
        self.records.outcome(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=self.attempt_evidence(self.records, attempt))

        original_inventory = notes._inventory_once
        samples = []

        def mutate_media_after_first_sample(directory):
            rows = original_inventory(directory)
            samples.append(rows)
            if len(samples) == 1:
                source.write_bytes(changed_bytes)
            return rows

        before = self.event_bytes()
        with mock.patch.object(
                notes, '_inventory_once',
                side_effect=mutate_media_after_first_sample):
            with self.assertRaisesRegex(NotesError, 'DOWNLOAD_NOT_STABLE'):
                self.records.verify(
                    session_id=self.session,
                    attempt_id=attempt['attempt_id'],
                    verifier=self.pass_verifier,
                    stability_interval=0)
        self.assertEqual(len(samples), 2)
        self.assertEqual(source.read_bytes(), changed_bytes)
        self.assertEqual(environment.read_bytes(),
                         b'protected inventory environment')
        self.assertEqual(self.event_bytes(), before)
        self.assertFalse(any(
            event['kind'] in ('verification', 'completion') and
            event['data'].get('attempt_id') == attempt['attempt_id']
            for event in self.records.events))

    def test_new_publish_post_directory_with_only_environment_attachment(self):
        identity = notes.media_identity(
            kind=PHOTO, visual_key='new-post-environment')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'],
            'post-new-post-environment', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        post_directory, existed = self.records._post_directory_for_publish(
            post_key_value)
        self.assertFalse(existed)
        self.assertFalse(post_directory.exists())
        post_directory.mkdir(parents=True)
        environment = post_directory / '.DS_Store'
        environment.write_bytes(b'new post environment')
        payload = png((5, 6, 7))

        _attempt, completion = self.download(
            self.records, key, 'first.png', payload)

        self.assertEqual(completion['data']['target_file']['name'],
                         'media_001.png')
        self.assertEqual(completion['data']['source_manifest']['name'],
                         'first.png')
        verification = next(
            event for event in self.records.events
            if event['kind'] == 'verification' and
            event['data']['media_key'] == key)
        self.assertEqual(
            verification['data']['manifest'],
            [completion['data']['source_manifest']])
        self.assertEqual(environment.read_bytes(), b'new post environment')
        self.assertEqual((post_directory / 'media_001.png').read_bytes(), payload)
        self.assertEqual(
            sorted(path.name for path in post_directory.iterdir()),
            ['.DS_Store', 'media_001.png'])
        self.assertEqual(self.records._pending_publish_plans(), [])
        self.assertEqual(self.reopen(self.records).resume()['action'],
                         'NO_NAMING_TRANSACTION')
        self.assertFalse(any(
            b'.DS_Store' in raw for raw in self.event_bytes().values()))

    def test_publish_rejects_unknown_staging_entry_after_environment(self):
        identity = notes.media_identity(
            kind=PHOTO, visual_key='publish-staging-negative')
        _, post_key_value, _ = self.observe_post(
            self.records, self.summary['list_key'],
            'post-publish-staging-negative', [identity])
        key = self.media_key(self.records, post_key_value, identity)
        attempt = self.records.intent(
            session_id=self.session, media_key_value=key)
        staging = Path(attempt['destination'])
        source = staging / 'first.png'
        source.write_bytes(png((4, 5, 6)))
        environment = staging / '.DS_Store'
        environment.write_bytes(b'protected staging environment')
        self.records.outcome(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=self.attempt_evidence(self.records, attempt))

        original_unlink = notes._unlink_regular
        added = []

        def unlink_then_add_unknown(source_path, code):
            result = original_unlink(source_path, code)
            extra = staging / 'unexpected.bin'
            extra.write_bytes(b'protected post-link extra')
            added.append(extra)
            return result

        with mock.patch.object(
                notes, '_unlink_regular', side_effect=unlink_then_add_unknown):
            with self.assertRaisesRegex(
                    NotesError, 'STAGING_NOT_EMPTY_AFTER_PUBLISH'):
                self.records.verify(
                    session_id=self.session,
                    attempt_id=attempt['attempt_id'],
                    verifier=self.pass_verifier,
                    stability_interval=0)
        self.assertEqual(len(added), 1)
        self.assertEqual(environment.read_bytes(),
                         b'protected staging environment')
        self.assertEqual(added[0].read_bytes(), b'protected post-link extra')
        self.assertFalse(any(
            event['kind'] == 'completion' and
            event['data']['media_key'] == key
            for event in self.records.events))
        self.assertEqual(len(self.records._pending_publish_plans()), 1)

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
            outcome='DOWNLOAD_FINISHED',
            evidence=self.attempt_evidence(self.records, attempt))
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

    def test_completion_environment_file_keeps_verified_state_without_being_read(self):
        records, summary, post_key_value, identity, completion = (
            self.completed_ledger('environment'))
        directory = Path(completion['data']['destination'])
        environment = directory / '.DS_Store'
        before_events = self.event_bytes(records)
        original_read = notes.read_file

        def guarded_read(path, *args, **kwargs):
            if Path(path).name == '.DS_Store':
                raise AssertionError('environment file must not be read')
            return original_read(path, *args, **kwargs)

        for payload in (b'environment', b'changed environment'):
            environment.write_bytes(payload)
            reopened = self.reopen(records)
            key = notes.media_key(
                summary['list_key'], post_key_value, identity)
            with mock.patch.object(notes, 'read_file', side_effect=guarded_read):
                result = reopened.summary()
            row = next(item for item in result['media']
                       if item['media_key'] == key)
            self.assertEqual((row['status'], row['local_files']),
                             ('COMPLETED', LOCAL_VERIFIED))

        environment.unlink()
        reopened = self.reopen(records)
        key = notes.media_key(summary['list_key'], post_key_value, identity)
        result = reopened.summary()
        row = next(item for item in result['media'] if item['media_key'] == key)
        self.assertEqual((row['status'], row['local_files']),
                         ('COMPLETED', LOCAL_VERIFIED))
        self.assertEqual(self.event_bytes(reopened), before_events)
        self.assertFalse(any(
            b'.DS_Store' in raw for raw in self.event_bytes(reopened).values()))
        self.assertEqual(summary['list_key'], reopened.list_data['list_key'])

    def test_irregular_completion_environment_entry_is_local_changed(self):
        for entry_type in ('symlink', 'directory', 'hardlink'):
            with self.subTest(entry_type=entry_type):
                records, _summary, post_key_value, identity, completion = (
                    self.completed_ledger('environment-' + entry_type))
                directory = Path(completion['data']['destination'])
                environment = directory / '.DS_Store'
                if entry_type == 'symlink':
                    target = self.base / ('environment-' + entry_type)
                    target.write_bytes(b'environment symlink target')
                    environment.symlink_to(target)
                elif entry_type == 'directory':
                    environment.mkdir()
                else:
                    media = directory / completion['data']['target_file']['name']
                    os.link(media, environment)
                reopened = self.reopen(records)
                result = reopened.summary()
                key = self.media_key(reopened, post_key_value, identity)
                row = next(item for item in result['media']
                           if item['media_key'] == key)
                self.assertEqual((row['status'], row['local_files']),
                                 ('COMPLETED', LOCAL_CHANGED))

    def test_completion_environment_and_other_dotfile_together_are_local_changed(self):
        records, summary, post_key_value, identity, completion = (
            self.completed_ledger('environment-and-other-dotfile'))
        directory = Path(completion['data']['destination'])
        environment = directory / '.DS_Store'
        environment.write_bytes(b'completion environment')
        other_dotfile = directory / '.AppleDouble'
        other_dotfile.write_bytes(b'other completion dotfile')
        before = self.event_bytes(records)

        reopened = self.reopen(records)
        result = reopened.summary()
        key = self.media_key(reopened, post_key_value, identity)
        row = next(item for item in result['media'] if item['media_key'] == key)

        self.assertEqual((row['status'], row['local_files']),
                         ('COMPLETED', LOCAL_CHANGED))
        self.assertEqual(environment.read_bytes(), b'completion environment')
        self.assertEqual(other_dotfile.read_bytes(),
                         b'other completion dotfile')
        self.assertEqual(self.event_bytes(reopened), before)

    def test_completion_environment_file_survives_session_without_unknown(self):
        records, summary, post_key_value, identity, completion = (
            self.completed_ledger('environment-new-session'))
        directory = Path(completion['data']['destination'])
        environment = directory / '.DS_Store'
        environment.write_bytes(b'cross-session environment')
        before = self.event_bytes(records)
        reopened = self.reopen(records)
        reopened.summary()
        self.bind(reopened, 'new-session-environment')
        key = notes.media_key(summary['list_key'], post_key_value, identity)
        result = reopened.summary()
        row = next(item for item in result['media'] if item['media_key'] == key)
        self.assertEqual((row['status'], row['local_files']),
                         ('COMPLETED', LOCAL_VERIFIED))
        self.observe_post(
            reopened, summary['list_key'], 'post-environment-new-session',
            [identity], session='new-session-environment')
        with self.assertRaisesRegex(
                NotesError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            reopened.intent(
                session_id='new-session-environment', media_key_value=key)
        self.assertEqual(environment.read_bytes(),
                         b'cross-session environment')
        preserved = self.event_bytes(reopened)
        for name, raw in before.items():
            self.assertEqual(preserved[name], raw)

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
                             outcome='NOT_SENT',
                             evidence=self.attempt_evidence(reopened, attempt))
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
            outcome='DOWNLOAD_FINISHED',
            evidence=self.attempt_evidence(records, attempt))
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
        self.assertIn('list-key', help_result.stdout)
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

    def test_lists_records_root_feeds_summary_without_local_list_id_flag(self):
        listed = self.run_cli('lists', '--collection', self.collection_path)
        self.assertEqual(listed.returncode, 0, listed.stderr)
        listed_payload = json.loads(listed.stdout)
        self.assertEqual(len(listed_payload['lists']), 1)
        row = listed_payload['lists'][0]
        self.assertEqual(row['records_root'], self.summary['records_root'])
        self.assertEqual(row['list_key'], self.summary['list_key'])

        summarized = self.run_cli(
            'summary', '--records-root', row['records_root'])
        self.assertEqual(summarized.returncode, 0, summarized.stderr)
        summary_payload = json.loads(summarized.stdout)
        self.assertEqual(summary_payload['records_root'], row['records_root'])
        self.assertEqual(summary_payload['local_list_id'], row['local_list_id'])
        self.assertEqual(summary_payload['list_key'], row['list_key'])
        self.assertFalse(summary_payload['dispatch_authorized'])

        unknown_flag = self.run_cli(
            'summary', '--records-root', row['records_root'],
            '--local-list-id', row['local_list_id'])
        self.assertEqual(unknown_flag.returncode, 2)
        self.assertEqual(unknown_flag.stdout, '')
        self.assertIn('unrecognized arguments', unknown_flag.stderr)

    def test_rejected_evidence_pack_does_not_append_business_event(self):
        before = self.event_bytes()
        missing_parent = self.evidence_packs / uuid.uuid4().hex / 'new-bundle'
        rejected = self.run_cli(
            'evidence-pack',
            '--statement', self.evidence,
            '--asset', 'screenshot', self.screenshot,
            '--list-key', self.summary['list_key'],
            '--output-dir', missing_parent)

        self.assertEqual(rejected.returncode, 4)
        payload = json.loads(rejected.stdout)
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertEqual(payload['reason'], 'EVIDENCE_OUTPUT_PARENT_REQUIRED')
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(self.event_bytes(), before)
        self.assertFalse(missing_parent.exists())

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


class NotesListKeyCliTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='notes-list-key-', dir=PRIVATE_TASKS)
        self.base = Path(self.temporary.name).resolve()
        self.collection = self.base / 'collection'
        self.photo_root = self.base / 'photos'
        self.statement = self.base / 'statement.txt'
        self.statement.write_bytes(b'synthetic list identity statement\n')
        self.screenshot = self.base / 'screenshot.bin'
        self.screenshot.write_bytes(b'synthetic list identity screenshot')
        self.packs = self.base / 'evidence-packs'
        self.packs.mkdir()
        self.active_read = mock.patch.object(
            notes, '_read_active_hint', return_value=None)
        self.active_write = mock.patch.object(
            notes, '_write_active_hint', return_value=None)
        self.active_read.start()
        self.active_write.start()

    def tearDown(self):
        self.active_write.stop()
        self.active_read.stop()
        self.temporary.cleanup()

    def run_main(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch('sys.stdout', new=stdout), \
                mock.patch('sys.stderr', new=stderr):
            try:
                code = notes.main([str(value) for value in args])
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def list_key_payload(self, *args):
        code, stdout, stderr = self.run_main('list-key', *args)
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(payload['list_key'], notes.list_key(payload['identity']))
        return payload

    def make_bundle(self, list_key_value):
        output = self.packs / uuid.uuid4().hex
        return notes_evidence.create_bundle(
            statement=str(self.statement),
            assets=[('screenshot', str(self.screenshot))],
            context=dict(list_key=list_key_value),
            output_dir=str(output))['bundle_path']

    def test_list_key_matches_init_and_readback(self):
        identity_args = (
            '--visual-key', '  Synthetic List Ω  ',
            '--context-id', '  Foreground e\u0301  ',
            '--signals', '{"z":[2,1],"a":{"second":2,"first":1}}')
        computed = self.list_key_payload(*identity_args)
        first_bundle = self.make_bundle(computed['list_key'])
        second_bundle = self.make_bundle(computed['list_key'])

        code, stdout, stderr = self.run_main(
            'init', '--collection', self.collection,
            '--photo-root', self.photo_root, '--name', 'Synthetic Notes',
            *identity_args,
            '--binding-evidence', first_bundle,
            '--history-scope-evidence', second_bundle)
        self.assertEqual(code, 0, stderr)
        initialized = json.loads(stdout)
        self.assertFalse(initialized['dispatch_authorized'])
        self.assertEqual(initialized['identity'], computed['identity'])
        self.assertEqual(initialized['list_key'], computed['list_key'])
        readback = NotesRecords(initialized['records_root']).summary()
        self.assertEqual(readback['list_key'], computed['list_key'])

    def test_list_key_preserves_identity_json_semantics_and_boundaries(self):
        plain = self.list_key_payload('--visual-key', 'plain')
        as_null = self.list_key_payload(
            '--visual-key', 'plain', '--signals', 'null')
        empty_object = self.list_key_payload(
            '--visual-key', 'plain', '--signals', '{}')
        self.assertNotIn('signals', plain['identity'])
        self.assertEqual(as_null, plain)
        self.assertEqual(empty_object['identity']['signals'], {})
        self.assertNotEqual(empty_object['list_key'], plain['list_key'])

        reordered_a = self.list_key_payload(
            '--visual-key', 'ordered', '--signals',
            '{"b":[2],"a":{"y":2,"x":1}}')
        reordered_b = self.list_key_payload(
            '--visual-key', 'ordered', '--signals',
            '{ "a": {"x": 1, "y": 2}, "b": [2] }')
        self.assertEqual(reordered_a, reordered_b)

        array_a = self.list_key_payload(
            '--visual-key', 'array', '--signals', '{"items":["a","b"]}')
        array_b = self.list_key_payload(
            '--visual-key', 'array', '--signals', '{"items":["b","a"]}')
        self.assertNotEqual(array_a['list_key'], array_b['list_key'])

        spaced = self.list_key_payload(
            '--visual-key', '  列表 Ω  ',
            '--context-id', '  前景 e\u0301  ',
            '--signals', '{"text":"  keep case Ω  "}')
        self.assertEqual(spaced['identity']['visual_key'], '  列表 Ω  ')
        self.assertEqual(spaced['identity']['context_id'], '  前景 e\u0301  ')
        self.assertEqual(spaced['identity']['signals']['text'], '  keep case Ω  ')
        trimmed = self.list_key_payload('--visual-key', '列表 Ω')
        self.assertNotEqual(spaced['list_key'], trimmed['list_key'])

        self.list_key_payload('--visual-key', 'x' * 4096)
        self.list_key_payload(
            '--visual-key', 'x', '--context-id', 'c' * 4096)
        for args, reason in (
                (('--visual-key', '   '), 'LIST_VISUAL_KEY_REQUIRED'),
                (('--visual-key', 'x', '--context-id', '   '),
                 'INVALID_CONTEXT_ID'),
                (('--visual-key', 'x' * 4097), 'LIST_VISUAL_KEY_REQUIRED'),
                (('--visual-key', 'x', '--context-id', 'c' * 4097),
                 'INVALID_CONTEXT_ID')):
            with self.subTest(reason=reason, length=len(args[1])):
                code, stdout, stderr = self.run_main('list-key', *args)
                self.assertEqual(code, 4, stderr)
                payload = json.loads(stdout)
                self.assertEqual(payload['status'], 'REFUSED')
                self.assertEqual(payload['reason'], reason)
                self.assertFalse(payload['dispatch_authorized'])

        oversized = self.base / 'oversized-signals.json'
        oversized.write_text(
            json.dumps({'blob': 'x' * (256 * 1024)}), encoding='utf-8')
        code, stdout, _stderr = self.run_main(
            'list-key', '--visual-key', 'large', '--signals', '@' + str(oversized))
        self.assertEqual(code, 4)
        self.assertEqual(json.loads(stdout)['reason'], 'INVALID_IDENTITY_SIGNALS')

        for value in (
                '{"a":1,"a":2}', '{"number":NaN}', '{not-json}'):
            with self.subTest(signals=value):
                code, stdout, stderr = self.run_main(
                    'list-key', '--visual-key', 'bad-json', '--signals', value)
                self.assertEqual(code, 2)
                self.assertEqual(stdout, '')
                self.assertIn('--signals must be valid JSON', stderr)

        code, stdout, stderr = self.run_main('list-key')
        self.assertEqual(code, 2)
        self.assertEqual(stdout, '')
        self.assertIn('--visual-key', stderr)
        code, stdout, _stderr = self.run_main(
            'list-key', '--visual-key', 'x', '--collection', self.collection)
        self.assertEqual(code, 2)
        self.assertEqual(stdout, '')

        output = io.StringIO()
        with mock.patch.object(notes, 'list_key', side_effect=RuntimeError('synthetic')):
            with mock.patch('sys.stdout', new=output):
                code = notes.main(['list-key', '--visual-key', 'synthetic'])
        self.assertEqual(code, 70)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload['status'], 'INTERNAL_ERROR')
        self.assertEqual(payload['reason'], 'UNEXPECTED_EXCEPTION')
        self.assertFalse(payload['dispatch_authorized'])


class NotesListKeyIsolationTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='notes-list-key-isolation-', dir=PRIVATE_TASKS)
        self.base = Path(self.temporary.name).resolve()
        self.collection = self.base / 'collection'
        self.photo_root = self.base / 'photos'
        self.ledger = self.collection / 'synthetic-ledger'
        self.events = self.ledger / 'events'
        self.events.mkdir(parents=True)
        (self.events / '00000001.json').write_bytes(b'{"synthetic":"event"}\n')
        (self.ledger / '.lock').write_bytes(b'lock-bytes')
        (self.collection / 'index.json').write_bytes(
            b'{"synthetic":"index"}\n'
        )
        self.photo_root.mkdir()
        (self.photo_root / 'synthetic-photo.jpg').write_bytes(b'photo-bytes')
        (self.base / 'active-notes-task.json').write_bytes(
            b'{"synthetic":"active-hint"}\n')

    def tearDown(self):
        self.temporary.cleanup()

    def snapshot(self):
        result = {}
        for path in sorted(self.base.rglob('*')):
            relative = str(path.relative_to(self.base))
            info = path.lstat()
            if path.is_dir():
                result[relative] = ('directory', info.st_mode)
            else:
                result[relative] = ('file', info.st_mode, path.read_bytes())
        return result

    def run_main(self, *args):
        stdout = io.StringIO()
        with mock.patch('sys.stdout', new=stdout):
            try:
                code = notes.main([str(value) for value in args])
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue()

    def test_list_key_reads_no_files_or_constructs_ledgers_without_signals_file(self):
        before = self.snapshot()
        with mock.patch.object(notes, 'NotesCollection', side_effect=AssertionError):
            with mock.patch.object(notes, 'NotesRecords', side_effect=AssertionError):
                with mock.patch.object(notes, '_read_active_hint',
                                       side_effect=AssertionError):
                    with mock.patch.object(notes, '_write_active_hint',
                                           side_effect=AssertionError):
                        with mock.patch.object(
                                notes.Path, 'read_bytes', autospec=True,
                                side_effect=AssertionError('unexpected file read')):
                            with mock.patch.object(
                                    notes, '_open_lock',
                                    side_effect=AssertionError('unexpected lock')):
                                with mock.patch.object(
                                        notes.subprocess, 'run',
                                        side_effect=AssertionError('unexpected subprocess')):
                                    with mock.patch.object(
                                            notes.subprocess, 'Popen',
                                            side_effect=AssertionError('unexpected subprocess')):
                                        code, stdout = self.run_main(
                                            'list-key', '--visual-key', 'no-ledger')
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(stdout)['dispatch_authorized'])
        self.assertEqual(self.snapshot(), before)

    def test_list_key_reads_only_the_named_signals_file_without_retry(self):
        signals = self.base / 'signals.json'
        signals.write_bytes(b'{"list":"synthetic"}\n')
        before = self.snapshot()
        reads = []
        original_read = Path.read_bytes

        def tracked_read(path):
            reads.append(path)
            if path != signals:
                raise AssertionError('unexpected file read: %s' % path)
            return original_read(path)

        with mock.patch.object(notes, 'NotesCollection', side_effect=AssertionError):
            with mock.patch.object(notes, 'NotesRecords', side_effect=AssertionError):
                with mock.patch.object(notes, '_read_active_hint',
                                       side_effect=AssertionError):
                    with mock.patch.object(notes, '_write_active_hint',
                                           side_effect=AssertionError):
                        with mock.patch.object(
                                notes.Path, 'read_bytes', autospec=True,
                                side_effect=tracked_read):
                            code, stdout = self.run_main(
                                'list-key', '--visual-key', 'with-file',
                                '--signals', '@' + str(signals))
        self.assertEqual(code, 0)
        self.assertEqual(reads, [signals])
        self.assertEqual(json.loads(stdout)['identity']['signals'],
                         {'list': 'synthetic'})
        self.assertEqual(self.snapshot(), before)

        duplicate = self.base / 'duplicate-signals.json'
        duplicate.write_bytes(b'{"a":1,"a":2}\n')
        before = self.snapshot()
        reads[:] = []

        def duplicate_read(path):
            reads.append(path)
            if path != duplicate:
                raise AssertionError('unexpected file read: %s' % path)
            return original_read(path)

        with mock.patch.object(
                notes.Path, 'read_bytes', autospec=True,
                side_effect=duplicate_read):
            code, stdout = self.run_main(
                'list-key', '--visual-key', 'bad-file',
                '--signals', '@' + str(duplicate))
        self.assertEqual(code, 2)
        self.assertEqual(stdout, '')
        self.assertEqual(reads, [duplicate])
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
