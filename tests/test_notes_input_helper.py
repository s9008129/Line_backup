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


def documented_tools_source():
    text = TEMPLATE.read_text(encoding='utf-8')
    start = text.index(START) + len(START)
    code_start = text.index('```js', start) + len('```js')
    code_end = text.index('```', code_start)
    return text[code_start:code_end]


class NotesInputHelperTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
