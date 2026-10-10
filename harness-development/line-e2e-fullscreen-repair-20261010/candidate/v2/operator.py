"""Task-local RC2 CAS writer. No UI, dispatcher, initialization or resume permit."""
from __future__ import annotations
import argparse
import contextlib
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
sys.dont_write_bytecode = True
ROOT = Path('/Users/hsiaojohnny/Documents/ChatGPT/Line_backup')
TASK = ROOT / 'harness-development/line-e2e-fullscreen-repair-20261010'
sys.path.insert(0, str(ROOT / 'src'))
from line_backup_acceptance.common import atomic_write_json, json_bytes, utc_now, validate_state_strict, _check_calibration, PHASES
from line_backup_acceptance.project_binding import ProjectReader, strict_json, validate_config, validate_history, history_decision, _same_json
from line_backup_acceptance.verifier import _inventory, _inventory_key, _classify_filesystem

sha = lambda data: hashlib.sha256(data).hexdigest()

class Refusal(Exception):
    pass

def require(predicate, message):
    if not predicate:
        raise Refusal(message)

def no_symlink(path, missing_leaf=False):
    path = Path(path)
    require(path.is_absolute() and path == Path(os.path.normpath(path)), 'noncanonical path')
    chain = list(reversed([path, *path.parents]))
    for i, component in enumerate(chain):
        try:
            info = component.lstat()
        except FileNotFoundError:
            require(missing_leaf and i == len(chain)-1, 'missing authority/path parent')
            return
        require(not stat.S_ISLNK(info.st_mode), 'symlink path')
        if i < len(chain)-1:
            require(stat.S_ISDIR(info.st_mode), 'non-directory path parent')

def read_json_path(path):
    no_symlink(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        s = os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_size < 16*1024*1024, 'unbounded/nonregular JSON')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read()
        require(ProjectReader.ident(s) == ProjectReader.ident(os.fstat(fd)), 'JSON changed while reading')
        return strict_json(raw, 'INVALID_INPUT'), raw
    finally:
        os.close(fd)

def read_task_artifact(record, label, *, as_json=True):
    require(isinstance(record, dict) and set(record) == {'path', 'sha256'}, f'{label} reference shape')
    relative = Path(record['path'])
    require(not relative.is_absolute() and '..' not in relative.parts, f'{label} path invalid')
    path = TASK / relative
    require(path.resolve(strict=True).is_relative_to(TASK), f'{label} path outside task')
    no_symlink(path)
    raw = path.read_bytes()
    require(sha(raw) == record['sha256'], f'{label} SHA-256 drift')
    if not as_json:
        return path, raw, None
    return path, raw, strict_json(raw, f'INVALID_{label.upper().replace(" ", "_")}')

def append_projection(path, receipt):
    no_symlink(path)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    try:
        a, b = os.fstat(fd), path.lstat()
        require(stat.S_ISREG(a.st_mode) and (a.st_dev,a.st_ino) == (b.st_dev,b.st_ino), 'unsafe run-log projection')
        with os.fdopen(fd, 'a', closefd=False) as stream:
            stream.write('\n'+json.dumps(receipt,ensure_ascii=False)+'\n')
    finally:
        os.close(fd)

@contextlib.contextmanager
def shared_guard(root):
    # Same inode/name as all existing Python writers, with no-follow opening.
    lock = root / 'state/.line-backup-state.lock'
    no_symlink(lock, missing_leaf=True)
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        require(stat.S_ISREG(os.fstat(fd).st_mode), 'nonregular lock')
        fcntl.flock(fd, fcntl.LOCK_EX)
        def verify_lock():
            a, b = os.fstat(fd), lock.lstat()
            require((a.st_dev,a.st_ino,a.st_mode) == (b.st_dev,b.st_ino,b.st_mode), 'lock identity changed')
        verify_lock()
        yield verify_lock
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

