# LINE 相簿自動備份：給 GPT-5.6 Luna 的交接

日期：2026-09-16。這是新對話的使用者目標與事實交接，不是 production 授權，也不是已批准的 Stage03 handoff。本輪工作是唯讀根因分析及文件修正；沒有修復或重新動態驗證產品程式。文末提供可直接貼入新對話的 `/goal`。

## 1. 唯一主軸與完成定義

完成 LINE `jp.naver.line.mac` 群組「旻謙允禎成長日記」、相簿「2024/05/13～05/17」、57 張的安全自動備份；本輪最多此一相簿。已有有效備份時採 verify-only 加來源／既有登錄核對，禁止為驗收而重下載。只有證明需要下載且取得精確 production gate，才做一次真實下載。

備份成功必須同時有：正確来源、完整檔案、正確目的地、可信 state/registry/intent 一致性、可重用中斷恢復與重複防護、必要独立驗收。主軸是實際備份結果，不是寫更多測試、讓 bridge 啟動、取得更多 PASS 或完成文件。

分開報告三個結果：

1. **本相簿資料結果**：來源已確定且既有 57 張與歷史登錄相符，可透過 verify-only 完成核對；不為補欄位偽造新的 VERIFIED run。
2. **可重用自動化能力**：實際執行路徑安全、恢復不重送、關鍵驗證有獨立證據。尚無 GUI 真實執行時，必須標為未證實的部分。
3. **整體任務結案**：本相簿結果及使用者要求的可重用能力都達成；否則分項未完成。新下載不是有效既有備份的必要條件。

CORE：來源、檔案、狀態、至多一次 dispatch、恢復、防重複、必要獨立驗收與目前 runtime 選路。SUPPORTING：只有證明必要才修 bridge/service。BEST_EFFORT：全面歷史整理、通用框架、額外相簿與無關測試。不要把 SUPPORTING 失敗變成檔案驗證的全域否決。

## 2. 權威位置與最小載入

以下為明列路徑，不允許以 cwd 或搜尋到的其他 root 替代正式 authority：

| 名稱 | 絕對路徑 |
|---|---|
| WORK | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup` |
| DATA_PROJECT_ROOT | `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state` |
| DATA_CONFIG | `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json` |
| DATA_STATE | `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json` |
| DATA_LOG | `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/run_log.md` |
| EXISTING_DEST | `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` |
| CURRENT_TASK | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance` |
| SKILL | `/Users/hsiaojohnny/.codex/skills/line-album-backup/SKILL.md` |

先完整讀本文件、適用 AGENTS、SKILL 與本階段要求的 references。再讀 WORK 的 `src/line_backup_acceptance/{transaction,verifier,authority,common,cli,status}.py`、必要測試和 CURRENT_TASK 的 plan/review/handoff/result。只依引用追原始證據，不掃描全部歷史任務。GUI 工作之前另完整讀 evidence、state-machine、ui-procedure 及 runtime 當場提供的 API 文件。

WORK 尚有大量 untracked files；修改前讀 git status，保留它們。正式 root、照片、state/intent/registry/config/log 目前均只授權唯讀。WORK 可做必要修復、準備與隔離測試；sandbox 另有約束，不能繞過。

舊根目錄 handoff 已原樣存至 `WORK/evidence/20260916-handoff-root-cause/attempt-01/handoff-before.md`。CURRENT_TASK 的 plan/handoff/review/result 未覆寫。它們保存歷史判斷，本文件的新程式發現要求重新審查其「implementation complete」推論。

## 3. 可以保留的證據，以及不能承接的結論

歷史獨立驗收 `CURRENT_TASK/e2e/attempt-03/review_report.md` 結果為 ACCEPTED_WITH_SCOPED_BLOCKER，記錄 verifier 28/28、authority 11/11、status 18/18、transaction 12/12。這些測試與報告確實存在，但不證明第4節未測路徑安全，不能直接沿用成 production readiness。

最近正式唯讀 reconciliation：`WORK/evidence/20260916-product-verify/attempt-03/reconciliation.json`。報告記錄 57 個 regular files、17,924,900 bytes，filesystem PASS；registry FAIL、source UNRESOLVED、state LEGACY_PROVENANCE_LIMITED、overall UNKNOWN、exit 4。baseline UNCHANGED。本轮没有重新读取全部照片或运行 formal verification，不把历史观察改称当前实时结果。

