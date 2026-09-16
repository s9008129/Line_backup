# LINE 相簿自動備份 — 自動化驗證階段交接文件

版本：H2.1（2026-09-16 19:36 Asia/Taipei）
修訂（H2 → H2.1）：新增 §5 B1 使用者事實記錄、§11 證據索引一列與版本字樣；其餘內容未變。
接手對象：新對話中的 coding agent（本檔是唯一啟動輸入）
本檔取代舊版 `handoff.md`；舊版已封存於
`evidence/20260916-handoff-root-cause/attempt-02/handoff-root-before-automation-testing.md`
（25871 bytes，SHA-256 `5f35f6d306e2ecaab45435d8fedf3780a046d4c981ad02bea83d6e68ee9f97e0`，內容未改）。

## 0. 這份文件是什麼、不是什麼

- 是：使用者目標、已核對事實、權威路徑、**接下來自動化測試的流程步驟邏輯**、停止與升級條件。
- 不是：production 授權、Stage03 已批准 handoff、GUI 輸入授權、修復批准、下載授權。
- 任何修復只要碰到安全／持久化／成功語意，都必須走 CRITICAL 流程重新修訂 `plan.md`、獨立 review、
  重新編譯 handoff，再由 fresh implementer 執行。本檔不能當成批准。

## 1. 目標與完成定義（Goal Contract）

**最終目標（使用者）**：LINE macOS 相簿「全自動」備份，全程不需要人工介入。
**本輪里程碑（使用者指定）**：把「整個流程的**自動化驗證**」做實——可重跑、誠實、可獨立複驗的測試與驗收，
而不是增加 PASS 數量或文件。
**本輪最大範圍**：只做一個相簿：`2024/05/13～05/17`，預期 57 張。不得擴張到其他相簿或群組批次。

三個結果必須分開報告：

1. **本相簿資料結果**：來源、檔案、目的地、state/registry/intent 一致性。
2. **可重用自動化能力**：實際執行路徑安全、at-most-once dispatch、中斷恢復不重送、重複防護、可獨立驗收。
3. **整體任務結案**：1 與 2 都成立才 `complete`。

分類（不得混淆）：

- `CORE`：來源身分、檔案完整性、目的地正確、state/registry/intent 一致、at-most-once dispatch、
  crash 恢復、重複防護、必要獨立驗收、目前 runtime 的可靠選路。
- `SUPPORTING`：bridge/服務修復（**只有在實驗證明它是完成備份的必要因果條件時**才動）。
- `BEST_EFFORT`：歷史整理、通用框架、其他相簿、擴充測試框架。

`SUPPORTING` 失敗不得變成檔案驗證的全域否決；`BEST_EFFORT` 失敗不得阻擋主軸。
反過來：offline／fixture PASS **不得**冒充 GUI 端到端成功。

## 2. 最小載入順序（控制 context）

1. 本檔（`WORK/handoff.md`）與新對話的 `/goal`。
2. 適用 `AGENTS.md`；skill：`/Users/hsiaojohnny/.codex/skills/line-album-backup/SKILL.md`（1.0-rc2）。
   要動 GUI 前才加讀 `references/state-machine.md`、`references/ui-procedure.md`、`references/evidence.md`；
   每次驗證前讀 `references/verification.md`；啟動即讀 `references/state-contract.md`。
3. `CURRENT_TASK/plan.md`（Rev13，105280 bytes，SHA `ad1ac6ac…`）——只讀需要段落，不要整份重讀。
4. `CURRENT_TASK/e2e/attempt-03/review_report.md` 與 `CURRENT_TASK/result.md`（歷史結論與 blocker）。
5. `WORK/src/line_backup_acceptance/*.py`（受測程式本體）。
6. 其餘只在被引用時追原始證據；**不要**掃描 `.agent/tasks/*` 其他任務。

## 3. 權威位置（不得用 cwd、搜尋結果或其他 root 替代）

