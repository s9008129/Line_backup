import copy
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from line_backup_acceptance import project_binding as pb
from line_backup_acceptance.cli import main, parser

REPO = Path(__file__).resolve().parents[1]
TASK = Path(os.environ.get('LINE_BACKUP_BATCH_TASK', REPO / 'harness-development/line-v3-live-e2e-20261010'))
SEED = Path(os.environ.get('LINE_BACKUP_INSPECTION_TEST_ROOT', TASK / 'fixtures')) / 'project_binding_seed'


def fixture(root):
    (root / 'config').mkdir(); (root / 'state').mkdir()
    shutil.copytree(REPO / 'src/line_backup_acceptance', root / 'src/line_backup_acceptance')
    cfg = json.loads((SEED / pb.CONFIG_PATH).read_bytes())
    cfg['backup_root'] = str(root / 'backups')
    state = json.loads((SEED / pb.STATE_PATH).read_text().replace(str(REPO), str(root)))
    for entry in state['verified_albums']:
        _, relative, _ = pb.parse_binding_reference(entry['evidence'])
        dest = root / relative; dest.parent.mkdir(parents=True, exist_ok=True)
        record = json.loads((SEED / relative).read_text().replace(str(REPO), str(root)))
        record['fixture_provenance'] = 'Synthetic root rebasing of retained identity join; no actual new native observation'
        for proof in record['evidence']:
            if proof['path'].endswith('/filesystem-verification.json'):
                original = SEED / Path(proof['path']).relative_to(root)
                target = Path(proof['path']); target.parent.mkdir(parents=True, exist_ok=True)
                proof_bytes = original.read_bytes(); target.write_bytes(proof_bytes)
                proof.update(bytes=len(proof_bytes), sha256=pb.sha(proof_bytes))
        data = json.dumps(record, ensure_ascii=False, sort_keys=True).encode(); dest.write_bytes(data)
        previous = entry['evidence']
        entry['evidence'] = 'join:' + relative + ':' + pb.sha(data)
        for run in state['runs']:
            for event in run['events']:
                if event['evidence'] == previous:
                    event['evidence'] = entry['evidence']
    (root / pb.CONFIG_PATH).write_text(json.dumps(cfg, ensure_ascii=False))
    (root / pb.STATE_PATH).write_text(json.dumps(state, ensure_ascii=False))
    return cfg, state


