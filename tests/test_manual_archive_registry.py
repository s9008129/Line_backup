import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from line_backup_acceptance.common import AcceptanceError
from line_backup_acceptance.manual_archive import (
    A45, A56, B53, B78, EXCLUDED_65, REGISTRY_PATH, load_manual_archives,
    owner_target_allowed, owner_target_excluded, record_manual_archives, required_for_root,
)
from line_backup_acceptance.project_binding import ProjectReader, history_decision

GROUP_NAME = 'Owner Group'
GROUP_KEY = 'line:jp.naver.line.mac:' + GROUP_NAME
APP = 'jp.naver.line.mac'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def date_label(fingerprint):
    return fingerprint['start_date'].replace('-', '/') + '～' + fingerprint['end_date'][5:].replace('-', '/')


def archive_files(fingerprint):
    count = fingerprint['expected_images']
    return [(f'image-{index:04d}.jpg', f'{fingerprint["start_date"]}:{index}'.encode())
            for index in range(count)]


def file_rows(fingerprint):
    return [dict(file=name, bytes=len(data), sha256=sha(data)) for name, data in archive_files(fingerprint)]


class ManualRegistryFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(dir='/private/tmp')
        self.root = Path(self.temp.name)
        (self.root / 'state').mkdir()
        (self.root / 'config').mkdir()
        (self.root / 'archive').mkdir()
        (self.root / 'backups' / GROUP_NAME).mkdir(parents=True)
        (self.root / 'config/line_backup_config.json').write_text(json.dumps(dict(
            schema_version=2, group_key=GROUP_KEY, group_name=GROUP_NAME,
            backup_root=str(self.root / 'backups'), app_identifier=APP, max_albums_per_run=1,
            recovery_limit=1, poll_interval_seconds=1, stable_samples=2, max_wait_seconds=30,
        )), encoding='utf-8')
        self.registry = dict(schema_version=1, kind='manual_archive_registry', app_identifier=APP,
                             group_key=GROUP_KEY, entries=[])

    def close(self):
        self.temp.cleanup()

    def add(self, fingerprint):
        rows = file_rows(fingerprint)
        manifest = ''.join(f'{row["sha256"]}  {row["file"]}\n' for row in rows).encode()
        verification = dict(
            schema='MANUAL_DIAGNOSTIC_ALBUM_VERIFICATION/1',
            mode='MANUAL_DIAGNOSTIC_NOT_FORMAL_E2E',
            album=dict(dates=date_label(fingerprint), expected_images=fingerprint['expected_images']),
            destination_workspace_relative=(f'backups/{GROUP_NAME}/{fingerprint["start_date"]}_'
                                            f'{fingerprint["end_date"]}_{fingerprint["expected_images"]}張'),
            files=dict(count=len(rows), total_bytes=sum(row['bytes'] for row in rows), entries=rows),
        )
        stem = f'{fingerprint["start_date"]}-{fingerprint["expected_images"]}'
        manifest_path = self.root / 'archive' / f'{stem}-sha256.txt'
        verification_path = self.root / 'archive' / f'{stem}-verification.json'
        destination = self.root / verification['destination_workspace_relative']
        destination.mkdir()
        for name, data in archive_files(fingerprint):
            (destination / name).write_bytes(data)
        manifest_path.write_bytes(manifest)
        verification_path.write_text(json.dumps(verification, ensure_ascii=False, sort_keys=True), encoding='utf-8')
        entry = dict(fingerprint=dict(fingerprint), provenance='MANUAL_DIAGNOSTIC',
                     recorded_at='2026-10-20T12:00:00+00:00',
                     manifest_path=str(manifest_path), manifest_sha256=sha(manifest),
                     verification_path=str(verification_path),
                     verification_sha256=sha(verification_path.read_bytes()),
                     file_count=len(rows), total_bytes=sum(row['bytes'] for row in rows))
        self.registry['entries'].append(entry)
        return entry, manifest_path, verification_path, destination

    def write(self):
        (self.root / REGISTRY_PATH).write_text(json.dumps(self.registry, ensure_ascii=False, sort_keys=True),
                                               encoding='utf-8')

    def load(self, **kwargs):
        reader = ProjectReader(str(self.root))
        try:
            return load_manual_archives(reader, app_identifier=APP, group_key=GROUP_KEY, **kwargs)
        finally:
            reader.close()