| 名稱 | 絕對路徑 |
|---|---|
| WORK | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup` |
| DATA_PROJECT_ROOT | `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state` |
| DATA_CONFIG | `<DATA_PROJECT_ROOT>/config/line_backup_config.json` |
| DATA_STATE | `<DATA_PROJECT_ROOT>/state/backup_state.json` |
| DATA_LOG | `<DATA_PROJECT_ROOT>/state/run_log.md` |
| EXISTING_DEST | `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` |
| CURRENT_TASK | `WORK/.agent/tasks/T20260916-0102-01-line-backup-acceptance` |
| SKILL | `/Users/hsiaojohnny/.codex/skills/line-album-backup/SKILL.md` |
| 舊版交接封存 | `WORK/evidence/20260916-handoff-root-cause/attempt-02/handoff-root-before-automation-testing.md` |
| CUA 證明與 BYOK 查證 | `WORK/evidence/20260916-cua-cli-proof/`（見 §6） |

授權狀態：正式 `config`、`state`、`run_log`、`EXISTING_DEST` 內 57 張照片 **目前全部唯讀**。
`WORK` 內可做隔離測試與必要修復準備。WORK 是 untracked 的 git repo（尚無 commit）；動任何檔案前先看 `git status`。

## 4. 現況快照（2026-09-16 18:34–18:45 實際讀回）

**受測程式（bytes／SHA-256）**：`transaction.py` 13835／`c486edbe…`、`verifier.py` 15541／`b38ee6d5…`、
`status.py` 7454／`20a95f7c…`、`authority.py` 8522／`a98964e3…`、`cli.py` 4583／`a5bbbbf6…`、
`common.py` 4021／`59a85c47…`（與舊交接記載一致，未變動）。

**任務 artifacts**：`plan.md` Rev13（105280 bytes／`ad1ac6ac3cc5b63b5b6e1e48d8db525f556c680046abd026b7201680defb251a`，
批准於 `review/attempt-16/review_report.md`）、Stage03 `handoff.md`（10495／`60e51a62…`）、
`execution.md`（12268／`3df8527e…`）、`result.md`（4472／`a89fa3e5…`）。

**正式 authority**：`DATA_CONFIG.group_key = line:jp.naver.line.mac:旻謙允楨成長日記`（**楨** U+6968）；
`DATA_STATE` revision 39、`current_run_id: null`、`unresolved_runs: null`。`verified_albums` 共 4 筆，全部
`group_key` 為 **楨** 系列、`source_kind: filesystem_verification`（legacy 匯入，沒有 `source_authority` join）：
index 0–2（65／56／53 張）為 `verified_run_id: null`、`destinations: []`；**index 3 就是本案**
（`2024-05-13`～`2024-05-17`、57 張），`verified_run_id: "RUN-20260907-154331-01"`、
`destinations: ["/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57"]`。
它是 legacy 匯入、不是本次 transaction 的 VERIFIED commit；verifier 要求
`source_authority='authoritative_exact_join'`，所以 registry FAIL 是「來源品質不足」，不是「entry 不存在」。
`outputs/`、`work/` 為空。

**正式 authority 現檔 hash（2026-09-16 讀回）**：state 48146 bytes／
`e9313a563bf298d4b1e9ae243c5d3d404ad1333f69cb71b156e68589a8ec2f59`；config 372 bytes／
`390cbdcf36a88c9f134c0ecb29d39018ebadf42babfb7a264a741337499d3b3b`；run_log 15950 bytes／
`a62dd07d1df1a34fb91a11d6eec6ac8aae7146abf9eb7011b78b1d27914158bf`（與
`evidence/20260916-baseline/attempt-01/baseline-pre.json` 記載一致）。

**既有備份**：`EXISTING_DEST` 現況實測 57 個檔案、17,924,900 bytes、全部 `image/jpeg`、
檔名 `LINE_ALBUM_20240513～0517_260907_N.jpg`、最後寫入 2026-09-07 15:53。內容完整但來源為 legacy。

**最近結論**：`result.md` = `ACCEPTED_WITH_SCOPED_BLOCKER`；`IMPLEMENTATION_STATUS: COMPLETE`、
`CORE_ACCEPTANCE_STATUS: BLOCKED`、`TASK_CLOSURE_STATUS: CORE_ACCEPTANCE_BLOCKED`、`BASELINE_REGRESSION_DELTA: UNCHANGED`。
`evidence/20260916-product-verify/attempt-03/reconciliation.json`：filesystem PASS、registry FAIL、
source UNRESOLVED、state LEGACY_PROVENANCE_LIMITED、overall UNKNOWN、exit 4。
`evidence/20260916-route/attempt-01/route-decision.json`：`route_status UNKNOWN`、
`decision SAFE_ABORT_NO_GUI_INPUT`、ellipsis 額度 2/2 已用完、`save_all_click_count 0`、
`backup_state_write_count 0`、`production_dispatch FORBIDDEN`。

## 5. 兩個 Scoped Blocker（唯一未解項）

**B1 — 來源身分（禎／楨）**
使用者要求的是 `旻謙允禎成長日記`（**禎** U+798E）；正式 config/state 是 `旻謙允楨成長日記`（**楨** U+6968）。
兩者必須保持獨立字串與 key：**禁止合併、正規化、改寫 canonical key，或用相同日期／count／hash 推斷同群**。
解法只有兩條（`result.md` 已定）：

1. authoritative exact source join；或
2. **一筆精確保留的使用者事實**：記錄原始請求 group、原始持久化 group、app、相簿／日期／數量、
   精確問題與精確回答、提供者與時間、證據 SHA-256，且**不得合併兩字**。

> 2026-09-16 18:39 新觀察（supporting only）：Computer Use 從 LINE 視窗讀到的**現行標題**顯示為
> `旻謙允禎成長日記 (3)`（**禎**）。截圖證據：`evidence/20260916-cua-cli-proof/crop-header-3x.jpg`
> （`04b35c35…`）、`crop-sidebar-3x.jpg`（`80f44aa7…`）、原始 `line-window-raised-20260916T1839+0800.jpg`
> （`9e6aeaf0…`）。這是 `[OBSERVED]` 視覺文字，**不是**身分證明，不能單獨用來合併字串；它只能在使用者
> 給出精確回答後，與該回答一起構成解法 2 的證據。

> 2026-09-16 19:29 使用者事實（已記錄）：使用者對上面第 1 問回答「正確是「禎」」；第 2 問（既有 57 張是否即
> 該群組 2024/05/13～05/17 的備份）尚未回答。原始問題、原始回答、供應者、時間與唯讀複核 hash 已保存於
> `evidence/20260916-user-fact/source-identity-user-fact.json`（複核 19:32：config/state/run_log hash 與
> 57 張皆未變動）。**兩字仍不得合併**；是否足以讓 SOURCE_CORRESPONDENCE=CONFIRMED 須由接手任務的
> plan／review 判定。

**B2 — GUI 觀察 gate（純觀察，不是下載）**
需要使用者一次明確授權：「在 LINE 已顯示精確目標（app `jp.naver.line.mac`、群組 `旻謙允禎成長日記`、
相簿 `2024/05/13～05/17`、57 張）時，允許**恰好一次** current-target ellipsis 觀察輸入，取得即時 post 證據
後停止」。該 gate **不**授權：點選單項、點 Save All、進 chooser、鍵盤快捷鍵、任何 state 寫入、任何下載、
任何 production transaction。歷史 ellipsis 額度已用盡（2/2），新的授權是新的、必須精確。

## 6. 環境事實（本回合新查證；直接影響自動化驗證設計）

### 6.1 Codex CLI 的 Computer Use 可用，而且**不綁 OpenAI 模型**

- 活證（同一台機器、同一個 CLI session）：模型 `deepseek-v4.1-flash`、provider `ollama_cloud`
  （`https://ollama.com/v1`、`wire_api="responses"`、`model_reasoning_effort="max"`），CUA 外掛
  `unified-computer-use@openai-bundled 26.908.70816` 提供的 `cua_repl` 工具**實際完成**：
  `getState`、`getApp("jp.naver.line.mac")`、`rewriteDocumentation`、`performSecondaryAction(0,"Raise")`、
  `getScreenshot()`。
