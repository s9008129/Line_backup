// live_runner.mjs -- TASK-20261010-line-v3-live-e2e live bridge (task package; NOT product code).
//
// Load ONLY inside the documented cua_repl kernel with a genuine App object. No GUI is
// synthesized here; every click/key/scroll is performed by scripts/line_backup_cua_adapter.mjs
// after the implementer has announced the exact action and the user has handed over the LINE
// foreground for THIS run.
//
// Frozen pieces wired here:
//   scripts/line_backup_cua_adapter.mjs          createHostedSession / createAlbumSupportCallbacks
//   line_backup_batch.cli                        inspect/begin/admit/prepare/calibrate/intent/
//                                                dispatch/finalize/stop/finish/release/gui_reserve/gui_consume
//   rev28ctl album-support[-guard]               read-only SCK menu support producer / guard
//
// STATUS (2026-10-10, implement-02): two reviewed live components are NOT available with the
// frozen toolchain. They fail closed here instead of being improvised; both need a new reviewed
// plan and an explicit user decision (see E2E測試報告.md, decisions D1/D2):
//   D1 classify(): a grounded LINE AX -> 17-key observation-frame classifier. No real
//      implementation exists (tests use fakes). -> LIVE_CLASSIFIER_NOT_GROUNDED
//   D2 frameSupport(): a SCREEN_CAPTURE_KIT sidecar producer for NON-menu frames. rev28ctl
//      album-support is structurally menu-only: it requires menu-bounds ∩ addressable-bounds
//      >= 16x16 and exactly one OCR row "儲存全部" (main.swift:752-806, OcrEngine.swift:536-556),
//      while observations.frame() requires a live sidecar for EVERY frame (observations.py:69,143;
//      executable proof: evidence/live-branch-proof.stdout) -> LIVE_FRAME_SUPPORT_UNAVAILABLE
//
// Runtime preconditions to verify at live preflight (do NOT assume):
//   * the kernel can run child processes; this module never imports node:child_process itself,
//     the caller injects runProcess built from whatever the kernel documents
//   * cua.getApp('jp.naver.line.mac') exposes the six documented App methods (adaptApp checks)
//   * the LINE foreground handoff is FRESH for this run (old handoffs are not evidence)
//
// Hard integration facts encoded below:
//   * bridge('intent'|'dispatch') must wrap the flat CLI stdout as {new_intent, receipt_token,
//     result:<flat stdout>} -- the adapter reads committed.result.* and recorded.result.status.
//   * save_all_point must stay JSON-integer identical through calibrate -> intent -> guard argv
//     (Python compares json_bytes(guard.actionPoint) == json_bytes(intent.calibration.save_all_point)).
//   * popup.png is re-read under a 16 MiB authority cap (project_binding.py:122); the guard hook
//     pre-checks it BEFORE the Save All click, never after.
//   * `owner` MUST equal the execution grant's owner (store.py:341 require(owner==grant['owner']))
//     and `authorization` MUST be that same grant file; both grants live in TASK.*. Call
//     preflightLive() once before the first LINE capture to fail fast with a readable code.

import {createHash} from 'node:crypto';

const REL = 'harness-development/line-v3-live-e2e-20261010';
export const TASK = {
  rel: REL,
  grant1: REL + '/live-grant-1.json',
  grant2: REL + '/live-grant-2.json',
  binary: REL + '/swift-build-26.5/debug/rev28ctl',
  decoder: REL + '/bin/image_decode',
  decoderSha256: '1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf',
  bundleId: 'jp.naver.line.mac',
  authorityReadCap: 16 * 1024 * 1024,
};

const HEX64 = /^[0-9a-f]{64}$/;
const encoder = new TextEncoder();
export const sha256Hex = bytes => createHash('sha256').update(bytes).digest('hex');
export function fail(code, message = code) {
  const error = new Error(message);
  error.code = code;
  throw error;
}
const requireFact = (ok, code) => { if (!ok) fail(code); };
const isInt = v => Number.isInteger(v);