class Operator:
    def __init__(self, root, expected_config_sha, run_id, owner_id, fp, target_evidence=None,
                 target_evidence_sha256=None, test_mode=False):
        self.root = Path(root)
        require(self.root == ROOT if not test_mode else self.root.is_relative_to(TASK/'fixtures'), 'root not authorized')
        self.expected_config_sha = expected_config_sha
        self.run_id, self.owner_id = run_id, owner_id
        self.fp = copy.deepcopy(fp)
        self.target_evidence = target_evidence
        self.target_evidence_sha256 = target_evidence_sha256
        require(isinstance(self.fp, dict) and set(self.fp) == {'start_date','end_date','expected_images'}, 'fingerprint shape')
        self.path = self.root / 'state/backup_state.json'
        no_symlink(self.path)
        self.test_mode = test_mode
        self.evidence = TASK/'evidence'/'runs'/self.run_id
        require(self.evidence.is_relative_to(TASK/'evidence'/'runs'), 'run evidence path outside task')

    def load(self, reader):
        raw_cfg, _ = reader.read('config/line_backup_config.json')
        require(sha(raw_cfg) == self.expected_config_sha, 'config drift')
        cfg = strict_json(raw_cfg, 'INVALID_CONFIG')
        validate_config(cfg, str(self.root))
        raw, identity = reader.read('state/backup_state.json')
        state = strict_json(raw, 'INVALID_STATE')
        by_id = validate_history(state, cfg, reader)
        return cfg, state, by_id, raw, identity

    def snapshot(self):
        reader = ProjectReader(str(self.root))
        try:
            cfg,state,_,raw,identity = self.load(reader)
            return dict(revision=state['revision'],sha256=sha(raw),state_identity=list(identity),config_sha256=self.expected_config_sha,
                        run_id=self.run_id,owner_id=self.owner_id,operation='snapshot',project_root=str(self.root))
        finally:
            reader.close()

    def destination(self, cfg):
        dest = Path(cfg['backup_root']) / cfg['group_name'] / f"{self.fp['start_date']}_{self.fp['end_date']}_{self.fp['expected_images']}張"
        no_symlink(dest, missing_leaf=True)
        require(dest.parent.is_dir() and dest.is_relative_to(Path(cfg['backup_root'])), 'destination containment/parent')
        if os.path.lexists(dest):
            require(dest.is_dir() and not list(dest.iterdir()), 'destination nonempty/not directory')
        return dest

    def validate_calibration_package(self, payload, cfg, calibration):
        bundle = payload.get('calibration_evidence')
        expected_keys = {'target_evidence', 'menu_capture_manifest', 'menu_capture_image', 'menu_ocr',
                         'anchors', 'geometry', 'profile', 'safe_close_manifest', 'safe_close_image',
                         'closure_observation'}
        require(isinstance(bundle, dict) and set(bundle) == expected_keys, 'calibration evidence bundle shape')
        require(self.target_evidence is not None and self.target_evidence_sha256 is not None,
                'run authority has no target evidence binding')

        target_path, target_raw, target = read_task_artifact(bundle['target_evidence'], 'target evidence')
        require(bundle['target_evidence']['path'] == self.target_evidence and
                bundle['target_evidence']['sha256'] == self.target_evidence_sha256,
                'calibration target evidence differs from run authority')
        require(target.get('target_fingerprint') == self.fp and target.get('group') == cfg['group_name'],
                'calibration target identity mismatch')
        target_post = target.get('postcondition', {})
        expected_title = self.fp['start_date'].replace('-', '/') + '~' + self.fp['end_date'][5:].replace('-', '/')
        require(target_post.get('surface') == 'album_detail' and target_post.get('date_text') == expected_title and
                target_post.get('count_text') == f"{self.fp['expected_images']}張照片",
                'calibration target detail mismatch')

        manifest_path, manifest_raw, capture = read_task_artifact(bundle['menu_capture_manifest'], 'menu capture manifest')
        image_path, image_raw, _ = read_task_artifact(bundle['menu_capture_image'], 'menu capture image', as_json=False)
        ocr_path, ocr_raw, ocr = read_task_artifact(bundle['menu_ocr'], 'menu OCR')
        anchors_path, anchors_raw, anchors = read_task_artifact(bundle['anchors'], 'calibration anchors')
        geometry_path, geometry_raw, geometry = read_task_artifact(bundle['geometry'], 'calibration geometry')
        profile_path, profile_raw, profile = read_task_artifact(bundle['profile'], 'calibration profile')
        close_manifest_path, close_manifest_raw, close_manifest = read_task_artifact(bundle['safe_close_manifest'], 'safe-close manifest')
        close_image_path, close_image_raw, _ = read_task_artifact(bundle['safe_close_image'], 'safe-close image', as_json=False)
        closure_path, closure_raw, closure = read_task_artifact(bundle['closure_observation'], 'calibration closure observation')

        capture_sha = sha(image_raw)
        require(capture.get('verdict') == 'CAPTURED' and capture.get('capture_did_not_activate_or_input') is True,
                'menu capture is not a read-only captured frame')
        require(capture.get('image_sha256') == capture_sha and capture.get('image_path') == str(image_path),
                'menu capture manifest/image mismatch')
        capture_windows = {int(w['window_id']): w for w in capture.get('sck_window_inventory', [])}
        detail_id, popup_id = int(geometry['detail_window_id']), int(geometry['popup_window_id'])
        require(capture.get('selected_window_id') == detail_id and
                capture_windows.get(detail_id, {}).get('on_screen') is True and
                capture_windows.get(popup_id, {}).get('on_screen') is True,
                'menu capture does not show the selected detail and popup windows')
        require(target.get('native_full_display_evidence', {}).get('manifest_path') == bundle['menu_capture_manifest']['path'] and
                target.get('native_full_display_evidence', {}).get('image_path') == bundle['menu_capture_image']['path'] and
                target.get('native_full_display_evidence', {}).get('image_sha256') == capture_sha,
                'target and calibration do not share one native frame')
        require(ocr.get('input_sha256') == capture_sha and geometry.get('capture_sha256') == capture_sha and
                geometry.get('ocr_input_sha256') == capture_sha and anchors.get('source_capture_sha256') == capture_sha,
                'menu capture, OCR, anchors, and geometry are not hash-bound')
        menu_texts = [candidate.get('text') for result in ocr.get('results', [])
                      for observation in result.get('observations', [])
                      for candidate in observation.get('top_candidates', [])[:1]]
        expected_menu_rows = ['選擇項目', '修改相簿名稱', '儲存全部', '刪除相簿', '分享相簿']
        require([text for text in menu_texts if text in expected_menu_rows] == expected_menu_rows,
                'native menu rows/order are incomplete or ambiguous')
        require(geometry.get('capture_nonce') == capture.get('nonce') and
                anchors.get('detail_window_id') == geometry.get('detail_window_id'),
                'menu capture nonce/window binding mismatch')
        require(geometry.get('candidate') == 'observed-menu-coordinate-fix-v2' and
                geometry.get('pre_dispatch_ready') is True and profile.get('profile_id') == geometry.get('profile_id'),
                'calibration geometry/profile is not the reviewed v2 candidate')
        require(ocr.get('profile', {}).get('processing_scale') == profile.get('processing_scale'),
                'OCR processing scale/profile mismatch')

        policy = profile.get('geometry_policy', {})
        row = geometry.get('save_all_bracketing_rows', {})
        required_clearance = float(geometry.get('mapping_uncertainty_source_pixels', 1e9)) + 4.0
        require(float(geometry.get('maximum_anchor_residual_source_pixels', 1e9)) <=
                float(policy.get('maximum_anchor_residual_source_pixels', -1)), 'anchor residual exceeds profile')
        require(float(row.get('target_clearance_display_pixels', -1)) >= required_clearance and
                float(row.get('required_clearance_display_pixels', -1)) >= required_clearance,
                'Save All row clearance is insufficient')
        intersection = geometry.get('actionable_intersection_pixels', {})
        require(float(intersection.get('width', 0)) >= float(policy.get('minimum_actionable_intersection_width_pixels', 1e9)) and
                float(intersection.get('height', 0)) >= float(policy.get('minimum_actionable_intersection_height_pixels', 1e9)),
                'popup/detail actionable intersection is too small')
        require(row.get('above') == '修改相簿名稱' and row.get('target') == '儲存全部' and row.get('below') == '刪除相簿',
                'Save All row is not bracketed by the expected adjacent menu rows')
        cua_size = geometry.get('cua_screenshot_pixels', {})
        require(calibration.get('screenshot_width') == cua_size.get('width') and
                calibration.get('screenshot_height') == cua_size.get('height'), 'calibration screenshot size drift')
        expected_point = geometry.get('derived_save_all_cua_screenshot_pixel', {})
        actual_point = calibration.get('save_all_point')
        require(isinstance(actual_point, list) and len(actual_point) == 2 and
                abs(float(actual_point[0]) - float(expected_point.get('x', -1))) <= 0.5 and
                abs(float(actual_point[1]) - float(expected_point.get('y', -1))) <= 0.5,
                'calibration dispatch point differs from bound geometry')

        require(close_manifest.get('verdict') == 'CAPTURED' and close_manifest.get('image_sha256') == sha(close_image_raw) and
                close_manifest.get('image_path') == str(close_image_path) and
                close_manifest.get('selected_window_id') == geometry.get('detail_window_id') and
                close_manifest.get('target_application_on_screen_window_count') == 2,
                'safe-close frame does not show the same detail with the popup absent')
        close_windows = {int(w['window_id']): w for w in close_manifest.get('sck_window_inventory', [])}
        require(close_windows.get(int(geometry['detail_window_id']), {}).get('on_screen') is True and
                close_windows.get(int(geometry['popup_window_id']), {}).get('on_screen') is not True,
                'safe-close detail/popup window postcondition mismatch')
        post_close = closure.get('post_close_identity', {})
        post_group = read_task_artifact(post_close.get('group_ocr'), 'post-close group OCR')[2]
        post_detail = read_task_artifact(post_close.get('detail_ocr'), 'post-close detail OCR')[2]
        require(post_close.get('same_capture_sha256') == close_manifest.get('image_sha256') and
                post_group.get('input_sha256') == close_manifest.get('image_sha256') and
                post_detail.get('input_sha256') == close_manifest.get('image_sha256'),
                'post-close OCR is not bound to the safe-close display frame')
        def post_texts(ocr):
            return [candidate.get('text') for result in ocr.get('results', [])
                    for observation in result.get('observations', [])
                    for candidate in observation.get('top_candidates', [])[:1]]
        require(post_texts(post_group).count(cfg['group_name']) == 1 and
                post_texts(post_detail).count(expected_title) == 1 and
                post_texts(post_detail).count(f"{self.fp['expected_images']}張照片") == 1,
                'post-close group/detail identity did not remain matched')
        require(closure.get('visual_status') == 'OBSERVED' and
                closure.get('target', {}).get('group') == cfg['group_name'] and
                closure.get('target', {}).get('detail_window_id') == detail_id and
                closure.get('target', {}).get('date_text') == expected_title and
                closure.get('target', {}).get('count_text') == f"{self.fp['expected_images']}張照片",
                'post-close target observation identity mismatch')
        ellipsis = closure.get('cua_closed_surface_observation', {})
        require(isinstance(ellipsis, dict) and ellipsis.get('status') == 'OBSERVED' and
                ellipsis.get('menu_visible_in_bound_window') is False and
                ellipsis.get('screenshot_pixels') == [calibration['screenshot_width'], calibration['screenshot_height']]
                and ellipsis.get('ellipsis_center_pixels') == calibration.get('ellipsis') and
                ellipsis.get('dot_spacing_pixels') == calibration.get('dot_spacing'), 'fresh ellipsis observation mismatch')
        safe_close = closure.get('safe_close', {})
        require(isinstance(safe_close, dict) and safe_close.get('status') == 'OBSERVED' and
                safe_close.get('activation') == 'NONE' and safe_close.get('popup_absent') is True and
                safe_close.get('same_detail_window_still_on_screen') is True and
                safe_close.get('postcondition_manifest') == bundle['safe_close_manifest']['path'] and
                safe_close.get('postcondition_image') == bundle['safe_close_image']['path'],
                'safe-close no-activation proof missing')
        require(calibration.get('evidence') == json.dumps(bundle, ensure_ascii=False, sort_keys=True),
                'persisted calibration evidence reference differs from validated evidence bundle')

    def eligibility(self, state, cfg, exclude_current=False):
        view = copy.deepcopy(state)
        if exclude_current:
            view['runs'] = [r for r in view['runs'] if r['run_id'] != self.run_id]
            view['current_run_id'] = None
            view['active_writer_id'] = None
            view['context_lock'] = None
        by_id = {r['run_id']:r for r in view['runs']}
        return history_decision(view, dict(fingerprint=self.fp), by_id)[0]

    def run(self, state):
        found = [r for r in state['runs'] if r['run_id'] == self.run_id]
        require(len(found) == 1, 'run not uniquely bound')
        return found[0]

    def event(self, state, phase, evidence):
        require(phase in PHASES, 'invalid event phase')
        r = self.run(state)
        item = dict(phase=phase, at=utc_now(), evidence=evidence if isinstance(evidence,str) else json.dumps(evidence, ensure_ascii=False, sort_keys=True))
        r['phase'] = phase
        r['events'].append(item)
        r['checkpoint'] = item

    def commit(self, operation, expected, payload=None):
        payload = payload or {}
        # Authority must exist before even creating the shared lock.
        pre = ProjectReader(str(self.root))
        try:
            self.load(pre)
        finally:
            pre.close()
        with shared_guard(self.root) as verify_lock:
            reader = ProjectReader(str(self.root))
            try:
                cfg,before,by_id,raw,identity = self.load(reader)
                require(expected.get('project_root') == str(self.root) and expected.get('config_sha256') == self.expected_config_sha, 'receipt authority mismatch')
                require(type(expected.get('revision')) is int and before['revision'] == expected['revision'] and sha(raw) == expected['sha256'], 'stale revision/content')
                require(list(identity) == expected['state_identity'], 'state identity/ABA drift')
                require(expected.get('run_id') == self.run_id and expected.get('owner_id') == self.owner_id, 'receipt actor mismatch')
                candidate = copy.deepcopy(before)
                if operation == 'acquire':
                    require(before['active_writer_id'] is None and before['context_lock'] is None, 'foreign/active ownership')
                    require(self.run_id not in by_id, 'run ID already used')
                    require(self.eligibility(before,cfg) == 'PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION', 'duplicate/unresolved/ambiguous/busy')
                    dest = self.destination(cfg)
                    if not os.path.lexists(dest):
                        dest.mkdir(exist_ok=False)
                    self.destination(cfg)
                    item = dict(phase='LOAD_STATE',at=utc_now(),evidence=json.dumps(dict(owner=self.owner_id,run=self.run_id,source='fresh guarded acquisition; existing prior history preserved; destination observed empty'),ensure_ascii=False))
                    candidate['runs'].append(dict(run_id=self.run_id,mode='backup_one',group_key=cfg['group_key'],album_id=None,fingerprint=copy.deepcopy(self.fp),observed_title=self.fp['start_date'].replace('-','/')+'~'+self.fp['end_date'][5:].replace('-','/'),title_confidence='HIGH',destination=str(dest),destination_initially_empty=True,
                        phase='LOAD_STATE',checkpoint=item,events=[item],intent=None,recovery_used={},runtime_errors=[],verification=None,workflow_outcome='IN_PROGRESS',stop_reason=None,batch_id=None,intent_state='INTENT_NONE',manual_reconciliation_required=False,reconciliation_reason=None,contract_revision='1.0-rc2',dispatch_state='NOT_ATTEMPTED',dispatch_evidence=None,reconciliations=[]))
                    candidate['current_run_id'] = self.run_id
                    candidate['active_writer_id'] = self.owner_id
                else:
                    require(before['active_writer_id'] == self.owner_id and before['current_run_id'] == self.run_id, 'foreign/retired owner')
                    r = self.run(candidate)
                    require(r['workflow_outcome'] == 'IN_PROGRESS', 'terminal owner fenced')
                    require(r['group_key'] == cfg['group_key'] and r['fingerprint'] == self.fp, 'run identity drift')
                    require(r['destination'] == str(Path(cfg['backup_root'])/cfg['group_name']/f"{self.fp['start_date']}_{self.fp['end_date']}_{self.fp['expected_images']}張"), 'run destination drift')
                    self.event(candidate,r['phase'],dict(prior_observation=dict(intent_state=r['intent_state'],dispatch_state=r['dispatch_state'],intent=copy.deepcopy(r['intent']),dispatch_evidence=copy.deepcopy(r['dispatch_evidence'])),maintenance='append prior fields before progression'))
                    if operation == 'event':
                        require(payload['phase'] not in {'VERIFIED','SAFE_ABORT','SAVE_ALL_INTENT_COMMITTED','TRIGGER_CONFIRMED','TRIGGER_UNKNOWN'}, 'reserved phase')
                        require(r['intent'] is None or payload['phase'] in {'CHOOSER','DOWNLOAD_STARTED','VERIFYING'}, 'post-intent navigation forbidden')
                        self.event(candidate,payload['phase'],payload['evidence'])
                        if payload.get('context_confirmed') is True:
                            require(r['intent'] is None, 'context acquisition after intent')
                            candidate['context_lock'] = dict(group_key=cfg['group_key'],source='USER_CONFIRMATION',confirmed_at=utc_now(),execution_id=self.owner_id,continuity_evidence=json.dumps(payload['evidence'],ensure_ascii=False))
                        r['runtime_errors'].extend(payload.get('runtime_errors',[]))
                    elif operation == 'intent':
                        require(r['intent'] is None and r['intent_state'] == 'INTENT_NONE' and r['dispatch_evidence'] is None, 'intent already present: no loaded permit')
                        require(r['phase'] == 'SAVE_ALL_CALIBRATION', 'calibration phase required')
                        require(self.eligibility(before,cfg,True) == 'PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION', 'fresh duplicate/history gate')
                        require(str(self.destination(cfg)) == r['destination'], 'destination drift')
                        require(candidate['context_lock'] is not None and candidate['context_lock']['execution_id'] == self.owner_id, 'context missing')
                        require(payload.get('fresh_target_match') is True and payload.get('safe_calibration_closed_no_activation') is True, 'fresh target/calibration safety')
                        cal = payload['calibration']; _check_calibration(cal)
                        self.validate_calibration_package(payload, cfg, cal)
                        r['intent'] = dict(action_id='ACTION-'+self.run_id,committed_at=utc_now(),owner_execution_id=self.owner_id,group_key=cfg['group_key'],fingerprint=copy.deepcopy(self.fp),destination=r['destination'],calibration=copy.deepcopy(cal),save_all_retry_allowed=False,dispatch_outcome='NOT_ATTEMPTED',trigger_outcome='NOT_APPLICABLE')
                        r['intent_state'] = 'INTENT_COMMITTED'
                        self.event(candidate,'SAVE_ALL_INTENT_COMMITTED',payload)
                    elif operation == 'dispatch':
                        require(r['intent'] is not None and r['intent_state'] == 'INTENT_COMMITTED' and r['dispatch_evidence'] is None, 'no new dispatch record permitted')
                        d = payload['dispatch_evidence']
                        require(d['run_id'] == self.run_id and d['execution_id'] == self.owner_id and d['action_id'] == r['intent']['action_id'], 'dispatch identity mismatch')
                        r['dispatch_evidence'] = copy.deepcopy(d)
                        r['intent']['dispatch_outcome'] = payload['dispatch_outcome']
                        r['intent']['trigger_outcome'] = 'TRIGGER_CONFIRMED' if d['folder_chooser_appeared'] is True else 'UNKNOWN'
                        r['intent_state'] = 'TRIGGER_CONFIRMED' if d['folder_chooser_appeared'] is True else 'TRIGGER_UNKNOWN'
                        r['dispatch_state'] = 'SAVE_ALL_RETURNED' if d['save_all_invocation_attempted'] is True and payload['dispatch_outcome'] == 'RETURNED' else 'UNKNOWN'
                        r['manual_reconciliation_required'] = d['folder_chooser_appeared'] is not True
                        r['reconciliation_reason'] = None if not r['manual_reconciliation_required'] else 'Actual or uncertain dispatch; no retry; retained intent.'
                        self.event(candidate,r['intent_state'],payload)
                    elif operation == 'finalize':
                        require(payload['outcome'] in {'VERIFIED','SAFE_ABORT'}, 'terminal outcome required')
                        if payload['outcome'] == 'VERIFIED':
                            v = payload['verification']; d = r['dispatch_evidence']
                            require(r['intent'] is not None and r['intent_state'] == 'TRIGGER_CONFIRMED' and d is not None, 'no confirmed transaction')
                            require(d['save_all_click_count'] == 1 and d['save_all_invocation_attempted'] is True and d['folder_chooser_appeared'] is True, 'dispatch/chooser proof')
                            require(payload.get('download_started') is True and payload.get('correct_destination_confirmed') is True, 'download/destination proof')
                            require(v['outcome'] == 'PASS' and type(v['image_files']) is int and v['image_files'] == self.fp['expected_images'] and v['stable_samples'] >= 3, 'verification count/stability')
                            require(not any(v[k] for k in ['subdirectories','zero_byte_files','partial_temp_files','unrecognized_files','other_entries']), 'verification anomalies')
                            # The payload must describe the current dynamic destination, not just a PASS label.
                            dest = Path(r['destination']); no_symlink(dest)
                            current = _inventory(dest,False)
                            require(_classify_filesystem([current],self.fp['expected_images'])[0] == 'PASS', 'current filesystem not passing')
                            require(_inventory_key(current) == _inventory_key(dict(entries=v['inventory'])) and current['total_bytes'] == v['total_bytes'] and current['regular_files'] == v['regular_files'], 'verification inventory not current')
                            evidence = self.root/'evidence' if self.test_mode else self.evidence
                            retained,_ = read_json_path(evidence/'filesystem-verification.json')
                            decoding,_ = read_json_path(evidence/'image-decode.stdout.json')
                            receipt,_ = read_json_path(evidence/'verification-receipt.json')
                            require(_same_json(retained,v) and _same_json(receipt['verification'],v) and receipt['verdict'] == 'PASS' and receipt['decoder_exit_code'] == 0, 'verification receipts disagree')
                            require(decoding['verdict'] == 'PASS' and decoding['destination'] == r['destination'] and len(decoding['entries']) == self.fp['expected_images'] and all(e['decoded'] is True for e in decoding['entries']), 'full decode receipt missing')
                            require({e['name'] for e in decoding['entries']} == {e['relative_path'] for e in current['entries']}, 'decoded file set mismatch')
                            require(receipt['decoder_sha256'] == sha((TASK/'candidate/v2/bin/image-decode').read_bytes()) and receipt['decoder_stdout_sha256'] == sha((evidence/'image-decode.stdout.json').read_bytes()), 'decoder binding drift')
                            r['verification'] = copy.deepcopy(v)
                            r['dispatch_evidence']['download_started'] = True
                            candidate['verified_albums'].append(dict(group_key=cfg['group_key'],fingerprint=copy.deepcopy(self.fp),verified_run_id=self.run_id,destinations=[r['destination']],source_kind='filesystem_verification',evidence=payload['source_reference']))
                            self.event(candidate,'VERIFIED',payload['source_reference'])
                        elif r['intent'] is not None:
                            r['manual_reconciliation_required'] = True
                            r['reconciliation_reason'] = 'SAFE_ABORT with retained intent: dispatch/result unresolved; no automatic retry.'
                        r['workflow_outcome'] = payload['outcome']
                        r['stop_reason'] = payload.get('stop_reason')
                        self.event(candidate,payload['outcome'],payload)
                        if payload['outcome'] == 'VERIFIED':
                            self.event(candidate,'VERIFIED',payload['source_reference'])
                        candidate['active_writer_id'] = None
                        candidate['context_lock'] = None
                    else:
                        raise Refusal('unknown operation')
                candidate['revision'] = before['revision'] + 1
                validate_state_strict(candidate)
                validate_history(candidate,cfg,reader)
                require(candidate['runs'][:len(before['runs'])-int(operation!='acquire')] == before['runs'][:len(before['runs'])-int(operation!='acquire')], 'prior runs changed')
                require(candidate['verified_albums'][:len(before['verified_albums'])] == before['verified_albums'], 'prior registry changed')
                for relative,(observed,ident) in list(reader.observations.items()):
                    require(reader.read(relative) == (observed,ident), 'precommit authority drift')
                reader.fresh_root(); verify_lock()
                meta = atomic_write_json(self.path,candidate)
                verify_lock()
                check = ProjectReader(str(self.root))
                try:
                    cfg2,state2,_,after,afteridentity = self.load(check)
                    require(after == json_bytes(candidate) and sha(after) == meta['sha256'], 'committed readback uncertainty')
                    require(cfg2 == cfg and state2['revision'] == before['revision']+1, 'readback authority/revision')
                finally:
                    check.close()
                return dict(operation=operation,revision=candidate['revision'],sha256=sha(after),state_identity=list(afteridentity),config_sha256=self.expected_config_sha,run_id=self.run_id,owner_id=self.owner_id,project_root=str(self.root),active_writer_id=candidate['active_writer_id'],durability=meta['durability'])
            finally:
                reader.close()