- 機制：CUA 是外掛＋MCP 工具（本地執行、以 function call 回傳結果），與模型是誰無關；外掛設定檔與 CLI
  binary 內**沒有**任何 model/provider 閘門。
- 真正的模型相關閘門只有 ModelInfo metadata：`input_modalities`（不含 image 時，圖片在送上游前被替換成
  `<image content omitted because you do not support image input>`）與 `node_repl_disabled`；BYOK 未知名模型
  套用 fallback metadata（本機所有 catalog 都是 `text,image`、`node_repl_disabled=false`）。
- 圖片路徑已實測：MCP 工具回圖 → `input_image`（base64 data URL、`detail`）→ Responses API。
  2026-09-16 18:35 隔離探針結論 `IMAGE_PATH_WORKS`：圖送出後續請求全部完成、0 error、0 aborted turn。
  殘留不確定性：未檢視 provider 端原始 wire log；「被接受」= 未被拒絕且對話持續。
- 官方文件立場：`wire_api` 設定參考只支援 `responses`；Computer Use 官方文件只寫桌面 App（未提 CLI）；
  API-key 登入時 plugins 為 `limited`；官方**沒有**明文說 Computer Use 需要特定模型或需要 image input。
- 已知風險（社群實測）：工具回圖在部分第三方 provider 會 400；`reasoning_content` 必須回傳；
  平行工具呼叫有 thread 損毀案例。→ 若換模型／換 provider，必須重跑一次本節的 CUA 小實驗。
