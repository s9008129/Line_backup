import {spawn, execFileSync} from 'node:child_process';
import {createHash, randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';
import os from 'node:os';

const MODULE_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_SCRIPT = join(MODULE_DIR, 'line_backup_agent_resume.py');
const DEFAULT_PYTHON = '/usr/bin/python3';
const MAX_LINE_BYTES = 1024 * 1024;
const DEFAULT_TIMEOUT_MS = 10_000;
const FIXED_ROOT = join(os.homedir(), 'Library', 'Application Support', 'LineBackup', 'agent-resume');

export class AgentResumeSessionError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'AgentResumeSessionError';
    this.code = code;
    this.details = details;
  }
}

function processEnv() {
  return {...process.env, LC_ALL: 'C', TZ: 'UTC'};
}

export function readProcessIdentity(pid = process.pid) {
  const output = execFileSync('ps', ['-o', 'lstart=', '-p', String(pid)], {
    encoding: 'utf8',
    env: processEnv(),
  });
  const startedAt = output.trim().split(/\s+/).join(' ');
  if (!startedAt) throw new AgentResumeSessionError('PROCESS_IDENTITY_UNAVAILABLE', 'process identity is empty');
  return {pid: Number(pid), started_at: startedAt};
}

export function readBootIdentity() {
  const output = execFileSync('sysctl', ['-n', 'kern.bootsessionuuid'], {
    encoding: 'utf8',
    env: processEnv(),
  }).trim();
  if (!output) throw new AgentResumeSessionError('BOOT_IDENTITY_UNAVAILABLE', 'boot identity is empty');
  return output;
}

function fixedRootSha256() {
  return createHash('sha256').update(FIXED_ROOT, 'utf8').digest('hex');
}

function validateHello(result, expected, pythonPid) {
  if (!result || typeof result !== 'object') throw new AgentResumeSessionError('HELLO_INVALID', 'hello result is missing');
  if (result.generation !== 0 || result.writer_lock !== 'held' || result.record_state !== 'active') {
    throw new AgentResumeSessionError('HELLO_INVALID', 'hello did not bind the initial durable writer state');
  }
  if (result.root_sha256 !== fixedRootSha256()) {
    throw new AgentResumeSessionError('ROOT_MISMATCH', 'controller did not bind the fixed runtime root');
  }
  if (result.boot_id !== expected.bootId) {
    throw new AgentResumeSessionError('BOOT_IDENTITY_MISMATCH', 'controller boot identity changed');
  }
  if (result.session_id !== expected.sessionId) {
    throw new AgentResumeSessionError('SESSION_ID_MISMATCH', 'controller session identity changed');
  }
  if (!result.controller || result.controller.pid !== pythonPid || typeof result.controller.started_at !== 'string') {
    throw new AgentResumeSessionError('CONTROLLER_IDENTITY_MISMATCH', 'controller identity is not the spawned process');
  }
  if (!result.host || result.host.pid !== expected.host.pid || result.host.started_at !== expected.host.started_at) {
    throw new AgentResumeSessionError('HOST_IDENTITY_MISMATCH', 'GUI host identity changed');
  }
  for (const key of ['file_fsync', 'fullfsync', 'directory_fsync', 'readback']) {
    if (result.sync?.[key] !== true) throw new AgentResumeSessionError('SYNC_CAPABILITY_MISSING', 'target Mac sync capability is incomplete');
  }
  if (result.gui_observations !== 0 || result.gui_dispatches !== 0) {
    throw new AgentResumeSessionError('ZERO_GUI_BOUNDARY_BROKEN', 'M0 session must not observe or dispatch GUI');
  }
}

function waitForExit(child, timeoutMs) {
  if (child.exitCode !== null || child.signalCode !== null) return Promise.resolve(child.exitCode);
  return new Promise(resolve => {
    let settled = false;
    const done = (code, signal) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(code ?? (signal ? 128 : null));
    };
    const timer = setTimeout(() => done(null, 'TIMEOUT'), timeoutMs);
    child.once('exit', done);
  });
}