class ManualArchiveRegistryTests(unittest.TestCase):
    def setUp(self):
        self.f = ManualRegistryFixture()

    def tearDown(self):
        self.f.close()

    def test_valid_registry_returns_a56_and_b53(self):
        self.f.add(A56)
        self.f.add(B53)
        self.f.write()
        self.assertEqual(self.f.load(required=True, required_fingerprints=(A56, B53)),
                         frozenset({(A56['start_date'], A56['end_date'], 56),
                                    (B53['start_date'], B53['end_date'], 53)}))

    def test_missing_required_registry_fails_closed_but_generic_load_is_empty(self):
        self.assertEqual(self.f.load(), frozenset())
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load(required=True)
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_REQUIRED')

    def test_registry_is_required_only_for_the_installed_project(self):
        self.assertTrue(required_for_root(str(Path(__file__).resolve().parents[1])))
        self.assertFalse(required_for_root(str(self.f.root)))

    def test_manifest_hash_change_fails_closed(self):
        _, manifest_path, _, _ = self.f.add(A56)
        self.f.write()
        manifest_path.write_bytes(manifest_path.read_bytes() + b'x')
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_verification_count_change_fails_closed(self):
        entry, _, verification_path, _ = self.f.add(A56)
        value = json.loads(verification_path.read_bytes())
        value['files']['count'] -= 1
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
        verification_path.write_bytes(raw)
        entry['verification_sha256'] = sha(raw)
        self.f.write()
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_missing_manifest_fails_closed(self):
        _, manifest_path, _, _ = self.f.add(A56)
        self.f.write()
        manifest_path.unlink()
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_redacted_or_noncanonical_destination_fails_closed(self):
        entry, _, verification_path, _ = self.f.add(A56)
        value = json.loads(verification_path.read_bytes())
        value['destination_workspace_relative'] = value['destination_workspace_relative'].replace(GROUP_NAME, '<REDACTED_GROUP>')
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
        verification_path.write_bytes(raw)
        entry['verification_sha256'] = sha(raw)
        self.f.write()
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_wrong_provenance_fails_closed(self):
        entry, _, _, _ = self.f.add(A56)
        entry['provenance'] = 'FORMAL_VERIFIED'
        self.f.write()
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_required_fingerprint_missing_fails_closed(self):
        self.f.add(A56)
        self.f.write()
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load(required=True, required_fingerprints=(A56, B53))
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_REQUIRED')

    def test_owner_excluded_65_cannot_be_recorded_as_manual(self):
        entry, _, _, _ = self.f.add(EXCLUDED_65)
        self.f.write()
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_unknown_manual_fingerprint_is_not_a_skip_permission(self):
        entry, _, _, _ = self.f.add(A45)
        self.f.write()
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_recorder_hashes_actual_files_and_reloads_registry(self):
        records = []
        for fingerprint in (A56, B53):
            entry, manifest_path, verification_path, destination = self.f.add(fingerprint)
            records.append(dict(fingerprint=dict(fingerprint), destination=str(destination),
                                manifest_path=str(manifest_path), verification_path=str(verification_path)))
        result = record_manual_archives(str(self.f.root), records,
                                        recorded_at='2026-10-21T00:00:00+00:00')
        self.assertEqual(result['status'], 'MANUAL_ARCHIVE_REGISTRY_RECORDED')
        registry = json.loads((self.f.root / REGISTRY_PATH).read_bytes())
        self.assertTrue(all(not entry['manifest_path'].startswith('/') for entry in registry['entries']))
        self.assertTrue(all(not entry['verification_path'].startswith('/') for entry in registry['entries']))
        self.assertEqual(self.f.load(required=True, required_fingerprints=(A56, B53)),
                         frozenset({(A56['start_date'], A56['end_date'], 56),
                                    (B53['start_date'], B53['end_date'], 53)}))

    def test_recorder_rejects_local_file_byte_drift(self):
        entry, manifest_path, verification_path, destination = self.f.add(A56)
        (destination / 'image-0000.jpg').write_bytes(b'tampered')
        with self.assertRaises(AcceptanceError) as caught:
            record_manual_archives(str(self.f.root), [dict(
                fingerprint=dict(A56), destination=str(destination), manifest_path=str(manifest_path),
                verification_path=str(verification_path))])
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_registry_load_rechecks_actual_archive_bytes(self):
        entry, _, _, destination = self.f.add(A56)
        self.f.write()
        (destination / 'image-0000.jpg').write_bytes(b'tampered')
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')

    def test_registry_load_rejects_extra_archive_file(self):
        entry, _, _, destination = self.f.add(A56)
        self.f.write()
        (destination / 'unexpected.jpg').write_bytes(b'extra')
        with self.assertRaises(AcceptanceError) as caught:
            self.f.load()
        self.assertEqual(caught.exception.code, 'MANUAL_ARCHIVE_REGISTRY_INVALID')


class ManualDecisionPrecedenceTests(unittest.TestCase):
    def state(self):
        return dict(active_batch=None, active_writer_id=None, context_lock=None, current_run_id=None,
                    runs=[], verified_albums=[])

    def run_record(self, fingerprint=A56, **changes):
        value = dict(run_id='run-1', fingerprint=dict(fingerprint), workflow_outcome='SAFE_ABORT', intent=None,
                     intent_state='INTENT_NONE', manual_reconciliation_required=False,
                     dispatch_state='NOT_ATTEMPTED', reconciliations=[])
        value.update(changes)
        return value

    def test_precedence_keeps_verified_ambiguous_and_unresolved_ahead_of_manual(self):
        key = (A56['start_date'], A56['end_date'], 56)
        target = dict(fingerprint=A56)
        verified = self.state(); verified['runs'] = [self.run_record(workflow_outcome='VERIFIED')]
        self.assertEqual(history_decision(verified, target, {}, {key})[0], 'SKIP_VERIFIED')
        ambiguous = self.state(); ambiguous['runs'] = [self.run_record(fingerprint=dict(A56, expected_images=55))]
        self.assertEqual(history_decision(ambiguous, target, {}, {key})[0], 'AMBIGUOUS_FINGERPRINT')
        unresolved = self.state(); unresolved['runs'] = [self.run_record(workflow_outcome='IN_PROGRESS')]
        self.assertEqual(history_decision(unresolved, target, {}, {key})[0], 'BLOCKED_UNRESOLVED')
        manual = self.state()
        decision, facts = history_decision(manual, target, {}, {key})
        self.assertEqual(decision, 'SKIP_MANUAL_DIAGNOSTIC')
        self.assertTrue(facts['manual_archive_match'])
        self.assertEqual(facts['destination_status'], 'MANUAL_ARCHIVE_RECORDED')

    def test_owner_allowlist_contains_only_a45_and_b78_and_permanently_excludes_65(self):
        self.assertTrue(owner_target_allowed(A45))
        self.assertTrue(owner_target_allowed(B78))
        self.assertFalse(owner_target_allowed(A56))
        self.assertFalse(owner_target_allowed(B53))
        self.assertTrue(owner_target_excluded(EXCLUDED_65))
        self.assertFalse(owner_target_excluded(A45))


if __name__ == '__main__':
    unittest.main()