- 隱私：BYOK 時 LINE 畫面文字與截圖會送往該供應商（本例 Ollama Cloud），與 OpenAI 的資料路徑不同。

### 6.2 執行環境

`codex` 預設 `model = "gpt-5.6-luna"`、`model_reasoning_effort = "xhigh"`；`[features]` 只有 `js_repl=false`；
`codex features list`：`computer_use stable true`、`browser_use stable true`；
`[mcp_servers.computer-use] enabled=false`（舊路徑），實際由外掛 `.mcp.json` 提供 `cua_repl`（enabled）。
`node_repl` MCP server 指向 ChatGPT.app 的 `cua_node/bin/node_repl`。

## 7. 為什麼目前的「自動化測試」還不足以聲稱安全（R1–R7）

以下已由 2026-09-16 高階主代理讀過程式確認（細節見封存舊檔 §4；本節是必須落地的清單）：

- **R1 正常路徑 crash window 未被覆蓋**：`transaction.resume()` 只在測試旗標分支先寫 UNKNOWN barrier，
  正常分支先 `_dispatch(ns)` 後才 `_commit_payload()`。真實 crash 無法預告旗標 → 保存狀態可能再次 dispatch。
- **R2 新程序載入 intent 仍可 dispatch**：以 run/owner/revision＋`INTENT_COMMITTED` 判定，owner 字串不是執行連續性證據；
  Case01 本身用「不同 subprocess prepare→resume」，把違約行為當 happy path。`state-contract.md` 只允許
  「剛完成 intent write/read-back 的同一不中斷 caller」做原始一次 dispatch。
- **R3 prepare 前置檢查不足、duplicate gate 可被新目的地繞過**：`_base_run()` 一律填 `[1,1]` calibration、HIGH、
  `source_provenance='test fixture'`、`destination_initially_empty=True`；`duplicate_check()` 額外要求 destination 相同，
  同群同 fingerprint 換目的地會漏過，也未檢查歷史 unresolved intent 或同日期改 count。
