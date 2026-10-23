// Supplemental fake-I/O regression checks for scripts/line_backup_cua_adapter.mjs (frozen revision
// sha256 bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2).
// Launched with tests/test_cua_adapter.mjs via `node --test`; imports no fs/child_process/network
// modules, touches no real app, bridge, UI, or state, and writes nothing at runtime.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {runInNewContext} from 'node:vm';
import {createHostedSession, normalizeScreenshotBytes}
  from '../../../../../../scripts/line_backup_cua_adapter.mjs';

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const flipHex = hex => `${hex[0] === '0' ? '1' : '0'}${hex.slice(1)}`;
const ISO_UTC = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;
const SESSION_ID = 'capture-regression';

function makeHarness(options = {}) {
  const calls = [];
  const counters = {capture: 0, retain: 0, classify: 0, bridge: 0, click: 0};
  let now = options.startAt ?? 0;
  const sourceBytes = options.screenshot ?? new Uint8Array([10, 20, 30, 40]);
  const app = {
    async getAXStateAndScreenshot() {
      counters.capture += 1;
      calls.push('capture');
      if (options.captureAdvanceMs) now += options.captureAdvanceMs;
      return {state: options.state === undefined ? 'fixture AX state' : options.state, screenshot: sourceBytes};
    },
    async getAXState() {calls.push('getAXState'); return 'fixture AX state';},
    async click(point) {counters.click += 1; calls.push(['click', point]);},
    async pressKey(key) {calls.push(['key', key]);},
    async setValue(index, value) {calls.push(['setValue', index, value]);},
    async scroll(target, direction, distance) {calls.push(['scroll', target, direction, distance]);}
  };
  const retain = async value => {
    counters.retain += 1;
    calls.push('retain');
    if (options.retainAdvanceMs) now += options.retainAdvanceMs;
    if (options.retainError) throw options.retainError;
    if (typeof options.retain === 'function') return options.retain(value);
    const ax = Buffer.from(value.ax);
    return {path: `harness-development/frame-${value.frameId.slice(0, 12)}.json`,
      bytes: value.screenshot.byteLength, sha256: value.frameId,
      ax: {path: `harness-development/ax-${value.frameId.slice(0, 12)}.txt`, bytes: ax.byteLength, sha256: sha256(ax)}};
  };
  const classify = async value => {
    counters.classify += 1;
    calls.push('classify');
    if (options.classifyAdvanceMs) now += options.classifyAdvanceMs;
    if (typeof options.classify === 'function') return options.classify(value);
    return {frame_id: value.frameId, session_id: value.sessionId, surface: 'ALBUM_DETAIL'};
  };
  const bridge = async (operation, payload) => {
    counters.bridge += 1;
    calls.push(['bridge', operation]);
    if (typeof options.bridge === 'function') return options.bridge(operation, payload);
    if (operation === 'gui_reserve') {
      return {reservation: {id: `res-${operation}`, kind: payload.data.kind, count: payload.data.count}};
    }
    if (operation === 'gui_consume') return {reservation: {id: payload.data.reservation_id, state: 'CONSUMED'}};
    return {};
  };
  const session = createHostedSession({app, bridge, retain, classify, sessionId: SESSION_ID, clock: () => now,
    wait: async ms => {calls.push(['timer', ms]); now += ms;}});
  return {session, calls, counters, advance: ms => {now += ms;}, clockNow: () => now, sourceBytes};
}

test('normalizeScreenshotBytes rejects invalid byte sources and accepts exactly 16 MiB', () => {
  const invalid = [null, undefined, {}, 'bytes', [1, 2, 3], new DataView(new ArrayBuffer(8)),
    new Uint16Array([1, 2]), new Float64Array([1]), new Uint8Array(0),
    {buffer: new ArrayBuffer(8), byteOffset: 0, byteLength: 4}, new Uint8Array(16 * 1024 * 1024 + 1)];
  for (const value of invalid) {
    assert.throws(() => normalizeScreenshotBytes(value), /CAPTURE_BYTES_INVALID/);
  }
  const exact = normalizeScreenshotBytes(new Uint8Array(16 * 1024 * 1024));
  assert.ok(exact instanceof Uint8Array);
  assert.equal(exact.byteLength, 16 * 1024 * 1024);
  assert.equal(exact.buffer.byteLength, 16 * 1024 * 1024);
  assert.equal(exact[0], 0);
});

