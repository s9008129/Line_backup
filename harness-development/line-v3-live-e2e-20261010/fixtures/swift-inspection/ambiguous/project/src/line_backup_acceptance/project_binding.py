"""Read-only project inspection. A report is neither a lease nor execution permission."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

from .common import AcceptanceError, parse_binding_reference, validate_state_strict

CONFIG_PATH = 'config/line_backup_config.json'
STATE_PATH = 'state/backup_state.json'
SOURCE_DIR = 'src/line_backup_acceptance'
SOURCE_NAMES = ['__init__.py', '__main__.py', 'authority.py', 'cli.py', 'common.py',
                'project_binding.py', 'status.py', 'transaction.py', 'verifier.py']
CONFIG_KEYS = {'schema_version', 'group_key', 'group_name', 'backup_root', 'app_identifier',
               'max_albums_per_run', 'recovery_limit', 'poll_interval_seconds', 'stable_samples',
               'max_wait_seconds'}
FLAGS = dict(dispatch_authorized=False, writer_acquired=False,
             native_observation_performed=False, state_modified=False)


def fail(code, message):
    raise AcceptanceError(code, message, 2)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data, code):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail(code, 'Duplicate JSON object key')
            result[key] = value
        return result
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=lambda _: fail(code, 'Nonfinite JSON number'))
    except (ValueError, UnicodeError, RecursionError):
        fail(code, 'Invalid UTF-8 JSON')


def integer(value, minimum=0):
    return type(value) is int and minimum <= value <= 2**53 - 1


def dates(start, end, code='INVALID_INPUT'):
    try:
        if any(not isinstance(v, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', v)
               for v in (start, end)):
            raise ValueError()
        if datetime.date.fromisoformat(start) > datetime.date.fromisoformat(end):
            raise ValueError()
    except ValueError:
        fail(code, 'Invalid Gregorian date range')


def component(value):
    return isinstance(value, str) and bool(value) and value not in {'.', '..'} and not any(
        c in value for c in ('/', '\\', '\0')) and not any(ord(c) < 32 for c in value)


def canonical_path(value):
    return isinstance(value, str) and value.startswith('/') and value != '/' and all(
        component(c) for c in value[1:].split('/'))


class ProjectReader:
    """Walk with directory descriptors and O_NOFOLLOW; never create files or locks."""
    def __init__(self, root):
        if not canonical_path(root):
            fail('INVALID_PROJECT_AUTHORITY', 'An explicit canonical absolute project root is required')
        self.root = root
        self.observations = {}
        self.fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in root[1:].split('/'):
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fd)
                os.close(self.fd)
                self.fd = next_fd
            self.identity = self.ident(os.fstat(self.fd))
        except OSError:
            os.close(self.fd)
            fail('INVALID_PROJECT_AUTHORITY', 'Project root is missing, non-directory or symlinked')

    @staticmethod
    def ident(s):
        return (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

    def close(self):
        os.close(self.fd)

    def open(self, relative, directory=False):
        if not isinstance(relative, str) or not all(component(c) for c in relative.split('/')):
            fail('INVALID_PATH', 'Unsafe relative path')
        parent = os.dup(self.fd)
        try:
            parts = relative.split('/')
            for part in parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                os.close(parent)
                parent = child
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if directory:
                flags |= os.O_DIRECTORY
            return os.open(parts[-1], flags, dir_fd=parent)
        finally:
            os.close(parent)

    def read(self, relative, code='INVALID_PROJECT_AUTHORITY'):
        try:
            fd = self.open(relative)
            try:
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode) or before.st_size > 16 * 1024 * 1024:
                    fail(code, 'Authority material is not a bounded regular file')
                chunks = []
                while True:
                    chunk = os.read(fd, 65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if sum(map(len, chunks)) > 16 * 1024 * 1024:
                        fail('PROJECT_SNAPSHOT_CHANGED', 'Authority material grew while reading')
                after = os.fstat(fd)
                data = b''.join(chunks)
                if self.ident(before) != self.ident(after) or len(data) != before.st_size:
                    fail('PROJECT_SNAPSHOT_CHANGED', 'Authority changed while reading')
                result = (data, self.ident(after))
                if relative in self.observations and self.observations[relative] != result:
                    fail("PROJECT_SNAPSHOT_CHANGED", "Authority material changed between reads")
                self.observations[relative] = result
                return result
            finally:
                os.close(fd)
        except OSError:
            fail(code, 'Required regular no-follow authority material is unavailable')

    def directory_names(self, relative):
        fd = self.open(relative, directory=True)
        try:
            return sorted(os.listdir(fd))
        finally:
            os.close(fd)

    def fresh_root(self):
        other = ProjectReader(self.root)
        try:
            if other.identity[:3] != self.identity[:3]:
                fail('PROJECT_SNAPSHOT_CHANGED', 'Selected project directory identity changed')
        finally:
            other.close()


def validate_config(cfg, root):
    if not isinstance(cfg, dict) or set(cfg) != CONFIG_KEYS:
        fail('INVALID_CONFIG', 'Config does not match the accepted v2 contract')
    if type(cfg['schema_version']) is not int or cfg['schema_version'] != 2:
        fail('INVALID_CONFIG', 'Invalid config version')
    if cfg['app_identifier'] != 'jp.naver.line.mac' or not component(cfg['group_name']):
        fail('INVALID_CONFIG', 'Invalid bundle or unsafe group name')
    if cfg['group_key'] != 'line:jp.naver.line.mac:' + cfg['group_name']:
        fail('INVALID_CONFIG', 'Config group identity is inconsistent')
    if cfg['backup_root'] != root + '/backups':
        fail('INVALID_CONFIG', 'Backup root is not a canonical child of the selected project')
    for key in CONFIG_KEYS - {'schema_version', 'group_key', 'group_name', 'backup_root', 'app_identifier'}:
        if not integer(cfg[key], 1):
            fail('INVALID_CONFIG', 'Invalid config numeric setting')
    if cfg['recovery_limit'] != 1:
        fail('INVALID_CONFIG', 'Unsupported album or recovery limit')


def _same_json(left, right):
    """JSON equality that does not conflate booleans, integers and floats."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_same_json(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_same_json(a, b) for a, b in zip(left, right))
    return left == right