let counter = 0;
const nonce = label => `${label}-${Date.now().toString(36)}-${(++counter).toString(36)}`;

// ---------------------------------------------------------------- preflight

export async function preflightLive({io, repoRoot, authorization, owner}) {
  requireFact(typeof authorization === 'string' && authorization.startsWith('harness-development/'), 'GRANT_PATH_UNSAFE');
  requireFact(typeof owner === 'string' && owner, 'GRANT_OWNER_REQUIRED');
  const raw = await io.readFile(`${repoRoot}/${authorization}`);
  let grant;
  try { grant = JSON.parse(new TextDecoder().decode(raw)); } catch { fail('GRANT_UNPARSEABLE'); }
  requireFact(grant && grant.grant_version === 'line-batch-execution-grant-1' && grant.fixture === false, 'GRANT_SHAPE');
  requireFact(grant.project_root === repoRoot, 'GRANT_PROJECT_MISMATCH');
  requireFact(grant.owner === owner, 'GRANT_OWNER_MISMATCH');
  requireFact(grant.contract_sha256 === '6505ad3817a899c223d42a8e814ec81cbb0f3317bb206d73a4a503671726d419', 'GRANT_CONTRACT_DRIFT');
  requireFact(grant.native_binary_sha256 === TASK.decoderSha256, 'GRANT_NATIVE_BINARY_DRIFT');
  const needed = ['begin', 'admit', 'prepare', 'calibrate', 'intent', 'dispatch', 'finalize', 'finish', 'release', 'gui_reserve', 'gui_consume'];
  requireFact(needed.every(op => grant.operations.includes(op)), 'GRANT_OPERATIONS_INCOMPLETE');
  return Object.freeze({grant, limits: Object.freeze({
    albumQuota: grant.album_quota, lifecycleAlbumLimit: grant.lifecycle_album_limit,
    saveAllDispatchLimit: grant.save_all_dispatch_limit, chooserConfirmationLimit: grant.chooser_confirmation_limit,
    reversibleGuiInvocationLimit: grant.reversible_gui_invocation_limit})});
}

const rectText = value => {
  requireFact(Array.isArray(value) && value.length === 4 && value.every(Number.isFinite), 'INVALID_RECT');
  return value.join(',');
};
const intPointText = value => {
  requireFact(Array.isArray(value) && value.length === 2 && value.every(isInt), 'SAVE_ALL_POINT_MUST_STAY_INTEGER');
  return `${value[0]},${value[1]}`;
};

// ---------------------------------------------------------------- CLI bridge

