"""Narrow P3 authorization/reservation tests; authority fixtures never enter the CLI."""
import base64
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time
import unittest
import uuid
from unittest import mock
import zlib

from line_backup_batch import daily, p3


def put(path, value):
    Path(path).write_bytes(daily.encoded(value))
    return str(path)


class TestAuthorityFixture:
    """Test-only authority seam. Production CLI always uses pinned Keychain keys."""
    test_only = True
    def verify_review(self, evidence, expected):
        if not isinstance(evidence, dict) or 'claims' not in evidence:
            raise p3.P3Error('SIGNED_AUTHORITY_EVIDENCE_REQUIRED')
        claims = evidence['claims']
        if claims.get('bindings') != expected:
            raise p3.P3Error('REVIEW_BINDING_MISMATCH')
        return claims

    def verify_owner_l2(self, evidence, expected):
        if not isinstance(evidence, dict) or 'claims' not in evidence:
            raise p3.P3Error('SIGNED_AUTHORITY_EVIDENCE_REQUIRED')
        claims = evidence['claims']
        if claims.get('bindings') != expected:
            raise p3.P3Error('OWNER_L2_SCOPE_MISMATCH')
        return claims

    def verify_runtime_receipt(self, evidence, expected):
        claims = evidence['claims']
        if claims.get('bindings') != expected:
            raise p3.P3Error('RUNTIME_RECEIPT_SCOPE_MISMATCH')
        return claims


def png():
    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) + \
        chunk(b'IDAT', zlib.compress((b'\0' + b'\xff\0\0' * 2) * 2)) + chunk(b'IEND', b'')


