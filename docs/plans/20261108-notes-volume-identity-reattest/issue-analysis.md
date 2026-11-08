# 記事本目錄 device 漂移：單一根因診斷

## 本角色結論

**`ANALYSIS_COMPLETE`。唯一建議路線：`PLANNER_REPLAN`。**

已確認的直接原因是：目前列表目錄的 `st_dev` 與已保存的 destination binding 不同；`_require_current_list_directory()` 因此拒絕建立第一個 v3 intent。現行程式沒有同一路徑的受控重新見證入口。這是可用性與安全恢復協議的缺口，不是本輪已證實的 LINE 下載、chooser 或媒體損壞。

尚未確認的是「為何 device 改變」及「是否為同一個持久物件」。本輪核對支持目前物件與舊 witness 相符，但不能把這點寫成「已證實正常 remount」或「已排除 volume replacement」。原提報開頭的確定語氣應以此限制閱讀；本輪保留原提報，不回寫其結論。

建議由 Owner 另開 Planner 主 Session，先規劃**僅重新見證目前 list directory binding** 的最小切片，明確處理既有 `OPEN_BATCH`。不預設需要把舊 completion、candidate、staging 的 device 一併轉換，也不要求先把完成檔投影改回 `VERIFIED_PRESENT`。這個方向尚未獲計畫核准，更不是本輪實作或重下授權。

## 1. 輸入、版本與授權

| 項目 | 精確身分／範圍 |
|---|---|
| 角色 | Owner 明示指定 `06_high_reasoning_review_prompt.md` 的 High-Reasoning Reviewer；診斷而已 |
| 選定根因 | `NOTES-LIST-DIRECTORY-DEVICE-DRIFT`；只解釋本次 `CURRENT_NOTES_LIST_DIRECTORY_CHANGED` |
| Repo | `/Users/hsiaojohnny/dev/Line_backup` |
| 分支與候選 | `feature/line-notes-media`；`3cfb068cc83508b308f427cdf69ebcd6b13fbcd4` |
| 原提報基準 | `3fdad13838ab309103ff287f6bf18464b526e97f` |
| 兩版本差異 | `git diff <原提報基準> <候選> --stat` 只有 `problem-report.md`，763 行；產品程式相同 |
| 初始 Git 狀態 | 工作樹乾淨；本地分支與本地 remote-tracking ref 一致；未將它冒稱已即時查詢遠端 |
| 執行環境 | `Darwin 27.2.0 arm64`；`/usr/bin/python3` 3.9.6；Node v24.22.1 |
| 輸入文件 | 同目錄 `problem-report.md`；Owner 本輪貼上的交接與背景補充 |
| 原始證據 | 專案私有任務 `notes-daily-20261108-112810`；相符永久帳本；不把私人識別碼提交到 Git |
| 本輪可寫範圍 | 診斷報告、progress 與專案私有診斷產物；Owner 另明示授權本輪文件 add、commit、push |
| 停止邊界 | 不修改產品、Skill、Prompt、ledger、原始媒體；不操作 LINE，不建立 intent，不執行建議路線 |

專案根目錄沒有 `policies/`。已讀全域同版本的 `/Users/hsiaojohnny/.codex/policies/v4.9.0/workflow-routing.md` 與 `subagent-model-policy.md`，僅遵循人工角色交接規範；沒有啟動 controller 或恢復退役 Harness。未借用其他版本政策。報告採同版本 `role-report.template.md` 的證據與六狀態結構。

## 2. 最小時間線與重現

以下序號來自本輪直接讀取的原帳本 JSON；未重新執行任何真實帳本命令。

