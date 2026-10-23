#!/usr/bin/env python3

from __future__ import annotations

import base64
import copy
import datetime as dt
import errno
import hashlib
import fcntl
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import line_backup_agent_resume as resume


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
GROUP_KEY = "fixture-group"

ATOMIC_KILL_WORKER = r"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
import line_backup_agent_resume as resume

target = Path(sys.argv[2])
value = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
hook_name = sys.argv[4]
resume._atomic_json_write(target, value, hooks={hook_name: lambda: os._exit(77)})
"""

PROCESS_RESUME_WORKER = r"""
import base64
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
import line_backup_agent_resume as resume

root = Path(sys.argv[2])
task_id = sys.argv[3]
action = sys.argv[4]
pid_log = Path(sys.argv[5])
decoder_helper = sys.argv[6]
session_id = "process-%d" % os.getpid()
png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
with pid_log.open("a", encoding="utf-8") as stream:
    stream.write("%d\n" % os.getpid())
    stream.flush()
    os.fsync(stream.fileno())


def grounding(task, album_key, chooser=False):
    common = {
        "app_identifier": task["scope"]["app_identifier"],
        "group_key": task["scope"]["group_key"],
        "album_key": album_key,
        "window_id": "fixture-window-%d" % os.getpid(),
        "foreground_authorization_reference": "OWNER_FIXTURE_FOREGROUND",
        "click_point": {"x": 120.0, "y": 240.0},
        "evidence_sha256": hashlib.sha256(
            ("%s:%s:%s" % (action, os.getpid(), album_key)).encode("utf-8")
        ).hexdigest(),
    }
    if chooser:
        return {**common, "chooser_identity": "fixture-chooser"}
    return {
        **common,
        "detail_identity": "fixture-detail",
        "menu_identity": "fixture-save-all-menu",
        "destination_empty": True,
    }


def dispatch_and_choose(store, task, album_key):
    generation = store["generation"]
    intent = resume.prepare_save_all(
        root,
        task_id,
        session_id,
        generation,
        album_key,
        grounding(task, album_key),
    )
    result = resume.record_save_all_result(
        root,
        task_id,
        session_id,
        intent["generation"],
        album_key,
        intent["action_id"],
        "RETURNED",
        hashlib.sha256(("save:%s" % album_key).encode("utf-8")).hexdigest(),
    )
    chooser = resume.prepare_chooser_confirm(
        root,
        task_id,
        session_id,
        result["generation"],
        album_key,
        grounding(task, album_key, chooser=True),
    )
    final = resume.record_chooser_result(
        root,
        task_id,
        session_id,
        chooser["generation"],
        album_key,
        chooser["action_id"],
        "RETURNED",
        hashlib.sha256(("chooser:%s" % album_key).encode("utf-8")).hexdigest(),
    )
    return final["generation"]


def write_expected_files(task, album_key):
    album = task["albums"][album_key]
    destination = resume._task_absolute_path(root, task_id, album["destination"])
    for index in range(int(album["identity"]["expected_images"])):
        (destination / ("%04d.png" % index)).write_bytes(png)


def state_snapshot(store):
    state = resume.derive_task_state(root, store, task_id, deep=False)
    return {
        "generation": state["generation"],
        "phase": state["task_phase"],
        "next_safe_ordinal": state["next_safe_ordinal"],
        "next_safe_action": state["next_safe_action"],
        "counts": state["counts"],
        "photo_count": state["photo_count"],
        "blocker": state["first_blocker"],
        "pending_input": state["pending_input"],
        "owner_action": state["owner_action"],
        "metrics": state["resume_metrics"],
    }


store = resume.read_store(root)
task = store["tasks"][task_id]
state = resume.derive_task_state(root, store, task_id, deep=False)
if action in ("inspect", "open-only"):
    print(json.dumps(state_snapshot(store), sort_keys=True), flush=True)
elif action == "open-only-kill":
    print(json.dumps(state_snapshot(store), sort_keys=True), flush=True)
    os._exit(77)
elif action == "intent-only-kill":
    album_key = state["next_safe_album_key"]
    intent = resume.prepare_save_all(
        root,
        task_id,
        session_id,
        store["generation"],
        album_key,
        grounding(task, album_key),
    )
    print(json.dumps({"album_key": album_key, "action_id": intent["action_id"]}), flush=True)
    os._exit(77)
elif action == "save-returned-kill":
    album_key = state["next_safe_album_key"]
    intent = resume.prepare_save_all(
        root,
        task_id,
        session_id,
        store["generation"],
        album_key,
        grounding(task, album_key),
    )
    result = resume.record_save_all_result(
        root,
        task_id,
        session_id,
        intent["generation"],
        album_key,
        intent["action_id"],
        "RETURNED",
        hashlib.sha256(("save:%s" % album_key).encode("utf-8")).hexdigest(),
    )
    print(json.dumps({"album_key": album_key, "generation": result["generation"]}), flush=True)
    os._exit(77)
elif action == "chooser-click-files-kill":
    album_key = state["next_safe_album_key"]
    intent = resume.prepare_save_all(
        root,
        task_id,
        session_id,
        store["generation"],
        album_key,
        grounding(task, album_key),
    )
    result = resume.record_save_all_result(
        root,
        task_id,
        session_id,
        intent["generation"],
        album_key,
        intent["action_id"],
        "RETURNED",
        hashlib.sha256(("save:%s" % album_key).encode("utf-8")).hexdigest(),
    )
    chooser = resume.prepare_chooser_confirm(
        root,
        task_id,
        session_id,
        result["generation"],
        album_key,
        grounding(task, album_key, chooser=True),
    )
    write_expected_files(task, album_key)
    print(json.dumps({
        "album_key": album_key,
        "chooser_action_id": chooser["action_id"],
        "generation": chooser["generation"],
    }), flush=True)
    os._exit(77)
elif action == "dispatch-files-kill":
    album_key = state["next_safe_album_key"]
    dispatch_and_choose(store, task, album_key)
    write_expected_files(task, album_key)
    print(json.dumps({"album_key": album_key, "ordinal": state["next_safe_ordinal"]}), flush=True)
    os._exit(77)
elif action in ("verify-real", "verify-fake"):
    album_key = next(item["album_key"] for item in state["albums"] if item["state"] == "VERIFYING")
    resume._compile_decoder = lambda _directory: Path(decoder_helper)
    result = resume.verify_album(
        root,
        task_id,
        session_id,
        store["generation"],
        album_key,
        interval_seconds=0,
        timeout_seconds=10,
        sleep_fn=lambda _seconds: None,
    )
    print(json.dumps(result, sort_keys=True), flush=True)
elif action == "dispatch-verify-fake":
    album_key = state["next_safe_album_key"]
    if album_key is None:
        raise SystemExit("no dispatchable album")
    dispatch_and_choose(store, task, album_key)
    write_expected_files(task, album_key)
    refreshed = resume.read_store(root)
    resume._compile_decoder = lambda _directory: Path(decoder_helper)
    result = resume.verify_album(
        root,
        task_id,
        session_id,
        refreshed["generation"],
        album_key,
        interval_seconds=0,
        timeout_seconds=10,
        sleep_fn=lambda _seconds: None,
    )
    print(json.dumps(result, sort_keys=True), flush=True)
else:
    raise SystemExit("unknown action")
