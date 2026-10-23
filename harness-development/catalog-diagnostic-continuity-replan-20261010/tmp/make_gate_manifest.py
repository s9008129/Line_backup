#!/usr/bin/env python3
# make_gate_manifest.py -- build the four-gate evidence manifest with freshly
# computed hashes (exclusive create). Read-only otherwise.
import hashlib
import json
import os


TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(TASK))
PREFIX = "harness-development/catalog-diagnostic-continuity-replan-20261010/"


def sha256_file(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def entry(rel, observation):
    raw = open(os.path.join(ROOT, rel), "rb").read()
    return {"path": rel, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "observation": observation}


def main():
    candidate_manifest = json.loads(
        open(os.path.join(ROOT, PREFIX + "offline-validation/candidate-manifest.json"), "rb")
        .read().decode("utf-8"))
    packet_rel = PREFIX + "results/pre-live-review.packet.json"
    manifest = {
        "format": "local-gate-evidence-manifest-1",
        "task_id": "TASK-20261010-catalog-diagnostic-continuity-replan",
        "candidate_hash": candidate_manifest["candidate_hash"],
        "packet_sha256": sha256_file(packet_rel),
        "validation_fact": "NOT_RUN",
        "validation_note": ("No applicable stage packet exists; CONTRACT/RESULT validation stays "
                            "NOT_RUN and no controller receipt is claimed. A supplementary local "
                            "fixed-tool schema check of implementer.result.json is recorded "
                            "separately (results/implementer.result.schema-validation.json; local "
                            "record only, not a controller receipt)."),
        "controller_admission": "BLOCKED",
        "gates": {
            "G_OFFLINE": {
                "verdict": "PASS",
                "evidence": [
                    entry(PREFIX + "offline-validation/results.json",
                          "R01-R19: 19 PASS / 0 FAIL; R20 NOT_RUN; four-frame continuity/indicator/identity/movement/overlap evidence"),
                    entry(PREFIX + "offline-validation/candidate-manifest.json",
                          "Frozen candidate hash 646145c69265cc33aae2ceaa860efa97048b04cc0e4c17c6bdea69902e11a5b6; method file hashes; non-method tool note"),
                    entry(PREFIX + "offline-validation/binding.json",
                          "Frozen binding (candidate/profile/decoder/binding hashes)"),
                    entry(PREFIX + "replay/manifest.json",
                          "43 byte-exact replay copies; source==copy hash; content formats recorded"),
                    entry(PREFIX + "tmp/verify-packet-01/verify-packet.json",
                          "63 source records PASS; plan-contract==handoff bytes; spec/plan/review hash bindings (byte binding only)"),
                ],
            },
            "G_LIVE": {
                "verdict": "NOT_RUN",
                "blocked_reason": ("Pre-live independent review pending (native dispatch platform-failed "
                                   "twice; ready-to-forward packet cd6edf3e...); no fresh user-coordinated "
                                   "LINE foreground; zero inputs sent"),
                "evidence": [
                    entry(PREFIX + "results/pre-live-review.result.json",
                          "PENDING_INDEPENDENT_REVIEW; native dispatch failed at platform layer; no reviewer artifact"),
                    entry(PREFIX + "results/pre-live-review.dispatch.json",
                          "Two spawn attempts, same platform error; no completion records; no fabrication"),
                    entry(packet_rel,
                          "Final ready-to-forward packet after correcting the stale candidate-manifest entry"),
                    entry(PREFIX + "live/README.md",
                          "NOT_RUN; capability facts; zero inputs; budget 0/6"),
                    entry(PREFIX + "results/attempt-ledger.json",
                          "Live slot unused; scroll_calls_used=0; remaining_budget=6"),
                ],
            },
            "G_PRESERVE": {
                "verdict": "PASS",
                "note": ("preservation.after.json / preservation.delta.json (09:42) remain as the earlier "
                         "interim snapshot; the final-state re-capture is below."),
                "evidence": [
                    entry(PREFIX + "results/preservation.before.json",
                          "Implementation-start Git/worktree baseline (HEAD 4a7a36f5, branch v43-ab/codex-rev28)"),
                    entry(PREFIX + "results/preservation.after-02.json",
                          "Final-state re-capture taken at close-out"),
                    entry(PREFIX + "results/preservation.delta-02.json",
                          "verdict PASS; protected sets unchanged; only task-scope additions"),
                ],
            },
            "G_ACCEPTANCE": {
                "verdict": "NOT_RUN",
                "note": "Final independent Acceptance requires a non-contributor after the live session; not run.",
                "evidence": [
                    entry(PREFIX + "問題單.md",
                          "Ready-to-forward independent review request (updated 2026-10-10)"),
                ],
            },
        },
        "notes": [
            "validation_fact NOT_RUN: no applicable stage packet; no fabricated validators, invitations, or receipts.",
            "controller admission remains BLOCKED; nothing in this manifest lifts it.",
            "candidate hash is the single frozen candidate bound to the pending review: 646145c69265cc33aae2ceaa860efa97048b04cc0e4c17c6bdea69902e11a5b6.",
        ],
    }
    out_path = os.path.join(TASK, "results", "gate-evidence-manifest.json")
    if os.path.exists(out_path):
        raise SystemExit("OUTPUT_EXISTS: " + out_path)
    with open(out_path, "xb") as fh:
        fh.write(json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n")
    print(json.dumps({"out": out_path, "packet_sha256": manifest["packet_sha256"],
                      "candidate_hash": manifest["candidate_hash"]}))


if __name__ == "__main__":
    main()