| 事件／資料 | 核對結果 | 證據強度 |
|---|---|---|
| #1 `created` | 保存 list directory 的舊 device／inode | 原事件 |
| #10、#17 | 第一個 v2 intent 已有 completion | 原事件；不代表本輪重新解碼 |
| #18、#19 | 第二個 v2 intent 與 outcome 仍保留；先前摘要列 `UNKNOWN` | 原事件與原摘要；空 staging 不證明已停止 |
| #20 | 新 Session binding | 原事件；不替當前 Session 簽發 GUI 權限 |
| #21 | `restart-confirm`，且原結果 `CONFIRMED`、`replayed=false` | 原事件與當時 CLI 輸出 |
| #22–#24 | confirm 之後的新 scan start、page、scan finish | 原事件；GUI 覆蓋仍依原證據，而非本輪目視重驗 |
| #25–#28 | 兩篇 post 與兩份 media inventory | 原事件 |
| 第一個 v3 intent | 保存的輸出為 `REFUSED`／`CURRENT_NOTES_LIST_DIRECTORY_CHANGED`／`dispatch_authorized=false` | 原 CLI stdout；exit 4 由當時 blocker 紀錄提供 |
| 拒絕後到本輪 | 帳本仍為 28 事件、2 個 v2 intent、0 個 v3 intent；沒有 restart candidate／activation | 本輪靜態核對 |

原命令形狀如下。此段是**原事故命令的遮蔽表示，本輪沒有重跑**：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes intent \
  --records-root <PRIVATE_LEDGER> \
  --session-id <ORIGINAL_SESSION> \
  --media-key <ORIGINAL_MEDIA> \
  --restart-id <ORIGINAL_RESTART>