正式 config/state 使用「旻謙允**楨**成長日記」，使用者指定「旻謙允**禎**成長日記」。来源尚未闭合；不能合併字串、改 canonical key、用同日期/count/hash 推斷同群。先查既有原始來源，仍無法決定才問一次精確事實。只確認名字對應也不必然證明這 57 個檔案來自那個相簿，必須保留來源鏈的範圍與強度。

歷史 state revision=39，current_run_id、active_writer_id、context_lock 為 null；57 張 entry 關聯 `RUN-20260907-154331-01`。legacy 缺欄位不得自動初始化成成功或未 dispatch；仍須檢查所有相關歷史 intent。

原始 menu ledger 的索引在 `WORK/evidence/20260916-route/attempt-01/route-decision.json`，引用：
`/Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/outputs/20260913T141849Z-menu-discovery-0d9a87b5-cef1-4815-b886-ccdb34fa803b/actions.jsonl`。
歷史 ellipsis 額度 2/2；menu-item、Save All 為0。當時 menu/AX 證據不足，不能推論現在 runtime 必然不支援，亦不能推論 bridge 必要。新對話不得因模型切換重置額度。

## 4. 本輪第一性原理根因：靜態程式直接證據

下列是2026-09-16讀取現行程式所得。**已確認程式結構缺口；尚未以新隔離 subprocess 重現事故。** Luna 必須先建立可區辨重現，再改程式；不得把「風險可推導」寫成「已發生重複下載」。

### R1. 正常路徑的 crash window 沒被故障測試覆蓋

`transaction.resume()` 只在 `crash_after_dispatch` 或 `dispatcher_outcome == UNKNOWN` 這些預設測試旗標分支，先持久化 UNKNOWN barrier。正常分支先 `_dispatch(ns)`，成功後才 `_commit_payload()`；正常 adapter 例外也可能留下原 `INTENT_COMMITTED`。真實 crash 無法預告測試旗標。

因果鏈：正常副作用發生 → 程序在 barrier 寫入前失敗 → 儲存狀態仍可被 resume 判定可 dispatch → 再次副作用風險。根因是安全行為依賴預告失敗，而非所有真實路徑共用同一副作用邊界。

### R2. 新程序載入 intent 仍可 dispatch，違反既有 skill

`resume()` 以 run/owner/revision 與 `INTENT_COMMITTED` 判定，未證明是剛提交 intent 的同一不中斷執行。owner 字串不是執行連續性的證據。Case01 本身用不同 subprocess prepare → resume；這會把違約行為當成 happy path。

`state-contract.md` 已明定：只有剛完成 intent write/read-back 的不中斷 caller 可做原始一次 dispatch；新 session 的 loaded intent 只可 reconciliation。修复必须让真正新交易在同一执行拥有原始 dispatch 权限，resume 不从 persisted 字串重建权限；不提出不必要的分散式 exactly-once 設計。

### R3. prepare 沒有真正前置安全檢查；重複 gate 可被新目的地繞過

`_base_run()` 無論 production/test 都填 `[1,1]` calibration、HIGH、`source_provenance='test fixture'`、`destination_initially_empty=True`。`prepare()` 主要檢查 active ownership，未整合已備份 fingerprint、歷史 unresolved intent、destination 真實空目錄、fresh source/calibration。

`duplicate_check()` 的 match 額外要求 destination 相同；同群同 fingerprint 換 destination 會漏過，也未檢查歷史 unresolved intent 或同日期改 count 的 reconciliation。獨立 CLI 可被略過，必須在真正交易入口及 commit 邊界落實安全判斷。

### R4. finalize 能信任任意 JSON 宣稱 VERIFIED

`commit()`、`finalize()` 只讀 `--verification-json`，未驗其來源、實際檔案、target/run 關聯或結論。`finalize --outcome VERIFIED` 就新增 registry。現有 case driver 自行建立含 PASS/57 的 verification JSON，目的地沒有實際圖片；此測試僅證明欄位寫入，不證明有效備份。

另外 finalize 新增的 entry 沒有 verifier 所要求的 `source_authority='authoritative_exact_join'`，沒有一條真正從新交易到 verify-only 的整合閉環。不能單純補該字串來過測試，必須驗證對應原始來源證據。

### R5. verifier 仍有來源與讀取錯誤缺口

`verifier._association()` 以 entry 的 `source_authority` 魔法字串作來源肯定，未讀取驗證其原始證據；未充分檢查 `verified_run_id` 與唯一候選 run、terminal outcome、owner/intent 一致。

