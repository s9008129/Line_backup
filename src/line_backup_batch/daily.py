"""Destination-bound records for the foreground CUA Agent; never grants GUI authority.

The Agent grounds cards and boundary observations. This module checks accounting,
durably reserves attempts and verifies files. It neither finds nor clicks controls.
Historical formal state/grants are deliberately outside its write surface.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import time
import uuid

from line_backup_acceptance.project_binding import strict_json

NORMALIZED_HISTORY_SCHEMA = 'line-backup-daily-history/v1'


class DailyError(ValueError):
    pass


def need(condition, code):
    if not condition:
        raise DailyError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       separators=(',', ':')) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def directory(value):
    path = Path(value).expanduser().absolute()
    need(path == path.resolve(strict=True) and path.is_dir(), 'CANONICAL_DIRECTORY_REQUIRED')
    return path


def read_file(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'REGULAR_SINGLE_LINK_FILE_REQUIRED')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            raw = stream.read()
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'FILE_CHANGED')
        need(os.stat(path, follow_symlinks=False).st_ino == after.st_ino, 'FILE_REPLACED')
        return raw
    finally:
        os.close(fd)


def reference(value):
    path = Path(value).expanduser().absolute()
    need(path == path.resolve(strict=True), 'EVIDENCE_SYMLINK_REFUSED')
    raw = read_file(path)
    need(bool(raw), 'EMPTY_EVIDENCE')
    return dict(path=str(path), bytes=len(raw), sha256=digest(raw))


def check_ref(ref):
    need(isinstance(ref, dict) and reference(ref['path']) == ref, 'EVIDENCE_DRIFT')


def sync_dir(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def create_json(path, value):
    """Publish complete bytes exclusively; a failed write never replaces old data."""
    temporary = path.parent / ('.pending-' + uuid.uuid4().hex)
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        raw = encoded(value)
        with os.fdopen(os.dup(fd), 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(str(temporary), str(path), follow_symlinks=False)
    finally:
        os.close(fd)
    temporary.unlink()
    sync_dir(path.parent)
    need(read_file(path) == raw, 'RECORD_READBACK_FAILED')


def album_key(identity):
    need(isinstance(identity, dict) and set(identity) ==
         {'start_date', 'end_date', 'expected_images', 'visual_key'}, 'ALBUM_IDENTITY_REQUIRED')
    need(type(identity['expected_images']) is int and identity['expected_images'] > 0,
         'PHOTO_COUNT_REQUIRED')
    for name in ('start_date', 'end_date', 'visual_key'):
        need(isinstance(identity[name], str) and bool(identity[name].strip()), 'VISUAL_IDENTITY_REQUIRED')
    # visual_key is a persisted Agent-grounded disambiguator, not Chinese OCR.
    return digest(encoded(identity))


def boundary_reference(path, edge, session_id, key, screenshot, previous_screenshot=None):
    ref = reference(path)
    observation = strict_json(read_file(path), 'INVALID_BOUNDARY_OBSERVATION')
    need(observation.get('edge') == edge and observation.get('session_id') == session_id and
         observation.get('edge_key') == key, 'BOUNDARY_CONTEXT_MISMATCH')
    before, after = observation.get('before_offset'), observation.get('after_offset')
    need(type(before) in (int, float) and type(after) in (int, float) and
         math.isfinite(before) and math.isfinite(after) and before >= 0 and before == after,
         'BOUNDARY_MOVEMENT_OBSERVED')
    if edge == 'top':
        need(after == 0, 'TOP_NOT_REACHED')
    for name in ('before_screenshot', 'after_screenshot', 'input_receipt'):
        check_ref(observation[name])
    need(observation['after_screenshot'] == screenshot, 'BOUNDARY_FRAME_MISMATCH')
    if previous_screenshot is not None:
        need(observation['before_screenshot'] == previous_screenshot, 'BOUNDARY_BEFORE_FRAME_MISMATCH')
    return ref


class DailyRecords:
    def __init__(self, root):
        self.root = directory(root)
        self.records = self.root / 'backup-records'

    def initialize(self, *, binding_evidence, history_scope_evidence, context_id=None):
        """Only after current foreground handoff and history-scope inspection.

        context_id is an optional reliable opaque LINE id. An OCR title is not one.
        Evidence is an observation/Owner source reference, never manufactured consent.
        """
        binding = reference(binding_evidence)
        history = reference(history_scope_evidence)
        need(context_id is None or isinstance(context_id, str) and bool(context_id), 'INVALID_CONTEXT_ID')
        need(not self.records.exists() and not self.records.is_symlink(), 'RECORDS_ALREADY_EXIST')
        self.records.mkdir(mode=0o700)
        (self.records / 'events').mkdir(mode=0o700)
        identity = self.root.stat()
        group = dict(version=1, local_group_id=str(uuid.uuid4()), destination=str(self.root),
                     destination_device=identity.st_dev, destination_inode=identity.st_ino,
                     context_id=context_id, binding_evidence=binding, history_scope_evidence=history,
                     recovery_strategy='ALBUM_LEVEL', photo_level_resume='FUTURE_RESEARCH')
        create_json(self.records / 'group.json', group)
        sync_dir(self.root)
        return group

    @contextlib.contextmanager
    def locked(self):
        directory(self.root)
        need(directory(self.records) == self.records, 'RECORD_DIRECTORY_CHANGED')
        need(directory(self.records / 'events') == self.records / 'events', 'EVENT_DIRECTORY_CHANGED')
        fd = os.open(str(self.records / '.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            need(stat.S_ISREG(os.fstat(fd).st_mode) and os.fstat(fd).st_nlink == 1, 'UNSAFE_LOCK')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.group = strict_json(read_file(self.records / 'group.json'), 'INVALID_GROUP_RECORD')
            identity = self.root.stat()
            need(self.group['destination'] == str(self.root) and
                 self.group['destination_device'] == identity.st_dev and
                 self.group['destination_inode'] == identity.st_ino, 'DESTINATION_BINDING_CHANGED')
            self.events = []
            previous = None
            for index, path in enumerate(sorted((self.records / 'events').iterdir()), 1):
                need(path.name == '%08d.json' % index, 'EVENT_SEQUENCE_OR_PENDING_WRITE')
                raw = read_file(path)
                event = strict_json(raw, 'INVALID_EVENT')
                need(event['sequence'] == index and event['previous_sha256'] == previous and
                     event['local_group_id'] == self.group['local_group_id'], 'EVENT_BINDING_CHANGED')
                self.events.append(event)
                previous = digest(raw)
            self.previous = previous
            yield
        finally:
            os.close(fd)

    def append(self, kind, data):
        event = dict(sequence=len(self.events) + 1, previous_sha256=self.previous,
                     local_group_id=self.group['local_group_id'], kind=kind, data=data)
        create_json(self.records / 'events' / ('%08d.json' % event['sequence']), event)
        self.events.append(event)
        self.previous = digest(encoded(event))
        return data

    def matching(self, kind):
        return [e['data'] for e in self.events if e['kind'] == kind]

    def bound(self, session_id):
        bindings = self.matching('binding')
        need(bindings and bindings[-1]['session_id'] == session_id, 'FRESH_FOREGROUND_BINDING_REQUIRED')
        for ref in bindings[-1]['evidence'].values():
            check_ref(ref)

    def bind(self, *, session_id, local_group_id, observation, handoff, context_id=None):
        with self.locked():
            need(local_group_id == self.group['local_group_id'], 'WRONG_LOCAL_GROUP')
            need(context_id == self.group['context_id'], 'WRONG_CONTEXT')
            need(isinstance(session_id, str) and bool(session_id), 'SESSION_REQUIRED')
            return self.append('binding', dict(session_id=session_id,
                evidence=dict(observation=reference(observation), handoff=reference(handoff))))

    def history(self, *, session_id, scope_evidence, entries):
        """Import explicitly group-mapped barriers; no implicit date/count match.

        The Agent inspects formal state, manual archives, private completions and
        exclusions first. Each imported barrier keeps its original source/provenance.
        """
        with self.locked():
            self.bound(session_id)
            need(not self.matching('history'), 'HISTORY_ALREADY_RECONCILED')
            result = []
            for entry in entries:
                key = album_key(entry['identity'])
                need(entry['local_group_id'] == self.group['local_group_id'], 'CROSS_GROUP_HISTORY_REFUSED')
                need(entry['status'] in ('COMPLETED', 'EXCLUDED'), 'INVALID_HISTORY_STATUS')
                need(key not in [r['album_key'] for r in result], 'AMBIGUOUS_HISTORY')
                source = reference(entry['source'])
                supported = self._normalized_history(source['path'], entry['identity'])
                status = (supported if supported in ('COMPLETED', 'EXCLUDED') and
                          supported == entry['status'] else 'PROTECTED_HISTORY')
                result.append(dict(album_key=key, identity=entry['identity'], status=status,
                                   declared_status=entry['status'], source=source))
            return self.append('history', dict(scope_evidence=reference(scope_evidence), entries=result))

    def _normalized_history(self, source_path, identity):
        """Return a supported normalized status; preserve every other legacy source.

        Normalization verifies the stated local group and full album identity, and,
        for a completion, the manifest and ImageIO evidence files. It does not turn
        historical provenance into a fresh download or formal verification.
        """
        try:
            document = json.loads(read_file(source_path))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(document, dict) or document.get('schema') != NORMALIZED_HISTORY_SCHEMA:
            return None
        if (document.get('local_group_id') != self.group['local_group_id'] or
                document.get('identity') != identity or
                document.get('album_key') != album_key(identity)):
            return None
        status = document.get('status')
        if status == 'EXCLUDED':
            try:
                exclusion_ref = document['exclusion_evidence']
                check_ref(exclusion_ref)
                exclusion = json.loads(read_file(exclusion_ref['path']))
                if (not isinstance(exclusion, dict) or
                        exclusion.get('schema') != 'line-backup-exclusion/v1' or
                        exclusion.get('local_group_id') != self.group['local_group_id'] or
                        exclusion.get('identity') != identity or
                        exclusion.get('album_key') != album_key(identity) or
                        exclusion.get('decision') != 'EXCLUDE_ALBUM'):
                    return None
                check_ref(exclusion['owner_source'])
            except (KeyError, DailyError, OSError, ValueError, TypeError):
                return None
            return status
        if status != 'COMPLETED':
            return None
        try:
            proof = document['photo_verification']
            expected = identity['expected_images']
            if proof['expected_images'] != expected:
                return None
            manifest_ref = proof['manifest_evidence']
            imageio_ref = proof['imageio_evidence']
            check_ref(manifest_ref)
            check_ref(imageio_ref)
            manifest_doc = json.loads(read_file(manifest_ref['path']))
            imageio = json.loads(read_file(imageio_ref['path']))
            manifest = manifest_doc['manifest']
            if (manifest_doc.get('manifest_sha256') != digest(encoded(manifest)) or
                    proof.get('manifest_sha256') != manifest_doc['manifest_sha256'] or
                    not isinstance(manifest, list) or len(manifest) != expected):
                return None
            names = set()
            for row in manifest:
                name = row['name']
                if (not isinstance(name, str) or not name or Path(name).name != name or
                        name.startswith('.') or name in names or type(row['size']) is not int or
                        row['size'] <= 0 or not isinstance(row['sha256'], str) or
                        len(row['sha256']) != 64 or any(c not in '0123456789abcdef' for c in row['sha256'])):
                    return None
                names.add(name)
            decoded = imageio.get('entries')
            if (imageio.get('verdict') != 'PASS' or imageio.get('readOnly') is not True or
                    imageio.get('expected') != expected or imageio.get('actualEntries') != expected or
                    not isinstance(decoded, list) or len(decoded) != expected):
                return None
            decoded_by_name = {}
            for row in decoded:
                if row.get('decoded') is not True or row.get('name') in decoded_by_name:
                    return None
                decoded_by_name[row['name']] = row.get('sha256')
            if decoded_by_name != {row['name']: row['sha256'] for row in manifest}:
                return None
            return status
        except (AttributeError, KeyError, DailyError, OSError, ValueError, TypeError):
            return None

    def start_scan(self, *, session_id):
        with self.locked():
            self.bound(session_id)
            need(self.matching('history'), 'HISTORY_RECONCILIATION_REQUIRED')
            return self.append('scan', dict(scan_id=str(uuid.uuid4()), session_id=session_id))

    def pages(self):
        scans = self.matching('scan')
        return [p for p in self.matching('page') if scans and p['scan_id'] == scans[-1]['scan_id']]

    def page(self, *, session_id, cards, screenshot, ax, boundary_evidence=None,
             top_confirmed=False, bottom_stationary=False, scroll_evidence=None, unresolved=0):
        with self.locked():
            self.bound(session_id)
            scans = self.matching('scan')
            need(scans and scans[-1]['session_id'] == session_id, 'NEW_SCAN_REQUIRED_AFTER_HANDOFF')
            need(type(unresolved) is int and unresolved >= 0, 'INVALID_UNRESOLVED_COUNT')
            need(isinstance(cards, list) and cards, 'NO_GROUNDED_CARDS')
            keys = [album_key(card) for card in cards]
            need(len(keys) == len(set(keys)), 'AMBIGUOUS_SAME_PAGE_CARDS')
            pages = self.pages()
            evidence = dict(screenshot=reference(screenshot), ax=reference(ax))
            if not pages:
                need(top_confirmed is True and boundary_evidence, 'TOP_BOUNDARY_REQUIRED')
                evidence['boundary'] = boundary_reference(boundary_evidence, 'top', session_id,
                                                           keys[0], evidence['screenshot'])
                need(not bottom_stationary, 'SEPARATE_BOTTOM_OBSERVATION_REQUIRED')
            else:
                need(not pages[-1]['bottom_stationary'], 'SCAN_ALREADY_AT_BOTTOM')
                previous = pages[-1]['keys']
                need(scroll_evidence, 'SCROLL_OBSERVATION_REQUIRED')
                evidence['scroll'] = reference(scroll_evidence)
                need(evidence['screenshot'] != pages[-1]['evidence']['screenshot'], 'FRESH_OBSERVATION_REQUIRED')
                # The overlapping suffix/prefix must preserve order. A mere set
                # intersection cannot prove that no rows were skipped.
                overlap = max((n for n in range(1, min(len(previous), len(keys)) + 1)
                               if previous[-n:] == keys[:n]), default=0)
                need(overlap > 0, 'LIST_OVERLAP_GAP')
                seen = {key for p in pages for key in p['keys']}
                need(not (set(keys[overlap:]) & seen), 'LIST_REORDER_OR_LOOP')
                if bottom_stationary:
                    need(previous == keys and unresolved == 0 and boundary_evidence,
                         'BOTTOM_NOT_STATIONARY')
                    evidence['boundary'] = boundary_reference(boundary_evidence, 'bottom', session_id,
                        keys[-1], evidence['screenshot'], pages[-1]['evidence']['screenshot'])
                else:
                    need(previous != keys, 'NO_MOVEMENT_IS_NOT_A_NEW_PAGE')
            return self.append('page', dict(scan_id=scans[-1]['scan_id'], cards=cards, keys=keys,
                unresolved=unresolved, bottom_stationary=bottom_stationary, evidence=evidence))

    def status_map(self):
        result = {}
        for event in self.events:
            data = event['data']
            if event['kind'] == 'history':
                check_ref(data['scope_evidence'])
                for entry in data['entries']:
                    check_ref(entry['source'])
                    status = entry['status']
                    if status in ('COMPLETED', 'EXCLUDED') and self._normalized_history(
                            entry['source']['path'], entry['identity']) != status:
                        status = 'PROTECTED_HISTORY'
                    result[entry['album_key']] = status
            elif event['kind'] == 'page':
                for key in data['keys']:
                    result.setdefault(key, 'INCOMPLETE')
            elif event['kind'] == 'intent':
                result[data['album_key']] = 'UNKNOWN'
            elif event['kind'] == 'outcome':
                result[data['album_key']] = 'UNKNOWN' if data['outcome'] == 'UNKNOWN' else 'INCOMPLETE'
            elif event['kind'] == 'completion':
                for row in data['proof']['manifest']:
                    path = Path(data['destination']) / row['name']
                    need(path.exists() and not path.is_symlink(), 'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD')
                    info = path.stat()
                    need(stat.S_ISREG(info.st_mode) and info.st_size == row['size'] and
                         info.st_mtime_ns == row['mtime_ns'] and info.st_ctime_ns == row['ctime_ns'],
                         'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD')
                need(sorted(p.name for p in Path(data['destination']).iterdir()) ==
                     [row['name'] for row in data['proof']['manifest']], 'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD')
                result[data['album_key']] = 'COMPLETED'
        return result

    def detail(self, *, session_id, identity, evidence):
        with self.locked():
            self.bound(session_id)
            key = album_key(identity)
            need(key in {k for p in self.pages() for k in p['keys']}, 'TARGET_NOT_IN_CURRENT_SCAN')
            return self.append('detail', dict(session_id=session_id, album_key=key,
                                              evidence=reference(evidence)))

    def intent(self, *, session_id, identity, recovery_authorization=None):
        """Local reservation only. Caller must also pass real transaction gates.

        RESERVED immediately means UNKNOWN until a separately observed outcome.
        A crash between this durable write and GUI input cannot allow replay.
        """
        with self.locked():
            self.bound(session_id)
            key = album_key(identity)
            states = self.status_map()
            need(states.get(key) != 'PROTECTED_HISTORY', 'PROTECTED_NO_REDOWNLOAD')
            need(states.get(key) not in ('COMPLETED', 'EXCLUDED'), 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD')
            need(key in {k for p in self.pages() for k in p['keys']}, 'TARGET_NOT_IN_CURRENT_SCAN')
            attempts = self.matching('intent')
            if attempts and attempts[-1]['album_key'] != key:
                need(states[attempts[-1]['album_key']] == 'COMPLETED', 'PENDING_OTHER_ALBUM_NO_DISPATCH')
            need(self.matching('history'), 'HISTORY_RECONCILIATION_REQUIRED')
            details = self.matching('detail')
            need(details and details[-1]['session_id'] == session_id and details[-1]['album_key'] == key,
                 'FRESH_DETAIL_REQUIRED')
            check_ref(details[-1]['evidence'])
            prior = [i for i in self.matching('intent') if i['album_key'] == key]
            recovery = None
            if prior:
                outcomes = [o for o in self.matching('outcome') if o['attempt_id'] == prior[-1]['attempt_id']]
                need(outcomes and outcomes[-1]['outcome'] in ('STOPPED', 'NOT_SENT'), 'UNKNOWN_OR_RUNNING_NO_REPLAY')
                check_ref(outcomes[-1]['evidence'])
                need(recovery_authorization, 'ALBUM_RECOVERY_AUTHORIZATION_REQUIRED')
                recovery = reference(recovery_authorization)
                decision = strict_json(read_file(recovery_authorization), 'INVALID_RECOVERY_AUTHORIZATION')
                need(decision.get('decision') == 'AUTHORIZE_ALBUM_RECOVERY' and
                     decision.get('local_group_id') == self.group['local_group_id'] and
                     decision.get('album_key') == key and
                     decision.get('previous_attempt_id') == prior[-1]['attempt_id'] and
                     decision.get('preserve_existing') is True, 'RECOVERY_AUTHORIZATION_SCOPE_MISMATCH')
                check_ref(decision['owner_source'])
            else:
                need(recovery_authorization is None, 'NO_PRIOR_ATTEMPT_TO_RECOVER')
            album_root = self.root / 'albums'
            if not album_root.exists():
                album_root.mkdir(mode=0o700)
            directory(album_root)
            attempt_id = uuid.uuid4().hex
            destination = album_root / attempt_id
            destination.mkdir(mode=0o700)
            sync_dir(album_root)
            need(not list(destination.iterdir()), 'EMPTY_DESTINATION_REQUIRED')
            return self.append('intent', dict(album_key=key, identity=identity, attempt_id=attempt_id,
                session_id=session_id, destination=str(destination),
                recovery_of=prior[-1]['attempt_id'] if prior else None, recovery_authorization=recovery,
                save_all_retry_allowed=False, dispatch_authorized=False))

    def outcome(self, *, session_id, attempt_id, outcome, evidence):
        with self.locked():
            self.bound(session_id)
            need(outcome in ('UNKNOWN', 'NOT_SENT', 'STOPPED', 'DOWNLOAD_FINISHED'), 'INVALID_OUTCOME')
            attempts = self.matching('intent')
            need(attempts and attempts[-1]['attempt_id'] == attempt_id, 'ONLY_LATEST_ATTEMPT_CAN_CHANGE')
            target = attempts[-1]
            need(self.status_map()[target['album_key']] != 'COMPLETED', 'COMPLETION_IMMUTABLE')
            outcomes = [o for o in self.matching('outcome') if o['attempt_id'] == attempt_id]
            need(not outcomes, 'OUTCOME_ALREADY_KNOWN')
            return self.append('outcome', dict(attempt_id=attempt_id, album_key=target['album_key'],
                                               outcome=outcome, evidence=reference(evidence)))

    def complete(self, *, session_id, attempt_id, decoder, decoder_sha256):
        with self.locked():
            self.bound(session_id)
            attempts = self.matching('intent')
            need(attempts and attempts[-1]['attempt_id'] == attempt_id, 'ONLY_LATEST_ATTEMPT_CAN_COMPLETE')
            target = attempts[-1]
            need(self.status_map()[target['album_key']] != 'COMPLETED', 'COMPLETION_IMMUTABLE')
            outcomes = [o for o in self.matching('outcome') if o['attempt_id'] == attempt_id]
            need(outcomes and outcomes[-1]['outcome'] == 'DOWNLOAD_FINISHED', 'KNOWN_DOWNLOAD_FINISH_REQUIRED')
            check_ref(outcomes[-1]['evidence'])
            proof = verify_directory(target['destination'], target['identity']['expected_images'],
                                     decoder, decoder_sha256)
            return self.append('completion', dict(attempt_id=attempt_id, album_key=target['album_key'],
                destination=target['destination'], proof=proof, execution_lane='MANUAL_DIAGNOSTIC',
                formal_auto_verified=False))

    def summary(self):
        with self.locked():
            pages = self.pages()
            current = {key for page in pages for key in page['keys']}
            ever_seen = {key for page in self.matching('page') for key in page['keys']}
            states = self.status_map()
            counts = {status: sum(states.get(key) == status for key in current)
                      for status in ('COMPLETED', 'EXCLUDED', 'INCOMPLETE', 'UNKNOWN', 'PROTECTED_HISTORY')}
            counts['UNKNOWN'] += sum(p['unresolved'] for p in pages) + len(ever_seen - current)
            covered = bool(pages and pages[-1]['bottom_stationary'])
            return dict(local_group_id=self.group['local_group_id'], total=len(current), **counts,
                list_coverage='OBSERVED' if covered else 'INCOMPLETE',
                ALL_ELIGIBLE_ALBUMS_BACKED_UP='PASS' if covered and current and
                    counts['INCOMPLETE'] == counts['UNKNOWN'] == counts['PROTECTED_HISTORY'] == 0 else 'INCOMPLETE',
                dispatch_authorized=False, formal_auto_verified=False,
                recovery_strategy='ALBUM_LEVEL', photo_level_resume='FUTURE_RESEARCH',
                evidence_role='AGENT_ATTESTED_OBSERVATIONS', sensor_verified=False,
                real_line_e2e='NOT_TESTED', pass_scope='AGENT_ATTESTED_ACCOUNTING_ONLY')

    def authorization_request(self, *, session_id, identity, owner_request):
        """Prepare missing cross-group issuance inputs without minting credentials."""
        with self.locked():
            self.bound(session_id)
            key = album_key(identity)
            need(key in {k for p in self.pages() for k in p['keys']}, 'TARGET_NOT_IN_CURRENT_SCAN')
            need(self.status_map().get(key) == 'INCOMPLETE', 'TARGET_NOT_ELIGIBLE_FOR_REQUEST')
            need(not [i for i in self.matching('intent') if i['album_key'] == key], 'RECOVERY_REQUIRES_SEPARATE_AUTHORIZATION')
            return dict(request_version=1, local_group_id=self.group['local_group_id'],
                destination=str(self.root), destination_device=self.group['destination_device'],
                destination_inode=self.group['destination_inode'], identity=identity, album_key=key,
                owner_request=reference(owner_request),
                source_files=[reference(Path(__file__).with_name(name).resolve()) for name in
                              ('daily.py', 'cli.py', 'store.py', 'service.py', 'image_decode.swift')],
                record_head_sha256=self.previous, session_id=session_id,
                external_plan_review=None, external_implementation_review=None, runtime_grant=None,
                status='BLOCKED_NEW_GROUP_ISSUER_REQUIRES_REVIEW', dispatch_authorized=False,
                required=['review exact foreground source and grant/ledger design',
                          'implement reviewed destination/group-bound issuer and transaction entry',
                          'genuine external implementation approval and bound runtime',
                          'Owner current foreground handoff plus separate L1/L2 authority'],
                legacy_profile_reusable=False, native_authorize_is_issuer=False)


def image_inventory(destination):
    root = directory(destination)
    result = []
    for path in sorted(root.iterdir()):
        need(not path.name.startswith('.') and path.suffix.lower() in ('.jpg', '.jpeg', '.png'),
             'UNEXPECTED_DOWNLOAD_ENTRY')
        raw = read_file(path)
        need(bool(raw), 'EMPTY_DOWNLOAD')
        info = path.stat()
        result.append(dict(name=path.name, size=len(raw), sha256=digest(raw),
                           mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns))
    return result


def verify_directory(destination, expected, decoder, decoder_sha256):
    need(type(expected) is int and expected > 0, 'PHOTO_COUNT_REQUIRED')
    binary = reference(decoder)
    need(binary['sha256'] == decoder_sha256, 'DECODER_DRIFT')
    samples = []
    for sample in range(3):
        if sample:
            time.sleep(1)
        rows = image_inventory(destination)
        need(len(rows) == expected, 'DOWNLOAD_COUNT_MISMATCH')
        need(not samples or rows == samples[-1], 'DOWNLOAD_NOT_STABLE')
        samples.append(rows)
    run = subprocess.run([str(decoder), str(destination), str(expected)], capture_output=True, timeout=120)
    need(run.returncode == 0, 'IMAGEIO_DECODE_FAILED')
    result = strict_json(run.stdout, 'INVALID_IMAGEIO_RESULT')
    need(result.get('verdict') == 'PASS' and result.get('readOnly') is True and
         result.get('destination') == str(destination) and result.get('expected') == expected and
         result.get('actualEntries') == expected, 'IMAGEIO_BINDING_MISMATCH')
    decoded = result.get('entries', [])
    need(len(decoded) == expected and len({r['name'] for r in decoded}) == expected and
         {r['name']: r.get('sha256') for r in decoded if r.get('decoded') is True} ==
         {r['name']: r['sha256'] for r in rows}, 'IMAGEIO_CONTENT_MISMATCH')
    need(reference(decoder) == binary and image_inventory(destination) == rows, 'CONTENT_CHANGED_AFTER_DECODE')
    return dict(manifest=rows, manifest_sha256=digest(encoded(rows)), imageio=result,
                imageio_stdout_sha256=digest(run.stdout), decoder=binary, stable_samples=3)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['init', 'bind', 'history', 'scan', 'page', 'detail',
                                             'intent', 'outcome', 'verify', 'summary', 'authorization-request',
                                             'p3-prepare', 'p3-reserve', 'p3-finalize'])
    parser.add_argument('--root', required=True)
    parser.add_argument('--input', help='Private JSON input, using the method argument names in daily.py')
    ns = parser.parse_args(argv)
    if ns.operation in ('p3-prepare', 'p3-reserve', 'p3-finalize'):
        if not ns.input:
            print(json.dumps(dict(status='REFUSED', reason='P3_INPUT_REQUIRED',
                                  dispatch_authorized=False)))
            return 4
        from .p3 import main as p3_main
        return p3_main([ns.operation.removeprefix('p3-'), '--root', ns.root,
                        '--input', ns.input])
    try:
        methods = {'init': 'initialize', 'scan': 'start_scan', 'verify': 'complete',
                   'authorization-request': 'authorization_request'}
        data = strict_json(read_file(ns.input), 'INVALID_INPUT') if ns.input else {}
        result = getattr(DailyRecords(ns.root), methods.get(ns.operation, ns.operation))(**data)
        print(json.dumps(dict(result=result, dispatch_authorized=False), ensure_ascii=False))
        return 0
    except (DailyError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status='REFUSED', reason=str(exc), dispatch_authorized=False)))
        return 4


if __name__ == '__main__':
    raise SystemExit(main())