```

精確原命令與當時 exit 4 保存在原任務的 `directory-identity-blocker.txt`；該紀錄明列拒絕發生的精確時間未捕獲，不能用紀錄寫入時間代替。

### 本輪最小合成重現

在新建且會清除的私有 synthetic 目錄，直接呼叫既有唯讀方法。只在記憶體中更改 synthetic binding，不改真實 stat、不寫產品事件、不模擬實際 remount，也不使用真實影片。

| 控制變因 | 實際結果 |
|---|---|
| baseline：保存值與目前 stat 相同 | list directory 通過；完成可用性 `VERIFIED_PRESENT` |
| 僅 synthetic 保存的 directory device 不同 | `CURRENT_NOTES_LIST_DIRECTORY_CHANGED` |
| 僅 synthetic 保存的 directory inode 不同 | 相同拒絕；此控制項說明錯誤碼本身不能單獨識別 device 根因 |
| 僅 synthetic completion 目錄的 device 不同 | `LOCAL_CHANGED` |
| 僅 synthetic completion 檔案的 device 不同 | `LOCAL_CHANGED` |
| 全程 synthetic bytes | SHA-256 不變 |

命令 exit 0，所有列出的斷言成立。這證明當前程式對 device 不符的行為，不等於完整 restart 生命週期、實際掛載或真實 LINE E2E 通過。

## 3. 事實、推論與未知

### 直接核對到的事實

- list directory 存在、是 canonical path、不是 symlink；inode 與 #1 一致。device 從記錄中的 `16777229` 變成目前 `16777232`。
- #17 的完成目錄 inode 一致，完成目錄 device 不同；目錄內名稱集合與完成 manifest 精確相符。
- #17 完成檔為 regular file、非 symlink、`nlink=1`；inode、size、mtime、ctime、SHA-256 均與 completion 相符。hash 讀取前後 stat 相同。這補足原 blocker 未列出的時間與檔名集合證據。
- 舊 #18 staging 仍存在且為空；舊 #10 staging 不存在，與已完成發布的歷史相容。兩者都不能推翻其各自既有業務狀態。
- 28 個事件的序號、檔名、前序 raw-file SHA-256 link 與帳本 ID 相符。這是靜態鏈結核對，不是完整 product validator、evidence-audit 或 GUI 真實性驗證。
- 本輪診斷前後，記事本紀錄區一般檔案及 active-notes-task 共 1,102 個檔案的路徑與 SHA-256 清單相同。此聲明限內容清單，不含 atime、所有 OS metadata 或平台隔離保證。
- `notes --help` exit 0；CLI parser 與事件驗證的原始碼沒有 reattestation 入口。`destination()` 會先擋未解 attempt／`LOCAL_CHANGED`，且要求新 root 並建新 list directory，不能用來重新見證原路徑。

### 因果推論

對「為何這次 intent 被拒絕」，證據足夠：目錄型別、canonical path、symlink 與 inode 條件均成立，device 條件不成立；原始碼在 staging 建立前檢查這個條件。合成對照又確認單獨 device 不符足以造成同一拒絕。

對「為何 device 不同」，證據不足。Apple `stat(2)` 將 `st_dev` 定義為物件所在 device 的識別欄位，將 `st_ino` 定義為 inode 編號；這份文件沒有承諾它們是跨掛載的永久認證，也沒有證明本次曾 remount。[Apple stat(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/stat.2.html)

因此合理的設計推論是：持久 binding 沒有對 device 漂移提供受控恢復協議；不能推成「OS 一定正常，工具只需放行」。`(st_dev, st_ino)` 仍有當次物件替換防護價值，應保留既有比較，另規劃有證據與授權的 binding 轉接。

### 仍未知／未執行

| 問題 | 本輪口徑 |
|---|---|
| 造成 device 改變的 OS 事件、歷史 volume UUID、掛載歷史 | `UNKNOWN`；沒有取得足以唯一歸因的系統證據 |
| 同一持久物件、volume replacement、內容完全相同的 clone 如何區分 | `UNKNOWN`；相同 witness 不足以證明來源連續性 |
| 舊 UNKNOWN 是否稍後仍可能產生結果 | `UNKNOWN`；空 staging 不提供停止證明 |
| 第三次下載的歸屬 | Owner `OBSERVED`；目前 2 個 intent 不能推出第三個 attempt |
| Owner 所說兩本記事本與 active list 的兩篇貼文 | 保留兩種來源語意，沒有以 ledger 目錄數或中文名稱合併 |
| 服務端原始位元、外部副本、完整影片解碼 | 本輪 `NOT_RUN`；本機 hash 一致不能代替 |
| 真實 remount、LINE GUI、跨 Session 恢復、獨立 Acceptance | 本輪 `NOT_RUN` |

原任務「本批 GUI 派送 0 次」是原任務的操作紀錄；本輪沒有重新觀察 LINE，也沒有將它升格為獨立感測結果。當前程式的 gate 順序與無新 intent 相互支持，但帳本本身不能證明歷史 GUI 從未被帳外操作。

## 4. 程式因果鏈與可推翻條件

| 程式位置（本候選） | 可核對行為 | 結論 |
|---|---|---|
| `src/line_backup_batch/notes.py:2177` | current destination 只選最後 `destination`，否則取 `created` | 舊 device 被持續當成現行 binding |
| `src/line_backup_batch/notes.py:2183` | `st_dev` 與 `st_ino` 都必須相等 | 直接拒絕點 |
| `src/line_backup_batch/notes.py:3727` | `_restart_intent()` 先檢查 list directory | 先於 coverage 等後續 gate；不能宣稱其他 gate 也已通過 |
| `src/line_backup_batch/notes.py:3779` | 之後才建立 staging，再追加 intent | 此拒絕點尚未到建立新 staging 的程式分支 |
| `src/line_backup_batch/notes.py:3277`、`:3296` | completion 目錄與檔案另有 device guard | 單改 list gate 不會恢復舊 completion 的本機可用性 |
| `src/line_backup_batch/notes.py:3758` | restart 明確允許精確 scope 中的 `LOCAL_CHANGED` | 本次接續不必以舊 completion 回到 verified 為先決條件 |
| `src/line_backup_batch/notes.py:3560`、`:3630` | 一次最多一個 open restart；preview 可返回 `OPEN_BATCH` | 新設計必須涵蓋事故當下已存在的批次 |
| `src/line_backup_batch/notes.py:4887` | 後續 restart scope 核對來源身分與 scan | 不可因 list binding 接受就省略這些檢查 |
| `src/line_backup_batch/notes.py:4468` | staging 自身 device／inode 仍須符合 intent | 不應以 list 層轉接順便重認舊 UNKNOWN staging |

可推翻本診斷的條件包括：當時使用不同產品版本、拒絕其實來自非 canonical／symlink／inode 條件，或原輸出與另一個帳本／命令混配。原 blocker、當前 stat、版本 diff 與合成對照目前相容；沒有取得能證實這些替代說法的證據。當前 stat 不能倒推所有事故瞬間細節，這個限制保留。

其他替代解釋：

- **LINE／chooser 失敗**：不是這個 CLI 拒絕的必要原因；程式在 GUI 派送前即停止。
- **新 scan 不完整或 session 綁定錯誤**：不是已定位的目錄比較根因；後續 gate 尚未執行，仍不可預填為通過。
- **媒體 bytes 已損壞**：目前 hash 與舊 witness 相符，不支持這個解釋；未重新解碼，不能宣稱影片健康已全面驗證。
- **目錄或 volume 被替換**：尚無正面證據，亦未排除；這正是保留 fail-closed、要求明確信任邊界的理由。

## 5. 先前嘗試與本輪新增資訊

| 同根因歷史 | 已做／結果 | 新學習／不能推論 |
|---|---|---|
| 原恢復批次 | confirm 與 recovery scan 後，第一次 v3 intent 被拒絕 | 定位到派送前目錄 gate；沒有證據支持盲目重送 |
| 原問題提報 | 唯讀比對路徑、inode、device、size、hash；提出多層 reattestation 候選 | 提供方向，尚非核准計畫；不能證明 remount |
| 本輪診斷 | 讀事件鏈、完整時間欄位／名稱 witness，執行一組隔離合成對照 | 補足只差 device 的現況證據；辨識 `OPEN_BATCH` 與最小 list-only 路線 |

本輪沒有消耗新的真實下載／恢復 attempt。舊 UNKNOWN 的原下載問題與此次目錄 device gate 並非同一個根因，不藉此清空任何嘗試歷史。沒有重跑拒絕命令、改目的地、開空帳或換下載入口；既有拒絕已足以停止相同派送路徑。

## 6. 唯一路線：PLANNER_REPLAN

### 有界規劃任務

規劃「notes 目前 list directory 的追加式重新見證」，以恢復**已確認批次中的 list-directory gate** 為首切片。這涉及新的事件、投影與資料信任邊界，目前沒有核准設計，所以不直接推薦進入 Implementer。

規劃限於 `src/line_backup_batch/notes.py`、對應 notes 測試，以及記事本 Skill／references 與必要手冊說明。保持相簿介面、`daily.py`、舊事件、媒體與原始提報不變；不要求新增控制器、外部服務或通用 attestation 框架。本輪沒有對這些產品檔案動手。

### 計畫必須解決的最小決策

1. **信任目標。** 見證宣稱的是「目前路徑與列出的舊 witness 相符，Owner 接受這個 binding 轉接」，而非已證明同一實體 volume。若 Owner 要求排除 byte-identical clone，舊證據不足，應保留阻塞；事後加 nonce 或只讀當前 volume UUID 不能補造歷史證明。
2. **精確事件與重播。** 設計 versioned append-only 轉接，綁 logical list、canonical path、原 binding ref、新舊 device／inode、witness manifest digest、確認證據與 ledger tip。先有唯讀 preview，再由精確確認追加；同一轉接重播不新增事件，衝突／stale preview 拒絕。事件名稱與 schema 尚待計畫定稿。
3. **最小作用域。** 首切片只改現行 list binding 的解析。不自動重認 completion、candidate、舊 staging、pending publish 或 UNKNOWN；不把舊 `LOCAL_CHANGED` 消失列成必要成功條件。完整檔案 witness 用來支持本次轉接，不能變成全列表內容的永久背書。
4. **既有 OPEN_BATCH。** 指定既有 confirmation ref／scope digest／generation／目標路徑的處理方式。最小候選是保留批次與舊 scope，追加獨立的 list binding 確認，再重新做完整 recovery scan；本機 availability 不變，故不預期因此重建 restart scope。若實作必須更動 scope，不能偷偷沿用舊授權，也不能撞到 `RESTART_BATCH_ALREADY_OPEN` 後另開第二批；須另提人工決策。
5. **空目錄與異常。** 首版沒有足夠舊 witness 就拒絕，不要求為本事故擴充空帳遷移。inode／hash／時間／名稱不符、缺檔／額外檔、symlink／hardlink、scope 外異常維持保護。全列表不能用「只有 completion 名稱」當精確集合；根目錄還可能有合法 staging、貼文與 versions，須定義各層允許集合。
6. **交易安全。** 同 ledger lock 內重算 tip、binding 與 witness，定義檔案替換競態的偵測範圍；ledger lock 本身不會鎖住外部 App 寫入。確認前後 crash、再次 device 漂移、並行確認與讀回失敗均需有停止結果。事件提交不建立 intent、staging 或 GUI 動作。

### 狀態交互的規劃約束

| 現有狀態 | list-only 轉接後應保留什麼 |
|---|---|
| 舊完成、目前 `LOCAL_CHANGED` | 舊 completion 與本機可用性判定保留；精確 restart 仍按既有規則建立新版本 |
| 舊 UNKNOWN／空 staging | 原事件、路徑與未知結果不變；不證明停止，也不重認 staging |
| 已確認 restart 批次 | 精確身分、scope、generation、路徑與額外空間承諾不擴張；須新的完整 recovery scan |
| pending naming／candidate | 首切片不授權重新見證這些物件；無合法現有恢復路徑就停止並回報限制 |
| scope 外 `LOCAL_CHANGED` | 仍阻擋相關派送 |
| `LOCAL_MISSING`、排除、受保護歷史 | 不因 list binding 轉接取得重下載資格 |

原提報將「UNKNOWN 可在其他保護下保留」與 `REATTEST_UNRESOLVED_ATTEMPT` 錯誤碼並列。計畫必須說清楚錯誤碼限在哪些物件與情境；若 blanket 拒絕列表內任何 UNKNOWN，會再次擋住本事故的已確認 restart 例外。這不是放寬 UNKNOWN，而是分離 binding 轉接與下載資格。

### 成功檢查

規劃完成需交出最小首切片、精確 schema／CLI／投影規則、相容性與 OPEN_BATCH 接續證明、風險及人工關卡；由 Owner 另行選擇下一角色，不能用本分析當計畫 PASS。

未來實作驗證至少需覆蓋以下矩陣；**全部是後續要求，本輪 `NOT_RUN`**：

| 檢查 | 必要結果 |
|---|---|
| 舊帳本沒有轉接事件 | 舊行為及 fail-closed 保護保持相同 |
| 同路徑／inode、witness 相符，只有 device 不同 | 精確 preview／confirm 只追加一次 binding 轉接；不建 staging／intent |
| 轉接成功但 UNKNOWN／completion 尚在 | 舊事實與本機可用性不被重寫 |
| 本事故形狀：既有 OPEN_BATCH，confirm 後舊 scan 已完成 | 轉接加新 recovery scan 後，合格 scoped v3 intent 可通過 directory gate；其他 gate 仍須各自成立 |
| stale tip、witness 漂移、inode 改變、clone 證據不足、無 witness | 拒絕且不留下成功轉接或下載副作用 |
| 同時 confirm、crash、讀回失敗、再次 device 漂移 | 無分叉成功投影、無自動重送、可確定停止點 |
| 相簿回歸、notes 舊版本重播與 CLI exit 分類 | 保持相容；內部錯誤不作可重試業務拒絕 |
| 受控 macOS 掛載、真實 LINE、跨 Session | 另案有效授權與前景後取證；離線成功不能替代 |

### 停止條件與所需人工決策

若計畫需要忽略 device、手改事件、重認舊 UNKNOWN staging、刪除／改寫既有批次、擴 scope、把沒有歷史證據的 volume 宣稱為同一物件，或修改相簿流程，停止並退回 Owner。若 minimal list-only 方向不足以處理後續 gate，先交出具體證據與有界擴案，不直接加入所有層級的 reattestation。

需要 Owner 決定的是：是否另開規劃，並接受上述 witness-based binding 轉接的信任邊界。這不是要求重複授權本輪診斷、文件提交或推送。本輪到診斷交接為止，不啟動 Planner、Implementer 或 Acceptance。

## 7. 實際命令、證據與完整性

本輪執行的主要命令如下；工作目錄均為 repo 根目錄：

| 命令 | Exit／結果 |
|---|---|
| `git status --short --branch`、`git rev-parse --show-toplevel`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list` | 各 exit 0；候選與乾淨初始狀態已核對 |
| `git diff 3fdad13838ab309103ff287f6bf18464b526e97f 3cfb068cc83508b308f427cdf69ebcd6b13fbcd4 --stat` | exit 0；只有原提報文件 |
| `uname -srm`、`/usr/bin/python3 --version`、`node --version` | 各 exit 0；版本見第 1 節 |
| `PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/notes-volume-review-20261108/diagnose.py` | exit 0；stdout／stderr 保存為 `diagnose.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0；保存為 `notes-help.txt` |
| `shasum -a 256`，對下表指定來源／產物 | exit 0；hash 如下 |

初期定位 `policies/` 的 `rg` 因專案無該目錄 exit 2；後來以全域**同版本**文件完成讀取。另一次試讀不存在的記事本 `references/backup-and-resume.md` exit 2，隨後列出實際 references 並讀 `verification-and-recovery.md`。這兩次是唯讀來源定位失敗，不是產品拒絕或恢復嘗試。

本輪未重跑完整 notes／daily 測試；原提報的 171／73 PASS 是前輪報告，不沿用為本輪測試結果。診斷範圍產品未變，故本輪執行最小因果對照與文件檢查；不藉完整舊測試補成修復驗收。

私有產物均位於 `.local/line-backup/tasks/notes-volume-review-20261108/`；原始證據保留在原任務與原帳本，沒有複製至公開文件。

| 檔案 | SHA-256 |
|---|---|
| `src/line_backup_batch/notes.py` | `80d0ab5b61b27eee4b5ee9727eef6176ba5a489365ae1651e27f0295fc1170b0` |
| `src/line_backup_batch/daily.py` | `20031ef9c8ad6f5eb695cee192568c3afd1a75c3b213591cb3f9254e9a83f970` |
| 本目錄 `problem-report.md` | `68020c506134b353df6681dc82a7167553f704aa77c9e9dcd733a3493acea0f3` |
| 私有 `diagnose.py` | `5bdca55e8651f4ce0e6b2172cb0e52ca0a5aae21db44815b4fca53aa29df5a37` |
| 私有 `read-only-audit.json` | `4a35195c73bbe43ac84dfc519b61f16e73452fad75d089af8b8467d501411825` |
| 私有 `synthetic-probe.json` | `88a48cc851056aacd8098de21047c8a639bc79371dfdc9cda9d61fb1870ade8e` |
| 私有 `protected-snapshot-result.json` | `f76bc469226cccd221dd368a7af51bfadb02a7df8fdc836321964efa3beb0903` |

模型證據分層：本輪沒有由角色名稱推定主模型／effort。Owner 指定一個 GPT-6 Luna helper 在分析完成後整理 commit 訊息；它只協助文件交付，不參與正式獨立驗收。實際派送參數與平台回傳另留私有交付紀錄；沒有 provider usage 證據就不宣稱後端身分、成本或 token 節省。

## 8. 六項狀態與交接

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE
IMPLEMENTATION_STATUS: NOT_APPLICABLE; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_RESTART_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_DIAGNOSTIC_ONLY; PRODUCT_REGRESSION_AND_REAL_E2E_NOT_RUN_THIS_ROUND
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; DIAGNOSIS_DELIVERED_AWAITING_HUMAN_ROUTE_DECISION
```

`PASS_DIAGNOSTIC_ONLY` 僅指本輪的靜態核對、最小合成因果對照與 help 成功；文件差異、提交與遠端核對另記交付紀錄。它不代表推薦設計通過、產品修復或任務備份完成。

人工交接輸入為本文件與原 `problem-report.md`，私有來源供有權限者核對。唯一建議為 `PLANNER_REPLAN`；停止在此，不自動執行下一角色或任何真實下載。
