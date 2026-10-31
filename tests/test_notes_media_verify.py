"""Synthetic offline verification tests; no LINE, GUI, or private media."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import zlib

from line_backup_batch import media_verify
from line_backup_batch.media_verify import (
    FFMPEG_PATH,
    FFPROBE_PATH,
    MediaVerificationError,
    inspect_video_tools,
    run_decode_command,
    verify_photo,
    verify_video,
)


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DECODER_SOURCE = ROOT / 'src/line_backup_batch/image_decode.swift'


def png(color=(255, 0, 0)):
    def chunk(name, data):
        return (struct.pack('>I', len(data)) + name + data +
                struct.pack('>I', zlib.crc32(name + data) & 0xffffffff))

    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * 2) * 2)) +
            chunk(b'IEND', b''))


class PhotoVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = tempfile.TemporaryDirectory(
            prefix='.line-notes-photo-tests-', dir=ROOT)
        cls.tools = tempfile.TemporaryDirectory(
            prefix='decoder-', dir=cls.fixtures.name)
        cls.decoder = (Path(cls.tools.name).resolve() / 'image_decode')
        sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
        sdk_args = ['-sdk', str(sdk)] if sdk.exists() else []
        try:
            result = subprocess.run(
                ['xcrun', 'swiftc', *sdk_args, str(IMAGE_DECODER_SOURCE),
                 '-o', str(cls.decoder)],
                capture_output=True, text=True)
        except OSError as exc:
            cls.tools.cleanup()
            cls.fixtures.cleanup()
            raise unittest.SkipTest('Swift compiler unavailable: {}'.format(exc))
        if result.returncode:
            cls.tools.cleanup()
            cls.fixtures.cleanup()
            raise unittest.SkipTest(
                'Swift decoder cannot be built in this environment: {}'.format(
                    result.stderr[:500]))
        cls.decoder_sha = hashlib.sha256(
            cls.decoder.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.tools.cleanup()
        cls.fixtures.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            prefix='case-', dir=self.fixtures.name)
        self.base = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def verify(self, path):
        return verify_photo(
            path, str(self.decoder), self.decoder_sha,
            stable_interval=0, stable_samples=3)

    def decoder_evidence_runner(self, *, expected=1, actual_entries=1):
        def runner(command, **kwargs):
            isolated = Path(command[1])
            target = next(isolated.iterdir())
            payload = {
                'verdict': 'PASS',
                'readOnly': True,
                'destination': str(isolated),
                'expected': expected,
                'actualEntries': actual_entries,
                'entries': [{
                    'name': target.name,
                    'decoded': True,
                    'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                    'width': 2,
                    'height': 2,
                }],
            }
            return subprocess.CompletedProcess(
                command, 0, json.dumps(payload).encode('utf-8'), b'')
        return runner

    def test_valid_photo_full_decode_and_single_file_isolation(self):
        target = self.base / 'photo.png'
        target.write_bytes(png())
        sibling = self.base / 'sibling.jpg'
        sibling.write_bytes(b'not an image and must not enter isolation')

        result = self.verify(target)

        self.assertEqual(result['verdict'], 'PASS')
        self.assertEqual(result['kind'], 'PHOTO')
        self.assertEqual(result['isolation']['entry_count'], 1)
        self.assertEqual(result['isolation']['entry_name'], 'photo.png')
        self.assertEqual(result['manifest'][0]['sha256'],
                         hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(len(result['stable_samples']), 3)
        self.assertTrue(result['imageio']['entries'][0]['decoded'])
        self.assertEqual(result['imageio']['actualEntries'], 1)
        self.assertFalse(result['dispatch_authorized'])

    def test_invalid_sibling_is_not_seen_when_target_is_valid(self):
        target = self.base / 'only.png'
        target.write_bytes(png((0, 255, 0)))
        (self.base / 'broken.jpg').write_bytes(b'broken sibling')
        self.assertEqual(self.verify(target)['verdict'], 'PASS')

    def test_empty_photo_is_rejected(self):
        target = self.base / 'empty.png'
        target.write_bytes(b'')
        with self.assertRaises(MediaVerificationError) as raised:
            self.verify(target)
        self.assertEqual(raised.exception.code, 'EMPTY_MEDIA')

    def test_malformed_photo_fails_full_decode(self):
        target = self.base / 'malformed.png'
        target.write_bytes(b'not a decodable image')
        with self.assertRaises(MediaVerificationError) as raised:
            self.verify(target)
        self.assertIn(raised.exception.code,
                      {'IMAGEIO_DECODE_FAILED', 'INVALID_IMAGEIO_RESULT',
                       'IMAGEIO_CONTENT_MISMATCH', 'PHOTO_FORMAT_MISMATCH'})

    def test_photo_extension_must_match_magic_format(self):
        target = self.base / 'actually-png.jpg'
        target.write_bytes(png())

        with self.assertRaises(MediaVerificationError) as raised:
            self.verify(target)

        self.assertEqual(raised.exception.code, 'PHOTO_FORMAT_MISMATCH')
        self.assertEqual(raised.exception.evidence['expected_format'], 'jpeg')
        self.assertEqual(raised.exception.evidence['actual_format'], 'png')

    def test_symlink_photo_is_not_accepted(self):
        real = self.base / 'real.png'
        real.write_bytes(png())
        link = self.base / 'link.png'
        link.symlink_to(real)
        with self.assertRaises(MediaVerificationError) as raised:
            self.verify(link)
        self.assertIn(raised.exception.code,
                      {'CANONICAL_FILE_REQUIRED', 'SOURCE_SYMLINK_REFUSED'})

    def test_photo_drift_after_decode_is_rejected(self):
        target = self.base / 'drift.png'
        target.write_bytes(png((255, 0, 0)))

        def drifting_runner(command, **kwargs):
            result = subprocess.run(command, **kwargs)
            target.write_bytes(png((0, 0, 255)))
            return result

        with self.assertRaises(MediaVerificationError) as raised:
            verify_photo(target, str(self.decoder), self.decoder_sha,
                         stable_interval=0, stable_samples=2,
                         runner=drifting_runner)
        self.assertEqual(raised.exception.code, 'CONTENT_CHANGED_AFTER_DECODE')

    def test_decoder_actual_entries_bool_is_rejected(self):
        target = self.base / 'bool-actual.png'
        target.write_bytes(png())

        with self.assertRaises(MediaVerificationError) as raised:
            verify_photo(
                target, str(self.decoder), self.decoder_sha,
                stable_interval=0, stable_samples=2,
                runner=self.decoder_evidence_runner(actual_entries=True))

        self.assertEqual(raised.exception.code, 'IMAGEIO_BINDING_MISMATCH')
        self.assertIsInstance(raised.exception.evidence, dict)
        self.assertIn('command', raised.exception.evidence)

    def test_decoder_expected_float_is_rejected(self):
        target = self.base / 'float-expected.png'
        target.write_bytes(png())

        with self.assertRaises(MediaVerificationError) as raised:
            verify_photo(
                target, str(self.decoder), self.decoder_sha,
                stable_interval=0, stable_samples=2,
                runner=self.decoder_evidence_runner(expected=1.0))

        self.assertEqual(raised.exception.code, 'IMAGEIO_BINDING_MISMATCH')
        self.assertIsInstance(raised.exception.evidence, dict)
        self.assertIn('command', raised.exception.evidence)


class VideoVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (FFMPEG_PATH.is_file() and FFPROBE_PATH.is_file()):
            raise unittest.SkipTest(
                'pinned Homebrew ffmpeg/ffprobe pair is unavailable')
        try:
            cls.tools = inspect_video_tools()
        except MediaVerificationError as exc:
            raise unittest.SkipTest('pinned video tools unavailable: {}'.format(exc))
        cls.fixtures = tempfile.TemporaryDirectory(
            prefix='line-notes-video-tests-')
        cls.root = Path(cls.fixtures.name).resolve()
        try:
            cls.generate_fixtures()
        except Exception:
            cls.fixtures.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.fixtures.cleanup()

    @classmethod
    def ffmpeg(cls, *args):
        result = subprocess.run(
            [str(FFMPEG_PATH), '-nostdin', '-hide_banner', '-loglevel', 'error',
             *args], capture_output=True)
        if result.returncode:
            raise unittest.SkipTest(
                'ffmpeg fixture generation failed: {}'.format(
                    result.stderr.decode('utf-8', 'replace')[:500]))

    @classmethod
    def generate_fixtures(cls):
        cls.av = cls.root / 'with-audio.mp4'
        cls.silent = cls.root / 'silent.mp4'
        cls.audio_only = cls.root / 'audio-only.m4a'
        cls.truncated = cls.root / 'truncated.mp4'
        cls.bad_frames = cls.root / 'bad-frames.mp4'
        common = ['-f', 'lavfi', '-i', 'color=c=red:s=64x64:d=1:r=10']
        cls.ffmpeg(*common, '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=1',
                   '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                   '-c:a', 'aac', '-movflags', '+faststart', str(cls.av))
        cls.ffmpeg(*common, '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                   '-movflags', '+faststart', str(cls.silent))
        cls.ffmpeg('-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
                   '-c:a', 'aac', str(cls.audio_only))
        raw = cls.av.read_bytes()
        cls.truncated.write_bytes(raw[:max(1, len(raw) // 2)])
        marker = raw.find(b'mdat')
        if marker >= 0:
            damaged = bytearray(raw)
            for index in range(marker + 8, len(damaged)):
                damaged[index] = 0
            cls.bad_frames.write_bytes(damaged)
        else:
            cls.bad_frames.write_bytes(cls.av.read_bytes()[:1])

    def test_tools_are_the_fixed_pair_and_record_versions_and_hashes(self):
        tools = inspect_video_tools()
        self.assertEqual(tools['ffmpeg']['configured_path'], str(FFMPEG_PATH))
        self.assertEqual(tools['ffprobe']['configured_path'], str(FFPROBE_PATH))
        self.assertEqual(tools['ffmpeg']['sha256'], media_verify.FFMPEG_SHA256)
        self.assertEqual(tools['ffprobe']['sha256'], media_verify.FFPROBE_SHA256)
        self.assertEqual(tools['ffmpeg']['version'], '7.1.1')
        self.assertEqual(tools['ffprobe']['version'], '7.1.1')

    def test_pinned_hash_mismatch_fails_closed(self):
        with mock.patch.dict(
                media_verify.VIDEO_TOOL_PINS['ffmpeg'],
                {'sha256': '0' * 64}):
            with self.assertRaises(MediaVerificationError) as raised:
                inspect_video_tools()
        self.assertEqual(raised.exception.code, 'VIDEO_TOOL_SHA256_MISMATCH')

    def test_audio_and_silent_video_decode_every_av_stream(self):
        for path, expected_types in (
                (self.av, {'video', 'audio'}),
                (self.silent, {'video'})):
            with self.subTest(path=path.name):
                result = verify_video(path, stable_interval=0, stable_samples=3)
                self.assertEqual(result['verdict'], 'PASS')
                self.assertEqual(
                    {row['stream']['codec_type'] for row in result['streams']},
                    expected_types)
                self.assertEqual(len(result['streams']),
                                 result['all_audio_video_streams_decoded'])
                for row in result['streams']:
                    self.assertTrue(row['coverage']['duration_covered'])
                    self.assertTrue(row['coverage']['frames_covered'])
                    self.assertEqual(row['decode']['progress']['final_progress'], 'end')
                    self.assertEqual(row['decode']['exit_code'], 0)
                    self.assertTrue(row['decode']['stderr_empty'])

    def test_audio_only_is_not_a_valid_video(self):
        with self.assertRaises(MediaVerificationError) as raised:
            verify_video(self.audio_only, stable_interval=0, stable_samples=2)
        self.assertEqual(raised.exception.code, 'NO_VIDEO_STREAM')

    def test_truncated_video_never_passes(self):
        with self.assertRaises(MediaVerificationError) as raised:
            verify_video(self.truncated, stable_interval=0, stable_samples=2)
        self.assertIn(raised.exception.code,
                      {'PROBE_FAILED', 'PROBE_STDERR', 'INVALID_PROBE_JSON',
                       'DECODE_NONZERO_EXIT', 'DECODE_STDERR',
                       'DURATION_COVERAGE_SHORT', 'FRAME_COVERAGE_SHORT'})

    def test_corrupt_frames_never_pass(self):
        with self.assertRaises(MediaVerificationError) as raised:
            verify_video(self.bad_frames, stable_interval=0, stable_samples=2)
        self.assertFalse(getattr(raised.exception, 'evidence', {}).get('verdict') == 'PASS')

    def test_duplicate_probe_json_keys_are_rejected(self):
        real_run = subprocess.run

        def duplicate_runner(command, **kwargs):
            if command[-1] == str(self.silent):
                return subprocess.CompletedProcess(
                    command, 0,
                    b'{"format":{},"streams":[],"streams":[]}', b'')
            return real_run(command, **kwargs)

        with self.assertRaises(MediaVerificationError) as raised:
            verify_video(self.silent, stable_interval=0, stable_samples=2,
                         runner=duplicate_runner)
        self.assertEqual(raised.exception.code, 'INVALID_PROBE_JSON')

    def test_decode_nonzero_exit_is_fail_closed(self):
        script = ('import sys\n'
                  "sys.stdout.write('frame=1\\nprogress=end\\n')\n"
                  "sys.stdout.flush()\n"
                  "sys.stderr.write('synthetic decode failure\\n')\n"
                  "sys.stderr.flush()\n"
                  "sys.exit(1)\n")

        def failing_popen(_command, **kwargs):
            return subprocess.Popen([sys.executable, '-c', script], **kwargs)

        with self.assertRaises(MediaVerificationError) as raised:
            verify_video(self.silent, stable_interval=0, stable_samples=2,
                         popen_factory=failing_popen)
        self.assertEqual(raised.exception.code, 'DECODE_NONZERO_EXIT')

    def test_stall_watchdog_kills_without_writing_pass(self):
        script = ('import sys,time\n'
                  "sys.stdout.write('frame=1\\nprogress=continue\\n')\n"
                  "sys.stdout.flush()\n"
                  "time.sleep(10)\n")
        started = time.monotonic()
        with self.assertRaises(MediaVerificationError) as raised:
            run_decode_command(
                [sys.executable, '-c', script], stream_index=0,
                stall_timeout=0.2)
        elapsed = time.monotonic() - started
        self.assertEqual(raised.exception.code, 'DECODE_STALLED')
        self.assertLess(elapsed, 5)
        self.assertNotEqual(raised.exception.evidence.get('verdict'), 'PASS')
        self.assertEqual(raised.exception.evidence['progress']['count'], 1)

    def test_repeated_identical_heartbeat_does_not_extend_watchdog(self):
        script = ('import sys,time\n'
                  "for _ in range(200):\n"
                  "    sys.stdout.write('frame=1\\nout_time_us=100000\\nprogress=continue\\n')\n"
                  "    sys.stdout.flush()\n"
                  "    time.sleep(0.01)\n")
        started = time.monotonic()
        with self.assertRaises(MediaVerificationError) as raised:
            run_decode_command(
                [sys.executable, '-c', script], stream_index=0,
                stall_timeout=0.25)
        elapsed = time.monotonic() - started

        self.assertEqual(raised.exception.code, 'DECODE_STALLED')
        self.assertLess(elapsed, 2)
        self.assertGreater(raised.exception.evidence['progress']['count'], 1)

    def test_strictly_advancing_progress_extends_watchdog(self):
        script = ('import sys,time\n'
                  "for index in range(1, 6):\n"
                  "    sys.stdout.write('frame={}\\nout_time_us={}\\nprogress=continue\\n'.format(index, index * 100000))\n"
                  "    sys.stdout.flush()\n"
                  "    time.sleep(0.15)\n"
                  "sys.stdout.write('frame=6\\nout_time_us=600000\\nprogress=end\\n')\n"
                  "sys.stdout.flush()\n")
        evidence = run_decode_command(
            [sys.executable, '-c', script], stream_index=0,
            stall_timeout=0.35)

        self.assertEqual(evidence['exit_code'], 0)
        self.assertEqual(evidence['progress']['count'], 6)
        self.assertEqual(evidence['progress']['final_progress'], 'end')

    def synthetic_probe_runner(self, payload):
        real_run = subprocess.run

        def runner(command, **kwargs):
            if command[-1] == str(self.silent):
                return subprocess.CompletedProcess(command, 0, payload, b'')
            return real_run(command, **kwargs)

        return runner

    def test_huge_duration_ts_or_time_base_fails_closed(self):
        huge = '9' * 400
        cases = {
            'huge_duration_ts': {'duration_ts': huge, 'time_base': '1/1'},
            'huge_time_base': {'duration_ts': '1', 'time_base': huge + '/1'},
        }
        for label, timing in cases.items():
            with self.subTest(label=label):
                stream = {
                    'index': 0,
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 64,
                    'height': 64,
                    'disposition': {'attached_pic': 0},
                }
                stream.update(timing)
                payload = json.dumps({
                    'format': {'format_name': 'mov,mp4,m4a,3gp,3g2,mj2'},
                    'streams': [stream],
                }).encode('utf-8')

                with self.assertRaises(MediaVerificationError) as raised:
                    verify_video(
                        self.silent, stable_interval=0, stable_samples=2,
                        runner=self.synthetic_probe_runner(payload))

                self.assertEqual(raised.exception.code, 'INVALID_STREAM_DURATION')

    def test_probe_integer_fields_reject_bool_and_float(self):
        cases = (
            ({'disposition': {'attached_pic': True}},
             'INVALID_STREAM_DISPOSITION'),
            ({'nb_frames': 1.0}, 'INVALID_STREAM_FRAME_COUNT'),
            ({'duration_ts': 1.0, 'time_base': '1/1'},
             'INVALID_STREAM_DURATION'),
        )
        for extra, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                stream = {
                    'index': 0,
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 64,
                    'height': 64,
                    'disposition': {'attached_pic': 0},
                }
                stream.update(extra)
                payload = json.dumps({
                    'format': {'format_name': 'mov,mp4,m4a,3gp,3g2,mj2'},
                    'streams': [stream],
                }).encode('utf-8')

                with self.assertRaises(MediaVerificationError) as raised:
                    verify_video(
                        self.silent, stable_interval=0, stable_samples=2,
                        runner=self.synthetic_probe_runner(payload))

                self.assertEqual(raised.exception.code, expected_code)

    def test_container_format_must_match_extension(self):
        payload = json.dumps({
            'format': {'format_name': 'matroska,webm'},
            'streams': [{
                'index': 0,
                'codec_type': 'video',
                'codec_name': 'h264',
                'width': 64,
                'height': 64,
                'disposition': {'attached_pic': 0},
                'duration': '1.0',
                'nb_frames': '10',
            }],
        }).encode('utf-8')

        def forbidden_popen(*_args, **_kwargs):
            self.fail('decode started after a container-format mismatch')

        with self.assertRaises(MediaVerificationError) as raised:
            verify_video(
                self.silent, stable_interval=0, stable_samples=2,
                runner=self.synthetic_probe_runner(payload),
                popen_factory=forbidden_popen)

        self.assertEqual(raised.exception.code, 'CONTAINER_FORMAT_MISMATCH')
        self.assertEqual(raised.exception.evidence['suffix'], '.mp4')
        self.assertEqual(raised.exception.evidence['format_name'], 'matroska,webm')

    def test_container_aliases_accept_supported_extensions(self):
        cases = {
            '.mp4': 'mov,mp4,m4a,3gp,3g2,mj2',
            '.mov': 'mov,mp4,m4a,3gp,3g2,mj2',
            '.m4v': 'mov,mp4,m4a,3gp,3g2,mj2',
            '.avi': 'avi',
            '.mkv': 'matroska,webm',
        }
        for suffix, format_name in cases.items():
            with self.subTest(suffix=suffix):
                result = media_verify._validate_container_format(
                    Path('probe' + suffix),
                    {'format': {'format_name': format_name}})
                self.assertEqual(result['suffix'], suffix)

    def test_progress_callback_receives_continuous_events(self):
        script = ('import sys\n'
                  "sys.stdout.write('frame=1\\nout_time_us=100000\\nprogress=continue\\n')\n"
                  "sys.stdout.write('frame=2\\nout_time_us=200000\\nprogress=continue\\n')\n"
                  "sys.stdout.write('frame=2\\nout_time_us=200000\\nprogress=end\\n')\n")
        seen = []
        evidence = run_decode_command(
            [sys.executable, '-c', script], stream_index=4,
            stall_timeout=2, progress_callback=seen.append)
        self.assertEqual(evidence['progress']['count'], 3)
        self.assertEqual([row['stream_index'] for row in seen], [4, 4, 4])

    def test_progress_end_alone_is_not_success(self):
        script = "import sys; sys.stdout.write('progress=end\\n')"
        with self.assertRaises(MediaVerificationError) as raised:
            run_decode_command([sys.executable, '-c', script], stream_index=0,
                               stall_timeout=2)
        self.assertEqual(raised.exception.code, 'DECODE_PROGRESS_WITHOUT_METRICS')

    def test_progress_without_end_is_not_success(self):
        script = ("import sys; sys.stdout.write('frame=1\\nout_time_us=1\\n"
                  "progress=continue\\n')")
        with self.assertRaises(MediaVerificationError) as raised:
            run_decode_command([sys.executable, '-c', script], stream_index=0,
                               stall_timeout=2)
        self.assertEqual(raised.exception.code, 'DECODE_PROGRESS_NOT_EOF')


if __name__ == '__main__':
    unittest.main()
