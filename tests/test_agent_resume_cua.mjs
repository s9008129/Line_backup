import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn, spawnSync} from 'node:child_process';
import {once} from 'node:events';
import {randomUUID} from 'node:crypto';
import {mkdtempSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {
  AgentResumeSessionError,
  openAgentResumeSession,
  readBootIdentity,
  readProcessIdentity,
} from '../scripts/line_backup_agent_resume_cua.mjs';

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

function killIfAlive(pid) {
  try {
    process.kill(pid, 'SIGKILL');
  } catch {
    return;
  }
}

function createFakeController(directory, mode) {
  const path = join(directory, `fake-controller-${mode}.py`);
  writeFileSync(path, String.raw`
import hashlib
import json
import os
import sys

MODE = ${JSON.stringify(mode)}
args = sys.argv[1:]
task_id = args[args.index("--task") + 1]
root = args[args.index("--root") + 1]
CHECKPOINT = "a" * 64


def emit(value):
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    sys.stdout.flush()


if args and args[0] == "inspect":
    emit({
        "ok": True,
        "task_id": task_id,
        "generation": 0,
        "checkpoint_sha256": CHECKPOINT,
        "manifest_binding_sha256": "b" * 64,
        "album_count": 100,
        "gui_dispatches": 0,
    })
    raise SystemExit(0)

for raw in sys.stdin:
    request = json.loads(raw)
    operation = request["operation"]
    request_id = request["request_id"]
    response = {
        "ok": True,
        "version": 1,
        "request_id": request_id,
        "session_id": request["session_id"],
        "operation": operation,
    }
    if operation == "hello":
        response["result"] = {
            "generation": 0,
            "writer_lock": "held",
            "record_state": "ACTIVE",
            "checkpoint_sha256": CHECKPOINT,
            "root_sha256": hashlib.sha256(root.encode("utf-8")).hexdigest(),
            "boot_id": request["data"]["boot_id"],
            "session_id": request["session_id"],
            "controller": {"pid": os.getpid(), "started_at": "fake-controller-start"},
            "host": request["data"]["host"],
            "resume_state": {
                "task_id": task_id,
                "generation": 0,
                "checkpoint_sha256": CHECKPOINT,
                "manifest_binding_sha256": "b" * 64,
                "album_count": 100,
                "task_phase": "READY_TO_DISPATCH",
                "albums": [{
                    "album_key": "c" * 64,
                    "ordinal": 50,
                    "state": "NOT_STARTED",
                    "dispatchable": True,
                    "reason": None,
                    "inventory_count": 0,
                }],
                "counts": {"VERIFIED": 0, "NOT_STARTED": 100},
                "photo_count": 0,
                "first_blocker": None,
                "pending_input": False,
                "owner_action": None,
                "next_safe_album_key": "c" * 64,
                "next_safe_ordinal": 50,
                "next_safe_action": "PREPARE_SAVE_ALL:" + "c" * 64,
                "resume_metrics": {
                    "fast_resume_elapsed_ms": 0,
                    "verified_albums_skipped": 0,
                    "metadata_files_checked": 0,
                    "prior_verified_rehash_bytes": 0,
                    "prior_verified_decode_calls": 0,
                    "target_album_decode_calls": 0,
                },
                "gui_dispatches": 0,
            },
            "sync": {
                "file_fsync": True,
                "fullfsync": True,
                "directory_fsync": True,
                "readback": True,
            },
            "gui_observations": 0,
            "gui_dispatches": 0,
        }
        emit(response)
    elif operation == "reconcile":
        result = {"task_id": task_id, "generation": 0, "album_count": 100}
        if MODE == "malformed":
            sys.stdout.write("{not-json\n")
            sys.stdout.flush()
        elif MODE == "oversized":
            sys.stdout.write("x" * (1024 * 1024 + 1) + "\n")
            sys.stdout.flush()
        elif MODE == "binding":
            response["operation"] = "wrong-operation"
            response["result"] = result
            emit(response)
        elif MODE == "lost-ack":
            continue
        else:
            response["result"] = result
            emit(response)
            if MODE == "duplicate":
                emit(response)
    elif operation == "close":
        if MODE == "close-error":
            emit({"ok": False, "request_id": request_id, "error": {"code": "FAKE_CLOSE_FAILURE", "message": "close rejected"}})
            raise SystemExit(3)
        response["result"] = {"closed": True, "generation": 0}
        emit(response)
        raise SystemExit(0)
`, {encoding: 'utf8', mode: 0o700});
  return path;
}

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
history_base = dt.date(2023, 1, 1)
barriers = []
for index in range(49):
    day = history_base + dt.timedelta(days=index)
    barriers.append(resume._barrier(
        "fixture_history",
        source_sha,
        "fixture-group",
        {"start_date": day.isoformat(), "end_date": day.isoformat(), "expected_images": 1},
        [str(history_destination.resolve())],
        1,
        "SYNTHETIC_HISTORY_BARRIER",
        "fixture-history-%03d" % (index + 1),
    ))
store = resume._initial_store()
store["history"] = {"references": [reference], "barriers": barriers}
store["payload_sha256"] = resume._payload_digest(store)
resume._atomic_json_write(root / "checkpoint.json", store)

active_base = dt.date(2025, 1, 1)
albums = []
for index in range(100):
    ordinal = index + 1
    if ordinal <= 49:
        day = history_base + dt.timedelta(days=ordinal - 1)
    else:
        day = active_base + dt.timedelta(days=ordinal - 50)
    expected_images = 80 if ordinal == 50 else 1
    albums.append({
        "identity": {
            "group_key": "fixture-group",
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "expected_images": expected_images,
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

test('fake controller protocol failures are terminal and never gain GUI retry', async t => {
  const host = await startFakeHost();
  const directory = mkdtempSync(join(tmpdir(), 'agent-resume-protocol-'));
  t.after(async () => {
    await stopFakeHost(host);
    rmSync(directory, {recursive: true, force: true});
  });

  const rejectingModes = new Map([
    ['malformed', 'PROTOCOL_JSON_INVALID'],
    ['oversized', 'PROTOCOL_LINE_TOO_LARGE'],
    ['binding', 'PROTOCOL_BINDING_MISMATCH'],
    ['lost-ack', 'REQUEST_TIMEOUT'],
  ]);
  for (const [mode, expectedCode] of rejectingModes) {
    await t.test(`${mode} closes the wrapper`, async () => {
      let session;
      try {
        session = await openAgentResumeSession({
          taskId: `AGENT-RESUME-PROTOCOL-${mode}`,
          host: host.identity,
          app: fakeApp,
          scriptPath: createFakeController(directory, mode),
          requestTimeoutMs: 1_000,
          longOperationTimeoutMs: 1_000,
        });
        await assert.rejects(
          session.reconcile(),
          error => error instanceof AgentResumeSessionError && error.code === expectedCode,
        );
      } finally {
        if (session && !session.closed) {
          try { await session.close(); } catch {}
        }
      }
    });
  }

  await t.test('duplicate response is fatal even after the first acknowledgement', async () => {
    const session = await openAgentResumeSession({
      taskId: 'AGENT-RESUME-PROTOCOL-duplicate',
      host: host.identity,
      app: fakeApp,
      scriptPath: createFakeController(directory, 'duplicate'),
      requestTimeoutMs: 1_000,
      longOperationTimeoutMs: 1_000,
    });
    try {
      await session.reconcile();
      await waitUntil(() => session.closed);
      await assert.rejects(session.preflight(), error => error instanceof AgentResumeSessionError);
    } finally {
      killIfAlive(session.controller.pid);
    }
  });

  await t.test('close rejection is surfaced and leaves an unusable session', async () => {
    const session = await openAgentResumeSession({
      taskId: 'AGENT-RESUME-PROTOCOL-close-error',
      host: host.identity,
      app: fakeApp,
      scriptPath: createFakeController(directory, 'close-error'),
      requestTimeoutMs: 1_000,
      longOperationTimeoutMs: 1_000,
    });
    await assert.rejects(
      session.close(),
      error => error instanceof AgentResumeSessionError && error.code === 'FAKE_CLOSE_FAILURE',
    );
    killIfAlive(session.controller.pid);
    await assert.rejects(session.reconcile(), error => error instanceof AgentResumeSessionError);
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
      await assert.rejects(
        openAgentResumeSession({taskId, host: host.identity, app: fakeApp, longOperationTimeoutMs: 0}),
        error => error.code === 'LONG_OPERATION_TIMEOUT_INVALID',
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

  await t.test('successful click followed by result-record loss stays UNKNOWN with zero retry', async t => {
    const taskId = `AGENT-RESUME-RECORD-LOSS-${randomUUID()}`;
    const originalHome = process.env.HOME;
    const fixture = createResumeFixture(taskId);
    process.env.HOME = fixture.home;
    const firstHost = await startFakeHost();
    let firstSession;
    let secondSession;
    let secondClicks = 0;
    try {
      let clicked = false;
      firstSession = await openAgentResumeSession({
        taskId,
        host: firstHost.identity,
        app: {
          async click() {
            clicked = true;
            process.kill(firstSession.controller.pid, 'SIGKILL');
            return {clicked: true};
          },
        },
      });
      const album = firstNotStartedAlbum(firstSession);
      await assert.rejects(
        firstSession.saveAll({
          albumKey: album.album_key,
          grounding: saveAllGrounding(album.album_key),
          resultEvidenceSha256: '3'.repeat(64),
        }),
        error => error instanceof AgentResumeSessionError
          && error.code === 'INTENT_RESULT_RECORD_FAILED'
          && error.details.outcome === 'RETURNED',
      );
      assert.equal(clicked, true);
      await waitUntil(() => firstSession.closed);
      await stopFakeHost(firstHost);

      const root = join(fixture.home, 'Library', 'Application Support', 'LineBackup', 'agent-resume');
      const inspected = spawnSync('/usr/bin/python3', [
        join(process.cwd(), 'scripts', 'line_backup_agent_resume.py'),
        'inspect', '--root', root, '--task', taskId,
      ], {encoding: 'utf8', env: {...process.env, HOME: fixture.home}});
      assert.equal(inspected.status, 0, inspected.stderr);
      const inspectedTask = JSON.parse(inspected.stdout.trim());
      const durableAlbum = inspectedTask.albums.find(item => item.album_key === album.album_key);
      assert.equal(durableAlbum.state, 'UNKNOWN');
      assert.equal(durableAlbum.reason, 'SAVE_ALL_OUTCOME_UNKNOWN');

      const secondHost = await startFakeHost();
      try {
        await assert.rejects(
          openAgentResumeSession({
            taskId,
            host: secondHost.identity,
            app: {
              async click() {
                secondClicks += 1;
                return {clicked: true};
              },
            },
          }),
          error => error instanceof AgentResumeSessionError && error.code === 'PENDING_INPUT_UNRESOLVED',
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