export function createCli({io, runProcess, repoRoot, pythonBin, baseEnv = {}, authorization = null}) {
  const state = {lastToken: null};

  async function cli(operation, {authorization: callAuthorization = authorization, payload = null} = {}) {
    const argv = [pythonBin, '-B', '-m', 'line_backup_batch.cli', operation, '--project-root', repoRoot];
    if (callAuthorization !== null) argv.push('--authorization', callAuthorization);
    if (payload !== null) {
      const inputRel = `${REL}/inputs/${nonce(operation)}.json`;
      await io.mkdirp(`${repoRoot}/${REL}/inputs`);
      await io.writeFile(`${repoRoot}/${inputRel}`, encoder.encode(JSON.stringify(payload)));
      argv.push('--input', inputRel);
    }
    const result = await runProcess(argv, {cwd: repoRoot, env: {...baseEnv, PYTHONPATH: 'src', PYTHONDONTWRITEBYTECODE: '1'}});
    if (result.status !== 0) {
      let code = result.status === 4 ? 'CLI_REFUSED' : 'CLI_PROCESS_FAILURE';
      let message = String(result.stderr || '').trim();
      try { const parsed = JSON.parse(result.stderr); code = parsed.code || code; message = parsed.message || message; } catch {}
      fail(code, `${operation}: ${message}`);
    }
    let parsed;
    try { parsed = JSON.parse(result.stdout); } catch { fail('CLI_STDOUT_UNPARSEABLE', operation); }
    if (typeof parsed.receipt_token === 'string') state.lastToken = parsed.receipt_token;
    return parsed;
  }

  // Adapter-facing bridge. gui_* pass through; intent/dispatch are wrapped for the adapter.
  async function bridge(operation, {expected_token: expectedToken = null, data = {}} = {}) {
    if (operation === 'gui_reserve' || operation === 'gui_consume') {
      // store.reserve_gui/consume_gui re-authorize against the live grant (store.py:345,368);
      // they use the immutable grant, not the receipt-token CAS chain.
      requireFact(typeof authorization === 'string', 'GUI_LEDGER_AUTHORIZATION_REQUIRED');
      const payload = expectedToken === null ? {data} : {expected_token: expectedToken, data};
      return cli(operation, {authorization, payload});
    }
    if (operation === 'intent') {
      const parsed = await cli('intent', {payload: {expected_token: expectedToken, data}});
      // store._update returns {receipt, result, lock_identity, new_intent}; the CLI pops `receipt`
      // to receipt_token, so the operation payload is always nested under `result`.
      requireFact(parsed.new_intent === true && parsed.result && typeof parsed.result.status === 'string', 'INTENT_SHAPE');
      return {new_intent: parsed.new_intent, receipt_token: parsed.receipt_token, result: parsed.result};
    }
    if (operation === 'dispatch') {
      const parsed = await cli('dispatch', {payload: {expected_token: expectedToken, data}});
      requireFact(parsed.result && typeof parsed.result.status === 'string', 'DISPATCH_SHAPE');
      return {receipt_token: parsed.receipt_token, result: parsed.result};
    }
    fail('BRIDGE_OPERATION_UNKNOWN', operation);
  }

  // Callable facade: runLifecycle calls cli(...) and reads cli.state.lastToken, while the
  // hosted session needs cli.bridge. Expose one object that is both.
  return Object.assign(cli, {bridge, state});
}

// ---------------------------------------------------------------- retain

export function createRetain({io, repoRoot}) {
  return async function retain(payload) {
    if (payload.receipt !== undefined) {
      requireFact(payload.kind === 'cua-dispatch-receipt-1' && HEX64.test(payload.frameId), 'RETAIN_RECEIPT_SHAPE');
      const raw = encoder.encode(JSON.stringify(payload.receipt, null, 2) + '\n');
      const path = `${REL}/evidence/live-receipts/${payload.frameId.slice(0, 16)}-${nonce('receipt')}.json`;
      await io.mkdirp(`${repoRoot}/${REL}/evidence/live-receipts`);
      await io.writeFile(`${repoRoot}/${path}`, raw);
      return {path, bytes: raw.byteLength, sha256: sha256Hex(raw)};
    }
    requireFact(payload.screenshot instanceof Uint8Array && typeof payload.ax === 'string', 'RETAIN_FRAME_SHAPE');
    requireFact(HEX64.test(payload.frameId) && sha256Hex(payload.screenshot) === payload.frameId, 'RETAIN_FRAME_IDENTITY');
    requireFact(payload.screenshot.byteLength <= TASK.authorityReadCap, 'FRAME_BYTES_OVER_AUTHORITY_CAP');
    const path = `${REL}/evidence/live-frames/${payload.frameId}.png`;
    const axPath = `${REL}/evidence/live-frames/${payload.frameId}.ax.txt`;
    await io.mkdirp(`${repoRoot}/${REL}/evidence/live-frames`);
    await io.writeFile(`${repoRoot}/${path}`, payload.screenshot);
    await io.writeFile(`${repoRoot}/${axPath}`, encoder.encode(payload.ax));
    return {path, bytes: payload.screenshot.byteLength, sha256: payload.frameId};
  };
}

// ------------------------------------------------- SCK menu producer hook

