#!/usr/bin/env python3
"""Freeze v2 live grants to the reviewed contract and current runtime bytes."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys


ROOT = Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
CON = "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03"
TASK = "TASK-20261010-line-v3-live-e2e"
CONTRACT_SHA256 = "d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219"
DECISION_PATH = "harness-development/line-v3-live-e2e-20261010/continuations/implement-02/user-decision-A.json"
SENSOR_SCOPE = {
    "bundle_id": "jp.naver.line.mac",
    "provider": "SCREEN_CAPTURE_KIT",
    "capture_scope": "FULL_DISPLAY",
    "surfaces": ["ALBUMS", "ALBUM_DETAIL", "FOLDER_CHOOSER"],
    "menu_capture_guard": True,
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def ref(path):
    raw = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(raw), "sha256": sha(raw)}


def write_new(path, value, *, refresh=False):
    target = ROOT / path
    if target.exists() and not refresh:
        raise SystemExit(f"refusing to overwrite existing artifact: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(json_bytes(value))


def main():
    refresh = sys.argv[1:] == ["--refresh"]
    if sys.argv[1:] and not refresh:
        raise SystemExit("usage: build_runtime_bindings.py [--refresh]")
    sys.path.insert(0, str(ROOT / "src"))
    from line_backup_batch.store import SOURCE_PATHS, Store

    product = ROOT / "harness-development/line-v3-live-e2e-20261010"
    producer_relative = f"{CON}/bin/rev28ctl"
    producer = ROOT / producer_relative
    if not producer.exists():
        built = ROOT / CON / "swift-build-26.5/debug/rev28ctl"
        if not built.is_file() or not os.access(built, os.X_OK):
            raise SystemExit("missing executable rev28ctl produced by the reserved Swift full suite")
        producer.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built, producer)
    if not producer.is_file() or not os.access(producer, os.X_OK):
        raise SystemExit("producer binary is not an executable regular file")

    project = Store(str(ROOT)).snapshot()
    decision_ref = ref(DECISION_PATH)
    waiver_ref = ref(f"{CON}/plan-review-waiver.json")
    contract_ref = ref(f"{CON}/plan-contract.json")
    if contract_ref["sha256"] != CONTRACT_SHA256:
        raise SystemExit("reviewed contract hash changed")
    native_ref = ref("harness-development/line-v3-live-e2e-20261010/bin/image_decode")
    if native_ref["sha256"] != "1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf":
        raise SystemExit("existing decoder binary hash changed")

    replaceable = [
        f"{CON}/runtime-binding.json",
        f"{CON}/authorization.json",
        f"{CON}/live-grant-1.json",
        f"{CON}/live-grant-2.json",
    ]
    if refresh:
        archive_dir = ROOT / CON / "evidence/superseded-bindings-01"
        archive_dir.mkdir(parents=True, exist_ok=False)
        archived = []
        for path in replaceable:
            source = ROOT / path
            if source.is_file():
                target = archive_dir / Path(path).name
                shutil.copy2(source, target)
                raw = target.read_bytes()
                archived.append({"original_path": path, "archived_path": str(target.relative_to(ROOT)),
                                 "bytes": len(raw), "sha256": sha(raw)})
        note = {
            "kind": "SUPERSEDED_RUNTIME_BINDINGS",
            "reason": "Product source changed after the initial v2 binding preflight; these byte-identical artifacts are retained for history and are not current authority.",
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "archived": archived,
        }
        note_path = ROOT / CON / "evidence/superseded-bindings-01.json"
        note_path.write_bytes(json_bytes(note))

    python_path = Path(sys.executable).resolve(strict=True)
    swift_sources = sorted(
        str(path.relative_to(ROOT))
        for base in (ROOT / "rev28/Sources/Rev28Core", ROOT / "rev28/Sources/rev28ctl")
        for path in base.rglob("*.swift")
        if path.is_file()
    )
    memberships = {
        "product_sources_21": sorted(SOURCE_PATHS),
        "task_modules": sorted([
            SOURCE_PATHS[-1],
            f"{CON}/live_runner.mjs",
            f"{CON}/live_classifier.mjs",
            f"{CON}/chooser_locators.mjs",
        ]),
        "swift_sources": swift_sources,
        "package_manifest": ["rev28/Package.swift"],
        "python_runtime": [str(python_path)],
        "producer_binary": [producer_relative],
    }
    included = {}
    for group, paths in memberships.items():
        for path in paths:
            included.setdefault(path, set()).add(group)
    files = []
    for path in sorted(included):
        source = Path(path) if path.startswith("/") else ROOT / path
        raw = source.read_bytes()
        files.append({
            "path": path,
            "bytes": len(raw),
            "sha256": sha(raw),
            "member_of": sorted(included[path]),
        })

    runtime = {
        "version": 1,
        "task_id": TASK,
        "project_root": str(ROOT),
        "contract_path": f"{CON}/plan-contract.json",
        "contract_sha256": CONTRACT_SHA256,
        "source_sha256": project["receipt"]["source_sha256"],
        "memberships": memberships,
        "files": files,
    }
    runtime_path = f"{CON}/runtime-binding.json"
    write_new(runtime_path, runtime, refresh=refresh)

    authorization = {
        "format_version": "3",
        "task_id": TASK,
        "project_root": str(ROOT),
        "artifact_dir": CON,
        "contract_path": f"{CON}/plan-contract.json",
        "contract_sha256": CONTRACT_SHA256,
        "source_sha256": project["receipt"]["source_sha256"],
        "config_sha256": project["receipt"]["config_sha256"],
        "authorized_owners": ["live-grounding-03-g1", "live-grounding-03-g2"],
        "decision_code": "A",
        "decision_ref": decision_ref,
        "plan_review_decision": "USER_WAIVED_NOT_RUN",
        "plan_review_waiver_ref": waiver_ref,
        "sensor_scope": SENSOR_SCOPE,
        "album_quota": 2,
        "config_albums_per_lifecycle": 1,
        "save_all_dispatch_cap": 2,
        "chooser_confirmation_cap": 2,
        "additional_reversible_gui_invocation_cap": 1000,
        "independent_acceptance_required": True,
    }
    auth_path = f"{CON}/authorization.json"
    write_new(auth_path, authorization, refresh=refresh)

    acceptance_ref = None
    operations = [
        "begin", "admit", "prepare", "calibrate", "intent", "dispatch",
        "finalize", "stop", "finish", "release", "resume",
        "gui_reserve", "gui_consume", "frame_support",
    ]
    for slot, owner in enumerate(authorization["authorized_owners"], start=1):
        grant = {
            "grant_version": "line-batch-execution-grant-2",
            "task_id": TASK,
            "project_root": str(ROOT),
            "fixture": False,
            "artifact_dir": CON,
            "owner": owner,
            "operations": operations,
            "config_sha256": project["receipt"]["config_sha256"],
            "source_sha256": project["receipt"]["source_sha256"],
            "album_quota": 2,
            "lifecycle_album_limit": 1,
            "save_all_dispatch_limit": 2,
            "chooser_confirmation_limit": 2,
            "reversible_gui_invocation_limit": 1000,
            "authorization_evidence": ref(auth_path),
            "acceptance_evidence": acceptance_ref,
            "contract_sha256": CONTRACT_SHA256,
            "native_binary_sha256": native_ref["sha256"],
            "gui_ledger": "harness-development/line-v3-live-e2e-20261010/gui-ledger.json",
            "contract_path": f"{CON}/plan-contract.json",
            "producer_binary": ref(producer_relative),
            "runtime_binding": ref(runtime_path),
            "sensor_scope": SENSOR_SCOPE,
        }
        write_new(f"{CON}/live-grant-{slot}.json", grant, refresh=refresh)

    print(json.dumps({
        "source_sha256": project["receipt"]["source_sha256"],
        "config_sha256": project["receipt"]["config_sha256"],
        "runtime_binding": ref(runtime_path),
        "authorization": ref(auth_path),
        "grants": [ref(f"{CON}/live-grant-{slot}.json") for slot in (1, 2)],
        "producer_binary": ref(producer_relative),
        "decision_ref": decision_ref,
        "waiver_ref": waiver_ref,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