`inspect()` 的 `read_error` 只檢查 samples[0]；第2/3次讀取錯誤可能被當一般 INPUT_NEGATIVE/4，與內部錯誤 UNKNOWN/1 契約不同。`file --mime-type` 加 hash 也不是完整影像解碼，不能聲稱已證實無截斷或原始畫質。

### R6. status fixture 的自證與證據保存互相污染

`status.evaluate()` 按 `scenario` 查固定 tuple；`scenario='done'` 可直接得到 ACHIEVED/PASS/DONE。18/18 最多驗映射，不能當整體備份驗收證據。應從實際流程事實產生結果，或將此模組降為非驗收展示工具，經 plan 明確決定；不要擴建不必要 status framework。

`authority_negative_driver.setup_case_roots()` 刪除共用 case-01..12；`test_transaction_core.py` setup/teardown 刪除 case-12；verifier/case driver 同樣重用並刪除 case root。因此 Case12 消失有兩個直接來源，並非單純 tmp 被系統清除。調執行順序只是暫時補救。根因為測試 ownership 不隔離且保留策略依賴慣例。

修復方向：每次 attempt 的唯一 workspace、fixture roots 明確注入且保持正式 authority 隔離、不得清除別套測試或歷史 attempts。現有 hard-coded fixture allowlist 的修改若影響 authority 必須 CRITICAL review；不要為測試直接解除限制。

### R7. 產品宣稱超過實際流程

README 明寫沒有命令 dispatch LINE Save All；`_dispatch()` 只是外部腳本介面。尚未證實 GUI 來源辨識、chooser、download polling 與 transaction engine 形成真實 workflow。現有機械測試、manifest hash 與獨立 review 都無法补證缺席的真實路徑。

根本問題是「如何讓測試通过」取代「使用者備份如何成功」：測試預設成功事實、故障旗標改變待測安全行為、缺少反例與端到端關聯。修復必須回到可觀察的副作用、來源、檔案與狀態，不再追 PASS 數量。

## 5. 接手順序與自主範圍

1. 核對程式/hash、正式 authority、既有原始來源與 ledger。建立一張短表：使用者結果 → 目前證據 → 尚缺證據 → 最小下一步。不得因過往 blocked 直接要求人類。
2. 先隔離並保存舊證據，再準備 R1–R6 的 focused reproductions。不得直接重跑會刪除共用 root 的舊 harness。每個 attempt 保存完整輸入、argv/env（去秘密）、stdout/stderr/exit、受測程式 hash、獨立 side-effect counter、前後 state 與 artifact manifest。
3. R1–R5 涉安全／持久化／成功語意，現有 Rev13 approval 不足以批准修復。依 CRITICAL 更新目前任務的 plan revision、真正 fresh independent review、保存舊 handoff，再由 fresh implementer 執行與獨立驗收。不能主審兼自評，也不能只改測試期望以迎合目前實作。
4. 本轮高阶分析已发现上述缺口；Luna 对明确局部修复可自主执行。遇下节升级条件立刻交由高阶模型，勿连续试错或先宣称「不需要」。例行 reviewed 实作无需反复请求用户批准。
5. 精簡閉環：入口實際前置檢查 → 同次執行 intent/原始一次副作用 → chooser/目的地 → 下載穩定驗證 → guarded terminal commit/read-back → 第二次執行 SKIP，不重點。verify-only 是優先資料完成路徑，不能為此強迫下載或遷移 legacy。
6. 獨立完成所有無 GUI 依賴工作，再為仍必要的 GUI 試驗準備具體操作與一次 Human Gate。獲得必要證據／授權就繼續，不再詢問相同問題。

## 6. 自動化測試範圍、目的、分支

每個測試先寫「主張、真實受測入口、外部可觀察 oracle、結果如何改變下一步」。優先下表，相關修復後一次風險適當回歸；不無限重跑全套。

