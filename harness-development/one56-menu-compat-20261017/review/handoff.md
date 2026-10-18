# HUMAN_ASSISTED_ONE56/1 — Plan → Implement Handoff

## 給下一個新 Session Implementer 的完整 Boot Prompt

```text
你是 Owner 在下一階段選定的 Implementer；請在全新、未繼承上一 Session 推理歷史的
Session 中接手 `HUMAN_ASSISTED_ONE56/1`。實際模型／provider／reasoning／Session ID
必須以 runtime 可驗證事實記錄；不可冒稱 Owner 尚未指定的模型。

治理版本邊界：PR #10 base 的 `AGENTS.md` 仍保留過去固定 Sol／Luna／DeepSeek 的角色
描述；PR #12 是尚未合併的 Owner 指定試行治理方案，不可描述成已寫入該 base 的正式
憲法。Owner 現行決策是每個階段自行指定實際 Provider／Model／Session；本 Handoff 只
如實記錄，不得為符合舊模型名稱而冒充身分或造假 Controller 收據。若真正執行中的
Harness Controller／權限政策仍強制舊角色，而本 Session 無法合法符合，立即停止並回報
`ROLE_POLICY_CONFLICT`，交 Owner／外部 ChatGPT 處理，不得繞過。不得修改 PR #10 的
`AGENTS.md`、合併 PR #12、修改全域 Harness 4.8.0，也不得改動已核准 Plan 的任何
bytes／SHA。

目前狀態是 `PLAN_APPROVED / HANDOFF_PENDING_EXTERNAL_REVIEW`。Plan 已在 exact HEAD
`95e90abd587009d7c2246f2bccd2b60e948fcdc4` 取得真實外部
`APPROVE_PLAN`；本 Handoff 本身尚未取得外部 Handoff approval，也不是 Code Review、
runtime grant、foreground handoff、E2E PASS 或執行命令。

開場只做唯讀核對：
1. repository=`s9008129/Line_backup`；frozen base HEAD=
   `95e90abd587009d7c2246f2bccd2b60e948fcdc4`；base branch=
   `implement/line-two-album-pilot-v1-20261014`。
2. Plan artifact=`harness-development/one56-menu-compat-20261017/review/human-assisted-one56-contract-delta.md`；Plan SHA-256=
   `1c00d80ff3dc50b167f5fe9e40b25736a13677b7011c40d6f8e1ba7c6ff00c66`。
3. 必須找到真實外部 ChatGPT Plan Review：
   `https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561377799`；
   verdict=`APPROVE_PLAN`，reviewed HEAD=`95e90abd587009d7c2246f2bccd2b60e948fcdc4`，
   Plan SHA 必須與上列一致，scope=`HUMAN_ASSISTED_ONE56/1_A_ONLY`。這是
   COMMENT review 的 external Plan approval，不是 GitHub APPROVE、Controller receipt
   或 implementation approval。若 SHA／HEAD／scope／AC 不一致，停止並回報
   `BLOCKED_EXTERNAL_PLAN_BINDING_MISMATCH`。
4. 必須另找到外部 ChatGPT 對「本 Handoff PR 的精確 HEAD」完成獨立 Handoff Review，
   且 verdict 為 `APPROVE_HANDOFF`。若沒有、只審舊 Handoff HEAD、只有 COMMENT 中的
   局部接受，或 scope 不一致，立即停止並回報 `BLOCKED_PENDING_EXTERNAL_HANDOFF_REVIEW`；
   不得修改產品、測試、grant、ledger、AGENTS.md、Harness、runtime 或照片。
5. 先讀本 Handoff 的 Plan 身分、AC、已完成／未完成事項、blockers、frozen paths 與
   安全停止條件，再讀專案 `AGENTS.md`、上述 Plan artifact 與必要的既有證據。
   不要載入其他 Session 的完整對話、私人照片、原始 grant 或舊推理歷史。

實作准入分兩層，不得混用：

A. **Implementation Admission（只能開始離線寫程式、focused tests 與 build）：**
   - 必須有真正匹配的 external Plan `APPROVE_PLAN`、綁定本 Handoff 新 exact HEAD 的
     external `APPROVE_HANDOFF`、相同 Plan SHA 與 approved frozen scope。
   - 必須確認正確工作樹／版本，沒有不可安全處理的 dirty 或 source identity 衝突；
     不得擴張下列 11 條產品 source paths、7 個 focused test paths、AC、交易保護或
     原有授權檔案。
   - 若 Plan／Handoff 核准不符、必須變更安全契約，或環境／編譯阻塞無法解決，停止
     並保留證據。
   - 在此階段，尚無未來的新 Grant、已安裝對齊 Runtime、LINE 當次前景或空下載目的地，
     屬預期的 `NOT_READY_FOR_LIVE_E2E`；不是拒絕離線 Implementation／Focused Tests／
     Build 的理由。

B. **Live Transaction Admission（才能操作真實 LINE、Save All、Chooser 或消耗 A56）：**
   - 必須另有精確來源的 `APPROVE_IMPLEMENTATION`、真實 installed source／producer／
     decoder／runtime alignment、綁定實際 E2E actor 的新 immutable HUMAN grant，以及
     Owner 當次 foreground handoff。
   - 必須完成 A56 新鮮身份／eligible、原 canonical ledger／未解 intent／writer／
     reservation、唯一人工作業 request、正確空目的地與完整 chooser path 等檢核。
   - 任一缺失、來源不一致或副作用未知，立即停止所有真實 GUI／Save All／Chooser／
     交易操作；絕不重送或改寫原保護狀態，也不得把 Implementation Admission 當成
     Live Transaction Admission。

只有上述 A 的綁定一致後，才可在 Owner 提供的新隔離 worktree／branch 中做最小實作。
允許修改的產品 source 只能是：
- src/line_backup_batch/cli.py
- src/line_backup_batch/service.py
- src/line_backup_batch/observations.py
- src/line_backup_batch/store.py
- src/line_backup_batch/state_v3.schema.json
- src/line_backup_batch/schema.py
- src/line_backup_acceptance/common.py
- harness-development/line-two-album-pilot-20261014/two_album_entry.mjs
- harness-development/line-two-album-pilot-20261014/mac_runtime.mjs
- harness-development/line-two-album-pilot-20261014/mac/producer.mjs
- rev28/Sources/rev28ctl/VisualDiagnostic.swift

focused tests 只能加到 Plan 明列的 7 個既有測試檔。不得擴寫 scope、新增 framework、
改 2px／u+4／16×16、改 M5/M6、重做 OCR／NCC／shadow-click、修改 canonical
task／Owner／ledger／初始化收據／既有 counters 或舊 grant。

實作必須讓程式支援並以 focused tests 驗證 Plan 的 A56 單本流程：唯讀 readiness →
cap1 begin／admit／prepare → Owner 人工 CARD → 人工視覺校準／closure → 原 intent 與
durable readback → 唯一 SAVE_ALL request → Owner 一次人工 Save All → 精確 chooser
path／空目的地 → 真實下載證據 → 56 檔穩定 inventory／逐檔 SHA-256／完整 ImageIO
解碼 → finalize／VERIFIED readback／stop／release。A admission 只允許離線 code／
tests／build；上述 live 步驟與任何 LINE GUI、Save All、Chooser、正式交易只能在 B
admission 後，由 Owner 當次前景交接與獨立 E2E Session 執行。正式 E2E 必須另經 Code
Review、精確 source/runtime/grant，並由 Owner 在 E2E 階段指定新的獨立 Session 執行。
Implementer 與 E2E 的 provider／model／reasoning／Session ID 均不得硬編碼；新
immutable grant 必須綁定當輪實際選定並由 runtime 證實的 E2E 身分及 Owner human-input
actor。

遇到下列任一情況立即停止並保留證據；A 與 B 必須分開判定：
- **A／Implementation Admission：** Plan／Handoff review／HEAD／SHA／actor／scope
  不匹配；正確 worktree／source identity 有不可安全處理的衝突；需要擴張 frozen
  paths、AC 或交易保護；環境／編譯阻塞無法解決。
- **B／Live Transaction Admission：** 沒有新的 `APPROVE_IMPLEMENTATION` 或有效
  grant；source-runtime closure／producer／decoder binding／installed runtime
  alignment 缺失；有未解 intent／writer／reservation；A56 身份不唯一；目的地不精確
  或非空；Owner 未提供當次前景交接；人工 request 重複；chooser 結果不明；Save All
  結果未知；任何 protected state 需要改寫。
- 缺少未來 grant、runtime、LINE 前景或空目的地本身只阻止 B，不得因此阻止 A 的離線
  Implementation／Focused Tests／Build。
未知 Save All 不重送，ledger／quota／slot 不重置或退還，A 未 VERIFIED／release
前不得使用 ONE56 操作 B。

完成工作包後，建立 `implement-to-e2e` 實例 Handoff，固定實際 diff、Commit／HEAD、
測試／build 命令與結果、source/runtime hashes、逐項 AC 狀態、已知 FAIL／BLOCKED／
NOT_RUN，依規定 Commit／Push／更新同範圍 Draft PR。Commit body 必須有
「意圖／做了什麼／驗證與結果／下一步的建議」。到此停止 Session；不要自審、
不要假冒外部 ChatGPT Code Review、不要啟動正式 E2E、不要宣稱 Save All 或照片備份完成。
```

