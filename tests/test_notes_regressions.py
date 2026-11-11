"""Synthetic regressions for Notes ledger and decode fail-closed boundaries.

These tests use only generated records and local process fixtures. They do not
observe LINE, operate a GUI, or touch private media or permanent ledgers.
"""
import contextlib
import copy
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock
import uuid

from line_backup_batch import media_verify, notes, notes_evidence
from line_backup_batch.daily import digest, encoded
from line_backup_batch.media_verify import (
    MediaVerificationError,
    run_decode_command,
)
from line_backup_batch.notes import (
    PHOTO,
    VIDEO,
    NotesCollection,
    NotesError,
    NotesRecords,
)


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TASKS = ROOT / '.local' / 'line-backup' / 'tasks'
STRICT_VERIFY_SIGNATURE = inspect.signature(media_verify.verify_media)


class _Ledger(SimpleNamespace):
    def evidence(self, **context):
        context = {key: value for key, value in context.items()
                   if value is not None and value != 'UNKNOWN'}
        output = self.evidence_packs / uuid.uuid4().hex
        return notes_evidence.create_bundle(
            statement=str(self.evidence_source),
            assets=[('screenshot', str(self.evidence_screenshot))],
            context=context,
            output_dir=str(output))['bundle_path']

    def evidence_for_attempt(self, attempt):
        return self.evidence(
            list_key=self.summary['list_key'], post_key=attempt['post_key'],
            media_key=attempt['media_key'],
            attempt_id=attempt['attempt_id'], scan_id=attempt.get('scan_id'))

    def evidence_for_media(self, media_key_value):
        return self.evidence(**self.records._media_evidence_context(
            media_key_value))

    def stored_evidence_for_attempt(self, attempt):
        context = self.records._intent_evidence_context(attempt['attempt_id'])
        return notes._preserve_evidence(
            self.records.records, self.evidence_for_attempt(attempt), context)

    def stored_evidence_for_media(self, media_key_value):
        context = self.records._media_evidence_context(media_key_value)
        return notes._preserve_evidence(
            self.records.records, self.evidence(**context), context)

    def evidence_for_scan(self, scan_id=None):
        return self.evidence(list_key=self.summary['list_key'],
                             scan_id=scan_id)

    def evidence_for_post(self, post_key_value):
        latest, _scans = self.records._open_scan()
        return self.evidence(list_key=self.summary['list_key'],
                             post_key=post_key_value, scan_id=latest)


class _EofThenHangs:
    """Process double: stdout closes while the child remains alive."""

    def __init__(self, command, **_kwargs):
        read_fd, write_fd = os.pipe()
        try:
            os.write(
                write_fd,
                b'frame=1\nout_time_us=100000\nprogress=continue\n',
            )
        finally:
            os.close(write_fd)
        self.args = command
        self.stdout = os.fdopen(read_fd, 'rb', buffering=0)
        self._stopped = False

    def poll(self):
        return -15 if self._stopped else None

    def wait(self, timeout=None):
        if self._stopped:
            return -15
        if timeout is None:
            raise AssertionError('unbounded wait after stdout EOF')
        deadline = time.monotonic() + timeout
        while not self._stopped and time.monotonic() < deadline:
            time.sleep(0.005)
        if self._stopped:
            return -15
        raise subprocess.TimeoutExpired(self.args, timeout)

    def terminate(self):
        self._stopped = True

    def kill(self):
        self._stopped = True


class NotesRegressionTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='.line-notes-regressions-', dir=str(PRIVATE_TASKS))
        self.base = Path(self.temporary.name).resolve()
        self.active_patch = mock.patch.object(
            notes, '_write_active_hint', return_value=None)
        self.active_patch.start()

    def tearDown(self):
        self.active_patch.stop()
        self.temporary.cleanup()

    def new_ledger(self, label, *, recovery_authorized=True):
        case = self.base / label
        case.mkdir()
        evidence = case / 'synthetic-evidence.txt'
        evidence.write_bytes(b'synthetic notes evidence\n')
        screenshot = case / 'synthetic-screenshot.txt'
        screenshot.write_bytes(b'synthetic notes screenshot\n')
        evidence_packs = case / 'evidence-packs'
        evidence_packs.mkdir()
        photo_root = case / 'photos'
        collection_path = case / 'records'
        collection = NotesCollection(str(collection_path))
        list_key_value = notes.list_key(
            notes.list_identity(visual_key='list-' + label))
        context = dict(list_key=list_key_value)
        binding_evidence = notes_evidence.create_bundle(
            statement=str(evidence),
            assets=[('screenshot', str(screenshot))],
            context=context,
            output_dir=str(evidence_packs / uuid.uuid4().hex))['bundle_path']
        history_evidence = notes_evidence.create_bundle(
            statement=str(evidence),
            assets=[('screenshot', str(screenshot))],
            context=context,
            output_dir=str(evidence_packs / uuid.uuid4().hex))['bundle_path']
        summary = collection.create(
            photo_root=str(photo_root),
            display_name='Synthetic ' + label,
            identity=notes.list_identity(visual_key='list-' + label),
            binding_evidence=binding_evidence,
            history_scope_evidence=history_evidence,
            recovery_authorized=recovery_authorized,
        )
        records = NotesRecords(
            summary['records_root'], _allow_injected_verification=True)
        session = 'session-' + label
        observation = notes_evidence.create_bundle(
            statement=str(evidence),
            assets=[('screenshot', str(screenshot))],
            context=context,
            output_dir=str(evidence_packs / uuid.uuid4().hex))['bundle_path']
        handoff = notes_evidence.create_bundle(
            statement=str(evidence),
            assets=[('screenshot', str(screenshot))],
            context=context,
            output_dir=str(evidence_packs / uuid.uuid4().hex))['bundle_path']
        records.bind(session_id=session,
                     observation=observation, handoff=handoff)
        return _Ledger(
            records=records,
            summary=summary,
            collection=collection,
            photo_root=photo_root,
            evidence_source=evidence,
            evidence_screenshot=screenshot,
            evidence_packs=evidence_packs,
            session=session,
        )

    def reopen(self, ledger):
        return NotesRecords(str(ledger.records.records),
                            _allow_injected_verification=True)

    def run_notes_cli(self, *args):
        output = io.StringIO()
        with mock.patch('sys.stdout', new=output):
            code = notes.main([str(value) for value in args])
        return code, json.loads(output.getvalue())

    def observe_post(self, ledger, visual_key, media_identities, *,
                     no_media=False, media_count=None):
        records = ledger.records
        session = ledger.session
        list_key_value = ledger.summary['list_key']
        evidence = ledger.evidence(list_key=list_key_value)
        post = notes.post_identity(visual_key=visual_key)
        post_key_value = notes.post_key(ledger.summary['list_key'], post)
        scan = records.scan(session_id=session, action='START', evidence=evidence)
        records.page(
            session_id=session,
            scan_id=scan['scan_id'],
            page_index=0,
            posts=[dict(identity=post, date_summary='synthetic')],
            top_reached=True,
            bottom_reached=True,
            overlap_keys=[],
            evidence=ledger.evidence(list_key=list_key_value,
                                     scan_id=scan['scan_id']),
        )
        records.scan(
            session_id=session,
            action='FINISH',
            scan_id=scan['scan_id'],
            evidence=ledger.evidence(list_key=list_key_value,
                                     scan_id=scan['scan_id']),
        )
        count = 0 if no_media else (
            len(media_identities) if media_count is None else media_count)
        records.record_post(
            session_id=session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=count,
            text_sha256=None,
            evidence=ledger.evidence(list_key=list_key_value,
                                     post_key=post_key_value,
                                     scan_id=scan['scan_id']),
            no_media=no_media,
        )
        if media_identities:
            records.record_media(
                session_id=session,
                post_key_value=post_key_value,
                items=[{'identity': identity} for identity in media_identities],
                missing=[],
                evidence=ledger.evidence(list_key=list_key_value,
                                         post_key=post_key_value,
                                         scan_id=scan['scan_id']),
            )
        return post, post_key_value

    def observe_without_detail(self, ledger, visual_key):
        records = ledger.records
        session = ledger.session
        list_key_value = ledger.summary['list_key']
        evidence = ledger.evidence(list_key=list_key_value)
        post = notes.post_identity(visual_key=visual_key)
        post_key_value = notes.post_key(ledger.summary['list_key'], post)
        scan = records.scan(session_id=session, action='START', evidence=evidence)
        records.page(
            session_id=session,
            scan_id=scan['scan_id'],
            page_index=0,
            posts=[dict(identity=post, date_summary='synthetic')],
            top_reached=True,
            bottom_reached=True,
            overlap_keys=[],
            evidence=ledger.evidence(list_key=list_key_value,
                                     scan_id=scan['scan_id']),
        )
        records.scan(
            session_id=session,
            action='FINISH',
            scan_id=scan['scan_id'],
            evidence=ledger.evidence(list_key=list_key_value,
                                     scan_id=scan['scan_id']),
        )
        return post_key_value

    def scan_with_pages(self, ledger, pages):
        records = ledger.records
        session = ledger.session
        list_key_value = ledger.summary['list_key']
        evidence = ledger.evidence(list_key=list_key_value)
        scan = records.scan(session_id=session, action='START', evidence=evidence)
        for page_index, (post_identities, overlap_identities) in enumerate(pages):
            records.page(
                session_id=session,
                scan_id=scan['scan_id'],
                page_index=page_index,
                posts=[dict(identity=identity, date_summary='synthetic')
                       for identity in post_identities],
                top_reached=page_index == 0,
                bottom_reached=page_index == len(pages) - 1,
                overlap_keys=[notes.post_key(ledger.summary['list_key'], identity)
                              for identity in overlap_identities],
                evidence=ledger.evidence(list_key=list_key_value,
                                         scan_id=scan['scan_id']),
            )
        records.scan(
            session_id=session, action='FINISH', scan_id=scan['scan_id'],
            evidence=ledger.evidence(list_key=list_key_value,
                                     scan_id=scan['scan_id']))
        return scan

    def append_historical_scan(self, ledger, post_identities):
        """Append a legacy scan graph directly after the public gates existed."""
        records = ledger.records
        list_key_value = ledger.summary['list_key']
        scan_id = uuid.uuid4().hex
        rows = [dict(post_key=notes.post_key(list_key_value, identity),
                     identity=identity, date_summary='synthetic',
                     source_order=index)
                for index, identity in enumerate(post_identities)]
        start_context = notes._evidence_context(list_key=list_key_value)
        scan_context = notes._evidence_context(
            list_key=list_key_value, scan_id=scan_id)
        records.append('scan', dict(
            schema='line-notes-scan/v1', action='START', scan_id=scan_id,
            session_id=ledger.session,
            evidence=notes._preserve_evidence(
                records.records,
                ledger.evidence(list_key=list_key_value),
                start_context)))
        records.append('page', dict(
            schema='line-notes-page/v1', scan_id=scan_id,
            session_id=ledger.session, page_index=0, top_reached=True,
            bottom_reached=True, overlap_keys=[], posts=rows,
            evidence=notes._preserve_evidence(
                records.records,
                ledger.evidence(list_key=list_key_value, scan_id=scan_id),
                scan_context)))
        records.append('scan', dict(
            schema='line-notes-scan/v1', action='COMPLETE', scan_id=scan_id,
            session_id=ledger.session, posts=rows,
            evidence=notes._preserve_evidence(
                records.records,
                ledger.evidence(list_key=list_key_value, scan_id=scan_id),
                scan_context)))
        return scan_id

    def mutate_page(self, ledger, page_index, post_identities,
                    overlap_identities):
        events = self.read_events(ledger.records)
        pages = [event for event in events if event['kind'] == 'page']
        page = pages[page_index]
        page['data']['posts'] = [
            dict(post_key=notes.post_key(ledger.summary['list_key'], identity),
                 identity=identity, date_summary='synthetic',
                 source_order=index)
            for index, identity in enumerate(post_identities)
        ]
        page['data']['overlap_keys'] = [
            notes.post_key(ledger.summary['list_key'], identity)
            for identity in overlap_identities
        ]
        self.rewrite_events(ledger.records, events)

    def media_key(self, ledger, post_key_value, identity):
        return notes.media_key(
            ledger.summary['list_key'], post_key_value, identity)

    @staticmethod
    def pass_verifier(_path, row, _identity):
        return dict(verdict='PASS', sha256=row['sha256'])

    def prepare_download(self, ledger, kind, label):
        identity = notes.media_identity(kind=kind, visual_key=label)
        _, post_key_value = self.observe_post(ledger, label, [identity])
        key = self.media_key(ledger, post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        staging = Path(attempt['destination'])
        filename = 'synthetic.png' if kind == PHOTO else 'synthetic.mp4'
        target = staging / filename
        target.write_bytes(('synthetic ' + label).encode('utf-8'))
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(attempt),
        )
        return identity, key, attempt, target

    def complete_media(self, ledger, kind, label, *, post_key_value=None,
                       identity=None):
        identity = identity or notes.media_identity(
            kind=kind, visual_key=label)
        if post_key_value is None:
            _, post_key_value = self.observe_post(ledger, label, [identity])
        key = self.media_key(ledger, post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        staging = Path(attempt['destination'])
        filename = 'complete.png' if kind == PHOTO else 'complete.mp4'
        (staging / filename).write_bytes(('complete ' + label).encode('utf-8'))
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(attempt),
        )
        completion = ledger.records.verify(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier,
            stability_interval=0,
        )
        return identity, key, attempt, completion

    @staticmethod
    def event_bytes(records):
        return {path.name: path.read_bytes()
                for path in (records.records / 'events').iterdir()}

    def strict_public_source(self, path):
        raw = Path(path).read_bytes()
        info = Path(path).stat()
        return {
            'name': Path(path).name,
            'size': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'mtime_ns': info.st_mtime_ns,
            'ctime_ns': info.st_ctime_ns,
        }

    @contextlib.contextmanager
    def strict_dispatch(self, response):
        calls = []
        original_verify_media = media_verify.verify_media
        original_verify_photo = media_verify.verify_photo
        original_verify_video = media_verify.verify_video

        def dispatch(*args, **kwargs):
            bound = STRICT_VERIFY_SIGNATURE.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = dict(bound.arguments)
            path = Path(arguments['path'])
            kind = arguments['kind']
            calls.append((path, kind, arguments))
            if isinstance(response, BaseException):
                raise response
            if callable(response):
                return response(path, kind)
            return response

        patches = [mock.patch.object(
            media_verify, 'verify_media', side_effect=dispatch)]
        for name in ('verify_photo', 'verify_video'):
            patches.append(mock.patch.object(
                media_verify,
                name,
                side_effect=AssertionError(
                    'production must dispatch through strict verify_media'),
            ))
        for name, value in vars(notes).items():
            if value is original_verify_media:
                patches.append(mock.patch.object(
                    notes, name, side_effect=dispatch))
            elif value is original_verify_photo or value is original_verify_video:
                patches.append(mock.patch.object(
                    notes,
                    name,
                    side_effect=AssertionError(
                        'production must dispatch through strict verify_media'),
                ))

        with contextlib.ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            yield calls

    def strict_pass(self, path, kind):
        source = self.strict_public_source(path)
        manifest = [source]
        result = {
            'verdict': 'PASS',
            'kind': kind,
            'source': source,
            'manifest': manifest,
            'manifest_sha256': digest(encoded(manifest)),
            'stable_samples': [source, source, source],
            'stable_sample_count': 3,
            'pass_scope': 'SYNTHETIC_STRICT_VERIFIER',
            'dispatch_authorized': False,
            'sensor_verified': False,
            'real_line_e2e': 'NOT_TESTED',
        }
        if kind == PHOTO:
            result.update({
                'imageio': {
                    'verdict': 'PASS',
                    'readOnly': True,
                    'expected': 1,
                    'actualEntries': 1,
                    'entries': [{
                        'name': source['name'],
                        'sha256': source['sha256'],
                        'decoded': True,
                        'width': 2,
                        'height': 2,
                    }],
                },
                'full_decode_evidence': {
                    'command': ['/synthetic/image_decode', '/synthetic', '1'],
                    'exit_code': 0,
                    'stdout_sha256': '0' * 64,
                    'stderr_sha256': 'e3b0c44298fc1c149afbf4c8996fb924'
                                     '27ae41e4649b934ca495991b7852b855',
                },
            })
        else:
            stream = {
                'index': 0,
                'codec_type': 'video',
                'codec_name': 'h264',
                'duration_seconds': 1.0,
                'expected_frames': 1,
                'attached_pic': False,
            }
            result.update({
                'tools': {
                    'ffmpeg': {
                        'configured_path': str(notes.FFMPEG),
                        'version': media_verify.VIDEO_TOOL_VERSION,
                        'version_first_line': 'ffmpeg version synthetic',
                        'sha256': media_verify.FFMPEG_SHA256,
                        'expected_sha256': media_verify.FFMPEG_SHA256,
                        'executable': True,
                    },
                    'ffprobe': {
                        'configured_path': str(notes.FFPROBE),
                        'version': media_verify.VIDEO_TOOL_VERSION,
                        'version_first_line': 'ffprobe version synthetic',
                        'sha256': media_verify.FFPROBE_SHA256,
                        'expected_sha256': media_verify.FFPROBE_SHA256,
                        'executable': True,
                    },
                },
                'probe': {
                    'streams': [stream],
                    'result': {},
                    'exit_code': 0,
                    'stderr_empty': True,
                    'command': ['/synthetic/ffprobe', str(path)],
                },
                'streams': [{
                    'stream': stream,
                    'decode': {
                        'stream_index': 0,
                        'command': ['/synthetic/ffmpeg', '-map', '0:0',
                                    '-f', 'null', '-'],
                        'exit_code': 0,
                        'stdout_eof': True,
                        'stdout_bytes': 1,
                        'stdout_sha256': '0' * 64,
                        'stderr_empty': True,
                        'stderr_bytes': 0,
                        'stderr_sha256': 'e3b0c44298fc1c149afbf4c8996fb924'
                                         '27ae41e4649b934ca495991b7852b855',
                        'stderr_preview': '',
                        'progress': {
                            'final_progress': 'end',
                            'final_out_time_us': 1000000,
                            'final_frame': 1,
                            'last': {'progress': 'end'},
                        },
                    },
                    'coverage': {
                        'duration_covered': True,
                        'frames_covered': True,
                        'duration_seconds': 1.0,
                        'expected_frames': 1,
                        'observed_out_time_us': 1000000,
                        'observed_frames': 1,
                    },
                }],
                'all_audio_video_streams_decoded': 1,
            })
        return result

    def test_photo_dispatch_uses_strict_media_verify(self):
        ledger = self.new_ledger('strict-photo')
        _identity, _key, attempt, target = self.prepare_download(
            ledger, PHOTO, 'strict-photo-media')
        with self.strict_dispatch(self.strict_pass) as calls:
            completion = ledger.records.verify(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                decoder='/synthetic/image_decode',
                decoder_sha256='0' * 64,
                stability_interval=0,
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], target)
        self.assertEqual(calls[0][1], PHOTO)
        self.assertEqual(completion['kind'], 'completion')

    def test_video_dispatch_uses_strict_media_verify(self):
        ledger = self.new_ledger('strict-video')
        _identity, _key, attempt, target = self.prepare_download(
            ledger, VIDEO, 'strict-video-media')
        with self.strict_dispatch(self.strict_pass) as calls:
            completion = ledger.records.verify(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                stability_interval=0,
                stall_seconds=0.01,
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], target)
        self.assertEqual(calls[0][1], VIDEO)
        self.assertEqual(completion['kind'], 'completion')

    def test_video_verification_reloads_with_flat_decode_schema(self):
        ledger = self.new_ledger('strict-video-reload')
        _identity, _key, attempt, _target = self.prepare_download(
            ledger, VIDEO, 'strict-video-reload-media')
        with self.strict_dispatch(self.strict_pass):
            completion = ledger.records.verify(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                stability_interval=0,
                stall_seconds=0.01,
            )
        self.assertEqual(completion['kind'], 'completion')

        reopened = self.reopen(ledger)
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        verification_event = next(
            event for event in reopened.events
            if event['kind'] == 'verification' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        verification = verification_event['data']['verification']
        self.assertNotIn('decode_stderr_policy', verification)
        rows = verification['decoded_streams']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['index'], 0)
        self.assertNotIn('stream', rows[0])

    def test_new_video_stderr_policy_round_trips_nonempty_diagnostic(self):
        ledger = self.new_ledger('strict-video-diagnostic')
        _identity, _key, attempt, _target = self.prepare_download(
            ledger, VIDEO, 'strict-video-diagnostic-media')
        diagnostic = b'Non-monotonic DTS in output stream 0:0; synthetic.\n'

        def payload(path, kind):
            result = self.strict_pass(path, kind)
            result['decode_stderr_policy'] = \
                media_verify.VIDEO_DECODE_STDERR_POLICY
            decode = result['streams'][0]['decode']
            decode.update(
                stderr_empty=False,
                stderr_bytes=len(diagnostic),
                stderr_sha256=hashlib.sha256(diagnostic).hexdigest(),
                stderr_preview=diagnostic.decode('utf-8'),
            )
            return result

        with self.strict_dispatch(payload):
            completion = ledger.records.verify(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                stability_interval=0,
                stall_seconds=0.01,
            )
        self.assertEqual(completion['kind'], 'completion')

        verification_event = next(
            event for event in ledger.records.events
            if event['kind'] == 'verification' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        verification = verification_event['data']['verification']
        self.assertEqual(
            verification['decode_stderr_policy'],
            media_verify.VIDEO_DECODE_STDERR_POLICY)
        decode = verification['decoded_streams'][0]['decode']
        self.assertFalse(decode['stderr_empty'])
        self.assertEqual(decode['stderr_bytes'], len(diagnostic))
        self.assertEqual(decode['stderr_sha256'],
                         hashlib.sha256(diagnostic).hexdigest())
        self.assertEqual(decode['stderr_preview'],
                         diagnostic.decode('utf-8'))

        reopened = self.reopen(ledger)
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        replay_event = next(
            event for event in reopened.events
            if event['kind'] == 'verification' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        self.assertEqual(
            replay_event['data']['verification']['decode_stderr_policy'],
            media_verify.VIDEO_DECODE_STDERR_POLICY)

    def test_legacy_nonempty_video_evidence_is_rejected_on_reload(self):
        ledger = self.new_ledger('strict-video-legacy-nonempty')
        _identity, _key, attempt, _target = self.prepare_download(
            ledger, VIDEO, 'strict-video-legacy-nonempty-media')
        diagnostic = b'legacy nonempty decode diagnostic\n'

        def payload(path, kind):
            result = self.strict_pass(path, kind)
            result['decode_stderr_policy'] = \
                media_verify.VIDEO_DECODE_STDERR_POLICY
            decode = result['streams'][0]['decode']
            decode.update(
                stderr_empty=False,
                stderr_bytes=len(diagnostic),
                stderr_sha256=hashlib.sha256(diagnostic).hexdigest(),
                stderr_preview=diagnostic.decode('utf-8'),
            )
            return result

        with self.strict_dispatch(payload):
            ledger.records.verify(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                stability_interval=0,
                stall_seconds=0.01,
            )
        events = self.read_events(ledger.records)
        verification = next(
            event for event in events
            if event['kind'] == 'verification' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        verification['data']['verification'].pop('decode_stderr_policy')
        self.rewrite_events(ledger.records, events)
        with self.assertRaisesRegex(
                NotesError, 'INVALID_VIDEO_DECODE_EVIDENCE'):
            self.reopen(ledger).summary()

    def test_video_stderr_policy_rejects_malformed_evidence_without_events(self):
        diagnostic = b'synthetic decode diagnostic\n'
        empty_hash = hashlib.sha256(b'').hexdigest()
        nonempty_hash = hashlib.sha256(diagnostic).hexdigest()

        def set_stderr(result, raw=diagnostic):
            decode = result['streams'][0]['decode']
            decode.update(
                stderr_empty=not raw,
                stderr_bytes=len(raw),
                stderr_sha256=hashlib.sha256(raw).hexdigest(),
                stderr_preview=raw[:4000].decode('utf-8', 'replace'),
            )
            return result

        def new_policy(result, raw=diagnostic):
            result['decode_stderr_policy'] = \
                media_verify.VIDEO_DECODE_STDERR_POLICY
            return set_stderr(result, raw)

        def mutate_bytes_bool(result):
            decode = set_stderr(result)['streams'][0]['decode']
            result['decode_stderr_policy'] = \
                media_verify.VIDEO_DECODE_STDERR_POLICY
            decode['stderr_bytes'] = True
            return result

        def mutate_bytes_float(result):
            decode = set_stderr(result)['streams'][0]['decode']
            result['decode_stderr_policy'] = \
                media_verify.VIDEO_DECODE_STDERR_POLICY
            decode['stderr_bytes'] = float(len(diagnostic))
            return result

        def mutate_short_duration(result):
            result = new_policy(result)
            row = result['streams'][0]
            row['decode']['progress']['final_out_time_us'] = 0
            row['coverage']['observed_out_time_us'] = 0
            row['coverage']['duration_covered'] = False
            return result

        def mutate_short_frames(result):
            result = new_policy(result)
            row = result['streams'][0]
            row['decode']['progress']['final_frame'] = 0
            row['coverage']['observed_frames'] = 0
            row['coverage']['frames_covered'] = False
            return result

        def mutate_forged_duration(result):
            result = new_policy(result)
            row = result['streams'][0]
            row['decode']['progress']['final_out_time_us'] = 0
            row['coverage']['observed_out_time_us'] = 0
            return result

        def mutate_missing_stream(result):
            result = new_policy(result)
            result['streams'] = []
            return result

        def mutate_duplicate_stream(result):
            result = new_policy(result)
            result['streams'].append(copy.deepcopy(result['streams'][0]))
            return result

        def mutate_probe_stderr(result):
            result = new_policy(result)
            result['probe']['stderr_empty'] = False
            return result

        def mutate_empty_flag(result):
            result = new_policy(result)
            result['streams'][0]['decode']['stderr_empty'] = True
            return result

        def mutate_empty_hash(result):
            result = new_policy(result)
            result['streams'][0]['decode']['stderr_sha256'] = empty_hash
            return result

        def mutate_nonempty_hash(result):
            result = new_policy(result, b'')
            result['streams'][0]['decode']['stderr_sha256'] = nonempty_hash
            return result

        def mutate_empty_preview(result):
            result = new_policy(result)
            result['streams'][0]['decode']['stderr_preview'] = ''
            return result

        def mutate_nonempty_preview(result):
            result = new_policy(result, b'')
            result['streams'][0]['decode']['stderr_preview'] = 'diagnostic'
            return result

        def mutate_missing_preview(result):
            result = new_policy(result)
            result['streams'][0]['decode'].pop('stderr_preview')
            return result

        def mutate_long_preview(result):
            result = new_policy(result)
            result['streams'][0]['decode']['stderr_preview'] = 'x' * 4001
            return result

        def mutate_missing_eof(result):
            result = new_policy(result)
            result['streams'][0]['decode']['stdout_eof'] = False
            return result

        cases = {
            'legacy_nonempty': (lambda result: set_stderr(result),
                                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'unknown_policy': (
                lambda result: dict(result, decode_stderr_policy='UNKNOWN'),
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'policy_wrong_type': (
                lambda result: dict(result, decode_stderr_policy=True),
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'stderr_bytes_bool': (
                mutate_bytes_bool, 'INVALID_VIDEO_DECODE_EVIDENCE'),
            'stderr_bytes_float': (
                mutate_bytes_float, 'INVALID_VIDEO_DECODE_EVIDENCE'),
            'empty_flag_for_nonempty': (
                mutate_empty_flag,
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'empty_hash_for_nonempty': (
                mutate_empty_hash,
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'nonempty_hash_for_empty': (
                mutate_nonempty_hash,
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'preview_empty_for_nonempty': (
                mutate_empty_preview,
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'preview_nonempty_for_empty': (
                mutate_nonempty_preview,
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'preview_missing_for_nonempty': (
                mutate_missing_preview,
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'preview_too_long': (
                mutate_long_preview,
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'missing_stdout_eof': (
                mutate_missing_eof,
                'INVALID_VIDEO_DECODE_EVIDENCE'),
            'short_duration': (
                mutate_short_duration, 'INVALID_VIDEO_DECODE_EVIDENCE'),
            'short_frames': (
                mutate_short_frames, 'INVALID_VIDEO_DECODE_EVIDENCE'),
            'forged_duration_coverage': (
                mutate_forged_duration, 'INVALID_VIDEO_DECODE_EVIDENCE'),
            'missing_stream': (
                mutate_missing_stream, 'INVALID_VIDEO_DECODE_EVIDENCE'),
            'duplicate_stream': (
                mutate_duplicate_stream, 'INVALID_VIDEO_DECODE_EVIDENCE'),
            'probe_stderr': (
                mutate_probe_stderr, 'INVALID_VIDEO_PROBE_EVIDENCE'),
        }
        for label, (mutate, expected_code) in cases.items():
            with self.subTest(label=label):
                ledger = self.new_ledger('policy-' + label)
                _identity, _key, attempt, _target = self.prepare_download(
                    ledger, VIDEO, 'policy-media-' + label)
                before = self.event_bytes(ledger.records)

                def payload(path, kind, mutate=mutate):
                    return mutate(self.strict_pass(path, kind))

                with self.strict_dispatch(payload):
                    with self.assertRaises(NotesError) as raised:
                        ledger.records.verify(
                            session_id=ledger.session,
                            attempt_id=attempt['attempt_id'],
                            stability_interval=0,
                            stall_seconds=0.01,
                        )
                self.assertEqual(raised.exception.args[0], expected_code)
                self.assertEqual(self.event_bytes(ledger.records), before)
                self.assertFalse(any(
                    event['kind'] in ('verification', 'completion')
                    for event in ledger.records.events))

    def test_photo_verification_loader_requires_exact_entry_counts(self):
        for mutation in ('actual_bool', 'actual_float',
                         'missing_expected', 'expected_float',
                         'returncode_false', 'decode_exit_float'):
            with self.subTest(mutation=mutation):
                ledger = self.new_ledger('forged-photo-' + mutation)
                _identity, _key, attempt, _target = self.prepare_download(
                    ledger, PHOTO, 'forged-photo-media-' + mutation)
                with self.strict_dispatch(self.strict_pass):
                    ledger.records.verify(
                        session_id=ledger.session,
                        attempt_id=attempt['attempt_id'],
                        decoder='/synthetic/image_decode',
                        decoder_sha256='0' * 64,
                        stability_interval=0,
                    )
                events = self.read_events(ledger.records)
                verification = next(
                    event for event in events
                    if event['kind'] == 'verification' and
                    event['data']['attempt_id'] == attempt['attempt_id'])
                imageio = verification['data']['verification']['result']
                if mutation == 'actual_bool':
                    imageio['actualEntries'] = True
                elif mutation == 'actual_float':
                    imageio['actualEntries'] = 1.0
                elif mutation == 'missing_expected':
                    imageio.pop('expected')
                elif mutation == 'expected_float':
                    imageio['expected'] = 1.0
                elif mutation == 'returncode_false':
                    verification['data']['verification']['returncode'] = False
                else:
                    verification['data']['verification'][
                        'full_decode_evidence']['exit_code'] = 0.0
                self.rewrite_events(ledger.records, events)
                with self.assertRaisesRegex(
                        NotesError, 'INVALID_PHOTO'):
                    self.reopen(ledger).summary()

    def test_video_verification_loader_rejects_forged_coverage(self):
        for mutation in ('duration', 'frames', 'probe_exit_float'):
            with self.subTest(mutation=mutation):
                ledger = self.new_ledger('forged-video-' + mutation)
                _identity, _key, attempt, _target = self.prepare_download(
                    ledger, VIDEO, 'forged-video-media-' + mutation)
                with self.strict_dispatch(self.strict_pass):
                    ledger.records.verify(
                        session_id=ledger.session,
                        attempt_id=attempt['attempt_id'],
                        stability_interval=0,
                        stall_seconds=0.01,
                    )
                events = self.read_events(ledger.records)
                verification = next(
                    event for event in events
                    if event['kind'] == 'verification' and
                    event['data']['attempt_id'] == attempt['attempt_id'])
                payload = verification['data']['verification']
                row = payload['decoded_streams'][0]
                if mutation == 'duration':
                    row['decode']['progress']['final_out_time_us'] = 0
                    row['coverage']['observed_out_time_us'] = 0
                elif mutation == 'frames':
                    row['nb_frames'] = 2
                    row['coverage']['expected_frames'] = 2
                    row['coverage']['observed_frames'] = 1
                    row['decode']['progress']['final_frame'] = 1
                    payload['probe']['streams'][0]['expected_frames'] = 2
                else:
                    payload['probe']['exit_code'] = 0.0
                self.rewrite_events(ledger.records, events)
                with self.assertRaisesRegex(
                        NotesError, 'INVALID_VIDEO'):
                    self.reopen(ledger).summary()

    def test_strict_verifier_error_is_fail_closed_for_both_kinds(self):
        for kind in (PHOTO, VIDEO):
            with self.subTest(kind=kind):
                ledger = self.new_ledger('strict-error-' + kind.lower())
                _identity, _key, attempt, target = self.prepare_download(
                    ledger, kind, 'strict-error-media-' + kind.lower())
                before = self.event_bytes(ledger.records)
                raised = None
                with self.strict_dispatch(MediaVerificationError(
                        'SYNTHETIC_VERIFIER_REJECTED')) as calls:
                    try:
                        ledger.records.verify(
                            session_id=ledger.session,
                            attempt_id=attempt['attempt_id'],
                            decoder='/synthetic/image_decode',
                            decoder_sha256='0' * 64,
                            stability_interval=0,
                            stall_seconds=0.01,
                        )
                    except (NotesError, MediaVerificationError) as exc:
                        raised = exc
                self.assertIsNotNone(raised)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][0], target)
                self.assertEqual(calls[0][1], kind)
                self.assertEqual(self.event_bytes(ledger.records), before)
                self.assertTrue(target.is_file())

    def test_summary_blocks_detail_pending_even_when_known_media_complete(self):
        ledger = self.new_ledger('detail-pending')
        self.complete_media(ledger, PHOTO, 'complete-before-detail-gap')
        pending_key = self.observe_without_detail(ledger, 'detail-pending-post')

        summary = self.reopen(ledger).summary()
        pending = next(row for row in summary['posts']
                       if row['post_key'] == pending_key)
        self.assertEqual(pending['state'], 'DETAIL_PENDING')
        self.assertFalse(summary['all_known_media_complete'])
        self.assertIn('POST_DETAIL_PENDING', summary['dispatch_blockers'])

    def test_summary_counts_only_latest_complete_scan(self):
        ledger = self.new_ledger('summary-latest-counts')
        old_identity = notes.media_identity(
            kind=PHOTO, visual_key='summary-latest-counts-old')
        self.observe_post(ledger, 'summary-latest-counts-old', [old_identity])
        self.observe_post(
            ledger, 'summary-latest-counts-new', [], no_media=True)

        summary = self.reopen(ledger).summary()
        self.assertEqual(sum(summary['status_counts'].values()), 0)
        self.assertEqual(sum(summary['local_counts'].values()), 0)
        self.assertTrue(summary['all_known_media_complete'])

    def test_summary_blocks_unknown_attempt_outside_latest_scan(self):
        ledger = self.new_ledger('summary-unknown-outside-scan')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='summary-unknown-outside-scan-media')
        _post, post_key_value = self.observe_post(
            ledger, 'summary-unknown-outside-scan-post', [identity])
        key = self.media_key(ledger, post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='STOPPED',
            evidence=ledger.evidence_for_attempt(attempt),
        )
        self.observe_post(
            ledger, 'summary-unknown-outside-scan-new', [], no_media=True)
        events = self.read_events(ledger.records)
        outcome = next(event for event in events
                       if event['kind'] == 'outcome' and
                       event['data']['attempt_id'] == attempt['attempt_id'])
        outcome['data']['outcome'] = 'UNKNOWN'
        self.rewrite_events(ledger.records, events)

        summary = self.reopen(ledger).summary()
        self.assertFalse(summary['all_known_media_complete'])
        self.assertIn('UNKNOWN_ATTEMPT', summary['dispatch_blockers'])

    def test_missing_existing_media_uses_observed_total_and_blocks_completion(self):
        ledger = self.new_ledger('missing-observed-total')
        first = notes.media_identity(
            kind=PHOTO, visual_key='missing-observed-total-first')
        second = notes.media_identity(
            kind=PHOTO, visual_key='missing-observed-total-second')
        post, post_key_value = self.observe_post(
            ledger, 'missing-observed-total-post', [first, second])
        first_key = self.media_key(ledger, post_key_value, first)
        second_key = self.media_key(ledger, post_key_value, second)
        self.complete_media(
            ledger, PHOTO, 'missing-observed-total-first',
            post_key_value=post_key_value, identity=first)

        self.scan_with_pages(ledger, [([post], [])])
        ledger.records.record_post(
            session_id=ledger.session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=2,
            text_sha256=None,
            evidence=ledger.evidence_for_post(post_key_value),
            no_media=False,
        )
        with self.assertRaisesRegex(NotesError, 'INVALID_MEDIA_MISSING'):
            ledger.records.record_media(
                session_id=ledger.session,
                post_key_value=post_key_value,
                items=[{'identity': first}],
                missing=[{'media_key': second_key,
                          'reason': 'source order omitted'}],
                evidence=ledger.evidence_for_post(post_key_value),
            )
        data = ledger.records.record_media(
            session_id=ledger.session,
            post_key_value=post_key_value,
            items=[{'identity': first}],
            missing=[{'media_key': second_key, 'source_order': 1,
                      'reason': 'synthetic unavailable'}],
            evidence=ledger.evidence_for_post(post_key_value),
        )
        self.assertEqual(data['missing'],
                         [{'media_key': second_key,
                           'source_order': 1,
                           'reason': 'synthetic unavailable'}])

        summary = self.reopen(ledger).summary()
        by_key = {row['media_key']: row for row in summary['media']}
        self.assertEqual(by_key[first_key]['status'], 'COMPLETED')
        self.assertTrue(by_key[second_key]['missing'])
        self.assertEqual(by_key[second_key]['status'], 'PREVIOUSLY_INCOMPLETE')
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(summary['status_counts']['PREVIOUSLY_INCOMPLETE'], 1)
        self.assertFalse(summary['all_known_media_complete'])
        self.assertNotIn('POST_COVERAGE_INCOMPLETE',
                         summary['dispatch_blockers'])

    def test_missing_first_slot_keeps_present_source_order(self):
        ledger = self.new_ledger('missing-first-slot')
        first = notes.media_identity(
            kind=PHOTO, visual_key='missing-first-slot-first')
        second = notes.media_identity(
            kind=PHOTO, visual_key='missing-first-slot-second')
        post, post_key_value = self.observe_post(
            ledger, 'missing-first-slot-post', [first, second])
        first_key = self.media_key(ledger, post_key_value, first)
        second_key = self.media_key(ledger, post_key_value, second)

        self.scan_with_pages(ledger, [([post], [])])
        ledger.records.record_post(
            session_id=ledger.session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=2,
            text_sha256=None,
            evidence=ledger.evidence_for_post(post_key_value),
            no_media=False,
        )
        data = ledger.records.record_media(
            session_id=ledger.session,
            post_key_value=post_key_value,
            items=[{'identity': second}],
            missing=[{'media_key': first_key, 'source_order': 0,
                      'reason': 'synthetic unavailable'}],
            evidence=ledger.evidence_for_post(post_key_value),
        )
        self.assertEqual(data['items'][0]['source_order'], 1)

        summary = self.reopen(ledger).summary()
        by_key = {row['media_key']: row for row in summary['media']}
        self.assertEqual(by_key[first_key]['source_order'], 0)
        self.assertEqual(by_key[second_key]['source_order'], 1)
        self.assertTrue(by_key[first_key]['missing'])


    def test_media_count_is_present_plus_explicit_missing(self):
        ledger = self.new_ledger('media-count-total')
        first = notes.media_identity(
            kind=PHOTO, visual_key='media-count-total-first')
        second = notes.media_identity(
            kind=PHOTO, visual_key='media-count-total-second')
        post, post_key_value = self.observe_post(
            ledger, 'media-count-total-post', [first, second])
        self.scan_with_pages(ledger, [([post], [])])
        ledger.records.record_post(
            session_id=ledger.session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=3,
            text_sha256=None,
            evidence=ledger.evidence_for_post(post_key_value),
            no_media=False,
        )
        with self.assertRaisesRegex(
                NotesError, 'POST_MEDIA_COUNT_MISMATCH'):
            ledger.records.record_media(
                session_id=ledger.session,
                post_key_value=post_key_value,
                items=[{'identity': first}, {'identity': second}],
                missing=[],
                evidence=ledger.evidence_for_post(post_key_value),
            )

    def test_summary_blocks_media_count_coverage_mismatch(self):
        ledger = self.new_ledger('coverage-mismatch')
        _, post_key_value = self.observe_post(
            ledger, 'coverage-mismatch-post', [], no_media=True)
        self.mutate_post_count(ledger, post_key_value, 1)

        summary = self.reopen(ledger).summary()
        post = next(row for row in summary['posts']
                    if row['post_key'] == post_key_value)
        self.assertEqual(post['media_count'], 1)
        self.assertEqual(len(post['media']), 0)
        self.assertFalse(summary['all_known_media_complete'])
        self.assertIn('POST_COVERAGE_INCOMPLETE',
                      summary['dispatch_blockers'])

    def test_fresh_scan_can_resume_after_partial_detail_and_intent_is_local(self):
        ledger = self.new_ledger('scan-coverage-gate')
        detailed_post = notes.post_identity(
            visual_key='scan-coverage-detailed-post')
        pending_post = notes.post_identity(
            visual_key='scan-coverage-pending-post')
        self.scan_with_pages(
            ledger, [([detailed_post, pending_post], [])])
        detailed_key = notes.post_key(
            ledger.summary['list_key'], detailed_post)
        pending_key = notes.post_key(
            ledger.summary['list_key'], pending_post)
        identity = notes.media_identity(
            kind=PHOTO, visual_key='scan-coverage-detailed-media')
        media_key_value = self.media_key(
            ledger, detailed_key, identity)
        ledger.records.record_post(
            session_id=ledger.session,
            post_key_value=detailed_key,
            date_summary='synthetic',
            media_count=1,
            text_sha256=None,
            evidence=ledger.evidence_for_post(detailed_key),
            no_media=False,
        )
        ledger.records.record_media(
            session_id=ledger.session,
            post_key_value=detailed_key,
            items=[dict(identity=identity)],
            missing=[],
            evidence=ledger.evidence_for_post(detailed_key),
        )

        summary = ledger.records.summary()
        self.assertIn('POST_DETAIL_PENDING', summary['dispatch_blockers'])
        fresh_session = ledger.session + '-fresh'
        ledger.records.bind(
            session_id=fresh_session,
            observation=ledger.evidence(list_key=ledger.summary['list_key']),
            handoff=ledger.evidence(list_key=ledger.summary['list_key']))
        before = self.event_bytes(ledger.records)
        scan = ledger.records.scan(
            session_id=fresh_session, action='START',
            evidence=ledger.evidence_for_scan())
        self.assertIn('scan_id', scan)
        after = self.event_bytes(ledger.records)
        self.assertEqual(len(after), len(before) + 1)
        with self.assertRaisesRegex(
                NotesError, 'COMPLETE_NOTES_SCAN_REQUIRED'):
            ledger.records.intent(
                session_id=fresh_session,
                media_key_value=media_key_value)

    def test_intent_allows_complete_target_while_other_post_detail_is_pending(self):
        ledger = self.new_ledger('local-intent-coverage')
        first = notes.post_identity(visual_key='eligible-post')
        pending = notes.post_identity(visual_key='pending-post')
        self.scan_with_pages(ledger, [([first, pending], [])])
        first_key = notes.post_key(ledger.summary['list_key'], first)
        pending_key = notes.post_key(ledger.summary['list_key'], pending)
        identity = notes.media_identity(
            kind=PHOTO, visual_key='eligible-media')
        target_key = self.media_key(ledger, first_key, identity)
        ledger.records.record_post(
            session_id=ledger.session, post_key_value=first_key,
            date_summary='synthetic', media_count=1, text_sha256=None,
            evidence=ledger.evidence_for_post(first_key), no_media=False)
        ledger.records.record_media(
            session_id=ledger.session, post_key_value=first_key,
            items=[dict(identity=identity)], missing=[],
            evidence=ledger.evidence_for_post(first_key))

        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=target_key)
        self.assertTrue(Path(attempt['destination']).is_dir())
        summary = ledger.records.summary()
        row = next(item for item in summary['posts']
                   if item['post_key'] == pending_key)
        self.assertEqual(row['state'], 'DETAIL_PENDING')
        self.assertFalse(summary['all_known_media_complete'])
        self.assertIn('POST_DETAIL_PENDING', summary['dispatch_blockers'])

        staging = Path(attempt['destination'])
        (staging / 'eligible.png').write_bytes(b'synthetic completion')
        ledger.records.outcome(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(attempt))
        completion = ledger.records.verify(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(completion['data']['media_key'], target_key)

        self.assertFalse(ledger.records.summary()['all_known_media_complete'])

        pending_identity = notes.media_identity(
            kind=PHOTO, visual_key='pending-post-media')
        pending_media_key = self.media_key(
            ledger, pending_key, pending_identity)
        ledger.records.record_post(
            session_id=ledger.session, post_key_value=pending_key,
            date_summary='synthetic', media_count=1, text_sha256=None,
            evidence=ledger.evidence_for_post(pending_key), no_media=False)
        ledger.records.record_media(
            session_id=ledger.session, post_key_value=pending_key,
            items=[dict(identity=pending_identity)], missing=[],
            evidence=ledger.evidence_for_post(pending_key))
        pending_attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=pending_media_key)
        pending_staging = Path(pending_attempt['destination'])
        (pending_staging / 'pending.png').write_bytes(b'synthetic completion')
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=pending_attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(pending_attempt))
        pending_completion = ledger.records.verify(
            session_id=ledger.session,
            attempt_id=pending_attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(pending_completion['data']['media_key'],
                         pending_media_key)
        self.assertTrue(ledger.records.summary()['all_known_media_complete'])

        fresh_session = ledger.session + '-next'
        ledger.records.bind(
            session_id=fresh_session,
            observation=ledger.evidence(list_key=ledger.summary['list_key']),
            handoff=ledger.evidence(list_key=ledger.summary['list_key']))
        ledger.session = fresh_session
        self.scan_with_pages(ledger, [([first, pending], [])])
        ledger.records.record_post(
            session_id=fresh_session, post_key_value=first_key,
            date_summary='synthetic', media_count=1, text_sha256=None,
            evidence=ledger.evidence_for_post(first_key), no_media=False)
        ledger.records.record_media(
            session_id=fresh_session, post_key_value=first_key,
            items=[dict(identity=identity)], missing=[],
            evidence=ledger.evidence_for_post(first_key))
        with self.assertRaisesRegex(
                NotesError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            ledger.records.intent(
                session_id=fresh_session, media_key_value=target_key)

    def test_unknown_attempt_for_other_post_blocks_intent_without_new_staging(self):
        ledger = self.new_ledger('other-unknown-blocks-intent')
        first = notes.post_identity(visual_key='first-post')
        second = notes.post_identity(visual_key='second-post')
        self.scan_with_pages(ledger, [([first, second], [])])
        first_key = notes.post_key(ledger.summary['list_key'], first)
        second_key = notes.post_key(ledger.summary['list_key'], second)
        first_media = notes.media_identity(
            kind=PHOTO, visual_key='first-photo')
        second_media = notes.media_identity(
            kind=PHOTO, visual_key='second-photo')
        for post_key_value, identity in ((first_key, first_media),
                                         (second_key, second_media)):
            ledger.records.record_post(
                session_id=ledger.session, post_key_value=post_key_value,
                date_summary='synthetic', media_count=1, text_sha256=None,
                evidence=ledger.evidence_for_post(post_key_value),
                no_media=False)
            ledger.records.record_media(
                session_id=ledger.session, post_key_value=post_key_value,
                items=[dict(identity=identity)], missing=[],
                evidence=ledger.evidence_for_post(post_key_value))

        second_media_key = self.media_key(ledger, second_key, second_media)
        active = ledger.records.intent(
            session_id=ledger.session, media_key_value=second_media_key)
        ledger.records.outcome(
            session_id=ledger.session, attempt_id=active['attempt_id'],
            outcome='UNKNOWN', evidence=ledger.evidence_for_attempt(active))
        first_media_key = self.media_key(ledger, first_key, first_media)
        before_events = self.event_bytes(ledger.records)
        before_staging = sorted(
            str(path.relative_to(ledger.photo_root))
            for path in ledger.photo_root.rglob('.line-notes-incoming-*'))
        with self.assertRaisesRegex(
                NotesError, 'ANOTHER_MEDIA_ATTEMPT_UNRESOLVED'):
            ledger.records.intent(
                session_id=ledger.session, media_key_value=first_media_key)
        self.assertEqual(self.event_bytes(ledger.records), before_events)
        self.assertEqual(
            sorted(str(path.relative_to(ledger.photo_root))
                   for path in ledger.photo_root.rglob(
                       '.line-notes-incoming-*')),
            before_staging)

    def test_start_scan_blocks_unresolved_attempts_and_verify_required(self):
        ledger = self.new_ledger('scan-unresolved-attempt')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='scan-unresolved-media')
        _post, post_key_value = self.observe_post(
            ledger, 'scan-unresolved-post', [identity])
        key = self.media_key(ledger, post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)

        summary = ledger.records.summary()
        self.assertIn('UNKNOWN_ATTEMPT', summary['dispatch_blockers'])
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.scan(
                session_id=ledger.session, action='START',
                evidence=ledger.evidence_for_scan())
        self.assertEqual(raised.exception.args[0],
                         'UNRESOLVED_ATTEMPT_BLOCKS_CHANGE')
        self.assertEqual(self.event_bytes(ledger.records), before)

        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='UNKNOWN',
            evidence=ledger.evidence_for_attempt(attempt),
        )
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.scan(
                session_id=ledger.session, action='START',
                evidence=ledger.evidence_for_scan())
        self.assertEqual(raised.exception.args[0],
                         'UNRESOLVED_ATTEMPT_BLOCKS_CHANGE')
        self.assertEqual(self.event_bytes(ledger.records), before)
        ledger.records.reconcile(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            result='STOPPED',
            evidence=ledger.evidence_for_attempt(attempt),
        )
        repaired_scan = ledger.records.scan(
            session_id=ledger.session, action='START',
            evidence=ledger.evidence_for_scan())
        self.assertIn('scan_id', repaired_scan)

        ledger2 = self.new_ledger('scan-verify-required')
        _identity, _key, _attempt, _target = self.prepare_download(
            ledger2, PHOTO, 'scan-verify-required-media')
        summary = ledger2.records.summary()
        self.assertIn('VERIFY_REQUIRED', summary['dispatch_blockers'])
        before = self.event_bytes(ledger2.records)
        with self.assertRaises(NotesError) as raised:
            ledger2.records.scan(
                session_id=ledger2.session, action='START',
                evidence=ledger2.evidence_for_scan())
        self.assertEqual(raised.exception.args[0],
                         'UNRESOLVED_ATTEMPT_BLOCKS_CHANGE')
        self.assertEqual(self.event_bytes(ledger2.records), before)

    def test_start_scan_blocks_pending_naming_transaction(self):
        ledger = self.new_ledger('scan-pending-naming')
        _identity, _key, attempt, _target = self.prepare_download(
            ledger, PHOTO, 'scan-pending-naming-media')
        with mock.patch.object(
                NotesRecords, '_execute_publish',
                side_effect=OSError('synthetic publish interruption')):
            with self.assertRaisesRegex(
                    OSError, 'synthetic publish interruption'):
                ledger.records.verify(
                    session_id=ledger.session,
                    attempt_id=attempt['attempt_id'],
                    verifier=self.pass_verifier,
                    stability_interval=0,
                )
        summary = ledger.records.summary()
        self.assertIn('PENDING_NAMING', summary['dispatch_blockers'])
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.scan(
                session_id=ledger.session, action='START',
                evidence=ledger.evidence_for_scan())
        self.assertEqual(raised.exception.args[0],
                         'PENDING_NAMING_TRANSACTION')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def read_events(self, records):
        rows = []
        for path in sorted((records.records / 'events').iterdir()):
            rows.append(json.loads(path.read_text(encoding='utf-8')))
        return rows

    def rewrite_events(self, records, events):
        previous = None
        for index, event in enumerate(events, 1):
            event['sequence'] = index
            event['previous_sha256'] = previous
            raw = encoded(event)
            notes._atomic_replace_json(
                records.records / 'events' / ('%08d.json' % index), event)
            previous = digest(raw)
        return events

    def mutate_intent(self, ledger, attempt_id, **changes):
        events = self.read_events(ledger.records)
        target = None
        for event in events:
            if (event['kind'] == 'intent' and
                    event['data']['attempt_id'] == attempt_id):
                target = event
                break
        self.assertIsNotNone(target)
        target['data'].update(changes)
        if ('recovery_of' in changes and
                'recovery_evidence' not in changes and
                target['data']['recovery_evidence'] is not None):
            prior = next(event['data'] for event in events
                         if event['kind'] == 'intent' and
                         event['data']['attempt_id'] ==
                         target['data']['recovery_of'])
            target['data']['recovery_evidence'] = \
                ledger.stored_evidence_for_attempt(prior)
        self.rewrite_events(ledger.records, events)

    def legacy_evidence(self, ledger, label):
        raw = ('legacy opaque ' + label).encode('utf-8')
        sha256 = digest(raw)
        path = ledger.records.records / 'evidence' / sha256
        path.write_bytes(raw)
        return dict(path=str(path), bytes=len(raw), sha256=sha256)

    def mutate_post_count(self, ledger, post_key_value, media_count):
        events = self.read_events(ledger.records)
        target = None
        for event in events:
            if (event['kind'] == 'post' and
                    event['data']['post_key'] == post_key_value):
                target = event
        self.assertIsNotNone(target)
        target['data']['media_count'] = media_count
        target['data']['no_media'] = False
        self.rewrite_events(ledger.records, events)

    def set_recovery_authorized(self, ledger, value):
        records = ledger.records
        events = self.read_events(records)
        self.assertEqual(events[0]['kind'], 'created')
        events[0]['data']['recovery_authorized'] = value
        self.rewrite_events(records, events)

        list_path = records.records / 'list.json'
        list_data = json.loads(list_path.read_text(encoding='utf-8'))
        list_data['recovery_authorized'] = value
        list_raw = encoded(list_data)
        notes._atomic_replace_json(list_path, list_data)

        store_path = records.records / 'store.json'
        store = json.loads(store_path.read_text(encoding='utf-8'))
        store['list_json_sha256'] = digest(list_raw)
        store['created_event_sha256'] = digest(encoded(events[0]))
        store_raw = encoded(store)
        notes._atomic_replace_json(store_path, store)

        index_path = ledger.collection.path / 'index.json'
        index = json.loads(index_path.read_text(encoding='utf-8'))
        index['lists'][records.records.name]['store_sha256'] = digest(store_raw)
        notes._atomic_replace_json(index_path, index)

    def stopped_attempt(self, ledger, key, *, recovery_evidence=None):
        prior = None
        if recovery_evidence:
            prior = next(event['data'] for event in reversed(
                ledger.records.events)
                if event['kind'] == 'intent' and
                event['data']['media_key'] == key)
        attempt = ledger.records.intent(
            session_id=ledger.session,
            media_key_value=key,
            recovery_evidence=(str(ledger.evidence_for_attempt(prior))
                               if recovery_evidence else None),
        )
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='STOPPED',
            evidence=ledger.evidence_for_attempt(attempt),
        )
        return attempt

    def assert_recovery_reload_fails(self, ledger):
        with self.assertRaises(NotesError) as raised:
            NotesRecords(str(ledger.records.records)).summary()
        self.assertIn('RECOVERY', str(raised.exception))

    def test_recovery_graph_is_fail_closed(self):
        with self.subTest(case='non_latest_prior'):
            ledger = self.new_ledger('recovery-non-latest')
            identity = notes.media_identity(
                kind=PHOTO, visual_key='recovery-non-latest-media')
            _, post_key_value = self.observe_post(
                ledger, 'recovery-non-latest-post', [identity])
            key = self.media_key(ledger, post_key_value, identity)
            first = self.stopped_attempt(ledger, key)
            second = self.stopped_attempt(
                ledger, key, recovery_evidence=True)
            third = ledger.records.intent(
                session_id=ledger.session,
                media_key_value=key,
                recovery_evidence=ledger.evidence_for_attempt(second),
            )
            self.mutate_intent(ledger, third['attempt_id'], recovery_of=first['attempt_id'])
            self.assertNotEqual(second['attempt_id'], first['attempt_id'])
            self.assert_recovery_reload_fails(ledger)

        with self.subTest(case='missing_authorization'):
            ledger = self.new_ledger('recovery-unauthorized')
            identity = notes.media_identity(
                kind=PHOTO, visual_key='recovery-unauthorized-media')
            _, post_key_value = self.observe_post(
                ledger, 'recovery-unauthorized-post', [identity])
            key = self.media_key(ledger, post_key_value, identity)
            self.stopped_attempt(ledger, key)
            self.stopped_attempt(ledger, key, recovery_evidence=True)
            self.set_recovery_authorized(ledger, False)
            self.assert_recovery_reload_fails(ledger)

        with self.subTest(case='missing_evidence'):
            ledger = self.new_ledger('recovery-no-evidence')
            identity = notes.media_identity(
                kind=PHOTO, visual_key='recovery-no-evidence-media')
            _, post_key_value = self.observe_post(
                ledger, 'recovery-no-evidence-post', [identity])
            key = self.media_key(ledger, post_key_value, identity)
            self.stopped_attempt(ledger, key)
            recovery = self.stopped_attempt(
                ledger, key, recovery_evidence=True)
            self.mutate_intent(
                ledger, recovery['attempt_id'], recovery_evidence=None)
            self.assert_recovery_reload_fails(ledger)

        with self.subTest(case='cross_media'):
            ledger = self.new_ledger('recovery-cross-media')
            first_identity = notes.media_identity(
                kind=PHOTO, visual_key='recovery-cross-media-a')
            second_identity = notes.media_identity(
                kind=PHOTO, visual_key='recovery-cross-media-b')
            _, post_key_value = self.observe_post(
                ledger,
                'recovery-cross-media-post',
                [first_identity, second_identity],
            )
            first_key = self.media_key(ledger, post_key_value, first_identity)
            second_key = self.media_key(ledger, post_key_value, second_identity)
            self.stopped_attempt(ledger, first_key)
            prior = self.stopped_attempt(
                ledger, first_key, recovery_evidence=True)
            unrelated = ledger.records.intent(
                session_id=ledger.session, media_key_value=second_key)
            self.mutate_intent(
                ledger,
                unrelated['attempt_id'],
                recovery_of=prior['attempt_id'],
                recovery_evidence=ledger.stored_evidence_for_attempt(prior),
            )
            self.assert_recovery_reload_fails(ledger)

    def test_pending_publish_is_blocked_before_local_changed(self):
        ledger = self.new_ledger('pending-local-changed')
        first = notes.media_identity(
            kind=PHOTO, visual_key='pending-local-changed-a')
        second = notes.media_identity(
            kind=PHOTO, visual_key='pending-local-changed-b')
        _, post_key_value = self.observe_post(
            ledger, 'pending-local-changed-post', [first, second])
        _, _, _, first_completion = self.complete_media(
            ledger,
            PHOTO,
            'pending-local-changed-a',
            post_key_value=post_key_value,
        )

        second_key = self.media_key(ledger, post_key_value, second)
        second_attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=second_key)
        second_staging = Path(second_attempt['destination'])
        (second_staging / 'pending.png').write_bytes(b'synthetic pending media')
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=second_attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(second_attempt),
        )
        with mock.patch.object(
                NotesRecords,
                '_execute_publish',
                side_effect=OSError('synthetic naming interruption')):
            with self.assertRaisesRegex(OSError, 'synthetic naming interruption'):
                ledger.records.verify(
                    session_id=ledger.session,
                    attempt_id=second_attempt['attempt_id'],
                    verifier=self.pass_verifier,
                    stability_interval=0,
                )

        first_target = (
            Path(first_completion['data']['destination']) /
            first_completion['data']['target_file']['name'])
        first_target.write_bytes(b'changed synthetic completed media')
        reopened = self.reopen(ledger)
        reopened.summary()
        self.assertEqual(len(reopened._pending_publish_plans()), 1)
        before = self.event_bytes(reopened)

        with self.assertRaisesRegex(
                NotesError, 'COMPLETED_FILES_CHANGED|LOCAL_CHANGED'):
            reopened.verify(
                session_id=ledger.session,
                attempt_id=second_attempt['attempt_id'],
                verifier=self.pass_verifier,
                stability_interval=0,
            )
        self.assertEqual(self.event_bytes(reopened), before)
        self.assertEqual(len(reopened._pending_publish_plans()), 1)
        self.assertEqual(first_target.read_bytes(),
                         b'changed synthetic completed media')

    def test_loader_rejects_verification_for_unknown_attempt(self):
        ledger = self.new_ledger('loader-unknown-verification')
        _identity, _key, attempt, _completion = self.complete_media(
            ledger, PHOTO, 'loader-unknown-verification-media')
        events = self.read_events(ledger.records)
        outcome = next(
            event for event in events
            if event['kind'] == 'outcome' and
            event['data']['attempt_id'] == attempt['attempt_id'])
        outcome['data']['outcome'] = 'UNKNOWN'
        self.rewrite_events(ledger.records, events)

        with self.assertRaisesRegex(
                NotesError, 'VERIFICATION_REQUIRES_DOWNLOAD_FINISHED'):
            self.reopen(ledger).summary()

    def test_loader_rejects_completion_target_content_mismatch(self):
        ledger = self.new_ledger('loader-target-content')
        _identity, _key, _attempt, completion = self.complete_media(
            ledger, PHOTO, 'loader-target-content-media')
        events = self.read_events(ledger.records)
        stored = next(
            event for event in events
            if event['kind'] == 'completion' and
            event['data']['transaction_id'] ==
            completion['data']['transaction_id'])
        current = stored['data']['target_file']['sha256']
        stored['data']['target_file']['sha256'] = (
            '0' * 64 if current != '0' * 64 else '1' * 64)
        self.rewrite_events(ledger.records, events)

        with self.assertRaisesRegex(
                NotesError, 'COMPLETION_TARGET_CONTENT_CHANGED'):
            self.reopen(ledger).summary()

    def test_record_post_rejects_post_absent_from_latest_complete_scan(self):
        ledger = self.new_ledger('stale-post')
        old_identity = notes.media_identity(
            kind=PHOTO, visual_key='stale-post-media')
        _old_post, old_key = self.observe_post(
            ledger, 'stale-post-old', [old_identity])
        new_key = self.observe_without_detail(ledger, 'stale-post-new')
        with self.assertRaisesRegex(
                NotesError, 'POST_NOT_IN_OBSERVED_SCAN'):
            ledger.records.record_post(
                session_id=ledger.session,
                post_key_value=old_key,
                date_summary='synthetic',
                media_count=1,
                text_sha256=None,
                evidence=ledger.evidence_for_post(old_key),
                no_media=False,
            )
        summary = ledger.records.summary()
        keys = {row['post_key'] for row in summary['posts']}
        self.assertNotIn(old_key, keys)
        self.assertIn(new_key, keys)

    def test_intent_rejects_stale_post_detail(self):
        ledger = self.new_ledger('stale-post-detail')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='stale-post-detail-media')
        post, post_key_value = self.observe_post(
            ledger, 'stale-post-detail-post', [identity])
        key = self.media_key(ledger, post_key_value, identity)
        self.scan_with_pages(ledger, [([post], [])])

        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.intent(session_id=ledger.session,
                                  media_key_value=key)
        self.assertEqual(raised.exception.args[0], 'STALE_POST_DETAIL')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_intent_rejects_stale_media_inventory(self):
        ledger = self.new_ledger('stale-media-inventory')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='stale-media-inventory-media')
        post, post_key_value = self.observe_post(
            ledger, 'stale-media-inventory-post', [identity])
        key = self.media_key(ledger, post_key_value, identity)
        self.scan_with_pages(ledger, [([post], [])])
        ledger.records.record_post(
            session_id=ledger.session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=1,
            text_sha256=None,
            evidence=ledger.evidence_for_post(post_key_value),
            no_media=False,
        )

        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.intent(session_id=ledger.session,
                                  media_key_value=key)
        self.assertEqual(raised.exception.args[0], 'STALE_MEDIA_INVENTORY')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_summary_does_not_count_stale_detail_or_inventory_as_complete(self):
        ledger = self.new_ledger('summary-stale-coverage')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='summary-stale-coverage-media')
        post, post_key_value = self.observe_post(
            ledger, 'summary-stale-coverage-post', [identity])

        self.scan_with_pages(ledger, [([post], [])])
        summary = self.reopen(ledger).summary()
        self.assertFalse(summary['all_known_media_complete'])
        self.assertIn('STALE_POST_DETAIL', summary['dispatch_blockers'])
        self.assertIn('STALE_MEDIA_INVENTORY', summary['dispatch_blockers'])
        row = next(item for item in summary['posts']
                   if item['post_key'] == post_key_value)
        self.assertEqual(row['state'], 'DETAIL_PENDING')
        self.assertEqual(row['media'], [])

        ledger.records.record_post(
            session_id=ledger.session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=1,
            text_sha256=None,
            evidence=ledger.evidence_for_post(post_key_value),
            no_media=False,
        )
        summary = self.reopen(ledger).summary()
        self.assertFalse(summary['all_known_media_complete'])
        self.assertNotIn('STALE_POST_DETAIL', summary['dispatch_blockers'])
        self.assertIn('STALE_MEDIA_INVENTORY', summary['dispatch_blockers'])
        row = next(item for item in summary['posts']
                   if item['post_key'] == post_key_value)
        self.assertEqual(row['media'], [])

    def test_summary_blocks_unbound_legacy_detail_and_inventory(self):
        ledger = self.new_ledger('summary-legacy-unbound')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='summary-legacy-unbound-media')
        post, post_key_value = self.observe_post(
            ledger, 'summary-legacy-unbound-post', [identity])

        self.scan_with_pages(ledger, [([post], [])])
        events = self.read_events(ledger.records)
        legacy = self.legacy_evidence(ledger, 'unbound-detail')
        for event in events:
            if event['kind'] in ('post', 'media'):
                event['data'].pop('scan_id', None)
                event['data']['evidence'] = legacy
        self.rewrite_events(ledger.records, events)

        ledger.records.record_post(
            session_id=ledger.session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=1,
            text_sha256=None,
            evidence=ledger.evidence_for_post(post_key_value),
            no_media=False,
        )
        ledger.records.record_media(
            session_id=ledger.session,
            post_key_value=post_key_value,
            items=[dict(identity=identity)],
            missing=[],
            evidence=ledger.evidence_for_post(post_key_value),
        )

        summary = self.reopen(ledger).summary()
        self.assertFalse(summary['all_known_media_complete'])
        self.assertIn('STALE_POST_DETAIL', summary['dispatch_blockers'])
        self.assertIn('STALE_MEDIA_INVENTORY', summary['dispatch_blockers'])

    def test_v2_detail_evidence_requires_bound_scan_context(self):
        for kind in ('post', 'media'):
            with self.subTest(kind=kind):
                label = 'v2-detail-scan-context-' + kind
                ledger = self.new_ledger(label)
                identities = []
                if kind == 'media':
                    identities.append(notes.media_identity(
                        kind=PHOTO, visual_key=label + '-media'))
                _post, post_key_value = self.observe_post(
                    ledger, label + '-post', identities,
                    no_media=not identities)
                context = dict(list_key=ledger.summary['list_key'],
                               post_key=post_key_value)
                source = ledger.evidence(**context)
                stored = notes._preserve_evidence(
                    ledger.records.records, source, context)
                events = self.read_events(ledger.records)
                target = next(event for event in events
                              if event['kind'] == kind)
                target['data'].pop('scan_id')
                target['data']['evidence'] = stored
                self.rewrite_events(ledger.records, events)

                with self.assertRaises(NotesError) as raised:
                    self.reopen(ledger).summary()
                self.assertEqual(
                    raised.exception.args[0],
                    'EVIDENCE_SCAN_CONTEXT_REQUIRED')

    def test_same_scan_duplicate_post_and_media_writes_are_rejected(self):
        ledger = self.new_ledger('duplicate-writer-events')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='duplicate-writer-events-media')
        _post, post_key_value = self.observe_post(
            ledger, 'duplicate-writer-events-post', [identity])
        before = self.event_bytes(ledger.records)

        with self.assertRaises(NotesError) as raised:
            ledger.records.record_post(
                session_id=ledger.session,
                post_key_value=post_key_value,
                date_summary='synthetic',
                media_count=1,
                text_sha256=None,
                evidence=ledger.evidence_for_post(post_key_value),
                no_media=False,
            )
        self.assertEqual(raised.exception.args[0],
                         'POST_DETAIL_ALREADY_RECORDED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        with self.assertRaises(NotesError) as raised:
            ledger.records.record_media(
                session_id=ledger.session,
                post_key_value=post_key_value,
                items=[dict(identity=identity)],
                missing=[],
                evidence=ledger.evidence_for_post(post_key_value),
            )
        self.assertEqual(raised.exception.args[0],
                         'MEDIA_INVENTORY_ALREADY_RECORDED')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_loader_rejects_duplicate_scan_bound_post_and_media(self):
        for kind in ('post', 'media'):
            with self.subTest(kind=kind):
                ledger = self.new_ledger('duplicate-loader-' + kind)
                identity = notes.media_identity(
                    kind=PHOTO,
                    visual_key='duplicate-loader-%s-media' % kind)
                self.observe_post(
                    ledger, 'duplicate-loader-%s-post' % kind, [identity])
                events = self.read_events(ledger.records)
                index = next(index for index, event in enumerate(events)
                             if event['kind'] == kind)
                duplicate = json.loads(json.dumps(events[index]))
                events.insert(index + 1, duplicate)
                self.rewrite_events(ledger.records, events)

                expected = ('POST_DETAIL_ALREADY_RECORDED'
                            if kind == 'post'
                            else 'MEDIA_INVENTORY_ALREADY_RECORDED')
                with self.assertRaises(NotesError) as raised:
                    self.reopen(ledger).summary()
                self.assertEqual(raised.exception.args[0], expected)

    def test_unbound_intent_verify_and_resume_fail_closed(self):
        ledger = self.new_ledger('unbound-intent')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='unbound-intent-media')
        _post, post_key_value = self.observe_post(
            ledger, 'unbound-intent-post', [identity])
        key = self.media_key(ledger, post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        events = self.read_events(ledger.records)
        intent = next(event for event in events
                      if event['kind'] == 'intent' and
                      event['data']['attempt_id'] == attempt['attempt_id'])
        intent['data'].pop('scan_id')
        intent['data']['schema'] = 'line-notes-intent/v1'
        intent['data'].pop('effective_kind')
        intent['data'].pop('kind_correction_ref')
        self.rewrite_events(ledger.records, events)
        reopened = self.reopen(ledger)
        before = self.event_bytes(ledger.records)

        with self.assertRaises(NotesError) as raised:
            reopened.verify(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                verifier=self.pass_verifier,
                stability_interval=0,
            )
        self.assertEqual(raised.exception.args[0],
                         'INTENT_SCAN_BINDING_REQUIRED')
        self.assertEqual(self.event_bytes(ledger.records), before)
        resumed = reopened.resume()
        self.assertEqual(resumed['pending'][0]['action'],
                         'SCAN_BINDING_REVIEW_REQUIRED')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_verify_and_pending_resume_reject_attempt_after_new_scan(self):
        ledger = self.new_ledger('cross-scan-attempt')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='cross-scan-attempt-media')
        post, post_key_value = self.observe_post(
            ledger, 'cross-scan-attempt-post', [identity])
        key = self.media_key(ledger, post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        staging = Path(attempt['destination'])
        (staging / 'cross.png').write_bytes(b'synthetic cross scan media')
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(attempt),
        )

        self.append_historical_scan(ledger, [post])
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.verify(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                verifier=self.pass_verifier,
                stability_interval=0,
            )
        self.assertEqual(raised.exception.args[0],
                         'ATTEMPT_SCAN_BINDING_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        ledger2 = self.new_ledger('cross-scan-pending')
        identity2 = notes.media_identity(
            kind=PHOTO, visual_key='cross-scan-pending-media')
        post2, post_key_value2 = self.observe_post(
            ledger2, 'cross-scan-pending-post', [identity2])
        key2 = self.media_key(ledger2, post_key_value2, identity2)
        attempt2 = ledger2.records.intent(
            session_id=ledger2.session, media_key_value=key2)
        (Path(attempt2['destination']) / 'pending.png').write_bytes(
            b'synthetic pending cross scan media')
        ledger2.records.outcome(
            session_id=ledger2.session,
            attempt_id=attempt2['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger2.evidence_for_attempt(attempt2),
        )
        with mock.patch.object(
                NotesRecords, '_execute_publish',
                side_effect=OSError('synthetic publish interruption')):
            with self.assertRaisesRegex(OSError, 'synthetic publish interruption'):
                ledger2.records.verify(
                    session_id=ledger2.session,
                    attempt_id=attempt2['attempt_id'],
                    verifier=self.pass_verifier,
                    stability_interval=0,
                )

        self.append_historical_scan(ledger2, [post2])
        before = self.event_bytes(ledger2.records)
        with self.assertRaises(NotesError) as raised:
            ledger2.records.resume()
        self.assertEqual(raised.exception.args[0],
                         'SCAN_BINDING_REVIEW_REQUIRED')
        self.assertEqual(self.event_bytes(ledger2.records), before)

    def test_new_session_bind_interrupts_open_scan_and_recovery_resumes(self):
        ledger = self.new_ledger('bind-open-scan')
        post = notes.post_identity(visual_key='bind-open-scan-post')
        scan = ledger.records.scan(
            session_id=ledger.session, action='START',
            evidence=ledger.evidence_for_scan())
        ledger.records.page(
            session_id=ledger.session,
            scan_id=scan['scan_id'],
            page_index=0,
            posts=[dict(identity=post, date_summary='synthetic')],
            top_reached=True,
            bottom_reached=True,
            overlap_keys=[],
            evidence=ledger.evidence_for_scan(scan['scan_id']),
        )
        before = self.event_bytes(ledger.records)
        new_session = 'new-session-during-open-scan'
        rebound = self.reopen(ledger)
        rebound.bind(
            session_id=new_session,
            observation=ledger.evidence_for_scan(),
            handoff=ledger.evidence_for_scan(),
        )
        after_bind = self.event_bytes(rebound)
        for name, raw in before.items():
            self.assertEqual(after_bind[name], raw)

        latest, scans = rebound._open_scan()
        self.assertEqual(latest, scan['scan_id'])
        self.assertIsNone(scans[scan['scan_id']]['complete'])
        self.assertIsNone(scans[scan['scan_id']]['interrupted'])
        self.assertEqual(
            scans[scan['scan_id']]['pages'][0]['data']['posts'][0]['identity'],
            post)

        interrupted = rebound.scan(
            session_id=new_session, action='INTERRUPT',
            scan_id=scan['scan_id'], reason='synthetic foreground loss',
            evidence=ledger.evidence_for_scan(scan['scan_id']))
        self.assertEqual(interrupted['action'], 'INTERRUPTED')

        reopened = self.reopen(ledger)
        recovery = reopened.scan(
            session_id=new_session, action='START', recovery=True,
            evidence=ledger.evidence_for_scan())
        self.assertIn('scan_id', recovery)
        latest, scans = reopened._open_scan()
        self.assertEqual(latest, recovery['scan_id'])
        self.assertIsNone(scans[scan['scan_id']]['complete'])
        self.assertEqual(
            scans[scan['scan_id']]['interrupted']['data']['action'],
            'INTERRUPTED')
        self.assertEqual(len(scans[scan['scan_id']]['pages']), 1)

    def test_page_and_finish_session_mismatch_are_refused_before_append(self):
        ledger = self.new_ledger('scan-session-write-guard')
        identity = notes.post_identity(
            visual_key='scan-session-write-guard-post')
        scan = ledger.records.scan(
            session_id=ledger.session, action='START',
            evidence=ledger.evidence_for_scan())
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.page(
                session_id='wrong-session',
                scan_id=scan['scan_id'],
                page_index=0,
                posts=[dict(identity=identity, date_summary='synthetic')],
                top_reached=True,
                bottom_reached=True,
                overlap_keys=[],
                evidence=ledger.evidence_for_scan(scan['scan_id']),
            )
        self.assertEqual(raised.exception.args[0], 'PAGE_SESSION_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        ledger.records.page(
            session_id=ledger.session,
            scan_id=scan['scan_id'],
            page_index=0,
            posts=[dict(identity=identity, date_summary='synthetic')],
            top_reached=True,
            bottom_reached=True,
            overlap_keys=[],
            evidence=ledger.evidence_for_scan(scan['scan_id']),
        )
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.scan(
                session_id='wrong-session',
                action='FINISH',
                scan_id=scan['scan_id'],
                evidence=ledger.evidence_for_scan(scan['scan_id']),
            )
        self.assertEqual(raised.exception.args[0], 'SCAN_SESSION_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_zero_post_scan_remains_fail_closed(self):
        ledger = self.new_ledger('zero-post-scan')
        scan = ledger.records.scan(
            session_id=ledger.session, action='START',
            evidence=ledger.evidence_for_scan())
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.page(
                session_id=ledger.session,
                scan_id=scan['scan_id'],
                page_index=0,
                posts=[],
                top_reached=True,
                bottom_reached=True,
                overlap_keys=[],
                evidence=ledger.evidence_for_scan(scan['scan_id']),
            )
        self.assertEqual(raised.exception.args[0], 'EMPTY_PAGE_NOT_ALLOWED')
        self.assertEqual(self.event_bytes(ledger.records), before)
        with self.assertRaises(NotesError) as raised:
            ledger.records.scan(
                session_id=ledger.session,
                action='FINISH',
                scan_id=scan['scan_id'],
                evidence=ledger.evidence_for_scan(scan['scan_id']),
            )
        self.assertEqual(raised.exception.args[0], 'SCAN_REQUIRES_PAGE')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_page_overlap_loader_rejects_invalid_shapes(self):
        cases = (
            ('previous_tail', [0, 3], [0], 'OVERLAP_NOT_PREVIOUS_TAIL'),
            ('next_head', [3, 2], [2], 'OVERLAP_NOT_NEXT_HEAD'),
            ('empty_page', [], [], 'EMPTY_PAGE_NOT_ALLOWED'),
            ('duplicate_outside_overlap', [2, 1, 3], [2],
             'PAGE_DUPLICATE_REQUIRES_OVERLAP'),
        )
        for label, page_indexes, overlap_indexes, expected in cases:
            with self.subTest(case=label):
                ledger = self.new_ledger('overlap-' + label)
                identities = [
                    notes.post_identity(visual_key='overlap-%s-%d' % (label, index))
                    for index in range(4)
                ]
                self.scan_with_pages(
                    ledger,
                    [(identities[:3], []), ([identities[2], identities[3]],
                                             [identities[2]])],
                )
                self.mutate_page(
                    ledger, 1,
                    [identities[index] for index in page_indexes],
                    [identities[index] for index in overlap_indexes],
                )
                with self.assertRaises(NotesError) as raised:
                    self.reopen(ledger).summary()
                self.assertEqual(raised.exception.args[0], expected)

    def test_adjacent_page_overlap_is_accepted(self):
        ledger = self.new_ledger('overlap-valid')
        identities = [
            notes.post_identity(visual_key='overlap-valid-%d' % index)
            for index in range(4)
        ]
        self.scan_with_pages(
            ledger,
            [(identities[:3], []), (identities[1:], identities[1:3])],
        )
        summary = self.reopen(ledger).summary()
        expected = [
            notes.post_key(ledger.summary['list_key'], identity)
            for identity in identities
        ]
        self.assertEqual([row['post_key'] for row in summary['posts']], expected)

    def test_loader_rejects_scan_completion_posts_mismatch(self):
        ledger = self.new_ledger('scan-completion-posts')
        self.observe_without_detail(ledger, 'scan-completion-posts-real')
        events = self.read_events(ledger.records)
        complete = next(
            event for event in events
            if event['kind'] == 'scan' and
            event['data']['action'] == 'COMPLETE')
        fake_identity = notes.post_identity(
            visual_key='scan-completion-posts-fake')
        complete['data']['posts'].append(dict(
            post_key=notes.post_key(
                ledger.summary['list_key'], fake_identity),
            identity=fake_identity,
            date_summary='fake',
            source_order=len(complete['data']['posts']),
        ))
        self.rewrite_events(ledger.records, events)

        with self.assertRaisesRegex(
                NotesError, 'SCAN_COMPLETION_POSTS_CHANGED'):
            self.reopen(ledger).summary()

    def test_loader_rejects_terminal_state_over_active_attempt(self):
        ledger = self.new_ledger('terminal-active-attempt')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='terminal-active-attempt-media')
        _post, post_key_value = self.observe_post(
            ledger, 'terminal-active-attempt-post', [identity])
        key = self.media_key(ledger, post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='UNKNOWN',
            evidence=ledger.evidence_for_attempt(attempt),
        )
        events = self.read_events(ledger.records)
        media_event = next(event for event in events
                           if event['kind'] == 'media')
        events.append(dict(
            sequence=0,
            previous_sha256=None,
            local_list_id=ledger.records.records.name,
            kind='exclusion',
            data=dict(
                schema='line-notes-exclusion/v1',
                media_key=key,
                reason='synthetic terminal mutation',
                evidence=ledger.stored_evidence_for_media(key),
            ),
        ))
        self.rewrite_events(ledger.records, events)

        with self.assertRaisesRegex(
                NotesError, 'TERMINAL_MEDIA_WITH_ACTIVE_ATTEMPT'):
            self.reopen(ledger).summary()

    def run_progress_script(self, script, *, stall_timeout=2):
        return run_decode_command(
            [sys.executable, '-c', script],
            stream_index=0,
            stall_timeout=stall_timeout,
        )

    def test_decode_stall_after_stdout_eof_is_bounded(self):
        started = time.monotonic()
        with self.assertRaises(MediaVerificationError) as raised:
            run_decode_command(
                [sys.executable, '-c', 'pass'],
                stream_index=0,
                stall_timeout=0.05,
                popen_factory=_EofThenHangs,
            )
        elapsed = time.monotonic() - started
        self.assertEqual(raised.exception.code, 'DECODE_STALLED')
        self.assertLess(elapsed, 2.0)

    def test_duplicate_progress_end_is_rejected(self):
        script = (
            'import sys\n'
            "sys.stdout.write('frame=1\\nout_time_us=100000\\nprogress=end\\n')\n"
            "sys.stdout.write('frame=2\\nout_time_us=200000\\nprogress=end\\n')\n"
        )
        with self.assertRaises(MediaVerificationError) as raised:
            self.run_progress_script(script)
        self.assertEqual(raised.exception.code, 'INVALID_PROGRESS')

    def test_regressing_progress_metrics_are_rejected(self):
        script = (
            'import sys\n'
            "sys.stdout.write('frame=10\\nout_time_us=1000000\\nprogress=continue\\n')\n"
            "sys.stdout.write('frame=5\\nout_time_us=500000\\nprogress=end\\n')\n"
        )
        with self.assertRaises(MediaVerificationError) as raised:
            self.run_progress_script(script)
        self.assertEqual(raised.exception.code, 'INVALID_PROGRESS')

    def test_end_block_without_coverage_metrics_is_rejected(self):
        script = (
            'import sys\n'
            "sys.stdout.write('frame=1\\nout_time_us=100000\\nprogress=continue\\n')\n"
            "sys.stdout.write('progress=end\\n')\n"
        )
        with self.assertRaises(MediaVerificationError) as raised:
            self.run_progress_script(script)
        self.assertIn(raised.exception.code,
                      {'INVALID_PROGRESS', 'DECODE_PROGRESS_WITHOUT_METRICS'})

    def test_evidence_audit_reports_outer_drift_and_refuses_projection(self):
        ledger = self.new_ledger('audit-outer-drift')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='audit-outer-drift-media')
        self.observe_post(ledger, 'audit-outer-drift-post', [identity])
        before = self.event_bytes(ledger.records)

        audit = ledger.records.evidence_audit()
        self.assertEqual(audit['schema'], 'line-notes-evidence-audit/v1')
        self.assertEqual(audit['event_chain'], 'VERIFIED')
        self.assertTrue(audit['integrity_ok'])
        self.assertTrue(audit['business_projection_omitted'])
        self.assertTrue(audit['references'])
        self.assertNotIn('status_counts', audit)
        self.assertNotIn('posts', audit)
        self.assertTrue(all(row['integrity_ok']
                            for row in audit['references']))
        self.assertEqual(self.event_bytes(ledger.records), before)

        code, payload = self.run_notes_cli(
            'evidence-audit', '--records-root', ledger.records.records)
        self.assertEqual(code, 0)
        self.assertTrue(payload['integrity_ok'])
        self.assertFalse(payload['dispatch_authorized'])

        events = self.read_events(ledger.records)
        page = next(event for event in events if event['kind'] == 'page')
        Path(page['data']['evidence']['path']).write_bytes(
            b'tampered saved evidence bundle\n')
        before = self.event_bytes(ledger.records)
        audit = ledger.records.evidence_audit()
        self.assertFalse(audit['integrity_ok'])
        row = next(row for row in audit['references']
                   if row['event_sequence'] == page['sequence'])
        self.assertFalse(row['integrity_ok'])
        self.assertIn('EVIDENCE_DRIFT', row['errors'])
        self.assertEqual(self.event_bytes(ledger.records), before)

        with self.assertRaises(NotesError) as raised:
            ledger.records.summary()
        self.assertEqual(raised.exception.args[0], 'EVIDENCE_DRIFT')

        code, payload = self.run_notes_cli(
            'evidence-audit', '--records-root', ledger.records.records)
        self.assertEqual(code, 4)
        self.assertFalse(payload['integrity_ok'])
        self.assertTrue(payload['business_projection_omitted'])
        self.assertNotIn('status_counts', payload)
        self.assertFalse(payload['dispatch_authorized'])

    def test_evidence_audit_reports_child_missing_and_symlink_drift(self):
        for case in ('missing', 'symlink'):
            with self.subTest(case=case):
                ledger = self.new_ledger('audit-child-' + case)
                identity = notes.media_identity(
                    kind=PHOTO, visual_key='audit-child-' + case + '-media')
                self.observe_post(
                    ledger, 'audit-child-' + case + '-post', [identity])
                events = self.read_events(ledger.records)
                page = next(event for event in events
                            if event['kind'] == 'page')
                bundle = json.loads(
                    Path(page['data']['evidence']['path']).read_bytes())
                child = (ledger.records.records / 'evidence' /
                         bundle['assets'][0]['sha256'])
                child.unlink()
                if case == 'symlink':
                    child.symlink_to(ledger.evidence_source)

                audit = ledger.records.evidence_audit()
                self.assertFalse(audit['integrity_ok'])
                row = next(row for row in audit['references']
                           if row['event_sequence'] == page['sequence'])
                self.assertFalse(row['integrity_ok'])
                self.assertEqual(row['reference_check'],
                                 'REFERENCE_CHECK_NOT_AVAILABLE')
                self.assertTrue(any(
                    child_row['status'] == 'DRIFT' and
                    child_row['error'] == 'EVIDENCE_CHILD_MISSING'
                    for child_row in row['child_assets']))
                with self.assertRaises(NotesError) as raised:
                    ledger.records.summary()
                self.assertEqual(raised.exception.args[0],
                                 'EVIDENCE_CHILD_MISSING')

    def test_evidence_audit_stops_on_malformed_structural_ref(self):
        ledger = self.new_ledger('audit-malformed-ref')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='audit-malformed-ref-media')
        self.observe_post(ledger, 'audit-malformed-ref-post', [identity])
        events = self.read_events(ledger.records)
        page = next(event for event in events if event['kind'] == 'page')
        page['data']['evidence'].pop('sha256')
        self.rewrite_events(ledger.records, events)
        before = self.event_bytes(ledger.records)

        with self.assertRaises(NotesError) as raised:
            ledger.records.evidence_audit()
        self.assertEqual(raised.exception.args[0], 'INVALID_PAGE_EVENT')
        code, payload = self.run_notes_cli(
            'evidence-audit', '--records-root', ledger.records.records)
        self.assertEqual(code, 4)
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertEqual(payload['reason'], 'INVALID_PAGE_EVENT')
        self.assertNotIn('integrity_ok', payload)
        self.assertNotIn('status_counts', payload)
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_evidence_audit_keeps_legacy_page_opaque_and_exits_zero(self):
        ledger = self.new_ledger('audit-legacy-page')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='audit-legacy-page-media')
        self.observe_post(ledger, 'audit-legacy-page-post', [identity])
        events = self.read_events(ledger.records)
        page = next(event for event in events if event['kind'] == 'page')
        page['data']['evidence'] = self.legacy_evidence(
            ledger, 'audit-legacy-page')
        self.rewrite_events(ledger.records, events)
        before = self.event_bytes(ledger.records)

        audit = ledger.records.evidence_audit()
        self.assertTrue(audit['integrity_ok'])
        row = next(row for row in audit['references']
                   if row['event_sequence'] == page['sequence'])
        self.assertEqual(row['classification'], 'LEGACY_OPAQUE')
        self.assertEqual(row['reference_check'],
                         'REFERENCE_CHECK_NOT_AVAILABLE')
        self.assertTrue(row['integrity_ok'])
        self.assertEqual(self.event_bytes(ledger.records), before)
        summary = ledger.records.summary()
        self.assertEqual(summary['evidence_corrections'], [])

        code, payload = self.run_notes_cli(
            'evidence-audit', '--records-root', ledger.records.records)
        self.assertEqual(code, 0)
        self.assertTrue(payload['integrity_ok'])
        self.assertFalse(payload['dispatch_authorized'])

    def test_evidence_correction_appends_only_to_exact_target_and_chain(self):
        ledger = self.new_ledger('evidence-correction-chain')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='evidence-correction-chain-media')
        self.observe_post(ledger, 'evidence-correction-chain-post', [identity])
        events = self.read_events(ledger.records)
        page = next(event for event in events if event['kind'] == 'page')
        scan = next(event for event in events
                    if event['kind'] == 'scan' and
                    event['data']['action'] == 'START')
        page_sequence = page['sequence']
        page_sha256 = digest(encoded(page))
        original_sha256 = page['data']['evidence']['sha256']
        scan_id = page['data']['scan_id']
        replacement = ledger.evidence(
            list_key=ledger.summary['list_key'], scan_id=scan_id)

        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.evidence_correct(
                session_id=ledger.session,
                page_sequence=scan['sequence'],
                page_sha256=page_sha256,
                original_evidence_sha256=original_sha256,
                replacement=replacement,
                reason='synthetic correction',
            )
        self.assertEqual(raised.exception.args[0],
                         'EVIDENCE_CORRECTION_TARGET_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        with self.assertRaises(NotesError) as raised:
            ledger.records.evidence_correct(
                session_id=ledger.session,
                page_sequence=page_sequence,
                page_sha256='0' * 64,
                original_evidence_sha256=original_sha256,
                replacement=replacement,
                reason='synthetic correction',
            )
        self.assertEqual(raised.exception.args[0],
                         'EVIDENCE_CORRECTION_TARGET_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        with self.assertRaises(NotesError) as raised:
            ledger.records.evidence_correct(
                session_id=ledger.session,
                page_sequence=page_sequence,
                page_sha256=page_sha256,
                original_evidence_sha256='0' * 64,
                replacement=replacement,
                reason='synthetic correction',
            )
        self.assertEqual(raised.exception.args[0],
                         'EVIDENCE_CORRECTION_ORIGINAL_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        with self.assertRaises(NotesError) as raised:
            ledger.records.evidence_correct(
                session_id=ledger.session,
                page_sequence=page_sequence,
                page_sha256=page_sha256,
                original_evidence_sha256=original_sha256,
                replacement=replacement,
                reason='synthetic correction',
                previous_correction_ref=dict(
                    sequence=1, sha256='0' * 64),
            )
        self.assertEqual(raised.exception.args[0],
                         'EVIDENCE_CORRECTION_CHAIN_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        first = ledger.records.evidence_correct(
            session_id=ledger.session,
            page_sequence=page_sequence,
            page_sha256=page_sha256,
            original_evidence_sha256=original_sha256,
            replacement=replacement,
            reason='synthetic correction',
        )
        self.assertEqual(first['schema'],
                         'line-notes-evidence-correction/v1')
        after_first = self.event_bytes(ledger.records)
        self.assertEqual(set(before) - set(after_first), set())
        for name, raw in before.items():
            self.assertEqual(after_first[name], raw)
        summary = ledger.records.summary()
        self.assertEqual(len(summary['evidence_corrections']), 1)
        self.assertEqual(summary['evidence_corrections'][0]['sequence'],
                         first['correction_ref']['sequence'])

        second = ledger.records.evidence_correct(
            session_id=ledger.session,
            page_sequence=page_sequence,
            page_sha256=page_sha256,
            original_evidence_sha256=original_sha256,
            replacement=replacement,
            reason='synthetic repeated correction',
            previous_correction_ref=first['correction_ref'],
        )
        summary = ledger.records.summary()
        self.assertEqual(len(summary['evidence_corrections']), 2)
        self.assertEqual(
            summary['evidence_corrections'][1]['previous_correction_ref'],
            first['correction_ref'])
        self.assertEqual(second['previous_correction_ref'],
                         first['correction_ref'])

        before_fork = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.evidence_correct(
                session_id=ledger.session,
                page_sequence=page_sequence,
                page_sha256=page_sha256,
                original_evidence_sha256=original_sha256,
                replacement=replacement,
                reason='synthetic forked correction',
            )
        self.assertEqual(raised.exception.args[0],
                         'EVIDENCE_CORRECTION_CHAIN_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before_fork)

        events = self.read_events(ledger.records)
        correction = [event for event in events
                      if event['kind'] == 'evidence-correction'][-1]
        correction['data']['previous_correction_ref'] = None
        self.rewrite_events(ledger.records, events)
        with self.assertRaises(NotesError) as raised:
            self.reopen(ledger).summary()
        self.assertEqual(raised.exception.args[0],
                         'EVIDENCE_CORRECTION_CHAIN_CHANGED')

    def test_evidence_correction_scopes_to_target_page_and_scan(self):
        ledger = self.new_ledger('evidence-correction-scope')
        post_a = notes.post_identity(visual_key='evidence-scope-a')
        post_b = notes.post_identity(visual_key='evidence-scope-b')
        self.scan_with_pages(
            ledger, [([post_a], []), ([post_a, post_b], [post_a])])
        events = self.read_events(ledger.records)
        pages = [event for event in events if event['kind'] == 'page']
        self.assertEqual(len(pages), 2)
        Path(pages[1]['data']['evidence']['path']).write_bytes(
            b'tampered non-target page evidence\n')
        replacement = ledger.evidence(
            list_key=ledger.summary['list_key'],
            scan_id=pages[0]['data']['scan_id'])
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.evidence_correct(
                session_id=ledger.session,
                page_sequence=pages[0]['sequence'],
                page_sha256=digest(encoded(pages[0])),
                original_evidence_sha256=pages[0]['data']['evidence']['sha256'],
                replacement=replacement,
                reason='synthetic target-only correction',
            )
        self.assertEqual(raised.exception.args[0],
                         'EVIDENCE_REPAIR_SCOPE_MISMATCH')
        self.assertEqual(self.event_bytes(ledger.records), before)

        ledger2 = self.new_ledger('evidence-correction-scan-context')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='evidence-correction-scan-context-media')
        post, _post_key = self.observe_post(
            ledger2, 'evidence-correction-scan-context-post', [identity])
        page = next(event for event in self.read_events(ledger2.records)
                    if event['kind'] == 'page')
        original_scan_id = page['data']['scan_id']
        unique_statement = ledger2.photo_root.parent / 'unique-page-evidence.txt'
        unique_statement.write_bytes(b'unique page evidence statement\n')
        page_context = dict(list_key=ledger2.summary['list_key'],
                            scan_id=original_scan_id)
        unique_page_bundle = notes_evidence.create_bundle(
            statement=str(unique_statement),
            assets=[('screenshot', str(ledger2.evidence_screenshot))],
            context=page_context,
            output_dir=str(ledger2.evidence_packs / uuid.uuid4().hex),
        )['bundle_path']
        events = self.read_events(ledger2.records)
        page = next(event for event in events if event['kind'] == 'page')
        page['data']['evidence'] = notes._preserve_evidence(
            ledger2.records.records, unique_page_bundle, page_context)
        self.rewrite_events(ledger2.records, events)
        ledger2.records = self.reopen(ledger2)
        ledger2.records.summary()
        page = next(event for event in self.read_events(ledger2.records)
                    if event['kind'] == 'page')
        original_sha256 = page['data']['evidence']['sha256']
        self.append_historical_scan(ledger2, [post])
        latest_scan_id = ledger2.records._latest_complete_scan_id()
        latest_replacement = ledger2.evidence(
            list_key=ledger2.summary['list_key'], scan_id=latest_scan_id)
        target_replacement = ledger2.evidence(
            list_key=ledger2.summary['list_key'], scan_id=original_scan_id)
        Path(page['data']['evidence']['path']).write_bytes(
            b'tampered original page evidence\n')
        before = self.event_bytes(ledger2.records)
        with self.assertRaises(NotesError) as raised:
            ledger2.records.evidence_correct(
                session_id=ledger2.session,
                page_sequence=page['sequence'],
                page_sha256=digest(encoded(page)),
                original_evidence_sha256=original_sha256,
                replacement=latest_replacement,
                reason='synthetic wrong scan context',
            )
        self.assertEqual(raised.exception.args[0], 'EVIDENCE_CONTEXT_MISMATCH')
        self.assertEqual(self.event_bytes(ledger2.records), before)

        correction = ledger2.records.evidence_correct(
            session_id=ledger2.session,
            page_sequence=page['sequence'],
            page_sha256=digest(encoded(page)),
            original_evidence_sha256=original_sha256,
            replacement=target_replacement,
            reason='synthetic target scan correction',
        )
        summary = ledger2.records.summary()
        self.assertEqual(len(summary['evidence_corrections']), 1)
        self.assertEqual(summary['evidence_corrections'][0]['page_sequence'],
                         page['sequence'])
        self.assertEqual(correction['replacement_ref']['sha256'],
                         summary['evidence_corrections'][0]
                         ['replacement_ref']['sha256'])

        audit = ledger2.records.evidence_audit()
        self.assertFalse(audit['integrity_ok'])
        page_row = next(row for row in audit['references']
                        if row['event_sequence'] == page['sequence'])
        self.assertIn('EVIDENCE_DRIFT', page_row['errors'])
        correction_row = next(
            row for row in audit['references']
            if row.get('event_kind') == 'evidence-correction' and
            row.get('event_page_sequence') == page['sequence'])
        self.assertTrue(correction_row['integrity_ok'])

    def test_media_kind_correction_preserves_nineteen_items_and_v2_attempt(self):
        ledger = self.new_ledger('kind-correction-nineteen')
        identities = [
            notes.media_identity(
                kind=PHOTO, visual_key='kind-correction-%02d' % index)
            for index in range(19)]
        _post, post_key_value = self.observe_post(
            ledger, 'kind-correction-nineteen-post', identities)
        list_key_value = ledger.summary['list_key']
        events = self.read_events(ledger.records)
        media_event = next(event for event in events
                           if event['kind'] == 'media')
        scan_id = media_event['data']['scan_id']
        items = media_event['data']['items']
        self.assertEqual(len(items), 19)
        before_summary = ledger.records.summary()
        before_media = {row['media_key']: row
                        for row in before_summary['media']}
        self.assertEqual(len(before_media), 19)
        before_status = dict(before_summary['status_counts'])
        before_bytes = self.event_bytes(ledger.records)
        inventory_sha256 = digest(encoded(media_event))

        for index, item in enumerate(items):
            evidence = ledger.evidence(
                list_key=list_key_value, post_key=post_key_value,
                media_key=item['media_key'], scan_id=scan_id)
            ledger.records.media_kind_correct(
                session_id=ledger.session,
                media_key_value=item['media_key'],
                inventory_sequence=media_event['sequence'],
                inventory_sha256=(inventory_sha256 if index == 0 else None),
                to_kind=VIDEO,
                evidence=evidence,
            )

        after_summary = ledger.records.summary()
        after_media = {row['media_key']: row
                       for row in after_summary['media']}
        self.assertEqual(set(after_media), set(before_media))
        self.assertEqual(len(after_media), 19)
        self.assertEqual(after_summary['status_counts'], before_status)
        for key, before_row in before_media.items():
            after_row = after_media[key]
            self.assertEqual(after_row['post_key'], before_row['post_key'])
            self.assertEqual(after_row['source_order'],
                             before_row['source_order'])
            self.assertEqual(after_row['kind'], PHOTO)
            self.assertEqual(after_row['effective_kind'], VIDEO)
            self.assertIsNotNone(after_row['kind_correction_ref'])
        after_bytes = self.event_bytes(ledger.records)
        for name, raw in before_bytes.items():
            self.assertEqual(after_bytes[name], raw)
        self.assertEqual(len(after_bytes), len(before_bytes) + 19)

        reopened = self.reopen(ledger)
        reopened_summary = reopened.summary()
        self.assertEqual(
            {row['effective_kind'] for row in reopened_summary['media']},
            {VIDEO})
        key = items[0]['media_key']
        attempt = reopened.intent(
            session_id=ledger.session, media_key_value=key)
        self.assertEqual(attempt['schema'], 'line-notes-intent/v2')
        self.assertEqual(attempt['identity']['kind'], PHOTO)
        self.assertEqual(attempt['effective_kind'], VIDEO)
        self.assertIsNotNone(attempt['kind_correction_ref'])
        self.assertEqual(attempt['scan_id'], scan_id)

        target = Path(attempt['destination']) / 'corrected-kind.mp4'
        target.write_bytes(b'synthetic corrected video bytes')
        reopened.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(attempt),
        )
        with self.strict_dispatch(self.strict_pass) as calls:
            completion = reopened.verify(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                stability_interval=0,
                stall_seconds=0.01,
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], VIDEO)
        self.assertEqual(completion['kind'], 'completion')
        self.assertEqual(reopened.summary()['status_counts']['COMPLETED'], 1)

    def test_media_kind_correction_rejects_scope_hash_and_stale_scan(self):
        ledger = self.new_ledger('kind-correction-scope')
        post_a = notes.post_identity(visual_key='kind-scope-a')
        post_b = notes.post_identity(visual_key='kind-scope-b')
        list_key_value = ledger.summary['list_key']
        scan = self.scan_with_pages(ledger, [([post_a, post_b], [])])
        post_key_a = notes.post_key(list_key_value, post_a)
        post_key_b = notes.post_key(list_key_value, post_b)
        identity_a0 = notes.media_identity(
            kind=PHOTO, visual_key='kind-scope-a-0')
        identity_a1 = notes.media_identity(
            kind=PHOTO, visual_key='kind-scope-a-1')
        identity_b0 = notes.media_identity(
            kind=PHOTO, visual_key='kind-scope-b-0')
        ledger.records.record_post(
            session_id=ledger.session, post_key_value=post_key_a,
            date_summary='synthetic', media_count=2, text_sha256=None,
            evidence=ledger.evidence(
                list_key=list_key_value, post_key=post_key_a,
                scan_id=scan['scan_id']),
            scan_id=scan['scan_id'])
        ledger.records.record_media(
            session_id=ledger.session, post_key_value=post_key_a,
            items=[{'identity': identity_a0}, {'identity': identity_a1}],
            missing=[], evidence=ledger.evidence(
                list_key=list_key_value, post_key=post_key_a,
                scan_id=scan['scan_id']),
            scan_id=scan['scan_id'])
        ledger.records.record_post(
            session_id=ledger.session, post_key_value=post_key_b,
            date_summary='synthetic', media_count=1, text_sha256=None,
            evidence=ledger.evidence(
                list_key=list_key_value, post_key=post_key_b,
                scan_id=scan['scan_id']),
            scan_id=scan['scan_id'])
        ledger.records.record_media(
            session_id=ledger.session, post_key_value=post_key_b,
            items=[{'identity': identity_b0}], missing=[],
            evidence=ledger.evidence(
                list_key=list_key_value, post_key=post_key_b,
                scan_id=scan['scan_id']),
            scan_id=scan['scan_id'])
        events = self.read_events(ledger.records)
        media_a = next(event for event in events
                       if event['kind'] == 'media' and
                       event['data']['post_key'] == post_key_a)
        media_b = next(event for event in events
                       if event['kind'] == 'media' and
                       event['data']['post_key'] == post_key_b)
        key_b = notes.media_key(list_key_value, post_key_b, identity_b0)
        evidence_b = ledger.evidence(
            list_key=list_key_value, post_key=post_key_b,
            media_key=key_b, scan_id=scan['scan_id'])

        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.media_kind_correct(
                session_id=ledger.session, media_key_value=key_b,
                inventory_sequence=media_b['sequence'],
                inventory_sha256='0' * 64, to_kind=VIDEO,
                evidence=evidence_b)
        self.assertEqual(raised.exception.args[0],
                         'MEDIA_KIND_INVENTORY_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        with self.assertRaises(NotesError) as raised:
            ledger.records.media_kind_correct(
                session_id=ledger.session, media_key_value=key_b,
                inventory_sequence=media_a['sequence'], to_kind=VIDEO,
                evidence=evidence_b)
        self.assertEqual(raised.exception.args[0],
                         'MEDIA_KIND_SCOPE_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        self.append_historical_scan(ledger, [post_a, post_b])
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.media_kind_correct(
                session_id=ledger.session, media_key_value=key_b,
                inventory_sequence=media_b['sequence'], to_kind=VIDEO,
                evidence=evidence_b)
        self.assertEqual(raised.exception.args[0],
                         'MEDIA_KIND_SCAN_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_media_kind_correction_rejects_after_attempt_or_completion(self):
        ledger = self.new_ledger('kind-correction-after-attempt')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='kind-correction-after-attempt-media')
        _post, post_key_value = self.observe_post(
            ledger, 'kind-correction-after-attempt-post', [identity])
        list_key_value = ledger.summary['list_key']
        key = notes.media_key(list_key_value, post_key_value, identity)
        events = self.read_events(ledger.records)
        media_event = next(event for event in events
                           if event['kind'] == 'media')
        scan_id = media_event['data']['scan_id']
        evidence = ledger.evidence(
            list_key=list_key_value, post_key=post_key_value,
            media_key=key, scan_id=scan_id)
        ledger.records.media_kind_correct(
            session_id=ledger.session, media_key_value=key,
            inventory_sequence=media_event['sequence'], to_kind=VIDEO,
            evidence=evidence)
        ledger.records.intent(session_id=ledger.session, media_key_value=key)
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.media_kind_correct(
                session_id=ledger.session, media_key_value=key,
                inventory_sequence=media_event['sequence'], to_kind=PHOTO,
                evidence=evidence)
        self.assertEqual(raised.exception.args[0], 'MEDIA_KIND_AFTER_ATTEMPT')
        self.assertEqual(self.event_bytes(ledger.records), before)

        ledger2 = self.new_ledger('kind-correction-after-completion')
        _identity2, key2, _attempt2, _completion2 = self.complete_media(
            ledger2, PHOTO, 'kind-correction-after-completion-media')
        events2 = self.read_events(ledger2.records)
        media_event2 = next(event for event in events2
                            if event['kind'] == 'media')
        scan_id2 = media_event2['data']['scan_id']
        evidence2 = ledger2.evidence(
            list_key=ledger2.summary['list_key'],
            post_key=media_event2['data']['post_key'],
            media_key=key2, scan_id=scan_id2)
        before2 = self.event_bytes(ledger2.records)
        with self.assertRaises(NotesError) as raised:
            ledger2.records.media_kind_correct(
                session_id=ledger2.session, media_key_value=key2,
                inventory_sequence=media_event2['sequence'], to_kind=VIDEO,
                evidence=evidence2)
        self.assertEqual(raised.exception.args[0], 'MEDIA_KIND_AFTER_ATTEMPT')
        self.assertEqual(self.event_bytes(ledger2.records), before2)

    def test_v1_intent_compatibility_and_forged_post_correction_order(self):
        ledger = self.new_ledger('kind-v1-intent-valid')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='kind-v1-intent-valid-media')
        _post, post_key_value = self.observe_post(
            ledger, 'kind-v1-intent-valid-post', [identity])
        key = notes.media_key(
            ledger.summary['list_key'], post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        events = self.read_events(ledger.records)
        intent_event = next(event for event in events
                            if event['kind'] == 'intent' and
                            event['data']['attempt_id'] ==
                            attempt['attempt_id'])
        intent_event['data']['schema'] = 'line-notes-intent/v1'
        intent_event['data'].pop('effective_kind')
        intent_event['data'].pop('kind_correction_ref')
        self.rewrite_events(ledger.records, events)
        (Path(attempt['destination']) / 'v1-intent.png').write_bytes(
            b'synthetic v1 intent media')
        ledger.records.outcome(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(attempt))
        completion = ledger.records.verify(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            verifier=self.pass_verifier, stability_interval=0)
        self.assertEqual(completion['kind'], 'completion')
        self.assertEqual(ledger.records.summary()['status_counts']['COMPLETED'], 1)

        ledger2 = self.new_ledger('kind-v1-intent-forged')
        identity2 = notes.media_identity(
            kind=PHOTO, visual_key='kind-v1-intent-forged-media')
        _post2, post_key2 = self.observe_post(
            ledger2, 'kind-v1-intent-forged-post', [identity2])
        key2 = notes.media_key(
            ledger2.summary['list_key'], post_key2, identity2)
        events2 = self.read_events(ledger2.records)
        media_event = next(event for event in events2
                           if event['kind'] == 'media')
        ledger2.records.media_kind_correct(
            session_id=ledger2.session, media_key_value=key2,
            inventory_sequence=media_event['sequence'], to_kind=VIDEO,
            evidence=ledger2.evidence(
                list_key=ledger2.summary['list_key'], post_key=post_key2,
                media_key=key2, scan_id=media_event['data']['scan_id']))
        attempt2 = ledger2.records.intent(
            session_id=ledger2.session, media_key_value=key2)
        events2 = self.read_events(ledger2.records)
        intent2 = next(event for event in events2
                       if event['kind'] == 'intent' and
                       event['data']['attempt_id'] == attempt2['attempt_id'])
        intent2['data']['schema'] = 'line-notes-intent/v1'
        intent2['data'].pop('effective_kind')
        intent2['data'].pop('kind_correction_ref')
        self.rewrite_events(ledger2.records, events2)
        with self.assertRaises(NotesError) as raised:
            self.reopen(ledger2).summary()
        self.assertEqual(raised.exception.args[0],
                         'V1_INTENT_AFTER_KIND_CORRECTION')

        ledger3 = self.new_ledger('kind-correction-wrong-order')
        identity3 = notes.media_identity(
            kind=PHOTO, visual_key='kind-correction-wrong-order-media')
        _post3, post_key3 = self.observe_post(
            ledger3, 'kind-correction-wrong-order-post', [identity3])
        key3 = notes.media_key(
            ledger3.summary['list_key'], post_key3, identity3)
        events3 = self.read_events(ledger3.records)
        media_event3 = next(event for event in events3
                            if event['kind'] == 'media')
        ledger3.records.media_kind_correct(
            session_id=ledger3.session, media_key_value=key3,
            inventory_sequence=media_event3['sequence'], to_kind=VIDEO,
            evidence=ledger3.evidence(
                list_key=ledger3.summary['list_key'], post_key=post_key3,
                media_key=key3, scan_id=media_event3['data']['scan_id']))
        ledger3.records.intent(session_id=ledger3.session, media_key_value=key3)
        events3 = self.read_events(ledger3.records)
        correction_index = next(
            index for index, event in enumerate(events3)
            if event['kind'] == 'media-kind-correction')
        intent_index = next(
            index for index, event in enumerate(events3)
            if event['kind'] == 'intent')
        events3[correction_index], events3[intent_index] = (
            events3[intent_index], events3[correction_index])
        self.rewrite_events(ledger3.records, events3)
        with self.assertRaises(NotesError) as raised:
            self.reopen(ledger3).summary()
        self.assertEqual(raised.exception.args[0], 'MEDIA_KIND_AFTER_ATTEMPT')

    def test_source_unavailable_preserves_incomplete_without_recovery(self):
        ledger = self.new_ledger('source-unavailable-preserve')
        identities = [
            notes.media_identity(
                kind=PHOTO, visual_key='source-unavailable-%d' % index)
            for index in range(2)]
        _post, post_key_value = self.observe_post(
            ledger, 'source-unavailable-preserve-post', identities)
        list_key_value = ledger.summary['list_key']
        key_a = notes.media_key(
            list_key_value, post_key_value, identities[0])
        key_b = notes.media_key(
            list_key_value, post_key_value, identities[1])
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key_a)
        ledger.records.outcome(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            outcome='STOPPED', evidence=ledger.evidence_for_attempt(attempt))

        before = ledger.records.summary()
        before_rows = {row['media_key']: row for row in before['media']}
        self.assertEqual(before_rows[key_a]['status'], 'PREVIOUSLY_INCOMPLETE')
        self.assertEqual(before_rows[key_a]['source_availability'], 'UNKNOWN')
        self.assertEqual(before_rows[key_b]['status'], 'PENDING')
        self.assertEqual(before_rows[key_b]['source_availability'], 'UNKNOWN')
        before_counts = dict(before['status_counts'])
        before_incomplete = before['current_incomplete']
        self.assertEqual(before_counts['PREVIOUSLY_INCOMPLETE'], 1)
        self.assertEqual(before_counts['PENDING'], 1)
        self.assertFalse(before['all_known_media_complete'])

        resume_before = ledger.records.resume()
        self.assertEqual(len(resume_before['pending']), 1)
        self.assertEqual(resume_before['pending'][0]['media_key'], key_a)
        self.assertEqual(resume_before['pending'][0]['action'],
                         'RECOVERY_REVIEW_REQUIRED')

        result = ledger.records.source_unavailable(
            session_id=ledger.session, media_key_value=key_a,
            attempt_id=attempt['attempt_id'],
            evidence=ledger.evidence_for_attempt(attempt))
        self.assertEqual(result['schema'],
                         'line-notes-source-unavailable/v1')
        self.assertEqual(result['reason'], 'SOURCE_EXPIRED')

        after = ledger.records.summary()
        after_rows = {row['media_key']: row for row in after['media']}
        self.assertEqual(after_rows[key_a]['status'],
                         'PREVIOUSLY_INCOMPLETE')
        self.assertEqual(after_rows[key_a]['source_availability'], 'EXPIRED')
        self.assertEqual(after_rows[key_b]['status'], 'PENDING')
        self.assertEqual(after_rows[key_b]['source_availability'], 'UNKNOWN')
        self.assertEqual(after['status_counts'], before_counts)
        self.assertEqual(after['current_incomplete'], before_incomplete)
        self.assertFalse(after['all_known_media_complete'])
        unresolved = {row['media_key']: row
                      for row in after['unresolved_attempts']}
        self.assertEqual(unresolved[key_a]['source_availability'], 'EXPIRED')
        self.assertEqual(unresolved[key_a]['last_result'], 'STOPPED')
        self.assertTrue(unresolved[key_a]['has_outcome'])
        self.assertNotIn(key_b, unresolved)

        before_intent = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.intent(
                session_id=ledger.session, media_key_value=key_a)
        self.assertEqual(raised.exception.args[0],
                         'SOURCE_UNAVAILABLE_NO_RECOVERY')
        self.assertEqual(self.event_bytes(ledger.records), before_intent)

        resume_after = ledger.records.resume()
        by_key = {row['media_key']: row for row in resume_after['pending']}
        self.assertEqual(by_key[key_a]['action'], 'SOURCE_UNAVAILABLE')
        self.assertFalse(resume_after['dispatch_authorized'])

        before_duplicate = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.source_unavailable(
                session_id=ledger.session, media_key_value=key_a,
                attempt_id=attempt['attempt_id'],
                evidence=ledger.evidence_for_attempt(attempt))
        self.assertEqual(raised.exception.args[0],
                         'DUPLICATE_SOURCE_UNAVAILABLE')
        self.assertEqual(self.event_bytes(ledger.records), before_duplicate)
        final = ledger.records.summary()
        self.assertEqual(final['status_counts']['COMPLETED'], 0)
        self.assertEqual(final['status_counts']['EXCLUDED'], 0)

    def test_source_unavailable_rejects_unknown_and_forged_recovery(self):
        ledger = self.new_ledger('source-unavailable-unknown')
        identity = notes.media_identity(
            kind=PHOTO, visual_key='source-unavailable-unknown-media')
        _post, post_key_value = self.observe_post(
            ledger, 'source-unavailable-unknown-post', [identity])
        key = notes.media_key(
            ledger.summary['list_key'], post_key_value, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        ledger.records.outcome(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            outcome='UNKNOWN', evidence=ledger.evidence_for_attempt(attempt))
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.source_unavailable(
                session_id=ledger.session, media_key_value=key,
                attempt_id=attempt['attempt_id'],
                evidence=ledger.evidence_for_attempt(attempt))
        self.assertEqual(raised.exception.args[0],
                         'SOURCE_UNAVAILABLE_REQUIRES_STOPPED')
        self.assertEqual(self.event_bytes(ledger.records), before)

        ledger2 = self.new_ledger('source-unavailable-forged-intent')
        identity2 = notes.media_identity(
            kind=PHOTO, visual_key='source-unavailable-forged-media')
        _post2, post_key2 = self.observe_post(
            ledger2, 'source-unavailable-forged-post', [identity2])
        key2 = notes.media_key(
            ledger2.summary['list_key'], post_key2, identity2)
        attempt2 = ledger2.records.intent(
            session_id=ledger2.session, media_key_value=key2)
        ledger2.records.outcome(
            session_id=ledger2.session, attempt_id=attempt2['attempt_id'],
            outcome='STOPPED',
            evidence=ledger2.evidence_for_attempt(attempt2))
        ledger2.records.source_unavailable(
            session_id=ledger2.session, media_key_value=key2,
            attempt_id=attempt2['attempt_id'],
            evidence=ledger2.evidence_for_attempt(attempt2))

        events = self.read_events(ledger2.records)
        original_intent = next(event for event in events
                               if event['kind'] == 'intent')
        forged = copy.deepcopy(original_intent)
        forged['data']['attempt_id'] = uuid.uuid4().hex
        forged['data']['schema'] = 'line-notes-intent/v1'
        forged['data'].pop('effective_kind')
        forged['data'].pop('kind_correction_ref')
        forged['data']['recovery_of'] = attempt2['attempt_id']
        forged['data']['recovery_evidence'] = (
            ledger2.stored_evidence_for_attempt(attempt2))
        events.append(forged)
        self.rewrite_events(ledger2.records, events)
        with self.assertRaises(NotesError) as raised:
            self.reopen(ledger2).summary()
        self.assertEqual(raised.exception.args[0],
                         'INTENT_AFTER_SOURCE_UNAVAILABLE')


if __name__ == '__main__':
    unittest.main()
