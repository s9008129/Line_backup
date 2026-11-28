"""Download-only ledger checks using generated media; no LINE or real records."""
import hashlib
import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest import mock
import zipfile

from line_backup_batch import media_verify, notes
import test_notes_media_verify as media_fixtures
import test_notes_regressions as ledger_fixtures
import test_notes_restart as restart_fixtures


class DownloadOnlyTests(unittest.TestCase):
    def setUp(self):
        # Compose the fixture helper: inheriting/importing its TestCase would
        # cause unittest discovery to execute the entire regression suite twice.
        self.helper = ledger_fixtures.NotesRegressionTests()
        self.helper.setUp()
        self.addCleanup(self.helper.tearDown)
        self.decode_guard = mock.patch.object(
            media_verify, 'verify_media',
            side_effect=AssertionError('download-only must never decode media'))
        self.decode = self.decode_guard.start()
        self.addCleanup(self.decode_guard.stop)

    def attempt(self, label, *, kind=notes.VIDEO, outcome='DOWNLOAD_FINISHED',
                name='image.png', content=None):
        ledger = self.helper.new_ledger(label)
        identity = notes.media_identity(kind=kind, visual_key=label + '-media')
        _, post_key = self.helper.observe_post(
            ledger, label + '-post', [identity])
        key = notes.media_key(ledger.summary['list_key'], post_key, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        path = Path(attempt['destination']) / name
        if content is not None:
            path.write_bytes(content)
        if outcome is not None:
            ledger.records.outcome(
                session_id=ledger.session, attempt_id=attempt['attempt_id'],
                outcome=outcome, evidence=ledger.evidence_for_attempt(attempt))
        return ledger, attempt, path

    def check(self, ledger, attempt):
        return ledger.records.download_check(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            stability_interval=0)

    def prepare_basic_media(self, ledger, identity, post_key):
        key = notes.media_key(ledger.summary['list_key'], post_key, identity)
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=key)
        source = Path(attempt['destination']) / 'download.png'
        source.write_bytes(media_fixtures.png())
        ledger.records.outcome(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(attempt))
        return key, attempt

    def complete_basic_media(self, ledger, identity, post_key):
        key, attempt = self.prepare_basic_media(ledger, identity, post_key)
        return key, attempt, self.check(ledger, attempt)

    def pending_second_media(self, label):
        """Build a synthetic completed sibling plus an interrupted BASIC plan."""
        ledger = self.helper.new_ledger(label)
        first_identity = notes.media_identity(
            kind=notes.PHOTO, visual_key=label + '-first')
        second_identity = notes.media_identity(
            kind='UNCLASSIFIED', visual_key=label + '-second')
        _, post_key = self.helper.observe_post(
            ledger, label + '-post', [first_identity, second_identity])
        first_key, _first_attempt, first_completion = \
            self.complete_basic_media(
                ledger, first_identity, post_key)

        second_key = notes.media_key(
            ledger.summary['list_key'], post_key, second_identity)
        second_attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=second_key)
        source = Path(second_attempt['destination']) / 'second.png'
        source.write_bytes(media_fixtures.png())
        ledger.records.outcome(
            session_id=ledger.session,
            attempt_id=second_attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=ledger.evidence_for_attempt(second_attempt))
        with mock.patch.object(
                notes.NotesRecords, '_execute_publish',
                side_effect=OSError('synthetic publish interruption')):
            with self.assertRaisesRegex(
                    OSError, 'synthetic publish interruption'):
                self.check(ledger, second_attempt)
        plan = ledger.records._pending_publish_plans()[0]
        target = Path(plan['data']['target_directory']) / plan['data']['target_name']
        self.assertEqual(first_completion['kind'], 'completion')
        self.assertEqual(first_completion['data']['media_key'], first_key)
        return ledger, first_completion, second_attempt, source, target

    @staticmethod
    def local_file_identity(path):
        info = Path(path).lstat()
        raw = Path(path).read_bytes()
        return (info.st_dev, info.st_ino, info.st_nlink, info.st_size,
                info.st_mtime_ns, info.st_ctime_ns,
                hashlib.sha256(raw).hexdigest())

    def assert_first_completion_unchanged(self, completion, before):
        target = Path(completion['data']['destination']) / \
            completion['data']['target_file']['name']
        self.assertEqual(self.local_file_identity(target), before)

    def recovery_scan(self, ledger, post_identity, attempt, *, detail):
        """Start a new session and complete a recovery card scan.

        The optional detail step re-observes the post and its media in the new
        scan. The no-detail form models a fully covered card list whose post
        contents have not yet been opened.
        """
        records = self.helper.reopen(ledger)
        session = ledger.session + '-recovery'
        list_key = ledger.summary['list_key']
        records.bind(
            session_id=session,
            observation=ledger.evidence(list_key=list_key),
            handoff=ledger.evidence(list_key=list_key))
        scan = records.scan(
            session_id=session, action='START', recovery=True,
            evidence=ledger.evidence(list_key=list_key))
        scan_evidence = ledger.evidence(list_key=list_key,
                                        scan_id=scan['scan_id'])
        records.page(
            session_id=session, scan_id=scan['scan_id'], page_index=0,
            posts=[dict(identity=post_identity, date_summary='synthetic')],
            top_reached=True, bottom_reached=True, overlap_keys=[],
            evidence=scan_evidence)
        records.scan(session_id=session, action='FINISH',
                     scan_id=scan['scan_id'], evidence=scan_evidence)
        if detail:
            post_key = notes.post_key(list_key, post_identity)
            post_evidence = ledger.evidence(
                list_key=list_key, post_key=post_key, scan_id=scan['scan_id'])
            records.record_post(
                session_id=session, post_key_value=post_key,
                date_summary='synthetic', media_count=1, text_sha256=None,
                evidence=post_evidence)
            records.record_media(
                session_id=session, post_key_value=post_key,
                items=[dict(identity=attempt['identity'])], missing=[],
                evidence=post_evidence)
        return records, session, scan

    def assert_download_completion(self, completion, kind):
        self.assertEqual(completion['kind'], 'completion')
        data = completion['data']
        self.assertEqual(data['schema'], 'line-notes-completion/v2')
        evidence = data['verification']
        self.assertEqual(evidence['assurance'], 'DOWNLOAD_ONLY')
        self.assertEqual(evidence['verifier'], 'FILE_SIGNATURE')
        self.assertEqual(evidence['kind'], kind)
        self.assertIs(evidence['content_verified'], False)
        self.decode.assert_not_called()

    def test_video_intent_accepts_downloaded_image_without_kind_reconcile(self):
        original = media_fixtures.png()
        ledger, attempt, _ = self.attempt('video-to-image', content=original)
        before = self.helper.event_bytes(ledger.records)
        completion = self.check(ledger, attempt)
        self.assert_download_completion(completion, notes.PHOTO)
        target = Path(completion['data']['destination']) / completion['data']['target_file']['name']
        self.assertEqual(target.read_bytes(), original)
        after = self.helper.event_bytes(ledger.records)
        for name, raw in before.items():
            self.assertEqual(after[name], raw)
        events = self.helper.read_events(ledger.records)
        self.assertEqual(sum(event['kind'] == 'intent' for event in events), 1)
        self.assertFalse(any(event['kind'] == 'media-kind-reconcile' for event in events))
        summary = self.helper.reopen(ledger).summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(summary['local_counts']['VERIFIED_PRESENT'], 1)

    def test_unclassified_source_can_download_and_complete(self):
        ledger, attempt, _ = self.attempt(
            'unclassified', kind='UNCLASSIFIED', content=media_fixtures.png())
        self.assert_download_completion(self.check(ledger, attempt), notes.PHOTO)
        self.assertEqual(attempt['identity']['kind'], 'UNCLASSIFIED')

    def test_unknown_legally_resolved_to_finished_can_complete(self):
        ledger, attempt, _ = self.attempt(
            'late-finish', outcome='UNKNOWN', content=media_fixtures.png())
        ledger.records.reconcile(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            result='DOWNLOAD_FINISHED', evidence=ledger.evidence_for_attempt(attempt))
        before = self.helper.event_bytes(ledger.records)
        self.assert_download_completion(self.check(ledger, attempt), notes.PHOTO)
        after = self.helper.event_bytes(ledger.records)
        for name, raw in before.items():
            self.assertEqual(after[name], raw)
        self.assertEqual(self.helper.reopen(ledger).summary()['status_counts']['COMPLETED'], 1)

    def test_photo_intent_accepts_downloaded_video_without_decoding(self):
        if not media_verify.FFMPEG_PATH.is_file():
            self.skipTest('Homebrew ffmpeg unavailable for synthetic fixture')
        ledger, attempt, path = self.attempt(
            'photo-to-video', kind=notes.PHOTO, name='video.mp4')
        result = subprocess.run(
            [str(media_verify.FFMPEG_PATH), '-nostdin', '-hide_banner', '-v', 'error',
             '-f', 'lavfi', '-i', 'color=c=red:s=16x16:r=1', '-t', '1',
             '-c:v', 'mpeg4', '-an', str(path)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_download_completion(self.check(ledger, attempt), notes.VIDEO)
        self.assertEqual(self.helper.reopen(ledger).summary()['status_counts']['COMPLETED'], 1)

    def test_unknown_and_missing_outcome_do_not_publish(self):
        for index, outcome in enumerate((None, 'UNKNOWN', 'STOPPED')):
            with self.subTest(outcome=outcome):
                ledger, attempt, path = self.attempt(
                    'unfinished-' + str(index), outcome=outcome,
                    content=media_fixtures.png())
                before = self.helper.event_bytes(ledger.records)
                with self.assertRaises(notes.NotesError):
                    self.check(ledger, attempt)
                self.assertEqual(self.helper.event_bytes(ledger.records), before)
                self.assertTrue(path.is_file())

    def test_finished_v2_attempt_download_check_survives_recovery_scan(self):
        for detail in (False, True):
            with self.subTest(detail=detail):
                label = 'cross-scan-download-check-' + str(detail)
                ledger, attempt, _ = self.attempt(
                    label, kind=notes.VIDEO, content=media_fixtures.png())
                post_identity = notes.post_identity(visual_key=label + '-post')
                original_events = self.helper.event_bytes(ledger.records)
                records, session, _scan = self.recovery_scan(
                    ledger, post_identity, attempt, detail=detail)
                after_scan = self.helper.event_bytes(records)
                for name, raw in original_events.items():
                    self.assertEqual(after_scan[name], raw)

                completion = records.download_check(
                    session_id=session, attempt_id=attempt['attempt_id'],
                    stability_interval=0)
                self.assert_download_completion(completion, notes.PHOTO)
                after_check = self.helper.event_bytes(records)
                for name, raw in original_events.items():
                    self.assertEqual(after_check[name], raw)
                events = self.helper.read_events(records)
                self.assertEqual(sum(row['kind'] == 'intent' for row in events), 1)
                self.assertEqual(sum(row['kind'] == 'completion' for row in events), 1)
                summary = self.helper.reopen(ledger).summary()
                media = next(row for row in summary['media']
                             if row['media_key'] == attempt['media_key'])
                self.assertEqual(media['downloaded_kind'], notes.PHOTO)
                self.assertEqual(media['assurance'], 'DOWNLOAD_ONLY')

    def test_unknown_or_missing_outcome_still_rejects_download_check_after_scan(self):
        for index, outcome in enumerate((None, 'UNKNOWN')):
            with self.subTest(outcome=outcome):
                ledger, attempt, path = self.attempt(
                    'cross-scan-undecided-' + str(index), outcome=outcome,
                    content=media_fixtures.png())
                post_identity = notes.post_identity(
                    visual_key='cross-scan-undecided-' + str(index) + '-post')
                records, session, _scan = self.recovery_scan(
                    ledger, post_identity, attempt, detail=True)
                before = self.helper.event_bytes(records)
                with self.assertRaises(notes.NotesError):
                    records.download_check(
                        session_id=session, attempt_id=attempt['attempt_id'],
                        stability_interval=0)
                self.assertEqual(self.helper.event_bytes(records), before)
                self.assertTrue(path.is_file())

    def test_pending_basic_publish_resumes_after_recovery_scan_and_rebind(self):
        ledger, attempt, _ = self.attempt(
            'cross-scan-basic-publish', kind=notes.VIDEO,
            content=media_fixtures.png())
        with mock.patch.object(
                notes.NotesRecords, '_execute_publish',
                side_effect=OSError('synthetic publish interruption')):
            with self.assertRaisesRegex(OSError, 'synthetic publish interruption'):
                self.check(ledger, attempt)

        pending = self.helper.reopen(ledger)
        events_before_recovery = self.helper.read_events(pending)
        self.assertEqual(sum(row['kind'] == 'verification' and
                             row['data']['schema'] == notes.BASIC_VERIFICATION_SCHEMA
                             for row in events_before_recovery), 1)
        self.assertEqual(sum(row['kind'] == 'publish-plan'
                             for row in events_before_recovery), 1)
        post_identity = notes.post_identity(
            visual_key='cross-scan-basic-publish-post')
        records, _session, _scan = self.recovery_scan(
            ledger, post_identity, attempt, detail=True)
        resumed = records.resume()
        self.assertEqual(resumed['action'], 'PUBLISH_RESUMED')
        self.assertEqual(resumed['completion']['verification']['assurance'],
                         'DOWNLOAD_ONLY')
        events = self.helper.read_events(records)
        self.assertEqual(sum(row['kind'] == 'intent' for row in events), 1)
        self.assertEqual(sum(row['kind'] == 'publish-plan' for row in events), 1)
        self.assertEqual(sum(row['kind'] == 'completion' for row in events), 1)
        self.assertEqual(sum(row['kind'] == 'verification' and
                             row['data']['schema'] == notes.BASIC_VERIFICATION_SCHEMA
                             for row in events), 1)
        summary = self.helper.reopen(ledger).summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        media = next(row for row in summary['media']
                     if row['media_key'] == attempt['media_key'])
        self.assertEqual(media['downloaded_kind'], notes.PHOTO)
        self.assertEqual(media['assurance'], 'DOWNLOAD_ONLY')

    def test_download_check_publishes_second_unclassified_media_with_completed_sibling(self):
        ledger = self.helper.new_ledger('completed-sibling-download-check')
        first_identity = notes.media_identity(
            kind=notes.PHOTO, visual_key='completed-sibling-first')
        second_identity = notes.media_identity(
            kind='UNCLASSIFIED', visual_key='completed-sibling-second')
        _, post_key = self.helper.observe_post(
            ledger, 'completed-sibling-post',
            [first_identity, second_identity])
        first_key, _first_attempt, first_completion = \
            self.complete_basic_media(
                ledger, first_identity, post_key)
        first_target = Path(first_completion['data']['destination']) / \
            first_completion['data']['target_file']['name']
        first_before = self.local_file_identity(first_target)
        second_key, second_attempt = self.prepare_basic_media(
            ledger, second_identity, post_key)
        before_counts = {
            kind: sum(event['kind'] == kind for event in ledger.records.events)
            for kind in ('intent', 'verification', 'publish-plan', 'completion')}
        completion = self.check(ledger, second_attempt)

        self.assert_download_completion(completion, notes.PHOTO)
        self.assertEqual(completion['data']['media_key'], second_key)
        self.assertEqual(completion['data']['post_key'], post_key)
        self.assertEqual(second_attempt['identity']['kind'], 'UNCLASSIFIED')
        after_counts = {
            kind: sum(event['kind'] == kind for event in ledger.records.events)
            for kind in before_counts}
        self.assertEqual(after_counts, {
            'intent': before_counts['intent'],
            'verification': before_counts['verification'] + 1,
            'publish-plan': before_counts['publish-plan'] + 1,
            'completion': before_counts['completion'] + 1,
        })
        first_after = next(
            event for event in ledger.records.events
            if event['kind'] == 'completion' and
            event['data']['media_key'] == first_key)
        self.assertEqual(first_after, first_completion)
        self.assert_first_completion_unchanged(first_completion, first_before)
        self.assertEqual(self.local_file_identity(
            Path(completion['data']['destination']) /
            completion['data']['target_file']['name'])[2], 1)

    def test_pending_publish_with_completed_sibling_resumes_all_link_states(self):
        for state in ('plan-only', 'linked-two-paths', 'target-only'):
            with self.subTest(state=state):
                (ledger, first_completion, second_attempt, source,
                 target) = self.pending_second_media('sibling-resume-' + state)
                first_target = Path(first_completion['data']['destination']) / \
                    first_completion['data']['target_file']['name']
                first_before = self.local_file_identity(first_target)
                if state != 'plan-only':
                    os.link(source, target)
                    self.assertEqual(source.stat().st_ino, target.stat().st_ino)
                    self.assertEqual(source.stat().st_nlink, 2)
                    if state == 'target-only':
                        source.unlink()
                        self.assertFalse(source.exists())
                        self.assertEqual(target.stat().st_nlink, 1)

                reopened = self.helper.reopen(ledger)
                events_before_resume = self.helper.read_events(reopened)
                before_counts = {
                    kind: sum(event['kind'] == kind
                              for event in events_before_resume)
                    for kind in ('intent', 'verification', 'publish-plan',
                                 'completion')}
                first_event = next(
                    event for event in events_before_resume
                    if event['kind'] == 'completion' and
                    event['data']['media_key'] == first_completion['data']['media_key'])

                resumed = reopened.resume()

                self.assertEqual(resumed['action'], 'PUBLISH_RESUMED')
                self.assertEqual(resumed['completion']['attempt_id'],
                                 second_attempt['attempt_id'])
                after_counts = {
                    kind: sum(event['kind'] == kind for event in reopened.events)
                    for kind in before_counts}
                self.assertEqual(after_counts, {
                    'intent': before_counts['intent'],
                    'verification': before_counts['verification'],
                    'publish-plan': before_counts['publish-plan'],
                    'completion': before_counts['completion'] + 1,
                })
                self.assertEqual(next(
                    event for event in reopened.events
                    if event['kind'] == 'completion' and
                    event['data']['media_key'] == first_completion['data']['media_key']),
                    first_event)
                self.assert_first_completion_unchanged(
                    first_completion, first_before)
                self.assertEqual(target.stat().st_nlink, 1)
                expected_sha = next(
                    event['data']['source']['sha256']
                    for event in reopened.events
                    if event['kind'] == 'publish-plan' and
                    event['data']['attempt_id'] == second_attempt['attempt_id'])
                self.assertEqual(self.local_file_identity(target)[-1],
                                 expected_sha)
                summary = reopened.summary()
                self.assertEqual(summary['local_counts']['VERIFIED_PRESENT'], 2)
                self.assertEqual(reopened._pending_publish_plans(), [])
                events_after_resume = self.helper.event_bytes(reopened)
                repeated = reopened.resume()
                self.assertEqual(repeated['action'], 'NO_NAMING_TRANSACTION')
                self.assertEqual(self.helper.event_bytes(reopened),
                                 events_after_resume)

    def test_pending_publish_with_completed_sibling_still_rejects_invalid_targets(self):
        for mutation in ('missing-completed', 'extra-file',
                         'different-inode-same-bytes', 'symlink-target'):
            with self.subTest(mutation=mutation):
                (ledger, first_completion, second_attempt, source,
                 target) = self.pending_second_media(
                     'sibling-negative-' + mutation)
                first_target = Path(first_completion['data']['destination']) / \
                    first_completion['data']['target_file']['name']
                first_before = self.local_file_identity(first_target)
                if mutation == 'missing-completed':
                    first_target.unlink()
                elif mutation == 'extra-file':
                    (first_target.parent / 'unexpected.bin').write_bytes(
                        b'unexpected synthetic extra')
                elif mutation == 'different-inode-same-bytes':
                    target.write_bytes(source.read_bytes())
                    self.assertNotEqual(source.stat().st_ino,
                                        target.stat().st_ino)
                    self.assertEqual(source.read_bytes(), target.read_bytes())
                else:
                    target.symlink_to(source)
                    self.assertTrue(target.is_symlink())
                target_before = self.local_file_identity(target) \
                    if target.exists() else None
                target_was_symlink = target.is_symlink()
                target_link = os.readlink(target) if target_was_symlink else None
                target_bytes = target.read_bytes() if target.exists() else None
                source_before = self.local_file_identity(source)
                reopened = self.helper.reopen(ledger)
                events_before = self.helper.read_events(reopened)
                event_bytes_before = self.helper.event_bytes(reopened)
                before_counts = {
                    kind: sum(event['kind'] == kind for event in events_before)
                    for kind in ('intent', 'verification', 'publish-plan')}
                with self.assertRaises(notes.NotesError):
                    reopened.resume()
                events_after = self.helper.read_events(reopened)
                event_bytes_after = self.helper.event_bytes(reopened)
                for name, raw in event_bytes_before.items():
                    self.assertEqual(event_bytes_after[name], raw)
                new_events = [event for event in events_after
                              if event['sequence'] > len(events_before)]
                self.assertTrue(all(
                    event['kind'] == 'publish-progress' and
                    event['data']['action'] == 'DIRECTORY_READY'
                    for event in new_events))
                self.assertEqual({
                    kind: sum(event['kind'] == kind for event in events_after)
                    for kind in before_counts}, before_counts)
                self.assertEqual(sum(
                    event['kind'] == 'completion' for event in events_after), 1)
                self.assertFalse(any(
                    event['kind'] == 'completion' and
                    event['data']['media_key'] == second_attempt['media_key']
                    for event in events_after))
                if mutation not in ('missing-completed', 'extra-file'):
                    self.assertEqual(self.local_file_identity(target),
                                     target_before)
                    self.assertEqual(target.is_symlink(), target_was_symlink)
                    if target_was_symlink:
                        self.assertEqual(os.readlink(target), target_link)
                    self.assertEqual(target.read_bytes(), target_bytes)
                else:
                    self.assertTrue(source.is_file())
                self.assertEqual(self.local_file_identity(source), source_before)
                if mutation == 'missing-completed':
                    self.assertFalse(first_target.exists())
                if mutation != 'missing-completed':
                    self.assert_first_completion_unchanged(
                        first_completion, first_before)

    def test_empty_and_unknown_octet_stream_do_not_publish(self):
        for index, content in enumerate((b'', bytes(range(256)) * 4)):
            with self.subTest(index=index):
                ledger, attempt, path = self.attempt(
                    'invalid-' + str(index), content=content)
                before = self.helper.event_bytes(ledger.records)
                with self.assertRaises(notes.NotesError):
                    self.check(ledger, attempt)
                self.assertEqual(self.helper.event_bytes(ledger.records), before)
                self.assertEqual(path.read_bytes(), content)

    def test_known_nonmedia_are_excluded_and_staging_is_preserved(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as archive:
            archive.writestr('payload.txt', 'synthetic archive')
        samples = (
            ('plain', b'plain text, not an image\n', 'text/plain'),
            ('html', b'<html><body>synthetic</body></html>\n', 'text/html'),
            ('pdf', b'%PDF-1.4\nsynthetic pdf\n', 'application/pdf'),
            ('zip', zip_buffer.getvalue(), 'application/zip'),
        )
        for label, content, mime_type in samples:
            with self.subTest(label=label):
                ledger, attempt, path = self.attempt(
                    'nonmedia-' + label, content=content)
                event = self.check(ledger, attempt)
                self.assertEqual(event['kind'], 'download-exclusion')
                self.assertEqual(event['data']['schema'],
                                 'line-notes-download-exclusion/v1')
                self.assertEqual(event['data']['signature']['kind'], 'NON_MEDIA')
                self.assertEqual(event['data']['signature']['mime_type'], mime_type)
                self.assertEqual(event['data']['reason'], 'DOWNLOADED_NON_MEDIA')
                self.assertEqual(path.read_bytes(), content)
                self.assertEqual(self.helper.reopen(ledger).summary()
                                 ['status_counts']['EXCLUDED'], 1)
                self.assertFalse(any(row['kind'] == 'completion'
                                     for row in self.helper.read_events(ledger.records)))
                self.decode.assert_not_called()
        ledger, attempt, _ = self.attempt(
            'wrong-extension', name='image.mp4', content=media_fixtures.png())
        with self.assertRaises(notes.NotesError):
            self.check(ledger, attempt)

    def test_forged_download_exclusion_session_is_rejected_on_reload(self):
        ledger, attempt, _ = self.attempt(
            'forged-exclusion-session', content=b'<html>synthetic</html>')
        self.check(ledger, attempt)
        events = self.helper.read_events(ledger.records)
        exclusion = next(event for event in events
                         if event['kind'] == 'download-exclusion')
        exclusion['data']['session_id'] = 'session-not-bound-here'
        self.helper.rewrite_events(ledger.records, events)
        with self.assertRaisesRegex(notes.NotesError,
                                    'FRESH_FOREGROUND_BINDING_REQUIRED'):
            self.helper.reopen(ledger).summary()

    def test_forged_download_exclusion_result_ref_is_rejected_on_reload(self):
        ledger, attempt, _ = self.attempt(
            'forged-exclusion-result-ref', content=b'<html>synthetic</html>')
        self.check(ledger, attempt)
        events = self.helper.read_events(ledger.records)
        exclusion = next(event for event in events
                         if event['kind'] == 'download-exclusion')
        exclusion['data']['result_ref'] = exclusion['data']['intent_ref']
        self.helper.rewrite_events(ledger.records, events)
        with self.assertRaisesRegex(notes.NotesError,
                                    'DOWNLOAD_EXCLUSION_RESULT_CHANGED'):
            self.helper.reopen(ledger).summary()

    def test_unknown_reconciled_to_finished_can_be_excluded(self):
        content = b'<html><body>arrived after uncertain outcome</body></html>'
        ledger, attempt, path = self.attempt(
            'unknown-nonmedia', outcome='UNKNOWN', content=content)
        ledger.records.reconcile(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            result='DOWNLOAD_FINISHED', evidence=ledger.evidence_for_attempt(attempt))
        event = self.check(ledger, attempt)
        self.assertEqual(event['kind'], 'download-exclusion')
        self.assertEqual(path.read_bytes(), content)
        summary = self.helper.reopen(ledger).summary()
        self.assertEqual(summary['status_counts']['EXCLUDED'], 1)
        self.assertEqual(summary['status_counts']['COMPLETED'], 0)

    def test_download_check_cli_publishes_signature_completion(self):
        ledger, attempt, _ = self.attempt(
            'download-check-cli', kind='UNCLASSIFIED',
            content=media_fixtures.png())
        code, response = self.helper.run_notes_cli(
            'download-check', '--records-root', ledger.records.records,
            '--session-id', ledger.session,
            '--attempt-id', attempt['attempt_id'])
        self.assertEqual(code, 0)
        self.assertIs(response['dispatch_authorized'], False)
        self.assertEqual(response['kind'], 'completion')
        self.assertEqual(response['data']['schema'], 'line-notes-completion/v2')
        self.assertEqual(response['data']['verification']['assurance'],
                         'DOWNLOAD_ONLY')
        self.assertEqual(response['data']['verification']['verifier'],
                         'FILE_SIGNATURE')
        self.assertIs(response['data']['verification']['content_verified'], False)
        self.decode.assert_not_called()

    def test_media_kind_reconcile_cli_records_legacy_v1_reference(self):
        ledger, attempt, path = self.attempt(
            'media-kind-reconcile-cli', kind=notes.VIDEO,
            name='observed.png', content=media_fixtures.png())
        code, response = self.helper.run_notes_cli(
            'media-kind-reconcile', '--records-root', ledger.records.records,
            '--session-id', ledger.session,
            '--attempt-id', attempt['attempt_id'], '--to-kind', notes.PHOTO,
            '--evidence', ledger.evidence_for_attempt(attempt))
        self.assertEqual(code, 0)
        self.assertIs(response['dispatch_authorized'], False)
        self.assertEqual(response['schema'], notes.MEDIA_KIND_RECONCILE_SCHEMA)
        self.assertEqual(response['from_kind'], notes.VIDEO)
        self.assertEqual(response['to_kind'], notes.PHOTO)
        self.assertEqual(response['source']['name'], path.name)
        events = self.helper.read_events(self.helper.reopen(ledger))
        self.assertEqual(response['intent_ref']['sequence'],
                         next(event['sequence'] for event in events
                              if event['kind'] == 'intent'))
        self.assertEqual(response['outcome_ref']['sequence'],
                         next(event['sequence'] for event in events
                              if event['kind'] == 'outcome'))
        self.assertEqual(response['reconcile_ref']['sequence'],
                         next(event['sequence'] for event in events
                              if event['kind'] == 'media-kind-reconcile'))
        self.assertTrue(path.is_file())
        self.decode.assert_not_called()

    def test_extra_file_and_symlink_do_not_publish(self):
        ledger, attempt, path = self.attempt('extra-file', content=media_fixtures.png())
        (path.parent / 'extra.txt').write_bytes(b'extra')
        before = self.helper.event_bytes(ledger.records)
        with self.assertRaises(notes.NotesError):
            self.check(ledger, attempt)
        self.assertEqual(self.helper.event_bytes(ledger.records), before)
        ledger, attempt, path = self.attempt('symlink-file')
        os.symlink('/dev/null', str(path))
        before = self.helper.event_bytes(ledger.records)
        with self.assertRaises(notes.NotesError):
            self.check(ledger, attempt)
        self.assertEqual(self.helper.event_bytes(ledger.records), before)

    def test_file_drift_during_signature_check_does_not_publish(self):
        ledger, attempt, path = self.attempt('signature-drift', content=media_fixtures.png())
        original_run = subprocess.run

        def change_after_identification(command, *args, **kwargs):
            result = original_run(command, *args, **kwargs)
            if str(command[0]) == '/usr/bin/file':
                path.write_bytes(media_fixtures.png((0, 255, 0)))
            return result

        with mock.patch('subprocess.run', side_effect=change_after_identification):
            with self.assertRaises(notes.NotesError):
                self.check(ledger, attempt)
        self.assertFalse(any(event['kind'] == 'completion'
                             for event in self.helper.read_events(ledger.records)))

    def test_completed_content_drift_is_reported_and_not_redownloaded(self):
        ledger, attempt, _ = self.attempt('completion-drift', content=media_fixtures.png())
        completion = self.check(ledger, attempt)
        target = Path(completion['data']['destination']) / completion['data']['target_file']['name']
        target.write_bytes(media_fixtures.png((0, 255, 0)))
        before = self.helper.event_bytes(ledger.records)
        summary = self.helper.reopen(ledger).summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(summary['local_counts']['LOCAL_CHANGED'], 1)
        with self.assertRaises(notes.NotesError):
            ledger.records.intent(session_id=ledger.session, media_key_value=attempt['media_key'])
        self.assertEqual(self.helper.event_bytes(ledger.records), before)


    def test_download_completion_reloads_with_signature_assurance(self):
        ledger, attempt, _ = self.attempt(
            'reload-v2', kind='UNCLASSIFIED', content=media_fixtures.png())
        completion = self.check(ledger, attempt)
        reopened = self.helper.reopen(ledger)
        summary = reopened.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(summary['local_counts']['VERIFIED_PRESENT'], 1)
        media = next(row for row in summary['media']
                     if row['media_key'] == attempt['media_key'])
        self.assertEqual(media['assurance'], 'DOWNLOAD_ONLY')
        self.assertEqual(media['downloaded_kind'], notes.PHOTO)
        event = next(event for event in reopened.events
                     if event['kind'] == 'completion')
        self.assertEqual(event['data']['schema'], 'line-notes-completion/v2')
        self.assertEqual(event['data']['verification']['assurance'],
                         'DOWNLOAD_ONLY')
        self.assertEqual(event['data']['verification']['kind'], notes.PHOTO)

    def test_v1_basic_signature_payload_is_rejected_on_reload(self):
        ledger, attempt, _ = self.attempt(
            'forged-v1-basic', content=media_fixtures.png())
        self.check(ledger, attempt)
        events = self.helper.read_events(ledger.records)
        verification = next(event for event in events
                            if event['kind'] == 'verification')
        self.assertEqual(verification['data']['verification']['verifier'],
                         'FILE_SIGNATURE')
        verification['data']['schema'] = 'line-notes-verification/v1'
        self.helper.rewrite_events(ledger.records, events)
        with self.assertRaises(notes.NotesError):
            self.helper.reopen(ledger).summary()

    def test_restart_resume_download_only_verifies_signature_and_activates(self):
        restart = restart_fixtures.NotesRestartTests()
        restart.setUp()
        self.addCleanup(restart.tearDown)
        context = restart.one_media_restart_context('download-only-restart')
        attempt = restart.restart_download(
            restart.records, context['key'], 'fresh.png',
            media_fixtures.png((70, 71, 72)),
            context['preview']['restart_id'])
        result = restart.records.restart_resume(
            session_id=restart.session, stability_interval=0,
            download_only=True)
        self.assertEqual(result['action'], 'RESTART_ACTIVATED')
        self.assertEqual(result['activation']['restart_id'],
                         context['preview']['restart_id'])
        events = restart.read_events(restart.records)
        candidate = next(event for event in events
                         if event['kind'] == 'restart-candidate')
        self.assertEqual(candidate['data']['verification']['verifier'],
                         'FILE_SIGNATURE')
        self.assertEqual(candidate['data']['verification']['kind'], notes.PHOTO)
        self.assertEqual(candidate['data']['kind'], notes.PHOTO)
        self.assertEqual(candidate['data']['attempt_id'], attempt['attempt_id'])
        self.assertEqual(candidate['data']['schema'],
                         notes.BASIC_RESTART_CANDIDATE_SCHEMA)
        self.assertFalse(any(event['kind'] == 'verification' and
                             event['data'].get('attempt_id') == attempt['attempt_id']
                             for event in events))
        reopened = restart.reopen(restart.records)
        self.assertEqual(reopened.summary()['status_counts']['COMPLETED'], 1)

    def test_restart_default_resume_refuses_download_only_candidate(self):
        restart = restart_fixtures.NotesRestartTests()
        restart.setUp()
        self.addCleanup(restart.tearDown)
        context = restart.one_media_restart_context('restart-policy-guard')
        attempt = restart.restart_download(
            restart.records, context['key'], 'fresh.png',
            media_fixtures.png((73, 74, 75)),
            context['preview']['restart_id'])
        restart.records.verify(
            session_id=restart.session, attempt_id=attempt['attempt_id'],
            stability_interval=0, download_only=True)
        before = restart.event_files()
        with self.assertRaisesRegex(notes.NotesError, 'DOWNLOAD_CHECK_REQUIRED'):
            restart.records.restart_resume(
                session_id=restart.session, stability_interval=0)
        self.assertEqual(restart.event_files(), before)
        resumed = restart.records.restart_resume(
            session_id=restart.session, stability_interval=0,
            download_only=True)
        self.assertEqual(resumed['action'], 'RESTART_ACTIVATED')
        self.assertEqual(sum(event['kind'] == 'restart-activation'
                             for event in restart.read_events(restart.records)), 1)

    def test_unclassified_rekey_guard_rejects_writer_and_forged_history(self):
        # A current inventory cannot split an existing source with uncertain
        # kind into a second key for the same post and visual identity.
        ledger = self.helper.new_ledger('rekey-writer')
        first_identity = notes.media_identity(
            kind='UNCLASSIFIED', visual_key='same-visual')
        self.helper.observe_post(ledger, 'same-post', [first_identity])
        changed_identity = notes.media_identity(
            kind=notes.PHOTO, visual_key='same-visual')
        with self.assertRaisesRegex(notes.NotesError,
                                    'EXISTING_MEDIA_KEY_REQUIRED'):
            self.helper.observe_post(ledger, 'same-post', [changed_identity])

        # The projection rechecks the same invariant when loading a forged
        # append-only event chain, even when each individual key hashes.
        forged = self.helper.new_ledger('rekey-load')
        self.helper.observe_post(forged, 'same-post', [first_identity])
        self.helper.observe_post(forged, 'same-post', [first_identity])
        events = self.helper.read_events(forged.records)
        media_events = [event for event in events if event['kind'] == 'media']
        self.assertEqual(len(media_events), 2)
        row = media_events[-1]['data']['items'][0]
        row['identity'] = changed_identity
        row['media_key'] = notes.media_key(
            forged.summary['list_key'], media_events[-1]['data']['post_key'],
            changed_identity)
        self.helper.rewrite_events(forged.records, events)
        with self.assertRaisesRegex(notes.NotesError,
                                    'EXISTING_MEDIA_KEY_REQUIRED'):
            self.helper.reopen(forged).summary()

    def test_completed_media_cannot_reappear_as_new_unclassified_key(self):
        ledger, attempt, _ = self.attempt(
            'completed-no-rekey', kind=notes.PHOTO,
            content=media_fixtures.png())
        self.check(ledger, attempt)
        existing_identity = attempt['identity']
        uncertain_identity = notes.media_identity(
            kind='UNCLASSIFIED', visual_key=existing_identity['visual_key'])
        with self.assertRaisesRegex(notes.NotesError,
                                    'EXISTING_MEDIA_KEY_REQUIRED'):
            self.helper.observe_post(
                ledger, 'completed-no-rekey-post', [uncertain_identity])
        alternate_key = notes.media_key(
            ledger.summary['list_key'], attempt['post_key'], uncertain_identity)
        with self.assertRaises(notes.NotesError):
            ledger.records.intent(
                session_id=ledger.session, media_key_value=alternate_key)
        events = self.helper.read_events(ledger.records)
        intents = [row for row in events if row['kind'] == 'intent']
        completions = [row for row in events if row['kind'] == 'completion']
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0]['data']['media_key'], attempt['media_key'])
        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]['data']['media_key'], attempt['media_key'])

    def test_download_check_cli_help(self):
        result = subprocess.run(
            [os.sys.executable, '-B', '-m', 'line_backup_batch.notes',
             'download-check', '--help'], capture_output=True, text=True,
            env=dict(os.environ, PYTHONPATH=str(ledger_fixtures.ROOT / 'src')))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--attempt-id', result.stdout)


if __name__ == '__main__':
    unittest.main()
