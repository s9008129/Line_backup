"""Execute the single-input helper documented in the Notes evidence template."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / '.agents' / 'skills' / 'line-notes-agent-cua' / 'references' / 'evidence-template.md'
TASKS = ROOT / '.local' / 'line-backup' / 'tasks'
START = '<!-- cua-evidence-tools:start -->'
END = '<!-- cua-evidence-tools:end -->'
INITIAL_START = '<!-- cua-initial-observation:start -->'
INITIAL_END = '<!-- cua-initial-observation:end -->'
REVEAL_START = '<!-- notes-reveal-capture:start -->'
REVEAL_END = '<!-- notes-reveal-capture:end -->'
DISPATCH_START = '<!-- notes-intent-dispatch:start -->'
DISPATCH_END = '<!-- notes-intent-dispatch:end -->'


def documented_tools_source():
    text = TEMPLATE.read_text(encoding='utf-8')
    start = text.index(START) + len(START)
    code_start = text.index('```js', start) + len('```js')
    code_end = text.index('```', code_start)
    return text[code_start:code_end]


def documented_initial_observation_source():
    text = TEMPLATE.read_text(encoding='utf-8')
    start = text.index(INITIAL_START) + len(INITIAL_START)
    end = text.index(INITIAL_END, start)
    section = text[start:end]
    if section.count('```js') != 1 or section.count('```') != 2:
        raise AssertionError(
            'cua-initial-observation must enclose exactly one js block')
    code_start = section.index('```js') + len('```js')
    code_end = section.index('```', code_start)
    if section[code_end + 3:].strip():
        raise AssertionError(
            'unexpected content after cua-initial-observation js block')
    return section[code_start:code_end]


def documented_reveal_source():
    text = TEMPLATE.read_text(encoding='utf-8')
    start = text.index(REVEAL_START) + len(REVEAL_START)
    code_start = text.index('```js', start) + len('```js')
    code_end = text.index('```', code_start)
    return text[code_start:code_end]


def documented_dispatch_source():
    text = TEMPLATE.read_text(encoding='utf-8')
    start = text.index(DISPATCH_START) + len(DISPATCH_START)
    code_start = text.index('```js', start) + len('```js')
    code_end = text.index('```', code_start)
    return text[code_start:code_end]


BLOCK_MARKERS = (
    'notes-intent-preflight',
    'notes-intent-readback',
    'notes-intent-capture',
    'notes-download-builder',
    'notes-direct-dispatch',
    'notes-reveal-path',
    'notes-reveal-download',
)


def documented_blocks():
    text = TEMPLATE.read_text(encoding='utf-8')
    blocks = {}
    for name in BLOCK_MARKERS:
        start_marker = '<!-- %s:start -->' % name
        end_marker = '<!-- %s:end -->' % name
        start = text.index(start_marker) + len(start_marker)
        end = text.index(end_marker, start)
        section = text[start:end]
        code_start = section.index('```js') + len('```js')
        code_end = section.index('```', code_start)
        if section[code_end + 3:].strip():
            raise AssertionError('unexpected content after js block: ' + name)
        blocks[name] = section[code_start:code_end]
    return blocks


DISPATCH_SETUP = r'''
const dispatchEventSha = 'a'.repeat(64);
const dispatchEventRef = () => ({sequence: 7, event_sha256: dispatchEventSha});
const dispatchIntent = (attemptId, overrides = {}) => ({
  attempt_id: attemptId,
  status: 'UNKNOWN',
  dispatch_authorized: false,
  ...overrides,
});
const dispatchCapture = () => ({
  state: '{"role":"AXWindow","marker":"dispatch"}',
  screenshot: new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
});
const dispatchFreshCapture = label => ({
  state: JSON.stringify({role: 'AXWindow', marker: label}),
  screenshot: new TextEncoder().encode('SYNTHETIC_CAPTURE:' + label),
});
async function dispatchObservation(observationId, capture = dispatchCapture()) {
  return evidenceTools.persistObservation({
    taskDir: process.env.INPUT_TEST_ROOT,
    observationDir: process.env.INPUT_TEST_DIR,
    observationId,
    capture,
  });
}
const dispatchRef = asset => ({
  path: asset.path, bytes: asset.bytes, sha256: asset.sha256,
});
function dispatchDownloadRequest(attemptId, observation, target = [60, 70]) {
  const screenshot = dispatchRef(observation.assets.screenshot);
  return {
    input_phase: 'DOWNLOAD_CONTROL',
    attempt_id: attemptId,
    intent_event_ref: dispatchEventRef(),
    app_window_binding: {
      app_bundle_id: 'jp.naver.line.mac',
      window_id: 'synthetic-window',
    },
    source_observation: screenshot,
    source_observation_ref: {...screenshot},
    mapping_evidence_ref: dispatchRef(observation.assets.ax),
    mapping_status: 'MATCH',
    observation_order: 'PRE_INPUT',
    grounding_conclusion: 'PASS_TO_INPUT',
    candidate_point_relation: 'INSIDE',
    coordinate_space_match: 'MATCH',
    control_region_coord_space: 'SCREEN_POINTS',
    target_coord_space: 'SCREEN_POINTS',
    control_region: [20, 30, 80, 90],
    candidate_point: target,
    prepared_target: target,
  };
}
function dispatchNavigationRequest(attemptId, ordinal = 1) {
  const request = {
    input_phase: 'NAVIGATION',
    attempt_id: attemptId,
    intent_event_ref: dispatchEventRef(),
    navigation_kind: 'selected-filmstrip-safe-edge',
    reveal_candidate_id: 'candidate-1',
    reveal_scope_ref: 'scope-1',
    candidate_ordinal: ordinal,
    prepared_target: [50, 60],
  };
  return ordinal === 1
    ? {...request, prior_candidate_refs: 'NONE',
       budget_before: 0, budget_after: 1}
    : {...request, prior_candidate_refs: ['prior-candidate-receipt'],
       budget_before: 1, budget_after: 2};
}
const dispatchPaths = () => ({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
});
const dispatchRevealOptions = (attemptId, request, app, overrides = {}) => ({
  ...dispatchPaths(),
  intent: dispatchIntent(attemptId),
  intentEventRef: dispatchEventRef(),
  request,
  app,
  ...overrides,
});
const dispatchGatedRevealOptions = (stage, app, overrides = {}) => ({
  ...dispatchPaths(),
  intent: dispatchIntent(stage.request.attempt_id),
  intentEventRef: dispatchEventRef(),
  request: stage.request,
  app,
  preIntentReveal: stage.preIntentReveal,
  beforeObservation: stage.beforeObservation,
  windowBinding: stage.windowBinding,
  ...overrides,
});
const dispatchDownloadOptions = (attemptId, request, app, source,
                                  overrides = {}) => ({
  ...dispatchPaths(),
  intent: dispatchIntent(attemptId),
  intentEventRef: dispatchEventRef(),
  request,
  app,
  ...source,
  ...overrides,
});
const dispatchReadinessApp = (counters = {}) => ({
  async click(target) {
    counters.clicks = (counters.clicks || 0) + 1;
    return {target};
  },
  async getAXStateAndScreenshot() {
    counters.captures = (counters.captures || 0) + 1;
    return dispatchCapture();
  },
});
const dispatchWindowBinding = (overrides = {}) => ({
  app_bundle_id: 'jp.naver.line.mac',
  window_id: 'synthetic-readiness-window',
  ...overrides,
});
function dispatchDirectReadinessDecision(observation, overrides = {}) {
  const screenshot = dispatchRef(observation.assets.screenshot);
  return {
    control_visibility: 'VISIBLE',
    control_owner: 'MATCH',
    enabled_state: 'ENABLED',
    mapping_status: 'MATCH',
    observation_order: 'PRE_INPUT',
    grounding_conclusion: 'PASS_TO_INPUT',
    candidate_point_relation: 'INSIDE',
    coordinate_space_match: 'MATCH',
    control_region_coord_space: 'SCREEN_POINTS',
    target_coord_space: 'SCREEN_POINTS',
    control_region: [20, 30, 80, 90],
    candidate_point: [60, 70],
    prepared_target: [60, 70],
    position_source_ref: screenshot,
    ...overrides,
  };
}
function dispatchRevealReadinessDecision(observation, ordinal = 1, overrides = {}) {
  const screenshot = dispatchRef(observation.assets.screenshot);
  const ax = dispatchRef(observation.assets.ax);
  const request = {
    navigation_kind: 'selected-filmstrip-safe-edge',
    reveal_candidate_id: 'candidate-' + ordinal,
    reveal_scope_ref: 'scope-synthetic-1',
    candidate_ordinal: ordinal,
    prior_candidate_refs: ordinal === 1 ? 'NONE' : ['prior-candidate-receipt'],
    budget_before: ordinal === 1 ? 0 : 1,
    budget_after: ordinal,
    before_screenshot_ref: screenshot,
    before_ax_ref: ax,
    selected_state_before: 'SELECTED',
    selected_media_ref: 'media-synthetic-1',
    safe_zone_ref: 'safe-edge-synthetic-1',
    safe_zone: [40, 50, 100, 110],
    prepared_target: [70, 80],
    mapping_id: 'mapping-synthetic-1',
    mapping_valid_at: '2026-11-20T00:00:00Z',
    mapping_status: 'MATCH',
    observation_order: 'PRE_INPUT',
    coordinate_space_match: 'MATCH',
    control_region_coord_space: 'SCREEN_POINTS',
    target_coord_space: 'SCREEN_POINTS',
    position_source_ref: screenshot,
  };
  if (ordinal === 2) {
    request.rearm_preconditions_ref = 'prior-candidate-after';
    request.rearm_new_information_ref = 'current-tool-document';
    request.rearm_new_information_conclusion = 'PASS';
  }
  return {...request, ...overrides};
}
function dispatchRevealRequest(attemptId, observation, ordinal = 1, overrides = {}) {
  return {
    input_phase: 'NAVIGATION',
    attempt_id: attemptId,
    intent_event_ref: dispatchEventRef(),
    ...dispatchRevealReadinessDecision(observation, ordinal, overrides),
  };
}
async function dispatchRevealStage(
  attemptId, ordinal = 1, windowBinding = dispatchWindowBinding(), overrides = {},
  stageLabel = attemptId,
) {
  const app = dispatchReadinessApp();
  const preObservation = await dispatchObservation(
    stageLabel + '-pre', dispatchFreshCapture(stageLabel + '-pre'));
  const preIntentReveal = notesIntentDispatch.checkDownloadReadiness({
    app,
    observation: preObservation,
    windowBinding,
    branch: 'REVEAL',
    decision: dispatchRevealReadinessDecision(preObservation, ordinal, overrides),
  });
  const beforeObservation = await dispatchObservation(
    stageLabel + '-before', dispatchFreshCapture(stageLabel + '-before'));
  const request = dispatchRevealRequest(
    attemptId, beforeObservation, ordinal, overrides);
  return {
    preObservation,
    beforeObservation,
    preIntentReveal,
    request,
    windowBinding,
  };
}
'''


class NodeHelperRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools_source = documented_tools_source()
        cls.reveal_source = documented_reveal_source()
        cls.dispatch_source = documented_dispatch_source()
        TASKS.mkdir(parents=True, exist_ok=True)

    def run_helper(self, body, extra_source='',
                   observation_id='INTENT_AFTER_OBSERVATION_ID'):
        with tempfile.TemporaryDirectory(prefix='.notes-input-helper-', dir=TASKS) as temp:
            root = Path(temp).resolve()
            output_dir = root / 'observations'
            output_dir.mkdir()
            for old, new in (
                ('/ABS/PRIVATE_TASK', str(root)),
                ('/ABS/TASK_PRIVATE_DIR', str(root)),
                ('/ABS/EXISTING_PRIVATE_OBSERVATION_DIR', str(output_dir)),
                ('/ABS/EXISTING_PRIVATE_INPUT_DIR', str(output_dir)),
                ('INTENT_AFTER_OBSERVATION_ID', observation_id),
            ):
                body = body.replace(old, new)
            script = self.tools_source + '\n' + r'''
const fsTest = await import('node:fs/promises');
const nodeRepl = {
  writes: [],
  write(value) { this.writes.push(String(value)); },
  async emitImage() {},
};
const result = await (async () => {
''' + extra_source + '\n' + body + r'''
})();
console.log(JSON.stringify(result));
'''
            env = dict(os.environ, INPUT_TEST_ROOT=str(root),
                       INPUT_TEST_DIR=str(output_dir))
            completed = subprocess.run(
                ['node', '--input-type=module', '-e', script],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0,
                             msg='node exit=%s\nstdout:\n%s\nstderr:\n%s' %
                             (completed.returncode, completed.stdout,
                              completed.stderr))
            return json.loads(completed.stdout), output_dir


class NotesInputHelperTests(NodeHelperRunner):
    def run_reveal(self, body):
        return self.run_helper(body, extra_source=self.reveal_source)

    def run_dispatch(self, body):
        return self.run_helper(
            body, extra_source=self.reveal_source + '\n' + self.dispatch_source)

    def test_cross_realm_error_preserves_numeric_code_full_message_and_own_fields_once(self):
        result, output_dir = self.run_helper(r'''
let calls = 0;
const message = 'long-error-' + 'x'.repeat(4096);
const foreignError = Object.create(null);
Object.defineProperty(foreignError, 'name', {value: 'ForeignError', enumerable: false});
Object.defineProperty(foreignError, 'message', {value: message, enumerable: false});
Object.defineProperty(foreignError, 'code', {value: -10005, enumerable: false});
Object.defineProperty(foreignError, 'window_id', {value: 'synthetic-window', enumerable: false});
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'foreign-error',
  request: {api: 'click', target: {x: 11, y: 17}},
  invoke: async () => { calls += 1; throw foreignError; },
});
const raw = JSON.parse(await fsTest.readFile(receipt.files.raw_return, 'utf8'));
const diagnostic = JSON.parse(await fsTest.readFile(receipt.files.diagnostic, 'utf8'));
return {calls, receipt, raw, diagnostic, messageLength: message.length};
''')
        self.assertEqual(result['calls'], 1)
        self.assertEqual(result['receipt']['raw_return']['kind'], 'ERROR')
        self.assertTrue(result['receipt']['raw_return']['complete'])
        self.assertEqual(result['raw']['error']['code'], -10005)
        self.assertIsInstance(result['raw']['error']['code'], int)
        self.assertEqual(result['raw']['error']['message'], 'long-error-' + 'x' * 4096)
        self.assertEqual(result['raw']['error']['own_fields']['window_id'], 'synthetic-window')
        self.assertEqual(result['diagnostic']['raw_return']['error_summary']['code'], -10005)
        self.assertTrue(result['diagnostic']['raw_return']['complete'])
        self.assertEqual(result['messageLength'], 4107)
        self.assertEqual(result['receipt']['request']['readback'], 'MATCH')
        self.assertEqual(result['receipt']['diagnostic']['readback'], 'MATCH')

    def test_success_reads_back_request_inside_single_invoke(self):
        result, _ = self.run_helper(r'''
let calls = 0;
let requestVisibleInsideInvoke = false;
const request = {api: 'click', target: {x: 31, y: 47}, modifiers: ['shift']};
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'success-once', request,
  invoke: async (actualRequest) => {
    calls += 1;
    const saved = JSON.parse(await fsTest.readFile(
      process.env.INPUT_TEST_DIR + '/success-once.input.request.json', 'utf8'));
    requestVisibleInsideInvoke = JSON.stringify(saved.request) === JSON.stringify(actualRequest) &&
      JSON.stringify(actualRequest) === JSON.stringify(request);
    return {success: true, receiptCode: 0};
  },
});
const raw = JSON.parse(await fsTest.readFile(receipt.files.raw_return, 'utf8'));
return {calls, requestVisibleInsideInvoke, receipt, raw};
''')
        self.assertEqual(result['calls'], 1)
        self.assertTrue(result['requestVisibleInsideInvoke'])
        self.assertEqual(result['receipt']['request']['readback'], 'MATCH')
        self.assertTrue(result['receipt']['raw_return']['complete'])
        self.assertEqual(result['raw']['value'], {'success': True, 'receiptCode': 0})
        self.assertEqual(result['receipt']['diagnostic']['readback'], 'MATCH')

    def test_top_level_undefined_uses_typed_raw_without_success_claim(self):
        result, _ = self.run_helper(r'''
let calls = 0;
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'top-level-undefined', request: {input_phase: 'NAVIGATION'},
  invoke: async () => { calls += 1; return undefined; },
});
const raw = JSON.parse(await fsTest.readFile(receipt.files.raw_return, 'utf8'));
const diagnostic = JSON.parse(await fsTest.readFile(receipt.files.diagnostic, 'utf8'));
return {calls, receipt, raw, diagnostic};
''')
        self.assertEqual(result['calls'], 1)
        self.assertEqual(result['receipt']['status'], 'INVOKED')
        self.assertEqual(result['receipt']['raw_return']['kind'],
                         'NATIVE_RETURN_UNDEFINED')
        self.assertEqual(result['receipt']['raw_return']['value_type'], 'undefined')
        self.assertTrue(result['receipt']['raw_return']['complete'])
        self.assertFalse(result['receipt']['receipt_is_os_event_trace'])
        self.assertEqual(result['raw'],
                         {'kind': 'NATIVE_RETURN_UNDEFINED',
                          'value_type': 'undefined'})
        self.assertNotIn('value', result['raw'])
        self.assertEqual(result['diagnostic']['raw_return']['kind'],
                         'NATIVE_RETURN_UNDEFINED')
        self.assertTrue(result['diagnostic']['raw_return']['complete'])

    def test_undefined_return_property_is_not_claimed_as_complete_raw(self):
        result, _ = self.run_helper(r'''
let calls = 0;
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'undefined-return', request: {api: 'read'},
  invoke: async () => { calls += 1; return {success: true, hidden: undefined}; },
});
const diagnostic = JSON.parse(await fsTest.readFile(receipt.files.diagnostic, 'utf8'));
return {calls, receipt, diagnostic};
''')
        self.assertEqual(result['calls'], 1)
        self.assertEqual(result['receipt']['status'], 'RAW_SERIALIZATION_FAILED')
        self.assertFalse(result['receipt']['raw_return']['complete'])
        self.assertIn('UNSUPPORTED_UNDEFINED',
                      result['receipt']['raw_return']['serialization_error']['message'])
        self.assertEqual(result['diagnostic']['status'], 'RAW_SERIALIZATION_FAILED')
        self.assertFalse(result['diagnostic']['raw_return']['complete'])
        self.assertEqual(result['receipt']['diagnostic']['readback'], 'MATCH')

    def test_request_serialization_failure_does_not_invoke_and_saves_gap(self):
        result, output_dir = self.run_helper(r'''
let calls = 0;
const request = {api: 'click'};
request.self = request;
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'circular-request', request,
  invoke: async () => { calls += 1; return {ok: true}; },
});
const diagnostic = JSON.parse(await fsTest.readFile(receipt.files.diagnostic, 'utf8'));
const requestExists = await fsTest.stat(receipt.files.request).then(() => true, () => false);
return {calls, receipt, diagnostic, requestExists};
''')
        self.assertEqual(result['calls'], 0)
        self.assertEqual(result['receipt']['status'], 'REQUEST_SERIALIZATION_FAILED')
        self.assertEqual(result['receipt']['diagnostic']['readback'], 'MATCH')
        self.assertEqual(result['diagnostic']['status'], 'REQUEST_SERIALIZATION_FAILED')
        self.assertFalse(result['requestExists'])

    def test_circular_raw_return_saves_serializable_incomplete_diagnostic(self):
        result, output_dir = self.run_helper(r'''
let calls = 0;
const circular = {ok: true};
circular.self = circular;
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'circular-return', request: {api: 'read'},
  invoke: async () => { calls += 1; return circular; },
});
const diagnostic = JSON.parse(await fsTest.readFile(receipt.files.diagnostic, 'utf8'));
const rawExists = await fsTest.stat(receipt.files.raw_return).then(() => true, () => false);
return {calls, receipt, diagnostic, rawExists};
''')
        self.assertEqual(result['calls'], 1)
        self.assertEqual(result['receipt']['status'], 'RAW_SERIALIZATION_FAILED')
        self.assertFalse(result['receipt']['raw_return']['complete'])
        self.assertIn('循環', result['receipt']['raw_return']['gap'])
        self.assertEqual(result['diagnostic']['status'], 'RAW_SERIALIZATION_FAILED')
        self.assertFalse(result['diagnostic']['raw_return']['complete'])
        self.assertEqual(result['receipt']['diagnostic']['readback'], 'MATCH')
        self.assertFalse(result['rawExists'])

    def test_request_filename_collision_does_not_invoke_or_overwrite(self):
        result, _ = self.run_helper(r'''
let calls = 0;
const file = process.env.INPUT_TEST_DIR + '/collision.input.request.json';
await fsTest.writeFile(file, 'original sentinel', {flag: 'wx'});
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'collision', request: {api: 'click'},
  invoke: async () => { calls += 1; return {ok: true}; },
});
return {calls, receipt, saved: await fsTest.readFile(file, 'utf8')};
''')
        self.assertEqual(result['calls'], 0)
        self.assertEqual(result['saved'], 'original sentinel')
        self.assertEqual(result['receipt']['status'], 'REQUEST_PERSIST_FAILED')
        self.assertEqual(result['receipt']['request']['write'], 'FAILED')

    def test_readback_mismatch_prevents_invoke_and_is_diagnosed(self):
        result, _ = self.run_helper(r'''
let calls = 0;
let readbacks = 0;
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'readback-mismatch', request: {api: 'click'},
  invoke: async () => { calls += 1; return {ok: true}; },
  readbackExact: async (file, bytes) => {
    readbacks += 1;
    return readbacks === 1 ? {status: 'MISMATCH', saved_bytes: 0,
      saved_sha256: '0'.repeat(64)} : evidenceTools.readbackExact(file, bytes);
  },
});
const diagnostic = JSON.parse(await fsTest.readFile(receipt.files.diagnostic, 'utf8'));
return {calls, readbacks, receipt, diagnostic};
''')
        self.assertEqual(result['calls'], 0)
        self.assertEqual(result['receipt']['status'], 'REQUEST_READBACK_FAILED')
        self.assertEqual(result['receipt']['request']['readback'], 'MISMATCH')
        self.assertEqual(result['diagnostic']['status'], 'REQUEST_READBACK_FAILED')
        self.assertEqual(result['receipt']['diagnostic']['readback'], 'MATCH')

    def test_diagnostic_filename_collision_is_reported_incomplete_without_overwrite(self):
        result, _ = self.run_helper(r'''
let calls = 0;
const diagnosticFile = process.env.INPUT_TEST_DIR + '/diagnostic-collision.input.diagnostic.json';
await fsTest.writeFile(diagnosticFile, 'keep diagnostic sentinel', {flag: 'wx'});
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'diagnostic-collision', request: {api: 'read'},
  invoke: async () => { calls += 1; return {success: true}; },
});
return {calls, receipt, saved: await fsTest.readFile(diagnosticFile, 'utf8')};
''')
        self.assertEqual(result['calls'], 1)
        self.assertEqual(result['saved'], 'keep diagnostic sentinel')
        self.assertEqual(result['receipt']['diagnostic']['status'], 'FAILED')
        self.assertFalse(result['receipt']['diagnostic']['complete'])
        self.assertIn('DIAGNOSTIC_PERSISTENCE_INCOMPLETE',
                      result['receipt']['blockers'])

    def test_raw_filename_collision_preserves_existing_file_and_marks_incomplete(self):
        result, _ = self.run_helper(r'''
let calls = 0;
const rawFile = process.env.INPUT_TEST_DIR + '/raw-collision.input.raw.json';
await fsTest.writeFile(rawFile, 'keep original', {flag: 'wx'});
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'raw-collision', request: {api: 'click'},
  invoke: async () => { calls += 1; return {ok: true}; },
});
return {calls, receipt, saved: await fsTest.readFile(rawFile, 'utf8')};
''')
        self.assertEqual(result['calls'], 1)
        self.assertEqual(result['saved'], 'keep original')
        self.assertEqual(result['receipt']['raw_return']['write'], 'FAILED')
        self.assertFalse(result['receipt']['raw_return']['complete'])
        self.assertIn('RAW_RETURN_INCOMPLETE', result['receipt']['blockers'])

    def test_symbol_keyed_error_field_is_reported_as_incomplete_without_losing_other_fields(self):
        result, _ = self.run_helper(r'''
let calls = 0;
const error = Object.create(null);
Object.defineProperty(error, 'name', {value: 'ForeignError', enumerable: false});
Object.defineProperty(error, 'message', {value: 'symbol-error', enumerable: false});
Object.defineProperty(error, 'code', {value: 17, enumerable: false});
Object.defineProperty(error, 'request_id', {value: 'keep-this-field', enumerable: false});
const symbolKey = Symbol('private-trace-key');
Object.defineProperty(error, symbolKey, {
  value: 'do-not-invent-a-string-key', enumerable: false,
});
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'symbol-keyed-error',
  request: {api: 'read'},
  invoke: async () => { calls += 1; throw error; },
});
const raw = JSON.parse(await fsTest.readFile(receipt.files.raw_return, 'utf8'));
const diagnostic = JSON.parse(await fsTest.readFile(receipt.files.diagnostic, 'utf8'));
return {calls, receipt, raw, diagnostic};
''')
        snapshot = result['raw']['error']
        summary = result['diagnostic']['raw_return']['error_summary']
        self.assertEqual(result['calls'], 1)
        self.assertEqual(snapshot['code'], 17)
        self.assertEqual(snapshot['message'], 'symbol-error')
        self.assertEqual(snapshot['own_fields']['request_id'], 'keep-this-field')
        self.assertFalse(snapshot['fields_complete'])
        self.assertEqual(snapshot['field_gaps'], ['SYMBOL_KEYED_OWN_FIELDS_UNCAPTURED:1'])
        self.assertFalse(result['receipt']['raw_return']['complete'])
        self.assertIn('RAW_RETURN_INCOMPLETE', result['receipt']['blockers'])
        self.assertFalse(summary['fields_complete'])
        self.assertEqual(summary['field_gaps'], ['SYMBOL_KEYED_OWN_FIELDS_UNCAPTURED:1'])
        self.assertEqual(summary['code'], 17)
        self.assertNotIn('Symbol(private-trace-key)', snapshot['own_fields'])

    def test_reveal_composition_reads_request_then_clicks_and_captures_before_raw(self):
        result, _ = self.run_reveal(r'''
let clicks = 0;
let captures = 0;
let requestReadable = false;
let rawAtCapture = true;
const afterBytes = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x01, 0x02]);
const rawPath = process.env.INPUT_TEST_DIR + '/reveal-order.input.raw.json';
const app = {
  async click(target) {
    clicks += 1;
    const saved = JSON.parse(await fsTest.readFile(
      process.env.INPUT_TEST_DIR + '/reveal-order.input.request.json', 'utf8'));
    requestReadable = saved.request.input_phase === 'NAVIGATION' &&
      JSON.stringify(saved.request.prepared_target) === JSON.stringify(target);
    return {native_code: 0};
  },
  async getAXStateAndScreenshot() {
    captures += 1;
    rawAtCapture = await fsTest.stat(rawPath).then(() => true, () => false);
    return {state: '{"role":"AXWindow"}', screenshot: afterBytes};
  },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'reveal-order',
  observationId: 'reveal-order-after',
  request: {input_phase: 'NAVIGATION', prepared_target: [12, 34]},
  app,
});
const rawAtReturn = await fsTest.stat(rawPath).then(() => true, () => false);
return {clicks, captures, requestReadable, rawAtCapture, rawAtReturn, run};
''')
        run = result['run']
        self.assertEqual(result['clicks'], 1)
        self.assertEqual(result['captures'], 1)
        self.assertTrue(result['requestReadable'])
        self.assertFalse(result['rawAtCapture'])
        self.assertTrue(result['rawAtReturn'])
        self.assertEqual(run['inputReceipt']['status'], 'INVOKED')
        self.assertEqual(run['inputReceipt']['request']['readback'], 'MATCH')
        self.assertEqual(run['inputReceipt']['raw_return']['readback'], 'MATCH')
        self.assertEqual(run['inputReceipt']['raw_return']['kind'], 'RETURN')
        self.assertTrue(run['afterObservation']['ready_for_bind'])
        self.assertFalse(run['fail_closed'])
        self.assertEqual(run['hostCalls']['input_call_sequence'], 1)
        self.assertEqual(run['hostCalls']['capture_call_sequence'], 2)
        self.assertNotEqual(run['hostCalls']['input_call_started_at'], 'UNKNOWN')
        self.assertNotEqual(run['hostCalls']['input_call_returned_at'], 'UNKNOWN')
        self.assertNotEqual(run['hostCalls']['capture_call_started_at'], 'UNKNOWN')
        self.assertNotEqual(run['hostCalls']['capture_call_returned_at'], 'UNKNOWN')
        self.assertEqual(run['hostCalls']['os_event_time'], 'UNKNOWN')

    def test_reveal_undefined_click_return_keeps_typed_raw_and_saves_after(self):
        result, _ = self.run_reveal(r'''
let captures = 0;
const app = {
  async click() { return undefined; },
  async getAXStateAndScreenshot() {
    captures += 1;
    return {
      state: '{"role":"AXWindow"}',
      screenshot: new Uint8Array([0x89, 0x50, 0x4e, 0x47]),
    };
  },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'reveal-undefined',
  observationId: 'reveal-undefined-after',
  request: {input_phase: 'NAVIGATION', prepared_target: [1, 2]},
  app,
});
const raw = JSON.parse(await fsTest.readFile(
  run.inputReceipt.files.raw_return, 'utf8'));
return {captures, run, raw};
''')
        self.assertEqual(result['captures'], 1)
        self.assertEqual(result['raw'],
                         {'kind': 'NATIVE_RETURN_UNDEFINED',
                          'value_type': 'undefined'})
        self.assertEqual(result['run']['inputReceipt']['raw_return']['kind'],
                         'NATIVE_RETURN_UNDEFINED')
        self.assertTrue(result['run']['inputReceipt']['raw_return']['complete'])
        self.assertTrue(result['run']['afterObservation']['ready_for_bind'])
        self.assertFalse(result['run']['fail_closed'])

    def test_reveal_capture_error_preserves_input_return_and_never_reclicks(self):
        result, _ = self.run_reveal(r'''
let clicks = 0;
let captures = 0;
const captureError = new Error('synthetic capture failed');
captureError.code = 'CAPTURE_TEST';
const app = {
  async click() { clicks += 1; return {native_code: 7}; },
  async getAXStateAndScreenshot() { captures += 1; throw captureError; },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'reveal-capture-error',
  observationId: 'reveal-capture-error-after',
  request: {input_phase: 'NAVIGATION', prepared_target: [3, 4]},
  app,
});
const raw = JSON.parse(await fsTest.readFile(
  run.inputReceipt.files.raw_return, 'utf8'));
const diagnostic = JSON.parse(await fsTest.readFile(
  run.afterObservation.files.diagnostic, 'utf8'));
return {clicks, captures, run, raw, diagnostic};
''')
        self.assertEqual(result['clicks'], 1)
        self.assertEqual(result['captures'], 1)
        self.assertEqual(result['raw']['kind'], 'RETURN')
        self.assertEqual(result['raw']['value'], {'native_code': 7})
        self.assertTrue(result['run']['inputReceipt']['raw_return']['complete'])
        self.assertFalse(result['run']['afterObservation']['ready_for_bind'])
        self.assertTrue(result['run']['fail_closed'])
        self.assertEqual(result['run']['afterObservation']['blockers'],
                         ['CAPTURE:FAILED'])
        self.assertEqual(result['diagnostic']['blockers'], ['CAPTURE:FAILED'])
        self.assertEqual(result['run']['hostCalls']['capture_call_sequence'], 2)

    def test_reveal_input_error_preserves_raw_and_skips_capture_and_after(self):
        result, _ = self.run_reveal(r'''
let clicks = 0;
let captures = 0;
const inputError = new Error('synthetic click failed');
inputError.code = 91;
const app = {
  async click() { clicks += 1; throw inputError; },
  async getAXStateAndScreenshot() { captures += 1; throw new Error('unexpected'); },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'reveal-input-error',
  observationId: 'reveal-input-error-after',
  request: {input_phase: 'NAVIGATION', prepared_target: [5, 6]},
  app,
});
const raw = JSON.parse(await fsTest.readFile(
  run.inputReceipt.files.raw_return, 'utf8'));
const afterExists = await fsTest.stat(
  process.env.INPUT_TEST_DIR + '/reveal-input-error-after.diagnostic.json')
  .then(() => true, () => false);
return {clicks, captures, run, raw, afterExists};
''')
        self.assertEqual(result['clicks'], 1)
        self.assertEqual(result['captures'], 0)
        self.assertEqual(result['raw']['kind'], 'ERROR')
        self.assertEqual(result['raw']['error']['code'], 91)
        self.assertEqual(result['run']['inputReceipt']['raw_return']['kind'],
                         'ERROR')
        self.assertIsNone(result['run']['afterObservation'])
        self.assertTrue(result['run']['fail_closed'])
        self.assertEqual(result['run']['hostCalls']['capture_call_sequence'],
                         'NOT_RUN')
        self.assertFalse(result['afterExists'])

    def test_reveal_after_observation_saves_same_bytes_without_recapture(self):
        result, _ = self.run_reveal(r'''
let captures = 0;
const expected = [0x89, 0x50, 0x4e, 0x47, 0x00, 0x2a];
const app = {
  async click() { return {native_code: 0}; },
  async getAXStateAndScreenshot() {
    captures += 1;
    return {state: '{"role":"AXWindow"}', screenshot: new Uint8Array(expected)};
  },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'reveal-same-bytes',
  observationId: 'reveal-same-bytes-after',
  request: {input_phase: 'NAVIGATION', prepared_target: [7, 8]},
  app,
});
const saved = Array.from(await fsTest.readFile(
  run.afterObservation.files.screenshot));
return {captures, expected, saved, run};
''')
        self.assertEqual(result['captures'], 1)
        self.assertEqual(result['saved'], result['expected'])
        self.assertTrue(result['run']['afterObservation']['ready_for_bind'])
        self.assertFalse(result['run']['fail_closed'])

    def test_deferred_candidate_request_is_readback_before_input_and_slot_cannot_reenter(self):
        result, _ = self.run_reveal(r'''
let clicks = 0;
let captures = 0;
let requestSeenAtClick = null;
const operationId = 'notes-reveal-c2-attempt-delayed';
const requestPath = process.env.INPUT_TEST_DIR +
  '/notes-reveal-c2-attempt-delayed.input.request.json';
const priorRef = {
  path: process.env.INPUT_TEST_ROOT + '/synthetic-candidate-1.receipt.json',
  bytes: 1,
  sha256: 'a'.repeat(64),
};
const request = {
  input_phase: 'NAVIGATION',
  attempt_id: 'attempt-delayed',
  intent_event_ref: 'intent-event-synthetic',
  navigation_kind: 'selected-filmstrip-safe-edge',
  reveal_candidate_id: 'candidate-2-synthetic',
  reveal_scope_ref: 'list-post-media-synthetic',
  candidate_ordinal: 2,
  prior_candidate_refs: [priorRef],
  budget_before: 1,
  budget_after: 2,
  rearm_preconditions_ref: 'synthetic-gate-ref',
  rearm_new_information_ref: 'synthetic-control-lost-ref',
  before_screenshot_ref: 'synthetic-before-screenshot-ref',
  before_ax_ref: 'synthetic-before-ax-ref',
  prepared_target: [31, 47],
};
const app = {
  async click(target) {
    clicks += 1;
    const saved = JSON.parse(await fsTest.readFile(requestPath, 'utf8'));
    requestSeenAtClick = saved.request;
    return {target};
  },
  async getAXStateAndScreenshot() {
    captures += 1;
    return {
      state: '{"role":"AXWindow"}',
      screenshot: new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x01]),
    };
  },
};
const common = {
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId,
  app,
};
const first = await persistRevealWithDirectAfter({
  ...common,
  observationId: 'deferred-candidate-after-1',
  request,
});
const second = await persistRevealWithDirectAfter({
  ...common,
  observationId: 'deferred-candidate-after-2',
  request: {...request, prepared_target: [32, 48]},
});
const saved = JSON.parse(await fsTest.readFile(requestPath, 'utf8'));
return {clicks, captures, first, second, requestSeenAtClick, saved};
''')
        self.assertEqual(result['clicks'], 1)
        self.assertEqual(result['captures'], 1)
        self.assertEqual(result['first']['inputReceipt']['request']['readback'], 'MATCH')
        self.assertEqual(result['first']['inputReceipt']['status'], 'INVOKED')
        self.assertEqual(result['first']['inputReceipt']['raw_return']['readback'], 'MATCH')
        self.assertTrue(result['first']['afterObservation']['ready_for_bind'])
        self.assertFalse(result['first']['fail_closed'])
        self.assertEqual(result['requestSeenAtClick']['attempt_id'], 'attempt-delayed')
        self.assertEqual(result['requestSeenAtClick']['intent_event_ref'],
                         'intent-event-synthetic')
        self.assertEqual(result['requestSeenAtClick']['candidate_ordinal'], 2)
        self.assertEqual(result['requestSeenAtClick']['budget_before'], 1)
        self.assertEqual(result['requestSeenAtClick']['budget_after'], 2)
        self.assertEqual(result['requestSeenAtClick']['prior_candidate_refs'],
                         result['saved']['request']['prior_candidate_refs'])
        self.assertEqual(result['second']['inputReceipt']['status'],
                         'REQUEST_PERSIST_FAILED')
        self.assertIsNone(result['second']['afterObservation'])
        self.assertTrue(result['second']['fail_closed'])

    def test_deferred_candidate_capture_error_has_no_after_source_for_download(self):
        result, _ = self.run_reveal(r'''
let clicks = 0;
let captures = 0;
const captureError = new Error('synthetic deferred capture failed');
captureError.code = 'DEFERRED_CAPTURE_TEST';
const app = {
  async click() { clicks += 1; return {native_code: 0}; },
  async getAXStateAndScreenshot() { captures += 1; throw captureError; },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'notes-reveal-c2-attempt-capture-error',
  observationId: 'deferred-candidate-capture-error-after',
  request: {
    input_phase: 'NAVIGATION',
    attempt_id: 'attempt-capture-error',
    intent_event_ref: 'intent-event-capture-error',
    candidate_ordinal: 2,
    prior_candidate_refs: ['synthetic-candidate-1'],
    budget_before: 1,
    budget_after: 2,
    prepared_target: [41, 57],
  },
  app,
});
const screenshotExists = await fsTest.stat(
  run.afterObservation.files.screenshot).then(() => true, () => false);
return {clicks, captures, run, screenshotExists};
''')
        self.assertEqual(result['clicks'], 1)
        self.assertEqual(result['captures'], 1)
        self.assertTrue(result['run']['fail_closed'])
        self.assertFalse(result['run']['afterObservation']['ready_for_bind'])
        self.assertEqual(result['run']['afterObservation']['blockers'],
                         ['CAPTURE:FAILED'])
        self.assertFalse(result['screenshotExists'])

    def test_deferred_candidate_same_after_bytes_feed_grounded_helper_once(self):
        result, _ = self.run_reveal(r'''
let revealClicks = 0;
let revealCaptures = 0;
let downloadClicks = 0;
const afterBytes = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const revealApp = {
  async click() { revealClicks += 1; return {native_code: 0}; },
  async getAXStateAndScreenshot() {
    revealCaptures += 1;
    return {
      state: '{"role":"AXWindow","marker":"same-after"}',
      screenshot: new Uint8Array(afterBytes),
    };
  },
};
const revealRun = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'notes-reveal-c2-attempt-download-handoff',
  observationId: 'deferred-candidate-download-handoff-after',
  request: {
    input_phase: 'NAVIGATION',
    attempt_id: 'attempt-download-handoff',
    intent_event_ref: 'intent-event-download-handoff',
    candidate_ordinal: 2,
    prior_candidate_refs: ['synthetic-candidate-1'],
    budget_before: 1,
    budget_after: 2,
    prepared_target: [51, 67],
  },
  app: revealApp,
});
const screenshotAsset = revealRun.afterObservation.assets.screenshot;
const axAsset = revealRun.afterObservation.assets.ax;
const screenshotRef = {
  path: screenshotAsset.path,
  bytes: screenshotAsset.bytes,
  sha256: screenshotAsset.sha256,
};
const axRef = {path: axAsset.path, bytes: axAsset.bytes, sha256: axAsset.sha256};
const sourceBytes = new Uint8Array(await fsTest.readFile(screenshotRef.path));
const downloadRequest = {
  input_phase: 'DOWNLOAD_CONTROL',
  attempt_id: 'attempt-download-handoff',
  app_window_binding: {
    app_bundle_id: 'jp.naver.line.mac',
    window_id: 'synthetic-window',
  },
  source_observation: screenshotRef,
  source_observation_ref: screenshotRef,
  mapping_evidence_ref: axRef,
  mapping_status: 'MATCH',
  observation_order: 'PRE_INPUT',
  grounding_conclusion: 'PASS_TO_INPUT',
  candidate_point_relation: 'INSIDE',
  coordinate_space_match: 'MATCH',
  control_region_coord_space: 'SCREEN_POINTS',
  target_coord_space: 'SCREEN_POINTS',
  control_region: [20, 30, 80, 90],
  candidate_point: [50, 60],
  prepared_target: [50, 60],
};
const downloadApp = {async click(target) { downloadClicks += 1; return {target}; }};
const downloadOperationId = 'notes-download-attempt-download-handoff';
const firstDownload = await evidenceTools.persistGroundedDownloadClick({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: downloadOperationId,
  request: downloadRequest,
  source_observation_bytes: sourceBytes,
  app: downloadApp,
});
const secondDownload = await evidenceTools.persistGroundedDownloadClick({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: downloadOperationId,
  request: {...downloadRequest, candidate_point: [51, 61], prepared_target: [51, 61]},
  source_observation_bytes: sourceBytes,
  app: downloadApp,
});
const savedAfterBytes = Array.from(await fsTest.readFile(screenshotRef.path));
return {
  revealClicks, revealCaptures, revealRun, sourceBytes: Array.from(sourceBytes),
  savedAfterBytes, screenshotAsset, downloadClicks, firstDownload, secondDownload,
};
''')
        self.assertEqual(result['revealClicks'], 1)
        self.assertEqual(result['revealCaptures'], 1)
        self.assertFalse(result['revealRun']['fail_closed'])
        self.assertTrue(result['revealRun']['afterObservation']['ready_for_bind'])
        self.assertEqual(result['savedAfterBytes'], result['sourceBytes'])
        self.assertEqual(result['firstDownload']['status'], 'INVOKED')
        self.assertEqual(result['firstDownload']['source_observation_readback']['status'],
                         'MATCH')
        self.assertEqual(result['firstDownload']['mapping_evidence_readback']['status'],
                         'MATCH')
        self.assertEqual(result['downloadClicks'], 1)
        self.assertEqual(result['secondDownload']['status'], 'REQUEST_PERSIST_FAILED')
        self.assertEqual(result['downloadClicks'], 1)

    def test_reveal_request_persist_gate_blocks_click_capture_and_after(self):
        result, _ = self.run_reveal(r'''
let clicks = 0;
let captures = 0;
const requestPath = process.env.INPUT_TEST_DIR + '/reveal-request-gate.input.request.json';
await fsTest.writeFile(requestPath, 'keep request sentinel', {flag: 'wx'});
const app = {
  async click() { clicks += 1; return {native_code: 0}; },
  async getAXStateAndScreenshot() { captures += 1; throw new Error('unexpected'); },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'reveal-request-gate',
  observationId: 'reveal-request-gate-after',
  request: {input_phase: 'NAVIGATION', prepared_target: [9, 10]},
  app,
});
const afterExists = await fsTest.stat(
  process.env.INPUT_TEST_DIR + '/reveal-request-gate-after.diagnostic.json')
  .then(() => true, () => false);
return {
  clicks, captures, run, afterExists,
  saved: await fsTest.readFile(requestPath, 'utf8'),
};
''')
        self.assertEqual(result['clicks'], 0)
        self.assertEqual(result['captures'], 0)
        self.assertEqual(result['saved'], 'keep request sentinel')
        self.assertEqual(result['run']['inputReceipt']['status'],
                         'REQUEST_PERSIST_FAILED')
        self.assertIsNone(result['run']['afterObservation'])
        self.assertTrue(result['run']['fail_closed'])
        self.assertFalse(result['afterExists'])

    def test_reveal_partial_input_persistence_saves_after_and_fails_closed(self):
        result, _ = self.run_reveal(r'''
let clicks = 0;
let captures = 0;
const expected = [0x89, 0x50, 0x4e, 0x47];
const rawPath = process.env.INPUT_TEST_DIR + '/reveal-partial.input.raw.json';
await fsTest.writeFile(rawPath, 'keep raw sentinel', {flag: 'wx'});
const app = {
  async click() { clicks += 1; return {native_code: 0}; },
  async getAXStateAndScreenshot() {
    captures += 1;
    return {
      state: '{"role":"AXWindow"}',
      screenshot: new Uint8Array(expected),
    };
  },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'reveal-partial',
  observationId: 'reveal-partial-after',
  request: {input_phase: 'NAVIGATION', prepared_target: [11, 12]},
  app,
});
const savedScreenshot = Array.from(await fsTest.readFile(
  run.afterObservation.files.screenshot));
return {
  clicks, captures, run, expected, savedScreenshot,
  saved: await fsTest.readFile(rawPath, 'utf8'),
};
''')
        self.assertEqual(result['clicks'], 1)
        self.assertEqual(result['captures'], 1)
        self.assertEqual(result['saved'], 'keep raw sentinel')
        self.assertEqual(result['run']['inputReceipt']['raw_return']['write'],
                         'FAILED')
        self.assertFalse(result['run']['inputReceipt']['raw_return']['complete'])
        self.assertTrue(result['run']['afterObservation']['ready_for_bind'])
        self.assertEqual(result['savedScreenshot'], result['expected'])
        self.assertTrue(result['run']['fail_closed'])

    def test_reveal_diagnostic_persistence_failure_saves_after_and_fails_closed(self):
        result, _ = self.run_reveal(r'''
let clicks = 0;
let captures = 0;
const expected = [0x89, 0x50, 0x4e, 0x47, 0x2a];
const diagnosticPath =
  process.env.INPUT_TEST_DIR + '/reveal-diagnostic-partial.input.diagnostic.json';
await fsTest.writeFile(diagnosticPath, 'keep diagnostic sentinel', {flag: 'wx'});
const app = {
  async click() { clicks += 1; return {native_code: 0}; },
  async getAXStateAndScreenshot() {
    captures += 1;
    return {
      state: '{"role":"AXWindow"}',
      screenshot: new Uint8Array(expected),
    };
  },
};
const run = await persistRevealWithDirectAfter({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  observationDir: process.env.INPUT_TEST_DIR,
  operationId: 'reveal-diagnostic-partial',
  observationId: 'reveal-diagnostic-partial-after',
  request: {input_phase: 'NAVIGATION', prepared_target: [13, 14]},
  app,
});
const savedScreenshot = Array.from(await fsTest.readFile(
  run.afterObservation.files.screenshot));
return {
  clicks, captures, run, expected, savedScreenshot,
  savedDiagnostic: await fsTest.readFile(diagnosticPath, 'utf8'),
};
''')
        self.assertEqual(result['clicks'], 1)
        self.assertEqual(result['captures'], 1)
        self.assertEqual(result['savedDiagnostic'], 'keep diagnostic sentinel')
        self.assertEqual(result['run']['inputReceipt']['raw_return']['readback'],
                         'MATCH')
        self.assertTrue(result['run']['inputReceipt']['raw_return']['complete'])
        self.assertEqual(result['run']['inputReceipt']['diagnostic']['status'],
                         'FAILED')
        self.assertFalse(result['run']['inputReceipt']['diagnostic']['complete'])
        self.assertTrue(result['run']['afterObservation']['ready_for_bind'])
        self.assertEqual(result['savedScreenshot'], result['expected'])
        self.assertTrue(result['run']['fail_closed'])

    def test_observation_success_persists_final_ready_state_before_readback(self):
        result, _ = self.run_helper(r'''
const screenshotBytes = new Uint8Array([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x01,
]);
const observation = await evidenceTools.persistObservation({
  taskDir: process.env.INPUT_TEST_ROOT,
  observationDir: process.env.INPUT_TEST_DIR,
  observationId: 'observation-ready-success',
  capture: {state: '{"role":"AXWindow"}', screenshot: screenshotBytes},
});
const diagnostic = JSON.parse(await fsTest.readFile(
  observation.files.diagnostic, 'utf8'));
const axText = await fsTest.readFile(observation.files.ax, 'utf8');
const screenshotReadback = Array.from(
  await fsTest.readFile(observation.files.screenshot));
return {observation, diagnostic, axText, screenshotReadback};
''')
        observation = result['observation']
        diagnostic = result['diagnostic']
        self.assertTrue(observation['ready_for_bind'])
        self.assertEqual(observation['blockers'], [])
        self.assertTrue(diagnostic['ready_for_bind'])
        self.assertEqual(diagnostic['blockers'], [])
        self.assertEqual(observation['metadata_persistence']['write'], 'WRITTEN')
        self.assertEqual(observation['metadata_persistence']['readback'], 'MATCH')
        self.assertEqual(diagnostic['stages']['AX_PERSISTENCE']['status'], 'MATCH')
        self.assertEqual(
            diagnostic['stages']['SCREENSHOT_PERSISTENCE']['status'], 'MATCH')
        self.assertEqual(result['axText'], '{"role":"AXWindow"}')
        self.assertEqual(result['screenshotReadback'],
                         [0x89, 0x50, 0x4e, 0x47, 0x0d,
                          0x0a, 0x1a, 0x0a, 0x00, 0x01])

    def test_observation_failure_persists_ready_false_with_blockers(self):
        result, _ = self.run_helper(r'''
const observation = await evidenceTools.persistObservation({
  taskDir: process.env.INPUT_TEST_ROOT,
  observationDir: process.env.INPUT_TEST_DIR,
  observationId: 'observation-ready-failure',
  captureError: {code: 'SYNTHETIC_CAPTURE_FAILED'},
});
const diagnostic = JSON.parse(await fsTest.readFile(
  observation.files.diagnostic, 'utf8'));
return {observation, diagnostic};
''')
        observation = result['observation']
        diagnostic = result['diagnostic']
        self.assertFalse(observation['ready_for_bind'])
        self.assertEqual(observation['blockers'], ['CAPTURE:FAILED'])
        self.assertFalse(diagnostic['ready_for_bind'])
        self.assertEqual(diagnostic['blockers'], ['CAPTURE:FAILED'])
        self.assertEqual(observation['metadata_persistence']['write'], 'WRITTEN')
        self.assertEqual(observation['metadata_persistence']['readback'], 'MATCH')

    def test_observation_diagnostic_collision_keeps_outer_failure_and_original(self):
        result, _ = self.run_helper(r'''
const diagnosticPath = process.env.INPUT_TEST_DIR +
  '/observation-diagnostic-collision.diagnostic.json';
await fsTest.writeFile(diagnosticPath, 'keep original diagnostic', {flag: 'wx'});
const observation = await evidenceTools.persistObservation({
  taskDir: process.env.INPUT_TEST_ROOT,
  observationDir: process.env.INPUT_TEST_DIR,
  observationId: 'observation-diagnostic-collision',
  capture: {
    state: '{"role":"AXWindow"}',
    screenshot: new Uint8Array([0x89, 0x50, 0x4e, 0x47]),
  },
});
return {
  observation,
  saved: await fsTest.readFile(diagnosticPath, 'utf8'),
};
''')
        observation = result['observation']
        self.assertFalse(observation['ready_for_bind'])
        self.assertEqual(observation['blockers'],
                         ['DIAGNOSTIC_PERSISTENCE:FAILED'])
        self.assertEqual(observation['metadata_persistence']['write'], 'FAILED')
        self.assertEqual(observation['metadata_persistence']['readback'], 'NOT_RUN')
        self.assertEqual(result['saved'], 'keep original diagnostic')

    def test_observation_ax_no_change_stub_persists_raw_and_fails_closed(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
const counters = {};
const app = dispatchReadinessApp(counters);
const cases = [
  {
    observationId: 'ax-no-change-line',
    state: 'There has been no change in the accessibility tree for ' +
      'Window: "LINE".\nThe focused UI element is 39 文字',
  },
  {
    observationId: 'ax-no-change-empty-title',
    state: 'There has been no change in the accessibility tree for ' +
      'Window: "".',
  },
];
const results = [];
for (const item of cases) {
  const observation = await evidenceTools.persistObservation({
    taskDir: process.env.INPUT_TEST_ROOT,
    observationDir: process.env.INPUT_TEST_DIR,
    observationId: item.observationId,
    capture: {
      state: item.state,
      screenshot: dispatchFreshCapture(item.observationId).screenshot,
    },
  });
  const diagnostic = JSON.parse(await fsTest.readFile(
    observation.files.diagnostic, 'utf8'));
  results.push({
    observationId: item.observationId,
    expectedState: item.state,
    observation,
    diagnostic,
    axText: await fsTest.readFile(observation.files.ax, 'utf8'),
    screenshotBytes: Array.from(
      await fsTest.readFile(observation.files.screenshot)),
    readiness: notesIntentDispatch.checkDownloadReadiness({
      app,
      observation,
      windowBinding: dispatchWindowBinding(),
      branch: 'DIRECT',
      decision: dispatchDirectReadinessDecision(observation),
    }),
  });
}
return {results, counters};
''')
        self.assertEqual(result['counters'].get('clicks', 0), 0)
        self.assertEqual(result['counters'].get('captures', 0), 0)
        for item in result['results']:
            with self.subTest(case=item['observationId']):
                observation = item['observation']
                stages = observation['stages']
                self.assertEqual(item['axText'], item['expectedState'])
                self.assertTrue(item['screenshotBytes'])
                self.assertEqual(stages['AX']['status'], 'DIFF_NO_CHANGE')
                self.assertFalse(stages['AX']['full_tree'])
                self.assertTrue(stages['AX']['diff_only'])
                self.assertTrue(stages['AX']['stale_index_warning'])
                self.assertEqual(stages['AX']['utf8_bytes'],
                                 len(item['expectedState'].encode('utf-8')))
                self.assertEqual(stages['AX_PERSISTENCE']['status'], 'MATCH')
                self.assertIn('AX:DIFF_NO_CHANGE', observation['blockers'])
                self.assertFalse(observation['ready_for_bind'])
                self.assertEqual(item['diagnostic']['stages'], stages)
                self.assertFalse(item['diagnostic']['ready_for_bind'])
                self.assertEqual(item['readiness']['status'], 'STOP')
                self.assertIn('DOWNLOAD_OBSERVATION_INVALID',
                              item['readiness']['blockers'])

    def test_observation_ax_no_change_guard_avoids_false_positives_and_rejects_whitespace(self):
        result, _ = self.run_helper(r'''
const cases = [
  {
    observationId: 'ax-phrase-in-tree',
    expectedStatus: 'OK',
    state: 'Window: "LINE".\n0 標準視窗\n1 列表\n' +
      '\t2 row 文字 There has been no change in the accessibility tree\n' +
      '\t3 row\n',
  },
  {
    observationId: 'ax-phrase-in-json',
    expectedStatus: 'OK',
    state: '{"role":"AXWindow","text":"There has been no change in the ' +
      'accessibility tree"}',
  },
  {
    observationId: 'ax-short-popup-tree',
    expectedStatus: 'OK',
    state: 'Window: "", App: LINE.\n0 浮動視窗 Secondary Actions: Raise\n' +
      '1 menu bar\n\t2 LINE\n\t3 顯示\n\t4 好友\n\t5 視窗\n\t6 常見問題\n\n' +
      'The focused UI element is 0 浮動視窗 Secondary Actions: Raise',
  },
  {
    observationId: 'ax-stub-followed-by-numbered-node',
    expectedStatus: 'OK',
    state: 'There has been no change in the accessibility tree for ' +
      'Window: "LINE".\n0 標準視窗',
  },
  {
    observationId: 'ax-whitespace',
    expectedStatus: 'EMPTY',
    state: ' \n\t ',
  },
];
const results = [];
for (const item of cases) {
  const observation = await evidenceTools.persistObservation({
    taskDir: process.env.INPUT_TEST_ROOT,
    observationDir: process.env.INPUT_TEST_DIR,
    observationId: item.observationId,
    capture: {
      state: item.state,
      screenshot: new TextEncoder().encode('AX-GUARD:' + item.observationId),
    },
  });
  results.push({
    observationId: item.observationId,
    expectedStatus: item.expectedStatus,
    stateBytes: new TextEncoder().encode(item.state).length,
    observation,
  });
}
return {results};
''')
        for item in result['results']:
            with self.subTest(case=item['observationId']):
                observation = item['observation']
                ax_stage = observation['stages']['AX']
                if item['expectedStatus'] == 'OK':
                    self.assertEqual(ax_stage['status'], 'OK')
                    self.assertTrue(ax_stage['full_tree'])
                    self.assertFalse(ax_stage['diff_only'])
                    self.assertEqual(ax_stage['utf8_bytes'], item['stateBytes'])
                    self.assertEqual(observation['blockers'], [])
                    self.assertTrue(observation['ready_for_bind'])
                else:
                    self.assertEqual(ax_stage['status'], 'EMPTY')
                    self.assertIn('AX:EMPTY', observation['blockers'])
                    self.assertFalse(observation['ready_for_bind'])

    def test_observation_capture_boundary_stage_distinguishes_recorded_and_missing(self):
        result, _ = self.run_helper(r'''
const paths = () => ({
  taskDir: process.env.INPUT_TEST_ROOT,
  observationDir: process.env.INPUT_TEST_DIR,
});
globalThis.cua = {
  getApp: async () => ({
    getAXStateAndScreenshot: async () => ({
      state: '{"role":"AXWindow","marker":"boundary-ok"}',
      screenshot: new TextEncoder().encode('BOUNDARY-OK'),
    }),
  }),
};
const recorded = await evidenceTools.captureAndPersist({
  ...paths(), observationId: 'boundary-recorded'});
globalThis.cua = {
  getApp: async () => ({
    getAXStateAndScreenshot: async () => {
      throw new Error('synthetic boundary capture throw');
    },
  }),
};
const thrown = await evidenceTools.captureAndPersist({
  ...paths(), observationId: 'boundary-thrown'});
globalThis.cua = {
  getApp: async () => {
    throw new Error('synthetic boundary pre-call rejection');
  },
};
const preCall = await evidenceTools.captureAndPersist({
  ...paths(), observationId: 'boundary-pre-call'});
const bare = await evidenceTools.persistObservation({
  ...paths(), observationId: 'boundary-bare',
  capture: {state: '{"role":"AXWindow","marker":"boundary-bare"}',
            screenshot: new TextEncoder().encode('BOUNDARY-BARE')},
});
return {recorded, thrown, preCall, bare};
''')
        self.assertEqual(
            result['recorded']['stages']['CAPTURE_BOUNDARY']['status'],
            'RECORDED')
        self.assertTrue(result['recorded']['ready_for_bind'])
        self.assertEqual(
            result['thrown']['stages']['CAPTURE_BOUNDARY']['status'],
            'RECORDED')
        self.assertEqual(result['thrown']['blockers'], ['CAPTURE:FAILED'])
        self.assertEqual(
            result['preCall']['stages']['CAPTURE_BOUNDARY']['status'],
            'MISSING')
        self.assertEqual(
            result['bare']['stages']['CAPTURE_BOUNDARY']['status'], 'MISSING')
        self.assertTrue(result['bare']['ready_for_bind'])
        self.assertEqual(result['bare']['blockers'], [])

    def test_dispatch_direct_path_checks_intent_event_and_same_observation(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
let clicks = 0;
const observation = await dispatchObservation('direct-observation');
const request = dispatchDownloadRequest('attempt-direct', observation);
const common = dispatchDownloadOptions('attempt-direct', request,
  {async click(target) { clicks += 1; return {target}; }},
  {observation, source_observation_bytes: dispatchCapture().screenshot});
const invalidIntent = await notesIntentDispatch.persistDownload({
  ...common,
  intent: dispatchIntent('attempt-direct', {dispatch_authorized: true}),
});
const legacyEvent = await notesIntentDispatch.persistDownload({
  ...common,
  intentEventRef: {sequence: 7, sha256: dispatchEventSha},
  request: {...request, intent_event_ref: {sequence: 7, sha256: dispatchEventSha}},
});
const eventMismatch = await notesIntentDispatch.persistDownload({
  ...common,
  intentEventRef: {sequence: 8, event_sha256: dispatchEventSha},
});
const attemptMismatch = await notesIntentDispatch.persistDownload({
  ...common,
  request: {...request, attempt_id: 'attempt-other'},
});
const observationMismatch = await notesIntentDispatch.persistDownload({
  ...common,
  observation: await dispatchObservation('old-observation'),
});
const valid = await notesIntentDispatch.persistDownload(common);
return {clicks, invalidIntent, legacyEvent, eventMismatch,
        attemptMismatch, observationMismatch, valid};
''')
        self.assertEqual(result['clicks'], 1)
        for name, reason in (
            ('invalidIntent', 'INTENT_NOT_DISPATCHABLE'),
            ('legacyEvent', 'INTENT_EVENT_REF_INVALID'),
            ('eventMismatch', 'INTENT_EVENT_REF_MISMATCH'),
            ('attemptMismatch', 'INTENT_ATTEMPT_MISMATCH'),
            ('observationMismatch', 'DOWNLOAD_SOURCE_OBSERVATION_MISMATCH'),
        ):
            self.assertEqual(result[name]['reason'], reason)
        self.assertEqual(result['valid']['status'], 'INVOKED')
        self.assertEqual(result['valid']['operation_id'],
                         'notes-download-attempt-direct')
        self.assertEqual(result['valid']['source_mode'],
                         'DIRECT_INTENT_OBSERVATION')

    def test_two_stage_visible_direct_does_not_consume_reveal(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
let revealClicks = 0, downloadClicks = 0, captures = 0;
const app = {
  async click(target) {
    if (target[0] === 70 && target[1] === 80) revealClicks += 1;
    else downloadClicks += 1;
    return {target};
  },
  async getAXStateAndScreenshot() {
    captures += 1;
    return dispatchCapture();
  },
};
const windowBinding = dispatchWindowBinding({window_id: 4242});
const preObservation = await dispatchObservation(
  'visible-pre', dispatchFreshCapture('visible-pre'));
const direct = notesIntentDispatch.checkDownloadReadiness({
  app, observation: preObservation, windowBinding, branch: 'DIRECT',
  decision: dispatchDirectReadinessDecision(preObservation),
});
const preIntentReveal = notesIntentDispatch.checkDownloadReadiness({
  app, observation: preObservation, windowBinding, branch: 'REVEAL',
  decision: dispatchRevealReadinessDecision(preObservation),
});
const freshObservation = await dispatchObservation(
  'visible-fresh', dispatchFreshCapture('visible-fresh'));
const request = dispatchDownloadRequest('attempt-visible-direct', freshObservation);
const sourceBytes = new Uint8Array(
  await fsTest.readFile(freshObservation.assets.screenshot.path));
const download = await notesIntentDispatch.persistDownload(
  dispatchDownloadOptions('attempt-visible-direct', request, app,
    {observation: freshObservation, source_observation_bytes: sourceBytes}));
return {direct, preIntentReveal, download,
        revealClicks, downloadClicks, captures};
''')
        self.assertEqual(result['direct']['status'], 'READY')
        self.assertEqual(result['preIntentReveal']['status'], 'READY')
        self.assertEqual(result['preIntentReveal']['window_binding']['window_id'], 4242)
        self.assertEqual(result['download']['status'], 'INVOKED')
        self.assertEqual(result['download']['source_mode'],
                         'DIRECT_INTENT_OBSERVATION')
        self.assertEqual(result['revealClicks'], 0)
        self.assertEqual(result['captures'], 0)
        self.assertEqual(result['downloadClicks'], 1)

    def test_two_stage_visible_to_hidden_uses_fresh_before_and_same_after_once(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
let revealClicks = 0, downloadClicks = 0, captureCalls = 0;
const app = {
  async click(target) {
    if (target[0] === 70 && target[1] === 80) revealClicks += 1;
    else downloadClicks += 1;
    return {target};
  },
  async getAXStateAndScreenshot() {
    captureCalls += 1;
    return dispatchCapture();
  },
};
const windowBinding = dispatchWindowBinding({window_id: 4242});
const preObservation = await dispatchObservation(
  'transition-pre', dispatchFreshCapture('transition-pre'));
const preDirect = notesIntentDispatch.checkDownloadReadiness({
  app, observation: preObservation, windowBinding, branch: 'DIRECT',
  decision: dispatchDirectReadinessDecision(preObservation),
});
const preIntentReveal = notesIntentDispatch.checkDownloadReadiness({
  app, observation: preObservation, windowBinding, branch: 'REVEAL',
  decision: dispatchRevealReadinessDecision(preObservation),
});
const beforeObservation = await dispatchObservation(
  'transition-before', dispatchFreshCapture('transition-before'));
const freshDirect = notesIntentDispatch.checkDownloadReadiness({
  app, observation: beforeObservation, windowBinding, branch: 'DIRECT',
  decision: dispatchDirectReadinessDecision(
    beforeObservation, {control_visibility: 'NOT_OBSERVED'}),
});
const request = dispatchRevealRequest(
  'attempt-visible-hidden', beforeObservation);
const revealRun = await notesIntentDispatch.persistReveal({
  ...dispatchPaths(),
  intent: dispatchIntent('attempt-visible-hidden'),
  intentEventRef: dispatchEventRef(),
  request,
  preIntentReveal,
  beforeObservation,
  windowBinding,
  app,
});
const after = revealRun.afterObservation;
const afterShot = dispatchRef(after.assets.screenshot);
const afterBytes = new Uint8Array(await fsTest.readFile(afterShot.path));
const downloadRequest = {
  ...dispatchDownloadRequest('attempt-visible-hidden', after),
  app_window_binding: windowBinding,
  source_observation: afterShot,
  source_observation_ref: afterShot,
  mapping_evidence_ref: dispatchRef(after.assets.ax),
};
const download = await notesIntentDispatch.persistDownload(
  dispatchDownloadOptions('attempt-visible-hidden', downloadRequest, app,
    {reveal: revealRun, source_observation_bytes: afterBytes}));
return {preDirect, preIntentReveal, preObservationId: preObservation.observation_id,
        beforeObservationId: beforeObservation.observation_id, freshDirect,
        revealRun, download, revealClicks, downloadClicks, captureCalls};
''')
        self.assertEqual(result['preDirect']['status'], 'READY')
        self.assertEqual(result['preIntentReveal']['status'], 'READY')
        self.assertEqual(result['freshDirect']['status'], 'STOP')
        self.assertIn('DOWNLOAD_CONTROL_VISIBILITY_REQUIRED',
                      result['freshDirect']['blockers'])
        self.assertNotEqual(result['preObservationId'],
                            result['beforeObservationId'])
        self.assertEqual(result['revealRun']['status'], 'INVOKED')
        self.assertEqual(result['revealRun']['operation_id'],
                         'notes-reveal-c2-attempt-visible-hidden')
        self.assertEqual(result['download']['status'], 'INVOKED')
        self.assertEqual(result['download']['source_mode'], 'REVEAL_SAME_AFTER')
        self.assertEqual(result['revealClicks'], 1)
        self.assertEqual(result['captureCalls'], 1)
        self.assertEqual(result['downloadClicks'], 1)

    def test_dispatch_reveal_same_after_feeds_one_download_and_fixed_slot(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
let revealClicks = 0, revealCaptures = 0, downloadClicks = 0;
const app = {
  async click(target) {
    if (target[0] === 70 && target[1] === 80) revealClicks += 1;
    else downloadClicks += 1;
    return {target};
  },
  async getAXStateAndScreenshot() {
    revealCaptures += 1;
    return dispatchCapture();
  },
};
const stage = await dispatchRevealStage(
  'attempt-reveal', 1, dispatchWindowBinding({window_id: 4242}));
const revealRun = await notesIntentDispatch.persistReveal(
  dispatchGatedRevealOptions(stage, app));
const after = revealRun.afterObservation;
const afterShot = dispatchRef(after.assets.screenshot);
const afterBytes = new Uint8Array(await fsTest.readFile(afterShot.path));
const request = {
  ...dispatchDownloadRequest('attempt-reveal', after),
  app_window_binding: stage.windowBinding,
  source_observation: afterShot,
  source_observation_ref: afterShot,
  mapping_evidence_ref: dispatchRef(after.assets.ax),
};
const download = overrides => notesIntentDispatch.persistDownload(
  dispatchDownloadOptions('attempt-reveal', request, app,
    {source_observation_bytes: afterBytes}, overrides));
const stale = await download({
  observation: await dispatchObservation('before-observation'),
});
const wrongWindow = await download({
  reveal: revealRun,
  request: {...request, app_window_binding: dispatchWindowBinding({window_id: 4243})},
});
const sameAfter = await download({reveal: revealRun});
const replay = await download({
  reveal: revealRun,
  request: {...request, candidate_point: [61, 71], prepared_target: [61, 71]},
});
return {revealClicks, revealCaptures, downloadClicks, revealRun,
        stale, wrongWindow, sameAfter, replay};
''')
        self.assertEqual(result['revealClicks'], 1)
        self.assertEqual(result['revealCaptures'], 1)
        self.assertEqual(result['revealRun']['status'], 'INVOKED')
        self.assertEqual(result['revealRun']['operation_id'],
                         'notes-reveal-c2-attempt-reveal')
        self.assertEqual(result['revealRun']['window_binding']['window_id'], 4242)
        self.assertEqual(result['stale']['reason'],
                         'DOWNLOAD_SOURCE_OBSERVATION_MISMATCH')
        self.assertEqual(result['wrongWindow']['reason'],
                         'DOWNLOAD_REVEAL_WINDOW_BINDING_MISMATCH')
        self.assertEqual(result['sameAfter']['status'], 'INVOKED')
        self.assertEqual(result['sameAfter']['source_mode'], 'REVEAL_SAME_AFTER')
        self.assertEqual(result['sameAfter']['operation_id'],
                         'notes-download-attempt-reveal')
        self.assertEqual(result['replay']['reason'],
                         'DOWNLOAD_SLOT_OR_HELPER_BLOCKED')
        self.assertEqual(result['replay']['receipt']['status'],
                         'REQUEST_PERSIST_FAILED')
        self.assertEqual(result['downloadClicks'], 1)

    def test_dispatch_reveal_rejects_budget_race_ordinal_switch_and_capture_error(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
let revealClicks = 0, revealCaptures = 0, downloadClicks = 0;
const app = {
  async click(target) { revealClicks += 1; return {target}; },
  async getAXStateAndScreenshot() {
    revealCaptures += 1;
    return dispatchCapture();
  },
};
const reveal = (attemptId, request, overrides = {}) =>
  notesIntentDispatch.persistReveal(
    dispatchRevealOptions(attemptId, request, app, overrides));
const invalidIntent = await reveal('attempt-invalid',
  dispatchNavigationRequest('attempt-invalid', 1),
  {intent: dispatchIntent('attempt-invalid', {dispatch_authorized: true})});
const legacyEvent = await reveal('attempt-legacy',
  {...dispatchNavigationRequest('attempt-legacy', 1),
   intent_event_ref: {sequence: 7, sha256: dispatchEventSha}},
  {intentEventRef: {sequence: 7, sha256: dispatchEventSha}});
const eventMismatch = await reveal('attempt-event',
  dispatchNavigationRequest('attempt-event', 1),
  {intentEventRef: {sequence: 8, event_sha256: dispatchEventSha}});
const attemptMismatch = await reveal('attempt-attempt',
  {...dispatchNavigationRequest('attempt-attempt', 1), attempt_id: 'other'});
const badBudget = await reveal('attempt-budget',
  {...dispatchNavigationRequest('attempt-budget', 1), budget_after: 2});
const badOrdinal = await reveal('attempt-ordinal',
  dispatchNavigationRequest('attempt-ordinal', 3));
const badPrior = await reveal('attempt-prior',
  {...dispatchNavigationRequest('attempt-prior', 2), prior_candidate_refs: []});
const hoverKind = await reveal('attempt-hover',
  {...dispatchNavigationRequest('attempt-hover', 1), navigation_kind: 'hover'});
const ordinalTwoStage = await dispatchRevealStage('attempt-two', 2);
const ordinalTwo = await notesIntentDispatch.persistReveal(
  dispatchGatedRevealOptions(ordinalTwoStage, app));
const raceStage = await dispatchRevealStage('attempt-race', 1);
const [raceFirst, raceSecond] = await Promise.all([
  notesIntentDispatch.persistReveal(dispatchGatedRevealOptions(raceStage, app)),
  notesIntentDispatch.persistReveal(dispatchGatedRevealOptions(raceStage, app)),
]);
const ordinalSwitchStage = await dispatchRevealStage(
  'attempt-race', 2, dispatchWindowBinding(), {}, 'attempt-race-switch');
const ordinalSwitch = await notesIntentDispatch.persistReveal(
  dispatchGatedRevealOptions(ordinalSwitchStage, app));
const failedRevealStage = await dispatchRevealStage('attempt-capture-error', 1);
const failedReveal = await notesIntentDispatch.persistReveal(
  dispatchGatedRevealOptions(failedRevealStage, {
      async click(target) { revealClicks += 1; return {target}; },
      async getAXStateAndScreenshot() {
        throw new Error('synthetic dispatch capture failed');
      },
    }));
const observation = await dispatchObservation('capture-error-observation');
const failedDownload = await notesIntentDispatch.persistDownload(
  dispatchDownloadOptions('attempt-capture-error',
    dispatchDownloadRequest('attempt-capture-error', observation),
    {async click(target) { downloadClicks += 1; return {target}; }},
    {reveal: failedReveal, source_observation_bytes: dispatchCapture().screenshot}));
return {revealClicks, revealCaptures, downloadClicks, invalidIntent, legacyEvent,
        eventMismatch, attemptMismatch, badBudget, badOrdinal, badPrior, hoverKind,
        ordinalTwo, raceFirst, raceSecond, ordinalSwitch, failedReveal,
        failedDownload};
''')
        for name, reason in (
            ('invalidIntent', 'INTENT_NOT_DISPATCHABLE'),
            ('legacyEvent', 'INTENT_EVENT_REF_INVALID'),
            ('eventMismatch', 'INTENT_EVENT_REF_MISMATCH'),
            ('attemptMismatch', 'INTENT_ATTEMPT_MISMATCH'),
            ('badBudget', 'REVEAL_ORDINAL_BUDGET_MISMATCH'),
            ('badOrdinal', 'REVEAL_ORDINAL_INVALID'),
            ('badPrior', 'REVEAL_ORDINAL_BUDGET_MISMATCH'),
            ('hoverKind', 'REVEAL_KIND_UNSUPPORTED'),
        ):
            self.assertEqual(result[name]['reason'], reason)
        self.assertEqual(result['ordinalTwo']['status'], 'INVOKED')
        self.assertEqual(result['ordinalTwo']['candidate_ordinal'], 2)
        self.assertEqual(result['revealClicks'], 3)
        self.assertEqual(result['revealCaptures'], 2)
        statuses = sorted([result['raceFirst']['status'],
                           result['raceSecond']['status']])
        self.assertEqual(statuses, ['STOP', 'STOP'])
        race_receipts = sorted([
            result['raceFirst']['run']['inputReceipt']['status'],
            result['raceSecond']['run']['inputReceipt']['status'],
        ])
        self.assertEqual(race_receipts,
                         ['INVOKED', 'REQUEST_PERSIST_FAILED'])
        self.assertEqual(sum(1 for item in (result['raceFirst'],
                                            result['raceSecond'])
                             if item.get('afterObservation')), 1)
        self.assertEqual(result['ordinalSwitch']['status'], 'STOP')
        self.assertEqual(result['ordinalSwitch']['run']['inputReceipt']['status'],
                         'REQUEST_PERSIST_FAILED')
        self.assertEqual(result['failedReveal']['reason'],
                         'REVEAL_INPUT_OR_AFTER_INCOMPLETE')
        self.assertTrue(result['failedReveal']['run']['fail_closed'])
        self.assertFalse(result['failedReveal']['afterObservation']['ready_for_bind'])
        self.assertEqual(result['failedDownload']['reason'],
                         'REVEAL_AFTER_NOT_DISPATCHABLE')
        self.assertEqual(result['downloadClicks'], 0)

    def test_download_readiness_accepts_direct_and_reveal_without_side_effects(self):
        """Synthetic gate fixture only; no real LINE app, CLI, or download."""
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
const counters = {};
const app = dispatchReadinessApp(counters);
const observation = await dispatchObservation('readiness-accepted');
const windowBinding = dispatchWindowBinding();
const common = {app, observation, windowBinding};
const beforeFiles = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
const direct = notesIntentDispatch.checkDownloadReadiness({
  ...common,
  branch: 'DIRECT',
  decision: dispatchDirectReadinessDecision(observation),
});
const revealOne = notesIntentDispatch.checkDownloadReadiness({
  ...common,
  branch: 'REVEAL',
  decision: dispatchRevealReadinessDecision(observation, 1),
});
const revealTwo = notesIntentDispatch.checkDownloadReadiness({
  ...common,
  branch: 'REVEAL',
  decision: dispatchRevealReadinessDecision(observation, 2),
});
const afterFiles = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {counters, direct, revealOne, revealTwo, beforeFiles, afterFiles};
''')
        self.assertEqual(result['counters'].get('clicks', 0), 0)
        self.assertEqual(result['counters'].get('captures', 0), 0)
        self.assertEqual(result['beforeFiles'], result['afterFiles'])
        self.assertEqual(result['direct']['status'], 'READY')
        self.assertEqual(result['direct']['branch'], 'DIRECT')
        self.assertEqual(result['direct']['blockers'], [])
        self.assertEqual(result['revealOne']['status'], 'READY')
        self.assertEqual(result['revealOne']['candidate_ordinal'], 1)
        self.assertEqual(result['revealOne']['budget_before'], 0)
        self.assertEqual(result['revealOne']['budget_after'], 1)
        self.assertEqual(result['revealTwo']['status'], 'READY')
        self.assertEqual(result['revealTwo']['candidate_ordinal'], 2)
        self.assertEqual(result['revealTwo']['budget_before'], 1)
        self.assertEqual(result['revealTwo']['budget_after'], 2)
        self.assertFalse(any('notes-reveal-c2-' in name or 'notes-download-' in name
                             for name in result['afterFiles']))

    def test_reveal_preflight_errors_and_slot_collision_make_zero_input(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
let clicks = 0, captures = 0;
const app = {
  async click(target) { clicks += 1; return {target}; },
  async getAXStateAndScreenshot() {
    captures += 1;
    return dispatchCapture();
  },
};
const windowBinding = dispatchWindowBinding({window_id: 4242});
const stage = await dispatchRevealStage(
  'attempt-zero-input', 1, windowBinding);
const base = dispatchGatedRevealOptions(stage, app);
const cases = [
  ['missingPreflight', {...base, preIntentReveal: undefined},
   'REVEAL_PREFLIGHT_REQUIRED'],
  ['staleBefore', {...base, beforeObservation: stage.preObservation},
   'REVEAL_BEFORE_OBSERVATION_NOT_FRESH'],
  ['windowChanged', {
    ...base, windowBinding: dispatchWindowBinding({window_id: 4243}),
  }, 'REVEAL_WINDOW_BINDING_CHANGED'],
  ['candidateChanged', {
    ...base,
    request: {...stage.request, reveal_candidate_id: 'candidate-other'},
  }, 'REVEAL_REQUEST_DRIFT'],
  ['scopeChanged', {
    ...base,
    request: {...stage.request, reveal_scope_ref: 'scope-other'},
  }, 'REVEAL_REQUEST_DRIFT'],
  ['notStrictInterior', {
    ...base,
    request: {...stage.request, safe_zone: [70, 80, 100, 110]},
  }, 'REVEAL_BEFORE_OBSERVATION_BLOCKED'],
];
const results = [];
for (const [name, options, expected] of cases) {
  results.push([name, expected, await notesIntentDispatch.persistReveal(options)]);
}
const slotPath = process.env.INPUT_TEST_DIR +
  '/notes-reveal-c2-attempt-zero-input.input.request.json';
await fsTest.writeFile(slotPath, 'keep reveal slot sentinel', {flag: 'wx'});
const duplicate = await notesIntentDispatch.persistReveal(base);
return {
  clicks, captures, results, duplicate,
  slot: await fsTest.readFile(slotPath, 'utf8'),
};
''')
        for name, expected, outcome in result['results']:
            with self.subTest(case=name):
                self.assertEqual(outcome['status'], 'STOP')
                self.assertEqual(outcome['reason'], expected)
        self.assertEqual(result['clicks'], 0)
        self.assertEqual(result['captures'], 0)
        self.assertEqual(result['duplicate']['status'], 'STOP')
        self.assertEqual(result['duplicate']['reason'],
                         'REVEAL_INPUT_OR_AFTER_INCOMPLETE')
        self.assertEqual(result['duplicate']['run']['inputReceipt']['status'],
                         'REQUEST_PERSIST_FAILED')
        self.assertIsNone(result['duplicate']['afterObservation'])
        self.assertEqual(result['slot'], 'keep reveal slot sentinel')

    def test_download_readiness_table_drives_stops_without_side_effects(self):
        """Synthetic blocker table only; no real LINE app, CLI, or download."""
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
const counters = {};
const app = dispatchReadinessApp(counters);
const observation = await dispatchObservation('readiness-rejections');
const windowBinding = dispatchWindowBinding();
const direct = (overrides = {}) => dispatchDirectReadinessDecision(observation, overrides);
const reveal = (ordinal = 1, overrides = {}) =>
  dispatchRevealReadinessDecision(observation, ordinal, overrides);
const check = (branch, overrides = {}) => notesIntentDispatch.checkDownloadReadiness({
  app, observation, windowBinding, branch,
  decision: branch === 'DIRECT' ? direct() : reveal(),
  ...overrides,
});
const rawCase = (branch, overrides, expected) => [branch, overrides, expected];
const directCase = (overrides, expected) =>
  rawCase('DIRECT', {decision: direct(overrides)}, expected);
const revealCase = (overrides, expected) =>
  rawCase('REVEAL', {decision: reveal(1, overrides)}, expected);
const revealTwoCase = (overrides, expected) =>
  rawCase('REVEAL', {decision: reveal(2, overrides)}, expected);
const cases = {
  unknownWindow: rawCase('DIRECT', {
    windowBinding: dispatchWindowBinding({window_id: 'UNKNOWN'}),
  }, 'APP_WINDOW_CONTEXT_REQUIRED'),
  wrongBundle: rawCase('DIRECT', {
    windowBinding: dispatchWindowBinding({app_bundle_id: 'example.other.app'}),
  }, 'APP_WINDOW_CONTEXT_REQUIRED'),
  missingClick: rawCase('DIRECT', {
    app: {async getAXStateAndScreenshot() { return dispatchCapture(); }},
  }, 'APP_CLICK_UNAVAILABLE'),
  missingCapture: rawCase('DIRECT', {
    app: {async click() { return {target: [60, 70]}; }},
  }, 'APP_CAPTURE_UNAVAILABLE'),
  missingDecision: rawCase('DIRECT', {decision: undefined}, 'DOWNLOAD_DECISION_REQUIRED'),
  missingObservation: rawCase('DIRECT', {
    observation: undefined,
  }, 'DOWNLOAD_OBSERVATION_INVALID'),
  missingObservationAssets: rawCase('DIRECT', {
    observation: {...observation, assets: undefined},
  }, 'DOWNLOAD_OBSERVATION_INVALID'),
  missingPositionSource: directCase(
    {position_source_ref: undefined}, 'DOWNLOAD_CONTROL_POSITION_SOURCE_MISMATCH'),
  boundaryPoint: directCase(
    {candidate_point: [20, 70]}, 'DOWNLOAD_CONTROL_POINT_NOT_STRICT_INTERIOR'),
  targetMismatch: directCase(
    {prepared_target: [61, 71]}, 'DOWNLOAD_CONTROL_PREPARED_TARGET_MISMATCH'),
  coordinateMismatch: directCase(
    {target_coord_space: 'APP_BOUND_SCREENSHOT_POINTS'},
    'DOWNLOAD_CONTROL_TARGET_COORD_SPACE_INVALID'),
  mappingUnknown: directCase(
    {mapping_status: 'UNKNOWN'}, 'DOWNLOAD_CONTROL_MAPPING_UNKNOWN'),
  notVisible: directCase(
    {control_visibility: 'NOT_OBSERVED'}, 'DOWNLOAD_CONTROL_VISIBILITY_REQUIRED'),
  wrongOwner: directCase({control_owner: 'UNKNOWN'}, 'DOWNLOAD_CONTROL_OWNER_REQUIRED'),
  disabled: directCase({enabled_state: 'DISABLED'}, 'DOWNLOAD_CONTROL_NOT_ENABLED'),
  invalidBranch: rawCase('HOVER', {decision: direct()}, 'DOWNLOAD_BRANCH_INVALID'),
  hover: revealCase({navigation_kind: 'hover'}, 'REVEAL_KIND_UNSUPPORTED'),
  notSelected: revealCase({selected_state_before: 'UNKNOWN'}, 'REVEAL_SELECTION_REQUIRED'),
  wrongBeforeScreenshot: revealCase(
    {before_screenshot_ref: dispatchRef(observation.assets.ax)},
    'REVEAL_BEFORE_SCREENSHOT_MISMATCH'),
  wrongBeforeAx: revealCase(
    {before_ax_ref: dispatchRef(observation.assets.screenshot)},
    'REVEAL_BEFORE_AX_MISMATCH'),
  invalidSafeZone: revealCase({safe_zone: [40, 50, 40, 110]}, 'REVEAL_SAFE_ZONE_INVALID'),
  missingSafeZoneRef: revealCase(
    {safe_zone_ref: undefined}, 'REVEAL_SAFE_ZONE_REF_REQUIRED'),
  boundaryTarget: revealCase(
    {prepared_target: [40, 80]}, 'REVEAL_TARGET_NOT_STRICT_INTERIOR'),
  badBudget: revealCase({budget_after: 2}, 'REVEAL_ORDINAL_BUDGET_MISMATCH'),
  badOrdinal: revealTwoCase({candidate_ordinal: 3}, 'REVEAL_ORDINAL_INVALID'),
  unknownCandidateId: revealTwoCase(
    {reveal_candidate_id: 'UNKNOWN'}, 'REVEAL_CANDIDATE_ID_REQUIRED'),
  missingMappingId: revealCase(
    {mapping_id: 'UNKNOWN'}, 'REVEAL_MAPPING_ID_REQUIRED'),
  missingMappingTime: revealCase(
    {mapping_valid_at: 'UNKNOWN'}, 'REVEAL_MAPPING_TIME_REQUIRED'),
  coordinateUnknown: revealCase(
    {coordinate_space_match: 'UNKNOWN'}, 'REVEAL_COORDINATE_SPACE_UNKNOWN'),
  positionMismatch: revealCase({position_source_ref: {
    path: '/tmp/other', bytes: 1, sha256: 'f'.repeat(64),
  }}, 'REVEAL_POSITION_SOURCE_MISMATCH'),
  missingRearm: revealTwoCase(
    {rearm_new_information_ref: 'UNKNOWN'}, 'REVEAL_REARM_NEW_INFORMATION_REQUIRED'),
};
const stopped = {};
for (const [name, [branch, overrides, expected]] of Object.entries(cases)) {
  stopped[name] = {...check(branch, overrides), expected};
}
return {counters, stopped};
''')
        self.assertEqual(len(result['stopped']), 31)
        for name, item in result['stopped'].items():
            self.assertEqual(item['status'], 'STOP', name)
            self.assertIn(item['expected'], item['blockers'], name)
        self.assertEqual(result['counters'].get('clicks', 0), 0)
        self.assertEqual(result['counters'].get('captures', 0), 0)

    def test_invalid_second_reveal_refs_stop_before_intent_and_input(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
const counters = {};
const app = dispatchReadinessApp(counters);
const observation = await dispatchObservation('review-second-reveal');
const windowBinding = dispatchWindowBinding();
const invalidCases = [
  ['null', [null], 'REVEAL_ORDINAL_BUDGET_MISMATCH'],
  ['UNKNOWN', ['UNKNOWN'], 'REVEAL_ORDINAL_BUDGET_MISMATCH'],
  ['NONE', ['NONE'], 'REVEAL_ORDINAL_BUDGET_MISMATCH'],
  ['empty', [''], 'REVEAL_ORDINAL_BUDGET_MISMATCH'],
  ['sparse', Array(1), 'REVEAL_REQUEST_SERIALIZATION_FAILED'],
  ['number', [42], 'REVEAL_ORDINAL_BUDGET_MISMATCH'],
  ['object', [{}], 'REVEAL_ORDINAL_BUDGET_MISMATCH'],
];
const beforeFiles = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
const results = [];
for (const [label, refs, expectedRevealReason] of invalidCases) {
  const attemptId = 'attempt-review-' + label;
  const overrides = {prior_candidate_refs: refs};
  const readiness = notesIntentDispatch.checkDownloadReadiness({
    app, observation, windowBinding, branch: 'REVEAL',
    decision: dispatchRevealReadinessDecision(observation, 2, overrides),
  });
  const request = {...dispatchNavigationRequest(attemptId, 2), ...overrides};
  const reveal = await notesIntentDispatch.persistReveal(
    dispatchRevealOptions(attemptId, request, app));
  results.push({label, expectedRevealReason, readiness, reveal});
}
const afterFiles = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {counters, beforeFiles, afterFiles, results};
''')
        for case in result['results']:
            with self.subTest(case=case['label']):
                self.assertEqual(case['readiness']['status'], 'STOP')
                self.assertIn('REVEAL_ORDINAL_BUDGET_MISMATCH',
                              case['readiness']['blockers'])
                self.assertEqual(case['reveal']['status'], 'STOP')
                self.assertEqual(case['reveal']['reason'],
                                 case['expectedRevealReason'])
        sparse = next(item for item in result['results']
                      if item['label'] == 'sparse')
        self.assertEqual(sparse['reveal']['reason'],
                         'REVEAL_REQUEST_SERIALIZATION_FAILED')
        self.assertEqual(result['counters'].get('clicks', 0), 0)
        self.assertEqual(result['counters'].get('captures', 0), 0)
        self.assertEqual(result['beforeFiles'], result['afterFiles'])


GROUNDED_SETUP = r'''
const fsNative = await import('node:fs');
const sourcePath = process.env.INPUT_TEST_ROOT + '/grounded-source.bin';
const sourceBytes = Buffer.from('grounded source observation\n', 'utf8');
fsNative.writeFileSync(sourcePath, sourceBytes);
const sourceRef = {
  path: sourcePath,
  bytes: sourceBytes.length,
  sha256: evidenceTools.sha256(sourceBytes),
};
function makeGroundedRequest() {
  return {
    input_phase: 'DOWNLOAD_CONTROL',
    attempt_id: 'attempt-grounded',
    app_window_binding: {
      app_bundle_id: 'jp.naver.line.mac',
      window_id: 'window-grounded',
    },
    mapping_status: 'MATCH',
    observation_order: 'PRE_INPUT',
    grounding_conclusion: 'PASS_TO_INPUT',
    candidate_point_relation: 'INSIDE',
    coordinate_space_match: 'MATCH',
    control_region_coord_space: 'SCREEN_POINTS',
    target_coord_space: 'SCREEN_POINTS',
    source_observation: {...sourceRef},
    source_observation_ref: {...sourceRef},
    mapping_evidence_ref: {...sourceRef},
    control_region: [10, 20, 110, 120],
    candidate_point: [60, 70],
    prepared_target: [60, 70],
  };
}
function makeGroundedOptions(operationId, click) {
  return {
    taskDir: process.env.INPUT_TEST_ROOT,
    inputDir: process.env.INPUT_TEST_DIR,
    operationId,
    request: makeGroundedRequest(),
    source_observation_bytes: new Uint8Array(sourceBytes),
    app: {click},
  };
}
async function readJson(file) {
  return JSON.parse(await fsTest.readFile(file, 'utf8'));
}
'''


class NotesGroundedDownloadHelperTests(NodeHelperRunner):
    def test_grounded_request_validation_stops_before_click(self):
        result, _ = self.run_helper(GROUNDED_SETUP + r'''
const cases = [
  ['missing-field', request => { delete request.mapping_status; },
   'DOWNLOAD_CONTROL_GROUNDING_INVALID', 'DOWNLOAD_CONTROL_MAPPING_UNKNOWN'],
  ['outside-region', request => {
    request.candidate_point = [0, 70];
    request.prepared_target = [0, 70];
  }, 'DOWNLOAD_CONTROL_GROUNDING_INVALID',
   'DOWNLOAD_CONTROL_POINT_NOT_STRICT_INTERIOR'],
  ['border', request => {
    request.candidate_point = [10, 70];
    request.prepared_target = [10, 70];
  }, 'DOWNLOAD_CONTROL_GROUNDING_INVALID',
   'DOWNLOAD_CONTROL_POINT_NOT_STRICT_INTERIOR'],
  ['nonfinite-point', request => {
    request.candidate_point = [NaN, 70];
    request.prepared_target = [NaN, 70];
  }, 'REQUEST_SERIALIZATION_FAILED', 'REQUEST_SERIALIZATION_FAILED'],
  ['unknown-mapping', request => { request.mapping_status = 'UNKNOWN'; },
   'DOWNLOAD_CONTROL_GROUNDING_INVALID', 'DOWNLOAD_CONTROL_MAPPING_UNKNOWN'],
  ['post-input-order', request => { request.observation_order = 'POST_INPUT'; },
   'DOWNLOAD_CONTROL_GROUNDING_INVALID',
   'DOWNLOAD_CONTROL_OBSERVATION_ORDER_UNKNOWN'],
  ['source-hash-mismatch', request => {
    request.source_observation_ref.sha256 = '0'.repeat(64);
  }, 'DOWNLOAD_CONTROL_GROUNDING_INVALID',
   'DOWNLOAD_CONTROL_SOURCE_REF_MISMATCH'],
  ['mapping-hash-mismatch', request => {
    request.mapping_evidence_ref.sha256 = '1'.repeat(64);
  }, 'MAPPING_EVIDENCE_READBACK_FAILED',
   'MAPPING_EVIDENCE_READBACK_MISMATCH'],
];
const results = [];
for (const [name, mutate, expectedStatus, expectedBlocker] of cases) {
  let clicks = 0;
  const options = makeGroundedOptions('validation-' + name, async () => {
    clicks += 1;
    return {ok: true};
  });
  mutate(options.request);
  const receipt = await evidenceTools.persistGroundedDownloadClick(options);
  results.push({name, clicks, expectedStatus, expectedBlocker, receipt});
}
return {results};
''')
        self.assertEqual(
            [item['name'] for item in result['results']],
            ['missing-field', 'outside-region', 'border', 'nonfinite-point',
             'unknown-mapping', 'post-input-order', 'source-hash-mismatch',
             'mapping-hash-mismatch'])
        for item in result['results']:
            with self.subTest(case=item['name']):
                self.assertEqual(item['clicks'], 0)
                self.assertEqual(item['receipt']['status'],
                                 item['expectedStatus'])
                self.assertIn(item['expectedBlocker'], item['receipt']['blockers'])
                self.assertEqual(item['receipt']['dispatch_call_target'], 'NOT_SENT')
                self.assertEqual(item['receipt']['native_dispatched_target'], 'UNKNOWN')

    def test_grounded_source_readback_mismatch_stops_before_click(self):
        result, _ = self.run_helper(GROUNDED_SETUP + r'''
let clicks = 0;
const options = makeGroundedOptions('source-readback-mismatch', async () => {
  clicks += 1;
  return {ok: true};
});
const pending = evidenceTools.persistGroundedDownloadClick(options);
fsNative.writeFileSync(sourcePath, Buffer.from('tampered source observation\n', 'utf8'));
const receipt = await pending;
return {clicks, receipt};
''')
        self.assertEqual(result['clicks'], 0)
        self.assertEqual(result['receipt']['status'],
                         'SOURCE_OBSERVATION_READBACK_FAILED')
        self.assertIn('SOURCE_OBSERVATION_READBACK_MISMATCH',
                      result['receipt']['blockers'])
        self.assertEqual(result['receipt']['dispatch_call_target'], 'NOT_SENT')
        self.assertEqual(result['receipt']['native_dispatched_target'], 'UNKNOWN')

    def test_grounded_request_snapshot_survives_nested_caller_mutation(self):
        result, _ = self.run_helper(GROUNDED_SETUP + r'''
const original = makeGroundedRequest();
const expected = JSON.parse(JSON.stringify(original));
const options = makeGroundedOptions('snapshot-request', async target => {
  return {accepted: true, native_code: 0, target, optional: null};
});
options.request = original;
const pending = evidenceTools.persistGroundedDownloadClick(options);
options.request.control_region[0] = -1000;
options.request.candidate_point[0] = -1;
options.request.prepared_target[0] = -1;
options.request.app_window_binding.window_id = 'mutated-window';
options.request.source_observation.sha256 = '2'.repeat(64);
const receipt = await pending;
const saved = await readJson(receipt.files.request);
const raw = await readJson(receipt.files.raw_return);
return {expected, saved, raw, receipt};
''')
        self.assertEqual(result['receipt']['status'], 'INVOKED')
        self.assertEqual(result['saved']['request'], result['expected'])
        self.assertEqual(result['raw']['kind'], 'RETURN')
        self.assertEqual(result['raw']['value']['target'], [60, 70])
        self.assertEqual(result['raw']['value']['native_code'], 0)
        self.assertIsNone(result['raw']['value']['optional'])
        self.assertEqual(result['receipt']['dispatch_call_target'], [60, 70])
        self.assertEqual(result['receipt']['native_dispatched_target'], 'UNKNOWN')
        self.assertEqual(result['receipt']['receipt_target_match'], 'UNKNOWN')
        self.assertFalse(result['receipt']['receipt_is_os_event_trace'])

    def test_generic_download_control_rejects_and_boolean_flags_cannot_bypass(self):
        result, _ = self.run_helper(r'''
let calls = 0;
const receipt = await evidenceTools.persistSingleInput({
  taskDir: process.env.INPUT_TEST_ROOT,
  inputDir: process.env.INPUT_TEST_DIR,
  operationId: 'generic-download-control',
  request: {input_phase: 'DOWNLOAD_CONTROL', strict: true},
  strict: true,
  allowDownloadControl: true,
  grounded: true,
  invoke: async () => { calls += 1; return {ok: true}; },
});
return {calls, receipt};
''')
        self.assertEqual(result['calls'], 0)
        self.assertEqual(result['receipt']['status'],
                         'DOWNLOAD_CONTROL_REQUIRES_GROUNDED_HELPER')
        self.assertEqual(result['receipt']['blockers'],
                         ['DOWNLOAD_CONTROL_REQUIRES_GROUNDED_HELPER'])
        self.assertEqual(result['receipt']['files'], {})

    def test_grounded_wrapper_ignores_caller_invoke_and_readback_callbacks(self):
        result, _ = self.run_helper(GROUNDED_SETUP + r'''
let appClicks = 0;
let callerInvokes = 0;
let callerReadbacks = 0;
const options = makeGroundedOptions('strict-callback-isolation', async target => {
  appClicks += 1;
  return {target};
});
options.invoke = async () => { callerInvokes += 1; return {forged: true}; };
options.readbackExact = async () => {
  callerReadbacks += 1;
  return {status: 'MATCH', saved_bytes: 0, saved_sha256: '0'.repeat(64)};
};
const receipt = await evidenceTools.persistGroundedDownloadClick(options);
return {appClicks, callerInvokes, callerReadbacks, receipt};
''')
        self.assertEqual(result['appClicks'], 1)
        self.assertEqual(result['callerInvokes'], 0)
        self.assertEqual(result['callerReadbacks'], 0)
        self.assertEqual(result['receipt']['status'], 'INVOKED')
        self.assertEqual(result['receipt']['request']['readback'], 'MATCH')
        self.assertEqual(result['receipt']['dispatch_call_target'], [60, 70])

    def test_grounded_throw_and_undefined_dispatch_once_with_native_separation(self):
        result, _ = self.run_helper(GROUNDED_SETUP + r'''
const nativeError = Object.create(null);
Object.defineProperty(nativeError, 'name', {value: 'NativeError', enumerable: false});
Object.defineProperty(nativeError, 'message', {value: 'native-failure', enumerable: false});
Object.defineProperty(nativeError, 'code', {value: 77, enumerable: false});
let throwClicks = 0;
const throwReceipt = await evidenceTools.persistGroundedDownloadClick(
  makeGroundedOptions('native-throw', async () => {
    throwClicks += 1;
    throw nativeError;
  }));
const throwRaw = await readJson(throwReceipt.files.raw_return);
let undefinedClicks = 0;
const undefinedReceipt = await evidenceTools.persistGroundedDownloadClick(
  makeGroundedOptions('native-undefined', async () => {
    undefinedClicks += 1;
    return undefined;
  }));
const undefinedRaw = await readJson(undefinedReceipt.files.raw_return);
return {throwClicks, throwReceipt, throwRaw, undefinedClicks,
        undefinedReceipt, undefinedRaw};
''')
        self.assertEqual(result['throwClicks'], 1)
        self.assertEqual(result['throwReceipt']['raw_return']['kind'], 'ERROR')
        self.assertEqual(result['throwRaw']['error']['code'], 77)
        self.assertIsInstance(result['throwRaw']['error']['code'], int)
        self.assertEqual(result['throwRaw']['error']['message'], 'native-failure')
        self.assertEqual(result['throwReceipt']['dispatch_call_target'], [60, 70])
        self.assertEqual(result['throwReceipt']['native_dispatched_target'], 'UNKNOWN')
        self.assertEqual(result['throwReceipt']['native_return_type'], 'ERROR')

        self.assertEqual(result['undefinedClicks'], 1)
        self.assertEqual(result['undefinedRaw']['kind'], 'NATIVE_RETURN_UNDEFINED')
        self.assertEqual(result['undefinedRaw']['value_type'], 'undefined')
        self.assertEqual(result['undefinedReceipt']['dispatch_call_target'], [60, 70])
        self.assertEqual(result['undefinedReceipt']['native_dispatched_target'], 'UNKNOWN')
        self.assertEqual(result['undefinedReceipt']['native_return_type'], 'UNDEFINED')


class NotesTransientToolbarBlockTests(NodeHelperRunner):
    """Execute the copyable routing blocks in one Node scope per case."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            cls.blocks = documented_blocks()
        except ValueError:
            cls.blocks = {}

    PREFLIGHT_PRELUDE = r'''
const caseCounters = {captures: 0, clicks: 0, clickTargets: []};
const app = {
  async click(target) {
    caseCounters.clicks += 1;
    caseCounters.clickTargets.push(target);
    return {accepted: true, native_code: 0, target};
  },
  async getAXStateAndScreenshot() {
    caseCounters.captures += 1;
    return {
      state: JSON.stringify({role: 'AXWindow',
                             marker: 'block-capture-' + caseCounters.captures}),
      screenshot: new TextEncoder().encode(
        'SYNTHETIC_BLOCK_CAPTURE:' + caseCounters.captures),
    };
  },
};
const windowBinding = {app_bundle_id: 'jp.naver.line.mac', window_id: 4242};
const observation = await evidenceTools.persistObservation({
  taskDir: process.env.INPUT_TEST_ROOT,
  observationDir: process.env.INPUT_TEST_DIR,
  observationId: 'preflight-observation',
  capture: {
    state: '{"role":"AXWindow","marker":"preflight"}',
    screenshot: new TextEncoder().encode('SYNTHETIC_PREFLIGHT_CAPTURE'),
  },
  hostCalls: {
    capture_call_started_at: '2026-11-22T00:00:00.000Z',
    capture_call_returned_at: '2026-11-22T00:00:00.010Z',
  },
});
const filesBefore = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
const B1_CONTROL_VISIBLE = @@CONTROL_VISIBLE@@;
const B1_REVEAL_METHOD_INDEPENDENTLY_AUDITABLE = @@REVEAL_METHOD@@;
'''

    DIRECT_PLACEHOLDERS = r'''
const CURRENT_CONTROL_REGION = @@REGION@@;
const CURRENT_CANDIDATE_POINT = @@POINT@@;
const CURRENT_VERIFIED_DOWNLOAD_TARGET = @@TARGET@@;
'''

    REVEAL_PLACEHOLDERS = r'''
const CURRENT_REVEAL_CANDIDATE_ID = '@@CANDIDATE_ID@@';
const CURRENT_LIST_POST_MEDIA_SCOPE = 'scope-synthetic-1';
const CURRENT_SELECTED_MEDIA_REF = 'media-synthetic-1';
const CURRENT_SAFE_EDGE_REF = 'safe-edge-synthetic-1';
const CURRENT_VERIFIED_SAFE_EDGE_REGION = @@SAFE_ZONE@@;
const CURRENT_VERIFIED_SAFE_EDGE_TARGET = [70, 80];
const CURRENT_MAPPING_ID = 'mapping-synthetic-1';
const CURRENT_MAPPING_VALID_AT = '2026-11-22T00:00:00Z';
'''

    PREFLIGHT_RESULT = r'''
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {
  nextAction: intentReadiness?.status === 'READY'
    ? 'RUN_EXISTING_NOTES_INTENT_ONCE' : 'B1_LOCAL_STOP',
  directStatus: directReadiness?.status ?? null,
  directReason: directReadiness?.reason ?? null,
  directBlockers: directReadiness?.blockers ?? null,
  revealStatus: preIntentReveal?.status ?? null,
  revealReason: preIntentReveal?.reason ?? null,
  revealBlockers: preIntentReveal?.blockers ?? null,
  retainedStatus: retainedReveal?.status ?? null,
  retainedOrdinal: retainedReveal?.candidate_ordinal ?? null,
  retainedObservationId: retainedReveal?.observation_id ?? null,
  revealOrdinalDeclared: typeof REVEAL_CANDIDATE_ORDINAL !== 'undefined',
  preObservationId: observation.observation_id,
  captureCalls: caseCounters.captures,
  clickCalls: caseCounters.clicks,
  clickTargets: caseCounters.clickTargets,
  filesBefore,
  filesAfter,
};
'''

    DIRECT_INPUTS = r'''
const DIRECT_WINDOW_BINDING_FROM_OBSERVATION = windowBinding;
const DIRECT_CONTROL_REGION_FROM_OBSERVATION = [20, 30, 80, 90];
const DIRECT_DOWNLOAD_TARGET_FROM_OBSERVATION = [60, 70];
const DIRECT_COORDINATE_SPACE_FROM_OBSERVATION = 'SCREEN_POINTS';
'''

    DIRECT_EPILOGUE = r'''
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
const downloadDiagnostic = directDownloadReceipt.receipt
  ? JSON.parse(await fsTest.readFile(
      directDownloadReceipt.receipt.files.diagnostic, 'utf8'))
  : null;
return {
  nextAction: intentReadiness?.status === 'READY'
    ? 'RUN_EXISTING_NOTES_INTENT_ONCE' : 'B1_LOCAL_STOP',
  directStatus: directReadiness?.status ?? null,
  directReason: directReadiness?.reason ?? null,
  revealStatus: preIntentReveal?.status ?? null,
  revealReason: preIntentReveal?.reason ?? null,
  revealBlockers: preIntentReveal?.blockers ?? null,
  retainedStatus: retainedReveal?.status ?? null,
  retainedOrdinal: retainedReveal?.candidate_ordinal ?? null,
  revealOrdinalDeclared: typeof REVEAL_CANDIDATE_ORDINAL !== 'undefined',
  preObservationId: observation.observation_id,
  intentObservation: {
    observation_id: intentObservation.observation_id,
    ready_for_bind: intentObservation.ready_for_bind,
    assets: intentObservation.assets,
    hostCalls: intentObservation.hostCalls,
  },
  intentCaptureBytes: Array.from(intentCapture.screenshot),
  directDownloadReceipt,
  downloadDiagnostic,
  captureCalls: caseCounters.captures,
  clickCalls: caseCounters.clicks,
  clickTargets: caseCounters.clickTargets,
  filesBefore,
  filesAfter,
};
'''

    REVEAL_PATH_INPUTS = r'''
const FRESH_WINDOW_BINDING_FROM_THIS_OBSERVATION = windowBinding;
const CURRENT_FRESH_VERIFIED_SAFE_EDGE_REGION = [40, 50, 100, 110];
const CURRENT_FRESH_CONTROL_COORDINATE_SPACE = 'SCREEN_POINTS';
const CURRENT_FRESH_TARGET_COORDINATE_SPACE = 'SCREEN_POINTS';
'''

    AFTER_INPUTS = r'''
const AFTER_WINDOW_BINDING_FROM_THIS_OBSERVATION = windowBinding;
const AFTER_CONTROL_REGION_FROM_THIS_OBSERVATION = [20, 30, 80, 90];
const AFTER_DOWNLOAD_TARGET_FROM_THIS_OBSERVATION = [60, 70];
const AFTER_COORDINATE_SPACE_FROM_THIS_OBSERVATION = 'SCREEN_POINTS';
'''

    REVEAL_EPILOGUE = r'''
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
const afterDiagnostic = revealAfter
  ? JSON.parse(await fsTest.readFile(revealAfter.files.diagnostic, 'utf8'))
  : null;
const downloadDiagnostic = revealDownloadReceipt.receipt
  ? JSON.parse(await fsTest.readFile(
      revealDownloadReceipt.receipt.files.diagnostic, 'utf8'))
  : null;
const revealSavedRequest = revealRun?.run?.inputReceipt?.files?.request
  ? JSON.parse(await fsTest.readFile(
      revealRun.run.inputReceipt.files.request, 'utf8')).request
  : null;
return {
  nextAction: intentReadiness?.status === 'READY'
    ? 'RUN_EXISTING_NOTES_INTENT_ONCE' : 'B1_LOCAL_STOP',
  directStatus: directReadiness?.status ?? null,
  revealStatus: preIntentReveal?.status ?? null,
  retainedStatus: retainedReveal?.status ?? null,
  retainedOrdinal: retainedReveal?.candidate_ordinal ?? null,
  retainedPriorRefs: retainedReveal?.prior_candidate_refs ?? null,
  retainedBudgetBefore: retainedReveal?.budget_before ?? null,
  retainedBudgetAfter: retainedReveal?.budget_after ?? null,
  revealOrdinalDeclared: typeof REVEAL_CANDIDATE_ORDINAL !== 'undefined',
  revealSavedRequest,
  preObservationId: observation.observation_id,
  intentObservation: {
    observation_id: intentObservation.observation_id,
    ready_for_bind: intentObservation.ready_for_bind,
    assets: intentObservation.assets,
    hostCalls: intentObservation.hostCalls,
  },
  intentCaptureBytes: Array.from(intentCapture.screenshot),
  revealRun: {
    status: revealRun.status,
    reason: revealRun.reason,
    operation_id: revealRun.operation_id,
    candidate_ordinal: revealRun.candidate_ordinal,
    pre_intent_observation_id: revealRun.pre_intent_observation_id,
    before_observation_id: revealRun.before_observation_id,
    fail_closed: revealRun.fail_closed,
    hostCalls: revealRun.run?.hostCalls ?? null,
    inputStatus: revealRun.run?.inputReceipt?.status ?? null,
  },
  revealAfter: revealAfter && {
    observation_id: revealAfter.observation_id,
    ready_for_bind: revealAfter.ready_for_bind,
    blockers: revealAfter.blockers,
    assets: revealAfter.assets,
    hostCalls: revealAfter.hostCalls,
  },
  revealAfterBytes: revealAfterBytes ? Array.from(revealAfterBytes) : null,
  afterDiagnostic,
  revealDownloadReceipt,
  downloadDiagnostic,
  captureCalls: caseCounters.captures,
  clickCalls: caseCounters.clicks,
  clickTargets: caseCounters.clickTargets,
  filesBefore,
  filesAfter,
};
'''

    SHARED_CAPTURE_EPILOGUE = r'''
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {
  nextAction: intentReadiness?.status === 'READY'
    ? 'RUN_EXISTING_NOTES_INTENT_ONCE' : 'B1_LOCAL_STOP',
  directStatus: directReadiness?.status ?? null,
  revealStatus: preIntentReveal?.status ?? null,
  retainedStatus: retainedReveal?.status ?? null,
  retainedOrdinal: retainedReveal?.candidate_ordinal ?? null,
  intentObservation: {
    observation_id: intentObservation.observation_id,
    ready_for_bind: intentObservation.ready_for_bind,
    assets: intentObservation.assets,
  },
  intentCaptureBytes: Array.from(intentCapture.screenshot),
  captureCalls: caseCounters.captures,
  clickCalls: caseCounters.clicks,
  clickTargets: caseCounters.clickTargets,
  filesBefore,
  filesAfter,
};
'''

    CANDIDATE_TWO_ARM_PLACEHOLDERS = r'''
const CURRENT_PRIOR_CANDIDATE_REFS = ['prior-candidate-receipt'];
const CURRENT_REARM_PRECONDITIONS_REF = 'prior-candidate-after';
const CURRENT_REARM_NEW_INFORMATION_REF = 'current-tool-document';
const CURRENT_B1_REARM_NEW_INFORMATION_CONCLUSION = 'PASS';
'''

    def run_sections(self, sections, observation_id='intent-after-observation'):
        result, _ = self.run_helper(
            '\n'.join(sections),
            extra_source=self.reveal_source + '\n' + self.dispatch_source,
            observation_id=observation_id)
        return result

    def preflight_prelude(self, *, control_visible, reveal_method,
                          direct=None, reveal=None, ordinal=1,
                          reveal_candidate_id=None):
        source = (self.PREFLIGHT_PRELUDE
                  .replace('@@CONTROL_VISIBLE@@', control_visible)
                  .replace('@@REVEAL_METHOD@@', reveal_method))
        if direct is not None or reveal is not None:
            source += (
                "const CURRENT_CONTROL_COORDINATE_SPACE = 'SCREEN_POINTS';\n"
                "const CURRENT_TARGET_COORDINATE_SPACE = 'SCREEN_POINTS';\n")
        if direct is not None:
            region, point, target = direct
            source += (self.DIRECT_PLACEHOLDERS
                       .replace('@@REGION@@', region)
                       .replace('@@POINT@@', point)
                       .replace('@@TARGET@@', target))
        if reveal is not None:
            source += 'const REVEAL_CANDIDATE_ORDINAL = %d;\n' % ordinal
            source += (self.REVEAL_PLACEHOLDERS
                       .replace('@@SAFE_ZONE@@', reveal)
                       .replace('@@CANDIDATE_ID@@',
                                reveal_candidate_id or 'candidate-%d' % ordinal))
            if ordinal == 2:
                source += self.CANDIDATE_TWO_ARM_PLACEHOLDERS
        return source

    @staticmethod
    def intent_readback_inputs(attempt_id):
        return r'''
const intentReadback = {attempt_id: '%s', status: 'UNKNOWN',
                        dispatch_authorized: false};
await fsTest.writeFile(process.env.INPUT_TEST_ROOT + '/intent-readback.json',
  JSON.stringify(intentReadback) + '\n');
await fsTest.writeFile(process.env.INPUT_TEST_ROOT + '/intent-event.sequence',
  '7\n');
await fsTest.writeFile(process.env.INPUT_TEST_ROOT + '/intent-event.sha256',
  'a'.repeat(64) + '\n');
''' % attempt_id

    def run_preflight_case(self, **kwargs):
        sections = [
            self.preflight_prelude(**kwargs),
            self.blocks['notes-intent-preflight'],
            self.PREFLIGHT_RESULT,
        ]
        return self.run_sections(sections)

    def run_direct_route(self, *, attempt_id, **kwargs):
        sections = [
            self.preflight_prelude(**kwargs),
            self.blocks['notes-intent-preflight'],
            self.intent_readback_inputs(attempt_id),
            self.blocks['notes-intent-readback'],
            self.blocks['notes-intent-capture'],
            self.blocks['notes-download-builder'],
            self.DIRECT_INPUTS,
            self.blocks['notes-direct-dispatch'],
            self.DIRECT_EPILOGUE,
        ]
        return self.run_sections(
            sections, observation_id='intent-capture-' + attempt_id)

    def run_reveal_route(self, *, attempt_id, ordinal=1, **kwargs):
        sections = [
            self.preflight_prelude(ordinal=ordinal, **kwargs),
            self.blocks['notes-intent-preflight'],
            self.intent_readback_inputs(attempt_id),
            self.blocks['notes-intent-readback'],
            self.blocks['notes-intent-capture'],
            self.blocks['notes-download-builder'],
            self.REVEAL_PATH_INPUTS,
            self.blocks['notes-reveal-path'],
            self.AFTER_INPUTS,
            self.blocks['notes-reveal-download'],
            self.REVEAL_EPILOGUE,
        ]
        return self.run_sections(
            sections, observation_id='intent-capture-' + attempt_id)

    def run_shared_capture_stop(self, *, attempt_id, **kwargs):
        sections = [
            self.preflight_prelude(**kwargs),
            self.blocks['notes-intent-preflight'],
            self.intent_readback_inputs(attempt_id),
            self.blocks['notes-intent-readback'],
            self.blocks['notes-intent-capture'],
            self.SHARED_CAPTURE_EPILOGUE,
        ]
        return self.run_sections(
            sections, observation_id='intent-capture-' + attempt_id)

    def run_candidate_two_route(self, *, attempt_id):
        return self.run_reveal_route(
            attempt_id=attempt_id, ordinal=2, control_visible='false',
            reveal_method='true', reveal='[40, 50, 100, 110]',
            reveal_candidate_id='candidate-2')

    def assert_no_files(self, names, *prefixes):
        for prefix in prefixes:
            matching = [name for name in names if name.startswith(prefix)]
            self.assertEqual(matching, [], msg=prefix)

    def test_a1_each_marker_encloses_one_js_block_in_document_order(self):
        text = TEMPLATE.read_text(encoding='utf-8')
        cursor = -1
        for name in BLOCK_MARKERS:
            start_marker = '<!-- %s:start -->' % name
            end_marker = '<!-- %s:end -->' % name
            start = text.index(start_marker)
            end = text.index(end_marker, start)
            self.assertGreater(start, cursor, name)
            cursor = end
            section = text[start:end]
            self.assertEqual(section.count('```js'), 1, name)
            self.assertEqual(section.count('```'), 2, name)
            code_start = section.index('```js') + len('```js')
            code_end = section.index('```', code_start)
            self.assertEqual(section[code_end + 3:].strip(), '', name)
        self.assertIn('let directReadiness = null',
                      self.blocks['notes-intent-preflight'])
        self.assertIn('let preIntentReveal = null',
                      self.blocks['notes-intent-preflight'])
        self.assertIn('const retainedReveal = preIntentReveal?.status',
                      self.blocks['notes-intent-preflight'])
        self.assertIn('const INTENT_READBACK = JSON.parse',
                      self.blocks['notes-intent-readback'])
        self.assertIn('const intentObservation', self.blocks['notes-intent-capture'])
        self.assertIn('async function dispatchDownload',
                      self.blocks['notes-download-builder'])
        self.assertIn('const directDispatchDecision',
                      self.blocks['notes-direct-dispatch'])
        self.assertIn('const beforeObservation = intentObservation',
                      self.blocks['notes-reveal-path'])
        self.assertIn('const revealCandidateArm = REVEAL_CANDIDATE_ORDINAL',
                      self.blocks['notes-reveal-path'])
        self.assertIn('const revealDownloadReceipt = await dispatchDownload',
                      self.blocks['notes-reveal-download'])

    def test_a1_visible_direct_ready_with_ready_alternate_selects_direct(self):
        result = self.run_direct_route(
            attempt_id='a1-case1', control_visible='true', reveal_method='true',
            direct=('[20, 30, 80, 90]', '[60, 70]', '[60, 70]'),
            reveal='[40, 50, 100, 110]')
        self.assertEqual(result['nextAction'], 'RUN_EXISTING_NOTES_INTENT_ONCE')
        self.assertEqual(result['directStatus'], 'READY')
        self.assertEqual(result['revealStatus'], 'READY')
        self.assertEqual(result['retainedStatus'], 'READY')
        self.assertEqual(result['retainedOrdinal'], 1)
        self.assertEqual(result['captureCalls'], 1)
        self.assertEqual(result['clickCalls'], 1)
        self.assertEqual(result['clickTargets'], [[60, 70]])
        self.assertEqual(result['directDownloadReceipt']['status'], 'INVOKED')
        self.assertEqual(result['directDownloadReceipt']['source_mode'],
                         'DIRECT_INTENT_OBSERVATION')
        self.assertEqual(result['directDownloadReceipt']['operation_id'],
                         'notes-download-a1-case1')
        self.assertEqual(result['intentCaptureBytes'],
                         list(b'SYNTHETIC_BLOCK_CAPTURE:1'))
        self.assertEqual(result['downloadDiagnostic']['dispatch_call_target'],
                         [60, 70])
        self.assertEqual(
            result['directDownloadReceipt']['source_observation']['path'],
            result['intentObservation']['assets']['screenshot']['path'])
        self.assertEqual(
            result['directDownloadReceipt']['receipt']['hostCalls'],
            result['downloadDiagnostic']['hostCalls'])
        self.assertLessEqual(
            result['intentObservation']['hostCalls']['capture_call_returned_at'],
            result['directDownloadReceipt']['receipt']['hostCalls']
                  ['dispatch_call_started_at'])
        self.assertNotEqual(result['intentObservation']['hostCalls']
                            ['capture_call_started_at'], 'NOT_RUN')
        self.assert_no_files(result['filesAfter'], 'notes-reveal-c2-')
        self.assertEqual(
            sorted(name for name in result['filesAfter']
                   if name.startswith('notes-download-a1-case1.')),
            ['notes-download-a1-case1.input.diagnostic.json',
             'notes-download-a1-case1.input.raw.json',
             'notes-download-a1-case1.input.request.json'])

    def test_a1_visible_direct_without_reveal_method_never_evaluates_reveal(self):
        result = self.run_direct_route(
            attempt_id='a1-case2', control_visible='true', reveal_method='false',
            direct=('[20, 30, 80, 90]', '[60, 70]', '[60, 70]'))
        self.assertEqual(result['nextAction'], 'RUN_EXISTING_NOTES_INTENT_ONCE')
        self.assertEqual(result['directStatus'], 'READY')
        self.assertIsNone(result['revealStatus'])
        self.assertIsNone(result['retainedStatus'])
        self.assertFalse(result['revealOrdinalDeclared'])
        self.assertEqual(result['captureCalls'], 1)
        self.assertEqual(result['clickCalls'], 1)
        self.assertEqual(result['clickTargets'], [[60, 70]])
        self.assertEqual(result['directDownloadReceipt']['status'], 'INVOKED')
        self.assert_no_files(result['filesAfter'], 'notes-reveal-c2-')

    def test_a1_visible_direct_with_reveal_stop_keeps_direct_and_null_retainer(self):
        result = self.run_direct_route(
            attempt_id='a1-case3', control_visible='true', reveal_method='true',
            direct=('[20, 30, 80, 90]', '[60, 70]', '[60, 70]'),
            reveal='[70, 80, 70, 90]')
        self.assertEqual(result['nextAction'], 'RUN_EXISTING_NOTES_INTENT_ONCE')
        self.assertEqual(result['directStatus'], 'READY')
        self.assertEqual(result['revealStatus'], 'STOP')
        self.assertEqual(result['revealReason'], 'DOWNLOAD_READINESS_BLOCKED')
        self.assertIn('REVEAL_SAFE_ZONE_INVALID',
                      result.get('revealBlockers') or [])
        self.assertIsNone(result['retainedStatus'])
        self.assertEqual(result['directDownloadReceipt']['status'], 'INVOKED')
        self.assertEqual(result['captureCalls'], 1)
        self.assertEqual(result['clickCalls'], 1)
        self.assert_no_files(result['filesAfter'], 'notes-reveal-c2-')

    def test_a1_initial_hidden_reveal_ready_uses_capture_reveal_and_same_after(self):
        result = self.run_reveal_route(
            attempt_id='a1-case4', control_visible='false', reveal_method='true',
            reveal='[40, 50, 100, 110]')
        self.assertEqual(result['nextAction'], 'RUN_EXISTING_NOTES_INTENT_ONCE')
        self.assertIsNone(result['directStatus'])
        self.assertEqual(result['revealStatus'], 'READY')
        self.assertEqual(result['retainedStatus'], 'READY')
        self.assertEqual(result['captureCalls'], 2)
        self.assertEqual(result['clickCalls'], 2)
        self.assertEqual(result['clickTargets'], [[70, 80], [60, 70]])
        self.assertEqual(result['revealRun']['status'], 'INVOKED')
        self.assertEqual(result['revealRun']['before_observation_id'],
                         result['intentObservation']['observation_id'])
        self.assertEqual(result['revealRun']['pre_intent_observation_id'],
                         result['preObservationId'])
        self.assertEqual(result['revealAfterBytes'],
                         list(b'SYNTHETIC_BLOCK_CAPTURE:2'))
        self.assertEqual(result['revealDownloadReceipt']['status'], 'INVOKED')
        self.assertEqual(result['revealDownloadReceipt']['source_mode'],
                         'REVEAL_SAME_AFTER')
        self.assertEqual(
            result['revealDownloadReceipt']['source_observation']['path'],
            result['revealAfter']['assets']['screenshot']['path'])
        self.assertNotEqual(result['revealAfter']['hostCalls']
                            ['capture_call_started_at'], 'UNKNOWN')
        self.assertEqual(result['afterDiagnostic']['hostCalls'],
                         result['revealAfter']['hostCalls'])
        self.assertEqual(
            result['revealDownloadReceipt']['receipt']['hostCalls'],
            result['downloadDiagnostic']['hostCalls'])
        self.assertLessEqual(
            result['revealAfter']['hostCalls']['capture_call_returned_at'],
            result['revealDownloadReceipt']['receipt']['hostCalls']
                  ['dispatch_call_started_at'])
        self.assertTrue(any(name.startswith('notes-reveal-c2-a1-case4')
                            for name in result['filesAfter']))
        self.assertEqual(
            sorted(name for name in result['filesAfter']
                   if name.startswith('notes-download-a1-case4.')),
            ['notes-download-a1-case4.input.diagnostic.json',
             'notes-download-a1-case4.input.raw.json',
             'notes-download-a1-case4.input.request.json'])

    def test_a1_unknown_visibility_and_hidden_without_reveal_stop_before_intent(self):
        for label, visible in (('unknown', 'null'), ('hidden-no-reveal', 'false')):
            with self.subTest(case=label):
                result = self.run_preflight_case(
                    control_visible=visible, reveal_method='false')
                self.assertEqual(result['nextAction'], 'B1_LOCAL_STOP')
                self.assertIsNone(result['directStatus'])
                self.assertIsNone(result['revealStatus'])
                self.assertIsNone(result['retainedStatus'])
                self.assertFalse(result['revealOrdinalDeclared'])
                self.assertEqual(result['captureCalls'], 0)
                self.assertEqual(result['clickCalls'], 0)
                self.assertEqual(result['filesAfter'], result['filesBefore'])

    def test_a1_visible_direct_stop_with_reveal_ready_stops_before_intent(self):
        result = self.run_preflight_case(
            control_visible='true', reveal_method='true',
            direct=('[20, 30, 80, 90]', '[20, 70]', '[20, 70]'),
            reveal='[40, 50, 100, 110]')
        self.assertEqual(result['nextAction'], 'B1_LOCAL_STOP')
        self.assertEqual(result['directStatus'], 'STOP')
        self.assertIn('DOWNLOAD_CONTROL_POINT_NOT_STRICT_INTERIOR',
                      result['directBlockers'])
        self.assertEqual(result['revealStatus'], 'READY')
        self.assertEqual(result['retainedStatus'], 'READY')
        self.assertEqual(result['captureCalls'], 0)
        self.assertEqual(result['clickCalls'], 0)
        self.assertEqual(result['filesAfter'], result['filesBefore'])

    def test_a1_visible_to_hidden_uses_shared_capture_then_reveal_after(self):
        result = self.run_reveal_route(
            attempt_id='a1-visible-hidden', control_visible='true',
            reveal_method='true',
            direct=('[20, 30, 80, 90]', '[60, 70]', '[60, 70]'),
            reveal='[40, 50, 100, 110]')
        self.assertEqual(result['nextAction'], 'RUN_EXISTING_NOTES_INTENT_ONCE')
        self.assertEqual(result['directStatus'], 'READY')
        self.assertEqual(result['retainedStatus'], 'READY')
        self.assertEqual(result['captureCalls'], 2)
        self.assertEqual(result['clickCalls'], 2)
        self.assertEqual(result['clickTargets'], [[70, 80], [60, 70]])
        self.assertEqual(result['revealRun']['status'], 'INVOKED')
        self.assertEqual(result['revealRun']['before_observation_id'],
                         result['intentObservation']['observation_id'])
        self.assertEqual(result['revealAfterBytes'],
                         list(b'SYNTHETIC_BLOCK_CAPTURE:2'))
        self.assertEqual(result['revealDownloadReceipt']['source_mode'],
                         'REVEAL_SAME_AFTER')
        self.assertEqual(
            result['revealDownloadReceipt']['source_observation']['path'],
            result['revealAfter']['assets']['screenshot']['path'])

    def test_a1_direct_ready_reveal_stop_then_hidden_keeps_only_shared_capture(self):
        result = self.run_shared_capture_stop(
            attempt_id='a1-hidden-stop', control_visible='true',
            reveal_method='true',
            direct=('[20, 30, 80, 90]', '[60, 70]', '[60, 70]'),
            reveal='[70, 80, 70, 90]')
        self.assertEqual(result['nextAction'], 'RUN_EXISTING_NOTES_INTENT_ONCE')
        self.assertEqual(result['directStatus'], 'READY')
        self.assertEqual(result['revealStatus'], 'STOP')
        self.assertIsNone(result['retainedStatus'])
        self.assertEqual(result['captureCalls'], 1)
        self.assertEqual(result['clickCalls'], 0)
        self.assertEqual(result['intentCaptureBytes'],
                         list(b'SYNTHETIC_BLOCK_CAPTURE:1'))
        self.assert_no_files(result['filesAfter'], 'notes-reveal-c2-')
        self.assert_no_files(result['filesAfter'], 'notes-download-')

    def test_a1_invalid_reveal_ordinal_stops_before_intent(self):
        result = self.run_preflight_case(
            control_visible='false', reveal_method='true',
            reveal='[40, 50, 100, 110]', ordinal=3,
            reveal_candidate_id='candidate-3')
        self.assertEqual(result['nextAction'], 'B1_LOCAL_STOP')
        self.assertEqual(result['revealStatus'], 'STOP')
        self.assertIn('REVEAL_ORDINAL_INVALID', result['revealBlockers'])
        self.assertIsNone(result['retainedStatus'])
        self.assertEqual(result['captureCalls'], 0)
        self.assertEqual(result['clickCalls'], 0)
        self.assertEqual(result['filesAfter'], result['filesBefore'])

    def test_a1_candidate_two_reveal_uses_ordinal_two_arm(self):
        result = self.run_candidate_two_route(attempt_id='a1-candidate-two')
        self.assertEqual(result['nextAction'], 'RUN_EXISTING_NOTES_INTENT_ONCE')
        self.assertEqual(result['revealStatus'], 'READY')
        self.assertEqual(result['retainedStatus'], 'READY')
        self.assertEqual(result['retainedOrdinal'], 2)
        self.assertEqual(result['revealRun']['status'], 'INVOKED')
        self.assertEqual(result['revealRun']['candidate_ordinal'], 2)
        self.assertEqual(result['revealRun']['pre_intent_observation_id'],
                         result['preObservationId'])
        self.assertEqual(result['revealRun']['before_observation_id'],
                         result['intentObservation']['observation_id'])
        self.assertEqual(result['revealSavedRequest']['candidate_ordinal'], 2)
        self.assertEqual(result['revealSavedRequest']['prior_candidate_refs'],
                         result['retainedPriorRefs'])
        self.assertEqual(result['revealSavedRequest']['budget_before'],
                         result['retainedBudgetBefore'])
        self.assertEqual(result['revealSavedRequest']['budget_after'],
                         result['retainedBudgetAfter'])
        self.assertEqual(result['revealRun']['operation_id'],
                         'notes-reveal-c2-a1-candidate-two')
        self.assertEqual(result['revealRun']['inputStatus'], 'INVOKED')
        self.assertEqual(result['captureCalls'], 2)
        self.assertEqual(result['clickCalls'], 2)
        self.assertEqual(result['clickTargets'], [[70, 80], [60, 70]])
        self.assertEqual(result['revealAfterBytes'],
                         list(b'SYNTHETIC_BLOCK_CAPTURE:2'))
        self.assertEqual(result['revealDownloadReceipt']['source_mode'],
                         'REVEAL_SAME_AFTER')
        self.assertEqual(
            result['revealDownloadReceipt']['source_observation']['path'],
            result['revealAfter']['assets']['screenshot']['path'])
        self.assertIn('notes-reveal-c2-a1-candidate-two.input.request.json',
                      result['filesAfter'])
        self.assertIn('notes-download-a1-candidate-two.input.request.json',
                      result['filesAfter'])

    def test_a2_stale_assets_reused_path_and_reused_id_reject_before_input(self):
        result = self.run_sections([DISPATCH_SETUP, r'''
const counters = {clicks: 0, captures: 0};
const app = {
  async click(target) { counters.clicks += 1; return {target}; },
  async getAXStateAndScreenshot() {
    counters.captures += 1;
    return {state: '{"role":"AXWindow"}',
            screenshot: new TextEncoder().encode('A2-AFTER')};
  },
};
const windowBinding = dispatchWindowBinding({window_id: 4242});
const pre = await dispatchObservation('a2-pre', dispatchFreshCapture('a2-pre'));
const preIntentReveal = notesIntentDispatch.checkDownloadReadiness({
  app, observation: pre, windowBinding, branch: 'REVEAL',
  decision: dispatchRevealReadinessDecision(pre, 1),
});
const before = await dispatchObservation(
  'a2-before', dispatchFreshCapture('a2-before'));
const acceptBefore = await dispatchObservation(
  'a2-accept-before', dispatchFreshCapture('a2-pre'));
const options = (attemptId, beforeObservation, request) => ({
  ...dispatchPaths(),
  intent: dispatchIntent(attemptId),
  intentEventRef: dispatchEventRef(),
  request,
  app,
  preIntentReveal,
  beforeObservation,
  windowBinding,
});
const rejectionCases = [
  ['screenshot-stale',
   {...before, assets: {...before.assets, screenshot: pre.assets.screenshot}}],
  ['ax-stale',
   {...before, assets: {...before.assets, ax: pre.assets.ax}}],
  ['path-reused-changed-refs',
   {...before, assets: {...before.assets, screenshot: {
     ...pre.assets.screenshot,
     bytes: pre.assets.screenshot.bytes + 9,
     sha256: 'f'.repeat(64),
   }}}],
  ['observation-id-reused', {...before, observation_id: pre.observation_id}],
];
const beforeFiles = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
const rejected = [];
for (const [label, beforeObservation] of rejectionCases) {
  const attemptId = 'attempt-a2-' + label;
  rejected.push([label, await notesIntentDispatch.persistReveal(
    options(attemptId, beforeObservation,
            dispatchRevealRequest(attemptId, before)))]);
}
const acceptRequest = dispatchRevealRequest('attempt-a2-accept', acceptBefore);
const acceptReadiness = notesIntentDispatch.checkDownloadReadiness({
  app, observation: acceptBefore, windowBinding, branch: 'REVEAL',
  decision: acceptRequest,
});
const accepted = await notesIntentDispatch.persistReveal(
  options('attempt-a2-accept', acceptBefore, acceptRequest));
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {
  rejected: rejected.map(([label, outcome]) => ({
    label, status: outcome.status, reason: outcome.reason,
  })),
  acceptReadiness,
  accepted,
  counters,
  beforeFiles,
  filesAfter,
  preScreenshot: pre.assets.screenshot,
  acceptScreenshot: acceptBefore.assets.screenshot,
};
'''])
        for item in result['rejected']:
            with self.subTest(case=item['label']):
                self.assertEqual(item['status'], 'STOP')
                self.assertEqual(item['reason'],
                                 'REVEAL_BEFORE_OBSERVATION_NOT_FRESH')
        self.assertEqual(result['acceptReadiness']['status'], 'READY')
        self.assertEqual(result['accepted']['status'], 'INVOKED')
        self.assertEqual(result['accepted']['reason'], None)
        self.assertEqual(result['counters'], {'clicks': 1, 'captures': 1})
        self.assertNotEqual(result['preScreenshot']['path'],
                            result['acceptScreenshot']['path'])
        self.assertEqual(result['preScreenshot']['sha256'],
                         result['acceptScreenshot']['sha256'])
        for label in ('screenshot-stale', 'ax-stale',
                      'path-reused-changed-refs', 'observation-id-reused'):
            self.assert_no_files(result['filesAfter'],
                                 'notes-reveal-c2-attempt-a2-' + label)
        self.assertTrue(any(name.startswith('notes-reveal-c2-attempt-a2-accept')
                            for name in result['filesAfter']))

    def test_a3_reveal_snapshot_survives_deferred_caller_mutation_once(self):
        result = self.run_sections([DISPATCH_SETUP, r'''
const fsNative = await import('node:fs');
const counters = {clicks: 0, captures: 0, targets: []};
const gate = new Promise(resolve => setTimeout(resolve, 0));
const app = {
  async click(target) {
    counters.clicks += 1;
    counters.targets.push(target);
    await gate;
    return {target};
  },
  async getAXStateAndScreenshot() {
    counters.captures += 1;
    await gate;
    return dispatchFreshCapture('a3-after');
  },
};
const windowBinding = dispatchWindowBinding({window_id: 4242});
const stage = await dispatchRevealStage(
  'attempt-a3-mutate', 1, windowBinding);
const options = dispatchGatedRevealOptions(stage, app);
const original = {
  candidateOrdinal: stage.request.candidate_ordinal,
  priorCandidateRefs: stage.request.prior_candidate_refs,
  safeZone: [...stage.request.safe_zone],
  preparedTarget: [...stage.request.prepared_target],
  preIntentObservationId: stage.preObservation.observation_id,
  beforeObservationId: stage.beforeObservation.observation_id,
  beforeScreenshotPath: stage.beforeObservation.assets.screenshot.path,
};
const pending = notesIntentDispatch.persistReveal(options);
options.request.prepared_target = [9999, 9999];
options.request.safe_zone = [-1000, -1000, -1, -1];
options.request.candidate_ordinal = 99;
options.request.before_screenshot_ref.path = '/ABS/MUTATED_SCREENSHOT';
options.preIntentReveal.observation_id = 'mutated-pre';
options.beforeObservation.observation_id = 'mutated-before';
const requestExistedAtMutation = fsNative.existsSync(
  process.env.INPUT_TEST_DIR +
  '/notes-reveal-c2-attempt-a3-mutate.input.request.json');
const run = await pending;
const saved = JSON.parse(await fsTest.readFile(
  run.run.inputReceipt.files.request, 'utf8'));
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {
  run,
  savedRequest: saved.request,
  counters,
  original,
  requestExistedAtMutation,
  filesAfter,
};
'''])
        self.assertEqual(result['run']['status'], 'INVOKED')
        self.assertEqual(result['run']['reason'], None)
        self.assertEqual(result['run']['candidate_ordinal'], 1)
        self.assertEqual(result['run']['pre_intent_observation_id'],
                         result['original']['preIntentObservationId'])
        self.assertEqual(result['run']['before_observation_id'],
                         result['original']['beforeObservationId'])
        self.assertEqual(result['run']['run']['inputReceipt']['status'],
                         'INVOKED')
        self.assertEqual(result['savedRequest']['candidate_ordinal'], 1)
        self.assertEqual(result['savedRequest']['safe_zone'], [40, 50, 100, 110])
        self.assertEqual(result['savedRequest']['prepared_target'], [70, 80])
        self.assertEqual(result['savedRequest']['before_screenshot_ref']['path'],
                         result['original']['beforeScreenshotPath'])
        self.assertEqual(result['counters']['clicks'], 1)
        self.assertEqual(result['counters']['captures'], 1)
        self.assertEqual(result['counters']['targets'], [[70, 80]])
        self.assertFalse(result['requestExistedAtMutation'])
        self.assertTrue(any(
            name.startswith('notes-reveal-c2-attempt-a3-mutate.input.request')
            for name in result['filesAfter']))

    def test_a3_missing_or_unserializable_request_stops_before_slot_and_input(self):
        result = self.run_sections([DISPATCH_SETUP, r'''
const counters = {clicks: 0, captures: 0};
const app = {
  async click(target) { counters.clicks += 1; return {target}; },
  async getAXStateAndScreenshot() {
    counters.captures += 1;
    return dispatchFreshCapture('a3-stop-after');
  },
};
const windowBinding = dispatchWindowBinding({window_id: 4242});
const missingStage = await dispatchRevealStage(
  'attempt-a3-missing-request', 1, windowBinding);
const missing = await notesIntentDispatch.persistReveal({
  ...dispatchGatedRevealOptions(missingStage, app),
  request: undefined,
});
const badStage = await dispatchRevealStage(
  'attempt-a3-unserializable', 1, windowBinding);
const circular = {...badStage.request};
circular.self = circular;
const unserializable = await notesIntentDispatch.persistReveal({
  ...dispatchGatedRevealOptions(badStage, app),
  request: circular,
});
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {counters, missing, unserializable, filesAfter};
'''])
        self.assertEqual(result['missing']['status'], 'STOP')
        self.assertEqual(result['missing']['reason'], 'REVEAL_REQUEST_REQUIRED')
        self.assertEqual(result['unserializable']['status'], 'STOP')
        self.assertEqual(result['unserializable']['reason'],
                         'REVEAL_REQUEST_SERIALIZATION_FAILED')
        self.assertIn('REVEAL_REQUEST_SERIALIZATION_FAILED',
                      result['unserializable']['blockers'])
        self.assertEqual(result['counters'], {'clicks': 0, 'captures': 0})
        for attempt in ('attempt-a3-missing-request',
                        'attempt-a3-unserializable'):
            self.assert_no_files(result['filesAfter'],
                                 'notes-reveal-c2-' + attempt)
            self.assert_no_files(result['filesAfter'],
                                 'notes-reveal-c2-' + attempt + '-after')

    def test_a4_observation_host_calls_success_throw_and_pre_call_rejection(self):
        result = self.run_sections([r'''
const fsTest = await import('node:fs/promises');
const paths = () => ({
  taskDir: process.env.INPUT_TEST_ROOT,
  observationDir: process.env.INPUT_TEST_DIR,
});
globalThis.cua = {
  getApp: async () => ({
    getAXStateAndScreenshot: async () => ({
      state: '{"role":"AXWindow"}',
      screenshot: new TextEncoder().encode('OBSERVATION-OK'),
    }),
  }),
};
const ok = await evidenceTools.captureAndPersist({
  ...paths(), observationId: 'a4-observation-ok'});
const okDiagnostic = JSON.parse(await fsTest.readFile(
  ok.files.diagnostic, 'utf8'));
globalThis.cua = {
  getApp: async () => ({
    getAXStateAndScreenshot: async () => {
      throw new Error('synthetic capture throw');
    },
  }),
};
const thrown = await evidenceTools.captureAndPersist({
  ...paths(), observationId: 'a4-observation-throw'});
const thrownDiagnostic = JSON.parse(await fsTest.readFile(
  thrown.files.diagnostic, 'utf8'));
globalThis.cua = {
  getApp: async () => {
    throw new Error('synthetic pre-call rejection');
  },
};
const preCall = await evidenceTools.captureAndPersist({
  ...paths(), observationId: 'a4-observation-pre-call'});
const preCallDiagnostic = JSON.parse(await fsTest.readFile(
  preCall.files.diagnostic, 'utf8'));
const bare = await evidenceTools.persistObservation({
  ...paths(), observationId: 'a4-observation-bare',
  capture: {state: '{"role":"AXWindow"}',
            screenshot: new TextEncoder().encode('BARE')},
});
return {ok, okDiagnostic, thrown, thrownDiagnostic,
        preCall, preCallDiagnostic, bare};
'''])
        ok_calls = result['ok']['hostCalls']
        thrown_calls = result['thrown']['hostCalls']
        pre_calls = result['preCall']['hostCalls']
        self.assertTrue(result['ok']['ready_for_bind'])
        self.assertEqual(ok_calls['clock_source'], 'HOST_JS_DATE')
        self.assertEqual(ok_calls['precision'], 'CALL_BOUNDARY_ONLY')
        self.assertEqual(ok_calls['os_event_time'], 'UNKNOWN')
        self.assertNotEqual(ok_calls['capture_call_started_at'], 'NOT_RUN')
        self.assertNotEqual(ok_calls['capture_call_returned_at'], 'NOT_RUN')
        self.assertLessEqual(ok_calls['capture_call_started_at'],
                             ok_calls['capture_call_returned_at'])
        self.assertEqual(result['okDiagnostic']['hostCalls'], ok_calls)

        self.assertFalse(result['thrown']['ready_for_bind'])
        self.assertEqual(result['thrown']['blockers'], ['CAPTURE:FAILED'])
        self.assertNotEqual(thrown_calls['capture_call_started_at'], 'NOT_RUN')
        self.assertNotEqual(thrown_calls['capture_call_returned_at'], 'NOT_RUN')
        self.assertLessEqual(thrown_calls['capture_call_started_at'],
                             thrown_calls['capture_call_returned_at'])
        self.assertEqual(result['thrownDiagnostic']['hostCalls'], thrown_calls)

        self.assertFalse(result['preCall']['ready_for_bind'])
        self.assertEqual(result['preCall']['blockers'], ['CAPTURE:FAILED'])
        for key in ('capture_call_started_at', 'capture_call_returned_at'):
            self.assertEqual(pre_calls[key], 'NOT_RUN')
            self.assertEqual(result['preCallDiagnostic']['hostCalls'][key],
                             'NOT_RUN')
        self.assertEqual(result['bare']['hostCalls'], pre_calls)

    def test_a4_grounded_dispatch_host_calls_success_throw_and_pre_call_rejection(self):
        result = self.run_sections([GROUNDED_SETUP, r'''
let successClicks = 0;
const success = await evidenceTools.persistGroundedDownloadClick(
  makeGroundedOptions('a4-dispatch-success', async target => {
    successClicks += 1;
    return {native_code: 0, target};
  }));
const successDiagnostic = await readJson(success.files.diagnostic);
let throwClicks = 0;
const throwError = Object.assign(new Error('synthetic native throw'), {code: 91});
const thrown = await evidenceTools.persistGroundedDownloadClick(
  makeGroundedOptions('a4-dispatch-throw', async () => {
    throwClicks += 1;
    throw throwError;
  }));
const thrownDiagnostic = await readJson(thrown.files.diagnostic);
let gateClicks = 0;
const gateOptions = makeGroundedOptions('a4-dispatch-gate', async () => {
  gateClicks += 1;
  return {ok: true};
});
gateOptions.request.mapping_status = 'UNKNOWN';
const gate = await evidenceTools.persistGroundedDownloadClick(gateOptions);
const gateDiagnostic = await readJson(gate.files.diagnostic);
let slotClicks = 0;
const slotOptions = makeGroundedOptions('a4-dispatch-slot', async target => {
  slotClicks += 1;
  return {target};
});
await fsTest.writeFile(
  process.env.INPUT_TEST_DIR + '/a4-dispatch-slot.input.request.json',
  'keep slot sentinel', {flag: 'wx'});
const slot = await evidenceTools.persistGroundedDownloadClick(slotOptions);
const slotDiagnostic = await readJson(slot.files.diagnostic);
return {success, successDiagnostic, successClicks,
        thrown, thrownDiagnostic, throwClicks,
        gate, gateDiagnostic, gateClicks,
        slot, slotDiagnostic, slotClicks};
'''])
        success_calls = result['success']['hostCalls']
        self.assertEqual(result['success']['status'], 'INVOKED')
        self.assertEqual(result['successClicks'], 1)
        self.assertEqual(result['success']['native_return_type'], 'VALUE')
        self.assertEqual(result['success']['dispatch_call_target'], [60, 70])
        self.assertEqual(success_calls['clock_source'], 'HOST_JS_DATE')
        self.assertEqual(success_calls['precision'], 'CALL_BOUNDARY_ONLY')
        self.assertEqual(success_calls['os_event_time'], 'UNKNOWN')
        self.assertNotEqual(success_calls['dispatch_call_started_at'], 'NOT_RUN')
        self.assertNotEqual(success_calls['dispatch_call_returned_at'], 'NOT_RUN')
        self.assertLessEqual(success_calls['dispatch_call_started_at'],
                             success_calls['dispatch_call_returned_at'])
        self.assertEqual(result['successDiagnostic']['hostCalls'], success_calls)
        self.assertEqual(result['successDiagnostic']['dispatch_call_target'],
                         [60, 70])

        thrown_calls = result['thrown']['hostCalls']
        self.assertEqual(result['throwClicks'], 1)
        self.assertEqual(result['thrown']['status'], 'INVOKED')
        self.assertEqual(result['thrown']['native_return_type'], 'ERROR')
        self.assertNotEqual(thrown_calls['dispatch_call_started_at'], 'NOT_RUN')
        self.assertNotEqual(thrown_calls['dispatch_call_returned_at'], 'NOT_RUN')
        self.assertLessEqual(thrown_calls['dispatch_call_started_at'],
                             thrown_calls['dispatch_call_returned_at'])
        self.assertEqual(result['thrownDiagnostic']['hostCalls'], thrown_calls)

        self.assertEqual(result['gateClicks'], 0)
        self.assertEqual(result['gate']['status'],
                         'DOWNLOAD_CONTROL_GROUNDING_INVALID')
        for key in ('dispatch_call_started_at', 'dispatch_call_returned_at'):
            self.assertEqual(result['gate']['hostCalls'][key], 'NOT_RUN')
            self.assertEqual(result['gateDiagnostic']['hostCalls'][key], 'NOT_RUN')

        self.assertEqual(result['slotClicks'], 0)
        self.assertEqual(result['slot']['status'], 'REQUEST_PERSIST_FAILED')
        for key in ('dispatch_call_started_at', 'dispatch_call_returned_at'):
            self.assertEqual(result['slot']['hostCalls'][key], 'NOT_RUN')
            self.assertEqual(result['slotDiagnostic']['hostCalls'][key], 'NOT_RUN')

    def test_a4_intent_capture_throw_records_host_calls_without_input(self):
        result = self.run_sections([
            self.preflight_prelude(
                control_visible='true', reveal_method='false',
                direct=('[20, 30, 80, 90]', '[60, 70]', '[60, 70]')),
            self.blocks['notes-intent-preflight'],
            self.intent_readback_inputs('a4-capture-throw'),
            self.blocks['notes-intent-readback'],
            r'''
app.getAXStateAndScreenshot = async () => {
  caseCounters.captures += 1;
  throw new Error('synthetic block capture throw');
};
''',
            self.blocks['notes-intent-capture'],
            r'''
const diagnostic = JSON.parse(await fsTest.readFile(
  intentObservation.files.diagnostic, 'utf8'));
return {
  intentObservation,
  diagnosticHostCalls: diagnostic.hostCalls,
  diagnosticBlockers: diagnostic.blockers,
  captureCalls: caseCounters.captures,
  clickCalls: caseCounters.clicks,
};
''',
        ], observation_id='a4-capture-throw-after')
        self.assertEqual(result['captureCalls'], 1)
        self.assertEqual(result['clickCalls'], 0)
        self.assertFalse(result['intentObservation']['ready_for_bind'])
        self.assertEqual(result['intentObservation']['blockers'],
                         ['CAPTURE:FAILED'])
        host_calls = result['intentObservation']['hostCalls']
        self.assertEqual(host_calls['clock_source'], 'HOST_JS_DATE')
        self.assertEqual(host_calls['precision'], 'CALL_BOUNDARY_ONLY')
        self.assertEqual(host_calls['os_event_time'], 'UNKNOWN')
        self.assertNotEqual(host_calls['capture_call_started_at'], 'NOT_RUN')
        self.assertNotEqual(host_calls['capture_call_returned_at'], 'NOT_RUN')
        self.assertLessEqual(host_calls['capture_call_started_at'],
                             host_calls['capture_call_returned_at'])
        self.assertEqual(result['diagnosticHostCalls'], host_calls)
        self.assertEqual(result['diagnosticBlockers'], ['CAPTURE:FAILED'])

    def test_a5_missing_stop_or_direct_preflight_rejects_with_zero_input(self):
        result = self.run_sections([DISPATCH_SETUP, r'''
const counters = {clicks: 0, captures: 0};
const app = {
  async click(target) { counters.clicks += 1; return {target}; },
  async getAXStateAndScreenshot() {
    counters.captures += 1;
    return dispatchFreshCapture('a5-preflight-after');
  },
};
const windowBinding = dispatchWindowBinding({window_id: 4242});
const stage = await dispatchRevealStage(
  'attempt-a5-preflight', 1, windowBinding);
const directReadiness = notesIntentDispatch.checkDownloadReadiness({
  app, observation: stage.beforeObservation, windowBinding, branch: 'DIRECT',
  decision: dispatchDirectReadinessDecision(stage.beforeObservation),
});
const stopReadiness = notesIntentDispatch.checkDownloadReadiness({
  app, observation: stage.preObservation, windowBinding, branch: 'REVEAL',
  decision: dispatchRevealReadinessDecision(
    stage.preObservation, 1, {selected_state_before: 'UNKNOWN'}),
});
const options = (attemptId, preIntentReveal) => ({
  ...dispatchPaths(),
  intent: dispatchIntent(attemptId),
  intentEventRef: dispatchEventRef(),
  request: dispatchRevealRequest(attemptId, stage.beforeObservation),
  app,
  preIntentReveal,
  beforeObservation: stage.beforeObservation,
  windowBinding,
});
const beforeFiles = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
const cases = [
  ['missing', options('attempt-a5-missing', undefined)],
  ['stop', options('attempt-a5-stop', stopReadiness)],
  ['direct', options('attempt-a5-direct', directReadiness)],
];
const results = [];
for (const [label, caseOptions] of cases) {
  results.push([label, await notesIntentDispatch.persistReveal(caseOptions)]);
}
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {results: results.map(([label, outcome]) => ({
  label, status: outcome.status, reason: outcome.reason,
})), counters, beforeFiles, filesAfter, stopReadiness, directReadiness};
'''])
        self.assertEqual(result['stopReadiness']['status'], 'STOP')
        self.assertEqual(result['directReadiness']['status'], 'READY')
        for item in result['results']:
            with self.subTest(case=item['label']):
                self.assertEqual(item['status'], 'STOP')
                self.assertEqual(item['reason'], 'REVEAL_PREFLIGHT_REQUIRED')
        self.assertEqual(result['counters'], {'clicks': 0, 'captures': 0})
        for attempt in ('attempt-a5-missing', 'attempt-a5-stop',
                        'attempt-a5-direct'):
            self.assert_no_files(result['filesAfter'],
                                 'notes-reveal-c2-' + attempt)

    def test_a5_reveal_request_drift_and_ordinal_budget_drift_zero_input(self):
        result = self.run_sections([DISPATCH_SETUP, r'''
const counters = {clicks: 0, captures: 0};
const app = {
  async click(target) { counters.clicks += 1; return {target}; },
  async getAXStateAndScreenshot() {
    counters.captures += 1;
    return dispatchFreshCapture('a5-drift-after');
  },
};
const windowBinding = dispatchWindowBinding({window_id: 4242});
const stageOne = await dispatchRevealStage(
  'attempt-a5-drift-one', 1, windowBinding);
const stageTwo = await dispatchRevealStage(
  'attempt-a5-drift-two', 2, windowBinding);
const options = (attemptId, request, stage) => ({
  ...dispatchPaths(),
  intent: dispatchIntent(attemptId),
  intentEventRef: dispatchEventRef(),
  request: {...request, attempt_id: attemptId},
  app,
  preIntentReveal: stage.preIntentReveal,
  beforeObservation: stage.beforeObservation,
  windowBinding,
});
const cases = [
  ['ordinal-drift',
   options('attempt-a5-ordinal-drift',
     {...stageOne.request, candidate_ordinal: 2,
      prior_candidate_refs: ['prior-candidate-receipt'],
      budget_before: 1, budget_after: 2,
      rearm_preconditions_ref: 'prior-candidate-after',
      rearm_new_information_ref: 'current-tool-document',
      rearm_new_information_conclusion: 'PASS'}, stageOne)],
  ['budget-before-drift',
   options('attempt-a5-budget-before',
     {...stageOne.request, budget_before: 1}, stageOne)],
  ['budget-after-drift',
   options('attempt-a5-budget-after',
     {...stageOne.request, budget_after: 2}, stageOne)],
  ['prior-refs-drift',
   options('attempt-a5-prior-refs',
     {...stageOne.request, prior_candidate_refs: ['other-prior-ref']},
     stageOne)],
  ['ordinal-two-prior-refs-drift',
   options('attempt-a5-ordinal-two-prior',
     {...stageTwo.request, prior_candidate_refs: ['other-prior-ref']},
     stageTwo)],
];
const beforeFiles = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
const results = [];
for (const [label, caseOptions] of cases) {
  results.push([label, await notesIntentDispatch.persistReveal(caseOptions)]);
}
const filesAfter = (await fsTest.readdir(process.env.INPUT_TEST_DIR)).sort();
return {results: results.map(([label, outcome]) => ({
  label, status: outcome.status, reason: outcome.reason,
})), counters, beforeFiles, filesAfter};
'''])
        expected = {
            'ordinal-drift': 'REVEAL_REQUEST_DRIFT',
            'budget-before-drift': 'REVEAL_ORDINAL_BUDGET_MISMATCH',
            'budget-after-drift': 'REVEAL_ORDINAL_BUDGET_MISMATCH',
            'prior-refs-drift': 'REVEAL_ORDINAL_BUDGET_MISMATCH',
            'ordinal-two-prior-refs-drift': 'REVEAL_REQUEST_DRIFT',
        }
        self.assertEqual({item['label']: item['reason']
                          for item in result['results']}, expected)
        for item in result['results']:
            with self.subTest(case=item['label']):
                self.assertEqual(item['status'], 'STOP')
        self.assertEqual(result['counters'], {'clicks': 0, 'captures': 0})
        for label in expected:
            self.assert_no_files(result['filesAfter'],
                                 'notes-reveal-c2-attempt-a5-' + label)