export function createProducerHook({io, runProcess, repoRoot, binary = TASK.binary, geometryProvider}) {
  const geometryBySupport = new Map();

  async function runProducer(argv, code) {
    const result = await runProcess([binary, ...argv], {cwd: repoRoot, env: {}});
    if (result.status !== 0) fail(code, String(result.stderr || '').trim() || `exit ${result.status}`);
    try { return JSON.parse(result.stdout); } catch { fail('PRODUCER_RECEIPT_UNPARSEABLE'); }
  }

  // The adapter calls invokeProducer({mode:'capture', action, pairFrameId, sessionId, requestedAt,
  // cuaFrame, cuaCapturedAt}) and supplies NO geometry; geometryProvider must return the live
  // window/menu grounding: {pid, windowId, displayId, layoutKey, cuaBounds, menuBounds,
  // addressableBounds, uncertaintyPx} for the exact frame the menu was opened on.
  async function captureMenuSupport({action, pairFrameId, sessionId, requestedAt, cuaFrame, cuaCapturedAt}) {
    requireFact(typeof geometryProvider === 'function', 'LIVE_GEOMETRY_PROVIDER_REQUIRED');
    const geometry = await geometryProvider({action, pairFrameId, sessionId, requestedAt, cuaFrame, cuaCapturedAt});
    requireFact(geometry && isInt(geometry.pid) && isInt(geometry.windowId) && isInt(geometry.displayId)
      && typeof geometry.layoutKey === 'string' && Number.isFinite(geometry.uncertaintyPx) && geometry.uncertaintyPx >= 2,
      'LIVE_FRAME_GEOMETRY_REQUIRED');
    requireFact(cuaFrame && HEX64.test(cuaFrame.sha256) && cuaFrame.sha256 === pairFrameId
      && typeof cuaFrame.path === 'string' && cuaFrame.path.startsWith('harness-development/'), 'CUA_FRAME_REFERENCE_REQUIRED');
    requireFact(typeof cuaCapturedAt === 'string' && cuaCapturedAt.includes('.'), 'CUA_CAPTURED_AT_FRACTIONAL_REQUIRED');
    const output = `${REL}/evidence/live-support/${pairFrameId.slice(0, 16)}-${nonce('support')}`;
    await io.mkdirp(`${repoRoot}/${output}`);
    const receipt = await runProducer(['album-support',
      '--project-root', repoRoot, '--output', output, '--bundle-id', TASK.bundleId,
      '--pid', String(geometry.pid), '--window-id', String(geometry.windowId), '--display-id', String(geometry.displayId),
      '--session-id', sessionId, '--layout-key', geometry.layoutKey,
      '--pair-frame', cuaFrame.path, '--pair-frame-id', cuaFrame.sha256, '--cua-captured-at', cuaCapturedAt,
      '--cua-bounds', rectText(geometry.cuaBounds), '--menu-bounds', rectText(geometry.menuBounds),
      '--addressable-bounds', rectText(geometry.addressableBounds),
      '--save-all-point', intPointText(action.save_all), '--uncertainty-px', String(geometry.uncertaintyPx),
    ], 'PRODUCER_CAPTURE_REFUSED');
    requireFact(receipt.provider === 'SCREEN_CAPTURE_KIT' && receipt.pairFrameId === pairFrameId
      && HEX64.test(receipt.popupFrameId) && receipt.popupFrameId !== pairFrameId && receipt.sessionId === sessionId
      && receipt.reference && typeof receipt.reference.path === 'string' && receipt.reference.path.startsWith('harness-development/')
      && isInt(receipt.reference.bytes) && HEX64.test(receipt.reference.sha256), 'PRODUCER_CAPTURE_RECEIPT_SHAPE');
    geometryBySupport.set(receipt.reference.sha256, {...geometry, saveAllPoint: [...action.save_all],
      popupFrameId: receipt.popupFrameId, uncertaintyPx: receipt.uncertaintyPx});
    return receipt;
  }

  // Adapter contract (line_backup_cua_adapter.mjs:30-31): invokeProducer({mode:'guard',
  // support:<reference>, pairFrameId, popupFrameId, saveAllPoint, uncertaintyPx, sessionId});
  // `support` is the retained sidecar reference, not the full capture receipt.
  async function guardMenu({support, pairFrameId, popupFrameId, saveAllPoint, uncertaintyPx, sessionId}) {
    requireFact(support && typeof support.path === 'string' && support.path.startsWith('harness-development/')
      && HEX64.test(support.sha256), 'SCK_SUPPORT_REFERENCE_REQUIRED');
    const geometry = geometryBySupport.get(support.sha256);
    requireFact(geometry, 'PRODUCER_GEOMETRY_UNKNOWN');
    requireFact(popupFrameId === geometry.popupFrameId && uncertaintyPx === geometry.uncertaintyPx
      && intPointText(saveAllPoint) === intPointText(geometry.saveAllPoint), 'SCK_SUPPORT_BINDING');
    const guard = await runProducer(['album-support-guard',
      '--project-root', repoRoot, '--support', support.path, '--support-sha256', support.sha256,
      '--pair-frame-id', pairFrameId, '--session-id', sessionId,
      '--pid', String(geometry.pid), '--window-id', String(geometry.windowId), '--layout-key', geometry.layoutKey,
      '--save-all-point', intPointText(saveAllPoint), '--uncertainty-px', String(geometry.uncertaintyPx),
    ], 'PRODUCER_GUARD_REFUSED');
    requireFact(guard.verdict === 'PASS' && guard.provider === 'SCREEN_CAPTURE_KIT'
      && guard.pairFrameId === pairFrameId && guard.popupFrameId === popupFrameId
      && guard.supportSha256 === support.sha256
      && Array.isArray(guard.actionPoint) && guard.actionPoint.length === 2
      && guard.actionPoint[0] === geometry.saveAllPoint[0] && guard.actionPoint[1] === geometry.saveAllPoint[1],
      'SCK_MENU_GUARD_REFUSED');
    await precheckPopup(support);
    return guard;
  }

  // The popup is re-read under a strict 16 MiB authority cap AFTER Save All (service.py:256-261).
  // Fail closed HERE, before the Save All click can happen, whenever the retained bytes could
  // not be re-read later.
  async function precheckPopup(reference) {
    const supportBytes = await io.readFile(`${repoRoot}/${reference.path}`);
    requireFact(sha256Hex(supportBytes) === reference.sha256, 'SUPPORT_BYTES_DRIFT');
    let sidecar;
    try { sidecar = JSON.parse(new TextDecoder().decode(supportBytes)); } catch { fail('SUPPORT_SIDECAR_UNPARSEABLE'); }
    requireFact(sidecar && sidecar.sck_frame && typeof sidecar.sck_frame.path === 'string', 'SUPPORT_SIDECAR_SHAPE');
    const stat = await io.stat(`${repoRoot}/${sidecar.sck_frame.path}`);
    requireFact(isInt(stat.size) && stat.size === sidecar.sck_frame.bytes, 'POPUP_BYTES_DRIFT');
    requireFact(stat.size <= TASK.authorityReadCap, 'LIVE_POPUP_OVER_AUTHORITY_CAP');
    const popupBytes = await io.readFile(`${repoRoot}/${sidecar.sck_frame.path}`);
    requireFact(sha256Hex(popupBytes) === sidecar.sck_frame.sha256, 'POPUP_BYTES_DRIFT');
  }

  // createAlbumSupportCallbacks({invokeProducer}) routes BOTH capture and guard calls through
  // one function, distinguished by request.mode (adapter lines 16 and 30).
  async function invokeProducer(request) {
    requireFact(request && typeof request.mode === 'string', 'PRODUCER_MODE_REQUIRED');
    if (request.mode === 'guard') return guardMenu(request);
    if (request.mode === 'capture') return captureMenuSupport(request);
    fail('PRODUCER_MODE_UNKNOWN', request.mode);
  }

  return {captureMenuSupport, guardMenu, invokeProducer, precheckPopup};
}

