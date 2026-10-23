import {spawn, spawnSync, execFileSync} from 'node:child_process';
import {createHash, randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';
import os from 'node:os';
import {StringDecoder} from 'node:string_decoder';

const MODULE_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_SCRIPT = join(MODULE_DIR, 'line_backup_agent_resume.py');
const DEFAULT_PYTHON = '/usr/bin/python3';
const MAX_LINE_BYTES = 1024 * 1024;
const DEFAULT_TIMEOUT_MS = 10_000;
const LONG_OPERATION_TIMEOUT_MS = 660_000;
const TASK_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const MUTATING_OPERATIONS = new Set([
  'prepare_save_all',
  'record_save_all_result',
  'prepare_chooser_confirm',
  'record_chooser_result',
  'verify_album',
]);

export class AgentResumeSessionError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'AgentResumeSessionError';
    this.code = code;
    this.details = details;
  }
}

function fixedRoot() {
  return join(os.homedir(), 'Library', 'Application Support', 'LineBackup', 'agent-resume');
}

function fixedRootSha256(root) {
  return createHash('sha256').update(root, 'utf8').digest('hex');
}

function processEnv() {
  return {...process.env, LC_ALL: 'C', TZ: 'UTC'};
}

function requireSha256(value, code, field) {
  if (typeof value !== 'string' || !SHA256_PATTERN.test(value)) {
    throw new AgentResumeSessionError(code, `${field} must be a lowercase SHA-256`);
  }
}

function requireNonEmptyString(value, code, field) {
  if (typeof value !== 'string' || !value) {
    throw new AgentResumeSessionError(code, `${field} must be a non-empty string`);
  }
}

function requireIdentity(value, code, field) {
  if (!value || !Number.isInteger(value.pid) || value.pid <= 0) {
    throw new AgentResumeSessionError(code, `${field} pid is invalid`);
  }
  requireNonEmptyString(value.started_at, code, `${field}.started_at`);
}

function identitiesEqual(left, right) {
  return Boolean(left && right && left.pid === right.pid && left.started_at === right.started_at);
}

function setEquals(keys, expected) {
  return keys.length === expected.length && expected.every(item => keys.includes(item));
}

export function readProcessIdentity(pid = process.pid) {
  try {
    const output = execFileSync('ps', ['-o', 'lstart=', '-p', String(pid)], {
      encoding: 'utf8',
      env: processEnv(),
      timeout: 3_000,
    });
    const startedAt = output.trim().split(/\s+/).join(' ');
    if (!startedAt) throw new Error('empty process start identity');
    return {pid: Number(pid), started_at: startedAt};
  } catch (error) {
    throw new AgentResumeSessionError('PROCESS_IDENTITY_UNAVAILABLE', 'process identity is unavailable', {
      pid,
      cause: String(error),
    });
  }
}

export function readBootIdentity() {
  try {
    const output = execFileSync('sysctl', ['-n', 'kern.bootsessionuuid'], {
      encoding: 'utf8',
      env: processEnv(),
      timeout: 3_000,
    }).trim();
    if (!output) throw new Error('empty boot identity');
    return output;
  } catch (error) {
    throw new AgentResumeSessionError('BOOT_IDENTITY_UNAVAILABLE', 'boot identity is unavailable', {
      cause: String(error),
    });
  }
}

function parseSingleJsonLine(raw, code, label) {
  const lines = raw.split(/\r?\n/).filter(line => line.length > 0);
  if (lines.length !== 1) throw new AgentResumeSessionError(code, `${label} did not emit exactly one JSON line`);
  try {
    return JSON.parse(lines[0]);
  } catch (error) {
    throw new AgentResumeSessionError(code, `${label} emitted invalid JSON`, {cause: String(error)});
  }
}