def _read_evidence_entry(reader, entry):
    if not isinstance(entry, dict) or set(entry) != {'path', 'bytes', 'sha256'}:
        fail('INVALID_PROJECT_HISTORY', 'Evidence artifact entry shape is invalid')
    path = entry['path']
    if (not canonical_path(path) or not path.startswith(reader.root + '/')
            or not integer(entry['bytes']) or not isinstance(entry['sha256'], str)
            or not re.fullmatch(r'[0-9a-f]{64}', entry['sha256'])):
        fail('INVALID_PROJECT_HISTORY', 'Evidence artifact entry is outside the selected project or malformed')
    raw, _ = reader.read(path[len(reader.root) + 1:], 'INVALID_PROJECT_HISTORY')
    if len(raw) != entry['bytes'] or sha(raw) != entry['sha256']:
        fail('INVALID_PROJECT_HISTORY', 'Evidence artifact entry digest/size changed')
    return raw


def _validate_evidence_content(data, kind, entry, run, cfg, reader):
    """Join source identity and verification to their history; hashing alone is insufficient."""
    def bad(message):
        fail('INVALID_PROJECT_HISTORY', message)
    record = strict_json(data, 'INVALID_PROJECT_HISTORY')
    if not isinstance(record, dict) or record.get('app_identifier') != cfg['app_identifier']:
        bad('Evidence content has an invalid application identity')
    fp = record.get('fingerprint')
    if not isinstance(fp, dict) or not _same_json(fp, entry['fingerprint']):
        bad('Evidence content fingerprint disagrees with registry')
    if kind == 'user_fact':
        if entry['source_kind'] != 'user_attestation' or run is not None:
            bad('User fact cannot claim a verified machine run')
        if (record.get('record_version') != '1.0' or record.get('kind') != 'source_identity_user_fact'
                or record.get('status') != 'CONFIRMED' or record.get('source_correspondence_result') != 'CONFIRMED'
                or record.get('merge_prohibited') is not True
                or record.get('raw_requested_group') != cfg['group_name']):
            bad('User fact lacks exact confirmed source identity')
        if 'group_key' in record and record['group_key'] != entry['group_key']:
            bad('User fact group identity is contradictory')
        if record.get('run_id') is not None:
            bad('User attestation must not claim a machine run')
        if 'destination' in record and record['destination'] not in entry['destinations']:
            bad('User fact destination disagrees with registry')
        question, answer = record.get('question'), record.get('answer')
        if (not isinstance(question, dict) or not isinstance(question.get('text'), str) or not question['text'].strip()
                or not isinstance(answer, dict) or not isinstance(answer.get('raw'), str) or not answer['raw'].strip()):
            bad('User fact question/answer is missing')
        part = answer.get('part_2')
        label = fp['start_date'].replace('-', '/') + '～' + fp['end_date'][5:].replace('-', '/')
        if (not isinstance(part, dict) or part.get('confirms_same_source') is not True
                or part.get('confirmed_group_string') != cfg['group_name'] or part.get('confirmed_album') != label
                or not integer(part.get('confirmed_expected_images'), 1)
                or part['confirmed_expected_images'] != fp['expected_images']):
            bad('User fact answer does not confirm this exact group/album/count')
        proof = record.get('evidence')
        if not isinstance(proof, list) or not proof:
            bad('User fact evidence is missing')
        for item in proof:
            _read_evidence_entry(reader, item)
        return
    if entry['source_kind'] != 'filesystem_verification' or run is None:
        bad('Filesystem source evidence must link to an exact verified run')
    if (record.get('group_key') != entry['group_key'] or record.get('run_id') != run['run_id']
            or record.get('destination') != run['destination']):
        bad('Evidence content group/run/destination disagrees with verified history')
    if not any(event['phase'] == 'VERIFIED' and event['evidence'] == entry['evidence'] for event in run['events']):
        bad('Registry evidence reference is not bound by the verified run event')
    if kind == 'fixture':
        # A fixture is still synthetic: exact content joins never grant native readiness.
        installed = Path(__file__).resolve().parents[2]
        if not (Path(reader.root).is_relative_to(installed / 'harness-development') and '/fixtures/' in reader.root):
            bad('Fixture history cannot authorize the live project')
        if not _same_json(record.get('verification'), run['verification']):
            bad('Fixture evidence verification disagrees with verified history')
        return
    if (kind != 'join' or record.get('record_version') != '1.0'
            or record.get('kind') != 'actual_cua_source_identity_join'
            or record.get('join_authority') != 'authoritative_exact_join'):
        bad('Unsupported or non-authoritative join evidence')
    if record.get('test_mode') is True:
        installed = Path(__file__).resolve().parents[2]
        if not (Path(reader.root).is_relative_to(installed / 'harness-development') and '/fixtures/' in reader.root):
            bad('Synthetic joins cannot authorize the live project')
    proof = record.get('evidence')
    if not isinstance(proof, list) or not proof:
        bad('Join verification evidence is missing')
    paths = []
    for item in proof:
        if (not isinstance(item, dict) or set(item) != {'path', 'bytes', 'sha256'}
                or not canonical_path(item['path']) or not item['path'].startswith(reader.root + '/')
                or not integer(item['bytes']) or not isinstance(item['sha256'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', item['sha256'])):
            bad('Join evidence entries are malformed or outside the selected project')
        paths.append(item['path'])
    if len(set(paths)) != len(paths):
        bad('Join evidence entries are duplicated')
    verification = [item for item in proof if item['path'].endswith('/filesystem-verification.json')]
    if len(verification) != 1:
        bad('Join lacks one exact filesystem verification artifact')
    raw = _read_evidence_entry(reader, verification[0])
    if not _same_json(strict_json(raw, 'INVALID_PROJECT_HISTORY'), run['verification']):
        bad('Join verification content disagrees with verified history')


def validate_history(state, cfg, reader, *, allow_v3=False):
    # Frozen historical Operator.load calls this before lock creation/mkdir.
    if isinstance(state, dict) and state.get('schema_version') == 3 and not allow_v3:
        fail('LEGACY_WRITER_DISABLED', 'V3 history is read-only to legacy callers')
    try:
        validate_state_strict(state)
    except (AcceptanceError, KeyError, TypeError):
        fail('INVALID_STATE', 'State does not match the accepted RC2/legacy contract')
    if type(state['schema_version']) is not int or not integer(state['revision']):
        fail('INVALID_STATE', 'Invalid state version or revision')
    runs = state['runs']
    ids = []
    group = cfg['group_key']
    def bad(message):
        fail('INVALID_PROJECT_HISTORY', message)
    def fp(value):
        if value is not None:
            dates(value['start_date'], value['end_date'], 'INVALID_PROJECT_HISTORY')
            if not integer(value['expected_images'], 1):
                bad('Invalid history fingerprint')
    def destination(value):
        if value is not None and (not canonical_path(value) or not value.startswith(cfg['backup_root'] + '/')):
            bad('History destination is outside selected project backup root')
    for run in runs:
        rid = run['run_id']
        if not isinstance(rid, str) or not rid or rid in ids:
            bad('Missing or duplicate run identity')
        ids.append(rid)
        if run['group_key'] != group:
            bad('Foreign group in project history')
        for k in ('destination_initially_empty', 'manual_reconciliation_required'):
            if type(run[k]) is not bool:
                bad('Invalid history boolean')
        fp(run['fingerprint']); destination(run['destination'])
        intent = run['intent']
        if intent is not None:
            if (intent['group_key'] != group or intent['fingerprint'] != run['fingerprint']
                    or intent['destination'] != run['destination']):
                bad('Intent and run identity disagree')
        if run['workflow_outcome'] == 'VERIFIED':
            v = run['verification']
            if run['fingerprint'] is None or run['destination'] is None or v is None or v['outcome'] != 'PASS':
                bad('Verified run lacks exact passing verification')
            if not isinstance(v['evidence'], str) or not v['evidence'] or not integer(v['image_files'], 1) or v['image_files'] != run['fingerprint']['expected_images']:
                bad('Verified count/evidence is inconsistent')
    current = state['current_run_id']
    if current is not None and current not in ids:
        bad('Dangling current run pointer')
    if state['active_writer_id'] is not None and not state['active_writer_id']:
        bad('Empty writer identity')
    lock = state['context_lock']
    if lock is not None and lock['group_key'] != group:
        bad('Foreign context lock')
    by_id = {r['run_id']: r for r in runs}
    for e in state['verified_albums']:
        fp(e['fingerprint'])
        if e['group_key'] != group or not e['destinations'] or len(set(e['destinations'])) != len(e['destinations']):
            bad('Invalid registry group/destinations')
        for d in e['destinations']:
            destination(d)
        rid = e['verified_run_id']
        r = None
        if e['source_kind'] == 'filesystem_verification':
            r = by_id.get(rid)
            if r is None or r['workflow_outcome'] != 'VERIFIED' or r['group_key'] != e['group_key'] or r['fingerprint'] != e['fingerprint'] or r['destination'] not in e['destinations']:
                bad('Registry and verified run disagree')
        elif rid is not None:
            bad('User attestation must not claim a verified machine run')
        ref = parse_binding_reference(e['evidence'])
        if ref is None or ref[0] not in {'join', 'user_fact', 'fixture'}:
            bad('Registry evidence reference is malformed')
        data, _ = reader.read(ref[1], 'INVALID_PROJECT_HISTORY')
        if sha(data) != ref[2]:
            bad('Registry evidence reference digest changed')
        _validate_evidence_content(data, ref[0], e, r, cfg, reader)
    return by_id


def history_decision(state, target, by_id):
    """Pure decision precedence; terminal current pointers are not active ownership."""
    fp = target['fingerprint']
    runs = state['runs']
    same = [r for r in runs if r['fingerprint'] == fp]
    verified = sorted(r['run_id'] for r in same if r['workflow_outcome'] == 'VERIFIED')
    registries = sum(e['fingerprint'] == fp for e in state['verified_albums'])
    def unresolved(r):
        return r['workflow_outcome'] != 'VERIFIED' and (
            r['workflow_outcome'] not in {'VERIFIED', 'SAFE_ABORT'} or r['intent'] is not None
            or r['intent_state'] not in {'NONE', 'INTENT_NONE'}
            or r['manual_reconciliation_required'] or r.get('dispatch_state', 'NOT_ATTEMPTED') not in {'NOT_ATTEMPTED', 'ELLIPSIS_FAILED'}
            or bool(r.get('reconciliations')))
    unresolved_ids = sorted(r['run_id'] for r in same if unresolved(r))
    releases = sorted(r['run_id'] for r in same if any(
        rec.get('blocking_intent_released') is True for rec in r.get('reconciliations', [])))
    current = by_id.get(state['current_run_id'])
    terminal = None if current is None else current['workflow_outcome'] in {'VERIFIED', 'SAFE_ABORT'}
    facts = dict(current_run_id=state['current_run_id'], current_run_terminal=terminal,
                 active_writer_id=state['active_writer_id'], context_lock_present=state['context_lock'] is not None,
                 verified_match_run_ids=verified, verified_match_registry_count=registries,
                 unresolved_run_ids=unresolved_ids, purported_release_run_ids=releases,
                 destination_status='NOT_INSPECTED_BLOCKED')
    if state.get('active_batch') is not None or state['active_writer_id'] is not None or state['context_lock'] is not None or any(
            r['fingerprint'] != fp and unresolved(r) for r in runs):
        decision = 'PROJECT_BUSY'
    elif verified or registries:
        decision = 'SKIP_VERIFIED'; facts['destination_status'] = 'NOT_INSPECTED_VERIFIED'
    elif any(e is not None and e['start_date'] == fp['start_date'] and e['end_date'] == fp['end_date'] and e['expected_images'] != fp['expected_images']
             for e in [r['fingerprint'] for r in runs] + [e['fingerprint'] for e in state['verified_albums']]):
        decision = 'AMBIGUOUS_FINGERPRINT'
    elif unresolved_ids:
        decision = 'BLOCKED_UNRESOLVED'
    else:
        decision = 'PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION'
    return decision, facts


def _destination_snapshot(reader, relative):
    """Capture each no-follow directory identity and the absent/unsafe boundary."""
    fd = os.dup(reader.fd)
    witness = [('project', reader.ident(os.fstat(fd)))]
    try:
        walked = []
        for part in relative.split('/'):
            walked.append(part)
            path = '/'.join(walked)
            try:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                witness.append((path, 'ABSENT'))
                return 'ABSENT', witness
            except OSError as exc:
                # Bind the unsafe boundary without following or reading its content.
                try:
                    identity = reader.ident(os.stat(part, dir_fd=fd, follow_symlinks=False))
                except OSError:
                    identity = None
                witness.append((path, 'UNSAFE', exc.errno, identity))
                return 'UNSAFE', witness
            os.close(fd); fd = child
            witness.append((path, reader.ident(os.fstat(fd))))
        before = reader.ident(os.fstat(fd))
        names = sorted(os.listdir(fd))
        if before != reader.ident(os.fstat(fd)):
            fail('PROJECT_SNAPSHOT_CHANGED', 'Destination changed while inspecting')
        witness.append(('entries', names))
        return ('NONEMPTY' if names else 'EMPTY'), witness
    finally:
        os.close(fd)


def destination_status(reader, relative):
    """Directory observations are rechecked before return; never read photo bytes."""
    status, witness = _destination_snapshot(reader, relative)
    reader.destination_observation = (relative, status, witness)
    return status


def inspect(project_root, start_date, end_date, expected_images):
    dates(start_date, end_date)
    if not integer(expected_images, 1):
        fail('INVALID_INPUT', 'Expected images must be a positive integer')
    reader = ProjectReader(project_root)
    try:
        raw_config, config_id = reader.read(CONFIG_PATH)
        raw_state, state_id = reader.read(STATE_PATH)
        cfg = strict_json(raw_config, 'INVALID_CONFIG')
        state = strict_json(raw_state, 'INVALID_STATE')
        validate_config(cfg, project_root)
        by_id = validate_history(state, cfg, reader, allow_v3=True)
        fp = dict(start_date=start_date, end_date=end_date, expected_images=expected_images)
        relative = f"backups/{cfg['group_name']}/{start_date}_{end_date}_{expected_images}張"
        target = dict(group_key=cfg['group_key'], fingerprint=fp, proposed_destination=project_root + '/' + relative)
        decision, facts = history_decision(state, target, by_id)
        if decision == 'PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION':
            facts['destination_status'] = destination_status(reader, relative)
            if facts['destination_status'] in {'UNSAFE', 'NONEMPTY'}:
                decision = 'BLOCKED_DESTINATION'
        names = reader.directory_names(SOURCE_DIR)
        paths = [SOURCE_DIR + '/' + n for n in names if n.endswith('.py')]
        if paths != [SOURCE_DIR + '/' + n for n in SOURCE_NAMES]:
            fail('INVALID_PROJECT_AUTHORITY', 'Selected project lacks the producer source set')
        files = []; aggregate = hashlib.sha256(); materials = []
        for path in paths:
            data, identity = reader.read(path)
            files.append(dict(path=path, bytes=len(data), sha256=sha(data)))
            aggregate.update(path.encode() + b'\0' + data + b'\0')
            materials.append((path, data, identity))
        if state['schema_version'] == 3:
            from line_backup_batch.store import SOURCE_PATHS, sources
            sources(reader)  # Includes membership checks for the new producer.
            for path in SOURCE_PATHS:
                if path in paths:
                    continue
                data, identity = reader.read(path)
                files.append(dict(path=path, bytes=len(data), sha256=sha(data)))
                aggregate.update(path.encode() + b'\0' + data + b'\0')
                materials.append((path, data, identity))
        # Second round binds actual bytes and file identities, without claiming a writer lease.
        for path, (data, identity) in list(reader.observations.items()):
            if reader.read(path) != (data, identity):
                fail('PROJECT_SNAPSHOT_CHANGED', 'Authority/source snapshot changed between reads')
        if reader.directory_names(SOURCE_DIR) != names:
            fail('PROJECT_SNAPSHOT_CHANGED', 'Producer source membership changed')
        if hasattr(reader, 'destination_observation'):
            relative_path, observed_status, observed_witness = reader.destination_observation
            if _destination_snapshot(reader, relative_path) != (observed_status, observed_witness):
                fail('PROJECT_SNAPSHOT_CHANGED', 'Destination or parent identity/entries changed between reads')
        reader.fresh_root()
        report = dict(report_format_version=1, kind='REPORT', scope='PROJECT_PREFLIGHT_READ_ONLY',
                      request=dict(project_root=project_root, start_date=start_date, end_date=end_date, expected_images=expected_images),
                      authority=dict(project_root=project_root, config=dict(path=CONFIG_PATH, bytes=len(raw_config), sha256=sha(raw_config)),
                                     state=dict(path=STATE_PATH, bytes=len(raw_state), sha256=sha(raw_state)), state_revision=state['revision'],
                                     group_name=cfg['group_name'], group_key=cfg['group_key'], app_identifier=cfg['app_identifier'], backup_root=cfg['backup_root']),
                      target=target, decision=decision, reasons=[decision], state_facts=facts,
                      producer=dict(source_files=files, source_sha256=aggregate.hexdigest(), attestation='UNKNOWN'),
                      expected_total_bytes=None, expected_content_multiset_sha256=None,
                      content_expectation='MEASURE_AFTER_DOWNLOAD_NOT_YET_VERIFIED', **FLAGS)
        return report, 0 if decision in {'SKIP_VERIFIED', 'PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION'} else 4
    finally:
        reader.close()


def run(ns):
    try:
        result, code = inspect(ns.project_root, ns.start_date, ns.end_date, ns.expected_images)
    except AcceptanceError as exc:
        result = dict(report_format_version=1, kind='REFUSAL', scope='PROJECT_PREFLIGHT_READ_ONLY',
                      error=dict(code=exc.code, message=exc.message, exit_code=exc.exit_code), **FLAGS)
        code = exc.exit_code
    except Exception:
        result = dict(report_format_version=1, kind='REFUSAL', scope='PROJECT_PREFLIGHT_READ_ONLY',
                      error=dict(code='INTERNAL_ERROR', message='Project inspection failed', exit_code=1), **FLAGS)
        code = 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if code:
        print(result.get('error', {}).get('message', result.get('decision', 'Inspection refused')), file=sys.stderr)
    return code
