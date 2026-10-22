import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn, spawnSync} from 'node:child_process';
import {once} from 'node:events';
import {randomUUID} from 'node:crypto';
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
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

const fakeApp = {
  async click() {
    return {clicked: true};
  },
};

const fixtureScript = String.raw`
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.environ["REPO_ROOT"], "scripts"))
import line_backup_agent_resume as resume

home = Path(os.environ["HOME"])
root = home / "Library" / "Application Support" / "LineBackup" / "agent-resume"
root.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(root, 0o700)

source = root / "fixture-history.json"
source.write_bytes(resume.canonical_json({"fixture": "m0-history"}) + b"\n")
source_raw = source.read_bytes()
history_destination = root / "fixture-history-destination"
history_destination.mkdir(mode=0o700, exist_ok=True)
os.chmod(history_destination, 0o700)
(history_destination / "history.bin").write_bytes(b"h")
source_sha = resume.sha256_bytes(source_raw)
reference = {
    "source_kind": "fixture_history",
    "path": str(source.resolve()),
    "sha256": source_sha,
    "bytes": len(source_raw),
    "imported_at_utc": resume.utc_now(),
}
barrier = resume._barrier(
    "fixture_history",
    source_sha,
    "fixture-group",
    {"start_date": "2023-01-01", "end_date": "2023-01-01", "expected_images": 1},
    [str(history_destination.resolve())],
    1,
    "SYNTHETIC_HISTORY_BARRIER",
    "fixture-history",
)
store = resume._initial_store()
store["history"] = {"references": [reference], "barriers": [barrier]}
store["payload_sha256"] = resume._payload_digest(store)
resume._atomic_json_write(root / "checkpoint.json", store)

active_base = dt.date(2026, 1, 1)
albums = []
for index in range(100):
    if index == 0:
        day = dt.date(2023, 1, 1)
    else:
        day = active_base + dt.timedelta(days=index - 1)
    ordinal = index + 1
    albums.append({
        "identity": {
            "group_key": "fixture-group",
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "expected_images": 1,
            "observed_title": "fixture-album-%03d" % ordinal,
            "disambiguator": "fixture:%03d" % ordinal,
        },
        "destination": "downloads/album-%03d" % ordinal,
    })
manifest = {
    "schema_version": 1,
    "task_id": os.environ["TASK_ID"],
    "scope": {
        "group_key": "fixture-group",
        "app_identifier": "com.example.line-fixture",
        "owner_id": "fixture-owner",
        "scope_id": "fixture-scope",
    },
    "owner_authorization_reference": "OWNER_FIXTURE_ONLY",
    "exclusions": [],
    "albums": albums,
}
manifest_path = home / "fixture-manifest.json"
manifest_path.write_bytes(resume.canonical_json(manifest) + b"\n")
resume.create_task(root, manifest_path)
print(json.dumps({"generation": resume.read_store(root)["generation"]}))
`;

function createResumeFixture(taskId) {
  const home = mkdtempSync(join(tmpdir(), 'agent-resume-cua-'));
  const setup = spawnSync('/usr/bin/python3', ['-c', fixtureScript], {
    encoding: 'utf8',
    env: {
      ...process.env,
      HOME: home,
      REPO_ROOT: process.cwd(),
      TASK_ID: taskId,
    },
    timeout: 30_000,
  });
  if (setup.status !== 0) {
    rmSync(home, {recursive: true, force: true});
    throw new Error(`fixture setup failed: ${setup.stderr || setup.stdout || `exit ${setup.status}`}`);
  }
  return {home, generation: JSON.parse(setup.stdout.trim()).generation};
}

function firstNotStartedAlbum(session) {
  const album = session.reconcileResult?.albums?.find(item => item.state === 'NOT_STARTED');
  assert.ok(album, 'fixture must expose a not-started album');
  return album;
}

function saveAllGrounding(albumKey) {
  return {
    app_identifier: 'com.example.line-fixture',
    group_key: 'fixture-group',
    album_key: albumKey,
    window_id: 'fixture-window',
    foreground_authorization_reference: 'OWNER_FIXTURE_FOREGROUND',
    detail_identity: 'fixture-detail',
    menu_identity: 'fixture-save-all-menu',
    click_point: {x: 120, y: 240},
    destination_empty: true,
    evidence_sha256: 'a'.repeat(64),
  };
}