| 測試 | 必須實際驗證什麼 | 結果決定 |
|---|---|---|
| 正常路徑意外中斷 | 不開 crash flag；正常 adapter 寫一次獨立 counter 後硬中斷父程序，在實際副作用前後/commit 前後可控邊界重啟 | fresh resume 的 counter 必不增加；增加即阻止 production，修 barrier/continuity |
| loaded intent | prepare 程序退出，再以相同 owner/run/revision 的新程序呼叫 resume，不能靠 `--no-dispatch` 才安全 | 即使呼叫端沒給安全旗標也不 dispatch，否則流程未完成 |
| 重複與歷史 intent | 同群/fingerprint 改目的地；SAFE_ABORT 未解決 intent；同日期改 count；多筆歧義 | 真正 prepare/開始備份入口拒絕；清 owner、新 run ID 或新路徑不得繞過 |
| 前置條件與 test/prod 隔離 | 非空、symlink、outside destination；虛構／過期 calibration；缺来源；production 帶 fixture flags | 副作用前拒絕且不改正式檔案；不能用 fixture HIGH 通過 |
| 真假 verification | 真圖 fixture 由實際 verifier 得出資料；空目錄、FAIL/UNKNOWN、篡改 hash、錯 run/source 的 JSON 試圖 finalize | 無效證據不能新增 VERIFIED/registry；有效可原子 commit/read-back |
| 真正流程整合 | 同一實際核心、新交易到 finalization、再 verify-only、再重複執行；fake GUI adapter 只替換外部 I/O | source/registry/intent/owner 與真實檔案相符；不能只保存測試的 PASS 常數 |
| 並行與儲存故障 | 一個 winner、stale writer、owner mismatch、寫入/replace/read-back 不確定、terminal 後遲到寫入 | 任一違反即修正；不確定保留 UNKNOWN，不重送 GUI |
| 檔案負向 | 真實56/58、零bytes、partial、hidden、不明檔、symlink、特殊檔、任一 sample 讀錯、內容/mtime 改變、特殊檔名 | 正確拒絕／UNKNOWN 分類；計數與manifest由獨立讀回驗證 |
| 影像完整性 | 先用已可用 decoder 完整讀取 fixture 和需要核對的既有圖片，保持只讀；截斷但 MIME 正常的圖作反例 | 解碼失敗不能稱完整圖片；依賴不可用則明列未驗證，不擅自安裝 |
| 來源/registry | 错 `verified_run_id`、非 terminal run、偽造 source_authority、cross-entry、legacy缺資料、禎/楨未證實 | 不能把字串或相似名稱升為 source CONFIRMED；精確證據解決才前進 |
| harness 保留 | unit/authority/transaction 次序任意、重跑／並行不同attempt | 不互刪、不覆寫既有證據；完成後所有 manifest 可獨立 SHA/bytes 讀回 |
| 正式 verify-only | 必要修復後一次讀取 EXISTING_DEST 和選定正式 authority，前後 baseline | 已有有效57張保持不重下載；來源仍未知單獨標示 |
| GUI observation | 取得授權後依當前 documented runtime，fresh target→一次允許操作→post證據 | 確認真正 Save All/幾何才具備該路徑；陰性只定位觀察缺口，不等於 bridge 必要 |
| 真實備份 acceptance | 僅確有下載必要且 gate有效時：一次真實來源→Save All→chooser→安全新目的地→驗證→commit | GUI關閉不算完成；檔案及state/read-back成立才 VERIFIED，未知不重送 |

測試可用 fake adapter，但它只能模擬外部回應／計數副作用，不能替產品決定 UNKNOWN、寫 barrier、製造 VERIFIED 或充當來源證據。記錄 test-mode 與 production 共享哪些程式分支；不以 test-only 成功推論 LINE E2E。

## 7. GUI、來源與 production 的精確授權邊界

本文件及新的 `/goal` 不新增 GUI 額度、不授權正式 state mutation 或下載。使用者原指令要求先核 ledger、所有自動前置工作完成後才問一次精確試驗授權。尚無答覆，不能當已批准。

來源問題用普通中文問一次：請使用者指出 LINE 中目標群組的實際名稱，以及既有目錄是否確實是該群這個日期、57張相簿的備份；允許「不知道」，不要要求說出 exact join 等術語或誘導同意合併。保存原問題/原答覆/時間/證據範圍，不能自動改正式 key。

GUI gate 必須分清純觀察與點擊：ellipsis 是可逆 GUI input，不是唯讀。如果不能在已授權證據中確定目前正確畫面，先把所需初次 snapshot、有限導覽／開相簿及點擊額度明列；不要要求使用者先手動把相簿開好來掩蓋自主導覽缺口。導覽持久化若 skill 要求，事先界定 state write 權限，不能同時承諾零 state write 且執行須寫 checkpoint 的動作。

試驗目標必須是本 app/群/相簿/57，fresh 肯定辨識後最多一次被批准的 ellipsis，取得 post evidence 後停止；不點菜单项/Save All，不進 chooser，不下載。實際工具能力由新 runtime 文件決定，禁止猜 API、猜座標、AXPress、AXUIElementPerformAction、AX write、OCR-only 通過、sandbox workaround。