"""


def write_json(path: Path, value: object) -> None:
    Path(path).write_bytes(resume.canonical_json(value) + b"\n")


def create_fake_decoder(directory: Path) -> Path:
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    decoder = directory / "fake_image_decode"
    decoder.write_text(
        "#!/usr/bin/env python3\n"
        "import hashlib\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "root = Path(sys.argv[1])\n"
        "expected = int(sys.argv[2])\n"
        "names = sorted(entry.name for entry in root.iterdir())\n"
        "entries = []\n"
        "for name in names:\n"
        "    raw = (root / name).read_bytes()\n"
        "    entries.append({\n"
        "        'name': name, 'decoded': True, 'width': 1, 'height': 1,\n"
        "        'contentType': 'public.png',\n"
        "        'sha256': hashlib.sha256(raw).hexdigest(),\n"
        "    })\n"
        "passed = len(entries) == expected and all(item['decoded'] for item in entries)\n"
        "print(json.dumps({\n"
        "    'verdict': 'PASS' if passed else 'FAIL', 'expected': expected,\n"
        "    'actualEntries': len(entries), 'destination': str(root), 'entries': entries,\n"
        "}, sort_keys=True))\n"
        "raise SystemExit(0 if passed else 1)\n",
        encoding="utf-8",
    )
    decoder.chmod(0o700)
    return decoder


def run_worker(code: str, arguments: list[str], *, timeout: float = 60.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "-c", code, *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


def send_session_request(process: subprocess.Popen[str], payload: dict) -> dict:
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
    process.stdin.flush()
    line = process.stdout.readline()
    if not line:
        code = process.wait(timeout=5)
        stderr = process.stderr.read() if process.stderr is not None else ""
        raise AssertionError("session controller exited without a response: %s %s" % (code, stderr))
    return json.loads(line)


def seed_history_store(root: Path, count: int = 49) -> dict:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    source = root / "fixture-history.json"
    write_json(source, {"fixture": "synthetic-history", "barriers": count})
    source_raw = source.read_bytes()
    destination = root / "fixture-history-destination"
    destination.mkdir(mode=0o700, exist_ok=True)
    os.chmod(destination, 0o700)
    (destination / "history.png").write_bytes(PNG_1X1)
    reference = {
        "source_kind": "fixture_history",
        "path": str(source.resolve()),
        "sha256": hashlib.sha256(source_raw).hexdigest(),
        "bytes": len(source_raw),
        "imported_at_utc": resume.utc_now(),
    }
    base = dt.date(2023, 1, 1)
    barriers = []
    for index in range(count):
        day = base + dt.timedelta(days=index)
        barriers.append(
            resume._barrier(
                "fixture_history",
                reference["sha256"],
                GROUP_KEY,
                {
                    "start_date": day.isoformat(),
                    "end_date": day.isoformat(),
                    "expected_images": 1,
                },
                [str(destination.resolve())],
                1,
                "SYNTHETIC_HISTORY_BARRIER",
                "history-%03d" % (index + 1),
            )
        )
    store = resume._initial_store()
    store["history"] = {"references": [reference], "barriers": barriers}
    store["payload_sha256"] = resume._payload_digest(store)
    resume._atomic_json_write(root / "checkpoint.json", store)
    return store


def build_manifest(task_id: str, *, date_offset_days: int = 0) -> dict:
    history_base = dt.date(2023, 1, 1)
    active_base = dt.date(2025, 1, 1) + dt.timedelta(days=date_offset_days)
    albums = []
    for ordinal in range(1, 101):
        day = history_base + dt.timedelta(days=ordinal - 1) if ordinal <= 49 else active_base + dt.timedelta(days=ordinal - 50)
        expected = 80 if ordinal == 50 else 1
        albums.append(
            {
                "identity": {
                    "group_key": GROUP_KEY,
                    "start_date": day.isoformat(),
                    "end_date": day.isoformat(),
                    "expected_images": expected,
                    "observed_title": "album-%03d" % ordinal,
                    "disambiguator": "owner:%03d" % ordinal,
                },
                "destination": "downloads/album-%03d" % ordinal,
            }
        )
    return {
        "schema_version": 1,
        "task_id": task_id,
        "scope": {
            "group_key": GROUP_KEY,
            "app_identifier": "com.example.line-fixture",
            "owner_id": "fixture-owner",
            "scope_id": "fixture-scope",
        },
        "owner_authorization_reference": "OWNER_FIXTURE_ONLY",
        "exclusions": [],
        "albums": albums,
    }


def create_runtime_fixture(root: Path, task_id: str, *, date_offset_days: int = 0) -> dict:
    checkpoint = root / "checkpoint.json"
    if checkpoint.exists():
        store = resume.read_store(root)
        if not store["history"]["barriers"]:
            seed_history_store(root)
    else:
        seed_history_store(root)
    manifest_path = root.parent / ("%s-manifest.json" % task_id)
    manifest = build_manifest(task_id, date_offset_days=date_offset_days)
    write_json(manifest_path, manifest)
    result = resume.create_task(root, manifest_path)
    lock = root / ".session.lock"
    if lock.exists():
        lock.unlink()
    return {"root": root, "task_id": task_id, "manifest": manifest, "result": result}


def build_custom_manifest(
    task_id: str,
    prefix_albums: list[dict],
    *,
    active_count: int = 96,
    active_date_offset_days: int = 0,
) -> dict:
    albums = list(prefix_albums)
    active_base = dt.date(2026, 1, 1) + dt.timedelta(days=active_date_offset_days)
    for index in range(active_count):
        ordinal = len(albums) + 1
        day = active_base + dt.timedelta(days=index)
        albums.append(
            {
                "identity": {
                    "group_key": GROUP_KEY,
                    "start_date": day.isoformat(),
                    "end_date": day.isoformat(),
                    "expected_images": 1,
                    "observed_title": "active-%03d" % ordinal,
                    "disambiguator": "fixture:%03d" % ordinal,
                },
                "destination": "downloads/active-%03d" % ordinal,
            }
        )
    return {
        "schema_version": 1,
        "task_id": task_id,
        "scope": {
            "group_key": GROUP_KEY,
            "app_identifier": "com.example.line-fixture",
            "owner_id": "fixture-owner",
            "scope_id": "fixture-scope",
        },
        "owner_authorization_reference": "OWNER_FIXTURE_ONLY",
        "exclusions": [],
        "albums": albums,
    }


def create_custom_runtime_fixture(
    root: Path,
    task_id: str,
    prefix_albums: list[dict],
    *,
    active_count: int = 96,
    active_date_offset_days: int = 0,
    history_count: int = 1,
) -> dict:
    checkpoint = root / "checkpoint.json"
    if not checkpoint.exists():
        seed_history_store(root, count=history_count)
    manifest_path = root.parent / ("%s-manifest.json" % task_id)
    manifest = build_custom_manifest(
        task_id,
        prefix_albums,
        active_count=active_count,
        active_date_offset_days=active_date_offset_days,
    )
    write_json(manifest_path, manifest)
    result = resume.create_task(root, manifest_path)
    lock = root / ".session.lock"
    if lock.exists():
        lock.unlink()
    return {"root": root, "task_id": task_id, "manifest": manifest, "result": result}


def create_active_runtime_fixture(
    root: Path,
    task_id: str,
    count: int,
    *,
    active_date_offset_days: int = 0,
    expected_images_by_ordinal: dict[int, int] | None = None,
) -> dict:
    if not (root / "checkpoint.json").exists():
        seed_history_store(root, count=1)
    manifest = build_custom_manifest(
        task_id,
        [],
        active_count=count,
        active_date_offset_days=active_date_offset_days,
    )
    for ordinal, expected_images in (expected_images_by_ordinal or {}).items():
        manifest["albums"][ordinal - 1]["identity"]["expected_images"] = expected_images
    manifest_path = root.parent / ("%s-manifest.json" % task_id)
    write_json(manifest_path, manifest)
    result = resume.create_task(root, manifest_path)
    lock = root / ".session.lock"
    if lock.exists():
        lock.unlink()
    return {"root": root, "task_id": task_id, "manifest": manifest, "result": result}


def verify_prefix_for_fast_resume(root: Path, task_id: str, count: int) -> int:
    session_id = "fast-resume-prefix"
    with mock.patch.object(resume, "_decode_inventory", side_effect=fake_decode_from_inventory) as decode:
        for ordinal in range(1, count + 1):
            store = resume.read_store(root)
            task = store["tasks"][task_id]
            state = resume.derive_task_state(root, store, task_id, deep=False)
            if state["next_safe_ordinal"] != ordinal:
                raise AssertionError("fast resume expected ordinal %d, got %r" % (ordinal, state["next_safe_ordinal"]))
            album_key = task["album_order"][ordinal - 1]
            album = task["albums"][album_key]
            generation, _, _ = dispatch_and_choose(
                root,
                task_id,
                session_id,
                store["generation"],
                album_key,
                task,
            )
            destination = resume._task_absolute_path(root, task_id, album["destination"])
            write_png_count(destination, int(album["identity"]["expected_images"]))
            verified = resume.verify_album(
                root,
                task_id,
                session_id,
                generation,
                album_key,
                interval_seconds=0,
                timeout_seconds=1,
                sleep_fn=lambda _seconds: None,
            )
            if verified["state"] != "VERIFIED":
                raise AssertionError("fast resume prefix album was not verified")
    return decode.call_count


def task_and_album(root: Path, task_id: str, ordinal: int) -> tuple[dict, dict]:
    store = resume.read_store(root)
    task = store["tasks"][task_id]
    return store, task["albums"][task["album_order"][ordinal - 1]]


def make_grounding(task: dict, album_key: str, *, chooser: bool = False) -> dict:
    common = {
        "app_identifier": task["scope"]["app_identifier"],
        "group_key": task["scope"]["group_key"],
        "album_key": album_key,
        "window_id": "fixture-window",
        "foreground_authorization_reference": "OWNER_FIXTURE_FOREGROUND",
        "click_point": {"x": 120.0, "y": 240.0},
        "evidence_sha256": hashlib.sha256(("evidence:%s" % album_key).encode("utf-8")).hexdigest(),
    }
    if chooser:
        return {**common, "chooser_identity": "fixture-chooser"}
    return {
        **common,
        "detail_identity": "fixture-detail",
        "menu_identity": "fixture-save-all-menu",
        "destination_empty": True,
    }


def dispatch_and_choose(
    root: Path,
    task_id: str,
    session_id: str,
    generation: int,
    album_key: str,
    task: dict,
) -> tuple[int, dict, dict]:
    evidence = hashlib.sha256(("result:%s" % album_key).encode("utf-8")).hexdigest()
    save_intent = resume.prepare_save_all(
        root,
        task_id,
        session_id,
        generation,
        album_key,
        make_grounding(task, album_key),
    )
    save_result = resume.record_save_all_result(
        root,
        task_id,
        session_id,
        save_intent["generation"],
        album_key,
        save_intent["action_id"],
        "RETURNED",
        evidence,
    )
    chooser_intent = resume.prepare_chooser_confirm(
        root,
        task_id,
        session_id,
        save_result["generation"],
        album_key,
        make_grounding(task, album_key, chooser=True),
    )
    chooser_result = resume.record_chooser_result(
        root,
        task_id,
        session_id,
        chooser_intent["generation"],
        album_key,
        chooser_intent["action_id"],
        "RETURNED",
        evidence,
    )
    return chooser_result["generation"], save_intent, chooser_intent


def write_png_count(destination: Path, count: int) -> None:
    for index in range(count):
        (destination / ("%04d.png" % index)).write_bytes(PNG_1X1)


def fake_decode_from_inventory(path: Path, expected: int, *, decoder_binary: Path | None = None):
    inventory = resume._inventory_directory(path, max_entries=max(resume.MAX_EXPECTED_IMAGES, expected + 1))
    if inventory["count"] != expected:
        raise AssertionError("fixture decoder count mismatch")
    decoded = {
        entry["name"]: {
            "decoded": True,
            "width": 1,
            "height": 1,
            "content_type": "public.png",
            "sha256": entry["sha256"],
        }
        for entry in inventory["entries"]
    }
    return decoded, "d" * 64


def home_temporary_directory() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="line-backup-agent-resume-test-", dir=Path.home())


def write_lock_record(root: Path, record: dict) -> None:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    lock = root / ".session.lock"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, resume.canonical_json(record) + b"\n")
        os.fsync(fd)
        fcntl.fcntl(fd, fcntl.F_FULLFSYNC, 0)
    finally:
        os.close(fd)


class StrictJsonTests(unittest.TestCase):
    def test_duplicate_key_is_rejected(self) -> None:
        with self.assertRaises(resume.InputError) as caught:
            resume.strict_json_loads(b'{"a":1,"a":2}')
        self.assertEqual(caught.exception.code, "DUPLICATE_JSON_KEY")

    def test_non_finite_number_is_rejected(self) -> None:
        with self.assertRaises(resume.InputError) as caught:
            resume.strict_json_loads(b'{"value":NaN}')
        self.assertEqual(caught.exception.code, "NON_FINITE_JSON")

    def test_nul_and_size_are_rejected(self) -> None:
        with self.assertRaises(resume.InputError):
            resume.strict_json_loads(b'{"a":1}\x00')
        with self.assertRaises(resume.InputError):
            resume.strict_json_loads(b" " * (resume.MAX_LINE_BYTES + 1))


class IdentityAndSyncTests(unittest.TestCase):
    def test_real_process_and_boot_identity(self) -> None:
        observed = resume.current_process_identity()
        self.assertEqual(observed["pid"], os.getpid())
        self.assertTrue(observed["started_at"])
        self.assertEqual(resume.process_identity(os.getpid()), observed)
        self.assertTrue(resume.boot_identity())
        self.assertIsNone(resume.process_identity(999_999_999))

    def test_sync_probe_uses_real_primitives_and_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            result = resume.sync_probe(root)
            self.assertTrue(result["file_fsync"])
            self.assertTrue(result["fullfsync"])
            self.assertTrue(result["directory_fsync"])
            self.assertTrue(result["readback"])
            self.assertRegex(result["probe_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(list(root.glob(".sync-probe-*")), [])
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)

    def test_pinned_swift_sources_are_byte_identical(self) -> None:
        expected = {
            "image_decode.swift": "238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b",
            "modern_ocr.swift": "19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861",
        }
        for name, digest in expected.items():
            actual = hashlib.sha256((REPO_ROOT / "scripts" / "agent_resume" / name).read_bytes()).hexdigest()
            self.assertEqual(actual, digest)


class AtomicWriteFaultTests(unittest.TestCase):
    HOOKS = (
        "before_write",
        "after_write",
        "after_file_sync",
        "before_replace",
        "after_replace",
        "after_directory_sync",
        "after_readback",
    )
    PRE_REPLACE_HOOKS = set(HOOKS[:4])

    @staticmethod
    def _store(generation: int) -> dict:
        value = resume._initial_store()
        value["generation"] = generation
        value["payload_sha256"] = resume._payload_digest(value)
        return value

    def test_process_interruption_at_every_atomic_boundary_keeps_one_valid_revision(self) -> None:
        for hook_name in self.HOOKS:
            with self.subTest(hook=hook_name), home_temporary_directory() as temporary:
                root = Path(temporary).resolve() / "agent-resume"
                root.mkdir(mode=0o700)
                checkpoint = root / "checkpoint.json"
                resume._atomic_json_write(checkpoint, self._store(0))
                replacement_path = root.parent / ("replacement-%s.json" % hook_name)
                write_json(replacement_path, self._store(1))

                completed = run_worker(
                    ATOMIC_KILL_WORKER,
                    [str(REPO_ROOT / "scripts"), str(checkpoint), str(replacement_path), hook_name],
                )
                self.assertEqual(completed.returncode, 77, completed.stderr)

                observed = resume.read_store(root)
                expected_generation = 0 if hook_name in self.PRE_REPLACE_HOOKS else 1
                self.assertEqual(observed["generation"], expected_generation)
                self.assertEqual(observed["payload_sha256"], resume._payload_digest(observed))
                temp_files = list(root.glob(".checkpoint.json.tmp.*"))
                self.assertEqual(len(temp_files), 1 if hook_name in self.PRE_REPLACE_HOOKS else 0)

    def test_enospc_fsync_replace_and_readback_failures_are_explicit(self) -> None:
        cases = (
            ("ENOSPC", mock.patch.object(resume, "_write_all", side_effect=OSError(errno.ENOSPC, "full")), "ATOMIC_WRITE_FAILED", 0),
            ("file-fsync", mock.patch.object(resume, "_full_sync", side_effect=OSError(errno.EIO, "fsync")), "ATOMIC_WRITE_FAILED", 0),
            ("replace", mock.patch.object(resume.os, "replace", side_effect=OSError(errno.EIO, "replace")), "ATOMIC_WRITE_FAILED", 0),
            ("directory-fsync", mock.patch.object(resume, "_directory_sync", side_effect=OSError(errno.EIO, "dir")), "ATOMIC_WRITE_FAILED", 1),
            ("readback", mock.patch.object(resume, "_read_regular_bytes", return_value=b"wrong\n"), "ATOMIC_READBACK_MISMATCH", 1),
        )
        for name, patcher, expected_code, expected_generation in cases:
            with self.subTest(case=name), home_temporary_directory() as temporary:
                root = Path(temporary).resolve() / "agent-resume"
                root.mkdir(mode=0o700)
                checkpoint = root / "checkpoint.json"
                resume._atomic_json_write(checkpoint, self._store(0))
                with patcher:
                    with self.assertRaises(resume.StorageRuntimeError) as caught:
                        resume._atomic_json_write(checkpoint, self._store(1))
                self.assertEqual(caught.exception.code, expected_code)
                observed = resume.read_store(root)
                self.assertEqual(observed["generation"], expected_generation)
                self.assertEqual(observed["payload_sha256"], resume._payload_digest(observed))

    def test_failed_intent_write_never_returns_click_eligibility(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-ENOSPC-INTENT"
            create_runtime_fixture(root, task_id)
            store, album = task_and_album(root, task_id, 50)
            task = store["tasks"][task_id]
            original = (root / "checkpoint.json").read_bytes()
            with mock.patch.object(resume, "_full_sync", side_effect=OSError(errno.ENOSPC, "full")):
                with self.assertRaises(resume.StorageRuntimeError) as caught:
                    resume.prepare_save_all(
                        root,
                        task_id,
                        "failed-intent-session",
                        store["generation"],
                        album["album_key"],
                        make_grounding(task, album["album_key"]),
                    )
            self.assertEqual(caught.exception.code, "ATOMIC_WRITE_FAILED")
            self.assertEqual((root / "checkpoint.json").read_bytes(), original)
            state = resume.derive_task_state(root, resume.read_store(root), task_id, deep=False)
            self.assertEqual(state["next_safe_ordinal"], 50)

            with mock.patch.object(resume, "_directory_sync", side_effect=OSError(errno.EIO, "dir")):
                with self.assertRaises(resume.StorageRuntimeError) as caught:
                    resume.prepare_save_all(
                        root,
                        task_id,
                        "uncertain-intent-session",
                        store["generation"],
                        album["album_key"],
                        make_grounding(task, album["album_key"]),
                    )
            self.assertEqual(caught.exception.code, "ATOMIC_WRITE_FAILED")
            recovered = resume.read_store(root)
            recovered_album = recovered["tasks"][task_id]["albums"][album["album_key"]]
            self.assertIsNotNone(recovered_album["save_all_intent"])
            recovered_state = resume.derive_task_state(root, recovered, task_id, deep=False)
            self.assertEqual(recovered_state["first_blocker"]["reason"], "SAVE_ALL_OUTCOME_UNKNOWN")


class DecoderFaultTests(unittest.TestCase):
    def _input(self, directory: Path) -> tuple[Path, Path]:
        destination = directory / "downloads"
        destination.mkdir(mode=0o700)
        (destination / "0001.png").write_bytes(PNG_1X1)
        decoder = directory / "decoder-binary"
        decoder.write_bytes(b"fixture decoder")
        decoder.chmod(0o700)
        return destination, decoder

    def test_decoder_timeout_is_distinct_and_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination, decoder = self._input(Path(temporary))
            with mock.patch.object(resume, "_validate_decoder_source"):
                with mock.patch.object(
                    resume.subprocess,
                    "run",
                    side_effect=subprocess.TimeoutExpired(cmd=[str(decoder)], timeout=60),
                ):
                    with self.assertRaises(resume.StorageRuntimeError) as caught:
                        resume._decode_inventory(destination, 1, decoder_binary=decoder)
            self.assertEqual(caught.exception.code, "IMAGE_DECODER_TIMEOUT")
            self.assertEqual((destination / "0001.png").read_bytes(), PNG_1X1)

    def test_decoder_malformed_duplicate_and_oversized_output_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination, decoder = self._input(Path(temporary))
            completed = subprocess.CompletedProcess(args=[str(decoder)], returncode=0, stdout=b'{}', stderr=b"")
            with mock.patch.object(resume, "_validate_decoder_source"):
                for name, stdout in (
                    ("malformed", b'{"verdict":'),
                    ("duplicate", b'{"verdict":"PASS","verdict":"FAIL"}'),
                ):
                    with self.subTest(case=name), mock.patch.object(
                        resume.subprocess,
                        "run",
                        return_value=subprocess.CompletedProcess(args=completed.args, returncode=0, stdout=stdout, stderr=b""),
                    ):
                        with self.assertRaises(resume.SafetyBlock) as caught:
                            resume._decode_inventory(destination, 1, decoder_binary=decoder)
                    self.assertEqual(caught.exception.code, "IMAGE_DECODER_OUTPUT_INVALID")
                with mock.patch.object(resume, "MAX_DECODER_OUTPUT_BYTES", 64):
                    with mock.patch.object(
                        resume.subprocess,
                        "run",
                        return_value=subprocess.CompletedProcess(args=completed.args, returncode=0, stdout=b" " * 65, stderr=b""),
                    ):
                        with self.assertRaises(resume.SafetyBlock) as caught:
                            resume._decode_inventory(destination, 1, decoder_binary=decoder)
            self.assertEqual(caught.exception.code, "IMAGE_DECODER_OUTPUT_INVALID")


class MacImageDecoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory(prefix="line-backup-imageio-test-")
        cls.decoder = resume._compile_decoder(Path(cls._temporary.name))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def test_pinned_imageio_decodes_valid_png_and_rejects_truncated_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            valid = base / "valid"
            valid.mkdir(mode=0o700)
            (valid / "0001.png").write_bytes(PNG_1X1)
            decoded, binary_sha256 = resume._decode_inventory(valid, 1, decoder_binary=self.decoder)
            self.assertEqual(decoded["0001.png"]["width"], 1)
            self.assertEqual(decoded["0001.png"]["height"], 1)
            self.assertRegex(binary_sha256, r"^[0-9a-f]{64}$")

            truncated = base / "truncated"
            truncated.mkdir(mode=0o700)
            truncated_bytes = PNG_1X1[:20]
            (truncated / "0001.png").write_bytes(truncated_bytes)
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume._decode_inventory(truncated, 1, decoder_binary=self.decoder)
            self.assertIn(caught.exception.code, {"IMAGE_DECODE_REJECTED", "IMAGE_DECODE_COUNT_MISMATCH"})
            self.assertEqual((truncated / "0001.png").read_bytes(), truncated_bytes)

    def test_real_imageio_decode_then_destination_change_is_not_verified(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-IMAGEIO-POST-DECODE"
            create_runtime_fixture(root, task_id)
            store, album = task_and_album(root, task_id, 50)
            generation, _, _ = dispatch_and_choose(
                root,
                task_id,
                "imageio-post-decode",
                store["generation"],
                album["album_key"],
                store["tasks"][task_id],
            )
            destination = resume._task_absolute_path(root, task_id, album["destination"])
            write_png_count(destination, 80)
            real_decode = resume._decode_inventory
            decoder = self.decoder

            def decode_then_change(path: Path, expected: int, *, decoder_binary: Path | None = None):
                result = real_decode(path, expected, decoder_binary=decoder)
                target = path / "0000.png"
                target.write_bytes(target.read_bytes() + b"changed-after-decode")
                return result

            with mock.patch.object(resume, "_decode_inventory", side_effect=decode_then_change):
                with self.assertRaises(resume.SafetyBlock) as caught:
                    resume.verify_album(
                        root,
                        task_id,
                        "imageio-post-decode",
                        generation,
                        album["album_key"],
                        interval_seconds=0,
                        timeout_seconds=1,
                        sleep_fn=lambda _seconds: None,
                    )
            self.assertEqual(caught.exception.code, "DESTINATION_CHANGED")
            current = resume.read_store(root)
            self.assertIsNone(current["tasks"][task_id]["albums"][album["album_key"]]["verification"])


class DestinationSafetyTests(unittest.TestCase):
    def test_partial_zero_symlink_and_non_directory_entries_fail_closed(self) -> None:
        cases = []

        def partial(path: Path) -> None:
            (path / "0001.png.part").write_bytes(PNG_1X1)

        def zero(path: Path) -> None:
            (path / "0001.png").write_bytes(b"")

        def symlink(path: Path) -> None:
            target = path.parent / "outside.png"
            target.write_bytes(PNG_1X1)
            (path / "0001.png").symlink_to(target)

        def directory(path: Path) -> None:
            (path / "nested").mkdir()

        cases.extend(
            (
                ("partial", partial, "PARTIAL_FILE_PRESENT"),
                ("zero", zero, "ZERO_BYTE_FILE"),
                ("symlink", symlink, "DESTINATION_INVALID"),
                ("directory", directory, "DESTINATION_INVALID"),
            )
        )
        for name, populate, expected_code in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                destination = Path(temporary) / "downloads"
                destination.mkdir(mode=0o700)
                populate(destination)
                with self.assertRaises(resume.SafetyBlock) as caught:
                    resume._inventory_directory(destination)
                self.assertEqual(caught.exception.code, expected_code)

    def test_traversal_destination_is_rejected_before_any_task_directory(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            seed_history_store(root)
            manifest = build_custom_manifest("AGENT-RESUME-TEST-TRAVERSAL", [], active_count=100)
            manifest["albums"][0]["destination"] = "../../escape"
            manifest_path = root.parent / "traversal.json"
            write_json(manifest_path, manifest)
            with self.assertRaises(resume.InputError) as caught:
                resume.create_task(root, manifest_path)
            self.assertEqual(caught.exception.code, "DESTINATION_INVALID")
            self.assertFalse((root / "tasks" / "AGENT-RESUME-TEST-TRAVERSAL").exists())

    def test_extra_file_after_returned_chooser_blocks_without_redownload(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-EXTRA-AFTER-INTENT"
            create_runtime_fixture(root, task_id)
            store, album = task_and_album(root, task_id, 50)
            generation, _, _ = dispatch_and_choose(
                root,
                task_id,
                "extra-after-intent",
                store["generation"],
                album["album_key"],
                store["tasks"][task_id],
            )
            destination = resume._task_absolute_path(root, task_id, album["destination"])
            write_png_count(destination, 81)
            before = {path.name: path.read_bytes() for path in destination.iterdir()}
            state = resume.derive_task_state(root, resume.read_store(root), task_id, deep=False)
            self.assertEqual(state["first_blocker"]["reason"], "UNEXPECTED_EXTRA_FILES")
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.verify_album(
                    root,
                    task_id,
                    "extra-after-intent",
                    generation,
                    album["album_key"],
                    interval_seconds=0,
                    timeout_seconds=1,
                    sleep_fn=lambda _: None,
                )
            self.assertIn(caught.exception.code, {"TASK_BLOCKED", "UNEXPECTED_EXTRA_FILES"})
            self.assertEqual({path.name: path.read_bytes() for path in destination.iterdir()}, before)


class ResumeCoreTests(unittest.TestCase):
    @staticmethod
    def _compile_decoder_in(directory: Path) -> Path:
        decoder_directory = directory / "decoder"
        decoder_directory.mkdir(mode=0o700)
        return resume._compile_decoder(decoder_directory)

    def test_ordered_manifest_resumes_at_50_and_read_only_views_do_not_mutate(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-READONLY"
            create_runtime_fixture(root, task_id)
            before = (root / "checkpoint.json").read_bytes()

            first = resume.inspect_task(root, task_id)
            second = resume.inspect_task(root, task_id)
            with mock.patch.object(resume, "_compile_decoder", return_value=Path("/unused-fixture-decoder")):
                reconciled = resume.reconcile_task(root, task_id)

            first_stable = copy.deepcopy(first)
            second_stable = copy.deepcopy(second)
            first_stable["resume_metrics"]["fast_resume_elapsed_ms"] = 0
            second_stable["resume_metrics"]["fast_resume_elapsed_ms"] = 0
            self.assertEqual(first_stable, second_stable)
            self.assertEqual(reconciled["generation"], first["generation"])
            self.assertEqual(first["album_count"], 100)
            self.assertEqual(first["next_safe_ordinal"], 50)
            self.assertEqual(first["counts"]["SKIPPED_EXISTING"], 49)
            self.assertEqual(first["counts"]["NOT_STARTED"], 51)
            self.assertEqual(first["gui_dispatches"], 0)
            self.assertEqual((root / "checkpoint.json").read_bytes(), before)

    def test_deep_state_compiles_decoder_only_when_a_verified_binding_is_present(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-LAZY-DECODER"
            create_runtime_fixture(root, task_id)
            store = resume.read_store(root)
            with mock.patch.object(
                resume,
                "_compile_decoder",
                side_effect=AssertionError("decoder must stay lazy before any verification exists"),
            ):
                state = resume.derive_task_state(root, store, task_id, deep=True)
            self.assertEqual(state["next_safe_ordinal"], 50)
            self.assertEqual(state["counts"]["SKIPPED_EXISTING"], 49)

    def test_small_owner_authorized_manifests_and_empty_manifest_rejection(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            for index, count in enumerate((1, 2, 5, 10)):
                task_id = "AGENT-RESUME-TEST-SMALL-%02d" % count
                fixture = create_active_runtime_fixture(
                    root,
                    task_id,
                    count,
                    active_date_offset_days=index * 20,
                )
                self.assertEqual(fixture["result"]["album_count"], count)
                inspected = resume.inspect_task(root, task_id)
                self.assertEqual(inspected["album_count"], count)
                self.assertEqual(inspected["next_safe_ordinal"], 1)
                self.assertEqual(inspected["task_phase"], "READY_TO_DISPATCH")

            empty_manifest = build_custom_manifest("AGENT-RESUME-TEST-EMPTY", [], active_count=0)
            empty_path = root.parent / "empty-manifest.json"
            write_json(empty_path, empty_manifest)
            with self.assertRaises(resume.InputError) as caught:
                resume.create_task(root, empty_path)
            self.assertEqual(caught.exception.code, "TASK_MANIFEST_EMPTY")

    def test_maximum_manifest_fits_cua_hello_line_and_one_over_is_rejected(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-MAX-PAYLOAD"
            create_active_runtime_fixture(root, task_id, resume.MAX_TASK_ALBUMS)
            state = resume.inspect_task(root, task_id)
            request = {
                "request_id": "request-fixture",
                "session_id": "session-fixture",
                "operation": "hello",
            }
            response = resume._response(request, {"resume_state": state})
            response_bytes = len(resume.canonical_json(response))
            self.assertEqual(state["album_count"], resume.MAX_TASK_ALBUMS)
            self.assertLessEqual(response_bytes, resume.MAX_LINE_BYTES)

            checkpoint_before = (root / "checkpoint.json").read_bytes()
            oversized = build_custom_manifest(
                "AGENT-RESUME-TEST-OVER-MAX-PAYLOAD",
                [],
                active_count=resume.MAX_TASK_ALBUMS + 1,
            )
            manifest_path = root.parent / "over-limit-manifest.json"
            write_json(manifest_path, oversized)
            with self.assertRaises(resume.InputError) as caught:
                resume.create_task(root, manifest_path)
            self.assertEqual(caught.exception.code, "TASK_MANIFEST_TOO_LARGE")
            self.assertEqual((root / "checkpoint.json").read_bytes(), checkpoint_before)

    def test_fast_resume_skips_49_verified_then_verifies_only_50(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-FAST-RESUME"
            create_active_runtime_fixture(
                root,
                task_id,
                count=100,
                expected_images_by_ordinal={50: 80},
            )
            self.assertEqual(verify_prefix_for_fast_resume(root, task_id, 49), 49)

            with mock.patch.object(
                resume,
                "_decode_inventory",
                side_effect=AssertionError("fast resume must not decode prior VERIFIED albums"),
            ), mock.patch.object(
                resume,
                "_compile_decoder",
                side_effect=AssertionError("fast resume must not compile the ImageIO helper"),
            ):
                fast = resume.inspect_task(root, task_id)
            self.assertEqual(fast["counts"]["VERIFIED"], 49)
            self.assertEqual(fast["counts"]["NOT_STARTED"], 51)
            self.assertEqual(fast["next_safe_ordinal"], 50)
            self.assertEqual(fast["resume_metrics"]["verified_albums_skipped"], 49)
            self.assertEqual(fast["resume_metrics"]["metadata_files_checked"], 49)
            self.assertEqual(fast["resume_metrics"]["prior_verified_rehash_bytes"], 0)
            self.assertEqual(fast["resume_metrics"]["prior_verified_decode_calls"], 0)
            self.assertGreaterEqual(fast["resume_metrics"]["fast_resume_elapsed_ms"], 0)

            store = resume.read_store(root)
            task = store["tasks"][task_id]
            album_key = task["album_order"][49]
            album = task["albums"][album_key]
            generation, _, _ = dispatch_and_choose(
                root,
                task_id,
                "fast-resume-target",
                store["generation"],
                album_key,
                task,
            )
            destination = resume._task_absolute_path(root, task_id, album["destination"])
            write_png_count(destination, 80)
            ready = resume.inspect_task(root, task_id)
            self.assertEqual(ready["task_phase"], "READY_TO_VERIFY")
            self.assertEqual(ready["first_blocker"], None)
            self.assertEqual(ready["next_safe_ordinal"], 50)
            self.assertEqual(ready["next_safe_album_key"], album_key)
            self.assertEqual(ready["next_safe_album_identity"], album["identity"])
            self.assertEqual(ready["resume_metrics"]["prior_verified_rehash_bytes"], 0)
            self.assertEqual(ready["resume_metrics"]["prior_verified_decode_calls"], 0)

            with mock.patch.object(resume, "_decode_inventory", side_effect=fake_decode_from_inventory) as decode:
                verified = resume.verify_album(
                    root,
                    task_id,
                    "fast-resume-target",
                    generation,
                    album_key,
                    interval_seconds=0,
                    timeout_seconds=1,
                    sleep_fn=lambda _seconds: None,
                )
            self.assertEqual(decode.call_count, 1)
            self.assertEqual(verified["state"], "VERIFIED")
            self.assertEqual(verified["target_album_decode_calls"], 1)
            resumed = resume.inspect_task(root, task_id)
            self.assertEqual(resumed["counts"]["VERIFIED"], 50)
            self.assertEqual(resumed["next_safe_ordinal"], 51)
            self.assertEqual(resumed["resume_metrics"]["verified_albums_skipped"], 50)
            self.assertEqual(resumed["resume_metrics"]["prior_verified_rehash_bytes"], 0)
            self.assertEqual(resumed["resume_metrics"]["prior_verified_decode_calls"], 0)

    def test_blocker_never_exposes_a_later_verifying_album_as_next_safe(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-BLOCKER-ORDER"
            create_active_runtime_fixture(root, task_id, count=2)
            store = resume.read_store(root)

            def derived_album(_root, _store, _task, album, **_kwargs):
                is_blocked = album["ordinal"] == 1
                return {
                    "album_key": album["album_key"],
                    "ordinal": album["ordinal"],
                    "state": "UNKNOWN" if is_blocked else "VERIFYING",
                    "dispatchable": False,
                    "reason": "SAVE_ALL_OUTCOME_UNKNOWN" if is_blocked else "FULL_INVENTORY_NEEDS_VERIFICATION",
                    "inventory_count": 0,
                }

            with mock.patch.object(resume, "_derive_album_state", side_effect=derived_album):
                state = resume.derive_task_state(root, store, task_id)
            self.assertEqual(state["task_phase"], "BLOCKED_AND_PRESERVE_WHOLE_TASK")
            self.assertEqual(state["first_blocker"]["ordinal"], 1)
            self.assertIsNone(state["next_safe_album_key"])
            self.assertIsNone(state["next_safe_ordinal"])
            self.assertIsNone(state["next_safe_album_identity"])
            self.assertEqual(state["next_safe_action"], "STOP_AND_RECONCILE_ONLY")

    def test_chooser_click_then_process_kill_stays_unknown_and_blocks_takeover(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-CHOOSER-CRASH"
            create_active_runtime_fixture(
                root,
                task_id,
                count=100,
                expected_images_by_ordinal={50: 80},
            )
            self.assertEqual(verify_prefix_for_fast_resume(root, task_id, 49), 49)

            def prefix_hashes() -> dict[str, str]:
                store = resume.read_store(root)
                task = store["tasks"][task_id]
                hashes = {}
                for ordinal in range(1, 50):
                    album = task["albums"][task["album_order"][ordinal - 1]]
                    destination = resume._task_absolute_path(root, task_id, album["destination"])
                    for entry in destination.iterdir():
                        hashes["%02d/%s" % (ordinal, entry.name)] = hashlib.sha256(entry.read_bytes()).hexdigest()
                return hashes

            before_prefix = prefix_hashes()
            host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            process = None
            try:
                host_identity = resume.process_identity(host.pid)
                self.assertIsNotNone(host_identity)
                server_code = (
                    "import sys\n"
                    "from pathlib import Path\n"
                    "sys.path.insert(0, sys.argv[1])\n"
                    "import line_backup_agent_resume as resume\n"
                    "raise SystemExit(resume.SessionServer(sys.argv[2], Path(sys.argv[3])).run())\n"
                )
                process = subprocess.Popen(
                    [sys.executable, "-B", "-c", server_code, str(REPO_ROOT / "scripts"), task_id, str(root)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                session_id = "chooser-crash-session"
                current = resume.read_store(root)
                hello = send_session_request(process, {
                    "version": 1,
                    "request_id": "crash-hello",
                    "session_id": session_id,
                    "task_id": task_id,
                    "expected_generation": current["generation"],
                    "operation": "hello",
                    "data": {"host": host_identity, "boot_id": resume.boot_identity()},
                })
                self.assertTrue(hello["ok"], hello)
                self.assertEqual(hello["result"]["resume_state"]["next_safe_ordinal"], 50)
                generation = hello["result"]["generation"]

                store, album = task_and_album(root, task_id, 50)
                task = store["tasks"][task_id]
                album_key = album["album_key"]
                prepare_save = send_session_request(process, {
                    "version": 1,
                    "request_id": "crash-save-prepare",
                    "session_id": session_id,
                    "task_id": task_id,
                    "expected_generation": generation,
                    "operation": "prepare_save_all",
                    "data": {"album_key": album_key, "grounding": make_grounding(task, album_key)},
                })
                self.assertTrue(prepare_save["ok"], prepare_save)
                self.assertTrue(prepare_save["result"]["click_eligible"])

                record_save = send_session_request(process, {
                    "version": 1,
                    "request_id": "crash-save-record",
                    "session_id": session_id,
                    "task_id": task_id,
                    "expected_generation": prepare_save["result"]["generation"],
                    "operation": "record_save_all_result",
                    "data": {
                        "album_key": album_key,
                        "action_id": prepare_save["result"]["action_id"],
                        "outcome": "RETURNED",
                        "evidence_sha256": hashlib.sha256(b"crash-save-returned").hexdigest(),
                    },
                })
                self.assertTrue(record_save["ok"], record_save)

                prepare_chooser = send_session_request(process, {
                    "version": 1,
                    "request_id": "crash-chooser-prepare",
                    "session_id": session_id,
                    "task_id": task_id,
                    "expected_generation": record_save["result"]["generation"],
                    "operation": "prepare_chooser_confirm",
                    "data": {
                        "album_key": album_key,
                        "grounding": make_grounding(task, album_key, chooser=True),
                    },
                })
                self.assertTrue(prepare_chooser["ok"], prepare_chooser)
                self.assertTrue(prepare_chooser["result"]["click_eligible"])
                destination = resume._task_absolute_path(root, task_id, album["destination"])
                write_png_count(destination, 80)
                before_crash_checkpoint = (root / "checkpoint.json").read_bytes()

                process.kill()
                self.assertLess(process.wait(timeout=5), 0)

                inspected = resume.inspect_task(root, task_id)
                self.assertEqual(inspected["task_phase"], "BLOCKED_AND_PRESERVE_WHOLE_TASK")
                self.assertEqual(inspected["first_blocker"]["album_key"], album_key)
                self.assertEqual(inspected["first_blocker"]["state"], "UNKNOWN")
                self.assertEqual(inspected["first_blocker"]["reason"], "CHOOSER_OUTCOME_UNKNOWN")
                self.assertIsNone(inspected["next_safe_ordinal"])
                self.assertTrue(inspected["pending_input"])
                self.assertEqual(
                    inspected["owner_action"],
                    "DO_NOT_TAKE_OVER; INSPECT_ONLY; RECONCILE_PRIVATE_FILES_WITH_OWNER",
                )
                self.assertEqual(inspected["counts"]["VERIFIED"], 49)
                self.assertEqual(inspected["resume_metrics"]["prior_verified_rehash_bytes"], 0)
                self.assertEqual(inspected["resume_metrics"]["prior_verified_decode_calls"], 0)
                self.assertEqual((root / "checkpoint.json").read_bytes(), before_crash_checkpoint)

                blocked = resume.SessionRoot(root)
                with self.assertRaises(resume.SafetyBlock) as caught:
                    blocked.acquire()
                self.assertEqual(caught.exception.code, "PENDING_INPUT_UNRESOLVED")

                crashed_store = resume.read_store(root)
                crashed_album = crashed_store["tasks"][task_id]["albums"][album_key]
                self.assertEqual(crashed_album["save_all_intent"]["result"]["outcome"], "RETURNED")
                self.assertIsNone(crashed_album["chooser_confirm_intent"]["result"])
                self.assertIsNone(crashed_album["verification"])
                with self.assertRaises(resume.SafetyBlock) as verify_error:
                    resume.verify_album(
                        root,
                        task_id,
                        session_id,
                        prepare_chooser["result"]["generation"],
                        album_key,
                        interval_seconds=0,
                        timeout_seconds=1,
                        sleep_fn=lambda _seconds: None,
                    )
                self.assertEqual(verify_error.exception.code, "DISPATCH_EVIDENCE_INCOMPLETE")
                with self.assertRaises(resume.SafetyBlock) as dispatch_error:
                    resume.prepare_save_all(
                        root,
                        task_id,
                        "fresh-crash-session",
                        prepare_chooser["result"]["generation"],
                        album_key,
                        make_grounding(task, album_key),
                    )
                self.assertEqual(dispatch_error.exception.code, "SAVE_ALL_INTENT_EXISTS")
                self.assertEqual((root / "checkpoint.json").read_bytes(), before_crash_checkpoint)
                self.assertEqual(prefix_hashes(), before_prefix)
                self.assertEqual(len(list(destination.iterdir())), 80)
            finally:
                if process is not None and process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                if process is not None:
                    for stream in (process.stdin, process.stdout, process.stderr):
                        if stream is not None:
                            stream.close()
                host.terminate()
                host.wait(timeout=5)

    def test_partial_50_blocks_whole_task_and_preserves_32_files(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-PARTIAL"
            create_runtime_fixture(root, task_id)
            store, task = task_and_album(root, task_id, 50)
            album_key = task["album_key"]
            generation, _, _ = dispatch_and_choose(
                root,
                task_id,
                "partial-session",
                store["generation"],
                album_key,
                store["tasks"][task_id],
            )
            destination = resume._task_absolute_path(root, task_id, task["destination"])
            write_png_count(destination, 32)
            before_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in destination.iterdir()}
            before_checkpoint = (root / "checkpoint.json").read_bytes()

            state = resume.derive_task_state(root, resume.read_store(root), task_id, deep=False)
            self.assertEqual(state["task_phase"], "BLOCKED_AND_PRESERVE_WHOLE_TASK")
            self.assertEqual(state["first_blocker"]["state"], "BLOCKED_PARTIAL")
            self.assertEqual(state["first_blocker"]["inventory_count"], 32)
            self.assertIsNone(state["next_safe_album_key"])

            current_task = resume.read_store(root)["tasks"][task_id]
            for ordinal in range(51, 101):
                candidate_key = current_task["album_order"][ordinal - 1]
                with self.subTest(ordinal=ordinal):
                    with self.assertRaises(resume.SafetyBlock) as caught:
                        resume.prepare_save_all(
                            root,
                            task_id,
                            "partial-session",
                            generation,
                            candidate_key,
                            make_grounding(current_task, candidate_key),
                        )
                    self.assertEqual(caught.exception.code, "TASK_BLOCKED")

            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.verify_album(
                    root,
                    task_id,
                    "partial-session",
                    generation,
                    album_key,
                    interval_seconds=0,
                    timeout_seconds=1,
                    sleep_fn=lambda _: None,
                )
            self.assertEqual(caught.exception.code, "TASK_BLOCKED")
            with mock.patch.object(resume, "_compile_decoder", return_value=Path("/unused-fixture-decoder")):
                reconciled = resume.reconcile_task(root, task_id)
            self.assertEqual(reconciled["first_blocker"]["state"], "BLOCKED_PARTIAL")
            self.assertEqual((root / "checkpoint.json").read_bytes(), before_checkpoint)
            self.assertEqual(
                {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in destination.iterdir()},
                before_hashes,
            )

    def test_fresh_process_intent_kill_leaves_unknown_without_retry(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-PROCESS-INTENT"
            create_runtime_fixture(root, task_id)
            decoder = create_fake_decoder(base / "fake-intent-decoder")
            pid_log = base / "intent-pids.log"

            killed = run_worker(
                PROCESS_RESUME_WORKER,
                [str(REPO_ROOT / "scripts"), str(root), task_id, "intent-only-kill", str(pid_log), str(decoder)],
            )
            self.assertEqual(killed.returncode, 77, killed.stderr)
            killed_record = json.loads(killed.stdout.strip())

            observed = run_worker(
                PROCESS_RESUME_WORKER,
                [str(REPO_ROOT / "scripts"), str(root), task_id, "inspect", str(pid_log), str(decoder)],
            )
            self.assertEqual(observed.returncode, 0, observed.stderr)
            snapshot = json.loads(observed.stdout.strip())
            self.assertEqual(snapshot["phase"], "BLOCKED_AND_PRESERVE_WHOLE_TASK")
            self.assertEqual(snapshot["blocker"]["state"], "UNKNOWN")
            self.assertEqual(snapshot["blocker"]["reason"], "SAVE_ALL_OUTCOME_UNKNOWN")

            store, album = task_and_album(root, task_id, 50)
            self.assertEqual(album["album_key"], killed_record["album_key"])
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.prepare_save_all(
                    root,
                    task_id,
                    "fresh-retry-session",
                    store["generation"],
                    album["album_key"],
                    make_grounding(store["tasks"][task_id], album["album_key"]),
                )
            self.assertEqual(caught.exception.code, "SAVE_ALL_INTENT_EXISTS")
            pids = [int(line) for line in pid_log.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(pids), 2)
            self.assertEqual(len(set(pids)), 2)

    def test_fresh_process_without_intent_leaves_50_fresh(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-PROCESS-BEFORE-INTENT"
            create_runtime_fixture(root, task_id)
            decoder = create_fake_decoder(base / "fake-before-intent-decoder")
            pid_log = base / "before-intent-pids.log"
            before_checkpoint = (root / "checkpoint.json").read_bytes()

            killed = run_worker(
                PROCESS_RESUME_WORKER,
                [str(REPO_ROOT / "scripts"), str(root), task_id, "open-only-kill", str(pid_log), str(decoder)],
            )
            self.assertEqual(killed.returncode, 77, killed.stderr)
            self.assertEqual(json.loads(killed.stdout.strip())["next_safe_ordinal"], 50)

            observed = run_worker(
                PROCESS_RESUME_WORKER,
                [str(REPO_ROOT / "scripts"), str(root), task_id, "inspect", str(pid_log), str(decoder)],
            )
            self.assertEqual(observed.returncode, 0, observed.stderr)
            snapshot = json.loads(observed.stdout.strip())
            self.assertEqual(snapshot["next_safe_ordinal"], 50)
            self.assertIsNone(snapshot["blocker"])
            self.assertEqual((root / "checkpoint.json").read_bytes(), before_checkpoint)

    def test_fresh_process_save_all_returned_before_chooser_preserves_unknown(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-PROCESS-SAVE-RETURNED"
            create_runtime_fixture(root, task_id)
            decoder = create_fake_decoder(base / "fake-save-decoder")
            pid_log = base / "save-pids.log"
            before_checkpoint = (root / "checkpoint.json").read_bytes()

            killed = run_worker(
                PROCESS_RESUME_WORKER,
                [str(REPO_ROOT / "scripts"), str(root), task_id, "save-returned-kill", str(pid_log), str(decoder)],
            )
            self.assertEqual(killed.returncode, 77, killed.stderr)

            observed = run_worker(
                PROCESS_RESUME_WORKER,
                [str(REPO_ROOT / "scripts"), str(root), task_id, "inspect", str(pid_log), str(decoder)],
            )
            self.assertEqual(observed.returncode, 0, observed.stderr)
            snapshot = json.loads(observed.stdout.strip())
            self.assertEqual(snapshot["blocker"]["state"], "UNKNOWN")
            self.assertEqual(snapshot["blocker"]["reason"], "CHOOSER_OUTCOME_UNKNOWN")
            self.assertNotEqual((root / "checkpoint.json").read_bytes(), before_checkpoint)

            store, album = task_and_album(root, task_id, 50)
            destination = resume._task_absolute_path(root, task_id, album["destination"])
            self.assertEqual(list(destination.iterdir()), [])
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.prepare_save_all(
                    root,
                    task_id,
                    "fresh-save-retry",
                    store["generation"],
                    album["album_key"],
                    make_grounding(store["tasks"][task_id], album["album_key"]),
                )
            self.assertEqual(caught.exception.code, "SAVE_ALL_INTENT_EXISTS")

    def test_missing_chooser_evidence_blocks_verification_without_mutation(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-MISSING-CHOOSER"
            create_runtime_fixture(root, task_id)
            store, album = task_and_album(root, task_id, 50)
            task = store["tasks"][task_id]
            intent = resume.prepare_save_all(
                root,
                task_id,
                "missing-chooser-session",
                store["generation"],
                album["album_key"],
                make_grounding(task, album["album_key"]),
            )
            result = resume.record_save_all_result(
                root,
                task_id,
                "missing-chooser-session",
                intent["generation"],
                album["album_key"],
                intent["action_id"],
                "RETURNED",
                "a" * 64,
            )
            destination = resume._task_absolute_path(root, task_id, album["destination"])
            write_png_count(destination, 80)
            before = (root / "checkpoint.json").read_bytes()
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.verify_album(
                    root,
                    task_id,
                    "missing-chooser-session",
                    result["generation"],
                    album["album_key"],
                    interval_seconds=0,
                    timeout_seconds=1,
                    sleep_fn=lambda _seconds: None,
                )
            self.assertEqual(caught.exception.code, "DISPATCH_EVIDENCE_INCOMPLETE")
            self.assertEqual((root / "checkpoint.json").read_bytes(), before)

    def test_fresh_process_80_of_80_kill_verifies_then_advances_to_51(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-PROCESS-80"
            create_runtime_fixture(root, task_id)
            decoder = create_fake_decoder(base / "fake-verify-decoder")
            pid_log = base / "verify-pids.log"

            dispatched = run_worker(
                PROCESS_RESUME_WORKER,
                [str(REPO_ROOT / "scripts"), str(root), task_id, "dispatch-files-kill", str(pid_log), str(decoder)],
            )
            self.assertEqual(dispatched.returncode, 77, dispatched.stderr)
            killed_record = json.loads(dispatched.stdout.strip())
            self.assertEqual(killed_record["ordinal"], 50)
            store, album = task_and_album(root, task_id, 50)
            destination = resume._task_absolute_path(root, task_id, album["destination"])
            before_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in destination.iterdir()
            }
            self.assertEqual(len(before_hashes), 80)

            verified = run_worker(
                PROCESS_RESUME_WORKER,
                [str(REPO_ROOT / "scripts"), str(root), task_id, "verify-fake", str(pid_log), str(decoder)],
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)
            verification = json.loads(verified.stdout.strip())
            self.assertEqual(verification["state"], "VERIFIED")
            self.assertEqual(
                {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in destination.iterdir()},
                before_hashes,
            )

            resumed = resume.derive_task_state(root, resume.read_store(root), task_id, deep=True)
            self.assertEqual(resumed["next_safe_ordinal"], 51)
            self.assertEqual(resumed["counts"]["SKIPPED_EXISTING"], 49)
            self.assertEqual(resumed["counts"]["VERIFIED"], 1)
            self.assertEqual(resumed["counts"]["NOT_STARTED"], 50)
            pids = [int(line) for line in pid_log.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(pids), 2)
            self.assertEqual(len(set(pids)), 2)

    def test_full_50_verification_advances_to_51_then_completes_100(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-FULL"
            create_runtime_fixture(root, task_id)
            decoder = self._compile_decoder_in(base)
            session_id = "full-session"

            with mock.patch.object(resume, "_compile_decoder", return_value=decoder):
                for ordinal in range(50, 101):
                    store = resume.read_store(root)
                    task = store["tasks"][task_id]
                    state = resume.derive_task_state(root, store, task_id, deep=False)
                    self.assertEqual(state["next_safe_ordinal"], ordinal)
                    album_key = task["album_order"][ordinal - 1]
                    album = task["albums"][album_key]
                    generation, _, _ = dispatch_and_choose(
                        root,
                        task_id,
                        session_id,
                        store["generation"],
                        album_key,
                        task,
                    )
                    destination = resume._task_absolute_path(root, task_id, album["destination"])
                    write_png_count(destination, int(album["identity"]["expected_images"]))
                    ready = resume.derive_task_state(root, resume.read_store(root), task_id, deep=False)
                    self.assertEqual(ready["task_phase"], "READY_TO_VERIFY")
                    result = resume.verify_album(
                        root,
                        task_id,
                        session_id,
                        generation,
                        album_key,
                        interval_seconds=0,
                        timeout_seconds=10,
                        sleep_fn=lambda _: None,
                    )
                    self.assertEqual(result["state"], "VERIFIED")
                    if ordinal == 50:
                        resumed = resume.derive_task_state(root, resume.read_store(root), task_id, deep=False)
                        self.assertEqual(resumed["next_safe_ordinal"], 51)
                        self.assertEqual(resumed["counts"]["SKIPPED_EXISTING"], 49)
                        self.assertEqual(resumed["counts"]["VERIFIED"], 1)

                completed_store = resume.read_store(root)
                completed = resume.derive_task_state(root, completed_store, task_id, deep=False)
                self.assertEqual(completed["task_phase"], "COMPLETE")
                self.assertEqual(completed["counts"]["SKIPPED_EXISTING"], 49)
                self.assertEqual(completed["counts"]["VERIFIED"], 51)
                self.assertEqual(completed["photo_count"], 179)
                before_idempotent = (root / "checkpoint.json").read_bytes()
                again = resume.verify_album(
                    root,
                    task_id,
                    session_id,
                    completed["generation"],
                    next(item["album_key"] for item in completed["albums"] if item["state"] == "VERIFIED"),
                    interval_seconds=0,
                    timeout_seconds=10,
                    sleep_fn=lambda _: None,
                )
                self.assertTrue(again["already_verified"])
                self.assertEqual((root / "checkpoint.json").read_bytes(), before_idempotent)

    def test_deep_reconcile_redecodes_verified_album(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-DEEP-DECODE"
            create_runtime_fixture(root, task_id)
            decoder = create_fake_decoder(base / "deep-verify-decoder")
            store, album = task_and_album(root, task_id, 50)
            task = store["tasks"][task_id]
            generation, _, _ = dispatch_and_choose(
                root,
                task_id,
                "deep-decode-session",
                store["generation"],
                album["album_key"],
                task,
            )
            destination = resume._task_absolute_path(root, task_id, album["destination"])
            write_png_count(destination, int(album["identity"]["expected_images"]))
            with mock.patch.object(resume, "_compile_decoder", return_value=decoder):
                verified = resume.verify_album(
                    root,
                    task_id,
                    "deep-decode-session",
                    generation,
                    album["album_key"],
                    interval_seconds=0,
                    timeout_seconds=1,
                    sleep_fn=lambda _seconds: None,
                )
            self.assertEqual(verified["state"], "VERIFIED")

            real_decode = resume._decode_inventory

            def decode_with_fixture(path: Path, expected: int, *, decoder_binary: Path | None = None):
                return real_decode(path, expected, decoder_binary=decoder)

            with mock.patch.object(resume, "_decode_inventory", side_effect=decode_with_fixture) as decode:
                reconciled = resume.reconcile_task(root, task_id)
            self.assertEqual(decode.call_count, 1)
            self.assertEqual(reconciled["counts"]["VERIFIED"], 1)
            self.assertEqual(reconciled["next_safe_ordinal"], 51)
            self.assertEqual(reconciled["resume_metrics"]["prior_verified_decode_calls"], 1)
            self.assertEqual(
                reconciled["resume_metrics"]["prior_verified_rehash_bytes"],
                len(PNG_1X1) * int(album["identity"]["expected_images"]),
            )

    def test_verified_album_missing_moved_or_modified_metadata_blocks_fast_resume(self) -> None:
        cases = (
            ("missing", lambda destination: (destination / "0000.png").unlink(), "VERIFIED_CONTENT_CHANGED"),
            ("moved", lambda destination: destination.rename(destination.with_name(destination.name + "-moved")), "DESTINATION_MISSING"),
            ("modified", lambda destination: (destination / "0000.png").write_bytes(b"changed"), "VERIFIED_CONTENT_CHANGED"),
            ("truncated", lambda destination: (destination / "0000.png").write_bytes(b""), "ZERO_BYTE_FILE"),
        )
        for name, corrupt, expected_code in cases:
            with self.subTest(case=name), home_temporary_directory() as temporary:
                base = Path(temporary).resolve()
                root = base / "agent-resume"
                task_id = "AGENT-RESUME-TEST-POST-VERIFIED-%s" % name.upper()
                create_runtime_fixture(root, task_id)
                decoder = create_fake_decoder(base / "fake-decoder")
                store, album = task_and_album(root, task_id, 50)
                task = store["tasks"][task_id]
                album_key = album["album_key"]
                generation, _, _ = dispatch_and_choose(
                    root,
                    task_id,
                    "post-verified-%s" % name,
                    store["generation"],
                    album_key,
                    task,
                )
                destination = resume._task_absolute_path(root, task_id, album["destination"])
                write_png_count(destination, int(album["identity"]["expected_images"]))
                with mock.patch.object(resume, "_compile_decoder", return_value=decoder):
                    verified = resume.verify_album(
                        root,
                        task_id,
                        "post-verified-%s" % name,
                        generation,
                        album_key,
                        interval_seconds=0,
                        timeout_seconds=10,
                        sleep_fn=lambda _seconds: None,
                    )
                self.assertEqual(verified["state"], "VERIFIED")
                before_checkpoint = (root / "checkpoint.json").read_bytes()
                corrupt(destination)
                with mock.patch.object(
                    resume,
                    "_decode_inventory",
                    side_effect=AssertionError("fast metadata inspection must not decode"),
                ), mock.patch.object(
                    resume,
                    "_compile_decoder",
                    side_effect=AssertionError("fast metadata inspection must not compile"),
                ):
                    fast = resume.inspect_task(root, task_id)
                self.assertEqual(fast["first_blocker"]["reason"], expected_code)
                self.assertIsNone(fast["next_safe_album_key"])
                self.assertEqual(fast["resume_metrics"]["prior_verified_rehash_bytes"], 0)
                self.assertEqual(fast["resume_metrics"]["prior_verified_decode_calls"], 0)
                self.assertEqual((root / "checkpoint.json").read_bytes(), before_checkpoint)
                with mock.patch.object(resume, "_compile_decoder", return_value=decoder):
                    state = resume.reconcile_task(root, task_id)
                self.assertEqual(state["first_blocker"]["reason"], expected_code)
                self.assertIsNone(state["next_safe_album_key"])
                self.assertEqual((root / "checkpoint.json").read_bytes(), before_checkpoint)

                next_task = resume.read_store(root)["tasks"][task_id]
                next_key = next_task["album_order"][50]
                with self.assertRaises(resume.SafetyBlock) as caught:
                    resume.prepare_save_all(
                        root,
                        task_id,
                        "post-verified-next",
                        resume.read_store(root)["generation"],
                        next_key,
                        make_grounding(next_task, next_key),
                    )
                self.assertEqual(caught.exception.code, "TASK_BLOCKED")
                next_destination = resume._task_absolute_path(root, task_id, next_task["albums"][next_key]["destination"])
                self.assertTrue(next_destination.is_dir())
                self.assertEqual(list(next_destination.iterdir()), [])

    def test_fresh_process_resume_completes_50_through_100_with_distinct_pids(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            task_id = "AGENT-RESUME-TEST-FRESH-PROCESS"
            create_runtime_fixture(root, task_id)
            decoder = create_fake_decoder(base / "fake-process-decoder")
            pid_log = base / "fresh-process-pids.log"

            for ordinal in range(50, 101):
                state = resume.derive_task_state(root, resume.read_store(root), task_id, deep=False)
                self.assertEqual(state["next_safe_ordinal"], ordinal)
                completed = run_worker(
                    PROCESS_RESUME_WORKER,
                    [str(REPO_ROOT / "scripts"), str(root), task_id, "dispatch-verify-fake", str(pid_log), str(decoder)],
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                result = json.loads(completed.stdout.strip())
                self.assertEqual(result["state"], "VERIFIED")

            completed = resume.derive_task_state(root, resume.read_store(root), task_id, deep=False)
            self.assertEqual(completed["task_phase"], "COMPLETE")
            self.assertEqual(completed["counts"]["SKIPPED_EXISTING"], 49)
            self.assertEqual(completed["counts"]["VERIFIED"], 51)
            pids = [int(line) for line in pid_log.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(pids), 51)
            self.assertEqual(len(set(pids)), 51)

    def test_protected_fixture_sentinels_remain_byte_identical(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            protected = base / "protected"
            protected.mkdir(mode=0o700)
            sentinels = {
                protected / "grant.bin": b"grant-fixture",
                protected / "ledger.json": b"ledger-fixture",
                protected / "manual.bin": b"manual-fixture",
            }
            for path, payload in sentinels.items():
                path.write_bytes(payload)
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in sentinels}
            create_runtime_fixture(root, "AGENT-RESUME-TEST-PROTECTED")
            store, album = task_and_album(root, "AGENT-RESUME-TEST-PROTECTED", 50)
            task = store["tasks"]["AGENT-RESUME-TEST-PROTECTED"]
            dispatch_and_choose(
                root,
                "AGENT-RESUME-TEST-PROTECTED",
                "protected-session",
                store["generation"],
                album["album_key"],
                task,
            )
            destination = resume._task_absolute_path(root, "AGENT-RESUME-TEST-PROTECTED", album["destination"])
            write_png_count(destination, int(album["identity"]["expected_images"]))
            after = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in sentinels}
            self.assertEqual(after, before)

    def test_intent_before_click_is_unknown_and_never_retried(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-UNKNOWN"
            create_runtime_fixture(root, task_id)
            store, task = task_and_album(root, task_id, 50)
            album_key = task["album_key"]
            intent = resume.prepare_save_all(
                root,
                task_id,
                "unknown-session",
                store["generation"],
                album_key,
                make_grounding(store["tasks"][task_id], album_key),
            )
            after_prepare = (root / "checkpoint.json").read_bytes()
            state = resume.derive_task_state(root, resume.read_store(root), task_id, deep=False)
            self.assertEqual(state["task_phase"], "BLOCKED_AND_PRESERVE_WHOLE_TASK")
            self.assertEqual(state["first_blocker"]["state"], "UNKNOWN")
            self.assertEqual(state["first_blocker"]["reason"], "SAVE_ALL_OUTCOME_UNKNOWN")

            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.prepare_save_all(
                    root,
                    task_id,
                    "unknown-session",
                    intent["generation"],
                    album_key,
                    make_grounding(store["tasks"][task_id], album_key),
                )
            self.assertEqual(caught.exception.code, "SAVE_ALL_INTENT_EXISTS")
            self.assertEqual((root / "checkpoint.json").read_bytes(), after_prepare)

    def test_missing_or_nonempty_destination_blocks_without_recreation(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            missing_root = base / "missing" / "agent-resume"
            missing_task = "AGENT-RESUME-TEST-MISSING-DEST"
            create_runtime_fixture(missing_root, missing_task)
            store, task = task_and_album(missing_root, missing_task, 50)
            destination = resume._task_absolute_path(missing_root, missing_task, task["destination"])
            destination.rmdir()
            state = resume.derive_task_state(missing_root, store, missing_task, deep=False)
            self.assertEqual(state["first_blocker"]["reason"], "DESTINATION_MISSING")
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.prepare_save_all(
                    missing_root,
                    missing_task,
                    "missing-session",
                    store["generation"],
                    task["album_key"],
                    make_grounding(store["tasks"][missing_task], task["album_key"]),
                )
            self.assertEqual(caught.exception.code, "TASK_BLOCKED")
            self.assertFalse(destination.exists())

            extra_root = base / "extra" / "agent-resume"
            extra_task = "AGENT-RESUME-TEST-EXTRA-DEST"
            create_runtime_fixture(extra_root, extra_task)
            extra_store, extra_album = task_and_album(extra_root, extra_task, 50)
            extra_destination = resume._task_absolute_path(extra_root, extra_task, extra_album["destination"])
            (extra_destination / "unknown.bin").write_bytes(b"do not overwrite")
            extra_state = resume.derive_task_state(extra_root, extra_store, extra_task, deep=False)
            self.assertEqual(extra_state["first_blocker"]["reason"], "DESTINATION_NOT_EMPTY_WITHOUT_INTENT")
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.prepare_save_all(
                    extra_root,
                    extra_task,
                    "extra-session",
                    extra_store["generation"],
                    extra_album["album_key"],
                    make_grounding(extra_store["tasks"][extra_task], extra_album["album_key"]),
                )
            self.assertEqual(caught.exception.code, "TASK_BLOCKED")
            self.assertEqual((extra_destination / "unknown.bin").read_bytes(), b"do not overwrite")

    def test_stable_inventory_waits_for_late_destination_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "downloads"
            destination.mkdir(mode=0o700)
            clock = [0.0]
            created = [False]

            def sleep(seconds: float) -> None:
                clock[0] += seconds
                if not created[0]:
                    (destination / "0001.png").write_bytes(PNG_1X1)
                    created[0] = True

            with mock.patch.object(resume.time, "monotonic", side_effect=lambda: clock[0]):
                stable = resume._sample_stable_inventory(
                    destination,
                    interval_seconds=1.0,
                    timeout_seconds=10.0,
                    sleep_fn=sleep,
                )

            self.assertEqual(stable["count"], 1)
            self.assertEqual(stable["stability_samples"], 3)
            self.assertTrue(created[0])

    def test_stable_inventory_empty_destination_times_out(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "downloads"
            destination.mkdir(mode=0o700)
            clock = [0.0]

            def sleep(seconds: float) -> None:
                clock[0] += seconds

            with mock.patch.object(resume.time, "monotonic", side_effect=lambda: clock[0]):
                with self.assertRaises(resume.SafetyBlock) as caught:
                    resume._sample_stable_inventory(
                        destination,
                        interval_seconds=1.0,
                        timeout_seconds=2.0,
                        sleep_fn=sleep,
                    )

            self.assertEqual(caught.exception.code, "DESTINATION_EMPTY")
            self.assertEqual(list(destination.iterdir()), [])


class HistoryAndCrossTaskTests(unittest.TestCase):
    def test_history_barriers_cover_239_109_329_and_65_without_redownload(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            root.mkdir(mode=0o700, parents=True)
            source = root / "history-fixture.json"
            write_json(source, {"fixture": "history-totals"})
            source_raw = source.read_bytes()
            source_sha = hashlib.sha256(source_raw).hexdigest()
            specifications = [
                ("official_state", "2022-01-01", 239),
                ("manual_archives", "2022-02-01", 109),
                ("pr28_checkpoints", "2022-03-01", 329),
                ("exclusion_gate", "2022-04-01", 65),
            ]
            references = [
                {
                    "source_kind": source_kind,
                    "path": str(source.resolve()),
                    "sha256": source_sha,
                    "bytes": len(source_raw),
                    "imported_at_utc": resume.utc_now(),
                }
                for source_kind, _date_text, _count in specifications
            ]
            barriers = []
            prefix_albums = []
            for source_kind, date_text, count in specifications:
                destination = root / ("history-%s" % source_kind)
                destination.mkdir(mode=0o700)
                for index in range(count):
                    (destination / ("%04d.bin" % index)).write_bytes(b"h")
                barriers.append(
                    resume._barrier(
                        source_kind,
                        source_sha,
                        GROUP_KEY,
                        {
                            "start_date": date_text,
                            "end_date": date_text,
                            "expected_images": count,
                        },
                        [str(destination.resolve())],
                        count,
                        "HISTORY_ALREADY_BACKED_UP",
                        "history-%s" % source_kind,
                    )
                )
                prefix_albums.append(
                    {
                        "identity": {
                            "group_key": GROUP_KEY,
                            "start_date": date_text,
                            "end_date": date_text,
                            "expected_images": count,
                            "observed_title": source_kind,
                            "disambiguator": "owner:%s" % source_kind,
                        },
                        "destination": "downloads/history-%s" % source_kind,
                    }
                )
            store = resume._initial_store()
            store["history"] = {"references": references, "barriers": barriers}
            store["payload_sha256"] = resume._payload_digest(store)
            resume._atomic_json_write(root / "checkpoint.json", store)
            task_id = "AGENT-RESUME-TEST-HISTORY-TOTALS"
            fixture = create_custom_runtime_fixture(root, task_id, prefix_albums, active_count=96)

            self.assertEqual(fixture["result"]["skipped_existing_count"], 4)
            current = resume.read_store(root)
            state = resume.derive_task_state(root, current, task_id, deep=False)
            self.assertEqual(state["counts"]["SKIPPED_EXISTING"], 4)
            self.assertEqual(state["photo_count"], 742)
            self.assertEqual(state["next_safe_ordinal"], 5)
            observed_counts = [album["history"]["verified_file_count"] for album in state["albums"][:4]]
            self.assertEqual(observed_counts, [239, 109, 329, 65])
            for _source_kind, _date_text, count in specifications:
                self.assertGreater(count, 0)

    def test_cross_task_verified_album_is_skipped_and_unresolved_intent_blocks_new_task(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            first_task_id = "AGENT-RESUME-TEST-CROSS-A"
            first_fixture = create_custom_runtime_fixture(root, first_task_id, [], active_count=100, history_count=1)
            self.assertEqual(first_fixture["result"]["album_count"], 100)
            decoder = ResumeCoreTests._compile_decoder_in(base)
            with mock.patch.object(resume, "_compile_decoder", return_value=decoder):
                first_store = resume.read_store(root)
                first_task = first_store["tasks"][first_task_id]
                first_key = first_task["album_order"][0]
                first_album = first_task["albums"][first_key]
                generation, _, _ = dispatch_and_choose(
                    root,
                    first_task_id,
                    "cross-session-a",
                    first_store["generation"],
                    first_key,
                    first_task,
                )
                first_destination = resume._task_absolute_path(root, first_task_id, first_album["destination"])
                write_png_count(first_destination, 1)
                verified = resume.verify_album(
                    root,
                    first_task_id,
                    "cross-session-a",
                    generation,
                    first_key,
                    interval_seconds=0,
                    timeout_seconds=10,
                    sleep_fn=lambda _: None,
                )
                self.assertEqual(verified["state"], "VERIFIED")

            exact_prefix = [
                {
                    "identity": dict(first_album["identity"]),
                    "destination": "downloads/cross-verified",
                }
            ]
            second_task_id = "AGENT-RESUME-TEST-CROSS-B"
            second_fixture = create_custom_runtime_fixture(
                root,
                second_task_id,
                exact_prefix,
                active_count=99,
                active_date_offset_days=365,
            )
            self.assertEqual(second_fixture["result"]["skipped_existing_count"], 1)
            second_store = resume.read_store(root)
            second_state = resume.derive_task_state(root, second_store, second_task_id, deep=False)
            self.assertEqual(second_state["albums"][0]["state"], "SKIPPED_EXISTING")
            self.assertEqual(second_state["albums"][0]["reason"], "CROSS_TASK_VERIFIED")

            first_store = resume.read_store(root)
            first_task = first_store["tasks"][first_task_id]
            second_key = first_task["album_order"][1]
            resume.prepare_save_all(
                root,
                first_task_id,
                "cross-session-a",
                first_store["generation"],
                second_key,
                make_grounding(first_task, second_key),
            )
            unresolved_prefix = [
                {
                    "identity": dict(first_task["albums"][second_key]["identity"]),
                    "destination": "downloads/cross-unresolved",
                }
            ]
            third_task_id = "AGENT-RESUME-TEST-CROSS-C"
            third_manifest = build_custom_manifest(
                third_task_id,
                unresolved_prefix,
                active_count=99,
                active_date_offset_days=365,
            )
            third_manifest_path = root.parent / ("%s-manifest.json" % third_task_id)
            write_json(third_manifest_path, third_manifest)
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.create_task(root, third_manifest_path)
            self.assertEqual(caught.exception.code, "CROSS_TASK_INTENT_UNRESOLVED")
            self.assertFalse((root / "tasks" / third_task_id).exists())

    def test_cross_task_date_ambiguity_propagates_exact_blocker(self) -> None:
        with home_temporary_directory() as temporary:
            base = Path(temporary).resolve()
            root = base / "agent-resume"
            first_task_id = "AGENT-RESUME-TEST-DATE-CROSS-A"
            create_custom_runtime_fixture(root, first_task_id, [], active_count=100, history_count=1)
            first_store = resume.read_store(root)
            first_task = first_store["tasks"][first_task_id]
            first_key = first_task["album_order"][0]
            first_album = first_task["albums"][first_key]

            ambiguous_identity = dict(first_album["identity"])
            ambiguous_identity["expected_images"] += 1
            ambiguous_identity["observed_title"] = "same-date-different-count"
            ambiguous_identity["disambiguator"] = "ambiguous:same-date"
            ambiguous_prefix = [
                {
                    "identity": ambiguous_identity,
                    "destination": "downloads/ambiguous-date",
                }
            ]
            second_task_id = "AGENT-RESUME-TEST-DATE-CROSS-B"
            second_manifest = build_custom_manifest(
                second_task_id,
                ambiguous_prefix,
                active_count=99,
                active_date_offset_days=365,
            )
            second_manifest_path = root.parent / ("%s-manifest.json" % second_task_id)
            write_json(second_manifest_path, second_manifest)

            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.create_task(root, second_manifest_path)
            self.assertEqual(caught.exception.code, "CROSS_TASK_DATE_AMBIGUOUS")
            self.assertFalse((root / "tasks" / second_task_id).exists())


class StoreValidationTests(unittest.TestCase):
    def _assert_store_rejected(self, mutate, expected_code: str) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-SCHEMA"
            create_runtime_fixture(root, task_id)
            store = resume.read_store(root)
            mutate(root, store)
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.read_store(root)
            self.assertEqual(caught.exception.code, expected_code)

    def test_generation_change_during_inspection_is_reported_without_mutation(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-UNSTABLE"
            create_runtime_fixture(root, task_id)
            first = resume.read_store(root)
            changed = copy.deepcopy(first)
            changed["generation"] += 1
            changed["payload_sha256"] = resume._payload_digest(changed)
            before = (root / "checkpoint.json").read_bytes()
            with mock.patch.object(resume, "read_store", side_effect=[first, changed]):
                with self.assertRaises(resume.SafetyBlock) as caught:
                    resume.inspect_task(root, task_id)
            self.assertEqual(caught.exception.code, "GENERATION_UNSTABLE")
            self.assertEqual((root / "checkpoint.json").read_bytes(), before)

    def test_store_checksum_schema_and_manifest_bindings_fail_closed(self) -> None:
        def checksum_mutation(root: Path, store: dict) -> None:
            store["generation"] += 1
            resume._atomic_json_write(root / "checkpoint.json", store)

        def schema_mutation(root: Path, store: dict) -> None:
            store["schema_version"] = 2
            store["payload_sha256"] = resume._payload_digest(store)
            resume._atomic_json_write(root / "checkpoint.json", store)

        def album_mutation(root: Path, store: dict) -> None:
            task = store["tasks"]["AGENT-RESUME-TEST-SCHEMA"]
            album_key = task["album_order"][0]
            task["albums"][album_key]["identity"]["observed_title"] = "tampered"
            store["payload_sha256"] = resume._payload_digest(store)
            resume._atomic_json_write(root / "checkpoint.json", store)

        def binding_mutation(root: Path, store: dict) -> None:
            task = store["tasks"]["AGENT-RESUME-TEST-SCHEMA"]
            task["manifest_binding_sha256"] = "0" * 64
            store["payload_sha256"] = resume._payload_digest(store)
            resume._atomic_json_write(root / "checkpoint.json", store)

        self._assert_store_rejected(checksum_mutation, "STORE_CHECKSUM_INVALID")
        self._assert_store_rejected(schema_mutation, "STORE_SCHEMA_UNKNOWN")
        self._assert_store_rejected(album_mutation, "STORE_SCHEMA_INVALID")
        self._assert_store_rejected(binding_mutation, "STORE_MANIFEST_BINDING_INVALID")

    def test_symlink_and_orphan_temp_checkpoint_fail_closed(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "symlink-root"
            create_runtime_fixture(root, "AGENT-RESUME-TEST-SYMLINK")
            checkpoint = root / "checkpoint.json"
            backup = root / "checkpoint.backup"
            checkpoint.rename(backup)
            checkpoint.symlink_to(backup)
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.read_store(root)
            self.assertEqual(caught.exception.code, "CHECKPOINT_SYMLINK")

        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "temp-root"
            create_runtime_fixture(root, "AGENT-RESUME-TEST-TEMP")
            checkpoint = root / "checkpoint.json"
            checkpoint.rename(root / ".checkpoint.tmp.fixture")
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.read_store(root)
            self.assertEqual(caught.exception.code, "STORE_MISSING_WITH_TEMP")

    def test_stale_generation_and_foreign_scope_grounding_cannot_prepare(self) -> None:
        with home_temporary_directory() as temporary:
            root = Path(temporary).resolve() / "agent-resume"
            task_id = "AGENT-RESUME-TEST-GENERATION"
            create_runtime_fixture(root, task_id)
            store, album = task_and_album(root, task_id, 50)
            task = store["tasks"][task_id]
            with self.assertRaises(resume.SafetyBlock) as caught:
                resume.prepare_save_all(
                    root,
                    task_id,
                    "stale-session",
                    store["generation"] - 1,
                    album["album_key"],
                    make_grounding(task, album["album_key"]),
                )
            self.assertEqual(caught.exception.code, "GENERATION_STALE")

            foreign_grounding = make_grounding(task, album["album_key"])
            foreign_grounding["app_identifier"] = "com.example.foreign"
            with self.assertRaises(resume.InputError) as caught:
                resume.prepare_save_all(
                    root,
                    task_id,
                    "foreign-session",
                    store["generation"],
                    album["album_key"],
                    foreign_grounding,
                )
            self.assertEqual(caught.exception.code, "SAVE_ALL_GROUNDING_INVALID")
            unchanged = resume.read_store(root)
            self.assertEqual(unchanged["generation"], store["generation"])
            self.assertIsNone(unchanged["tasks"][task_id]["albums"][album["album_key"]]["save_all_intent"])


class SessionRootTests(unittest.TestCase):
    def _record(self, host: dict, pending_input: bool = False) -> dict:
        now = resume.utc_now()
        return {
            "schema_version": 1,
            "state": "ACTIVE",
            "session_id": "session-test",
            "task_id": "AGENT-RESUME-P0-20261022",
            "boot_id": resume.boot_identity(),
            "controller": {"pid": 999_999_998, "started_at": "not-running"},
            "host": host,
            "pending_input": pending_input,
            "started_at_utc": now,
            "updated_at_utc": now,
            "checkpoint_generation": 0,
        }

    def test_global_writer_lock_and_clean_close(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            try:
                identity = resume.process_identity(host.pid)
                self.assertIsNotNone(identity)
                first = resume.SessionRoot(root)
                first.acquire()
                first.activate(self._record(identity))
                second = resume.SessionRoot(root)
                with self.assertRaises(resume.WriterBusy) as caught:
                    second.acquire()
                self.assertEqual(caught.exception.code, "WRITER_BUSY")
                first.close_clean()
                third = resume.SessionRoot(root)
                third.acquire()
                third.activate(self._record(identity))
                third.close_clean()
                record = json.loads((root / ".session.lock").read_text(encoding="utf-8"))
                self.assertEqual(record["state"], "CLOSED")
                self.assertEqual(stat.S_IMODE((root / ".session.lock").stat().st_mode), 0o600)
            finally:
                host.terminate()
                host.wait(timeout=5)

    def test_live_old_host_blocks_takeover_until_it_exits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            identity = resume.process_identity(host.pid)
            self.assertIsNotNone(identity)
            first = resume.SessionRoot(root)
            first.acquire()
            first.activate(self._record(identity))
            first.release_without_close()
            blocked = resume.SessionRoot(root)
            with self.assertRaises(resume.SafetyBlock) as caught:
                blocked.acquire()
            self.assertEqual(caught.exception.code, "OLD_HOST_ALIVE")
            host.terminate()
            host.wait(timeout=5)
            time.sleep(0.1)
            takeover = resume.SessionRoot(root)
            takeover.acquire()
            takeover.activate(self._record(resume.current_process_identity()))
            takeover.close_clean()

    def test_pending_input_blocks_takeover_even_after_host_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            record = self._record({"pid": 999_999_999, "started_at": "not-running"}, pending_input=True)
            write_lock_record(root, record)
            blocked = resume.SessionRoot(root)
            with self.assertRaises(resume.SafetyBlock) as caught:
                blocked.acquire()
            self.assertEqual(caught.exception.code, "PENDING_INPUT_UNRESOLVED")

    def test_corrupt_or_non_private_owner_record_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            write_lock_record(root, {"schema_version": 1, "state": "active"})
            (root / ".session.lock").write_bytes(b'{"schema_version":1,"state":"active","state":"closed"}\n')
            blocked = resume.SessionRoot(root)
            with self.assertRaises(resume.SafetyBlock) as caught:
                blocked.acquire()
            self.assertEqual(caught.exception.code, "SESSION_OWNER_RECORD_INVALID")


class SessionEofTests(unittest.TestCase):
    def test_eof_after_hello_is_unclean_and_leaves_takeover_barrier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-resume"
            task_id = "AGENT-RESUME-M0-EOF"
            create_runtime_fixture(root, task_id)
            base_generation = resume.read_store(root)["generation"]
            host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            process = None
            try:
                host_identity = resume.process_identity(host.pid)
                self.assertIsNotNone(host_identity)
                server_code = (
                    "import sys\n"
                    "from pathlib import Path\n"
                    "sys.path.insert(0, sys.argv[1])\n"
                    "import line_backup_agent_resume as resume\n"
                    "raise SystemExit(resume.SessionServer(sys.argv[2], Path(sys.argv[3])).run())\n"
                )
                process = subprocess.Popen(
                    [sys.executable, "-B", "-c", server_code, str(REPO_ROOT / "scripts"), task_id, str(root)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                request = {
                    "version": 1,
                    "request_id": "eof-hello",
                    "session_id": "eof-session",
                    "task_id": task_id,
                    "expected_generation": base_generation,
                    "operation": "hello",
                    "data": {"host": host_identity, "boot_id": resume.boot_identity()},
                }
                process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
                process.stdin.flush()
                response = json.loads(process.stdout.readline())
                self.assertTrue(response["ok"])
                process.stdin.close()
                self.assertEqual(process.wait(timeout=5), resume.EXIT_SAFETY_BLOCK)

                blocked = resume.SessionRoot(root)
                with self.assertRaises(resume.SafetyBlock) as caught:
                    blocked.acquire()
                self.assertEqual(caught.exception.code, "OLD_HOST_ALIVE")
            finally:
                if process is not None and process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                if process is not None:
                    for stream in (process.stdin, process.stdout, process.stderr):
                        if stream is not None:
                            stream.close()
                host.terminate()
                host.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
