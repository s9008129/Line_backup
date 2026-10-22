import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {randomUUID} from 'node:crypto';
import {
  AgentResumeSessionError,
  openAgentResumeSession,
  readBootIdentity,
  readProcessIdentity,
} from '../scripts/line_backup_agent_resume_cua.mjs';

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function startFakeHost() {
  const child = spawn(process.execPath, ['-e', 'setInterval(() => {}, 1000)'], {
    stdio: 'ignore',
  });
  await once(child, 'spawn');
  return {child, identity: readProcessIdentity(child.pid)};
}

async function stopFakeHost(host) {
  if (!host || host.child.exitCode !== null || host.child.signalCode !== null) return;
  host.child.kill('SIGKILL');
  await once(host.child, 'exit');
  await delay(50);
}

async function waitUntil(predicate, timeoutMs = 2_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (predicate()) return;
    await delay(20);
  }
  throw new Error('condition timeout');
}

test('M0 fixed-root JSON-lines session capabilities', async t => {
  const taskId = `AGENT-RESUME-M0-${randomUUID()}`;

  await t.test('single stdio session, real identities, full sync, clean close', async () => {
    const host = await startFakeHost();
    let session;
    try {
      session = await openAgentResumeSession({taskId, host: host.identity});
      assert.equal(session.generation, 0);
      assert.equal(session.closed, false);
      assert.notEqual(session.controller.pid, host.identity.pid);
      assert.equal(typeof session.controller.started_at, 'string');
      assert.deepEqual(session.host, {...host.identity});
      assert.equal(session.bootId, readBootIdentity());
      assert.match(session.rootSha256, /^[0-9a-f]{64}$/);
      assert.deepEqual(session.sync && {
        file_fsync: session.sync.file_fsync,
        fullfsync: session.sync.fullfsync,
        directory_fsync: session.sync.directory_fsync,
        readback: session.sync.readback,
      }, {file_fsync: true, fullfsync: true, directory_fsync: true, readback: true});
      assert.deepEqual(await session.ping(), {pong: true, stopped: false});
      assert.deepEqual(await session.close(), {closed: true, exitCode: 0});
      await waitUntil(() => session.closed);
      await assert.rejects(session.ping(), error => error instanceof AgentResumeSessionError);
    } finally {
      if (session && !session.closed) {
        try { await session.close(); } catch {}
      }
      await stopFakeHost(host);
    }
  });

  await t.test('stale host start identity is refused before GUI capability', async () => {
    const host = await startFakeHost();
    try {
      await assert.rejects(
        openAgentResumeSession({
          taskId,
          host: {pid: host.identity.pid, started_at: 'not-the-real-start'},
        }),
        error => error.code === 'HOST_IDENTITY_STALE',
      );
    } finally {
      await stopFakeHost(host);
    }
  });

  await t.test('controller loss permanently closes wrapper; live old host blocks takeover', async () => {
    const oldHost = await startFakeHost();
    const newHost = await startFakeHost();
    let session;
    try {
      session = await openAgentResumeSession({taskId, host: oldHost.identity});
      process.kill(session.controller.pid, 'SIGKILL');
      await waitUntil(() => session.closed);
      await assert.rejects(session.ping(), error => error instanceof AgentResumeSessionError);

      await assert.rejects(
        openAgentResumeSession({taskId, host: newHost.identity}),
        error => error.code === 'OLD_HOST_ALIVE',
      );

      await stopFakeHost(oldHost);
      const takeover = await openAgentResumeSession({taskId, host: newHost.identity});
      assert.deepEqual(await takeover.ping(), {pong: true, stopped: false});
      assert.deepEqual(await takeover.close(), {closed: true, exitCode: 0});
    } finally {
      if (session && !session.closed) {
        try { await session.close(); } catch {}
      }
      await stopFakeHost(oldHost);
      await stopFakeHost(newHost);
    }
  });

  await t.test('second controller receives writer busy', async () => {
    const firstHost = await startFakeHost();
    const secondHost = await startFakeHost();
    let first;
    try {
      first = await openAgentResumeSession({taskId, host: firstHost.identity});
      await assert.rejects(
        openAgentResumeSession({taskId, host: secondHost.identity}),
        error => error.code === 'WRITER_BUSY',
      );
      assert.deepEqual(await first.close(), {closed: true, exitCode: 0});
    } finally {
      if (first && !first.closed) {
        try { await first.close(); } catch {}
      }
      await stopFakeHost(firstHost);
      await stopFakeHost(secondHost);
    }
  });
});