// ------------------------------------------- blocked components (D1/D2)

export function createClassifier() {
  return async function classify() {
    fail('LIVE_CLASSIFIER_NOT_GROUNDED',
      'no grounded LINE AX -> 17-key observation classifier exists; decision D1 required (see live_runner.mjs header)');
  };
}

export function createFrameSupport() {
  return async function frameSupport() {
    fail('LIVE_FRAME_SUPPORT_UNAVAILABLE',
      'rev28ctl album-support is menu-only; non-menu frames have no SCREEN_CAPTURE_KIT sidecar producer; decision D2 required');
  };
}

// ---------------------------------------------------------------- App adapter

const APP_METHODS = ['getAXStateAndScreenshot', 'getAXState', 'click', 'pressKey', 'setValue', 'scroll'];
export function adaptApp(app) {
  requireFact(app && APP_METHODS.every(name => typeof app[name] === 'function'), 'DOCUMENTED_APP_REQUIRED');
  const call = (name, ...args) => app[name](...args);
  return Object.freeze({
    getAXStateAndScreenshot: async options => {
      const capture = await call('getAXStateAndScreenshot', options);
      requireFact(capture && typeof capture.state === 'string', 'CAPTURE_STATE_MISSING');
      let screenshot = capture.screenshot;
      if (typeof screenshot === 'string') screenshot = Uint8Array.from(Buffer.from(screenshot, 'base64'));
      requireFact(screenshot instanceof Uint8Array && screenshot.byteLength > 0, 'CAPTURE_SCREENSHOT_MISSING');
      return {state: capture.state, screenshot};
    },
    getAXState: options => call('getAXState', options),
    click: point => call('click', point),
    pressKey: key => call('pressKey', key),
    setValue: (index, value) => call('setValue', index, value),
    scroll: (target, direction, distance) => call('scroll', target, direction, distance),
  });
}