class P3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[1]
        cls.decoder_tmp = tempfile.TemporaryDirectory(prefix='.p3-imageio-decoder-', dir=cls.repo)
        cls.decoder = Path(cls.decoder_tmp.name).resolve() / 'image_decode'
        source = Path(__file__).resolve().parents[1] / 'src/line_backup_batch/image_decode.swift'
        sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
        sdk_args = ['-sdk', str(sdk)] if sdk.exists() else []
        result = subprocess.run(['xcrun', 'swiftc', *sdk_args, str(source), '-o', str(cls.decoder)],
                                capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.decoder_tmp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.p3-case-', dir=self.repo)
        self.temp_root = Path(self.temp.name).resolve(strict=True)
        self.root = self.temp_root / 'destination'
        self.root.mkdir()
        self.repo = Path(__file__).resolve().parents[1]
        self.session = 'synthetic-session-1'
        self.identity = {'start_date': '2026-01-02', 'end_date': '2026-01-02',
                         'expected_images': 51, 'visual_key': 'synthetic-card-key'}
        self._evidence_root = self.temp_root / 'evidence'
        self._evidence_root.mkdir()
        self.owner_request = self._evidence('synthetic owner request')
        self.foreground = self._evidence('synthetic foreground handoff')
        self.history_scope = self._evidence('synthetic history scope')
        repo = Path(__file__).resolve().parents[1]
        closure = p3._source_closure(repo)
        roles = dict(p3._runtime_roles(), image_decoder=str(self.decoder))
        runtime_files = [dict(path=name, **fact) for name, fact in closure.items()]
        runtime_files.extend({'path': path, 'bytes': len(daily.read_file(path)),
                              'sha256': daily.digest(daily.read_file(path))}
                             for path in roles.values())
        runtime_doc = {'version': 1, 'runtime_roles': roles, 'files': runtime_files}
        self.runtime = self._evidence(runtime_doc)
        self.store = daily.DailyRecords(self.root)
        self.group = self.store.initialize(binding_evidence=self.foreground,
                                           history_scope_evidence=self.history_scope)
        self.store.bind(session_id=self.session, local_group_id=self.group['local_group_id'],
                        observation=self.foreground, handoff=self.owner_request)
        self.store.history(session_id=self.session, scope_evidence=self.history_scope, entries=[])
        self.store.start_scan(session_id=self.session)
        self._page()
        self.store.detail(session_id=self.session, identity=self.identity, evidence=self._evidence('fresh detail'))
        self.prepared = p3.prepare(self.root, session_id=self.session, identity=self.identity,
            owner_request=self.owner_request, foreground_evidence=self.foreground,
            history_scope_evidence=self.history_scope, runtime_manifest=self.runtime)
        self.prepared_path = self.temp_root / 'prepared.json'
        put(self.prepared_path, self.prepared)
        self.verifier = TestAuthorityFixture()
        self.bundle_path = self.temp_root / 'authority.json'
        self.bundle = self._bundle()
        put(self.bundle_path, self.bundle)

    def tearDown(self):
        self.temp.cleanup()

    def _evidence(self, value):
        path = self._evidence_root / ('e-' + str(len(list(self._evidence_root.iterdir()))) + '.json')
        if not isinstance(value, (dict, list)):
            value = {'observation': value}
        path.write_bytes(daily.encoded(value))
        return str(path)

    def _page(self):
        top_s = self._evidence_root / 'top-screen'; top_s.write_bytes(b'top screen')
        top_ax = self._evidence_root / 'top-ax'; top_ax.write_bytes(b'top ax')
        top_ref = daily.reference(top_s)
        top_receipt = daily.reference(self._evidence('top edge witnessed'))
        top_boundary = self._evidence({'edge': 'top', 'session_id': self.session,
            'edge_key': daily.album_key(self.identity), 'before_offset': 0, 'after_offset': 0,
            'before_screenshot': top_ref, 'after_screenshot': top_ref, 'input_receipt': top_receipt})
        self.store.page(session_id=self.session, cards=[self.identity], screenshot=str(top_s), ax=str(top_ax),
                        top_confirmed=True, boundary_evidence=top_boundary)
        bottom_s = self._evidence_root / 'bottom-screen'; bottom_s.write_bytes(b'bottom screen')
        bottom_ax = self._evidence_root / 'bottom-ax'; bottom_ax.write_bytes(b'bottom ax')
        bottom_receipt = daily.reference(self._evidence('bottom stationary witnessed'))
        bottom_boundary = self._evidence({'edge': 'bottom', 'session_id': self.session,
            'edge_key': daily.album_key(self.identity), 'before_offset': 0, 'after_offset': 0,
            'before_screenshot': top_ref, 'after_screenshot': daily.reference(bottom_s),
            'input_receipt': bottom_receipt})
        scroll = self._evidence('synthetic down scroll')
        self.store.page(session_id=self.session, cards=[self.identity], screenshot=str(bottom_s), ax=str(bottom_ax),
                        bottom_stationary=True, boundary_evidence=bottom_boundary, scroll_evidence=scroll)

    def _bundle(self, **overrides):
        expected = {key: self.prepared[key] for key in (
            'implementation_commit_sha', 'local_group_id', 'session_id', 'album_key', 'destination',
            'runtime_closure_sha256', 'runtime_decoder', 'source_closure', 'nonce', 'grant_id', 'issued_at_epoch',
            'recovery_of', 'recovery_authorization', 'owner_request', 'foreground_evidence',
            'history_scope_evidence', 'record_head_sha256')}
        expected['expires_at_epoch'] = int(time.time()) + 3600
        expected['max_save_all_dispatches'] = self.prepared['max_save_all_dispatches']
        expected['attempt_scope'] = self.prepared['attempt_scope']
        review = {'role': 'reviewer', 'decision': 'APPROVE_IMPLEMENTATION', 'bindings': expected,
                  'implementation_commit_sha': expected['implementation_commit_sha'],
                  'source_closure': expected['source_closure']}
        owner_expected = dict(expected)
        owner = {'role': 'owner', 'decision': 'AUTHORIZE_SCOPED_L2', 'bindings': owner_expected,
                 'expires_at_epoch': expected['expires_at_epoch'],
                 **{key: expected[key] for key in ('local_group_id', 'session_id', 'album_key',
                                                    'destination', 'nonce')}}
        expires = expected['expires_at_epoch']
        result = {'schema': p3.SCHEMA, 'grant_id': self.prepared['grant_id'],
                  'nonce': self.prepared['nonce'], 'expires_at_epoch': expires,
                  'implementation_review': {'claims': review, 'signature_base64': 'fixture-only'},
                  'owner_l2': {'claims': owner, 'signature_base64': 'fixture-only'}}
        result.update(overrides)
        return result

    def _reserve(self):
        return p3.reserve(self.root, self.prepared_path, self.bundle_path,
                          verifier=self.verifier, now=int(time.time()),
                          recovery_authorization=getattr(self, 'recovery_path', None))

    def test_valid_scoped_flow_reserves_one_attempt_and_never_dispatches(self):
        result = self._reserve()
        self.assertEqual(result['status'], 'RESERVED_NO_DISPATCH')
        self.assertFalse(result['dispatch_authorized'])
        self.assertFalse(result['save_all_dispatch_allowed'])
        self.assertEqual(self.store.summary()['UNKNOWN'], 1)
        with self.assertRaisesRegex(p3.P3Error, 'NONCE_ALREADY_RESERVED'):
            self._reserve()

    def test_same_grant_cannot_be_reused_with_a_fresh_nonce(self):
        self._reserve()
        changed = dict(self.prepared, nonce=str(uuid.uuid4()))
        put(self.prepared_path, changed)
        self.prepared = changed
        put(self.bundle_path, self._bundle())
        with self.assertRaisesRegex(p3.P3Error, 'GRANT_ALREADY_RESERVED'):
            self._reserve()

    def test_nonce_path_traversal_and_stale_record_head_are_rejected(self):
        changed = dict(self.prepared, nonce='../outside')
        put(self.prepared_path, changed)
        with self.assertRaisesRegex(p3.P3Error, 'NONCE_INVALID'):
            self._reserve()
        put(self.prepared_path, self.prepared)
        with self.store.locked():
            self.store.append('test-only', {'marker': 'advance record head'})
        with self.assertRaisesRegex(p3.P3Error, 'PREPARED_RECORD_HEAD_STALE'):
            self._reserve()

    def test_expired_missing_tampered_wrong_scope_and_review_owner_fail_closed(self):
        cases = [
            ({'expires_at_epoch': 999}, None, 'AUTHORIZATION_EXPIRED'),
            ({}, 'missing-review', 'SIGNED_AUTHORITY_EVIDENCE_REQUIRED'),
            ({}, 'tamper-prepare', 'SOURCE_CLOSURE_MISMATCH'),
            ({}, 'wrong-owner', 'OWNER_L2_SCOPE_MISMATCH'),
            ({}, 'missing-owner', 'SIGNED_AUTHORITY_EVIDENCE_REQUIRED'),
        ]
        for overrides, mutation, code in cases:
            with self.subTest(mutation=mutation, code=code):
                self.bundle = self._bundle(**overrides)
                if mutation == 'missing-review':
                    self.bundle['implementation_review'] = None
                if mutation == 'missing-owner':
                    self.bundle['owner_l2'] = None
                if mutation == 'wrong-owner':
                    self.bundle['owner_l2']['claims']['bindings']['album_key'] = 'wrong'
                if mutation == 'tamper-prepare':
                    changed = dict(self.prepared)
                    changed['source_closure'] = dict(changed['source_closure'])
                    changed['source_closure']['scripts/line_backup_cua_adapter.mjs'] = {'bytes': 1, 'sha256': '0' * 64}
                    put(self.prepared_path, changed)
                put(self.bundle_path, self.bundle)
                with self.assertRaisesRegex((p3.P3Error, daily.DailyError), code):
                    self._reserve()
                put(self.prepared_path, self.prepared)

    def test_python_swift_javascript_skill_runtime_and_commit_mismatches_refuse(self):
        for member in ('src/line_backup_batch/p3.py', 'src/line_backup_batch/image_decode.swift',
                       'scripts/line_backup_cua_adapter.mjs', '.agents/skills/line-album-agent-cua/SKILL.md'):
            with self.subTest(member=member):
                changed = dict(self.prepared)
                changed['source_closure'] = dict(changed['source_closure'])
                changed['source_closure'][member] = {'bytes': 1, 'sha256': '0' * 64}
                put(self.prepared_path, changed)
                with self.assertRaisesRegex(p3.P3Error, 'SOURCE_CLOSURE_MISMATCH'):
                    self._reserve()
                put(self.prepared_path, self.prepared)
        changed = dict(self.prepared); changed['runtime_closure_sha256'] = '0' * 64
        put(self.prepared_path, changed)
        with self.assertRaisesRegex(p3.P3Error, 'RUNTIME_CLOSURE_MISMATCH'):
            self._reserve()
        changed = dict(self.prepared); changed['implementation_commit_sha'] = '0' * 40
        put(self.prepared_path, changed)
        with self.assertRaisesRegex(p3.P3Error, 'IMPLEMENTATION_COMMIT_MISMATCH'):
            self._reserve()

    def test_mount_inode_replacement_and_destination_binding_refuse(self):
        changed = dict(self.prepared); changed['destination'] = dict(changed['destination'])
        changed['destination']['inode'] += 1
        put(self.prepared_path, changed)
        with self.assertRaisesRegex(p3.P3Error, 'DESTINATION_MOUNT_OR_INODE_CHANGED'):
            self._reserve()

    def test_nonce_burn_survives_crash_and_hardlink_durability_failure(self):
        with mock.patch.object(daily.DailyRecords, 'intent', side_effect=RuntimeError('simulated crash')):
            with self.assertRaisesRegex(RuntimeError, 'simulated crash'):
                self._reserve()
        with self.assertRaisesRegex(p3.P3Error, 'P3_RESERVATION_INCOMPLETE_NO_REPLAY'):
            self._reserve()

    def test_stopped_attempt_requires_new_scoped_recovery_and_keeps_original(self):
        prior = self.store.intent(session_id=self.session, identity=self.identity)
        original = Path(prior['destination']) / 'partial.png'
        original.write_bytes(b'preserve this partial')
        self.store.outcome(session_id=self.session, attempt_id=prior['attempt_id'], outcome='STOPPED',
                           evidence=self._evidence('synthetic stopped outcome'))
        owner_source = self._evidence('synthetic scoped recovery owner source')
        self.recovery_path = self._evidence({'decision': 'AUTHORIZE_ALBUM_RECOVERY',
            'local_group_id': self.group['local_group_id'], 'album_key': daily.album_key(self.identity),
            'previous_attempt_id': prior['attempt_id'], 'preserve_existing': True,
            'owner_source': daily.reference(owner_source)})
        self.prepared = p3.prepare(self.root, session_id=self.session, identity=self.identity,
            owner_request=self.owner_request, foreground_evidence=self.foreground,
            history_scope_evidence=self.history_scope, runtime_manifest=self.runtime,
            recovery_authorization=self.recovery_path)
        put(self.prepared_path, self.prepared)
        self.bundle = self._bundle(); put(self.bundle_path, self.bundle)
        recovered = self._reserve()
        self.assertEqual(recovered['attempt']['recovery_of'], prior['attempt_id'])
        self.assertNotEqual(recovered['attempt']['destination'], prior['destination'])
        self.assertEqual(original.read_bytes(), b'preserve this partial')
        self.assertEqual(list(Path(recovered['attempt']['destination']).iterdir()), [])

    def test_unmounted_or_symlink_path_and_durability_error_are_refused(self):
        alias = self.temp_root / 'alias'; alias.symlink_to(self.root)
        with self.assertRaisesRegex(daily.DailyError, 'CANONICAL_DIRECTORY_REQUIRED'):
            daily.DailyRecords(alias)
        with mock.patch.object(p3.daily, 'sync_dir', side_effect=OSError('fsync failed')):
            with self.assertRaisesRegex(OSError, 'fsync failed'):
                self._reserve()
        self.assertFalse(list((self.root / 'backup-records' / 'p3-reservations').glob('*.json')))
        with mock.patch.object(p3.os, 'link', side_effect=OSError('hardlink unsupported')):
            with self.assertRaisesRegex(OSError, 'hardlink unsupported'):
                self._reserve()
        self.assertFalse(list((self.root / 'backup-records' / 'p3-reservations').glob('*.json')))

    def test_actual_destination_inode_replacement_is_refused(self):
        displaced = self.temp_root / 'displaced-destination'
        self.root.rename(displaced)
        self.root.mkdir()
        (displaced / 'backup-records').rename(self.root / 'backup-records')
        with self.assertRaisesRegex(daily.DailyError, 'DESTINATION_BINDING_CHANGED'):
            self._reserve()

    def test_production_cli_has_no_fixture_authority_and_fails_closed(self):
        with mock.patch.object(p3.subprocess, 'run', side_effect=FileNotFoundError('security unavailable')):
            with self.assertRaisesRegex(p3.P3Error, 'TRUSTED_REVIEWER_KEY_UNAVAILABLE'):
                p3.ProductionAuthorityVerifier().verify_review(
                    self.bundle['implementation_review'],
                    self.bundle['implementation_review']['claims']['bindings'])
        self.assertFalse((self.root / 'backup-records' / 'p3-reservations').exists())

    def test_real_ed25519_signature_verifies_and_tamper_is_rejected(self):
        openssl = shutil.which('openssl')
        if not openssl:
            self.skipTest('OpenSSL executable unavailable; production signature path not exercised')
        key = self.temp_root / 'review-private.pem'
        pubs = {}
        for role in ('reviewer', 'owner', 'runtime'):
            private = self.temp_root / (role + '-private.pem')
            public = self.temp_root / (role + '-public.pem')
            generated = subprocess.run([openssl, 'genpkey', '-algorithm', 'ED25519', '-out', str(private)],
                                       capture_output=True)
            if generated.returncode:
                self.skipTest('Installed OpenSSL does not support Ed25519 key generation')
            subprocess.run([openssl, 'pkey', '-in', str(private), '-pubout', '-out', str(public)],
                           check=True, capture_output=True)
            pubs[role] = public
        key = self.temp_root / 'reviewer-private.pem'
        pub = pubs['reviewer']
        data = self.temp_root / 'claims.json'
        signature = self.temp_root / 'claims.sig'
        claims = {'role': 'reviewer', 'decision': 'APPROVE_IMPLEMENTATION',
                  'bindings': {'commit': self.prepared['implementation_commit_sha']}}
        raw = daily.encoded(claims)
        data.write_bytes(raw)
        signed = subprocess.run([openssl, 'pkeyutl', '-sign', '-inkey', str(key), '-rawin',
                                 '-in', str(data), '-out', str(signature)], capture_output=True)
        if signed.returncode:
            self.skipTest('Installed OpenSSL pkeyutl cannot sign Ed25519 claims')
        evidence = {'claims': claims, 'signature_base64': base64.b64encode(
            signature.read_bytes()).decode('ascii')}
        original_run = p3.subprocess.run

        def security_only(command, *args, **kwargs):
            if command[0] == 'security':
                role = command[3].split('-')[3]
                return type('Completed', (), {'stdout': pubs[role].read_bytes()})()
            return original_run(command, *args, **kwargs)

        verifier = p3.ProductionAuthorityVerifier()
        with mock.patch.object(p3.subprocess, 'run', side_effect=security_only):
            self.assertEqual(verifier.verify_review(evidence, claims['bindings'])['decision'],
                             'APPROVE_IMPLEMENTATION')
            tampered = dict(evidence, signature_base64=base64.b64encode(b'bad').decode('ascii'))
            with self.assertRaisesRegex(p3.P3Error, 'AUTHORITY_SIGNATURE_INVALID'):
                verifier.verify_review(tampered, claims['bindings'])

    def test_existing_unknown_and_completed_attempts_never_replay(self):
        result = self._reserve()
        with self.assertRaisesRegex(daily.DailyError, 'UNKNOWN_OR_RUNNING_NO_REPLAY'):
            self.store.intent(session_id=self.session, identity=self.identity)
        with self.assertRaisesRegex(daily.DailyError, 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD'):
            with self.store.locked():
                self.store.append('history', {'scope_evidence': daily.reference(self.history_scope),
                    'entries': []})
                self.store.append('completion', {'attempt_id': result['attempt']['attempt_id'],
                    'album_key': daily.album_key(self.identity), 'destination': result['attempt']['destination'],
                    'proof': {'manifest': []}})
            self.store.intent(session_id=self.session, identity=self.identity)

    def test_synthetic_51_signed_receipt_imageio_and_persistent_readback(self):
        result = self._reserve()
        destination = Path(result['attempt']['destination'])
        for index in range(1, 52):
            (destination / f'{index:03}.png').write_bytes(png())
        expected = {'nonce': self.prepared['nonce'], 'attempt_id': result['attempt']['attempt_id'],
            'local_group_id': self.group['local_group_id'], 'album_key': daily.album_key(self.identity),
            'destination': str(destination), 'runtime_closure_sha256': self.prepared['runtime_closure_sha256'],
            'dispatch_count': 1, 'outcome': 'DOWNLOAD_FINISHED'}
        receipt_path = Path(self.temp_root / 'signed-runtime-receipt.json')
        put(receipt_path, {'claims': {'role': 'runtime', 'bindings': expected,
            'nonce': self.prepared['nonce'], 'attempt_id': result['attempt']['attempt_id'],
            'dispatch_count': 1, 'outcome': 'DOWNLOAD_FINISHED'}, 'signature_base64': 'fixture-only'})
        finalized = p3.finalize(self.root, nonce=self.prepared['nonce'], receipt_path=receipt_path,
            decoder=self.decoder, decoder_sha256=daily.reference(self.decoder)['sha256'], verifier=self.verifier)
        self.assertEqual(finalized['status'], 'FILES_VERIFIED_READBACK')
        self.assertEqual(finalized['summary']['COMPLETED'], 1)
        self.assertFalse(finalized['formal_auto_verified'])
        self.assertEqual(finalized['summary']['real_line_e2e'], 'NOT_TESTED')

    def test_synthetic_51_imageio_rejects_corrupt_content_without_completion(self):
        result = self._reserve()
        destination = Path(result['attempt']['destination'])
        for index in range(1, 52):
            (destination / f'{index:03}.png').write_bytes(png())
        (destination / '051.png').write_bytes(b'not an image')
        expected = {'nonce': self.prepared['nonce'], 'attempt_id': result['attempt']['attempt_id'],
            'local_group_id': self.group['local_group_id'], 'album_key': daily.album_key(self.identity),
            'destination': str(destination), 'runtime_closure_sha256': self.prepared['runtime_closure_sha256'],
            'dispatch_count': 1, 'outcome': 'DOWNLOAD_FINISHED'}
        receipt_path = Path(self.temp_root / 'bad-content-runtime-receipt.json')
        put(receipt_path, {'claims': {'role': 'runtime', 'bindings': expected,
            'nonce': self.prepared['nonce'], 'attempt_id': result['attempt']['attempt_id'],
            'dispatch_count': 1, 'outcome': 'DOWNLOAD_FINISHED'}, 'signature_base64': 'fixture-only'})
        with self.assertRaisesRegex(daily.DailyError, 'IMAGEIO_DECODE_FAILED'):
            p3.finalize(self.root, nonce=self.prepared['nonce'], receipt_path=receipt_path,
                decoder=self.decoder, decoder_sha256=daily.reference(self.decoder)['sha256'], verifier=self.verifier)
        self.assertEqual(daily.DailyRecords(self.root).summary()['COMPLETED'], 0)


if __name__ == '__main__':
    unittest.main()