test('normalizeScreenshotBytes copies Buffer subarrays, whole Buffers, and cross-realm views independently', () => {
  const raw = Buffer.from([9, 4, 5, 6, 8]);
  const view = raw.subarray(1, 4);
  assert.equal(view.byteOffset, raw.byteOffset + 1);
  const copy = normalizeScreenshotBytes(view);
  assert.equal(copy.byteLength, 3);
  assert.deepEqual([...copy], [4, 5, 6]);
  assert.notEqual(copy.buffer, view.buffer);
  assert.notEqual(copy.buffer, raw.buffer);
  copy[0] = 99;
  assert.equal(raw[1], 4);
  const whole = normalizeScreenshotBytes(raw);
  assert.equal(whole.byteLength, raw.byteLength);
  assert.deepEqual([...whole], [9, 4, 5, 6, 8]);
  assert.notEqual(whole.buffer, raw.buffer);
  assert.equal(whole.buffer.byteLength, raw.byteLength);
  const foreign = runInNewContext('new Uint8Array([9, 1, 2, 3, 8]).subarray(1, 4)');
  assert.equal(foreign instanceof Uint8Array, false);
  assert.equal(ArrayBuffer.isView(foreign), true);
  const foreignCopy = normalizeScreenshotBytes(foreign);
  assert.deepEqual([...foreignCopy], [1, 2, 3]);
  assert.notEqual(foreignCopy.buffer, foreign.buffer);
  foreignCopy[0] = 77;
  assert.equal(foreign[0], 1);
});

test('capture records the request interval, hashes the copied bytes, and returns the classifier result', async () => {
  const raw = new Uint8Array([7, 1, 2, 3]);
  let classifyArgs = null, classifyResult = null;
  const harness = makeHarness({screenshot: raw, captureAdvanceMs: 250, classify: value => {
    classifyArgs = value;
    classifyResult = {frame_id: value.frameId, session_id: value.sessionId, surface: 'ALBUM_DETAIL'};
    return classifyResult;
  }});
  const observation = await harness.session.observe();
  assert.equal(observation, classifyResult);
  assert.deepEqual([...classifyArgs.capture.screenshot], [7, 1, 2, 3]);
  assert.notEqual(classifyArgs.capture.screenshot.buffer, raw.buffer);
  assert.equal(observation.frame_id, sha256(classifyArgs.capture.screenshot));
  assert.match(observation.frame_id, /^[0-9a-f]{64}$/);
  assert.equal(classifyArgs.sessionId, SESSION_ID);
  assert.match(classifyArgs.requestStartedAtUtc, ISO_UTC);
  assert.match(classifyArgs.requestEndedAtUtc, ISO_UTC);
  assert.equal(classifyArgs.capturedAt, classifyArgs.requestStartedAtUtc);
  assert.ok(Number.isFinite(Date.parse(classifyArgs.requestStartedAtUtc)));
  assert.ok(Date.parse(classifyArgs.requestEndedAtUtc) >= Date.parse(classifyArgs.requestStartedAtUtc));
  const interval = classifyArgs.monotonicInterval;
  assert.equal(interval.start_ms, 0);
  assert.equal(interval.end_ms, 250);
  assert.equal(interval.duration_ms, interval.end_ms - interval.start_ms);
  assert.equal(harness.clockNow(), 250);
});