若既有57張完整有效，永不為 GUI 測試重下載。若確有必要下載，先完成 reviewed 修復、來源、destination安全檢查及回復方案，最後一次提出 production gate：精確群組/相簿/57張、從正式 config 導出的全新空安全絕對目的地、唯一一次下載、明列正式 state/control write set。EXISTING_DEST 非空，不能覆寫或另名規避 duplicate barrier。Save All 不確定不重點，錯相簿終止。

不要要求使用者 Terminal diagnostics、反覆重裝或重加權限。只有實驗證明 bridge 缺口是必要因果條件，才準備一次已審查、可回滾部署；服務正常不代表選單成功。

## 8. 指名高階模型介入的條件

Luna 每輪有意義的工作回報：目前瓶頸、事實／未決假設、下一個可區辨實驗、是否需高階介入。不要每個命令都重複口號。

下列情況必須指名「交由高階模型 GPT-6 Astra（當前 runtime 若無此型號，明報不可用並要求可用高階模型）」：

- 無法兼容同一 uninterrupted execution dispatch、crash recovery 與當前 CLI／GUI transport；需要改安全／持久化／authority 契約。
- 來源／歷史 intent 證據互相矛盾，無法提出安全且最小的 reconciliation。
- 相同根因兩次實質修復仍失敗，或独立审查再次发现测试自证、正式副作用遗漏、跨测试污染。
- 無法判斷 bridge 必要性，或者 runtime／skill 的能力契約衝突會改變可執行路徑。

能依既有證据局部修復、以及純缺使用者來源事實/GUI授權，不必為了「更強」無故升级。升级包必含最小重現、原命令/stdout/stderr/exit、受測版本與hash、失敗attempt、假設/反證、要求高階決定的單一問題。高階分析不是獨立驗收的替代品。

目前已由高階主代理深讀並識別 R1–R7；Luna 接手先驗證與落地，不必重新討論是否存在已讀到的程式分支，也不可假裝这些問題已修好。若高階工具不能用，先完成其他已授權工作，精確回報能力缺口；不建立使用者新對話冒充 subagent。

## 9. 證據索引與版本錨點

路徑相對 WORK；本輪讀回下列程式／task digest：

| 檔案 | bytes | SHA-256 |
|---|---:|---|
| src/line_backup_acceptance/transaction.py | 13835 | c486edbeaa483fcc7ec5e6c2edf192a9f048aa5e99afdbbd513d2028e916ce13 |
| src/line_backup_acceptance/verifier.py | 15541 | b38ee6d5457a1a2f56917b403b05d95d499ff5518b22ab5ffe615326219dde29 |
| src/line_backup_acceptance/status.py | 7454 | 20a95f7c24c0d7371ab4bf1ecfb56b841f2c8e9ba999995aaa543305bb4f9c36 |
| src/line_backup_acceptance/authority.py | 8522 | a98964e374077d0bf7e81c8088a849c5d19fc9aa598ac02000f3bb414aec0f76 |
| src/line_backup_acceptance/cli.py | 4583 | a5bbbbf6bd6d39402660f219ed7732d41397a8c447716b9ddccac5c6ba1441a8 |
| src/line_backup_acceptance/common.py | 4021 | 59a85c47b80f0c80a9beab5e1c6b4f277232ff24da0b68c52ab0895ed73a5ac5 |

CURRENT_TASK plan Rev13 SHA `ad1ac6ac3cc5b63b5b6e1e48d8db525f556c680046abd026b7201680defb251a`；批准 `review/attempt-16/review_report.md`。Stage03 handoff SHA `60e51a62a9c52b9159b6a8a4a88a3fa07a39144406e68ae31131a91734d70a90`。歷史 result SHA `a89fa3e5da41ef1d5a6993423c8ff8080f33b8e5d51b7e749d5c1cceea86e179`。新修復不可沿用此 revision/hash 的批准。

原始及最近證據：