class NotesInitialObservationBlockTests(NodeHelperRunner):
    INITIAL_HARNESS = r'''
const fsSync = await import('node:fs');
const initialWritesFile = process.env.INITIAL_WRITES_FILE;
const initialEmitsFile = process.env.INITIAL_EMITS_FILE;
const initialCaptureCallsFile = process.env.INITIAL_CAPTURE_CALLS_FILE;
let initialCaptureCalls = 0;
globalThis.cua = {
  getApp: async bundleId => {
    if (bundleId !== 'jp.naver.line.mac') {
      throw new Error('UNEXPECTED_BUNDLE_ID: ' + bundleId);
    }
    return {
      getAXStateAndScreenshot: async options => {
        initialCaptureCalls += 1;
        fsSync.writeFileSync(initialCaptureCallsFile,
                             String(initialCaptureCalls));
        if (options.emit !== false || options.disableDiffing !== true) {
          throw new Error('UNEXPECTED_CAPTURE_OPTIONS');
        }
@@CAPTURE_BODY@@
      },
    };
  },
};
const nodeRepl = {
  writes: [],
  emitted: [],
  write(value) {
    const text = String(value);
    this.writes.push(text);
    fsSync.appendFileSync(initialWritesFile, JSON.stringify(text) + '\n');
    if (process.env.INITIAL_TAMPER && this.writes.length === 1) {
      const screenshotPath = OBSERVATION.assets.screenshot.path;
      if (process.env.INITIAL_TAMPER === 'SCREENSHOT_APPEND') {
        fsSync.appendFileSync(screenshotPath, new Uint8Array([0x00]));
      } else if (process.env.INITIAL_TAMPER === 'AX_REWRITE_SAME_LENGTH') {
        const axPath = OBSERVATION.assets.ax.path;
        const mutated = Buffer.from(fsSync.readFileSync(axPath));
        mutated[0] = mutated[0] === 0x7b ? 0x5b : 0x7b;
        fsSync.writeFileSync(axPath, mutated);
      }
    }
  },
  async emitImage(value) {
    const entry = {
      isUint8Array: value instanceof Uint8Array,
      bytes: Array.from(value),
    };
    this.emitted.push(entry);
    fsSync.appendFileSync(initialEmitsFile, JSON.stringify(entry) + '\n');
  },
};
'''

    CAPTURE_OK = r'''
        return {
          state: '{"role":"AXWindow","marker":"initial-observation"}',
          screenshot: new Uint8Array([
            0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
            0xde, 0xad, 0xbe, 0xef,
          ]),
        };
'''

    CAPTURE_THROW = r'''
        throw Object.assign(new Error('synthetic initial capture throw'),
                            {code: 'ESYNTHETIC'});
'''

    SUCCESS_EPILOGUE = r'''
const fs = await import('node:fs/promises');
const savedScreenshot = await fs.readFile(OBSERVATION.assets.screenshot.path);
const savedAx = await fs.readFile(OBSERVATION.assets.ax.path, 'utf8');
const diagnostic = JSON.parse(
  await fs.readFile(OBSERVATION.files.diagnostic, 'utf8'));
console.log(JSON.stringify({
  captureCalls: initialCaptureCalls,
  observation: OBSERVATION,
  savedScreenshotBytes: Array.from(savedScreenshot),
  savedAx,
  diagnostic,
  emitted: nodeRepl.emitted,
  writes: nodeRepl.writes,
}));
'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.initial_source = documented_initial_observation_source()

    def run_initial_observation(self, *, capture_body,
                                create_observation_dir=True, tamper=None,
                                epilogue='', tools_mode='tools'):
        with tempfile.TemporaryDirectory(
                prefix='.notes-initial-observation-', dir=TASKS) as temp:
            root = Path(temp).resolve()
            observation_dir = root / 'observations'
            if create_observation_dir:
                observation_dir.mkdir()
            writes_file = root / 'node-writes.jsonl'
            emits_file = root / 'node-emits.jsonl'
            calls_file = root / 'capture-calls.txt'
            observation_id = 'initial-observation-sample'
            source = (self.initial_source
                      .replace('/ABS/TASK_PRIVATE_DIR', str(root))
                      .replace('/ABS/OBSERVATION_DIR', str(observation_dir))
                      .replace('UNIQUE_OBSERVATION_ID', observation_id))
            if tools_mode == 'tools':
                preload = self.tools_source
            elif tools_mode == 'none':
                preload = ''
            elif tools_mode == 'empty':
                preload = 'const evidenceTools = {};'
            elif tools_mode == 'stub-missing-boundary':
                preload = (
                    'const evidenceTools = {\n'
                    '  captureAndPersist: async () => ({\n'
                    '    ready_for_bind: true, blockers: [],\n'
                    "    observation_id: 'stub-observation', files: {},\n"
                    "    stages: {CAPTURE_BOUNDARY: {status: 'MISSING'}},\n"
                    '    assets: {},\n'
                    '  }),\n'
                    '};\n'
                )
            else:
                raise AssertionError('unknown tools_mode: %r' % (tools_mode,))
            script = '\n'.join([
                preload,
                self.INITIAL_HARNESS.replace('@@CAPTURE_BODY@@', capture_body),
                source,
                epilogue,
            ])
            env = dict(
                os.environ,
                INITIAL_WRITES_FILE=str(writes_file),
                INITIAL_EMITS_FILE=str(emits_file),
                INITIAL_CAPTURE_CALLS_FILE=str(calls_file),
            )
            if tamper:
                env['INITIAL_TAMPER'] = tamper
            completed = subprocess.run(
                ['node', '--input-type=module', '-e', script],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            writes = ([json.loads(line) for line in
                       writes_file.read_text(encoding='utf-8').splitlines()]
                      if writes_file.is_file() else [])
            emits = ([json.loads(line) for line in
                      emits_file.read_text(encoding='utf-8').splitlines()]
                     if emits_file.is_file() else [])
            screenshot_path = observation_dir / (observation_id + '.screenshot.bin')
            ax_path = observation_dir / (observation_id + '.ax.txt')
            diagnostic_path = observation_dir / (observation_id + '.diagnostic.json')
            return {
                'returncode': completed.returncode,
                'stdout': completed.stdout,
                'stderr': completed.stderr,
                'writes': writes,
                'emits': emits,
                'captureCalls': (int(calls_file.read_text(encoding='utf-8'))
                                 if calls_file.is_file() else 0),
                'observationDirExists': observation_dir.is_dir(),
                'screenshotBytes': (list(screenshot_path.read_bytes())
                                    if screenshot_path.is_file() else None),
                'axText': (ax_path.read_text(encoding='utf-8')
                           if ax_path.is_file() else None),
                'diagnostic': (
                    json.loads(diagnostic_path.read_text(encoding='utf-8'))
                    if diagnostic_path.is_file() else None),
                'fileNames': (sorted(path.name for path in observation_dir.iterdir())
                              if observation_dir.is_dir() else []),
            }

    def test_initial_observation_marker_encloses_one_js_block(self):
        text = TEMPLATE.read_text(encoding='utf-8')
        self.assertEqual(text.count(INITIAL_START), 1)
        self.assertEqual(text.count(INITIAL_END), 1)
        start = text.index(INITIAL_START)
        end = text.index(INITIAL_END, start)
        section = text[start:end]
        self.assertEqual(section.count('```js'), 1)
        self.assertEqual(section.count('```'), 2)
        code_start = section.index('```js') + len('```js')
        code_end = section.index('```', code_start)
        self.assertEqual(section[code_end + 3:].strip(), '')
        source = documented_initial_observation_source()
        self.assertIn('const OBSERVATION = await evidenceTools.captureAndPersist',
                      source)
        self.assertIn('CUA_RAW_OBSERVATION_INCOMPLETE', source)
        self.assertIn('CUA_EVIDENCE_TOOLS_NOT_LOADED', source)
        self.assertIn('CAPTURE_BOUNDARY', source)
        self.assertIn('CAPTURE_BOUNDARY:MISSING', source)
        self.assertIn('CUA_OBSERVATION_EMIT_READBACK_MISMATCH', source)
        self.assertIn("const fs = await import('node:fs/promises');", source)
        self.assertIn('await nodeRepl.emitImage(new Uint8Array(savedScreenshot));',
                      source)
        self.assertIn("nodeRepl.write(savedAx.toString('utf8'));", source)
        self.assertEqual(section.count('nodeRepl.emitImage'), 1)

    def test_initial_observation_unloaded_tools_fails_closed_without_capture_or_emit(self):
        for tools_mode in ('none', 'empty'):
            with self.subTest(tools_mode=tools_mode):
                run = self.run_initial_observation(
                    capture_body=self.CAPTURE_OK, tools_mode=tools_mode)
                self.assertNotEqual(run['returncode'], 0)
                self.assertIn('CUA_EVIDENCE_TOOLS_NOT_LOADED', run['stderr'])
                self.assertNotIn('ReferenceError', run['stderr'])
                self.assertEqual(run['captureCalls'], 0)
                self.assertEqual(run['emits'], [])
                self.assertEqual(run['writes'], [])
                self.assertTrue(run['observationDirExists'])
                self.assertEqual(run['fileNames'], [])

    def test_initial_observation_success_emits_landed_bytes_once(self):
        run = self.run_initial_observation(
            capture_body=self.CAPTURE_OK, epilogue=self.SUCCESS_EPILOGUE)
        self.assertEqual(run['returncode'], 0, msg=run['stderr'])
        result = json.loads(run['stdout'])
        observation = result['observation']
        self.assertTrue(observation['ready_for_bind'])
        self.assertEqual(observation['blockers'], [])
        self.assertEqual(observation['stages']['PRIVATE_PATHS']['status'], 'OK')
        self.assertEqual(observation['stages']['CAPTURE']['status'], 'OK')
        self.assertEqual(observation['stages']['AX_PERSISTENCE']['status'],
                         'MATCH')
        self.assertEqual(observation['stages']['SCREENSHOT_PERSISTENCE']['status'],
                         'MATCH')
        self.assertEqual(run['captureCalls'], 1)
        self.assertEqual(result['captureCalls'], 1)
        self.assertIsNotNone(run['screenshotBytes'])
        self.assertIsNotNone(run['axText'])
        self.assertEqual(result['savedScreenshotBytes'], run['screenshotBytes'])
        self.assertEqual(result['savedAx'], run['axText'])
        self.assertEqual(len(run['emits']), 1)
        self.assertTrue(run['emits'][0]['isUint8Array'])
        self.assertEqual(run['emits'][0]['bytes'], run['screenshotBytes'])
        self.assertEqual(len(run['writes']), 2)
        self.assertEqual(json.loads(run['writes'][0]), observation)
        self.assertEqual(run['writes'][1], run['axText'])
        self.assertEqual(result['writes'], run['writes'])
        self.assertTrue(run['diagnostic']['ready_for_bind'])
        self.assertIn('initial-observation-sample.diagnostic.json',
                      run['fileNames'])
        screenshot_asset = observation['assets']['screenshot']
        ax_asset = observation['assets']['ax']
        self.assertEqual(screenshot_asset['bytes'], len(run['screenshotBytes']))
        self.assertEqual(
            screenshot_asset['sha256'],
            hashlib.sha256(bytes(run['screenshotBytes'])).hexdigest())
        self.assertEqual(
            ax_asset['sha256'],
            hashlib.sha256(run['axText'].encode('utf-8')).hexdigest())

    def test_initial_observation_blocked_paths_and_capture_never_emit(self):
        cases = (
            ('PRIVATE_PATHS:FAILED', self.CAPTURE_OK, False, 'PRIVATE_PATHS'),
            ('CAPTURE:FAILED', self.CAPTURE_THROW, True, 'CAPTURE'),
        )
        for blocker, capture_body, create_dir, stage in cases:
            with self.subTest(blocker=blocker):
                run = self.run_initial_observation(
                    capture_body=capture_body,
                    create_observation_dir=create_dir)
                self.assertNotEqual(run['returncode'], 0)
                self.assertIn('CUA_RAW_OBSERVATION_INCOMPLETE', run['stderr'])
                self.assertIn(blocker, run['stderr'])
                self.assertEqual(run['emits'], [])
                self.assertEqual(run['captureCalls'], 1)
                self.assertEqual(len(run['writes']), 1)
                observation = json.loads(run['writes'][0])
                self.assertFalse(observation['ready_for_bind'])
                self.assertIn(blocker, observation['blockers'])
                self.assertEqual(observation['stages'][stage]['status'], 'FAILED')
                if blocker == 'PRIVATE_PATHS:FAILED':
                    self.assertFalse(run['observationDirExists'])
                    self.assertEqual(
                        observation['stages']['PRIVATE_PATHS']['error']['code'],
                        'ENOENT')
                    self.assertIsNone(run['diagnostic'])
                else:
                    self.assertEqual(observation['stages']['AX']['status'],
                                     'NOT_AVAILABLE')
                    self.assertEqual(
                        observation['stages']['CAPTURE']['error'],
                        {'name': 'Error', 'code': 'ESYNTHETIC',
                         'message': 'synthetic initial capture throw'})

    def test_initial_observation_no_change_ax_persists_but_never_emits(self):
        no_change_state = ('There has been no change in the accessibility '
                           'tree for Window: "LINE".\n'
                           'The focused UI element is 39 文字')
        run = self.run_initial_observation(
            capture_body=r'''
        return {
          state: 'There has been no change in the accessibility tree for ' +
            'Window: "LINE".\nThe focused UI element is 39 文字',
          screenshot: new Uint8Array([
            0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
          ]),
        };
