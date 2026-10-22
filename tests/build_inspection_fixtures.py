#!/usr/bin/env python3
"""Generate Rev28 project-inspection fixtures from the real producer.

The generated project roots are local to the output directory and contain only
public synthetic data. The Swift consumer reads the producer's stdout, config,
state, and source bytes through the paths recorded by this script, so this is
an integration fixture rather than a hand-built report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SEED = REPO / "tests/fixtures/project_inspection/seed.json"
SOURCE_RELATIVE = "src/line_backup_acceptance"
CASE_DECISIONS = {
    "eligible": "PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION",
    "verified": "SKIP_VERIFIED",
    "busy": "PROJECT_BUSY",
    "unresolved": "BLOCKED_UNRESOLVED",
    "ambiguous": "AMBIGUOUS_FINGERPRINT",
    "destination": "BLOCKED_DESTINATION",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> bytes:
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def destination(root: Path, group_name: str, target: dict[str, Any]) -> str:
    return (
        f"{root}/backups/{group_name}/"
        f"{target['start_date']}_{target['end_date']}_{target['expected_images']}張"
    )


def base_state() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "revision": 1,
        "current_run_id": None,
        "verified_albums": [],
        "runs": [],
        "active_writer_id": None,
        "context_lock": None,
    }


def synthetic_run(
    *,
    run_id: str,
    group_key: str,
    target: dict[str, Any],
    destination_path: str,
    outcome: str = "SAFE_ABORT",
) -> dict[str, Any]:
    phase = "SAFE_ABORT" if outcome == "SAFE_ABORT" else "LOAD_STATE"
    checkpoint = {
        "phase": phase,
        "at": "2025-01-13T00:00:00Z",
        "evidence": "fixture:synthetic-checkpoint",
    }
    return {
        "run_id": run_id,
        "mode": "backup_one",
        "group_key": group_key,
        "album_id": None,
        "fingerprint": target,
        "observed_title": "Synthetic album",
        "title_confidence": "HIGH",
        "destination": destination_path,
        "destination_initially_empty": True,
        "phase": phase,
        "checkpoint": checkpoint,
        "events": [],
        "intent": None,
        "recovery_used": {},
        "runtime_errors": [],
        "verification": None,
        "workflow_outcome": outcome,
        "stop_reason": None,
        "batch_id": None,
        "intent_state": "INTENT_NONE",
        "manual_reconciliation_required": False,
        "reconciliation_reason": None,
        "contract_revision": "1.0-rc2",
        "dispatch_state": "NOT_ATTEMPTED",
        "dispatch_evidence": None,
        "reconciliations": [],
    }


def copy_producer_sources(project_root: Path, source_names: list[str]) -> None:
    target = project_root / SOURCE_RELATIVE
    target.mkdir(parents=True)
    for name in source_names:
        source = REPO / SOURCE_RELATIVE / name
        if not source.is_file():
            raise SystemExit(f"missing current producer source: {source}")
        shutil.copyfile(source, target / name)


def user_fact_evidence(
    project_root: Path,
    *,
    group_name: str,
    group_key: str,
    target: dict[str, Any],
    destination_path: str,
) -> str:
    proof_path = project_root / "evidence" / "synthetic-user-fact-proof.json"
    proof_bytes = write_json(
        proof_path,
        {
            "fixture_provenance": "PUBLIC_SYNTHETIC_PROJECT_INSPECTION",
            "observation": "No native observation, LINE interaction, or real archive is represented.",
        },
    )
    label = target["start_date"].replace("-", "/") + "～" + target["end_date"][5:].replace("-", "/")
    record = {
        "app_identifier": "jp.naver.line.mac",
        "group_key": group_key,
        "fingerprint": target,
        "record_version": "1.0",
        "kind": "source_identity_user_fact",
        "status": "CONFIRMED",
        "source_correspondence_result": "CONFIRMED",
        "merge_prohibited": True,
        "raw_requested_group": group_name,
        "run_id": None,
        "destination": destination_path,
        "question": {"text": "Synthetic fixture: confirm this exact source?"},
        "answer": {
            "raw": "Synthetic fixture confirmation; not an owner statement.",
            "part_2": {
                "confirms_same_source": True,
                "confirmed_group_string": group_name,
                "confirmed_album": label,
                "confirmed_expected_images": target["expected_images"],
            },
        },
        "evidence": [
            {
                "path": str(proof_path),
                "bytes": len(proof_bytes),
                "sha256": sha256(proof_bytes),
            }
        ],
    }
    evidence_path = "evidence/synthetic-user-fact.json"
    evidence_bytes = write_json(project_root / evidence_path, record)
    return f"user_fact:{evidence_path}:{sha256(evidence_bytes)}"


def build_case(
    *,
    output: Path,
    case: str,
    seed: dict[str, Any],
    source_names: list[str],
) -> dict[str, Any]:
    case_root = output / case
    project_root = case_root / "project"
    project_root.mkdir(parents=True)
    copy_producer_sources(project_root, source_names)

    group_name = seed["group_name"]
    group_key = f"line:jp.naver.line.mac:{group_name}"
    target = dict(seed["target"])
    destination_path = destination(project_root, group_name, target)
    state = base_state()

    if case == "verified":
        evidence_ref = user_fact_evidence(
            project_root,
            group_name=group_name,
            group_key=group_key,
            target=target,
            destination_path=destination_path,
        )
        state["verified_albums"].append(
            {
                "group_key": group_key,
                "fingerprint": target,
                "verified_run_id": None,
                "destinations": [destination_path],
                "source_kind": "user_attestation",
                "evidence": evidence_ref,
            }
        )
    elif case == "busy":
        state["active_writer_id"] = "synthetic-writer"
    elif case in {"unresolved", "ambiguous"}:
        case_target = dict(target)
        if case == "ambiguous":
            case_target["expected_images"] = target["expected_images"] + 1
        run = synthetic_run(
            run_id=f"RUN-SYNTHETIC-{case.upper()}",
            group_key=group_key,
            target=case_target,
            destination_path=destination(project_root, group_name, case_target),
            outcome="FAILED" if case == "unresolved" else "SAFE_ABORT",
        )
        state["runs"].append(run)
        if case == "unresolved":
            state["current_run_id"] = run["run_id"]
    elif case not in {"eligible", "destination"}:
        raise SystemExit(f"unsupported fixture case: {case}")

    config = {
        "schema_version": 2,
        "group_key": group_key,
        "group_name": group_name,
        "backup_root": str(project_root / "backups"),
        "app_identifier": "jp.naver.line.mac",
        "max_albums_per_run": 1,
        "recovery_limit": 1,
        "poll_interval_seconds": 1,
        "stable_samples": 2,
        "max_wait_seconds": 10,
    }
    config_bytes = write_json(project_root / "config" / "line_backup_config.json", config)
    state_bytes = write_json(project_root / "state" / "backup_state.json", state)

    if case == "destination":
        dest = Path(destination_path)
        dest.mkdir(parents=True)
        (dest / "synthetic-existing.jpg").write_bytes(b"public synthetic destination blocker\n")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src") + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    command = [
        sys.executable,
        "-m",
        "line_backup_acceptance",
        "project-preflight",
        "--project-root",
        str(project_root),
        "--start-date",
        target["start_date"],
        "--end-date",
        target["end_date"],
        "--expected-images",
        str(target["expected_images"]),
    ]
    result = subprocess.run(
        command,
        cwd=REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if not result.stdout:
        raise SystemExit(f"{case}: producer emitted no stdout")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{case}: producer stdout is not JSON: {exc}") from exc
    expected_decision = CASE_DECISIONS[case]
    if report.get("decision") != expected_decision:
        raise SystemExit(
            f"{case}: expected {expected_decision}, got {report.get('decision')!r}; "
            f"stderr={result.stderr.decode('utf-8', 'replace').strip()}"
        )
    if report.get("state_facts", {}).get("manual_archive_match") is not False:
        raise SystemExit(f"{case}: current producer did not emit manual_archive_match=false")

    (case_root / "stdout.json").write_bytes(result.stdout)
    write_json(case_root / "config.json", config)
    write_json(case_root / "state.json", state)
    if result.stderr:
        (case_root / "producer.stderr").write_bytes(result.stderr)

    return {
        "case": case,
        "decision": expected_decision,
        "exit_code": result.returncode,
        "config_sha256": sha256(config_bytes),
        "state_sha256": sha256(state_bytes),
        "stdout_sha256": sha256(result.stdout),
        "source_sha256": report["producer"]["source_sha256"],
        "source_files": [entry["path"] for entry in report["producer"]["source_files"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    cases = seed.get("cases")
    if not isinstance(cases, list) or len(cases) != len(CASE_DECISIONS) or set(cases) != set(CASE_DECISIONS):
        raise SystemExit("seed must request each supported fixture case exactly once")
    sys.path.insert(0, str(REPO / "src"))
    from line_backup_acceptance.project_binding import SOURCE_NAMES

    manifest = []
    for case in cases:
        case_root = output / case
        if case_root.exists():
            shutil.rmtree(case_root)
        manifest.append(build_case(output=output, case=case, seed=seed, source_names=SOURCE_NAMES))
    write_json(output / "manifest.json", {"schema": "project-inspection-fixtures-v1", "cases": manifest})
    print(json.dumps({"status": "PASS", "output": str(output), "case_count": len(manifest)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