- **R4 finalize 信任任意 JSON 宣稱 VERIFIED**：只讀 `--verification-json`，不驗來源、實際檔案、target/run 關聯；
  新增 entry 也缺少 verifier 要求的 `source_authority='authoritative_exact_join'`。→ 沒有真正從新交易到 verify-only 的整合閉環。
- **R5 verifier 來源與讀取缺口**：`_association()` 以 `source_authority` 魔法字串作來源肯定，未讀原始證據；
  `inspect()` 的 `read_error` 只看 `samples[0]`；`file --mime-type`＋hash 不是完整影像解碼。
- **R6 status fixture 自證＋測試互刪證據**：`status.evaluate()` 依 `scenario` 查固定 tuple（`done` 直接 ACHIEVED/PASS/DONE）；
  `authority_negative_driver.setup_case_roots()`、`test_transaction_core.py` setup/teardown 都會刪共用 `case-01..12` root
  （Case12 消失的直接來源），根因是測試 ownership 不隔離。
- **R7 產品宣稱超過實際流程**：README 明寫沒有任何命令 dispatch LINE Save All；`_dispatch()` 只是外部腳本介面；
  GUI 來源辨識、chooser、download polling 與 transaction engine 從未形成真實 workflow。

**共同根因**：「如何讓測試通過」取代了「使用者備份如何成功」：測試預設成功事實、故障旗標改變待測安全行為、
缺少反例與端到端關聯。修復必須回到可觀察副作用、來源、檔案與狀態。

## 8. 自動化測試流程步驟邏輯（本檔核心）

每個 Phase 都必須先寫下：**主張 → 真正受測入口 → 外部可觀察 oracle → 結果如何改變下一步**。
不寫清楚就不准跑。所有 attempt append-only，永不覆寫既有證據。

### Phase 0 — 前置核對與唯讀基線（不可跳）

進入條件：無。這是第一個動作。

```bash
cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
git status --short                      # 先看 untracked / 髒檔，不得覆蓋使用者既有工作
PYTHONPATH=src /usr/bin/python3 -m line_backup_acceptance --help
/usr/bin/python3 tests/authority_baseline.py \
  --config  "$DATA_CONFIG" --state "$DATA_STATE" --run-log "$DATA_LOG" \
  --destination "/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57" \
  --output evidence/<new-attempt>/baseline-pre.json
```

- oracle：57 個 regular file、17,924,900 bytes、`image/jpeg`；config／state／run-log 三個 hash 與 §4 相同
  （config `390cbdcf…`／state `e9313a56…`／run_log `a62dd07d…`）；任一不符即停下回報差異。
- 證據：argv（去秘密）、stdout/stderr、exit code、baseline JSON、SHA-256/bytes 清單。
- 停止條件：任何 hash 不符或檔案數不符 → 先當 `[OBSERVED]` 差異回報，不得自行「修正」正式資料。

### Phase 1 — 隔離與封存（先保護舊證據）

- 把要重跑前會受影響的既有 evidence **複製**（不搬移、不刪除）到新 attempt 目錄，記錄 SHA-256 與 bytes。
- 新 attempt 目錄命名：`evidence/<YYYYMMDD>-<topic>/attempt-NN/`；同一份檔案只有一個 writer。
- 停止條件：發現 driver 會刪共用 root（R6）→ 先封存再跑，且**不得同時**執行兩套 driver。

### Phase 2 — R1–R7 focused reproduction（用真正入口，不用預告旗標）