''')
        self.assertNotEqual(run['returncode'], 0)
        self.assertIn('CUA_RAW_OBSERVATION_INCOMPLETE', run['stderr'])
        self.assertIn('AX:DIFF_NO_CHANGE', run['stderr'])
        self.assertEqual(run['emits'], [])
        self.assertEqual(len(run['writes']), 1)
        observation = json.loads(run['writes'][0])
        self.assertFalse(observation['ready_for_bind'])
        self.assertIn('AX:DIFF_NO_CHANGE', observation['blockers'])
        self.assertEqual(observation['stages']['AX']['status'],
                         'DIFF_NO_CHANGE')
        self.assertEqual(observation['stages']['AX_PERSISTENCE']['status'],
                         'MATCH')
        self.assertEqual(run['axText'], no_change_state)
        self.assertIsNotNone(run['screenshotBytes'])
        self.assertIsNotNone(run['diagnostic'])
        self.assertFalse(run['diagnostic']['ready_for_bind'])
        self.assertEqual(run['diagnostic']['stages']['AX']['status'],
                         'DIFF_NO_CHANGE')
        self.assertIn('initial-observation-sample.diagnostic.json',
                      run['fileNames'])

    def test_initial_observation_missing_capture_boundary_fails_closed_without_emit(self):
        run = self.run_initial_observation(
            capture_body=self.CAPTURE_OK,
            tools_mode='stub-missing-boundary')
        self.assertNotEqual(run['returncode'], 0)
        self.assertIn('CUA_RAW_OBSERVATION_INCOMPLETE', run['stderr'])
        self.assertIn('CAPTURE_BOUNDARY:MISSING', run['stderr'])
        self.assertEqual(run['emits'], [])
        self.assertEqual(len(run['writes']), 1)
        observation = json.loads(run['writes'][0])
        self.assertTrue(observation['ready_for_bind'])
        self.assertEqual(
            observation['stages']['CAPTURE_BOUNDARY']['status'], 'MISSING')

    def test_initial_observation_readback_drift_never_emits(self):
        for tamper in ('SCREENSHOT_APPEND', 'AX_REWRITE_SAME_LENGTH'):
            with self.subTest(tamper=tamper):
                run = self.run_initial_observation(
                    capture_body=self.CAPTURE_OK, tamper=tamper,
                    epilogue=self.SUCCESS_EPILOGUE)
                self.assertNotEqual(run['returncode'], 0)
                self.assertIn('CUA_OBSERVATION_EMIT_READBACK_MISMATCH',
                              run['stderr'])
                self.assertNotIn('CUA_RAW_OBSERVATION_INCOMPLETE', run['stderr'])
                self.assertEqual(run['emits'], [])
                self.assertEqual(run['captureCalls'], 1)
                self.assertEqual(len(run['writes']), 1)
                observation = json.loads(run['writes'][0])
                self.assertTrue(observation['ready_for_bind'])
                self.assertEqual(observation['blockers'], [])
                if tamper == 'SCREENSHOT_APPEND':
                    asset = observation['assets']['screenshot']
                    self.assertEqual(len(run['screenshotBytes']),
                                     asset['bytes'] + 1)
                    self.assertNotEqual(
                        hashlib.sha256(bytes(run['screenshotBytes'])).hexdigest(),
                        asset['sha256'])
                else:
                    ax_bytes = run['axText'].encode('utf-8')
                    self.assertEqual(len(ax_bytes),
                                     observation['assets']['ax']['bytes'])
                    self.assertNotEqual(
                        hashlib.sha256(ax_bytes).hexdigest(),
                        observation['assets']['ax']['sha256'])


if __name__ == '__main__':
    unittest.main()