// ------------------------------------------------------------- orchestration

// live must provide (all currently blocked by D1/D2; injected so the driver is testable):
//   repoRoot                          -> absolute prefix for the frozen native decoder path
//   producer: {captureMenuSupport, guardMenu}
//                                    -> createAlbumSupportCallbacks(...) (REQUIRED; destructured in buildLiveRunner)
//   producerGeometry(args)            -> {pid,windowId,displayId,layoutKey,cuaBounds,menuBounds,
//                                         addressableBounds,uncertaintyPx} for the menu producer
//   locators: {locatePathField, validatePath, validateLeaf, locateConfirm}
//                                    -> exactChooser groundings for the real folder chooser
//   captureCatalog({afterFirstAlbum}) -> {records:[17-key frames in scroll order]}
//   prepareCandidates(records)        -> [17-key frame containing each successive eligible card]
//   calibrateMenu(detail, prepared)   -> {detail, calibration, menu, closure} (menu opened+closed)
//   captureFresh(detail)              -> 17-key ALBUM_DETAIL frame for intent
//   finalRecords()                    -> fresh catalog records for finish
export async function runLifecycle({cli, session, owner, authorization, limit = 1, live, log = () => {}}) {
  const trace = [];
  const step = async (name, fn) => {
    log(name);
    const value = await fn();
    trace.push({name, at: Date.now()});
    return value;
  };
  const token = () => {
    requireFact(typeof cli.state.lastToken === 'string', 'RECEIPT_TOKEN_UNAVAILABLE');
    return cli.state.lastToken;
  };

  requireFact(typeof live.repoRoot === 'string' && live.repoRoot, 'LIVE_REPO_ROOT_REQUIRED');
  const inspect = await step('inspect', () => cli('inspect', {authorization: null}));
  await step('begin', () => cli('begin', {authorization, payload: {expected_token: inspect.receipt_token, data: {mode: 'backup_batch', limit}}}));

  const catalog = await step('captureCatalog', () => live.captureCatalog({afterFirstAlbum: live.afterFirstAlbum === true}));
  requireFact(catalog && Array.isArray(catalog.records) && catalog.records.length > 0, 'CATALOG_RECORDS_REQUIRED');
  await step('admit', () => cli('admit', {authorization, payload: {expected_token: token(), data: {records: catalog.records, session: owner}}}));

  let prepared = null;
  const candidates = live.prepareCandidates(catalog.records);
  requireFact(Array.isArray(candidates) && candidates.length > 0, 'NO_PREPARE_CANDIDATE');
  for (const observation of candidates) {
    const response = await step(`prepare`, () => cli('prepare', {authorization, payload: {expected_token: token(), data: {observation}}}));
    const candidate = response.result;
    if (candidate && candidate.status === 'ALBUM_OPEN_READY') { prepared = candidate; break; }
    requireFact(candidate && candidate.status === 'SKIP_VERIFIED', 'PREPARE_UNEXPECTED');
  }
  requireFact(prepared !== null && typeof prepared.run_id === 'string' && typeof prepared.frame_id === 'string'
    && Array.isArray(prepared.click) && prepared.click.length === 2 && prepared.click.every(Number.isFinite),
    'PREPARE_UNEXPECTED');

  const detail = await step('openAlbum+observe', () => session.openAlbum(prepared));
  const calibration = await step('calibrateMenu', () => live.calibrateMenu(detail, prepared));
  await step('calibrate', () => cli('calibrate', {authorization, payload: {expected_token: token(), data: calibration}}));

  const fresh = await step('captureFresh', () => live.captureFresh(detail));
  const permit = await step('originalIntent', () => session.originalIntent({receiptToken: token(), freshObservation: fresh}));

  const {captureMenuSupport, guardMenu} = live.producer;
  const dispatch = await step('originalAtomicDispatch', () => session.originalAtomicDispatch(permit, {captureMenuSupport, guardMenu}));
  const chooser = await step('exactChooser', () => session.exactChooser({dispatch, ...live.locators}));

  const finalized = await step('finalize', async () => cli('finalize', {authorization, payload: {expected_token: token(), data: {
    decoder: `${live.repoRoot}/${TASK.decoder}`, decoder_sha256: TASK.decoderSha256}}}));
  const released = await step('finish', () => cli('finish', {authorization, payload: {expected_token: token(), data: {records: live.finalRecords(), session: owner}}}));
  const release = await step('release', () => cli('release', {authorization, payload: {expected_token: token(), data: {}}}));
  return {inspect, prepared, chooser, finalized, released, release, trace};
}

