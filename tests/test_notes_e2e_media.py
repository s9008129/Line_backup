"""Offline end-to-end tests through NotesRecords production verifiers."""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest import mock
import zlib

from line_backup_batch import media_verify, notes
from line_backup_batch.notes import (
    LOCAL_VERIFIED,
    PHOTO,
    VIDEO,
    NotesCollection,
    NotesError,
    NotesRecords,
)


ROOT = Path(__file__).resolve().parents[1]
SWIFT_DECODER_SOURCE = ROOT / 'src/line_backup_batch/image_decode.swift'
FFMPEG = Path('/opt/homebrew/bin/ffmpeg')
FFPROBE = Path('/opt/homebrew/bin/ffprobe')


def png(color=(255, 0, 0)):
    def chunk(name, data):
        return (struct.pack('>I', len(data)) + name + data +
                struct.pack('>I', zlib.crc32(name + data) & 0xffffffff))

    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * 2) * 2)) +
            chunk(b'IEND', b''))


class NotesE2EMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = tempfile.TemporaryDirectory(
            prefix='.line-notes-e2e-tests-', dir=str(ROOT))
        cls.fixture_root = Path(cls.fixtures.name).resolve()
        try:
            cls._require_video_pair()
            cls.decoder = cls._build_decoder()
            cls.decoder_sha256 = hashlib.sha256(
                cls.decoder.read_bytes()).hexdigest()
            cls.video = cls.fixture_root / 'valid.mp4'
            cls._generate_video(cls.video)
            raw = cls.video.read_bytes()
            cls.truncated_video = cls.fixture_root / 'truncated.mp4'
            cls.truncated_video.write_bytes(raw[:max(1, len(raw) // 2)])
        except Exception:
            cls.fixtures.cleanup()
            cls.fixtures = None
            raise

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, 'fixtures', None) is not None:
            cls.fixtures.cleanup()

    @classmethod
    def _require_video_pair(cls):
        if not FFMPEG.is_file() or not FFPROBE.is_file():
            raise unittest.SkipTest(
                'pinned Homebrew ffmpeg/ffprobe pair is unavailable')
        try:
            tools = media_verify.inspect_video_tools()
        except media_verify.MediaVerificationError as exc:
            raise unittest.SkipTest(
                'pinned video tools unavailable: {}'.format(exc))
        if (tools['ffmpeg']['configured_path'] != str(notes.FFMPEG) or
                tools['ffprobe']['configured_path'] != str(notes.FFPROBE)):
            raise AssertionError('production video tool paths are not pinned')
        cls.video_tools = tools

    @classmethod
    def _build_decoder(cls):
        if not SWIFT_DECODER_SOURCE.is_file():
            raise unittest.SkipTest('Swift ImageIO decoder source is unavailable')
        decoder = cls.fixture_root / 'image_decode'
        sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
        sdk_args = ['-sdk', str(sdk)] if sdk.exists() else []
        try:
            result = subprocess.run(
                ['xcrun', 'swiftc', *sdk_args, str(SWIFT_DECODER_SOURCE),
                 '-o', str(decoder)],
                capture_output=True, text=True)
        except OSError as exc:
            raise unittest.SkipTest(
                'Swift compiler unavailable: {}'.format(exc))
        if result.returncode:
            raise unittest.SkipTest(
                'Swift decoder cannot be built: {}'.format(result.stderr[:500]))
        if not decoder.is_file() or not decoder.stat().st_mode & 0o111:
            raise unittest.SkipTest('Swift decoder output is not executable')
        return decoder

    @classmethod
    def _generate_video(cls, path):
        command = [
            str(FFMPEG), '-nostdin', '-hide_banner', '-loglevel', 'error',
            '-f', 'lavfi', '-i', 'color=c=red:s=64x64:d=1:r=10',
            '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=1',
            '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-movflags', '+faststart', str(path),
        ]
        try:
            result = subprocess.run(command, capture_output=True)
        except OSError as exc:
            raise unittest.SkipTest(
                'fixed ffmpeg fixture generation unavailable: {}'.format(exc))
        if result.returncode:
            raise unittest.SkipTest(
                'fixed ffmpeg fixture generation failed: {}'.format(
                    result.stderr.decode('utf-8', 'replace')[:500]))
        if not path.is_file() or path.stat().st_size <= 0:
            raise unittest.SkipTest('ffmpeg did not produce a video fixture')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            prefix='.line-notes-e2e-tests-', dir=str(ROOT))
        self.base = Path(self.temp.name).resolve()
        self.evidence = self.base / 'synthetic-evidence.txt'
        self.evidence.write_bytes(b'synthetic notes e2e evidence')
        self.photo_root = self.base / 'photos'
        self.collection_path = self.base / 'records'
        self.collection = NotesCollection(str(self.collection_path))
        self.session = 'e2e-session-1'
        self.active_patch = mock.patch.object(
            notes, '_write_active_hint', return_value=None)
        self.active_patch.start()
        self.records, self.memory = self._new_ledger('e2e-list-1')

    def tearDown(self):
        self.active_patch.stop()
        self.temp.cleanup()

    def _new_ledger(self, visual_key):
        memory = self.collection.create(
            photo_root=str(self.photo_root),
            display_name='E2E Notes ' + visual_key,
            identity=notes.list_identity(visual_key=visual_key),
            binding_evidence=str(self.evidence),
            history_scope_evidence=str(self.evidence))
        records = NotesRecords(memory['records_root'])
        records.bind(session_id=self.session,
                     observation=str(self.evidence),
                     handoff=str(self.evidence))
        return records, memory

    def _observe_post(self, visual_key, media_identities):
        post = notes.post_identity(visual_key=visual_key)
        post_key_value = notes.post_key(
            self.memory['list_key'], post)
        scan = self.records.scan(
            session_id=self.session, action='START',
            evidence=str(self.evidence))
        self.records.page(
            session_id=self.session, scan_id=scan['scan_id'], page_index=0,
            posts=[dict(identity=post, date_summary='2026-10-31')],
            top_reached=True, bottom_reached=True, overlap_keys=[],
            evidence=str(self.evidence))
        self.records.scan(
            session_id=self.session, action='FINISH',
            scan_id=scan['scan_id'], evidence=str(self.evidence))
        self.records.record_post(
            session_id=self.session, post_key_value=post_key_value,
            date_summary='2026-10-31', media_count=len(media_identities),
            text_sha256=None, evidence=str(self.evidence),
            no_media=not media_identities)
        if media_identities:
            self.records.record_media(
                session_id=self.session, post_key_value=post_key_value,
                items=[dict(identity=identity)
                       for identity in media_identities],
                missing=[], evidence=str(self.evidence))
        return post_key_value

    def _download_finished(self, media_key_value, filename, payload):
        attempt = self.records.intent(
            session_id=self.session, media_key_value=media_key_value)
        staging = Path(attempt['destination'])
        self.assertTrue(staging.is_dir())
        self.assertEqual(list(staging.iterdir()), [])
        staged = staging / filename
        staged.write_bytes(payload)
        self.records.outcome(
            session_id=self.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED', evidence=str(self.evidence))
        return attempt, staging, staged

    def _verify(self, attempt, progress=None):
        kind = attempt['identity']['kind']
        kwargs = dict(
            session_id=self.session,
            attempt_id=attempt['attempt_id'],
            stability_interval=0,
            stall_seconds=30,
        )
        if kind == PHOTO:
            kwargs.update(decoder=str(self.decoder),
                          decoder_sha256=self.decoder_sha256)
        if progress is not None:
            kwargs['progress_callback'] = progress.append
        return self.records.verify(**kwargs)

    def _event_bytes(self):
        return {path.name: path.read_bytes()
                for path in (self.records.records / 'events').iterdir()}

    def test_two_photos_one_video_use_production_verifiers(self):
        photos = [
            notes.media_identity(kind=PHOTO, visual_key='photo-red'),
            notes.media_identity(kind=PHOTO, visual_key='photo-green'),
        ]
        video = notes.media_identity(kind=VIDEO, visual_key='video-audio')
        identities = [photos[0], photos[1], video]
        post_key_value = self._observe_post('post-mixed-media', identities)
        keys = [notes.media_key(self.memory['list_key'], post_key_value,
                                identity)
                for identity in identities]

        photo_completions = []
        for key, filename, payload in (
                (keys[0], 'photo-red.png', png((255, 0, 0))),
                (keys[1], 'photo-green.png', png((0, 255, 0)))):
            attempt, staging, staged = self._download_finished(
                key, filename, payload)
            completion = self._verify(attempt)
            self.assertFalse(staging.exists())
            self.assertFalse(staged.exists())
            photo_completions.append(completion)

        video_progress = []
        video_attempt, video_staging, video_source = self._download_finished(
            keys[2], 'clip.mp4', self.video.read_bytes())
        video_completion = self._verify(video_attempt,
                                        progress=video_progress)
        self.assertFalse(video_staging.exists())
        self.assertFalse(video_source.exists())

        for completion, key in zip(photo_completions, keys[:2]):
            verification = completion['data']['verification']
            self.assertEqual(completion['kind'], 'completion')
            self.assertEqual(completion['data']['media_key'], key)
            self.assertEqual(verification['verifier'], 'IMAGEIO')
            self.assertEqual(verification['returncode'], 0)
            self.assertEqual(verification['result']['verdict'], 'PASS')
            self.assertEqual(verification['result']['expected'], 1)
            self.assertEqual(verification['result']['actualEntries'], 1)
            self.assertTrue(verification['result']['entries'][0]['decoded'])

        video_verification = video_completion['data']['verification']
        self.assertEqual(video_completion['kind'], 'completion')
        self.assertEqual(video_completion['data']['media_key'], keys[2])
        self.assertEqual(video_verification['verifier'],
                         'FFMPEG_NULL_DECODE')
        self.assertTrue(video_verification['completed'])
        self.assertEqual(video_verification['valid_video_streams'], 1)
        self.assertEqual(
            {row['codec_type'] for row in video_verification['decoded_streams']},
            {'video', 'audio'})
        self.assertTrue(video_progress)
        self.assertTrue(any(row.get('key') == 'progress' and
                            row.get('value') == 'end'
                            for row in video_progress))
        for name, path, sha256 in (
                ('ffmpeg', FFMPEG, media_verify.FFMPEG_SHA256),
                ('ffprobe', FFPROBE, media_verify.FFPROBE_SHA256)):
            tool = video_verification['tools'][name]
            self.assertEqual(tool['path'], str(path))
            self.assertEqual(tool['sha256'], sha256)
            self.assertTrue(tool['version']['first_line'].startswith(
                name + ' version 7.1.1'))
        self.assertEqual(video_verification['tools']['ffmpeg']['path'],
                         str(notes.FFMPEG))
        self.assertEqual(video_verification['tools']['ffprobe']['path'],
                         str(notes.FFPROBE))

        post_directory = Path(video_completion['data']['destination'])
        self.assertEqual(
            sorted(path.name for path in post_directory.iterdir()),
            ['media_001.png', 'media_002.png', 'media_003.mp4'])

        reopened = NotesRecords(str(self.records.records))
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 3)
        self.assertEqual(summary['local_counts'][LOCAL_VERIFIED], 3)
        self.assertTrue(summary['all_known_media_complete'])
        self.assertEqual(summary['dispatch_blockers'], [])
        self.assertFalse(summary['external_copy_verified'])
        self.assertEqual(summary['real_line_e2e'], 'NOT_TESTED')
        self.assertEqual(sum(row['status'] == 'COMPLETED'
                             for row in summary['media']), 3)

        completion_events = [event for event in reopened.events
                             if event['kind'] == 'completion']
        self.assertEqual(len(completion_events), 3)
        for event in completion_events:
            data = event['data']
            verification_event = next(
                candidate for candidate in reopened.events
                if candidate['kind'] == 'verification' and
                candidate['data']['attempt_id'] == data['attempt_id'])
            self.assertEqual(data['verification'],
                             verification_event['data']['verification'])
            self.assertEqual(data['source_manifest'],
                             verification_event['data']['manifest'][0])
            target = Path(data['destination']) / data['target_file']['name']
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),
                             data['source_manifest']['sha256'])

    def test_truncated_video_fails_without_events_or_staging_upgrade(self):
        identity = notes.media_identity(
            kind=VIDEO, visual_key='truncated-video')
        post_key_value = self._observe_post(
            'post-truncated-video', [identity])
        key = notes.media_key(
            self.memory['list_key'], post_key_value, identity)
        attempt, staging, staged = self._download_finished(
            key, 'truncated.mp4', self.truncated_video.read_bytes())
        before_events = self._event_bytes()
        before_staged = staged.read_bytes()

        with self.assertRaises(NotesError) as raised:
            self._verify(attempt)
        self.assertTrue(raised.exception.args)
        self.assertNotIn('VIDEO_TOOLCHAIN_MISSING', raised.exception.args[0])
        self.assertEqual(self._event_bytes(), before_events)
        self.assertTrue(staging.is_dir())
        self.assertEqual(sorted(path.name for path in staging.iterdir()),
                         ['truncated.mp4'])
        self.assertEqual(staged.read_bytes(), before_staged)

        reopened = NotesRecords(str(self.records.records))
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 0)
        self.assertEqual(summary['status_counts']['PENDING'], 1)
        self.assertIn('VERIFY_REQUIRED', summary['dispatch_blockers'])
        self.assertNotIn('completion',
                         [event['kind'] for event in reopened.events])


if __name__ == '__main__':
    unittest.main()
