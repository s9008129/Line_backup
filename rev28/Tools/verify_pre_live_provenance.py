#!/usr/bin/env python3
"""Fail-closed guard for the current Rev28 W2 item-5 CI freeze.

This prevents source/evidence drift: if the cadence-critical sampler changes,
pre-live review/live use must stop until a new append-only hosted freeze is
published. Later evidence/docs-only commits are allowed while the sampler blob
remains byte-identical.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "evidence/20260925-rev28-native-closed-loop/harness/ci-w2-item5-freeze-provenance-v3.json"


def fail(message: str) -> None:
    raise SystemExit(f"PRELIVE_PROVENANCE_FAIL: {message}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")


def main() -> int:
    if not MANIFEST.is_file():
        fail("missing v3 provenance manifest")
    m = read_json(MANIFEST)
    if m.get("status") != "FROZEN_VALIDATED" or m.get("generation") != "v3":
        fail("manifest is not FROZEN_VALIDATED v3")

    impl = m["implementation"]
    source = ROOT / impl["sourcePath"]
    if not source.is_file():
        fail(f"missing implementation source {impl['sourcePath']}")
    blob = subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(source)], text=True
    ).strip()
    if blob != impl["sourceGitBlobSHA"]:
        fail(
            "HarnessCalibration.swift drifted after the validated CI freeze: "
            f"expected blob {impl['sourceGitBlobSHA']} got {blob}. "
            "Re-run headed CI and publish a new append-only freeze before review/live use."
        )

    for rel, expected in m["frozenFiles"].items():
        path = ROOT / rel
        if not path.is_file():
            fail(f"missing frozen file {rel}")
        actual = sha256(path)
        if actual != expected:
            fail(f"hash mismatch {rel}: expected {expected} got {actual}")

    bounds_path = ROOT / "evidence/20260925-rev28-native-closed-loop/harness/frozen/postcondition-bounds-v3.json"
    latency_path = ROOT / "evidence/20260925-rev28-native-closed-loop/harness/frozen/postcondition-latency-observations-v3.json"
    proof_path = ROOT / "evidence/20260925-rev28-native-closed-loop/harness/runs/HARNESS-20260925-105114/items/05-postcondition-proofs.json"
    bounds = read_json(bounds_path)
    latency = read_json(latency_path)
    proof = read_json(proof_path)

    expected_bounds = {
        "fastCadenceMs": 150,
        "fastPhaseSeconds": 8,
        "slowCadenceMs": 500,
        "hardCapSeconds": 15,
        "lateForensicSampleDelaySeconds": 30,
    }
    if bounds.get("frozenBounds") != expected_bounds or bounds.get("planTimeBounds") != expected_bounds:
        fail("v3 frozen bounds differ from reviewed plan-time bounds")
    if bounds.get("runID") != m["harness"]["runID"]:
        fail("v3 bounds runID does not match provenance")
    if int(latency.get("runCount", 0)) < 20 or len(latency.get("samples", [])) < 20:
        fail("latency evidence has fewer than 20 samples")
    if float(latency.get("maxMs", 1e99)) >= expected_bounds["fastPhaseSeconds"] * 1000:
        fail("observed panel latency is not bounded by the reviewed fast phase")

    expected_outcomes = {
        "withinWindowOutcome": "chooserVerified",
        "timeoutOutcome": "noChooserObserved",
        "lateOutcome": "chooserObservedAfterWindow",
    }
    for key, value in expected_outcomes.items():
        if proof.get(key) != value:
            fail(f"proof {key} expected {value} got {proof.get(key)!r}")
    if proof.get("lateAffirmationNonNil") is not True:
        fail("late outcome lacks affirmative evidence")
    if proof.get("monitorInputPosts") != 0 or proof.get("zeroFurtherInputDuringMonitors") is not True:
        fail("postcondition monitor was not input-free")

    cap = m["hostedCapability"]
    if not (cap.get("accessibility") and cap.get("screenCapture") and cap.get("postEvent")):
        fail("hosted core capability provenance is incomplete")
    if cap.get("screenCaptureKit") != "OK":
        fail("hosted ScreenCaptureKit provenance is not OK")
    vision = cap.get("vision", {})
    if vision.get("status") != "ERROR" or vision.get("error") != "unknownError":
        fail("hosted Vision limitation signature changed")

    result = {
        "status": "PASS",
        "generation": "v3",
        "validatedImplementationCommit": impl["validatedCommitSHA"],
        "implementationSourceGitBlobSHA": blob,
        "workflowRunID": m["ci"]["workflowRunID"],
        "headedArtifactDigest": m["ci"]["headedArtifactDigest"],
        "harnessRunID": m["harness"]["runID"],
        "sampleCount": latency["runCount"],
        "maxLatencyMs": latency["maxMs"],
        "outcomes": expected_outcomes,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
