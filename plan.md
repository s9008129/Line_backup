# plan.md｜LINE Agent 跨 Session 與 Mac 重啟接續備份

- **Task ID：** `AGENT-RESUME-P0-20261022`
- **版本：** v1.1／2026-10-22；承接本對話 v1.0 技術計畫。
- **需求基準：**《LINE_backup_PRD_Agent_Interrupted_Resume_v1.0_20261022.md》，SHA-256 `0d69c560490504f1b2af5466db680768e27924c4416c879d8c0545f1224a75d5`。
- **本階段產物：** 計畫與交接文件；產品實作、故障測試、LINE GUI、下載與新 E2E 均為 `NOT_RUN`。
- **指定 Planner：** `gpt-6.1-sol / xhigh`；目前工具未提供可獨立核對的模型／effort 執行收據，不冒稱 runtime attestation。

## 0. 本次 Owner 決策與適用順序

Owner 在本對話後續明確指示：本次不用外部獨立審查，將計畫實際落檔並交接 `deepseek-v4.1-flash:1017` 實作；無法解決的問題必須寫問題提報單，交高階模型分析；本輪以 GPT-6 luna 子代理梳理上下文及撰寫提交訊息，再 add／commit／push。

因此，本工作包可由 DeepSeek 直接依本計畫開始離線實作，不再等待原 v1.0 的外部 Plan／Handoff 審查。此次工作包不以外部 Chief 審查作新增執行前置；審查狀態記為 `OWNER_WAIVED`，絕不寫成 `APPROVE_PLAN`、`APPROVE_IMPLEMENTATION` 或獨立 review PASS。這是本次 Owner 的流程決策，不修改 AGENTS.md、Harness 或任何正式執行 guard，也不把豁免擴張到其他任務。

獨立實機 E2E、資料驗證、當次前景交接與新相簿下載授權沒有免除。實作者不能自填獨立 E2E PASS；實機仍由 Owner 另啟全新 DeepSeek Session。Git 交付授權不等於 GUI、Save All 或 Mac 重開機的當次授權。

本版相對 v1.0 僅變更角色、審查路線、文件落檔及阻塞提報要求；核心功能、安全不變條件和驗收標準不變。`handoff.md` 必須與本版一致，不能把原先待外部核准或 Luna 實作的文字留作有效指令。

## 1. GOAL / SCOPE / SUCCESS CRITERIA

### 1.1 目標與最小方案

保留 PR #28 已成功的 DeepSeek Computer Use、fresh screenshot、AX、Vision OCR、Save All、Chooser、SHA-256 與 ImageIO 流程，新增薄型恢復控制：

**有序任務清單＋單一原子 checkpoint＋跨 Session 防重送屏障＋唯讀 reconcile＋受控 GUI 包裝。**

Owner 已選定：

- 新 checkpoint 與新下載照片放在 `~/Library/Application Support/LineBackup/agent-resume/`，跨 worktree 使用同一個固定資料根目錄。
- 最小真實 E2E 使用兩本未備份的新相簿；第一本完整驗證後，由 Owner 重開 Mac，再以全新 DeepSeek Session 接續第二本。
- 既有照片保留原處，只建立唯讀參照。

### 1.2 P0 成功標準／Acceptance Criteria

| AC | 必須成立的結果 |
|---|---|
| AC-01 | 至少 100 本固定順序任務可跨程序／Session 恢復，不依賴舊對話。 |
| AC-02 | #50 從未 intent：核對前 49 本後可 fresh 定位 #50；#1～49 不重送。 |
| AC-03 | #50 完整下載但未提交 VERIFIED：重新驗證、持久提交後下一次 Save All 僅 #51；#1～50新增派送 0。 |
| AC-04 | #50 只有32／80或 dispatch不明：保留所有檔案，停止整個任務，#50～100不得自動派送。 |
| AC-05 | 重複請求、回覆遺失、程序崩潰與 Mac 重啟不解除 intent 屏障；單 writer成立。 |
| AC-06 | 兩本新相簿完成第一本→Mac重啟→新Session→跳過第一本→第二本；每本各一次Save All、完整SHA／ImageIO及checkpoint讀回。 |
| AC-07 | 歷史239／109／329與排除65張不重下載、不覆寫；正式State／Grant／Ledger／Harness不變。 |
| AC-08 | 最小diff、TC-01～20對應證據、來源／runtime hashes、完整報告與未解問題皆可追溯。 |

### 1.3 不做事項

不做相簿內續傳、強制重試、跳過 PARTIAL 後繼續、排程、開機自動執行、GUI 引擎重寫、正式 AUTO 修復、大範圍分支合併或歷史照片搬移。

功能名稱為 `AGENT_RESUMABLE_BACKUP`；不宣稱 `FORMAL_TWO_ALBUM_AUTO=PASS`。不以 Issue #25／#27 或正式 Authorizer、Grant、Ledger 作必要依賴。

## 2. SOURCE-VERIFIED BASELINE

### 2.1 已核對來源與證據邊界

以下是本次唯讀規劃的觀察，不代表產品功能已實作。

