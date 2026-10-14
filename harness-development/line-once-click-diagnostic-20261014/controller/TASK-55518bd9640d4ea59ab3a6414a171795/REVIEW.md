# PR #8：B01–B05 最小修正與外部重新審查

本修訂回應 [Chief Reviewer 的 CHANGES_REQUIRED](https://github.com/s9008129/Line_backup/pull/8#issuecomment-6159433025)，原受審 HEAD=`ba1f1a1f23063a859680c333dc9debdbf8db4bc1`。請一併閱讀 [plan.md](plan.md)、[plan-contract.json](plan-contract.json)、[.gitignore](.gitignore) 與 [focused validation](validation.json)。這些是待重新審查的 PR 候選文件，不是新原生 publication、Independent Review PASS 或 Controller admission。

Sol／xhigh 僅 Planner／Orchestrator，ChatGPT 是唯一 External Independent Chief Reviewer，Luna／high 僅 Implementer。沒有調用任何 Reviewer／Implementer Agent 或存取 LINE。B01／B02 已修正；B03／B04／B05 的下述能力／政策阻塞仍未解決，禁止 formal live admission。以下政策核對與分類理由不是 Sol 的獨立審查判決。

## B01：詳細頁視窗 lineage

已移除 D02 的前後 window identity／geometry 相等要求。[attempt-14 scope](https://github.com/s9008129/Line_backup/blob/ed22d202f2a17ca87cadf132b1752998afafae28/evidence/20260916-route/attempt-14/99-scope-status.json) 的 s5 記錄新 detail-window 並保留 list-window；[composite-decision](https://github.com/s9008129/Line_backup/blob/ed22d202f2a17ca87cadf132b1752998afafae28/evidence/20260916-route/attempt-14/composite-decision.json) 用 app／frontmost、unique target、AX surface、screenshot-window binding、header context 與 frame binding 驗證，detail AX 可為 chrome-only。新版沿用这些概念：fresh source grounding → 一次 click trace → 同 LINE process/session 中唯一 resulting detail-window，以該次 screenshot／AX、visual／既有 OCR 核對身份；群組承接 verified navigation context，不以日期／張數 alone 推定。不重用歷史座標、tool PASS 或授權，不建立新 vision 工具。

## B02：private/ 與 native path scope

新增 task-local `.gitignore` 的 `/private/`。完整 raw、binding、intent 放在 private/；D03 要求 0700／0600、capture 前 `git check-ignore`／index preflight、commit／push 前 staged 精確白名單，禁止 force-add／raw report／upload。focused validation 只用可刪除的空白非 LINE permission probe 驗證 ignore／modes，沒有私人畫面／AX。

令 R 為 Mac pinned root：`harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/runtime/resources-luna`。private/ 位於既有 task allowed_path；R/`tools/harness/controller.py::_read_regular` L55–81 讀取 task root 內非 symlink regular evidence，`_evidence` L1455–1496 依相對路徑／bytes／hash 驗證，不依 Git tracked／ignored 身分授權；`_snapshot` L203–211 排除 task state_root。驗證只證明 containment／reader／ignore，不是 OS sandbox、network denial 或真機能力證明。

## B03：固定 schema 與 zero-retry enforcement

R/`schemas/v3/task.schema.json` L90–109 固定：

```json
"transient_read_only_retries": {"const": 2},
"delays_seconds": {"const": [10, 30]}
```

既有 `SchemaBundle.validate` 的 focused check：現有 contract 合法，0／[] 記憶體 variant 被拒絕。沒有修改 schema 或保存非法 contract。R/`tools/harness/lifecycle.py::retry_delays` L351–356 對 IMPLEMENTER 一律回傳 `()`，只有明列 read-only role、確定 dispatch 與 TRANSIENT_SERVICE 可得 `(10,30)`。但選定 native tools 只有此函式定義、沒有呼叫點；它不是已綁到 cua_repl 的 capture／click executor，不能保證 transport／agent 不會隱藏 recapture／重送。

`ZERO_DIAGNOSTIC_RETRY_ENFORCEMENT=UNPROVEN`。固定 retry_policy 不改、不視為診斷 retry grant，也不假裝文字禁止已有機械約束。需 competent authority 證實合法且實際適用的既有 zero-retry 約束；未成立前禁止 formal live admission。沒有新增 guard／wrapper／framework。

## B04：non-PASS accounting

`NON_PASS_GOVERNANCE_BLOCKER=UNRESOLVED`。R/`tools/harness/controller.py::record_result` L1643–1650：

```python
if run["stage"] == "IMPLEMENT" and not passed and result["candidate_fact"] in {"PARTIAL", "FAIL", "BLOCKED"} and not self._pending(task_id):
    from .escalation import IssueLedger
    packet = self._issue_packet(state, run, result)
    issue_id = IssueLedger(self.state_root / "issues").open(packet)
```

`reconcile` L1878–1894 拒絕 pending Issue，且需 BLOCKED、無 active run、已接受的 failed run／consumption；ABANDON 不是未匯入 failure 時跳過 mandatory accounting 的入口。record_result L1509–1510 亦拒絕 caller 額外 flags。沒有發現符合「誠實記錄 FAIL／PARTIAL／BLOCKED 且不新增 Issue」的既有 route；不以 PASS、NOT_RUN、換 stage 或不實 closure 規避。

撤回舊稿「不匯入 non-PASS 即 lawful closure」假設。需 competent authority 指出既有合法 failure accounting／disposition 及授權；在禁止新 Issue／修改 V4.8.0 的條件下無法自行解決，故在 formal live admission 前 STOP，不先執行再壓住 accounting。未呼叫 result import／reconciliation。舊 [c6 blocker](../../../line-v3-live-e2e-20261010/continuations/minimal-live-08/replanner-handoff/evidence/c6/controller-protocol-blocker.md) 與 [native admission](../../../line-v3-live-e2e-20261010/continuations/minimal-live-08/replanner-handoff/evidence/c6/native-admission-receipt.md) 的 accounting 不授權新 Task 建立 Issue。

## B05：上層分類與外部 Reviewer

實際讀取的 `/Users/hsiaojohnny/.codex/AGENTS.md` §2 原文：

> STANDARD: Planner → independent Plan Review when the Plan requires it → deterministic Handoff → Implementer. Add Acceptance only when risk or a required gate calls for it.

> Critical means real security/privacy, data loss or migration, public compatibility, production, or consequential semantic risk. Do not classify routine reversible work as Critical by default.

§3 另有 “Runtime/model selection is configurable and separate from role meaning.” 與 “Reviewers and their helpers remain read-only and independent of every contributor to the artifact under review.” R/`policies/v4.8.0/workflow-routing.md` 的 Risk routes 與之相符；STANDARD 的 Plan Review／Acceptance 取決於對應 workflow 欄位／required Acceptance gate，Handoff 為 reviewed contract 的 deterministic compile。來源 hashes 與節錄行數在 validation.json。

依此保留 STANDARD 候選及 `plan_review_required=true`、`independent_acceptance_required=false`、`handoff_review_required=false`：只限另行明確同意的 LINE app 範圍內本地私有觀察與單次導覽，不改既有安全／隱私邊界、不下載或改資料；Chief Reviewer 明確必要，無已證實要求新增 Acceptance gate 或 Handoff 模型審查的規則。不只依可逆性，也不將私人資料當成無風險。若實際 capture／資料流涉及未准許外傳、其他 app 或 consequential privacy boundary，停止、交 Chief Reviewer／Owner 判定；不能用 STANDARD 擴權。這仍是待獨立重新審查的分類理由。

`EXTERNAL_REVIEWER_NATIVE_ROUTE=BLOCKED`。新 Task run.json 固定 R；R/`templates/v4.8.0/runtime-defaults.json` 的 `plan_reviewer` 為 `gpt-6-luna/high`。R/`tools/harness/controller.py::_role_policy` L300–313 讀取這個 mapping；`allocate_run` L360–440 無 external-reviewer override，`_provenance` L586–633 要求真實 bound invitation／completion／actor／session 與符合 pinned policy 的 requested_model／effort。GitHub comment 不是這些 records，同 GitHub actor 也不是原生獨立 actor 證明。沒有已證實的 ChatGPT external attestation 接入口；不得用 Luna／Sol 代審、捏造 records 或私改 mapping。需 competent authority 確立合法外部身份／attestation／role-setting route，本次不建立此能力。原生 schema receipt、review receipt、Controller admission／Handoff 均未成立。

## Publication provenance 與停止狀態

原受審／本地原生 Plan SHA256=`469b093b33e8e89bd69506ab2fe7a91109800df034dba2924dd43192ac7f1dcf`；contract SHA256=`127d4ac65a4dc19604c476ad162e6f50bc4ea397fedf25020bd376caaf4267ad`。新 Plan hash 見 validation.json，contract bytes 不變；Git commit 只 supersede PR review candidate，**未重新 native publish**。原始本地 Plan／contract／publication／result／state 都按原 hash 保留，沒有沿用舊審查結論。

真正原生修訂須走已有 `publish_plan`：R/`tools/harness/controller.py` L443–455 驗證目前 allocated Planner；L485–508 保留 digest-indexed Plan／immutable publication，更新 hashes 並清除 reviewed Plan pin，仍需新的真實 result／schema receipts／Independent Review。此 mutation 本輪未呼叫，不冒充原 Planner child session。

保留 P01／D01／D02／D03，無新增或 PASS gate。原 Task BLOCKED、Issue WAIT_HUMAN、c6 consumed=1／remaining=0、原 28 gates 與 Harness 不變。無新 Task／Issue／continuation／PR、Agent、GUI、framework、CI／Swift／JS 修復或私人 LINE 資料上傳。

`NEXT_ACTION=RETURN_TO_CHATGPT_FOR_INDEPENDENT_RE_REVIEW`。即使外部 PASS，B03／B04／B05、合法新版 publication／receipts／Handoff／Controller admission 及新具體 GUI grant 都須另行真實成立，才可能分派 Luna Implementer。