class ProjectBindingTests(unittest.TestCase):
    def setUp(self):
        taskroot = os.environ.get('LINE_BACKUP_INSPECTION_TEST_ROOT')
        if not taskroot:
            raise RuntimeError('Explicit task-local test root is required')
        self.temp = tempfile.TemporaryDirectory(dir=taskroot)
        self.root = Path(self.temp.name)
        self.cfg, self.state = fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        (self.root / pb.CONFIG_PATH).write_text(json.dumps(self.cfg, ensure_ascii=False))
        (self.root / pb.STATE_PATH).write_text(json.dumps(self.state, ensure_ascii=False))

    def inspect(self, start='2024-05-06', end='2024-05-10', count=182):
        return pb.inspect(str(self.root), start, end, count)

    def refuse(self, code):
        with self.assertRaises(pb.AcceptanceError) as cm:
            self.inspect()
        self.assertEqual(cm.exception.code, code)

    def new_run(self, outcome='SAFE_ABORT', intent=False):
        r = copy.deepcopy(self.state['runs'][0])
        r.update(run_id='new-run', workflow_outcome=outcome, verification=None,
                 fingerprint=dict(start_date='2024-05-06', end_date='2024-05-10', expected_images=182),
                 destination=str(self.root / 'backups' / self.cfg['group_name'] / '2024-05-06_2024-05-10_182張'),
                 manual_reconciliation_required=False, intent_state='INTENT_NONE',
                 dispatch_state='NOT_ATTEMPTED', reconciliations=[], intent=None)
        if intent:
            r['intent'] = copy.deepcopy(self.state['runs'][0]['intent'])
            r['intent'].update(fingerprint=r['fingerprint'], destination=r['destination'])
            r['intent_state'] = 'TRIGGER_UNKNOWN'; r['dispatch_state'] = 'UNKNOWN'
        self.state['runs'].append(r)
        return r

    def evidence_record(self):
        entry = self.state['verified_albums'][0]
        _, relative, _ = pb.parse_binding_reference(entry['evidence'])
        return json.loads((self.root / relative).read_bytes())

    def replace_evidence(self, payload, kind='join'):
        entry = self.state['verified_albums'][0]
        _, relative, _ = pb.parse_binding_reference(entry['evidence'])
        previous = entry['evidence']
        raw = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        (self.root / relative).write_bytes(raw)
        entry['evidence'] = kind + ':' + relative + ':' + pb.sha(raw)
        for run in self.state['runs']:
            for event in run['events']:
                if event['evidence'] == previous:
                    event['evidence'] = entry['evidence']
        self.save()
        return raw

    def user_fact(self):
        entry = self.state['verified_albums'][0]; fp = entry['fingerprint']
        path = self.root / 'user-fact-proof.json'; raw = b'{"answer":"confirmed fixture"}'; path.write_bytes(raw)
        return dict(record_version='1.0', kind='source_identity_user_fact', status='CONFIRMED',
                    source_correspondence_result='CONFIRMED', merge_prohibited=True,
                    app_identifier=self.cfg['app_identifier'], raw_requested_group=self.cfg['group_name'],
                    fingerprint=copy.deepcopy(fp), question=dict(text='Is this the exact source?'),
                    answer=dict(raw='yes', part_2=dict(confirms_same_source=True,
                                confirmed_group_string=self.cfg['group_name'],
                                confirmed_album=fp['start_date'].replace('-', '/') + '～' + fp['end_date'][5:].replace('-', '/'),
                                confirmed_expected_images=fp['expected_images'])),
                    evidence=[dict(path=str(path), bytes=len(raw), sha256=pb.sha(raw))])

    def test_correctly_rehashed_foreign_join_content_refused(self):
        original = self.evidence_record()
        mutations = [('app_identifier', 'foreign.app'), ('group_key', 'line:foreign'),
                     ('run_id', 'foreign-run'), ('destination', str(REPO / 'backups/old-destination')),
                     ('join_authority', 'unverified'), ('kind', 'unsupported'), ('record_version', '2.0'),
                     ('fingerprint', dict(start_date='2024-05-13', end_date='2024-05-17', expected_images=58)),
                     ('fingerprint', dict(start_date='2024-05-13', end_date='2024-05-17', expected_images=True))]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                record = copy.deepcopy(original); record[key] = value
                self.replace_evidence(record); self.refuse('INVALID_PROJECT_HISTORY')

    def test_correctly_rehashed_nonjson_and_duplicate_keys_refused(self):
        for raw in (b'not JSON', b'null', b'[]', b'\xff', b'{"app_identifier":"jp.naver.line.mac","app_identifier":"jp.naver.line.mac"}', b'{"fingerprint":NaN}'):
            with self.subTest(raw=raw):
                self.replace_evidence(raw); self.refuse('INVALID_PROJECT_HISTORY')

    def test_missing_join_anchors_and_event_reference_refused(self):
        original = self.evidence_record()
        for key in ('app_identifier', 'group_key', 'fingerprint', 'run_id', 'destination', 'join_authority', 'evidence'):
            with self.subTest(key=key):
                record = copy.deepcopy(original); record.pop(key)
                self.replace_evidence(record); self.refuse('INVALID_PROJECT_HISTORY')
        self.replace_evidence(original)
        run = self.state['runs'][0]
        run['events'] = [e for e in run['events'] if e['phase'] != 'VERIFIED']; self.save()
        self.refuse('INVALID_PROJECT_HISTORY')

    def test_verification_content_mismatch_with_correct_digest_refused(self):
        record = self.evidence_record()
        proof = next(e for e in record['evidence'] if e['path'].endswith('/filesystem-verification.json'))
        path = Path(proof['path']); original = json.loads(path.read_bytes())
        for key, value in [('image_files', 58), ('outcome', 'FAIL'), ('total_bytes', True)]:
            with self.subTest(key=key):
                v = copy.deepcopy(original); v[key] = value; raw = json.dumps(v).encode(); path.write_bytes(raw)
                changed = copy.deepcopy(record); p = next(e for e in changed['evidence'] if e['path'] == str(path))
                p.update(bytes=len(raw), sha256=pb.sha(raw)); self.replace_evidence(changed)
                self.refuse('INVALID_PROJECT_HISTORY')

    def test_join_verification_references_refused_if_missing_or_unsafe(self):
        original = self.evidence_record()
        for mode in ('missing', 'duplicate', 'foreign', 'bad-digest', 'bool-bytes', 'symlink'):
            with self.subTest(mode=mode):
                record = copy.deepcopy(original)
                proof = next(e for e in record['evidence'] if e['path'].endswith('/filesystem-verification.json'))
                if mode == 'missing': record['evidence'].remove(proof)
                elif mode == 'duplicate': record['evidence'].append(copy.deepcopy(proof))
                elif mode == 'foreign': proof['path'] = str(REPO / 'verification/filesystem-verification.json')
                elif mode == 'bad-digest': proof['sha256'] = '0' * 64
                elif mode == 'bool-bytes': proof['bytes'] = True
                elif mode == 'symlink':
                    path = Path(proof['path']); saved = path.with_suffix('.saved'); path.rename(saved); path.symlink_to(saved)
                self.replace_evidence(record); self.refuse('INVALID_PROJECT_HISTORY')
                if mode == 'symlink': path.unlink(); saved.rename(path)

    def test_new_verification_read_is_in_stable_snapshot(self):
        record = self.evidence_record()
        proof = next(e for e in record['evidence'] if e['path'].endswith('/filesystem-verification.json'))
        relative = str(Path(proof['path']).relative_to(self.root)); original = pb.ProjectReader.read; reads = 0
        def changed(reader, path, code='INVALID_PROJECT_AUTHORITY'):
            nonlocal reads
            result = original(reader, path, code)
            if path == relative:
                reads += 1
                if reads == 1:
                    target = self.root / relative; target.write_bytes(target.read_bytes() + b' ')
            return result
        with patch.object(pb.ProjectReader, 'read', changed): self.refuse('PROJECT_SNAPSHOT_CHANGED')

    def test_fixture_kind_joins_exact_run_and_verification(self):
        record = self.evidence_record(); record['verification'] = copy.deepcopy(self.state['runs'][0]['verification'])
        self.replace_evidence(record, kind='fixture')
        self.assertEqual(self.inspect('2024-05-13', '2024-05-17', 57)[0]['decision'], 'SKIP_VERIFIED')
        record['verification']['image_files'] = 58; self.replace_evidence(record, kind='fixture')
        self.refuse('INVALID_PROJECT_HISTORY')

    def test_user_attestation_null_run_still_skips(self):
        entry = self.state['verified_albums'][0]
        entry.update(source_kind='user_attestation', verified_run_id=None)
        self.state['runs'] = []; self.state['current_run_id'] = None
        record = self.user_fact(); self.replace_evidence(record, kind='user_fact')
        report, code = self.inspect('2024-05-13', '2024-05-17', 57)
        self.assertEqual((code, report['decision']), (0, 'SKIP_VERIFIED'))
        self.assertEqual(report['state_facts']['verified_match_registry_count'], 1)
        self.assertEqual(report['state_facts']['verified_match_run_ids'], [])
        self.assertIs(report['dispatch_authorized'], False)

    def test_user_fact_source_kind_and_confirmation_mismatches_refused(self):
        record = self.user_fact(); self.replace_evidence(record, kind='user_fact')
        self.refuse('INVALID_PROJECT_HISTORY')  # It still claims a machine-verified run.
        entry = self.state['verified_albums'][0]; entry.update(source_kind='user_attestation', verified_run_id=None)
        original = copy.deepcopy(record)
        for key, value in [('raw_requested_group', 'wrong'), ('merge_prohibited', 1), ('status', 'UNKNOWN'),
                           ('source_correspondence_result', 'UNKNOWN'), ('run_id', 'machine-run'),
                           ('destination', str(REPO / 'backups/foreign'))]:
            with self.subTest(key=key):
                changed = copy.deepcopy(original); changed[key] = value
                self.replace_evidence(changed, kind='user_fact'); self.refuse('INVALID_PROJECT_HISTORY')
        for key, value in [('confirms_same_source', 1), ('confirmed_group_string', 'wrong'),
                           ('confirmed_album', 'wrong'), ('confirmed_expected_images', True)]:
            changed = copy.deepcopy(original); changed['answer']['part_2'][key] = value
            self.replace_evidence(changed, kind='user_fact'); self.refuse('INVALID_PROJECT_HISTORY')
        for mode in ('foreign', 'bad-digest', 'empty'):
            changed = copy.deepcopy(original)
            if mode == 'foreign': changed['evidence'][0]['path'] = str(REPO / 'outside')
            elif mode == 'bad-digest': changed['evidence'][0]['sha256'] = '0' * 64
            else: changed['evidence'] = []
            self.replace_evidence(changed, kind='user_fact'); self.refuse('INVALID_PROJECT_HISTORY')

    def test_terminal_pointer_and_unknown_content(self):
        before = inventory(self.root)
        report, code = self.inspect()
        self.assertEqual((code, report['decision']), (0, 'PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION'))
        self.assertTrue(report['state_facts']['current_run_terminal'])
        self.assertIsNone(report['expected_total_bytes']); self.assertIsNone(report['expected_content_multiset_sha256'])
        for k in pb.FLAGS: self.assertIs(report[k], False)
        self.assertEqual(before, inventory(self.root))

    def test_verified_skip_never_inspects_photos(self):
        with patch.object(pb, 'destination_status', side_effect=AssertionError('must not inspect')):
            report, code = self.inspect('2024-05-13', '2024-05-17', 57)
        self.assertEqual((code, report['decision']), (0, 'SKIP_VERIFIED'))
        self.assertEqual(report['state_facts']['destination_status'], 'NOT_INSPECTED_VERIFIED')
        # The registry remains a barrier even when its attested destination differs.
        e = self.state['verified_albums'][0]; e.update(source_kind='user_attestation', verified_run_id=None)
        e['destinations'] = [str(self.root / 'backups' / 'other-destination')]
        self.replace_evidence(self.user_fact(), kind='user_fact')
        self.save(); self.assertEqual(self.inspect('2024-05-13', '2024-05-17', 57)[0]['decision'], 'SKIP_VERIFIED')

    def test_busy_precedes_skip(self):
        for field, value in [('active_writer_id', 'writer'), ('context_lock', dict(group_key=self.cfg['group_key'], source='USER_CONFIRMATION', confirmed_at='now', execution_id='e', continuity_evidence='proof'))]:
            with self.subTest(field=field):
                original = self.state[field]; self.state[field] = value; self.save()
                r, c = self.inspect('2024-05-13', '2024-05-17', 57)
                self.assertEqual((r['decision'], c), ('PROJECT_BUSY', 4))
                self.state[field] = original

    def test_nonterminal_other_target_is_busy(self):
        r = self.new_run(outcome='IN_PROGRESS'); r['fingerprint']['start_date'] = '2024-05-01'
        self.save(); self.assertEqual(self.inspect()[0]['decision'], 'PROJECT_BUSY')

    def test_unknown_intent_failed_and_safe_abort_block(self):
        for outcome in ('IN_PROGRESS', 'FAILED', 'SAFE_ABORT'):
            with self.subTest(outcome=outcome):
                self.state['runs'] = self.state['runs'][:1]
                self.new_run(outcome=outcome, intent=True); self.save()
                self.assertEqual(self.inspect()[0]['decision'], 'BLOCKED_UNRESOLVED')

    def test_legacy_unknown_is_not_permission(self):
        r = self.new_run(intent=True)
        for k in ('contract_revision', 'dispatch_state', 'dispatch_evidence'): r.pop(k, None)
        r['intent_state'] = 'UNKNOWN'; self.save()
        self.assertEqual(self.inspect()[0]['decision'], 'BLOCKED_UNRESOLVED')

    def test_purported_release_does_not_clear_intent(self):
        r = self.new_run(intent=True)
        proof = dict(run_id=r['run_id'], action_id='a', execution_id='e', observed_at='now',
                     save_all_click_count=0, save_all_invocation_attempted=False,
                     failure_boundary='BEFORE_SAVE_ALL_INVOCATION', folder_chooser_appeared=False,
                     download_started=False, provenance='fixture')
        r['reconciliations'] = [dict(reconciliation_id='rec', recorded_at='now', run_id=r['run_id'],
             action_id='a', execution_id='e', outcome='ABORTED_BEFORE_SAVE_ALL_DISPATCH',
             trigger_outcome='NOT_TRIGGERED', blocking_intent_released=True,
             manual_reconciliation_required=False, original_observation=dict(reference='fixture', trigger_outcome='UNKNOWN'),
             proof=proof, evidence='fixture')]
        r['intent_state'] = 'ABORTED_BEFORE_SAVE_ALL_DISPATCH'; self.save()
        report, code = self.inspect()
        self.assertEqual((report['decision'], code), ('BLOCKED_UNRESOLVED', 4))
        self.assertEqual(report['state_facts']['purported_release_run_ids'], [r['run_id']])

    def test_registry_evidence_is_part_of_stable_snapshot(self):
        original = pb.ProjectReader.read
        evidence_path = pb.parse_binding_reference(self.state['verified_albums'][0]['evidence'])[1]
        reads = 0
        def changed(reader, relative, code='INVALID_PROJECT_AUTHORITY'):
            nonlocal reads
            result = original(reader, relative, code)
            if relative == evidence_path:
                reads += 1
                if reads == 1:
                    p = self.root / relative; p.write_bytes(p.read_bytes() + b' ')
            return result
        with patch.object(pb.ProjectReader, 'read', changed):
            self.refuse('PROJECT_SNAPSHOT_CHANGED')

    def test_count_ambiguity(self):
        r, c = self.inspect('2024-05-13', '2024-05-17', 58)
        self.assertEqual((r['decision'], c), ('AMBIGUOUS_FINGERPRINT', 4))

    def test_invalid_history_relationships(self):
        original = copy.deepcopy(self.state)
        mutations = [lambda s: s.update(current_run_id='dangling'),
                     lambda s: s['runs'].append(copy.deepcopy(s['runs'][0])),
                     lambda s: s['runs'][0].update(group_key='foreign'),
                     lambda s: s['verified_albums'][0].update(verified_run_id='missing'),
                     lambda s: s['verified_albums'][0]['fingerprint'].update(expected_images=58),
                     lambda s: s['runs'][0].update(verification=None),
                     lambda s: s['verified_albums'][0].update(source_kind='user_attestation'),
                     lambda s: s['runs'][0]['intent'].update(group_key='foreign')]
        for m in mutations:
            with self.subTest(m=m):
                self.state = copy.deepcopy(original); m(self.state); self.save(); self.refuse('INVALID_PROJECT_HISTORY')

    def test_config_contract(self):
        original = copy.deepcopy(self.cfg)
        for key, value in [('group_key', 'wrong'), ('group_name', '../unsafe'), ('app_identifier', 'foreign'),
                           ('backup_root', '/foreign'), ('schema_version', True), ('stable_samples', True), ('max_wait_seconds', None)]:
            with self.subTest(key=key):
                self.cfg = copy.deepcopy(original); self.cfg[key] = value; self.save(); self.refuse('INVALID_CONFIG')

    def test_dates_and_count_types(self):
        for start, end, count in [('2024-02-30', '2024-05-10', 182), ('2024-05-10', '2024-05-06', 182),
                                  ('2024-5-06', '2024-05-10', 182), ('2024-05-06', '2024-05-10', True),
                                  ('2024-05-06', '2024-05-10', 0), ('2024-05-06', '2024-05-10', 1.5)]:
            with self.subTest(count=count, start=start):
                with self.assertRaises(pb.AcceptanceError) as cm: self.inspect(start, end, count)
                self.assertEqual(cm.exception.code, 'INVALID_INPUT')

    def test_duplicate_keys_and_malformed_state(self):
        (self.root / pb.STATE_PATH).write_bytes(b'{"revision":1,"revision":2}')
        self.refuse('INVALID_STATE')
        for data in (b'null', b'{"revision":NaN}', b'\xff'):
            (self.root / pb.STATE_PATH).write_bytes(data); self.refuse('INVALID_STATE')

    def test_root_and_component_symlinks(self):
        for root in ('relative', str(self.root) + '/..', None):
            with self.assertRaises(pb.AcceptanceError): pb.inspect(root, '2024-05-06', '2024-05-10', 182)
        p = self.root / pb.STATE_PATH; real = p.with_suffix('.real'); p.rename(real); p.symlink_to(real)
        self.refuse('INVALID_PROJECT_AUTHORITY')
        p.unlink(); real.rename(p)
        directory = self.root / 'config'; actual = self.root / 'actual-config'; directory.rename(actual); directory.symlink_to(actual)
        self.refuse('INVALID_PROJECT_AUTHORITY')

    def test_missing_source_and_evidence(self):
        (self.root / 'src/line_backup_acceptance/project_binding.py').unlink(); self.refuse('INVALID_PROJECT_AUTHORITY')

    def test_evidence_hash_or_path_is_not_trusted(self):
        original = self.state['verified_albums'][0]['evidence']
        for value in ('join:../outside:' + 'a'*64, original[:-1] + ('a' if original[-1] != 'a' else 'b')):
            self.state['verified_albums'][0]['evidence'] = value; self.save()
            with self.assertRaises(pb.AcceptanceError): self.inspect()

    def test_nonempty_and_unsafe_destination(self):
        r, _ = self.inspect(); dest = Path(r['target']['proposed_destination'])
        dest.mkdir(parents=True); (dest / 'existing.jpg').write_bytes(b'existing')
        self.assertEqual(self.inspect()[0]['decision'], 'BLOCKED_DESTINATION')
        (dest / 'existing.jpg').unlink(); self.assertEqual(self.inspect()[0]['state_facts']['destination_status'], 'EMPTY')
        dest.rmdir(); dest.symlink_to(self.root)
        self.assertEqual(self.inspect()[0]['state_facts']['destination_status'], 'UNSAFE')

    def test_destination_and_parent_replacement_rejected(self):
        destination = self.root / 'backups' / self.cfg['group_name'] / '2024-05-06_2024-05-10_182張'
        destination.mkdir(parents=True)
        for replacement in ('destination', 'parent'):
            with self.subTest(replacement=replacement):
                inode = destination.stat().st_ino
                original = os.listdir
                fired = False
                def changed(fd):
                    nonlocal fired
                    result = original(fd)
                    if isinstance(fd, int) and os.fstat(fd).st_ino == inode and not fired:
                        fired = True
                        if replacement == 'destination':
                            destination.rename(destination.with_name('old-destination'))
                            destination.mkdir(); (destination / 'arrived').write_bytes(b'new')
                        else:
                            parent = destination.parent; moved = parent.with_name('moved-group')
                            parent.rename(moved); parent.symlink_to(moved)
                    return result
                with patch.object(os, 'listdir', changed): self.refuse('PROJECT_SNAPSHOT_CHANGED')
                self.assertTrue(fired)
                if replacement == 'destination':
                    (destination / 'arrived').unlink(); destination.rmdir(); destination.with_name('old-destination').rename(destination)
                else:
                    parent = destination.parent; moved = parent.with_name('moved-group')
                    parent.unlink(); moved.rename(parent)

    def test_absent_destination_becoming_nonempty_rejected(self):
        original = pb._destination_snapshot
        first = True
        def changed(reader, relative):
            nonlocal first
            result = original(reader, relative)
            if first:
                first = False
                path = self.root / relative; path.mkdir(parents=True); (path / 'arrived').write_bytes(b'new')
            return result
        with patch.object(pb, '_destination_snapshot', changed): self.refuse('PROJECT_SNAPSHOT_CHANGED')

    def test_stable_read_rejects_change_and_replacement(self):
        original = pb.ProjectReader.read
        for replacement in (False, True):
            calls = 0
            def changed(reader, relative, code='INVALID_PROJECT_AUTHORITY'):
                nonlocal calls
                result = original(reader, relative, code)
                if relative == pb.CONFIG_PATH:
                    calls += 1
                    if calls == 1:
                        p = self.root / relative
                        if replacement:
                            b = p.read_bytes(); p.unlink(); p.write_bytes(b)
                        else: p.write_bytes(p.read_bytes() + b' ')
                return result
            with self.subTest(replacement=replacement), patch.object(pb.ProjectReader, 'read', changed):
                self.refuse('PROJECT_SNAPSHOT_CHANGED')
            self.save()

    def test_cli_refusal_and_legacy_parser(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            c = main(['project-preflight', '--project-root', str(self.root), '--start-date', 'bad', '--end-date', '2024-05-10', '--expected-images', '182'])
        self.assertEqual(c, 2); self.assertEqual(json.loads(out.getvalue())['kind'], 'REFUSAL')
        self.assertEqual(parser().parse_args(['transaction', 'resume']).command, 'transaction')
        self.assertEqual(parser().parse_args(['verify-only']).command, 'verify-only')
        self.assertEqual(parser().parse_args(['status', 'evaluate']).operation, 'evaluate')

    def test_wire_schema_offline(self):
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry
        schema = json.loads((TASK / 'contracts/project-binding-report.schema.json').read_bytes())
        def refuse(uri): raise AssertionError('external schema lookup ' + uri)
        v = Draft202012Validator(schema, registry=Registry(retrieve=refuse), format_checker=FormatChecker())
        v.validate(self.inspect()[0]); v.validate(self.inspect('2024-05-13', '2024-05-17', 57)[0])


def inventory(root):
    return [(str(p.relative_to(root)), pb.sha(p.read_bytes())) for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()]


if __name__ == '__main__': unittest.main()
