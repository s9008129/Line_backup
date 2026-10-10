#!/usr/bin/env python3
# finalize_result.py -- update results/implementer.result.json to its final state:
# fix the CORE_ACCEPTANCE_STATUS enum value, re-point gate/evidence manifests at
# freshly hashed artifacts, and refresh the human-facing fields.
import hashlib
import json
import os


TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(TASK))
PREFIX = "harness-development/catalog-diagnostic-continuity-replan-20261010/"
RUN_ID = "2d52b72c-e184-5204-9a42-ff032631d6f6"
TASK_ID = "TASK-20261010-catalog-diagnostic-continuity-replan"


def ev(evidence_id, rel, observation):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).hexdigest()
    return {
        "bytes": len(raw), "contract_sha256": None, "evidence_id": evidence_id,
        "observation": observation, "path": rel, "role": "IMPLEMENTER",
        "run_id": RUN_ID, "sha256": digest, "source_sha256": digest,
        "stage": "IMPLEMENT", "task_id": TASK_ID,
    }


def main():
    path = os.path.join(TASK, "results", "implementer.result.json")
    result = json.loads(open(path, "rb").read().decode("utf-8"))

    result["statuses"]["CORE_ACCEPTANCE_STATUS"] = "NOT_RUN"

    gm = PREFIX + "results/gate-evidence-manifest.json"
    result["gate_results"] = [
        {"gate_id": "G_OFFLINE", "verdict": "PASS", "evidence_manifest": gm},
        {"gate_id": "G_LIVE", "verdict": "NOT_RUN", "evidence_manifest": gm},
        {"gate_id": "G_PRESERVE", "verdict": "PASS", "evidence_manifest": gm},
        {"gate_id": "G_ACCEPTANCE", "verdict": "NOT_RUN", "evidence_manifest": gm},
    ]

    result["evidence_ids"] = [
        "REPLAY_COPY_HASHES", "PACKET_BINDING", "CANDIDATE_BUILD_PROFILE_HASHES",
        "OFFLINE_R01_R19_RESULTS", "PRE_LIVE_INDEPENDENT_REVIEW",
        "LIVE_R20_ACTION_CONTINUITY_EFFECT_OVERLAP", "PRESERVATION_BASELINE_DELTA",
        "HISTORIC3_AUTHORIZED_EXTENSION_LEDGER", "FINAL_INDEPENDENT_ACCEPTANCE",
        "GATE_EVIDENCE_MANIFEST",
    ]

    result["evidence_manifests"] = [
        ev("REPLAY_COPY_HASHES", PREFIX + "replay/manifest.json",
           "43 byte-exact replay copies; every source_sha256 == copy_sha256; no source drift; content formats recorded"),
        ev("PACKET_BINDING", PREFIX + "tmp/verify-packet-01/verify-packet.json",
           "63 source records PASS; plan-contract.json == handoff.json bytes; handoff/spec/plan/review hash bindings PASS; byte binding only, not schema VALID"),
        ev("CANDIDATE_BUILD_PROFILE_HASHES", PREFIX + "offline-validation/candidate-manifest.json",
           "Frozen candidate hash across the five method files; profiles.json hash recorded; capture_preservation.py noted as non-method tool"),
        ev("OFFLINE_R01_R19_RESULTS", PREFIX + "offline-validation/results.json",
           "R01-R19: 19 PASS / 0 FAIL with recorded expected/actual/verdict; R20 NOT_RUN; four-frame continuity/indicator/identity/movement/overlap evidence"),
        ev("PRE_LIVE_INDEPENDENT_REVIEW", PREFIX + "results/pre-live-review.result.json",
           "PENDING_INDEPENDENT_REVIEW; root_self_signature=false; native delegation dispatch attempted twice, both rejected at the platform layer (same error), no reviewer artifact; ready-to-forward packet sha256 cd6edf3e...; dispatch record results/pre-live-review.dispatch.json"),
        ev("LIVE_R20_ACTION_CONTINUITY_EFFECT_OVERLAP", PREFIX + "live/README.md",
           "NOT_RUN: no live session started; pre-live review pending and no fresh user-coordinated LINE foreground; documented CUA surface availability verified read-only; budget 0/6; zero inputs"),
        ev("PRESERVATION_BASELINE_DELTA", PREFIX + "results/preservation.delta-02.json",
           "PASS; final-state re-capture: no HEAD/branch/index/diff change; canonical state, old task, backups, product sources and frozen documents unchanged; only task-scope additions"),
        ev("HISTORIC3_AUTHORIZED_EXTENSION_LEDGER", PREFIX + "results/attempt-ledger.json",
           "Historic 3 attempts preserved; authorized extension consumed once with candidate/profile hashes; live slot unused (0/6)"),
        ev("FINAL_INDEPENDENT_ACCEPTANCE", PREFIX + "問題單.md",
           "PENDING; requires a non-contributor after the live session; ready-to-forward issue packet updated 2026-10-10"),
        ev("GATE_EVIDENCE_MANIFEST", gm,
           "Four-gate evidence manifest with fresh hashes; validation_fact=NOT_RUN; controller admission BLOCKED"),
    ]

    result["analysis"]["facts"] = [
        "Replay copies: 43/43 byte-exact, source==copy hash, no drift; packet binding 63/63 PASS; plan-contract equals handoff bytes.",
        "Offline fixed method: all four frames pass full-slot exact-RGBA continuity (scan-000 bootstrap), indicator structure PASS, identity COMPLETE, movement YES x3 with joint D ranges [-292.029,-243.804], [-292.029,-243.804], [-292.029,-246.483] (all within the expected values), ordered overlap PASS x3.",
        "scan-003 modern OCR keeps raw 相溥 (confidence 0.30); no replacement, no 0.95 threshold; legacy comparison only.",
        "OCR outputs byte-stable across development runs (16 artifacts identical sha256), so no parameter search happened.",
        "R01-R19 all PASS with recorded expected/actual/verdict; R20 NOT_RUN (no live session started).",
        "Preservation delta (final re-capture) PASS: no tracked/index/HEAD change; canonical state, old task, backups, product sources and frozen documents unchanged.",
        "Review packet corrected: stale candidate-manifest.json entry replaced by the current hash; packet re-hashed to cd6edf3e...; all packet entries re-verified byte-identical to current files.",
        "Native delegation dispatch for the configured HIGH_REASONING_REVIEWER was attempted twice and failed at the platform layer with the same rejection ('unknown input item type: additional_tools'); no analysis was received (results/pre-live-review.dispatch.json).",
        "Read-only inventory confirms the documented CUA surface exists on this host (getApp/getAXStateAndScreenshot/App.scroll) and LINE (jp.naver.line.mac) is running; zero inputs were sent.",
        "A fixed-tool local schema check of an earlier draft of this result caught an enum error (statuses/CORE_ACCEPTANCE_STATUS); corrected to NOT_RUN before submission; validation_fact remains NOT_RUN because no applicable stage packet exists.",
    ]
    result["analysis"]["unknowns"] = [
        "External independent pre-live review (non-contributor) has not happened: native channel failed at the platform layer and the ready-to-forward packet awaits the user's relay.",
        "The live CUA session is unexercised; fresh user-coordinated LINE foreground readiness is not established.",
        "Legacy candidate completeness stays UNKNOWN (single stored candidate; not fabricated).",
        "Controller-native admission stays BLOCKED; no applicable stage packet exists, so CONTRACT/RESULT validation is NOT_RUN.",
    ]
    result["analysis"]["evidence"] = result["evidence_ids"]
    result["analysis"]["dependencies"] = {
        "final_acceptance": "PREREQUISITE_BLOCKED",
        "live_session": "PREREQUISITE_BLOCKED",
        "pre_live_independent_review": "PREREQUISITE_BLOCKED",
    }

    result["convergence"]["meaningful_attempts"] = 3
    result["convergence"]["consecutive_no_progress"] = 0
    result["convergence"]["information_gain"] = True
    result["convergence"]["stuck"] = True
    result["convergence"]["last_attempt"] = (
        "Offline artifacts finalized with fresh hashes; stale packet entry corrected and packet "
        "re-hashed (cd6edf3e...); native reviewer dispatch attempted twice, both rejected at the "
        "platform layer, no artifact; ready-to-forward packet presented for external non-contributor review.")

    result["blocker_fingerprint"] = ("native-delegation-platform-failure; independent-pre-live-review-pending; "
                                     "live-cua-available-not-run; controller-admission-blocked")

    result["handoff_summary"] = (
        "離線固定方法與反向測試完成並 PASS（19 PASS/0 FAIL、R20 NOT_RUN）：四幀 continuity／indicator／identity／"
        "movement／overlap 全數通過，scan-003 原始「相溥」保留；封包內一筆暫存舊 hash 已更正（封包現值 sha256 "
        "cd6edf3edbf44d68ac318d0f508914f83ab771aab989d4b0f1e4fe20a5d315c4）並全數重驗相符；preservation 最終"
        "重拍 delta=PASS；歷史 3 次、追加 1 次已消耗、實機 0/6。卡點：同 candidate 的 pre-live 獨立審查——native "
        "delegation 兩次皆於平台層失敗（同一錯誤），root 不能自簽；已備妥可轉交封包與問題單，請轉交非 contributor "
        "高階模型；PASS 後即可在你確認 LINE 前景就緒時執行唯一一次 ≤6 次 scroll 實機（CUA 已確認可用）。"
        "validation_fact=NOT_RUN、controller admission BLOCKED。")

    result["human_decisions"] = [{
        "id": "forward-pre-live-review",
        "question": ("native 派送失敗；請把 results/pre-live-review.packet.json（＋問題單.md）轉交給 non-contributor "
                     "的高階模型做獨立 pre-live 審查。審查 PASS 後，請確認 LINE 已切到已確認群組的相簿列表前景，"
                     "我再執行唯一一次 ≤6 次 scroll 實機。"),
        "options": [
            "轉交封包做獨立審查（建議），PASS 後我再協調實機",
            "先自行檢視封包與離線證據再決定",
            "暫停本診斷，不進實機",
        ],
        "recommendation": "轉交封包：這是 G_LIVE 與最終 Acceptance 的硬前置；目前實機 0/6、零輸入，尚無任何不可逆動作。",
    }]
    result["needs_human"] = True

    assert len(result["handoff_summary"]) <= 1200, "handoff_summary too long"
    assert len(result["convergence"]["last_attempt"]) <= 500, "last_attempt too long"
    for decision in result["human_decisions"]:
        assert len(decision["question"]) <= 500
        assert 2 <= len(decision["options"]) <= 4
        assert all(len(option) <= 200 for option in decision["options"])
        assert len(decision["recommendation"]) <= 300

    with open(path, "wb") as fh:
        fh.write(json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n")
    with open(path, "rb") as fh:
        final = fh.read()
    print(json.dumps({"out": path, "bytes": len(final),
                      "sha256": hashlib.sha256(final).hexdigest()}))


if __name__ == "__main__":
    main()