| 缺口 | 最小重現（受測入口） | 通不過就代表 | 結果決定 |
|---|---|---|---|
| R1 | 正常 adapter 寫一次獨立 side-effect counter，於副作用前／commit 前後由**父程序硬中斷**，再 fresh resume；不設 `--crash-after-dispatch` | 恢復路徑會重送副作用 | counter 增加即阻止 production，修 barrier/continuity |
| R2 | `prepare` 程序退出後，以相同 owner/run/revision 的**新程序**呼叫 `resume` | 安全行為靠呼叫端旗標 | 未帶安全旗標仍不得 dispatch |
| R3 | 同群同 fingerprint 改 destination；未解的 SAFE_ABORT intent；同日期改 count；多筆歧義；production 帶 fixture flags | 真正入口沒有前置安全檢查 | 副作用前即拒絕，且不動正式檔案 |
| R4 | 自製「假 verification JSON（PASS/57、無實際檔案）」→ 試圖 finalize 成 VERIFIED | 任意 JSON 可新增 registry | 無效證據不得新增 VERIFIED；有效者需原子 commit＋read-back |
| R5 | 偽造 `source_authority`、錯 `verified_run_id`、非 terminal run、第 2/3 個 sample 讀取錯誤、截斷但 MIME 正常的圖 | 來源可被字串升格、讀取錯誤被吞 | 依契約分類為 UNKNOWN/INPUT_NEGATIVE，不得 PASS |
| R6 | 任意順序／並行重跑 unit、authority、transaction、verifier、status drivers | 證據互相刪除 | 不互刪、不覆寫；完成後每個 manifest 可獨立 SHA/bytes 讀回 |
| R7 | fake GUI adapter 只替換外部 I/O，跑「新交易→finalization→verify-only→重複執行」整合 | 產品宣稱超過實際流程 | source/registry/intent/owner 與真實檔案相符；不得只保存 PASS 常數 |

證據規則：每個 attempt 保存完整輸入、argv/env（去秘密）、stdout/stderr/exit、受測程式 hash、
**獨立** side-effect counter、前後 state 與 artifact manifest（SHA-256＋bytes）。
`/private/tmp` 不得當長期保存；required artifacts 必須有 durable copy。

### Phase 3 — 流程升級（語意變更的唯一合法路徑）

只要要動：安全語意、required/optional、validity、gating/veto、錯誤語意、fallback、priority、failure propagation，
或新增架構／契約／migration／root-cause 決策 → 依 CRITICAL：

1. 更新**同一任務**的 `plan.md`（`PLAN_REVISION` 遞增，只改受影響決策）。
2. 真正 fresh 的獨立 plan review（`.agent/tasks/<TASK_ID>/review/attempt-NN/`，append-only）。
3. 重新編譯 `handoff.md`（舊版先封存）。
4. fresh implementer 執行；實作期間若再遇到語意問題 → `escalation.md` + replan。

任何舊批准（含 Rev13 與 `review/attempt-16`）**不得**沿用於新修復。

### Phase 4 — 最小完整修復

- 只修 Phase 2 證實的缺口；能用最小 diff 就別重構。
- 不得為了讓測試通過而改測試期望、放寬 authority allowlist、或新增 fixture 專用後門。
- `status` 模組若無法從真實流程事實產生結果，就依 plan 明確降級為非驗收展示工具，**不要**擴建框架。

### Phase 5 — 回歸 + 真正的整合（fake adapter 的合法邊界）

- 回歸只跑受變更影響的測試 + 風險適當的廣度；不無限重跑全套。
- fake adapter 只能模擬**外部 I/O 與計數**，不得替產品決定 UNKNOWN、寫 barrier、製造 VERIFIED、充當來源證據。
- 必須記錄 test-mode 與 production 共用哪些程式分支。

### Phase 6 — GUI 觀察（需要 Human Gate；B2）

- 先核對 ledger：歷史 ellipsis 額度已用盡，本檔不新增額度。
- 完成所有無 GUI 前置工作後，**一次**提出精確 gate（見 §5 B2 與 §10）。
- 執行時：fresh 肯定辨識 → 恰好一次被批准的 ellipsis → 立即 post 證據 → 停止。
- 禁止：AXPress、`AXUIElementPerformAction`、AX write、猜座標、OCR-only 通過、任何 sandbox workaround。
- 陰性結果只定位「觀察缺口」，**不等於**證明 bridge 是必要的。

### Phase 7 — 獨立驗收與結案