## 交接身分與版本綁定

| 欄位 | 固定值 |
| --- | --- |
| Task / stage / original PR | `HUMAN_ASSISTED_ONE56/1` / `PLAN_TO_IMPLEMENT` / Draft [#10](https://github.com/s9008129/Line_backup/pull/10) |
| Owner 已選 execution mode | `HUMAN_ASSISTED`；Owner 是人工 GUI 輸入者 |
| 後續 Independent E2E actor | Owner 在 E2E 階段另行指定；實際 provider／model／reasoning／Session ID 尚未指定，必須由 runtime 如實記錄並綁定 grant；不得沿用本文件中的歷史名稱 |
| Implementer | Owner 尚未在本 Handoff 指定；實際模型／provider／reasoning／Session ID 必須由新 Session 誠實記錄 |
| Repo / frozen base branch / base HEAD | `s9008129/Line_backup` / `implement/line-two-album-pilot-v1-20261014` / `95e90abd587009d7c2246f2bccd2b60e948fcdc4` |
| Plan artifact | [`human-assisted-one56-contract-delta.md`](https://github.com/s9008129/Line_backup/blob/95e90abd587009d7c2246f2bccd2b60e948fcdc4/harness-development/one56-menu-compat-20261017/review/human-assisted-one56-contract-delta.md) |
| Plan SHA-256 | `1c00d80ff3dc50b167f5fe9e40b25736a13677b7011c40d6f8e1ba7c6ff00c66` |
| Plan review status | `APPROVE_PLAN`；external COMMENT review，scope 限 `HUMAN_ASSISTED_ONE56/1_A_ONLY` |
| Plan review URL / verdict / reviewed HEAD | [#5561377799](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561377799) / `APPROVE_PLAN` / `95e90abd587009d7c2246f2bccd2b60e948fcdc4` |
| Handoff review status | `PENDING_EXTERNAL_HANDOFF_REVIEW`；必須綁定本 Handoff PR 的最終 exact HEAD |
| Machine-readable v3 plan contract | `NOT_AVAILABLE`；目前只有 Plan／contract-delta 文件，不得冒充 schema v3 contract |
| Harness Controller admission / receipt | `NOT_VERIFIED` |
| Governance template reference | PR [#12](https://github.com/s9008129/Line_backup/pull/12)，Commit `2189631c9c3073d32c8da94db3f77732090d5380`，`docs/agent-session-handoff/templates/plan-to-implement.md`；尚未合併，只作試行治理範本，不是 PR #10 base 的正式憲法 |
| 本 Handoff 的隔離工作分支／PR base | `handoff/one56-trial-20261018` / `implement/line-two-album-pilot-v1-20261014` |

本文件只依 GitHub 可確認的事實整理交接。原 Sol Session 因額度中斷；任何只存在於其
本機、未提交或未同步的工作，皆列為 `UNKNOWN`，不得當成核准來源或已完成成果。

治理版本邊界：PR #10 base 的 `AGENTS.md` 仍保留歷史固定 Sol／Luna／DeepSeek 角色；
PR #12 是尚未合併的 Owner 指定試行治理方案，不能描述成已寫入 base 的正式憲法。
Owner 現行決策是每個階段自行指定實際 Provider／Model／Session，本 Handoff 只如實
記錄。若執行中的 Harness Controller／權限政策仍強制舊角色而無法合法符合，停止並
回報 `ROLE_POLICY_CONFLICT`，交 Owner／外部 ChatGPT 處理；不得修改 base `AGENTS.md`、
合併 PR #12、修改全域 Harness 4.8.0，或改動已核准 Plan 的 bytes／SHA。

## 真正的業務目標與 AC

最終可觀察成果是：在真實 macOS LINE 上，對兩本不同、尚未備份且符合資格的相簿，
各自完成一次受控 Save All、下載原圖、逐檔 SHA-256 與完整 ImageIO 解碼、正式
`VERIFIED` 讀回及 release。GUI 成功訊息、單張檔案的偶然存在、合成測試或診斷觀察
都不能代替這個結果。

| AC | 必要結果 | 目前狀態 |
| --- | --- | --- |
| AC0 執行身分與來源 | 真實 external Plan／Handoff approval、exact-source Code Review、同一 installed source／producer／runtime／有效 grant、Owner 當次前景交接、唯一 GUI 操作者 | `IN_PROGRESS`；Plan 已核准，其餘 gates `NOT_RUN`／`NOT_READY` |
| AC1 A56 身份與資格 | 當下群組／process／window lineage；符合 Plan 的 A56 fingerprint；排除歷史 VERIFIED、人工 65 張及不明 intent | `NOT_RUN` |
| AC2 A 正式交易 | 原 slots／intent／CAS／writer／獨立空目的地／at-most-once；Owner 一次人工 Save All；精確 chooser path 與確認 | `NOT_RUN` |
| AC3 A 原圖 | 正好 56 張穩定原圖；逐檔 SHA-256；完整 ImageIO 解碼；無 partial／空檔／symlink／未知異常 | `NOT_RUN` |
| AC4 A 正式狀態 | 真正 `VERIFIED` commit／readback，與 fingerprint、檔案與目的地證據相符；stop／release 成功 | `NOT_RUN` |
| AC5 B | A 完成後回列表、至少一次真實向下捲動；找到不同且未備份的 eligible B；使用新的獨立 B grant／入口重複完整交易與驗證 | `NOT_RUN`；不得由 ONE56 自動啟動 |
| AC6 保全與獨立判定 | 239 張歷史與人工 65 張排除；canonical ledger／state 完整；每項僅依自身證據判定 | `NOT_RUN`；過往檢查只能作歷史事實 |

A56 的固定辨識條件來自 Plan：相簿列表日期範圍 `2024/05/27–05/31`、`56` 張。
既有真機 detail 曾記錄 `56張照片` 與畫面日期 `2024.06.01`；兩者關係不得靠推論補足。
正式執行必須以當次新鮮、唯一且符合凍結 fingerprint 的證據核對，不得把舊畫面、
舊點位或已排除的 65 張相簿當作 A56。

### 不可破壞的資料與交易邊界

- 歷史 `239` 張 `VERIFIED` 相片必須保留；不得重下載、重選或以其湊第二本。
- 人工備份的 `65` 張相簿（列表曾觀察為 `2024/06/02–06/07`）必須排除，不得選入。
- 保留原 canonical task／Owner、`private/gui-ledger.json`、初始化收據、已用
  counters／slots、observation quota 與任何 failure latch。
- 不建立替代 ledger、不重置／改名 checkpoint、不退還 quota、不重開舊 pending grant。
- Save All 最多一次；request 不可重發；chooser confirm 最多一次；結果不明不得重送。
- 人工來源標 `OBSERVED`／`OPERATOR_REPORTED`；交易結果標 `HUMAN_ASSISTED`，
  不得標成 `FULL_AUTOMATIC_PASS` 或 native precision PASS。
- 機器仍須驗證 duplicate、writer、空目的地、CAS、readback、原 intent、no-refund、
  no-replay 及逐檔內容。
- A 完成 `VERIFIED`／readback／release 前，不得操作 B；B 必須是不同 eligible 相簿，
  並取得新的獨立 grant／entry。

## 已完成與未完成事項

### 已有、可保留的 GitHub 事實

- Owner 已明確選擇 `HUMAN_ASSISTED` 模式；這只授權提出最小契約差異，不是 Plan、
  Code Review 或 runtime 核准。
- 外部 ChatGPT 已在 exact HEAD `95e90ab`、Plan SHA-256
  `1c00d80ff3dc50b167f5fe9e40b25736a13677b7011c40d6f8e1ba7c6ff00c66` 上完成
  [Plan Review #5561377799](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561377799)，
  verdict=`APPROVE_PLAN`，scope=`HUMAN_ASSISTED_ONE56/1_A_ONLY`。此裁決不包含
  implementation、GUI、grant 或 E2E 授權。
- Plan artifact 固定在 reviewed base HEAD `95e90ab`，SHA-256 為
  `1c00d80ff3dc50b167f5fe9e40b25736a13677b7011c40d6f8e1ba7c6ff00c66`。
- M5／M6 product source 切片曾在 exact HEAD `13b547a` 取得
  `ACCEPT_M5_M6_SOURCE_SLICE_ONLY`；整筆自動交易仍為 `CHANGES_REQUIRED`。
- DeepSeek 獨立 E2E 角色／handoff 文件曾在 exact HEAD `55396e8` 取得
  `ACCEPT_DEEPSEEK_E2E_ROLE_AND_HANDOFF_DOCS_ONLY`；不是 product 或 transaction approval。
- 真實 LINE 診斷曾觀察相簿列表、scroll、56 張相簿的名稱／detail、選單與
  `儲存全部` popup，並保留可逆關閉證據；這些是 UI enabler 事實，不是正式交易 PASS。

### 尚未完成

- 本 Handoff 的外部 Handoff Review：`PENDING_EXTERNAL_HANDOFF_REVIEW`。
- 產品 source／schema／entry／Swift 的 HUMAN mode 實作：`NOT_STARTED`。
- Plan 所屬 focused tests、native build、authorizer smoke：`NOT_RUN`。
- exact implementation HEAD 的外部 Code Review：`NOT_RUN`。
- 合法安裝／producer rebuild／source-runtime closure／新 immutable grant：`NOT_READY`。
- Owner 當次 LINE foreground handoff：`NOT_RENEWED`。
- 獨立 E2E 的 provider／model／reasoning／Session ID：`NOT_ASSIGNED`；
  必須由 Owner 在 E2E 階段指定，grant 綁定實際身分。
- 獨立正式 E2E Session：`NOT_STARTED`。
- A56 正式 Save All、chooser、下載、56 檔驗證、`VERIFIED` 讀回：`NOT_RUN`。
- B 的身份、scroll、grant、Save All、下載與驗證：`NOT_RUN`。
- PR #10 整體 implementation approval、merge、deployment：`NOT_APPROVED`。

## 實際阻塞與來源／runtime 對帳

1. **Plan gate 已解除、但不能升格。** exact HEAD `95e90ab` 上的 external
   `APPROVE_PLAN` 已滿足 Plan gate；它仍明列 `APPROVE_IMPLEMENTATION=NOT_GRANTED`、
   `MATCHED_RUNTIME_AND_GRANT=NOT_READY`。本 Handoff 尚待外部 Handoff Review；
   舊 R1 的 `APPROVE_PLAN` 只屬於 `ANCHOR-DETAIL-R1`，R2 曾為
   `CHANGES_REQUIRED_GOAL_ALIGNMENT`，均不能重用。
2. **正式 authorizer 已真實拒絕。** 既有唯讀 preflight 以舊 pending ONE56 bundle 呼叫
   `native_authorize`，exit `4`、`PROJECT_IMPLEMENTATION_REVIEW_REQUIRED`、
   `dispatch_authorized=false`。這是實際第一拒絕，不是幾何測試 PASS。
3. **candidate 與 installed 來源不一致。**
   - candidate 21-file source closure：`be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d`
   - installed source closure：`ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54`
   - installed native producer：`9ef75efe4b217edd1049a623f26739bc0ea4d5950115e208f704976bb1efdf20`
   - ImageIO decoder binding：`1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf`
   - 舊 runtime binding：`cd41ee25387fb784f2aef5158d7dd6bbde27bd44a42d2d42c5a905767b1b6076`；
     它綁定舊 installed 8beb 來源，不是 candidate 的有效 authority。
4. **舊 pending bundle 不是授權。** 其 project grant SHA-256 為
   `93dc5640e85512e49e50fe0d6613c3a15bd9c9a192315a1715dea5325b0149c7`，
   review 仍為 pending；不得修改它來取得綠燈。
5. **自動路徑仍有已證實的限制。** 在現有支援 API／證據範圍內，
   `AUTOMATIC_CLICK_PROOF_UNSUPPORTED`；P1 pixel registration 實驗已
   `BLOCKED_CLOSED`，R2 shadow-click 未核准且沒有重跑。不得重做 OCR／NCC／
   shadow-click／EventTap 研究。
6. **正式 ledger／state 不得改寫。** 公開歷史證據記載 state revision `35`、
   no active batch／writer／context、formal ledger lifecycle `0`／entries `0`、
   ledger SHA-256 `08aa18e42bfee7a8e4d0529bac5b793d830efc1127794dac4baa8f4bdb9864e2`。
   後續 Session 必須從 canonical state 重新讀取；以上只是當時證據，不是可寫入的授權值。
7. **A56 當次前景不是 ready。** 最近一次唯讀觀察看到頂端 65 張排除相簿，
   A56 fingerprint 不可見，且當次 `fresh_foreground_handoff=NOT_RENEWED_THIS_SESSION`。
   不得重用舊點位或猜點。
8. **原 Sol 可能存在未同步成果。** 未提交／未推送內容一律 `UNKNOWN`；本 Handoff
   不引用完整的本機材料作核准依據。

## 外部 Review 狀態（只列 GitHub 可確認裁決）

| Review | 綁定的 exact HEAD | 真正裁決 | 可否重用 |
| --- | --- | --- | --- |
| [5557707124](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5557707124) | `d27c80b` | B1/B2 source slice accepted；live Save All `CHANGES_REQUIRED` | 只作歷史來源接受 |
| [5558490383](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5558490383) | `4bbec71` | M5／M6 issues；`CHANGES_REQUIRED` | 不可作新 HEAD approval |
| [5560487952](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5560487952) | `a846df0` | 只對 `ANCHOR-DETAIL-R1-20261018` 給 `APPROVE_PLAN` | 不可作本 HUMAN Plan approval |
| [5560750050](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5560750050) | `7b16c60` | `ACCEPT_P1_BLOCKED_AS_CORRECT_FAIL_CLOSED` | 只作 P1 停止裁決 |
| [5561025091](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561025091) | `5b96083` | R2 `CHANGES_REQUIRED_GOAL_ALIGNMENT` | 不可作本 Plan approval |
| [5561111099](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561111099) | `13b547a` | M5／M6 source accepted only；full auto transaction `CHANGES_REQUIRED` | 不可作 product／transaction approval |
| [5561127794](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561127794) | `55396e8` | 歷史 E2E role／handoff docs accepted only | 不可作 HUMAN Plan／Code Review，也不指定本輪 E2E 模型 |
| [5561377799](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561377799) | `95e90ab` | `APPROVE_PLAN`；scope=`HUMAN_ASSISTED_ONE56/1_A_ONLY`；`APPROVE_IMPLEMENTATION=NOT_GRANTED` | 只作 approved Plan gate；本 Handoff、Code Review、grant 與 E2E 均未核准 |

外部 ChatGPT 的 COMMENT 或局部 ACCEPT 不會建立 Harness Controller receipt；本機
Session 也不得代寫或預填外部審查結果。

## Frozen implementation contract

### 允許修改的 source（literal paths；不得用 glob 擴張）

1. `src/line_backup_batch/cli.py`
2. `src/line_backup_batch/service.py`
3. `src/line_backup_batch/observations.py`
4. `src/line_backup_batch/store.py`
5. `src/line_backup_batch/state_v3.schema.json`
6. `src/line_backup_batch/schema.py`
7. `src/line_backup_acceptance/common.py`
8. `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs`
9. `harness-development/line-two-album-pilot-20261014/mac_runtime.mjs`
10. `harness-development/line-two-album-pilot-20261014/mac/producer.mjs`
11. `rev28/Sources/rev28ctl/VisualDiagnostic.swift`

### 只可補 focused cases 的既有測試

- `tests/test_single_album_authority.py`
- `tests/test_batch_authority.py`
- `tests/test_batch_observations.py`
- `tests/test_batch_lifecycle.py`
- `tests/test_single_album_entry.mjs`
- `tests/test_visual_diagnostic.mjs`
- `rev28/Tests/Rev28CoreTests/VisualDiagnosticContractTests.swift`

不得修改 `mac/analyzer.mjs`、`mac/classifier.mjs`、`OcrEngine.swift`、自動 CUA
adapter、content／decoder、AGENTS.md、全域 Harness、policy、grant、ledger、state
或私人照片。若實作證明必須新增 source 邊界，停止並交付精確 delta，不得自行擴寫。

### 最小實作順序

1. 嚴格新增 HUMAN grant／review scope／entry／payload admission；AUTO 分支保持原語義。
2. 新增 typed HUMAN observation／manifest／calibration union，不得偽造
   `sck_support`、座標、`CLASSIFIER PASS` 或 native precision。
3. 沿用原 CARD、CAL pair、ATOMIC pair、CHOOSER quartet、slot、CAS、
   durable intent 與 no-refund／no-replay；只追加 actor-bound outcome。
4. Owner 的人工 request 必須在 reservation 與 readback 後唯一發放；同一
   task／grant／run／action／stage 不可重發。
5. chooser 必須驗證完整 path、同窗 lineage 與獨立空目的地；不能只信 leaf name
   或 Owner 的成功摘要。
6. dispatch 後由 Owner 在 E2E 階段指定並由 grant 綁定的獨立 E2E actor 核對 56 張
   穩定 inventory、逐檔 SHA-256 與完整 ImageIO 解碼，再走原 finalize／readback／
   stop／release；不得預先寫死 provider／model／reasoning 或 Session ID。
7. 所有 focused tests、negative cases、Swift build 與 authorizer smoke 完成後，
   固定 exact source／producer／decoder／runtime hashes，交付 external Code Review。

### 立即停止的代碼與條件

- **A／Implementation Admission：** Plan／Handoff review SHA／HEAD／actor／scope
  不一致；或找不到綁定本 Handoff exact HEAD 的 external `APPROVE_HANDOFF`，而只有
  COMMENT 中的局部接受；正確 worktree／source identity 有不可安全處理的衝突；需要
  擴張 frozen 11 source paths、7 focused test paths、AC 或交易保護。
- **B／Live Transaction Admission：** 缺少精確來源的 `APPROVE_IMPLEMENTATION`、有效
  新 grant、source-runtime closure、producer／decoder binding、installed runtime
  alignment 或 Owner 當次前景交接；需要改寫舊 grant；A56 身份、日期／張數、群組、
  process／window、popup、目標相簿或目的地有歧義；人工 request 已存在、重複、跨
  Session 重放、slot 已使用或 readback 失敗；GUI 可能誤觸其他控制、畫面改變或出現
  未預期副作用；Save All／chooser／下載結果不明。
- 上述 B 類未就緒本身只阻止真實 GUI／Save All／Chooser／交易操作，不得被當成離線
  Implementation／Focused Tests／Build 的停止原因。
- 需要改 canonical ledger、239 歷史、65 排除、原 counters、2px／u+4／16×16、
  Plan AC、證據政策或 public contract 才能前進。

## 六個狀態（互不替代）

```text
PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED
IMPLEMENTATION_STATUS=NOT_STARTED
CORE_ACCEPTANCE_STATUS=NOT_RUN
REQUIRED_VERIFICATION_STATUS=PLAN_APPROVED; IMPLEMENTATION_TESTS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
```

其他不可混淆的狀態：

```text
EXTERNAL_PLAN_REVIEW=APPROVE_PLAN_AT_95e90ab
EXTERNAL_PLAN_REVIEW_SCOPE=HUMAN_ASSISTED_ONE56/1_A_ONLY
APPROVE_IMPLEMENTATION=NOT_GRANTED
EXTERNAL_HANDOFF_REVIEW=PENDING
EXTERNAL_CODE_REVIEW=NOT_STARTED
FORMAL_RUNTIME_GRANT_READY=NO
MATCHED_RUNTIME_AND_GRANT=NOT_READY
FORMAL_AUTHORIZER_FIRST_REFUSAL=PROJECT_IMPLEMENTATION_REVIEW_REQUIRED
REAL_SAVE_ALL_DISPATCH_COUNT=0
CHOOSER=NOT_RUN
ALBUM_A_FILES_VERIFIED=NOT_RUN
ALBUM_A_VERIFIED=NOT_RUN
ALBUM_B_VERIFIED=NOT_RUN
INDEPENDENT_E2E=NOT_RUN
HISTORICAL_239_PRESERVED=YES_AS_PRIOR_VERIFIED_EVIDENCE
MANUAL_65_EXCLUDED=YES_PER_CONTRACT
CONTROLLER_ADMISSION=NOT_VERIFIED
```

## 下一步

1. Owner 將本 Handoff PR、精確 HEAD、Plan Review #5561377799 與 reviewed base
   `95e90ab` 交給外部 ChatGPT；由它獨立審查 Handoff，不由本機 Session 代審。
2. 外部 Reviewer 回覆 `APPROVE_HANDOFF`／`CHANGES_REQUIRED`／`BLOCKED`，並綁定本
   Handoff PR 的最終 exact HEAD。沒有真實 `APPROVE_HANDOFF` 前不得開始實作。
3. 若 `CHANGES_REQUIRED`，只修 Handoff 文件並重新送審；不要先改產品或測試。
4. Handoff 核准後，Owner 選擇新 Implementer Session；從 reviewed base `95e90ab`
   實作、focused tests／build、
   Commit／Push 與 `implement-to-e2e` Handoff 完成後，再交外部 Code Review。
5. Code Review 通過且 installed source／producer／runtime／grant 精確閉合後，才由
   Owner 指定 E2E provider／model／reasoning／Session、建立當次前景交接並啟動新的
   獨立 E2E Session；immutable grant 必須綁定該實際身分與 Owner human-input actor。
6. A56 完整 `VERIFIED`／readback／release 後，另取不同 eligible B 的獨立授權；
   本 Handoff 不授權 B。

## 本 Handoff 的證據索引

| 文件／證據 | 相對路徑或 GitHub ref | SHA-256／用途 |
| --- | --- | --- |
| 專案治理 | `AGENTS.md` @ `95e90ab` | `faa2524cd04a971cfe0a6cbca663107d005e148aeebce3a02b42d7430310d404`；工作契約，不得修改 |
| Plan | `harness-development/one56-menu-compat-20261017/review/human-assisted-one56-contract-delta.md` @ `95e90ab` | `1c00d80ff3dc50b167f5fe9e40b25736a13677b7011c40d6f8e1ba7c6ff00c66` |
| External Plan Review | [PR #10 review 5561377799](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561377799) | `APPROVE_PLAN`；reviewed HEAD `95e90ab`；只解 Plan gate |
| 完整 E2E／阻塞報告 | `harness-development/one56-menu-compat-20261017/review/E2E測試報告.md` @ `95e90ab` | `0b0a375cdbe0f8a721dc10c0a67228539f385d60098ca0af01dbd93a9a5c7a87` |
| 歷史 E2E 交接文件 | `harness-development/one56-menu-compat-20261017/review/deepseek1017-e2e-handoff.md` @ `95e90ab` | `b08a551b68f1315f7ccdb3ff98761f916b8fd95546fe0f7b5dc4b2af8ea736fb`；只作歷史文件，不指定本輪 E2E 模型 |
| Formal route preflight | `harness-development/one56-menu-compat-20261017/review/formal-route-preflight-20261018.json` | `65cd1d51c4308c6090f2143bd3fe3d228c71d76f61b43e519d840268eb10af56` |
| Runtime 對帳證據 | `harness-development/one56-menu-compat-20261017/review/resume-runtime-evidence-20261018.json` | `307f9c87e64ae7451e56b3157e7c0703ade1852af6b5e86d616428090bd11a5c` |
| R2 被拒 Plan | `harness-development/one56-menu-compat-20261017/anchor-detail-r2-plan.md` | `be4de7516177fecff2f15dcd2c32c2eafdb817e6ac9552514c8930314cecb669`；不可重用為本 Plan |
| 專案 policy | `policies/line-two-album-pilot-v1.json` | `59d94b72f4fd59d829b56d21a494c9d83c6b91eb2513c15795a58021194a39e9`；唯讀，不得改 grant／ledger |
| 私人原始證據 | `harness-development/one56-menu-compat-20261017/private/`（未上傳） | 只供有權限的 Reviewer／E2E 依 manifest 核對；不得公開照片、人名、原始 grant 或絕對路徑 |

上表的 hash 是公開文件在 frozen base 的文字識別，不是 runtime grant、Controller
receipt 或 E2E PASS。任何後續 source 變更都必須重新計算並重新綁定。

## Handoff 產生紀錄

- 產生日：`2026-10-18`（Asia/Taipei）。
- 產生角色：Owner 指定的隔離 DeepSeek BYOK Handoff Trial Agent；實際 provider／
  model 標識以 Session runtime 可驗證資料為準，未在本文件冒填。
- 已核對 PR #10 遠端 HEAD 為 `95e90ab`，external Plan Review #5561377799 綁定同一
  exact HEAD 且 verdict=`APPROVE_PLAN`；Handoff 文件重放到 reviewed base 之上。
- 只使用 reviewed base `95e90ab` 與 governance reference `2189631` 的 GitHub／唯讀內容；
  未修改 Plan、產品 source、AGENTS.md、Harness 4.8.0、runtime、grant、ledger、
  state 或備份照片。
- 本輪沒有 LINE GUI、Computer Use 輸入、Save All、下載、OCR／NCC／
  shadow-click 重跑、正式交易或獨立 E2E。

`HANDOFF_STATUS=READY_FOR_EXTERNAL_HANDOFF_REVIEW`
`PLAN_STATUS=APPROVE_PLAN_AT_95e90ab`
`EXTERNAL_HANDOFF_REVIEW=PENDING`
`NEXT_ACTION=OWNER_TRANSFER_EXACT_HANDOFF_PR_HEAD_TO_EXTERNAL_CHATGPT`