def authorize(run_authority_path, project_root):
    require(project_root == str(ROOT), 'explicit selected project root mismatch')
    auth,_ = read_json_path(TASK/'authorization.json')
    waiver,_ = read_json_path(TASK/'user-plan-review-waiver.json')
    contract,_ = read_json_path(TASK/'plan-contract.json')
    run_authority,_ = read_json_path(run_authority_path)
    require(auth.get('task_id') == contract.get('task_id') == 'TASK-20261010-line-e2e-fullscreen-repair', 'task authority mismatch')
    require(auth.get('plan_review_decision') == 'Explicit user waiver; NOT a reviewer PASS', 'user authorization missing')
    require(waiver.get('decision') == 'WAIVE_PLAN_REVIEW_PRECONDITION' and waiver.get('local_execution_authorized') is True, 'local execution waiver missing')
    require((TASK/'handoff.json').read_bytes() == (TASK/'plan-contract.json').read_bytes(), 'handoff/contract mismatch')
    require(run_authority.get('project_root') == str(ROOT), 'run authority root mismatch')
    require(run_authority.get('plan_contract_sha256') == sha((TASK/'plan-contract.json').read_bytes()), 'plan contract binding drift')
    require(run_authority.get('authorization_sha256') == sha((TASK/'authorization.json').read_bytes()), 'authorization binding drift')
    expected_config_sha = run_authority.get('config_sha256')
    cfg_path = ROOT/'config/line_backup_config.json'
    no_symlink(cfg_path)
    cfg_raw = cfg_path.read_bytes()
    require(sha(cfg_raw) == expected_config_sha, 'config binding drift')
    cfg = strict_json(cfg_raw, 'INVALID_CONFIG')
    validate_config(cfg, str(ROOT))
    fp = run_authority.get('fingerprint')
    require(isinstance(fp, dict) and set(fp) == {'start_date','end_date','expected_images'}, 'run authority fingerprint shape')
    require(isinstance(fp['start_date'], str) and isinstance(fp['end_date'], str) and type(fp['expected_images']) is int and fp['expected_images'] > 0, 'run authority fingerprint value')
    require(isinstance(run_authority.get('run_id'), str) and run_authority['run_id'].startswith('RUN-'), 'run ID missing')
    require(isinstance(run_authority.get('owner_id'), str) and run_authority['owner_id'].startswith('OWNER-'), 'owner ID missing')
    evidence_rel = run_authority.get('target_evidence')
    require(isinstance(evidence_rel, str) and not Path(evidence_rel).is_absolute() and '..' not in Path(evidence_rel).parts, 'target evidence path missing')
    target_path = TASK/evidence_rel
    require(target_path.resolve(strict=False).is_relative_to(TASK), 'target evidence outside task')
    target,target_raw = read_json_path(target_path)
    require(sha(target_raw) == run_authority.get('target_evidence_sha256'), 'target evidence binding drift')
    require(target.get('target_fingerprint') == fp, 'target evidence/fingerprint mismatch')
    expected_title = fp['start_date'].replace('-', '/') + '~' + fp['end_date'][5:].replace('-', '/')
    expected_count = f"{fp['expected_images']}張照片"
    post = target.get('postcondition', {})
    require(target.get('group') == cfg['group_name'] and post.get('surface') == 'album_detail', 'target context is not the configured album detail')
    require(post.get('date_text') == expected_title and post.get('count_text') == expected_count, 'detail identity mismatch')
    native = target.get('native_full_display_evidence', {})
    manifest_rel = native.get('manifest_path')
    image_rel = native.get('image_path')
    require(isinstance(manifest_rel, str) and isinstance(image_rel, str), 'native detail evidence missing')
    for rel in (manifest_rel, image_rel):
        require(not Path(rel).is_absolute() and '..' not in Path(rel).parts, 'native evidence path invalid')
    manifest_path, image_path = TASK/manifest_rel, TASK/image_rel
    require(manifest_path.resolve(strict=False).is_relative_to(TASK) and image_path.resolve(strict=False).is_relative_to(TASK), 'native evidence outside task')
    manifest,manifest_raw = read_json_path(manifest_path)
    image_data = image_path.read_bytes()
    dimensions = native.get('dimensions_pixels', [])
    require(manifest.get('image_sha256') == native.get('image_sha256') == sha(image_data), 'native detail image binding mismatch')
    require(len(dimensions) == 2 and manifest.get('image_width_pixels') == dimensions[0] and manifest.get('image_height_pixels') == dimensions[1], 'native detail dimensions mismatch')
    group_path = post.get('group_ocr_path')
    group_sha = post.get('group_ocr_sha256')
    detail_path = post.get('detail_ocr_path')
    detail_sha = post.get('detail_ocr_sha256')
    group_ocr = read_task_artifact({'path': group_path, 'sha256': group_sha}, 'target group OCR')[2]
    detail_ocr = read_task_artifact({'path': detail_path, 'sha256': detail_sha}, 'target detail OCR')[2]
    require(group_ocr.get('input_sha256') == detail_ocr.get('input_sha256') == native.get('image_sha256'),
            'target group/detail OCR is not bound to the native target frame')
    def recognized(ocr):
        return [candidate.get('text') for result in ocr.get('results', [])
                for observation in result.get('observations', [])
                for candidate in observation.get('top_candidates', [])[:1]]
    require(recognized(group_ocr).count(cfg['group_name']) == 1, 'configured group title not unique in native OCR')
    detail_texts = recognized(detail_ocr)
    require(detail_texts.count(expected_title) == 1 and detail_texts.count(expected_count) == 1,
            'target date/count not unique in native detail OCR')
    return run_authority