- `evidence/20260915-verify-only-57/`：舊 verifier 與 inventory；舊腳本56/58假陽性已重現。
- `evidence/20260916-acceptance/attempt-02/`：verifier/authority/status summaries、literal manifest、legacy false-positive summary、`transactions/case-01..12/` durable copies。
- `evidence/20260916-baseline/attempt-01/baseline-pre.json`：19005 bytes，SHA `ab6747f28b22557458baba2f38e9af6770257ce4cee27a26d78f3726761685b5`（歷史報告值，接手需讀回）。
- `evidence/20260916-product-verify/attempt-03/`：正式唯讀 argv/stdout/stderr/exit/inventory/reconciliation。
- `CURRENT_TASK/e2e/attempt-02/`：REJECTED，保存錯56/58與遺失artifact等發現；`attempt-03/` 是後來 scoped acceptance，均不得覆寫。
- `evidence/20260916-route/attempt-01/route-decision.json`：歷史GUI ledger、路徑未知與額度；不是現 runtime實測。

不得依賴 `/private/tmp` 長期保留。新 attempt 的 required artifacts 要有 durable copy、SHA-256、byte length 與可獨立讀回清單；失敗輸出也保留。已遺失原始內容不能補造。hash 一致只證明內容相同，不證明語意正確。

## 10. 停止與交付

交付真正可重用流程、必要修復、精簡操作說明、實際命令與原始證據、action ledger、inventory/hash、獨立plan review及acceptance。每個完成主張連到實際程式路徑與原始觀察。不要把 scenario DONE、offline PASS、文件或服務修復當 goal complete。

本相簿及可重用流程未有逐項證據時不 complete。遇外部必需輸入先完成所有不依賴它的工作，提出一次精確 Human Gate，說明來源是使用者既有授權限制。blocked 遵守當前 goal 工具三輪規則；新任務/恢復後重新計算，不能把同一turn內多次wait算多輪，也不要為達門檻空轉。

## 11. 可直接貼入新對話的 GOAL

```text
/goal

請使用 GPT-5.6 Luna，完整讀取並核對：
/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff.md

唯一目標：完成 LINE jp.naver.line.mac 群組「旻謙允禎成長日記」相簿「2024/05/13～05/17」57張的安全自動備份，本輪最多一相簿；有效既有57張優先verify-only，禁止為測試重下載。交付來源/檔案/state-registry-intent一致、可重用恢復与防重複、必要獨立驗收與目前runtime最短可靠選路。

本文件為交接輸入，不是批准。先對照第4節R1–R7的現行程式、skill與原始證據；歷史28/28、12/12、ACCEPTED_WITH_SCOPED_BLOCKER不能證明production安全。特別修正正常dispatch的crash window、loaded intent重新dispatch、改目的地繞duplicate、偽造calibration、任意verification JSON寫VERIFIED、scenario自證及測試互刪證據。先以實際受測流程重現，依CRITICAL plan修訂、真正獨立review/handoff後做最小完整修復；不得只改測試預期。正式資料目前保持唯讀。

自主完成已授權的唯讀核對、必要本地修復準備與隔離測試。每個測試說明結果如何改變備份下一步；保留所有attempt、原argv/input/stdout/stderr/exit、程式hash、獨立副作用計數、inventory、required artifacts的SHA-256/bytes。優先測正常路徑意外中斷與fresh resume，不靠預告故障旗標製造安全行為。修復测试隔離後再跑必要回歸，不反覆跑全套或擴張框架。

每輪評估瓶頸與是否需高階模型。安全/持久化/authority契約衝突、兩次同根因修復失敗、獨立審查再發現自證或無法判斷runtime/bridge必要性時，必須指名交由高階模型GPT-6 Astra分析，附最小重現與精確待決問題；工具不可用就明報，不假裝已升级。高階分析與獨立驗收分開。

核對「禎/楨」來源，不合併或改canonical key。先查來源證據，仍未知才一次精確事實問題。新GUI observation前核對ledger；本指令不新增GUI額度/正式state寫入/下載授權。完成所有自動前置工作後，為必要試驗一次提出具體觀察、有限導覽/ellipsis範圍與持久化權限。只有確實需要下載才請求精確群/相簿/57張/新空安全絕對目的地/一次下載及state write set的production gate；既有答覆授權有效則不重問。

禁止AXPress、AXUIElementPerformAction、AX write、猜座標、OCR-only通過、sandbox workaround；dispatch未知不重點Save All，保留正式state/intent/registry/照片與失敗證據。不要要求使用者Terminal diagnostics或無新證據重裝/重加權限。bridge只有必要性獲證才準備一次已審查部署。

分開報告本相簿資料結果、可重用自動化能力與整體結案。有效既有備份不以新下載作完成條件；offline測試不冒充GUI E2E。所有目標有逐項證據才goal complete；真正需外部輸入時精確Human Gate，依goal blocked規則停止空轉。
```