function inspectTask({pythonExecutable, scriptPath, taskId}) {
  const root = fixedRoot();
  const completed = spawnSync(
    pythonExecutable,
    [scriptPath, 'inspect', '--root', root, '--task', taskId],
    {
      shell: false,
      encoding: 'utf8',
      env: processEnv(),
      timeout: DEFAULT_TIMEOUT_MS,
      maxBuffer: MAX_LINE_BYTES * 4,
    },
  );
  if (completed.error) {
    throw new AgentResumeSessionError('INSPECT_FAILED', 'read-only task inspection could not run', {
      cause: String(completed.error),
    });
  }
  const result = parseSingleJsonLine(completed.stdout ?? '', 'INSPECT_OUTPUT_INVALID', 'inspection');
  if (completed.status !== 0 || result.ok !== true) {
    const code = typeof result.error?.code === 'string' ? result.error.code : 'INSPECT_FAILED';
    throw new AgentResumeSessionError(code, 'read-only task inspection was rejected', {
      exitCode: completed.status,
      stderr: completed.stderr ?? '',
    });
  }
  if (result.task_id !== taskId) {
    throw new AgentResumeSessionError('INSPECT_TASK_MISMATCH', 'inspection returned a different task');
  }
  if (!Number.isInteger(result.generation) || result.generation < 0) {
    throw new AgentResumeSessionError('INSPECT_GENERATION_INVALID', 'inspection generation is invalid');
  }
  requireSha256(result.checkpoint_sha256, 'INSPECT_CHECKPOINT_INVALID', 'checkpoint_sha256');
  if (!Number.isInteger(result.album_count) || result.album_count < 1) {
    throw new AgentResumeSessionError('INSPECT_MANIFEST_INVALID', 'inspection did not bind an ordered manifest');
  }
  if (result.gui_dispatches !== 0) {
    throw new AgentResumeSessionError('INSPECT_NOT_READ_ONLY', 'inspection reported a GUI dispatch');
  }
  return result;
}

function validateHello(result, expected) {
  if (!result || typeof result !== 'object') {
    throw new AgentResumeSessionError('HELLO_INVALID', 'hello result is missing');
  }
  if (!Number.isInteger(result.generation) || result.generation < 0) {
    throw new AgentResumeSessionError('HELLO_INVALID', 'hello generation is invalid');
  }
  if (result.writer_lock !== 'held' || result.record_state !== 'ACTIVE') {
    throw new AgentResumeSessionError('HELLO_INVALID', 'hello did not bind the durable writer state');
  }
  requireSha256(result.checkpoint_sha256, 'HELLO_INVALID', 'checkpoint_sha256');
  if (result.root_sha256 !== fixedRootSha256(expected.root)) {
    throw new AgentResumeSessionError('ROOT_MISMATCH', 'controller did not bind the fixed runtime root');
  }
  if (result.boot_id !== expected.bootId) {
    throw new AgentResumeSessionError('BOOT_IDENTITY_MISMATCH', 'controller boot identity changed');
  }
  if (result.session_id !== expected.sessionId) {
    throw new AgentResumeSessionError('SESSION_ID_MISMATCH', 'controller session identity changed');
  }
  if (!result.controller || result.controller.pid !== expected.controllerPid) {
    throw new AgentResumeSessionError('CONTROLLER_IDENTITY_MISMATCH', 'controller identity is not the spawned process');
  }
  requireIdentity(result.controller, 'CONTROLLER_IDENTITY_MISMATCH', 'controller');
  if (!identitiesEqual(result.host, expected.host)) {
    throw new AgentResumeSessionError('HOST_IDENTITY_MISMATCH', 'GUI host identity changed');
  }
  for (const key of ['file_fsync', 'fullfsync', 'directory_fsync', 'readback']) {
    if (result.sync?.[key] !== true) {
      throw new AgentResumeSessionError('SYNC_CAPABILITY_MISSING', 'target Mac sync capability is incomplete');
    }
  }
  if (result.gui_observations !== 0 || result.gui_dispatches !== 0) {
    throw new AgentResumeSessionError('ZERO_GUI_BOUNDARY_BROKEN', 'hello must not observe or dispatch GUI');
  }
  if (
    !result.resume_state
    || typeof result.resume_state !== 'object'
    || result.resume_state.task_id !== expected.taskId
    || result.resume_state.generation !== result.generation
    || result.resume_state.checkpoint_sha256 !== result.checkpoint_sha256
    || !Number.isInteger(result.resume_state.album_count)
    || result.resume_state.album_count < 1
  ) {
    throw new AgentResumeSessionError('HELLO_PREFLIGHT_INVALID', 'hello did not include a bound fast preflight');
  }
}

