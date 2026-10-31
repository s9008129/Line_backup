"""Synthetic regressions for Notes ledger and decode fail-closed boundaries.

These tests use only generated records and local process fixtures. They do not
observe LINE, operate a GUI, or touch private media or permanent ledgers.
"""
import contextlib
import hashlib
import inspect
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

from line_backup_batch import media_verify, notes
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
STRICT_VERIFY_SIGNATURE = inspect.signature(media_verify.verify_media)


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
        self.temporary = tempfile.TemporaryDirectory(
            prefix='.line-notes-regressions-', dir=str(ROOT))
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
        photo_root = case / 'photos'
        collection_path = case / 'records'
        collection = NotesCollection(str(collection_path))
        summary = collection.create(
            photo_root=str(photo_root),
            display_name='Synthetic ' + label,
            identity=notes.list_identity(visual_key='list-' + label),
            binding_evidence=str(evidence),
            history_scope_evidence=str(evidence),
            recovery_authorized=recovery_authorized,
        )
        records = NotesRecords(
            summary['records_root'], _allow_injected_verification=True)
        session = 'session-' + label
        records.bind(session_id=session,
                     observation=str(evidence), handoff=str(evidence))
        return SimpleNamespace(
            records=records,
            summary=summary,
            collection=collection,
            photo_root=photo_root,
            evidence=evidence,
            session=session,
        )

    def reopen(self, ledger):
        return NotesRecords(str(ledger.records.records),
                            _allow_injected_verification=True)

    def observe_post(self, ledger, visual_key, media_identities, *,
                     no_media=False, media_count=None):
        records = ledger.records
        session = ledger.session
        evidence = str(ledger.evidence)
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
            evidence=evidence,
        )
        records.scan(
            session_id=session,
            action='FINISH',
            scan_id=scan['scan_id'],
            evidence=evidence,
        )
        count = 0 if no_media else (
            len(media_identities) if media_count is None else media_count)
        records.record_post(
            session_id=session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=count,
            text_sha256=None,
            evidence=evidence,
            no_media=no_media,
        )
        if media_identities:
            records.record_media(
                session_id=session,
                post_key_value=post_key_value,
                items=[{'identity': identity} for identity in media_identities],
                missing=[],
                evidence=evidence,
            )
        return post, post_key_value

    def observe_without_detail(self, ledger, visual_key):
        records = ledger.records
        session = ledger.session
        evidence = str(ledger.evidence)
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
            evidence=evidence,
        )
        records.scan(
            session_id=session,
            action='FINISH',
            scan_id=scan['scan_id'],
            evidence=evidence,
        )
        return post_key_value

    def scan_with_pages(self, ledger, pages):
        records = ledger.records
        session = ledger.session
        evidence = str(ledger.evidence)
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
                evidence=evidence,
            )
        records.scan(
            session_id=session, action='FINISH', scan_id=scan['scan_id'],
            evidence=evidence)
        return scan

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
            evidence=str(ledger.evidence),
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
            evidence=str(ledger.evidence),
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
        rows = verification_event['data']['verification']['decoded_streams']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['index'], 0)
        self.assertNotIn('stream', rows[0])

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
            outcome='UNKNOWN',
            evidence=str(ledger.evidence),
        )
        self.observe_post(
            ledger, 'summary-unknown-outside-scan-new', [], no_media=True)

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
            evidence=str(ledger.evidence),
            no_media=False,
        )
        with self.assertRaisesRegex(NotesError, 'INVALID_MEDIA_MISSING'):
            ledger.records.record_media(
                session_id=ledger.session,
                post_key_value=post_key_value,
                items=[{'identity': first}],
                missing=[{'media_key': second_key,
                          'reason': 'source order omitted'}],
                evidence=str(ledger.evidence),
            )
        data = ledger.records.record_media(
            session_id=ledger.session,
            post_key_value=post_key_value,
            items=[{'identity': first}],
            missing=[{'media_key': second_key, 'source_order': 1,
                      'reason': 'synthetic unavailable'}],
            evidence=str(ledger.evidence),
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
            evidence=str(ledger.evidence),
            no_media=False,
        )
        data = ledger.records.record_media(
            session_id=ledger.session,
            post_key_value=post_key_value,
            items=[{'identity': second}],
            missing=[{'media_key': first_key, 'source_order': 0,
                      'reason': 'synthetic unavailable'}],
            evidence=str(ledger.evidence),
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
            evidence=str(ledger.evidence),
            no_media=False,
        )
        with self.assertRaisesRegex(
                NotesError, 'POST_MEDIA_COUNT_MISMATCH'):
            ledger.records.record_media(
                session_id=ledger.session,
                post_key_value=post_key_value,
                items=[{'identity': first}, {'identity': second}],
                missing=[],
                evidence=str(ledger.evidence),
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
        self.rewrite_events(ledger.records, events)

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
        attempt = ledger.records.intent(
            session_id=ledger.session,
            media_key_value=key,
            recovery_evidence=(str(ledger.evidence)
                               if recovery_evidence else None),
        )
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=attempt['attempt_id'],
            outcome='STOPPED',
            evidence=str(ledger.evidence),
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
                recovery_evidence=str(ledger.evidence),
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
            prior_evidence = next(
                event['data']['recovery_evidence']
                for event in self.read_events(ledger.records)
                if event['kind'] == 'intent' and
                event['data']['attempt_id'] == prior['attempt_id']
            )
            self.mutate_intent(
                ledger,
                unrelated['attempt_id'],
                recovery_of=prior['attempt_id'],
                recovery_evidence=prior_evidence,
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
            evidence=str(ledger.evidence),
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
                evidence=str(ledger.evidence),
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
            evidence=str(ledger.evidence),
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
            evidence=str(ledger.evidence),
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

        events = self.read_events(ledger.records)
        for event in events:
            if event['kind'] in ('post', 'media'):
                event['data'].pop('scan_id', None)
        self.rewrite_events(ledger.records, events)

        self.scan_with_pages(ledger, [([post], [])])
        ledger.records.record_post(
            session_id=ledger.session,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=1,
            text_sha256=None,
            evidence=str(ledger.evidence),
            no_media=False,
        )
        ledger.records.record_media(
            session_id=ledger.session,
            post_key_value=post_key_value,
            items=[dict(identity=identity)],
            missing=[],
            evidence=str(ledger.evidence),
        )

        summary = self.reopen(ledger).summary()
        self.assertFalse(summary['all_known_media_complete'])
        self.assertIn('STALE_POST_DETAIL', summary['dispatch_blockers'])
        self.assertIn('STALE_MEDIA_INVENTORY', summary['dispatch_blockers'])

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
                evidence=str(ledger.evidence),
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
                evidence=str(ledger.evidence),
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
        with self.assertRaises(NotesError) as raised:
            reopened.resume()
        self.assertEqual(raised.exception.args[0],
                         'INTENT_SCAN_BINDING_REQUIRED')
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
            evidence=str(ledger.evidence),
        )

        self.scan_with_pages(ledger, [([post], [])])
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
            evidence=str(ledger2.evidence),
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

        self.scan_with_pages(ledger2, [([post2], [])])
        before = self.event_bytes(ledger2.records)
        with self.assertRaises(NotesError) as raised:
            ledger2.records.resume()
        self.assertEqual(raised.exception.args[0],
                         'ATTEMPT_SCAN_BINDING_CHANGED')
        self.assertEqual(self.event_bytes(ledger2.records), before)

    def test_bind_is_refused_while_scan_is_open(self):
        ledger = self.new_ledger('bind-open-scan')
        before = self.event_bytes(ledger.records)
        ledger.records.scan(
            session_id=ledger.session, action='START',
            evidence=str(ledger.evidence))
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.bind(
                session_id='new-session-during-open-scan',
                observation=str(ledger.evidence),
                handoff=str(ledger.evidence))
        self.assertEqual(raised.exception.args[0], 'SCAN_ALREADY_OPEN')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_page_and_finish_session_mismatch_are_refused_before_append(self):
        ledger = self.new_ledger('scan-session-write-guard')
        identity = notes.post_identity(
            visual_key='scan-session-write-guard-post')
        scan = ledger.records.scan(
            session_id=ledger.session, action='START',
            evidence=str(ledger.evidence))
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
                evidence=str(ledger.evidence),
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
            evidence=str(ledger.evidence),
        )
        before = self.event_bytes(ledger.records)
        with self.assertRaises(NotesError) as raised:
            ledger.records.scan(
                session_id='wrong-session',
                action='FINISH',
                scan_id=scan['scan_id'],
                evidence=str(ledger.evidence),
            )
        self.assertEqual(raised.exception.args[0], 'SCAN_SESSION_CHANGED')
        self.assertEqual(self.event_bytes(ledger.records), before)

    def test_zero_post_scan_remains_fail_closed(self):
        ledger = self.new_ledger('zero-post-scan')
        scan = ledger.records.scan(
            session_id=ledger.session, action='START',
            evidence=str(ledger.evidence))
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
                evidence=str(ledger.evidence),
            )
        self.assertEqual(raised.exception.args[0], 'EMPTY_PAGE_NOT_ALLOWED')
        self.assertEqual(self.event_bytes(ledger.records), before)
        with self.assertRaises(NotesError) as raised:
            ledger.records.scan(
                session_id=ledger.session,
                action='FINISH',
                scan_id=scan['scan_id'],
                evidence=str(ledger.evidence),
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
            evidence=str(ledger.evidence),
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
                evidence=media_event['data']['evidence'],
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


if __name__ == '__main__':
    unittest.main()
