"""Execute the single-input helper documented in the Notes evidence template."""
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
async function dispatchObservation(observationId) {
  return evidenceTools.persistObservation({
    taskDir: process.env.INPUT_TEST_ROOT,
    observationDir: process.env.INPUT_TEST_DIR,
    observationId,
    capture: dispatchCapture(),
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
'''


class NotesInputHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools_source = documented_tools_source()
        cls.reveal_source = documented_reveal_source()
        cls.dispatch_source = documented_dispatch_source()
        TASKS.mkdir(parents=True, exist_ok=True)

    def run_helper(self, body, extra_source=''):
        with tempfile.TemporaryDirectory(prefix='.notes-input-helper-', dir=TASKS) as temp:
            root = Path(temp).resolve()
            output_dir = root / 'observations'
            output_dir.mkdir()
            script = self.tools_source + '\n' + r'''
const fsTest = await import('node:fs/promises');
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

    def test_dispatch_reveal_same_after_feeds_one_download_and_fixed_slot(self):
        result, _ = self.run_dispatch(DISPATCH_SETUP + r'''
let revealClicks = 0, revealCaptures = 0, downloadClicks = 0;
const app = {
  async click(target) {
    if (target[0] === 50 && target[1] === 60) revealClicks += 1;
    else downloadClicks += 1;
    return {target};
  },
  async getAXStateAndScreenshot() {
    revealCaptures += 1;
    return dispatchCapture();
  },
};
const revealRun = await notesIntentDispatch.persistReveal(
  dispatchRevealOptions('attempt-reveal',
    dispatchNavigationRequest('attempt-reveal', 1), app));
const after = revealRun.afterObservation;
const afterShot = dispatchRef(after.assets.screenshot);
const afterBytes = new Uint8Array(await fsTest.readFile(afterShot.path));
const request = {
  ...dispatchDownloadRequest('attempt-reveal', after),
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
const sameAfter = await download({reveal: revealRun});
const replay = await download({
  reveal: revealRun,
  request: {...request, candidate_point: [61, 71], prepared_target: [61, 71]},
});
return {revealClicks, revealCaptures, downloadClicks, revealRun,
        stale, sameAfter, replay};
''')
        self.assertEqual(result['revealClicks'], 1)
        self.assertEqual(result['revealCaptures'], 1)
        self.assertEqual(result['revealRun']['status'], 'INVOKED')
        self.assertEqual(result['revealRun']['operation_id'],
                         'notes-reveal-c2-attempt-reveal')
        self.assertEqual(result['stale']['reason'],
                         'DOWNLOAD_SOURCE_OBSERVATION_MISMATCH')
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
const ordinalTwo = await reveal('attempt-two',
  dispatchNavigationRequest('attempt-two', 2));
const raceRequest = dispatchNavigationRequest('attempt-race', 1);
const [raceFirst, raceSecond] = await Promise.all([
  reveal('attempt-race', raceRequest),
  reveal('attempt-race', raceRequest),
]);
const ordinalSwitch = await reveal('attempt-race',
  dispatchNavigationRequest('attempt-race', 2));
const failedReveal = await notesIntentDispatch.persistReveal(
  dispatchRevealOptions('attempt-capture-error',
    dispatchNavigationRequest('attempt-capture-error', 1), {
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
        self.assertEqual(len(result['stopped']), 30)
        for name, item in result['stopped'].items():
            self.assertEqual(item['status'], 'STOP', name)
            self.assertIn(item['expected'], item['blockers'], name)
        self.assertEqual(result['counters'].get('clicks', 0), 0)
        self.assertEqual(result['counters'].get('captures', 0), 0)


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


class NotesGroundedDownloadHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools_source = documented_tools_source()
        TASKS.mkdir(parents=True, exist_ok=True)

    def run_helper(self, body):
        with tempfile.TemporaryDirectory(prefix='.notes-input-helper-', dir=TASKS) as temp:
            root = Path(temp).resolve()
            output_dir = root / 'observations'
            output_dir.mkdir()
            script = self.tools_source + '\n' + r'''
const fsTest = await import('node:fs/promises');
const result = await (async () => {
''' + body + r'''
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


if __name__ == '__main__':
    unittest.main()