- `INDEPENDENT_ACCEPTANCE_REQUIRED: YES`（本任務屬 CRITICAL）→ 用 `e2e/attempt-NN/`，append-only，verifier 不改產品碼。
- 先驗 `CORE` acceptance，再談其他；`E2E_REQUIRED: YES` 時必須真的執行使用者旅程（或明確標示替代層級）。
- `result.md` 只在最後由 closing role 寫；本輪的 `execution.md`/`result.md` 不得被覆寫。
- 正式 `verify-only` 只在必要修復後跑一次（讀 `EXISTING_DEST` + 選定正式 authority，前後 baseline）。
  **既有有效 57 張永不為測試重下載。**

## 9. 測試案例矩陣（優先序由高到低）

1. 正常路徑意外中斷 → fresh resume 的副作用 counter 不得增加。
2. loaded intent → 新程序不得靠「沒給安全旗標」才安全。
3. 重複與歷史 intent → 真正交易入口拒絕，換目的地／清 owner／新 run ID 都不得繞過。
4. 前置條件與 test/prod 隔離 → 非空、symlink、outside destination、虛構 calibration、缺來源都要在副作用前拒絕。
5. 真假 verification → 空目錄、FAIL/UNKNOWN、篡改 hash、錯 run/source 不得新增 VERIFIED。
6. 真正流程整合 → 同一實際核心、新交易到 finalization、再 verify-only、再重複執行。
7. 並行與儲存故障 → 一個 winner、stale writer、owner mismatch、read-back 不確定、terminal 後遲到寫入。
8. 檔案負向 → 真實 56/58、零 bytes、partial、hidden、不明檔、symlink、特殊檔、任一 sample 讀錯、內容/mtime 改變。
9. 影像完整性 → 用可用 decoder 完整讀取 fixture 與需核對的既有圖片（只讀）；截斷但 MIME 正常者作反例。
10. 來源/registry → 錯 `verified_run_id`、非 terminal run、偽造 `source_authority`、cross-entry、legacy 缺資料、禎/楨未證實。
11. harness 保留 → 任意順序與並行重跑後，所有 manifest 可獨立讀回。
12. 正式 verify-only → 修復後一次讀取，前後 baseline；來源未知單獨標示。
13. GUI observation → 取得授權後依當前 documented runtime 執行；陰性只定位觀察缺口。
14. 真實備份 acceptance → **僅**在確有下載必要且 gate 有效時：一次真實來源 → Save All → chooser → 安全新目的地 → 驗證 → commit。

## 10. 邊界、禁令與 Human Gate

- 使用者只做「不可自動完成」的事：OS 權限／登入／安全政策、缺失的目標身分、必要的 GUI 觀察額度、
  首次正式下載授權。**不要**要求使用者做 Terminal diagnostics、反覆重裝、反覆重加權限。
- **不要執行會觸發管理員／授權密碼視窗的命令**（例如 `sfltool dumpbtm`、`sudo`、TCC 相關工具）。
  2026-09-16 曾因 `sfltool` 連續觸發授權視窗，使用者已明確要求避免。
- 正式 state/intent/registry/config/run-log 與 57 張照片維持唯讀；dispatch 不明不重送；錯相簿立即終止。
- 來源問題只用**一次**精確問題解決，允許使用者答「不知道」；保存原問題、原答、時間與證據 SHA-256。
- 若真的需要下載：新目的地必須是從正式 config 導出的全新、空、安全絕對路徑；`EXISTING_DEST` 非空，
  不得覆寫或改名規避 duplicate barrier。

## 11. 證據索引與版本錨點

- `evidence/20260915-verify-only-57/`：舊 verifier 與 inventory；舊腳本 56/58 假陽性已重現。
- `evidence/20260916-acceptance/attempt-02/`：verifier/authority/status summaries、literal manifest、
  legacy false-positive summary、`transactions/case-01..12/` durable copies。