test('retain or classify time passing never refreshes the capture freshness window', async () => {
  for (const mode of ['retain', 'classify']) {
    const harness = makeHarness(mode === 'retain' ? {retainAdvanceMs: 6000} : {classifyAdvanceMs: 6000});
    const observation = await harness.session.observe();
    assert.equal(harness.counters.retain, 1);
    assert.equal(harness.counters.classify, 1);
    assert.equal(harness.clockNow(), 6000);
    const bridgeBefore = harness.counters.bridge;
    await assert.rejects(harness.session.openAlbum({frame_id: observation.frame_id, click: [1, 2], run_id: 'r'}),
      /FRESH_CAPTURE_REQUIRED/);
    assert.equal(harness.counters.bridge, bridgeBefore);
    assert.equal(harness.counters.bridge, 0);
    assert.equal(harness.counters.click, 0);
  }
});

test('a capture aged exactly 5000 ms still passes freshness to the bridge', async () => {
  const sentinel = new Error('SENTINEL_BRIDGE_REACHED');
  const harness = makeHarness({bridge: operation => {
    if (operation === 'gui_reserve') throw sentinel;
    return {};
  }});
  const observation = await harness.session.observe();
  harness.advance(5000);
  let caught = null;
  try {
    await harness.session.openAlbum({frame_id: observation.frame_id, click: [1, 2], run_id: 'r'});
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, sentinel);
  assert.match(caught.message, /SENTINEL_BRIDGE_REACHED/);
  assert.equal(harness.counters.bridge, 1);
  assert.deepEqual(harness.calls[harness.calls.length - 1], ['bridge', 'gui_reserve']);
  assert.equal(harness.counters.click, 0);
});

test('an invalid retained frame reference is refused before classify', async () => {
  for (const mode of ['sha256', 'bytes']) {
    const harness = makeHarness({retain: value => {
      const reference = {path: `harness-development/frame-${value.frameId.slice(0, 12)}.json`,
        bytes: value.screenshot.byteLength, sha256: value.frameId,
        ax: {path: 'harness-development/ax.txt', bytes: 4, sha256: 'a'.repeat(64)}};
      if (mode === 'sha256') reference.sha256 = flipHex(value.frameId);
      if (mode === 'bytes') reference.bytes += 1;
      return reference;
    }});
    await assert.rejects(harness.session.observe(), /CUA_FRAME_REFERENCE_REQUIRED/);
    assert.equal(harness.counters.retain, 1);
    assert.equal(harness.counters.classify, 0);
  }
});

test('a classifier frame or session mismatch rejects the observation', async () => {
  const frameMismatch = makeHarness({classify: value => ({frame_id: flipHex(value.frameId), session_id: value.sessionId})});
  await assert.rejects(frameMismatch.session.observe(), /CLASSIFIER_FRAME_MISMATCH/);
  assert.equal(frameMismatch.counters.classify, 1);
  const sessionMismatch = makeHarness({classify: value => ({frame_id: value.frameId, session_id: `${value.sessionId}-other`})});
  await assert.rejects(sessionMismatch.session.observe(), /CLASSIFIER_FRAME_MISMATCH/);
  assert.equal(sessionMismatch.counters.classify, 1);
});

test('a non-string AX state is rejected before retain and classify', async () => {
  for (const state of [null, 42]) {
    const harness = makeHarness({state});
    await assert.rejects(harness.session.observe(), /CAPTURE_INCOMPLETE/);
    assert.equal(harness.counters.capture, 1);
    assert.equal(harness.counters.retain, 0);
    assert.equal(harness.counters.classify, 0);
    assert.equal(harness.counters.bridge, 0);
  }
});

test('a retain failure propagates and classify is never called', async () => {
  const failure = new Error('RETAIN_SENTINEL_FAILURE');
  const harness = makeHarness({retainError: failure});
  let caught = null;
  try {
    await harness.session.observe();
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, failure);
  assert.equal(harness.counters.retain, 1);
  assert.equal(harness.counters.classify, 0);
});