function chooserGrounding(albumKey) {
  return {
    app_identifier: 'com.example.line-fixture',
    group_key: 'fixture-group',
    album_key: albumKey,
    window_id: 'fixture-window',
    foreground_authorization_reference: 'OWNER_FIXTURE_FOREGROUND',
    chooser_identity: 'fixture-chooser',
    click_point: {x: 140, y: 260},
    evidence_sha256: 'b'.repeat(64),
  };
}

test('M0 fixed-root JSON-lines session capabilities', async t => {
  const taskId = `AGENT-RESUME-M0-${randomUUID()}`;
  const originalHome = process.env.HOME;
  const fixture = createResumeFixture(taskId);
  process.env.HOME = fixture.home;
  t.after(() => {
    if (originalHome === undefined) delete process.env.HOME;
    else process.env.HOME = originalHome;
    rmSync(fixture.home, {recursive: true, force: true});
  });

  await t.test('single stdio session, real identities, full sync, clean close', async () => {
    const host = await startFakeHost();
    let session;
    try {
      session = await openAgentResumeSession({taskId, host: host.identity, app: fakeApp});
      assert.ok(session.generation >= fixture.generation);
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
      assert.ok((await session.reconcile()).album_count >= 100);
      const closed = await session.close();
      assert.equal(closed.closed, true);
      assert.equal(closed.exitCode, 0);
      await waitUntil(() => session.closed);
      await assert.rejects(session.reconcile(), error => error instanceof AgentResumeSessionError);
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
      session = await openAgentResumeSession({taskId, host: oldHost.identity, app: fakeApp});
      process.kill(session.controller.pid, 'SIGKILL');
      await waitUntil(() => session.closed);
      await assert.rejects(session.reconcile(), error => error instanceof AgentResumeSessionError);

      await assert.rejects(
        openAgentResumeSession({taskId, host: newHost.identity, app: fakeApp}),
        error => error.code === 'OLD_HOST_ALIVE',
      );

      await stopFakeHost(oldHost);
      const takeover = await openAgentResumeSession({taskId, host: newHost.identity, app: fakeApp});
      assert.ok((await takeover.reconcile()).album_count >= 100);
      const closed = await takeover.close();
      assert.equal(closed.closed, true);
      assert.equal(closed.exitCode, 0);
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
      first = await openAgentResumeSession({taskId, host: firstHost.identity, app: fakeApp});
      await assert.rejects(
        openAgentResumeSession({taskId, host: secondHost.identity, app: fakeApp}),
        error => error.code === 'WRITER_BUSY',
      );
      const closed = await first.close();
      assert.equal(closed.closed, true);
      assert.equal(closed.exitCode, 0);
    } finally {
      if (first && !first.closed) {
        try { await first.close(); } catch {}
      }
      await stopFakeHost(firstHost);
      await stopFakeHost(secondHost);
    }
  });
});