export async function openAgentResumeSession({
  taskId,
  host = readProcessIdentity(process.pid),
  pythonExecutable = DEFAULT_PYTHON,
  scriptPath = DEFAULT_SCRIPT,
  requestTimeoutMs = DEFAULT_TIMEOUT_MS,
} = {}) {
  if (typeof taskId !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(taskId)) {
    throw new AgentResumeSessionError('TASK_ID_INVALID', 'taskId is invalid');
  }
  if (!host || !Number.isInteger(host.pid) || host.pid <= 0 || typeof host.started_at !== 'string' || !host.started_at) {
    throw new AgentResumeSessionError('HOST_IDENTITY_INVALID', 'host pid/start identity is required');
  }

  const sessionId = randomUUID();
  const bootId = readBootIdentity();
  const child = spawn(pythonExecutable, [scriptPath, 'session', '--task', taskId], {
    shell: false,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: {...processEnv(), PYTHONUNBUFFERED: '1'},
  });

  let closed = false;
  let fatalError = null;
  let stdoutBuffer = '';
  let stderrBuffer = '';
  const pending = new Map();

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
  };

  child.stdin.on('error', error => markClosed(new AgentResumeSessionError('STDIO_WRITE_FAILED', error.message)));
  child.stderr.on('data', chunk => {
    stderrBuffer = (stderrBuffer + chunk.toString('utf8')).slice(-64 * 1024);
  });
  child.once('error', error => markClosed(new AgentResumeSessionError('SESSION_SPAWN_FAILED', error.message)));
  child.once('exit', (code, signal) => {
    if (code === 4) markClosed(new AgentResumeSessionError('WRITER_BUSY', 'another controller holds the writer lock', {code, signal}));
    else if (code === 3) markClosed(new AgentResumeSessionError('SAFETY_BLOCK', 'controller stopped at a safety boundary', {code, signal, stderr: stderrBuffer}));
    else if (code === 5) markClosed(new AgentResumeSessionError('STORAGE_RUNTIME', 'controller reported a storage/runtime failure', {code, signal, stderr: stderrBuffer}));
    else markClosed(new AgentResumeSessionError('SESSION_EXITED', 'controller exited', {code, signal, stderr: stderrBuffer}));
  });

  const handleMessage = message => {
    if (!message || typeof message !== 'object') {
      markClosed(new AgentResumeSessionError('PROTOCOL_INVALID', 'controller emitted a non-object response'));
      return;
    }
    if (message.ok === false) {
      const code = typeof message.error?.code === 'string' ? message.error.code : 'PROTOCOL_ERROR';
      const error = new AgentResumeSessionError(
        code,
        typeof message.error?.message === 'string' ? message.error.message : 'controller rejected the request',
      );
      const waiting = message.request_id != null ? pending.get(message.request_id) : null;
      if (waiting) {
        clearTimeout(waiting.timer);
        pending.delete(message.request_id);
        waiting.reject(error);
      } else {
        markClosed(error);
      }
      return;
    }
    const waiting = pending.get(message.request_id);
    if (!waiting) {
      markClosed(new AgentResumeSessionError('PROTOCOL_REQUEST_MISMATCH', 'controller response does not match a pending request'));
      return;
    }
    clearTimeout(waiting.timer);
    pending.delete(message.request_id);
    if (message.version !== 1 || message.session_id !== sessionId || message.operation !== waiting.operation) {
      waiting.reject(new AgentResumeSessionError('PROTOCOL_BINDING_MISMATCH', 'controller response binding is invalid'));
      return;
    }
    waiting.resolve(message.result);
  };

  child.stdout.on('data', chunk => {
    stdoutBuffer += chunk.toString('utf8');
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

  const request = (operation, data, expectedGeneration) => {
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
      }, requestTimeoutMs);
      pending.set(requestId, {resolve, reject, timer, operation});
      const line = JSON.stringify(payload) + '\n';
      try {
        child.stdin.write(line, error => {
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

  let hello;
  try {
    hello = await request('hello', {host, boot_id: bootId}, 0);
    validateHello(hello, {host, bootId, sessionId}, child.pid);
  } catch (error) {
    markClosed(error instanceof AgentResumeSessionError ? error : new AgentResumeSessionError('HELLO_FAILED', String(error)));
    child.kill('SIGKILL');
    await waitForExit(child, 2_000);
    throw fatalError ?? error;
  }

  const ping = async () => {
    const result = await request('ping', {}, 0);
    if (!result || result.pong !== true || result.stopped !== false) {
      throw new AgentResumeSessionError('PING_INVALID', 'ping result is invalid');
    }
    return Object.freeze({pong: true, stopped: false});
  };

  const close = async () => {
    if (closed) throw fatalError ?? new AgentResumeSessionError('SESSION_CLOSED', 'session is already closed');
    const result = await request('close', {}, 0);
    if (!result || result.closed !== true) throw new AgentResumeSessionError('CLOSE_INVALID', 'close result is invalid');
    child.stdin.end();
    const exitCode = await waitForExit(child, requestTimeoutMs);
    markClosed(new AgentResumeSessionError('SESSION_CLOSED', 'session closed'));
    if (exitCode !== 0) throw new AgentResumeSessionError('CLOSE_EXIT_NONZERO', 'controller did not exit cleanly');
    return Object.freeze({closed: true, exitCode: 0});
  };

  return Object.freeze({
    taskId,
    sessionId,
    bootId,
    controller: Object.freeze({...hello.controller}),
    host: Object.freeze({...hello.host}),
    rootSha256: hello.root_sha256,
    sync: Object.freeze({...hello.sync}),
    generation: hello.generation,
    ping,
    close,
    get closed() {
      return closed;
    },
  });
}