def write_exclusive_json(path, value):
    path = Path(path)
    require(path.is_relative_to(TASK), 'receipt outside task')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode('utf-8') + b'\n')

def main():
    p = argparse.ArgumentParser(); p.add_argument('operation',choices=['snapshot','acquire','event','intent','dispatch','finalize'])
    p.add_argument('--project-root',required=True);p.add_argument('--run-authority',required=True);p.add_argument('--receipt');p.add_argument('--payload');p.add_argument('--output',required=True)
    a = p.parse_args()
    authority_path = Path(a.run_authority); require(authority_path.is_relative_to(TASK), 'run authority outside task')
    authority = authorize(authority_path, a.project_root)
    op = Operator(ROOT,authority['config_sha256'],authority['run_id'],authority['owner_id'],authority['fingerprint'],
                  authority['target_evidence'],authority['target_evidence_sha256'])
    if a.operation == 'snapshot':
        receipt = op.snapshot()
    else:
        require(a.receipt is not None,'expected receipt required');receipt_path=Path(a.receipt)
        require(receipt_path.is_relative_to(TASK),'receipt outside task');expected,_=read_json_path(receipt_path)
        payload={}
        if a.payload:
            payload_path=Path(a.payload);require(payload_path.is_relative_to(TASK),'payload outside task');payload,_=read_json_path(payload_path)
        next_revision = expected['revision'] + 1
        copy_path = TASK/'evidence'/f"state-r{next_revision:06}.json"
        require(not copy_path.exists(), 'refusing to overwrite state evidence')
        receipt = op.commit(a.operation,expected,payload)
        with copy_path.open('xb') as stream: stream.write(op.path.read_bytes())
        try:
            append_projection(ROOT/'state/run_log.md',receipt)
        except Exception as error:
            receipt['non_gating_projection_error'] = str(error)
    write_exclusive_json(a.output,receipt)
    print(json.dumps(receipt,ensure_ascii=False))

if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(json.dumps(dict(verdict='REFUSAL',error=str(error),no_dispatcher=True)),file=sys.stderr)
        raise SystemExit(1)
