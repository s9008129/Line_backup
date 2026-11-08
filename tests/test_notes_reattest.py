"""Synthetic read-only list-directory reattestation preview coverage."""
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
import uuid

from line_backup_batch import notes, notes_evidence


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TASKS = ROOT / '.local' / 'line-backup' / 'tasks'


class NotesReattestPreviewTests(unittest.TestCase):
    def setUp(self):
        PRIVATE_TASKS.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='.line-notes-reattest-s1-', dir=str(PRIVATE_TASKS))
        self.base = Path(self.temporary.name).resolve()
        self.active_path = self.base / 'active-notes-task.json'
        self.active_path.write_bytes(b'{"synthetic":"unchanged"}\n')
        self.evidence_source = self.base / 'statement.txt'
        self.evidence_source.write_bytes(b'synthetic notes preview evidence\n')
        self.evidence_asset = self.base / 'screenshot.txt'
        self.evidence_asset.write_bytes(b'synthetic-only screenshot placeholder\n')
        self.evidence_packs = self.base / 'evidence-packs'
        self.evidence_packs.mkdir()
        self.patches = [
            mock.patch.object(notes, '_active_task_path',
                              return_value=self.active_path),
            mock.patch.object(notes, '_read_active_hint', return_value=None),
            mock.patch.object(notes, '_write_active_hint', return_value=None),
        ]
        for patch in self.patches:
            patch.start()
        self.case_number = 0

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.temporary.cleanup()

    def evidence(self, list_key, **context):
        return notes_evidence.create_bundle(
            statement=str(self.evidence_source),
            assets=[('screenshot', str(self.evidence_asset))],
            context=dict(list_key=list_key, **context),
            output_dir=str(self.evidence_packs / uuid.uuid4().hex)
        )['bundle_path']

    def new_ledger(self):
        self.case_number += 1
        label = 'case-%02d' % self.case_number
        case = self.base / label
        case.mkdir()
        photo_root = case / 'photos'
        collection_path = case / 'records'
        identity = notes.list_identity(visual_key='reattest-' + label)
        key = notes.list_key(identity)
        collection = notes.NotesCollection(str(collection_path))
        summary = collection.create(
            photo_root=str(photo_root), display_name='Synthetic ' + label,
            identity=identity,
            binding_evidence=self.evidence(key),
            history_scope_evidence=self.evidence(key),
            recovery_authorized=True)
        records = notes.NotesRecords(
            summary['records_root'], _allow_injected_verification=True)
        session = 'reattest-session-' + label
        records.bind(session_id=session,
                     observation=self.evidence(key),
                     handoff=self.evidence(key))
        return dict(case=case, photo_root=photo_root,
                    collection=collection, records=records,
                    list_key=key, session=session)

    def scan_posts(self, ledger, posts):
        records = ledger['records']
        key = ledger['list_key']
        scan = records.scan(
            session_id=ledger['session'], action='START',
            evidence=self.evidence(key))
        page_rows = [dict(identity=post['identity'],
                          date_summary=post['date']) for post in posts]
        scan_evidence = self.evidence(key, scan_id=scan['scan_id'])
        records.page(
            session_id=ledger['session'], scan_id=scan['scan_id'],
            page_index=0, posts=page_rows, top_reached=True,
            bottom_reached=True, overlap_keys=[], evidence=scan_evidence)
        records.scan(session_id=ledger['session'], action='FINISH',
                     scan_id=scan['scan_id'], evidence=scan_evidence)
        result = {}
        for post in posts:
            post_key = notes.post_key(key, post['identity'])
            post_evidence = self.evidence(
                key, post_key=post_key, scan_id=scan['scan_id'])
            media = post['media']
            records.record_post(
                session_id=ledger['session'], post_key_value=post_key,
                date_summary=post['date'], media_count=len(media),
                text_sha256=None, evidence=post_evidence,
                no_media=not media)
            if media:
                records.record_media(
                    session_id=ledger['session'], post_key_value=post_key,
                    items=[dict(identity=row) for row in media], missing=[],
                    evidence=post_evidence)
            result[post['name']] = dict(
                post_key=post_key, scan=scan,
                media_keys={row['visual_key']: notes.media_key(
                    key, post_key, row) for row in media})
        return result

    def complete_media(self, ledger, post_key, media_key, label):
        records = ledger['records']
        attempt = records.intent(
            session_id=ledger['session'], media_key_value=media_key)
        (Path(attempt['destination']) / (label + '.png')).write_bytes(
            b'synthetic completed photo ' + label.encode('ascii'))
        attempt_evidence = self.evidence(
            ledger['list_key'], post_key=post_key, media_key=media_key,
            attempt_id=attempt['attempt_id'], scan_id=attempt['scan_id'])
        records.outcome(
            session_id=ledger['session'], attempt_id=attempt['attempt_id'],
            outcome='DOWNLOAD_FINISHED', evidence=attempt_evidence)

        def verifier(path, row, identity):
            del path, identity
            return dict(verdict='PASS', sha256=row['sha256'])

        records.verify(session_id=ledger['session'],
                       attempt_id=attempt['attempt_id'],
                       verifier=verifier, stability_interval=0)
        return attempt

    def unknown_media(self, ledger, post_key, media_key):
        records = ledger['records']
        attempt = records.intent(
            session_id=ledger['session'], media_key_value=media_key)
        records.outcome(
            session_id=ledger['session'], attempt_id=attempt['attempt_id'],
            outcome='UNKNOWN',
            evidence=self.evidence(
                ledger['list_key'], post_key=post_key,
                media_key=media_key, attempt_id=attempt['attempt_id'],
                scan_id=attempt['scan_id']))
        return attempt

    def record_old_device(self, ledger, *, wrong_completion_device=False):
        records = ledger['records']
        list_directory = Path(records.events[0]['data']['list_directory'])
        current_device = list_directory.stat().st_dev
        old_device = current_device + 1000003
        events = [json.loads(path.read_text(encoding='utf-8'))
                  for path in sorted((records.records / 'events').iterdir())]
        plans = {event['data']['transaction_id']: event['data']
                 for event in events if event['kind'] == 'publish-plan'}
        completed = [event for event in events
                     if event['kind'] == 'completion' and
                     Path(event['data']['destination']).parent == list_directory]
        wrong_attempt = (completed[0]['data']['attempt_id']
                         if wrong_completion_device and completed else None)
        for event in events:
            data = event['data']
            if event['kind'] in ('created', 'destination') and \
                    data['list_directory'] == str(list_directory):
                data['directory_device'] = old_device
            elif event['kind'] == 'intent' and \
                    Path(data['destination']).parent == list_directory:
                data['directory_device'] = old_device
            elif event['kind'] == 'completion' and \
                    Path(data['destination']).parent == list_directory:
                device = (old_device + 1 if
                          data['attempt_id'] == wrong_attempt else old_device)
                data['target_file']['device'] = device
                data['target_directory']['device'] = old_device
            elif event['kind'] == 'publish-progress':
                plan = plans.get(data.get('transaction_id'))
                if plan is None or Path(plan['target_directory']).parent != \
                        list_directory:
                    continue
                if data['action'] == 'DIRECTORY_READY':
                    data['directory_device'] = old_device
                else:
                    data['target_device'] = old_device

        previous = None
        verification_hashes = {}
        for index, event in enumerate(events, start=1):
            event['sequence'] = index
            event['previous_sha256'] = previous
            if event['kind'] in ('publish-plan', 'completion'):
                sequence = event['data']['verification_sequence']
                event['data']['verification_sha256'] = verification_hashes[sequence]
            raw = notes.encoded(event)
            notes._atomic_replace_json(
                records.records / 'events' / ('%08d.json' % index), event)
            previous = notes.digest(raw)
            if event['kind'] == 'verification':
                verification_hashes[index] = previous
        store_path = records.records / 'store.json'
        store = json.loads(store_path.read_text(encoding='utf-8'))
        store['created_event_sha256'] = notes.digest(notes.encoded(events[0]))
        notes._atomic_replace_json(store_path, store)
        index_path = ledger['collection'].path / 'index.json'
        index = json.loads(index_path.read_text(encoding='utf-8'))
        index['lists'][records.records.name]['store_sha256'] = notes.digest(
            store_path.read_bytes())
        notes._atomic_replace_json(index_path, index)
        ledger['old_device'] = old_device
        ledger['new_device'] = current_device
        ledger['records'] = notes.NotesRecords(
            str(records.records), _allow_injected_verification=True)

    def prepare_batch(self, *, include_completion=True, outside_scope=False,
                      change_device=True, wrong_completion_device=False):
        ledger = self.new_ledger()
        photo_a = notes.media_identity(
            kind=notes.PHOTO, visual_key='completed-' + str(self.case_number))
        photo_b = notes.media_identity(
            kind=notes.PHOTO, visual_key='unknown-' + str(self.case_number))
        if outside_scope:
            outside_identity = notes.post_identity(
                visual_key='outside-post-' + str(self.case_number))
            outside_photo = notes.media_identity(
                kind=notes.PHOTO,
                visual_key='outside-completed-' + str(self.case_number))
            outside = self.scan_posts(ledger, [dict(
                name='outside', identity=outside_identity, date='synthetic',
                media=[outside_photo])])
            outside_key = outside['outside']['media_keys'][
                outside_photo['visual_key']]
            self.complete_media(
                ledger, outside['outside']['post_key'], outside_key,
                'outside-complete-' + str(self.case_number))
        post_identity = notes.post_identity(
            visual_key='current-post-' + str(self.case_number))
        current_media = [photo_b]
        if include_completion:
            current_media.insert(0, photo_a)
        current = self.scan_posts(ledger, [dict(
            name='current', identity=post_identity, date='synthetic',
            media=current_media)])
        media_keys = current['current']['media_keys']
        if include_completion:
            self.complete_media(
                ledger, current['current']['post_key'],
                media_keys[photo_a['visual_key']],
                'complete-' + str(self.case_number))
        unknown = self.unknown_media(
            ledger, current['current']['post_key'],
            media_keys[photo_b['visual_key']])
        if change_device:
            self.record_old_device(
                ledger, wrong_completion_device=wrong_completion_device)
        else:
            ledger['records'].summary()
            ledger['old_device'] = Path(
                ledger['records'].events[0]['data']['list_directory']).stat().st_dev
            ledger['new_device'] = ledger['old_device']
            ledger['records'] = notes.NotesRecords(
                str(ledger['records'].records),
                _allow_injected_verification=True)
        preview = ledger['records'].restart_preview()
        self.assertEqual(preview['status'], 'RESTART_REQUIRED')
        scoped = {row['media_key'] for post in preview['scope']['posts']
                  for row in post['media']}
        self.assertIn(unknown['media_key'], scoped)
        if include_completion and not outside_scope and change_device:
            self.assertTrue(any(
                'LOCAL_CHANGED' in post['reasons']
                for post in preview['scope']['posts']))
        ledger['records'].restart_confirm(
            session_id=ledger['session'], preview=preview,
            evidence=self.evidence(
                ledger['list_key'], scan_id=preview['scope']['scan_id']))
        ledger['records'] = notes.NotesRecords(
            str(ledger['records'].records), _allow_injected_verification=True)
        ledger['records'].summary()
        ledger['confirmation'] = next(
            event for event in ledger['records'].events
            if event['kind'] == 'restart-confirm')
        ledger['unknown_intent'] = unknown
        ledger['completion_key'] = (
            media_keys[photo_a['visual_key']] if include_completion else None)
        ledger['current_key'] = media_keys[photo_b['visual_key']]
        return ledger

    def run_preview(self, ledger, *extra_args):
        output = io.StringIO()
        args = ['reattest', 'preview', '--records-root',
                ledger['records'].records, '--session-id', ledger['session']]
        args.extend(extra_args)
        records_type = notes.NotesRecords

        def constructor(root):
            return records_type(root, _allow_injected_verification=True)

        with mock.patch.object(notes, 'NotesRecords', side_effect=constructor):
            with mock.patch('sys.stdout', new=output):
                code = notes.main([str(value) for value in args])
        return code, json.loads(output.getvalue())

    @staticmethod
    def snapshot_tree(root):
        root = Path(root)
        rows = []
        for current, directories, files in os.walk(root, followlinks=False):
            current_path = Path(current)
            for name in sorted(directories + files):
                path = current_path / name
                info = os.lstat(path)
                row = (str(path.relative_to(root)), info.st_mode,
                       info.st_dev, info.st_ino, info.st_size,
                       info.st_mtime_ns, info.st_ctime_ns)
                if stat.S_ISLNK(info.st_mode):
                    row += (os.readlink(path),)
                elif stat.S_ISREG(info.st_mode):
                    row += (hashlib.sha256(path.read_bytes()).hexdigest(),)
                rows.append(row)
        return tuple(rows)

    def assert_refused_without_mutation(self, ledger, reason):
        before = self.snapshot_tree(ledger['case'])
        code, payload = self.run_preview(ledger)
        self.assertEqual(code, 4)
        self.assertEqual(payload['status'], 'REFUSED')
        self.assertEqual(payload['reason'], reason)
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(self.snapshot_tree(ledger['case']), before)

    def test_confirmation_required_witness_is_complete_and_read_only(self):
        ledger = self.prepare_batch()
        before = self.snapshot_tree(ledger['case'])
        code, preview = self.run_preview(ledger)
        self.assertEqual(code, 0)
        self.assertEqual(preview['schema'],
                         'line-notes-list-reattest-preview/v1')
        self.assertEqual(preview['status'], 'CONFIRMATION_REQUIRED')
        self.assertFalse(preview['dispatch_authorized'])
        self.assertFalse(preview['external_copy_verified'])
        self.assertEqual(preview['real_line_e2e'], 'NOT_TESTED')
        self.assertEqual(preview['scope']['open_batch'], dict(
            confirmation_ref=notes._event_ref(ledger['confirmation']),
            restart_id=ledger['confirmation']['data']['restart_id'],
            generation=ledger['confirmation']['data']['generation'],
            scope_digest=ledger['confirmation']['data']['scope_digest']))
        witness = preview['scope']['witness']
        self.assertEqual(witness['schema'], 'line-notes-list-witness/v1')
        self.assertEqual(len(witness['completions']), 1)
        self.assertEqual(len(witness['staging']), 2)
        self.assertEqual({row['state'] for row in witness['staging']},
                         {'ABSENT_COMPLETED', 'PRESENT_EMPTY'})
        completion = witness['completions'][0]
        self.assertEqual(completion['directory_before']['device'],
                         ledger['old_device'])
        self.assertEqual(completion['directory_after']['device'],
                         ledger['new_device'])
        self.assertEqual(completion['file_before']['device'],
                         ledger['old_device'])
        self.assertEqual(completion['file_after']['device'],
                         ledger['new_device'])
        for key in ('name', 'inode', 'size', 'sha256', 'mtime_ns', 'ctime_ns'):
            self.assertEqual(completion['file_before'][key],
                             completion['file_after'][key])
        self.assertEqual(preview['scope']['witness_sha256'],
                         notes.digest(notes.encoded(witness)))
        digest_input = dict(schema=preview['schema'],
                            session_id=preview['session_id'],
                            expected_tip=preview['expected_tip'],
                            scope=preview['scope'])
        self.assertEqual(preview['preview_digest'],
                         notes.digest(notes.encoded(digest_input)))
        self.assertEqual(self.snapshot_tree(ledger['case']), before)

    def test_same_device_returns_no_change_with_empty_witness(self):
        ledger = self.prepare_batch(change_device=False)
        before = self.snapshot_tree(ledger['case'])
        code, preview = self.run_preview(ledger)
        self.assertEqual(code, 0)
        self.assertEqual(preview['status'], 'NO_CHANGE')
        self.assertEqual(preview['scope']['witness'], dict(
            schema='line-notes-list-witness/v1', completions=[], staging=[]))
        self.assertEqual(self.snapshot_tree(ledger['case']), before)

    def test_cli_requires_records_root_and_session_id(self):
        for args in (['reattest', 'preview'],
                     ['reattest', 'preview', '--records-root',
                      str(self.base / 'missing-records')]):
            with self.subTest(args=args):
                with mock.patch('sys.stderr', new=io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        notes.main(args)
                self.assertEqual(raised.exception.code, 2)

    def test_no_completion_witness_is_refused(self):
        ledger = self.prepare_batch(include_completion=False)
        self.assert_refused_without_mutation(ledger, 'REATTEST_NO_WITNESS')

    def test_extra_list_entry_is_refused(self):
        ledger = self.prepare_batch()
        (ledger['records'].current_list_directory / '.DS_Store').write_bytes(
            b'synthetic extra list entry')
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_UNSUPPORTED_LAYOUT')

    def test_unknown_staging_directory_is_refused(self):
        ledger = self.prepare_batch()
        unknown = ledger['records'].current_list_directory / \
            '.line-notes-incoming-unregistered'
        unknown.mkdir()
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_UNSUPPORTED_LAYOUT')

    def test_missing_and_extra_completion_files_are_refused(self):
        ledger = self.prepare_batch()
        completion = next(event for event in ledger['records'].events
                          if event['kind'] == 'completion')
        path = Path(completion['data']['destination']) / \
            completion['data']['target_file']['name']
        path.unlink()
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_WITNESS_CHANGED')

        ledger = self.prepare_batch()
        completion = next(event for event in ledger['records'].events
                          if event['kind'] == 'completion')
        directory = Path(completion['data']['destination'])
        (directory / 'unexpected.bin').write_bytes(b'synthetic extra file')
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_UNSUPPORTED_LAYOUT')

    def test_list_and_completion_inode_changes_are_refused(self):
        ledger = self.prepare_batch()
        list_directory = ledger['records'].current_list_directory
        moved = list_directory.with_name(list_directory.name + '.moved')
        list_directory.rename(moved)
        list_directory.mkdir()
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_BINDING_CHANGED')

        ledger = self.prepare_batch()
        completion = next(event for event in ledger['records'].events
                          if event['kind'] == 'completion')
        directory = Path(completion['data']['destination'])
        original = ledger['case'] / 'moved-completion-directory'
        original_file = directory / completion['data']['target_file']['name']
        directory.rename(original)
        directory.mkdir()
        (original / original_file.name).rename(directory / original_file.name)
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_WITNESS_CHANGED')

    def test_symlink_directory_and_ancestor_are_refused(self):
        ledger = self.prepare_batch()
        completion = next(event for event in ledger['records'].events
                          if event['kind'] == 'completion')
        directory = Path(completion['data']['destination'])
        moved = ledger['case'] / 'moved-completion-directory'
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_WITNESS_CHANGED')

        ledger = self.prepare_batch()
        root = ledger['photo_root']
        moved_root = root.with_name(root.name + '.real')
        root.rename(moved_root)
        root.symlink_to(moved_root, target_is_directory=True)
        self.assert_refused_without_mutation(
            ledger, 'INVALID_RESTART_SCOPE')

    def test_nonempty_and_missing_unresolved_staging_are_refused(self):
        ledger = self.prepare_batch()
        staging = Path(ledger['unknown_intent']['destination'])
        (staging / 'unexpected.bin').write_bytes(b'synthetic partial')
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_UNSUPPORTED_LAYOUT')

        ledger = self.prepare_batch()
        staging = Path(ledger['unknown_intent']['destination'])
        staging.rmdir()
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_WITNESS_CHANGED')

    def test_changed_completion_hash_and_metadata_are_refused(self):
        for mode in ('hash', 'size', 'mtime', 'ctime', 'inode'):
            with self.subTest(mode=mode):
                ledger = self.prepare_batch()
                completion = next(
                    event for event in ledger['records'].events
                    if event['kind'] == 'completion')
                path = Path(completion['data']['destination']) / \
                    completion['data']['target_file']['name']
                raw = path.read_bytes()
                info = path.stat()
                if mode == 'hash':
                    path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
                elif mode == 'size':
                    path.write_bytes(raw + b'x')
                elif mode == 'mtime':
                    os.utime(path, ns=(info.st_atime_ns,
                                       info.st_mtime_ns + 1000000000))
                elif mode == 'ctime':
                    original = notes._read_regular

                    def changed_ctime(target, **kwargs):
                        contents, stat_result = original(target, **kwargs)
                        # os.stat_result exposes nanosecond ctime via attributes;
                        # use a tiny proxy so the reader's other checks stay real.
                        class StatProxy:
                            pass
                        proxy = StatProxy()
                        for name in dir(stat_result):
                            if name.startswith('st_'):
                                try:
                                    setattr(proxy, name, getattr(stat_result, name))
                                except (AttributeError, TypeError):
                                    pass
                        proxy.st_ctime_ns = stat_result.st_ctime_ns + 1
                        return contents, proxy

                    with mock.patch.object(notes, '_read_regular',
                                           side_effect=changed_ctime):
                        self.assert_refused_without_mutation(
                            ledger, 'REATTEST_WITNESS_CHANGED')
                    continue
                else:
                    replacement = path.with_name('replacement.png')
                    replacement.write_bytes(raw)
                    path.unlink()
                    replacement.rename(path)
                self.assert_refused_without_mutation(
                    ledger, 'REATTEST_WITNESS_CHANGED')

    def test_symlink_hardlink_and_wrong_device_mapping_are_refused(self):
        ledger = self.prepare_batch()
        completion = next(event for event in ledger['records'].events
                          if event['kind'] == 'completion')
        path = Path(completion['data']['destination']) / \
            completion['data']['target_file']['name']
        target = ledger['case'] / 'symlink-target'
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_WITNESS_CHANGED')

        ledger = self.prepare_batch()
        completion = next(event for event in ledger['records'].events
                          if event['kind'] == 'completion')
        path = Path(completion['data']['destination']) / \
            completion['data']['target_file']['name']
        os.link(path, ledger['case'] / 'external-hardlink')
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_WITNESS_CHANGED')

        ledger = self.prepare_batch(wrong_completion_device=True)
        self.assert_refused_without_mutation(
            ledger, 'REATTEST_BINDING_CHANGED')

    def test_local_changed_completion_outside_batch_scope_is_refused(self):
        ledger = self.prepare_batch(outside_scope=True)
        before = self.snapshot_tree(ledger['case'])
        code, payload = self.run_preview(ledger)
        self.assertEqual(code, 4)
        self.assertEqual(payload['reason'], 'REATTEST_SCOPE_BLOCKED')
        self.assertEqual(payload['classification'], 'UNSCOPED_LOCAL_CHANGED')
        self.assertTrue(payload['event_refs'])
        self.assertFalse(payload['dispatch_authorized'])
        self.assertEqual(self.snapshot_tree(ledger['case']), before)


if __name__ == '__main__':
    unittest.main()