function waitForExit(child, timeoutMs) {
  if (child.exitCode !== null || child.signalCode !== null) {
    return Promise.resolve({code: child.exitCode, signal: child.signalCode});
  }
  return new Promise((resolve, reject) => {
    let settled = false;
    const done = (code, signal) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({code, signal});
    };
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      reject(new AgentResumeSessionError('CONTROLLER_EXIT_TIMEOUT', 'controller did not exit in time'));
    }, timeoutMs);
    child.once('exit', done);
  });
}

function clickPoint(grounding) {
  const point = grounding?.click_point;
  if (!point || typeof point !== 'object' || !setEquals(Object.keys(point), ['x', 'y'])) {
    throw new AgentResumeSessionError('CLICK_POINT_INVALID', 'grounding click point is invalid');
  }
  for (const axis of ['x', 'y']) {
    if (typeof point[axis] !== 'number' || !Number.isFinite(point[axis]) || point[axis] < 0) {
      throw new AgentResumeSessionError('CLICK_POINT_INVALID', 'grounding click point is invalid');
    }
  }
  return {x: point.x, y: point.y};
}

export async function openAgentResumeSession({
  taskId,
  host,
  app,
  pythonExecutable = DEFAULT_PYTHON,
  scriptPath = DEFAULT_SCRIPT,
  requestTimeoutMs = DEFAULT_TIMEOUT_MS,
  longOperationTimeoutMs = LONG_OPERATION_TIMEOUT_MS,
  clickTimeoutMs = DEFAULT_TIMEOUT_MS,
} = {}) {
  if (typeof taskId !== 'string' || !TASK_ID_PATTERN.test(taskId)) {
    throw new AgentResumeSessionError('TASK_ID_INVALID', 'taskId is invalid');
  }
  requireIdentity(host, 'HOST_IDENTITY_INVALID', 'host');
  if (host.pid === process.pid) {
    throw new AgentResumeSessionError('HOST_PROCESS_CONFUSED', 'the GUI host must be a distinct process');
  }
  const observedHost = readProcessIdentity(host.pid);
  if (!identitiesEqual(observedHost, host)) {
    throw new AgentResumeSessionError('HOST_IDENTITY_STALE', 'GUI host process identity is stale');
  }
  if (!app || typeof app.click !== 'function') {
    throw new AgentResumeSessionError('APP_HANDLE_INVALID', 'an existing app handle with click(point) is required');
  }
  if (!Number.isFinite(clickTimeoutMs) || clickTimeoutMs <= 0) {
    throw new AgentResumeSessionError('CLICK_TIMEOUT_INVALID', 'clickTimeoutMs must be positive');
  }
  if (!Number.isFinite(requestTimeoutMs) || requestTimeoutMs <= 0) {
    throw new AgentResumeSessionError('REQUEST_TIMEOUT_INVALID', 'requestTimeoutMs must be positive');
  }
  if (!Number.isFinite(longOperationTimeoutMs) || longOperationTimeoutMs <= 0) {
    throw new AgentResumeSessionError('LONG_OPERATION_TIMEOUT_INVALID', 'longOperationTimeoutMs must be positive');
  }

  const root = fixedRoot();
  const initial = inspectTask({pythonExecutable, scriptPath, taskId});
  const sessionId = randomUUID();
  const bootId = readBootIdentity();
  const child = spawn(pythonExecutable, [scriptPath, 'session', '--root', root, '--task', taskId], {
    shell: false,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: {...processEnv(), PYTHONUNBUFFERED: '1'},
  });

  let generation = initial.generation;
  let closed = false;
  let fatalError = null;
  let stdoutBuffer = '';
  let stderrBuffer = '';
  let preflighted = false;
  let latestReconcile = null;
  const pending = new Map();
  const consumedActionIds = new Set();
  let serialTail = Promise.resolve();

  const rejectPending = error => {
    for (const entry of pending.values()) {
      clearTimeout(entry.timer);
      entry.reject(error);
    }
    pending.clear();
  };

  const markClosed = error => {
    if (closed) return;
    closed = true;
    if (error && !fatalError) fatalError = error;
    rejectPending(error ?? new AgentResumeSessionError('SESSION_CLOSED', 'session is permanently closed'));
    child.kill('SIGKILL');
  };

  const serialized = operation => {
    const next = serialTail.then(operation, operation);
    serialTail = next.catch(() => {});
    return next;
  };

  child.stdin.on('error', error => {
    markClosed(new AgentResumeSessionError('STDIO_WRITE_FAILED', error.message));
  });
  child.stderr.on('data', chunk => {
    stderrBuffer = (stderrBuffer + chunk.toString('utf8')).slice(-64 * 1024);
  });
  child.once('error', error => {
    markClosed(new AgentResumeSessionError('SESSION_SPAWN_FAILED', error.message));
  });
  child.once('exit', (code, signal) => {
    if (code === 4) {
      markClosed(new AgentResumeSessionError('WRITER_BUSY', 'another controller holds the writer lock', {code, signal}));
    } else if (code === 3) {
      markClosed(new AgentResumeSessionError('SAFETY_BLOCK', 'controller stopped at a safety boundary', {
        code,
        signal,
        stderr: stderrBuffer,
      }));
    } else if (code === 5) {
      markClosed(new AgentResumeSessionError('STORAGE_RUNTIME', 'controller reported a storage/runtime failure', {
        code,
        signal,
        stderr: stderrBuffer,
      }));
    } else if (code !== 0 || !closed) {
      markClosed(new AgentResumeSessionError('SESSION_EXITED', 'controller exited', {code, signal, stderr: stderrBuffer}));
    }
  });

  const handleMessage = message => {
    if (!message || typeof message !== 'object') {
      markClosed(new AgentResumeSessionError('PROTOCOL_INVALID', 'controller emitted a non-object response'));
      return;
    }
    const waiting = message.request_id != null ? pending.get(message.request_id) : null;
    if (message.ok === false) {
      const code = typeof message.error?.code === 'string' ? message.error.code : 'PROTOCOL_ERROR';
      const error = new AgentResumeSessionError(
        code,
        typeof message.error?.message === 'string' ? message.error.message : 'controller rejected the request',
      );
      if (waiting) {
        clearTimeout(waiting.timer);
        pending.delete(message.request_id);
        waiting.reject(error);
      }
      markClosed(error);
      return;
    }
    if (!waiting) {
      markClosed(new AgentResumeSessionError('PROTOCOL_REQUEST_MISMATCH', 'controller response does not match a pending request'));
      return;
    }
    clearTimeout(waiting.timer);
    pending.delete(message.request_id);
    if (message.version !== 1 || message.session_id !== sessionId || message.operation !== waiting.operation) {
      const error = new AgentResumeSessionError('PROTOCOL_BINDING_MISMATCH', 'controller response binding is invalid');
      waiting.reject(error);
      markClosed(error);
      return;
    }
    waiting.resolve(message.result);
  };

  const stdoutDecoder = new StringDecoder('utf8');
  child.stdout.on('data', chunk => {
    stdoutBuffer += stdoutDecoder.write(chunk);
    if (Buffer.byteLength(stdoutBuffer, 'utf8') > MAX_LINE_BYTES && !stdoutBuffer.includes('\n')) {
      markClosed(new AgentResumeSessionError('PROTOCOL_LINE_TOO_LARGE', 'controller response exceeds the size limit'));
      return;
    }
    while (true) {
      const newline = stdoutBuffer.indexOf('\n');
      if (newline < 0) break;
      const line = stdoutBuffer.slice(0, newline);
      stdoutBuffer = stdoutBuffer.slice(newline + 1);
      if (!line) continue;
      if (Buffer.byteLength(line, 'utf8') > MAX_LINE_BYTES) {
        markClosed(new AgentResumeSessionError('PROTOCOL_LINE_TOO_LARGE', 'controller response exceeds the size limit'));
        return;
      }
      let parsed;
      try {
        parsed = JSON.parse(line);
      } catch {
        markClosed(new AgentResumeSessionError('PROTOCOL_JSON_INVALID', 'controller emitted invalid JSON'));
        return;
      }
      handleMessage(parsed);
    }
  });

  const request = (operation, data = {}, expectedGeneration = generation, timeoutMs = requestTimeoutMs) => {
    if (closed) {
      return Promise.reject(fatalError ?? new AgentResumeSessionError('SESSION_CLOSED', 'session is permanently closed'));
    }
    const requestId = randomUUID();
    const payload = {
      version: 1,
      request_id: requestId,
      session_id: sessionId,
      task_id: taskId,
      expected_generation: expectedGeneration,
      operation,
      data,
    };
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(requestId);
        const error = new AgentResumeSessionError('REQUEST_TIMEOUT', 'controller request timed out');
        markClosed(error);
        child.kill('SIGKILL');
        reject(error);
      }, timeoutMs);
      pending.set(requestId, {resolve, reject, timer, operation});
      try {
        child.stdin.write(JSON.stringify(payload) + '\n', error => {
          if (!error) return;
          const waiting = pending.get(requestId);
          if (!waiting) return;
          clearTimeout(waiting.timer);
          pending.delete(requestId);
          const failure = new AgentResumeSessionError('STDIO_WRITE_FAILED', error.message);
          markClosed(failure);
          waiting.reject(failure);
        });
      } catch (error) {
        clearTimeout(timer);
        pending.delete(requestId);
        const failure = new AgentResumeSessionError('STDIO_WRITE_FAILED', String(error));
        markClosed(failure);
        reject(failure);
      }
    });
  };

  const updateGeneration = result => {
    if (!Number.isInteger(result?.generation) || result.generation < generation) {
      throw new AgentResumeSessionError('GENERATION_RESULT_INVALID', 'controller returned an invalid generation');
    }
    generation = result.generation;
    return result;
  };

  const readback = () => inspectTask({pythonExecutable, scriptPath, taskId});

  const verifyCheckpointBinding = (expectedGeneration, expectedCheckpoint) => {
    const current = readback();
    if (current.generation !== expectedGeneration || current.checkpoint_sha256 !== expectedCheckpoint) {
      throw new AgentResumeSessionError('CHECKPOINT_READBACK_MISMATCH', 'durable checkpoint readback does not match the ack');
    }
    return current;
  };

  const reconcileInternal = async () => {
    const result = await request('reconcile', {}, generation, longOperationTimeoutMs);
    if (!result || result.task_id !== taskId || !Number.isInteger(result.generation)) {
      throw new AgentResumeSessionError('RECONCILE_INVALID', 'reconciliation result is invalid');
    }
    updateGeneration(result);
    preflighted = true;
    latestReconcile = result;
    return result;
  };

  let hello;
  try {
    hello = await request('hello', {host, boot_id: bootId}, initial.generation);
    validateHello(hello, {taskId, host, bootId, sessionId, root, controllerPid: child.pid});
    updateGeneration(hello);
    const postHello = verifyCheckpointBinding(hello.generation, hello.checkpoint_sha256);
    if (
      postHello.album_count < 1
      || hello.resume_state.album_count !== postHello.album_count
      || hello.resume_state.manifest_binding_sha256 !== postHello.manifest_binding_sha256
    ) {
      throw new AgentResumeSessionError('HELLO_MANIFEST_INVALID', 'session task manifest is incomplete');
    }
    preflighted = true;
    latestReconcile = hello.resume_state;
  } catch (error) {
    const failure = error instanceof AgentResumeSessionError
      ? error
      : new AgentResumeSessionError('HELLO_FAILED', String(error));
    markClosed(failure);
    child.kill('SIGKILL');
    await waitForExit(child, 2_000).catch(() => {});
    throw fatalError ?? failure;
  }

  const assertHostLive = () => {
    const observed = readProcessIdentity(host.pid);
    if (!identitiesEqual(observed, host)) {
      throw new AgentResumeSessionError('HOST_IDENTITY_STALE', 'GUI host process changed before input');
    }
  };

  const clickOnce = point => new Promise((resolve, reject) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      reject(new AgentResumeSessionError('GUI_CLICK_TIMEOUT', 'GUI click did not settle in time'));
    }, clickTimeoutMs);
    Promise.resolve()
      .then(() => app.click(point))
      .then(value => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(value);
      }, error => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        reject(error);
      });
  });

  const validateIntentAck = (result, operation, albumKey) => {
    if (!result || typeof result !== 'object') {
      throw new AgentResumeSessionError('INTENT_ACK_INVALID', `${operation} acknowledgement is missing`);
    }
    if (result.click_eligible !== true || result.album_key !== albumKey) {
      throw new AgentResumeSessionError('INTENT_ACK_INVALID', `${operation} acknowledgement is not click eligible`);
    }
    if (typeof result.action_id !== 'string' || !UUID_PATTERN.test(result.action_id)) {
      throw new AgentResumeSessionError('INTENT_ACK_INVALID', `${operation} action id is invalid`);
    }
    if (consumedActionIds.has(result.action_id)) {
      throw new AgentResumeSessionError('INTENT_ACK_REPLAYED', `${operation} acknowledgement was already consumed`);
    }
    if (!Number.isInteger(result.generation) || result.generation < 0) {
      throw new AgentResumeSessionError('INTENT_ACK_INVALID', `${operation} generation is invalid`);
    }
    requireSha256(result.checkpoint_sha256, 'INTENT_ACK_INVALID', 'checkpoint_sha256');
    updateGeneration(result);
    const current = verifyCheckpointBinding(result.generation, result.checkpoint_sha256);
    const album = Array.isArray(current.albums) ? current.albums.find(item => item.album_key === albumKey) : null;
    if (!album) throw new AgentResumeSessionError('INTENT_ALBUM_MISSING', 'durable checkpoint does not expose the prepared album');
    if (!MUTATING_OPERATIONS.has(operation)) {
      throw new AgentResumeSessionError('INTENT_OPERATION_INVALID', 'intent operation is invalid');
    }
    return result;
  };

  const recordUnknownEvidence = (error, fallback) => {
    const detail = {
      code: error && typeof error.code === 'string' ? error.code : 'GUI_CALL_AMBIGUOUS',
      message: error && typeof error.message === 'string' ? error.message : String(error ?? ''),
      fallback,
    };
    return createHash('sha256').update(JSON.stringify(detail), 'utf8').digest('hex');
  };

  const executeIntent = async ({
    prepareOperation,
    recordOperation,
    albumKey,
    grounding,
    resultEvidenceSha256,
  }) => {
    if (!preflighted) {
      throw new AgentResumeSessionError('FAST_PREFLIGHT_REQUIRED', 'a fast preflight must succeed first');
    }
    requireSha256(resultEvidenceSha256, 'RESULT_EVIDENCE_INVALID', 'resultEvidenceSha256');
    const point = clickPoint(grounding);
    const prepared = await request(prepareOperation, {album_key: albumKey, grounding}, generation);
    validateIntentAck(prepared, prepareOperation, albumKey);
    consumedActionIds.add(prepared.action_id);

    let outcome = 'RETURNED';
    let clickError = null;
    let clickInvoked = false;
    try {
      assertHostLive();
      if (closed || child.exitCode !== null || child.signalCode !== null) {
        throw (fatalError ?? new AgentResumeSessionError('SESSION_CLOSED', 'controller was lost before GUI input'));
      }
      clickInvoked = true;
      await clickOnce(point);
    } catch (error) {
      outcome = 'UNKNOWN';
      clickError = error;
    }
    const evidenceSha256 = outcome === 'RETURNED'
      ? resultEvidenceSha256
      : recordUnknownEvidence(clickError, `${prepareOperation}:${albumKey}`);

    let recorded;
    try {
      recorded = await request(
        recordOperation,
        {album_key: albumKey, action_id: prepared.action_id, outcome, evidence_sha256: evidenceSha256},
        generation,
      );
      updateGeneration(recorded);
    } catch (error) {
      throw new AgentResumeSessionError(
        'INTENT_RESULT_RECORD_FAILED',
        'the GUI call occurred but its durable result could not be committed',
        {outcome, actionId: prepared.action_id, cause: String(error)},
      );
    }
    return Object.freeze({
      albumKey,
      actionId: prepared.action_id,
      outcome,
      clickAttempted: clickInvoked,
      clickError: clickError ? String(clickError) : null,
      generation: recorded.generation,
      checkpointSha256: recorded.checkpoint_sha256,
    });
  };

  const reconcile = () => serialized(() => reconcileInternal());

  const preflight = () => serialized(async () => {
    if (closed) {
      throw fatalError ?? new AgentResumeSessionError('SESSION_CLOSED', 'session is permanently closed');
    }
    const current = readback();
    if (current.generation !== generation) {
      throw new AgentResumeSessionError('GENERATION_STALE', 'fast preflight observed a newer checkpoint');
    }
    latestReconcile = current;
    preflighted = true;
    return current;
  });

  const saveAll = ({albumKey, grounding, resultEvidenceSha256} = {}) => serialized(() => executeIntent({
    prepareOperation: 'prepare_save_all',
    recordOperation: 'record_save_all_result',
    albumKey,
    grounding,
    resultEvidenceSha256,
  }));

  const confirmChooser = ({albumKey, grounding, resultEvidenceSha256} = {}) => serialized(() => executeIntent({
    prepareOperation: 'prepare_chooser_confirm',
    recordOperation: 'record_chooser_result',
    albumKey,
    grounding,
    resultEvidenceSha256,
  }));

  const verifyAlbum = ({albumKey} = {}) => serialized(async () => {
    if (!preflighted) {
      throw new AgentResumeSessionError('FAST_PREFLIGHT_REQUIRED', 'a fast preflight must succeed first');
    }
    if (typeof albumKey !== 'string' || !SHA256_PATTERN.test(albumKey)) {
      throw new AgentResumeSessionError('ALBUM_KEY_INVALID', 'albumKey is invalid');
    }
    const result = await request('verify_album', {album_key: albumKey}, generation, longOperationTimeoutMs);
    updateGeneration(result);
    return Object.freeze({...result});
  });

  const close = () => serialized(async () => {
    if (closed) throw fatalError ?? new AgentResumeSessionError('SESSION_CLOSED', 'session is already closed');
    const result = await request('close', {}, generation);
    if (!result || result.closed !== true || !Number.isInteger(result.generation)) {
      throw new AgentResumeSessionError('CLOSE_INVALID', 'close result is invalid');
    }
    updateGeneration(result);
    child.stdin.end();
    const exit = await waitForExit(child, requestTimeoutMs);
    if (exit.code !== 0) {
      throw new AgentResumeSessionError('CLOSE_EXIT_NONZERO', 'controller did not exit cleanly', exit);
    }
    markClosed(new AgentResumeSessionError('SESSION_CLOSED', 'session closed'));
    return Object.freeze({closed: true, exitCode: 0, generation: result.generation});
  });

  return Object.freeze({
    taskId,
    sessionId,
    bootId,
    controller: Object.freeze({...hello.controller}),
    host: Object.freeze({...hello.host}),
    rootSha256: hello.root_sha256,
    sync: Object.freeze({...hello.sync}),
    get generation() {
      return generation;
    },
    get reconcileResult() {
      return latestReconcile;
    },
    get preflightResult() {
      return latestReconcile;
    },
    reconcile,
    preflight,
    saveAll,
    confirmChooser,
    verifyAlbum,
    close,
    get closed() {
      return closed;
    },
  });
}
