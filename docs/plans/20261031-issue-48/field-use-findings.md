# LINE 相簿備份實機使用回饋與下一輪迭代建議

## 文件定位

- 日期：2026-10-31（Asia/Taipei）
- 關聯 Issue：[#46](https://github.com/s9008129/Line_backup/issues/46)、[#48](https://github.com/s9008129/Line_backup/issues/48)
- 關聯候選：[PR #47](https://github.com/s9008129/Line_backup/pull/47)
- 性質：真實現行流程的使用回饋、問題定位與下一輪迭代建議。
- 本文件不是實作完成、GUI 驗收或獨立 acceptance 報告。

## 主要意圖

本專案的 Skill、references、日常 Prompt、Computer Use 操作規則與記錄工具已經建置到可實際使用的階段，因此這次最重要的不是再增加理論設計，而是把實際使用時遇到的問題留下來。

本次 Owner 已人工開啟指定列表並正式交接前景，Agent 也確實開始依 Skill 核對畫面、完整盤點及查詢歷史。問題發生在「已經盤點完成，準備建立本次正式紀錄與開始下載」的交接點。這個問題只有在 Skill、工具、真實電腦畫面與既有歷史放在一起使用時才暴露，單靠文件審查或合成案例不容易發現。

因此本紀錄的目的，是提供下一次真實驗證與迭代的明確輸入：

1. 保留真實使用中的觀察與阻塞。
2. 區分是授權、前景、列表身分、歷史帳本或工具能力哪一層出問題。
3. 把錯誤的 Agent 行為轉成可檢查的決策案例。
4. 修正後用同一條真實日常流程驗證是否真的改善。

## 白話結論

本次沒有缺少下載授權。

Owner 已透過正式 Prompt 一次授權單一列表備份、GUI 導覽、逐本 Save All、新空白目的地、下載、驗證、保存進度及相簿級恢復。Agent 也已完成列表盤點。真正卡住的是：

> 永久帳本尚未建立，但照片區已有其他列表的舊帳本；Agent 沒有清楚規則判斷這屬於日常初始化與安全對帳，於是錯誤地停下來詢問 Owner 是否要再次授權。

這是現行 Skill 與工具整合後的真實使用缺口。保護舊歷史的規則本身正確；需要補的是它的 bootstrap 路徑，以及「什麼情況才應問 Owner」的分類。

後續永久帳本工作已用 copy-only migration 將既有帳本遷入專案永久區並保留原件，所以當時的立即阻塞已消退。Issue #48 仍然有效，重點轉為防止下一次新列表、舊帳本或中斷恢復時再次發生相同誤判。

## 本次實際使用到哪裡

已發生：

- Owner 人工開啟一個連續的 LINE 相簿列表並正式交接前景。
- Agent 依 Skill 核對入口、頁面與列表連續性。
- Agent 以當次畫面完成頂端、底端及相鄰重疊盤點。
- Agent 保存私有盤點草稿，沒有把聊天記憶當成唯一依據。
- Agent 查詢舊任務、`active-task`、永久／legacy 帳本與預設照片位置。

尚未發生：

- 沒有開啟任何相簿。
- 沒有按任何 Save All。
- 沒有下載任何照片。
- 沒有建立正式 scan／intent／completion。
- 沒有修改 active-task、舊帳本、舊照片或完成事實。

因此本次是一筆乾淨的「盤點完成、正式下載前阻塞」現場證據，適合用來修正流程，而不會與下載結果或照片驗證混在一起。

## 當時觀察到的狀態

1. 正式 Prompt 已授權，且前景交接有效。
2. 當前畫面是單一連續列表，完整盤點已成立。
3. 全域永久 `backup-records/` 尚不存在。
4. `active-task` 指向舊版照片區內的 records root。
5. 預設照片區內存在其他列表的 legacy `backup-records/group.json`。
6. `daily groups` 因此拒絕，不能把缺少 catalog 當成空歷史。
7. Agent 已有安全保存 legacy records 的 migration 能力，但沒有明確規則說明可在本次日常任務中自行執行。
8. Agent 最後以「需要再次授權」詢問 Owner，造成使用者合理質疑。

## 為什麼會誤報成再次授權

### 規則一：一次授權其實已經足夠

現行文件明確支持本次授權已完整：

- `AGENTS.md:9`：正式 Prompt 的提交同時提供任務授權與前景交接；前景中斷後只重新交接，不重複已有效的備份授權。
- `.agents/skills/line-album-agent-cua/SKILL.md:20`：已授權整份列表時，不要求另說口令，也不在每本前重新請示。
- `.agents/skills/line-album-agent-cua/SKILL.md:22`：缺少 popup 是觀察問題，不能報成缺少下載授權。
- `.agents/skills/line-album-agent-cua/SKILL.md:26`：重新交接不要求重複備份授權。
- `docs/LINE相簿備份_使用手冊.md:3`、`:20`、`:45-59`、`:125`：一次 Prompt 已涵蓋 Save All、新空白目的地與相簿級恢復。
- `.agents/skills/line-album-agent-cua/references/daily-backup.md:116`、`:126`：不得以再次授權解鎖 UNKNOWN；舊 authorization-request 已退役。

所以 Agent 不應該詢問第二次下載授權。

### 規則二：保護舊歷史的 gate 先觸發了

目前程式把「已知歷史不得被當成空帳」放在全域 collection 的建立路徑：

- `src/line_backup_batch/record_store.py:16-23`：`history_expected()` 會因 active-task 指向 collection，或預設照片區存在 legacy group，而回傳 true。
- `src/line_backup_batch/record_store.py:33-40`：建立 collection 時共用同一 gate，失敗為 `KNOWN_RECORDS_MISSING_NO_EMPTY_HISTORY`。
- `src/line_backup_batch/record_store.py:135-140`：若新 group 的 root 內有 legacy `backup-records/`，會拒絕為 `LEGACY_RECORDS_REQUIRE_MIGRATION`。
- `src/line_backup_batch/record_store.py:157-161`：collection 不存在時，`daily groups` 也可能以同一保護拒絕。
- `src/line_backup_batch/daily.py:341-367`：建立新 group 必須有真實 foreground binding 與 history-scope evidence；這個要求正確，不應用聊天字串冒充。

這些拒絕保護了舊歷史，不應直接刪除。真正的缺口是缺少從「catalog 尚未 bootstrap」安全走到「migration、groups readback、新 group、下載」的日常決策。

### 規則三：文件只有「不明就問」，缺少「已證明新列表就自行初始化」

- `.agents/skills/line-album-agent-cua/references/inventory.md:10`、`:64` 要求先核對帳本與目的地，不可猜配。
- `.agents/skills/line-album-agent-cua/references/backup-and-resume.md:132` 說「疑似另一列表或 Owner 指定不同位置而對應不明時才問」。

方向正確，但沒有定義：

- 完整盤點後已確認是新列表，應由 Agent 自行建立新帳本；
- 舊 legacy records 存在時，應先安全遷移並讀回；
- migration 是可保留原件的技術初始化，不是第二次下載授權；
- 只有來源衝突、歷史缺失或兩個以上合理列表候選時才停下問 Owner。

因此 Agent 把技術拒絕誤分類成授權不足。

## 核心發現

### F1. 缺少的是「帳本 bootstrap」狀態，而不是權限

至少有以下不同的狀態，目前文件沒有把它們拆開：

| 狀態 | 應有處理 |
|---|---|
| 沒有下載授權 | 才詢問 Owner 授權 |
| 有授權但前景中斷 | 停止 GUI，請 Owner 重新交接前景 |
| 新列表已確認，catalog 已建立且無相符帳本 | Agent 自動建立新 group，不詢問授權 |
| Catalog 尚缺，但 legacy records 可驗證 | Agent 安全 copy-only migration，保留原件，讀回後繼續 |
| Active-task 指向的歷史與來源都缺失 | 停止新派送，保存 missing-history 事實，問一個具體對帳問題 |
| Migration 衝突、symlink、drift | 保留兩邊並停止，不繞過 |
| 兩個以上列表候選 | 只問列表身分，不問下載授權 |
| UNKNOWN／未解派送 | 查證或保留阻塞，不重送、不以再授權解鎖 |

### F2. `active-task` 是定位資訊，不是授權或唯一歷史

`AGENTS.md:15` 已明說 active-task 只協助定位，不是唯一歷史入口。但它仍可能讓全域 collection 的建立被擋住。

正確方向不是忽略它，而是：

1. 保存 active-task 指向 missing records 的異常；
2. 找出可驗證的 legacy 來源；
3. 有來源就 copy-only migration 並驗證；
4. 沒有來源就停止，不用新空帳或再授權掩蓋。

### F3. 目的地層級需要說白

Owner 的 `BACKUP_ROOT` 是照片區上層；永久 group 的 `--root` 是該列表實際照片 destination。兩者不可混用。

當預設照片區內有舊 `backup-records/` 時，Agent 不應把整個照片區直接當成新 group root，也不應為了初始化刪除 legacy records。應在 Owner 指定的照片區內選擇或建立一個新的、無衝突的列表 root，再 `init`、`bind` 與建立每本新的空白 album 目錄。

現行文字沒有把這個層級講得足夠集中，是真實使用時容易誤判的地方。

### F4. 現有測試保住 fail-closed，但缺少正向新列表案例

`tests/test_permanent_records.py:71-83` 已確認：若 catalog 缺失、active-task 指向其中，而且沒有可安全重建的歷史，`groups` 與 `create_group` 必須拒絕，不能建立空 collection。

這項負向測試應保留。目前缺少的是成對的正向案例：舊 legacy records 可驗證、當前已證明是另一個新列表時，Agent 應能走完安全 bootstrap，而不是詢問再次授權。

## 根因

本次不是單一文件寫錯，而是三個層面沒有接好：

1. **授權層**：已足夠，但 Agent 沒有被明確禁止把帳本初始化說成授權問題。
2. **記錄層**：保護 gate 正確，但沒有對「可安全遷移」與「真正歷史缺失」分流。
3. **驗證層**：有 fail-closed 測試，卻沒有「新列表 bootstrap 後仍可下載」的正向回歸案例。

真實使用讓這三個層面的缺口同時出現，這正是本紀錄最需要保留的價值。

## 下一輪迭代建議

### 1. 先修產品契約與詢問分類

建議 Planner 先在 `AGENTS.md`、`SKILL.md` 與 references 建立唯一決策表，明定：

- 一次正式 Prompt 已含下載授權；
- 新列表 bootstrap 是技術初始化，不是再次授權；
- 安全 copy-only migration 屬日常啟動可自行完成的記錄對帳；
- 只有真正缺少授權、前景需重新交接、歷史無來源、migration 衝突或列表身分歧義才停；
- 任何情況下都不得要求 Owner 重貼 Prompt 或逐本說「開始」。

建議的 bootstrap 順序：

1. 完整盤點與當前列表 binding；
2. 查全部永久的與 legacy records；
3. 若 catalog 缺且 legacy 來源可唯一驗證，執行 copy-only migration；
4. 用 `groups` 與各 `memory` 讀回；
5. 比對當前列表與全部帳本；
6. 已證明新列表時建立新 group；
7. 選新的無衝突 group root 及每本新的空白 destination；
8. 接續 `bind → scan/page → ... → Save All`。

### 2. 不要直接移除現有保護

不建議直接放寬 `history_expected()` 或 `LEGACY_RECORDS_REQUIRE_MIGRATION`。應先建立狀態分流與測試，再只在測試證明現有 orchestration 不足時做最小程式修改。

安全 copy-only migration 的必要限制：

- 僅在無活動下載且來源可唯一辨識時執行；
- 不刪除、搬走或覆寫 legacy records；
- 不改寫 completion、UNKNOWN 或原始 evidence；
- 任何來源變動、衝突、symlink 或中斷收據不明都 fail closed；
- 完成後必須讀回全部 groups 與相關 memory。

### 3. 補成對回歸案例

至少新增：

1. New-list bootstrap：catalog 缺、可驗證 legacy records、當前是新列表 → 安全遷移、讀回、建立新 group、繼續。
2. Missing history：catalog 缺、active-task 指向 missing records、沒有 legacy 來源 → 保持拒絕，不得建立空帳。
3. Migration conflict：來源或 copy 不一致 → 保留兩邊並停止。
4. Existing catalog + new list：無相符 group → 自動建立新 group。
5. Two candidates：只問一個列表身分問題，不得下載。
6. Foreground lost：只請 Owner 重新交接前景，不要求重複授權。
7. UNKNOWN：唯讀查證或保留阻塞，不以新 root、migration 或再授權解鎖。

### 4. 修正位置

建議依序處理：

1. `AGENTS.md:9`、`:15-20`：新列表 bootstrap 與詢問分類。
2. `.agents/skills/line-album-agent-cua/SKILL.md:20-32`：明說帳本初始化不是授權缺口。
3. `references/inventory.md:7-10`、`:64-68`：分開「疑似另一列表」與「已證明新列表」。
4. `references/backup-and-resume.md:28-32`、`:132-153`：唯一 bootstrap 順序、legacy 對帳與 group root 選擇。
5. `references/daily-backup.md:17-21`：`groups → migration（需要時）→ groups readback → init → bind` 的關係。
6. `docs/LINE相簿備份_使用手冊.md`：白話說明 Owner 不需為帳本初始化再授權，以及 `BACKUP_ROOT` 與 group root 的層級。
7. `tests/test_permanent_records.py`：保留既有 fail-closed 測試，新增正向 bootstrap 案例。

### 5. 用真實流程驗證是否改善

下一次驗收應使用同一類真實情境：

- Owner 開好指定列表，只貼一次正式 Prompt；
- 列表中包含尚未備份的合格相簿；
- 已有其他列表的完成歷史與 legacy records；
- 從盤點、帳本 bootstrap、逐本下載到最終對帳，全程沒有再次授權、逐本下令或手填 JSON；
- 分開保存 GUI 觀察、照片驗證、completion readback 與獨立 acceptance 證據。

若流程仍停住，必須回報唯一的具體阻塞是授權、前景、歷史來源、migration 衝突或列表身分中的哪一類，不可一律寫成「需要授權」。

## 不建議的做法

- 不應在缺少舊歷史來源時建立空 `backup-records/`。
- 不應把新列表直接綁到名稱相近的舊 group。
- 不應刪除 legacy `backup-records/` 來讓 guard 消失。
- 不應為了繼續下載而改寫 UNKNOWN、建立新 attempt 或重送 Save All。
- 不應要求 Owner 重貼 Prompt、再說「開始」或逐本確認。
- 不應用更長的授權文字掩蓋缺少的 bootstrap 狀態機。
- 不應把這次文件或離線測試冒充真實 LINE GUI 或獨立 E2E PASS。

## 這次紀錄的價值

這次不是「規格尚未設計」的問題，而是「規格與工具已落地，真實使用發現它們的交界仍不完整」。

保留這次現場可以避免兩種錯誤：

1. 把真實使用缺口誤認為 Owner 沒有授權，造成不必要的重複確認。
2. 為了讓流程繼續而直接放寬歷史保護，造成舊帳本被當成空帳或新列表被錯綁。

正確做法是把本次阻塞轉成新的決策案例、測試與下一輪真實驗證條件，讓整個 AI Agent 驅動的 LINE 備份機制逐步穩定。

## 狀態

- `PRIMARY_OUTCOME_STATUS`：真實現行使用問題已定位；Issue #48 已建立。
- `IMPLEMENTATION_STATUS`：NOT_STARTED；本文件只保存回饋與下一輪建議。
- `CORE_ACCEPTANCE_STATUS`：NOT_RUN。
- `REQUIRED_VERIFICATION_STATUS`：文件提交前只做文件與 Git 檢查；產品回歸待下一輪切片。
- `INDEPENDENT_ACCEPTANCE_STATUS`：NOT_RUN。
- `TASK_CLOSURE_STATUS`：本紀錄完成後可提交；產品修正尚未完成。
- GUI 觀察：本次實機入口與完整盤點曾由 Agent 觀察；私人證據留在專案私有目錄，不在此重述。
- 照片驗證：NOT_RUN；本次沒有下載。
- 完成紀錄：NOT_RUN；本次沒有建立或修改 completion。
