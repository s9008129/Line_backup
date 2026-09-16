#!/usr/bin/env python3
"""Phase 2 / R6 (ownership half, post-fix) — shared roots survive every driver run.

CLAIM (Rev14, reproduced pre-fix in attempt-01)  `tests/authority_negative_driver.py` and
       `tests/test_transaction_core.py` deleted the shared `/private/tmp/line-backup-acceptance-case-01..12`
       roots, destroying other drivers' evidence (historically: case-12 disappeared), so the wave
       was destructive and non-repeatable.

ENTRY  The real driver scripts run as subprocesses exactly as a test runner would:
       `tests/authority_negative_driver.py --summary ...`, `python3 -m unittest tests.test_transaction_core`,
       and one full `tests/acceptance_case_driver.py --case-id 01` run (a real heavy user of a shared root).

ORACLE (Rev15 §15.5)  Before the runs, the probe adopts every shared root that already carries a
       task marker and writes `driver-records/r6-ownership/*` probe files into the literal shared roots;
       roots without a marker are never created or touched by this probe (hard refusal).  After the
       runs it re-hashes every probed root's ownership marker and probe artifacts, and re-checks the
       existence of all `case-01`…`case-25` plus the authority/verifier/status roots.

DECIDE Post-fix: every marker, probe artifact and root must survive -> NO_DELETION_OBSERVED.
       Any removed root, changed marker or missing probe is TASK_REGRESSION (CROSS_TEST_DELETION_OBSERVED),
       never an environment failure.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as H  # noqa: E402

DRIVER_ID = "phase2-r6-ownership"
PROBE_DIR = "driver-records/r6-ownership"
SHARED_ROOTS = [Path(f"/private/tmp/line-backup-acceptance-case-{i:02d}") for i in range(1, 26)]
AUX_ROOTS = [Path("/private/tmp/line-backup-acceptance-authority"),
             Path("/private/tmp/line-backup-acceptance-verifier"),
             Path("/private/tmp/line-backup-acceptance-status-r6")]
# Roots whose content this probe may extend (all must already carry a task marker; the probe
# never creates or adopts an unowned root).  The verifier driver owns one root per matrix row
# beneath its base, so those are enumerated at runtime.
STATIC_PROBE_ROOTS = SHARED_ROOTS[:12] + [AUX_ROOTS[0], AUX_ROOTS[2]]


def snapshot(path: Path, *, probe: bool) -> dict:
    row = {"root": str(path), "exists": path.exists()}
    if not row["exists"]:
        return row
    marker = path / H.MARKER_NAME
    row["marker"] = H.sha256_file(marker) if marker.is_file() else None
    row["probe"] = None
    if probe:
        probe_file = path / PROBE_DIR / "probe.json"
        if probe_file.is_file():
            data = probe_file.read_bytes()
            row["probe"] = {"path": str(probe_file), "bytes": len(data), "sha256": H.sha256_bytes(data)}
    return row


def place_probe(root: Path, marker_driver: str) -> dict:
    """Adopt an already-owned shared root and drop this probe's artifact under `driver-records/`."""
    owned = H.ensure_owned_root(root, DRIVER_ID)
    probe_file = root / PROBE_DIR / "probe.json"
    payload = {"probe": DRIVER_ID, "root": str(root), "adopted_marker_driver": owned.get("driver_id"),
               "marker_driver_hint": marker_driver, "placed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    H.write_json(probe_file, payload)
    return payload


def run(argv: list[str], cwd: Path, timeout: float = 900.0) -> dict:
    proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, check=False, timeout=timeout)
    return {"argv": argv, "cwd": str(cwd), "exit_code": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    ev = Path(ns.evidence_dir)
    if ev.exists() and any(ev.iterdir()):
        raise SystemExit(f"refusing: evidence dir {ev} is not empty (append-only evidence)")
    ev.mkdir(parents=True, exist_ok=True)

    record: dict = {"claim": "shared case roots and recorded evidence survive every driver run",
                    "entry": "authority_negative_driver + unittest tests.test_transaction_core + "
                             "acceptance_case_driver --case-id 01, all as real subprocesses",
                    "oracle": "ownership markers, driver-records probe artifacts, root existence before/after",
                    "program_hashes": H.program_hashes()}

    # 1) inventory all shared roots, and place probes only into roots that already carry a task marker
    verifier_children = sorted(p for p in AUX_ROOTS[1].iterdir() if p.is_dir()) if AUX_ROOTS[1].is_dir() else []
    all_roots = SHARED_ROOTS + AUX_ROOTS + verifier_children
    probe_roots = STATIC_PROBE_ROOTS + verifier_children
    record["probe_root_candidates"] = [str(path) for path in probe_roots]
    probe_placement = {}
    skipped_unowned = []
    for root in probe_roots:
        if not root.exists() or not (root / H.MARKER_NAME).is_file():
            skipped_unowned.append({"root": str(root), "reason": "absent or no task ownership marker; "
                                                                 "the probe never creates or touches it"})
            continue
        probe_placement[str(root)] = place_probe(root, marker_driver="existing")
    record["probe_placement"] = probe_placement
    record["skipped_unowned"] = skipped_unowned
    probed = {str(root) for root in probe_roots}
    before = {str(path): snapshot(path, probe=str(path) in probed) for path in all_roots}

    # 2) run the historically destructive pair plus one full shared-root acceptance driver run
    runs = {}
    probe_scratch = ev / "probe-runs"
    probe_scratch.mkdir(parents=True, exist_ok=True)
    runs["authority_negative_driver"] = run(
        ["/usr/bin/python3", str(H.WORK / "tests/authority_negative_driver.py"),
         "--summary", str(probe_scratch / "authority-summary.json")], cwd=H.WORK)
    runs["test_transaction_core"] = run(
        ["/usr/bin/python3", "-m", "unittest", "-v", "tests.test_transaction_core"], cwd=H.WORK)
    case01 = Path("/private/tmp/line-backup-acceptance-case-01")
    manifest_stash = Path("/private/tmp/line-backup-acceptance-wave/r6-ownership-case-01-manifest.json")
    if (case01 / H.MARKER_NAME).is_file():
        # `--manifest` copies the case root's manifest, whose artifact paths are relative to the case
        # root; stash it in working space and keep the resolvable copy inside the durable tree instead
        # (`probe-runs/case-01-durable/manifest.json`, copied below with the whole case root).
        manifest_stash.parent.mkdir(parents=True, exist_ok=True)
        runs["acceptance_case_driver_01"] = run(
            ["/usr/bin/python3", str(H.WORK / "tests/acceptance_case_driver.py"), "--case-id", "01",
             "--case-root", str(case01),
             "--pre-state", str(probe_scratch / "case-01-pre.json"),
             "--state", str(case01 / "state" / "backup_state.json"),
             "--post-state", str(probe_scratch / "case-01-post.json"),
             "--counter", str(probe_scratch / "case-01-counter.jsonl"),
             "--result", str(probe_scratch / "case-01-result.json"),
             "--manifest", str(manifest_stash),
             "--stdout", str(probe_scratch / "case-01-stdout.log"),
             "--stderr", str(probe_scratch / "case-01-stderr.log"),
             "--exit-code", str(probe_scratch / "case-01-exit-code"),
             "--evidence-dir", str(probe_scratch)], cwd=H.WORK)
        durable_chain = ev / "probe-runs" / "case-01-durable"
        H.durable_copy_tree(case01, durable_chain)
        record["case_01_chain"] = {"case_root": str(case01), "durable_copy": str(durable_chain),
                                   "durable_manifest": str(durable_chain / "manifest.json"),
                                   "stashed_manifest_copy": str(manifest_stash),
                                   "stash_note": "the stash lives in working space only; the resolvable durable "
                                                 "manifest is the copy at the case-01-durable root"}
    for name, run_record in runs.items():
        (ev / f"{name}-stdout.log").write_text(run_record["stdout"], encoding="utf-8")
        (ev / f"{name}-stderr.log").write_text(run_record["stderr"], encoding="utf-8")
        (ev / f"{name}-exit-code").write_text(f"{run_record['exit_code']}\n", encoding="utf-8")
    record["runs"] = {name: {"argv": value["argv"], "exit_code": value["exit_code"]}
                      for name, value in runs.items()}

    # 3) re-read everything
    after = {str(path): snapshot(path, probe=str(path) in probed) for path in all_roots}
    destroyed = sorted(path for path in before if before[path]["exists"] and not after[path]["exists"])
    marker_changed = sorted(path for path in before
                            if before[path].get("marker") is not None
                            and before[path]["marker"] != after[path].get("marker"))
    probe_missing = sorted(path for path in before
                           if before[path].get("probe") is not None and before[path]["probe"] != after[path].get("probe"))
    markers_present = sorted(path for path in before if before[path].get("marker") is not None)
    probes_present = sorted(path for path in before if before[path].get("probe") is not None)

    record["roots_before"] = before
    record["roots_after"] = after
    record["markers_present"] = markers_present
    record["probes_present"] = probes_present
    record["destroyed_roots"] = destroyed
    record["markers_changed"] = marker_changed
    record["probes_missing_or_changed"] = probe_missing
    record["driver_exit_codes"] = {name: value["exit_code"] for name, value in runs.items()}
    safe = not destroyed and not marker_changed and not probe_missing
    record["verdict"] = "NO_DELETION_OBSERVED" if safe else "CROSS_TEST_DELETION_OBSERVED"
    record["deletion_evidence_passed"] = safe

    H.write_json(ev / "observation.json", record)
    manifest = H.write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "destroyed": destroyed, "markers_changed": marker_changed,
                      "probes_changed": probe_missing, "probed_roots": len(probe_placement),
                      "driver_exit_codes": record["driver_exit_codes"],
                      "manifest_sha256": manifest["manifest_sha256"]}, ensure_ascii=False))
    return 0 if safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
