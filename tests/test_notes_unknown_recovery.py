"""Synthetic regressions for Notes UNKNOWN-attempt recovery.

The fixtures use only generated ledgers and local files. They do not observe
LINE, operate a GUI, or claim real-device acceptance.
"""
import hashlib
import json
import os
from pathlib import Path
import threading
import unittest
from unittest import mock

from line_backup_batch import notes
import test_notes_media_verify as media_fixtures
import test_notes_regressions as regression_fixtures


class NotesUnknownRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.helper = regression_fixtures.NotesRegressionTests()
        self.helper.setUp()
        self.addCleanup(self.helper.tearDown)

    def seven_media_fixture(self, label, *, mark_unknown=True,
                            recovery_authorized=True):
        """Create one UNKNOWN attempt and six pending media in one post."""
        ledger = self.helper.new_ledger(
            label, recovery_authorized=recovery_authorized)
        identities = [
            notes.media_identity(
                kind=notes.PHOTO,
                visual_key='%s-media-%d' % (label, index),
            )
            for index in range(7)
        ]
        post_identity_value, post_key_value = self.helper.observe_post(
            ledger, label + '-post', identities)
        media_keys = [
            self.helper.media_key(ledger, post_key_value, identity)
            for identity in identities
        ]
        attempt = ledger.records.intent(
            session_id=ledger.session, media_key_value=media_keys[0])
        if mark_unknown:
            ledger.records.outcome(
                session_id=ledger.session,
                attempt_id=attempt['attempt_id'],
                outcome='UNKNOWN',
                evidence=ledger.evidence_for_attempt(attempt),
            )
        return dict(
            ledger=ledger,
            identities=identities,
            post_identity=post_identity_value,
            post_key=post_key_value,
            media_keys=media_keys,
            attempt=attempt,
            unknown=attempt if mark_unknown else None,
        )

    @staticmethod
    def media_row(summary, media_key_value):
        return next(
            row for row in summary['media']
            if row['media_key'] == media_key_value)

    @staticmethod
    def staging_state(fixture):
        root = Path(fixture['ledger'].photo_root)
        state = {}
        for path in sorted(root.rglob('*')):
            if path.is_dir():
                info = path.stat()
                state[str(path.relative_to(root))] = (
                    'directory', info.st_dev, info.st_ino)
            else:
                info = path.stat()
                state[str(path.relative_to(root))] = (
                    'file', info.st_dev, info.st_ino, info.st_size,
                    path.read_bytes())
        return state

    def complete_download(self, fixture, attempt, *, color=None):
        """Record a known finish, then run the daily basic file check."""
        staging = Path(attempt['destination'])
        (staging / 'media.png').write_bytes(
            media_fixtures.png(color) if color is not None
            else media_fixtures.png())
        records = fixture['ledger'].records
        session = fixture.get('s2_session', fixture['ledger'].session)
        records.outcome(
            session_id=session,
            attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED',
            evidence=fixture['ledger'].evidence_for_attempt(attempt),
        )
        return records.download_check(
            session_id=session, attempt_id=attempt['attempt_id'])

    def bind_session(self, records, fixture, session_id, label):
        evidence = fixture['ledger'].evidence(
            list_key=fixture['ledger'].summary['list_key'])
        return records.bind(
            session_id=session_id,
            observation=evidence,
            handoff=evidence,
        )

    def rescan_same_post(self, records, fixture, session_id, label):
        """Append a fresh complete scan and detail for the same post."""
        ledger = fixture['ledger']
        list_key_value = ledger.summary['list_key']
        post_key_value = notes.post_key(list_key_value, fixture['post_identity'])
        scan = records.scan(
            session_id=session_id, action='START',
            evidence=ledger.evidence(list_key=list_key_value))
        records.page(
            session_id=session_id,
            scan_id=scan['scan_id'],
            page_index=0,
            posts=[dict(identity=fixture['post_identity'],
                        date_summary='synthetic')],
            top_reached=True,
            bottom_reached=True,
            overlap_keys=[],
            evidence=ledger.evidence(
                list_key=list_key_value, scan_id=scan['scan_id']),
        )
        records.scan(
            session_id=session_id, action='FINISH',
            scan_id=scan['scan_id'],
            evidence=ledger.evidence(
                list_key=list_key_value, scan_id=scan['scan_id']))
        records.record_post(
            session_id=session_id,
            post_key_value=post_key_value,
            date_summary='synthetic',
            media_count=len(fixture['identities']),
            text_sha256=None,
            no_media=False,
            evidence=ledger.evidence(
                list_key=list_key_value,
                post_key=post_key_value,
                scan_id=scan['scan_id']),
        )
        records.record_media(
            session_id=session_id,
            post_key_value=post_key_value,
            items=[dict(identity=identity)
                   for identity in fixture['identities']],
            missing=[],
            evidence=ledger.evidence(
                list_key=list_key_value,
                post_key=post_key_value,
                scan_id=scan['scan_id']),
        )
        return scan['scan_id']

    def prepare_isolated_s2(self, label):
        """Isolate S1, replay, bind S2, then perform the new complete scan."""
        fixture = self.seven_media_fixture(label)
        records = fixture['ledger'].records
        tip = records.summary()['expected_tip']
        isolation = records.isolate(
            session_id=fixture['ledger'].session,
            attempt_id=fixture['attempt']['attempt_id'],
            evidence=fixture['ledger'].evidence_for_attempt(
                fixture['attempt']),
            expected_tip=tip,
        )
        self.assertFalse(isolation['replayed'])

        reopened = self.helper.reopen(fixture['ledger'])
        before_replay = self.helper.event_bytes(reopened)
        replay = reopened.isolate(
            session_id=fixture['ledger'].session,
            attempt_id=fixture['attempt']['attempt_id'],
            evidence=fixture['ledger'].evidence_for_attempt(
                fixture['attempt']),
            expected_tip=tip,
        )
        self.assertTrue(replay['replayed'])
        self.assertEqual(self.helper.event_bytes(reopened), before_replay)

        isolation_event = next(
            event for event in reopened.events
            if event['kind'] == 'attempt-isolation')
        s1_binding_ref = notes._event_ref(
            [event for event in reopened.events if event['kind'] == 'binding'][-1])
        self.assertEqual(isolation_event['data']['binding_ref'], s1_binding_ref)

        session = 'session-' + label + '-s2'
        self.bind_session(reopened, fixture, session, label + '-s2')
        bindings = [event for event in reopened.events
                    if event['kind'] == 'binding']
        self.assertEqual(bindings[-1]['data']['session_id'], session)
        self.assertEqual(isolation_event['data']['binding_ref'],
                         s1_binding_ref)
        self.assertNotEqual(isolation_event['data']['binding_ref'],
                            notes._event_ref(bindings[-1]))
        self.rescan_same_post(reopened, fixture, session, label + '-s2')

        fixture['ledger'].records = reopened
        fixture['ledger'].session = session
        fixture['isolation'] = isolation_event
        fixture['s1_binding_ref'] = s1_binding_ref
        fixture['s2_session'] = session
        return fixture

    def test_legacy_unknown_plus_six_pending_is_not_complete(self):
        fixture = self.seven_media_fixture('unknown-plus-six')
        summary = fixture['ledger'].records.summary()

        self.assertEqual(summary['status_counts']['UNKNOWN'], 1)
        self.assertEqual(summary['status_counts']['PENDING'], 6)
        self.assertEqual(summary['status_counts']['COMPLETED'], 0)
        self.assertEqual(summary['current_incomplete'], 7)
        self.assertFalse(summary['all_known_media_complete'])
        self.assertIn('UNKNOWN_ATTEMPT', summary['dispatch_blockers'])

        before_events = self.helper.event_bytes(fixture['ledger'].records)
        before_staging = self.staging_state(fixture)
        with self.assertRaisesRegex(
                notes.NotesError, 'UNRESOLVED_ATTEMPT_BLOCKS_CHANGE'):
            fixture['ledger'].records.scan(
                session_id=fixture['ledger'].session,
                action='START',
                evidence=fixture['ledger'].evidence_for_scan())
        with self.assertRaisesRegex(
                notes.NotesError,
                'UNKNOWN_OR_RUNNING_NO_REPLAY|'
                'ANOTHER_MEDIA_ATTEMPT_UNRESOLVED'):
            fixture['ledger'].records.intent(
                session_id=fixture['ledger'].session,
                media_key_value=fixture['media_keys'][1])
        self.assertEqual(
            self.helper.event_bytes(fixture['ledger'].records), before_events)
        self.assertEqual(self.staging_state(fixture), before_staging)

    def test_legacy_original_unknown_can_finish_before_isolation(self):
        fixture = self.seven_media_fixture('original-finishes-first')
        records = fixture['ledger'].records
        attempt = fixture['attempt']
        staging = Path(attempt['destination'])
        (staging / 'late.png').write_bytes(media_fixtures.png())

        records.reconcile(
            session_id=fixture['ledger'].session,
            attempt_id=attempt['attempt_id'],
            result='DOWNLOAD_FINISHED',
            evidence=fixture['ledger'].evidence_for_attempt(attempt),
        )
        completion = records.download_check(
            session_id=fixture['ledger'].session,
            attempt_id=attempt['attempt_id'],
        )
        self.assertEqual(completion['kind'], 'completion')
        summary = records.summary()
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(summary['status_counts']['PENDING'], 6)
        self.assertEqual(summary['current_incomplete'], 6)

        before_events = self.helper.event_bytes(records)
        with self.assertRaisesRegex(
                notes.NotesError, 'ISOLATION_RESULT_NOT_UNKNOWN'):
            records.isolate(
                session_id=fixture['ledger'].session,
                attempt_id=attempt['attempt_id'],
                evidence=fixture['ledger'].evidence_for_attempt(attempt),
                expected_tip=notes._event_ref(records.events[-1]),
            )
        self.assertEqual(self.helper.event_bytes(records), before_events)

    def test_legacy_cli_internal_error_has_no_event_writes(self):
        fixture = self.seven_media_fixture('cli-exit-70')
        records = fixture['ledger'].records
        before = self.helper.event_bytes(records)
        with mock.patch.object(
                notes.NotesRecords, 'summary',
                side_effect=RuntimeError('synthetic unexpected failure')):
            code, payload = self.helper.run_notes_cli(
                'summary', '--records-root', records.records)
        self.assertEqual(code, 70)
        self.assertEqual(payload['status'], 'INTERNAL_ERROR')
        self.assertEqual(payload['reason'], 'UNEXPECTED_EXCEPTION')
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(self.helper.event_bytes(records), before)

    def test_contract_summary_exposes_expected_tip(self):
        fixture = self.seven_media_fixture('summary-tip')
        records = fixture['ledger'].records
        summary = records.summary()
        self.assertIn('expected_tip', summary)
        self.assertEqual(summary['expected_tip'],
                         notes._event_ref(records.events[-1]))

    def test_contract_summary_distinguishes_no_outcome_from_unknown(self):
        no_outcome = self.seven_media_fixture(
            'summary-no-outcome', mark_unknown=False)
        summary = no_outcome['ledger'].records.summary()
        row = self.media_row(summary, no_outcome['attempt']['media_key'])
        self.assertIn('attempt_phase', row)
        self.assertEqual(row['attempt_phase'], 'OUTCOME_REQUIRED')

        unknown = self.seven_media_fixture('summary-unknown')
        summary = unknown['ledger'].records.summary()
        row = self.media_row(summary, unknown['attempt']['media_key'])
        self.assertIn('attempt_phase', row)
        self.assertEqual(row['attempt_phase'], 'RECONCILE_REQUIRED')

    def test_contract_s1_replay_bind_s2_scan_and_v5_intent(self):
        fixture = self.prepare_isolated_s2('s1-replay-s2')
        records = fixture['ledger'].records
        summary = records.summary()
        row = self.media_row(summary, fixture['attempt']['media_key'])
        self.assertIn('attempt_phase', row)
        self.assertEqual(row['attempt_phase'], 'REDOWNLOAD_REQUIRED')
        self.assertNotIn('REDOWNLOAD_REQUIRED', summary['dispatch_blockers'])
        self.assertFalse(summary['all_known_media_complete'])
        self.assertNotIn('UNKNOWN_ATTEMPT', summary['dispatch_blockers'])
        self.assertEqual(summary['expected_tip'],
                         notes._event_ref(records.events[-1]))

        v5 = records.intent(
            session_id=fixture['s2_session'],
            media_key_value=fixture['attempt']['media_key'],
        )
        self.assertEqual(v5['schema'], notes.INTENT_V5_SCHEMA)
        self.assertEqual(v5['phase'], 'OUTCOME_REQUIRED')
        self.assertEqual(v5['isolation_ref'],
                         notes._event_ref(fixture['isolation']))
        self.assertEqual(v5['redownload_budget'], 'CONSUMED')
        self.assertFalse(v5['dispatch_authorized'])
        v5_events = [
            event for event in records.events
            if event['kind'] == 'intent' and
            event['data']['schema'] == notes.INTENT_V5_SCHEMA]
        self.assertEqual(len(v5_events), 1)
        self.assertEqual(records.summary()['expected_tip'],
                         notes._event_ref(records.events[-1]))

    def test_contract_redownload_completes_once_and_reopens(self):
        fixture = self.prepare_isolated_s2('redownload-complete')
        records = fixture['ledger'].records
        v5 = records.intent(
            session_id=fixture['s2_session'],
            media_key_value=fixture['attempt']['media_key'],
        )
        completion = self.complete_download(fixture, v5)
        self.assertEqual(completion['kind'], 'completion')
        summary = records.summary()
        row = self.media_row(summary, fixture['attempt']['media_key'])
        self.assertEqual(row['status'], 'COMPLETED')
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(summary['status_counts']['PENDING'], 6)
        self.assertEqual(summary['current_incomplete'], 6)
        self.assertFalse(summary['all_known_media_complete'])

        reopened = self.helper.reopen(fixture['ledger'])
        replay = reopened.summary()
        replay_row = self.media_row(
            replay, fixture['attempt']['media_key'])
        self.assertEqual(replay_row['status'], 'COMPLETED')
        self.assertEqual(replay['status_counts']['COMPLETED'], 1)
        completions = [event for event in reopened.events
                       if event['kind'] == 'completion']
        self.assertEqual(len(completions), 1)

    def test_contract_late_old_staging_cannot_revive_or_overwrite(self):
        fixture = self.prepare_isolated_s2('late-old-staging')
        records = fixture['ledger'].records
        old_staging = Path(fixture['attempt']['destination'])
        late_file = old_staging / 'late.png'
        late_file.write_bytes(media_fixtures.png((0, 0, 255)))
        late_bytes = late_file.read_bytes()
        before = self.helper.event_bytes(records)

        with self.assertRaises(notes.NotesError):
            records.reconcile(
                session_id=fixture['s2_session'],
                attempt_id=fixture['attempt']['attempt_id'],
                result='DOWNLOAD_FINISHED',
                evidence=fixture['ledger'].evidence_for_attempt(
                    fixture['attempt']),
            )
        with self.assertRaises(notes.NotesError):
            records.download_check(
                session_id=fixture['s2_session'],
                attempt_id=fixture['attempt']['attempt_id'],
            )
        self.assertEqual(self.helper.event_bytes(records), before)

        v5 = records.intent(
            session_id=fixture['s2_session'],
            media_key_value=fixture['attempt']['media_key'],
        )
        self.complete_download(fixture, v5, color=(0, 255, 0))
        completion = next(
            event for event in records.events
            if event['kind'] == 'completion')
        self.assertNotEqual(Path(completion['data']['destination']),
                            old_staging)
        self.assertEqual(late_file.read_bytes(), late_bytes)
        self.assertNotIn(
            str(late_file), json.dumps(completion, sort_keys=True))

    def test_contract_second_unknown_exhausts_and_other_media_continues(self):
        fixture = self.prepare_isolated_s2('second-unknown')
        records = fixture['ledger'].records
        v5 = records.intent(
            session_id=fixture['s2_session'],
            media_key_value=fixture['attempt']['media_key'],
        )
        records.outcome(
            session_id=fixture['s2_session'],
            attempt_id=v5['attempt_id'],
            outcome='UNKNOWN',
            evidence=fixture['ledger'].evidence_for_attempt(v5),
        )
        summary = records.summary()
        self.assertEqual(
            self.media_row(summary, fixture['attempt']['media_key'])
            ['attempt_phase'], 'RECONCILE_REQUIRED')
        exhausted = records.isolate(
            session_id=fixture['s2_session'],
            attempt_id=v5['attempt_id'],
            evidence=fixture['ledger'].evidence_for_attempt(v5),
            expected_tip=summary['expected_tip'],
        )
        self.assertEqual(exhausted['disposition'], 'REDOWNLOAD_EXHAUSTED')
        self.assertEqual(exhausted['redownload_remaining'], 0)
        self.assertEqual(exhausted['next_action'], 'RECOVERY_EXHAUSTED')

        summary = records.summary()
        self.assertEqual(
            self.media_row(summary, fixture['attempt']['media_key'])
            ['attempt_phase'], 'RECOVERY_EXHAUSTED')
        self.assertNotIn('RECOVERY_EXHAUSTED', summary['dispatch_blockers'])
        self.assertFalse(summary['all_known_media_complete'])
        self.assertEqual(summary['status_counts']['UNKNOWN'], 1)
        self.assertEqual(summary['current_incomplete'], 7)
        before = self.helper.event_bytes(records)
        with self.assertRaisesRegex(
                notes.NotesError, 'REDOWNLOAD_BUDGET_EXHAUSTED'):
            records.intent(
                session_id=fixture['s2_session'],
                media_key_value=fixture['attempt']['media_key'],
            )
        self.assertEqual(self.helper.event_bytes(records), before)

        for key in fixture['media_keys'][1:]:
            other = records.intent(
                session_id=fixture['s2_session'], media_key_value=key)
            self.assertNotEqual(other['schema'], notes.INTENT_V5_SCHEMA)
            (Path(other['destination']) / 'item.png').write_bytes(
                media_fixtures.png())
            records.outcome(
                session_id=fixture['s2_session'],
                attempt_id=other['attempt_id'],
                outcome='DOWNLOAD_FINISHED',
                evidence=fixture['ledger'].evidence_for_attempt(other),
            )
            records.download_check(
                session_id=fixture['s2_session'],
                attempt_id=other['attempt_id'],
                stability_interval=0,
            )
        final = records.summary()
        self.assertEqual(final['status_counts']['COMPLETED'], 6)
        self.assertEqual(final['status_counts']['UNKNOWN'], 1)
        self.assertEqual(final['current_incomplete'], 1)
        self.assertFalse(final['all_known_media_complete'])

    def test_contract_dual_media_v5_budget_and_global_unknown_stop(self):
        fixture = self.prepare_isolated_s2('dual-media-v5-budget')
        ledger = fixture['ledger']
        records = ledger.records
        session = fixture['s2_session']
        a_key, b_key = fixture['media_keys'][:2]
        self.assertNotEqual(a_key, b_key)

        a_v5 = records.intent(session_id=session, media_key_value=a_key)
        self.assertEqual(a_v5['schema'], notes.INTENT_V5_SCHEMA)
        self.assertEqual(a_v5['redownload_budget'], 'CONSUMED')
        records.outcome(
            session_id=session,
            attempt_id=a_v5['attempt_id'],
            outcome='NOT_SENT',
            evidence=ledger.evidence_for_attempt(a_v5),
        )

        b_attempt = records.intent(session_id=session, media_key_value=b_key)
        self.assertNotEqual(b_attempt['schema'], notes.INTENT_V5_SCHEMA)
        records.outcome(
            session_id=session,
            attempt_id=b_attempt['attempt_id'],
            outcome='UNKNOWN',
            evidence=ledger.evidence_for_attempt(b_attempt),
        )
        self.assertIn('UNKNOWN_ATTEMPT', records.summary()['dispatch_blockers'])
        before_events = self.helper.event_bytes(records)
        before_staging = self.staging_state(fixture)
        with self.assertRaisesRegex(
                notes.NotesError, 'ANOTHER_MEDIA_ATTEMPT_UNRESOLVED'):
            records.intent(
                session_id=session,
                media_key_value=a_key,
                recovery_evidence=ledger.evidence_for_attempt(a_v5),
            )
        self.assertEqual(self.helper.event_bytes(records), before_events)
        self.assertEqual(self.staging_state(fixture), before_staging)

        b_isolation = records.isolate(
            session_id=session,
            attempt_id=b_attempt['attempt_id'],
            evidence=ledger.evidence_for_attempt(b_attempt),
            expected_tip=records.summary()['expected_tip'],
        )
        self.assertEqual(b_isolation['disposition'], 'REDOWNLOAD_AVAILABLE')
        self.assertEqual(b_isolation['redownload_remaining'], 1)
        self.rescan_same_post(records, fixture, session, 'dual-media-b-rescan')
        b_v5 = records.intent(session_id=session, media_key_value=b_key)
        self.assertEqual(b_v5['schema'], notes.INTENT_V5_SCHEMA)
        self.assertEqual(b_v5['redownload_budget'], 'CONSUMED')
        self.assertEqual(b_v5['isolation_ref'], b_isolation['isolation_ref'])
        self.assertEqual(b_v5['recovery_of'], b_attempt['attempt_id'])
        self.assertNotIn(b_v5['destination'],
                         (a_v5['destination'], b_attempt['destination']))
        self.assertEqual(list(Path(b_v5['destination']).iterdir()), [])

        reopened = self.helper.reopen(ledger)
        reopened.summary()
        stored_events = self.helper.event_bytes(reopened)
        self.assertEqual(
            {name: stored_events[name] for name in before_events}, before_events)

    def test_contract_cross_list_stale_tip_and_exact_replay(self):
        first = self.seven_media_fixture('cross-list-a')
        second = self.seven_media_fixture('cross-list-b')
        second_records = second['ledger'].records
        before_second = self.helper.event_bytes(second_records)
        with self.assertRaises(notes.NotesError):
            second_records.isolate(
                session_id=second['ledger'].session,
                attempt_id=first['attempt']['attempt_id'],
                evidence=first['ledger'].evidence_for_attempt(
                    first['attempt']),
                expected_tip=second_records.summary()['expected_tip'],
            )
        self.assertEqual(
            self.helper.event_bytes(second_records), before_second)

        records = first['ledger'].records
        stale_tip = records.summary()['expected_tip']
        session = 'session-cross-list-s2'
        self.bind_session(records, first, session, 'cross-list-s2')
        before_stale = self.helper.event_bytes(records)
        with self.assertRaisesRegex(
                notes.NotesError, 'ISOLATION_EXPECTED_TIP_CHANGED'):
            records.isolate(
                session_id=session,
                attempt_id=first['attempt']['attempt_id'],
                evidence=first['ledger'].evidence_for_attempt(
                    first['attempt']),
                expected_tip=stale_tip,
            )
        self.assertEqual(self.helper.event_bytes(records), before_stale)

        current_tip = records.summary()['expected_tip']
        isolated = records.isolate(
            session_id=session,
            attempt_id=first['attempt']['attempt_id'],
            evidence=first['ledger'].evidence_for_attempt(first['attempt']),
            expected_tip=current_tip,
        )
        self.assertFalse(isolated['replayed'])
        after_first = self.helper.event_bytes(records)
        replayed = records.isolate(
            session_id=session,
            attempt_id=first['attempt']['attempt_id'],
            evidence=first['ledger'].evidence_for_attempt(first['attempt']),
            expected_tip=current_tip,
        )
        self.assertTrue(replayed['replayed'])
        self.assertEqual(self.helper.event_bytes(records), after_first)

    def test_contract_concurrent_isolate_writes_one_branch(self):
        fixture = self.seven_media_fixture('concurrent-isolate')
        records = fixture['ledger'].records
        tip = records.summary()['expected_tip']
        evidence = fixture['ledger'].evidence_for_attempt(fixture['attempt'])
        records_a = self.helper.reopen(fixture['ledger'])
        records_b = self.helper.reopen(fixture['ledger'])
        barrier = threading.Barrier(2)
        results = []

        def worker(records):
            try:
                barrier.wait(timeout=2)
                result = records.isolate(
                    session_id=fixture['ledger'].session,
                    attempt_id=fixture['attempt']['attempt_id'],
                    evidence=evidence,
                    expected_tip=tip,
                )
                results.append(('ok', result))
            except BaseException as exc:
                results.append(('error', exc))

        threads = [threading.Thread(target=worker, args=(records,))
                   for records in (records_a, records_b)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        successes = [result for status, result in results
                     if status == 'ok']
        self.assertTrue(successes)
        self.assertEqual(len([
            result for result in successes if not result['replayed']]), 1)
        reopened = self.helper.reopen(fixture['ledger'])
        reopened.summary()
        self.assertEqual(len([
            event for event in reopened.events
            if event['kind'] == 'attempt-isolation']), 1)
        self.assertLessEqual(len(successes), 2)

    def test_contract_cli_stale_tip_exit_4_and_zero_events(self):
        fixture = self.seven_media_fixture('cli-exit-4')
        records = fixture['ledger'].records
        stale_tip = records.summary()['expected_tip']
        session = 'session-cli-exit-4-s2'
        self.bind_session(records, fixture, session, 'cli-exit-4-s2')
        before = self.helper.event_bytes(records)
        evidence = fixture['ledger'].evidence_for_attempt(fixture['attempt'])
        code, payload = self.helper.run_notes_cli(
            'isolate',
            '--records-root', records.records,
            '--session-id', session,
            '--attempt-id', fixture['attempt']['attempt_id'],
            '--evidence', evidence,
            '--expected-tip', json.dumps(stale_tip, separators=(',', ':')),
        )
        self.assertEqual(code, 4)
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertEqual(payload['reason'], 'ISOLATION_EXPECTED_TIP_CHANGED')
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(self.helper.event_bytes(records), before)

    def test_contract_v5_completion_survives_later_scan_and_reopen(self):
        fixture = self.prepare_isolated_s2('v5-later-scan')
        records = fixture['ledger'].records
        v5 = records.intent(
            session_id=fixture['s2_session'],
            media_key_value=fixture['attempt']['media_key'],
        )
        completion = self.complete_download(
            fixture, v5, color=(0, 255, 0))
        self.assertEqual(completion['kind'], 'completion')
        completion_ref = notes._event_ref(records.events[-1])
        before_scan = self.helper.event_bytes(records)

        session = 'session-v5-later-scan-s3'
        self.bind_session(records, fixture, session, 'v5-later-scan-s3')
        scan_id = self.rescan_same_post(
            records, fixture, session, 'v5-later-scan-s3')
        after_scan = self.helper.event_bytes(records)
        for name, raw in before_scan.items():
            self.assertEqual(after_scan[name], raw)

        reopened = self.helper.reopen(fixture['ledger'])
        summary = reopened.summary()
        row = self.media_row(summary, fixture['attempt']['media_key'])
        self.assertEqual(row['status'], 'COMPLETED')
        self.assertEqual(summary['status_counts']['COMPLETED'], 1)
        self.assertEqual(summary['status_counts']['PENDING'], 6)
        self.assertEqual(summary['expected_tip'],
                         notes._event_ref(reopened.events[-1]))
        self.assertEqual(
            [notes._event_ref(event) for event in reopened.events
             if event['kind'] == 'completion'],
            [completion_ref])
        self.assertNotIn(
            fixture['attempt']['media_key'],
            [row['media_key'] for row in summary['unresolved_attempts']])
        latest, scans = reopened._open_scan()
        self.assertEqual(latest, scan_id)
        self.assertIsNotNone(scans[scan_id]['complete'])
        self.assertFalse(summary['all_known_media_complete'])

    def test_contract_isolation_preserves_single_stable_media_in_old_staging(self):
        fixture = self.seven_media_fixture('isolation-nonempty-staging')
        ledger = fixture['ledger']
        records = ledger.records
        old_attempt = fixture['attempt']
        late_file = Path(old_attempt['destination']) / 'late.png'
        late_bytes = media_fixtures.png()
        late_file.write_bytes(late_bytes)
        tip = records.summary()['expected_tip']
        before_events = self.helper.event_bytes(records)
        before_staging = self.staging_state(fixture)
        result = records.isolate(
            session_id=ledger.session,
            attempt_id=old_attempt['attempt_id'],
            evidence=ledger.evidence_for_attempt(old_attempt),
            expected_tip=tip,
        )
        self.assertEqual(result['status'], 'ISOLATED')
        self.assertNotEqual(self.helper.event_bytes(records), before_events)
        self.assertEqual(self.staging_state(fixture), before_staging)

        session = ledger.session + '-resume'
        records = self.helper.reopen(ledger)
        self.bind_session(records, fixture, session, session)
        before_rejected = self.helper.event_bytes(records)
        with self.assertRaisesRegex(notes.NotesError,
                                    '^ISOLATED_ATTEMPT_IMMUTABLE$'):
            records.reconcile(
                session_id=session,
                attempt_id=old_attempt['attempt_id'],
                result='DOWNLOAD_FINISHED',
                evidence=ledger.evidence_for_attempt(old_attempt))
        with self.assertRaisesRegex(notes.NotesError,
                                    '^ISOLATED_ATTEMPT_IMMUTABLE$'):
            records.download_check(session_id=session,
                                   attempt_id=old_attempt['attempt_id'])
        self.assertEqual(self.helper.event_bytes(records), before_rejected)
        scan_id = self.rescan_same_post(records, fixture, session, session)
        new_attempt = records.intent(
            session_id=session, media_key_value=old_attempt['media_key'])
        self.assertEqual(new_attempt['schema'], notes.INTENT_V5_SCHEMA)
        self.assertNotEqual(new_attempt['destination'], old_attempt['destination'])
        self.assertEqual(list(Path(new_attempt['destination']).iterdir()), [])
        self.assertEqual(new_attempt['scan_id'], scan_id)
        fixture.update(s2_session=session)
        ledger.records = records
        completion = self.complete_download(fixture, new_attempt)
        self.assertEqual(completion['kind'], 'completion')
        self.assertEqual(late_file.read_bytes(), late_bytes)
        self.assertEqual(records._attempt_result(old_attempt['attempt_id']),
                         'UNKNOWN')
        completion_events = [event for event in records.events
                             if event['kind'] == 'completion']
        self.assertEqual(len(completion_events), 1)
        self.assertEqual(completion_events[0]['data']['attempt_id'],
                         new_attempt['attempt_id'])

    def test_isolation_rejects_unsafe_staging_shapes_without_writes(self):
        def zero(root):
            (root / 'empty.jpg').write_bytes(b'')

        def suffix(root):
            (root / 'partial.part').write_bytes(b'x')

        def document(root):
            (root / 'document.pdf').write_bytes(b'%PDF')

        def hidden(root):
            (root / '.hidden.jpg').write_bytes(media_fixtures.png())

        def multiple(root):
            (root / 'one.jpg').write_bytes(media_fixtures.png())
            (root / 'two.jpg').write_bytes(media_fixtures.png())

        def symlink(root):
            source = root.parent / 'outside.jpg'
            source.write_bytes(media_fixtures.png())
            (root / 'link.jpg').symlink_to(source)

        def hardlink(root):
            source = root.parent / 'outside.jpg'
            source.write_bytes(media_fixtures.png())
            os.link(source, root / 'link.jpg')

        def child_directory(root):
            (root / 'nested').mkdir()

        cases = (zero, suffix, document, hidden, multiple, symlink, hardlink,
                 child_directory)
        for index, make_invalid in enumerate(cases):
            with self.subTest(case=make_invalid.__name__):
                fixture = self.seven_media_fixture(
                    'unsafe-isolation-%d' % index)
                records = fixture['ledger'].records
                staging = Path(fixture['attempt']['destination'])
                make_invalid(staging)
                before_staging = self.staging_state(fixture)
                before_events = self.helper.event_bytes(records)
                evidence_dir = records.records / 'evidence'
                before_evidence = {
                    path.name: path.read_bytes() for path in evidence_dir.iterdir()
                }
                with self.assertRaisesRegex(
                        notes.NotesError,
                        '^ISOLATION_STAGING_NOT_EMPTY$'):
                    records.isolate(
                        session_id=fixture['ledger'].session,
                        attempt_id=fixture['attempt']['attempt_id'],
                        evidence=fixture['ledger'].evidence_for_attempt(
                            fixture['attempt']),
                        expected_tip=records.summary()['expected_tip'],
                        stability_interval=0)
                self.assertEqual(self.helper.event_bytes(records), before_events)
                self.assertEqual(self.staging_state(fixture), before_staging)
                self.assertEqual({
                    path.name: path.read_bytes() for path in evidence_dir.iterdir()
                }, before_evidence)

    def test_isolated_missing_post_stays_incomplete_when_latest_scan_omits_it(self):
        for exhausted in (False, True):
            with self.subTest(exhausted=exhausted):
                fixture = self.prepare_isolated_s2(
                    'omitted-exhausted' if exhausted else 'omitted-available')
                ledger = fixture['ledger']
                records = ledger.records
                key = fixture['attempt']['media_key']
                if exhausted:
                    v5 = records.intent(session_id=fixture['s2_session'],
                                        media_key_value=key)
                    records.outcome(
                        session_id=fixture['s2_session'],
                        attempt_id=v5['attempt_id'], outcome='UNKNOWN',
                        evidence=ledger.evidence_for_attempt(v5))
                    records.isolate(
                        session_id=fixture['s2_session'],
                        attempt_id=v5['attempt_id'],
                        evidence=ledger.evidence_for_attempt(v5),
                        expected_tip=records.summary()['expected_tip'])
                new_session = fixture['s2_session'] + '-omitting'
                self.bind_session(records, fixture, new_session, new_session)
                ledger.records = records
                ledger.session = new_session
                self.helper.observe_post(ledger, 'only-new-no-media', [],
                                         no_media=True)
                summary = records.summary()
                self.assertEqual(summary['current_incomplete'], 0)
                self.assertEqual(summary['dispatch_blockers'], [])
                self.assertFalse(summary['all_known_media_complete'])
                self.assertIn(key, [row['media_key'] for row in
                                    summary['unresolved_attempts']])

    def test_third_ordinary_attempt_can_finish_and_download_check(self):
        fixture = self.seven_media_fixture('third-attempt-settlement',
                                           mark_unknown=False)
        ledger = fixture['ledger']
        records = ledger.records
        attempt = fixture['attempt']
        for _ in range(2):
            records.outcome(
                session_id=ledger.session, attempt_id=attempt['attempt_id'],
                outcome='STOPPED', evidence=ledger.evidence_for_attempt(attempt))
            attempt = records.intent(
                session_id=ledger.session,
                media_key_value=fixture['media_keys'][0],
                recovery_evidence=ledger.evidence_for_attempt(attempt))
        self.assertEqual(len([event for event in records.events
                              if event['kind'] == 'intent' and
                              event['data']['media_key'] ==
                              fixture['media_keys'][0]]), 3)
        completion = self.complete_download(fixture, attempt)
        self.assertEqual(completion['kind'], 'completion')
        self.assertEqual(self.media_row(records.summary(),
                                        fixture['media_keys'][0])['status'],
                         'COMPLETED')

    def test_over_limit_legacy_history_remains_readable_but_not_extendable(self):
        fixture = self.seven_media_fixture('legacy-over-limit',
                                           mark_unknown=False)
        ledger = fixture['ledger']
        records = ledger.records
        key = fixture['media_keys'][0]
        attempt = fixture['attempt']
        for _ in range(2):
            records.outcome(
                session_id=ledger.session, attempt_id=attempt['attempt_id'],
                outcome='STOPPED', evidence=ledger.evidence_for_attempt(attempt))
            attempt = records.intent(
                session_id=ledger.session, media_key_value=key,
                recovery_evidence=ledger.evidence_for_attempt(attempt))
        records.outcome(
            session_id=ledger.session, attempt_id=attempt['attempt_id'],
            outcome='STOPPED', evidence=ledger.evidence_for_attempt(attempt))

        original_need = notes.need
        with mock.patch.object(
                notes, 'need',
                side_effect=lambda condition, code: (
                    None if code == 'AUTO_RECOVERY_ATTEMPT_LIMIT'
                    else original_need(condition, code))):
            fourth = records.intent(
                session_id=ledger.session, media_key_value=key,
                recovery_evidence=ledger.evidence_for_attempt(attempt))
        records.outcome(
            session_id=ledger.session, attempt_id=fourth['attempt_id'],
            outcome='STOPPED', evidence=ledger.evidence_for_attempt(fourth))
        reopened = self.helper.reopen(ledger)
        reopened.summary()
        self.assertEqual(len([event for event in reopened.events
                              if event['kind'] == 'intent' and
                              event['data']['media_key'] == key]), 4)
        with self.assertRaisesRegex(
                notes.NotesError, '^AUTO_RECOVERY_ATTEMPT_LIMIT$'):
            reopened.intent(
                session_id=ledger.session, media_key_value=key,
                recovery_evidence=ledger.evidence_for_attempt(fourth))

    def test_nonempty_isolation_rechecks_before_evidence_and_before_append(self):
        for change_during_evidence in (False, True):
            with self.subTest(change_during_evidence=change_during_evidence):
                label = 'staging-change-%s' % change_during_evidence
                fixture = self.seven_media_fixture(label)
                ledger = fixture['ledger']
                records = ledger.records
                attempt = fixture['attempt']
                payload = Path(attempt['destination']) / 'late.png'
                payload.write_bytes(media_fixtures.png())
                evidence = ledger.evidence_for_attempt(attempt)
                tip = records.summary()['expected_tip']
                before_events = self.helper.event_bytes(records)
                evidence_dir = records.records / 'evidence'
                before_evidence = set(evidence_dir.iterdir())
                preserve = notes._preserve_evidence

                def change_payload():
                    payload.write_bytes(b'new bytes written by another process')

                def preserve_and_change(*args, **kwargs):
                    ref = preserve(*args, **kwargs)
                    change_payload()
                    return ref

                patch = (mock.patch.object(
                    notes, '_preserve_evidence', side_effect=preserve_and_change)
                    if change_during_evidence else mock.patch.object(
                        notes.time, 'sleep', side_effect=lambda _: change_payload()))
                with patch, self.assertRaisesRegex(
                        notes.NotesError, '^ISOLATION_STAGING_CHANGED$'):
                    records.isolate(
                        session_id=ledger.session,
                        attempt_id=attempt['attempt_id'],
                        evidence=evidence,
                        expected_tip=tip,
                    )
                self.assertEqual(self.helper.event_bytes(records), before_events)
                if not change_during_evidence:
                    self.assertEqual(set(evidence_dir.iterdir()), before_evidence)

    def test_budget_survives_new_session_and_uses_historical_context(self):
        fixture = self.prepare_isolated_s2('automatic-budget')
        ledger = fixture['ledger']
        records = ledger.records
        session = fixture['s2_session']
        key, other_key = fixture['media_keys'][:2]
        second = records.intent(session_id=session, media_key_value=key)
        self.assertEqual(second['schema'], notes.INTENT_V5_SCHEMA)
        records.outcome(
            session_id=session, attempt_id=second['attempt_id'],
            outcome='NOT_SENT', evidence=ledger.evidence_for_attempt(second))

        records = self.helper.reopen(ledger)
        session = 'automatic-budget-s3'
        self.bind_session(records, fixture, session, session)
        new_scan = self.rescan_same_post(records, fixture, session, session)
        self.assertIn(
            'RECOVERY_REVIEW_REQUIRED',
            [row['action'] for row in records.resume()['pending']])
        before = self.helper.event_bytes(records), self.staging_state(fixture)
        with self.assertRaisesRegex(notes.NotesError, '^EVIDENCE_CONTEXT_MISMATCH$'):
            records.intent(
                session_id=session, media_key_value=key,
                recovery_evidence=ledger.evidence_for_attempt(
                    dict(second, scan_id=new_scan)))
        self.assertEqual(
            (self.helper.event_bytes(records), self.staging_state(fixture)), before)
        third = records.intent(
            session_id=session, media_key_value=key,
            recovery_evidence=ledger.evidence_for_attempt(second))
        self.assertEqual(third['scan_id'], new_scan)
        records.outcome(
            session_id=session, attempt_id=third['attempt_id'],
            outcome='STOPPED', evidence=ledger.evidence_for_attempt(third))

        records = self.helper.reopen(ledger)
        session = 'automatic-budget-s4'
        self.bind_session(records, fixture, session, session)
        self.rescan_same_post(records, fixture, session, session)
        actions = {row['media_key']: row['action']
                   for row in records.resume()['pending']}
        self.assertEqual(actions[key], 'RECOVERY_EXHAUSTED')
        before = self.helper.event_bytes(records), self.staging_state(fixture)
        with self.assertRaisesRegex(notes.NotesError, '^AUTO_RECOVERY_ATTEMPT_LIMIT$'):
            records.intent(
                session_id=session, media_key_value=key,
                recovery_evidence=ledger.evidence_for_attempt(third))
        self.assertEqual(
            (self.helper.event_bytes(records), self.staging_state(fixture)), before)
        other = records.intent(session_id=session, media_key_value=other_key)
        fixture.update(s2_session=session)
        ledger.records = records
        self.complete_download(fixture, other)
        self.assertEqual(self.media_row(records.summary(), other_key)['status'],
                         'COMPLETED')

    def test_third_unknown_isolates_without_changing_v1_disposition(self):
        fixture = self.seven_media_fixture('third-unknown', mark_unknown=False)
        ledger = fixture['ledger']
        records = ledger.records
        attempt = fixture['attempt']
        key, other_key = fixture['media_keys'][:2]
        for _ in range(2):
            evidence = ledger.evidence_for_attempt(attempt)
            records.outcome(session_id=ledger.session,
                            attempt_id=attempt['attempt_id'],
                            outcome='NOT_SENT', evidence=evidence)
            attempt = records.intent(
                session_id=ledger.session, media_key_value=key,
                recovery_evidence=evidence)
        evidence = ledger.evidence_for_attempt(attempt)
        records.outcome(session_id=ledger.session, attempt_id=attempt['attempt_id'],
                        outcome='UNKNOWN', evidence=evidence)
        tip = records.summary()['expected_tip']
        for replayed in (False, True):
            result = records.isolate(
                session_id=ledger.session, attempt_id=attempt['attempt_id'],
                evidence=evidence, expected_tip=tip)
            self.assertEqual(result['replayed'], replayed)
            self.assertEqual(result['disposition'], 'REDOWNLOAD_AVAILABLE')
            self.assertEqual(result['next_action'], 'RECOVERY_EXHAUSTED')
            self.assertEqual(result['redownload_remaining'], 0)
        summary = records.summary()
        self.assertEqual(self.media_row(summary, key)['attempt_phase'],
                         'RECOVERY_EXHAUSTED')
        self.assertFalse(summary['all_known_media_complete'])
        self.assertNotIn('UNKNOWN_ATTEMPT', summary['dispatch_blockers'])
        other = records.intent(session_id=ledger.session, media_key_value=other_key)
        self.complete_download(fixture, other)

    def test_contract_isolation_requires_recovery_authorization(self):
        fixture = self.seven_media_fixture(
            'isolation-not-authorized', recovery_authorized=False)
        records = fixture['ledger'].records
        tip = records.summary()['expected_tip']
        before_events = self.helper.event_bytes(records)
        before_staging = self.staging_state(fixture)
        with self.assertRaisesRegex(
                notes.NotesError, 'NOTES_RECOVERY_NOT_AUTHORIZED'):
            records.isolate(
                session_id=fixture['ledger'].session,
                attempt_id=fixture['attempt']['attempt_id'],
                evidence=fixture['ledger'].evidence_for_attempt(
                    fixture['attempt']),
                expected_tip=tip,
            )
        self.assertEqual(self.helper.event_bytes(records), before_events)
        self.assertEqual(self.staging_state(fixture), before_staging)

    def test_contract_s1_partial_s2_video_and_photo_complete_after_reopen(self):
        """Resume a partly completed three-media post using only one v5."""
        label = 's1-partial-s2-complete'
        ledger = self.helper.new_ledger(label)
        kinds = (notes.PHOTO, notes.VIDEO, notes.PHOTO)
        identities = [notes.media_identity(
            kind=kind, visual_key='%s-media-%d' % (label, index))
            for index, kind in enumerate(kinds)]
        post_identity, post_key_value = self.helper.observe_post(
            ledger, label + '-post', identities)
        media_keys = [self.helper.media_key(
            ledger, post_key_value, identity) for identity in identities]
        first_key, video_key, last_key = media_keys
        fixture = dict(ledger=ledger, identities=identities,
                       post_identity=post_identity, post_key=post_key_value,
                       media_keys=media_keys)
        records = ledger.records
        first_png = media_fixtures.png((0, 255, 0))
        first_attempt = records.intent(session_id=ledger.session,
                                       media_key_value=first_key)
        first_completion = self.complete_download(
            fixture, first_attempt, color=(0, 255, 0))
        first_event = '%08d.json' % first_completion['sequence']
        first_event_bytes = self.helper.event_bytes(records)[first_event]
        video_attempt = records.intent(session_id=ledger.session,
                                       media_key_value=video_key)
        partial = records.summary()
        self.assertEqual(tuple(partial['status_counts'][name] for name in
                               ('COMPLETED', 'UNKNOWN', 'PENDING')) +
                         (partial['current_incomplete'],), (1, 1, 1, 2))
        self.assertFalse(partial['all_known_media_complete'])
        reopened = self.helper.reopen(ledger)
        ledger.records = reopened
        session2 = label + '-s2'
        self.bind_session(reopened, fixture, session2, session2)
        ledger.session = session2
        video_evidence = ledger.evidence_for_attempt(video_attempt)
        unknown = reopened.outcome(session_id=session2, evidence=video_evidence,
                                   attempt_id=video_attempt['attempt_id'],
                                   outcome='UNKNOWN')
        self.assertEqual(unknown['outcome'], 'UNKNOWN')
        isolation = reopened.isolate(
            session_id=session2, attempt_id=video_attempt['attempt_id'],
            evidence=video_evidence,
            expected_tip=reopened.summary()['expected_tip'])
        self.assertEqual((isolation['disposition'],
                          isolation['redownload_remaining'],
                          isolation['next_action']),
                         ('REDOWNLOAD_AVAILABLE', 1,
                          'RECOVERY_SCAN_REQUIRED'))
        self.rescan_same_post(reopened, fixture, session2, session2)
        v5 = reopened.intent(session_id=session2, media_key_value=video_key)
        self.assertEqual(v5['schema'], notes.INTENT_V5_SCHEMA)
        self.assertEqual(v5['recovery_of'], video_attempt['attempt_id'])
        self.assertEqual(v5['isolation_ref'], isolation['isolation_ref'])
        self.assertEqual(v5['redownload_budget'], 'CONSUMED')
        self.assertNotEqual(v5['destination'], video_attempt['destination'])
        mp4 = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom'
        def finish(attempt, name, content):
            (Path(attempt['destination']) / name).write_bytes(content)
            reopened.outcome(session_id=session2, attempt_id=attempt['attempt_id'],
                             outcome='DOWNLOAD_FINISHED',
                             evidence=ledger.evidence_for_attempt(attempt))
            return reopened.download_check(session_id=session2,
                                           attempt_id=attempt['attempt_id'],
                                           stability_interval=0)

        video_completion = finish(v5, 'video.mp4', mp4)
        signature = video_completion['data']['verification']['signature']
        self.assertIn(signature['mime_type'], ('video/mp4', 'application/mp4'))
        last_png = media_fixtures.png((0, 0, 255))
        last_attempt = reopened.intent(session_id=session2,
                                       media_key_value=last_key)
        self.assertNotEqual(last_attempt['schema'], notes.INTENT_V5_SCHEMA)
        self.assertIsNone(last_attempt.get('recovery_of'))
        finish(last_attempt, 'photo-2.png', last_png)
        final_records = self.helper.reopen(ledger)
        final_summary = final_records.summary()
        completions = [event for event in final_records.events
                       if event['kind'] == 'completion']
        by_key = {event['data']['media_key']: event for event in completions}
        self.assertEqual((len(completions), set(by_key)),
                         (3, set(media_keys)))
        expected = ((first_key, notes.PHOTO, first_png),
                    (video_key, notes.VIDEO, mp4),
                    (last_key, notes.PHOTO, last_png))
        for key, kind, content in expected:
            row = self.media_row(final_summary, key)
            self.assertEqual((row['status'], row['kind'], row['effective_kind'],
                              row['local_files']), ('COMPLETED', kind, kind,
                                                    notes.LOCAL_VERIFIED))
            data = by_key[key]['data']
            target = Path(data['destination']) / data['target_file']['name']
            source_digest = hashlib.sha256(content).hexdigest()
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            self.assertEqual((data['target_file']['sha256'], digest),
                             (source_digest, source_digest))
            self.assertEqual(data['verification']['kind'], kind)
        self.assertEqual((final_summary['status_counts']['COMPLETED'],
                          final_summary['current_incomplete'],
                          final_summary['all_known_media_complete'],
                          final_summary['local_counts'][notes.LOCAL_VERIFIED]),
                         (3, 0, True, 3))
        final_events = self.helper.event_bytes(final_records)
        self.assertEqual(final_events[first_event], first_event_bytes)
        self.assertEqual(sum(
            event['kind'] == 'intent' and
            event['data']['media_key'] == first_key
            for event in final_records.events), 1)
        self.assertEqual(sum(
            event['kind'] == 'intent' and
            event['data']['schema'] == notes.INTENT_V5_SCHEMA
            for event in final_records.events), 1)