test('M1 wrapper intent calls remain single-shot and click-bounded', async t => {
  await t.test('non-positive timeouts are rejected before spawning the controller', async () => {
    const host = await startFakeHost();
    try {
      const taskId = `AGENT-RESUME-TIMEOUT-${randomUUID()}`;
      await assert.rejects(
        openAgentResumeSession({taskId, host: host.identity, app: fakeApp, clickTimeoutMs: 0}),
        error => error.code === 'CLICK_TIMEOUT_INVALID',
      );
      await assert.rejects(
        openAgentResumeSession({taskId, host: host.identity, app: fakeApp, requestTimeoutMs: -1}),
        error => error.code === 'REQUEST_TIMEOUT_INVALID',
      );
    } finally {
      await stopFakeHost(host);
    }
  });

  await t.test('save all and chooser each use the existing app exactly once', async t => {
    const taskId = `AGENT-RESUME-INTENT-${randomUUID()}`;
    const originalHome = process.env.HOME;
    const fixture = createResumeFixture(taskId);
    process.env.HOME = fixture.home;
    const host = await startFakeHost();
    const clicks = [];
    const app = {
      async click(point) {
        clicks.push({...point});
        return {clicked: true};
      },
    };
    let session;
    try {
      session = await openAgentResumeSession({taskId, host: host.identity, app});
      const album = firstNotStartedAlbum(session);
      const save = await session.saveAll({
        albumKey: album.album_key,
        grounding: saveAllGrounding(album.album_key),
        resultEvidenceSha256: 'c'.repeat(64),
      });
      assert.equal(save.outcome, 'RETURNED');
      assert.equal(save.clickAttempted, true);
      assert.equal(clicks.length, 1);

      const chooser = await session.confirmChooser({
        albumKey: album.album_key,
        grounding: chooserGrounding(album.album_key),
        resultEvidenceSha256: 'd'.repeat(64),
      });
      assert.equal(chooser.outcome, 'RETURNED');
      assert.equal(chooser.clickAttempted, true);
      assert.equal(clicks.length, 2);
      assert.notEqual(save.actionId, chooser.actionId);
      assert.deepEqual(clicks, [{x: 120, y: 240}, {x: 140, y: 260}]);

      await assert.rejects(
        session.saveAll({
          albumKey: album.album_key,
          grounding: saveAllGrounding(album.album_key),
          resultEvidenceSha256: 'e'.repeat(64),
        }),
        error => error.code === 'SAVE_ALL_INTENT_EXISTS',
      );
      assert.equal(clicks.length, 2);
      await waitUntil(() => session.closed);
    } finally {
      if (session && !session.closed) {
        try { await session.close(); } catch {}
      }
      await stopFakeHost(host);
      if (originalHome === undefined) delete process.env.HOME;
      else process.env.HOME = originalHome;
      rmSync(fixture.home, {recursive: true, force: true});
    }
  });

  await t.test('failed GUI click records UNKNOWN and survives into a fresh session without retry', async t => {
    const taskId = `AGENT-RESUME-UNKNOWN-${randomUUID()}`;
    const originalHome = process.env.HOME;
    const fixture = createResumeFixture(taskId);
    process.env.HOME = fixture.home;
    const firstHost = await startFakeHost();
    let firstSession;
    let secondSession;
    let firstClicks = 0;
    let secondClicks = 0;
    try {
      firstSession = await openAgentResumeSession({
        taskId,
        host: firstHost.identity,
        app: {
          async click() {
            firstClicks += 1;
            throw new Error('synthetic click failure');
          },
        },
      });
      const album = firstNotStartedAlbum(firstSession);
      const result = await firstSession.saveAll({
        albumKey: album.album_key,
        grounding: saveAllGrounding(album.album_key),
        resultEvidenceSha256: 'f'.repeat(64),
      });
      assert.equal(result.outcome, 'UNKNOWN');
      assert.equal(result.clickAttempted, true);
      assert.equal(firstClicks, 1);

      await assert.rejects(
        firstSession.saveAll({
          albumKey: album.album_key,
          grounding: saveAllGrounding(album.album_key),
          resultEvidenceSha256: '1'.repeat(64),
        }),
        error => error.code === 'SAVE_ALL_INTENT_EXISTS',
      );
      assert.equal(firstClicks, 1);
      await waitUntil(() => firstSession.closed);
      await stopFakeHost(firstHost);

      const secondHost = await startFakeHost();
      try {
        secondSession = await openAgentResumeSession({
          taskId,
          host: secondHost.identity,
          app: {
            async click() {
              secondClicks += 1;
              return {clicked: true};
            },
          },
        });
        const recoveredAlbum = secondSession.reconcileResult.albums.find(
          item => item.album_key === album.album_key,
        );
        assert.equal(recoveredAlbum.state, 'UNKNOWN');
        await assert.rejects(
          secondSession.saveAll({
            albumKey: album.album_key,
            grounding: saveAllGrounding(album.album_key),
            resultEvidenceSha256: '2'.repeat(64),
          }),
          error => error.code === 'SAVE_ALL_INTENT_EXISTS',
        );
        assert.equal(secondClicks, 0);
      } finally {
        if (secondSession && !secondSession.closed) {
          try { await secondSession.close(); } catch {}
        }
        await stopFakeHost(secondHost);
      }
    } finally {
      if (firstSession && !firstSession.closed) {
        try { await firstSession.close(); } catch {}
      }
      await stopFakeHost(firstHost);
      if (originalHome === undefined) delete process.env.HOME;
      else process.env.HOME = originalHome;
      rmSync(fixture.home, {recursive: true, force: true});
    }
  });
});