| 資產 | 核對結果 | 設計用途 |
|---|---|---|
| 本機原工作樹 | `v43-ab/codex-rev28`，HEAD `72dae704a9a5f3dbdee21e33178201350b6e7a06`；19項既存tracked修改及其他untracked資料 | 全部保留，不在該分支開發產品 |
| GitHub master | 本次讀回 `64515eb56b04accc40ade9e2db2fe0ad18c1ced3` | 乾淨文件交付與功能開發之共同祖先 |
| [PR #28](https://github.com/s9008129/Line_backup/pull/28) | 已關閉、未合併；HEAD如上；整體diff 1,887檔／176commits | 不整支合併 |
| [PR #29](https://github.com/s9008129/Line_backup/pull/29) | 已合併，僅八個證據檔 | 主線已有報告／公開索引，沒有完整實測工具 |
| [舊Chief Review](https://github.com/s9008129/Line_backup/pull/28#pullrequestreview-5608322661) | 接受manual-diagnostic evidence，保留私有證據未獨立重現之限制 | 不轉成新功能review PASS |
| PR28 `private/checkpoints.json` | 本機可讀；1783bytes；SHA `69d385ac9ccf3f5ba139ca45b6d0412c17499ce9e3e6c44eb50b62cb786f548e` | 唯讀歷史匯入 |
| [PR28報告88～146行](https://github.com/s9008129/Line_backup/blob/72dae704a9a5f3dbdee21e33178201350b6e7a06/harness-development/line-five-album-manual-20261022/E2E測試報告.md#L88) | metadata點擊、detail身分核對、真實menu OCR、Chooser、下載與完整解碼流程 | 保持既有操作順序 |
| [ImageIO decoder第7～68行](https://github.com/s9008129/Line_backup/blob/72dae704a9a5f3dbdee21e33178201350b6e7a06/src/line_backup_batch/image_decode.swift#L7) | 源碼與報告hash相同；完整RGB draw、逐檔SHA、只讀輸出 | 原樣重用 |
| 本機 `harness-development/catalog-diagnostic-20261010/modern_ocr.swift` | hash與報告相同；目前不是HEAD的tracked檔 | 將原始bytes納入新功能，不能假稱從Git HEAD取得 |
| [content.py第14～78行](https://github.com/s9008129/Line_backup/blob/72dae704a9a5f3dbdee21e33178201350b6e7a06/src/line_backup_batch/content.py#L14) | 有穩定取樣、hash／decoder交叉比對、解碼後再核對；依賴正式package與固定backups containment | 重用檢查方法，不整包import |
| [batch resume第588～591行](https://github.com/s9008129/Line_backup/blob/72dae704a9a5f3dbdee21e33178201350b6e7a06/src/line_backup_batch/service.py#L588) | RECONCILE_ONLY、禁止dispatch | 不修改、不當方案A入口 |
| [transaction resume第380～428行](https://github.com/s9008129/Line_backup/blob/72dae704a9a5f3dbdee21e33178201350b6e7a06/src/line_backup_acceptance/transaction.py#L380) | UNKNOWN barrier、不重新派送 | 參考不變條件，不調用正式授權流程 |

目前 Agent 入口為 DeepSeek 透過工具執行的程序；尚未找到 PR28 專用、可獨立呼叫的批次續跑 executable。

### 2.2 私有 checkpoint 實際結構

原測試包：`harness-development/line-five-album-manual-20261022/`。

頂層：`test_type, model, provider, session_id, repo_head_at_start, updated_at, albums, totals`。

`albums`是以A45／B78／C77／D42／E87為鍵的object；每本有`status, expected_images, verified_images, save_all_dispatches_this_session, destination, unknown_outcome`；A45另有`previous_session_save_all_dispatches`。

五本均記錄`FILES_VERIFIED`。目的地是相對於原測試包的路徑；以正確基準解析後，五個目錄存在，分別有45／78／77／42／87個非零一般檔案。

缺少schema version、ordered manifest、durable pre-intent、generation、事件序號及writer ownership。結論：原檔保留，不原地升級；建立sidecar，只讀匯入歷史參照。

### 2.3 UNVERIFIED ASSUMPTIONS

- 本輪沒有重新ImageIO解碼或逐檔重算五本照片hash；檔數核對不等於新的完整驗證PASS。
- JSON內容無法證明其歷史寫入原子性／fsync；舊成功也不證明任意crash點可恢復。
- 新GUI包裝、長生命週期鎖及固定目錄durability尚未實作／驗證。
- 已檢查設定與五本索引只有排除65張之摘要，尚缺完整可用排除身分映射。
- 原Mac Python為3.9.6；新Python須相容3.9。Swift／Node版本接手時重讀，不依賴規劃時版本。
- GitHub／新clone不包含本機私有checkpoint、原圖及未tracked OCR；缺少時誠實報錯，不能重建假資料。

## 3. ROOT CAUSE AND GAP MATRIX

根因是成功操作的持久化控制邊界尚未產品化：Agent上下文與完成摘要無法可靠回答crash時是否可能已派送Save All。

| FR | 現況／缺口 | 最小處理 |
|---|---|---|
| FR-01、14 | 五本摘要；無固定順序、scope digest與可推導進度 | manifest、task ID、摘要 |
| FR-02、05 | 獨立目的地／ImageIO已實測；無一致恢復入口 | 原樣decoder、只讀verifier、收據 |
| FR-03、04 | 無durable intent與click先後證據 | 原子checkpoint；成功提交才可click |
| FR-06、07 | 正式resume禁止派送；手動接續依提示詞 | 只讀reconcile與受控續跑分離 |
| FR-08、12 | partial／unknown恢復政策未一致 | BLOCK_AND_PRESERVE，禁止重試及後續派送 |
| FR-09 | fresh OCR／AX／detail已實測 | 每Session重新定位，不恢復座標 |
| FR-10 | 正式／manual／五本資料分散 | 統一唯讀歷史參照與跨task屏障 |
| FR-11、13 | 無方案A共用ownership | 固定根目錄全域session lock；當次交接獨立記錄 |
| FR-15 | 停止後無一致收尾 | 關閉新輸入、保留intent、等待已發出呼叫結束 |
| FR-16 | 舊schema現已可讀 | 專用非破壞匯入，不泛化migration framework |

## 4. MINIMAL FILE-LEVEL CHANGESET

文件交付分支`docs/agent-resume-handoff-20261022`只修改根目錄`plan.md`、`handoff.md`；產品實作另建`feature/agent-backup-resume`的外部乾淨worktree。實作以本次文件交付commit為base（parent為`64515eb...`），接手時解析並記錄精確SHA，不在原dirty分支切換／reset／clean／stash。若分支或位置已存在，先查其身分與狀態，不覆寫。

| 檔案 | 責任 |
|---|---|
| `scripts/line_backup_agent_resume.py` | 新增；標準庫schema、原子checkpoint、鎖、歷史匯入、reconcile、session controller與CLI |
| `scripts/line_backup_agent_resume_cua.mjs` | 新增；薄型CUA包裝，連接durable intent與原始單次Save All，不重寫辨識／定位 |
| `scripts/agent_resume/image_decode.swift` | 原樣複製；SHA `238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b` |
| `scripts/agent_resume/modern_ocr.swift` | 原樣複製本機來源；SHA `19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861` |
| `tests/test_agent_resume.py` | 100本、檔案驗證、持久化、鎖、故障注入 |
| `tests/test_agent_resume_cua.mjs` | 實際新包裝＋fake app；計算callback與重放拒絕 |
| `docs/agent-resume.md` | 使用流程、資料契約、恢復政策、一行Prompt、停止條件 |
| `.gitignore` | 只追加新測試包private忽略規則 |
| `plan.md`、`handoff.md` | 只允許必要的範圍內澄清與交付狀態更新；不能自行改AC／保護政策 |
| `harness-development/agent-resume-20261022/E2E測試報告.md` | 持續記錄離線／實機結果、FAIL／BLOCKED／NOT_RUN |
| `harness-development/agent-resume-20261022/progress.md` | 短記進度、嘗試次數、第一阻塞與next_action，不複製大量報告 |
| `harness-development/agent-resume-20261022/issues/` | 僅在有實際未解問題時新增問題提報單及安全的文字證據 |

開發／測試原始證據可寫新task package的`private/`，必須先確保忽略，不stage。新功能runtime資料只寫Owner選定固定私有根目錄。測試只能使用隔離臨時fixture，不能對正式資料注入故障。

絕不修改Harness／controller／schemas／runtime defaults、`src/line_backup_batch/`、`src/line_backup_acceptance/`、原`line_backup_cua_adapter.mjs`、正式`two_album_entry.mjs`、正式state／Grant／Ledger／pilot policy、歷史證據／照片與PR28原checkpoint。

新功能不import正式授權／交易package，只以普通只讀方式取得歷史防重複資料。

## 5. 持久化契約與技術決策

### 5.1 單一原子checkpoint

```text
agent-resume/
  checkpoint.json
  .session.lock
  tasks/<task_id>/
    downloads/<ordinal>-<album_key_prefix>/
    evidence/
    verification/
```

`checkpoint.json`為跨task唯一控制真相，包含已登記task、歷史archive references、exclusions、ownership與events。100本不需要SQLite或獨立JSONL journal；整份原子替換可避免雙檔一致性與journal尾端修復。events在邏輯上只能追加，既有事件不得改刪。

逐檔manifest／decoder收據／GUI證據另存不可變檔，checkpoint存摘要、參照與SHA。新store缺少時不自動初始化；無法證明完整歷史時不得GUI。

### 5.2 最低schema與相容性

| 區塊 | 必要資料 |
|---|---|
| Store | `schema_version=1, generation, payload_sha256, last_event_seq, owner` |
| Task manifest | task_id、建立時間、固定group scope、Owner scope reference、有序albums、排除規則、manifest_sha256 |
| Identity | ordinal、album_key、日期起訖、預期張數、可取得title／detail date等消歧欄位 |
| Operation | intent、dispatch observation、chooser intent／observation、固定目的地、來源身分證據 |
| Verification | outcome、count／bytes、逐檔manifest digest、decoder source／binary hash、收據、完成時間 |
| Event | 單調seq、時間、session／task／album、事件、前後狀態、證據參照 |
| Historical reference | source kind／root／digest、identity、原目的地、驗證參照、排除或屏障原因 |

Canonical JSON：UTF-8、排序object keys、固定separators，拒絕duplicate keys／NaN；digest排除自身欄位。未知schema版本直接拒絕，不猜測升降版。

Manifest建立後不可原地改scope／清單／身分／目的地／順序；新需求建新task，仍受全域歷史及intent屏障約束。不改寫舊checkpoint；不存在通用原地migration入口。

### 5.3 原子提交順序

1. 持session lock重讀，驗證schema、checksum、generation、事件前綴與操作前提。
2. 同目錄唯一temporary file完整寫入／flush。
3. file fsync；macOS對regular file執行F_FULLFSYNC。
4. os.replace原子替換checkpoint。
5. sync父目錄，再對新checkpoint full sync。
6. 重開解析，比對generation與digest。
7. 全部成功才回覆committed；不能提前發送GUI資格。

必要primitive不支援或任何步驟失敗，禁止GUI；不能默默降級。發現malformed checkpoint、未知schema、checksum錯或未完成temporary revision，回報`BLOCKED_STORAGE_INTEGRITY`；不自動載入較舊backup、刪暫存或初始化空紀錄。

一般fsync不等於drive已持久化；採Apple較強flush仍不宣稱任意硬體故障的絕對保證。[Apple fsync文件](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fsync.2.html)

### 5.4 公開CLI與輸出

- `init`：首次明確建立store，不由resume自動呼叫。
- `import-history`：匯入明列來源之唯讀參照。
- `create-task --manifest FILE`：驗證並凍結新清單。
- `inspect --task ID`：只讀結構／進度。
- `reconcile --task ID`：只讀檔案核對，stdout輸出恢復建議。
- `session --task ID`：供CUA包裝使用之session controller，持鎖／提交狀態，本身不生成GUI input。

所有命令顯式接受固定`--root`；Agent使用預設根目錄前仍確認與本task綁定，不自動搜尋另一store。`inspect/reconcile`不建鎖檔、不寫checkpoint、不提交VERIFIED，不依賴LINE／網路／模型。輸出generation、manifest digest、各狀態本數、照片統計、first blocker、next action及`gui_dispatches=0`。

退出碼：0成功；2輸入／schema不合法；3任務被阻塞；4writer busy；5storage／runtime不足。

## 6. STATE MACHINE / IDEMPOTENCY / LOCK

### 6.1 正交狀態

- Operation：`NOT_STARTED → INTENT_RECORDED → CALL_RETURNED / DISPATCH_UNKNOWN`。
- Chooser：獨立保存目標確認intent、呼叫結果及證據。
- Filesystem：`UNCHECKED / VERIFYING / COMPLETE / PARTIAL / INVALID`。
- 對外結果：`NOT_STARTED / VERIFIED / SKIPPED_EXISTING / BLOCKED_PARTIAL / BLOCKED_AMBIGUOUS`。

`TARGET_CONFIRMED`只屬當次有效GUI證據，不能載入後恢復有效性；task狀態與下一ordinal由資料推導，next_index最多是顯示快取。

### 6.2 Save All與Chooser邊界

沿用PR28：fresh list／detail→展開menu→fresh OCR找到實際儲存全部。在真正Save All click之前：

1. 檢查本次前景交接、fresh identity／menu binding、空目的地、跨task重複及未解屏障。
2. durable intent綁定task／album／session／action／目的地／證據。
3. 收到新提交成功回覆。
4. 記憶體中消耗原始呼叫資格，再呼叫一次app.click。
5. 保存返回／錯誤／觀察，timeout或錯誤皆不重試。

`dispatchSaveAllOnce(...)`自行只呼叫一次Save All input，不接受能迴圈dispatch的任意callback。相同request ID重送只能回覆已存在，不能重獲資格。資格不序列化、不從checkpoint重建，也不暴露成獨立可重播CLI token；回覆遺失直接停止，不以重試換新資格。

Chooser最終確認也先保存intent，並獨立限制單次確認。新Session不自動接續舊chooser；先filesystem reconcile，不足就停止。工具實際呼叫、RETURNED、UNKNOWN及保守預留計數分開報告，不能用預留計數冒稱真實click。

### 6.3 不變條件

- 有intent的同一相簿，所有後續Session／task都不得重新Save All。
- intent後crash，即使計數零或目的地空，也不能推論未派送。
- VERIFIED／SKIPPED_EXISTING不退回可下載；完整性失效轉BLOCKED。
- 清owner、換task ID／目的地不解除屏障。
- PARTIAL／UNKNOWN不略過，不派送下一本。
- intent與GUI無共同原子交易；接受可能沒下載但阻塞，不宣稱exactly-once。

### 6.4 單writer／接管

Python controller在整段GUI作業持有固定根目錄`.session.lock`的非阻塞exclusive flock，涵蓋所有task。短CLI退出不代表GUI ownership結束。

Owner記錄session、controller與GUI host的真實程序身分／boot identity。正常close停止新輸入、等待已發出呼叫結束、保存收尾才釋放鎖。程序結束／Mac重啟由OS釋放鎖；lock檔存在本身不表示busy。舊GUI host活著或不明就拒絕接管，回報`PREVIOUS_GUI_SESSION_NOT_RELEASED`；不TTL搶鎖、不自動kill、不unlink lock、不把stale owner當重送授權。

[flock是合作式鎖](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html)，無法禁止未遵循流程的其他工具或人工；實機期間Owner維持唯一GUI operator，不宣稱OS隔離。

第一實作里程碑以零GUI input preflight證明CUA載入、長生命週期controller、程序身分與bridge可用；失敗提報，不改Harness、不改用shell GUI引擎。

## 7. 歷史匯入、去重與驗證

### 7.1 歷史來源

固定支援正式backup_state verified／verification、manual_archives manifest／verification，以及PR28 checkpoint＋公開候選身分索引＋私有manifest／decoder／身分證據。另需Owner排除65張的完整scope-bound identity，只有65不能辨識。

匯入前保存來源digest；需備份時只在新私有目錄建副本，不改原檔／圖。PR28目的地以原測試包解析。初始狀態為HISTORICAL_REFERENCE，不能憑FILES_VERIFIED字串變新VERIFIED；身分映射及本機驗證成立才SKIPPED_EXISTING。來源缺少／身分不明保留deny barrier，不能當未備份。

### 7.2 跨task去重

album_key由固定group scope、日期起訖、預期張數及既有消歧欄位canonical identity計算，不只用title或照片內容hash。

- 完全相同且有效archive：核對後SKIP。
- 同scope同日期但張數改變：可能來源變動，先BLOCK，不能直接當新相簿。
- 同日期／張數多候選：需title／detail date等獨立證據，仍不明就BLOCK。
- 群組重名／改名／scope不明：BLOCK，不合併不同Unicode字元群組。
- 不同檔案可有相同內容hash；逐檔mapping／multiset核對，不以digest唯一性刪檔或拒絕。

歷史完成、exclusion與未解intent均跨task檢查；不得另建store規避。

### 7.3 完整檔案驗證

canonical no-follow路徑；拒絕traversal、symlink、未知子目錄／檔案。照片數必須等於expected，零byte／partial／temp／unrecognized均為0。取三次相同inventory、間隔3秒，核對檔名、大小、mtime、SHA；逐張ImageIO完整RGB解碼，decoder逐檔SHA必須與inventory一致，解碼後再取inventory。

新下載提交VERIFIED前，以只讀descriptor flush照片及目的地，失敗不提交。live等待上限600秒，不足／不穩定就保留原圖停止。P0每次恢復完整核對task中已完成項，不先做驗證快取。

檔數／hash不獨立證明LINE來源。in-flight滿額promotion另需intent前detail identity、空目錄證據、固定目的地及chooser目標綁定；缺少來源關聯，即使80張均解碼也AMBIGUOUS。公共manifest使用安全索引，不搬移或改名原圖。

## 8. 100本恢復演算法

1. 新Session先inspect／reconcile指定固定store；缺少／損壞停止，不自動init。
2. 驗證schema、checksum、manifest、scope、事件／狀態及路徑。
3. 檢查writer、歷史來源與跨task屏障。
4. 優先核對in-flight #50，再核對前49本；任何其他宣稱完成項也需有效。
5. 只輸出建議，不在唯讀階段提交。
6. 當次前景交接成立後，controller持鎖重核generation及檔案；未變才提交恢復結果。
7. 從第一個未完成ordinal開始，有前置BLOCKED則不進GUI。
8. 以新screenshot／AX／OCR重找相簿，list與detail均MATCH才Save All。
9. 每本完整驗證及checkpoint readback成功才返回列表、fresh scroll／grounding下一本。
10. 全部有效VERIFIED／SKIPPED_EXISTING、無未解intent／失效驗證，才COMPLETED。

| #50事實 | 結果 |
|---|---|
| 有效完整checkpoint從未有intent，目的地不存在／合法空 | NOT_STARTED；fresh定位後開始#50 |
| 有intent，目錄空 | DISPATCH_UNKNOWN；停止，不重送 |
| 有intent，32／80 | BLOCKED_PARTIAL；保留32，#50～100零派送 |
| 有intent，80／80及來源綁定完整 | 持鎖提交VERIFIED，下一本#51 |
| 80／80但來源不足／額外檔案 | BLOCKED_AMBIGUOUS |
| VERIFIED後少檔／hash改變／壞檔 | 失效驗證、BLOCKED，不補下載 |
| 壞checkpoint／manifest變動／多個未解in-flight | storage／identity conflict，停止 |

PARTIAL後外部下載自然完成，可再唯讀核對及持鎖提交，不等於重送。P0沒有force、reset、重開intent、跳過阻塞開關。

## 9. EXECUTION PLAN / ROLLBACK / ESCALATION

風險為CRITICAL（重送與照片污染），但本次外部獨立審查依Owner記為OWNER_WAIVED，不生成假review。實作由`deepseek-v4.1-flash:1017 / ollama_cloud`接手，記錄真實Session／模型／provider；不可用就報阻塞，不暗中換模型。後續產品實作不預設派子代理：max_parallel_read_only_helpers=0、max_parallel_writers=0。本輪Owner另授權一名GPT-6 luna／high只讀文件梳理與提交訊息，不是產品writer或獨立Acceptance。

| 階段 | Owner／工作 | 出口與失敗處理 |
|---|---|---|
| 0 文件交付 | 主Agent保存本plan／handoff與Owner決策；Luna只讀梳理並擬commit；主Agent驗證、commit／push／Draft PR | 文件一致、精確SHA可追溯；external review=OWNER_WAIVED，不等於功能PASS |
| 1 核心實作 | DeepSeek先環境對帳、兩Swift來源核對、零GUI runtime preflight；再store／import／reconcile／wrapper／tests | TC離線項、100本與重放計數有真實證據；未解問題按本節立即提報 |
| 2 整合交付 | DeepSeek完成最小diff、本地驗證、AC矩陣、完整報告、commit／push／Draft PR，供Owner讀取 | IMPLEMENTATION_DONE只代表實作範圍交付；不新增外部Chief前置，也不自填E2E PASS |
| 3 真實驗收 | Owner啟動新的獨立DeepSeek Session，授權新相簿與前景，中間由Owner重啟Mac | 兩本、完整檔案、零歷史重送、保護邊界均有證據才結案；FAIL／BLOCKED保留否決 |

Rollback僅停用新程式或回前一個相容程式版本；保留store／照片／intent，不刪資料、不恢復舊checkpoint、不讓舊程式猜新schema。

### 9.1 無法解決問題的強制提報

遇到無法在目前範圍／工具內解決、涉及架構／AC／安全邊界、證據矛盾、GUI能力不足或未知Save All結果，立即停止依賴該前提的動作，先保全證據，再寫`harness-development/agent-resume-20261022/issues/ISSUE-<UTC>-<slug>.md`，交Owner轉高階模型分析；不得只回聊天摘要。

同根因至多三次有證據嘗試；連續兩次無新資訊，或已遇material blocker，提前停止。重開Session／換模型不重置歷史。提報單含task／plan SHA／source commit、環境、受影響AC／TC、最小重現、expected／actual、第一拒絕與原始錯誤、GUI真實派送／UNKNOWN、狀態前後、每次嘗試及新資訊、facts／inferences／unknowns、證據定位及SHA、副作用、可安全繼續項、已停止項、高階模型需裁決的精確問題。私有raw留本機，公開版本遮蔽。

高階模型指定GPT-6.1-SOL／xhigh或Owner明確指定等級；未實際送達不能寫已提交／已分析／已核准。Owner轉交前記`HIGH_MODEL_HANDOFF=PENDING_OWNER_FORWARD`；取得回覆須記真實來源及精確結論。不得為等待分析反覆同樣測試或越權改AC。

## 10. TEST MATRIX

離線使用小型生成照片的100本fixture：前49完成，#50 expected80，其餘小型不同身分；包含合法相同照片bytes。測試只寫fixture，不碰live資料。

| TC | 必要測試與證據 |
|---|---|
| 01–02 | #50 intent前結束程序；新程序可開始#50；#1～49增量0 |
| 03 | durable intent後、click前kill；UNKNOWN、再次wrapper零click |
| 04 | click後回覆／chooser observation遺失，不重送 |
| 05 | 32／80保留全部hash；#50～100增量0 |
| 06 | 完整80／80＋來源綁定，未VERIFIED即kill；重核後僅#51 |
| 07 | VERIFIED後刪／改／截斷檔，BLOCK、不補下載 |
| 08 | temp write、file sync、replace、dir sync、readback前後失敗／kill；完整revision或BLOCK |
| 09 | HTTP413、timeout、回覆遺失、新程序、重複request，不重放 |
| 10 | fake app換視窗／session／binding，舊座標拒絕；實機另驗fresh定位 |
| 11 | 同task及不同task雙程序只一owner；helper死而GUI host活也拒接管 |
| 12 | 同日期不同張數、同名／改名、同日期張數碰撞不猜測／誤SKIP |
| 13 | 非空目的地／未知檔案／archive，SKIP或BLOCK，不能當新目的地 |
| 14 | manifest／scope／session／generation變動，拒stale mutation |
| 15 | ENOSPC、sync failure、decoder timeout、OCR／chooser缺證據；first failure保存，不重送 |
| 16 | fixtures涵蓋239／109／329與65 exclusion，跨task重複零派送 |
| 17 | #50恢復後#51～100完成；100／100正確、#1～50新增0 |
| 18 | 壞JSON／duplicate keys／未知版本／checksum／symlink／traversal／孤立tmp，零GUI零覆寫 |
| 19 | 重複只讀inspect／reconcile，checkpoint／照片bytes與可觀測結果不變 |
| 20 | 禁止範圍、舊checkpoint、歷史照片前後hash不變 |

```text
python3 -m unittest discover -s tests -p 'test_agent_resume.py'
node --test tests/test_agent_resume_cua.mjs
```

macOS須實際編譯原樣decoder，驗正常影像、截斷影像、解碼後變動及錯誤目的地。其他OS的stub只證明控制邏輯，不填ImageIO PASS。fault injection僅test-only依賴注入，production CLI無略過驗證／stub dispatch選項。kill -9不是實體斷電PASS。

### 10.1 最小真實Mac E2E

Owner在離線實作交付後另啟獨立`deepseek-v4.1-flash:1017 / ollama_cloud`，不得由實作者自己宣稱獨立驗收。

1. 登記F／G兩本未備份eligible新相簿、完整歷史及65 exclusion。
2. 保存正式資料、舊checkpoint與歷史照片baseline hashes。
3. 第一Session完成F：一次Save All、一次chooser確認、全檔SHA／ImageIO、durable checkpoint讀回。
4. 正常close controller並確認無pending input；Owner當次確認後自行重開Mac，Agent不自行reboot。
5. 第二全新Session只取得task ID、核准來源／資料位置／固定AC，不輸入實作者完整推理歷史；先無GUI reconcile。
6. F核對有效、Save All增量0；新前景交接後fresh定位G並完整完成一次下載／驗證。
7. 保存兩個Session／boot identities、F＋G完成、所有保護資料不變與歷史零派送。

不刻意中斷真實partial download；不為補測重跑舊相簿。真實中斷下載非P0必要，PARTIAL由離線注入覆蓋，報告分開標示。

## 11. RISK REGISTER / PROTECTION

| 風險 | 控制 |
|---|---|
| Save All回覆遺失重送 | durable intent、單次wrapper、重複request無新資格 |
| 部分下載 | 全task停、原圖保留、只讀核對 |
| 壞檔／假完成 | hash、完整ImageIO、穩定取樣、post-decode inventory |
| 雙Session | 全域持鎖，舊GUI host活／不明不接管 |
| 前景／定位過期 | 新Session交接、fresh list／detail／menu，前景變更停輸入 |
| 關機／磁碟滿 | 強持久化順序，uncertain commit無GUI，完整revision恢復 |
| dirty tree／廣泛誤合併 | 外部worktree、固定base、逐檔stage、不合併PR28歷史 |
| 隱私 | 私有目錄0700／檔0600，公開遮蔽索引，不上傳原照片／OCR／AX／個人絕對路徑 |
| 正式state污染 | 無正式package import、禁止寫入集合、diff與前後hash |
| 身分碰撞／來源變動 | scope-bound identity，不能只靠title／count／內容hash |
| store遺失／回復舊版 | 不自動init／downgrade；未解前禁止GUI |
| runtime不足 | 零GUI preflight，提報高階模型，不改Harness補洞 |
| 未解問題被掩蓋 | 強制問題提報、保留嘗試／未知與六狀態，不以文件完成宣稱產品完成 |

## 12. OPEN OWNER DECISIONS

目前沒有阻擋離線實作的未決產品選擇。資料根目錄、兩本＋Mac重啟、PARTIAL停止、DeepSeek實作、本次外部審查免除與高階模型提報皆已指定，不重問。

真實執行前仍需：F／G身分與下載授權、65排除身分映射、當次前景交接與Owner重啟時點。可從本機來源取得的先查，不憑摘要猜；缺少只阻擋相依的live操作，不拿來阻塞無關離線實作。

## 13. READY-TO-IMPLEMENT PROMPT

> 你是本工作包Implementor，指定deepseek-v4.1-flash:1017／ollama_cloud。先完整讀plan.md與handoff.md，記錄真實模型／Session；不可用就提報，不暗換。Owner已免本次外部審查，可直接進入有界離線實作；不是review PASS，也不是GUI或新下載授權。
>
> 以文件交付commit的乾淨外部worktree開發，只改第4節允許路徑，不動原dirty樹、Harness、正式AUTO程式／State／Grant／Ledger、舊checkpoint與照片。依指定SHA原樣納入decoder與本機未tracked OCR；缺少／hash不符提報。
>
> 先證明零GUI runtime／lock preflight，再實作單一原子checkpoint、固定manifest、append-only邏輯events、generation／checksum、只讀import／inspect／reconcile及受控session。Save All intent未完整durable commit／readback不click；loaded intent、重複request、timeout／回覆遺失不重送。保持PR28成功的fresh metadata／detail／menu OCR／Chooser流程，不建新引擎。
>
> 完成TC-01～20對應、100本fixture、32／80保留、80／80補提交僅#51續跑、雙Session、儲存故障與實際callback計數。用真實ImageIO測試時記錄source／binary hashes，stub不冒充實機。未獲Owner當次授權與前景交接不操作LINE；獨立實機由Owner另啟新Session。
>
> 任何無法解決問題立即保全證據、停止相依操作，按第9.1節寫問題提報單交Owner轉高階模型。最多三次有證據嘗試，連續兩次無新資訊提前停，不改AC或略過guard。回報精確問題、重現、原始錯誤、已做嘗試、GUI派送／UNKNOWN、證據SHA與需要高階模型裁決的一件事。
>
> 最後交付最小diff／commit、測試命令結果、AC逐項狀態、完整報告、未解問題及next_action；逐檔commit／push／Draft PR，commit body含意圖／做了什麼／驗證與結果／下一步的建議。不merge、不amend／force-push，不把IMPLEMENTATION_DONE當整體E2E PASS。

最短使用Prompt：

> 接續LINE備份任務`<task_id>`。先從固定私有store唯讀reconcile；PARTIAL／UNKNOWN就停。無阻塞時取得當次前景交接，只處理剩餘NOT_STARTED，不重送既有intent。

## 14. DELIVERY / ACCEPTANCE GATES

提供原PRD定位與digest、plan SHA、精確implementation commit、最小source diff、兩Swift／binary hashes、AC／TC矩陣、完整E2E報告。私有index記相對／絕對定位及SHA；公開index只用安全代碼。不曾讀取的私有內容標operator-reported，不冒稱獨立核驗。

| Gate | 狀態／PASS條件 |
|---|---|
| G0外部Plan／Handoff review | OWNER_WAIVED，不能寫PASS／APPROVE；文件版本／SHA仍須一致 |
| G1 runtime／離線 | 實際preflight、100本、fault injection、鎖、驗證及重放測試有可核對結果 |
| G2實作交付 | 精確HEAD、最小diff、AC矩陣、報告、必要測試與未解問題；本次外部Code Review不作新增前置，也不聲稱已完成 |
| G3獨立live E2E | Owner另啟DeepSeek新Session；兩本、Mac重啟、新Session、各一次Save All、全檔驗證、無歷史重送 |
| G4保護與結案 | 禁止範圍／歷史照片不變，G1～G3及全部AC成立，問題已解或未達標明確保留 |

Owner前景／重啟確認屬OBSERVED，不能代替檔案／程式Gate PASS。版本變更須影響分析與必要重驗。開發及E2E證據保存在task repository，非全域.codex；runtime原圖及持久化控制資料使用固定私有store，repo報告引用其可核對識別。

指定handoff prompt為`03_handoff_prompt.md`（v4.8 Optional Handoff Reviewer）。本次沒有此新task的controller stage packet／emitted CONTRACT／RESULT命令，故只交付advisory Markdown handoff，不冒稱deterministic compiler、format3機器契約驗證或controller admission PASS，也不借用其他task schema命令造收據。這不新增Harness依賴。

### 14.1 固定狀態欄位

```text
TASK_ID=AGENT-RESUME-P0-20261022
PLAN_REVISION=v1.1
PRD_VERSION=v1.0
PLANNER_MODEL=gpt-6.1-sol
REASONING_EFFORT=xhigh
MODEL_ATTRIBUTION=REQUESTED_NOT_RUNTIME_ATTESTED
IMPLEMENTOR_MODEL=deepseek-v4.1-flash:1017
IMPLEMENTOR_PROVIDER=ollama_cloud
SOURCE_BASELINE_HEAD=72dae704a9a5f3dbdee21e33178201350b6e7a06
DELIVERY_BASE=64515eb56b04accc40ade9e2db2fe0ad18c1ced3
IMPLEMENTATION_BASE=EXACT_COMMIT_CONTAINING_THIS_PLAN_AND_HANDOFF
CURRENT_AGENT_ENTRYPOINT=DEEPSEEK_TOOL_DRIVEN_MANUAL_DIAGNOSTIC
PRIVATE_CHECKPOINT_SCHEMA=VERIFIED
PRIVATE_PHOTO_FULL_VERIFICATION_THIS_PHASE=NOT_RUN
DESIGN_DECISION=ISOLATED_ATOMIC_CHECKPOINT_EMBEDDED_EVENTS_THIN_CUA_WRAPPER
P0_FILE_CHANGESET=SECTION_4
FORMAL_AUTO_CODE_TOUCHED=NO
HARNESS_TOUCHED=NO
DUPLICATE_GUARD_DESIGN=GLOBAL_HISTORY_IRREVERSIBLE_INTENT_BARRIER
CRASH_RECONCILIATION_DESIGN=READ_ONLY_VERIFY_LOCKED_REVALIDATE_COMMIT
PARTIAL_DOWNLOAD_POLICY=BLOCK_AND_PRESERVE
100_ALBUM_FIXTURE_PLAN=SECTION_10
MINIMAL_LIVE_E2E_PLAN=TWO_NEW_ALBUMS_OWNER_MAC_REBOOT_NEW_DEEPSEEK_SESSION
FIRST_IMPLEMENTATION_BLOCKER=NONE_BEFORE_PREFLIGHT
OWNER_DECISIONS=NONE_FOR_OFFLINE_IMPLEMENTATION
LIVE_INPUTS_PENDING=NEW_ALBUM_IDENTITIES_EXCLUSION_IDENTITY_FOREGROUND_HANDOFF
IMPLEMENTOR_PROMPT=SECTION_13_AND_HANDOFF_OPENING
EXTERNAL_REVIEW_GATE=OWNER_WAIVED_FOR_THIS_WORK_PACKAGE
HARNESS_HANDOFF_COMPILER=NOT_INVOKED
HIGH_MODEL_ESCALATION=REQUIRED_ON_UNRESOLVED_PROBLEM
PRIMARY_OUTCOME_STATUS=PLANNED_NOT_IMPLEMENTED
IMPLEMENTATION_STATUS=NOT_RUN
CORE_ACCEPTANCE_STATUS=NOT_RUN
REQUIRED_VERIFICATION_STATUS=NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
```

最終建議：採隔離sidecar；核心只有Python控制器與CUA薄包裝，兩個成熟Swift工具原樣重用。先證明durability／單次派送／100本恢復，再兩本真實重啟驗收。不增正式AUTO、相簿內續傳或大型框架；沒有可靠實作耗時資料，不估造工期。