- `evidence/20260916-baseline/attempt-01/baseline-pre.json`：19005 bytes／`ab6747f2…`（歷史值，接手需重新讀回）。
- `evidence/20260916-product-verify/attempt-03/`：正式唯讀 argv/stdout/stderr/exit/inventory/reconciliation。
- `evidence/20260916-route/attempt-01/route-decision.json`：3420 bytes／`90c2d650…`（歷史 GUI ledger，非現 runtime 實測）。
- `evidence/20260916-cua-cli-proof/`：本回合 CUA 活證、截圖、BYOK 圖片路徑探針（見該目錄 README）。
- `evidence/20260916-user-fact/`：禎／楨 來源身分使用者事實（2026-09-16；原問題、原答「正確是「禎」」、
  時間、唯讀複核 hash；見該目錄 README）。
- `CURRENT_TASK/e2e/attempt-02/` REJECTED（保存錯 56/58 與遺失 artifact）；`attempt-03/` scoped acceptance。兩者都不得覆寫。

## 12. 完成定義與狀態語意

分開報告：`PRIMARY_OUTCOME_STATUS`、`IMPLEMENTATION_STATUS`、`CORE_ACCEPTANCE_STATUS`、
`REQUIRED_VERIFICATION_STATUS`、`INDEPENDENT_ACCEPTANCE_STATUS`、`TASK_CLOSURE_STATUS`。
`Done` 只代表整體結案。`IMPLEMENTATION_BLOCKED` 只保留給「產品實作未完成且無法安全繼續」。
required verification 未完成不得抹去已證實的實作/CORE 事實；反之，實作完成不得冒充 CORE acceptance。

## 13. 升級條件（什麼時候必須交給高階模型）

指名交由高階模型（目前 runtime 為 GPT-6 Astra；不可用時明報並要求）：

- 無法同時滿足「同一不中斷執行 dispatch」「crash recovery」與當前 CLI/GUI transport，且需要改安全／持久化／authority 契約。
- 來源／歷史 intent 證據互相矛盾，無法提出安全且最小的 reconciliation。
- 相同根因兩次實質修復仍失敗，或獨立審查再次發現測試自證、正式副作用遺漏、跨測試污染。
- 無法判斷 bridge 必要性，或 runtime/skill 的能力契約衝突會改變可執行路徑。

升級包必須含：最小重現、原命令/stdout/stderr/exit、受測版本與 hash、失敗 attempt、假設／反證、
以及要求高階決定的**單一問題**。高階分析不是獨立驗收的替代品。

## 14. 可直接貼入新對話的 /goal

完整文字同步存放於 `WORK/GOAL-next-conversation.md`（以該檔為準，避免複製誤差）。

```text
/goal

請完整讀取 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff.md（H2.1）與其中的路徑表，然後接手執行。

目標：把 LINE 群組「旻謙允禎成長日記」相簿「2024/05/13～05/17」57 張的備份流程做「自動化驗證」——
用真正入口重現並修好 R1–R7，產出可重跑、可獨立複驗的證據，而不是增加 PASS 數字。有效既有 57 張
優先 verify-only，永不為測試重下載；正式 config/state/run-log/照片全部唯讀。

三個結果分開報告：本相簿資料結果、可重用自動化能力、整體結案。

依 handoff §8 的 Phase 0→7 執行；任何安全／持久化／成功語意變更都走 CRITICAL：更新同一任務 plan
（PLAN_REVISION 遞增）→ 真正獨立 review → 重新編譯 handoff → fresh implementer。舊批准不得沿用。

兩個 blocker 只有兩個合法解法：來源身分（禎 U+798E vs 楨 U+6968，禁止合併）需 authoritative join 或
一筆精確保留的使用者事實；GUI 需要一次精確的觀察 gate（只授權一次 current-target ellipsis 觀察，
不授權選單項／Save All／chooser／鍵盤／state 寫入／下載）。

禁止 AXPress、AXUIElementPerformAction、AX write、猜座標、OCR-only 通過、sandbox workaround；
不要執行會觸發管理員授權視窗的命令（如 sfltool）。工具不可用就明報，不假裝已升級。
```