export function buildLiveRunner({io, runProcess, repoRoot, pythonBin, app, cua, live, owner, authorization}) {
  requireFact(typeof live.producerGeometry === 'function', 'LIVE_GEOMETRY_PROVIDER_REQUIRED');
  const cli = createCli({io, runProcess, repoRoot, pythonBin, authorization});
  const retain = createRetain({io, repoRoot});
  const producer = createProducerHook({io, runProcess, repoRoot, geometryProvider: live.producerGeometry});
  const {createHostedSession, createAlbumSupportCallbacks} = live.adapterModule;
  const supportCallbacks = createAlbumSupportCallbacks({invokeProducer: producer.invokeProducer});
  const session = createHostedSession({
    app: adaptApp(app ?? cua),
    bridge: cli.bridge,
    retain,
    classify: live.classify ?? createClassifier(),
    sessionId: owner,
  });
  // afterFirstAlbum is a real cross-lifecycle fact: it flips only after a completed lifecycle
  // (whose last step is release) so the second catalog capture knows a release already happened.
  const runState = {releasedOnce: false};
  return {cli, retain, producer, session, supportCallbacks, runState, runLifecycle: options =>
    runLifecycle({cli, session, owner, authorization,
      live: {...live, repoRoot, producer: supportCallbacks, afterFirstAlbum: runState.releasedOnce}, ...options})
      .then(result => {runState.releasedOnce = true; return result;})};
}
